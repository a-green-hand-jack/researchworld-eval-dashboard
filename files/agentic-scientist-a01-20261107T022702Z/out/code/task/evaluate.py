"""Offline, evaluator-owned counterfactual investment benchmark.

Runtime: Linux x86_64, CPython 3.12, one evaluator and one candidate CPU thread.
Scientific soundness, search eligibility, and publication claims are distinct.
No superiority threshold is an eligibility gate. See the frozen plane plan.
"""

import time
START = time.monotonic()
import argparse
import base64
import collections
import contextlib
import decimal
import hashlib
import importlib.util
import itertools
import json
import math
import os
import pathlib
import re
import resource
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import unicodedata

for thread_name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[thread_name] = '1'
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.stats import rankdata

PLANE = 'search'
SEEDS = [1103, 2207]
TARGET_COUNT = 4
WALL_SECONDS = 900
RPC_BUDGET = 357
RESOURCE_HASHES = {'helm': 'bae5acaf3c7a12cf83afebd0d435c0758eabacdd0274cf6b84a3e65a7dc6343b', 'openllm': '79f57541f6c1f66a543ce69770d08319dd4d2c21fda7637d9e67f33781186dc0'}
PLAN_HASH = 'a0dea7e0284d2090dacb9c6bab6c853d5fe3efcc7aeb7724be917db880a15c90'
WIRE_LIMIT = 64 * 1024 * 1024
CHUNK_BYTES = 1024 * 1024
MAX_CHUNKS = 16
TOLERANCE = 1e-10
CASES = ('original', 'permutation', 'constant', 'copy')
CASE_WEIGHTS = (.7, .1, .1, .1)
WORKER_EVENTS = []
RULES = ('mean', 'median', 'borda')


class ProtocolError(RuntimeError):
    pass


class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise InvalidResetResponse('invalid reset response')


def require_operation_ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise ProtocolError('invalid operation acknowledgement')


def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value) else fallback


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'invalid_baseline_diagnostic')
        super().__init__('required baseline failed')


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {'component': 'candidate', 'category': 'invalid_reset_response', 'operation': 'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component': 'baseline', 'category': context.category, 'operation': 'baseline_worker'}
        if isinstance(context, ProtocolError):
            return {'component': 'candidate', 'category': 'protocol_error', 'operation': bounded_failure_name(operation, 'unknown')}
        context = context.__context__
        if context is None:
            break
    return {'component': 'candidate', 'category': 'timeout', 'operation': bounded_failure_name(operation, 'unknown')}


def fail_required_baseline(category, cancel_work, record_failure):
    failure = RequiredBaselineFailure(category)
    try:
        record_failure(failure.category)
    except Exception:
        failure.add_note('baseline diagnostic recording failed')
    try:
        cancel_work()
    except Exception:
        failure.add_note('baseline cleanup failed')
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
        category = 'baseline_timeout' if isinstance(error, TimeoutError) else 'baseline_result_failure'
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
        self.reader = threading.Thread(target=self._drain, name='worker-stderr-reader')
        self.reader.start()

    def _accept(self, chunk):
        self.observed_bytes += len(chunk)
        for segment in chunk.splitlines(keepends=True):
            complete = segment.endswith(b'\n')
            if not self.dropping_line:
                if len(self.pending) + len(segment) > self.LIMIT:
                    self.pending.clear()
                    self.dropping_line = True
                    self.truncated = True
                else:
                    self.pending.extend(segment)
            if complete:
                if not self.dropping_line:
                    line = bytes(self.pending).decode('utf-8', errors='replace')
                    size = len(line.encode('utf-8'))
                    if size <= self.LIMIT:
                        while self.retained_bytes + size > self.LIMIT:
                            self.retained_bytes -= len(self.lines.popleft().encode('utf-8'))
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
                self.capture_error = 'reader_stopped_before_eof'
                self.truncated = True
        except (OSError, ValueError):
            self.capture_error = 'stderr_capture_failed'
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
            raise RuntimeError('stderr reader cleanup unresolved')
        self.result = {'stderr': ''.join(self.lines), 'observed_bytes': self.observed_bytes,
                       'retained_bytes': self.retained_bytes, 'truncated': self.truncated,
                       'capture_error': self.capture_error}
        return dict(self.result)


def report_worker_exception(error):
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = 'WorkerException'
    try:
        message = str(error)
    except Exception:
        message = '<exception message unavailable>'
    if len(message) > 2048 or len(message.encode('utf-8', errors='replace')) > 2048:
        message = '<exception message omitted: too large>'
    print(f'worker_exception type={name}\n{message}', file=sys.stderr)


def json_line(value):
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    except (ValueError, TypeError, RecursionError) as error:
        raise ProtocolError('nonfinite or invalid json value') from error
    if len(encoded) >= WIRE_LIMIT:
        raise ProtocolError('wire size')
    return encoded


