"""Self-contained offline evaluator; candidate reports never establish validity."""

import argparse
import base64
import collections
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
import signal
import subprocess
import sys
import threading
import time

PLANE = 'search'
CASES = ['arc_challenge', 'ifeval', 'mmlu_pro']
SEEDS = [101, 211]
WALL_SECONDS = 3600
RPC_LIMIT = 296
MANIFEST_SHA = '3c5793b0f2f7b480d34a0d59a99626f4e2fed048773e4eb2265fce1344681742'
CONDITIONS = ('primary', 'constant', 'copy', 'permuted', 'no_diversity', 'no_calibration')
BUDGETS = (8, 16, 32)
WIRE_LIMIT = 64 * 1024 * 1024
FRAME_LIMIT = 16 * 1024 * 1024
CHUNK_BYTES = 4 * 1024 * 1024
METHOD_WORK_SECONDS = 30
WORKER_POLL_SECONDS = .05
METRICS = ('combined_score', 'mae', 'rmse', 'spearman', 'kendall_tau_b', 'uniform_mae', 'source_mean_mae', 'anchor_mae', 'irt_mae', 'constant_mae', 'copy_mae', 'permuted_mae', 'no_diversity_mae', 'no_calibration_mae', 'reset_mae', 'reset_max_abs_error', 'control_failure_rate', 'missing_episode_rate', 'delta_anchor_mae', 'delta_anchor_ci_low', 'delta_anchor_ci_high', 'correct')
STARTED = time.monotonic()
NATIVE_CPUSET = sorted(os.sched_getaffinity(0)) if hasattr(os, 'sched_getaffinity') else []
PENDING_WORKER_DIAGNOSTICS = {}


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(encoded) >= wire_limit:
        raise ProtocolError('wire_size')
    return encoded


def framed_size(value):
    envelope = {'method': 'handle', 'protocol': 'python_rpc_v1', 'id': 10000000, 'payload': value, 'framing_reserve': ' ' * 65536}
    encoded = bounded_json_line(envelope)
    if len(encoded) >= FRAME_LIMIT:
        raise ProtocolError('framed_size')
    return len(encoded)


class ProtocolError(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'malformed_response')
        super().__init__('invalid candidate protocol')


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
    for depth in range(8):
        if isinstance(context, InvalidResetResponse):
            return {'component': 'candidate', 'category': 'invalid_reset_response', 'operation': 'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component': 'baseline', 'category': context.category, 'operation': 'baseline_worker'}
        if isinstance(context, ProtocolError):
            return {'component': 'candidate', 'category': context.category, 'operation': bounded_failure_name(operation, 'unknown')}
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
    def guarded(request, **kwargs):
        check()
        try:
            result = call(request, check_required=check, **kwargs)
        except (TimeoutError, ProtocolError):
            check()
            raise
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
        self.result = {'stderr': ''.join(self.lines), 'observed_bytes': self.observed_bytes, 'retained_bytes': self.retained_bytes, 'truncated': self.truncated, 'capture_error': self.capture_error}
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


def repair_visibility():
    return PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')


def emit_worker_failure(snapshot, component, category, operation, returncode):
    if PLANE != 'search':
        return
    numeric_status = returncode if type(returncode) is int else None
    PENDING_WORKER_DIAGNOSTICS[component] = (numeric_status, snapshot)
    if repair_visibility() and snapshot['stderr']:
        print(snapshot['stderr'], end='', file=sys.stderr)


def record_failure(failure):
    if PLANE == 'search':
        component = bounded_failure_name(failure.get('component'), 'candidate')
        category = bounded_failure_name(failure.get('category'), 'unknown')
        operation = bounded_failure_name(failure.get('operation'), 'unknown')
        metadata = ''
        if type(failure.get('status')) is int:
            metadata = f' status={failure["status"]}'
        diagnostic = PENDING_WORKER_DIAGNOSTICS.pop(component, None)
        if diagnostic is not None:
            status, snapshot = diagnostic
            metadata = f' status={status} observed={snapshot["observed_bytes"]} retained={snapshot["retained_bytes"]} truncated={int(snapshot["truncated"])} capture_error={int(snapshot["capture_error"] is not None)}'
        PENDING_WORKER_DIAGNOSTICS.clear()
        print(f'episode_failure component={component} category={category} operation={operation}{metadata}'[:256], file=sys.stderr)
    else:
        category = bounded_failure_name(failure.get('category'), 'unknown')
        operation = bounded_failure_name(failure.get('operation'), 'unknown')
        print(f'sealed_episode_failure category={category} operation={operation}'[:256], file=sys.stderr)


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ', 'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES', 'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS', 'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1', OMP_NUM_THREADS='6', OPENBLAS_NUM_THREADS='6', MKL_NUM_THREADS='6', NUMEXPR_NUM_THREADS='6')
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError('invalid CPU budget')
    return math.ceil(wall_seconds * allowed_threads)


