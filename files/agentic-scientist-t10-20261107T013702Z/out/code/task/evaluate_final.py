"""Self-contained frozen-predictor mean-inference evaluator.

Only this plane's frozen resources are loaded. Scientific checks are independent
of candidate flags. The native subprocess is a Linux Landlock/seccomp sandbox;
production uses only the authenticated, exact-path harness proxy in-process.
"""
import time

STARTED = time.monotonic()
import argparse
import base64
import collections
import contextlib
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
import subprocess
import sys
import tempfile
import threading
import traceback

for thread_variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[thread_variable] = "2"
import numpy as np
from scipy.stats import beta, binom, norm, t as student_t

PLANE = "final"
WALL_SECONDS = 3600
STARTUP_RESERVE = 120
FINISH_RESERVE = 120
RESET_TIMEOUT = 0.75
WORK_SECONDS = 1.0
BASELINE_SECONDS = 0.05
EPISODE_OVERHEAD = 0.50
BROKER_EPISODE_OVERHEAD = 0.05
NATIVE_READER_RESERVE = 1.0
FIRST_RESET_STARTUP_SECONDS = 5.0
RPC_CAP = 1.0
MAX_CHUNKS = 4
WIRE_LIMIT = 64 * 1024**2
DESIGN_LIMIT = 8 * 1024**2
RESPONSE_LIMIT = 16 * 1024
CHUNK_BYTES = 1024**2
LOGICAL_LIMIT = 4 * 1024**2
RATIO_CAP = 1000000.0
DENOMINATOR_FLOOR = 1e-12
METRIC_NAMES = ("combined_score", "correct", "coverage", "mean_width", "width_ratio_ppiplus", "control_pass_rate")
BASELINE_NAMES = ("labeled_only_exact_binomial", "labeled_only_asymptotic_mean", "prediction_powered_mean", "ppi_plus_plus_mean", "full_range_sanity_interval")


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
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


class ProtocolFailure(RuntimeError):
    def __init__(self, category, operation):
        self.category = bounded_failure_name(category, "invalid_response")
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("candidate protocol failure")


class FatalTransportFailure(ProtocolFailure):
    pass


def describe_episode_failure(error, operation):
    context = error
    for unused in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, ProtocolFailure):
            return {"component": "candidate", "category": context.category, "operation": context.operation}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout", "operation": bounded_failure_name(operation, "unknown")}


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


def report_runtime_exception(error):
    if PLANE != "search" or not (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1" or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"):
        return
    report_worker_exception(error)
    for frame in traceback.extract_tb(error.__traceback__)[-8:]:
        filename = Path(frame.filename).name
        if re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", filename) and re.fullmatch(r"[A-Za-z0-9_<>]{1,80}", frame.name):
            print(f"failure_frame file={filename} function={frame.name} line={frame.lineno}", file=sys.stderr, flush=True)