def parse_json(encoded):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ProtocolError('duplicate key')
            result[key] = value
        return result
    try:
        value = json.loads(encoded, object_pairs_hook=pairs, parse_constant=lambda value: (_ for _ in ()).throw(ProtocolError('nonfinite')))
        json_line(value)
        return value
    except (ValueError, RecursionError, UnicodeError) as error:
        raise ProtocolError('invalid json') from error


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ', 'CUDA_VISIBLE_DEVICES',
                     'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES', 'OMP_NUM_THREADS',
                     'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


NATIVE_WORKER = r'''
import contextlib, ctypes, errno, importlib.util, io, json, os, pathlib, sys
library = ctypes.CDLL(None, use_errno=True)
if os.uname().machine != 'x86_64':
    raise RuntimeError('native isolation requires Linux x86_64')
class Ruleset(ctypes.Structure):
    _fields_ = [('handled_access_fs', ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int)]
abi = library.syscall(444, 0, 0, 1)
if abi < 1:
    raise RuntimeError('Landlock unavailable')
access = (1 << 13) - 1
if abi >= 2: access |= 1 << 13
if abi >= 3: access |= 1 << 14
ruleset = Ruleset(access)
descriptor = library.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
if descriptor < 0: raise RuntimeError('Landlock ruleset failed')
allowed = [sys.prefix, sys.base_prefix, '/usr', '/lib', '/lib64', str(pathlib.Path(sys.argv[1]).parent), '/etc/ld.so.cache', '/etc/localtime', '/dev/null', '/dev/urandom']
for path in allowed:
    if not os.path.exists(path): continue
    parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
    rights = (1 << 2) | ((1 << 3) if os.path.isdir(path) else 0) | (1 << 0)
    rule = PathRule(rights, parent)
    if library.syscall(445, descriptor, 1, ctypes.byref(rule), 0) != 0:
        raise RuntimeError('Landlock rule failed')
    os.close(parent)
if library.prctl(38, 1, 0, 0, 0) != 0 or library.syscall(446, descriptor, 0) != 0:
    raise RuntimeError('Landlock enforcement failed')
os.close(descriptor)
class Filter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte), ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint32)]
class Program(ctypes.Structure):
    _fields_ = [('len', ctypes.c_ushort), ('filter', ctypes.POINTER(Filter))]
instructions = [Filter(0x20,0,0,4), Filter(0x15,1,0,0xc000003e), Filter(0x06,0,0,0x80000000), Filter(0x20,0,0,0)]
denied = [41,42,43,44,45,49,50,53,57,58,59,62,101,165,200,234,272,303,304,308,310,311,321,322,425,438]
for number in denied:
    instructions.extend([Filter(0x15,0,1,number), Filter(0x06,0,0,0x50000 | errno.EPERM)])
instructions.extend([Filter(0x15,0,1,435), Filter(0x06,0,0,0x50000 | errno.ENOSYS)])
instructions.extend([Filter(0x15,0,4,56), Filter(0x20,0,0,16), Filter(0x45,1,0,0x10000), Filter(0x06,0,0,0x50000 | errno.EPERM), Filter(0x06,0,0,0x7fff0000), Filter(0x06,0,0,0x7fff0000)])
filters = (Filter * len(instructions))(*instructions)
program = Program(len(instructions), filters)
if library.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:
    raise RuntimeError('seccomp enforcement failed')
try:
    with contextlib.redirect_stdout(sys.stderr):
        spec = importlib.util.spec_from_file_location('candidate', sys.argv[1])
        candidate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(candidate)
    for line in sys.stdin.buffer:
        if len(line) >= 64 * 1024 * 1024: raise ValueError('request too large')
        request = json.loads(line)
        with contextlib.redirect_stdout(sys.stderr):
            response = candidate.handle(request)
        encoded = json.dumps(response, allow_nan=False, separators=(',', ':')).encode() + b'\n'
        if len(encoded) >= 64 * 1024 * 1024: raise ValueError('response too large')
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
except BaseException as error:
    if sys.argv[2] == 'repair':
        name = type(error).__name__
        message = str(error)
        if len(message.encode('utf-8', errors='replace')) > 2048: message = '<message too large>'
        print('worker_exception type=' + name[:80] + '\n' + message, file=sys.stderr)
    else:
        print('candidate_worker_failure', file=sys.stderr)
    raise SystemExit(1)
'''


def process_limits():
    resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
    cpu = math.ceil(WALL_SECONDS * 1)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})


def repair_visible():
    return PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')


