"""Offline compositional split-conformal benchmark. See starter RPC docstring.

Search eligibility is evidence/integrity validity, never comparative superiority.
Final correctness adds sealed production completion and paired uncertainty. Neither
predicate establishes a publication claim. Negative scientific results are valid.
Native draft isolation requires Linux x86_64, Landlock ABI >= 4 and seccomp BPF.
Python 3.12, NumPy 2.1.3; offline pip install -r requirements.txt from local wheels.
"""
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
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time

for thread_variable in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[thread_variable] = '1'
import numpy as np

PLANE = 'search'
WALL_SECONDS = 1200
RPC_LIMIT = 1375
STARTED = time.monotonic()
WIRE_LIMIT = 64 * 1024 * 1024
CHUNK = 4 * 1024 * 1024
CASES = ('H3', 'H10', 'B3', 'B10', 'S3', 'S10')
VARIANTS = ('actual', 'constant', 'permuted')
METRICS = ('combined_score', 'marginal_coverage_error', 'group_coverage_error',
           'reference_mass', 'global_ilr_score_gap', 'constant_control_score',
           'permuted_control_score', 'control_pass_fraction')
if PLANE == 'final':
    METRICS += ('combined_score_ci_low', 'combined_score_ci_high')


def unique_keys(pairs):
    value = {}
    for key, entry in pairs:
        if key in value:
            raise ValueError('duplicate JSON key')
        value[key] = entry
    return value


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(encoded) >= wire_limit:
        raise ProtocolError('message_bound')
    return encoded


class ProtocolError(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'malformed_response')
        super().__init__('protocol failure')


class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise InvalidResetResponse('invalid reset response')


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'invalid_baseline_diagnostic')
        super().__init__('required baseline failed')


def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value) else fallback


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return dict(component='candidate', category='invalid_reset_response', operation='reset')
        if isinstance(context, RequiredBaselineFailure):
            return dict(component='baseline', category=context.category, operation='baseline_worker')
        if isinstance(context, ProtocolError):
            return dict(component='candidate', category=context.category,
                        operation=bounded_failure_name(operation, 'unknown'))
        context = context.__context__
        if context is None:
            break
    return dict(component='candidate', category='timeout',
                operation=bounded_failure_name(operation, 'unknown'))


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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError('invalid CPU budget')
    return math.ceil(wall_seconds * allowed_threads)


def reserved_method_deadline(*, now, episode_deadline, methods_remaining,
                             work_seconds, cleanup_seconds):
    if (not all(math.isfinite(value) and value >= 0 for value in
                (now, episode_deadline, cleanup_seconds)) or work_seconds <= 0
            or not math.isfinite(work_seconds) or type(methods_remaining) is not int
            or methods_remaining < 0):
        raise ValueError('invalid method allowance')
    if now + (methods_remaining + 1) * (work_seconds + cleanup_seconds) > episode_deadline:
        raise TimeoutError('insufficient matched method reservations')
    return now + work_seconds


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
        self.result = dict(stderr=''.join(self.lines), observed_bytes=self.observed_bytes,
                           retained_bytes=self.retained_bytes, truncated=self.truncated,
                           capture_error=self.capture_error)
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
    print(f'worker_exception type={name}\n{message}', file=sys.stderr, flush=True)


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ',
                     'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES',
                     'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION',
                     'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1',
                       PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[name] = '1'
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


