"""Evaluator-owned finite-population network interference benchmark.

Frozen protocol: topology/mechanism/design/arm/seed order, then one first-case replay.
Each episode: reset 1, begin 1, upload <=8, fit(commit) 1, predict 1, release 1:
13 maximum calls even if a production input happens to fit one chunk. No state
exports/imports, polls or retries. Search 129*13=1677; final 577*13=7501.
Each scored topology/mechanism/design has equal weight, then equal seed weights.
Actual and permutation estimates are paired; replay is diagnostic, not Monte Carlo.
Candidate score is .8*(1-capped_normalized_MSE)+.15*controls+.05*replay.
Failed primary signed error=+1, loss=1, failed paired contrast=-1, control=0,
replay error=1. Nothing is omitted or renormalized. Normalize by max(1,abs(GATE)).
Controls: constant endpoints yield zero GATE; copy yields naive mean difference;
nonidentity graph permutation must change treatment exposures; no superiority
direction is required; reset/replay must reproduce decoded numeric regression.
Search correct: complete valid auditable regressions, baselines, controls, replay,
split integrity and finite fixed aggregation. Final correct: those same held-out
scientific prerequisites; comparative publication claims additionally require paired
uncertainty and faithful scope/negative-result reporting, not automatic superiority.
This evaluator cannot certify paper novelty, citations, checklist or narrative truth.
Bootstrap resamples complete seed vectors (512 draws); smoke/one seed uses full
bounded uncertainty intervals. No node-iid inference or public-topology replication.
Platform: Linux x86_64 CPython 3.11/3.12, Landlock ABI>=3, libseccomp.so.2 for
native checks; brokered runs use harness isolation. Runtime is entirely offline.
"""
import argparse
import base64
import ctypes
import errno
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
import subprocess
import sys
import tempfile
import time

PLANE = 'final'
WALL_SECONDS = 10800
RPC_BUDGET = 7501
WIRE_LIMIT = 64 * 1024**2
CHUNK_BYTES = 6 * 1024**2
MAX_CHUNKS = 8
METHOD_WORK_SECONDS = 2.5
METHOD_CLEANUP_SECONDS = 1.2
EPISODE_OVERHEAD_SECONDS = 2 * METHOD_CLEANUP_SECONDS + .1
STARTED = time.monotonic()
for variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[variable] = '2'
os.environ.setdefault('MPLCONFIGDIR', '/tmp')
import numpy as np
import networkx as nx
from scipy import sparse


class ProtocolError(RuntimeError):
    pass


class WorkerExit(RuntimeError):
    pass


def bounded_json_line(value):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(encoded) >= WIRE_LIMIT:
        raise ProtocolError('message_size')
    return encoded