NATIVE_RUNNER = r'''
import base64, contextlib, ctypes, errno, importlib.util, io, json, os, resource, sys
entry = os.path.abspath(sys.argv[1])
resource.setrlimit(resource.RLIMIT_AS, (16*1024**3,16*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(int(sys.argv[2]),int(sys.argv[2])))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
resource.setrlimit(resource.RLIMIT_FSIZE,(0,0))
if hasattr(os,'sched_getaffinity'):
    allowed=[int(value) for value in sys.argv[3].split(',')]; os.sched_setaffinity(0,allowed)
libc=ctypes.CDLL(None,use_errno=True)
libc.syscall.restype=ctypes.c_long
abi=libc.syscall(444,0,0,1)
if abi < 1: raise RuntimeError('Landlock unavailable; refusing unsafe native execution')
rights=(1<<13)-1
if abi>=2: rights|=1<<13
if abi>=3: rights|=1<<14
class Ruleset(ctypes.Structure): _fields_=[('handled_access_fs',ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_=1
    _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
rules=Ruleset(rights)
rules_fd=libc.syscall(444,ctypes.byref(rules),ctypes.sizeof(rules),0)
if rules_fd < 0: raise RuntimeError('Landlock ruleset failure')
allowed_paths={sys.prefix,sys.base_prefix,'/usr','/lib','/lib64',os.path.dirname(entry),'/dev/null','/dev/urandom'}
for path in allowed_paths:
    if not os.path.exists(path): continue
    descriptor=os.open(path,os.O_PATH|os.O_CLOEXEC)
    access=(1<<0)|(1<<2)
    if os.path.isdir(path):access|=1<<3
    rule=PathRule(access,descriptor)
    result=libc.syscall(445,rules_fd,1,ctypes.byref(rule),0)
    os.close(descriptor)
    if result<0:raise RuntimeError('Landlock path failure')
if libc.prctl(38,1,0,0,0)!=0 or libc.syscall(446,rules_fd,0)!=0:raise RuntimeError('Landlock activation failure')
os.close(rules_fd)
sec=ctypes.CDLL('libseccomp.so.2')
sec.seccomp_init.argtypes=[ctypes.c_uint32];sec.seccomp_init.restype=ctypes.c_void_p
sec.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p];sec.seccomp_syscall_resolve_name.restype=ctypes.c_int
sec.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
sec.seccomp_load.argtypes=[ctypes.c_void_p];sec.seccomp_release.argtypes=[ctypes.c_void_p]
filter=sec.seccomp_init(0x7fff0000)
for name in ('socket','socketpair','connect','bind','listen','accept','accept4','ptrace','process_vm_readv','process_vm_writev','kill','tkill','tgkill','pidfd_open','pidfd_getfd','pidfd_send_signal','rt_sigqueueinfo','rt_tgsigqueueinfo','prlimit64','mount','umount2','unshare','setns','setsid','setpgid','bpf','io_uring_setup','fork','vfork','execve','execveat'):
    number=sec.seccomp_syscall_resolve_name(name.encode())
    if number>=0 and sec.seccomp_rule_add(filter,0x00050000|errno.EPERM,number,0)!=0:raise RuntimeError('seccomp rule failure')
class ArgumentComparison(ctypes.Structure):
    _fields_=[('arg',ctypes.c_uint),('op',ctypes.c_int),('datum_a',ctypes.c_uint64),('datum_b',ctypes.c_uint64)]
sec.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(ArgumentComparison)]
comparison=ArgumentComparison(0,7,0x10000,0)
if sec.seccomp_rule_add_array(filter,0x00050000|errno.EPERM,sec.seccomp_syscall_resolve_name(b'clone'),1,ctypes.byref(comparison))!=0:raise RuntimeError('seccomp clone rule failure')
if sec.seccomp_rule_add(filter,0x00050000|errno.ENOSYS,sec.seccomp_syscall_resolve_name(b'clone3'),0)!=0:raise RuntimeError('seccomp clone3 rule failure')
if sec.seccomp_load(filter)!=0:raise RuntimeError('seccomp activation failure')
sec.seccomp_release(filter)
wire=sys.stdout
sys.path.insert(0,os.path.dirname(entry))
with contextlib.redirect_stdout(sys.stderr):
    spec=importlib.util.spec_from_file_location('submitted_candidate',entry)
    candidate=importlib.util.module_from_spec(spec);spec.loader.exec_module(candidate)
for line in sys.stdin.buffer:
    try:
        request=json.loads(line)
        with contextlib.redirect_stdout(sys.stderr):response=candidate.handle(request)
        encoded=json.dumps(response,allow_nan=False,separators=(',',':')).encode()+b'\n'
        if len(encoded)>=64*1024*1024:raise ValueError('response exceeds limit')
        wire.buffer.write(encoded);wire.flush()
    except Exception as error:
        print('candidate_exception type='+type(error).__name__,file=sys.stderr,flush=True)
        raise SystemExit(1)
'''


def stop_process(process):
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=1)