class Worker:
    def __init__(self, arguments, *, environment, cwd=None, component='candidate', seed=0):
        self.component = component
        self.seed = seed
        self.process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, cwd=cwd, env=environment, shell=False,
                                        start_new_session=True, preexec_fn=process_limits)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        self.buffer = bytearray()
        self.closed = False
        self.exit_status = None
        self.snapshot = None
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def exchange(self, request, timeout):
        deadline = time.monotonic() + timeout
        data = memoryview(json_line(request))
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while data:
                if not selector.select(max(0, deadline - time.monotonic())):
                    raise TimeoutError()
                try:
                    written = os.write(self.process.stdin.fileno(), data[:65536])
                    data = data[written:]
                except BlockingIOError:
                    continue
                except BrokenPipeError as error:
                    raise ProtocolError('worker exit') from error
            selector.unregister(self.process.stdin)
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                if not selector.select(max(0, deadline - time.monotonic())):
                    raise TimeoutError()
                try:
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise ProtocolError('worker exit')
                self.buffer.extend(chunk)
                if len(self.buffer) >= WIRE_LIMIT:
                    raise ProtocolError('wire size')
        line, _, remainder = self.buffer.partition(b'\n')
        self.buffer = bytearray(remainder)
        return parse_json(line)

    def close(self, failed=False):
        if self.closed:
            return
        self.closed = True
        causal_status = self.process.poll()
        try:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(self.process.pid, signal.SIGTERM)
            try:
                self.process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(self.process.pid, signal.SIGKILL)
                self.process.wait(timeout=1)
            with contextlib.suppress(ProcessLookupError):
                os.killpg(self.process.pid, signal.SIGKILL)
            self.exit_status = self.process.returncode
        finally:
            self.process.stdin.close()
            self.process.stdout.close()
            self.snapshot = self.capture.close()
            WORKER_EVENTS.append({'seed': self.seed, 'component': self.component, 'failed': failed,
                                  'causal_exit_status': causal_status, 'actual_exit_status': self.exit_status,
                                  'capture': {key: value for key, value in self.snapshot.items() if key != 'stderr'}})
            if failed and repair_visible() and self.snapshot['stderr']:
                print(self.snapshot['stderr'], end='', file=sys.stderr)


