"""Self-contained offline, evaluator-owned score-matrix experiment."""
import argparse
import base64
import collections
import contextlib
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

PLANE = 'search'
SEEDS = [1709, 3253]
WALL_SECONDS = 1800
RPC_BUDGET = 6681
RESOURCE_HASHES = {'definitions_license.txt': 'c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4', 'manifest.json': '00791fb6820a182dde79254fd49be0bd7c5fdf3cd2b0582c6ed9807c10e037c2', 'plan.json': '88ad2623b65b34279dc73bd41ab724eea1f26fc7953d0ee62e870eb1ed2e8eaf', 'rows.jsonl': 'f34959a93a63e61d787ecdaf6604d6782083a4c7cf758933ce8b2aae878561b0', 'source_license.txt': 'a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499', 'task_definitions.json': 'd5f7ac1056cbd7f3e1b26d76b209e88a0ca5ca4422e3674b703c85881a2a9195'}
WIRE_LIMIT = 64 * 1024**2
CHUNK_BYTES = 4 * 1024**2
MAX_CHUNKS = 64
FRAMING_RESERVE = 65536
BASELINES = ['column_mean', 'copy_skill', 'random_low_rank', 'variance_low_rank', 'linear_ridge']
CHECKPOINTS = [1, 2, 4, 8]
METRIC_NAMES = ['combined_score', 'mae', 'rmse', 'baseline_mae', 'delta_best_baseline', 'constant_control_mae', 'permuted_control_mae', 'reset_max_abs_delta', 'correct']
STARTED = time.monotonic()
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'
import numpy as np


class ProtocolFailure(RuntimeError):
    def __init__(self, category, operation):
        self.category = bounded_failure_name(category, 'malformed_response')
        self.operation = bounded_failure_name(operation, 'unknown')
        super().__init__('candidate protocol failure')


class FatalBrokerTransportFailure(RuntimeError):
    def __init__(self, operation):
        self.operation = bounded_failure_name(operation, 'unknown')
        super().__init__('broker transport unavailable')


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
    for level in range(8):
        if isinstance(context, InvalidResetResponse):
            return {'component': 'candidate', 'category': 'invalid_reset_response', 'operation': 'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component': 'baseline', 'category': context.category, 'operation': 'baseline_worker'}
        if isinstance(context, ProtocolFailure):
            return {'component': 'candidate', 'category': context.category, 'operation': context.operation}
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
        value = call(request)
        check()
        return value
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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError('invalid CPU budget')
    return math.ceil(wall_seconds * allowed_threads)


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
    for plane, profile in [('search', search), ('final', final)]:
        episodes, methods = profile['episode_count'], profile['method_count']
        if any(type(count) is not int or count <= 0 for count in [episodes, methods]):
            raise ValueError('invalid episode or method count')
        times = {name: finite_budget_seconds(profile[name]) for name in
                 ['wall_seconds', 'startup_seconds', 'reset_seconds', 'cleanup_seconds', 'finish_seconds']}
        work = positive_work_seconds(profile['work_seconds'])
        needed = (times['startup_seconds'] + times['finish_seconds']
                  + episodes * (times['reset_seconds'] + methods * (work + times['cleanup_seconds'])))
        if finite_budget_seconds(needed) > times['wall_seconds']:
            raise ValueError('productive work exceeds wall budget')
        required[plane] = needed
    return required


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in [now, episode_deadline, cleanup_seconds]:
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError('invalid remaining method count')
    if now + (methods_remaining + 1) * (work + cleanup_seconds) > episode_deadline:
        raise TimeoutError('insufficient matched method reservations')
    return now + work


@contextlib.contextmanager
def until(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError('deadline')
    entered = time.monotonic()
    previous_handler = signal.getsignal(signal.SIGALRM)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    def expired(signum, frame):
        raise TimeoutError('deadline')
    signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, min(remaining, previous_timer[0]) if previous_timer[0] > 0 else remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, max(.000001, previous_timer[0] - (time.monotonic()-entered)), previous_timer[1])


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':'), ensure_ascii=False).encode('utf-8') + b'\n'
    if len(encoded) + FRAMING_RESERVE >= wire_limit or len(encoded) >= 8 * 1024**2:
        raise ValueError('complete message exceeds wire limit')
    return encoded


def preflight_wire(columns):
    chunk = base64.b64encode(b'\xff' * CHUNK_BYTES).decode('ascii')
    request = {'op': 'upload_chunk', 'index': 63, 'data': chunk}
    request_bytes = len(bounded_json_line({'request': request, 'sequence': 10000000, 'protocol': 'python_rpc_v1'}))
    response = {'response': {'predictions': [0.12345678901234568] * max(columns, 4096)}, 'sequence': 10000000}
    response_bytes = len(bounded_json_line(response))
    assert len(chunk) == 4 * ((CHUNK_BYTES + 2) // 3)
    return {'raw_chunk_bytes': CHUNK_BYTES, 'base64_bytes': len(chunk),
            'request_json_line_bytes': request_bytes, 'response_json_line_bytes': response_bytes,
            'reserved_framing_bytes': FRAMING_RESERVE,
            'largest_complete_bytes': max(request_bytes, response_bytes) + FRAMING_RESERVE}


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ',
                     'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES',
                     'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS']:
        environment[name] = '3'
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


