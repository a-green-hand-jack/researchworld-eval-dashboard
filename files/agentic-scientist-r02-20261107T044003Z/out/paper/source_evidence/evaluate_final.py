"""Standalone evaluator; all candidate measurements are reconstructed privately.

Frozen resources include raw numeric SHA256 inventories before any ILR/features.
Candidate/evaluator communication never conveys filesystem names or private targets.
"""
import argparse
import base64
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
import subprocess
import sys
import tempfile
import threading
import time

STARTED = time.monotonic()
CPU_IDS = sorted(os.sched_getaffinity(0))
NATIVE_CPU_IDS = CPU_IDS[4:8] if len(CPU_IDS) >= 8 else CPU_IDS[:4]
os.sched_setaffinity(0, CPU_IDS[:4])
for THREAD_NAME in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[THREAD_NAME] = '4'
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import numpy as np

PLANE = 'final'
SEEDS = [1009, 2027, 3049, 4051, 5059]
COUNTS = (4096, 2048, 3840)
PROBES = 4096
WALL_SECONDS = 3600
RPC_BUDGET = 775
METRICS = ['combined_score', 'marginal_coverage', 'normalized_volume', 'worst_stratum_coverage', 'coverage_gap_vs_euclidean', 'volume_gain_vs_euclidean', 'coverage_gap_vs_ilr', 'volume_gain_vs_ilr']
CHUNK = 1048576
MAX_CHUNKS = 4
WIRE_LIMIT = 8 * 1024 * 1024
CASE_IDS = ('C1', 'C2', 'C3', 'C4', 'C5', 'C6')
REPAIR = PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                              or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')


class ProtocolError(RuntimeError):
    pass


class FatalTransportError(RuntimeError):
    pass


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
    import re
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value) else fallback


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {'component': 'candidate', 'category': 'invalid_reset_response', 'operation': 'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component': 'baseline', 'category': context.category, 'operation': 'baseline_worker'}
        if isinstance(context, ProtocolError):
            return {'component': 'candidate', 'category': 'protocol_error',
                    'operation': bounded_failure_name(operation, 'unknown')}
        context = context.__context__
        if context is None:
            break
    return {'component': 'candidate', 'category': 'timeout',
            'operation': bounded_failure_name(operation, 'unknown')}


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
    print(f'worker_exception type={name}\n{message}', file=sys.stderr, flush=True)


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
        times = {name: finite_budget_seconds(profile[name]) for name in (
            'wall_seconds', 'startup_seconds', 'reset_seconds', 'cleanup_seconds', 'finish_seconds')}
        work = positive_work_seconds(profile['work_seconds'])
        needed = (times['startup_seconds'] + times['finish_seconds'] + episodes * (
            times['reset_seconds'] + methods * (work + times['cleanup_seconds'])))
        finite_budget_seconds(needed)
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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0:
        raise ValueError('invalid CPU budget')
    if type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError('invalid CPU parallelism')
    return math.ceil(wall_seconds * allowed_threads)


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        'PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ',
        'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES',
        'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
        'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                       PYTHONUNBUFFERED='1')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[name] = '4'
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


def reject_constant(value):
    raise ProtocolError('nonfinite JSON')


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolError('duplicate JSON key')
        result[key] = value
    return result


def parse_json(raw):
    try:
        return json.loads(raw, parse_constant=reject_constant, object_pairs_hook=unique_pairs)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ProtocolError('invalid JSON') from error


def bounded_json_line(value):
    try:
        raw = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    except (ValueError, TypeError, RecursionError) as error:
        raise ProtocolError('nonfinite JSON value') from error
    envelope = json.dumps({'request': value, 'id': 9223372036854775807}, allow_nan=False,
                          separators=(',', ':')).encode('utf-8') + b'\n'
    if len(raw) >= WIRE_LIMIT or len(envelope) + 1 >= WIRE_LIMIT:
        raise ProtocolError('complete message exceeds wire ceiling')
    return raw


def encode(array):
    array = np.asarray(array, dtype='<f8', order='C')
    if not np.isfinite(array).all() or array.nbytes > MAX_CHUNKS * CHUNK:
        raise ProtocolError('invalid numeric buffer')
    return {'encoding': 'base64', 'dtype': '<f8', 'shape': list(array.shape), 'nbytes': array.nbytes,
            'data': base64.b64encode(array.tobytes()).decode('ascii')}


def decode(block, expected_shape=None):
    if type(block) is not dict or set(block) != {'encoding', 'dtype', 'shape', 'nbytes', 'data'}:
        raise ProtocolError('invalid numeric block')
    shape = block['shape']
    if (type(shape) is not list or not 1 <= len(shape) <= 3
            or any(type(size) is not int or not 1 <= size <= 1000000 for size in shape)
            or block['encoding'] != 'base64' or block['dtype'] != '<f8'
            or type(block['nbytes']) is not int or type(block['data']) is not str):
        raise ProtocolError('invalid numeric metadata')
    size = 8 * math.prod(shape)
    if size > MAX_CHUNKS * CHUNK or size != block['nbytes']:
        raise ProtocolError('invalid numeric length')
    if expected_shape is not None and shape != list(expected_shape):
        raise ProtocolError('invalid numeric shape')
    try:
        raw = base64.b64decode(block['data'], validate=True)
    except (ValueError, UnicodeError) as error:
        raise ProtocolError('invalid base64') from error
    if len(raw) != size:
        raise ProtocolError('invalid base64 length')
    array = np.frombuffer(raw, dtype='<f8').reshape(shape)
    if not np.isfinite(array).all():
        raise ProtocolError('nonfinite numeric output')
    return array


def check_keys(response, keys):
    if type(response) is not dict or set(response) != set(keys):
        raise ProtocolError('unexpected response keys')


def ack(response):
    check_keys(response, ('ok',))
    if response['ok'] is not True:
        raise ProtocolError('invalid acknowledgement')