def parse_line(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ProtocolError('duplicate_key')
            result[key] = value
        return result
    try:
        value = json.loads(data, object_pairs_hook=pairs,
                           parse_constant=lambda unused: (_ for _ in ()).throw(ProtocolError('nonfinite')))
        bounded_json_line(value)
        return value
    except (ValueError, TypeError, OverflowError, RecursionError) as error:
        raise ProtocolError('malformed_json') from error


def canonical_edges(edges, count):
    edges = np.asarray(edges, dtype='<i4').reshape(-1, 2)
    edges = np.sort(edges, axis=1)
    edges = np.unique(edges[edges[:, 0] != edges[:, 1]], axis=0)
    if len(edges) and (edges.min() < 0 or edges.max() >= count):
        raise ValueError('invalid graph universe')
    return edges.astype('<i4')


def raw_digest(edges, count, *arrays):
    digest = hashlib.sha256()
    digest.update(int(count).to_bytes(8, 'little'))
    for array in (canonical_edges(edges, count),) + arrays:
        array = np.asarray(array)
        digest.update(str(array.shape).encode('ascii'))
        digest.update(array.astype('<i4' if array.dtype.kind in 'iu' else '<f8').tobytes())
    return digest.hexdigest()


def graph_info(edges, count, treatment):
    adjacency = sparse.coo_matrix((np.ones(2 * len(edges)),
        (np.concatenate((edges[:, 0], edges[:, 1])),
         np.concatenate((edges[:, 1], edges[:, 0])))), shape=(count, count)).tocsr()
    degree = np.asarray(adjacency.sum(axis=1)).ravel()
    exposure = adjacency @ treatment / np.maximum(degree, 1)
    second = adjacency @ exposure / np.maximum(degree, 1)
    return degree, exposure, second


def matrices(edges, covariate, treatment):
    count = len(treatment)
    degree, exposure, second = graph_info(edges, count, treatment)
    scaled = degree / max(1, degree.max())
    def matrix(own, neighbor):
        return np.column_stack((np.ones(count), own, neighbor, own * neighbor,
                                neighbor ** 2, covariate, scaled, covariate * own))
    return (matrix(treatment, exposure), matrix(np.zeros(count), np.zeros(count)),
            matrix(np.ones(count), (degree > 0).astype(float)))


def potential(edges, covariate, noise, treatment, mechanism):
    degree, exposure, second = graph_info(edges, len(treatment), treatment)
    heterogeneity = .5 + degree / max(1, degree.max()) + .25 * (covariate > 0)
    base = .3 + .4 * covariate + noise + (.8 + .2 * covariate) * treatment
    if mechanism == 1:
        return base + .6 * exposure
    if mechanism == 2:
        return base + 1.2 * exposure**2 + .7 * treatment * exposure
    if mechanism == 3:
        return base + 1.5 * (second > .55) * heterogeneity
    return base


def permute_edges(edges, treatment, rng):
    original = graph_info(edges, len(treatment), treatment)[1]
    for unused in range(16):
        permutation = rng.permutation(len(treatment))
        changed = canonical_edges(permutation[edges], len(treatment))
        altered = graph_info(changed, len(treatment), treatment)[1]
        if not np.array_equal(permutation, np.arange(len(treatment))) and np.max(np.abs(altered-original)) > .01:
            return changed
    raise ValueError('vacuous permutation')


def baseline_values(payload):
    matrix = np.asarray(payload['matrix'])
    control, treated = np.asarray(payload['control']), np.asarray(payload['treated'])
    outcome, treatment = np.asarray(payload['y']), np.asarray(payload['z'])
    if not np.any(treatment == 0) or not np.any(treatment == 1):
        raise RuntimeError('empty_assignment_arm')
    dim = float(outcome[treatment == 1].mean() - outcome[treatment == 0].mean())
    constant_fit = float(outcome.mean())
    copied_groups = [float(outcome[treatment == group].mean()) for group in (0,1)]
    constant_endpoints = [constant_fit, constant_fit]
    copy_endpoints = [copied_groups[0], copied_groups[1]]
    estimates = {'dim': dim, 'constant': constant_endpoints[1]-constant_endpoints[0],
                 'copy': copy_endpoints[1]-copy_endpoints[0]}
    for name, columns in [('treatment', [0, 1]), ('linear', [0, 1, 2, 5, 6]),
                          ('nonlinear', list(range(8)))]:
        design = matrix[:, columns]
        penalty = np.diag([0.] + [1e-4] * (len(columns)-1))
        coefficient = np.linalg.solve(design.T @ design + penalty, design.T @ outcome)
        estimates[name] = float((treated[columns] - control[columns]) @ coefficient)
    oracle = np.asarray(payload['oracle'])
    coefficient = np.linalg.lstsq(oracle, outcome, rcond=1e-10)[0]
    estimates['oracle'] = float(np.asarray(payload['oracle_delta']) @ coefficient)
    if not all(math.isfinite(value) for value in estimates.values()):
        raise RuntimeError('nonfinite_baseline')
    return estimates


def baseline_payload(edges, covariate, treatment, outcome, mechanism):
    matrix, control, treated = matrices(edges, covariate, treatment)
    zero, one = np.zeros(len(treatment)), np.ones(len(treatment))
    structural = potential(edges, covariate, zero, treatment, mechanism) - .3 - .4*covariate
    low = potential(edges, covariate, zero, zero, mechanism) - .3 - .4*covariate
    high = potential(edges, covariate, zero, one, mechanism) - .3 - .4*covariate
    oracle = np.column_stack((one, covariate, structural))
    return dict(matrix=matrix.tolist(), control=control.mean(axis=0).tolist(),
                treated=treated.mean(axis=0).tolist(), y=outcome.tolist(), z=treatment.tolist(),
                oracle=oracle.tolist(), oracle_delta=[0., 0., float((high-low).mean())])


def require_ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise ProtocolError('invalid_ack')


def audit_prediction(response, edges, covariate, treatment, outcome):
    if type(response) is not dict or set(response) != {'beta', 'ridge', 'endpoints', 'gate'}:
        raise ProtocolError('prediction_schema')
    if type(response['beta']) is not list or len(response['beta']) != 8 or type(response['endpoints']) is not list or len(response['endpoints']) != 2:
        raise ProtocolError('prediction_shape')
    numbers = response['beta'] + response['endpoints'] + [response['ridge'], response['gate']]
    if any(type(value) not in (int, float) or not math.isfinite(value) or abs(value) > 1e12 for value in numbers):
        raise ProtocolError('prediction_numeric')
    ridge = response['ridge']
    if not 0 <= ridge <= 1e6:
        raise ProtocolError('ridge_range')
    coefficient = np.asarray(response['beta'])
    matrix, control, treated = matrices(edges, covariate, treatment)
    residual = matrix.T @ (matrix @ coefficient-outcome) + ridge*np.r_[0., coefficient[1:]]
    tolerance = 1e-6 * max(1., float(np.linalg.norm(matrix.T @ outcome)))
    if np.linalg.norm(residual) > tolerance:
        raise ProtocolError('regression_stationarity')
    endpoints = np.array([control.mean(axis=0) @ coefficient, treated.mean(axis=0) @ coefficient])
    if not np.allclose(response['endpoints'], endpoints, atol=1e-7, rtol=1e-7) or not math.isclose(response['gate'], float(endpoints[1]-endpoints[0]), abs_tol=1e-7, rel_tol=1e-7):
        raise ProtocolError('endpoint_reconstruction')
    return float(response['gate'])


def candidate_requests(edges, covariate, treatment, outcome):
    arrays = [edges.astype('<i4'), covariate.astype('<f8'), treatment.astype('<f8'), outcome.astype('<f8')]
    payload = b''.join(array.tobytes() for array in arrays)
    chunks = math.ceil(len(payload)/CHUNK_BYTES)
    if not 1 <= chunks <= MAX_CHUNKS or len(payload) > 48*1024**2:
        raise ValueError('input_transfer_exceeds_bound')
    descriptors = [dict(name=name, dtype=array.dtype.str, shape=list(array.shape))
                   for name, array in zip(['edges', 'x', 'z', 'y'], arrays)]
    yield dict(op='begin', n=len(treatment), edges=len(edges), bytes=len(payload), chunks=chunks,
               encoding='base64', byte_order='little', arrays=descriptors)
    for index in range(chunks):
        yield dict(op='upload', index=index,
                   data=base64.b64encode(payload[index*CHUNK_BYTES:(index+1)*CHUNK_BYTES]).decode('ascii'))
    yield {'op': 'fit'}

class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category, exit_status=None):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        self.exit_status = (exit_status if type(exit_status) is int
                            and -(2**31) <= exit_status < 2**31 else None)
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
            failure = {"component": "baseline", "category": context.category,
                       "operation": "baseline_worker",
                       "exception_type": bounded_failure_name(type(context).__name__.lower(), "runtimeerror")}
            if context.exit_status is not None:
                failure["worker_exit_status"] = context.exit_status
            return failure
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