WORKER = r'''
import base64, ctypes, importlib.util, json, math, os, pathlib, resource, sys
entry_path = sys.argv[1]
repair_mode = sys.argv[3] == 'repair'
resource.setrlimit(resource.RLIMIT_AS, (8*1024**3, 8*1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (int(sys.argv[2]), int(sys.argv[2])))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
import numpy
def isolate():
    if os.uname().machine != 'x86_64':
        raise RuntimeError('native isolation requires Linux x86_64')
    library = ctypes.CDLL(None, use_errno=True)
    library.syscall.restype = ctypes.c_long
    abi = library.syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError('Landlock ABI >=3 required')
    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]
    class PathRule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]
    handled = (1 << 15) - 1
    attributes = Ruleset(handled)
    ruleset = library.syscall(444, ctypes.byref(attributes), ctypes.sizeof(attributes), 0)
    if ruleset < 0:
        raise RuntimeError('Landlock create failed')
    roots = {str(pathlib.Path(sys.argv[1]).parent), sys.prefix, sys.base_prefix,
             '/usr/lib', '/usr/local/lib', '/lib', '/lib64', '/etc/ld.so.cache', '/dev/urandom'}
    for root in roots:
        if not os.path.exists(root):
            continue
        descriptor = os.open(root, os.O_PATH | os.O_CLOEXEC)
        allowed = (1 << 0) | (1 << 2) | ((1 << 3) if os.path.isdir(root) else 0)
        rule = PathRule(allowed, descriptor)
        if library.syscall(445, ruleset, 1, ctypes.byref(rule), 0) < 0:
            raise RuntimeError('Landlock rule failed')
        os.close(descriptor)
    if library.prctl(38, 1, 0, 0, 0) != 0 or library.syscall(446, ruleset, 0) != 0:
        raise RuntimeError('Landlock restrict failed')
    os.close(ruleset)
    seccomp = ctypes.CDLL('libseccomp.so.2')
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    context = seccomp.seccomp_init(0x7fff0000)
    if not context:
        raise RuntimeError('seccomp initialization failed')
    forbidden = ['socket', 'socketpair', 'connect', 'accept', 'accept4', 'bind', 'listen',
                 'ptrace', 'process_vm_readv', 'process_vm_writev', 'mount', 'umount2',
                 'unshare', 'setns', 'open_by_handle_at', 'bpf', 'io_uring_setup',
                 'io_uring_enter', 'io_uring_register', 'setsid', 'setpgid', 'kill']
    for name in forbidden:
        number = seccomp.seccomp_syscall_resolve_name(name.encode())
        if number >= 0 and seccomp.seccomp_rule_add(context, 0x50001, number, 0) != 0:
            raise RuntimeError('seccomp rule failed')
    if seccomp.seccomp_load(context) != 0:
        raise RuntimeError('seccomp load failed')
    seccomp.seccomp_release(context)
try:
    isolate()
    sys.argv = [entry_path]
    sys.orig_argv = [sys.executable, entry_path]
    specification = importlib.util.spec_from_file_location('candidate', entry_path)
    candidate = importlib.util.module_from_spec(specification)
    sys.path.insert(0, str(pathlib.Path(entry_path).parent))
    specification.loader.exec_module(candidate)
    while True:
        line = sys.stdin.buffer.readline(64*1024**2)
        if not line:
            break
        if not line.endswith(b'\n') or len(line) >= 64*1024**2:
            raise ValueError('invalid request framing')
        request = json.loads(line)
        response = candidate.handle(request)
        encoded = json.dumps({'response': response}, allow_nan=False, separators=(',', ':')).encode() + b'\n'
        if len(encoded) >= 64*1024**2:
            raise ValueError('oversized response')
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
except BaseException as error:
    if repair_mode:
        name = type(error).__name__
        name = name if name.isascii() and name.isidentifier() and len(name) <= 80 else 'WorkerException'
        try:
            message = str(error)
        except Exception:
            message = '<exception message unavailable>'
        if len(message.encode('utf-8', errors='replace')) > 2048:
            message = '<exception message omitted: too large>'
        print('worker_exception type=' + name + '\n' + message, file=sys.stderr, flush=True)
    else:
        print('candidate_worker_failure', file=sys.stderr, flush=True)
    sys.exit(1)
'''


