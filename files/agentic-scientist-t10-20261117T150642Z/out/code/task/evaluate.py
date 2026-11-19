"""Self-contained offline evaluator. Only this plane's frozen root is readable.

Scientific validity, operational search eligibility, and publication claims are
separate: supported negative findings are eligible; this scaffold does not
certify arbitrary candidates' theoretical variance assumptions or paper quality.
"""
import argparse
import base64
import collections
import ctypes
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time

PLANE = "search"
SEEDS = [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199]
WALL_SECONDS = 3600
CASES = ("linear", "nonlinear", "uninformative", "rare_outcome", "gene_expression",
         "constant_nonlinear", "permuted_nonlinear")
MAX_CHUNKS = 8
CHUNK_BYTES = 1024**2
WIRE_LIMIT = 64 * 1024**2
RPC_BUDGET = (7 * len(SEEDS) + 1) * (1 + 1 + MAX_CHUNKS + 1 + 2)
METRICS = ("combined_score", "nominal_coverage", "empirical_coverage", "minimum_case_coverage",
           "mean_width_ratio", "width_utility", "failure_fraction", "control_pass",
           "scientific_validity", "correct")

class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


def bounded_failure_name(value, fallback):
    import re
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


def describe_episode_failure(error, operation):
    # A finally-block cleanup exception may wrap the original required-worker failure.
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response",
                    "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category,
                    "operation": "baseline_worker"}
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


import collections
import os
import selectors
import sys
import threading


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
            # Only LF ends a diagnostic line. splitlines also splits CR; accumulate it.
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
            # Do not close a stream concurrently with its owner or claim cleanup passed.
            raise RuntimeError("stderr reader cleanup unresolved")
        self.result = {
            "stderr": "".join(self.lines),
            "observed_bytes": self.observed_bytes,
            "retained_bytes": self.retained_bytes,
            "truncated": self.truncated,
            "capture_error": self.capture_error,
        }
        return dict(self.result)


def report_worker_exception(error):
    # Search-only entry point; the host sanitizes this untrusted diagnostic later.
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = "WorkerException"
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    # Drop an oversized message whole; never retain a potentially split credential.
    if len(message) > 2048 or len(message.encode("utf-8", errors="replace")) > 2048:
        message = "<exception message omitted: too large>"
    print(f"worker_exception type={name}\n{message}", file=sys.stderr, flush=True)


def finite_budget_seconds(value):
    import math
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
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
            "wall_seconds", "startup_seconds", "reset_seconds", "cleanup_seconds", "finish_seconds"
        )}
        work = positive_work_seconds(profile["work_seconds"])
        needed = (times["startup_seconds"] + times["finish_seconds"]
                  + episodes * (times["reset_seconds"] + methods * (work + times["cleanup_seconds"])))
        finite_budget_seconds(needed)
        if needed > times["wall_seconds"]:
            raise ValueError(f"{plane} productive work exceeds the declared wall budget")
        required[plane] = needed
    return required


def require_productive_baseline(measured_seconds, *, minimum_seconds):
    try:
        measured = positive_work_seconds(measured_seconds)
        minimum = positive_work_seconds(minimum_seconds)
    except ValueError:
        raise ValueError("invalid productive baseline measurement") from None
    if measured < minimum:
        raise ValueError("productive baseline is shorter than its canonical minimum")


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid remaining method count")
    needed = (methods_remaining + 1) * (work + cleanup_seconds)
    if now + needed > episode_deadline:
        raise TimeoutError("insufficient matched method reservations")
    return now + work


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout,
                          episode_overhead, rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
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
        primary_error = None
        def call(request, method_deadline):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock(), method_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError()
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            timeout = min(reset_timeout, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError()
            require_reset_ack(rpc({"op": "reset", "seed": episode.get("reset_seed", episode["seed"])}, timeout=timeout))
            outcomes[index] = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                outcomes[index] = worst_case(episode)
                raise TimeoutError()
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            primary_error = error
            complete = False
            outcomes[index] = worst_case(episode)
            failure = primary_failure or describe_episode_failure(error, current_operation)
            outcomes[index]["failure_metadata"] = dict(failure)
            if getattr(error, "cleanup_failed", False):
                outcomes[index]["failure_metadata"]["cleanup_failed"] = True
            status = getattr(error, "baseline_status", None)
            if type(status) is int:
                outcomes[index]["failure_metadata"]["exit_status"] = status
            record_failure(failure)
        finally:
            try:
                rpc.cleanup(primary_error is not None)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                if primary_error is None:
                    complete = False
                    outcomes[index] = worst_case(episode)
                    outcomes[index]["failure_metadata"] = {"component": "candidate", "category": "cleanup_failure", "operation": "cleanup"}
                    record_failure(outcomes[index]["failure_metadata"])
                outcomes[index].setdefault("failure_metadata", {})["cleanup_failed"] = True
            outcomes[index]["duration"] = max(0.0, clock() - began)
    return outcomes, complete


class ProtocolError(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "malformed_response")
        super().__init__("candidate protocol failure")


_original_describe = describe_episode_failure


def describe_episode_failure(error, operation):
    if isinstance(error, ProtocolError):
        return {"component": "candidate", "category": error.category,
                "operation": bounded_failure_name(operation, "unknown")}
    return _original_describe(error, operation)


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ProtocolError("wire_limit")
    return encoded


def strict_json(raw):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("duplicate key")
            value[key] = item
        return value
    def invalid(value):
        raise ValueError("nonfinite JSON")
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError):
        raise ProtocolError("malformed_response") from None


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                       MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1", NUMBA_NUM_THREADS="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


