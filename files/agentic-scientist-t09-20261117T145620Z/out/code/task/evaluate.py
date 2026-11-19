"""Self-contained offline network-interference evaluator.

The local manifest freezes observed datasets, normalization, seeds, controls,
aggregation and maximum protocol counts. Truth never enters candidate RPC.
"""

import argparse
import base64
import collections
import contextlib
import ctypes
import hashlib
import importlib.util
import io
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
import zipfile

STARTED = time.monotonic()
NATIVE_ALLOWED_CPUS = sorted(os.sched_getaffinity(0))
PLANE = "search"
WALL = 1800 if PLANE == "search" else 10800
STARTUP_ALLOWANCE = 60 if PLANE == "search" else 600
METHOD_WORK = 0.3 if PLANE == "search" else 0.6
CHUNK = 8 * 1024 * 1024
WIRE_LIMIT = 64 * 1024 * 1024
RESULT_LIMIT = 1024 * 1024
METRIC_NAMES = ("combined_score", "gate_rmse", "gate_bias_lower", "gate_bias_upper",
                "coverage_95", "mean_interval_width", "failure_rate", "control_loss", "correct")
for thread_variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[thread_variable] = "2"

import networkx as nx
import numpy as np
from scipy import sparse
from scipy.io import mmread
from scipy.linalg import lstsq


class InvalidResetResponse(RuntimeError):
    pass


class ProtocolFailure(RuntimeError):
    pass


class SemanticFailure(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, ProtocolFailure):
            return {"component": "candidate", "category": "malformed_response",
                    "operation": bounded_failure_name(operation, "unknown")}
        if isinstance(context, SemanticFailure):
            return {"component": "candidate", "category": "regression_or_control_invalid", "operation": "fit"}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout",
            "operation": bounded_failure_name(operation, "unknown")}