def finite_budget_seconds(value):
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
            "wall_seconds", "startup_seconds", "reset_seconds", "cleanup_seconds", "finish_seconds")}
        work = positive_work_seconds(profile["work_seconds"])
        needed = times["startup_seconds"] + times["finish_seconds"] + episodes * (times["reset_seconds"] + methods * (work + times["cleanup_seconds"]))
        if needed > times["wall_seconds"]:
            raise ValueError("productive work exceeds declared wall budget")
        required[plane] = needed
    return required


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid remaining method count")
    if now + (methods_remaining + 1) * (work + cleanup_seconds) > episode_deadline:
        raise TimeoutError("insufficient matched method reservations")
    return now + work


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def bounded_json_line(value, limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= limit:
        raise ProtocolFailure("oversized_message", "unknown")
    return encoded


def finite_json(value, depth=0):
    if depth > 12:
        return False
    if value is None or type(value) in (bool, str, int):
        return True
    if type(value) is float:
        return math.isfinite(value)
    if type(value) is list:
        return all(finite_json(item, depth + 1) for item in value)
    if type(value) is dict:
        return all(type(key) is str and finite_json(item, depth + 1) for key, item in value.items())
    return False


def unique_object(pairs):
    output = {}
    for key, value in pairs:
        if key in output:
            raise ValueError("duplicate JSON key")
        output[key] = value
    return output


def loads_wire(raw):
    try:
        value = json.loads(raw, object_pairs_hook=unique_object)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ProtocolFailure("malformed_json", "unknown") from error
    if not finite_json(value):
        raise ProtocolFailure("nonfinite_response", "unknown")
    return value


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES",
        "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES", "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION", "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


NATIVE_RUNNER = r'''
import base64, ctypes, importlib.util, json, math, os, pathlib, resource, sys

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

def restrict_filesystem(program, workdir):
    library = ctypes.CDLL(None, use_errno=True)
    library.syscall.restype = ctypes.c_long
    abi = library.syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError("Landlock ABI >=3 required")
    class Ruleset(ctypes.Structure):
        _fields_ = [("handled_access_fs", ctypes.c_uint64)]
    class Rule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]
    handled = (1 << 15) - 1
    rules = Ruleset(handled)
    descriptor = library.syscall(444, ctypes.byref(rules), ctypes.sizeof(rules), 0)
    if descriptor < 0:
        raise RuntimeError("Landlock create failed")
    allowed = [(path, 1 | 4 | 8) for path in ("/usr", "/lib", "/lib64", sys.prefix, sys.base_prefix)]
    allowed += [(program, 4)]
    allowed += [(workdir, 4 | 8), ("/dev/null", 2 | 4), ("/dev/urandom", 4), ("/dev/random", 4)]
    for path, access in allowed:
        if not os.path.exists(path):
            continue
        path_fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        try:
            rule = Rule(access, path_fd)
            if library.syscall(445, descriptor, 1, ctypes.byref(rule), 0) != 0:
                raise RuntimeError("Landlock rule failed")
        finally:
            os.close(path_fd)
    if library.prctl(38, 1, 0, 0, 0) != 0 or library.syscall(446, descriptor, 0) != 0:
        raise RuntimeError("Landlock restrict failed")
    os.close(descriptor)

def restrict_syscalls():
    library = ctypes.CDLL("libseccomp.so.2", use_errno=True)
    library.seccomp_init.argtypes = [ctypes.c_uint32]
    library.seccomp_init.restype = ctypes.c_void_p
    library.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    library.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    library.seccomp_load.argtypes = [ctypes.c_void_p]
    library.seccomp_release.argtypes = [ctypes.c_void_p]
    context = library.seccomp_init(0x7fff0000)
    if not context:
        raise RuntimeError("seccomp initialization failed")
    forbidden = ("socket", "socketpair", "connect", "bind", "listen", "accept", "accept4", "sendto", "sendmsg", "recvfrom", "recvmsg", "ptrace", "process_vm_readv", "process_vm_writev", "pidfd_open", "pidfd_getfd", "fork", "vfork", "execve", "execveat", "mount", "umount2", "unshare", "setns", "bpf", "userfaultfd", "io_uring_setup", "open_by_handle_at", "name_to_handle_at", "kill", "tkill", "tgkill")
    for name in forbidden:
        number = library.seccomp_syscall_resolve_name(name.encode())
        if number >= 0 and library.seccomp_rule_add(context, 0x50000 | 1, number, 0) != 0:
            raise RuntimeError("seccomp rule failed")
    number = library.seccomp_syscall_resolve_name(b"clone3")
    if number >= 0 and library.seccomp_rule_add(context, 0x50000 | 38, number, 0) != 0:
        raise RuntimeError("seccomp clone3 rule failed")
    class Compare(ctypes.Structure):
        _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_uint), ("datum_a", ctypes.c_uint64), ("datum_b", ctypes.c_uint64)]
    library.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint, ctypes.POINTER(Compare)]
    compare = Compare(0, 7, 0x10000, 0)
    number = library.seccomp_syscall_resolve_name(b"clone")
    if library.seccomp_rule_add_array(context, 0x50000 | 1, number, 1, ctypes.byref(compare)) != 0 or library.seccomp_load(context) != 0:
        raise RuntimeError("seccomp load failed")
    library.seccomp_release(context)

try:
    program, workdir = sys.argv[1:3]
    affinity = sorted(os.sched_getaffinity(0))[:2]
    os.sched_setaffinity(0, affinity)
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_LIMIT, CPU_LIMIT))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.chdir(workdir)
    sys.dont_write_bytecode = True
    restrict_syscalls()
    restrict_filesystem(program, workdir)
    sys.path.insert(0, str(pathlib.Path(program).parent))
    spec = importlib.util.spec_from_file_location("candidate", program)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for line in sys.stdin.buffer:
        if len(line) >= 8 * 1024**2:
            raise ValueError("oversized request")
        request = json.loads(line)
        response = module.handle(request)
        encoded = json.dumps(response, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(encoded) >= 16 * 1024:
            raise ValueError("oversized response")
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
except BaseException as error:
    if REPAIR:
        report_worker_exception(error)
    else:
        print("worker_failure", file=sys.stderr, flush=True)
    sys.exit(1)
'''


class CandidateClient:
    def __init__(self, program, max_calls):
        self.program = str(program)
        socket_present = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
        proxy_path = self.program == "/broker-code/candidate_proxy.py"
        proxy_path = socket_present and proxy_path
        if not proxy_path:
            self.program = str(Path(program).absolute())
        self.proxy = None
        self.process = None
        self.capture = None
        self.directory = None
        self.calls = 0
        self.max_calls = max_calls
        self.resets = []
        self.last_capture = None
        self.last_exit = None
        self.repair = PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1" or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")
        if proxy_path:
            spec = importlib.util.spec_from_file_location("trusted_candidate_proxy", self.program)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle

    def launch(self):
        interpreter, environment = candidate_subprocess_settings(os.environ)
        self.directory = tempfile.TemporaryDirectory(prefix="candidate-native-")
        boot = "REPAIR=" + repr(self.repair) + "\nCPU_LIMIT=" + str(cpu_limit_seconds(RESET_TIMEOUT + WORK_SECONDS + BASELINE_SECONDS + EPISODE_OVERHEAD, 2)) + "\n" + NATIVE_RUNNER
        self.process = subprocess.Popen([interpreter, "-I", "-u", "-c", boot, self.program, self.directory.name],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        env=environment, cwd=self.directory.name, start_new_session=True, shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def finish_episode(self, failed=False):
        if self.process is None:
            return
        process, capture, directory = self.process, self.capture, self.directory
        self.process = self.capture = self.directory = None
        natural_exit = process.poll()
        try:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=.10)
            except subprocess.TimeoutExpired as error:
                raise RuntimeError("candidate cleanup unresolved") from error
            self.last_exit = natural_exit
        finally:
            process.stdin.close()
            process.stdout.close()
            snapshot = capture.close()
            self.last_capture = {key: value for key, value in snapshot.items() if key != "stderr"}
            if failed and self.repair and snapshot["stderr"]:
                sys.stderr.write(snapshot["stderr"])
                sys.stderr.flush()
            directory.cleanup()

    def rpc(self, request, *, timeout):
        self.calls += 1
        if self.calls > self.max_calls:
            raise ProtocolFailure("rpc_budget", request["op"])
        if request["op"] == "reset":
            self.resets.append(request["seed"])
        encoded = bounded_json_line(request, DESIGN_LIMIT)
        deadline = time.monotonic() + timeout
        try:
            if self.proxy is not None:
                try:
                    with alarm_deadline(deadline):
                        response = self.proxy(request)
                except TimeoutError as error:
                    report_runtime_exception(error)
                    raise
                except (RuntimeError, ValueError, TypeError) as error:
                    report_runtime_exception(error)
                    raise FatalTransportFailure("transport_failure", request["op"]) from error
                if not finite_json(response):
                    raise ProtocolFailure("nonfinite_response", request["op"])
                try:
                    bounded_json_line(response, RESPONSE_LIMIT)
                except (ValueError, TypeError, OverflowError) as error:
                    raise ProtocolFailure("invalid_response_schema", request["op"]) from error
                return response
            if request["op"] == "reset":
                if self.process is not None:
                    raise RuntimeError("native episode cleanup missing")
                self.launch()
            if self.process is None:
                raise ProtocolFailure("candidate_unavailable", request["op"])
            process = self.process
            sent = 0
            response = bytearray()
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdin, selectors.EVENT_WRITE)
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError("RPC deadline exceeded")
                    events = selector.select(remaining)
                    if not events:
                        raise TimeoutError("RPC deadline exceeded")
                    for key, mask in events:
                        if key.fileobj is process.stdin:
                            try:
                                sent += os.write(process.stdin.fileno(), encoded[sent:sent + 65536])
                            except BrokenPipeError as error:
                                raise ProtocolFailure("candidate_exit", request["op"]) from error
                            if sent == len(encoded):
                                selector.unregister(process.stdin)
                        else:
                            chunk = os.read(process.stdout.fileno(), 4096)
                            if not chunk:
                                status = process.poll()
                                category = "candidate_signal" if status is not None and status < 0 else "candidate_exit"
                                raise ProtocolFailure(category, request["op"])
                            response.extend(chunk)
                            if len(response) >= RESPONSE_LIMIT:
                                raise ProtocolFailure("oversized_response", request["op"])
                            if b"\n" in response:
                                if not response.endswith(b"\n") or response.count(b"\n") != 1 or sent != len(encoded):
                                    raise ProtocolFailure("malformed_framing", request["op"])
                                return loads_wire(response)
        except ProtocolFailure as error:
            error.operation = request["op"]
            raise
        except TimeoutError:
            raise
        except (OSError, ConnectionError) as error:
            raise FatalTransportFailure("transport_failure", request["op"]) from error


