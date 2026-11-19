"""Self-contained CPU neural factorial evaluator; no candidate-reported science."""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import selectors
import shutil
import signal
import statistics
import subprocess
import sys
import tempfile
import threading
import time

PLANE = "final"
SEEDS = [1009, 2027, 3037]
WALL_SECONDS = 64800
RPC_BUDGET = 1512
START = time.monotonic()
WIRE_LIMIT = 64 * 1024 * 1024
APPLICATION_LIMIT = 16384
CONTROLS = ("constant", "copy", "deranged", "initial")
FINAL_METRICS = ("combined_score", "correct", "completion_fraction", "delayed_fraction",
                 "restricted_mean_lag", "width_lag_contrast", "decay_interaction",
                 "width_lag_ci_low", "width_lag_ci_high", "control_gap")


class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


def bounded_failure_name(value, fallback):
    import re
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


class ProtocolError(RuntimeError):
    def __init__(self, category="malformed_response"):
        self.category = bounded_failure_name(category, "malformed_response")
        super().__init__(self.category)


class BrokerTransportFailure(RuntimeError):
    def __init__(self, operation):
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("broker_transport_failure")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, BrokerTransportFailure):
            return {"component": "broker", "category": "broker_transport_failure",
                    "operation": context.operation}
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, ProtocolError):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout",
            "operation": bounded_failure_name(operation, "unknown")}


def fail_required_baseline(category, cancel_work, record_failure):
    failure = RequiredBaselineFailure(category)
    try:
        record_failure(failure.category)
    except Exception:
        failure.add_note("baseline diagnostic recording failed")
    try:
        cancel_work()
    except Exception:
        failure.add_note("baseline cleanup failed")
    raise failure from None


def collect_required_baseline(result, *, deadline, clock, cancel_work, record_failure):
    try:
        remaining = deadline - clock()
        if remaining <= 0:
            raise TimeoutError()
        value = result(timeout=remaining)
        if clock() > deadline:
            raise TimeoutError()
        return value
    except RequiredBaselineFailure:
        raise
    except (RuntimeError, TimeoutError) as error:
        category = "baseline_timeout" if isinstance(error, TimeoutError) else "baseline_result_failure"
        fail_required_baseline(category, cancel_work, record_failure)


def guard_required_baseline(call, failure_category, cancel_work, record_failure):
    def check():
        category = failure_category()
        if category is not None:
            fail_required_baseline(category, cancel_work, record_failure)
    def guarded(request):
        check()
        result = call(request)
        check()
        return result
    return guarded


class BoundedWorkerStderr:
    LIMIT = 4096

    def __init__(self, stream):
        self.stream = stream
        self.fd = stream.fileno()
        os.set_blocking(self.fd, False)
        self.lines = collections.deque()
        self.pending = bytearray()
        self.dropping_line = False
        self.observed_bytes = 0
        self.retained_bytes = 0
        self.truncated = False
        self.capture_error = None
        self.stop = threading.Event()
        self.result = None
        self.reader = threading.Thread(target=self._drain, name="worker-stderr-reader")
        self.reader.start()

    def _accept(self, chunk):
        self.observed_bytes += len(chunk)
        for segment in chunk.splitlines(keepends=True):
            complete = segment.endswith(b"\n")
            if not self.dropping_line:
                if len(self.pending) + len(segment) > self.LIMIT:
                    self.pending.clear()
                    self.dropping_line = True
                    self.truncated = True
                else:
                    self.pending.extend(segment)
            if complete:
                if not self.dropping_line:
                    line = bytes(self.pending).decode("utf-8", errors="replace")
                    size = len(line.encode("utf-8"))
                    if size <= self.LIMIT:
                        while self.retained_bytes + size > self.LIMIT:
                            self.retained_bytes -= len(self.lines.popleft().encode("utf-8"))
                            self.truncated = True
                        self.lines.append(line)
                        self.retained_bytes += size
                    else:
                        self.truncated = True
                self.pending.clear()
                self.dropping_line = False

    def _drain(self):
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.fd, selectors.EVENT_READ)
                while not self.stop.is_set():
                    if not selector.select(timeout=.05):
                        continue
                    try:
                        chunk = os.read(self.fd, 8192)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        return
                    self._accept(chunk)
                self.capture_error = "reader_stopped_before_eof"
                self.truncated = True
        except (OSError, ValueError):
            self.capture_error = "stderr_capture_failed"
            self.truncated = True
        finally:
            if self.pending or self.dropping_line:
                self.truncated = True
            self.pending.clear()
            self.stream.close()

    def close(self):
        if self.result is not None:
            return dict(self.result)
        self.reader.join(timeout=.2)
        if self.reader.is_alive():
            self.stop.set()
            self.reader.join(timeout=.2)
        if self.reader.is_alive():
            raise RuntimeError("stderr reader cleanup unresolved")
        self.result = {"stderr": "".join(self.lines), "observed_bytes": self.observed_bytes,
                       "retained_bytes": self.retained_bytes, "truncated": self.truncated,
                       "capture_error": self.capture_error}
        return dict(self.result)