NATIVE_RUNNER = r'''
import base64,ctypes,importlib.util,json,math,os,resource,sys,tempfile
NATIVE_REPAIR_MODE = False

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

candidate_path=sys.argv[1]
tempfile.tempdir=os.getcwd()
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
resource.setrlimit(resource.RLIMIT_AS,(12*1024**3,12*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(int(sys.argv[2]),int(sys.argv[2])+1))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_NPROC,(64,64))
import numpy
import scipy.stats
libc=ctypes.CDLL(None,use_errno=True)
seccomp=ctypes.CDLL("libseccomp.so.2",use_errno=True)
def checked(value):
    if value < 0: raise RuntimeError("native sandbox unavailable")
    return value

class Ruleset(ctypes.Structure):
    _fields_=[("handled_access_fs",ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_=1
    _fields_=[("allowed_access",ctypes.c_uint64),("parent_fd",ctypes.c_int32)]
checked(libc.prctl(38,1,0,0,0))
abi=checked(libc.syscall(444,0,0,1))
if abi < 3: raise RuntimeError("Landlock ABI>=3 required")
handled=(1<<15)-1
if abi>=5: handled|=1<<15
ruleset=Ruleset(handled)
rule_fd=checked(libc.syscall(444,ctypes.byref(ruleset),ctypes.sizeof(ruleset),0))
allowed=[sys.prefix,sys.base_prefix,"/usr/lib","/lib","/lib64","/etc/ld.so.cache",
         "/dev/null","/dev/urandom",os.path.dirname(candidate_path)]
for location in allowed:
    if not os.path.exists(location): continue
    parent=checked(os.open(location,os.O_PATH|os.O_CLOEXEC))
    access=1|4|(8 if os.path.isdir(location) else 0)
    rule=PathRule(access,parent)
    checked(libc.syscall(445,rule_fd,1,ctypes.byref(rule),0))
    os.close(parent)
parent=checked(os.open(os.getcwd(),os.O_PATH|os.O_CLOEXEC))
rule=PathRule(4|8|32,parent)
checked(libc.syscall(445,rule_fd,1,ctypes.byref(rule),0))
os.close(parent)
checked(libc.syscall(446,rule_fd,0))
os.close(rule_fd)
seccomp.seccomp_init.argtypes=[ctypes.c_uint32]
seccomp.seccomp_init.restype=ctypes.c_void_p
seccomp.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
seccomp.seccomp_syscall_resolve_name.restype=ctypes.c_int
seccomp.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
seccomp.seccomp_load.argtypes=[ctypes.c_void_p]
seccomp.seccomp_release.argtypes=[ctypes.c_void_p]
context=seccomp.seccomp_init(0x7fff0000)
if not context: raise RuntimeError("seccomp unavailable")
for name in ("socket","socketpair","connect","bind","listen","accept","accept4","ptrace",
             "process_vm_readv","process_vm_writev","pidfd_getfd","mount","umount2",
             "bpf","perf_event_open","io_uring_setup","execve","execveat","fork","vfork",
             "kill","tkill","tgkill","setsid","setpgid"):
    number=seccomp.seccomp_syscall_resolve_name(name.encode())
    if number>=0: checked(seccomp.seccomp_rule_add(context,0x50000|1,number,0))
checked(seccomp.seccomp_load(context))
seccomp.seccomp_release(context)
spec=importlib.util.spec_from_file_location("candidate",candidate_path)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    try:
        request=json.loads(line)
        response=module.handle(request)
        encoded=json.dumps(response,allow_nan=False,separators=(",",":")).encode()+b"\n"
        if len(encoded)>=65536: raise ValueError("response_limit")
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    except Exception as error:
        if NATIVE_REPAIR_MODE:
            report_worker_exception(error)
        else:
            print("candidate_worker_failure",file=sys.stderr,flush=True)
        raise SystemExit(1)

'''


def repair_mode():
    return PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                 or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


def record_failure(failure):
    try:
        if type(failure) is str:
            failure = {"component": "baseline", "category": failure, "operation": "baseline_worker"}
        fields = [bounded_failure_name(failure.get(key), "unknown")[:48]
                  for key in ("component", "category", "operation")]
        print("episode_failure component=%s category=%s operation=%s" % tuple(fields), file=sys.stderr)
    except (OSError, ValueError):
        pass