def record_failure(failure):
    if PLANE == "search":
        component = bounded_failure_name(failure.get("component"), "unknown")
        category = bounded_failure_name(failure.get("category"), "unknown")
        operation = bounded_failure_name(failure.get("operation"), "unknown")
        print(f"episode_failure component={component} category={category} operation={operation}"[:256], file=sys.stderr)


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


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ProtocolFailure("complete message exceeds wire limit")
    return encoded


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode_json(value):
    return json.loads(value, object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    if not all(math.isfinite(value) and value >= 0 for value in
               (now, episode_deadline, work_seconds, cleanup_seconds)) or work_seconds <= 0:
        raise ValueError("invalid matched work allowance")
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid method count")
    needed = (methods_remaining + 1) * (work_seconds + cleanup_seconds)
    if now + needed > episode_deadline:
        raise TimeoutError("insufficient matched method reservations")
    return now + work_seconds


@contextlib.contextmanager
def bounded_work(deadline, baseline=False):
    def expired(signum, frame):
        if baseline:
            raise RequiredBaselineFailure("baseline_timeout")
        raise TimeoutError("work deadline")
    previous = signal.signal(signal.SIGALRM, expired)
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        signal.signal(signal.SIGALRM, previous)
        expired(None, None)
    entered = time.monotonic()
    previous_timer = signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if previous_timer[0] > 0:
            restored = max(1e-6, previous_timer[0] - (time.monotonic() - entered))
            signal.setitimer(signal.ITIMER_REAL, restored, previous_timer[1])


def candidate_subprocess_settings(parent_environment):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
                     "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
                     "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                     "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
                     "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


WORKER = r'''
import ctypes, errno, importlib.util, json, os, resource, sys
def restrict():
    allowed_cpus = [int(value) for value in sys.argv[3].split(",")]
    os.sched_setaffinity(0, allowed_cpus)
    library = ctypes.CDLL(None, use_errno=True)
    if os.uname().machine != "x86_64":
        raise RuntimeError("native smoke requires Linux x86_64")
    class Ruleset(ctypes.Structure):
        _fields_ = [("handled_access_fs", ctypes.c_uint64)]
    class PathRule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]
    abi = library.syscall(444, 0, 0, 1)
    if abi < 1:
        raise RuntimeError("Landlock unavailable")
    handled = (1 << 13) - 1
    if abi >= 2:
        handled |= 1 << 13
    if abi >= 3:
        handled |= 1 << 14
    descriptor = library.syscall(444, ctypes.byref(Ruleset(handled)), 8, 0)
    if descriptor < 0:
        raise OSError(ctypes.get_errno(), "Landlock ruleset")
    paths = {sys.prefix, sys.base_prefix, "/usr/lib", "/lib", "/lib64", "/etc/ld.so.cache", os.getcwd()}
    for path in sorted(paths):
        if not os.path.exists(path):
            continue
        parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
        rights = (1 << 2) | ((1 << 3) if os.path.isdir(path) else 0)
        rule = PathRule(rights, parent)
        if library.syscall(445, descriptor, 1, ctypes.byref(rule), 0) != 0:
            raise OSError(ctypes.get_errno(), "Landlock path")
        os.close(parent)
    if library.prctl(38, 1, 0, 0, 0) != 0 or library.syscall(446, descriptor, 0) != 0:
        raise OSError(ctypes.get_errno(), "Landlock restrict")
    os.close(descriptor)
    class Filter(ctypes.Structure):
        _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte),
                    ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]
    class Program(ctypes.Structure):
        _fields_ = [("length", ctypes.c_ushort), ("filters", ctypes.POINTER(Filter))]
    instructions = [Filter(0x20, 0, 0, 4), Filter(0x15, 1, 0, 0xc000003e),
                    Filter(0x06, 0, 0, 0x80000000), Filter(0x20, 0, 0, 0)]
    instructions.extend([Filter(0x15, 0, 4, 56), Filter(0x20, 0, 0, 16),
                         Filter(0x45, 1, 0, 0x10000), Filter(0x06, 0, 0, 0x50000 | errno.EPERM),
                         Filter(0x20, 0, 0, 0)])
    instructions.extend([Filter(0x15, 0, 4, 302), Filter(0x20, 0, 0, 16),
                         Filter(0x15, 1, 0, 0), Filter(0x06, 0, 0, 0x50000 | errno.EPERM),
                         Filter(0x20, 0, 0, 0)])
    denied = [29,30,31,41,42,43,44,45,49,50,53,57,58,62,64,65,66,67,68,69,70,71,
              76,77,90,91,92,93,94,101,129,132,141,142,144,155,161,165,166,188,189,190,
              197,198,199,200,203,234,235,260,261,268,272,280,288,297,298,304,308,310,311,
              321,323,424,425,426,427,434,452]
    instructions.extend([Filter(0x15, 0, 1, 435), Filter(0x06, 0, 0, 0x50000 | errno.ENOSYS)])
    for syscall in denied:
        instructions.extend([Filter(0x15, 0, 1, syscall), Filter(0x06, 0, 0, 0x50000 | errno.EPERM)])
    instructions.extend([Filter(0x35, 0, 1, 0x40000000), Filter(0x06, 0, 0, 0x50000 | errno.EPERM),
                         Filter(0x06, 0, 0, 0x7fff0000)])
    filters = (Filter * len(instructions))(*instructions)
    program = Program(len(instructions), filters)
    if library.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "seccomp restrict")
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (int(sys.argv[1]), int(sys.argv[1])))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
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

def main():
    restrict()
    sys.path.insert(0, os.getcwd())
    specification = importlib.util.spec_from_file_location("candidate", "candidate.py")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    for line in sys.stdin.buffer:
        if len(line) >= 64 * 1024**2:
            raise ValueError("request too large")
        response = module.handle(json.loads(line))
        encoded = json.dumps(response, allow_nan=False, separators=(",", ":")).encode() + b"\n"
        if len(encoded) >= 1024**2:
            raise ValueError("response too large")
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
try:
    main()
except Exception as error:
    if sys.argv[2] == "repair":
        report_worker_exception(error)
    else:
        print("candidate_worker_failure", file=sys.stderr, flush=True)
    sys.exit(1)
'''


class CandidateRPC:
    def __init__(self, path, maximum_calls):
        self.path = path
        self.maximum_calls = maximum_calls
        self.calls = 0
        self.process = None
        self.capture = None
        self.directory = None
        self.handle = None
        self.reset_transcript = []
        self.repair = PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                               or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")
        socket = os.environ.get("AGENTIC_CANDIDATE_SOCKET")
        if socket or path == "/broker-code/candidate_proxy.py":
            if not socket or path != "/broker-code/candidate_proxy.py":
                raise ProtocolFailure("broker requires both authentication signals")
            specification = importlib.util.spec_from_file_location("trusted_candidate_proxy", path)
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            self.handle = module.handle

    def _start(self):
        if len(NATIVE_ALLOWED_CPUS) < 4:
            raise ProtocolFailure("native isolation requires four available CPUs")
        self.directory = tempfile.TemporaryDirectory(prefix="gate-native-")
        shutil.copyfile(self.path, Path(self.directory.name) / "candidate.py")
        interpreter, environment = candidate_subprocess_settings(os.environ)
        self.process = subprocess.Popen(
            [interpreter, "-I", "-B", "-u", "-c", WORKER,
str(cpu_limit_seconds(WALL, 2)), "repair" if self.repair else "ordinary",
             ",".join(str(cpu) for cpu in NATIVE_ALLOWED_CPUS[2:4])],
            cwd=self.directory.name, env=environment, shell=False, start_new_session=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def close(self, failed=False):
        if self.process is None:
            return
        process, capture, directory = self.process, self.capture, self.directory
        self.process = self.capture = self.directory = None
        try:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=.3)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=.7)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        finally:
            process.stdin.close()
            process.stdout.close()
            snapshot = capture.close()
            if failed and self.repair:
                print(f"worker_capture observed_bytes={snapshot['observed_bytes']} retained_bytes={snapshot['retained_bytes']} "
                      f"truncated={int(snapshot['truncated'])} capture_error={snapshot['capture_error'] or 'none'}",
                      file=sys.stderr)
                if snapshot["stderr"]:
                    print(snapshot["stderr"], end="", file=sys.stderr)
            directory.cleanup()

    def __call__(self, request, timeout):
        self.calls += 1
        if self.calls > self.maximum_calls:
            raise ProtocolFailure("RPC count exceeded")
        encoded = bounded_json_line(request)
        if request["op"] == "reset":
            self.reset_transcript.append(request["seed"])
        deadline = time.monotonic() + timeout
        if self.handle is not None:
            with bounded_work(deadline):
                response = self.handle(request)
                try:
                    bounded_json_line(response, RESULT_LIMIT)
                except (ValueError, TypeError, RecursionError) as error:
                    raise ProtocolFailure("invalid broker response") from error
                return response
        if request["op"] == "reset":
            self.close()
            self._start()
        if self.process is None:
            raise ProtocolFailure("candidate process unavailable")
        received = bytearray()
        offset = 0
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("candidate RPC timeout")
                events = selector.select(remaining)
                if not events:
                    raise TimeoutError("candidate RPC timeout")
                for key, mask in events:
                    if key.fileobj is self.process.stdin:
                        try:
                            offset += os.write(key.fd, encoded[offset:offset + 65536])
                        except (BrokenPipeError, OSError) as error:
                            raise ProtocolFailure("candidate transport closed") from error
                        if offset == len(encoded):
                            selector.unregister(self.process.stdin)
                    else:
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            raise ProtocolFailure("candidate response missing")
                        received.extend(chunk)
                        if len(received) >= RESULT_LIMIT:
                            raise ProtocolFailure("candidate response too large")
                        if b"\n" in received:
                            if not received.endswith(b"\n") or received.count(b"\n") != 1:
                                raise ProtocolFailure("candidate response framing")
                            try:
                                response = decode_json(received)
                                bounded_json_line(response, RESULT_LIMIT)
                                return response
                            except (ValueError, TypeError, RecursionError) as error:
                                raise ProtocolFailure("malformed JSON response") from error