NATIVE_RUNNER = r'''
import base64, ctypes, importlib.util, json, math, os, pathlib, resource, struct, sys
import numpy
resource.setrlimit(resource.RLIMIT_AS, (6 * 1024**3, 6 * 1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (int(sys.argv[2]), int(sys.argv[2])))
resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
lib = ctypes.CDLL(None, use_errno=True)
if os.uname().machine != 'x86_64' or lib.syscall(444, 0, 0, 1) < 4:
    raise RuntimeError('native isolation requires x86_64 Landlock ABI 4')
class Ruleset(ctypes.Structure):
    _fields_ = [('fs', ctypes.c_uint64), ('net', ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [('allowed', ctypes.c_uint64), ('parent', ctypes.c_int32)]
rights = (1 << 15) - 1
ruleset = Ruleset(rights, 3)
fd = lib.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
if fd < 0:
    raise RuntimeError('landlock ruleset failed')
for path in (sys.prefix, '/usr/local/lib/python3.12', '/usr/lib', '/lib', '/lib64',
             '/dev/null', '/dev/urandom', os.getcwd()):
    if not os.path.exists(path):
        continue
    parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
    allowed = rights if path == os.getcwd() else ((1 << 0) | (1 << 2) | (1 << 3))
    if not os.path.isdir(path):
        allowed &= ~ (1 << 3)
    rule = PathRule(allowed, parent)
    if lib.syscall(445, fd, 1, ctypes.byref(rule), 0) < 0:
        raise RuntimeError('landlock rule failed')
    os.close(parent)
if lib.prctl(38, 1, 0, 0, 0) or lib.syscall(446, fd, 0):
    raise RuntimeError('landlock confinement failed')
os.close(fd)
class Filter(ctypes.Structure):
    _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte),
                ('jf', ctypes.c_ubyte), ('k', ctypes.c_uint32)]
class Program(ctypes.Structure):
    _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(Filter))]
filters = [Filter(0x20, 0, 0, 4), Filter(0x15, 1, 0, 0xc000003e),
           Filter(0x06, 0, 0, 0x80000000), Filter(0x20, 0, 0, 0)]
for number in (41,42,43,49,50,53,56,57,58,59,62,101,109,112,155,165,166,200,234,272,288,298,302,304,308,310,311,317,321,322,323,424,425,426,427,434,435,438):
    filters.extend((Filter(0x15,0,1,number), Filter(0x06,0,0,0x50001)))
filters.extend((Filter(0x35,0,1,0x40000000), Filter(0x06,0,0,0x50001),
                Filter(0x06,0,0,0x7fff0000)))
array = (Filter * len(filters))(*filters)
program = Program(len(filters), array)
if lib.prctl(22,2,ctypes.byref(program),0,0):
    raise RuntimeError('seccomp confinement failed')
spec = importlib.util.spec_from_file_location('candidate', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    try:
        request = json.loads(line)
        response = module.handle(request)
        encoded = json.dumps(response, allow_nan=False,separators=(',', ':')).encode() + b'\n'
        if len(encoded) >= 64 * 1024**2:
            raise ValueError('response bound')
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
    except Exception as error:
        if sys.argv[3] == 'repair':
            name = type(error).__name__
            message = str(error)
            if len(message.encode('utf-8', errors='replace')) > 2048:
                message = '<exception message omitted: too large>'
            print('worker_exception type=' + name + '\n' + message, file=sys.stderr, flush=True)
        else:
            print('candidate_worker_failure', file=sys.stderr, flush=True)
        sys.exit(1)
'''