class CandidateClient:
    def __init__(self, program, wall_seconds):
        self.program = pathlib.Path(program).absolute()
        self.wall_seconds = wall_seconds
        self.count = 0
        self.process = None
        self.capture = None
        self.directory = None
        self.diagnostics = []
        self.proxy = None
        self.failed = False
        socket_present = bool(os.environ.get('AGENTIC_CANDIDATE_SOCKET'))
        proxy_path = program == '/broker-code/candidate_proxy.py'
        if socket_present != proxy_path:
            raise RuntimeError('broker requires the fixed proxy path and authenticated socket')
        if proxy_path:
            specification = importlib.util.spec_from_file_location('trusted_candidate_proxy', self.program)
            self.proxy = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(self.proxy)
        else:
            self.directory = tempfile.TemporaryDirectory(prefix='score-candidate-')
            destination = pathlib.Path(self.directory.name) / 'code'
            destination.mkdir()
            total = 0
            entries = 0
            for source in self.program.parent.rglob('*'):
                entries += 1
                if entries > 4096:
                    raise RuntimeError('candidate source entry count exceeded')
                if source.is_symlink():
                    raise RuntimeError('candidate symlinks forbidden')
                if source.is_file():
                    total += source.stat().st_size
                    if total > 32 * 1024**2:
                        raise RuntimeError('candidate source too large')
                    target = destination / source.relative_to(self.program.parent)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            self.worker_entry = destination / self.program.name

    def start(self):
        self.shutdown()
        interpreter, environment = candidate_subprocess_settings(os.environ)
        repair = (PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                  or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'))
        self.process = subprocess.Popen([interpreter, '-I', '-B', '-u', '-c', WORKER,
                                         str(self.worker_entry), str(cpu_limit_seconds(self.wall_seconds, 3)),
                                         'repair' if repair else 'sealed'],
                                        cwd=self.directory.name, env=environment, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
                                        shell=False, close_fds=True)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.pending = bytearray()
        self.failed = False

    def shutdown(self):
        if self.process is None:
            return
        process, capture = self.process, self.capture
        self.process, self.capture = None, None
        exit_status = process.poll()
        try:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=1)
        finally:
            process.stdin.close()
            process.stdout.close()
            snapshot = capture.close()
            failed = self.failed or (exit_status is not None and exit_status != 0)
            self.diagnostics.append({'exit_status': exit_status, 'observed_bytes': snapshot['observed_bytes'],
                                     'retained_bytes': snapshot['retained_bytes'], 'truncated': snapshot['truncated'],
                                     'capture_error': snapshot['capture_error']})
            if failed and PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                    or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'):
                sys.stderr.write(snapshot['stderr'])

    def close(self):
        try:
            self.shutdown()
        finally:
            if self.directory is not None:
                self.directory.cleanup()

    def call(self, request, *, timeout):
        self.count += 1
        if self.count > RPC_BUDGET:
            raise ProtocolFailure('rpc_budget', request['op'])
        encoded = bounded_json_line(request)
        started = time.monotonic()
        deadline = started + timeout
        if self.proxy is not None:
            try:
                with until(deadline):
                    response = self.proxy.handle(request)
                bounded_json_line({'response': response})
                return response
            except TimeoutError as error:
                if PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                        or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'):
                    operation = bounded_failure_name(request['op'], 'unknown')
                    print(f'broker_timeout operation={operation} elapsed_seconds={time.monotonic()-started:.6f}'
                          f' timeout_seconds={timeout:.6f}', file=sys.stderr)
                    report_worker_exception(error)
                raise
            except (OSError, EOFError) as error:
                raise FatalBrokerTransportFailure(request['op']) from error
            except (ValueError, RuntimeError):
                raise ProtocolFailure('broker_failure', request['op']) from None
        if request['op'] == 'reset':
            self.start()
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                written = 0
                while written < len(encoded):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('candidate write timeout')
                    written += os.write(self.process.stdin.fileno(), encoded[written:written+65536])
                selector.unregister(self.process.stdin)
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b'\n' not in self.pending:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('candidate read timeout')
                    block = os.read(self.process.stdout.fileno(), 65536)
                    if not block:
                        raise ProtocolFailure('candidate_exit', request['op'])
                    self.pending.extend(block)
                    if len(self.pending) + FRAMING_RESERVE >= WIRE_LIMIT:
                        raise ProtocolFailure('oversized_response', request['op'])
            line, _, rest = self.pending.partition(b'\n')
            self.pending = bytearray(rest)
            envelope = json.loads(line)
            if type(envelope) is not dict or set(envelope) != {'response'}:
                raise ProtocolFailure('malformed_response', request['op'])
            bounded_json_line(envelope)
            return envelope['response']
        except (TimeoutError, ProtocolFailure):
            self.failed = True
            raise
        except (BrokenPipeError, ConnectionError, OSError, ValueError):
            self.failed = True
            raise ProtocolFailure('malformed_response', request['op']) from None