def normalize_edges(edges, count):
    edges = np.asarray(edges, dtype="<i8").reshape(-1, 2)
    edges = np.sort(edges, axis=1)
    edges = edges[edges[:, 0] != edges[:, 1]]
    edges = np.unique(edges, axis=0)
    if edges.size and (edges.min() < 0 or edges.max() >= count):
        raise ValueError("edge endpoint out of bounds")
    return np.ascontiguousarray(edges, dtype="<i8")


def topology_hash(edges, count):
    canonical = normalize_edges(edges, count)
    return hashlib.sha256(np.asarray([count], dtype="<i8").tobytes() + canonical.tobytes()).hexdigest()


def row_hashes(covariates, treatment, outcome):
    numeric = np.column_stack([covariates, treatment, outcome]).astype("<f8")
    numeric[numeric == 0] = 0
    if not np.isfinite(numeric).all():
        raise ValueError("nonfinite raw example")
    return [hashlib.sha256(row.tobytes()).digest() for row in numeric]


def examples_hash(covariates, treatments, outcomes):
    hashes = []
    for treatment, outcome in zip(treatments, outcomes):
        hashes.extend(row_hashes(covariates, treatment, outcome))
    return hashlib.sha256(b"".join(sorted(hashes))).hexdigest()


def public_graph(path):
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != "b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d":
        raise ValueError("public archive checksum mismatch")
    with zipfile.ZipFile(path) as archive:
        members = [name for name in archive.namelist() if name.endswith("socfb-Stanford3.mtx")]
        if len(members) != 1:
            raise ValueError("public archive layout mismatch")
        raw = archive.read(members[0])
    matrix = mmread(io.BytesIO(raw)).tocoo()
    if matrix.shape != (11586, 11586):
        raise ValueError("public graph shape mismatch")
    return normalize_edges(np.column_stack([matrix.row, matrix.col]), 11586)


def adjacency(edges, count):
    return sparse.csr_matrix((np.ones(2 * len(edges)),
                             (np.r_[edges[:, 0], edges[:, 1]], np.r_[edges[:, 1], edges[:, 0]])),
                            shape=(count, count))


def regression_arrays(edges, covariates, treatment):
    count = len(treatment)
    graph = adjacency(edges, count)
    degree = np.asarray(graph.sum(axis=1)).ravel()
    exposure = np.asarray(graph @ treatment).ravel() / np.maximum(degree, 1)
    centered = np.log1p(degree)
    centered -= centered.mean()
    first, second = covariates.T
    def matrix(assigned, exposed):
        return np.column_stack([np.ones(count), assigned, first, second, centered,
                                assigned * first, assigned * second, exposed, exposed ** 2,
                                assigned * exposed, first * exposed, second * exposed])
    design = matrix(treatment, exposure)
    difference = (matrix(np.ones(count), (degree > 0).astype(float)).mean(axis=0)
                  - matrix(np.zeros(count), np.zeros(count)).mean(axis=0))
    return design, difference, exposure


def solve_regression(design, outcome, ridge):
    count = design.shape[1]
    penalty = np.diag(np.r_[0., np.full(count - 1, math.sqrt(ridge))])
    try:
        coefficients = lstsq(np.concatenate((design, penalty), axis=0),
                             np.r_[outcome, np.zeros(count)], cond=1e-12, lapack_driver="gelsd")[0]
    except np.linalg.LinAlgError as error:
        raise RequiredBaselineFailure("baseline_result_failure") from error
    if not np.isfinite(coefficients).all():
        raise RequiredBaselineFailure("baseline_result_failure")
    return coefficients