class PipeWorker:
    def __init__(self, arguments, environment, directory, component):
        self.component = component
        self.process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, env=environment, cwd=directory,
                                        start_new_session=True, shell=False, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.closed = False
        self.failed = False
        self.exit_status = None

    def failure_category(self):
        status = self.process.poll()
        if status is None:
            return None
        self.exit_status = status
        return "baseline_signal" if status < 0 else "baseline_exit"

    def call(self, request, timeout):
        deadline = time.monotonic() + timeout
        encoded = bounded_json_line(request)
        received = bytearray()
        sent = 0
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                while sent < len(encoded):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    try:
                        sent += os.write(self.process.stdin.fileno(), encoded[sent:sent + 65536])
                    except BlockingIOError:
                        continue
                selector.unregister(self.process.stdin)
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ProtocolError("worker_exit")
                    received.extend(chunk)
                    if len(received) >= 65536:
                        raise ProtocolError("response_limit")
                    if b"\n" in received:
                        if received.count(b"\n") != 1 or not received.endswith(b"\n"):
                            raise ProtocolError("malformed_response")
                        return strict_json(received)
        except (BrokenPipeError, ConnectionResetError):
            self.failed = True
            raise ProtocolError("worker_exit") from None
        except (TimeoutError, ProtocolError):
            self.failed = True
            raise

    def close(self, failure=False):
        if self.closed:
            return
        self.closed = True
        if self.process.poll() is None:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            self.process.wait(timeout=.2)
            self.exit_status = self.process.returncode
        finally:
            self.process.stdin.close()
            self.process.stdout.close()
            snapshot = self.capture.close()
        if (failure or self.failed) and repair_mode():
            print("worker_capture component=%s observed_bytes=%d retained_bytes=%d truncated=%d capture_error=%s" % (
                self.component, snapshot["observed_bytes"], snapshot["retained_bytes"],
                int(snapshot["truncated"]), snapshot["capture_error"] or "none"), file=sys.stderr)
            if snapshot["stderr"]:
                print(snapshot["stderr"], file=sys.stderr, end="", flush=True)