def record_failure(failure):
    if PLANE == 'search':
        component = bounded_failure_name(failure.get('component'), 'candidate')
        category = bounded_failure_name(failure.get('category'), 'unknown_failure')
        operation = bounded_failure_name(failure.get('operation'), 'unknown')
        observed = failure.get('observed_bytes', 0)
        observed = observed if type(observed) is int and observed >= 0 else 0
        truncated = failure.get('truncated', False) is True
        capture_error = bounded_failure_name(failure.get('capture_error'), 'none')
        print((f'episode_failure component={component} category={category} operation={operation}'
               f' stderr_bytes={observed} truncated={int(truncated)} capture={capture_error}')[:255], file=sys.stderr)


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure, cleanup=lambda: None):
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
        episode_started = clock()
        current_operation = 'reset'
        primary_failure = None
        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc({'op': 'reset', 'seed': episode['seed']}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > work_deadline:
                raise TimeoutError('episode work deadline exceeded')
            cleanup()
            if clock() > episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                cleanup()
            except (OSError, RuntimeError, subprocess.TimeoutExpired):
                error.add_note('secondary cleanup failure')
            if not episode.get('failure_recorded', False):
                try:
                    record_failure(failure)
                except Exception:
                    error.add_note('episode diagnostic recording failed')
        finally:
            if isinstance(outcomes[index], dict) and 'duration' in outcomes[index]:
                outcomes[index]['duration'] = max(0.0, clock()-episode_started)
    return outcomes, complete


METRICS = ['accuracy', 'ndcg_at_10', 'v_measure', 'map', 'ap', 'cosine_spearman',
           'cos_sim_spearman', 'spearman', 'cosine_pearson', 'pearson', 'f1', 'max_ap',
           'map_at_1000', 'ndcg_at_20', 'recall_at_1', 'recall_at_10', 'max_accuracy',
           'ndcg_at_1', 'recall_at_100', 'recall_at_2', 'ndcg_at_5', 'kendalltau',
           'hit_rate_at_5', 'precision_at_1', 'mrr_at_5', 'mrr_at_10', 'paired_accuracy']


def canonical(value):
    if isinstance(value, str):
        return ' '.join(unicodedata.normalize('NFKC', value).split())
    if isinstance(value, list):
        return [canonical(item) for item in value]
    if isinstance(value, dict):
        return {canonical(key): canonical(item) for key, item in value.items()}
    if isinstance(value, (float, int)) and not isinstance(value, bool):
        if not math.isfinite(value):
            raise ValueError('nonfinite')
        return int(value) if value == int(value) else value
    return value


def digest(value):
    return hashlib.sha256(json.dumps(canonical(value), sort_keys=True, separators=(',', ':'),
                                     allow_nan=False, ensure_ascii=False).encode()).hexdigest()


def extract(document):
    output = []
    task = document.get('task_name')
    revision = document.get('dataset_revision')
    if not isinstance(task, str) or not isinstance(revision, str):
        return output
    definition = TASK_DEFINITIONS.get(task)
    if definition is None or definition['modalities'] != ['text'] or definition['metric'] not in METRICS:
        return output
    scores = document.get('scores', {})
    split = next((name for name in ['test', 'validation', 'dev'] if name in scores), None)
    if split is None or not isinstance(scores[split], list):
        return output
    for entry in scores[split]:
        if entry.get('languages') not in [['eng-Latn'], ['en'], ['eng']]:
            continue
        score = entry.get('main_score')
        if type(score) not in (int, float) or not math.isfinite(score):
            continue
        metric = definition['metric']
        if type(entry.get(metric)) not in (int, float) or not math.isclose(score, entry[metric], abs_tol=1e-8, rel_tol=0):
            continue
        correlation = 'spearman' in metric or 'pearson' in metric or metric == 'kendalltau'
        if not (-1 <= score <= 1 if correlation else 0 <= score <= 1):
            continue
        key = (task, revision, split, str(entry.get('hf_subset', 'default')), metric)
        output.append((key, (score + 1) / 2 if correlation else score))
    return output


def load_resources():
    global TASK_DEFINITIONS
    root = pathlib.Path(os.environ.get('TASK_SOURCE_DIR', pathlib.Path(__file__).resolve().parent)) / 'resources' / PLANE
    for name, expected in RESOURCE_HASHES.items():
        path = root / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('frozen resource integrity failure')
    TASK_DEFINITIONS = json.loads((root / 'task_definitions.json').read_text())
    manifest = json.loads((root / 'manifest.json').read_text())
    plan = json.loads((root / 'plan.json').read_text())
    rows = [json.loads(line) for line in (root / 'rows.jsonl').read_text().splitlines()]
    columns = [tuple(column) for column in manifest['columns']]
    identities = [row['source_id'] for row in rows]
    aliases = {alias for row in rows for alias in row['aliases']}
    if (len(identities) != len(set(identities)) or set(identities) & set(manifest['peer_source_ids'])
            or aliases & set(manifest['peer_aliases'])
            or {row['family'] for row in rows} & set(manifest['peer_families'])):
        raise RuntimeError('source identity, alias or outer-family overlap')
    if len(columns) < 24 or len(columns) > 4096 or len(rows) > 4096 or not manifest['cross_plane_disjoint']:
        raise RuntimeError('unsupported real-data coverage')
    peer_docs = set(manifest['peer_document_hashes'])
    peer_rows = set(manifest['peer_row_hashes'])
    for row in rows:
        extracted = {}
        for entry in row['documents']:
            prefix = 'results/' + row['source_id'] + '/' + row['revision'] + '/'
            if not entry['path'].startswith(prefix) or '..' in pathlib.PurePosixPath(entry['path']).parts:
                raise RuntimeError('invalid source row provenance')
            raw = entry['raw_text'].encode('utf-8')
            if hashlib.sha256(raw).hexdigest() != entry['raw_sha256']:
                raise RuntimeError('raw result digest failure')
            document = json.loads(raw)
            content_hash = digest({key: document[key] for key in ['task_name', 'dataset_revision', 'scores']})
            if content_hash != entry['content_sha256'] or content_hash in peer_docs:
                raise RuntimeError('normalized document overlap or corruption')
            extracted.update(extract(document))
        values = [extracted.get(column) for column in columns]
        row_hash = digest({'columns': columns, 'values': values})
        if values != row['values'] or row_hash != row['row_sha256'] or row_hash in peer_rows:
            raise RuntimeError('normalized example overlap or corruption')
        if sum(value is not None for value in values) < 12:
            raise RuntimeError('insufficient queryable/target support')
    for episode in plan['episodes']:
        history = [rows[index] for index in episode['history']]
        targets = [rows[index] for index in episode['test']]
        if not history or not targets or set(episode['history']) & set(episode['test']):
            raise RuntimeError('invalid split manifest')
        if {alias for row in history for alias in row['aliases']} & {alias for row in targets for alias in row['aliases']}:
            raise RuntimeError('history/target alias overlap')
        history_docs = {document['content_sha256'] for row in history for document in row['documents']}
        test_docs = {document['content_sha256'] for row in targets for document in row['documents']}
        if history_docs & test_docs or {row['row_sha256'] for row in history} & {row['row_sha256'] for row in targets}:
            raise RuntimeError('history/target normalized overlap')
        if episode['case'] == 'B' and {row['family'] for row in history} & {row['family'] for row in targets}:
            raise RuntimeError('family holdout overlap')
    return manifest, rows, plan


def ack(response, operation):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise ProtocolFailure('malformed_response', operation)


def prediction(response, columns):
    if type(response) is not dict or set(response) != {'predictions'} or type(response['predictions']) is not list:
        raise ProtocolFailure('malformed_response', 'predict')
    values = response['predictions']
    if len(values) != columns or any(type(value) not in (float, int) or not math.isfinite(value)
                                    or not 0 <= value <= 1 for value in values):
        raise ProtocolFailure('invalid_prediction', 'predict')
    return np.asarray(values, dtype=np.float64)


def upload(call, values, mask):
    raw = values.astype('<f8').tobytes() + mask.astype('u1').tobytes()
    chunks = math.ceil(len(raw) / CHUNK_BYTES)
    if chunks > MAX_CHUNKS or len(raw) > 256 * 1024**2:
        raise RuntimeError('history transfer exceeds declared bounds')
    ack(call({'op': 'upload_start', 'shape': list(values.shape), 'dtype': 'float64', 'byteorder': 'little',
              'mask_dtype': 'uint8', 'encoding': 'base64', 'layout': 'values_then_mask',
              'nbytes': len(raw), 'chunks': chunks}), 'upload_start')
    for index in range(chunks):
        ack(call({'op': 'upload_chunk', 'index': index,
                  'data': base64.b64encode(raw[index*CHUNK_BYTES:(index+1)*CHUNK_BYTES]).decode('ascii')}), 'upload_chunk')
    ack(call({'op': 'upload_commit'}), 'upload_commit')


def arrays(rows, indices):
    values = np.asarray([[0 if value is None else value for value in rows[index]['values']] for index in indices], dtype=np.float64)
    mask = np.asarray([[value is not None for value in rows[index]['values']] for index in indices], dtype=bool)
    return values, mask


def transformed_history(values, mask, case, seed):
    means = np.divide((values*mask).sum(axis=0), mask.sum(axis=0),
                      out=np.full(values.shape[1], .5), where=mask.sum(axis=0) > 0)
    if case == 'C':
        result = np.where(mask, means, 0)
        informative = any(np.ptp(values[mask[:, column], column]) > 1e-12
                          for column in range(values.shape[1]) if mask[:, column].sum() > 1)
        if not informative or np.allclose(result, values, rtol=0, atol=1e-12):
            raise ProtocolFailure('vacuous_control', 'fit')
        return result, mask.copy()
    if case == 'D':
        result, result_mask = values.copy(), mask.copy()
        rng = np.random.default_rng(seed + 13)
        for column in range(values.shape[1]):
            shift = int(rng.integers(1, len(values)))
            result[:, column] = np.roll(values[:, column], shift)
            result_mask[:, column] = np.roll(mask[:, column], shift)
        if np.array_equal(result, values) and np.array_equal(result_mask, mask):
            raise ProtocolFailure('vacuous_control', 'fit')
        if np.allclose(np.cov(result.T), np.cov(values.T), atol=1e-12, rtol=0):
            raise ProtocolFailure('vacuous_control', 'fit')
        return result, result_mask
    return values, mask


def fit_low_rank(values, mask, seed, sweeps):
    means = np.divide((values*mask).sum(axis=0), mask.sum(axis=0),
                      out=np.full(values.shape[1], .5), where=mask.sum(axis=0) > 0)
    centered = values - means
    rank = min(4, *values.shape)
    factors = np.random.default_rng(seed).normal(0, .1, (values.shape[1], rank))
    latent = np.zeros((values.shape[0], rank))
    regularizer = .1 * np.eye(rank)
    for sweep in range(sweeps):
        for row in range(len(values)):
            design = factors[mask[row]]
            latent[row] = np.linalg.solve(regularizer + design.T @ design, design.T @ centered[row, mask[row]])
        for column in range(values.shape[1]):
            design = latent[mask[:, column]]
            factors[column] = np.linalg.solve(regularizer + design.T @ design, design.T @ centered[mask[:, column], column])
    return means, factors


def partitions(rows, test_indices, seed):
    output = []
    for index in test_indices:
        available = np.flatnonzero([value is not None for value in rows[index]['values']])
        rng = np.random.default_rng(seed + index * 1009)
        shuffled = rng.permutation(available)
        cut = max(8, (2 * len(shuffled)) // 3)
        reservoir, targets = sorted(shuffled[:cut].tolist()), sorted(shuffled[cut:].tolist())
        if not targets or len(reservoir) < 8:
            raise RuntimeError('invalid frozen reservoir')
        output.append((reservoir, targets))
    return output


def error_pair(predicted, truth, indices):
    residual = predicted[indices] - truth[indices]
    return float(np.mean(np.abs(residual))), float(np.mean(residual**2))


def run_baseline(name, values, mask, tests, partitions_for_rows, seed, sweeps):
    means = np.divide((values*mask).sum(axis=0), mask.sum(axis=0),
                      out=np.full(values.shape[1], .5), where=mask.sum(axis=0) > 0)
    factors = None
    if name in ['random_low_rank', 'variance_low_rank']:
        means, factors = fit_low_rank(values, mask, seed, sweeps)
    variance = np.divide(((values-means)**2 * mask).sum(axis=0), mask.sum(axis=0),
                         out=np.zeros(values.shape[1]), where=mask.sum(axis=0)>0)
    losses = np.ones((len(tests), 4))
    for row, (reservoir, target) in enumerate(partitions_for_rows):
        if name == 'random_low_rank':
            selection = np.random.default_rng(seed + row * 37).permutation(reservoir).tolist()[:8]
        else:
            selection = sorted(reservoir, key=lambda index: (-variance[index], index))[:8]
        for checkpoint_index, budget in enumerate(CHECKPOINTS):
            observed = selection[:budget]
            if name == 'column_mean':
                predicted = means
            elif name == 'copy_skill':
                predicted = np.full(len(means), tests[row, observed].mean())
            elif name == 'linear_ridge':
                design = np.where(mask[:, observed], values[:, observed]-means[observed], 0)
                coefficients = np.linalg.solve(.1*np.eye(budget) + design.T@design,
                                               design.T @ np.where(mask, values-means, 0))
                predicted = np.clip(means + (tests[row, observed]-means[observed]) @ coefficients, 0, 1)
            else:
                design = factors[observed]
                latent = np.linalg.solve(.1*np.eye(factors.shape[1]) + design.T@design,
                                         design.T @ (tests[row, observed]-means[observed]))
                predicted = np.clip(means + factors @ latent, 0, 1)
            losses[row, checkpoint_index] = error_pair(predicted, tests[row], target)[0]
    return losses


def worst_case(episode):
    count = len(episode['test'])
    return {'mae': np.ones((count, 4)), 'mse': np.ones((count, 4)),
            'baselines': np.ones((5, count, 4)), 'predictions': None, 'queries': None,
            'all_unqueried_mae': np.ones((count, 4)), 'duration': 0.0, 'complete': False}


def evaluate_episode(episode, call, work_deadline, *, rows, smoke):
    started = time.monotonic()
    work = 1.5 if smoke else (20.0 if PLANE == 'search' else 60.0)
    method_cleanup = .25
    local_deadline = min(work_deadline, started + 6 * (work + method_cleanup) + .1)
    values, mask = arrays(rows, episode['history'])
    values, mask = transformed_history(values, mask, episode['case'], episode['seed'])
    tests, test_mask = arrays(rows, episode['test'])
    partition = partitions(rows, episode['test'], episode['seed'])
    sweeps = 2 if smoke else 50
    baseline_losses = []
    for method_index, name in enumerate(BASELINES):
        method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=local_deadline,
                                                   methods_remaining=5-method_index, work_seconds=work,
                                                   cleanup_seconds=method_cleanup)
        try:
            with until(method_deadline):
                baseline_losses.append(run_baseline(name, values, mask, tests, partition, episode['seed'], sweeps))
        except (TimeoutError, np.linalg.LinAlgError) as error:
            category = 'baseline_timeout' if isinstance(error, TimeoutError) else 'baseline_result_failure'
            def record_baseline_failure(category):
                record_failure({'component': 'baseline', 'category': category, 'operation': 'baseline_worker'})
                episode['failure_recorded'] = True
            fail_required_baseline(category, lambda: None, record_baseline_failure)
    method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=local_deadline,
                                               methods_remaining=0, work_seconds=work,
                                               cleanup_seconds=method_cleanup)
    result = worst_case(episode)
    result['baselines'] = np.asarray(baseline_losses)
    outputs, selections = [], []
    with until(method_deadline):
        upload(call, values, mask)
        ack(call({'op': 'fit', 'rank': 4, 'sweeps': sweeps, 'ridge': .1}), 'fit')
        for trajectory, (reservoir, targets) in enumerate(partition):
            ack(call({'op': 'begin', 'trajectory': trajectory, 'queryable': reservoir, 'budget': 8}), 'begin')
            observed = []
            checkpoints = []
            for step in range(1, 9):
                response = call({'op': 'select'})
                if type(response) is not dict or set(response) != {'index'} or type(response['index']) is not int:
                    raise ProtocolFailure('malformed_response', 'select')
                index = response['index']
                if index not in reservoir or index in observed:
                    raise ProtocolFailure('illegal_query', 'select')
                observed.append(index)
                ack(call({'op': 'observe', 'index': index, 'value': float(tests[trajectory, index])}), 'observe')
                if step in CHECKPOINTS:
                    predicted = prediction(call({'op': 'predict'}), tests.shape[1])
                    checkpoint = CHECKPOINTS.index(step)
                    result['mae'][trajectory, checkpoint], result['mse'][trajectory, checkpoint] = error_pair(predicted, tests[trajectory], targets)
                    unqueried = sorted(set(np.flatnonzero(test_mask[trajectory]).tolist()) - set(observed))
                    result['all_unqueried_mae'][trajectory, checkpoint] = error_pair(predicted, tests[trajectory], unqueried)[0]
                    checkpoints.append(predicted.tolist())
            outputs.append(checkpoints)
            selections.append(observed)
    result.update(predictions=outputs, queries=selections, duration=time.monotonic()-started, complete=True)
    return result