def interval(design, outcome, coefficients, difference, ridge, blocks):
    estimate = float(difference @ coefficients)
    residual = outcome - design @ coefficients
    penalty = np.diag(np.r_[0., np.full(len(coefficients) - 1, ridge)])
    bread = np.linalg.pinv(design.T @ design + penalty, rcond=1e-12)
    labels, membership = np.unique(blocks, return_inverse=True)
    group_count = len(labels)
    if group_count < 2 or len(outcome) <= np.linalg.matrix_rank(design, tol=1e-10):
        return [-100., 100.]
    scores = np.zeros((group_count, len(coefficients)))
    np.add.at(scores, membership, design * residual[:, None])
    projected = scores @ bread @ difference
    variance = float(projected @ projected) * group_count / (group_count - 1)
    radius = 1.959963984540054 * math.sqrt(max(variance, 0.))
    return [max(-100., min(100., estimate - radius)), max(-100., min(100., estimate + radius))]


def fit_summary(design, outcome, difference, blocks, ridge):
    coefficients = solve_regression(design, outcome, ridge)
    estimate = float(difference @ coefficients)
    try:
        bounds = interval(design, outcome, coefficients, difference, ridge, blocks)
    except np.linalg.LinAlgError as error:
        raise RequiredBaselineFailure("baseline_result_failure") from error
    return {"gate": estimate, "interval": bounds}, coefficients


def check_fit(response, design, outcome, difference, blocks):
    if type(response) is not dict or set(response) != {"basis", "ridge", "coefficients", "gate"}:
        raise ProtocolFailure("fit response schema")
    if response["basis"] not in ("linear", "augmented") or type(response["ridge"]) not in (int, float):
        raise ProtocolFailure("invalid recipe")
    if response["ridge"] not in (0, .01, .1, 1):
        raise ProtocolFailure("invalid penalty")
    width = 8 if response["basis"] == "linear" else 12
    coefficients = response["coefficients"]
    if (type(coefficients) is not list or len(coefficients) != width
            or any(type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e6
                   for value in coefficients)
            or type(response["gate"]) not in (int, float) or not math.isfinite(response["gate"])
            or abs(response["gate"]) > 1e6):
        raise ProtocolFailure("invalid mathematical output")
    restricted, contrast = design[:, :width], difference[:width]
    trusted = solve_regression(restricted, outcome, response["ridge"])
    coefficients = np.asarray(coefficients, dtype=float)
    estimate = float(contrast @ coefficients)
    if not np.allclose(trusted, coefficients, atol=2e-6, rtol=2e-6):
        raise SemanticFailure("not the declared regression solution")
    if not math.isclose(estimate, response["gate"], abs_tol=2e-6, rel_tol=2e-6):
        raise SemanticFailure("not the endpoint contrast")
    bounds = interval(restricted, outcome, coefficients, contrast, response["ridge"], blocks)
    return {"gate": estimate, "interval": bounds, "basis": response["basis"],
            "ridge": response["ridge"], "coefficients": coefficients.tolist()}


def input_messages(data):
    packed = bytearray()
    descriptors = []
    for name, dtype in [("edges", "<i8"), ("x", "<f8"), ("z", "|u1"), ("y", "<f8"), ("blocks", "<i8")]:
        values = np.ascontiguousarray(data[name], dtype=dtype)
        raw = values.tobytes()
        descriptors.append({"name": name, "dtype": dtype, "shape": list(values.shape),
                            "offset": len(packed), "nbytes": len(raw)})
        packed.extend(raw)
    if not 0 < len(packed) <= 8 * CHUNK:
        raise ValueError("logical input exceeds frozen cap")
    yield {"op": "begin", "n": len(data["z"]), "arrays": descriptors,
           "total_bytes": len(packed), "chunks": math.ceil(len(packed) / CHUNK),
           "sha256": hashlib.sha256(packed).hexdigest()}
    for index, offset in enumerate(range(0, len(packed), CHUNK)):
        chunk = packed[offset:offset + CHUNK]
        yield {"op": "upload", "index": index, "encoding": "base64",
               "data": base64.b64encode(chunk).decode("ascii"), "sha256": hashlib.sha256(chunk).hexdigest()}


def wire_preflight(episode_count):
    raw = b"\xff" * CHUNK
    request = {"op": "upload", "index": 7, "encoding": "base64",
               "data": base64.b64encode(raw).decode("ascii"), "sha256": hashlib.sha256(raw).hexdigest()}
    response = {"basis": "augmented", "ridge": 0.01,
                "coefficients": [-1.2345678901234567e-300] * 12, "gate": -1.2345678901234567e-300}
    lengths = []
    for message in (request, response, {"ok": True}):
        lengths.append(len(bounded_json_line({"id": 9223372036854775807, "method": "handle",
                                              "payload": message, "framing_reserve": " " * 4096})))
    if lengths[1] >= RESULT_LIMIT:
        raise ValueError("result envelope exceeds cap")
    counts = {"reset": episode_count, "begin": episode_count, "upload": 8 * episode_count,
              "fit": episode_count, "release": episode_count}
    trace = collections.Counter()
    for _ in range(episode_count):
        trace.update(["reset", "begin"] + ["upload"] * 8 + ["fit", "release"])
    if dict(trace) != counts or sum(counts.values()) > 10000000:
        raise ValueError("maximum protocol trace mismatch")
    return counts, lengths