class JsonProcess:
    def __init__(self, arguments, environment, *, component, cwd='/'):
        self.component = component
        self.process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, cwd=cwd, start_new_session=True, shell=False, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        self.buffer = bytearray()
        self.closed = False
        self.failed = None
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)

    def exchange(self, value, timeout, *, check_required=None):
        deadline = time.monotonic() + timeout
        encoded = bounded_json_line(value)
        written = 0
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while written < len(encoded):
                if check_required is not None:
                    check_required()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.failed = 'timeout'
                    raise TimeoutError()
                wait = min(remaining, WORKER_POLL_SECONDS) if check_required is not None else remaining
                if not selector.select(wait):
                    continue
                try:
                    written += os.write(self.process.stdin.fileno(), encoded[written:written + 65536])
                except BrokenPipeError:
                    self.failed = 'worker_exit'
                    raise ProtocolError('worker_exit') from None
            selector.unregister(self.process.stdin)
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b'\n' not in self.buffer:
                if check_required is not None:
                    check_required()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.failed = 'timeout'
                    raise TimeoutError()
                wait = min(remaining, WORKER_POLL_SECONDS) if check_required is not None else remaining
                if not selector.select(wait):
                    continue
                chunk = os.read(self.process.stdout.fileno(), 65536)
                if not chunk:
                    self.failed = 'worker_exit'
                    raise ProtocolError('worker_exit')
                self.buffer.extend(chunk)
                if len(self.buffer) >= WIRE_LIMIT:
                    self.failed = 'wire_size'
                    raise ProtocolError('wire_size')
        line, _, rest = self.buffer.partition(b'\n')
        self.buffer = bytearray(rest)
        try:
            def unique_object(pairs):
                response = {}
                for key, value in pairs:
                    if key in response:
                        raise ValueError('duplicate JSON key')
                    response[key] = value
                return response
            response = json.loads(line, object_pairs_hook=unique_object, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite')))
            bounded_json_line(response)
        except (ValueError, UnicodeError, TypeError, RecursionError):
            self.failed = 'malformed_response'
            raise ProtocolError('malformed_response') from None
        return response

    def close(self, failure=False, operation='unknown', failure_identity=None):
        if self.closed:
            return
        self.closed = True
        try:
            stop_process(self.process)
        finally:
            snapshot = self.capture.close()
            self.process.stdin.close()
            self.process.stdout.close()
        if failure or self.failed:
            category, status = failure_identity if failure_identity is not None else (self.failed or 'worker_failure', self.process.returncode)
            emit_worker_failure(snapshot, self.component, category, bounded_failure_name(operation, 'unknown'), status)


class CandidateRPC:
    def __init__(self, entry):
        self.entry = entry
        self.worker = None
        self.count = 0
        self.resets = []
        self.proxy = None
        socket = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        if entry == '/broker-code/candidate_proxy.py':
            if not socket:
                raise RuntimeError('broker proxy requires authenticated socket')
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', entry)
            self.proxy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.proxy)
        elif socket:
            raise RuntimeError('broker socket requires fixed proxy entrypoint')

    def __call__(self, request, *, timeout, check_required=None):
        self.count += 1
        if self.count > RPC_LIMIT:
            raise ProtocolError('rpc_limit')
        framed_size(request)
        operation = request['op']
        if operation == 'reset':
            self.resets.append(request['seed'])
        if self.proxy is not None:
            deadline = time.monotonic() + timeout
            def timeout_handler(signum, frame):
                if check_required is not None:
                    check_required()
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('broker RPC deadline')
                signal.setitimer(signal.ITIMER_REAL, min(remaining, WORKER_POLL_SECONDS))
            previous = signal.signal(signal.SIGALRM, timeout_handler)
            signal.setitimer(signal.ITIMER_REAL, min(timeout, WORKER_POLL_SECONDS) if check_required is not None else timeout)
            try:
                response = self.proxy.handle(request)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
        else:
            if operation == 'reset':
                if self.worker is not None:
                    self.worker.close(operation='reset')
                interpreter, environment = candidate_subprocess_settings(os.environ)
                cpus = ','.join(str(value) for value in NATIVE_CPUSET[-6:])
                self.worker = JsonProcess([interpreter, '-I', '-B', '-c', NATIVE_RUNNER, self.entry, str(cpu_limit_seconds(WALL_SECONDS, 6)), cpus], environment, component='candidate')
            if self.worker is None:
                raise ProtocolError('missing_reset')
            try:
                response = self.worker.exchange(request, timeout, check_required=check_required)
            except (TimeoutError, ProtocolError, RequiredBaselineFailure) as primary:
                try:
                    self.worker.close(failure=True, operation=operation)
                except (RuntimeError, subprocess.TimeoutExpired):
                    primary.add_note('secondary candidate cleanup failure')
                self.worker = None
                raise
        framed_size(response)
        return response

    def close(self):
        if self.worker is not None:
            self.worker.close()
            self.worker = None


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
        raise TimeoutError('insufficient method reservations')
    return now + work


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead, rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        episode_started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = 'reset'
        primary_failure = None

        def call(request, *, timeout=None, check_required=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock(), timeout if timeout is not None else rpc_cap)
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                try:
                    if check_required is None:
                        return rpc(request, timeout=timeout)
                    return rpc(request, timeout=timeout, check_required=check_required)
                except (TimeoutError, ProtocolError):
                    if check_required is not None:
                        check_required()
                    raise
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
            outcomes[index] = value
            if isinstance(value, dict) and 'duration' in value:
                value['duration'] = max(0.0, clock() - episode_started)
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            if isinstance(outcomes[index], dict) and 'duration' in outcomes[index]:
                outcomes[index]['duration'] = max(0.0, clock() - episode_started)
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
    return outcomes, complete


def pack(array, dtype):
    import numpy as np
    array = np.ascontiguousarray(array, dtype=dtype)
    return {'encoding': 'base64', 'dtype': dtype, 'shape': list(array.shape), 'data': base64.b64encode(array.tobytes()).decode('ascii')}


def unpack(value, dtype, shape):
    import numpy as np
    if type(value) is not dict or set(value) != {'encoding', 'dtype', 'shape', 'data'} or value['encoding'] != 'base64' or value['dtype'] != dtype or type(value['shape']) is not list or any(type(size) is not int for size in value['shape']) or value['shape'] != list(shape) or not isinstance(value['data'], str):
        raise ProtocolError('malformed_response')
    try:
        raw = base64.b64decode(value['data'], validate=True)
    except (ValueError, TypeError):
        raise ProtocolError('invalid_base64') from None
    if len(raw) != math.prod(shape) * np.dtype(dtype).itemsize:
        raise ProtocolError('invalid_shape')
    array = np.frombuffer(raw, dtype=dtype).reshape(shape)
    if not np.isfinite(array).all():
        raise ProtocolError('nonfinite_prediction')
    return array