def fixed_average(values):
    if not values or any(not math.isfinite(value) for value in values):
        raise ValueError('nonfinite fixed contribution')
    return sum(values) / len(values)


def aggregate(episodes, outcomes, complete):
    primary = [index for index, episode in enumerate(episodes) if episode['case'] in ['A', 'B'] and not episode['replay']]
    mae = fixed_average([float(outcomes[index]['mae'].mean()) for index in primary])
    mse = fixed_average([float(outcomes[index]['mse'].mean()) for index in primary])
    baseline_maes = [fixed_average([float(outcomes[index]['baselines'][method].mean()) for index in primary]) for method in range(5)]
    baseline_mae = min(baseline_maes)
    original, replay = outcomes[0], outcomes[-1]
    delta = 1.0
    if original['complete'] and replay['complete'] and original['queries'] == replay['queries']:
        delta = float(np.max(np.abs(np.asarray(original['predictions']) - np.asarray(replay['predictions']))))
    correct = bool(complete and all(outcome['complete'] for outcome in outcomes) and delta <= 1e-10)
    metrics = {'combined_score': 1-mae, 'mae': mae, 'rmse': math.sqrt(mse),
               'baseline_mae': baseline_mae, 'delta_best_baseline': baseline_mae-mae if complete else -1.0,
               'constant_control_mae': fixed_average([float(outcomes[index]['mae'].mean()) for index, episode in enumerate(episodes) if episode['case']=='C']),
               'permuted_control_mae': fixed_average([float(outcomes[index]['mae'].mean()) for index, episode in enumerate(episodes) if episode['case']=='D']),
               'reset_max_abs_delta': delta, 'correct': int(correct)}
    if PLANE == 'final':
        for checkpoint, budget in enumerate(CHECKPOINTS):
            metrics['mae_k'+str(budget)] = fixed_average([float(outcomes[index]['mae'][:, checkpoint].mean()) for index in primary])
        metrics['gain_ci_low'], metrics['gain_ci_high'] = -1.0, -1.0
    return metrics, correct