class Client:
    def __init__(self, path):
        self.path = Path(path).absolute()
        self.proxy = None
        self.process = None
        self.reader = None
        self.directory = None
        self.calls = 0
        self.resets = []
        self.buffer = bytearray()
        self.repair = PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                                               or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')
        is_proxy = str(self.path) == '/broker-code/candidate_proxy.py'
        socket_present = bool(os.environ.get('AGENTIC_CANDIDATE_SOCKET'))
        if is_proxy != socket_present:
            raise RuntimeError('broker requires exact proxy path and socket together')
        if is_proxy:
            specification = importlib.util.spec_from_file_location('trusted_broker_proxy', self.path)
            self.proxy = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(self.proxy)

    def start(self):
        self.directory = tempfile.TemporaryDirectory(prefix='composition-candidate-')
        target = Path(self.directory.name) / 'src'
        target.mkdir()
        for source in self.path.parent.rglob('*'):
            if source.is_symlink():
                raise ProtocolError('candidate_symlink')
            if source.is_file() and source.suffix in ('.py', '.json', '.txt'):
                relative = source.relative_to(self.path.parent)
                if source.stat().st_size > 8 * 1024 * 1024:
                    raise ProtocolError('candidate_source_bound')
                destination = target / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
        interpreter, environment = candidate_subprocess_settings(os.environ)
        self.process = subprocess.Popen(
            [interpreter, '-I', '-u', '-c', NATIVE_RUNNER,
             str(target / self.path.name), str(cpu_limit_seconds(WALL_SECONDS, 2)),
             'repair' if self.repair else 'ordinary'], cwd=self.directory.name,
            env=environment, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, start_new_session=True, shell=False, bufsize=0)
        self.reader = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.buffer.clear()

    def close(self, failed=False):
        if self.process is not None:
            process, self.process = self.process, None
            if process.poll() is None:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=.2)
                except subprocess.TimeoutExpired:
                    with contextlib.suppress(ProcessLookupError):
                        os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=.2)
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            snapshot = self.reader.close()
            process.stdin.close()
            process.stdout.close()
            if failed and PLANE == 'search':
                if self.repair and snapshot['stderr']:
                    print(snapshot['stderr'], file=sys.stderr, end='')
                if self.repair:
                    print('worker_capture ' + json.dumps({key: value for key, value in snapshot.items()
                                                         if key != 'stderr'}), file=sys.stderr)
        if self.directory is not None:
            self.directory.cleanup()
            self.directory = None

    def call(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_LIMIT:
            raise ProtocolError('rpc_budget')
        encoded = bounded_json_line(request)
        if request.get('op') == 'reset':
            self.resets.append(request['seed'])
        if self.proxy is not None:
            with time_bound(time.monotonic() + timeout):
                response = self.proxy.handle(request)
            try:
                bounded_json_line(response)
            except (ValueError, TypeError, RecursionError):
                raise ProtocolError('invalid_json') from None
            return response
        deadline = time.monotonic() + timeout
        if request.get('op') == 'reset':
            self.close()
            with time_bound(deadline):
                self.start()
        if self.process is None:
            raise ProtocolError('worker_unavailable')
        try:
            offset = 0
            while offset < len(encoded):
                with selectors.DefaultSelector() as selector:
                    selector.register(self.process.stdin, selectors.EVENT_WRITE)
                    if not selector.select(max(0, deadline - time.monotonic())):
                        raise TimeoutError()
                offset += os.write(self.process.stdin.fileno(), encoded[offset:offset + 65536])
            while b'\n' not in self.buffer:
                with selectors.DefaultSelector() as selector:
                    selector.register(self.process.stdout, selectors.EVENT_READ)
                    if not selector.select(max(0, deadline - time.monotonic())):
                        raise TimeoutError()
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    raise ProtocolError('candidate_exit')
                self.buffer.extend(chunk)
                if len(self.buffer) >= WIRE_LIMIT:
                    raise ProtocolError('message_bound')
            line, _, tail = self.buffer.partition(b'\n')
            self.buffer = bytearray(tail)
            try:
                response = json.loads(line, object_pairs_hook=unique_keys,
                                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                bounded_json_line(response)
            except (ValueError, TypeError, UnicodeError, RecursionError):
                raise ProtocolError('invalid_json') from None
            return response
        except (TimeoutError, ProtocolError, BrokenPipeError, ConnectionResetError, OSError) as error:
            primary = error if isinstance(error, (TimeoutError, ProtocolError)) else ProtocolError('transport_failure')
            try:
                self.close(failed=True)
            except Exception:
                primary.add_note('secondary cleanup failure')
            raise primary from None


@contextlib.contextmanager
def time_bound(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError()
    def expired(signum, frame):
        raise TimeoutError()
    previous = signal.signal(signal.SIGALRM, expired)
    old = signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if old[0]:
            signal.setitimer(signal.ITIMER_REAL, *old)


def encode(array):
    array = np.asarray(array, dtype='<f8', order='C')
    return dict(encoding='base64', dtype='<f8', shape=list(array.shape), nbytes=array.nbytes,
                data=base64.b64encode(array.tobytes()).decode('ascii'))


def scales(response, count):
    if type(response) is not dict or set(response) != {'scales'}:
        raise ProtocolError('prediction_schema')
    value = response['scales']
    if (type(value) is not dict or set(value) != {'encoding', 'dtype', 'shape', 'nbytes', 'data'}
            or value['encoding'] != 'base64' or value['dtype'] != '<f8'
            or value['shape'] != [count] or type(value['nbytes']) is not int
            or value['nbytes'] != count * 8 or not isinstance(value['data'], str)):
        raise ProtocolError('array_schema')
    try:
        raw = base64.b64decode(value['data'], validate=True)
    except (ValueError, TypeError):
        raise ProtocolError('array_encoding') from None
    if len(raw) != count * 8:
        raise ProtocolError('array_length')
    result = np.frombuffer(raw, dtype='<f8').copy()
    if not np.isfinite(result).all() or np.any(result <= 0):
        raise ProtocolError('invalid_scale')
    return np.clip(result, 1e-4, 1e4)


def preflight_payloads():
    requests = [dict(op='fit', x=encode(np.full((1024, 6), .25)),
                     residuals=encode(np.full(1024, .5)), dimension=10,
                     scale_min=.0001, scale_max=10000.0),
                dict(op='predict', x=encode(np.full((2048, 6), .25)))]
    responses = [dict(ok=True), dict(scales=encode(np.full(2048, .5)))]
    requests.append(dict(op='upload', token='buffer', offset=CHUNK,
                         data=base64.b64encode(bytes(CHUNK)).decode()))
    responses.append(dict(data=base64.b64encode(bytes(CHUNK)).decode()))
    records = []
    for request, response in zip(requests, responses):
        request_size = len(bounded_json_line(dict(id=9999999, method='handle', params=request))) + 4096
        response_size = len(bounded_json_line(dict(id=9999999, result=response))) + 4096
        if max(request_size, response_size) >= 8 * 1024 * 1024:
            raise ValueError('payload safety target')
        raw_input_bytes = (1024 * 7 * 8 if request['op'] == 'fit' else
                           2048 * 6 * 8 if request['op'] == 'predict' else CHUNK)
        raw_output_bytes = 0 if request['op'] == 'fit' else 2048 * 8 if request['op'] == 'predict' else CHUNK
        records.append(dict(operation=request['op'], raw_input_bytes=raw_input_bytes,
                            raw_output_bytes=raw_output_bytes,
                            base64_input_bytes=4 * math.ceil(raw_input_bytes / 3),
                            base64_output_bytes=4 * math.ceil(raw_output_bytes / 3),
                            application_request_bytes=len(bounded_json_line(request)),
                            application_response_bytes=len(bounded_json_line(response)),
                            conservative_framed_request_bytes=request_size,
                            conservative_framed_response_bytes=response_size,
                            framing_reserve_bytes=4096))
    return records


def basis(dimension):
    result = np.zeros((dimension, dimension - 1))
    for index in range(dimension - 1):
        result[:index + 1, index] = 1 / math.sqrt((index + 1) * (index + 2))
        result[index + 1, index] = -(index + 1) / math.sqrt((index + 1) * (index + 2))
    return result


def simplex(latent, matrix):
    logits = latent @ matrix.T
    logits -= logits.max(axis=-1, keepdims=True)
    probabilities = np.exp(logits)
    return probabilities / probabilities.sum(axis=-1, keepdims=True)


def quantile(values, alpha):
    rank = math.ceil((len(values) + 1) * (1 - alpha))
    if rank > len(values):
        return np.full(np.shape(values)[1:], np.inf)
    return np.sort(values, axis=0)[rank - 1]


def geometry_tests():
    for dimension in (3, 10):
        matrix = basis(dimension)
        assert np.allclose(matrix.T @ matrix, np.eye(dimension - 1), atol=1e-14)
        assert np.allclose(matrix.sum(axis=0), 0, atol=1e-14)
        latent = np.arange(dimension - 1)[None, :] / 10
        response = simplex(latent, matrix)
        assert np.all(response > 0) and np.allclose(response.sum(axis=1), 1)
        assert np.allclose(np.log(response) @ matrix, latent)
    assert quantile(np.arange(9), .2) == 7
    assert math.isinf(float(quantile(np.arange(3), .05)))
    assert np.array_equal(quantile(np.array([[1, 9], [3, 5], [2, 8]]), .5), [2, 8])
    assert np.linalg.norm(np.array([3., 4.])) == 5
    assert np.max(np.abs(np.array([.2, -.1, -.1]))) == .2


def generate_raw(case, lineage, sizes):
    """Reproduce the frozen original raw examples, before transforms or features."""
    dimension = int(case[1:])
    matrix = basis(dimension)
    rng = np.random.default_rng(np.random.SeedSequence(lineage))
    covariates = rng.normal(size=(sum(sizes), 6))
    if case[0] == 'S':
        covariates[-sizes[-1]:, 0] += 1.25
    coefficients = np.random.default_rng(333 + dimension).normal(0, .18, size=(6, dimension - 1))
    latent_mean = covariates @ coefficients
    if case[0] != 'H':
        dominant = np.zeros(dimension)
        dominant[0] = 4.5
        latent_mean += dominant @ matrix
    sigma = (np.full(len(covariates), .35) if case[0] == 'H'
             else .12 + .8 / (1 + np.exp(-1.5 * covariates[:, 0])))
    latent = latent_mean + sigma[:, None] * rng.normal(size=latent_mean.shape)
    responses = simplex(latent, matrix)
    if not np.isfinite(responses).all() or not np.all(responses > 0):
        raise ValueError('invalid generated composition')
    return covariates, responses


def raw_digest(array):
    canonical = np.asarray(array, dtype='<f8').copy()
    if not np.isfinite(canonical).all():
        raise ValueError('nonfinite raw data')
    canonical[canonical == 0] = 0
    return hashlib.sha256(canonical.tobytes()).hexdigest()


def load_resources(root, smoke):
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest['normalization'] != 'finite-f64le-c-order-negative-zero-to-positive-v1':
        raise ValueError('normalization mismatch')
    observed_examples, observed_covariates = set(), set()
    loaded = {}
    for item in manifest['files']:
        path = root / item['file']
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('resource integrity')
        archive = json.loads(path.read_text())
        covariates, responses = [np.frombuffer(base64.b64decode(archive[name]['data'], validate=True),
                                               dtype='<f8').reshape(archive[name]['shape']).copy()
                                 for name in ('x', 'y')]
        generated_x, generated_y = generate_raw(item['case'], item['lineage'], item['sizes'])
        if not np.array_equal(covariates, generated_x) or not np.array_equal(responses, generated_y):
            raise ValueError('generator provenance mismatch')
        example_hashes = [raw_digest(np.concatenate((covariate, response)))
                          for covariate, response in zip(covariates, responses)]
        covariate_hashes = [raw_digest(covariate) for covariate in covariates]
        if example_hashes != item['example_hashes'] or covariate_hashes != item['covariate_hashes']:
            raise ValueError('raw hash mismatch')
        if (observed_examples.intersection(example_hashes) or observed_covariates.intersection(covariate_hashes)
                or len(set(example_hashes)) != len(example_hashes)
                or len(set(covariate_hashes)) != len(covariate_hashes)):
            raise ValueError('raw content overlap')
        observed_examples.update(example_hashes)
        observed_covariates.update(covariate_hashes)
        if item['profile'] == ('smoke' if smoke else 'production'):
            loaded[item['case'], item['seed']] = (covariates, responses, item['sizes'])
    if manifest['cross_plane_check'] != 'raw-example-and-covariate-sha256-disjoint-verified-at-draft':
        raise ValueError('missing disjointness preflight')
    return manifest, loaded


def wilson(hits, count):
    if count <= 0:
        raise ValueError('empty coverage group')
    proportion = hits / count
    denominator = 1 + 1.96**2 / count
    center = (proportion + 1.96**2 / (2 * count)) / denominator
    radius = 1.96 * math.sqrt(proportion * (1 - proportion) / count + 1.96**2 / (4 * count**2)) / denominator
    return [max(0., center - radius), min(1., center + radius)]


def summarize(context, calibration_scores, test_scores, probe_scores, coordinatewise=False, conformal=True):
    errors, group_errors, masses, details = [], [], [], []
    for alpha in (.05, .10):
        threshold = (quantile(calibration_scores, alpha / context['dimension'] if coordinatewise else alpha)
                     if conformal else np.sort(calibration_scores, axis=0)[math.ceil(len(calibration_scores) * (1 - alpha)) - 1])
        test_hits = np.all(test_scores <= threshold, axis=-1) if coordinatewise else test_scores <= threshold
        probe_hits = np.all(probe_scores <= threshold, axis=-1) if coordinatewise else probe_scores <= threshold
        coverage = float(test_hits.mean())
        group_values, intervals = [], []
        for group in (context['groups'], ~context['groups']):
            if not group.any():
                raise RequiredBaselineFailure('empty_fixed_group')
            group_values.append(float(test_hits[group].mean()))
            intervals.append(wilson(int(test_hits[group].sum()), int(group.sum())))
        mass = float(probe_hits.mean())
        errors.append(abs(coverage - (1 - alpha)))
        group_errors.append(float(np.mean(np.abs(np.array(group_values) - (1 - alpha)))))
        masses.append(mass)
        details.append(dict(alpha=alpha, coverage=coverage, coverage_ci=wilson(int(test_hits.sum()), len(test_hits)),
                            group_coverage=group_values, group_ci=intervals, reference_mass=mass,
                            reference_mass_ci=wilson(int(probe_hits.sum()), probe_hits.size)))
    marginal, group_error, mass = float(np.mean(errors)), float(np.mean(group_errors)), float(np.mean(masses))
    utility = 1 - (.75 * (.5 * marginal + .5 * group_error) + .25 * mass)
    if not all(math.isfinite(value) and 0 <= value <= 1 for value in (marginal, group_error, mass, utility)):
        raise ValueError('nonfinite metric')
    return dict(utility=utility, marginal=marginal, group=group_error, mass=mass, details=details)


def deranged_targets(residuals):
    permutation = np.roll(np.arange(len(residuals)), 1)
    if (np.any(permutation == np.arange(len(residuals)))
            or np.array_equal(residuals[permutation], residuals)):
        raise RequiredBaselineFailure('vacuous_permutation')
    return permutation


def prepare_context(case, seed, raw, smoke):
    covariates, responses, sizes = raw
    dimension = responses.shape[1]
    matrix = basis(dimension)
    latent = np.log(responses) @ matrix
    boundaries = np.cumsum([0] + sizes)
    center_slice, train_slice, calibration_slice, test_slice = [slice(boundaries[index], boundaries[index + 1])
                                                               for index in range(4)]
    design = np.column_stack((np.ones(len(covariates)), covariates))
    center_design = design[center_slice]
    penalty = np.eye(7) * .01
    penalty[0, 0] = 0
    coefficients = np.linalg.solve(center_design.T @ center_design + penalty,
                                   center_design.T @ latent[center_slice])
    center = design @ coefficients
    residual_vectors = latent - center
    residuals = np.linalg.norm(residual_vectors, axis=1)
    context = dict(dimension=dimension, train_x=covariates[train_slice], residuals=residuals[train_slice],
                   calibration_x=covariates[calibration_slice], test_x=covariates[test_slice],
                   calibration_residuals=residuals[calibration_slice], test_residuals=residuals[test_slice],
                   groups=covariates[test_slice, 0] < 0)
    count, probes = (8, 32) if smoke else (128, 1024)
    selected = np.linspace(0, sizes[3] - 1, count, dtype=int)
    reference_rng = np.random.default_rng(np.random.SeedSequence([seed, dimension, ord(case[0]), 8821]))
    train_residuals = residual_vectors[:boundaries[2]]
    covariance = np.cov(train_residuals, rowvar=False) + np.eye(dimension - 1) * .01
    reference_noise = reference_rng.multivariate_normal(np.zeros(dimension - 1), covariance,
                                                       size=(count, probes // 2))
    reference_latent = center[test_slice][selected, None, :] + reference_noise
    uniform_response = reference_rng.dirichlet(np.ones(dimension), size=(count, probes // 2))
    uniform_latent = np.log(uniform_response) @ matrix
    probe_latent = np.concatenate((reference_latent, uniform_latent), axis=1)
    context['selected'] = selected
    context['probe_residuals'] = np.linalg.norm(probe_latent - center[test_slice][selected, None, :], axis=-1)
    raw_center = simplex(center, matrix)
    raw_residuals = np.abs(responses - raw_center)
    raw_probe_residuals = np.abs(simplex(probe_latent, matrix) - raw_center[test_slice][selected, None, :])
    baselines = {}
    baselines['global_ilr'] = summarize(context, residuals[calibration_slice], residuals[test_slice],
                                       context['probe_residuals'])
    baselines['raw_linf'] = summarize(context, raw_residuals[calibration_slice].max(axis=1),
                                     raw_residuals[test_slice].max(axis=1), raw_probe_residuals.max(axis=-1))
    baselines['bonferroni'] = summarize(context, raw_residuals[calibration_slice],
                                       raw_residuals[test_slice], raw_probe_residuals, coordinatewise=True)
    baselines['uncalibrated'] = summarize(context, residuals[train_slice], residuals[test_slice],
                                        context['probe_residuals'], conformal=False)
    full = summarize(context, np.ones(sizes[2]), np.zeros(sizes[3]), np.zeros((count, probes)))
    copy = summarize(context, np.zeros(sizes[2]), residuals[test_slice], context['probe_residuals'])
    if full['mass'] != 1 or any(item['coverage'] != 1 for item in full['details']):
        raise RequiredBaselineFailure('full_simplex_sanity')
    baselines['full_simplex'], baselines['copy_center'] = full, copy
    context['copy_ok'] = (copy['mass'] == float(np.mean(context['probe_residuals'] == 0))
                          and all(item['coverage'] == float(np.mean(residuals[test_slice] == 0))
                                  for item in copy['details']))
    context['baselines'] = baselines
    context['permutation'] = deranged_targets(residuals[train_slice])
    return context


def penalty():
    return dict(utility=0., marginal=1., group=1., mass=1., details=[])


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        episode_started = clock()
        work_deadline = min(episode_deadline - episode_overhead, clock() + 10.)
        current_operation, primary_failure = 'reset', None
        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc(dict(op='reset', seed=episode['seed']), timeout=timeout))
            method_deadline = reserved_method_deadline(now=clock(), episode_deadline=episode_deadline,
                methods_remaining=0, work_seconds=min(9., work_deadline - clock()), cleanup_seconds=episode_overhead)
            value = evaluate(episode, call, min(work_deadline, method_deadline))
            if clock() > episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
        finally:
            episode['duration_seconds'] = max(0., clock() - episode_started)
    return outcomes, complete


def record_failure(failure):
    if PLANE == 'search':
        fields = {name: bounded_failure_name(failure.get(name), 'unknown')
                  for name in ('component', 'category', 'operation')}
        print('episode_failure ' + ' '.join(f'{key}={value}' for key, value in fields.items()),
              file=sys.stderr, flush=True)


def evaluate_main(arguments):
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    source = Path(os.environ.get('TASK_SOURCE_DIR', Path(__file__).resolve().parent))
    root = source / 'resources' / PLANE
    hard_deadline = STARTED + WALL_SECONDS - 30
    payload_report = preflight_payloads()
    geometry_tests()
    manifest, loaded = load_resources(root, smoke)
    seeds = manifest['smoke_seeds'] if smoke else manifest['production_seeds']
    episodes = [dict(case=case, seed=seed, variant=variant, replay=False)
                for case in CASES for seed in seeds for variant in VARIANTS]
    episodes.append(dict(case=CASES[0], seed=seeds[0], variant='actual', replay=True))
    count = len(CASES) * len(seeds)
    if len(episodes) * 25 > RPC_LIMIT:
        raise ValueError('operation table exceeds RPC budget')
    contexts, preparation_failed = {}, False
    preparation_categories = {}
    productive_baseline_seconds = 0.
    baseline_reserve = count * 10
    reset_reserve = len(episodes) * 2.5
    if time.monotonic() + baseline_reserve + reset_reserve + len(episodes) * 10 + 30 > hard_deadline:
        raise TimeoutError('joint baseline/reset preflight')
    for case in CASES:
        for seed in seeds:
            try:
                productive_started = time.monotonic()
                with time_bound(productive_started + 10):
                    contexts[case, seed] = prepare_context(case, seed, loaded[case, seed], smoke)
                productive_baseline_seconds += time.monotonic() - productive_started
            except (TimeoutError, RequiredBaselineFailure, np.linalg.LinAlgError) as error:
                preparation_failed = True
                preparation_categories[case, seed] = (error.category if isinstance(error, RequiredBaselineFailure)
                    else 'baseline_timeout' if isinstance(error, TimeoutError) else 'baseline_result_failure')
                contexts[case, seed] = None
    client = Client(arguments.program_path)
    outputs, completion = {}, set()
    duration = {seed: 0. for seed in seeds}
    first_outputs = None
    replay_ok = False
    def evaluate(episode, call, deadline):
        nonlocal first_outputs, replay_ok
        started = time.monotonic()
        case, seed, variant = episode['case'], episode['seed'], episode['variant']
        context = contexts[case, seed]
        if context is None:
            raise RequiredBaselineFailure(preparation_categories[case, seed])
        covariates = context['train_x']
        residuals = context['residuals']
        if variant == 'constant':
            covariates = np.zeros_like(covariates)
        elif variant == 'permuted':
            residuals = residuals[context['permutation']]
        try:
            with time_bound(deadline):
                response = call(dict(op='fit', x=encode(covariates), residuals=encode(residuals),
                                     dimension=context['dimension'], scale_min=.0001, scale_max=10000.))
                if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
                    raise ProtocolError('fit_schema')
                calibration_x, test_x = context['calibration_x'], context['test_x']
                if variant == 'constant':
                    calibration_x, test_x = np.zeros_like(calibration_x), np.zeros_like(test_x)
                calibration_scales = scales(call(dict(op='predict', x=encode(calibration_x))), len(calibration_x))
                test_scales = scales(call(dict(op='predict', x=encode(test_x))), len(test_x))
                value = summarize(context, context['calibration_residuals'] / calibration_scales,
                                  context['test_residuals'] / test_scales,
                                  context['probe_residuals'] / test_scales[context['selected'], None])
                if episode['replay']:
                    replay_ok = (first_outputs is not None
                                 and np.allclose(calibration_scales, first_outputs[0], rtol=1e-10, atol=1e-12)
                                 and np.allclose(test_scales, first_outputs[1], rtol=1e-10, atol=1e-12)
                                 and math.isclose(value['utility'], first_outputs[2], rel_tol=1e-10, abs_tol=1e-12))
                else:
                    outputs[case, seed, variant] = (calibration_scales, test_scales)
                    completion.add((case, seed, variant))
                    if case == CASES[0] and seed == seeds[0] and variant == 'actual':
                        first_outputs = (calibration_scales.copy(), test_scales.copy(), value['utility'])
                return value
        finally:
            duration[seed] += time.monotonic() - started
    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=30, reset_timeout=1,
            episode_overhead=1.5, rpc_cap=3, clock=time.monotonic, rpc=client.call,
            evaluate=evaluate, worst_case=lambda episode: penalty(), record_failure=record_failure)
    finally:
        client.close()
    if client.resets != [episode['seed'] for episode in episodes]:
        complete = False
    table = {(episode['case'], episode['seed'], episode['variant']): value
             for episode, value in zip(episodes[:-1], outcomes[:-1])}
    completion.intersection_update(key for key, value in table.items() if value['details'])
    replay_ok = replay_ok and bool(outcomes[-1]['details'])
    duration = {seed: sum(episode.get('duration_seconds', 0.) for episode in episodes if episode['seed'] == seed)
                for seed in seeds}
    control_passes, control_valid = int(replay_ok), {}
    for case in CASES:
        for seed in seeds:
            context = contexts[case, seed]
            key = (case, seed)
            constant_ok = False
            if (*key, 'constant') in completion and context is not None:
                calibration_scales, test_scales = outputs[*key, 'constant']
                joined = np.concatenate((calibration_scales, test_scales))
                value = table[*key, 'constant']
                reference = context['baselines']['global_ilr']
                constant_ok = (np.allclose(joined, joined[0], rtol=1e-10, atol=1e-12)
                               and all(math.isclose(value[field], reference[field], rel_tol=1e-10, abs_tol=1e-12)
                                       for field in ('utility', 'marginal', 'group', 'mass')))
            if not constant_ok:
                table[*key, 'constant'] = penalty()
            permutation_ok = (*key, 'permuted') in completion and context is not None
            copy_ok = context is not None and context['copy_ok']
            control_passes += int(constant_ok) + int(permutation_ok) + int(copy_ok)
            control_valid[key] = constant_ok and permutation_ok and copy_ok
    control_fraction = control_passes / (3 * count + 1)
    def mean_field(variant, field):
        return float(np.mean([table[case, seed, variant][field] for case in CASES for seed in seeds]))
    gaps = [table[case, seed, 'actual']['utility'] - contexts[case, seed]['baselines']['global_ilr']['utility']
            if contexts[case, seed] is not None and (case, seed, 'actual') in completion else -1.
            for case in CASES for seed in seeds]
    metrics = dict(combined_score=mean_field('actual', 'utility') * control_fraction,
                   marginal_coverage_error=mean_field('actual', 'marginal'),
                   group_coverage_error=mean_field('actual', 'group'), reference_mass=mean_field('actual', 'mass'),
                   global_ilr_score_gap=float(np.mean(gaps)), constant_control_score=mean_field('constant', 'utility'),
                   permuted_control_score=mean_field('permuted', 'utility'), control_pass_fraction=control_fraction)
    seed_scores = np.array([[table[case, seed, 'actual']['utility'] for seed in seeds] for case in CASES])
    bootstrap = np.random.default_rng(67219).integers(0, len(seeds), size=(2000, len(seeds)))
    sampled = seed_scores[:, bootstrap].mean(axis=(0, 2)) * control_fraction
    paired_intervals = {}
    for comparison in ('global_ilr', 'raw_linf', 'bonferroni', 'uncalibrated', 'constant', 'permuted'):
        paired = np.array([[table[case, seed, 'actual']['utility'] - (
            table[case, seed, comparison]['utility'] if comparison in VARIANTS
            else contexts[case, seed]['baselines'][comparison]['utility'])
            if contexts[case, seed] is not None and (case, seed, 'actual') in completion
               and (comparison not in VARIANTS or ((case, seed, comparison) in completion
                                                    and table[case, seed, comparison]['details'])) else -1.
            for seed in seeds] for case in CASES])
        paired_intervals[comparison] = list(map(float, np.quantile(paired[:, bootstrap].mean(axis=(0, 2)), [.025, .975])))
    if PLANE == 'final':
        metrics['combined_score_ci_low'], metrics['combined_score_ci_high'] = map(float, np.quantile(sampled, [.025, .975]))
    feasible = (complete and not preparation_failed and len(completion) == 3 * count
                and control_fraction == 1 and time.monotonic() < hard_deadline)
    correct = feasible and control_fraction == 1 and not smoke
    evidence = []
    for seed in seeds:
        solutions = []
        for case in CASES:
            context = contexts[case, seed]
            solutions.append(dict(case=case,
                                  variants={variant: table[case, seed, variant] for variant in VARIANTS},
                                  baselines=context['baselines'] if context is not None else {},
                                  controls_valid=control_valid[case, seed]))
        evidence.append(dict(seed=seed, score=float(np.mean([table[case, seed, 'actual']['utility']
                                                            for case in CASES])) * control_fraction,
                             correct=bool(all(control_valid[case, seed] and (case, seed, 'actual') in completion
                                              for case in CASES) and replay_ok and not smoke),
                             duration_seconds=duration[seed], solution=dict(cases=solutions,
                                 manifest_sha256=hashlib.sha256((root / 'manifest.json').read_bytes()).hexdigest(),
                                 paired_seed_intervals=paired_intervals,
                                 serialized_payload_preflight=payload_report,
                                 productive_baseline_seconds=productive_baseline_seconds)))
    write_results(arguments.results_dir, metrics, bool(correct), bool(feasible and not smoke),
                  dict(schema_version=1, episodes=evidence))


def worst_metrics():
    values = dict(combined_score=0., marginal_coverage_error=1., group_coverage_error=1., reference_mass=1.,
                  global_ilr_score_gap=-1., constant_control_score=0., permuted_control_score=0.,
                  control_pass_fraction=0.)
    if PLANE == 'final':
        values.update(combined_score_ci_low=0., combined_score_ci_high=1.)
    return values


def write_results(directory, metrics, correct, feasible, evidence=None):
    if set(metrics) != set(METRICS) or not all(type(value) in (int, float) and math.isfinite(value)
                                             for value in metrics.values()):
        raise ValueError('metric schema')
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'metrics.json').write_bytes(bounded_json_line(metrics))
    (directory / 'correct.json').write_bytes(bounded_json_line(dict(correct=correct)))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (directory / 'qualification.json').write_bytes(bounded_json_line(dict(schema_version=1, feasible=feasible)))
    if evidence is not None:
        (directory / 'evaluation_evidence.json').write_bytes(bounded_json_line(evidence, 16 * 1024 * 1024))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    try:
        evaluate_main(arguments)
    except Exception as error:
        write_results(arguments.results_dir, worst_metrics(), False, False)
        if PLANE == 'search':
            name = bounded_failure_name(type(error).__name__.lower(), 'evaluator_exception')
            print(f'evaluator_exception type={name} message=evaluation_failed', file=sys.stderr)
        else:
            print('evaluator_exception type=runtime_error message=sealed_evaluation_failed', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