class CandidateRPC:
    def __init__(self, program_path):
        self.program_path = str(Path(program_path).absolute())
        self.calls = 0
        self.worker = None
        self.directory = None
        self.proxy = None
        trusted_path = self.program_path == "/broker-code/candidate_proxy.py"
        socket_present = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
        if trusted_path != socket_present:
            raise ValueError("invalid broker configuration")
        if trusted_path and socket_present:
            spec = importlib.util.spec_from_file_location("candidate_proxy", self.program_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        self.python, self.environment = candidate_subprocess_settings(os.environ)

    def __call__(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolError("rpc_limit")
        bounded_json_line(request)
        if self.proxy is not None:
            def expired(signum, frame):
                raise TimeoutError()
            previous = signal.signal(signal.SIGALRM, expired)
            began = time.monotonic()
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                response = self.proxy(request)
            except Exception as error:
                signal.setitimer(signal.ITIMER_REAL, 0)
                if repair_mode():
                    print("candidate_rpc_failure operation=%s call_index=%d elapsed_seconds=%.6f timeout_seconds=%.6f" % (
                        bounded_failure_name(request.get("op"), "unknown"),
                        self.calls, time.monotonic() - began, timeout), file=sys.stderr, flush=True)
                    report_worker_exception(error)
                raise
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
            if len(bounded_json_line(response)) >= 65536:
                raise ProtocolError("response_limit")
            return response
        if request["op"] == "reset":
            if self.worker is not None:
                raise RuntimeError("previous episode not cleaned up")
            self.directory = tempfile.TemporaryDirectory(prefix="interval-candidate-")
            native_code = NATIVE_RUNNER.replace("NATIVE_REPAIR_MODE = False", "NATIVE_REPAIR_MODE = " + repr(repair_mode()), 1)
            self.worker = PipeWorker([self.python, "-I", "-u", "-c", native_code,
                                      self.program_path, str(math.ceil(WALL_SECONDS))],
                                     self.environment, self.directory.name, "candidate")
        if self.worker is None:
            raise ProtocolError("reset_required")
        return self.worker.call(request, timeout)

    def cleanup(self, failure=False):
        if self.worker is not None:
            worker, self.worker = self.worker, None
            worker.close(failure)
        if self.directory is not None:
            self.directory.cleanup()
            self.directory = None


class Baseline:
    def __init__(self):
        self.cause_status = None
        python, environment = candidate_subprocess_settings(os.environ)
        arguments = [python, "-I", "-u", str(Path(__file__).resolve()), "--baseline-worker"]
        if repair_mode():
            arguments.append("--repair-worker")
        self.worker = PipeWorker(arguments, environment, "/tmp", "baseline")
        self.broken = None
        try:
            response = self.worker.call({"op": "preflight"}, timeout=45)
            if response != {"ok": True}:
                self.broken = "baseline_result_failure"
        except TimeoutError:
            self.broken = "baseline_timeout"
        except ProtocolError:
            self.broken = self.worker.failure_category() or "baseline_result_failure"
        if self.broken:
            self.cause_status = self.worker.process.poll()
            self.worker.close(True)

    def failure_category(self):
        category = self.broken or self.worker.failure_category()
        if category and self.cause_status is None and not self.worker.closed:
            self.cause_status = self.worker.process.poll()
        return category

    def cancel(self):
        self.worker.close(True)

    def check(self):
        category = self.failure_category()
        if category is not None:
            raise RequiredBaselineFailure(category)

    def compute(self, data, deadline):
        self.check()
        try:
            value = self.worker.call({"op": "intervals", "values": data}, deadline - time.monotonic())
        except TimeoutError:
            self.broken = "baseline_timeout"
            raise RequiredBaselineFailure(self.broken) from None
        except ProtocolError:
            self.broken = self.worker.failure_category() or "baseline_result_failure"
            self.cause_status = self.worker.exit_status
            raise RequiredBaselineFailure(self.broken) from None
        self.check()
        if type(value) is not dict or set(value) != {"label_only", "ppi", "ppi_plus_plus", "productive_seconds"}:
            self.broken = "baseline_result_failure"
            raise RequiredBaselineFailure(self.broken)
        try:
            for name in ("label_only", "ppi", "ppi_plus_plus"):
                interval(value[name], False)
        except ProtocolError:
            self.broken = "baseline_result_failure"
            raise RequiredBaselineFailure(self.broken) from None
        if not finite(value["productive_seconds"]) or value["productive_seconds"] < 0:
            raise RequiredBaselineFailure("baseline_result_failure")
        return value


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def interval(value, bernoulli):
    if type(value) is not dict or set(value) != {"lower", "upper"}:
        raise ProtocolError("malformed_response")
    lower, upper = value["lower"], value["upper"]
    if not finite(lower) or not finite(upper) or lower > upper or not math.isfinite(upper - lower):
        raise ProtocolError("invalid_interval")
    if bernoulli and not (0 <= lower <= upper <= 1):
        raise ProtocolError("invalid_interval_domain")
    return [float(lower), float(upper)]


def ack(value):
    if type(value) is not dict or set(value) != {"ok"} or value["ok"] is not True:
        raise ProtocolError("malformed_response")


def label_only(outcomes, kind):
    import numpy as np
    from scipy.stats import beta, t
    count = len(outcomes)
    if kind == "bernoulli":
        successes = int(np.sum(outcomes))
        lower = 0 if successes == 0 else beta.ppf(.025, successes, count - successes + 1)
        upper = 1 if successes == count else beta.ppf(.975, successes + 1, count - successes)
    else:
        center = np.mean(outcomes)
        radius = t.ppf(.975, count - 1) * np.std(outcomes, ddof=1) / math.sqrt(count)
        lower, upper = center - radius, center + radius
    return {"lower": float(lower), "upper": float(upper)}


def baseline_worker():
    repair = "--repair-worker" in sys.argv and PLANE == "search"
    try:
        resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(WALL_SECONDS), math.ceil(WALL_SECONDS) + 1))
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
        import numpy as np
        from scipy.stats import norm
        from ppi_py import ppi_mean_ci
        from ppi_py.ppi import _calc_lam_glm
        for line in sys.stdin.buffer:
            request = strict_json(line)
            if request["op"] == "preflight":
                predictions = np.linspace(0, 1, 32)
                outcomes = .2 + .3 * predictions + .03 * np.sin(17 * predictions)
                unlab = np.linspace(.01, .99, 256)
                expected = np.clip(np.mean((outcomes - outcomes.mean()) * (predictions - predictions.mean())) /
                                   ((1 + len(outcomes) / len(unlab)) * np.var(np.r_[predictions, unlab], ddof=1)), 0, 1)
                actual = _calc_lam_glm(outcomes[:, None], predictions[:, None], unlab[:, None], np.eye(1), clip=True)
                if not np.isclose(actual, expected, rtol=1e-12, atol=1e-12):
                    raise RuntimeError("coefficient path mismatch")
                original = np.asarray(ppi_mean_ci(outcomes, predictions, unlab, alpha=.05, lam=1)).reshape(2)
                optimized = np.asarray(ppi_mean_ci(outcomes, predictions, unlab, alpha=.05, lam=None)).reshape(2)
                explicit = np.asarray(ppi_mean_ci(outcomes, predictions, unlab, alpha=.05, lam=float(expected))).reshape(2)
                if np.allclose(original, optimized) or not np.allclose(optimized, explicit):
                    raise RuntimeError("reference methods not distinct")
                response = {"ok": True}
            else:
                started = time.monotonic()
                data = request["values"]
                values = np.frombuffer(base64.b64decode(data["data"], validate=True), dtype="<f8")
                count = data["n"]
                outcomes, predictions, unlab = np.split(values, [count, 2 * count])
                response = {"label_only": label_only(outcomes, data["label_kind"])}
                for name, coefficient in (("ppi", 1), ("ppi_plus_plus", None)):
                    if coefficient is None and np.var(np.r_[predictions, unlab]) == 0:
                        coefficient = 0
                    limits = np.asarray(ppi_mean_ci(outcomes, predictions, unlab, alpha=.05, lam=coefficient)).reshape(2)
                    response[name] = {"lower": float(limits[0]), "upper": float(limits[1])}
                response["productive_seconds"] = time.monotonic() - started
            sys.stdout.buffer.write(bounded_json_line(response))
            sys.stdout.buffer.flush()
    except Exception as error:
        if repair:
            report_worker_exception(error)
        else:
            print("baseline_worker_failure", file=sys.stderr, flush=True)
        return 1
    return 0