BOOTSTRAP = r'''
import base64,ctypes,errno,importlib.util,json,math,os,resource,sys
root,entry,cpu,cores = sys.argv[1:]
prefix=sys.prefix
os.sched_setaffinity(0,[int(value) for value in cores.split(',')])
resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(int(cpu),int(cpu)))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
libc=ctypes.CDLL(None,use_errno=True)
libc.syscall.restype=ctypes.c_long
class Ruleset(ctypes.Structure):
    _fields_=[('handled',ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _fields_=[('allowed',ctypes.c_uint64),('parent_fd',ctypes.c_int)]
abi=libc.syscall(444,0,0,1)
if abi<1: raise RuntimeError('Landlock unavailable')
handled=(1<<13)-1
if abi>=2: handled|=1<<13
if abi>=3: handled|=1<<14
rules=Ruleset(handled)
fd=libc.syscall(444,ctypes.byref(rules),ctypes.sizeof(rules),0)
if fd<0: raise RuntimeError('Landlock setup failed')
read=(1<<0)|(1<<2)|(1<<3)
paths=['/usr','/lib','/lib64','/etc/ld.so.cache','/dev/null','/dev/urandom',prefix,root]
for path in paths:
    if not os.path.exists(path): continue
    directory=os.path.isdir(path)
    allowed=handled if path==root else read
    if not directory: allowed&=~(1<<3)
    if path=='/dev/null': allowed|=1<<1
    path_fd=os.open(path,os.O_PATH|os.O_CLOEXEC)
    rule=PathRule(allowed,path_fd)
    if libc.syscall(445,fd,1,ctypes.byref(rule),0)<0: raise RuntimeError('Landlock rule failed')
    os.close(path_fd)
if libc.prctl(38,1,0,0,0)!=0: raise RuntimeError('no_new_privs failed')
if libc.syscall(446,fd,0)<0: raise RuntimeError('Landlock restriction failed')
os.close(fd)
class Filter(ctypes.Structure):
    _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('value',ctypes.c_uint)]
class Program(ctypes.Structure):
    _fields_=[('length',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
filters=[Filter(0x20,0,0,4),Filter(0x15,1,0,0xc000003e),Filter(0x06,0,0,0x80000000),Filter(0x20,0,0,0)]
filters.extend((Filter(0x15,0,2,435),Filter(0x06,0,0,0x00050000|errno.ENOSYS),Filter(0x20,0,0,0)))
filters.extend((Filter(0x15,0,4,56),Filter(0x20,0,0,16),Filter(0x45,1,0,0x10000),Filter(0x06,0,0,0x00050000|errno.EPERM),Filter(0x20,0,0,0)))
for number in (41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,101,155,165,166,246,272,298,304,308,310,311,321,323):
    if number==56: continue
    filters.extend((Filter(0x15,0,1,number),Filter(0x06,0,0,0x00050000|errno.EPERM)))
filters.extend((Filter(0x35,0,1,0x40000000),Filter(0x06,0,0,0x00050000|errno.EPERM),Filter(0x06,0,0,0x7fff0000)))
array=(Filter*len(filters))(*filters)
program=Program(len(filters),array)
if libc.prctl(22,2,ctypes.byref(program),0,0)!=0: raise RuntimeError('seccomp setup failed')
os.chdir(root)
sys.path.insert(0,root)
spec=importlib.util.spec_from_file_location('candidate',entry)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    if len(line)>=8*1024*1024: raise RuntimeError('request too large')
    request=json.loads(line)
    response=module.handle(request)
    encoded=json.dumps(response,allow_nan=False,separators=(',',':')).encode('utf-8')+b'\n'
    if len(encoded)>=8*1024*1024: raise RuntimeError('response too large')
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


def exchange(process, value, timeout):
    deadline = time.monotonic() + timeout
    outgoing = bounded_json_line(value)
    written = 0
    received = bytearray()
    os.set_blocking(process.stdin.fileno(), False)
    os.set_blocking(process.stdout.fileno(), False)
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdin, selectors.EVENT_WRITE)
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('worker response timeout')
            ready = selector.select(timeout=remaining)
            if not ready:
                raise TimeoutError('worker response timeout')
            for key, event in ready:
                if event & selectors.EVENT_WRITE:
                    try:
                        sent = os.write(key.fd, outgoing[written:written + 65536])
                    except (BrokenPipeError, OSError) as error:
                        raise ProtocolError('worker exited') from error
                    written += sent
                    if written == len(outgoing):
                        selector.unregister(process.stdin)
                if event & selectors.EVENT_READ:
                    chunk = os.read(key.fd, 65536)
                    if not chunk:
                        raise ProtocolError('worker exited')
                    received.extend(chunk)
                    if len(received) >= WIRE_LIMIT:
                        raise ProtocolError('worker message too large')
                    if b'\n' in received:
                        line, trailing = received.split(b'\n', 1)
                        if trailing or written != len(outgoing):
                            raise ProtocolError('unsolicited worker output')
                        value = parse_json(line)
                        bounded_json_line(value)
                        return value


class Worker:
    def __init__(self, arguments, environment, cwd=None):
        self.process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, env=environment, cwd=cwd,
                                        start_new_session=True, shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        self.closed = False
        self.snapshot = None
        self.exit_status = None
        self.forwarded = False

    def request(self, value, timeout):
        return exchange(self.process, value, timeout)

    def close(self, failed=False):
        if self.closed:
            if failed and REPAIR and self.snapshot and self.snapshot['stderr'] and not self.forwarded:
                self.forwarded = True
                print(self.snapshot['stderr'], end='', file=sys.stderr, flush=True)
            return
        self.closed = True
        process = self.process
        try:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=1)
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            self.exit_status = process.returncode
        finally:
            process.stdin.close()
            process.stdout.close()
            self.snapshot = self.capture.close()
            if failed and REPAIR and self.snapshot['stderr']:
                self.forwarded = True
                print(self.snapshot['stderr'], end='', file=sys.stderr, flush=True)


class Candidate:
    def __init__(self, path, work_seconds, reset_seconds):
        self.path = path
        self.calls = 0
        self.resets = []
        self.worker = None
        self.directory = None
        self.work_seconds = work_seconds
        self.reset_seconds = reset_seconds
        self.proxy = None
        fixed_proxy = '/broker-code/candidate_proxy.py'
        socket = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        if socket or str(path) == fixed_proxy:
            if not socket or str(path) != fixed_proxy:
                raise ProtocolError('broker requires both fixed proxy path and socket')
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', fixed_proxy)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle

    def start_native(self, deadline):
        self.directory = tempfile.TemporaryDirectory(prefix='composition-candidate-', dir='/tmp')
        root = Path(self.directory.name)
        source = Path(self.path).absolute()
        total = 0
        count = 0
        for entry_index, path in enumerate(source.parent.rglob('*')):
            if entry_index >= 512 or time.monotonic() >= deadline:
                raise TimeoutError('candidate preparation budget exhausted')
            if path.is_symlink():
                raise ProtocolError('candidate symlinks forbidden')
            if path.is_file():
                total += path.stat().st_size
                count += 1
                if total > 32 * 1024 * 1024 or count > 256:
                    raise ProtocolError('candidate source too large')
                relative = path.relative_to(source.parent)
                destination = root / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        interpreter, environment = candidate_subprocess_settings(os.environ)
        cpu = cpu_limit_seconds(self.work_seconds + self.reset_seconds + 3, 4)
        arguments = [interpreter, '-I', '-u', '-c', BOOTSTRAP, str(root), str(root / source.name), str(cpu), ','.join(map(str, NATIVE_CPU_IDS))]
        self.worker = Worker(arguments, environment, str(root))

    def rpc(self, request, timeout):
        deadline = time.monotonic() + timeout
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolError('RPC budget exceeded')
        bounded_json_line(request)
        if request['op'] == 'reset':
            self.resets.append(request['seed'])
            if self.proxy is None:
                self.start_native(deadline)
        if self.proxy is not None:
            def timed_out(signum, frame):
                raise TimeoutError('broker RPC budget exhausted')
            previous_handler = signal.signal(signal.SIGALRM, timed_out)
            previous_timer = signal.setitimer(signal.ITIMER_REAL, max(.001, deadline - time.monotonic()))
            try:
                response = self.proxy(request)
            except TimeoutError:
                raise
            except (ConnectionError, EOFError, OSError) as error:
                raise FatalTransportError('broker transport failure') from error
            finally:
                signal.setitimer(signal.ITIMER_REAL, *previous_timer)
                signal.signal(signal.SIGALRM, previous_handler)
            bounded_json_line(response)
            if time.monotonic() > deadline:
                raise TimeoutError('broker RPC budget exhausted')
            return response
        if self.worker is None:
            raise ProtocolError('candidate process unavailable')
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('candidate preparation budget exhausted')
        return self.worker.request(request, remaining)

    def close(self, failed=False):
        try:
            if self.worker is not None:
                self.worker.close(failed)
        finally:
            self.worker = None
            if self.directory is not None:
                self.directory.cleanup()
                self.directory = None


def ilr_basis(size):
    basis = np.zeros((size, size - 1))
    for index in range(size - 1):
        scale = math.sqrt((index + 1) * (index + 2))
        basis[:index + 1, index] = 1 / scale
        basis[index + 1, index] = -(index + 1) / scale
    return basis


def inverse_ilr(coordinates, basis):
    logits = coordinates @ basis.T
    logits -= logits.max(axis=-1, keepdims=True)
    components = np.exp(logits)
    return components / components.sum(axis=-1, keepdims=True)


def features(covariates):
    columns = [np.ones(len(covariates))]
    columns.extend(covariates[:, index] for index in range(5))
    columns.extend(covariates[:, index] ** 2 for index in range(5))
    columns.extend(covariates[:, first] * covariates[:, second]
                   for first in range(5) for second in range(first))
    return np.column_stack(columns)


def ridge(design, targets):
    return np.linalg.solve(design.T @ design + 0.01 * np.eye(design.shape[1]), design.T @ targets)


def baseline_worker():
    request = parse_json(sys.stdin.buffer.readline(WIRE_LIMIT))
    try:
        resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
        limit = cpu_limit_seconds(request['work_seconds'], 4)
        resource.setrlimit(resource.RLIMIT_CPU, (limit, limit))
        covariates = decode(request['x'])
        responses = decode(request['y'])
        query = decode(request['query'])
        basis = ilr_basis(responses.shape[1])
        productive_began = time.monotonic()
        cut = 3 * len(covariates) // 4
        targets = np.log(responses) @ basis if request['method'] == 'ilr' else responses
        coefficients = ridge(features(covariates[:cut]), targets[:cut])
        prediction = features(query) @ coefficients
        if request['method'] == 'euclidean':
            prediction = np.maximum(prediction, 1e-12)
            prediction /= prediction.sum(axis=1, keepdims=True)
        productive_seconds = time.monotonic() - productive_began
        sys.stdout.buffer.write(bounded_json_line({'prediction': encode(prediction),
                                                 'productive_seconds': productive_seconds}))
        sys.stdout.buffer.flush()
    except Exception as error:
        if PLANE == 'search' and request.get('repair'):
            report_worker_exception(error)
        else:
            print('baseline_worker_failure', file=sys.stderr, flush=True)
        raise SystemExit(1)


def run_baseline(method, covariates, responses, query, deadline, record):
    interpreter, environment = candidate_subprocess_settings(os.environ)
    worker = Worker([interpreter, '-I', '-u', str(Path(__file__).absolute()), '--baseline-worker'], environment)
    failed = True
    diagnostic = None

    def category():
        status = worker.process.poll()
        if status is not None and status != 0:
            return 'baseline_signal' if status < 0 else 'baseline_exit'
        return None

    def note(value):
        nonlocal diagnostic
        diagnostic = value
        record_failure({'component': 'baseline', 'category': value, 'operation': 'baseline_worker'}, record)

    def result(timeout):
        request = {'method': method, 'x': encode(covariates), 'y': encode(responses),
                   'query': encode(query), 'work_seconds': max(1, deadline - time.monotonic()), 'repair': REPAIR}
        guarded = guard_required_baseline(lambda item: worker.request(item, timeout), category, worker.close, note)
        try:
            response = guarded(request)
        except ProtocolError:
            try:
                worker.process.wait(timeout=min(.1, max(.001, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                pass
            fail_required_baseline(category() or 'baseline_result_failure', worker.close, note)
        shape = (len(query), responses.shape[1] - (method == 'ilr'))
        try:
            check_keys(response, ('prediction', 'productive_seconds'))
            prediction = decode(response['prediction'], shape)
            productive = response['productive_seconds']
            if type(productive) not in (int, float) or not math.isfinite(productive) or productive <= 0:
                raise ProtocolError('invalid trusted baseline measurement')
            record.setdefault('baseline_productive_seconds', {})[method] = productive
        except ProtocolError:
            fail_required_baseline('baseline_result_failure', worker.close, note)
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError()
        try:
            worker.process.wait(timeout=remaining)
        except subprocess.TimeoutExpired:
            raise TimeoutError() from None
        if category() is not None:
            fail_required_baseline(category(), worker.close, note)
        return prediction.copy()

    try:
        value = collect_required_baseline(result, deadline=deadline, clock=time.monotonic,
                                          cancel_work=worker.close, record_failure=note)
        failed = False
        return value
    finally:
        original = sys.exception()
        try:
            worker.close(failed)
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            record_secondary_failure({'component': 'baseline', 'category': 'cleanup_failure',
                                      'operation': 'cleanup'}, record)
            if original is None:
                raise
        if failed:
            record['worker_failure'] = {'category': diagnostic or category() or 'baseline_result_failure',
                                        'exit_status': worker.exit_status,
                                        'capture': {key: value for key, value in (worker.snapshot or {}).items()
                                                    if key != 'stderr'}}


def normalize_numeric_row(row):
    array = np.asarray(row, dtype='<f8').copy()
    if not np.isfinite(array).all():
        raise ValueError('nonfinite raw content')
    array[array == 0] = 0.0
    return len(array).to_bytes(4, 'little') + array.tobytes()


def raw_hashes(covariates, responses):
    return {name: [hashlib.sha256(normalize_numeric_row(row)).hexdigest() for row in rows]
            for name, rows in (('example', np.column_stack((covariates, responses))),
                               ('covariates', covariates), ('response', responses))}


def private_rng(private_entropy, domain):
    if type(private_entropy) is not bytes or len(private_entropy) != 32:
        raise ValueError('private corpus entropy must contain 256 bits')
    digest = hashlib.sha256(b'compositional-corpus-v2\0' + domain.encode('ascii')
                            + b'\0' + private_entropy).digest()
    return np.random.default_rng(int.from_bytes(digest, 'little'))


def generate_raw(family, counts, *, private_entropy):
    training, calibration, testing = counts
    rows = sum(counts)
    size = 3 if family <= 2 else 8
    parameter_rng = private_rng(private_entropy, f'family{family}/parameters')
    input_rng = private_rng(private_entropy, f'family{family}/covariates')
    response_rng = private_rng(private_entropy, f'family{family}/responses')
    covariates = input_rng.normal(size=(rows, 5))
    if family == 4:
        covariates[training + calibration:, 0] += 1.5
        covariates[training + calibration:, 1] *= 1.5
    coefficients = parameter_rng.normal(0, .35, size=(5, size - 1))
    mean = covariates @ coefficients + .2 * covariates[:, :1] ** 2
    if family <= 2:
        scale = np.full((rows, size - 1), .35)
        if family == 2:
            scale *= np.exp(.65 * np.clip(covariates[:, :1], -3, 3))
            scale *= np.linspace(.5, 1.5, size - 1)
        coordinates = mean + scale * response_rng.normal(size=mean.shape)
        responses = inverse_ilr(coordinates, ilr_basis(size))
    else:
        if family == 3:
            mean[:, 0] += 2.3
        proportions = inverse_ilr(mean, ilr_basis(size))
        concentration = np.maximum(proportions * (3 if family == 3 else 14), .15)
        responses = response_rng.gamma(concentration)
        invalid = (responses <= 0).any(axis=1) | ~np.isfinite(responses).all(axis=1)
        for _ in range(16):
            if not invalid.any():
                break
            responses[invalid] = response_rng.gamma(concentration[invalid])
            invalid = (responses <= 0).any(axis=1) | ~np.isfinite(responses).all(axis=1)
        if invalid.any():
            raise ValueError('invalid synthetic draw')
        responses /= responses.sum(axis=1, keepdims=True)
    if (responses <= 0).any() or not np.isfinite(responses).all():
        raise ValueError('invalid composition')
    return covariates.astype('<f8'), responses.astype('<f8')


def load_resources(root, deadline):
    manifest = json.loads((root / 'manifest.json').read_text())
    if manifest['plane'] != PLANE or manifest['seeds'] != SEEDS or manifest['counts'] != list(COUNTS):
        raise ValueError('resource configuration mismatch')
    if manifest['corpus_rng']['version'] != 2 or manifest['corpus_rng']['reset_seed_is_data_seed'] is not False:
        raise ValueError('private corpus RNG provenance required')
    if not manifest['cross_plane_audit']['disjoint']:
        raise ValueError('raw content overlaps')
    datasets = {}
    inventories = {name: set() for name in ('example', 'covariates', 'response')}
    for item in manifest['datasets']:
        if time.monotonic() >= deadline:
            raise TimeoutError('resource validation deadline')
        filename = item['file']
        if Path(filename).name != filename or not filename.endswith('.npz'):
            raise ValueError('invalid resource member')
        path = root / filename
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('resource digest mismatch')
        with np.load(path, allow_pickle=False) as stored:
            covariates, responses = stored['x'], stored['y']
            entropy = stored['generation_entropy']
            if entropy.dtype != np.dtype('uint8') or entropy.shape != (32,):
                raise ValueError('invalid private corpus entropy')
            entropy = entropy.tobytes()
            hashes = raw_hashes(covariates, responses)
            if covariates.shape != (sum(COUNTS), 5) or responses.shape != (sum(COUNTS), item['dimension']):
                raise ValueError('invalid raw shape')
            if not np.all(responses > 0) or not np.allclose(responses.sum(axis=1), 1, atol=1e-12, rtol=0):
                raise ValueError('invalid raw simplex')
            for name, values in hashes.items():
                if values != stored['hash_' + name].tolist() or len(set(values)) != len(values):
                    raise ValueError('raw inventory mismatch or duplicate')
                if inventories[name].intersection(values):
                    raise ValueError('raw examples overlap under different source IDs')
                inventories[name].update(values)
        datasets[(item['case'], item['seed'])] = (covariates, responses, entropy)
    expected = {(case, seed) for case in CASE_IDS[:4] for seed in SEEDS}
    if set(datasets) != expected:
        raise ValueError('incomplete frozen resources')
    return datasets


def quantile(scores, alpha=.1):
    rank = math.ceil((len(scores) + 1) * (1 - alpha))
    if rank > len(scores):
        return math.inf, rank
    return float(np.partition(scores, rank - 1)[rank - 1]), rank


def check_deadline(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError('evaluator work deadline')


def wilson(successes, total):
    if total == 0:
        return [0.0, 1.0]
    fraction = successes / total
    zvalue = 1.959963984540054
    denominator = 1 + zvalue**2 / total
    center = (fraction + zvalue**2 / (2 * total)) / denominator
    half = zvalue * math.sqrt(fraction * (1 - fraction) / total + zvalue**2 / (4 * total**2)) / denominator
    return [max(0., center - half), min(1., center + half)]


def region_statistics(method, locations, factors, calibration_y, testing_y, basis, probes,
                      query_x, anchors, deadline):
    calibration_count = len(calibration_y)
    testing_count = len(testing_y)
    calibration_locations = locations[:calibration_count]
    testing_locations = locations[calibration_count:calibration_count + testing_count]
    if method == 'euclidean':
        scores = np.linalg.norm(calibration_y - calibration_locations, axis=1)
        test_scores = np.linalg.norm(testing_y - testing_locations, axis=1)
        points = testing_locations
    else:
        calibration_z = np.log(calibration_y) @ basis
        testing_z = np.log(testing_y) @ basis
        if factors is None:
            scores = np.linalg.norm(calibration_z - calibration_locations, axis=1)
            test_scores = np.linalg.norm(testing_z - testing_locations, axis=1)
        else:
            scores = np.linalg.norm(np.linalg.solve(factors[:calibration_count],
                                  (calibration_z - calibration_locations)[..., None])[..., 0], axis=1)
            test_scores = np.linalg.norm(np.linalg.solve(
                factors[calibration_count:calibration_count + testing_count],
                (testing_z - testing_locations)[..., None])[..., 0], axis=1)
        points = inverse_ilr(testing_locations, basis)
    radius, rank = quantile(scores)
    covered = test_scores <= radius
    volumes = []
    volume_memberships = []
    integration_errors = []
    probe_coordinates = np.log(probes) @ basis if method != 'euclidean' else probes
    for index in range(anchors):
        check_deadline(deadline)
        offset = calibration_count + testing_count + index
        difference = probe_coordinates[index] - locations[offset]
        if method != 'euclidean' and factors is not None:
            difference = np.linalg.solve(factors[offset], difference.T).T
        membership = np.linalg.norm(difference, axis=1) <= radius
        volume_memberships.append(membership)
        fraction = float(membership.mean())
        volumes.append(fraction)
        integration_errors.append(fraction * (1 - fraction) / len(membership))
    volume = float(np.mean(volumes))
    coverage = float(covered.mean())
    test_x = query_x[calibration_count:calibration_count + testing_count]
    strata = []
    for column, threshold in ((0, 0.), (1, 0.)):
        for positive in (False, True):
            mask = test_x[:, column] >= threshold if positive else test_x[:, column] < threshold
            strata.append(float(covered[mask].mean()) if mask.any() else 0.)
    return {'coverage': coverage, 'volume': volume, 'strata': strata,
            '_volume_memberships': np.array(volume_memberships),
            'volume_mc_se': math.sqrt(sum(integration_errors)) / anchors,
            'volume_by_anchor': volumes, 'point_mse': float(np.mean(np.sum((points - testing_y)**2, axis=1))),
            'coverage_wilson95': wilson(int(covered.sum()), testing_count), 'calibration_rank': rank,
            'radius': None if math.isinf(radius) else radius,
            'coverage_indicators': covered.astype(int).tolist(),
            'utility': 1 - .8 * max(0., .9 - coverage) / .9 - .2 * volume}


def require_controls(expected, completed):
    if set(expected) - set(completed):
        raise ProtocolError('required control incomplete')


def evaluator_controls(locations, factors, testing_y, basis, probes):
    points = inverse_ilr(locations, basis)
    roundtrip = np.log(points) @ basis
    if not np.allclose(roundtrip, locations, atol=1e-8, rtol=1e-8):
        raise ProtocolError('ILR inverse inconsistent')
    singleton = np.linalg.norm(testing_y - points, axis=1) <= 0.0
    exact = np.all(testing_y == points, axis=1)
    if not np.array_equal(singleton, exact) or singleton.mean() > .01:
        raise ProtocolError('point-copy singleton control failed')
    if not np.all(probes > 0) or not np.allclose(probes.sum(axis=-1), 1, atol=1e-12):
        raise ProtocolError('full-simplex control failed')
    if not np.all(testing_y >= 0) or not np.allclose(testing_y.sum(axis=-1), 1, atol=1e-12):
        raise ProtocolError('full-simplex membership failed')
    simplex_test = (testing_y >= 0).all(axis=1) & np.isclose(testing_y.sum(axis=1), 1., atol=1e-12)
    simplex_probes = (probes >= 0).all(axis=-1) & np.isclose(probes.sum(axis=-1), 1., atol=1e-12)
    return {'point_copy': {'coverage': float(singleton.mean()), 'volume': 0.},
            'full_simplex': {'coverage': float(simplex_test.mean()), 'volume': float(simplex_probes.mean())}}


def training_transfer(call, covariates, responses, basis):
    flat = np.concatenate((covariates.ravel(), responses.ravel())).astype('<f8')
    chunks = math.ceil(flat.nbytes / CHUNK)
    ack(call({'op': 'fit_start', 'n_rows': len(covariates), 'composition_dim': responses.shape[1],
              'ilr_basis': basis.tolist(), 'alpha': .1, 'nbytes': flat.nbytes, 'chunks': chunks}))
    for index in range(chunks):
        block = flat[index * (CHUNK // 8):(index + 1) * (CHUNK // 8)]
        ack(call({'op': 'fit_chunk', 'index': index, 'block': encode(block)}))
    ack(call({'op': 'fit_commit'}))


def prediction_transfer(call, query, dimension):
    descriptor = call({'op': 'predict_start', 'x': encode(query)})
    check_keys(descriptor, ('n_rows', 'dimension', 'nbytes', 'chunks', 'encoding', 'dtype', 'shape'))
    columns = dimension + dimension**2
    size = len(query) * columns * 8
    expected = {'n_rows': len(query), 'dimension': dimension, 'nbytes': size,
                'chunks': math.ceil(size / CHUNK), 'encoding': 'base64', 'dtype': '<f8',
                'shape': [len(query), columns]}
    if descriptor != expected or any(type(descriptor[name]) is not int for name in ('n_rows', 'dimension', 'nbytes', 'chunks')):
        raise ProtocolError('invalid prediction descriptor')
    if descriptor['chunks'] > MAX_CHUNKS:
        raise ProtocolError('prediction too large')
    blocks = []
    for index in range(descriptor['chunks']):
        response = call({'op': 'predict_chunk', 'index': index})
        check_keys(response, ('block',))
        values = min(CHUNK, size - index * CHUNK) // 8
        blocks.append(decode(response['block'], (values,)))
    array = np.concatenate(blocks).reshape(len(query), columns)
    locations = array[:, :dimension]
    factors = array[:, dimension:].reshape(len(query), dimension, dimension)
    if np.max(np.abs(array)) > 1e6 or np.any(np.abs(np.triu(factors, 1)) > 1e-12):
        raise ProtocolError('invalid predictor bounds or triangular shape')
    if np.any(np.diagonal(factors, axis1=1, axis2=2) < 1e-8):
        raise ProtocolError('nonpositive shape')
    singular = np.linalg.svd(factors, compute_uv=False)
    if np.any(singular[:, 0] / singular[:, -1] > 1e10):
        raise ProtocolError('ill-conditioned shape')
    ack(call({'op': 'predict_release'}))
    return locations, factors


def make_episode_data(episode, datasets, smoke):
    case, seed = episode['case'], episode['seed']
    parent = 'C2' if case in ('C5', 'C6') else case
    all_x, all_y, _ = datasets[(parent, seed)]
    counts = (64, 64, 128) if smoke else COUNTS
    starts = (0, COUNTS[0], COUNTS[0] + COUNTS[1])
    pieces_x = [all_x[start:start + count].copy() for start, count in zip(starts, counts)]
    pieces_y = [all_y[start:start + count].copy() for start, count in zip(starts, counts)]
    completed = []
    if case == 'C5':
        for values in pieces_x:
            values.fill(0)
        if not all(np.array_equal(values, np.zeros_like(values)) for values in pieces_x):
            raise ValueError('constant intervention failed')
        if not np.any(all_x):
            raise ValueError('vacuous constant intervention')
        completed.append('constant_input')
    if case == 'C6':
        permutation = np.roll(np.arange(len(pieces_x[0])), 1)
        if np.any(permutation == np.arange(len(permutation))):
            raise ValueError('vacuous permutation')
        original = pieces_x[0].copy()
        pieces_x[0] = pieces_x[0][permutation]
        if np.any(np.all(original == pieces_x[0], axis=1)):
            raise ValueError('vacuous training derangement')
        completed.append('training_derangement')
    anchors = 8 if smoke else 64
    indices = np.linspace(0, len(pieces_x[2]) - 1, anchors, dtype=int)
    query = np.concatenate((pieces_x[1], pieces_x[2], pieces_x[2][indices]))
    return pieces_x[0], pieces_y[0], pieces_y[1], pieces_y[2], query, anchors, completed


def worst_case(episode):
    return {'case': episode['case'], 'seed': episode['seed'], 'complete': False, 'score': 0.,
            'coverage': 0., 'volume': 1., 'strata': [0.] * 4,
            'gaps': [-1.] * 4, 'duration_seconds': 0., 'details': None}


def record_failure(failure, record):
    if record.get('_failure_emitted'):
        return
    record['_failure_emitted'] = True
    safe = {key: bounded_failure_name(failure.get(key), 'unknown')
            for key in ('component', 'category', 'operation')}
    record['failure'] = safe
    if PLANE == 'search':
        print('episode_failure component={component} category={category} operation={operation}'.format(**safe)[:256],
              file=sys.stderr, flush=True)


def record_secondary_failure(failure, record):
    safe = {key: bounded_failure_name(failure.get(key), 'unknown')
            for key in ('component', 'category', 'operation')}
    record.setdefault('secondary_failures', []).append(safe)
    if PLANE == 'search':
        print('episode_secondary_failure component={component} category={category} operation={operation}'.format(**safe),
              file=sys.stderr, flush=True)


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure, cleanup):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        began = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = 'reset'
        primary_failure = None
        record = outcomes[index]
        failed = True

        def retain_failure():
            nonlocal record
            retained = worst_case(episode)
            for key in ('failure', '_failure_emitted', 'worker_failure', 'secondary_failures',
                        'baseline_productive_seconds'):
                if key in record:
                    retained[key] = record[key]
            outcomes[index] = retained
            record = retained

        def call(request, *, deadline=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock(),
                              (deadline - clock()) if deadline is not None else rpc_cap)
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                response = rpc(request, timeout=timeout)
                if deadline is not None and clock() > deadline:
                    raise TimeoutError('method work budget exhausted')
                return response
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc({'op': 'reset', 'seed': episode['seed']}, timeout=timeout))
            value = evaluate(episode, call, work_deadline, record)
            if clock() > work_deadline:
                raise TimeoutError('episode work deadline exceeded')
            outcomes[index] = value
            record = value
            failed = False
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            retain_failure()
            record_failure(failure, record)
        except FatalTransportError as error:
            complete = False
            retain_failure()
            record_failure({'component': 'broker', 'category': 'transport_failure',
                            'operation': bounded_failure_name(current_operation, 'unknown')}, record)
            error.outcomes = outcomes
            raise
        finally:
            original = sys.exception()
            try:
                cleanup(failed)
            except FatalTransportError as error:
                complete = False
                retain_failure()
                record_secondary_failure({'component': 'broker', 'category': 'transport_failure',
                                          'operation': 'cleanup'}, record)
                record['duration_seconds'] = max(0., clock() - began)
                error.outcomes = outcomes
                raise
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                complete = False
                if not failed:
                    retain_failure()
                    record_failure({'component': 'candidate', 'category': 'cleanup_failure',
                                    'operation': 'cleanup'}, record)
                else:
                    record_secondary_failure({'component': 'candidate', 'category': 'cleanup_failure',
                                              'operation': 'cleanup'}, record)
            record['duration_seconds'] = max(0., clock() - began)
        if clock() > episode_deadline:
            complete = False
            retain_failure()
            record['duration_seconds'] = max(0., clock() - began)
            failure = {'component': 'candidate', 'category': 'timeout', 'operation': 'cleanup'}
            if 'failure' in record:
                record_secondary_failure(failure, record)
            else:
                record_failure(failure, record)
    return outcomes, complete


def evaluate_episode(episode, call, deadline, record, *, datasets, smoke, work_seconds):
    covariates, training_y, calibration_y, testing_y, query, anchors, completed = make_episode_data(episode, datasets, smoke)
    dimension = training_y.shape[1] - 1
    basis = ilr_basis(dimension + 1)
    expected = ['query_invariance', 'point_copy', 'full_simplex']
    if episode['case'] == 'C5':
        expected.append('constant_input')
    if episode['case'] == 'C6':
        expected.append('training_derangement')
    methods = {}
    for index, method in enumerate(('euclidean', 'ilr')):
        method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                            methods_remaining=2 - index, work_seconds=work_seconds, cleanup_seconds=3)
        methods[method] = run_baseline(method, covariates, training_y, query, method_deadline, record)
    method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                        methods_remaining=0, work_seconds=work_seconds, cleanup_seconds=3)

    def candidate_call(request):
        return call(request, deadline=method_deadline)

    training_transfer(candidate_call, covariates, training_y, basis)
    locations, factors = prediction_transfer(candidate_call, query, dimension)
    permutation = np.arange(min(16, len(query)))[::-1]
    reordered_locations, reordered_factors = prediction_transfer(candidate_call, query[permutation], dimension)
    subset = permutation[::3]
    subset_locations, subset_factors = prediction_transfer(candidate_call, query[subset], dimension)
    for actual, reference in ((reordered_locations, locations[permutation]),
                              (reordered_factors, factors[permutation]),
                              (subset_locations, locations[subset]), (subset_factors, factors[subset])):
        if not np.allclose(actual, reference, rtol=1e-8, atol=1e-9):
            raise ProtocolError('predictor is not fixed and row-wise')
    completed.append('query_invariance')
    parent = 'C2' if episode['case'] in ('C5', 'C6') else episode['case']
    probe_rng = private_rng(datasets[(parent, episode['seed'])][2], 'volume_probes')
    probes = probe_rng.dirichlet(np.ones(dimension + 1), size=(anchors, 128 if smoke else PROBES))
    statistics = region_statistics('candidate', locations, factors, calibration_y, testing_y, basis,
                                  probes, query, anchors, deadline)
    references = {}
    for method, values in methods.items():
        references[method] = region_statistics(method, values, None, calibration_y, testing_y,
                                               basis, probes, query, anchors, deadline)
    start = len(calibration_y)
    stop = start + len(testing_y)
    controls = evaluator_controls(locations[start:stop], factors[start:stop], testing_y, basis, probes)
    completed.extend(('point_copy', 'full_simplex'))
    require_controls(expected, completed)
    check_deadline(deadline)
    paired_integration_se = {}
    for method, reference in references.items():
        differences = (reference['_volume_memberships'].astype(float)
                       - statistics['_volume_memberships'].astype(float))
        paired_integration_se[method] = float(np.sqrt(np.sum(np.var(differences, axis=1, ddof=1) / differences.shape[1])) / anchors)
        del reference['_volume_memberships']
    del statistics['_volume_memberships']
    gaps = [statistics['coverage'] - references['euclidean']['coverage'],
            references['euclidean']['volume'] - statistics['volume'],
            statistics['coverage'] - references['ilr']['coverage'],
            references['ilr']['volume'] - statistics['volume']]
    record.update(complete=True, score=statistics['utility'], coverage=statistics['coverage'],
                  volume=statistics['volume'], strata=statistics['strata'], gaps=gaps,
                  details={'candidate': statistics, 'baselines': references, 'controls': controls,
                           'completed_controls': completed, 'paired_volume_mc_se': paired_integration_se})
    record['_prediction'] = (locations, factors)
    return record


def fixed_weight_score(values, weights, worst_case):
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(weight) or weight < 0 for weight in weights)
            or not math.isclose(sum(weights), 1., rel_tol=0, abs_tol=1e-12)):
        raise ValueError('invalid predeclared aggregation weights')
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError('nonfinite contribution')
    return sum(value * weight for value, weight in zip(retained, weights))


def aggregate(outcomes, seeds):
    primary = outcomes[:-1]
    expected_slots = len(CASE_IDS) * len(seeds)
    if len(primary) != expected_slots:
        raise ValueError('incomplete slot list')
    weights = [1 / expected_slots] * expected_slots
    score = fixed_weight_score([value['score'] for value in primary], weights, 0.)
    result = {'combined_score': score}
    if PLANE == 'final':
        result.update(marginal_coverage=fixed_weight_score([value['coverage'] for value in primary], weights, 0.),
                      normalized_volume=fixed_weight_score([value['volume'] for value in primary], weights, 1.))
        strata = np.array([value['strata'] for value in primary]).reshape(6, len(seeds), 4)
        result['worst_stratum_coverage'] = float(strata.mean(axis=1).min())
        for index, name in enumerate(('coverage_gap_vs_euclidean', 'volume_gain_vs_euclidean',
                                      'coverage_gap_vs_ilr', 'volume_gain_vs_ilr')):
            result[name] = fixed_weight_score([value['gaps'][index] for value in primary], weights, -1.)
    if set(result) != set(METRICS) or not all(math.isfinite(value) for value in result.values()):
        raise ValueError('invalid scalar aggregation')
    return result


def evidence(outcomes, seeds):
    primary = outcomes[:-1]
    records = []
    seed_values = np.array([[value['score'] for value in primary if value['seed'] == seed] for seed in seeds])
    mean_per_seed = seed_values.mean(axis=1)
    rng = np.random.default_rng(80801)
    boot = rng.choice(mean_per_seed, size=(2000, len(seeds)), replace=True).mean(axis=1)
    score_interval = np.quantile(boot, [.025, .975]).tolist()
    comparison_values = np.array([[value['gaps'] for value in primary if value['seed'] == seed]
                                  for seed in seeds]).mean(axis=1)
    resample = rng.integers(0, len(seeds), size=(2000, len(seeds)))
    comparison_interval = np.quantile(comparison_values[resample].mean(axis=1), [.025, .975], axis=0).T.tolist()
    for seed in seeds:
        selected = [value for value in primary if value['seed'] == seed]
        all_episodes = [value for value in outcomes if value['seed'] == seed]
        cases = []
        for value in selected:
            cases.append({key: item for key, item in value.items()
                          if key not in ('_prediction', '_failure_emitted')})
        records.append({'seed': seed, 'score': float(np.mean([value['score'] for value in selected])),
                        'correct': all(value['complete'] for value in all_episodes),
                        'duration_seconds': sum(value['duration_seconds'] for value in all_episodes),
                        'solution': {'cases': cases, 'seed_bootstrap_score95': score_interval,
                                     'paired_seed_bootstrap_comparisons95': comparison_interval,
                                     'uncertainty_policy': 'paired seed resampling across all six cases; few-seed intervals unstable; four sign strata descriptive, no simultaneous conditional-coverage claim',
                                     'replay_completed': bool(outcomes[-1]['complete']) if seed == seeds[0] else None}})
    result = {'schema_version': 1, 'episodes': records}
    raw = json.dumps(result, allow_nan=False, separators=(',', ':')).encode('utf-8')
    if len(raw) > 16 * 1024 * 1024:
        raise ValueError('evidence bound exceeded')
    return result


def preflight_wire():
    basis = ilr_basis(8)
    training = np.full((COUNTS[0] * 13,), .125)
    query = np.full((COUNTS[1] + COUNTS[2] + 64, 5), -.3333333333333333)
    start = {'op': 'fit_start', 'n_rows': COUNTS[0], 'composition_dim': 8, 'ilr_basis': basis.tolist(),
             'alpha': .1, 'nbytes': training.nbytes, 'chunks': math.ceil(training.nbytes / CHUNK)}
    requests = [start, {'op': 'predict_start', 'x': encode(query)},
                {'op': 'fit_chunk', 'index': 0, 'block': encode(training[:CHUNK // 8])}]
    responses = [{'block': encode(np.full((CHUNK // 8,), -.3333333333333333))}]

    def measure(value, envelope_name):
        bounded_json_line(value)
        compact = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8')
        framed = json.dumps({envelope_name: value, 'id': 9223372036854775807}, allow_nan=False,
                            separators=(',', ':')).encode('utf-8') + b'\n'
        blocks = [item for item in value.values() if type(item) is dict and 'data' in item]
        base64_bytes = sum(len(block['data'].encode('ascii')) for block in blocks)
        return {'raw_tensor_bytes': sum(block['nbytes'] for block in blocks),
                'base64_bytes': base64_bytes, 'metadata_json_utf8_bytes': len(compact) - base64_bytes,
                'rpc_envelope_bytes': len(framed) - len(compact) - 1, 'framing_bytes': 1,
                'complete_bytes': len(framed)}

    request_sizes = [measure(value, 'request') for value in requests]
    response_sizes = [measure(value, 'response') for value in responses]
    maximum_request = max(request_sizes, key=lambda value: value['complete_bytes'])
    maximum_response = max(response_sizes, key=lambda value: value['complete_bytes'])
    largest = max(maximum_request['complete_bytes'], maximum_response['complete_bytes'])
    if largest >= WIRE_LIMIT or largest >= 64 * 1024 * 1024:
        raise ValueError('production wire preflight failed')
    return {'largest_complete_bytes': largest, 'production_max_request': maximum_request,
            'production_max_response': maximum_response, 'raw_chunk_bytes': CHUNK,
            'base64_chunk_bytes': 4 * math.ceil(CHUNK / 3), 'max_chunks': MAX_CHUNKS,
            'calls_per_episode': 1 + 1 + MAX_CHUNKS + 1 + 3 * (1 + MAX_CHUNKS + 1)}


def theoretical_checks():
    basis = ilr_basis(8)
    if not np.allclose(basis.T @ basis, np.eye(7), atol=1e-14) or not np.allclose(basis.sum(axis=0), 0):
        raise ValueError('invalid ILR basis')
    coordinates = np.arange(14).reshape(2, 7) / 10
    if not np.allclose(np.log(inverse_ilr(coordinates, basis)) @ basis, coordinates):
        raise ValueError('ILR round trip failed')
    if quantile(np.arange(9.))[0] != 8 or not math.isinf(quantile(np.arange(1.))[0]):
        raise ValueError('finite sample quantile check failed')
    if fixed_weight_score([None, .5], [.5, .5], 0.) != .25:
        raise ValueError('failure aggregation check failed')


def run(program_path, results_dir):
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    qualification = os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
    statistical_seeds = SEEDS[:1] if smoke else SEEDS
    episodes = [{'case': case, 'seed': seed} for case in CASE_IDS for seed in statistical_seeds]
    episodes.append({'case': 'C1', 'seed': statistical_seeds[0]})
    work_seconds = 1. if smoke else (10. if PLANE == 'search' else 30.)
    reset_timeout = 2. if smoke else 5.
    startup_allowance = 3. if smoke else 60.
    finish_reserve = 5. if smoke else 20.
    wall = 120. if smoke else WALL_SECONDS
    hard_deadline = STARTED + wall - startup_allowance
    profiles = {}
    for plane, count, limit, allowance in (('search', 19, 1200, 10), ('final', 31, 3600, 30)):
        profiles[plane] = {'episode_count': count, 'method_count': 3, 'wall_seconds': limit,
                          'startup_seconds': 80, 'finish_seconds': 20, 'reset_seconds': 7,
                          'cleanup_seconds': 3, 'work_seconds': allowance}
    require_joint_workload_budget(**profiles)
    theoretical_checks()
    preflight_wire()
    results_dir = Path(results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    outcomes = [worst_case(episode) for episode in episodes]
    complete = False
    client = None
    try:
        root = Path(os.environ.get('TASK_SOURCE_DIR', str(Path(__file__).absolute().parent))) / 'resources' / PLANE
        datasets = load_resources(root, hard_deadline - finish_reserve)
        client = Candidate(program_path, work_seconds, reset_timeout)
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline,
            finish_reserve=finish_reserve, reset_timeout=reset_timeout, episode_overhead=10.,
            rpc_cap=work_seconds + reset_timeout, clock=time.monotonic, rpc=client.rpc,
            evaluate=lambda episode, call, deadline, record: evaluate_episode(
                episode, call, deadline, record, datasets=datasets, smoke=smoke, work_seconds=work_seconds),
            worst_case=worst_case, record_failure=record_failure, cleanup=client.close)
        if client.resets != [episode['seed'] for episode in episodes]:
            raise ProtocolError('reset transcript mismatch')
        first, replay = outcomes[0], outcomes[-1]
        replay_ok = first['complete'] and replay['complete']
        if replay_ok:
            replay_ok = all(np.allclose(reference, actual, rtol=1e-8, atol=1e-9)
                            for reference, actual in zip(first['_prediction'], replay['_prediction']))
        if not replay_ok:
            complete = False
            duration = first['duration_seconds']
            outcomes[0] = worst_case(episodes[0])
            outcomes[0]['duration_seconds'] = duration
            outcomes[0]['failure'] = first.get('failure', {
                'component': 'candidate', 'category': 'replay_failure', 'operation': 'predict_start'})
            outcomes[-1]['complete'] = False
            record_failure({'component': 'candidate', 'category': 'replay_failure', 'operation': 'predict_start'}, outcomes[-1])
        complete = complete and all(value['complete'] for value in outcomes) and time.monotonic() < hard_deadline
    except FatalTransportError as error:
        outcomes = getattr(error, 'outcomes', outcomes)
        complete = False
        raise
    finally:
        original = sys.exception()
        if client is not None:
            try:
                client.close(original is not None)
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                complete = False
                if original is None:
                    raise
        metrics = aggregate(outcomes, statistical_seeds)
        correct = bool(complete)
        for filename, value in (('metrics.json', metrics), ('correct.json', {'correct': correct})):
            (results_dir / filename).write_text(json.dumps(value, allow_nan=False, separators=(',', ':')) + '\n')
        if qualification:
            (results_dir / 'qualification.json').write_text(json.dumps({'schema_version': 1,
                'feasible': bool(complete and not smoke)}, separators=(',', ':')) + '\n')
        if client is not None:
            observations = evidence(outcomes, statistical_seeds)
            observations['episodes'][0]['solution']['reset_transcript'] = {
                'planned': [episode['seed'] for episode in episodes], 'actual': client.resets,
                'complete': client.resets == [episode['seed'] for episode in episodes]}
            (results_dir / 'evaluation_evidence.json').write_text(json.dumps(observations,
                    allow_nan=False, separators=(',', ':')) + '\n')


def main():
    if sys.argv[1:] == ['--baseline-worker']:
        baseline_worker()
        return
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    existing = resource.getrlimit(resource.RLIMIT_CPU)
    ceiling = cpu_limit_seconds(WALL_SECONDS, 4)
    hard = ceiling if existing[1] == resource.RLIM_INFINITY else min(ceiling, existing[1])
    resource.setrlimit(resource.RLIMIT_CPU, (hard, hard))
    run(args.program_path, args.results_dir)


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        if PLANE == 'search':
            name = bounded_failure_name(type(error).__name__.lower(), 'evaluator_exception')
            print('evaluator_exception type=' + name + ' message=evaluation failed', file=sys.stderr, flush=True)
        else:
            print('evaluator_exception type=sealed_failure message=evaluation failed', file=sys.stderr, flush=True)
        raise SystemExit(1)