def bootstrap_gain(episodes, outcomes, rows):
    primary = [index for index, episode in enumerate(episodes) if episode['case'] in ['A', 'B'] and not episode['replay']]
    groups = sorted({rows[row]['component'] for index in primary for row in episodes[index]['test']})
    if not groups:
        return -1.0, -1.0
    group_index = {group: index for index, group in enumerate(groups)}
    rng = np.random.default_rng(424242)
    samples = np.zeros((400, 5))
    for resample in range(400):
        multiplicity = np.bincount(rng.integers(len(groups), size=len(groups)), minlength=len(groups))
        for index in primary:
            weights = np.asarray([multiplicity[group_index[rows[row]['component']]] for row in episodes[index]['test']], dtype=float)
            if weights.sum() == 0:
                samples[resample] += -np.ones(5) / len(primary)
            else:
                gain = outcomes[index]['baselines'].mean(axis=2) - outcomes[index]['mae'].mean(axis=1)
                samples[resample] += gain @ weights / weights.sum() / len(primary)
    intervals = np.quantile(samples, [.005, .995], axis=0)
    return float(intervals[0].min()), float(intervals[1].min())


def make_evaluation_evidence(episodes, outcomes, rows, seeds):
    records = []
    for seed in seeds:
        indices = [index for index, episode in enumerate(episodes) if episode['seed']==seed and not episode['replay']]
        scored = [index for index in indices if episodes[index]['case'] in ['A', 'B']]
        solution = {'cases': {}}
        for index in indices:
            outcome, episode = outcomes[index], episodes[index]
            solution['cases'][episode['case']] = {
                'completed': outcome['complete'], 'mae_by_row_checkpoint': outcome['mae'].tolist(),
                'all_unqueried_mae_by_row_checkpoint': outcome['all_unqueried_mae'].tolist(),
                'baseline_mae_by_method_row_checkpoint': outcome['baselines'].tolist(),
                'selected_indices': outcome['queries'],
                'observed_counts': [sum(value is not None for value in rows[row]['values']) for row in episode['test']],
                'resampling_components': [rows[row]['component'] for row in episode['test']]}
        seed_correct = all(outcomes[index]['complete'] for index, episode in enumerate(episodes) if episode['seed']==seed)
        if seed == episodes[0]['seed']:
            original, replay = outcomes[0], outcomes[-1]
            seed_correct = bool(seed_correct and original['queries'] == replay['queries']
                                and original['predictions'] is not None and replay['predictions'] is not None
                                and np.max(np.abs(np.asarray(original['predictions'])-np.asarray(replay['predictions']))) <= 1e-10)
        records.append({'seed': seed, 'score': 1-fixed_average([float(outcomes[index]['mae'].mean()) for index in scored]),
                        'correct': seed_correct,
                        'duration_seconds': sum(outcomes[index]['duration'] for index, episode in enumerate(episodes) if episode['seed']==seed),
                        'solution': solution})
    return {'schema_version': 1, 'episodes': records}