def preflight_protocol():
    import numpy as np
    episodes = len(CASES) * len(SEEDS) * len(CONDITIONS) + 1
    table = {'reset': episodes, 'source_chunk': episodes * 2, 'fit': episodes, 'observe': episodes * 3, 'release': episodes}
    if sum(table.values()) != RPC_LIMIT or RPC_LIMIT > 10000000:
        raise ValueError('RPC table mismatch')
    trace = [operation for episode in range(episodes) for operation in ('reset', 'source_chunk', 'source_chunk', 'fit', 'observe', 'observe', 'observe', 'release')]
    if collections.Counter(trace) != collections.Counter(table):
        raise ValueError('maximum trace mismatch')
    source = {'op': 'source_chunk', 'encoding': 'base64', 'dtype': 'uint8', 'shape': [512, 16384], 'offset': CHUNK_BYTES, 'total_bytes': 8388608, 'chunk_count': 2, 'data': base64.b64encode(b'\xff' * CHUNK_BYTES).decode('ascii')}
    requests = [source, {'op': 'fit', 'mode': 'primary', 'budgets': list(BUDGETS), 'source_groups': list(range(512))}, {'op': 'observe', 'budget': 32, **pack(np.ones((512, 32)), 'uint8')}]
    responses = [{'ok': True}, {'anchors': list(range(16352, 16384))}, pack(np.ones(512), '<f8')]
    for message in requests + responses:
        framed_size(message)
    require_joint_workload_budget(search={'episode_count': 37, 'method_count': 2, 'wall_seconds': 3600, 'startup_seconds': 300, 'reset_seconds': 2, 'cleanup_seconds': 3, 'finish_seconds': 180, 'work_seconds': METHOD_WORK_SECONDS}, final={'episode_count': 181, 'method_count': 2, 'wall_seconds': 14400, 'startup_seconds': 600, 'reset_seconds': 2, 'cleanup_seconds': 3, 'finish_seconds': 360, 'work_seconds': METHOD_WORK_SECONDS})


def load_cases(smoke):
    import numpy as np
    root = Path(os.environ.get('TASK_SOURCE_DIR', Path(__file__).resolve().parent)) / 'resources' / PLANE
    manifest_raw = (root / 'manifest.json').read_bytes()
    if hashlib.sha256(manifest_raw).hexdigest() != MANIFEST_SHA:
        raise ValueError('resource manifest integrity')
    manifest = json.loads(manifest_raw)
    if manifest['plane'] != PLANE or not manifest['cross_plane_content_disjoint']:
        raise ValueError('invalid audited resource plane')
    cases = {}
    for name in CASES[:1] if smoke else CASES:
        item = manifest['cases'][name]
        raw_matrix, raw_audit = (root / (name + '.npz')).read_bytes(), (root / (name + '.json')).read_bytes()
        if hashlib.sha256(raw_matrix).hexdigest() != item['matrix_sha256'] or hashlib.sha256(raw_audit).hexdigest() != item['audit_sha256']:
            raise ValueError('case integrity')
        matrix = np.load(root / (name + '.npz'), allow_pickle=False)['responses']
        audit = json.loads(raw_audit)
        if matrix.shape != tuple(item['shape']) or matrix.dtype != np.uint8 or not np.isin(matrix, [0, 1]).all() or matrix.shape[0] > 512 or matrix.shape[1] > 16384:
            raise ValueError('invalid production matrix')
        if len(audit['content']) != matrix.shape[1] or len(audit['rows']) != matrix.shape[0] or [entry['original_col'] for entry in audit['content']] != audit['kept_columns']:
            raise ValueError('invalid content alignment')
        groups = [entry['group'] for entry in audit['rows']]
        if len(set(groups)) < 5:
            raise ValueError('insufficient provenance groups')
        if smoke:
            columns = np.arange(min(256, matrix.shape[1]))
            matrix = matrix[:, columns]
        cases[name] = {'matrix': matrix, 'groups': groups, 'family': item['domain']}
    return cases


def split_case(case, seed, smoke):
    import numpy as np
    groups = case['groups']
    unique = sorted(set(groups), key=lambda group: hashlib.sha256(f'{seed}:{group}'.encode()).digest())
    cut = min(len(unique) - 1, max(3, round(.7 * len(unique))))
    source_set = set(unique[:cut])
    source = np.asarray([index for index, group in enumerate(groups) if group in source_set])
    target = np.asarray([index for index, group in enumerate(groups) if group not in source_set])
    if smoke:
        source = np.asarray(sorted(source, key=lambda index: (list(sorted(source_set)).index(groups[index]), int(index))))
        order = []
        for level in range(24):
            for group in sorted(source_set):
                matches = [index for index in source if groups[index] == group]
                if level < len(matches):
                    order.append(matches[level])
        source = np.asarray(order[:24])
        target = target[:4]
    if len(source) < 6 or len(target) < 2:
        raise ValueError('insufficient model split')
    source_groups = [groups[index] for index in source]
    if len(set(source_groups)) < 3:
        raise ValueError('insufficient source calibration groups')
    return case['matrix'][source], case['matrix'][target], source_groups, [groups[index] for index in target]


def anchor_baseline(source, target, budget, seed):
    import numpy as np
    from sklearn.cluster import KMeans
    vectors = source.astype(float).T
    vectors -= vectors.mean(axis=1, keepdims=True)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors /= np.maximum(norms, 1e-8)
    clusters = KMeans(n_clusters=budget, random_state=seed, n_init=1, max_iter=30).fit(vectors)
    representatives = []
    for center in clusters.cluster_centers_:
        distance = np.sum((vectors - center) ** 2, axis=1)
        distance[representatives] = np.inf
        representatives.append(int(np.argmin(distance)))
    distances = np.stack([np.sum((vectors - vectors[index]) ** 2, axis=1) for index in representatives], axis=1)
    assignment = np.argmin(distances, axis=1)
    weights = np.bincount(assignment, minlength=budget) / len(vectors)
    if len(set(representatives)) != budget or not np.isclose(weights.sum(), 1):
        raise RuntimeError('invalid anchor baseline')
    return target[:, representatives] @ weights