def report_worker_exception(error):
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = "WorkerException"
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    if len(message) > 2048 or len(message.encode("utf-8", errors="replace")) > 2048:
        message = "<exception message omitted: too large>"
    print(f"worker_exception type={name}\n{message}", file=sys.stderr, flush=True)


def repair_mode():
    return PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                  or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    except (ValueError, TypeError, RecursionError, OverflowError):
        raise ProtocolError("nonfinite_or_invalid_json") from None
    if len(encoded) >= wire_limit:
        raise ProtocolError("oversized_message")
    return encoded


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def finite_budget_seconds(value):
    if not finite_number(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError("work allowance must be positive")
    return value


def require_joint_workload_budget(*, search, final):
    required = {}
    for plane, profile in (("search", search), ("final", final)):
        episodes, methods = profile["episode_count"], profile["method_count"]
        if any(type(count) is not int or count <= 0 for count in (episodes, methods)):
            raise ValueError("invalid episode or method count")
        times = {name: finite_budget_seconds(profile[name]) for name in (
            "wall_seconds", "startup_seconds", "reset_seconds", "cleanup_seconds", "finish_seconds")}
        work = positive_work_seconds(profile["work_seconds"])
        needed = (times["startup_seconds"] + times["finish_seconds"] + episodes * (
            times["reset_seconds"] + methods * (work + times["cleanup_seconds"])))
        if needed > times["wall_seconds"]:
            raise ValueError("productive work exceeds wall budget")
        required[plane] = needed
    return required


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid remaining method count")
    if now + (methods_remaining + 1) * (work + cleanup_seconds) > episode_deadline:
        raise TimeoutError("insufficient matched reservations")
    return now + work


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if not finite_number(wall_seconds) or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def candidate_subprocess_settings(parent_environment):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES",
                     "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES", "OMP_NUM_THREADS",
                     "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                     "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION", "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "1"
    environment["CUDA_VISIBLE_DEVICES"] = ""
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


NATIVE_BOOT = r'''
import ctypes, importlib.util, json, math, os, resource, sys
root, entrypoint, wall = sys.argv[1], sys.argv[2], int(sys.argv[3])
resource.setrlimit(resource.RLIMIT_CPU, (wall, wall))
resource.setrlimit(resource.RLIMIT_AS, (256*1024**2, 256*1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE, (64,64))
os.umask(0o077)
os.sched_setaffinity(0, {max(os.sched_getaffinity(0))})
os.chdir(root)
libc = ctypes.CDLL(None, use_errno=True)
seccomp = ctypes.CDLL("libseccomp.so.2", use_errno=True)
class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs",ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access",ctypes.c_uint64),("parent_fd",ctypes.c_int)]
handled = (1<<13)-1
rules = Ruleset(handled)
rules_fd = libc.syscall(444, ctypes.byref(rules), ctypes.sizeof(rules), 0)
if rules_fd < 0:
    raise RuntimeError("landlock unavailable")
read = (1<<0)|(1<<2)|(1<<3)
paths = [(root,read),(sys.prefix,read),(sys.base_prefix,read),("/usr",read),("/lib",read),("/lib64",read),
         ("/dev/null",(1<<1)|(1<<2)),("/dev/urandom",1<<2)]
for path, access in paths:
    if not os.path.exists(path):
        continue
    descriptor = os.open(path,os.O_PATH|os.O_CLOEXEC)
    rule = PathRule(access,descriptor)
    if libc.syscall(445,rules_fd,1,ctypes.byref(rule),0) != 0:
        raise RuntimeError("landlock rule failure")
    os.close(descriptor)
if libc.prctl(38,1,0,0,0) != 0 or libc.syscall(446,rules_fd,0) != 0:
    raise RuntimeError("landlock restriction failure")
os.close(rules_fd)
seccomp.seccomp_init.restype = ctypes.c_void_p
seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
context = seccomp.seccomp_init(0x7fff0000)
if not context:
    raise RuntimeError("seccomp unavailable")
for name in ("socket","socketpair","connect","bind","listen","accept","accept4","execve","execveat",
             "fork","vfork","clone","clone3","ptrace","process_vm_readv","process_vm_writev","kill",
             "tkill","tgkill","rt_sigqueueinfo","rt_tgsigqueueinfo","pidfd_open","pidfd_getfd","pidfd_send_signal",
             "process_madvise","process_mrelease","kcmp","perf_event_open","userfaultfd","shmget","shmat",
             "shmctl","shmdt","msgget","msgsnd","msgrcv","msgctl","semget","semop","semtimedop","semctl",
             "mq_open","mount","umount2","unshare","setns","bpf","io_uring_setup","open_by_handle_at"):
    number = seccomp.seccomp_syscall_resolve_name(name.encode())
    if number >= 0 and seccomp.seccomp_rule_add(context,0x00050000|1,number,0) != 0:
        raise RuntimeError("seccomp rule failure")
if seccomp.seccomp_load(context) != 0:
    raise RuntimeError("seccomp restriction failure")
seccomp.seccomp_release(context)
sys.path.insert(0,root)
spec = importlib.util.spec_from_file_location("candidate",entrypoint)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    if len(line) >= 16384:
        raise RuntimeError("oversized request")
    response = module.handle(json.loads(line))
    encoded = json.dumps(response,allow_nan=False,separators=(",",":")).encode()+b"\n"
    if len(encoded) >= 16384:
        raise RuntimeError("oversized response")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


class PipeWorker:
    def __init__(self, arguments, environment, *, cwd=None, baseline=False):
        self.baseline = baseline
        self.closed = False
        self.cleanup_complete = False
        self.buffer = bytearray()
        self.exit_status = None
        self.snapshot = None
        self.process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, env=environment, cwd=cwd,
                                        start_new_session=True, shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdout.fileno(), False)
        os.set_blocking(self.process.stdin.fileno(), False)

    def failure_category(self):
        status = self.process.poll()
        if status is None:
            return None
        self.exit_status = status
        prefix = "baseline" if self.baseline else "candidate"
        return prefix + ("_signal" if status < 0 else "_exit")

    def _failed(self, category):
        if self.baseline:
            raise RequiredBaselineFailure(category)
        raise ProtocolError(category)

    def call(self, request, timeout):
        if self.closed:
            self._failed("baseline_result_failure" if self.baseline else "candidate_unavailable")
        deadline = time.monotonic() + timeout
        limit = 2 * 1024 * 1024 if self.baseline else APPLICATION_LIMIT
        message = bounded_json_line(request, limit)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                position = 0
                while position < len(message):
                    category = self.failure_category()
                    if category:
                        self._failed(category)
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    try:
                        position += os.write(self.process.stdin.fileno(), message[position:])
                    except BlockingIOError:
                        continue
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b"\n" not in self.buffer:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                    if not chunk:
                        remaining = deadline - time.monotonic()
                        if self.process.poll() is None and remaining > 0:
                            try:
                                self.process.wait(timeout=min(.1, remaining))
                            except subprocess.TimeoutExpired:
                                pass
                        self._failed(self.failure_category() or (
                            "baseline_result_failure" if self.baseline else "candidate_eof"))
                    self.buffer.extend(chunk)
                    if len(self.buffer) >= limit:
                        self._failed("baseline_result_failure" if self.baseline else "oversized_response")
            line, _, remainder = self.buffer.partition(b"\n")
            self.buffer = bytearray(remainder)
            try:
                value = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                bounded_json_line(value, limit)
            except (ValueError, UnicodeError, RecursionError):
                self._failed("baseline_result_failure" if self.baseline else "malformed_response")
            return value
        except TimeoutError:
            if self.baseline:
                raise RequiredBaselineFailure("baseline_timeout") from None
            raise
        except (BrokenPipeError, ConnectionError, OSError):
            self._failed(self.failure_category() or ("baseline_result_failure" if self.baseline else "transport_failure"))

    def close(self, failed=False):
        if self.cleanup_complete:
            return
        self.closed = True
        failures = []
        try:
            for termination_signal in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(self.process.pid, termination_signal)
                except ProcessLookupError:
                    pass
                except Exception as failure:
                    failures.append(failure)
                try:
                    if self.process.poll() is None:
                        self.process.wait(timeout=.5)
                except subprocess.TimeoutExpired as failure:
                    if termination_signal == signal.SIGKILL:
                        failures.append(failure)
                except Exception as failure:
                    failures.append(failure)
        finally:
            self.exit_status = self.process.returncode
            for stream in (self.process.stdin, self.process.stdout):
                try:
                    stream.close()
                except Exception as failure:
                    failures.append(failure)
            try:
                self.snapshot = self.capture.close()
            except Exception as failure:
                failures.append(failure)
            self.cleanup_complete = (self.exit_status is not None and self.process.stdin.closed
                                     and self.process.stdout.closed and self.snapshot is not None)
        if failed and repair_mode() and self.snapshot is not None:
            snapshot = self.snapshot
            if snapshot["stderr"]:
                print(snapshot["stderr"], end="", file=sys.stderr)
            print("worker_capture observed_bytes=%d retained_bytes=%d truncated=%d capture_error=%s exit_status=%s" % (
                snapshot["observed_bytes"], snapshot["retained_bytes"], snapshot["truncated"],
                snapshot["capture_error"] or "none", self.exit_status), file=sys.stderr)
        if failures:
            failure = failures[0]
            if len(failures) > 1:
                failure.add_note("additional worker cleanup failures")
            raise failure


class Candidate:
    def __init__(self, path, budget):
        self.count = 0
        self.budget = budget
        self.worker = None
        self.directory = None
        self.proxy = None
        self.path = Path(path)
        socket = os.environ.get("AGENTIC_CANDIDATE_SOCKET")
        fixed = str(path) == "/broker-code/candidate_proxy.py"
        if socket or fixed:
            if not socket or not fixed:
                raise RuntimeError("broker requires both authentication signals")
            spec = importlib.util.spec_from_file_location("trusted_candidate_proxy", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.directory = tempfile.TemporaryDirectory(prefix="recipe-candidate-")
            source = self.path.resolve().parent
            total = 0
            for item in source.rglob("*"):
                if item.is_symlink():
                    raise RuntimeError("candidate symlinks not allowed")
                if item.is_file():
                    total += item.stat().st_size
            if total > 4 * 1024 * 1024:
                raise RuntimeError("candidate source too large")
            shutil.copytree(source, Path(self.directory.name) / "src")

    def call(self, request, timeout):
        self.count += 1
        if self.count > self.budget:
            raise ProtocolError("rpc_budget_exceeded")
        bounded_json_line(request, APPLICATION_LIMIT)
        if self.proxy is not None:
            try:
                response = self._proxy_call(request, timeout)
            except TimeoutError:
                raise
            except (RuntimeError, ConnectionError, OSError) as failure:
                raise BrokerTransportFailure(request.get("op", "unknown")) from failure
        else:
            if request["op"] == "reset":
                if self.worker is not None:
                    self.worker.close()
                interpreter, environment = candidate_subprocess_settings(os.environ)
                root = str(Path(self.directory.name) / "src")
                entry = str(Path(root) / self.path.name)
                self.worker = PipeWorker([interpreter, "-I", "-u", "-c", NATIVE_BOOT,
                                          root, entry, str(WALL_SECONDS)], environment, cwd=root)
            if self.worker is None:
                raise ProtocolError("missing_reset")
            response = self.worker.call(request, timeout)
        bounded_json_line(response, APPLICATION_LIMIT)
        return response

    def _proxy_call(self, request, timeout):
        def expire(signum, frame):
            raise TimeoutError("candidate RPC deadline")
        previous = signal.signal(signal.SIGALRM, expire)
        signal.setitimer(signal.ITIMER_REAL, timeout)
        try:
            return self.proxy(request)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)

    def cancel(self, failed=False):
        if self.worker is not None:
            self.worker.close(failed=failed)
            self.worker = None

    def close(self, failed=False):
        try:
            self.cancel(failed=failed)
        finally:
            if self.directory is not None:
                self.directory.cleanup()


def canonical_document(operation, first, second):
    return json.dumps({"operation": operation, "p": 97, "a": first, "b": second},
                      ensure_ascii=False, separators=(",", ":"))


def raw_digest(operation, first, second):
    import unicodedata
    text = " ".join(unicodedata.normalize("NFKC", canonical_document(operation, first, second)).split())
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def expected_rows(operation):
    rows = [(raw_digest(operation, first, second), first, second)
            for first in range(97) for second in range(97)]
    rows.sort()
    midpoint = len(rows) // 2
    pool = rows[:midpoint] if PLANE == "search" else rows[midpoint:]
    pool.sort(key=lambda row: hashlib.sha256(("train-v1:" + row[0]).encode()).digest())
    training_count = len(pool) * 3 // 10
    result = []
    for index, (digest, first, second) in enumerate(pool):
        label = (first + second if operation == "addition" else first - second) % 97
        result.append({"source_id": operation + "-" + str(first * 97 + second),
                       "row": first * 97 + second, "a": first, "b": second, "label": label,
                       "content_sha256": digest, "split": "train" if index < training_count else "heldout"})
    return result


def load_resource():
    root = Path(os.environ.get("TASK_SOURCE_DIR", Path(__file__).resolve().parent)) / "resources" / PLANE
    path = root / "benchmark.json"
    if path.is_symlink():
        raise ValueError("resource symlink")
    data = json.loads(path.read_text())
    if data["schema_version"] != 1 or data["normalization"] != "nfkc-canonical-json-v1":
        raise ValueError("invalid raw normalization")
    for operation in ("addition", "subtraction"):
        if data["examples"][operation] != expected_rows(operation):
            raise ValueError("raw content or split provenance mismatch")
        rows = data["examples"][operation]
        train = {row["content_sha256"] for row in rows if row["split"] == "train"}
        test = {row["content_sha256"] for row in rows if row["split"] == "heldout"}
        if train & test or len(train) + len(test) != len(rows):
            raise ValueError("normalized content overlap")
    return data


def preflight():
    request = {"op": "recipe", "steps": 20000, "block_steps": 500, "min_lr": .0001, "max_lr": .01}
    responses = [{"ok": True}, {"initial_lr": .00010000000000000002, "decay_rate": .010000000000000002},
                 {"lr": .00010000000000000002}]
    messages = [request, {"op": "reset", "seed": 2**63 - 1},
                {"op": "schedule", "step": 19500, "steps": 20000, "block_steps": 500}] + responses
    for value in messages:
        bounded_json_line(value, APPLICATION_LIMIT)
        bounded_json_line({"request": value, "response": value, "id": 2**63 - 1,
                           "protocol": "python_rpc_v1", "metadata": {"encoding": "utf-8"}})
    operation_table = {"reset": 1, "recipe": 1, "schedule": 40,
                       "training_rpc": 0, "control_rpc": 0, "transfer_rpc": 0, "replay_rpc": 0}
    if sum(operation_table.values()) * 12 * len(SEEDS) != RPC_BUDGET:
        raise ValueError("RPC operation table mismatch")
    require_joint_workload_budget(search={"episode_count": 24, "method_count": 1, "wall_seconds": 21600,
        "startup_seconds": 900, "reset_seconds": 10, "cleanup_seconds": 4, "finish_seconds": 300,
        "work_seconds": 750}, final={"episode_count": 36, "method_count": 1, "wall_seconds": 64800,
        "startup_seconds": 1800, "reset_seconds": 10, "cleanup_seconds": 4, "finish_seconds": 300,
        "work_seconds": 1600})


def make_episodes(smoke):
    return [{"operation": operation, "decay": decay, "width": width, "seed": SEEDS[0] if smoke else seed}
            for operation in ("addition", "subtraction") for decay in (0, 1)
            for width in (16, 64, 256) for seed in ([SEEDS[0]] if smoke else SEEDS)]


def worst_case(episode, horizon=20000):
    return {"score": 0.0, "complete": False, "lag": float(horizon), "delayed": 0.0,
            "gap": -1.0, "trace": [], "duration": 0.0, "memorization": None, "generalization": None}


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure, outcomes=None):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    if outcomes is None:
        outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        began = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = "reset"
        primary_failure = None

        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
        except BrokerTransportFailure as error:
            try:
                record_failure(describe_episode_failure(error, current_operation))
            except Exception:
                error.add_note("episode diagnostic recording failed")
            raise
        finally:
            outcomes[index]["duration"] = max(0.0, clock() - began)
    return outcomes, complete


def first_sustained(trace, field, threshold):
    for index in range(len(trace) - 2):
        if all(row[field] >= threshold for row in trace[index:index + 3]):
            return trace[index]["step"]
    return None


def summarize_trace(trace, horizon):
    if len(trace) < 5 or any(not finite_number(value) for row in trace for key, value in row.items() if key != "controls"):
        raise RequiredBaselineFailure("baseline_result_failure")
    for row in trace:
        if set(row["controls"]) != set(CONTROLS) or any(not finite_number(value) or not 0 <= value <= 1
                                                       for value in row["controls"].values()):
            raise RequiredBaselineFailure("baseline_result_failure")
    memorization = first_sustained(trace, "train_accuracy", .99)
    generalization = first_sustained(trace, "heldout_accuracy", .95)
    lag = horizon if memorization is None else max(0, (horizon if generalization is None else generalization) - memorization)
    late = trace[-5:]
    return {"score": statistics.fmean(row["heldout_accuracy"] for row in late), "complete": True,
            "lag": float(lag), "delayed": float(memorization is not None and generalization is not None and lag > 0),
            "gap": statistics.fmean(row["heldout_accuracy"] - row["controls"][control]
                                    for row in late for control in CONTROLS),
            "memorization": memorization, "generalization": generalization, "trace": trace, "duration": 0.0}


def aggregate(episodes, outcomes, horizon):
    correct = all(row["complete"] for row in outcomes)
    metrics = {"combined_score": statistics.fmean(row["score"] for row in outcomes), "correct": int(correct)}
    if PLANE == "search":
        return metrics
    seed_order = sorted(set(episode["seed"] for episode in episodes))
    def contrast(seed, decay):
        values = []
        for operation in ("addition", "subtraction"):
            grouped = {}
            for width in (16, 256):
                grouped[width] = statistics.fmean(row["lag"] for episode, row in zip(episodes, outcomes)
                    if episode["seed"] == seed and episode["operation"] == operation
                    and episode["decay"] == decay and episode["width"] == width)
            values.append(grouped[16] - grouped[256])
        return statistics.fmean(values)
    contrasts = [contrast(seed, 1) for seed in seed_order]
    center = statistics.fmean(contrasts)
    radius = 2 * horizon if len(contrasts) < 2 else 4.302652729911275 * statistics.stdev(contrasts) / math.sqrt(len(contrasts))
    metrics.update(completion_fraction=statistics.fmean(int(row["complete"]) for row in outcomes),
                   delayed_fraction=statistics.fmean(row["delayed"] for row in outcomes),
                   restricted_mean_lag=statistics.fmean(row["lag"] for row in outcomes),
                   width_lag_contrast=center,
                   decay_interaction=center - statistics.fmean(contrast(seed, 0) for seed in seed_order),
                   width_lag_ci_low=max(-horizon, center - radius),
                   width_lag_ci_high=min(horizon, center + radius),
                   control_gap=statistics.fmean(row["gap"] for row in outcomes))
    return metrics


def evidence(episodes, outcomes):
    records = []
    for seed in sorted(set(episode["seed"] for episode in episodes)):
        selected = [(episode, outcome) for episode, outcome in zip(episodes, outcomes) if episode["seed"] == seed]
        records.append({"seed": seed, "score": statistics.fmean(row["score"] for _, row in selected),
                        "correct": all(row["complete"] for _, row in selected),
                        "duration_seconds": sum(row["duration"] for _, row in selected),
                        "solution": [{"case": episode, "observations": {key: value for key, value in row.items()
                                                                      if key != "duration"}}
                                     for episode, row in selected]})
    return {"schema_version": 1, "episodes": records}


def training_worker(repair):
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit_seconds(WALL_SECONDS, 1),) * 2)
    resource.setrlimit(resource.RLIMIT_AS, (3584 * 1024**2,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2,) * 2)
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
    import torch
    import torch.nn.functional as functional
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    state = {}

    def features(rows):
        pairs = torch.tensor([[row[0], row[1]] for row in rows], dtype=torch.int64)
        return functional.one_hot(pairs, 97).reshape(-1, 194).float()

    def checkpoint():
        model, train_x, test_x = state["model"], state["train_x"], state["test_x"]
        with torch.no_grad():
            train_logits, test_logits = model(train_x), model(test_x)
            train_accuracy = (train_logits.argmax(1) == state["train_y"]).float().mean().item()
            heldout_accuracy = (test_logits.argmax(1) == state["test_y"]).float().mean().item()
            controls = {"constant": state["constant"], "copy": state["copy"],
                        "deranged": (test_logits[state["permutation"]].argmax(1) == state["test_y"]).float().mean().item(),
                        "initial": (state["initial_model"](test_x).argmax(1) == state["test_y"]).float().mean().item()}
            return {"step": state["step"], "train_accuracy": train_accuracy, "heldout_accuracy": heldout_accuracy,
                    "train_loss": functional.cross_entropy(train_logits, state["train_y"]).item(),
                    "heldout_loss": functional.cross_entropy(test_logits, state["test_y"]).item(),
                    "weight_norm": math.sqrt(sum(parameter.double().square().sum().item() for parameter in model.parameters())),
                    "parameter_count": sum(parameter.numel() for parameter in model.parameters()), "controls": controls}

    for line in sys.stdin.buffer:
        request = json.loads(line)
        if request["op"] == "ready":
            response = {"ready": True}
        elif request["op"] == "init":
            import copy
            torch.manual_seed(request["seed"])
            width = request["width"]
            model = torch.nn.Sequential(torch.nn.Linear(194, width), torch.nn.ReLU(), torch.nn.Linear(width, 97))
            training, heldout = request["train"], request["test"]
            train_y = torch.tensor([row[2] for row in training], dtype=torch.int64)
            test_y = torch.tensor([row[2] for row in heldout], dtype=torch.int64)
            counts = torch.bincount(test_y, minlength=97)
            shift = int(counts.max().item())
            order = torch.argsort(test_y, stable=True)
            permutation = torch.empty(len(test_y), dtype=torch.int64)
            permutation[order] = order.roll(shift)
            if len(test_y) < 2 or (permutation == torch.arange(len(test_y))).any() or (test_y[permutation] == test_y).any():
                raise RuntimeError("vacuous_input_control")
            mode = torch.bincount(train_y, minlength=97).argmax().item()
            lookup = {(row[0], row[1]): row[2] for row in training}
            copied = torch.tensor([lookup.get((row[0], row[1]), mode) for row in heldout])
            state = {"model": model, "initial_model": copy.deepcopy(model), "train_x": features(training),
                     "test_x": features(heldout), "train_y": train_y, "test_y": test_y, "step": 0,
                     "permutation": permutation, "constant": (test_y == mode).float().mean().item(),
                     "copy": (copied == test_y).float().mean().item(), "horizon": request["horizon"],
                     "optimizer": torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=request["decay"],
                                                    betas=(.9, .999), eps=1e-8, foreach=False, fused=False)}
            if sum(parameter.numel() for parameter in model.parameters()) != 292 * width + 97:
                raise RuntimeError("invalid_architecture")
            response = checkpoint()
        elif request["op"] == "train":
            if state["step"] + request["steps"] > state["horizon"]:
                raise RuntimeError("update_budget_exceeded")
            for group in state["optimizer"].param_groups:
                group["lr"] = request["lr"]
            for _ in range(request["steps"]):
                state["optimizer"].zero_grad(set_to_none=True)
                loss = functional.cross_entropy(state["model"](state["train_x"]), state["train_y"])
                loss.backward()
                state["optimizer"].step()
                state["step"] += 1
            response = checkpoint()
        else:
            raise RuntimeError("unknown_worker_operation")
        sys.stdout.buffer.write(bounded_json_line(response))
        sys.stdout.buffer.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    horizon, block_steps = (16, 2) if smoke else (20000, 500)
    episodes = make_episodes(smoke)
    outcomes = [worst_case(episode, horizon) for episode in episodes]
    destination = Path(args.results_dir)
    destination.mkdir(parents=True, exist_ok=True)
    candidate = None
    worker = None
    error = None
    complete = False
    hard_deadline = START + (116 if smoke else WALL_SECONDS - (900 if PLANE == "search" else 1800))
    finish_reserve = 5 if smoke else 300
    baseline_failure = None
    cleanup_failed = False
    recipe_reference = None
    current_operation = "setup"
    try:
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
            os.environ[name] = "1"
        if len(os.sched_getaffinity(0)) < 2:
            raise RuntimeError("two CPU cores required")
        preflight()
        data = load_resource()
        candidate = Candidate(args.program_path, RPC_BUDGET)
        interpreter, environment = candidate_subprocess_settings(os.environ)
        worker = PipeWorker([interpreter, "-I", "-u", str(Path(__file__).resolve()), "--training-worker",
                             "1" if repair_mode() else "0"], environment, baseline=True)

        if worker.call({"op": "ready"}, timeout=20 if smoke else 120) != {"ready": True}:
            raise RequiredBaselineFailure("baseline_result_failure")

        def record_failure(failure):
            nonlocal cleanup_failed
            if PLANE == "search":
                print("episode_failure component=%s category=%s operation=%s" % (
                    bounded_failure_name(failure["component"], "candidate"),
                    bounded_failure_name(failure["category"], "unknown"),
                    bounded_failure_name(failure["operation"], "unknown")), file=sys.stderr)
            try:
                candidate.cancel(failed=True)
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                cleanup_failed = True
            if failure["component"] == "baseline":
                try:
                    worker.close(failed=True)
                except (RuntimeError, OSError, subprocess.TimeoutExpired):
                    cleanup_failed = True

        def evaluate_episode(episode, call, deadline):
            nonlocal recipe_reference, baseline_failure, current_operation
            work_allowance = 1.7 if smoke else (750 if PLANE == "search" else 1600)
            method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                methods_remaining=0, work_seconds=work_allowance, cleanup_seconds=.01 if smoke else 4)
            if baseline_failure is not None:
                raise RequiredBaselineFailure(baseline_failure)
            raw_call = call
            def checked_call(request):
                category = worker.failure_category()
                if category:
                    raise RequiredBaselineFailure(category)
                response = raw_call(request)
                category = worker.failure_category()
                if category:
                    raise RequiredBaselineFailure(category)
                return response
            call = checked_call
            recipe = call({"op": "recipe", "steps": horizon, "block_steps": block_steps, "min_lr": .0001, "max_lr": .01})
            if type(recipe) is not dict or set(recipe) != {"initial_lr", "decay_rate"} or any(
                not finite_number(value) for value in recipe.values()) or not .0001 <= recipe["initial_lr"] <= .01 or not .01 <= recipe["decay_rate"] <= 1:
                raise ProtocolError("invalid_recipe")
            normalized = (float(recipe["initial_lr"]), float(recipe["decay_rate"]))
            if recipe_reference is None:
                recipe_reference = normalized
            if normalized != recipe_reference:
                raise ProtocolError("nonshared_recipe")
            rows = data["examples"][episode["operation"]]
            training = [[row["a"], row["b"], row["label"]] for row in rows if row["split"] == "train"]
            heldout = [[row["a"], row["b"], row["label"]] for row in rows if row["split"] == "heldout"]
            if smoke:
                training, heldout = training[:128], heldout[:256]
            def train_call(request):
                nonlocal baseline_failure
                try:
                    return worker.call(request, timeout=max(.001, method_deadline - time.monotonic()))
                except RequiredBaselineFailure as failure:
                    baseline_failure = failure.category
                    raise
            current_operation = "baseline_worker"
            trace = [train_call({"op": "init", **episode, "train": training, "test": heldout, "horizon": horizon})]
            for step in range(0, horizon, block_steps):
                category = worker.failure_category()
                if category:
                    baseline_failure = category
                    raise RequiredBaselineFailure(category)
                response = call({"op": "schedule", "step": step, "steps": horizon, "block_steps": block_steps})
                expected = max(.0001, min(.01, normalized[0] * normalized[1] ** (step / horizon)))
                if type(response) is not dict or set(response) != {"lr"} or not finite_number(response["lr"]) or not .0001 <= response["lr"] <= .01 or not math.isclose(response["lr"], expected, rel_tol=0, abs_tol=1e-12):
                    raise ProtocolError("invalid_schedule")
                if time.monotonic() >= method_deadline:
                    raise TimeoutError()
                trace.append(train_call({"op": "train", "lr": response["lr"], "steps": block_steps}))
            if trace[-1]["step"] != horizon or len(trace) != horizon // block_steps + 1:
                raise RequiredBaselineFailure("baseline_result_failure")
            return summarize_trace(trace, horizon)

        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline,
            finish_reserve=finish_reserve, reset_timeout=1 if smoke else 10,
            episode_overhead=4, rpc_cap=1 if smoke else 15,
            clock=time.monotonic, rpc=candidate.call, evaluate=evaluate_episode,
            worst_case=lambda episode: worst_case(episode, horizon), record_failure=record_failure,
            outcomes=outcomes)
        if time.monotonic() >= hard_deadline - finish_reserve:
            complete = False
    except Exception as failure:
        error = failure
        complete = False
    finally:
        for participant in (worker, candidate):
            if participant is not None:
                try:
                    participant.close(failed=error is not None)
                except (RuntimeError, OSError, subprocess.TimeoutExpired) as failure:
                    cleanup_failed = True
                    if error is None:
                        error = failure
        complete = complete and not cleanup_failed
        metrics = aggregate(episodes, outcomes, horizon)
        metrics["correct"] = int(complete and all(row["complete"] for row in outcomes))
        expected_keys = {"combined_score", "correct"} if PLANE == "search" else set(FINAL_METRICS)
        if set(metrics) != expected_keys or not all(finite_number(value) for value in metrics.values()):
            raise RuntimeError("invalid evaluator metrics")
        (destination / "metrics.json").write_bytes(bounded_json_line(metrics))
        (destination / "correct.json").write_bytes(bounded_json_line({"correct": bool(metrics["correct"])}))
        observation = evidence(episodes, outcomes)
        (destination / "evaluation_evidence.json").write_bytes(bounded_json_line(observation, 16 * 1024 * 1024))
        if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
            (destination / "qualification.json").write_bytes(bounded_json_line(
                {"schema_version": 1, "feasible": bool(complete and not smoke)}))
    if error is not None:
        if PLANE == "search":
            if isinstance(error, RequiredBaselineFailure):
                print("required_worker_failure category=" + error.category, file=sys.stderr)
            print("evaluator_exception type=" + bounded_failure_name(type(error).__name__.lower(), "error")
                  + " message=evaluation_failed", file=sys.stderr)
        else:
            print("evaluator_exception category=evaluation_failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--training-worker":
        try:
            training_worker(sys.argv[2] == "1")
        except Exception as worker_error:
            if PLANE == "search" and sys.argv[2] == "1":
                report_worker_exception(worker_error)
            else:
                print("worker_failure category=baseline_result_failure", file=sys.stderr)
            sys.exit(1)
    else:
        sys.exit(main())