def preflight_wire():
    requests = [
        {"op": "reset", "seed": 2**63 - 1},
        {"op": "update", "phase": "start", "n": 8, "N": 1048560, "alpha": .05,
         "label_kind": "bernoulli", "dtype": "<f8", "encoding": "base64", "shape": [1048576],
         "total_bytes": 8 * 1024**2, "chunks": MAX_CHUNKS},
        {"op": "update", "phase": "chunk", "transfer_id": "a" * 64, "index": 7,
         "data": base64.b64encode(bytes(CHUNK_BYTES)).decode("ascii")},
        {"op": "update", "phase": "commit", "transfer_id": "a" * 64}, {"op": "infer"}]
    responses = [{"ok": True}, {"ok": True, "transfer_id": "a" * 64},
                 {"lower": -sys.float_info.max, "upper": sys.float_info.max}]
    sizes = [len(bounded_json_line(value)) for value in requests + responses]
    if max(sizes) >= 32 * 1024**2:
        raise ValueError("operational wire ceiling exceeded")
    mock = []
    for unused in range(7 * len(SEEDS) + 1):
        mock.extend(["reset", "update_start"] + ["update_chunk"] * MAX_CHUNKS
                    + ["update_commit", "infer", "infer"])
    if len(mock) != RPC_BUDGET or not 0 < RPC_BUDGET <= 10000000:
        raise ValueError("RPC operation table mismatch")
    return {"largest_json_line_bytes": max(sizes), "max_protocol_calls": len(mock)}


class Data:
    def __init__(self, root):
        import numpy as np
        self.root = root
        self.manifest = strict_json((root / "manifest.json").read_bytes())
        if self.manifest["seeds"] != SEEDS:
            raise ValueError("seed manifest mismatch")
        for name, expected in self.manifest["files"].items():
            if not re.fullmatch(r"[A-Za-z0-9_.]+", name):
                raise ValueError("invalid resource name")
            with open(root / name, "rb") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != expected:
                    raise ValueError("resource integrity failure")
        with np.load(root / "gene_expression.npz", allow_pickle=False) as source:
            self.real = source["raw"].copy()
        if not np.isfinite(self.real).all():
            raise ValueError("nonfinite raw source")
        self.current_case, self.current = None, None

    def episode(self, case, seed, smoke):
        import numpy as np
        count, unlab_count = (32, 256) if smoke else (128, 8192)
        kind = "real" if case == "gene_expression" else "bernoulli"
        underlying = "nonlinear" if case.endswith("_nonlinear") else case
        if underlying == "gene_expression":
            rng = np.random.default_rng(np.random.SeedSequence([seed, 4, 17923]))
            indices = rng.integers(len(self.real), size=count + unlab_count)
            sampled = self.real[indices]
            outcomes, predictions, unlab = sampled[:count, 0].copy(), sampled[:count, 1].copy(), sampled[count:, 1].copy()
            truth = float(self.real[:, 0].mean())
        else:
            if self.current_case != underlying:
                with np.load(self.root / (underlying + ".npz"), allow_pickle=False) as source:
                    self.current = source["raw"].copy()
                self.current_case = underlying
            raw = self.current[SEEDS.index(seed)]
            outcomes, predictions = raw[:count, 1].copy(), raw[:count, 0].copy()
            unlab = raw[128:128 + unlab_count, 0].copy()
            truth = {"linear": .5, "nonlinear": .1 + .8 / 3,
                     "uninformative": .5, "rare_outcome": .01 + .08 / 3}[underlying]
        if case == "constant_nonlinear":
            predictions.fill(.5)
            unlab.fill(.5)
        if case == "permuted_nonlinear":
            rng = np.random.default_rng(np.random.SeedSequence([seed, 991]))
            perm_labeled, perm_unlabeled = rng.permutation(count), rng.permutation(unlab_count)
            if (np.array_equal(perm_labeled, np.arange(count)) or np.array_equal(perm_unlabeled, np.arange(unlab_count))
                    or np.array_equal(predictions, predictions[perm_labeled])
                    or np.array_equal(unlab, unlab[perm_unlabeled])):
                raise ValueError("vacuous permutation")
            predictions, unlab = predictions[perm_labeled], unlab[perm_unlabeled]
        raw = np.concatenate([outcomes, predictions, unlab]).astype("<f8").tobytes()
        return raw, {"n": count, "N": unlab_count, "label_kind": kind}, truth


def upload(call, raw, settings):
    chunks = math.ceil(len(raw) / CHUNK_BYTES)
    if chunks > MAX_CHUNKS or not raw:
        raise ValueError("invalid logical input")
    response = call({"op": "update", "phase": "start", **settings, "alpha": .05,
                     "dtype": "<f8", "encoding": "base64", "shape": [2 * settings["n"] + settings["N"]],
                     "total_bytes": len(raw), "chunks": chunks})
    if (type(response) is not dict or set(response) != {"ok", "transfer_id"} or response["ok"] is not True
            or type(response["transfer_id"]) is not str
            or not re.fullmatch(r"[A-Za-z0-9_]{1,64}", response["transfer_id"])):
        raise ProtocolError("malformed_response")
    identifier = response["transfer_id"]
    for index in range(chunks):
        encoded = base64.b64encode(raw[index * CHUNK_BYTES:(index + 1) * CHUNK_BYTES]).decode("ascii")
        ack(call({"op": "update", "phase": "chunk", "transfer_id": identifier, "index": index, "data": encoded}))
    ack(call({"op": "update", "phase": "commit", "transfer_id": identifier}))


def worst_case(episode):
    return {"coverage": 0.0, "ratio": 100.0, "utility": 0.0, "failure": 1.0,
            "solution": None, "duration": 0.0, "correct": False}