def irt_baseline(source, target):
    import numpy as np
    from scipy.optimize import minimize
    from scipy.special import expit, logit
    source = source.astype(float)
    rows, columns = source.shape
    initial_theta = logit(np.clip(source.mean(axis=1), .02, .98))
    initial_theta = (initial_theta - initial_theta.mean()) / max(initial_theta.std(), .1)
    initial = np.concatenate((initial_theta, np.zeros(columns), -logit(np.clip(source.mean(axis=0), .02, .98))))

    def objective(parameters):
        theta = parameters[:rows]
        log_discrimination = parameters[rows:rows + columns]
        discrimination = np.exp(log_discrimination)
        difficulty = parameters[rows + columns:]
        logits = theta[:, None] * discrimination - difficulty
        residual = expit(logits) - source
        loss = np.sum(np.logaddexp(0, logits) - source * logits) + .5 * np.sum(theta ** 2) + .05 * np.sum(log_discrimination ** 2) + .005 * np.sum(difficulty ** 2)
        gradient = np.concatenate((residual @ discrimination + theta, np.sum(residual * theta[:, None], axis=0) * discrimination + .1 * log_discrimination, -residual.sum(axis=0) + .01 * difficulty))
        return float(loss), gradient

    fitted = minimize(objective, initial, method='L-BFGS-B', jac=True, bounds=[(-6, 6)] * rows + [(-3, 2)] * columns + [(-8, 8)] * columns, options={'maxiter': 40, 'maxls': 20, 'ftol': 1e-7})
    if not np.isfinite(fitted.x).all() or fitted.fun > objective(initial)[0] + 1e-7:
        raise RuntimeError('invalid IRT solver result')
    discrimination = np.exp(fitted.x[rows:rows + columns])
    difficulty = fitted.x[rows + columns:]
    probability = expit(-difficulty)
    order = np.argsort(-(discrimination ** 2 * probability * (1 - probability)), kind='stable')[:32]
    predictions = []
    for budget in BUDGETS:
        selected = order[:budget]
        answers = target[:, selected]
        ability = np.zeros(len(target))
        for step in range(30):
            probability = expit(ability[:, None] * discrimination[selected] - difficulty[selected])
            gradient = ((probability - answers) * discrimination[selected]).sum(axis=1) + ability
            hessian = (probability * (1 - probability) * discrimination[selected] ** 2).sum(axis=1) + 1
            ability = np.clip(ability - np.clip(gradient / hessian, -1, 1), -6, 6)
        predictions.append(expit(ability[:, None] * discrimination - difficulty).mean(axis=1))
    return np.asarray(predictions)


def baseline_worker():
    import numpy as np
    from threadpoolctl import threadpool_limits
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit_seconds(WALL_SECONDS, 2),) * 2)
    if hasattr(os, 'sched_getaffinity'):
        allowed = sorted(os.sched_getaffinity(0))
        os.sched_setaffinity(0, allowed[:min(2, len(allowed))])
    request = json.loads(sys.stdin.buffer.readline(WIRE_LIMIT))
    source = unpack(request['source'], 'uint8', request['source']['shape'])
    target = unpack(request['target'], 'uint8', request['target']['shape'])
    seed = request['seed']
    with threadpool_limits(limits=2):
        started = time.monotonic()
        order = np.random.default_rng(seed).permutation(source.shape[1])[:32]
        result = {'uniform': np.asarray([target[:, order[:budget]].mean(axis=1) for budget in BUDGETS]), 'source_mean': np.full((3, len(target)), source.mean()), 'anchor': np.asarray([anchor_baseline(source, target, budget, seed) for budget in BUDGETS]), 'irt': irt_baseline(source, target)}
        elapsed = time.monotonic() - started
    response = {name: pack(value, '<f8') for name, value in result.items()}
    response['productive_seconds'] = elapsed
    sys.stdout.buffer.write(bounded_json_line(response))
    sys.stdout.flush()


class BaselineJob:
    def __init__(self, source, target, seed, allowance):
        _, environment = candidate_subprocess_settings(os.environ)
        environment.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
        for name in ('AGENTIC_TASK_DRAFT_SMOKE', 'AGENTIC_TASK_QUALIFICATION'):
            if os.environ.get(name) == '1':
                environment[name] = '1'
        self.worker = JsonProcess([sys.executable, '-I', '-B', str(Path(__file__).resolve()), '--baseline-worker'], environment, component='baseline')
        self.deadline = time.monotonic() + allowance
        self.value = None
        self.error = None
        self.category = None
        self.diagnostic = None
        self.failure_status = None
        self.request = {'source': pack(source, 'uint8'), 'target': pack(target, 'uint8'), 'seed': seed}
        self.thread = threading.Thread(target=self._run)
        self.thread.start()

    def _run(self):
        try:
            self.value = self.worker.exchange(self.request, max(.001, self.deadline - time.monotonic()))
        except TimeoutError as error:
            self.error = error
            self.category = 'baseline_timeout'
        except ProtocolError as error:
            self.error = error
            status = self.worker.process.poll()
            if status is None and error.category == 'worker_exit':
                try:
                    status = self.worker.process.wait(timeout=.1)
                except subprocess.TimeoutExpired:
                    pass
            self.category = 'baseline_signal' if status is not None and status < 0 else 'baseline_exit' if status is not None else 'baseline_result_failure'
        except Exception as error:
            self.error = error

    def failure_category(self):
        if self.diagnostic is not None:
            return self.diagnostic
        status = self.worker.process.poll()
        if status is not None and status != 0:
            return 'baseline_signal' if status < 0 else 'baseline_exit'
        if self.category:
            return self.category
        if self.thread.is_alive() and time.monotonic() >= self.deadline:
            return 'baseline_timeout'
        return None

    def record(self, category):
        if self.diagnostic is None:
            self.diagnostic = bounded_failure_name(category, 'invalid_baseline_diagnostic')
            self.failure_status = self.worker.process.poll()
            record_failure({'component': 'baseline', 'category': self.diagnostic, 'operation': 'baseline_worker', 'status': self.failure_status})

    def result(self, timeout):
        self.thread.join(timeout=max(0, timeout))
        category = self.failure_category()
        if category:
            fail_required_baseline(category, self.cancel, self.record)
        if self.thread.is_alive():
            raise TimeoutError()
        if self.error is not None:
            raise self.error
        return self.value

    def cancel(self):
        identity = (self.diagnostic, self.failure_status) if self.diagnostic is not None else None
        self.worker.close(failure=self.error is not None or self.diagnostic is not None, operation='baseline_worker', failure_identity=identity)
        self.thread.join(timeout=1)
        if self.thread.is_alive():
            raise RuntimeError('baseline transport cleanup unresolved')