def write_outputs(directory, metrics, correct, feasible, evidence=None):
    directory = pathlib.Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    if set(metrics) != set(METRIC_NAMES) or any(type(value) not in (float, int) or not math.isfinite(value) for value in metrics.values()):
        raise RuntimeError('metric schema violation')
    objects = {'metrics.json': metrics, 'correct.json': {'correct': bool(correct)}}
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        objects['qualification.json'] = {'schema_version': 1, 'feasible': bool(feasible)}
    if evidence is not None:
        serialized = bounded_json_line(evidence)
        if len(serialized) >= 16 * 1024**2:
            raise RuntimeError('evidence size exceeded')
        objects['evaluation_evidence.json'] = evidence
    for name, value in objects.items():
        destination = directory / name
        temporary = directory / (name + '.tmp')
        temporary.write_bytes(json.dumps(value, allow_nan=False, separators=(',', ':')).encode() + b'\n')
        temporary.replace(destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    startup = 5 if smoke else (120 if PLANE=='search' else 300)
    finish = 5 if smoke else 30
    wall = 120 if smoke else WALL_SECONDS
    hard_deadline = STARTED + wall - startup
    metrics = {name: (-1.0 if name in ['delta_best_baseline', 'gain_ci_low', 'gain_ci_high'] else 1.0) for name in METRIC_NAMES}
    metrics['combined_score'], metrics['correct'] = 0.0, 0
    client = None
    try:
        with until(hard_deadline-finish):
            manifest, rows, plan = load_resources()
            preflight_wire(len(manifest['columns']))
        episodes = [dict(episode) for episode in plan['episodes'] if not smoke or episode['seed']==SEEDS[0]]
        if smoke:
            for episode in episodes:
                episode['history'] = episode['history'][:24]
                episode['test'] = episode['test'][:4]
        work = 1.5 if smoke else (20.0 if PLANE=='search' else 60.0)
        profiles = {
            'search': {'episode_count': 5 if smoke else 9, 'method_count': 6, 'wall_seconds': 120 if smoke else 1800,
                       'startup_seconds': 5 if smoke else 120, 'finish_seconds': 5 if smoke else 30,
                       'reset_seconds': 6, 'cleanup_seconds': 1.1, 'work_seconds': 1.5 if smoke else 20},
            'final': {'episode_count': 5 if smoke else 13, 'method_count': 6, 'wall_seconds': 120 if smoke else 7200,
                      'startup_seconds': 5 if smoke else 300, 'finish_seconds': 5 if smoke else 30,
                      'reset_seconds': 6, 'cleanup_seconds': 1.1, 'work_seconds': 1.5 if smoke else 60}}
        require_joint_workload_budget(**profiles)
        client = CandidateClient(arguments.program_path, wall)
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=finish, reset_timeout=6,
            episode_overhead=5, rpc_cap=work, clock=time.monotonic, rpc=client.call,
            evaluate=lambda episode, call, deadline: evaluate_episode(episode, call, deadline, rows=rows, smoke=smoke),
            worst_case=worst_case,
            record_failure=lambda failure: record_failure(dict(failure, **{
                key: client.diagnostics[-1].get(key) if client.diagnostics else None
                for key in ['observed_bytes', 'truncated', 'capture_error']})),
            cleanup=client.shutdown)
        metrics, correct = aggregate(episodes, outcomes, complete)
        if PLANE == 'final' and complete:
            with until(hard_deadline-5):
                metrics['gain_ci_low'], metrics['gain_ci_high'] = bootstrap_gain(episodes, outcomes, rows)
        evidence = make_evaluation_evidence(episodes, outcomes, rows, SEEDS[:1] if smoke else SEEDS)
        feasible = complete and not smoke and time.monotonic() < hard_deadline
        write_outputs(arguments.results_dir, metrics, correct, feasible, evidence)
    except Exception as error:
        try:
            metrics['correct'] = 0
            write_outputs(arguments.results_dir, metrics, False, False)
        finally:
            if PLANE == 'search':
                if isinstance(error, FatalBrokerTransportFailure):
                    record_failure({'component': 'broker', 'category': 'transport_failure',
                                    'operation': error.operation})
                name = bounded_failure_name(type(error).__name__.lower(), 'evaluator_exception')
                print('evaluator_exception type='+name+' message=evaluation failed', file=sys.stderr)
            else:
                print('evaluator_failure', file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