def summarize(outcomes, episodes, seeds, complete):
    import numpy as np
    from scipy.stats import beta
    groups = [[outcomes[index] for index, episode in enumerate(episodes)
               if episode["case"] == case and not episode["replay"]] for case in CASES]
    case_means = [[sum(item[key] for item in group) / len(group)
                   for key in ("coverage", "ratio", "utility", "failure")] for group in groups]
    correct = bool(complete and all(item["correct"] for item in outcomes))
    values = {
        "combined_score": sum(row[2] - 10 * max(0, .95 - row[0]) for row in case_means) / 7 if correct else -9.5,
        "nominal_coverage": .95,
        "empirical_coverage": sum(row[0] for row in case_means) / 7,
        "minimum_case_coverage": min(row[0] for row in case_means),
        "mean_width_ratio": sum(row[1] for row in case_means) / 7,
        "width_utility": sum(row[2] for row in case_means) / 7,
        "failure_fraction": sum(row[3] for row in case_means) / 7,
        "control_pass": int(correct), "scientific_validity": 0, "correct": int(correct)}
    summary = {}
    rng = np.random.default_rng(79231)
    tail = .05 / (7 * 4 * 2)
    for case, group in zip(CASES, groups):
        observations = sum(item["coverage"] for item in group)
        count = len(group)
        coverage_interval = [0.0 if observations == 0 else float(beta.ppf(tail, observations, count - observations + 1)),
                             1.0 if observations == count else float(beta.ppf(1 - tail, observations + 1, count - observations))]
        method_intervals = {"candidate": coverage_interval}
        for name in ("label_only", "ppi", "ppi_plus_plus"):
            covered = sum(item["solution"]["baseline_coverage"][name] if item["solution"] is not None else 0 for item in group)
            method_intervals[name] = [0.0 if covered == 0 else float(beta.ppf(tail, covered, count - covered + 1)),
                                      1.0 if covered == count else float(beta.ppf(1 - tail, covered + 1, count - covered))]
        summary[case] = {"coverage_intervals": method_intervals,
                         "missing": sum(item["failure"] for item in group), "paired_widths": None,
                         "empirical_undercoverage_detected": bool(coverage_interval[1] < .95)}
        if all(item["solution"] is not None for item in group):
            widths = np.array([[item["solution"]["candidate"][1] - item["solution"]["candidate"][0]]
                               + [item["solution"][name][1] - item["solution"][name][0]
                                  for name in ("label_only", "ppi", "ppi_plus_plus")] for item in group])
            selection = rng.integers(count, size=(512, count))
            means = (widths[selection] / count).sum(axis=1)
            comparison = {}
            for index, name in enumerate(("label_only", "ppi", "ppi_plus_plus"), 1):
                differences = means[:, 0] - means[:, index]
                with np.errstate(over="ignore", divide="ignore", invalid="ignore"):
                    ratios = means[:, 0] / np.maximum(means[:, index], np.finfo(float).tiny)
                comparison[name] = {"mean_candidate_width": float((widths[:, 0] / count).sum()),
                                    "mean_baseline_width": float((widths[:, index] / count).sum()),
                                    "candidate_width_interval": np.quantile(means[:, 0], [tail, 1 - tail]).tolist(),
                                    "baseline_width_interval": np.quantile(means[:, index], [tail, 1 - tail]).tolist(),
                                    "ratio_interval": (np.quantile(means[:, 0] / means[:, index], [.05 / 42, 1 - .05 / 42]).tolist()
                                                       if np.all(means[:, index] > 0) and np.isfinite(ratios).all() else None),
                                    "difference_interval": np.quantile(differences, [.05 / 42, 1 - .05 / 42]).tolist()}
            summary[case]["paired_widths"] = comparison
    evidence = []
    for seed in seeds:
        selected = [(episode, item) for episode, item in zip(episodes, outcomes) if episode["seed"] == seed]
        primary = [item for episode, item in selected if not episode["replay"]]
        record = {"seed": seed, "score": float(sum(item["utility"] - 10 * max(0, .95 - case_means[index][0])
                                                   for index, item in enumerate(primary)) / 7),
                  "correct": bool(all(item["correct"] for unused, item in selected)),
                  "duration_seconds": sum(item["duration"] for unused, item in selected),
                  "solution": {"cases": {episode["case"]: {"observations": item["solution"],
                                                          "coverage": item["coverage"], "width_ratio": item["ratio"],
                                                          "utility": item["utility"], "failure": item["failure"],
                                                          "failure_metadata": item.get("failure_metadata"),
                                                          "correct": item["correct"], "duration_seconds": item["duration"]}
                                          for episode, item in selected if not episode["replay"]}}}
        if seed == seeds[0]:
            record["solution"]["summary"] = summary
            replay = outcomes[-1]
            record["solution"]["reset_replay_pass"] = bool(replay["correct"])
            record["solution"]["reset_replay"] = {
                "observations": replay["solution"], "coverage": replay["coverage"],
                "width_ratio": replay["ratio"], "utility": replay["utility"], "failure": replay["failure"],
                "correct": replay["correct"], "duration_seconds": replay["duration"],
                "failure_metadata": replay.get("failure_metadata")}
        evidence.append(record)
    if set(values) != set(METRICS) or not all(finite(value) for value in values.values()):
        raise ValueError("nonfinite aggregate")
    return values, {"schema_version": 1, "episodes": evidence}