def episode_worst(episode):
    return {'mae': 1.0, 'rmse': 1.0, 'spearman': -1.0, 'kendall_tau_b': -1.0, 'control_failure': 1.0, 'success': False, 'predictions': None, 'anchors': None, 'duration': 0.0}


def correlation(function, truth, prediction):
    import numpy as np
    if np.ptp(truth) == 0 or np.ptp(prediction) == 0:
        return 0.0
    value = float(function(truth, prediction).statistic)
    if not math.isfinite(value):
        raise ValueError('unexpected nonfinite rank statistic')
    return value


class Investigation:
    def __init__(self, cases, smoke):
        self.cases = cases
        self.smoke = smoke
        self.pairs = {}
        self.originals = {}
        self.baselines = {}
        self.baseline_complete = True
        for name, case in cases.items():
            for seed in SEEDS[:1] if smoke else SEEDS:
                self.pairs[name, seed] = split_case(case, seed, smoke)

    def evaluate(self, episode, call, deadline):
        import numpy as np
        from scipy.stats import spearmanr, kendalltau
        started = time.monotonic()
        name, seed, condition = episode['case'], episode['seed'], episode['condition']
        source, target, source_groups, target_groups = self.pairs[name, seed]
        truth = target.mean(axis=1)
        work = 4.5 if self.smoke else METHOD_WORK_SECONDS
        method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline, methods_remaining=1, work_seconds=work, cleanup_seconds=3)
        baseline = None
        base_call = call
        if condition == 'primary' and not episode.get('replay'):
            baseline = BaselineJob(source, target, seed, work)
            self.baselines[name, seed] = None
            call = guard_required_baseline(call, baseline.failure_category, baseline.cancel, baseline.record)

        def bounded_call(request):
            return call(request, timeout=max(0, method_deadline - time.monotonic()))

        primary_error = None
        try:
            raw = source.tobytes()
            chunks = math.ceil(len(raw) / CHUNK_BYTES)
            if chunks < 1 or chunks > 2:
                raise ValueError('source transfer cap')
            for offset in range(0, len(raw), CHUNK_BYTES):
                response = bounded_call({'op': 'source_chunk', 'encoding': 'base64', 'dtype': 'uint8', 'shape': list(source.shape), 'offset': offset, 'total_bytes': len(raw), 'chunk_count': chunks, 'data': base64.b64encode(raw[offset:offset + CHUNK_BYTES]).decode('ascii')})
                if type(response) is not dict or response != {'ok': True} or type(response.get('ok')) is not bool:
                    raise ProtocolError('invalid_chunk_ack')
            mode = condition if condition in ('no_diversity', 'no_calibration') else 'primary'
            group_names = sorted(set(source_groups))
            response = bounded_call({'op': 'fit', 'mode': mode, 'budgets': list(BUDGETS), 'source_groups': [group_names.index(group) for group in source_groups]})
            if type(response) is not dict or set(response) != {'anchors'} or type(response['anchors']) is not list:
                raise ProtocolError('invalid_anchors')
            anchors = response['anchors']
            if len(anchors) != 32 or any(type(index) is not int or index < 0 or index >= source.shape[1] for index in anchors) or len(set(anchors)) != 32:
                raise ProtocolError('invalid_anchors')
            original = self.originals.get((name, seed))
            structural = True
            if mode == 'primary' and condition != 'primary' or mode == 'no_calibration':
                structural = original is not None and anchors == original['anchors']
            if mode == 'no_diversity':
                structural = anchors == np.random.default_rng(seed).permutation(source.shape[1])[:32].tolist()
            predictions = []
            structural_failures = []
            for budget in BUDGETS:
                checkpoint_structural = structural
                observations = target[:, anchors[:budget]].copy()
                permutation = np.roll(np.arange(len(target)), 1)
                if condition == 'constant':
                    if not np.any(observations):
                        raise ProtocolError('vacuous_constant')
                    observations.fill(0)
                elif condition == 'copy':
                    if np.all(observations == observations[0]):
                        raise ProtocolError('vacuous_copy')
                    observations[:] = observations[0]
                elif condition == 'permuted':
                    modified = observations[permutation]
                    if np.array_equal(modified, observations) or len(np.unique(observations, axis=0)) < 2:
                        raise ProtocolError('vacuous_permutation')
                    observations = modified
                response = bounded_call({'op': 'observe', 'budget': budget, **pack(observations, 'uint8')})
                prediction = unpack(response, '<f8', (len(target),))
                if np.any(prediction < 0) or np.any(prediction > 1):
                    raise ProtocolError('prediction_range')
                if condition in ('constant', 'copy') and np.max(prediction) - np.min(prediction) > 1e-10:
                    checkpoint_structural = False
                if mode == 'no_calibration' and not np.allclose(prediction, observations.mean(axis=1), rtol=0, atol=1e-10):
                    checkpoint_structural = False
                structural_failures.append(float(not checkpoint_structural))
                predictions.append(prediction.copy())
            require_reset_ack(bounded_call({'op': 'release'}))
            if baseline is not None:
                result = collect_required_baseline(baseline.result, deadline=min(method_deadline, baseline.deadline), clock=time.monotonic, cancel_work=baseline.cancel, record_failure=baseline.record)
                if type(result) is not dict or set(result) != {'uniform', 'source_mean', 'anchor', 'irt', 'productive_seconds'}:
                    fail_required_baseline('baseline_result_failure', baseline.cancel, baseline.record)
                validated = {}
                for method in ('uniform', 'source_mean', 'anchor', 'irt'):
                    try:
                        array = unpack(result[method], '<f8', (3, len(target)))
                    except ProtocolError:
                        fail_required_baseline('baseline_result_failure', baseline.cancel, baseline.record)
                    if np.any(array < 0) or np.any(array > 1):
                        fail_required_baseline('baseline_result_failure', baseline.cancel, baseline.record)
                    validated[method] = array.copy()
                if type(result['productive_seconds']) not in (float, int) or not math.isfinite(result['productive_seconds']) or result['productive_seconds'] <= 0:
                    fail_required_baseline('baseline_result_failure', baseline.cancel, baseline.record)
                self.baselines[name, seed] = validated
            predictions = np.asarray(predictions)
            outcome = {'mae': float(np.abs(predictions - truth).mean()), 'rmse': float(np.sqrt(np.mean((predictions - truth) ** 2, axis=1)).mean()), 'spearman': float(np.mean([correlation(spearmanr, truth, row) for row in predictions])), 'kendall_tau_b': float(np.mean([correlation(kendalltau, truth, row) for row in predictions])), 'control_failure': float(np.mean(structural_failures)), 'success': True, 'predictions': predictions, 'anchors': anchors, 'duration': time.monotonic() - started}
            if condition == 'primary' and not episode.get('replay'):
                self.originals[name, seed] = outcome
            return outcome
        except (TimeoutError, RequiredBaselineFailure, ProtocolError, InvalidResetResponse) as error:
            primary_error = error
            raise
        finally:
            if baseline is not None:
                try:
                    baseline.cancel()
                except (RuntimeError, subprocess.TimeoutExpired) as cleanup_error:
                    if primary_error is None:
                        raise
                    primary_error.add_note('secondary baseline cleanup failure')
                if self.baselines[name, seed] is None:
                    self.baseline_complete = False


