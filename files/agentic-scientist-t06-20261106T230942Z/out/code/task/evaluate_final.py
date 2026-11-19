"""Self-contained sealed-plane evaluation; CLI and numerical policy are frozen before scoring.
Search eligibility is integrity/completeness, never comparative superiority. Final correctness
uses the same integrity gates; publication additionally requires the manuscript and evidence.
Grouped bootstrap intervals are descriptive, not cross-design causal identification.
"""
import os
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "2"
import argparse
import base64
import collections
import contextlib
import ctypes
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import numpy as np
from scipy.special import expit

PLANE = 'final'
SEEDS = [401, 503, 607]
CASES = ['arena', 'nba-2011', 'nba-2012', 'nba-2013', 'nba-2014', 'nba-2015']
WALL_SECONDS = 14400
RESOURCE_HASHES = {'arena.json': '5f09a6fab5e9bc34b31d49d3413d8399f205d368fcd3f566b3be5fbef8976959', 'manifest.json': 'fc1d66eb5c2de6756e3d1018fe21e61cecc7e8c13f4dc70e0f1df5e11dacfb24', 'nba-2011.json': '03124543ea7be359edbcdbde5787861b7a7fa9f7227751dfb96260e062a60f06', 'nba-2012.json': '4049379918dbc12e2da108f2f56abad36cdc74c1ceb65d800dcc644ca1a100e3', 'nba-2013.json': 'deac91f0a0dab28a3e7e75e9e4273ab25ff93e5ff55238375d80632f70faafc0', 'nba-2014.json': 'd47a62763b94ae59b7d5fec55dac58ec1fecd08cd20e542cb7fc0774cd0a659a', 'nba-2015.json': 'a114460aa6d904ea9763dbc375061873e4e9ab88ca1df78ea7be727220030535'}
METRICS = ("combined_score", "random_flip_score", "degree_matched_score", "margin_heuristic_score",
           "mean_rank_displacement", "influence_error", "control_error", "scientific_valid", "correct")
CHUNK = 1048576
MAX_CHUNKS = 16
WIRE_LIMIT = 64 * 1048576
LOCAL_LIMIT = 8 * 1048576


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


def wire_check(value):
    line = bounded_json_line(value)
    framed = bounded_json_line({"request_id": 9223372036854775807, "payload": value, "error": None})
    if max(len(line), len(framed)) >= LOCAL_LIMIT:
        raise ProtocolError("message_bound")
    return line


class ProtocolError(RuntimeError):
    def __init__(self, category="malformed_response"):
        self.category = bounded_failure_name(category, "malformed_response")
        super().__init__(self.category)


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


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
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
        needed = (times["startup_seconds"] + times["finish_seconds"]
                  + episodes * (times["reset_seconds"] + methods * (work + times["cleanup_seconds"])))
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
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES",
        "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES", "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION", "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment

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


def repair_mode():
    return PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                 or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


def stop_process(process):
    if process.poll() is not None:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=.2)
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=.2)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=.2)


def report_capture(capture, *, failed, component, category, operation, exitcode):
    snapshot = capture.close()
    if failed and PLANE == "search":
        print("worker_capture component=%s category=%s operation=%s exit=%d observed=%d retained=%d truncated=%d capture_error=%s" % (
            component, bounded_failure_name(category, "unknown"), bounded_failure_name(operation, "unknown"),
            exitcode if exitcode is not None else 0, snapshot["observed_bytes"], snapshot["retained_bytes"],
            snapshot["truncated"], snapshot["capture_error"] or "none"), file=sys.stderr)
        if repair_mode() and snapshot["stderr"]:
            sys.stderr.write(snapshot["stderr"])