def worst_case(episode):
    return {"valid": False, "loss": 1., "squared_error": 10000., "bias_lower": -100.,
            "bias_upper": 100., "coverage": 0., "width": 200., "duration": 0., "solution": None}


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure, cleanup=None):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    baseline_failed = False
    for index, episode in enumerate(episodes):
        started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = "reset"
        primary_failure = None
        failed = False
        def call(request, timeout=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                allowance = min(rpc_cap, work_deadline - clock())
                if timeout is not None:
                    allowance = min(allowance, timeout)
                if allowance <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=allowance)
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            allowance = min(reset_timeout, rpc_cap, work_deadline - clock())
            if allowance <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=allowance))
            if baseline_failed:
                raise RequiredBaselineFailure("baseline_result_failure")
            value = evaluate(episode, call, work_deadline)
            if clock() > work_deadline:
                raise TimeoutError("episode work deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure, SemanticFailure) as error:
            failed = True
            complete = False
            baseline_failed |= isinstance(error, RequiredBaselineFailure)
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
        finally:
            if cleanup is not None:
                try:
                    cleanup(failed)
                except (OSError, RuntimeError, subprocess.TimeoutExpired):
                    complete = False
                    if not failed:
                        record_failure({"component": "candidate", "category": "cleanup_failure", "operation": "cleanup"})
                        failed = True
                    outcomes[index] = worst_case(episode)
            outcomes[index]["duration"] = max(0., clock() - started)
        if clock() > episode_deadline:
            complete = False
            if not failed:
                record_failure({"component": "candidate", "category": "cleanup_timeout", "operation": "cleanup"})
            outcomes[index] = dict(worst_case(episode), duration=max(0., clock() - started))
    return outcomes, complete


def blocks_from_graph(edges, count):
    graph = nx.Graph()
    graph.add_nodes_from(range(count))
    graph.add_edges_from(edges.tolist())
    ordered = []
    visited = set()
    for root in range(count):
        if root in visited:
            continue
        queue = collections.deque([root])
        visited.add(root)
        while queue:
            node = queue.popleft()
            ordered.append(node)
            for neighbor in sorted(graph[node]):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
    blocks = np.empty(count, dtype='<i8')
    blocks[ordered] = np.minimum(np.arange(count) * 16 // count, 15)
    return blocks

def generate_graph(seed, graph_index, count):
    generator = np.random.default_rng(np.random.SeedSequence([seed, graph_index, 10]))
    graph_seed = int(generator.integers(0, 2**32-1))
    if graph_index == 0:
        sizes = [count//4]*4
        sizes[-1] += count-sum(sizes)
        probabilities = np.full((4,4), 10/count)
        np.fill_diagonal(probabilities, 50/count)
        graph = nx.stochastic_block_model(sizes, probabilities, seed=graph_seed)
    elif graph_index == 1:
        graph = nx.barabasi_albert_graph(count, 10, seed=graph_seed)
    else:
        graph = nx.watts_strogatz_graph(count, 20, .1, seed=graph_seed)
    return normalize_edges(list(graph.edges()), count)

def simulation(seed, graph_index, edges, count):
    generator = np.random.default_rng(np.random.SeedSequence([seed, graph_index, 20]))
    covariates = generator.normal(size=(count,2)).astype('<f8')
    blocks = blocks_from_graph(edges, count)
    graph = adjacency(edges,count)
    degree = np.asarray(graph.sum(axis=1)).ravel()
    log_degree = np.log1p(degree)
    log_degree -= log_degree.mean()
    baseline = .3*covariates[:,0]-.2*covariates[:,1]+.2*log_degree
    direct = 1+.4*covariates[:,0]
    treatment_values = []
    for assignment in range(2):
        rng = np.random.default_rng(np.random.SeedSequence([seed,graph_index,30,assignment]))
        for attempt in range(64):
            treatment = rng.binomial(1,.5,size=count) if assignment == 0 else rng.binomial(1,.5,size=16)[blocks]
            if 0 < treatment.sum() < count:
                break
        else:
            raise RuntimeError('empty assignment arms')
        treatment_values.append(treatment.astype('|u1'))
    rng = np.random.default_rng(np.random.SeedSequence([seed,graph_index,40]))
    noise = .5*rng.normal(size=count)+.3*rng.normal(size=16)[blocks]
    def response(treatment, mechanism):
        exposure = (graph @ treatment)/np.maximum(degree,1)
        two_hop = (graph @ exposure)/np.maximum(degree,1)
        if mechanism == 0:
            spillover = np.zeros(count)
        elif mechanism == 1:
            spillover = exposure
        elif mechanism == 2:
            spillover = 1.5*(exposure>.75)
        else:
            spillover = .8*two_hop+.7*treatment*exposure
        return baseline+direct*treatment+spillover+noise
    treatments, outcomes, truths = [], [], []
    for mechanism in range(4):
        truth = float(np.mean(response(np.ones(count),mechanism)-response(np.zeros(count),mechanism)))
        for assignment in range(2):
            treatment = treatment_values[assignment]
            treatments.append(treatment)
            outcomes.append(response(treatment,mechanism))
            truths.append(truth)
    return {'x':covariates, 'blocks':blocks, 'z':np.asarray(treatments,dtype='|u1'),
            'y':np.asarray(outcomes,dtype='<f8'), 'truth':np.asarray(truths,dtype='<f8')}


def structural_response(edges, covariates, treatment, mechanism):
    graph = adjacency(edges, len(treatment))
    degree = np.asarray(graph.sum(axis=1)).ravel()
    exposure = graph @ treatment / np.maximum(degree, 1)
    two_hop = graph @ exposure / np.maximum(degree, 1)
    spillover = (np.zeros(len(treatment)), exposure, 1.5 * (exposure > .75),
                 .8 * two_hop + .7 * treatment * exposure)[mechanism]
    return (1 + .4 * covariates[:, 0]) * treatment + spillover


def load_resources(root, smoke):
    manifest = decode_json((root / "manifest.json").read_bytes())
    if manifest["plane"] != PLANE or not manifest["cross_plane_content_audit"]["disjoint"]:
        raise ValueError("invalid split manifest")
    for name, digest in manifest["files"].items():
        path = root / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("resource checksum mismatch")
    public = public_graph(root / "Stanford3.zip") if PLANE == "final" else None
    profiles = manifest["smoke"] if smoke else manifest["production"]
    datasets = {}
    for descriptor in profiles:
        with np.load(root / descriptor["file"], allow_pickle=False) as archive:
            data = {name: archive[name] for name in archive.files}
        edges = data.pop("edges") if "edges" in data else public
        count = len(data["x"])
        if count != descriptor["n"] or topology_hash(edges, count) != descriptor["topology_sha256"]:
            raise ValueError("topology normalization mismatch")
        if examples_hash(data["x"], data["z"], data["y"]) != descriptor["examples_sha256"]:
            raise ValueError("raw example normalization mismatch")
        if data["z"].shape != (8, count) or data["y"].shape != (8, count) or data["truth"].shape != (8,):
            raise ValueError("invalid frozen dataset shape")
        if not np.isfinite(data["truth"]).all() or not np.isfinite(data["x"]).all():
            raise ValueError("nonfinite resource")
        for mechanism in range(4):
            endpoint_truth = float(np.mean(
                structural_response(edges, data["x"], np.ones(count), mechanism)
                - structural_response(edges, data["x"], np.zeros(count), mechanism)))
            if not np.allclose(data["truth"][2*mechanism:2*mechanism+2], endpoint_truth, atol=1e-12, rtol=1e-12):
                raise ValueError("counterfactual target mismatch")
        datasets[(descriptor["seed"], descriptor["graph"])] = dict(data, edges=edges)
    return manifest, datasets


def episode_plan(seeds):
    episodes = []
    for seed in seeds:
        for graph in range(3):
            for mechanism in range(4):
                for design in range(2):
                    episodes.append({"seed": seed, "kind": "primary", "graph": graph,
                                     "cell": mechanism * 2 + design})
        for kind in ("constant", "shift", "permuted"):
            episodes.append({"seed": seed, "kind": kind, "graph": 0, "cell": 0})
    episodes.append({"seed": seeds[0], "kind": "replay", "graph": 0, "cell": 0})
    return episodes


def validated_episode_plan(manifest, protocol, smoke):
    for reduced in (False, True):
        seeds = manifest["seeds"][:1] if reduced else manifest["seeds"]
        expected = [episode["seed"] for episode in episode_plan(seeds)]
        key = "smoke_reset_sequence" if reduced else "reset_sequence"
        declared = protocol[f"{PLANE}_{key}"]
        if manifest[key] != expected or declared != expected:
            raise ValueError("declared reset transcript does not match complete episode plan")
    return episode_plan(manifest["seeds"][:1] if smoke else manifest["seeds"])


def permuted_treatment(treatment, edges, seed):
    generator = np.random.default_rng(np.random.SeedSequence([seed, 777]))
    graph = adjacency(edges, len(treatment))
    original_exposure = graph @ treatment
    for _ in range(64):
        proposal = generator.permutation(treatment)
        if np.count_nonzero(proposal != treatment) >= math.ceil(len(treatment) / 4):
            if np.any(graph @ proposal != original_exposure):
                return proposal
    raise SemanticFailure("vacuous permutation")


def outcome_summary(estimate, bounds, truth):
    error = estimate - truth
    clipped = float(np.clip(error, -100, 100))
    loss = 1. - 1. / (1. + error * error) if abs(error) < 1e150 else 1.
    return {"loss": loss, "squared_error": clipped ** 2, "bias_lower": clipped, "bias_upper": clipped,
            "coverage": float(bounds[0] <= truth <= bounds[1]), "width": bounds[1] - bounds[0],
            "raw_error": error, "clipped": error != clipped}


def make_episode_evaluator(datasets):
    anchors = {}
    def evaluate(episode, call, deadline):
        seed, kind, cell, graph_index = episode["seed"], episode["kind"], episode["cell"], episode["graph"]
        source = datasets[(seed, graph_index)]
        data = {"edges": source["edges"], "x": source["x"], "blocks": source["blocks"],
                "z": source["z"][cell].copy(), "y": source["y"][cell].copy()}
        truth = float(source["truth"][cell])
        if kind == "constant":
            data["y"].fill(2.75)
            truth = 0.
        elif kind == "shift":
            data["y"] += 3.25
        elif kind == "permuted":
            data["z"] = permuted_treatment(data["z"], data["edges"], seed)
            truth = 0.
        methods_end = deadline
        with bounded_work(min(deadline, time.monotonic() + 1.)):
            design, difference, exposure = regression_arrays(data["edges"], data["x"], data["z"])
        baseline_results = {}
        episode["baseline_results"] = baseline_results
        baseline_recipes = [("mean_difference", 0, 0.), ("no_interference_ols", 7, 0.),
                            ("linear_exposure_ols", 8, 0.), ("augmented_ridge", 12, .1),
                            ("constant_zero", 0, 0.), ("copy_mean", 0, 0.)]
        for method_index, (name, width, ridge) in enumerate(baseline_recipes):
            method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=methods_end,
                                                      methods_remaining=6 - method_index,
                                                      work_seconds=METHOD_WORK, cleanup_seconds=0.)
            with bounded_work(method_deadline, baseline=True):
                if width:
                    result, _ = fit_summary(design[:, :width], data["y"], difference[:width], data["blocks"], ridge)
                elif name == "mean_difference":
                    treated = data["z"].astype(bool)
                    if not treated.any() or treated.all():
                        raise RequiredBaselineFailure("baseline_result_failure")
                    weights = treated / treated.sum() - (~treated) / (~treated).sum()
                    estimate = float(weights @ data["y"])
                    scores = np.bincount(data["blocks"], weights=weights * (data["y"] - data["y"].mean()))
                    radius = 1.959963984540054 * float(np.linalg.norm(scores))
                    result = {"gate": estimate, "interval": [float(np.clip(estimate-radius,-100,100)),
                                                            float(np.clip(estimate+radius,-100,100))]}
                else:
                    estimate = 0. if name == "constant_zero" else float(data["y"].mean())
                    result = {"gate": estimate, "interval": [float(np.clip(estimate,-100,100))] * 2}
                if not math.isfinite(result["gate"]):
                    raise RequiredBaselineFailure("baseline_result_failure")
                baseline_results[name] = dict(result, **outcome_summary(result["gate"], result["interval"], truth))
        transport_deadline = min(deadline, time.monotonic() + 1.)
        for message in input_messages(data):
            response = call(message, timeout=transport_deadline - time.monotonic())
            if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
                raise ProtocolFailure("upload acknowledgement schema")
        candidate_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=methods_end,
                                                     methods_remaining=0, work_seconds=METHOD_WORK, cleanup_seconds=0.)
        response = call({"op": "fit"}, timeout=candidate_deadline - time.monotonic())
        released = call({"op": "release"})
        if type(released) is not dict or set(released) != {"ok"} or released["ok"] is not True:
            raise ProtocolFailure("release acknowledgement schema")
        with bounded_work(min(deadline, time.monotonic() + METHOD_WORK)):
            checked = check_fit(response, design, data["y"], difference, data["blocks"])
        if kind == "primary" and graph_index == 0 and cell == 0:
            anchors[seed] = checked
        if kind == "constant" and abs(checked["gate"]) > 2e-6:
            raise SemanticFailure("constant control nonzero")
        if kind in ("shift", "replay"):
            if seed not in anchors:
                raise SemanticFailure("missing matched control anchor")
            anchor = anchors[seed]
            if not math.isclose(checked["gate"], anchor["gate"], abs_tol=2e-6, rel_tol=2e-6):
                raise SemanticFailure("matched control differs")
            if kind == "replay":
                if (checked["basis"] != anchor["basis"] or checked["ridge"] != anchor["ridge"]
                        or not np.allclose(checked["coefficients"], anchor["coefficients"], atol=2e-6, rtol=2e-6)):
                    raise SemanticFailure("reset replay differs")
            error = checked["gate"] - anchor["gate"]
            control_loss = 0. if kind == "replay" else error ** 2 / (1 + error ** 2)
        else:
            error = checked["gate"] - truth
            control_loss = error ** 2 / (1 + error ** 2)
        summary = outcome_summary(checked["gate"], checked["interval"], truth)
        if kind != "primary":
            summary["loss"] = control_loss
        support = {"exposure_min": float(exposure.min()), "exposure_max": float(exposure.max()),
                   "endpoint_distance": float(min(exposure.min(), 1-exposure.max())),
                   "condition_number": float(min(np.linalg.cond(design), 1e100)),
                   "block_count": int(len(np.unique(data["blocks"]))) }
        solution = {"kind": kind, "graph": graph_index, "cell": cell, "truth": truth,
                    "candidate": checked, "baselines": baseline_results, "support": support,
                    "raw_error": summary["raw_error"], "clipped": summary["clipped"]}
        return dict(summary, valid=True, duration=0., solution=solution)
    def guarded_evaluate(episode, call, deadline):
        with bounded_work(deadline):
            return evaluate(episode, call, deadline)
    return guarded_evaluate


def aggregate(episodes, outcomes, seeds, complete):
    primary = [value for episode, value in zip(episodes, outcomes) if episode["kind"] == "primary"]
    controls = []
    for kind in ("constant", "shift", "permuted", "replay"):
        values = [value["loss"] for episode, value in zip(episodes, outcomes) if episode["kind"] == kind]
        controls.append(sum(values) / len(values))
    control_loss = sum(controls) / 4
    mean = lambda key: sum(value[key] for value in primary) / len(primary)
    valid = complete and all(value["valid"] for value in outcomes)
    metrics = {"combined_score": .9 * (1 - mean("loss")) + .1 * (1 - control_loss),
               "gate_rmse": math.sqrt(mean("squared_error")), "gate_bias_lower": mean("bias_lower"),
               "gate_bias_upper": mean("bias_upper"), "coverage_95": mean("coverage"),
               "mean_interval_width": mean("width"),
               "failure_rate": sum(not value["valid"] for value in outcomes) / len(outcomes),
               "control_loss": control_loss, "correct": int(valid)}
    records = []
    for seed in seeds:
        selected = [(episode, value) for episode, value in zip(episodes, outcomes) if episode["seed"] == seed]
        cases = []
        for episode, value in selected:
            cases.append(value["solution"] if value["solution"] is not None else
                         {"kind": episode["kind"], "graph": episode["graph"], "cell": episode["cell"],
                          "failed": True, "retained_loss": 1., "bias_lower": -100., "bias_upper": 100.,
                          "baselines": episode.get("baseline_results", {})})
        seed_primary = [value for episode, value in selected if episode["kind"] == "primary"]
        seed_controls = [value["loss"] for episode, value in selected
                         if episode["kind"] in ("constant", "shift", "permuted")]
        seed_score = .9 * (1 - sum(value["loss"] for value in seed_primary) / 24)
        seed_score += .1 * (1 - (sum(seed_controls) + controls[3]) / 4)
        records.append({"seed": seed, "score": seed_score,
                        "correct": all(value["valid"] for _, value in selected),
                        "duration_seconds": sum(value["duration"] for _, value in selected),
                        "solution": {"cases": cases}})
    bootstrap = np.random.default_rng(109)
    comparisons = {}
    for name in ("mean_difference", "no_interference_ols", "linear_exposure_ols", "augmented_ridge", "constant_zero", "copy_mean"):
        paired = []
        for seed in seeds:
            differences = []
            for episode, value in zip(episodes, outcomes):
                if episode["seed"] == seed and episode["kind"] == "primary":
                    baseline_loss = episode.get("baseline_results", {}).get(name, {"loss": 1.})["loss"]
                    differences.append(value["loss"] - baseline_loss)
            paired.append(sum(differences) / 24)
        samples = bootstrap.choice(paired, size=(500, len(seeds)), replace=True).mean(axis=1)
        comparisons[name] = {"candidate_minus_baseline_loss": float(np.mean(paired)),
                             "seed_bootstrap_95": np.quantile(samples, [.025,.975]).tolist(),
                             "independent_seed_count": len(seeds)}
    records[0]["solution"]["paired_monte_carlo"] = comparisons
    return metrics, valid, {"schema_version": 1, "episodes": records}


def write_results(directory, metrics, correct, feasible, evidence=None):
    directory.mkdir(parents=True, exist_ok=True)
    if set(metrics) != set(METRIC_NAMES) or not all(type(value) in (int,float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError("invalid metrics")
    (directory / "metrics.json").write_bytes(bounded_json_line(metrics))
    (directory / "correct.json").write_bytes(bounded_json_line({"correct": bool(correct)}))
    if evidence is not None:
        (directory / "evaluation_evidence.json").write_bytes(bounded_json_line(evidence, 16 * 1024**2))
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        (directory / "qualification.json").write_bytes(bounded_json_line({"schema_version": 1, "feasible": bool(feasible)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    arguments = parser.parse_args()
    os.sched_setaffinity(0, NATIVE_ALLOWED_CPUS[:2])
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    root = Path(os.environ.get("TASK_SOURCE_DIR", Path(__file__).resolve().parent)) / "resources" / PLANE
    hard_deadline = STARTED + WALL - STARTUP_ALLOWANCE
    manifest, datasets = load_resources(root, smoke)
    seeds = manifest["seeds"][:1] if smoke else manifest["seeds"]
    contract = decode_json((root.parent.parent / "task_contract.json").read_bytes())
    episodes = validated_episode_plan(manifest, contract["protocol"], smoke)
    reset_key = f"{PLANE}_{'smoke_reset_sequence' if smoke else 'reset_sequence'}"
    declared_resets = contract["protocol"][reset_key]
    counts, lengths = wire_preflight(len(episodes))
    production_calls = sum(manifest["rpc_operation_counts"].values())
    if production_calls != 12 * (27 * len(manifest["seeds"]) + 1):
        raise ValueError("frozen RPC table mismatch")
    if sum(counts.values()) > production_calls or max(lengths) >= WIRE_LIMIT:
        raise ValueError("preflight failed")
    needed = STARTUP_ALLOWANCE + 10 + len(episode_plan(manifest["seeds"])) * (2 + 2.4 + 1 + 7 * METHOD_WORK)
    if needed > WALL:
        raise ValueError("joint method work budget infeasible")
    client = CandidateRPC(arguments.program_path, production_calls)
    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=10., reset_timeout=2., episode_overhead=2.4,
            rpc_cap=5., clock=time.monotonic, rpc=client, evaluate=make_episode_evaluator(datasets),
            worst_case=worst_case, record_failure=record_failure, cleanup=lambda failed: client.close(failed))
    finally:
        client.close()
    if client.reset_transcript != declared_resets:
        complete = False
    metrics, correct, evidence = aggregate(episodes, outcomes, seeds, complete)
    feasible = complete and not smoke and time.monotonic() < hard_deadline
    write_results(Path(arguments.results_dir), metrics, correct, feasible, evidence)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        try:
            failed_metrics = dict(zip(METRIC_NAMES, [0.,100.,-100.,100.,0.,200.,1.,1.,0]))
            if "--results_dir" in sys.argv:
                output = Path(sys.argv[sys.argv.index("--results_dir") + 1])
                write_results(output, failed_metrics, False, False)
        finally:
            category = type(error).__name__[:80]
            message = "sealed evaluator failure" if PLANE == "final" else "evaluator preflight or execution failed"
            print(f"{category}: {message}", file=sys.stderr)
        sys.exit(1)
