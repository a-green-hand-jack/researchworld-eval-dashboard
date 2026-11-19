"""Self-contained offline grokking evaluator; policy is frozen in its resource manifest."""

import argparse
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
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

PLANE = "search"
SEEDS = [101, 211]
HORIZON = 6000
WALL_SECONDS = 14400
STARTUP_ALLOWANCE = 600
WORK_SECONDS = 480
POOL_SHA256 = "82395ffadc56bd9185830ddd65c1c8cededa19c6d0353df0211325d7adf514a1"
CPU_SECONDS = 26400
RPC_BUDGET = 12
ENTRY_TIME = time.monotonic()
WIRE_LIMIT = 64 * 1024 * 1024
SMALL_LIMIT = 16384
ARMS = ("fixed_reference", "candidate", "zero_decay", "initial_norm")
CONTROLS = ("constant", "training_copy", "initial_restore", "input_shift")
SCORE_NAME = "combined_score" if PLANE == "search" else "evidence_score"
METRIC_NAMES = (SCORE_NAME, "mean_final_accuracy", "grokking_incidence",
                "restricted_mean_delay", "control_validity_rate", "complete_episode_fraction")


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


def finite_tree(value, depth=0):
    if depth > 12:
        raise ValueError("JSON nesting exceeds limit")
    if value is None or type(value) in (bool, str, int):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            finite_tree(item, depth + 1)
        return
    if type(value) is dict and all(type(key) is str for key in value):
        for item in value.values():
            finite_tree(item, depth + 1)
        return
    raise ValueError("invalid finite JSON value")