def execute(program_path, smoke, started):
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "NUMBA_NUM_THREADS"):
        os.environ[name] = "1"
    import numpy as np
    hard_deadline = started + WALL_SECONDS - 60
    preflight_wire()
    require_joint_workload_budget(
        search={"episode_count": 701, "method_count": 2, "wall_seconds": 3600,
                "startup_seconds": 60, "finish_seconds": 15, "reset_seconds": 1.6,
                "cleanup_seconds": .7, "work_seconds": 1},
        final={"episode_count": 2801, "method_count": 2, "wall_seconds": 14400,
               "startup_seconds": 60, "finish_seconds": 15, "reset_seconds": 1.6,
               "cleanup_seconds": .7, "work_seconds": 1})
    root = Path(os.environ.get("TASK_SOURCE_DIR", str(Path(__file__).resolve().parent))) / "resources" / PLANE
    data = Data(root)
    seeds = SEEDS[:1] if smoke else SEEDS
    reset_seeds = SEEDS[:64]
    episodes = [{"case": case, "seed": seed, "reset_seed": reset_seeds[index % len(reset_seeds)],
                 "replay": False} for case in CASES for index, seed in enumerate(seeds)]
    episodes.append({"case": CASES[0], "seed": seeds[0], "reset_seed": reset_seeds[0], "replay": True})
    broker = CandidateRPC(program_path)
    baseline = Baseline()
    expected_controls = {(episode["case"], episode["seed"], "copy") for episode in episodes}
    expected_controls |= {("constant_nonlinear", seed, "constant") for seed in seeds}
    expected_controls |= {("permuted_nonlinear", seed, "permutation") for seed in seeds}
    expected_controls.add((CASES[0], seeds[0], "reset"))
    reference = None
    completed_controls = set()
    durations = [0.0] * len(episodes)
    operation = "reset"
    active_episode = -1
    baseline_productive = 0.0
    def evaluate(episode, call, deadline):
        nonlocal reference, operation, active_episode, baseline_productive
        active_episode += 1
        before = time.monotonic()
        failed = True
        primary = None
        try:
            raw, settings, truth = data.episode(episode["case"], episode["seed"], smoke)
            candidate_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                         methods_remaining=1, work_seconds=1, cleanup_seconds=.7)
            def guarded(request):
                nonlocal operation
                operation = request["op"]
                baseline.check()
                if time.monotonic() >= candidate_deadline:
                    raise TimeoutError()
                response = call(request, candidate_deadline)
                baseline.check()
                return response
            upload(guarded, raw, settings)
            candidate = interval(guarded({"op": "infer"}), settings["label_kind"] == "bernoulli")
            duplicate = interval(guarded({"op": "infer"}), settings["label_kind"] == "bernoulli")
            if not np.allclose(candidate, duplicate, rtol=0, atol=1e-12):
                raise ProtocolError("copy_control_failure")
            completed_controls.add((episode["case"], episode["seed"], "copy"))
            baseline_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                        methods_remaining=0, work_seconds=1, cleanup_seconds=.7)
            results = baseline.compute({**settings, "data": base64.b64encode(raw).decode("ascii")}, baseline_deadline)
            baseline_productive += results["productive_seconds"]
            limits = {name: interval(results[name], False) for name in ("label_only", "ppi", "ppi_plus_plus")}
            if episode["case"] == "constant_nonlinear":
                if not np.allclose(candidate, limits["label_only"], rtol=0, atol=1e-10):
                    raise ProtocolError("constant_control_failure")
                completed_controls.add((episode["case"], episode["seed"], "constant"))
            if episode["case"] == "permuted_nonlinear":
                completed_controls.add((episode["case"], episode["seed"], "permutation"))
            if episode["replay"]:
                if reference is None or not np.allclose(candidate, reference, rtol=0, atol=1e-10):
                    raise ProtocolError("reset_control_failure")
                completed_controls.add((episode["case"], episode["seed"], "reset"))
            elif episode["case"] == CASES[0] and episode["seed"] == seeds[0]:
                reference = candidate
            width = candidate[1] - candidate[0]
            denominator = limits["ppi_plus_plus"][1] - limits["ppi_plus_plus"][0]
            ratio = min(100.0, width / denominator) if denominator > 0 else (1.0 if width == 0 else 100.0)
            covered = float(candidate[0] <= truth <= candidate[1])
            solution = {"candidate": candidate, **limits, "target": truth,
                        "baseline_coverage": {name: float(bounds[0] <= truth <= bounds[1]) for name, bounds in limits.items()}}
            failed = False
            return {"coverage": covered, "ratio": ratio, "utility": 1 / (1 + ratio), "failure": 0.0,
                    "solution": solution, "duration": time.monotonic() - before, "correct": True}
        except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
            primary = error
            if isinstance(error, RequiredBaselineFailure):
                error.baseline_status = baseline.cause_status
                try:
                    baseline.cancel()
                except (OSError, RuntimeError, subprocess.TimeoutExpired):
                    error.add_note("baseline cleanup failed")
            raise
        except Exception as error:
            primary = error
            raise
        finally:
            try:
                broker.cleanup(failed)
            except (OSError, RuntimeError, subprocess.TimeoutExpired) as cleanup_error:
                if primary is None:
                    raise ProtocolError("cleanup_failure") from cleanup_error
                primary.cleanup_failed = True
            durations[active_episode] = time.monotonic() - before
    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=15, reset_timeout=1.6,
            episode_overhead=1.4, rpc_cap=1, clock=time.monotonic, rpc=broker,
            evaluate=evaluate, worst_case=worst_case, record_failure=record_failure)
        complete = complete and not (expected_controls - completed_controls)
        metrics, evidence = summarize(outcomes, episodes, seeds, complete)
        evidence["episodes"][0]["solution"]["productive_baseline_seconds"] = baseline_productive
        return metrics, evidence, bool(complete and not smoke and time.monotonic() < hard_deadline - 15)
    finally:
        broker.cleanup(True)
        baseline.worker.close(bool(baseline.broken))