def aggregate(episodes, outcomes, investigation):
    import numpy as np
    cases = list(investigation.cases)
    seeds = SEEDS[:1] if investigation.smoke else SEEDS
    families = sorted({investigation.cases[name]['family'] for name in cases})
    weights = {name: 1 / len(families) / sum(investigation.cases[other]['family'] == investigation.cases[name]['family'] for other in cases) for name in cases}
    records = {(episode['case'], episode['seed'], episode['condition']): outcome for episode, outcome in zip(episodes[:-1], outcomes[:-1])}

    def mean_condition(condition, metric):
        return sum(weights[name] / len(seeds) * records[name, seed, condition][metric] for name in cases for seed in seeds)

    metrics = {name: 1.0 for name in METRICS}
    for metric in ('mae', 'rmse', 'spearman', 'kendall_tau_b'):
        metrics[metric] = mean_condition('primary', metric)
    metrics['combined_score'] = 1 - metrics['mae']
    for condition in CONDITIONS[1:]:
        metrics[condition + '_mae'] = mean_condition(condition, 'mae')
    deltas = {}
    paired = True
    for method in ('uniform', 'source_mean', 'anchor', 'irt'):
        value = 0.0
        for name in cases:
            for seed in seeds:
                baseline = investigation.baselines.get((name, seed))
                truth = investigation.pairs[name, seed][1].mean(axis=1)
                error = 1.0 if baseline is None else float(np.abs(baseline[method] - truth).mean())
                value += weights[name] / len(seeds) * error
                if method == 'anchor':
                    primary = records[name, seed, 'primary']
                    if baseline is None or primary['predictions'] is None:
                        paired = False
                        deltas[name, seed] = None
                    else:
                        deltas[name, seed] = (np.abs(primary['predictions'] - truth) - np.abs(baseline[method] - truth)).mean(axis=0)
        metrics[method + '_mae'] = value
    metrics['delta_anchor_mae'] = float(sum(weights[name] / len(seeds) * (1.0 if deltas[name, seed] is None else deltas[name, seed].mean()) for name in cases for seed in seeds))
    metrics['delta_anchor_ci_low'], metrics['delta_anchor_ci_high'] = -1.0, 1.0
    if paired:
        random = np.random.default_rng(1729)
        lineages = sorted({group for pair in investigation.pairs.values() for group in pair[3]})
        draws = []
        for repeat in range(1000):
            seed_indices = random.integers(0, len(seeds), len(seeds))
            counts = np.bincount(random.integers(0, len(lineages), len(lineages)), minlength=len(lineages))
            value = 0.0
            supported = True
            for name in cases:
                for seed_index in seed_indices:
                    seed = seeds[int(seed_index)]
                    multipliers = np.asarray([counts[lineages.index(group)] for group in investigation.pairs[name, seed][3]])
                    if multipliers.sum() == 0:
                        supported = False
                        break
                    value += weights[name] / len(seeds) * float(np.average(deltas[name, seed], weights=multipliers))
            if not supported:
                draws = []
                break
            draws.append(value)
        if draws:
            metrics['delta_anchor_ci_low'], metrics['delta_anchor_ci_high'] = map(float, np.quantile(draws, [.025, .975]))
    replay = outcomes[-1]
    first = outcomes[0]
    reset_error = 1.0
    if replay['success'] and first['success'] and replay['anchors'] == first['anchors']:
        reset_error = float(np.max(np.abs(replay['predictions'] - first['predictions'])))
    metrics['reset_mae'] = replay['mae']
    metrics['reset_max_abs_error'] = reset_error
    metrics['control_failure_rate'] = (sum(mean_condition(condition, 'control_failure') for condition in ('constant', 'copy', 'permuted')) + float(reset_error > 1e-10)) / 4
    metrics['missing_episode_rate'] = sum(not outcome['success'] for outcome in outcomes) / len(episodes)
    correct = all(outcome['success'] and outcome['control_failure'] == 0 for outcome in outcomes) and reset_error <= 1e-10 and investigation.baseline_complete and all(investigation.baselines.get((name, seed)) is not None for name in cases for seed in seeds)
    metrics['correct'] = int(correct)
    if set(metrics) != set(METRICS) or not all(type(value) in (int, float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError('invalid aggregate metrics')
    evidence = []
    for seed in seeds:
        selected = [(episode, outcome) for episode, outcome in zip(episodes, outcomes) if episode['seed'] == seed]
        seed_mae = sum(weights[name] * records[name, seed, 'primary']['mae'] for name in cases)
        evidence.append({'seed': seed, 'score': 1 - seed_mae, 'correct': bool(all(outcome['success'] and outcome['control_failure'] == 0 for episode, outcome in selected) and reset_error <= 1e-10 and investigation.baseline_complete), 'duration_seconds': float(sum(outcome['duration'] for episode, outcome in selected))})
        if PLANE == 'final':
            solutions = {}
            for name in cases:
                baseline = investigation.baselines.get((name, seed))
                conditions = {}
                for episode, outcome in selected:
                    if episode['case'] != name:
                        continue
                    condition = 'reset_replay' if episode.get('replay') else episode['condition']
                    conditions[condition] = {'completed': outcome['success'], 'anchors': outcome['anchors'], 'predictions': None if outcome['predictions'] is None else outcome['predictions'].tolist(), 'mae': outcome['mae'], 'rmse': outcome['rmse'], 'spearman': outcome['spearman'], 'kendall_tau_b': outcome['kendall_tau_b'], 'structural_failure': outcome['control_failure'], 'duration_seconds': outcome['duration']}
                solutions[name] = {'target_full_means': investigation.pairs[name, seed][1].mean(axis=1).tolist(), 'target_lineages': investigation.pairs[name, seed][3], 'conditions': conditions, 'baseline_predictions': None if baseline is None else {method: value.tolist() for method, value in baseline.items()}, 'baseline_failure_mae': 1.0 if baseline is None else None}
            evidence[-1]['solution'] = {'budgets': list(BUDGETS), 'fixed_item_universes': True, 'cases': solutions}
    return metrics, bool(correct), {'schema_version': 1, 'episodes': evidence}


def write_results(directory, metrics, correct, feasible, evidence=None):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'metrics.json').write_bytes(bounded_json_line(metrics))
    (directory / 'correct.json').write_bytes(bounded_json_line({'correct': bool(correct)}))
    if evidence is not None:
        (directory / 'evaluation_evidence.json').write_bytes(bounded_json_line(evidence, 16 * 1024 * 1024))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (directory / 'qualification.json').write_bytes(bounded_json_line({'schema_version': 1, 'feasible': bool(feasible)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    directory = Path(arguments.results_dir)
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    ceiling = 118 if smoke else WALL_SECONDS
    startup = 5 if smoke else 60
    hard_deadline = STARTED + ceiling - startup
    rpc = None
    try:
        os.environ.update(OMP_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2', MKL_NUM_THREADS='2', NUMEXPR_NUM_THREADS='2')
        if NATIVE_CPUSET:
            os.sched_setaffinity(0, NATIVE_CPUSET[:2])
        preflight_protocol()
        cases = load_cases(smoke)
        investigation = Investigation(cases, smoke)
        episodes = [{'case': name, 'seed': seed, 'condition': condition} for name in cases for seed in (SEEDS[:1] if smoke else SEEDS) for condition in CONDITIONS]
        episodes.append({'case': next(iter(cases)), 'seed': SEEDS[0], 'condition': 'primary', 'replay': True})
        rpc = CandidateRPC(str(Path(arguments.program_path).absolute()))
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline, finish_reserve=8 if smoke else 180, reset_timeout=2, episode_overhead=8, rpc_cap=5 if smoke else METHOD_WORK_SECONDS, clock=time.monotonic, rpc=rpc, evaluate=investigation.evaluate, worst_case=episode_worst, record_failure=record_failure)
        metrics, correct, evidence = aggregate(episodes, outcomes, investigation)
        if rpc.resets != [episode['seed'] for episode in episodes]:
            raise RuntimeError('reset transcript mismatch')
        rpc.close()
        correct = bool(correct and complete and time.monotonic() < hard_deadline)
        metrics['correct'] = int(correct)
        feasible = not smoke and complete and investigation.baseline_complete and metrics['missing_episode_rate'] == 0 and time.monotonic() < hard_deadline
        write_results(directory, metrics, correct, feasible, evidence)
    except Exception as error:
        if rpc is not None:
            rpc.close()
        metrics = {name: 1.0 for name in METRICS}
        metrics.update(combined_score=0.0, spearman=-1.0, kendall_tau_b=-1.0, delta_anchor_ci_low=-1.0, correct=0)
        write_results(directory, metrics, False, False)
        if PLANE == 'search':
            name = type(error).__name__[:80]
            message = str(error)[:160] if not isinstance(error, ProtocolError) else 'candidate protocol failure'
            print(f'evaluator_exception type={name} message={message}', file=sys.stderr)
        else:
            print('evaluator_exception type=EvaluationFailure message=sealed_evaluation_failure', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    if sys.argv[1:] == ['--baseline-worker']:
        try:
            baseline_worker()
        except Exception as error:
            if repair_visibility():
                report_worker_exception(error)
            else:
                print('baseline_worker_failure', file=sys.stderr, flush=True)
            raise SystemExit(1)
    else:
        raise SystemExit(main())
