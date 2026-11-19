"""Self-contained evaluator. See task_contract.json for fixed scientific policy.

All observations and region tests are evaluator-owned. Candidate code sees training
rows and unlabeled prediction features only. No candidate self-report is scored.
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
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

for _thread_name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_thread_name] = '4'

INVOCATION_STARTED = time.monotonic()

import numpy as np

PLANE = 'search'
WALL_SECONDS = 1200
STARTUP_SECONDS = 120
RPC_BUDGET = 126
SEEDS = [17, 43, 97]
SCORE_NAME = 'combined_score'
CASES = ('LN_IID_K3', 'LN_IID_K8', 'DIR_IID_K3', 'DIR_IID_K8', 'DIR_SHIFT_K3', 'DIR_SHIFT_K8')
ALPHAS = (.05, .10, .20)
APP_LIMIT = 2 * 1024 * 1024
WIRE_LIMIT = 64 * 1024 * 1024
EXPECTED_CONTROLS = frozenset(('reset_unfitted', 'constant_input', 'permuted_input', 'copy_point'))
METHODS = ('scaled_ilr', 'unscaled_ilr', 'simplex_linf', 'bonferroni', 'constant_center',
           'whole_simplex', 'constant_input', 'permuted_input', 'copy_point')
METRIC_NAMES = (SCORE_NAME, 'iid_coverage_error', 'mean_volume', 'shift_coverage_error',
                'baseline_utility_gap', 'control_check_pass_rate', 'correct')
WORK_SECONDS = 3.0
METHOD_CLEANUP = .1
RESET_TIMEOUT = 3.0
EPISODE_OVERHEAD = 4.0
FINISH_RESERVE = 15.0


class ProtocolFailure(RuntimeError):
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
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value) else fallback


def describe_episode_failure(error, operation):
    context = error
    for context_depth in range(8):
        if isinstance(context, InvalidResetResponse):
            return {'component': 'candidate', 'category': 'invalid_reset_response', 'operation': 'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component': 'baseline', 'category': context.category, 'operation': 'baseline_worker'}
        if isinstance(context, ProtocolFailure):
            return {'component': 'candidate', 'category': 'invalid_protocol',
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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError('invalid CPU budget')
    return math.ceil(positive_work_seconds(wall_seconds) * allowed_threads)


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
        if not math.isfinite(needed) or needed > times['wall_seconds']:
            raise ValueError('productive work exceeds declared wall budget')
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


def bounded_json_line(value):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(encoded) >= APP_LIMIT or len(encoded) >= WIRE_LIMIT:
        raise ProtocolFailure('complete message exceeds limit')
    return encoded


def _reject_constant(value):
    raise ProtocolFailure('nonfinite JSON')


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ProtocolFailure('duplicate JSON key')
        value[key] = item
    return value


def parse_json(raw):
    try:
        value = json.loads(raw, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
        bounded_json_line(value)
        return value
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ProtocolFailure('invalid JSON') from error


def encode_array(array):
    array = np.ascontiguousarray(array, dtype='<f8')
    return {'encoding': 'base64', 'dtype': 'float64', 'byte_order': 'little',
            'shape': list(array.shape), 'data': base64.b64encode(array.tobytes()).decode('ascii')}


def decode_array(value, shape):
    if type(value) is not dict or set(value) != {'encoding', 'dtype', 'byte_order', 'shape', 'data'}:
        raise ProtocolFailure('array schema')
    if (value['encoding'] != 'base64' or value['dtype'] != 'float64'
            or value['byte_order'] != 'little' or value['shape'] != list(shape)
            or any(type(size) is not int for size in value['shape'])
            or type(value['data']) is not str or len(value['data']) > 1400000):
        raise ProtocolFailure('array metadata')
    try:
        raw = base64.b64decode(value['data'], validate=True)
    except ValueError as error:
        raise ProtocolFailure('array encoding') from error
    if len(raw) != math.prod(shape) * 8 or len(raw) > 1024 * 1024:
        raise ProtocolFailure('array size')
    result = np.frombuffer(raw, dtype='<f8').reshape(shape).copy()
    if not np.isfinite(result).all():
        raise ProtocolFailure('nonfinite prediction')
    return result


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ',
                     'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES',
                     'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION',
                     'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1',
                       PYTHONUNBUFFERED='1')
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


WORKER = r'''
import ctypes
import errno
import importlib.util
import json
import os
from pathlib import Path
import resource
import sys


def sandbox(workspace, wall_seconds):
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (int(wall_seconds) * 4, int(wall_seconds) * 4))
    resource.setrlimit(resource.RLIMIT_FSIZE, (32 * 1024**2, 32 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    available = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, available[:4])
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:
        raise RuntimeError('no_new_privileges unavailable')
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError('Landlock ABI 3 required')
    handled = (1 << 15) - 1
    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]
    class Rule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int)]
    ruleset = Ruleset(handled)
    descriptor = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
    if descriptor < 0:
        raise RuntimeError('Landlock ruleset unavailable')
    read_access = (1 << 0) | (1 << 2) | (1 << 3)
    roots = {sys.base_prefix, sys.prefix, '/usr/lib', '/lib', '/lib64',
             '/etc/ld.so.cache', '/dev/null', '/dev/urandom'}
    for root in sorted(roots | {workspace}):
        if not os.path.exists(root):
            continue
        access = read_access
        if not os.path.isdir(root):
            access &= (1 << 0) | (1 << 1) | (1 << 2) | (1 << 14)
        parent = os.open(root, os.O_PATH | os.O_CLOEXEC)
        rule = Rule(access, parent)
        if libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0) != 0:
            raise RuntimeError('Landlock path rule failed')
        os.close(parent)
    seccomp = ctypes.CDLL('libseccomp.so.2')
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    context = seccomp.seccomp_init(0x7fff0000)
    if not context:
        raise RuntimeError('seccomp init failed')
    forbidden = ('socket', 'socketpair', 'connect', 'bind', 'listen', 'accept', 'accept4',
                 'ptrace', 'process_vm_readv', 'process_vm_writev', 'pidfd_getfd',
                 'pidfd_send_signal', 'kill', 'mount', 'umount2', 'bpf', 'unshare', 'setns',
                 'fork', 'vfork', 'execve', 'execveat', 'tkill', 'rt_sigqueueinfo',
                 'rt_tgsigqueueinfo', 'io_uring_setup', 'io_uring_enter', 'io_uring_register',
                 'sched_setaffinity', 'sched_setscheduler', 'sched_setparam', 'sched_setattr',
                 'setpriority', 'setpgid', 'setsid', 'process_madvise', 'kcmp')
    for name in forbidden:
        syscall = seccomp.seccomp_syscall_resolve_name(name.encode())
        if syscall >= 0 and seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM, syscall, 0) != 0:
            raise RuntimeError('seccomp rule failed')
    clone3_number = seccomp.seccomp_syscall_resolve_name(b'clone3')
    if clone3_number >= 0:
        if seccomp.seccomp_rule_add(context, 0x50000 | errno.ENOSYS, clone3_number, 0) != 0:
            raise RuntimeError('seccomp clone3 rule failed')
    class ArgumentComparison(ctypes.Structure):
        _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_int),
                    ('datum_a', ctypes.c_uint64), ('datum_b', ctypes.c_uint64)]
    comparison = ArgumentComparison(0, 7, 0x10000, 0)
    seccomp.seccomp_rule_add_array.argtypes = [ctypes.c_void_p, ctypes.c_uint32,
                                             ctypes.c_int, ctypes.c_uint, ctypes.c_void_p]
    clone_number = seccomp.seccomp_syscall_resolve_name(b'clone')
    if clone_number < 0 or seccomp.seccomp_rule_add_array(
            context, 0x50000 | errno.EPERM, clone_number, 1, ctypes.byref(comparison)) != 0:
        raise RuntimeError('seccomp nonthread clone rule failed')
    for name, allowed_pid in ((b'tgkill', os.getpid()), (b'prlimit64', 0)):
        comparison = ArgumentComparison(0, 1, allowed_pid, 0)
        number = seccomp.seccomp_syscall_resolve_name(name)
        if number >= 0 and seccomp.seccomp_rule_add_array(
                context, 0x50000 | errno.EPERM, number, 1, ctypes.byref(comparison)) != 0:
            raise RuntimeError('seccomp peer-process rule failed')
    if seccomp.seccomp_load(context) != 0:
        raise RuntimeError('seccomp load failed')
    seccomp.seccomp_release(context)
    if libc.syscall(446, descriptor, 0) != 0:
        raise RuntimeError('Landlock enforcement failed')
    os.close(descriptor)


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


try:
    workspace, entrypoint, wall_seconds = sys.argv[1:]
    sandbox(workspace, float(wall_seconds))
    sys.path.insert(0, str(Path(entrypoint).parent))
    spec = importlib.util.spec_from_file_location('candidate', entrypoint)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for line in sys.stdin.buffer:
        request = json.loads(line)
        response = module.handle(request)
        encoded = json.dumps(response, allow_nan=False, separators=(',', ':')).encode() + b'\n'
        if len(encoded) >= 2 * 1024**2:
            raise ValueError('response too large')
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
except BaseException as error:
    __WORKER_DIAGNOSTIC__
    sys.exit(1)
'''


class RPC:
    def __init__(self, program_path, wall_seconds):
        self.program_path = Path(program_path).absolute()
        socket_present = bool(os.environ.get('AGENTIC_CANDIDATE_SOCKET'))
        proxy_path = program_path == '/broker-code/candidate_proxy.py'
        if socket_present != proxy_path:
            raise RuntimeError('broker requires fixed proxy path and socket together')
        self.proxy = None
        self.process = None
        self.capture = None
        self.directory = None
        self.calls = 0
        self.wall_seconds = wall_seconds
        self.failure_snapshot = None
        self.cleanup_failed = False
        if socket_present and proxy_path:
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', str(self.program_path))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.directory = tempfile.TemporaryDirectory(prefix='composition-native-')
            self.workspace = Path(self.directory.name)
            copied = self.workspace / 'code'
            copied.mkdir()
            if not self.program_path.is_file() or self.program_path.stat().st_size > 32 * 1024 ** 2:
                raise RuntimeError('native entrypoint must be a bounded regular file')
            self.entrypoint = copied / 'program.py'
            shutil.copyfile(self.program_path, self.entrypoint)

    def _start(self):
        self.close_process()
        interpreter, environment = candidate_subprocess_settings(os.environ)
        repair = PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                                        or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')
        failure_report = 'report_worker_exception(error)' if repair else "print('candidate_worker_failure', type(error).__name__, file=sys.stderr, flush=True)"
        worker_code = WORKER.replace('__WORKER_DIAGNOSTIC__', failure_report)
        self.process = subprocess.Popen(
            [interpreter, '-I', '-u', '-c', worker_code, str(self.workspace), str(self.entrypoint),
             str(self.wall_seconds)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, cwd=self.workspace, env=environment, shell=False,
            start_new_session=True, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdout.fileno(), False)
        os.set_blocking(self.process.stdin.fileno(), False)

    def __call__(self, request, *, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolFailure('RPC budget exceeded')
        raw = bounded_json_line(request)
        bounded_json_line({'request': request, 'rpc_id': self.calls, 'method': 'handle'})
        if self.proxy is not None:
            previous = signal.getsignal(signal.SIGALRM)
            def expired(signum, frame):
                raise TimeoutError('RPC deadline')
            signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                response = self.proxy(request)
                bounded_json_line({'response': response, 'rpc_id': self.calls})
                return response
            except TimeoutError:
                raise
            except (RuntimeError, ValueError) as error:
                raise ProtocolFailure('broker RPC failed') from error
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
        started = time.monotonic()
        if request['op'] == 'reset':
            self._start()
        if self.process is None:
            raise ProtocolFailure('reset required')
        deadline = started + timeout
        response_buffer = bytearray()
        written = 0
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                while written < len(raw):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('RPC write timeout')
                    written += os.write(self.process.stdin.fileno(), raw[written:])
                selector.unregister(self.process.stdin)
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b'\n' not in response_buffer:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('RPC read timeout')
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                    if not chunk:
                        raise ProtocolFailure('candidate exited')
                    response_buffer.extend(chunk)
                    if len(response_buffer) >= APP_LIMIT:
                        raise ProtocolFailure('response size exceeded')
            if not response_buffer.endswith(b'\n') or response_buffer.count(b'\n') != 1:
                raise ProtocolFailure('invalid response framing')
            response = parse_json(response_buffer)
            bounded_json_line({'response': response, 'rpc_id': self.calls})
            return response
        except TimeoutError:
            raise
        except OSError as error:
            raise ProtocolFailure('candidate pipe failure') from error

    def close_process(self, failed=False):
        if self.process is None:
            return
        process, capture = self.process, self.capture
        self.process = None
        self.capture = None
        try:
            if process.poll() is None:
                try:
                    os.killpg(process.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=.5)
                except subprocess.TimeoutExpired:
                    pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=.5)
        except (OSError, subprocess.TimeoutExpired):
            self.cleanup_failed = True
        finally:
            process.stdin.close()
            process.stdout.close()
            try:
                snapshot = capture.close()
            except RuntimeError:
                self.cleanup_failed = True
                snapshot = {'stderr': '', 'observed_bytes': capture.observed_bytes,
                            'retained_bytes': 0, 'truncated': True,
                            'capture_error': 'stderr_reader_cleanup_unresolved'}
            if failed:
                self.failure_snapshot = snapshot
                if (PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                        or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')):
                    if snapshot['stderr']:
                        sys.stderr.write(snapshot['stderr'])
                    print('worker_capture component=candidate observed_bytes={} retained_bytes={} truncated={} capture_error={}'.format(
                        snapshot['observed_bytes'], snapshot['retained_bytes'], int(snapshot['truncated']),
                        snapshot['capture_error'] or 'none'), file=sys.stderr)

    def close(self):
        self.close_process()
        if self.directory is not None:
            self.directory.cleanup()


def record_failure(failure):
    if PLANE == 'search':
        if type(failure) is str:
            failure = {'component': 'baseline', 'category': failure, 'operation': 'baseline_worker'}
        if type(failure) is not dict:
            failure = {}
        component = bounded_failure_name(failure.get('component'), 'unknown')
        category = bounded_failure_name(failure.get('category'), 'unknown')
        operation = bounded_failure_name(failure.get('operation'), 'unknown')
        try:
            print(f'episode_failure component={component} category={category} operation={operation}'[:256],
                  file=sys.stderr, flush=True)
        except OSError:
            pass


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout,
                          episode_overhead, rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = 'reset'
        primary_failure = None
        def call(request, *, deadline=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if deadline is not None:
                    timeout = min(timeout, deadline - clock())
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        started = clock()
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc({'op': 'reset', 'seed': episode['seed']}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            value['duration_seconds'] = max(0, clock() - started)
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
            if hasattr(rpc, 'close_process'):
                rpc.close_process(failed=True)
            outcomes[index]['duration_seconds'] = max(0, clock() - started)
    return outcomes, complete


def basis(dimension):
    matrix = np.zeros((dimension, dimension - 1))
    for column in range(1, dimension):
        denominator = math.sqrt(column * (column + 1))
        matrix[:column, column - 1] = 1 / denominator
        matrix[column, column - 1] = -column / denominator
    return matrix


def inverse_ilr(center, matrix):
    logits = center @ matrix.T
    logits -= logits.max(axis=1, keepdims=True)
    probabilities = np.exp(logits)
    return probabilities / probabilities.sum(axis=1, keepdims=True)


def numeric_hash(array):
    array = np.array(array, dtype='<f8', order='C', copy=True)
    if not np.isfinite(array).all():
        raise ValueError('nonfinite raw data')
    array[array == 0] = 0
    header = json.dumps({'schema': 'raw-f64-v1', 'shape': list(array.shape)},
                        sort_keys=True, separators=(',', ':')).encode('ascii')
    return hashlib.sha256(header + b'\n' + array.tobytes()).hexdigest()


def generate_arrays(seed, case_index, counts):
    """Frozen composition-v1 recipe; independent RNG substreams before any transform.

    Raw numeric normalization is float64 little endian, negative zero to zero.
    Logistic normal sigma=.25. Dirichlet has concentration 4+35*sigmoid(-2*x0),
    with a declared 1e-12 positivity floor then closure. Shift changes only test X.
    Subgroups: x0>0 and x0<=0. Uniform-simplex probes are Dirichlet(1,...,1).
    """
    case = CASES[case_index]
    dimension = 3 if case.endswith('K3') else 8
    matrix = basis(dimension)
    weights = np.sin(np.arange(6 * (dimension - 1)).reshape(6, dimension - 1) + 1) / 3
    arrays = {}
    for split_index, (split, count) in enumerate(zip(('train', 'calibration', 'test'), counts)):
        generator = np.random.default_rng(np.random.SeedSequence([seed, case_index, split_index, 202611]))
        if 'SHIFT' in case and split == 'test':
            features = np.clip(generator.normal(.8, 1.0, (count, 6)), -2.5, 3.0)
        else:
            features = generator.uniform(-1.5, 1.5, (count, 6))
        mean = .7 * np.sin(features @ weights) + .3 * features[:, :1] * np.cos(np.arange(dimension - 1))
        if case.startswith('LN'):
            composition = inverse_ilr(mean + generator.normal(0, .25, mean.shape), matrix)
        else:
            mean_composition = inverse_ilr(mean, matrix)
            concentration = 4 + 35 / (1 + np.exp(2 * features[:, 0]))
            gamma = generator.gamma(mean_composition * concentration[:, None], 1.0)
            gamma = np.maximum(gamma, 1e-12)
            composition = gamma / gamma.sum(axis=1, keepdims=True)
        arrays['x_' + split] = features
        arrays['y_' + split] = composition
    reference_rng = np.random.default_rng(np.random.SeedSequence([seed, case_index, 3, 202611]))
    arrays['contexts'] = reference_rng.choice(counts[2], size=128, replace=False)
    arrays['probes'] = reference_rng.dirichlet(np.ones(dimension), size=1024)
    return arrays


def load_resources(root, smoke, deadline):
    manifest = json.loads((root / 'manifest.json').read_text())
    if (manifest['schema_version'] != 1 or manifest['generator_version'] != 'composition-v1'
            or manifest['seeds'] != SEEDS or manifest['cross_plane_content_disjoint'] is not True):
        raise ValueError('invalid frozen resource manifest')
    selected = manifest['episodes'][:1] if smoke else manifest['episodes']
    expected = [(seed, case) for seed in SEEDS for case in CASES]
    if [(item['seed'], item['case']) for item in manifest['episodes']] != expected:
        raise ValueError('resource episode order')
    seen = {'x': set(), 'y': set(), 'pair': set()}
    episodes = []
    for entry in selected:
        check_deadline(deadline)
        path = root / entry['file']
        if not re.fullmatch(r'episode_[0-9]{3}\.npz', entry['file']) or path.is_symlink():
            raise ValueError('resource path')
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('resource checksum')
        with np.load(path, allow_pickle=False) as archive:
            arrays = {key: archive[key].copy() for key in archive.files}
        for split in ('train', 'calibration', 'test'):
            features, targets = arrays['x_' + split], arrays['y_' + split]
            provenance = entry['splits'][split]
            expected_source = '{}:{}:{}:{}'.format(PLANE, entry['seed'], entry['case'], split)
            expected_substream = [entry['seed'], CASES.index(entry['case']),
                                  ('train', 'calibration', 'test').index(split), 202611]
            if provenance['source_id'] != expected_source or provenance['rng_substream'] != expected_substream:
                raise ValueError('source or RNG provenance')
            if len(features) != provenance['count'] or len(provenance['rows']) != len(features):
                raise ValueError('row provenance count')
            if (not np.isfinite(features).all() or not np.isfinite(targets).all()
                    or not (targets > 0).all() or targets.shape[1] not in (3, 8)
                    or features.shape != (len(targets), 6)
                    or not np.allclose(targets.sum(1), 1, rtol=0, atol=1e-12)):
                raise ValueError('raw support check')
            for row, (feature, target) in enumerate(zip(features, targets)):
                hashes = {'x': numeric_hash(feature), 'y': numeric_hash(target),
                          'pair': numeric_hash(np.concatenate((feature, target)))}
                if provenance['rows'][row] != {'row': row, **hashes}:
                    raise ValueError('normalized row checksum')
                for kind, digest in hashes.items():
                    if digest in seen[kind]:
                        raise ValueError('normalized content overlap')
                    seen[kind].add(digest)
        if smoke:
            for split, count in (('train', 64), ('calibration', 32), ('test', 64)):
                arrays['x_' + split] = arrays['x_' + split][:count]
                arrays['y_' + split] = arrays['y_' + split][:count]
            arrays['contexts'] = np.arange(16)
            arrays['probes'] = arrays['probes'][:64]
        if (numeric_hash(arrays['probes']) != entry['probe_hash'] and not smoke):
            raise ValueError('reference probe checksum')
        dimension = arrays['y_train'].shape[1]
        matrix = basis(dimension)
        if not np.allclose(matrix.T @ matrix, np.eye(dimension - 1), atol=1e-12):
            raise ValueError('ILR orthogonality')
        if not np.allclose(inverse_ilr(np.log(arrays['y_train'][:5]) @ matrix, matrix),
                           arrays['y_train'][:5], atol=1e-12):
            raise ValueError('ILR roundtrip')
        episodes.append({'seed': entry['seed'], 'case': entry['case'], 'arrays': arrays})
    return episodes


def check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError('evaluator work deadline')


def quantile(scores, alpha):
    rank = math.ceil((len(scores) + 1) * (1 - alpha))
    if rank > len(scores):
        return math.inf
    return float(np.partition(scores, rank - 1)[rank - 1])


def wilson(successes, count, normal_quantile=1.959963984540054):
    if count == 0:
        return None
    proportion = successes / count
    quantile_squared = normal_quantile * normal_quantile
    denominator = 1 + quantile_squared / count
    center = (proportion + quantile_squared / (2 * count)) / denominator
    radius = normal_quantile * math.sqrt(proportion * (1 - proportion) / count + quantile_squared / (4 * count * count)) / denominator
    return [max(0, center - radius), min(1, center + radius)]


def prediction(response, rows, dimension):
    if type(response) is not dict or set(response) != {'center', 'scale'}:
        raise ProtocolFailure('prediction schema')
    center = decode_array(response['center'], (rows, dimension - 1))
    scale = decode_array(response['scale'], (rows, dimension - 1))
    if (np.abs(center) > 100).any() or (scale < 1e-4).any() or (scale > 100).any():
        raise ProtocolFailure('prediction support')
    return center, scale


def score_method(name, center, scale, arrays, deadline):
    check_deadline(deadline)
    calibration_targets, test_targets = arrays['y_calibration'], arrays['y_test']
    calibration_count = len(calibration_targets)
    dimension = test_targets.shape[1]
    matrix = basis(dimension)
    contexts, probes = arrays['contexts'], arrays['probes']
    if name == 'constant_center':
        fixed = (np.log(arrays['y_train']) @ matrix).mean(0)
        center = np.tile(fixed, (len(center), 1))
        scale = np.ones_like(center)
    elif name == 'unscaled_ilr':
        scale = np.ones_like(scale)
    calibration_center, test_center = center[:calibration_count], center[calibration_count:]
    calibration_scale, test_scale = scale[:calibration_count], scale[calibration_count:]
    center_simplex = inverse_ilr(center, matrix)
    ilr_family = name in ('scaled_ilr', 'unscaled_ilr', 'constant_center', 'constant_input', 'permuted_input')
    if ilr_family:
        calibration_residual = np.abs(np.log(calibration_targets) @ matrix - calibration_center) / calibration_scale
        test_residual = np.abs(np.log(test_targets) @ matrix - test_center) / test_scale
        probe_targets = np.log(probes) @ matrix
    else:
        calibration_residual = np.abs(calibration_targets - center_simplex[:calibration_count])
        test_residual = np.abs(test_targets - center_simplex[calibration_count:])
        probe_targets = probes
    records = []
    for alpha in ALPHAS:
        check_deadline(deadline)
        if name == 'whole_simplex':
            threshold = math.inf
        elif name == 'copy_point':
            threshold = 0.0
        elif name == 'bonferroni':
            threshold = np.array([quantile(calibration_residual[:, coordinate], alpha / dimension)
                                  for coordinate in range(dimension)])
        else:
            threshold = quantile(calibration_residual.max(axis=1), alpha)
        membership = np.all(test_residual <= threshold, axis=1)
        hits_per_context = []
        for offset in range(0, len(contexts), 16):
            check_deadline(deadline)
            indices = contexts[offset:offset + 16]
            if ilr_family:
                residual = np.abs(probe_targets[None, :, :] - test_center[indices, None, :]) / test_scale[indices, None, :]
            else:
                residual = np.abs(probe_targets[None, :, :] - center_simplex[calibration_count + indices, None, :])
            hits_per_context.extend(np.all(residual <= threshold, axis=2).sum(axis=1).tolist())
        coverage = float(membership.mean())
        volume = float(np.mean(hits_per_context) / len(probes))
        error = abs(coverage - (1 - alpha))
        utility = (1 - volume) * max(0, 1 - error / (1 - alpha))
        subgroup = arrays['x_test'][:, 0] > 0
        subgroup_records = []
        for mask in (subgroup, ~subgroup):
            count = int(mask.sum())
            successes = int(membership[mask].sum())
            subgroup_records.append({'count': count, 'coverage': successes / count if count else None,
                                     'conditional_wilson95': wilson(successes, count)})
        context_probabilities = np.array(hits_per_context) / len(probes)
        records.append({'alpha': alpha, 'coverage': coverage, 'volume': volume, 'utility': utility,
                        'coverage_error': error, 'conditional_wilson95': wilson(int(membership.sum()), len(membership)),
                        'subgroups': subgroup_records,
                        'quantile': np.where(np.isfinite(threshold), threshold, -1).tolist(),
                        'infinite_quantile': bool(np.any(np.isinf(threshold))),
                        'volume_probe_resolution': 1 / len(probes),
                        'zero_hit_contexts': int((np.array(hits_per_context) == 0).sum()),
                        'mean_context_mc_se_bound': float(np.mean(np.sqrt(context_probabilities * (1 - context_probabilities) / len(probes)))),
                        'zero_hit_one_sided95_upper': 1 - .05 ** (1 / len(probes)),
                        'ilr_center_mse': float(np.mean((np.log(test_targets) @ matrix - test_center) ** 2))})
    return records


def evaluate_episode(episode, call, work_deadline):
    arrays = episode['arrays']
    dimension = arrays['y_train'].shape[1]
    methods_remaining = 13
    local_deadline = min(work_deadline, time.monotonic() + 13 * (WORK_SECONDS + METHOD_CLEANUP) + .5)
    def allowance():
        nonlocal methods_remaining
        methods_remaining -= 1
        return reserved_method_deadline(now=time.monotonic(), episode_deadline=local_deadline,
            methods_remaining=methods_remaining, work_seconds=WORK_SECONDS, cleanup_seconds=METHOD_CLEANUP)
    active_deadline = allowance()
    def bounded_call(request):
        check_deadline(active_deadline)
        response = call(request, deadline=active_deadline)
        check_deadline(active_deadline)
        return response
    completed = set()
    unfitted = bounded_call({'op': 'predict', 'x': encode_array(arrays['x_train'][:2])})
    if unfitted != {'status': 'unfitted'}:
        raise ProtocolFailure('reset leakage control')
    completed.add('reset_unfitted')
    center_ack = bounded_call({'op': 'fit_center', 'x': encode_array(arrays['x_train']),
                               'y': encode_array(arrays['y_train']), 'dimension': dimension})
    if type(center_ack) is not dict or set(center_ack) != {'ok'} or center_ack['ok'] is not True:
        raise ProtocolFailure('fit center acknowledgment')
    scale_ack = bounded_call({'op': 'fit_scale'})
    if type(scale_ack) is not dict or set(scale_ack) != {'ok'} or scale_ack['ok'] is not True:
        raise ProtocolFailure('fit scale acknowledgment')
    features = np.concatenate((arrays['x_calibration'], arrays['x_test']))
    calibration_count = len(arrays['x_calibration'])
    constant_features = np.tile(arrays['x_train'].mean(0), (len(features), 1))
    permutation = np.concatenate((np.roll(np.arange(calibration_count), 1),
                                  calibration_count + np.roll(np.arange(len(arrays['x_test'])), 1)))
    changed_rows = np.any(features != features[permutation], axis=1)
    if ((permutation == np.arange(len(features))).any()
            or np.count_nonzero(changed_rows[:calibration_count]) < 2
            or np.count_nonzero(changed_rows[calibration_count:]) < 2):
        raise ProtocolFailure('vacuous permutation control')
    query_entropy = int.from_bytes(hashlib.sha256(arrays['probes'].tobytes()).digest()[:8], 'little')
    query_order = np.random.default_rng(query_entropy).permutation(len(features))
    original_order = np.argsort(query_order)
    predictions = {}
    for name, inputs in (('scaled_ilr', features), ('constant_input', constant_features),
                         ('permuted_input', features[permutation])):
        active_deadline = allowance()
        response = bounded_call({'op': 'predict', 'x': encode_array(inputs[query_order])})
        ordered_center, ordered_scale = prediction(response, len(inputs), dimension)
        predictions[name] = ordered_center[original_order], ordered_scale[original_order]
        if name == 'constant_input':
            center, scale = predictions[name]
            if not np.allclose(center, center[0], rtol=0, atol=1e-10) or not np.allclose(scale, scale[0], rtol=0, atol=1e-10):
                raise ProtocolFailure('constant input structural control')
            completed.add(name)
        elif name == 'permuted_input':
            center, scale = predictions[name]
            main_center, main_scale = predictions['scaled_ilr']
            if (not np.allclose(center, main_center[permutation], rtol=1e-10, atol=1e-10)
                    or not np.allclose(scale, main_scale[permutation], rtol=1e-10, atol=1e-10)):
                raise ProtocolFailure('prediction read-only alignment')
            completed.add(name)
    records = {}
    for name in METHODS:
        active_deadline = allowance()
        center, scale = predictions.get(name, predictions['scaled_ilr'])
        started = time.monotonic()
        try:
            records[name] = score_method(name, center, scale, arrays, active_deadline)
        except TimeoutError as error:
            if name not in ('scaled_ilr', 'constant_input', 'permuted_input', 'copy_point'):
                raise RequiredBaselineFailure('baseline_timeout') from error
            raise
        if time.monotonic() > active_deadline:
            raise RequiredBaselineFailure('baseline_timeout')
        for record in records[name]:
            record['productive_scoring_seconds'] = max(0, time.monotonic() - started)
    if any(record['coverage'] >= .5 for record in records['copy_point']):
        raise ProtocolFailure('zero radius scorer control')
    completed.add('copy_point')
    if EXPECTED_CONTROLS - completed:
        raise ProtocolFailure('required control incomplete')
    main = records['scaled_ilr']
    return {'score': float(np.mean([record['utility'] for record in main])),
            'error': float(np.mean([record['coverage_error'] for record in main])),
            'volume': float(np.mean([record['volume'] for record in main])),
            'controls': 1.0, 'correct': True, 'duration_seconds': 0.0,
            'solution': {'case': episode['case'], 'complete': True, 'controls': sorted(completed),
                         'control_checks': {name: name in completed for name in sorted(EXPECTED_CONTROLS)},
                         'methods': records}}


def worst_case(episode):
    return {'score': 0.0, 'error': 1.0, 'volume': 1.0, 'controls': 0.0,
            'correct': False, 'duration_seconds': 0.0,
            'solution': {'case': episode['case'], 'complete': False, 'controls': [],
                         'control_checks': {name: False for name in sorted(EXPECTED_CONTROLS)},
                         'methods': None}}


def fixed_mean(values):
    if not values or not all(type(value) in (int, float) and math.isfinite(value) for value in values):
        raise ValueError('invalid fixed-denominator contributions')
    return math.fsum(values) / len(values)


def uncertainty_by_case(episodes, outcomes):
    intervals = {}
    generator = np.random.default_rng(62845)
    selected_cases = list(dict.fromkeys(episode['case'] for episode in episodes))
    for case in selected_cases:
        case_outcomes = [outcome for episode, outcome in zip(episodes, outcomes) if episode['case'] == case]
        data = np.array([outcome['score'] for outcome in case_outcomes])
        if len(data) < 2:
            intervals[case] = {'seed_count': len(data), 'bootstrap95': None, 'paired_baselines': None}
            continue
        indices = generator.integers(0, len(data), size=(20000, len(data)))
        boot = data[indices].mean(1)
        comparisons = {}
        for baseline in ('unscaled_ilr', 'simplex_linf', 'bonferroni'):
            alpha_results = []
            for alpha_index in range(3):
                differences, volume_differences = [], []
                for outcome in case_outcomes:
                    methods = outcome['solution']['methods']
                    if methods is None:
                        differences.append(-1.0)
                        volume_differences.append(1.0)
                    else:
                        differences.append(methods['scaled_ilr'][alpha_index]['utility'] - methods[baseline][alpha_index]['utility'])
                        volume_differences.append(methods['scaled_ilr'][alpha_index]['volume'] - methods[baseline][alpha_index]['volume'])
                bootstrap_difference = np.array(differences)[indices].mean(1)
                bootstrap_volume = np.array(volume_differences)[indices].mean(1)
                adjusted_tail = .05 / (2 * 54)
                alpha_results.append({'alpha': ALPHAS[alpha_index], 'utility_difference': fixed_mean(differences),
                    'volume_difference': fixed_mean(volume_differences),
                    'paired_seed_bootstrap95': np.quantile(bootstrap_difference, [.025, .975]).tolist(),
                    'paired_volume_bootstrap95': np.quantile(bootstrap_volume, [.025, .975]).tolist(),
                    'bonferroni54_bootstrap_interval': np.quantile(bootstrap_difference, [adjusted_tail, 1 - adjusted_tail]).tolist()})
            comparisons[baseline] = alpha_results
        feature_controls = {}
        for control in ('constant_input', 'permuted_input'):
            control_differences = []
            for alpha_index in range(3):
                differences = []
                for outcome in case_outcomes:
                    methods = outcome['solution']['methods']
                    differences.append(-1.0 if methods is None else
                        methods['scaled_ilr'][alpha_index]['utility'] - methods[control][alpha_index]['utility'])
                distribution = np.array(differences)[indices].mean(1)
                control_differences.append({'alpha': ALPHAS[alpha_index], 'main_minus_control_utility': fixed_mean(differences),
                    'paired_seed_bootstrap95': np.quantile(distribution, [.025, .975]).tolist()})
            feature_controls[control] = control_differences
        intervals[case] = {'seed_count': len(data), 'bootstrap95': np.quantile(boot, [.025, .975]).tolist(),
                           'paired_baselines': comparisons, 'feature_controls': feature_controls}
    seed_scores = []
    for seed in dict.fromkeys(episode['seed'] for episode in episodes):
        seed_scores.append(fixed_mean([outcome['score'] for episode, outcome in zip(episodes, outcomes)
                                       if episode['seed'] == seed]))
    overall_interval = None
    if len(seed_scores) > 1:
        indices = generator.integers(0, len(seed_scores), size=(20000, len(seed_scores)))
        overall_interval = np.quantile(np.array(seed_scores)[indices].mean(1), [.025, .975]).tolist()
    intervals['overall_seed_block'] = {'seed_count': len(seed_scores), 'bootstrap95': overall_interval}
    return intervals


def aggregate(episodes, outcomes, complete):
    score = fixed_mean([outcome['score'] for outcome in outcomes])
    iid = [outcome['error'] for episode, outcome in zip(episodes, outcomes) if 'SHIFT' not in episode['case']]
    shift = [outcome['error'] for episode, outcome in zip(episodes, outcomes) if 'SHIFT' in episode['case']]
    valid = complete and all(outcome['correct'] for outcome in outcomes)
    baseline_gap = -1.0
    if valid:
        baseline_scores = []
        for name in ('unscaled_ilr', 'simplex_linf', 'bonferroni'):
            baseline_scores.append(fixed_mean([fixed_mean([record['utility'] for record in outcome['solution']['methods'][name]]) for outcome in outcomes]))
        baseline_gap = score - max(baseline_scores)
    metrics = {SCORE_NAME: score, 'iid_coverage_error': fixed_mean(iid) if iid else 1.0,
               'mean_volume': fixed_mean([outcome['volume'] for outcome in outcomes]),
               'shift_coverage_error': fixed_mean(shift) if shift else 1.0,
               'baseline_utility_gap': baseline_gap,
               'control_check_pass_rate': fixed_mean([outcome['controls'] for outcome in outcomes]),
               'correct': int(valid)}
    if set(metrics) != set(METRIC_NAMES) or not all(math.isfinite(value) for value in metrics.values()):
        raise ValueError('metric schema')
    evidence = []
    uncertainty = uncertainty_by_case(episodes, outcomes)
    for seed in dict.fromkeys(episode['seed'] for episode in episodes):
        selected = [outcome for episode, outcome in zip(episodes, outcomes) if episode['seed'] == seed]
        evidence.append({'seed': seed, 'score': fixed_mean([outcome['score'] for outcome in selected]),
                         'correct': all(outcome['correct'] for outcome in selected),
                         'duration_seconds': sum(outcome['duration_seconds'] for outcome in selected),
                         'solution': {'cases': [outcome['solution'] for outcome in selected],
                                      'seed_block_uncertainty': uncertainty}})
    return metrics, valid, {'schema_version': 1, 'episodes': evidence}


def preflight():
    for plane, count, wall, startup in (('search', 18, 1200, 120), ('final', 48, 3600, 180)):
        needed = startup + FINISH_RESERVE + count * (RESET_TIMEOUT + EPISODE_OVERHEAD + 13 * (WORK_SECONDS + METHOD_CLEANUP))
        if needed > wall:
            raise ValueError('joint production work reservations infeasible')
    if RPC_BUDGET != len(SEEDS) * len(CASES) * 7:
        raise ValueError('RPC operation ledger mismatch')
    for training_rows, prediction_rows in ((512, 1280), (1024, 2560), (4096, 4096)):
        features = encode_array(np.full((training_rows, 6), 9.999999999999))
        targets = encode_array(np.full((training_rows, 8), .125))
        requests = [({'op': 'reset', 'seed': 2 ** 63 - 1}, {'ok': True}),
                    ({'op': 'predict', 'x': encode_array(np.zeros((2, 6)))}, {'status': 'unfitted'}),
                    ({'op': 'fit_center', 'x': features, 'y': targets, 'dimension': 8}, {'ok': True}),
                    ({'op': 'fit_scale'}, {'ok': True})]
        for _arm in range(3):
            requests.append(({'op': 'predict', 'x': encode_array(np.zeros((prediction_rows, 6)))},
                {'center': encode_array(np.full((prediction_rows, 7), -100.0)),
                 'scale': encode_array(np.full((prediction_rows, 7), 100.0))}))
        if len(requests) != 7:
            raise ValueError('mock trace incomplete')
        for index, (request, response) in enumerate(requests):
            bounded_json_line(request)
            bounded_json_line(response)
            bounded_json_line({'request': request, 'rpc_id': 9999999, 'method': 'handle', 'framing': 'json-line-v1'})
            bounded_json_line({'response': response, 'rpc_id': 9999999, 'method': 'handle', 'framing': 'json-line-v1'})


def write_json(path, value, limit=16 * 1024 * 1024):
    raw = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(raw) > limit:
        raise ValueError('output limit')
    path.write_bytes(raw)


def main():
    started = INVOCATION_STARTED
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    results = Path(arguments.results_dir)
    results.mkdir(parents=True, exist_ok=True)
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    wall_seconds = 120 if smoke else WALL_SECONDS
    startup = 20 if smoke else STARTUP_SECONDS
    hard_deadline = started + wall_seconds - startup
    import resource
    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
    cpu_limit = cpu_limit_seconds(WALL_SECONDS, 4)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    available = sorted(os.sched_getaffinity(0))
    os.sched_setaffinity(0, available[:4])
    metrics = {name: 0.0 for name in METRIC_NAMES}
    metrics.update(iid_coverage_error=1.0, mean_volume=1.0, shift_coverage_error=1.0, baseline_utility_gap=-1.0)
    valid = False
    feasible = False
    rpc = None
    failed = None
    try:
        if np.__version__ != '1.26.4' or sys.version_info[:2] not in ((3, 11), (3, 12)):
            raise RuntimeError('requires NumPy 1.26.4 on CPython 3.11 or 3.12')
        preflight()
        root = Path(os.environ.get('TASK_SOURCE_DIR', str(Path(__file__).resolve().parent))) / 'resources' / PLANE
        episodes = load_resources(root, smoke, hard_deadline - FINISH_RESERVE)
        expected = [SEEDS[0]] if smoke else [seed for seed in SEEDS for _case in CASES]
        if [episode['seed'] for episode in episodes] != expected:
            raise ValueError('reset transcript mismatch')
        rpc = RPC(arguments.program_path, WALL_SECONDS)
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline,
            finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD,
            rpc_cap=WORK_SECONDS, clock=time.monotonic, rpc=rpc, evaluate=evaluate_episode,
            worst_case=worst_case, record_failure=record_failure)
        complete = complete and rpc.calls == len(episodes) * 7
        rpc.close()
        complete = complete and not rpc.cleanup_failed and time.monotonic() < hard_deadline
        metrics, valid, evidence = aggregate(episodes, outcomes, complete)
        feasible = complete and not smoke
        write_json(results / 'evaluation_evidence.json', evidence)
    except Exception as error:
        failed = error
    finally:
        if rpc is not None:
            try:
                rpc.close()
            except Exception as error:
                if failed is None:
                    failed = error
        if failed is not None:
            valid = False
            feasible = False
            metrics['correct'] = 0
        write_json(results / 'metrics.json', metrics)
        write_json(results / 'correct.json', {'correct': bool(valid)})
        if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
            write_json(results / 'qualification.json', {'schema_version': 1, 'feasible': bool(feasible)})
    if failed is not None:
        if PLANE == 'search':
            name = bounded_failure_name(type(failed).__name__.lower(), 'exception')
            print(f'evaluator_exception type={name} message=evaluation_failed', file=sys.stderr)
        else:
            print('evaluator_exception type=runtime_error message=sealed_evaluation_failed', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