def child_limits():
    os.setsid()
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024 ** 3, 4 * 1024 ** 3))
    seconds = cpu_limit_seconds(WALL_SECONDS, 2)
    resource.setrlimit(resource.RLIMIT_CPU, (seconds, seconds))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1048576, 32 * 1048576))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if hasattr(os, "sched_getaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:2])


NATIVE_RUNNER = r'''
import os, sys, ctypes, json, importlib.util, resource
root = os.path.dirname(sys.argv[1])
os.chdir(root)
libc = ctypes.CDLL(None, use_errno=True)
class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]
abi = libc.syscall(444, 0, 0, 1)
if abi < 3:
    raise RuntimeError("Landlock ABI 3 required")
handled = (1 << 15) - 1
ruleset = Ruleset(handled)
fd = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
if fd < 0:
    raise RuntimeError("Landlock create failed")
read_access = (1 << 0) | (1 << 2) | (1 << 3)
for path in list(dict.fromkeys(["/usr", "/lib", "/lib64", "/bin", sys.prefix, root])):
    if not os.path.exists(path):
        continue
    parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
    rule = PathRule(handled if path == root else read_access, parent)
    if libc.syscall(445, fd, 1, ctypes.byref(rule), 0) < 0:
        raise RuntimeError("Landlock rule failed")
    os.close(parent)
for path in ("/dev/null", "/dev/urandom", "/dev/random"):
    parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
    rule = PathRule((1 << 1) | (1 << 2), parent)
    if libc.syscall(445, fd, 1, ctypes.byref(rule), 0) < 0:
        raise RuntimeError("Landlock device rule failed")
    os.close(parent)
if libc.prctl(38, 1, 0, 0, 0) or libc.syscall(446, fd, 0):
    raise RuntimeError("Landlock restrict failed")
os.close(fd)
sec = ctypes.CDLL("libseccomp.so.2")
sec.seccomp_init.argtypes = [ctypes.c_uint32]
sec.seccomp_init.restype = ctypes.c_void_p
sec.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
sec.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
sec.seccomp_load.argtypes = [ctypes.c_void_p]
sec.seccomp_release.argtypes = [ctypes.c_void_p]
ctx = sec.seccomp_init(0x7fff0000)
for name in ("socket", "connect", "bind", "listen", "accept", "accept4", "ptrace", "process_vm_readv", "process_vm_writev", "pidfd_getfd", "mount", "umount2", "open_by_handle_at", "fork", "vfork", "execve", "execveat", "kill", "tkill", "tgkill", "setsid", "setpgid"):
    number = sec.seccomp_syscall_resolve_name(name.encode())
    if number >= 0 and sec.seccomp_rule_add(ctx, 0x50000 | 1, number, 0):
        raise RuntimeError("seccomp rule failed")
if sec.seccomp_load(ctx):
    raise RuntimeError("seccomp load failed")
sec.seccomp_release(ctx)
spec = importlib.util.spec_from_file_location("candidate", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    if len(line) >= 64 * 1048576:
        raise RuntimeError("request bound")
    request = json.loads(line)
    response = module.handle(request)
    encoded = json.dumps(response, allow_nan=False, separators=(",", ":")).encode() + b"\n"
    if len(encoded) >= 64 * 1048576:
        raise RuntimeError("response bound")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


class Candidate:
    def __init__(self, program_path):
        socket = os.environ.get("AGENTIC_CANDIDATE_SOCKET")
        self.brokered = str(program_path) == "/broker-code/candidate_proxy.py" and bool(socket)
        if str(program_path) == "/broker-code/candidate_proxy.py" and not socket:
            raise RuntimeError("broker proxy requires socket")
        self.path = program_path
        self.process = None
        self.capture = None
        self.directory = None
        self.buffer = bytearray()
        self.calls = 0
        self.cap = len(SEEDS) * len(CASES) * 37
        if self.brokered:
            spec = importlib.util.spec_from_file_location("trusted_candidate_proxy", str(program_path))
            self.proxy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.proxy)

    def start(self):
        self.close()
        self.directory = tempfile.TemporaryDirectory(prefix="candidate-")
        source = pathlib.Path(self.path).resolve()
        destination = pathlib.Path(self.directory.name) / "src"
        destination.mkdir()
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 16 * CHUNK:
            raise ProtocolError("invalid_entrypoint")
        shutil.copyfile(source, destination / source.name)
        interpreter, environment = candidate_subprocess_settings(os.environ)
        self.process = subprocess.Popen([interpreter, "-I", "-u", "-c", NATIVE_RUNNER, str(destination / source.name)],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        cwd=self.directory.name, env=environment, shell=False, preexec_fn=child_limits)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.buffer.clear()

    def rpc(self, request, timeout):
        self.calls += 1
        if self.calls > self.cap:
            raise ProtocolError("rpc_budget")
        payload = wire_check(request)
        if self.brokered:
            previous = signal.getsignal(signal.SIGALRM)
            def expired(signum, frame):
                raise TimeoutError()
            signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, max(.001, timeout))
            try:
                response = self.proxy.handle(request)
                wire_check(response)
                return response
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
        deadline = time.monotonic() + timeout
        if request.get("op") == "reset":
            self.start()
        if self.process is None:
            raise ProtocolError("transport_closed")
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                offset = 0
                while offset < len(payload):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    offset += os.write(self.process.stdin.fileno(), payload[offset:offset + 65536])
                selector.unregister(self.process.stdin)
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b"\n" not in self.buffer:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    block = os.read(self.process.stdout.fileno(), 65536)
                    if not block:
                        raise ProtocolError("candidate_exit")
                    self.buffer.extend(block)
                    if len(self.buffer) >= LOCAL_LIMIT:
                        raise ProtocolError("message_bound")
            line, remainder = self.buffer.split(b"\n", 1)
            self.buffer = bytearray(remainder)
            try:
                response = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                wire_check(response)
            except (ValueError, UnicodeError, TypeError, RecursionError) as error:
                raise ProtocolError("malformed_response") from error
            return response
        except (OSError, BrokenPipeError) as error:
            raise ProtocolError("transport_failure") from error

    def close(self, failed=False, operation="cleanup", category="candidate_failure"):
        if self.process is not None:
            process, capture = self.process, self.capture
            self.process, self.capture = None, None
            stop_process(process)
            report_capture(capture, failed=failed, component="candidate", category=category,
                           operation=operation, exitcode=process.returncode)
            process.stdin.close()
            process.stdout.close()
        if self.directory is not None:
            self.directory.cleanup()
            self.directory = None


def require_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise ProtocolError("malformed_response")


def rank(theta, participants):
    order = np.lexsort((np.arange(participants), -theta[:participants]))
    positions = np.empty(participants, dtype=int)
    positions[order] = np.arange(participants)
    return positions


def disruption(first, second):
    left, right = np.triu_indices(len(first), 1)
    return float(np.mean((first[left] < first[right]) != (second[left] < second[right])))


class NumericalFailure(RuntimeError):
    pass


class Model:
    def __init__(self, data, participants, home):
        self.data = np.asarray(data, dtype=float)
        self.participants = participants
        self.dimension = participants + int(home)
        groups, self.inverse = np.unique(self.data[:, [0, 1, 3]], axis=0, return_inverse=True)
        self.design = np.zeros((len(groups), self.dimension))
        self.design[np.arange(len(groups)), groups[:, 0].astype(int)] = 1
        self.design[np.arange(len(groups)), groups[:, 1].astype(int)] = -1
        if home:
            self.design[:, -1] = groups[:, 2]
        self.row_design = self.design[self.inverse]

    def fit(self, outcomes=None, weights=None, initial=None):
        outcomes = self.data[:, 2] if outcomes is None else outcomes
        weights = np.ones(len(self.data)) if weights is None else weights
        multiplicity = np.bincount(self.inverse, weights=weights, minlength=len(self.design))
        wins = np.bincount(self.inverse, weights=weights * outcomes, minlength=len(self.design))
        theta = np.zeros(self.dimension) if initial is None else np.array(initial, dtype=float)
        for iteration in range(100):
            logits = self.design @ theta
            probability = expit(logits)
            gradient = self.design.T @ (multiplicity * probability - wins) + theta
            hessian = self.design.T @ ((multiplicity * probability * (1 - probability))[:, None] * self.design) + np.eye(self.dimension)
            if np.max(np.abs(gradient)) < 2e-7:
                theta[:self.participants] -= theta[:self.participants].mean()
                return theta, hessian
            step = np.linalg.solve(hessian, gradient)
            objective = np.sum(multiplicity * np.logaddexp(0, logits) - wins * logits) + np.dot(theta, theta) / 2
            factor = 1.0
            for backtrack in range(35):
                trial = theta - factor * step
                trial_logits = self.design @ trial
                value = np.sum(multiplicity * np.logaddexp(0, trial_logits) - wins * trial_logits) + np.dot(trial, trial) / 2
                if value <= objective - 1e-4 * factor * np.dot(gradient, step) + 1e-10:
                    theta = trial
                    break
                factor /= 2
            else:
                raise NumericalFailure("reference_line_search")
        raise NumericalFailure("reference_nonconvergence")

    def edited(self, indices, weights=None, initial=None):
        outcomes = self.data[:, 2].copy()
        outcomes[indices] = 1 - outcomes[indices]
        return self.fit(outcomes, weights, initial)[0]


def target_contrast(theta, participants):
    order = np.lexsort((np.arange(participants), -theta[:participants]))[:min(10, participants)]
    position = int(np.argmin(theta[order[:-1]] - theta[order[1:]]))
    contrast = np.zeros(len(theta))
    contrast[order[position + 1]] = 1
    contrast[order[position]] = -1
    return contrast


@contextlib.contextmanager
def work_alarm(seconds):
    previous = signal.getsignal(signal.SIGALRM)
    def expired(signum, frame):
        raise NumericalFailure("baseline_timeout")
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, max(.001, seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def reference_work(payload):
    model = Model(payload["rows"], payload["participants"], payload["home"])
    data = model.data
    allowance = payload["method_seconds"]
    productive_start = time.monotonic()
    with work_alarm(allowance):
        theta, hessian = model.fit()
        original = rank(theta, model.participants)
        copy_theta, _ = model.fit(data[:, 2].copy())
        copy_ok = bool(np.allclose(theta, copy_theta, rtol=0, atol=1e-9))
        contrast = target_contrast(theta, model.participants)
        influences = (1 - 2 * data[:, 2]) * (model.row_design @ np.linalg.solve(hessian, contrast))
        audits = np.linalg.solve(hessian, model.row_design[payload["audit_rows"]].T).T
        finite_difference_ok = True
        for index, derivative in zip(payload["audit_rows"], audits):
            outcomes = data[:, 2].copy()
            outcomes[index] += 1e-3
            perturbed, _ = model.fit(outcomes, initial=theta)
            finite_difference_ok &= bool(np.allclose((perturbed - theta) / 1e-3, derivative, atol=2e-5, rtol=3e-3))
        synthetic = Model([[0, 1, 1, 0], [0, 1, 1, 0], [0, 1, 0, 0]], 2, False)
        synthetic_theta, _ = synthetic.fit()
        changed = synthetic.edited([0])
        constant_ok = bool(np.linalg.norm(changed - synthetic_theta) > .01)
    eligible = np.flatnonzero(data[:, 2] != .5)
    rng = np.random.default_rng(payload["seed"] + 8371)
    counts = payload["counts"]
    baseline_plans, baseline_curves = {}, {}
    degree = np.bincount(data[:, :2].astype(int).ravel(), minlength=model.participants)
    degree_value = degree[data[:, 0].astype(int)] + degree[data[:, 1].astype(int)]
    degree_bins = np.minimum(3, np.searchsorted(np.quantile(degree_value[eligible], [.25, .5, .75]), degree_value, side="right"))
    influence_plan = eligible[np.lexsort((eligible, -influences[eligible]))][:max(counts)]
    margin_value = np.abs(model.row_design @ theta)
    for method in ("random_flip_score", "degree_matched_score", "margin_heuristic_score"):
        with work_alarm(allowance):
            plans, curves = [], []
            stream_count = 1 if method == "margin_heuristic_score" else payload["streams"]
            for stream in range(stream_count):
                if method == "random_flip_score":
                    selected = rng.permutation(eligible)[:max(counts)]
                elif method == "margin_heuristic_score":
                    selected = eligible[np.lexsort((eligible, margin_value[eligible]))][:max(counts)]
                else:
                    pools = {bin_id: list(rng.permutation(eligible[degree_bins[eligible] == bin_id])) for bin_id in range(4)}
                    selected = np.array([pools[int(degree_bins[index])].pop() for index in influence_plan], dtype=int)
                plans.append(selected.tolist())
                curves.append([disruption(original, rank(model.edited(selected[:count], initial=theta), model.participants)) for count in counts])
            baseline_plans[method], baseline_curves[method] = plans, curves
    adjacency = np.zeros((model.participants, model.participants), dtype=bool)
    endpoints = data[:, :2].astype(int)
    adjacency[endpoints[:, 0], endpoints[:, 1]] = True
    adjacency |= adjacency.T
    reached, pending = set(), {0}
    while pending:
        current = pending.pop()
        reached.add(current)
        pending.update(set(np.flatnonzero(adjacency[current])) - reached)
    return {"theta": theta.tolist(), "influences": influences.tolist(), "audits": audits.tolist(),
            "copy_ok": copy_ok, "constant_ok": constant_ok, "finite_difference_ok": bool(finite_difference_ok),
            "baseline_plans": baseline_plans, "baseline_curves": baseline_curves,
            "graph": {"connected": len(reached) == model.participants, "participants": model.participants,
                      "edges": int(adjacency.sum() // 2), "minimum_degree": int(degree.min()),
                      "adjacent_min_gap": float(np.min(np.diff(np.sort(theta[:model.participants]))))},
            "productive_seconds": time.monotonic() - productive_start}


def score_work(payload):
    model = Model(payload["rows"], payload["participants"], payload["home"])
    data, reference = model.data, payload["reference"]
    theta = np.asarray(reference["theta"])
    original = rank(theta, model.participants)
    result = np.asarray(payload["result"], dtype=float)
    dimension, rows = model.dimension, len(data)
    candidate_theta = result[:dimension]
    influences = result[dimension:dimension + rows]
    audit_start = dimension + rows
    audits = result[audit_start:audit_start + 8 * dimension].reshape(8, dimension)
    selection_start = audit_start + 8 * dimension
    selected = result[selection_start:selection_start + max(payload["counts"])].astype(int)
    predictions = result[selection_start + max(payload["counts"]):].reshape(3, dimension)
    _, hessian = model.fit(initial=theta)
    method_ok = bool(np.allclose(candidate_theta, theta, atol=2e-5, rtol=2e-4)
                     and np.allclose(influences, reference["influences"], atol=2e-5, rtol=3e-3)
                     and np.allclose(audits, reference["audits"], atol=2e-5, rtol=3e-3)
                     and reference["finite_difference_ok"])
    curves, displacements, errors, edited_thetas = [], [], [], []
    for budget_index, count in enumerate(payload["counts"]):
        subset = selected[:count]
        changed = model.edited(subset, initial=theta)
        edited_thetas.append(changed)
        changed_rank = rank(changed, model.participants)
        curves.append(disruption(original, changed_rank))
        displacements.append(float(np.mean(np.abs(original - changed_rank)) / (model.participants - 1)))
        exact_linear = np.linalg.solve(hessian, model.row_design[subset].T @ (1 - 2 * data[subset, 2]))
        method_ok &= bool(np.allclose(predictions[budget_index], exact_linear, atol=2e-5, rtol=3e-3))
        discrepancy = np.linalg.norm((changed - theta) - predictions[budget_index])
        errors.append(float(discrepancy / (1 + discrepancy)))
    eligible = np.flatnonzero(data[:, 2] != .5)
    permuted = np.roll(influences[eligible], 1)
    permuted_plan = eligible[np.lexsort((eligible, -permuted))][:max(payload["counts"])]
    permutation_nonvacuous = bool(len(eligible) >= 2 and not np.array_equal(influences[eligible], permuted)
                                  and set(permuted_plan) != set(selected))
    permutation_curves = []
    permutation_effective = False
    for budget_index, count in enumerate(payload["counts"]):
        changed = model.edited(permuted_plan[:count], initial=theta)
        permutation_curves.append(disruption(original, rank(changed, model.participants)))
        permutation_effective |= not np.allclose(changed, edited_thetas[budget_index], rtol=0, atol=1e-9)
    controls = {"copy": bool(reference["copy_ok"]), "constant": bool(reference["constant_ok"]),
                "permutation": bool(permutation_nonvacuous and permutation_effective), "reset": bool(payload["reset_ok"])}
    degree = np.bincount(data[:, :2].astype(int).ravel(), minlength=model.participants)
    degree_value = degree[data[:, 0].astype(int)] + degree[data[:, 1].astype(int)]
    degree_bins = np.minimum(3, np.searchsorted(np.quantile(degree_value[eligible], [.25, .5, .75]), degree_value, side="right"))
    degree_rng = np.random.default_rng(payload["seed"] + 72831)
    degree_plans, degree_curves = [], []
    for stream in range(payload["streams"]):
        pools = {bin_id: list(degree_rng.permutation(eligible[degree_bins[eligible] == bin_id])) for bin_id in range(4)}
        plan = np.array([pools[int(degree_bins[index])].pop() for index in selected], dtype=int)
        degree_plans.append(plan.tolist())
        degree_curves.append([disruption(original, rank(model.edited(plan[:count], initial=theta), model.participants)) for count in payload["counts"]])
    reference["baseline_plans"]["degree_matched_score"] = degree_plans
    reference["baseline_curves"]["degree_matched_score"] = degree_curves
    baseline_curves = {name: np.mean(reference["baseline_curves"][name], axis=0) for name in reference["baseline_curves"]}
    groups, group_index = np.unique(payload["groups"], return_inverse=True)
    rng = np.random.default_rng(payload["seed"] + 49207)
    bootstrap = []
    rank_samples = []
    for replicate in range(payload["replicates"]):
        sampled = rng.integers(0, len(groups), len(groups))
        weights = np.bincount(sampled, minlength=len(groups))[group_index].astype(float)
        sampled_theta, _ = model.fit(weights=weights, initial=theta)
        sampled_rank = rank(sampled_theta, model.participants)
        rank_samples.append(sampled_rank.tolist())
        sample_curves = [disruption(sampled_rank, rank(model.edited(selected[:count], weights, sampled_theta), model.participants)) for count in payload["counts"]]
        paired = {}
        for method, plans in reference["baseline_plans"].items():
            baseline_values = [[disruption(sampled_rank, rank(model.edited(np.array(plan[:count]), weights, sampled_theta), model.participants))
                                for count in payload["counts"]] for plan in plans]
            paired[method] = float(np.mean(np.asarray(sample_curves) - np.mean(baseline_values, axis=0)))
        bootstrap.append({"candidate": float(np.mean(sample_curves)), "paired": paired})
    intervals = {method: np.quantile([sample["paired"][method] for sample in bootstrap], [.025, .975]).tolist()
                 for method in reference["baseline_plans"]}
    valid = bool(method_ok and all(controls.values()) and len(bootstrap) == payload["replicates"])
    values = {"combined_score": float(np.mean(curves)), "mean_rank_displacement": float(np.mean(displacements)),
              "influence_error": float(np.mean(errors)), "control_error": sum(not value for value in controls.values()) / 4,
              "scientific_valid": float(valid), "correct": float(valid)}
    values.update({name: float(np.mean(curve)) for name, curve in baseline_curves.items()})
    if not method_ok:
        values["combined_score"] = values["mean_rank_displacement"] = 0.0
        values["influence_error"] = 1.0
    return {"values": values, "solution": {"case": payload["case"], "counts": payload["counts"], "candidate_curves": curves,
            "baseline_curves": {name: value.tolist() for name, value in baseline_curves.items()}, "permutation_curves": permutation_curves,
            "controls": controls, "method_audit": method_ok, "paired_intervals": intervals,
            "rank_intervals": np.quantile(rank_samples, [.025, .975], axis=0).tolist(), "bootstrap": bootstrap,
            "selected_indices": selected.tolist(), "original_scores": theta.tolist(), "edited_scores": [value.tolist() for value in edited_thetas],
            "influence_errors": errors, "graph": reference["graph"], "productive_reference_seconds": reference["productive_seconds"]}}


def worker_main():
    payload = json.load(sys.stdin)
    try:
        with work_alarm(payload["total_seconds"]):
            value = reference_work(payload) if payload["phase"] == "reference" else score_work(payload)
        sys.stdout.buffer.write(bounded_json_line(value))
    except NumericalFailure as error:
        print("baseline_timeout" if str(error) == "baseline_timeout" else "baseline_result_failure", file=sys.stderr)
        raise SystemExit(4 if str(error) == "baseline_timeout" else 3)
    except Exception as error:
        if repair_mode():
            report_worker_exception(error)
        else:
            print("baseline_result_failure", file=sys.stderr)
        raise SystemExit(3)


class TrustedWorker:
    def __init__(self, payload):
        interpreter, environment = candidate_subprocess_settings(os.environ)
        if repair_mode():
            environment["AGENTIC_TASK_DRAFT_SMOKE"] = "1"
        self.process = subprocess.Popen([sys.executable, "-I", str(pathlib.Path(__file__).resolve()), "--worker"],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        env=environment, shell=False, preexec_fn=child_limits)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        self.process.stderr = None
        self.payload = bounded_json_line(payload)
        self.closed = False
        self.failed = False
        self.category = "baseline_result_failure"
        self.exitcode = None

    def failure_category(self):
        code = self.process.poll()
        if code is None or code == 0:
            return None
        self.exitcode = code
        self.category = "baseline_timeout" if code == 4 else "baseline_signal" if code < 0 else "baseline_exit"
        return self.category

    def result(self, timeout):
        try:
            output, _ = self.process.communicate(self.payload, timeout=timeout)
        except subprocess.TimeoutExpired as error:
            self.failed = True
            self.category = "baseline_timeout"
            raise TimeoutError() from error
        self.exitcode = self.process.returncode
        category = self.failure_category()
        if category is not None:
            self.failed = True
            self.category = category
            raise RequiredBaselineFailure(category)
        if len(output) > 16 * 1048576:
            self.failed = True
            raise RuntimeError("bounded worker result failed")
        try:
            return json.loads(output)
        except (ValueError, UnicodeError) as error:
            self.failed = True
            raise RuntimeError("bounded worker result failed") from error

    def close(self):
        if self.closed:
            return
        self.closed = True
        stop_process(self.process)
        report_capture(self.capture, failed=self.failed or self.process.returncode != 0, component="baseline",
                       category=self.category, operation="baseline_worker", exitcode=self.process.returncode)
        if self.process.stdin and not self.process.stdin.closed:
            self.process.stdin.close()
        if self.process.stdout and not self.process.stdout.closed:
            self.process.stdout.close()


def load_panels(smoke):
    base = pathlib.Path(os.environ.get("TASK_SOURCE_DIR", pathlib.Path(__file__).resolve().parent)) / "resources" / PLANE
    for name, expected in RESOURCE_HASHES.items():
        path = base / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("resource integrity failure")
    manifest = json.loads((base / "manifest.json").read_text())
    if manifest["content_disjoint"] is not True or manifest["source_disjoint"] is not True:
        raise ValueError("resource separation failure")
    panels = {}
    for case in CASES:
        panel = json.loads((base / (case + ".json")).read_text())
        if smoke:
            indices, seen_groups = [], set()
            by_group = collections.defaultdict(list)
            for index, row in enumerate(panel["provenance"]):
                by_group[row["group"]].append(index)
            for group, members in by_group.items():
                seen_groups.add(group)
                indices.extend(members)
                if len(indices) >= 1000:
                    break
            indices.sort()
            panel["rows"] = [panel["rows"][index] for index in indices]
            panel["provenance"] = [panel["provenance"][index] for index in indices]
        data = np.asarray(panel["rows"], dtype=float)
        participants = len(panel["participants"])
        if (data.ndim != 2 or data.shape[1] != 4 or not np.isfinite(data).all()
                or len(data) < 1000 or participants < 2 or participants > 256
                or np.any(data[:, :2] != np.floor(data[:, :2])) or np.any(data[:, :2] < 0)
                or np.any(data[:, :2] >= participants) or np.any(data[:, 0] == data[:, 1])
                or not np.isin(data[:, 2], [0, .5, 1]).all() or not np.isin(data[:, 3], [-1, 0, 1]).all()):
            raise ValueError("invalid observed comparison panel")
        panel["data"] = data
        panels[case] = panel
    return panels


def preflight():
    zeros = base64.b64encode(bytes(CHUNK)).decode("ascii")
    examples = [
        {"op": "upload_chunk", "token": "input", "index": 15, "encoding": "base64", "data": zeros},
        {"index": 15, "encoding": "base64", "data": zeros},
        {"op": "upload_start", "token": "input", "dtype": "<f8", "shape": [524288, 4],
         "byte_length": 16 * CHUNK, "chunks": 16, "participants": 256, "home": True},
        {"op": "analyze", "token": "input", "counts": [524, 2621, 5242], "audit_rows": [524287] * 8,
         "ridge": 1.0, "iterations": 2000},
        {"token": "result", "dtype": "<f8", "shape": [2097152], "byte_length": 16 * CHUNK, "chunks": 16}]
    sizes = [len(wire_check(example)) for example in examples]
    operations = {"reset": 1, "reset_probe": 1, "upload_start": 1, "upload_chunk": MAX_CHUNKS,
                  "upload_commit": 1, "analyze": 1, "download_chunk": MAX_CHUNKS}
    if sum(operations.values()) != 37 or max(sizes) >= LOCAL_LIMIT:
        raise ValueError("protocol preflight failed")
    profiles = {}
    for plane, episodes, wall, startup, finish, work in (("search", 12, 3600, 120, 60, 240), ("final", 18, 14400, 300, 120, 660)):
        profiles[plane] = dict(episode_count=episodes, method_count=1, wall_seconds=wall,
                               startup_seconds=startup, reset_seconds=2, cleanup_seconds=8,
                               finish_seconds=finish, work_seconds=work)
    require_joint_workload_budget(**profiles)
    return operations, sizes


def validate_result(value, expected):
    keys = {"token", "dtype", "shape", "byte_length", "chunks"}
    if (type(value) is not dict or set(value) != keys or value["token"] != "result" or value["dtype"] != "<f8"
            or value["shape"] != [expected] or type(value["byte_length"]) is not int
            or value["byte_length"] != 8 * expected or value["byte_length"] > 16 * CHUNK
            or type(value["chunks"]) is not int or value["chunks"] != math.ceil(8 * expected / CHUNK)):
        raise ProtocolError()


def penalty(episode):
    values = {name: 0.0 for name in METRICS}
    values["influence_error"] = values["control_error"] = 1.0
    return {"values": values, "solution": {"case": episode["case"], "completed": False}, "duration": 0.0}


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = "reset"
        primary_failure = None
        def call(request, *, deadline=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock(), float("inf") if deadline is None else deadline - clock())
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
            outcomes[index] = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                outcomes[index] = worst_case(episode)
                raise TimeoutError("episode cleanup deadline exceeded")
            if outcomes[index].get("values", {}).get("correct", 1) == 0:
                record_failure({"component": "candidate", "category": "scientific_check_failed", "operation": "analyze"})
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            outcomes[index] = worst_case(episode)
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
        outcomes[index]["duration"] = max(0.0, clock() - started)
    return outcomes, complete


def aggregate(episodes, outcomes):
    values = {}
    for name in METRICS:
        if name in ("correct", "scientific_valid"):
            values[name] = float(all(outcome["values"][name] == 1 for outcome in outcomes))
            continue
        case_values = {case: float(np.mean([outcome["values"][name] for episode, outcome in zip(episodes, outcomes) if episode["case"] == case])) for case in CASES}
        values[name] = .5 * case_values["arena"] + .5 * float(np.mean([case_values[case] for case in CASES[1:]]))
    if not all(math.isfinite(value) for value in values.values()):
        raise ValueError("nonfinite aggregation")
    return values


def write_results(directory, metrics, feasible, evidence=None):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "metrics.json").write_bytes(bounded_json_line(metrics))
    (directory / "correct.json").write_bytes(bounded_json_line({"correct": bool(metrics["correct"] == 1)}))
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        (directory / "qualification.json").write_bytes(bounded_json_line({"schema_version": 1, "feasible": bool(feasible)}))
    if evidence is not None:
        data = bounded_json_line({"schema_version": 1, "episodes": evidence}, 16 * 1048576)
        (directory / "evaluation_evidence.json").write_bytes(data)


def main():
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", type=pathlib.Path, required=True)
    parser.add_argument("--results_dir", type=pathlib.Path, required=True)
    args = parser.parse_args()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    startup, finish = ((2, 3) if smoke else (120, 60) if PLANE == "search" else (300, 120))
    hard_deadline = started + (120 if smoke else WALL_SECONDS) - startup
    preflight()
    panels = load_panels(smoke)
    seeds = SEEDS[:1] if smoke else SEEDS
    episodes = [{"seed": seed, "case": case} for seed in seeds for case in CASES]
    client = Candidate(args.program_path)
    method_seconds = 1.0 if smoke else 30.0 if PLANE == "search" else 90.0
    reference_seconds = 4 * method_seconds + (1 if smoke else 2)
    scoring_seconds = 4.0 if smoke else 90.0 if PLANE == "search" else 210.0
    streams = 1 if smoke else 4 if PLANE == "search" else 8
    replicates = 1 if smoke else 10 if PLANE == "search" else 30
    def record_failure(failure):
        if PLANE == "search":
            component = bounded_failure_name(failure.get("component"), "candidate")
            category = bounded_failure_name(failure.get("category"), "unknown")
            operation = bounded_failure_name(failure.get("operation"), "unknown")
            print(("episode_failure component=%s category=%s operation=%s" % (component, category, operation))[:256], file=sys.stderr)
        if failure.get("category") != "scientific_check_failed":
            try:
                client.close(failed=True, operation=bounded_failure_name(failure.get("operation"), "unknown"), category=bounded_failure_name(failure.get("category"), "unknown"))
            except Exception:
                if PLANE == "search":
                    print("cleanup_failure component=candidate category=cleanup_unresolved operation=cleanup", file=sys.stderr)
    def evaluate(episode, call, work_deadline):
        panel = panels[episode["case"]]
        data = panel["data"]
        participants = len(panel["participants"])
        home = episode["case"].startswith("nba-")
        dimension = participants + int(home)
        counts = [math.floor(fraction * len(data)) for fraction in (.001, .005, .01)]
        if min(counts) < 1 or max(counts) > np.sum(data[:, 2] != .5):
            raise ValueError("unusable edit budget")
        audit_rows = np.linspace(0, len(data) - 1, 8, dtype=int).tolist()
        reset_ok = call({"op": "analyze", "token": "input"}) == {"error": "no_data"}
        if not reset_ok:
            raise ProtocolError("reset_state_failure")
        episode_end = min(work_deadline, time.monotonic() + reference_seconds + method_seconds + scoring_seconds + 3)
        if time.monotonic() + reference_seconds + method_seconds + scoring_seconds > work_deadline:
            raise TimeoutError("insufficient full episode work reservation")
        payload = {"rows": panel["rows"], "participants": participants, "home": home, "counts": counts,
                   "seed": episode["seed"], "audit_rows": audit_rows, "method_seconds": method_seconds,
                   "streams": streams, "phase": "reference", "total_seconds": reference_seconds}
        baseline = TrustedWorker(payload)
        primary = None
        def note_failure(category):
            baseline.category = category
            baseline.failed = True
        try:
            reference_deadline = min(episode_end - method_seconds - scoring_seconds - 1, time.monotonic() + reference_seconds)
            reference = collect_required_baseline(baseline.result, deadline=reference_deadline, clock=time.monotonic,
                                                   cancel_work=baseline.close, record_failure=note_failure)
        except (TimeoutError, RequiredBaselineFailure) as error:
            primary = error
            raise
        finally:
            try:
                baseline.close()
            except Exception:
                if primary is None:
                    raise
        candidate_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_end - scoring_seconds,
                                                       methods_remaining=0, work_seconds=method_seconds, cleanup_seconds=.5)
        def candidate_call(request):
            if time.monotonic() >= candidate_deadline:
                raise TimeoutError()
            return call_with_bound(call, request, candidate_deadline)
        guarded = guard_required_baseline(candidate_call, baseline.failure_category, baseline.close, note_failure)
        raw = data.astype("<f8").tobytes()
        chunks = math.ceil(len(raw) / CHUNK)
        if chunks > MAX_CHUNKS:
            raise ValueError("input chunk bound")
        require_ack(guarded({"op": "upload_start", "token": "input", "dtype": "<f8", "shape": list(data.shape),
                            "byte_length": len(raw), "chunks": chunks, "participants": participants, "home": home}))
        for ordinal in range(chunks):
            require_ack(guarded({"op": "upload_chunk", "token": "input", "index": ordinal, "encoding": "base64",
                                 "data": base64.b64encode(raw[ordinal * CHUNK:(ordinal + 1) * CHUNK]).decode("ascii")}))
        require_ack(guarded({"op": "upload_commit", "token": "input"}))
        response = candidate_call({"op": "analyze", "token": "input", "counts": counts,
                                   "audit_rows": audit_rows, "ridge": 1.0, "iterations": 200 if smoke else 2000})
        expected = dimension + len(data) + 8 * dimension + max(counts) + 3 * dimension
        validate_result(response, expected)
        output = bytearray()
        for ordinal in range(response["chunks"]):
            block = candidate_call({"op": "download_chunk", "token": "result", "index": ordinal})
            if type(block) is not dict or set(block) != {"index", "encoding", "data"} or type(block["index"]) is not int or block["index"] != ordinal or block["encoding"] != "base64" or not isinstance(block["data"], str):
                raise ProtocolError()
            try:
                decoded = base64.b64decode(block["data"], validate=True)
            except (ValueError, TypeError) as error:
                raise ProtocolError() from error
            if len(decoded) != min(CHUNK, response["byte_length"] - ordinal * CHUNK):
                raise ProtocolError()
            output.extend(decoded)
        result = np.frombuffer(output, dtype="<f8")
        if len(result) != expected or not np.isfinite(result).all():
            raise ProtocolError()
        selection_start = dimension + len(data) + 8 * dimension
        selection = result[selection_start:selection_start + max(counts)]
        if (np.any(selection != np.floor(selection)) or np.any(selection < 0) or np.any(selection >= len(data))
                or len(set(selection.tolist())) != len(selection) or np.any(data[selection.astype(int), 2] == .5)):
            raise ProtocolError("invalid_edits")
        payload.update(phase="score", result=result.tolist(), reference=reference,
                       groups=[row["group"] for row in panel["provenance"]], reset_ok=reset_ok,
                       replicates=replicates, case=episode["case"], total_seconds=scoring_seconds)
        worker = TrustedWorker(payload)
        primary = None
        try:
            outcome = collect_required_baseline(worker.result, deadline=min(episode_end, time.monotonic() + scoring_seconds),
                                                clock=time.monotonic, cancel_work=worker.close,
                                                record_failure=lambda category: setattr(worker, "category", category))
        except (TimeoutError, RequiredBaselineFailure) as error:
            primary = error
            raise
        finally:
            try:
                worker.close()
            except Exception:
                if primary is None:
                    raise
        return outcome
    outcomes = [penalty(episode) for episode in episodes]
    complete = False
    try:
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline, finish_reserve=finish,
            reset_timeout=2, episode_overhead=2 if smoke else 8, rpc_cap=max(2, method_seconds),
            clock=time.monotonic, rpc=client.rpc, evaluate=evaluate, worst_case=penalty, record_failure=record_failure)
    finally:
        client.close()
    metrics = aggregate(episodes, outcomes)
    evidence = []
    for seed in seeds:
        subset = [(episode, outcome) for episode, outcome in zip(episodes, outcomes) if episode["seed"] == seed]
        seed_outcomes = [outcome for episode, outcome in subset]
        seed_metrics = aggregate([episode for episode, outcome in subset], seed_outcomes)
        evidence.append({"seed": seed, "score": seed_metrics["combined_score"], "correct": bool(seed_metrics["correct"]),
                         "duration_seconds": sum(outcome["duration"] for outcome in seed_outcomes),
                         "solution": {"cases": [outcome["solution"] for outcome in seed_outcomes]}})
    feasible = complete and not smoke and time.monotonic() < hard_deadline and all("completed" not in outcome["solution"] for outcome in outcomes)
    write_results(args.results_dir, metrics, feasible, evidence)


def call_with_bound(call, request, deadline):
    return call(request, deadline=deadline)


if __name__ == "__main__":
    if sys.argv[1:] == ["--worker"]:
        worker_main()
    else:
        try:
            main()
        except Exception as error:
            category = bounded_failure_name(type(error).__name__.lower(), "evaluator_exception")
            if PLANE == "search":
                print("evaluator_exception type=" + category + " message=evaluation aborted", file=sys.stderr)
            else:
                print("evaluator_exception", file=sys.stderr)
            try:
                position = sys.argv.index("--results_dir") + 1
                fallback = {name: 0.0 for name in METRICS}
                fallback["influence_error"] = fallback["control_error"] = 1.0
                write_results(pathlib.Path(sys.argv[position]), fallback, False)
            except Exception:
                pass
            raise SystemExit(1)