@contextlib.contextmanager
def alarm_deadline(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("work deadline exceeded")
    def expired(signum, frame):
        raise TimeoutError("work deadline exceeded")
    previous = signal.signal(signal.SIGALRM, expired)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, remaining)
    began = time.monotonic()
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, max(1e-6, previous_timer[0] - (time.monotonic() - began)) if previous_timer[0] else 0, previous_timer[1])
        signal.signal(signal.SIGALRM, previous)


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure, cleanup,
                          first_reset_startup=0.0, work_seconds=WORK_SECONDS + BASELINE_SECONDS):
    positive_work_seconds(reset_timeout)
    positive_work_seconds(rpc_cap)
    positive_work_seconds(work_seconds)
    finite_budget_seconds(episode_overhead)
    finite_budget_seconds(first_reset_startup)
    candidate_deadline = hard_deadline - finish_reserve
    episode_slot = reset_timeout + work_seconds + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + first_reset_startup + len(episodes) * episode_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared matched episode reservations")
    complete = True
    durations = []
    fatal_error = None
    for index, episode in enumerate(episodes):
        began = clock()
        remaining = len(episodes) - index - 1
        startup = first_reset_startup if index == 0 else 0.0
        episode_deadline = min(began + episode_slot + startup,
                               candidate_deadline - remaining * episode_slot)
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
                response = rpc(request, timeout=timeout)
                if clock() > work_deadline:
                    raise TimeoutError("episode work deadline exceeded")
                return response
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            reset_deadline = min(began + reset_timeout + startup, work_deadline)
            timeout = min(reset_timeout, rpc_cap) + startup
            timeout = min(timeout, reset_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode.get("reset_seed", episode["seed"])}, timeout=timeout))
            if clock() > reset_deadline:
                raise TimeoutError("episode reset deadline exceeded")
            if fatal_error is not None:
                continue
            work_deadline = min(clock() + work_seconds, work_deadline)
            value = evaluate(episode, call, work_deadline)
            if clock() > work_deadline:
                raise TimeoutError("episode work deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            complete = False
            primary_failure = primary_failure or describe_episode_failure(error, current_operation)
            outcomes[index] = worst_case(episode)
            if isinstance(error, FatalTransportFailure) and fatal_error is None:
                fatal_error = error
        finally:
            try:
                cleanup(primary_failure is not None)
            except RuntimeError:
                complete = False
                outcomes[index] = worst_case(episode)
                secondary = {"component": "candidate", "category": "cleanup_failure", "operation": "cleanup"}
                if primary_failure is not None:
                    record_failure(secondary)
                else:
                    primary_failure = secondary
            if clock() > episode_deadline:
                complete = False
                outcomes[index] = worst_case(episode)
                secondary = {"component": "candidate", "category": "cleanup_timeout", "operation": "cleanup"}
                if primary_failure is not None:
                    record_failure(secondary)
                else:
                    primary_failure = secondary
            if primary_failure is not None:
                record_failure(primary_failure)
            durations.append(max(0.0, clock() - began))
    if fatal_error is not None:
        fatal_error.outcomes = outcomes
        fatal_error.durations = durations
        raise fatal_error
    return outcomes, complete, durations


def record_failure(failure):
    if PLANE == "search":
        component = bounded_failure_name(failure.get("component"), "unknown")
        category = bounded_failure_name(failure.get("category"), "unknown")
        operation = bounded_failure_name(failure.get("operation"), "unknown")
        metadata = ""
        if type(failure.get("observed_bytes")) is int:
            metadata += f" stderr_bytes={min(failure['observed_bytes'], 10**12)} truncated={int(bool(failure.get('truncated')))}"
        if type(failure.get("exit_status")) is int:
            metadata += f" exit_status={failure['exit_status']}"
        print((f"episode_failure component={component} category={category} operation={operation}" + metadata)[:256], file=sys.stderr, flush=True)


def normalize_raw(values):
    normalized = np.array(values, dtype="<f8", copy=True)
    if not np.isfinite(normalized).all():
        raise ValueError("nonfinite raw example")
    normalized[normalized == 0] = 0.0
    return normalized


def row_hashes(values):
    normalized = normalize_raw(values)
    return np.frombuffer(b"".join(hashlib.sha256(b"z:float64:v1\0" + row.tobytes()).digest() for row in normalized.reshape(-1, 1)), dtype=np.uint8).reshape(-1, 32).copy()


def generate_raw(source_seed, labeled_size, unlabeled_size, coefficients, case):
    generator = np.random.default_rng(source_seed)
    raw = normalize_raw(generator.random(labeled_size + unlabeled_size))
    if case in (0, 1):
        probabilities = coefficients["quadratic"][0] + coefficients["quadratic"][1] * raw[:labeled_size]**2
    elif case == 2:
        probabilities = coefficients["linear"][0] + coefficients["linear"][1] * raw[:labeled_size]
    elif case == 3:
        probabilities = np.full(labeled_size, coefficients["independent"])
    else:
        low, high, threshold = coefficients["rare"]
        probabilities = low + high * (raw[:labeled_size] > threshold)
    labels = (generator.random(labeled_size) < probabilities).astype("<f8")
    return raw, labels


def analytic_truth(coefficients, case):
    if case in (0, 1, 5, 6):
        return coefficients["quadratic"][0] + coefficients["quadratic"][1] / 3
    if case == 2:
        return coefficients["linear"][0] + coefficients["linear"][1] / 2
    if case == 3:
        return coefficients["independent"]
    low, high, threshold = coefficients["rare"]
    return low + high * (1 - threshold)


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        while chunk := stream.read(1024**2):
            digest.update(chunk)
    return digest.hexdigest()


def prepare_input(root, manifest, episode):
    mode = "smoke" if episode["smoke"] else "production"
    source_case = 0 if episode["case"] >= 5 else episode["case"]
    key = f"{mode}_{episode['seed']}_{source_case}"
    entry = manifest["rows"][key]
    with np.load(root / "examples.npz", allow_pickle=False) as archive:
        raw = normalize_raw(archive[key + "_z"])
        labels = archive[key + "_y"].copy()
    labeled_size, unlabeled_size = entry["n"], entry["N"]
    if len(raw) != labeled_size + unlabeled_size or labels.shape != (labeled_size,) or not np.isin(labels, [0, 1]).all():
        raise ValueError("invalid frozen raw schema")
    if hashlib.sha256(raw.tobytes()).hexdigest() != entry["raw_sha256"] or hashlib.sha256(labels.tobytes()).hexdigest() != entry["label_sha256"]:
        raise ValueError("frozen row integrity failed")
    predictions, unlabeled = raw[:labeled_size].copy(), raw[labeled_size:].copy()
    nonvacuous = True
    if episode["case"] == 5:
        predictions.fill(0.5)
        unlabeled.fill(0.5)
    elif episode["case"] == 6:
        original_labeled, original_unlabeled = predictions.copy(), unlabeled.copy()
        predictions = np.roll(predictions, entry["labeled_shift"])
        unlabeled = np.roll(unlabeled, entry["unlabeled_shift"])
        nonvacuous = not np.array_equal(predictions, original_labeled) and not np.array_equal(unlabeled, original_unlabeled)
        if not nonvacuous:
            raise ValueError("vacuous permutation control")
    truth = analytic_truth(manifest["coefficients"], episode["case"])
    return labels, predictions, unlabeled, truth, nonvacuous


def interval(estimate, variance, alpha=.05):
    radius = float(norm.ppf(1 - alpha / 2)) * math.sqrt(max(0.0, variance))
    return {"estimate": float(np.clip(estimate, 0, 1)), "lower": float(np.clip(estimate - radius, 0, 1)), "upper": float(np.clip(estimate + radius, 0, 1))}


def compute_baselines(labels, predictions, unlabeled):
    labeled_size, unlabeled_size = len(labels), len(unlabeled)
    count = int(labels.sum())
    mean = float(labels.mean())
    exact = {"estimate": mean,
             "lower": 0.0 if count == 0 else float(beta.ppf(.025, count, labeled_size - count + 1)),
             "upper": 1.0 if count == labeled_size else float(beta.ppf(.975, count + 1, labeled_size - count))}
    classical = interval(mean, float(labels.var()) / labeled_size)
    centered_labels = labels - labels.mean()
    centered_predictions = predictions - predictions.mean()
    covariance = float(np.mean(centered_labels * centered_predictions))
    pooled_variance = float(np.var(np.concatenate([predictions, unlabeled]), ddof=1))
    denominator = (1 + labeled_size / unlabeled_size) * pooled_variance
    power = float(np.clip(covariance / denominator, 0, 1)) if denominator > 1e-30 else 0.0
    def powered(coefficient):
        residuals = labels - coefficient * predictions
        estimate = float(residuals.mean() + coefficient * unlabeled.mean())
        variance = float(residuals.var()) / labeled_size + coefficient**2 * float(unlabeled.var()) / unlabeled_size
        return interval(estimate, variance)
    results = [exact, classical, powered(1.0), powered(power), {"estimate": mean, "lower": 0.0, "upper": 1.0}]
    for result in results:
        try:
            validate_interval(result)
        except ProtocolFailure as error:
            raise RequiredBaselineFailure("baseline_result_failure") from error
    return dict(zip(BASELINE_NAMES, results))


def validate_interval(response):
    if type(response) is not dict or set(response) != {"estimate", "lower", "upper"}:
        raise ProtocolFailure("invalid_response_schema", "infer")
    if any(type(response[key]) not in (int, float) or (type(response[key]) is float and not math.isfinite(response[key])) for key in response):
        raise ProtocolFailure("nonfinite_response", "infer")
    if not 0 <= response["estimate"] <= 1 or not 0 <= response["lower"] <= response["upper"] <= 1:
        raise ProtocolFailure("invalid_interval", "infer")


def baseline_self_check():
    labels = np.array([0., 1., 0., 1., 1., 0., 1., 0.])
    constant = np.full(8, .5)
    result = compute_baselines(labels, constant, constant)
    if abs(result["ppi_plus_plus_mean"]["estimate"] - labels.mean()) > 1e-14 or result["full_range_sanity_interval"]["upper"] != 1:
        raise RequiredBaselineFailure("baseline_result_failure")
    varied = np.linspace(.05, .95, 8)
    result = compute_baselines((varied < .5).astype(float), varied, np.linspace(0., 1., 24))
    if result["prediction_powered_mean"] == result["ppi_plus_plus_mean"]:
        raise RequiredBaselineFailure("baseline_result_failure")
    for count in (0, 8):
        compute_baselines(np.full(8, count / 8), constant, constant)


def input_requests(labels, predictions, unlabeled, chunk_size=CHUNK_BYTES):
    raw = np.concatenate([labels, predictions, unlabeled]).astype("<f8").tobytes()
    if not 0 < len(raw) <= LOGICAL_LIMIT:
        raise ValueError("invalid logical payload")
    count = math.ceil(len(raw) / chunk_size)
    if not 1 <= count <= MAX_CHUNKS:
        raise ValueError("invalid chunk count")
    for index in range(count):
        offset = index * chunk_size
        yield {"op": "input", "n": len(labels), "N": len(unlabeled), "alpha": .05, "dtype": "<f8",
               "encoding": "base64", "shape": [2 * len(labels) + len(unlabeled)], "total_bytes": len(raw),
               "chunk_count": count, "chunk_index": index, "offset": offset,
               "data": base64.b64encode(raw[offset:offset + chunk_size]).decode("ascii")}


def payload_preflight():
    largest = list(input_requests(np.zeros(512), np.ones(512), np.full(32768, .5)))
    maximum = list(input_requests(np.zeros(2), np.zeros(2), np.zeros(LOGICAL_LIMIT // 8 - 4)))
    variants = [{"op": "reset", "seed": 9223372036854775807}, {"op": "infer"}, {"ok": True},
                {"ok": True, "received_bytes": LOGICAL_LIMIT},
                {"estimate": .12345678901234567, "lower": 1e-300, "upper": .9999999999999999}]
    sizes = []
    for value in largest + maximum + variants:
        native_size = len(bounded_json_line(value, DESIGN_LIMIT))
        envelope = {"id": 9223372036854775807, "method": "handle", "params": value}
        envelope_size = len(bounded_json_line(envelope, DESIGN_LIMIT)) + 8 + 65536
        if envelope_size >= DESIGN_LIMIT or envelope_size >= WIRE_LIMIT:
            raise ValueError("complete wire preflight failed")
        sizes.append((native_size, envelope_size))
    for value in variants[2:]:
        if len(bounded_json_line({"result": value, "id": 9223372036854775807})) + 8 >= RESPONSE_LIMIT:
            raise ValueError("response preflight failed")
    return {"raw_production_bytes": 270336, "base64_production_bytes": len(largest[0]["data"]),
            "native_production_bytes": sizes[0][0], "conservative_production_bytes": sizes[0][1],
            "max_native_bytes": max(size[0] for size in sizes), "max_reserved_envelope_bytes": max(size[1] for size in sizes),
            "max_chunks": len(maximum), "framing_reserve_bytes": 65536 + 8}


def episode_plan(seeds, smoke):
    primary = [{"seed": seed, "case": case, "smoke": smoke, "replay": False} for seed in seeds for case in range(7)]
    episodes = primary + [{"seed": seeds[0], "case": 0, "smoke": smoke, "replay": True}]
    for episode in episodes:
        episode["reset_seed"] = 1001 + (episode["seed"] - 1001) % 64
    return episodes


def rpc_operation_counts(episodes):
    return {"reset": len(episodes), "input_with_setup": MAX_CHUNKS * len(episodes), "infer_with_commit": len(episodes)}


def workload_preflight():
    profiles = {}
    for name, count, wall, startup, finish in (("search", 225, 600, 60, 30), ("final", 1793, 3600, 120, 120)):
        profiles[name] = {"episode_count": count, "method_count": 1, "wall_seconds": wall,
                          "startup_seconds": startup + FIRST_RESET_STARTUP_SECONDS, "reset_seconds": RESET_TIMEOUT,
                          "cleanup_seconds": BROKER_EPISODE_OVERHEAD, "finish_seconds": finish,
                          "work_seconds": WORK_SECONDS + BASELINE_SECONDS}
    return require_joint_workload_budget(**profiles)


def coverage_summary(indicators):
    count, total = int(sum(indicators)), len(indicators)
    lower = 0.0 if count == 0 else float(beta.ppf(.025, count, total - count + 1))
    upper = 1.0 if count == total else float(beta.ppf(.975, count + 1, total - count))
    rejected = float(binom.cdf(count, total, .95)) < .01 / 7
    return {"coverage": count / total, "lower95": lower, "upper95": upper, "nominal_not_rejected": not rejected}


def paired_summary(differences):
    average = float(np.mean(differences))
    if len(differences) > 1:
        radius = float(student_t.ppf(.975, len(differences) - 1)) * float(np.std(differences, ddof=1)) / math.sqrt(len(differences))
    else:
        radius = 1.0
    return {"mean_difference": average, "lower95": average - radius, "upper95": average + radius}


def aggregate(episodes, outcomes, complete, seeds):
    seed_count = len(seeds)
    primary_count = seed_count * 7
    widths = np.ones((seed_count, 7))
    covered = np.zeros((seed_count, 7))
    ratios = np.full((seed_count, 7), RATIO_CAP)
    case_records = [[] for unused in range(7)]
    controls = []
    for index, outcome in enumerate(outcomes[:primary_count]):
        seed_index, case = divmod(index, 7)
        case_records[case].append(outcome)
        if outcome is not None:
            widths[seed_index, case] = outcome["width"]
            covered[seed_index, case] = outcome["covered"]
            ratios[seed_index, case] = outcome["ratio"]
        if case >= 5:
            controls.append(outcome is not None and outcome["control_ok"])
    replay = outcomes[-1]
    first = outcomes[0]
    replay_ok = first is not None and replay is not None and all(abs(first["response"][key] - replay["response"][key]) <= 1e-12 for key in ("estimate", "lower", "upper"))
    controls.append(replay_ok)
    summaries = []
    nominal_flags = []
    for case in range(7):
        summary = coverage_summary(covered[:, case].tolist())
        nominal_flags.append(summary["nominal_not_rejected"])
        comparisons = {}
        for name in BASELINE_NAMES:
            differences, baseline_coverage, ratio_values = [], [], []
            missing = False
            zero_count = 0
            for seed_index, outcome in enumerate(case_records[case]):
                if outcome is None:
                    missing = True
                    differences.append(1.0)
                    baseline_coverage.append(0)
                    ratio_values.append(RATIO_CAP)
                else:
                    baseline = outcome["baselines"][name]
                    baseline_width = baseline["upper"] - baseline["lower"]
                    differences.append(widths[seed_index, case] - baseline_width)
                    baseline_coverage.append(int(baseline["lower"] <= outcome["truth"] <= baseline["upper"]))
                    ratio_values.append(min(RATIO_CAP, widths[seed_index, case] / max(DENOMINATOR_FLOOR, baseline_width)))
                    zero_count += int(baseline_width == 0)
            paired = paired_summary(differences)
            comparator_valid = coverage_summary(baseline_coverage)
            same_regime_valid = summary["nominal_not_rejected"] and comparator_valid["nominal_not_rejected"] and not missing
            gain = same_regime_valid and paired["upper95"] < 0
            loss = same_regime_valid and paired["lower95"] > 0
            comparisons[name] = {"difference": paired, "ratio": paired_summary(ratio_values),
                                 "baseline_coverage": comparator_valid, "zero_width_count": zero_count,
                                 "valid_gain_supported": gain, "valid_loss_supported": loss,
                                 "inconclusive_or_invalid": not gain and not loss}
        summary["comparisons"] = comparisons
        if case in (5, 6):
            contrast = paired_summary((widths[:, case] - widths[:, 0]).tolist())
            contrast["loss_of_efficiency_supported"] = contrast["lower95"] > 0
            contrast["inconclusive"] = contrast["lower95"] <= 0 <= contrast["upper95"]
            summary["matched_control_minus_original_width"] = contrast
        summary["case"] = case + 1
        summaries.append(summary)
    operational = complete and all(outcome is not None for outcome in outcomes)
    scientific_valid = all(nominal_flags[index] for index in (0, 1, 2, 3, 5, 6))
    integrity = operational and all(controls)
    correct = integrity and (scientific_valid if PLANE == "search" else True)
    utility = np.array([float(np.mean(1 - widths[:, case])) if nominal_flags[case] else 0.0 for case in range(7)])
    metrics = {"combined_score": float(utility.mean()) if correct else 0.0, "correct": int(correct),
               "coverage": float(covered.mean(axis=0).mean()), "mean_width": float(widths.mean(axis=0).mean()),
               "width_ratio_ppiplus": float(ratios.mean(axis=0).mean()), "control_pass_rate": sum(controls) / len(controls)}
    if set(metrics) != set(METRIC_NAMES) or not all(math.isfinite(value) for value in metrics.values()):
        raise ValueError("invalid scalar aggregation")
    return metrics, bool(correct), summaries, bool(integrity)


def make_evaluation_evidence(episodes, outcomes, durations, seeds, summaries, correct):
    records = []
    for seed_index, seed in enumerate(seeds):
        start = seed_index * 7
        selected = outcomes[start:start + 7]
        cases = []
        for case, outcome in enumerate(selected):
            if outcome is None:
                cases.append({"case": case + 1, "failed": True, "coverage": 0, "width": 1.0, "ratio": RATIO_CAP})
            else:
                cases.append({"case": case + 1, "failed": not outcome["control_ok"], "response": outcome["response"],
                              "coverage": int(outcome["covered"]), "width": outcome["width"], "ratio": outcome["ratio"],
                              "truth": outcome["truth"],
                              "baselines": outcome["baselines"], "control_ok": outcome["control_ok"]})
        duration = sum(durations[start:start + 7])
        if seed_index == 0:
            duration += durations[-1]
        solution = {"cases": cases, "reset_seed": episodes[start]["reset_seed"]}
        if seed_index == 0:
            solution["case_summaries"] = summaries
            solution["replay_completed"] = outcomes[-1] is not None
            solution["replay_passed"] = outcomes[0] is not None and outcomes[-1] is not None and all(
                abs(outcomes[0]["response"][key] - outcomes[-1]["response"][key]) <= 1e-12
                for key in ("estimate", "lower", "upper"))
            solution["replay_response"] = None if outcomes[-1] is None else outcomes[-1]["response"]
        score = sum(0.0 if outcome is None or not summaries[case]["nominal_not_rejected"] else 1 - outcome["width"] for case, outcome in enumerate(selected)) / 7 if correct else 0.0
        records.append({"seed": seed, "score": score, "correct": bool(correct and all(outcome is not None for outcome in selected)),
                        "duration_seconds": duration, "solution": solution})
    result = {"schema_version": 1, "episodes": records}
    validate_evaluation_evidence(result)
    return result


def validate_evaluation_evidence(evidence):
    if type(evidence) is not dict or set(evidence) != {"schema_version", "episodes"}:
        raise ValueError("invalid evidence envelope")
    if type(evidence["schema_version"]) is not int or evidence["schema_version"] != 1:
        raise ValueError("invalid evidence version")
    records = evidence["episodes"]
    if type(records) is not list or not 1 <= len(records) <= 10000 or not finite_json(evidence):
        raise ValueError("invalid evidence records")
    seeds = set()
    timeseries_rows = 0
    required = {"seed", "score", "correct", "duration_seconds"}
    optional = {"solution", "candidate_diagnostics", "candidate_timeseries"}
    def finite_number(value):
        return type(value) in (int, float) and math.isfinite(value)
    def valid_name(value):
        return type(value) is str and re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}", value) is not None
    for record in records:
        if type(record) is not dict or not required <= set(record) or set(record) - required - optional:
            raise ValueError("invalid evidence record schema")
        seed = record["seed"]
        if type(seed) is not int or not -(2**63) <= seed < 2**63 or seed in seeds:
            raise ValueError("invalid evidence seed")
        seeds.add(seed)
        if (not finite_number(record["score"]) or type(record["correct"]) is not bool
                or not finite_number(record["duration_seconds"]) or record["duration_seconds"] < 0):
            raise ValueError("invalid evidence measurements")
        if "candidate_diagnostics" in record:
            diagnostics = record["candidate_diagnostics"]
            if type(diagnostics) is not dict or any(not valid_name(key) or not finite_number(value) for key, value in diagnostics.items()):
                raise ValueError("invalid candidate diagnostics")
        if "candidate_timeseries" in record:
            rows = record["candidate_timeseries"]
            if type(rows) is not list:
                raise ValueError("invalid candidate timeseries")
            timeseries_rows += len(rows)
            if timeseries_rows > 100000:
                raise ValueError("oversized candidate timeseries")
            for row in rows:
                if (type(row) is not dict or set(row) != {"series_name", "step", "value"}
                        or not valid_name(row["series_name"]) or type(row["step"]) is not int
                        or row["step"] < 0 or not finite_number(row["value"])):
                    raise ValueError("invalid candidate timeseries row")
    encoded = bounded_json_line(evidence)
    if len(encoded) > 16 * 1024**2:
        raise ValueError("oversized evidence")
    decoded = json.loads(encoded, object_pairs_hook=unique_object)
    if decoded != evidence:
        raise ValueError("invalid evidence serialization")
    return encoded


def write_results(directory, metrics, correct, feasible, evidence=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    evidence_path = directory / "evaluation_evidence.json"
    if evidence_path.is_symlink():
        raise RuntimeError("result symlink forbidden")
    if evidence is not None:
        encoded = validate_evaluation_evidence(evidence)
        evidence_path.write_bytes(encoded)
        if evidence_path.read_bytes() != encoded:
            raise RuntimeError("evidence retention failed")
    elif evidence_path.exists():
        evidence_path.unlink()
    values = {"metrics.json": metrics, "correct.json": {"correct": bool(correct)}}
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        values["qualification.json"] = {"schema_version": 1, "feasible": bool(feasible)}
    for name, value in values.items():
        path = directory / name
        if path.is_symlink():
            raise RuntimeError("result symlink forbidden")
        path.write_bytes(bounded_json_line(value))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])
    for limit, ceiling in ((resource.RLIMIT_AS, 8 * 1024**3), (resource.RLIMIT_CPU, cpu_limit_seconds(WALL_SECONDS, 2))):
        soft, hard = resource.getrlimit(limit)
        target = ceiling if hard == resource.RLIM_INFINITY else min(ceiling, hard)
        resource.setrlimit(limit, (target, target))
    hard_deadline = STARTED + WALL_SECONDS - STARTUP_RESERVE
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    root = Path(os.environ.get("TASK_SOURCE_DIR", Path(__file__).resolve().parent)) / "resources" / PLANE
    defaults = {"combined_score": 0.0, "correct": 0, "coverage": 0.0, "mean_width": 1.0, "width_ratio_ppiplus": RATIO_CAP, "control_pass_rate": 0.0}
    client = None
    try:
        manifest = json.loads((root / "manifest.json").read_text())
        seeds = manifest["seeds"][:1] if smoke else manifest["seeds"]
        episodes = episode_plan(seeds, smoke)
        production_episodes = episode_plan(manifest["seeds"], False)
        rpc_budget = sum(rpc_operation_counts(production_episodes).values())
        if manifest["normalization"] != "z:float64:v1;finite;little-endian;negative-zero-to-zero" or not manifest["split_attestation"]["disjoint_normalized_raw_and_labeled"]:
            raise ValueError("invalid split attestation")
        if sha256_file(root / "examples.npz") != manifest["archive_sha256"]:
            raise ValueError("frozen archive digest mismatch")
        if rpc_budget > 10000000 or rpc_budget != manifest["rpc_budget"]:
            raise ValueError("RPC budget mismatch")
        payload_preflight()
        workload_preflight()
        baseline_ok = True
        try:
            baseline_self_check()
        except RequiredBaselineFailure:
            baseline_ok = False
        client = CandidateClient(args.program_path, rpc_budget)
        def evaluate(episode, call, work_deadline):
            if not baseline_ok:
                raise RequiredBaselineFailure("baseline_result_failure")
            local_deadline = work_deadline
            with alarm_deadline(local_deadline):
                labels, predictions, unlabeled, truth, nonvacuous = prepare_input(root, manifest, episode)
            began = time.monotonic()
            try:
                with alarm_deadline(min(local_deadline, began + BASELINE_SECONDS)):
                    baselines = compute_baselines(labels, predictions, unlabeled)
            except TimeoutError as error:
                raise RequiredBaselineFailure("baseline_timeout") from error
            productive_baseline_seconds.append(time.monotonic() - began)
            with alarm_deadline(local_deadline):
                for request in input_requests(labels, predictions, unlabeled):
                    response = call(request)
                    expected = request["offset"] + len(base64.b64decode(request["data"]))
                    if type(response) is not dict or set(response) != {"ok", "received_bytes"} or response["ok"] is not True or type(response["received_bytes"]) is not int or response["received_bytes"] != expected:
                        raise ProtocolFailure("invalid_input_ack", "input")
                response = call({"op": "infer"})
            validate_interval(response)
            width = float(response["upper"] - response["lower"])
            baseline_width = baselines["ppi_plus_plus_mean"]["upper"] - baselines["ppi_plus_plus_mean"]["lower"]
            control_ok = nonvacuous and (episode["case"] != 5 or abs(response["estimate"] - float(labels.mean())) <= 2e-12)
            if not control_ok:
                record_failure({"component": "candidate", "category": "control_failure", "operation": "infer"})
            return {"response": response, "width": width if control_ok else 1.0,
                    "covered": bool(control_ok and response["lower"] <= truth <= response["upper"]),
                    "ratio": min(RATIO_CAP, width / max(DENOMINATOR_FLOOR, baseline_width)) if control_ok else RATIO_CAP,
                    "truth": truth, "baselines": baselines, "control_ok": bool(control_ok)}
        productive_baseline_seconds = []
        outcomes, complete, durations = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT,
            episode_overhead=(EPISODE_OVERHEAD + NATIVE_READER_RESERVE if client.proxy is None else BROKER_EPISODE_OVERHEAD),
            rpc_cap=RPC_CAP, clock=time.monotonic, rpc=client.rpc,
            first_reset_startup=FIRST_RESET_STARTUP_SECONDS,
            evaluate=evaluate, worst_case=lambda episode: None,
            record_failure=lambda failure: record_failure(dict(failure, **(client.last_capture or {}), exit_status=client.last_exit)),
            cleanup=client.finish_episode)
        complete = complete and client.resets == [episode["reset_seed"] for episode in episodes] and time.monotonic() < hard_deadline
        metrics, correct, summaries, integrity = aggregate(episodes, outcomes, complete, seeds)
        feasible = not smoke and complete and integrity and all(outcome is not None for outcome in outcomes) and baseline_ok
        evidence = make_evaluation_evidence(episodes, outcomes, durations, seeds, summaries, correct)
        write_results(args.results_dir, metrics, correct, feasible, evidence)
    except Exception as error:
        report_runtime_exception(error)
        if isinstance(error, FatalTransportFailure) and hasattr(error, "outcomes"):
            metrics, correct, summaries, integrity = aggregate(episodes, error.outcomes, False, seeds)
            evidence = make_evaluation_evidence(episodes, error.outcomes, error.durations, seeds, summaries, False)
            write_results(args.results_dir, metrics, False, False, evidence)
        else:
            write_results(args.results_dir, defaults, False, False)
        if PLANE == "search":
            name = bounded_failure_name(type(error).__name__.lower(), "evaluation_error")
            print(f"evaluation_exception type={name} message=evaluation_did_not_complete", file=sys.stderr)
        else:
            print("evaluation_exception type=runtime_error message=sealed_evaluation_failed", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        if client is not None:
            client.finish_episode()


if __name__ == "__main__":
    main()