def strict_loads(encoded):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    value = json.loads(encoded, object_pairs_hook=pairs,
                       parse_constant=lambda unused: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    finite_tree(value)
    return value


class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class CandidateProtocolError(RuntimeError):
    def __init__(self, category="malformed_response"):
        self.category = bounded_failure_name(category, "malformed_response")
        super().__init__("candidate protocol failure")


class BrokerTransportError(RuntimeError):
    pass


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
        if isinstance(context, CandidateProtocolError):
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


def record_failure(failure):
    if getattr(record_failure, "emitted", False):
        return
    record_failure.emitted = True
    if PLANE == "search":
        component = bounded_failure_name(failure.get("component"), "unknown")
        category = bounded_failure_name(failure.get("category"), "unknown")
        operation = bounded_failure_name(failure.get("operation"), "unknown")
        print(f"episode_failure component={component} category={category} operation={operation}",
              file=sys.stderr, flush=True)


def worker_diagnostic(snapshot, category, component, returncode):
    if PLANE != "search":
        return
    if repair_mode() and snapshot["stderr"]:
        sys.stderr.write(snapshot["stderr"])
    if repair_mode():
        status = returncode if type(returncode) is int else 0
        print(f"worker_failure component={component} category={category} operation=worker "
              f"status_known={int(type(returncode) is int)} status={status} observed_bytes={snapshot['observed_bytes']} "
              f"retained_bytes={snapshot['retained_bytes']} truncated={int(snapshot['truncated'])} "
              f"capture_error={bounded_failure_name(snapshot['capture_error'], 'none')}",
              file=sys.stderr, flush=True)


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


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


def fixed_weight_score(values, weights, worst_case):
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(weight) or weight < 0 for weight in weights)
            or not math.isclose(sum(weights), 1.0, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("invalid predeclared aggregation weights")
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError("nonfinite contribution")
    return sum(value * weight for value, weight in zip(retained, weights))


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout,
                          episode_overhead, rpc_cap, clock, rpc, evaluate, worst_case,
                          record_failure, cleanup=lambda: None):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        episode_started = clock()
        if hasattr(record_failure, "__dict__"):
            record_failure.emitted = False
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
            except (TimeoutError, RequiredBaselineFailure, CandidateProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        pending = None
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > work_deadline:
                raise TimeoutError("episode work deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateProtocolError) as error:
            complete = False
            pending = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(pending)
        finally:
            try:
                cleanup()
            except (RuntimeError, TimeoutError):
                complete = False
                outcomes[index] = worst_case(episode)
                if pending is None:
                    record_failure({"component": "candidate", "category": "cleanup_failure", "operation": "cleanup"})
        if clock() > episode_deadline:
            complete = False
            outcomes[index] = worst_case(episode)
        if type(outcomes[index]) is dict and "duration_seconds" in outcomes[index]:
            outcomes[index]["duration_seconds"] = max(0., clock() - episode_started)
    return outcomes, complete


def candidate_subprocess_settings(parent_environment):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
                     "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
                     "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                     "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION", "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                       MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


NATIVE_WORKER = r'''
import ctypes, importlib.util, json, math, os, resource, sys
resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
if hasattr(os, "sched_getaffinity"):
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
libc = ctypes.CDLL(None, use_errno=True)
libc.syscall.restype = ctypes.c_long
if libc.prctl(38, 1, 0, 0, 0) != 0:
    raise RuntimeError("no_new_privs unavailable")
abi = libc.syscall(444, 0, 0, 1)
if abi < 3:
    raise RuntimeError("Landlock ABI 3 required")
class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]
handled = (1 << 15) - 1
ruleset = Ruleset(handled)
ruleset_fd = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
if ruleset_fd < 0:
    raise RuntimeError("Landlock create failed")
read_access = (1 << 0) | (1 << 2) | (1 << 3)
allowed = ["/usr", "/lib", "/lib64", "/etc/ld.so.cache", "/dev/null", "/dev/urandom", sys.prefix]
for path in dict.fromkeys(allowed + [os.getcwd()]):
    if not os.path.exists(path):
        continue
    descriptor = os.open(path, os.O_PATH | os.O_CLOEXEC)
    rights = read_access
    if not os.path.isdir(path):
        rights &= (1 << 0) | (1 << 1) | (1 << 2) | (1 << 14)
    rule = PathRule(rights, descriptor)
    if libc.syscall(445, ruleset_fd, 1, ctypes.byref(rule), 0) != 0:
        raise RuntimeError("Landlock rule failed")
    os.close(descriptor)
if libc.syscall(446, ruleset_fd, 0) != 0:
    raise RuntimeError("Landlock restriction failed")
os.close(ruleset_fd)
class Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]
class Program(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]
instructions = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e), (0x06, 0, 0, 0x80000000), (0x20, 0, 0, 0)]
for number in [41,42,43,49,50,53,56,57,58,59,62,101,155,165,166,200,234,246,248,249,250,272,288,298,303,304,308,310,311,313,321,322,323,425,426,427,435,438]:
    instructions += [(0x15, 0, 1, number), (0x06, 0, 0, 0x00050001)]
instructions += [(0x35, 0, 1, 0x40000000), (0x06, 0, 0, 0x00050001), (0x06, 0, 0, 0x7fff0000)]
filters = (Filter * len(instructions))(*(Filter(*instruction) for instruction in instructions))
program = Program(len(instructions), filters)
if libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
    raise RuntimeError("seccomp restriction failed")
sys.path.insert(0, os.getcwd())
spec = importlib.util.spec_from_file_location("candidate", "entry.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    if len(line) >= 16384:
        raise ValueError("oversized request")
    request = json.loads(line)
    response = module.handle(request)
    encoded = json.dumps(response, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= 16384:
        raise ValueError("oversized response")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


def stop_process(process):
    if process is None:
        return
    if process.poll() is None:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=.5)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=.5)
    with contextlib.suppress(ProcessLookupError):
        os.killpg(process.pid, signal.SIGKILL)


def read_line(process, timeout, limit):
    deadline = time.monotonic() + timeout
    output = bytearray()
    os.set_blocking(process.stdout.fileno(), False)
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("response timeout")
            if not selector.select(timeout=min(remaining, .05)):
                continue
            chunk = os.read(process.stdout.fileno(), min(65536, limit - len(output)))
            if not chunk:
                raise CandidateProtocolError("worker_exit")
            output.extend(chunk)
            if len(output) >= limit:
                raise CandidateProtocolError("oversized_response")
            if b"\n" in chunk:
                if not output.endswith(b"\n") or output.count(b"\n") != 1:
                    raise CandidateProtocolError("malformed_response")
                return bytes(output)


class CandidateClient:
    def __init__(self, program_path):
        self.path = program_path
        socket = os.environ.get("AGENTIC_CANDIDATE_SOCKET")
        self.broker = program_path == "/broker-code/candidate_proxy.py" and bool(socket)
        if bool(socket) != (program_path == "/broker-code/candidate_proxy.py"):
            raise ValueError("broker requires both trusted signals")
        self.calls = 0
        self.resets = []
        self.process = None
        self.capture = None
        self.directory = None
        self.failure = None
        if self.broker:
            spec = importlib.util.spec_from_file_location("trusted_candidate_proxy", program_path)
            self.module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = self.module
            spec.loader.exec_module(self.module)

    def _start(self):
        self.directory = tempfile.TemporaryDirectory(prefix="grok-candidate-")
        stage = Path(self.directory.name)
        source = Path(self.path).absolute()
        total = 0
        file_count = 0
        for item in source.parent.rglob("*"):
            if item.is_symlink():
                raise CandidateProtocolError("unsafe_candidate_file")
            if not item.is_file() or "__pycache__" in item.parts:
                continue
            total += item.stat().st_size
            file_count += 1
            if total > 8 * 1024 * 1024 or file_count > 256:
                raise CandidateProtocolError("candidate_source_too_large")
            destination = stage / item.relative_to(source.parent)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(item, destination)
        shutil.copyfile(source, stage / "entry.py")
        interpreter, environment = candidate_subprocess_settings(os.environ)
        self.process = subprocess.Popen([interpreter, "-I", "-B", "-u", "-c", NATIVE_WORKER],
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        cwd=stage, env=environment, start_new_session=True, shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)

    def rpc(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise CandidateProtocolError("rpc_budget_exceeded")
        bounded_json_line({"request": request, "id": self.calls, "protocol": "python_rpc_v1"}, SMALL_LIMIT)
        if request["op"] == "reset":
            self.resets.append(request["seed"])
        self.failure = None
        try:
            if self.broker:
                try:
                    with alarm_timeout(timeout):
                        response = self.module.handle(request)
                except (TimeoutError, CandidateProtocolError):
                    raise
                except (RuntimeError, OSError, EOFError) as error:
                    self.failure = "transport_failure"
                    raise BrokerTransportError("broker transport failed") from error
            else:
                try:
                    started = time.monotonic()
                    with alarm_timeout(timeout):
                        if request["op"] == "reset":
                            self.close()
                            self._start()
                        if self.process is None:
                            raise CandidateProtocolError("missing_candidate_process")
                        self.process.stdin.write(bounded_json_line(request, SMALL_LIMIT))
                        self.process.stdin.flush()
                        response = strict_loads(read_line(self.process, max(.001, timeout - (time.monotonic() - started)), SMALL_LIMIT))
                except TimeoutError:
                    raise
                except (ValueError, TypeError, OSError, EOFError) as error:
                    raise CandidateProtocolError("malformed_response") from error
            try:
                finite_tree(response)
                bounded_json_line({"response": response, "id": self.calls, "protocol": "python_rpc_v1"}, SMALL_LIMIT)
            except (ValueError, TypeError) as error:
                raise CandidateProtocolError("malformed_response") from error
            return response
        except TimeoutError:
            self.failure = "timeout"
            raise
        except CandidateProtocolError as error:
            self.failure = error.category
            raise

    def close(self):
        cleanup_error = None
        if self.process is not None:
            process, capture = self.process, self.capture
            self.process = None
            snapshot = None
            original_status = process.poll()
            try:
                stop_process(process)
            except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
                cleanup_error = error
            finally:
                try:
                    snapshot = capture.close()
                except RuntimeError as error:
                    cleanup_error = cleanup_error or error
                if self.failure and snapshot is not None:
                    worker_diagnostic(snapshot, self.failure, "candidate", original_status)
                with contextlib.suppress(OSError):
                    process.stdin.close()
                    process.stdout.close()
        if self.directory is not None:
            self.directory.cleanup()
            self.directory = None
        if cleanup_error is not None:
            raise RuntimeError("candidate cleanup failure") from None


@contextlib.contextmanager
def alarm_timeout(seconds):
    def expired(unused_signal, unused_frame):
        raise TimeoutError("operation deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    previous_timer = signal.setitimer(signal.ITIMER_REAL, max(.001, seconds))
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, *previous_timer)
        signal.signal(signal.SIGALRM, previous)


def plan_request(width, updates, checkpoints):
    return {"op": "plan", "modulus": 97, "operation": "addition", "width": width,
            "architecture": "two_embeddings_sum_gelu_linear_v1", "updates": updates,
            "checkpoints": checkpoints, "train_fraction": 0.6, "precision": "float32"}


def validate_plan(response):
    keys = {"learning_rate", "weight_decay", "init_multiplier"}
    if type(response) is not dict or set(response) != keys:
        raise CandidateProtocolError()
    for key, lower, upper in (("learning_rate", .0001, .01), ("weight_decay", .1, 2.), ("init_multiplier", .5, 2.)):
        value = response[key]
        if type(value) not in (float, int) or not math.isfinite(value) or not lower <= value <= upper:
            raise CandidateProtocolError("invalid_plan")
    return {key: float(response[key]) for key in sorted(keys)}


def raw_identity(row):
    return bounded_json_line({"operation": "addition", "modulus": 97, "a": row[0], "b": row[1]})[:-1]


def load_pool():
    root = Path(os.environ.get("TASK_SOURCE_DIR", Path(__file__).resolve().parent))
    path = root / "resources" / PLANE / "dataset.json"
    if path.is_symlink():
        raise ValueError("resource symlink")
    encoded = path.read_bytes()
    if hashlib.sha256(encoded).hexdigest() != POOL_SHA256:
        raise ValueError("resource checksum mismatch")
    pool = strict_loads(encoded)
    rows = pool["rows"]
    if len(rows) != pool["pool_size"] or pool["modulus"] != 97:
        raise ValueError("invalid pool")
    seen = set()
    for index, row in enumerate(rows):
        if (type(row) is not list or len(row) != 3 or any(type(value) is not int for value in row)
                or not all(0 <= value < 97 for value in row) or row[2] != (row[0] + row[1]) % 97):
            raise ValueError("invalid raw row")
        digest = hashlib.sha256(raw_identity(row)).hexdigest()
        if digest in seen or digest != pool["input_hashes"][index]:
            raise ValueError("duplicate normalized input")
        if hashlib.sha256(bounded_json_line(row)).hexdigest() != pool["example_hashes"][index]:
            raise ValueError("raw example integrity")
        if pool["source_rows"][index] != row[0] * 97 + row[1]:
            raise ValueError("row provenance mismatch")
        seen.add(digest)
    for seed in SEEDS:
        split = pool["splits"][str(seed)]
        train, test = split["train"], split["evaluation"]
        if (len(train) != math.floor(.6 * len(rows)) or len(set(train + test)) != len(rows)
                or sorted(train + test) != list(range(len(rows))) or set(train) & set(test)):
            raise ValueError("invalid split")
    if not pool["audit"]["cross_plane_content_disjoint"]:
        raise ValueError("missing privileged overlap audit")
    return pool


def worst_case(episode):
    return {"metrics": {name: (1.0 if name == "restricted_mean_delay" else 0.0) for name in METRIC_NAMES},
            "correct": False, "duration_seconds": 0.0, "solution": None}


def preflight(pool):
    expected = len(SEEDS) * 3 * 2
    if RPC_BUDGET != expected or RPC_BUDGET > 10000000:
        raise ValueError("RPC operation table mismatch")
    for request in ({"op": "reset", "seed": max(SEEDS)},
                    plan_request(256, HORIZON, list(range(0, HORIZON + 1, 100)))):
        bounded_json_line({"request": request, "id": RPC_BUDGET, "protocol": "python_rpc_v1"}, SMALL_LIMIT)
    for response in ({"ok": True}, {"learning_rate": .00010000000000000002,
                                   "weight_decay": .10000000000000002,
                                   "init_multiplier": 1.9999999999999998}):
        bounded_json_line({"response": response, "id": RPC_BUDGET, "protocol": "python_rpc_v1"}, SMALL_LIMIT)
    budget = pool["policy"]["joint_budget"]
    require_joint_workload_budget(search=budget["search"], final=budget["final"])
    if set(pool["policy"]["controls"]) != set(CONTROLS):
        raise ValueError("canonical controls mismatch")


def require_nonvacuous_shift(original, transformed):
    if not original or len(original) != len(transformed):
        raise ValueError("invalid control rows")
    for before, after in zip(original, transformed):
        if (after != [(before[0] + 1) % 97, before[1]] or before == after
                or sum(before) % 97 == sum(after) % 97):
            raise ValueError("vacuous or invalid permutation")
    if len({(number + 1) % 97 for number in range(97)}) != 97:
        raise ValueError("nonbijective permutation")


def limit_evaluator():
    allowed = sorted(os.sched_getaffinity(0))
    threads = min(2, len(allowed))
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = str(threads)
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    os.sched_setaffinity(0, set(allowed[:threads]))


def trusted_cpu_seconds():
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime


def train_worker(job):
    limit_evaluator()
    threads = len(os.sched_getaffinity(0))
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit_seconds(job["work_seconds"], threads),) * 2)
    import torch
    import torch.nn.functional as functional
    torch.set_num_threads(threads)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    if torch.__version__ != "2.5.1+cpu":
        raise RuntimeError("requires pinned CPU-only torch")
    started = time.monotonic()
    width, seed = job["width"], job["seed"]
    config, arm = job["configuration"], job["arm"]
    if arm == "fixed_reference":
        config = {"learning_rate": .001, "weight_decay": 1., "init_multiplier": 1.}
    elif arm == "zero_decay":
        config = dict(config, weight_decay=0.)

    class Network(torch.nn.Module):
        def __init__(self, hidden, multiplier):
            super().__init__()
            generator = torch.Generator(device="cpu").manual_seed(seed)
            first = torch.randn(97, 256, generator=generator)
            second = torch.randn(97, 256, generator=generator)
            output = torch.randn(256, 97, generator=generator)
            self.first = torch.nn.Parameter(first[:, :hidden].clone() * multiplier)
            self.second = torch.nn.Parameter(second[:, :hidden].clone() * multiplier)
            self.hidden_bias = torch.nn.Parameter(torch.zeros(hidden))
            self.output = torch.nn.Parameter(output[:hidden].clone() * (multiplier / math.sqrt(hidden)))
            self.output_bias = torch.nn.Parameter(torch.zeros(97))

        def forward(self, inputs):
            hidden = self.first[inputs[:, 0]] + self.second[inputs[:, 1]] + self.hidden_bias
            return functional.gelu(hidden) @ self.output + self.output_bias

    model = Network(width, config["init_multiplier"])
    if sum(parameter.numel() for parameter in model.parameters()) != 292 * width + 97:
        raise RuntimeError("architecture shape mismatch")
    if arm == "initial_norm":
        middle = Network(128, config["init_multiplier"])
        target_norm = torch.sqrt(sum(parameter.double().square().sum() for parameter in middle.parameters()))
        source_norm = torch.sqrt(sum(parameter.double().square().sum() for parameter in model.parameters()))
        with torch.no_grad():
            for parameter in model.parameters():
                parameter.mul_((target_norm / source_norm).float())
        del middle
    train = torch.tensor(job["train"], dtype=torch.long)
    test = torch.tensor(job["evaluation"], dtype=torch.long)
    inputs, labels = train[:, :2], train[:, 2]
    evaluation_inputs, evaluation_labels = test[:, :2], test[:, 2]
    optimizer = torch.optim.AdamW(model.parameters(), lr=config["learning_rate"],
                                 weight_decay=config["weight_decay"], foreach=False)
    initial_state = {key: value.detach().clone() for key, value in model.state_dict().items()}

    def serialized_state(state):
        metadata = [{"name": name, "dtype": "float32", "shape": list(tensor.shape)}
                    for name, tensor in state.items()]
        payload = bounded_json_line(metadata) + b"".join(tensor.detach().contiguous().numpy().tobytes()
                                                       for tensor in state.values())
        if len(payload) >= 1024 * 1024:
            raise RuntimeError("trusted serialized state bound exceeded")
        return payload

    initial_serialized = serialized_state(initial_state)
    archived = Network(width, config["init_multiplier"])
    archived.load_state_dict(initial_state)
    with torch.no_grad():
        initial_logits = model(evaluation_inputs).clone()
    majority = int(torch.bincount(labels, minlength=97).argmax())
    fallback_accuracy = float((evaluation_labels == majority).double().mean())
    table = {(int(row[0]), int(row[1])): int(row[2]) for row in train}
    if set(table) & {(int(row[0]), int(row[1])) for row in test}:
        raise RuntimeError("training/evaluation overlap")
    shifted = evaluation_inputs.clone()
    shifted[:, 0] = (shifted[:, 0] + 1) % 97
    require_nonvacuous_shift(evaluation_inputs.tolist(), shifted.tolist())
    if (torch.equal(shifted, evaluation_inputs)
            or not bool(((shifted[:, 0] + shifted[:, 1]) % 97 != evaluation_labels).all())
            or len({(number + 1) % 97 for number in range(97)}) != 97):
        raise RuntimeError("vacuous permutation")
    curves = []
    controls = []
    productive = 0.0
    updates = 0
    for step in range(job["updates"] + 1):
        if time.monotonic() - started > job["work_seconds"] - 2:
            raise TimeoutError("worker work allowance")
        tick = time.monotonic()
        if step:
            optimizer.zero_grad(set_to_none=True)
            loss = functional.cross_entropy(model(inputs), labels)
            if not bool(torch.isfinite(loss)):
                raise RuntimeError("nonfinite training loss")
            loss.backward()
            optimizer.step()
            updates += 1
        if step in job["checkpoints"]:
            with torch.no_grad():
                train_logits = model(inputs)
                evaluation_logits = model(evaluation_inputs)
                norms = {name: float(parameter.double().norm()) for name, parameter in model.named_parameters()}
                curves.append({"step": step, "wall_seconds": time.monotonic() - started,
                               "train_accuracy": float((train_logits.argmax(1) == labels).double().mean()),
                               "evaluation_accuracy": float((evaluation_logits.argmax(1) == evaluation_labels).double().mean()),
                               "train_loss": float(functional.cross_entropy(train_logits, labels)),
                               "evaluation_loss": float(functional.cross_entropy(evaluation_logits, evaluation_labels)),
                               "parameter_count": sum(parameter.numel() for parameter in model.parameters()),
                               "norms": norms, "global_norm": math.sqrt(sum(value * value for value in norms.values()))})
                if arm == "candidate":
                    constant = torch.full_like(evaluation_labels, majority)
                    copied = torch.tensor([table.get((int(row[0]), int(row[1])), majority) for row in test])
                    archived.load_state_dict(initial_state)
                    restored = archived(evaluation_inputs)
                    shifted_logits = model(shifted)
                    constant_accuracy = float((constant == evaluation_labels).double().mean())
                    copy_accuracy = float((copied == evaluation_labels).double().mean())
                    shift_accuracy = float((shifted_logits.argmax(1) == evaluation_labels).double().mean())
                    parent_accuracy = curves[-1]["evaluation_accuracy"]
                    valid = {"constant": constant_accuracy == fallback_accuracy,
                             "training_copy": copy_accuracy == fallback_accuracy,
                             "initial_restore": bool(torch.equal(restored, initial_logits))
                             and serialized_state(archived.state_dict()) == initial_serialized,
                             "input_shift": shifted_logits.shape == evaluation_logits.shape}
                    if not all(valid.values()):
                        raise RuntimeError("control execution failure")
                    controls.append({"step": step, "valid": valid,
                                     "constant_accuracy": constant_accuracy, "copy_accuracy": copy_accuracy,
                                     "initial_accuracy": float((restored.argmax(1) == evaluation_labels).double().mean()),
                                     "shift_accuracy": shift_accuracy,
                                     "causal_applicable": parent_accuracy >= .95,
                                     "causal_drop_supported": parent_accuracy >= .95 and shift_accuracy <= .1
                                     and parent_accuracy - shift_accuracy >= .8})
        productive += time.monotonic() - tick
    result = {"arm": arm, "curves": curves, "controls": controls, "updates": updates,
              "productive_seconds": productive, "duration_seconds": time.monotonic() - started,
              "initial_state_sha256": hashlib.sha256(initial_serialized).hexdigest(),
              "final_state_sha256": hashlib.sha256(serialized_state(model.state_dict())).hexdigest(),
              "serialized_state_bytes": len(initial_serialized)}
    finite_tree(result)
    return result


def run_training(job, *, deadline, category_sink):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ")
    environment = {name: os.environ[name] for name in runtime_names if name in os.environ}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2",
                       NUMEXPR_NUM_THREADS="2")
    process = subprocess.Popen([sys.executable, "-I", "-B", str(Path(__file__).resolve()),
                                "--trusted-worker", "--repair-worker" if repair_mode() else "--sealed-worker"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=environment, start_new_session=True, shell=False)
    capture = BoundedWorkerStderr(process.stderr)
    failure = None
    status = None
    try:
        with alarm_timeout(max(.001, deadline - time.monotonic())):
            process.stdin.write(bounded_json_line(job, 4 * 1024 * 1024))
            process.stdin.flush()
            process.stdin.close()
            try:
                encoded = read_line(process, max(.001, deadline - time.monotonic()), 4 * 1024 * 1024)
            except CandidateProtocolError:
                try:
                    process.wait(timeout=min(.2, max(.001, deadline - time.monotonic())))
                except subprocess.TimeoutExpired:
                    pass
                status = process.poll()
                category = ("baseline_timeout" if status == 124 else
                            "baseline_result_failure" if not status else
                            "baseline_signal" if status < 0 else "baseline_exit")
                fail_required_baseline(category, lambda: stop_process(process), category_sink)
            process.wait(timeout=max(.001, deadline - time.monotonic()))
            status = process.returncode
            if status:
                fail_required_baseline("baseline_timeout" if status == 124 else
                                       "baseline_signal" if status < 0 else "baseline_exit",
                                       lambda: stop_process(process), category_sink)
            try:
                result = strict_loads(encoded)
            except (ValueError, UnicodeError):
                fail_required_baseline("baseline_result_failure", lambda: stop_process(process), category_sink)
            if (result.get("arm") != job["arm"] or result.get("updates") != job["updates"]
                    or [point["step"] for point in result.get("curves", [])] != job["checkpoints"]):
                fail_required_baseline("baseline_result_failure", lambda: stop_process(process), category_sink)
            return result
    except (TimeoutError, subprocess.TimeoutExpired):
        failure = "baseline_timeout"
        fail_required_baseline(failure, lambda: stop_process(process), category_sink)
    except RequiredBaselineFailure as error:
        failure = error.category
        raise
    finally:
        primary_error = sys.exc_info()[1]
        cleanup_error = None
        snapshot = None
        try:
            stop_process(process)
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
            cleanup_error = error
        finally:
            try:
                snapshot = capture.close()
            except RuntimeError as error:
                cleanup_error = cleanup_error or error
            with contextlib.suppress(OSError):
                process.stdout.close()
                if not process.stdin.closed:
                    process.stdin.close()
            if failure and snapshot is not None:
                worker_diagnostic(snapshot, failure, "baseline", status)
        if cleanup_error is not None and primary_error is None:
            fail_required_baseline("baseline_cleanup", lambda: None, category_sink)
        if cleanup_error is not None and repair_mode():
            print("worker_cleanup_failure component=baseline category=cleanup_failure operation=cleanup",
                  file=sys.stderr, flush=True)


def sustained_time(curve, key, threshold):
    for index in range(len(curve) - 2):
        if all(point[key] >= threshold for point in curve[index:index + 3]):
            return curve[index]["step"]
    return None


def curve_events(curve, horizon):
    fit = sustained_time(curve, "train_accuracy", .99)
    generalize = sustained_time(curve, "evaluation_accuracy", .95)
    uncensored = fit is not None and generalize is not None
    delay = max(0, generalize - fit) if uncensored else horizon
    return {"memorization_step": fit, "generalization_step": generalize,
            "right_censored": not uncensored, "restricted_delay": delay / horizon,
            "grokking": uncensored and delay >= 1000}


def execute_episode(episode, call, deadline, *, pool, common_configuration, smoke):
    started = time.monotonic()
    horizon = 4 if smoke else HORIZON
    checkpoints = list(range(5)) if smoke else list(range(0, horizon + 1, 100))
    configuration = validate_plan(call(plan_request(episode["width"], horizon, checkpoints)))
    if common_configuration and configuration != common_configuration[0]:
        raise CandidateProtocolError("configuration_not_common")
    if not common_configuration:
        common_configuration.append(configuration)
    split = pool["splits"][str(episode["seed"]) ]
    train_indices = split["train"][:64] if smoke else split["train"]
    test_indices = split["evaluation"][:64] if smoke else split["evaluation"]
    train = [pool["rows"][index] for index in train_indices]
    evaluation = [pool["rows"][index] for index in test_indices]
    arms = {}
    work = 12 if smoke else WORK_SECONDS
    episode_deadline = min(deadline, time.monotonic() + 4 * (work + 3) + 1)
    for index, arm in enumerate(ARMS):
        if trusted_cpu_seconds() >= CPU_SECONDS - 10:
            raise RequiredBaselineFailure("baseline_cpu_budget")
        method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_deadline,
                                                   methods_remaining=len(ARMS) - index - 1,
                                                   work_seconds=work, cleanup_seconds=3)
        job = {"width": episode["width"], "seed": episode["seed"], "configuration": configuration,
               "arm": arm, "updates": horizon, "checkpoints": checkpoints, "train": train,
               "evaluation": evaluation, "work_seconds": work}
        arms[arm] = run_training(
            job, deadline=method_deadline,
            category_sink=lambda category: record_failure({"component": "baseline", "category": category,
                                                          "operation": "baseline_worker"}))
    candidate = arms["candidate"]
    completed = {name for name in CONTROLS if len(candidate["controls"]) == len(checkpoints)
                 and all(point["valid"].get(name) is True for point in candidate["controls"])}
    if set(CONTROLS) - completed:
        raise RequiredBaselineFailure("baseline_result_failure")
    trajectory_coverage = sum(len(arms[arm]["curves"]) / len(checkpoints) for arm in ARMS) / 4
    control_coverage = sum(sum(point["valid"][name] for point in candidate["controls"])
                           / len(checkpoints) for name in CONTROLS) / 4
    accuracy = candidate["curves"][-1]["evaluation_accuracy"]
    events = {arm: curve_events(arms[arm]["curves"], horizon) for arm in ARMS}
    metrics = dict(zip(METRIC_NAMES, (.5 * trajectory_coverage + .25 * control_coverage + .25 * accuracy,
                                    accuracy, float(events["candidate"]["grokking"]),
                                    events["candidate"]["restricted_delay"], control_coverage, 1.)))
    return {"metrics": metrics, "correct": True, "duration_seconds": time.monotonic() - started,
            "solution": {"width": episode["width"], "horizon": horizon, "configuration": configuration,
                         "arms": arms, "events": events, "split_digest": split["sha256"]}}


def aggregate(outcomes):
    count = len(outcomes)
    metrics = {name: fixed_weight_score([outcome["metrics"][name] for outcome in outcomes],
                                       [1 / count] * count,
                                       1. if name == "restricted_mean_delay" else 0.) for name in METRIC_NAMES}
    return metrics


def paired_contrasts(widths):
    by_width = {record["width"]: record for record in widths if record is not None}
    if set(by_width) != {32, 128, 256}:
        return None
    contrasts = {}
    for field in ("memorization_step", "generalization_step", "restricted_delay"):
        changes = {}
        for arm in ARMS:
            low = by_width[32]["events"][arm][field]
            high = by_width[256]["events"][arm][field]
            if field != "restricted_delay":
                horizon = by_width[32]["horizon"]
                low = 1. if low is None else low / horizon
                high = 1. if high is None else high / horizon
            changes[arm] = high - low
        contrasts[field] = {"wide_minus_narrow": changes,
                            "width_by_decay": changes["candidate"] - changes["zero_decay"],
                            "width_by_initial_norm": changes["candidate"] - changes["initial_norm"]}
    return contrasts


def evidence_records(episodes, outcomes):
    records = []
    for seed in dict.fromkeys(episode["seed"] for episode in episodes):
        selected = [outcome for episode, outcome in zip(episodes, outcomes) if episode["seed"] == seed]
        widths = [outcome["solution"] for outcome in selected]
        records.append({"seed": seed, "score": sum(outcome["metrics"][SCORE_NAME] for outcome in selected) / len(selected),
                        "correct": all(outcome["correct"] for outcome in selected),
                        "duration_seconds": sum(outcome["duration_seconds"] for outcome in selected),
                        "solution": {"widths": widths, "paired_contrasts": paired_contrasts(widths)}})
    contrast_records = [record["solution"]["paired_contrasts"] for record in records]
    if all(record is not None for record in contrast_records):
        intervals = {}
        import itertools
        for field in ("memorization_step", "generalization_step", "restricted_delay"):
            intervals[field] = {}
            for name in ("width_by_decay", "width_by_initial_norm") + ARMS:
                values = [(record[field][name] if name not in ARMS else
                           record[field]["wide_minus_narrow"][name]) for record in contrast_records]
                means = sorted(sum(sample) / len(values) for sample in itertools.product(values, repeat=len(values)))
                intervals[field][name] = {"paired_mean": sum(values) / len(values),
                                           "percentile_low": means[math.floor(.025 * (len(means) - 1))],
                                           "percentile_high": means[math.ceil(.975 * (len(means) - 1))]}
        records[0]["solution"]["exact_seed_bootstrap_intervals"] = intervals
    return {"schema_version": 1, "episodes": records}


def write_results(directory, metrics, correct, *, feasible, evidence=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    outputs = {"metrics.json": metrics, "correct.json": {"correct": bool(correct)}}
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        outputs["qualification.json"] = {"schema_version": 1, "feasible": bool(feasible)}
    if evidence is not None:
        bounded_json_line(evidence, 16 * 1024 * 1024)
        outputs["evaluation_evidence.json"] = evidence
    for name in ("qualification.json", "evaluation_evidence.json"):
        path = directory / name
        if name not in outputs and path.exists():
            if path.is_symlink():
                raise ValueError("result symlink")
            path.unlink()
    for name, value in outputs.items():
        encoded = bounded_json_line(value, 16 * 1024 * 1024)
        path = directory / name
        if path.is_symlink():
            raise ValueError("result symlink")
        path.write_bytes(encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    arguments = parser.parse_args()
    limit_evaluator()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    episodes = ([{"width": 32, "seed": SEEDS[0]}] if smoke else
                [{"width": width, "seed": seed} for width in (32, 128, 256) for seed in SEEDS])
    outcomes = [worst_case(episode) for episode in episodes]
    hard_deadline = ENTRY_TIME + ((120 - 5) if smoke else WALL_SECONDS - STARTUP_ALLOWANCE)
    client = None
    complete = False
    fatal = None
    common_configuration = []
    try:
        pool = load_pool()
        preflight(pool)
        client = CandidateClient(arguments.program_path)
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=5 if smoke else 60,
            reset_timeout=5, episode_overhead=16, rpc_cap=5, clock=time.monotonic,
            rpc=client.rpc,
            evaluate=lambda episode, call, deadline: execute_episode(
                episode, call, deadline, pool=pool, common_configuration=common_configuration, smoke=smoke),
            worst_case=worst_case, record_failure=record_failure, cleanup=client.close)
        complete = complete and client.resets == [episode["seed"] for episode in episodes] and client.calls == 2 * len(episodes)
        complete = complete and trusted_cpu_seconds() <= CPU_SECONDS
    except Exception as error:
        fatal = error
    finally:
        if client is not None:
            try:
                client.close()
            except Exception as error:
                if fatal is None:
                    fatal = error
        metrics = aggregate(outcomes)
        correct = complete and fatal is None and all(outcome["correct"] for outcome in outcomes)
        write_results(arguments.results_dir, metrics, correct,
                      feasible=complete and fatal is None and not smoke and time.monotonic() <= hard_deadline,
                      evidence=evidence_records(episodes, outcomes) if fatal is None else None)
    if fatal is not None:
        if PLANE == "search":
            name = bounded_failure_name(type(fatal).__name__.lower(), "evaluation_error")
            print(f"evaluation_exception type={name} message=evaluator_failed", file=sys.stderr)
        else:
            print("evaluation_exception type=EvaluationError message=sealed_evaluator_failed", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    if "--trusted-worker" in sys.argv:
        try:
            job = strict_loads(sys.stdin.buffer.readline(4 * 1024 * 1024))
            sys.stdout.buffer.write(bounded_json_line(train_worker(job), 4 * 1024 * 1024))
            sys.stdout.buffer.flush()
        except Exception as error:
            if PLANE == "search" and "--repair-worker" in sys.argv:
                report_worker_exception(error)
            else:
                print("required_worker_failure", file=sys.stderr, flush=True)
            raise SystemExit(124 if isinstance(error, TimeoutError) else 1)
    else:
        try:
            exit_code = main()
        except Exception as error:
            name = bounded_failure_name(type(error).__name__.lower(), "evaluation_error")
            message = "evaluation_failed" if PLANE == "search" else "sealed_evaluation_failed"
            print(f"evaluation_exception type={name} message={message}", file=sys.stderr, flush=True)
            exit_code = 1
        raise SystemExit(exit_code)