def evaluation_evidence_line(evidence):
    required = {"seed", "score", "correct", "duration_seconds"}
    optional = {"solution", "candidate_diagnostics", "candidate_timeseries"}
    name_pattern = r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}"
    if (type(evidence) is not dict or set(evidence) != {"schema_version", "episodes"}
            or type(evidence["schema_version"]) is not int or evidence["schema_version"] != 1
            or type(evidence["episodes"]) is not list or not 1 <= len(evidence["episodes"]) <= 10000):
        raise ValueError("invalid evidence envelope")
    seeds = set()
    timeseries_rows = 0
    for record in evidence["episodes"]:
        if type(record) is not dict or not required <= set(record) <= required | optional:
            raise ValueError("invalid evidence record fields")
        seed = record["seed"]
        if type(seed) is not int or not -(2**63) <= seed < 2**63 or seed in seeds:
            raise ValueError("invalid or duplicate evidence seed")
        seeds.add(seed)
        if (not finite(record["score"]) or type(record["correct"]) is not bool
                or not finite(record["duration_seconds"]) or record["duration_seconds"] < 0):
            raise ValueError("invalid evidence measurements")
        if "candidate_diagnostics" in record:
            diagnostics = record["candidate_diagnostics"]
            if (type(diagnostics) is not dict
                    or any(type(name) is not str or re.fullmatch(name_pattern, name) is None
                           or not finite(value) for name, value in diagnostics.items())):
                raise ValueError("invalid candidate diagnostics")
        if "candidate_timeseries" in record:
            rows = record["candidate_timeseries"]
            if type(rows) is not list:
                raise ValueError("invalid candidate timeseries")
            timeseries_rows += len(rows)
            if timeseries_rows > 100000:
                raise ValueError("too many candidate timeseries rows")
            for row in rows:
                if (type(row) is not dict or set(row) != {"series_name", "step", "value"}
                        or type(row["series_name"]) is not str
                        or re.fullmatch(name_pattern, row["series_name"]) is None
                        or type(row["step"]) is not int or row["step"] < 0 or not finite(row["value"])):
                    raise ValueError("invalid candidate timeseries row")
    def check_json(value, depth):
        if depth > 12:
            raise ValueError("evidence nesting too deep")
        if type(value) is dict:
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError("invalid evidence JSON key")
                check_json(item, depth + 1)
        elif type(value) is list:
            for item in value:
                check_json(item, depth + 1)
        elif value is not None and type(value) not in (str, bool):
            if not finite(value):
                raise ValueError("invalid evidence JSON value")
    check_json(evidence, 1)
    encoded = json.dumps(evidence, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) > 16 * 1024**2:
        raise ValueError("evidence exceeds size limit")
    strict_json(encoded)
    return encoded


def write_evaluation_evidence(path, evidence):
    encoded = evaluation_evidence_line(evidence)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError("evidence output must be a regular file")
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.truncate(0)
            stream.write(encoded)
    finally:
        os.close(descriptor)


def write_outputs(directory, metrics, evidence, feasible):
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (("metrics.json", metrics), ("correct.json", {"correct": bool(metrics["correct"])})):
        (directory / name).write_bytes(bounded_json_line(value))
    evidence_path = directory / "evaluation_evidence.json"
    if evidence is not None:
        write_evaluation_evidence(evidence_path, evidence)
    else:
        evidence_path.unlink(missing_ok=True)
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        (directory / "qualification.json").write_bytes(bounded_json_line({"schema_version": 1, "feasible": feasible}))


def main():
    started = time.monotonic()
    if "--baseline-worker" in sys.argv:
        return baseline_worker()
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    directory = Path(args.results_dir)
    try:
        metrics, evidence, feasible = execute(args.program_path, smoke, started)
        write_outputs(directory, metrics, evidence, feasible)
        return 0
    except Exception as error:
        metrics = dict.fromkeys(METRICS, 0.0)
        metrics.update(combined_score=-9.5, nominal_coverage=.95, mean_width_ratio=100.0, failure_fraction=1.0)
        write_outputs(directory, metrics, None, False)
        if PLANE == "search":
            name = bounded_failure_name(type(error).__name__.lower(), "evaluation_error")
            print("evaluation_exception type=%s message=evaluation_failed" % name, file=sys.stderr)
        else:
            print("evaluation_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