def candidate_subprocess_settings(parent_environment):
    import sys

    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
    environment = {
        name: parent_environment[name]
        for name in runtime_names
        if name in parent_environment
    }
    environment.update(
        HOME="/nonexistent",
        PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONUNBUFFERED="1",
    )
    return parent_environment.get("TASK_PYTHON", sys.executable), environment

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

def cpu_limit_seconds(wall_seconds, allowed_threads):
    import math
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)

NATIVE_RUNNER = r'''
import base64, ctypes, errno, importlib.util, json, os, resource, sys
class Ruleset(ctypes.Structure):
    _fields_ = [('handled_access_fs', ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int)]
libc = ctypes.CDLL(None, use_errno=True)
if libc.syscall(444, 0, 0, 1) < 3:
    raise RuntimeError('landlock_unavailable')
handled = (1 << 15) - 1
ruleset = Ruleset(handled)
descriptor = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
if descriptor < 0:
    raise RuntimeError('landlock_setup')
read_access = (1 << 0) | (1 << 2) | (1 << 3)
roots = ['/usr', '/lib', '/lib64', '/bin', sys.prefix, sys.base_prefix]
roots += ['/etc/ld.so.cache', '/dev/null', '/dev/urandom', sys.argv[2]]
for path in dict.fromkeys(roots):
    if not os.path.exists(path):
        continue
    parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
    access = handled if path == sys.argv[2] else read_access
    if not os.path.isdir(path):
        access &= ~((1 << 3) | (1 << 4) | (1 << 5) | (1 << 6) | (1 << 7) | (1 << 8) | (1 << 9) | (1 << 10) | (1 << 11) | (1 << 12) | (1 << 13))
    rule = PathRule(access, parent)
    if libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0) < 0:
        raise RuntimeError('landlock_rule')
    os.close(parent)
if libc.prctl(38, 1, 0, 0, 0) or libc.syscall(446, descriptor, 0):
    raise RuntimeError('landlock_enforce')
os.close(descriptor)
seccomp = ctypes.CDLL('libseccomp.so.2')
seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
seccomp.seccomp_init.restype = ctypes.c_void_p
seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
context = seccomp.seccomp_init(0x7fff0000)
for name in ('socket','socketpair','connect','bind','listen','accept','accept4','sendto','sendmsg',
             'ptrace','process_vm_readv','process_vm_writev','mount','umount2','unshare','setns',
             'kill','tkill','tgkill','execve','execveat','fork','vfork','setsid','setpgid','sched_setaffinity'):
    number = seccomp.seccomp_syscall_resolve_name(name.encode())
    if number >= 0 and seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM, number, 0):
        raise RuntimeError('seccomp_rule')
if seccomp.seccomp_load(context):
    raise RuntimeError('seccomp_enforce')
seccomp.seccomp_release(context)
spec = importlib.util.spec_from_file_location('candidate', sys.argv[1])
candidate = importlib.util.module_from_spec(spec)
sys.path.insert(0, os.path.dirname(sys.argv[1]))
spec.loader.exec_module(candidate)
for line in sys.stdin.buffer:
    if len(line) >= 64*1024**2:
        raise ValueError('message_size')
    response = candidate.handle(json.loads(line))
    encoded = json.dumps(response, allow_nan=False, separators=(',', ':')).encode() + b'\n'
    if len(encoded) >= 64*1024**2:
        raise ValueError('message_size')
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


def child_limits():
    resource.setrlimit(resource.RLIMIT_AS, (8*1024**3, 8*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit_seconds(WALL_SECONDS, 2),)*2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (64*1024**2,)*2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    available = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, available[:2])


class ProcessChannel:
    def __init__(self, command, environment, cwd):
        self.process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=environment, cwd=cwd, shell=False,
            start_new_session=True, preexec_fn=child_limits)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        self.closed = False
        self.buffer = bytearray()
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def exchange(self, request, deadline):
        encoded = bounded_json_line(request)
        offset = 0
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while offset < len(encoded):
                remaining = deadline-time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError()
                try:
                    offset += os.write(self.process.stdin.fileno(), encoded[offset:offset+65536])
                except (BrokenPipeError, OSError) as error:
                    raise WorkerExit() from error
            selector.unregister(self.process.stdin)
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                remaining = deadline-time.monotonic()
                if remaining <= 0 or not selector.select(remaining):
                    raise TimeoutError()
                try:
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise WorkerExit()
                self.buffer.extend(chunk)
                if len(self.buffer) >= WIRE_LIMIT:
                    raise ProtocolError('response_size')
            line, tail = self.buffer.split(b'\n', 1)
            self.buffer = bytearray(tail)
            if time.monotonic() > deadline:
                raise TimeoutError()
            return parse_line(line)

    def close(self, failed=False):
        if self.closed:
            return
        self.closed = True
        process = self.process
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=.05)
        except subprocess.TimeoutExpired:
            pass
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=.05)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('worker_reap_unresolved') from error
        finally:
            process.stdin.close()
            process.stdout.close()
            snapshot = self.capture.close()
            repair = os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
            if failed and PLANE == 'search' and repair:
                if snapshot['stderr']:
                    sys.stderr.write(snapshot['stderr'])
                metadata = {key: value for key, value in snapshot.items() if key != 'stderr'}
                print('worker_capture '+json.dumps(metadata, separators=(',', ':')), file=sys.stderr)


class CandidateRPC:
    def __init__(self, path):
        self.calls = 0
        self.worker = None
        self.directory = None
        self.proxy = None
        self.path = path
        broker_path = str(path) == '/broker-code/candidate_proxy.py'
        socket_present = bool(os.environ.get('AGENTIC_CANDIDATE_SOCKET'))
        if broker_path != socket_present:
            raise RuntimeError('broker_requires_both_signals')
        if broker_path and socket_present:
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.directory = tempfile.TemporaryDirectory(prefix='gate-candidate-')
            self.root = Path(self.directory.name)
            shutil.copytree(Path(path).absolute().parent, self.root/'src', symlinks=True)
            self.entrypoint = self.root/'src'/Path(path).name
            self.interpreter, self.environment = candidate_subprocess_settings(os.environ)
            for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
                self.environment[name] = '2'

    def call(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolError('rpc_budget')
        bounded_json_line(request)
        deadline = time.monotonic()+timeout
        if self.proxy is not None:
            def expired(unused_signal, unused_frame):
                raise TimeoutError()
            previous = signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                response = self.proxy(request)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
            bounded_json_line(response)
            return response
        if request['op'] == 'reset':
            if self.worker is not None:
                self.worker.close()
            self.worker = ProcessChannel([self.interpreter, '-I', '-u', '-c', NATIVE_RUNNER,
                                          str(self.entrypoint), str(self.root)], self.environment, self.root)
        if self.worker is None:
            raise ProtocolError('reset_required')
        return self.worker.exchange(request, deadline)

    def cancel(self, failed=False):
        if self.worker is not None:
            self.worker.close(failed)
            self.worker = None

    def close(self):
        self.cancel()
        if self.directory is not None:
            self.directory.cleanup()


def record_failure(failure):
    if PLANE == 'search':
        component = bounded_failure_name(failure.get('component'), 'candidate')
        category = bounded_failure_name(failure.get('category'), 'protocol_failure')
        operation = bounded_failure_name(failure.get('operation'), 'unknown')
        status = failure.get('worker_exit_status')
        metadata = f' worker_exit_status={status}' if type(status) is int and -(2**31) <= status < 2**31 else ''
        exception_type = bounded_failure_name(failure.get('exception_type'), 'unknown')
        try:
            print(f'episode_failure component={component} category={category} operation={operation}'
                  f' exception_type={exception_type}{metadata}', file=sys.stderr)
        except OSError:
            pass


def required_baseline(payload, deadline):
    interpreter, environment = candidate_subprocess_settings(os.environ)
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[name] = '2'
    repair = PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')
    command = [interpreter, '-I', '-u', str(Path(__file__).resolve()), '--baseline-worker']
    if repair:
        command.append('--repair')
    worker = ProcessChannel(command, environment, '/tmp')
    failed = False
    primary = None
    try:
        try:
            result = worker.exchange(payload, deadline)
            remaining = deadline-time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            worker.process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as error:
            raise TimeoutError() from error
        except WorkerExit as error:
            try:
                status = worker.process.wait(timeout=max(0., deadline-time.monotonic()))
            except subprocess.TimeoutExpired as wait_error:
                raise TimeoutError() from wait_error
            category = 'baseline_signal' if status < 0 else 'baseline_exit'
            raise RequiredBaselineFailure(category, status) from error
        status = worker.process.returncode
        if status != 0:
            raise RequiredBaselineFailure('baseline_signal' if status < 0 else 'baseline_exit', status)
        if type(result) is not dict or set(result) != {'values','work_seconds'} or type(result['work_seconds']) not in (int,float) or not math.isfinite(result['work_seconds']) or result['work_seconds']<=0:
            raise RequiredBaselineFailure('baseline_result_failure')
        values = result['values']
        if type(values) is not dict or set(values) != {'dim','constant','copy','treatment','linear','nonlinear','oracle'} or any(type(value) not in (int,float) or not math.isfinite(value) for value in values.values()):
            raise RequiredBaselineFailure('baseline_result_failure')
        return values, float(result['work_seconds'])
    except TimeoutError as error:
        failed = True
        primary = RequiredBaselineFailure('baseline_timeout')
        raise primary from error
    except (RequiredBaselineFailure, ProtocolError) as error:
        failed = True
        primary = error if isinstance(error, RequiredBaselineFailure) else RequiredBaselineFailure('baseline_result_failure')
        raise primary from error
    except Exception as error:
        failed = True
        primary = error
        raise
    finally:
        try:
            worker.close(failed)
        except RuntimeError as cleanup_error:
            cleanup = dict(component='baseline', category='baseline_cleanup_failure',
                           operation='baseline_worker_cleanup',
                           exception_type=bounded_failure_name(type(cleanup_error).__name__.lower(), 'runtimeerror'))
            if primary is None:
                raise RequiredBaselineFailure('baseline_cleanup_failure', worker.process.returncode) from cleanup_error
            primary.cleanup_failures = [cleanup]


def generate_instance(topology, seed, count, public_edges=None):
    rng=np.random.default_rng(seed)
    if topology==0:
        sizes=[count//4]*3+[count-3*(count//4)]
        probabilities=np.full((4,4),4./count)
        np.fill_diagonal(probabilities,36./count)
        graph=nx.stochastic_block_model(sizes, probabilities.tolist(), seed=seed)
        edges=canonical_edges(list(graph.edges()),count)
    elif topology==1:
        graph=nx.barabasi_albert_graph(count,6,seed=seed)
        edges=canonical_edges(list(graph.edges()),count)
    else:
        edges=canonical_edges(public_edges,count)
        graph=nx.Graph()
        graph.add_nodes_from(range(count))
        graph.add_edges_from(edges.tolist())
    covariate=rng.uniform(-1.,1.,count).astype('<f8')
    noise=rng.uniform(-.2,.2,count).astype('<f8')
    bernoulli=rng.binomial(1,.5,count).astype('<f8')
    visited=set()
    bfs=[]
    for node in sorted(graph):
        if node in visited:
            continue
        component=list(nx.bfs_tree(graph,node))
        visited.update(component)
        bfs.extend(component)
    cluster=np.empty(count,dtype='<f8')
    cluster_size=max(8,int(round(math.sqrt(count))))
    for start in range(0,count,cluster_size):
        cluster[np.asarray(bfs[start:start+cluster_size])]=rng.binomial(1,.5)
    assignments=np.array([bernoulli,cluster],dtype='<f8')
    outcomes=np.array([[potential(edges,covariate,noise,treatment,mechanism)
        for treatment in assignments] for mechanism in range(4)],dtype='<f8')
    truth=np.array([(potential(edges,covariate,noise,np.ones(count),mechanism)-
                     potential(edges,covariate,noise,np.zeros(count),mechanism)).mean()
                    for mechanism in range(4)],dtype='<f8')
    return dict(edges=edges,x=covariate,noise=noise,z=assignments,outcomes=outcomes,truth=truth,
                permuted0=permute_edges(edges,assignments[0],rng),
                permuted1=permute_edges(edges,assignments[1],rng))

def read_public_archive(path):
    import zipfile
    archive = path.read_bytes()
    if hashlib.sha256(archive).hexdigest() != 'b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d':
        raise ValueError('public_archive_integrity')
    with zipfile.ZipFile(path) as bundle:
        member = next(name for name in bundle.namelist() if name.endswith('socfb-Stanford3.mtx'))
        lines = bundle.read(member).decode('ascii').splitlines()
    records = [line for line in lines if line and not line.startswith('%')]
    count, columns, entries = map(int, records[0].split())
    if (count, columns, entries) != (11586,11586,568309) or len(records)-1 != entries:
        raise ValueError('public_graph_dimensions')
    edges = np.array([list(map(int, line.split()[:2])) for line in records[1:]], dtype='<i4')-1
    normalized = canonical_edges(edges, count)
    if len(normalized) != 568309:
        raise ValueError('public_graph_edge_convention')
    return normalized


class DataStore:
    def __init__(self, root, smoke):
        self.root = root
        self.manifest = json.loads((root/'manifest.json').read_text())
        self.smoke = smoke
        self.profile = self.manifest['smoke' if smoke else 'production']
        self.cache = {}
        self.opposite_graphs = set(self.manifest['opposite_graph_hashes'])
        self.opposite_examples = set(self.manifest['opposite_example_hashes'])
        if PLANE == 'final':
            read_public_archive(root/'socfb-Stanford3.zip')

    def instance(self, episode):
        key = f"{episode['topology']}-{episode['seed']}"
        entry = self.profile['instances'][key]
        if key not in self.cache:
            path = self.root/entry['file']
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('raw_instance_integrity')
            with np.load(path, allow_pickle=False) as archive:
                data = {name: archive[name] for name in archive.files}
            count = len(data['x'])
            graph_hash = raw_digest(data['edges'], count)
            permuted_hashes=[raw_digest(data[f'permuted{design}'],count) for design in range(2)]
            if permuted_hashes!=entry['permuted_graph_hashes'] or any(digest in self.opposite_graphs for digest in permuted_hashes):
                raise ValueError('normalized_permutation_graph_overlap_or_corruption')
            if graph_hash != entry['graph_hash'] or graph_hash in self.opposite_graphs:
                raise ValueError('normalized_graph_overlap_or_corruption')
            for mechanism in range(4):
                for design in range(2):
                    for arm in range(2):
                        edges = data['edges'] if arm == 0 else data[f'permuted{design}']
                        digest = raw_digest(edges, count, data['x'], data['z'][design], data['outcomes'][mechanism,design])
                        if digest != entry['example_hashes'][f'{mechanism}-{design}-{arm}'] or digest in self.opposite_examples:
                            raise ValueError('normalized_example_overlap_or_corruption')
            self.cache[key] = data
        return self.cache[key]


def episodes_for(profile):
    episodes = []
    for topology in range(profile['topologies']):
        for mechanism in range(4):
            for design in range(2):
                for arm in range(2):
                    for seed in profile['seeds']:
                        episodes.append(dict(topology=topology, mechanism=mechanism, design=design, arm=arm, seed=seed, replay=False))
    episodes.append(dict(episodes[0], replay=True))
    return episodes


def worst_case(episode):
    return dict(error=1., loss=1., complete=False, valid=False, truth=None,
                estimate=None, baselines=None, prediction=None, duration=0., support=None)


def evaluate_episode(episode, data, call, deadline):
    covariate = data['x']
    treatment = data['z'][episode['design']]
    outcome = data['outcomes'][episode['mechanism'], episode['design']]
    edges = data['edges'] if episode['arm'] == 0 else data[f"permuted{episode['design']}"]
    true_exposure = graph_info(data['edges'], len(covariate), treatment)[1]
    changed_exposure = graph_info(data[f"permuted{episode['design']}"], len(covariate), treatment)[1]
    if np.max(np.abs(changed_exposure-true_exposure)) <= .01:
        raise ProtocolError('vacuous_permutation')
    payload = baseline_payload(data['edges'], covariate, treatment, outcome, episode['mechanism'])
    baseline_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
        methods_remaining=1, work_seconds=METHOD_WORK_SECONDS, cleanup_seconds=METHOD_CLEANUP_SECONDS)
    baseline_started = time.monotonic()
    baselines, productive_baseline_seconds = required_baseline(payload, baseline_deadline)
    baseline_duration = time.monotonic()-baseline_started
    candidate_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
        methods_remaining=0, work_seconds=METHOD_WORK_SECONDS, cleanup_seconds=METHOD_CLEANUP_SECONDS)
    def bounded_call(request):
        if time.monotonic() >= candidate_deadline:
            raise TimeoutError()
        return call(request, candidate_deadline)
    for request in candidate_requests(edges, covariate, treatment, outcome):
        require_ack(bounded_call(request))
    response = bounded_call({'op': 'predict'})
    estimate = audit_prediction(response, edges, covariate, treatment, outcome)
    require_ack(bounded_call({'op': 'release'}))
    truth = float(data['truth'][episode['mechanism']])
    error = float(np.clip((estimate-truth)/max(1.,abs(truth)), -1., 1.))
    matrix = matrices(edges, covariate, treatment)[0]
    support = dict(exposure_min=float(matrix[:,2].min()), exposure_max=float(matrix[:,2].max()),
                   condition_number=float(min(1e12, np.linalg.cond(matrix))),
                   endpoint_distance=float(max(0., 1.-matrix[:,2].max(), matrix[:,2].min())))
    return dict(error=error, loss=error**2, complete=True, valid=True, truth=truth,
                estimate=estimate, baselines=baselines, prediction=response, duration=0.,
                support=support, baseline_duration=baseline_duration,
                productive_baseline_seconds=productive_baseline_seconds)


def schedule(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
             rpc_cap, clock, rpc, evaluate, cancel, record):
    candidate_deadline = hard_deadline-finish_reserve
    reset_slot = reset_timeout+episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock()+len(episodes)*reset_slot > candidate_deadline:
        raise TimeoutError('insufficient_reset_reservations')
    complete = True
    baseline_unavailable = None
    for index, episode in enumerate(episodes):
        remaining = len(episodes)-index-1
        episode_deadline = candidate_deadline-remaining*reset_slot
        work_deadline = episode_deadline-episode_overhead
        operation = 'reset'
        primary_failure = None
        failures = []
        def retain_failure(failure):
            failures.append(failure)
            record(failure)
        started = clock()
        def call(request, method_deadline):
            nonlocal operation, primary_failure
            operation = request['op']
            try:
                timeout = min(rpc_cap, method_deadline-clock(), work_deadline-clock())
                if timeout <= 0:
                    raise TimeoutError()
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError, WorkerExit) as error:
                if primary_failure is None:
                    if isinstance(error, ProtocolError):
                        primary_failure = dict(component='candidate', category='malformed_response', operation=operation)
                    elif isinstance(error, WorkerExit):
                        primary_failure = dict(component='candidate', category='candidate_exit', operation=operation)
                    else:
                        primary_failure = describe_episode_failure(error, operation)
                raise
        failed = False
        primary = None
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline-clock())
            if timeout <= 0:
                raise TimeoutError()
            require_reset_ack(rpc({'op':'reset','seed':episode['seed']}, timeout=timeout))
            if baseline_unavailable is not None:
                raise RequiredBaselineFailure(baseline_unavailable)
            value = evaluate(episode, call, work_deadline)
            if clock() > work_deadline:
                raise TimeoutError()
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError, WorkerExit) as error:
            primary = error
            if isinstance(error, RequiredBaselineFailure):
                baseline_unavailable = error.category
            failed = True
            complete = False
            if primary_failure is None:
                if isinstance(error, ProtocolError):
                    primary_failure = dict(component='candidate', category='protocol_failure', operation=operation)
                elif isinstance(error, WorkerExit):
                    primary_failure = dict(component='candidate', category='candidate_exit', operation=operation)
                else:
                    primary_failure = describe_episode_failure(error, operation)
            retain_failure(primary_failure)
            for cleanup in getattr(error, 'cleanup_failures', []):
                retain_failure(cleanup)
        finally:
            try:
                cancel(failed=failed)
            except RuntimeError as cleanup_error:
                complete = False
                retain_failure(dict(component='candidate', category='candidate_cleanup_failure',
                    operation='cancel',
                    exception_type=bounded_failure_name(type(cleanup_error).__name__.lower(), 'runtimeerror')))
                outcomes[index] = worst_case(episode)
            outcomes[index]['duration'] = max(0.,clock()-started)
        if clock() > episode_deadline:
            complete = False
            retain_failure(dict(component='evaluator', category='cleanup_deadline_exceeded', operation='cleanup'))
            outcomes[index] = dict(worst_case(episode), duration=max(0.,clock()-started))
        outcomes[index]['failures'] = failures
    return outcomes, complete


def aggregate(episodes, outcomes, seeds):
    primary = [(episode, outcome) for episode,outcome in zip(episodes,outcomes) if not episode['replay'] and episode['arm']==0]
    lookup = {(episode['topology'],episode['mechanism'],episode['design'],episode['arm'],episode['seed']): outcome
              for episode,outcome in zip(episodes[:-1],outcomes[:-1])}
    seed_errors = []
    seed_losses = []
    controls = []
    gains = []
    gaps = []
    for seed in seeds:
        selected = [(episode,outcome) for episode,outcome in primary if episode['seed']==seed]
        seed_errors.append([outcome['error'] for episode,outcome in selected])
        seed_losses.append([outcome['loss'] for episode,outcome in selected])
        for episode, outcome in selected:
            partner = lookup[(episode['topology'],episode['mechanism'],episode['design'],1,seed)]
            pair_valid = outcome['valid'] and partner['valid']
            if pair_valid:
                baseline = outcome['baselines']
                constant_ok = baseline['constant']==0.
                copy_ok = math.isclose(baseline['copy'], baseline['dim'], abs_tol=1e-12)
                controls.append((1.+float(constant_ok)+float(copy_ok))/3.)
                scale = max(1.,abs(outcome['truth']))
                dim_error = float(np.clip((baseline['dim']-outcome['truth'])/scale,-1.,1.))
                gains.append((dim_error**2,outcome['loss']))
                gaps.append((partner['loss'],outcome['loss']))
            else:
                controls.append(0.)
                gains.append(None)
                gaps.append(None)
    errors, losses = np.asarray(seed_errors), np.asarray(seed_losses)
    bias = float(errors.mean())
    rmse = float(np.sqrt(losses.mean()))
    if len(seeds) > 1 and all(outcome['complete'] for episode,outcome in primary):
        bootstrap = np.random.default_rng(123456).integers(0,len(seeds),size=(512,len(seeds)))
        bootstrap_bias = errors[bootstrap].mean(axis=(1,2))
        bootstrap_rmse = np.sqrt(losses[bootstrap].mean(axis=(1,2)))
        bias_interval = np.quantile(bootstrap_bias,[.025,.975]).tolist()
        rmse_interval = np.quantile(bootstrap_rmse,[.025,.975]).tolist()
    else:
        bias_interval,rmse_interval = [-1.,1.],[0.,1.]
    def paired_contrast(values):
        contributions = [-1. if value is None else math.sqrt(value[0])-math.sqrt(value[1]) for value in values]
        return float(sum(contributions)/len(contributions))
    first,last = outcomes[0],outcomes[-1]
    replay_error = 1.
    if first['valid'] and last['valid']:
        left = first['prediction']['beta']+first['prediction']['endpoints']+[first['prediction']['gate'],first['prediction']['ridge']]
        right = last['prediction']['beta']+last['prediction']['endpoints']+[last['prediction']['gate'],last['prediction']['ridge']]
        replay_error = float(min(1.,np.max(np.abs(np.asarray(left)-np.asarray(right)))))
    replay_pass = replay_error <= 1e-8
    control_rate = float(np.mean(controls))
    metrics = dict(combined_score=.8*(1.-float(losses.mean()))+.15*control_rate+.05*float(replay_pass),
        normalized_capped_rmse=rmse,normalized_capped_bias=bias,
        bias_ci_low=float(bias_interval[0]),bias_ci_high=float(bias_interval[1]),
        rmse_ci_low=float(rmse_interval[0]),rmse_ci_high=float(rmse_interval[1]),
        paired_rmse_gain_vs_dim=paired_contrast(gains), permutation_rmse_gap=paired_contrast(gaps),
        control_pass_rate=control_rate,replay_error=replay_error,
        failure_rate=float(np.mean([not outcome['complete'] for outcome in outcomes])))
    if not all(math.isfinite(value) for value in metrics.values()):
        raise ValueError('nonfinite_aggregation')
    correct = all(outcome['valid'] for outcome in outcomes) and control_rate==1. and replay_pass
    records=[]
    for seed_index,seed in enumerate(seeds):
        selected = [(episode,outcome) for episode,outcome in zip(episodes,outcomes) if episode['seed']==seed]
        cases = []
        for episode,outcome in selected:
            cases.append(dict(topology=episode['topology'],mechanism=episode['mechanism'],design=episode['design'],
                arm=episode['arm'],replay=episode['replay'],truth=outcome['truth'],estimate=outcome['estimate'],
                signed_capped_error=outcome['error'],loss=outcome['loss'],valid=outcome['valid'],
                baselines=outcome['baselines'],support=outcome['support'],
                productive_baseline_seconds=outcome.get('productive_baseline_seconds'),
                failures=outcome.get('failures', [])))
        records.append(dict(seed=seed,score=float(1.-np.mean(seed_losses[seed_index])),
            correct=all(outcome['valid'] for episode,outcome in selected) and (replay_pass if seed==seeds[0] else True),
            duration_seconds=float(sum(outcome['duration'] for episode,outcome in selected)),solution={'cases':cases}))
    return metrics,bool(correct),{'schema_version':1,'episodes':records}


def trusted_preflight():
    edges = np.array([[0,1],[1,2],[2,3]],dtype='<i4')
    covariate=np.array([-.4,.1,.2,.7])
    zero,one=np.zeros(4),np.ones(4)
    for mechanism in (0,1):
        low=potential(edges,covariate,zero,zero,mechanism)
        high=potential(edges,covariate,zero,one,mechanism)
        expected=.8+.2*covariate+(0. if mechanism==0 else .6)
        if not np.allclose(high-low,expected):
            raise ValueError('analytic_endpoint_failure')
    treatment=np.array([0.,1.,0.,1.])
    outcome=potential(edges,covariate,zero,treatment,1)
    fixture=baseline_values(baseline_payload(edges,covariate,treatment,outcome,1))
    if fixture['constant']!=0. or fixture['copy']!=fixture['dim']:
        raise ValueError('baseline_fixture_failure')
    counts = {'reset':1,'begin':1,'upload':8,'fit':1,'predict':1,'release':1}
    if sum(counts.values()) != 13:
        raise ValueError('invalid_rpc_table')
    largest = dict(op='upload',index=7,data=base64.b64encode(b'\xff'*CHUNK_BYTES).decode('ascii'))
    begin=dict(op='begin',n=20000,edges=2000000,bytes=48*1024**2,chunks=8,
        encoding='base64',byte_order='little',arrays=[dict(name='edges',dtype='<i4',shape=[2000000,2])]+[
            dict(name=name,dtype='<f8',shape=[20000]) for name in ['x','z','y']])
    requests=[{'op':'reset','seed':2**63-1},begin,largest,{'op':'fit'},{'op':'predict'},{'op':'release'}]
    bound=999999999999.9999
    responses=[{'ok':True},dict(beta=[-bound]*8,ridge=999999.9999999999,endpoints=[-bound,bound],gate=bound),
        {'error':'protocol_failure','message':'x'*256}]
    for value in requests+responses:
        encoded=bounded_json_line({'method':'handle','request':value,'id':2**63-1,
                                  'metadata':{'encoding':'json','schema_version':1,'reserved':'x'*4096}})
        if len(encoded) >= 32*1024**2:
            raise ValueError('payload_target_exceeded')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--program_path',required=True)
    parser.add_argument('--results_dir',required=True)
    arguments=parser.parse_args()
    available=sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0,available[:2])
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,)*2)
    resource.setrlimit(resource.RLIMIT_CPU,(cpu_limit_seconds(WALL_SECONDS,2),)*2)
    root=Path(os.environ.get('TASK_SOURCE_DIR',str(Path(__file__).resolve().parent)))/'resources'/PLANE
    result_dir=Path(arguments.results_dir)
    result_dir.mkdir(parents=True,exist_ok=True)
    smoke=os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1'
    wall=(300 if PLANE == 'search' else 900) if smoke else WALL_SECONDS
    startup_allowance=5 if smoke else 120
    hard_deadline=STARTED+wall-startup_allowance
    finish_reserve=5. if smoke else 20.
    trusted_preflight()
    store=DataStore(root,smoke)
    episodes=episodes_for(store.profile)
    if 13*len(episodes)>RPC_BUDGET:
        raise ValueError('rpc_preflight_failure')
    def budget_profile(episode_count, ceiling, reduced):
        return dict(episode_count=episode_count, method_count=2, wall_seconds=ceiling,
            startup_seconds=5 if reduced else 120, reset_seconds=1.1,
            cleanup_seconds=METHOD_CLEANUP_SECONDS, finish_seconds=5 if reduced else 20,
            work_seconds=METHOD_WORK_SECONDS)
    require_joint_workload_budget(search=budget_profile(129, 1800, False),
                                 final=budget_profile(577, 10800, False))
    require_joint_workload_budget(search=budget_profile(33, 300, True),
                                 final=budget_profile(49, 900, True))
    candidate=CandidateRPC(arguments.program_path)
    complete=False
    outcomes=[worst_case(episode) for episode in episodes]
    outer_error=None
    try:
        outcomes,complete=schedule(episodes,hard_deadline=hard_deadline,finish_reserve=finish_reserve,
            reset_timeout=1.,episode_overhead=EPISODE_OVERHEAD_SECONDS,rpc_cap=3.,clock=time.monotonic,rpc=candidate.call,
            evaluate=lambda episode,call,deadline:evaluate_episode(episode,store.instance(episode),call,deadline),
            cancel=candidate.cancel,record=record_failure)
    except Exception as error:
        outer_error=error
    finally:
        try:
            candidate.close()
        except Exception as error:
            complete=False
            if outer_error is None:
                outer_error=error
    metrics,correct,evidence=aggregate(episodes,outcomes,store.profile['seeds'])
    correct=bool(correct and complete and outer_error is None)
    (result_dir/'metrics.json').write_bytes(bounded_json_line(metrics))
    (result_dir/'correct.json').write_bytes(bounded_json_line({'correct':correct}))
    evidence_bytes=bounded_json_line(evidence)
    if len(evidence_bytes)>16*1024**2:
        raise ValueError('evidence_size')
    (result_dir/'evaluation_evidence.json').write_bytes(evidence_bytes)
    if os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1':
        feasible=bool(complete and not smoke and outer_error is None and time.monotonic()<hard_deadline)
        (result_dir/'qualification.json').write_bytes(bounded_json_line({'schema_version':1,'feasible':feasible}))
    if outer_error is not None:
        raise outer_error


def write_failure_results():
    parser=argparse.ArgumentParser(add_help=False)
    parser.add_argument('--program_path')
    parser.add_argument('--results_dir')
    arguments,unused=parser.parse_known_args()
    if not arguments.results_dir:
        return
    directory=Path(arguments.results_dir)
    directory.mkdir(parents=True,exist_ok=True)
    metrics=dict(combined_score=0.,normalized_capped_rmse=1.,normalized_capped_bias=1.,
        bias_ci_low=-1.,bias_ci_high=1.,rmse_ci_low=0.,rmse_ci_high=1.,
        paired_rmse_gain_vs_dim=-1.,permutation_rmse_gap=-1.,control_pass_rate=0.,replay_error=1.,failure_rate=1.)
    if not (directory/'metrics.json').exists():
        (directory/'metrics.json').write_bytes(bounded_json_line(metrics))
    (directory/'correct.json').write_bytes(bounded_json_line({'correct':False}))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1':
        (directory/'qualification.json').write_bytes(bounded_json_line({'schema_version':1,'feasible':False}))


if __name__=='__main__':
    if '--baseline-worker' in sys.argv:
        try:
            payload=parse_line(sys.stdin.buffer.readline(WIRE_LIMIT))
            work_started=time.monotonic()
            values=baseline_values(payload)
            work_seconds=time.monotonic()-work_started
            sys.stdout.buffer.write(bounded_json_line({'values':values,'work_seconds':work_seconds}))
            sys.stdout.buffer.flush()
        except Exception as error:
            if '--repair' in sys.argv and PLANE=='search':
                report_worker_exception(error)
            else:
                print('baseline_worker_failure',file=sys.stderr,flush=True)
            sys.exit(1)
    else:
        try:
            main()
        except Exception as error:
            write_failure_results()
            name=bounded_failure_name(type(error).__name__.lower(),'evaluator_exception')
            print(f'evaluator_exception type={name} message=evaluation_failed',file=sys.stderr)
            sys.exit(1)