class Candidate:
    def __init__(self, path):
        self.calls = 0
        self.worker = None
        self.proxy = None
        self.directory = None
        trusted_path = str(path) == '/broker-code/candidate_proxy.py'
        socket_present = bool(os.environ.get('AGENTIC_CANDIDATE_SOCKET'))
        if trusted_path != socket_present:
            raise RuntimeError('broker mode requires both signals')
        if trusted_path and socket_present:
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', str(path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.directory = tempfile.TemporaryDirectory(prefix='isolated-candidate-')
            source = pathlib.Path(path).resolve()
            for item in source.parent.iterdir():
                if item.is_file() and item.suffix == '.py' and not item.is_symlink():
                    (pathlib.Path(self.directory.name) / item.name).write_bytes(item.read_bytes())
            self.entrypoint = str(pathlib.Path(self.directory.name) / source.name)

    def call(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolError('rpc budget')
        json_line(request)
        if self.proxy:
            old_handler = signal.getsignal(signal.SIGALRM)
            def alarm_handler(signum, frame):
                raise TimeoutError()
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                result = self.proxy(request)
                json_line(result)
                return result
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
        if request['op'] == 'reset':
            self.cleanup()
            interpreter, environment = candidate_subprocess_settings(os.environ)
            self.worker = Worker([interpreter, '-I', '-u', '-c', NATIVE_WORKER, self.entrypoint,
                                  'repair' if repair_visible() else 'fixed'], environment=environment, cwd=self.directory.name, seed=request['seed'])
        if self.worker is None:
            raise ProtocolError('candidate unavailable')
        try:
            result = self.worker.exchange(request, timeout)
            if request['op'] == 'reset':
                require_reset_ack(result)
            return result
        except (TimeoutError, ProtocolError, InvalidResetResponse):
            try:
                self.cleanup(failed=True)
            except (RuntimeError, OSError, subprocess.TimeoutExpired):
                pass
            raise

    def cleanup(self, failed=False):
        if self.worker is not None:
            worker, self.worker = self.worker, None
            worker.close(failed=failed)

    def close(self):
        self.cleanup()
        if self.directory is not None:
            self.directory.cleanup()


def canonical_raw(value):
    if isinstance(value, str):
        return ' '.join(unicodedata.normalize('NFKC', value).split())
    if isinstance(value, (int, float)):
        return str(decimal.Decimal(str(value)).normalize())
    if isinstance(value, dict):
        return {canonical_raw(key): canonical_raw(item) for key, item in sorted(value.items())}
    return [canonical_raw(item) for item in value]


def raw_digest(value):
    encoded = json.dumps(canonical_raw(value), sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_boards(smoke):
    root = pathlib.Path(os.environ.get('TASK_SOURCE_DIR', pathlib.Path(__file__).resolve().parent)) / 'resources' / PLANE
    plan_bytes = (root / 'protocol.json').read_bytes()
    if hashlib.sha256(plan_bytes).hexdigest() != PLAN_HASH:
        raise ValueError('protocol integrity')
    plan = parse_json(plan_bytes)
    if plan['seeds'] != SEEDS or plan['max_candidate_rpc_calls'] != RPC_BUDGET:
        raise ValueError('protocol budget mismatch')
    boards = {}
    hashes = set()
    for family, task_count in (('helm', 57), ('openllm', 6)):
        path = root / (family + '.json')
        if path.is_symlink():
            raise ValueError('symlink resource')
        encoded = path.read_bytes()
        if hashlib.sha256(encoded).hexdigest() != RESOURCE_HASHES[family]:
            raise ValueError('resource integrity')
        document = parse_json(encoded)
        if len(document['tasks']) != task_count or len(document['rows']) < 9:
            raise ValueError('insufficient source data')
        if document['split']['cross_plane_raw_overlap'] != 0 or document['split']['cross_plane_cluster_overlap'] != 0:
            raise ValueError('split overlap')
        for row in document['rows']:
            content_hash = raw_digest(row['raw'])
            if content_hash != row['raw_hash'] or content_hash in hashes:
                raise ValueError('normalized raw-content duplicate')
            hashes.add(content_hash)
            expected = [row['raw'][task] / document['scale'] for task in document['tasks']]
            if expected != row['scores']:
                raise ValueError('unaudited features')
        rows = document['rows'][:12] if smoke else document['rows']
        matrix = np.round(np.array([row['scores'] for row in rows], dtype='<f8'), 10)
        if not np.isfinite(matrix).all() or np.any(matrix < 0) or np.any(matrix > 1):
            raise ValueError('invalid source score')
        means = np.mean(matrix, axis=1)
        nonwinners = [int(index) for index in np.argsort(-means, kind='stable') if means[index] < means.max() - TOLERANCE]
        count = 1 if smoke else min(TARGET_COUNT, len(nonwinners))
        if count < 1:
            raise ValueError('missing target population')
        targets = [nonwinners[int(index)] for index in np.linspace(0, len(nonwinners) - 1, count, dtype=int)]
        boards[family] = {'matrix': matrix, 'targets': targets, 'tasks': document['tasks']}
    return boards


def aggregate(matrix, rule):
    if rule == 'mean':
        return matrix.mean(axis=1)
    if rule == 'median':
        return np.median(matrix, axis=1)
    return np.mean((rankdata(matrix, axis=0, method='average') - 1) / (matrix.shape[0] - 1), axis=1)


class Decision:
    def __init__(self, matrix, target, rule, fraction):
        self.matrix, self.target, self.rule = matrix, target, rule
        self.count = matrix.shape[1]
        self.initial = matrix[target].copy()
        self.caps = np.round(self.initial + fraction * (1 - self.initial), 10)
        scores = aggregate(matrix, rule)
        self.rival = float(np.delete(scores, target).max())
        self.base = scores
        if rule == 'borda':
            old = np.sign(self.initial - matrix) / 2 + .5
            new = np.sign(self.caps - matrix) / 2 + .5
            change = new - old
            change[target] = 0
            self.coefficients = (change + change.sum(axis=0)) / ((matrix.shape[0] - 1) * self.count)

    def gap(self, indices):
        if self.rule == 'borda':
            margins = self.base[self.target] - self.base + self.coefficients[:, indices].sum(axis=1)
            return float(np.delete(margins, self.target).min())
        modified = self.initial.copy()
        modified[indices] = self.caps[indices]
        value = modified.mean() if self.rule == 'mean' else np.median(modified)
        return float(value - self.rival)

    def wins(self, indices):
        return self.gap(indices) >= -TOLERANCE

    def verify_direct(self, indices):
        modified = self.matrix.copy()
        modified[self.target, indices] = self.caps[indices]
        scores = aggregate(modified, self.rule)
        return float(np.delete(scores, self.target).max() - scores[self.target]) <= TOLERANCE


def check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError()


def witness(decision, indices, *, exact=False, lower=0):
    return {'tasks': list(indices), 'attainable': True, 'exact': exact, 'lower': lower, 'upper': len(indices)}


def baseline_decision(decision, name, rng, deadline):
    check_deadline(deadline)
    count = decision.count
    if decision.wins([]):
        return witness(decision, [], exact=True)
    if not decision.wins(list(range(count))):
        return {'tasks': [], 'attainable': False, 'exact': True, 'lower': count + 1, 'upper': count + 1}
    if name == 'none':
        return {'tasks': [], 'attainable': True, 'exact': False, 'lower': 0, 'upper': count + 1}
    if name == 'reference':
        if count <= 6:
            for size in range(1, count + 1):
                for subset in itertools.combinations(range(count), size):
                    check_deadline(deadline)
                    if decision.wins(list(subset)):
                        return witness(decision, subset, exact=True, lower=size)
        if decision.rule == 'mean':
            order = np.argsort(-(decision.caps - decision.initial), kind='stable').tolist()
            for size in range(1, count + 1):
                if decision.wins(order[:size]):
                    return witness(decision, order[:size], exact=True, lower=size)
        if decision.rule == 'median' and count % 2:
            threshold = decision.rival - TOLERANCE
            needed = max(0, count // 2 + 1 - int(np.sum(decision.initial >= threshold)))
            available = np.flatnonzero((decision.initial < threshold) & (decision.caps >= threshold)).tolist()
            selected = available[:needed]
            if len(selected) == needed and decision.wins(selected):
                return witness(decision, selected, exact=True, lower=needed)
        if decision.rule == 'borda':
            check_deadline(deadline)
            constraints = LinearConstraint(decision.coefficients, decision.base - decision.base[decision.target] - TOLERANCE, np.inf)
            result = milp(np.ones(count), integrality=np.ones(count), bounds=Bounds(0, 1), constraints=constraints,
                          options={'time_limit': max(.001, min(.15, deadline - time.monotonic())), 'mip_rel_gap': 0.0})
            lower = 0
            if getattr(result, 'mip_dual_bound', None) is not None and math.isfinite(result.mip_dual_bound):
                lower = max(0, min(count, math.ceil(result.mip_dual_bound - 1e-6)))
            if result.x is not None:
                selected = np.flatnonzero(result.x > .5).tolist()
                if decision.verify_direct(selected):
                    return witness(decision, selected, exact=lower == len(selected), lower=lower)
            return witness(decision, range(count), lower=lower)
    selected = []
    order = list(range(count))
    if name == 'random':
        rng.shuffle(order)
    while not decision.wins(selected):
        check_deadline(deadline)
        remaining = [column for column in order if column not in selected]
        if name in ('greedy', 'reference'):
            column = max(remaining, key=lambda item: decision.gap(selected + [item]))
        else:
            column = remaining[0]
        selected.append(column)
    return witness(decision, selected)


def baseline_worker(request):
    matrix = np.array(request['matrix'], dtype='<f8')
    decisions = [Decision(matrix, target, rule, fraction) for target in request['targets'] for rule in RULES for fraction in request['fractions']]
    methods = []
    for name in ('none', 'random', 'greedy', 'reference'):
        begin = time.monotonic()
        deadline = begin + request['work_seconds']
        rng = np.random.default_rng(request['seed'])
        observations = [baseline_decision(decision, name, rng, deadline) for decision in decisions]
        check_deadline(deadline)
        methods.append({'name': name, 'observations': observations, 'productive_seconds': time.monotonic() - begin})
    return {'methods': methods}


def run_baselines(matrix, targets, fractions, seed, work, deadline):
    interpreter, environment = candidate_subprocess_settings(os.environ)
    arguments = [interpreter, '-I', '-u', str(pathlib.Path(__file__).resolve()), '--baseline-worker']
    if repair_visible():
        arguments.append('--repair-worker')
    worker = Worker(arguments, environment=environment, component='baseline', seed=seed)
    failed = True
    primary = None
    try:
        request = {'matrix': matrix.tolist(), 'targets': targets, 'fractions': fractions, 'seed': seed, 'work_seconds': work}
        result = worker.exchange(request, timeout=max(.01, min(4 * work + 2, deadline - time.monotonic())))
        if type(result) is not dict or set(result) != {'methods'} or [item['name'] for item in result['methods']] != ['none', 'random', 'greedy', 'reference']:
            raise RequiredBaselineFailure('baseline_result_failure')
        try:
            status = worker.process.wait(timeout=max(.01, min(1., deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            raise TimeoutError() from None
        if status != 0:
            raise RequiredBaselineFailure('baseline_signal' if status < 0 else 'baseline_timeout' if status == 124 else 'baseline_exit')
        failed = False
        return result
    except TimeoutError:
        primary = RequiredBaselineFailure('baseline_timeout')
        raise primary from None
    except ProtocolError:
        status = worker.process.poll()
        if status is None:
            try:
                status = worker.process.wait(timeout=.1)
            except subprocess.TimeoutExpired:
                pass
        category = ('baseline_signal' if status is not None and status < 0 else
                    'baseline_timeout' if status == 124 else
                    'baseline_exit' if status is not None and status > 0 else 'baseline_result_failure')
        primary = RequiredBaselineFailure(category)
        raise primary from None
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            worker.close(failed=failed)
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            WORKER_EVENTS.append({'seed': seed, 'component': 'baseline', 'category': 'cleanup_failure'})
            if primary is None:
                raise RequiredBaselineFailure('baseline_cleanup_failure') from None


def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid time allowance')
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError('work allowance must be positive')
    return value


def require_joint_workload_budget(*, search, final):
    required = {}
    for plane, profile in (('search', search), ('final', final)):
        episodes, methods = profile['episode_count'], profile['method_count']
        if any(type(count) is not int or count <= 0 for count in (episodes, methods)):
            raise ValueError('invalid episode or method count')
        times = {name: finite_budget_seconds(profile[name]) for name in ('wall_seconds', 'startup_seconds', 'reset_seconds', 'cleanup_seconds', 'finish_seconds')}
        work = positive_work_seconds(profile['work_seconds'])
        needed = times['startup_seconds'] + times['finish_seconds'] + episodes * (times['reset_seconds'] + methods * (work + times['cleanup_seconds']))
        if needed > times['wall_seconds']:
            raise ValueError('productive work exceeds wall budget')
        required[plane] = needed
    return required


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError('invalid remaining method count')
    if now + (methods_remaining + 1) * (work + cleanup_seconds) > episode_deadline:
        raise TimeoutError('insufficient matched method reservations')
    return now + work


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = 'reset'
        primary_failure = None
        episode_begin = clock()
        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                if request.get('op') == 'solve':
                    timeout = min(timeout, request['work_seconds'])
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc({'op': 'reset', 'seed': episode['seed']}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            value['duration'] = clock() - episode_begin
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            outcomes[index]['duration'] = clock() - episode_begin
            outcomes[index]['failure'] = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(primary_failure or describe_episode_failure(error, current_operation))
    return outcomes, complete


def episode_plan(seeds):
    episodes = [{'family': family, 'case': case, 'seed': seed, 'replay': False}
                for family in ('helm', 'openllm') for case in CASES for seed in seeds]
    episodes.append(dict(episodes[0], replay=True))
    return episodes


def preflight(boards):
    largest = {'op': 'upload_chunk', 'index': 15, 'data': base64.b64encode(bytes(CHUNK_BYTES)).decode('ascii')}
    response = {'solutions': [{'status': 'feasible', 'tasks': list(range(100))} for _ in range(48)]}
    sizes = []
    for key, value in (('request', largest), ('response', response)):
        encoded = json_line({'id': '9' * 64, key: value})
        if len(encoded) + 131072 >= WIRE_LIMIT:
            raise ValueError('complete framed payload exceeds wire limit')
        sizes.append(len(encoded) + 131072)
    for board in boards.values():
        if board['matrix'].nbytes > 16 * CHUNK_BYTES:
            raise ValueError('logical board exceeds bound')
    expected = {'reset': 1, 'upload_start': 1, 'upload_chunk': MAX_CHUNKS, 'upload_commit': 1, 'solve': 1, 'release': 1}
    if sum(expected.values()) * len(episode_plan(SEEDS)) != RPC_BUDGET:
        raise ValueError('complete operation-count budget mismatch')
    profiles = {}
    for plane, episodes, wall, startup, work in (('search', 17, 900, 120, 5), ('final', 25, 1800, 180, 8)):
        profiles[plane] = dict(episode_count=episodes, method_count=5, wall_seconds=wall,
                               startup_seconds=startup, reset_seconds=5, cleanup_seconds=1,
                               finish_seconds=20, work_seconds=work)
    require_joint_workload_budget(**profiles)
    return sizes


def evaluate_episode(episode, call, deadline, candidate, boards, work):
    board = boards[episode['family']]
    matrix = board['matrix'].copy()
    task_ids = list(board['tasks'])
    if episode['case'] == 'permutation':
        permutation = np.roll(np.arange(matrix.shape[1]), 1)
        if np.array_equal(permutation, np.arange(matrix.shape[1])) or np.array_equal(matrix, matrix[:, permutation]):
            raise ValueError('vacuous task permutation')
        matrix = matrix[:, permutation]
        task_ids = [task_ids[index] for index in permutation]
    if episode['case'] == 'constant':
        matrix.fill(.5)
    fractions = [0., 0.] if episode['case'] == 'copy' else [1., .5]
    targets = board['targets']
    begin = time.monotonic()
    failed = True
    primary = None
    try:
        reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline, methods_remaining=4,
                                 work_seconds=work, cleanup_seconds=1)
        baselines = run_baselines(matrix, targets, fractions, episode['seed'], work,
                                  deadline - work - 2)
        binary = matrix.astype('<f8').tobytes()
        chunks = math.ceil(len(binary) / CHUNK_BYTES)
        require_operation_ack(call({'op': 'upload_start', 'encoding': 'base64', 'dtype': '<f8',
                                'shape': list(matrix.shape), 'byte_length': len(binary),
                                'chunk_count': chunks, 'sha256': hashlib.sha256(binary).hexdigest(), 'task_ids': task_ids}))
        for index in range(chunks):
            require_operation_ack(call({'op': 'upload_chunk', 'index': index,
                                    'data': base64.b64encode(binary[index * CHUNK_BYTES:(index + 1) * CHUNK_BYTES]).decode('ascii')}))
        require_operation_ack(call({'op': 'upload_commit'}))
        method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                   methods_remaining=0, work_seconds=work, cleanup_seconds=1)
        response = call({'op': 'solve', 'targets': targets, 'rules': list(RULES),
                         'cap_fractions': fractions, 'tolerance': TOLERANCE, 'work_seconds': work})
        if time.monotonic() > method_deadline:
            raise TimeoutError()
        expected = len(targets) * 6
        if type(response) is not dict or set(response) != {'solutions'} or type(response['solutions']) is not list or len(response['solutions']) != expected:
            raise ProtocolError('malformed solve response')
        contributions = []
        observations = []
        sound = True
        controls_complete = True
        signature = []
        decisions = [(target, rule, fraction) for target in targets for rule in RULES for fraction in fractions]
        for decision_index, ((target, rule, fraction), solution) in enumerate(zip(decisions, response['solutions'])):
            check_deadline(deadline)
            if type(solution) is not dict or set(solution) != {'status', 'tasks'}:
                raise ProtocolError('malformed solution')
            indices = solution['tasks']
            status = solution['status']
            if type(indices) is not list or any(type(column) is not int or not 0 <= column < matrix.shape[1] for column in indices) or len(indices) != len(set(indices)):
                raise ProtocolError('illegal allocation')
            if status not in ('feasible', 'unattainable', 'unresolved') or status != 'feasible' and indices:
                raise ProtocolError('illegal status')
            decision = Decision(matrix, target, rule, fraction)
            valid = True
            quality = 0.
            if status == 'feasible':
                valid = decision.verify_direct(indices)
                quality = 1 - len(indices) / matrix.shape[1] if valid else 0.
            elif status == 'unattainable':
                valid = not decision.verify_direct(list(range(matrix.shape[1])))
                quality = 1. if valid else 0.
            if episode['case'] == 'constant':
                valid = valid and status == 'feasible' and indices == []
            if episode['case'] == 'copy':
                expected_status = 'feasible' if decision.verify_direct([]) else 'unattainable'
                valid = valid and status == expected_status and indices == []
            if episode['case'] != 'original' and status == 'unresolved':
                controls_complete = False
            reference = baselines['methods'][3]['observations'][decision_index]
            if reference['exact'] and status == 'feasible' and len(indices) < reference['lower']:
                valid = False
            observations.append({'target': target, 'rule': rule, 'fraction': fraction, 'allocation': solution,
                                 'validated': valid, 'reference': reference,
                                 'baselines': {item['name']: item['observations'][decision_index] for item in baselines['methods'][:3]}})
            contributions.append(quality if valid else 0.)
            signature.append([status, len(indices)])
            sound = sound and valid
        require_operation_ack(call({'op': 'release'}))
        failed = False
        return {'score': sum(contributions) / expected, 'correct': sound and controls_complete,
                'complete': True, 'controls_completed': sound and controls_complete if episode['case'] != 'original' else True,
                'duration': time.monotonic() - begin, 'signature': signature,
                'observations': observations}
    except BaseException as error:
        primary = error
        raise
    finally:
        try:
            candidate.cleanup(failed=failed)
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            WORKER_EVENTS.append({'seed': episode['seed'], 'component': 'candidate', 'category': 'cleanup_failure'})
            if primary is None:
                raise ProtocolError('candidate cleanup failure') from None


def write_results(directory, score, correct, feasible, evidence=None):
    directory.mkdir(parents=True, exist_ok=True)
    metric = 'combined_score' if PLANE == 'search' else 'final_score'
    (directory / 'metrics.json').write_bytes(json_line({metric: float(score)}))
    (directory / 'correct.json').write_bytes(json_line({'correct': bool(correct)}))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (directory / 'qualification.json').write_bytes(json_line({'schema_version': 1, 'feasible': bool(feasible)}))
    if evidence is not None:
        encoded = json_line({'schema_version': 1, 'episodes': evidence})
        if len(encoded) <= 16 * 1024**2:
            (directory / 'evaluation_evidence.json').write_bytes(encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    directory = pathlib.Path(arguments.results_dir)
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    seeds = [SEEDS[0]] if smoke else SEEDS
    episodes = episode_plan(seeds)
    wall = 120 if smoke else WALL_SECONDS
    startup = 10 if smoke else 120 if PLANE == 'search' else 180
    hard_deadline = START + wall - startup
    work = .75 if smoke else 5 if PLANE == 'search' else 8
    outcomes = None
    candidate = None
    failed_episodes = []
    def record_failure(failure):
        failed_episodes.append(failure)
        if PLANE == 'search':
            print('episode_failure component=' + failure['component'] + ' category=' + failure['category'] + ' operation=' + failure['operation'], file=sys.stderr)
    try:
        boards = load_boards(smoke)
        preflight(boards)
        candidate = Candidate(arguments.program_path)
        reset_timeout = 2 if smoke else 5
        worst = lambda episode: {'score': 0., 'correct': False, 'complete': False, 'controls_completed': False, 'duration': 0., 'signature': None, 'observations': []}
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline,
            finish_reserve=5 if smoke else 20, reset_timeout=reset_timeout, episode_overhead=5,
            rpc_cap=max(reset_timeout, work + 1), clock=time.monotonic, rpc=candidate.call,
            evaluate=lambda episode, call, deadline: evaluate_episode(episode, call, deadline, candidate, boards, work),
            worst_case=worst, record_failure=record_failure)
        primary_count = len(episodes) - 1
        score = 0.
        for index, (episode, outcome) in enumerate(zip(episodes, outcomes)):
            if index < primary_count:
                score += .5 * CASE_WEIGHTS[CASES.index(episode['case'])] / len(seeds) * outcome['score']
        for episode, outcome in zip(episodes, outcomes):
            if outcome['complete'] and (not outcome['correct'] or any(item['allocation']['status'] == 'unresolved' for item in outcome['observations'])):
                record_failure({'component': 'candidate', 'category': 'invalid_solution' if not outcome['correct'] else 'unresolved', 'operation': 'solve'})
        seed_correct = {seed: all(outcome['correct'] for episode, outcome in zip(episodes, outcomes) if episode['seed'] == seed) for seed in seeds}
        originals = {(episode['family'], episode['seed']): outcome for episode, outcome in zip(episodes, outcomes) if episode['case'] == 'original' and not episode['replay']}
        for episode, outcome in zip(episodes, outcomes):
            if episode['case'] == 'permutation':
                original = originals[(episode['family'], episode['seed'])]
                if len(original['observations']) != len(outcome['observations']):
                    seed_correct[episode['seed']] = False
                for before, after in zip(original['observations'], outcome['observations']):
                    left, right = before['reference'], after['reference']
                    if left['attainable'] != right['attainable'] or left['exact'] and right['exact'] and left['lower'] != right['lower']:
                        seed_correct[episode['seed']] = False
        replay_ok = outcomes[0]['signature'] is not None and outcomes[-1]['signature'] == outcomes[0]['signature']
        seed_correct[seeds[0]] = seed_correct[seeds[0]] and replay_ok
        correct = all(seed_correct.values())
        if not replay_ok and outcomes[-1]['complete']:
            record_failure({'component': 'candidate', 'category': 'reset_replay_mismatch', 'operation': 'solve'})
        records = []
        for seed in seeds:
            selected = [(episode, outcome) for episode, outcome in zip(episodes, outcomes) if episode['seed'] == seed and not episode['replay']]
            records.append({'seed': seed,
                'score': sum(.5 * CASE_WEIGHTS[CASES.index(episode['case'])] * outcome['score'] for episode, outcome in selected),
                'correct': seed_correct[seed],
                'duration_seconds': sum(outcome['duration'] for episode, outcome in zip(episodes, outcomes) if episode['seed'] == seed),
                'solution': {'cases': [{'family': episode['family'], 'case': episode['case'], 'observations': outcome['observations'], 'failure': outcome.get('failure')} for episode, outcome in selected], 'workers': [event for event in WORKER_EVENTS if event['seed'] == seed], 'replay': {'correct': outcomes[-1]['correct'] and replay_ok, 'signature': outcomes[-1]['signature'], 'duration_seconds': outcomes[-1]['duration'], 'failure': outcomes[-1].get('failure')} if seed == seeds[0] else None}})
        candidate.close()
        candidate = None
        feasible = complete and not smoke and replay_ok and all(outcome.get('controls_completed', False) for outcome in outcomes) and time.monotonic() < hard_deadline
        write_results(directory, score, correct, feasible, records)
    except Exception as error:
        if candidate is not None:
            with contextlib.suppress(Exception):
                candidate.close()
        write_results(directory, 0., False, False)
        if PLANE == 'search':
            print('evaluator_exception type=' + type(error).__name__[:80] + ' message=' + str(error)[:160], file=sys.stderr)
        else:
            print('evaluator_exception category=sealed_failure', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    if '--baseline-worker' in sys.argv:
        try:
            request = parse_json(sys.stdin.buffer.readline(WIRE_LIMIT))
            sys.stdout.buffer.write(json_line(baseline_worker(request)))
            sys.stdout.buffer.flush()
        except BaseException as error:
            if '--repair-worker' in sys.argv and PLANE == 'search':
                report_worker_exception(error)
            else:
                print('baseline_worker_failure', file=sys.stderr)
            raise SystemExit(124 if isinstance(error, TimeoutError) else 1)
    else:
        raise SystemExit(main())
