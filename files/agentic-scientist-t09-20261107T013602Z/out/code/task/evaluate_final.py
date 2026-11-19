"""Offline, evaluator-owned GATE experiment; candidate outputs are predictions only."""

import time

START = time.monotonic()

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
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import zipfile

for _thread_name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_thread_name] = '1'

import networkx as nx
import numpy as np
from scipy import sparse

PLANE = 'final'
MANIFEST_SHA256 = 'af45e7f31ed7c4628090550af80080d3a4ee609b12424b60d96738b426953eba'
WALL = 900 if PLANE == 'search' else 7200
STARTUP = 30 if PLANE == 'search' else 180
WORK = .25 if PLANE == 'search' else 1.2
FINISH = 15 if PLANE == 'search' else 30
OVERHEAD = 2.7
RESET_TIMEOUT = 1.0
CHUNK = 4 * 1024 * 1024
MAX_CHUNKS = 8
WIRE = 64 * 1024 * 1024
METRICS = ('combined_score', 'mean_capped_normalized_rmse', 'mean_absolute_capped_normalized_bias',
           'failed_episode_fraction', 'control_success_fraction')
BASELINES = ('difference_in_means', 'own_treatment_ols', 'one_hop_ols', 'copy_observed', 'constant_prediction')


def bounded_json_line(value, wire_limit=WIRE):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(encoded) >= wire_limit:
        raise ProtocolError('message_limit')
    return encoded


def bounded_failure_name(value, fallback):
    import re
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value) else fallback


class InvalidResetResponse(RuntimeError):
    pass


class ProtocolError(RuntimeError):
    pass


class BrokerTransportFailure(RuntimeError):
    def __init__(self, operation):
        self.failure = {'component': 'broker', 'category': 'broker_transport_failure',
                        'operation': bounded_failure_name(operation, 'unknown')}
        super().__init__('broker transport failed')


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise InvalidResetResponse('invalid reset response')


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'invalid_baseline_diagnostic')
        super().__init__('required baseline failed')


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, BrokerTransportFailure):
            return dict(context.failure)
        if isinstance(context, InvalidResetResponse):
            return {'component': 'candidate', 'category': 'invalid_reset_response', 'operation': 'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component': 'baseline', 'category': context.category, 'operation': 'baseline_worker'}
        if isinstance(context, ProtocolError):
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


def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid time allowance')
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError('work allowance must be positive')
    return value


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError('invalid remaining method count')
    if now + (methods_remaining + 1) * (work + cleanup_seconds) > episode_deadline:
        raise TimeoutError('insufficient matched method reservations')
    return now + work


def require_joint_workload_budget():
    for episodes, wall, startup, work, finish in ((161, 900, 30, .25, 15), (625, 7200, 180, 1.2, 30)):
        needed = startup + finish + episodes * (RESET_TIMEOUT + OVERHEAD + 6 * (work + .01))
        if needed > wall:
            raise ValueError('joint workload budget infeasible')


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


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ',
                     'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES',
                     'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


WORKER = r'''
import base64, contextlib, ctypes, errno, importlib.util, json, math, os, resource, signal, sys
role, entrypoint, cpu_seconds, memory_bytes, allowed_cpus = sys.argv[1:]
resource.setrlimit(resource.RLIMIT_CPU, (int(cpu_seconds), int(cpu_seconds)))
resource.setrlimit(resource.RLIMIT_AS, (int(memory_bytes), int(memory_bytes)))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
os.sched_setaffinity(0, [int(value) for value in allowed_cpus.split(',')])
if role == 'candidate':
    libc = ctypes.CDLL(None, use_errno=True)
    class Ruleset(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]
    class PathRule(ctypes.Structure):
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 3:
        raise RuntimeError('Landlock ABI 3 required')
    handled = (1 << 15) - 1
    ruleset = Ruleset(handled)
    descriptor = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
    if descriptor < 0:
        raise RuntimeError('Landlock ruleset failed')
    allowed = [sys.base_prefix, sys.prefix, '/usr', '/lib', '/lib64', os.getcwd()]
    for directory in sorted(set(allowed)):
        if not os.path.exists(directory):
            continue
        handle = os.open(directory, os.O_PATH | os.O_CLOEXEC)
        rule = PathRule((1 << 0) | (1 << 2) | (1 << 3), handle)
        if libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0) != 0:
            raise RuntimeError('Landlock path rule failed')
        os.close(handle)
    if libc.prctl(38, 1, 0, 0, 0) != 0 or libc.syscall(446, descriptor, 0) != 0:
        raise RuntimeError('Landlock restriction failed')
    os.close(descriptor)
    seccomp = ctypes.CDLL('libseccomp.so.2')
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    context = seccomp.seccomp_init(0x7fff0000)
    for name in ('socket', 'socketpair', 'connect', 'bind', 'listen', 'accept', 'accept4',
                 'ptrace', 'process_vm_readv', 'process_vm_writev', 'pidfd_open', 'pidfd_getfd',
                 'fork', 'vfork', 'execve', 'execveat', 'mount', 'unshare', 'setns',
                 'bpf', 'io_uring_setup', 'keyctl', 'kill', 'tkill', 'tgkill',
                 'rt_sigqueueinfo', 'rt_tgsigqueueinfo', 'pidfd_send_signal',
                 'sched_setaffinity', 'sched_setscheduler', 'sched_setparam', 'setpriority', 'ioprio_set'):
        number = seccomp.seccomp_syscall_resolve_name(name.encode())
        if number >= 0 and seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM, number, 0) != 0:
            raise RuntimeError('seccomp rule failed')
    class Comparison(ctypes.Structure):
        _fields_ = [('arg', ctypes.c_uint), ('op', ctypes.c_int), ('datum_a', ctypes.c_uint64), ('datum_b', ctypes.c_uint64)]
    if seccomp.seccomp_rule_add(context, 0x50000 | errno.ENOSYS,
            seccomp.seccomp_syscall_resolve_name(b'clone3'), 0) != 0:
        raise RuntimeError('seccomp clone3 compatibility rule failed')
    comparison = Comparison(0, 7, 0x10000, 0)
    peer_comparison = Comparison(0, 1, 0, 0)
    if seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM,
            seccomp.seccomp_syscall_resolve_name(b'prlimit64'), 1, peer_comparison) != 0:
        raise RuntimeError('seccomp peer resource rule failed')
    if seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM,
            seccomp.seccomp_syscall_resolve_name(b'clone'), 1, comparison) != 0:
        raise RuntimeError('seccomp clone rule failed')
    if seccomp.seccomp_load(context) != 0:
        raise RuntimeError('seccomp load failed')
    seccomp.seccomp_release(context)
with contextlib.redirect_stdout(sys.stderr):
    if role == 'candidate':
        sys.path.insert(0, os.getcwd())
        spec = importlib.util.spec_from_file_location('candidate', entrypoint)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handle = module.handle
    else:
        import numpy as np
        def handle(request):
            count, width, edge_count = request['n'], request['p'], request['m']
            packed = base64.b64decode(request['data'], validate=True)
            edges = np.frombuffer(packed, '<i4', 2 * edge_count).reshape(-1, 2)
            covariates = np.frombuffer(packed, '<f8', count * width, 8 * edge_count).reshape(count, width)
            assignment = np.frombuffer(packed, 'u1', count, 8 * edge_count + 8 * count * width).astype(float)
            outcome = np.frombuffer(packed, '<f8', count, 8 * edge_count + 8 * count * width + count)
            method = request['method']
            if method in ('copy_observed', 'constant_prediction'):
                observed_prediction = outcome.copy() if method == 'copy_observed' else np.full(count, outcome.mean())
                treated_prediction = observed_prediction.copy()
                control_prediction = observed_prediction.copy()
                return {'estimate': float(np.mean(treated_prediction - control_prediction))}
            if assignment.min() == assignment.max():
                raise RuntimeError('missing_arm')
            if method == 'difference_in_means':
                return {'estimate': float(outcome[assignment == 1].mean() - outcome[assignment == 0].mean())}
            design = np.column_stack((np.ones(count), covariates, assignment))
            if method == 'one_hop_ols':
                degree = np.bincount(edges.ravel(), minlength=count)
                exposure = np.zeros(count)
                np.add.at(exposure, edges[:, 0], assignment[edges[:, 1]])
                np.add.at(exposure, edges[:, 1], assignment[edges[:, 0]])
                design = np.column_stack((design, exposure / np.maximum(degree, 1)))
            coefficients = np.linalg.lstsq(design, outcome, rcond=None)[0]
            contrast = coefficients[width + 1]
            if method == 'one_hop_ols':
                contrast += coefficients[-1] * np.mean(degree > 0)
            return {'estimate': float(contrast)}
for line in sys.stdin.buffer:
    request = json.loads(line)
    with contextlib.redirect_stdout(sys.stderr):
        response = handle(request)
    encoded = json.dumps(response, allow_nan=False, separators=(',', ':')).encode() + b'\n'
    if len(encoded) >= 64 * 1024 * 1024:
        raise RuntimeError('message_limit')
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


class ProcessChannel:
    def __init__(self, role, entrypoint, directory):
        interpreter, environment = candidate_subprocess_settings(os.environ)
        cpus = sorted(os.sched_getaffinity(0))[:4]
        cpus = cpus[-2:] if role == 'candidate' else cpus[:2]
        self.role = role
        self.process = subprocess.Popen([interpreter, '-I', '-B', '-u', '-c', WORKER, role,
                                         str(entrypoint), str(math.ceil(WALL * 2)), str(8 * 1024**3),
                                         ','.join(map(str, cpus))], cwd=directory, env=environment,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                        start_new_session=True, shell=False, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.closed = False
        self.failure_category = None
        self.exit_status = None
        self.snapshot = None
        self.failure = None

    def check(self):
        status = self.process.poll()
        if status is not None:
            self.exit_status = status
            self.failure_category = 'baseline_signal' if status < 0 else 'baseline_exit'
            return self.failure_category
        return None

    def exchange(self, request, timeout):
        try:
            return self._exchange(request, timeout)
        except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
            if self.role == 'baseline':
                category = (error.category if isinstance(error, RequiredBaselineFailure) else
                            'baseline_timeout' if isinstance(error, TimeoutError) else 'baseline_result_failure')
                self.failure = {'component': 'baseline', 'category': category, 'operation': 'baseline_worker'}
            else:
                self.failure = describe_episode_failure(error, request.get('op', 'unknown'))
            raise

    def _exchange(self, request, timeout):
        deadline = time.monotonic() + timeout
        payload = bounded_json_line(request)
        written = 0
        response = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while True:
                if self.check() is not None:
                    if self.role == 'baseline':
                        raise RequiredBaselineFailure(self.failure_category)
                    raise ProtocolError('candidate_exit')
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                if not selector.select(min(.02, remaining)):
                    continue
                try:
                    if written < len(payload):
                        written += os.write(self.process.stdin.fileno(), payload[written:written + 65536])
                        if written == len(payload):
                            selector.unregister(self.process.stdin)
                            selector.register(self.process.stdout, selectors.EVENT_READ)
                    else:
                        chunk = os.read(self.process.stdout.fileno(), 65536)
                        if not chunk:
                            status = self.process.poll()
                            if self.role == 'baseline':
                                self.exit_status = status
                                category = ('baseline_result_failure' if status is None else
                                            'baseline_signal' if status < 0 else 'baseline_exit')
                                raise RequiredBaselineFailure(category)
                            raise ProtocolError('candidate_exit')
                        response.extend(chunk)
                        if len(response) >= WIRE:
                            raise ProtocolError('message_limit')
                        if b'\n' in response:
                            if not response.endswith(b'\n') or response.count(b'\n') != 1:
                                raise ProtocolError('invalid_json_line')
                            try:
                                return json.loads(response, parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                            except (ValueError, UnicodeError, RecursionError):
                                raise ProtocolError('invalid_json_line') from None
                except BlockingIOError:
                    continue
                except BrokenPipeError:
                    if self.role == 'baseline':
                        status = self.process.poll()
                        self.exit_status = status
                        category = ('baseline_result_failure' if status is None else
                                    'baseline_signal' if status < 0 else 'baseline_exit')
                        raise RequiredBaselineFailure(category) from None
                    raise ProtocolError('candidate_exit') from None

    def close(self, failed=False):
        if self.closed:
            return
        self.closed = True
        try:
            if self.process.poll() is None:
                os.killpg(self.process.pid, signal.SIGTERM)
                try:
                    self.process.wait(timeout=.1)
                except subprocess.TimeoutExpired:
                    os.killpg(self.process.pid, signal.SIGKILL)
                    self.process.wait(timeout=.2)
        finally:
            self.process.stdin.close()
            self.process.stdout.close()
            self.snapshot = self.capture.close()
            if failed:
                failure = dict(self.failure or {'component': self.role, 'category': 'worker_failure',
                                                'operation': 'worker'})
                failure.update({name: self.snapshot[name] for name in (
                    'observed_bytes', 'retained_bytes', 'truncated', 'capture_error')})
                failure['exit_status'] = self.process.returncode
                failure['observed_exit_status'] = self.exit_status
                if self.process.returncode is not None and self.process.returncode < 0:
                    failure['signal'] = -self.process.returncode
                record_failure(failure)
                if PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                                          or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'):
                    print(self.snapshot['stderr'], end='', file=sys.stderr)


class Candidate:
    def __init__(self, program_path, rpc_budget):
        self.count = 0
        self.rpc_budget = rpc_budget
        self.channel = None
        self.directory = None
        self.proxy = None
        self.broker_usable = True
        path = Path(program_path)
        if program_path == '/broker-code/candidate_proxy.py':
            if not os.environ.get('AGENTIC_CANDIDATE_SOCKET'):
                raise RuntimeError('broker socket required')
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.directory = tempfile.TemporaryDirectory(prefix='gate-candidate-')
            destination = Path(self.directory.name) / 'code'
            destination.mkdir()
            total_size = 0
            for source in path.resolve().parent.rglob('*'):
                if source.is_symlink():
                    raise ValueError('candidate symlink forbidden')
                if source.is_file():
                    total_size += source.stat().st_size
                    if total_size > 50 * 1024**2:
                        raise ValueError('candidate source too large')
                    target = destination / source.relative_to(path.resolve().parent)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
            self.entrypoint = destination / path.name

    def rpc(self, request, timeout):
        if not self.broker_usable:
            raise BrokerTransportFailure(request.get('op', 'unknown'))
        if request['op'] != 'reset' and hasattr(self, 'method_deadline'):
            timeout = min(timeout, self.method_deadline - time.monotonic())
        if timeout <= 0:
            raise TimeoutError()
        self.count += 1
        if self.count > self.rpc_budget:
            raise ProtocolError('rpc_budget')
        bounded_json_line(request)
        if self.proxy is not None:
            def alarm_handler(signum, frame):
                raise TimeoutError()
            previous = signal.signal(signal.SIGALRM, alarm_handler)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                result = self.proxy(request)
            except TimeoutError:
                raise
            except (RuntimeError, ValueError, OSError) as error:
                self.broker_usable = False
                raise BrokerTransportFailure(request.get('op', 'unknown')) from error
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
        else:
            if request['op'] == 'reset':
                self.close_channel()
                self.channel = ProcessChannel('candidate', self.entrypoint, self.entrypoint.parent)
            if self.channel is None:
                raise ProtocolError('reset_required')
            try:
                result = self.channel.exchange(request, timeout)
            except (TimeoutError, ProtocolError) as failure:
                try:
                    self.close_channel(failed=True)
                except Exception:
                    failure.add_note('secondary candidate cleanup failure')
                raise
        try:
            bounded_json_line(result)
        except (TypeError, ValueError, OverflowError, RecursionError):
            raise ProtocolError('invalid_json_response') from None
        return result

    def close_channel(self, failed=False):
        if self.channel is not None:
            channel, self.channel = self.channel, None
            channel.close(failed)

    def close(self):
        try:
            self.close_channel()
        finally:
            if self.directory is not None:
                self.directory.cleanup()


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        episode_start = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = 'reset'
        primary_failure = None

        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError()
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError()
            require_reset_ack(rpc({'op': 'reset', 'seed': episode['seed']}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError()
            outcomes[index] = value
            if not value['ok']:
                complete = False
                record_failure({'component': 'candidate', 'category': 'behavioral_control', 'operation': 'predict'})
        except BrokerTransportFailure as error:
            outcomes[index]['duration'] = max(0., clock() - episode_start)
            error.outcomes = outcomes
            record_failure(error.failure)
            raise
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            failure = (describe_episode_failure(error, current_operation) if isinstance(error, RequiredBaselineFailure)
                       else primary_failure or describe_episode_failure(error, current_operation))
            record_failure(failure)
        outcomes[index]['duration'] = max(0., clock() - episode_start)
    return outcomes, complete


def normalize_edges(edges):
    edges = np.sort(np.asarray(edges, dtype='<i4').reshape(-1, 2), axis=1)
    return np.unique(edges[edges[:, 0] != edges[:, 1]], axis=0).astype('<i4')


def matrix_for(edges, count):
    return sparse.csr_matrix((np.ones(2 * len(edges)),
                              (edges.T.ravel(), edges[:, ::-1].T.ravel())), shape=(count, count))


def potential_outcome(assignment, covariates, noise, edges, mechanism):
    graph = matrix_for(edges, len(assignment))
    degree = np.asarray(graph.sum(axis=1)).ravel()
    exposure = (graph @ assignment) / np.maximum(degree, 1)
    two_hop = (graph @ exposure) / np.maximum(degree, 1)
    spill = [np.zeros(len(assignment)), .25 * exposure, 2 * exposure,
             2 * (exposure >= .75) + assignment * exposure, 2 * two_hop, 2 * exposure][mechanism]
    return .5 * covariates[:, 0] + assignment + spill + noise


def encode_input(edges, covariates, assignment, observed):
    packed = (edges.astype('<i4').tobytes() + covariates.astype('<f8').tobytes()
              + assignment.astype('u1').tobytes() + observed.astype('<f8').tobytes())
    if len(packed) > 32 * 1024**2:
        raise ValueError('logical input limit')
    return packed


def input_layout(count, width, edge_count):
    return [{'name': 'edges', 'dtype': '<i4', 'shape': [edge_count, 2], 'offset_bytes': 0},
            {'name': 'covariates', 'dtype': '<f8', 'shape': [count, width], 'offset_bytes': 8 * edge_count},
            {'name': 'treatment', 'dtype': 'uint8', 'shape': [count], 'offset_bytes': 8 * edge_count + 8 * count * width},
            {'name': 'observed', 'dtype': '<f8', 'shape': [count], 'offset_bytes': 8 * edge_count + 8 * count * width + count}]


def prediction(response, count):
    if (type(response) is not dict or set(response) != {'encoding', 'dtype', 'shape', 'data'}
            or response['encoding'] != 'base64' or response['dtype'] != '<f8'
            or response['shape'] != [3, count] or type(response['shape']) is not list
            or any(type(value) is not int for value in response['shape']) or type(response['data']) is not str):
        raise ProtocolError('prediction_schema')
    try:
        packed = base64.b64decode(response['data'], validate=True)
    except (ValueError, TypeError):
        raise ProtocolError('prediction_encoding') from None
    if len(packed) != 24 * count or len(packed) > CHUNK:
        raise ProtocolError('prediction_shape')
    values = np.frombuffer(packed, '<f8').reshape(3, count).copy()
    if not np.isfinite(values).all() or np.max(np.abs(values)) > 1e100:
        raise ProtocolError('prediction_nonfinite')
    return values


def load_resources():
    root = Path(os.environ.get('TASK_SOURCE_DIR', Path(__file__).resolve().parent)) / 'resources' / PLANE
    manifest_bytes = (root / 'manifest.json').read_bytes()
    if hashlib.sha256(manifest_bytes).hexdigest() != MANIFEST_SHA256:
        raise ValueError('manifest integrity failure')
    manifest = json.loads(manifest_bytes)
    archive_path = root / 'benchmark.npz'
    if hashlib.sha256(archive_path.read_bytes()).hexdigest() != manifest['benchmark_sha256']:
        raise ValueError('benchmark integrity failure')
    audit = manifest['split_audit']
    if (audit['normalized_graph_intersections'] != 0 or audit['normalized_raw_example_intersections'] != 0
            or not audit['source_seed_sets_disjoint'] or not audit['checked_before_fitting']):
        raise ValueError('split integrity failure')
    if PLANE == 'final':
        archive = root / 'Stanford3.zip'
        if hashlib.sha256(archive.read_bytes()).hexdigest() != 'b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d':
            raise ValueError('public asset integrity failure')
        with zipfile.ZipFile(archive) as source:
            name = next(name for name in source.namelist() if name.endswith('.mtx'))
            lines = [line for line in source.read(name).decode('ascii').splitlines() if line and not line.startswith('%')]
            if lines[0].split() != ['11586', '11586', '568309'] or len(lines) != 568310:
                raise ValueError('public asset dimensions failure')
            public_edges = normalize_edges([[int(value) - 1 for value in line.split()[:2]] for line in lines[1:]])
    data = np.load(archive_path, allow_pickle=False)
    if PLANE == 'final' and not np.array_equal(data['Stanford3_edges'], public_edges):
        raise ValueError('public normalization failure')
    return manifest, data


def episode_plan(manifest, smoke):
    seeds = manifest['seeds'][:1] if smoke else manifest['seeds']
    families = [manifest['families'][-1] if PLANE == 'final' else 'SBM'] if smoke else manifest['families']
    mechanisms = [0, 2] if smoke else list(range(6))
    episodes = [{'kind': 'scientific', 'family': family, 'mechanism': mechanism, 'seed': seed}
                for family in families for mechanism in mechanisms for seed in seeds]
    control_family = families[0] if smoke else 'SBM'
    for kind in ('constant', 'permutation'):
        episodes.extend({'kind': kind, 'family': control_family, 'mechanism': 2, 'seed': seed} for seed in seeds)
    replay = dict(episodes[0])
    replay['kind'] = 'replay'
    episodes.append(replay)
    return episodes


def require_nonvacuous_permutation(permutation, edges, covariates):
    count = len(covariates)
    if (not np.array_equal(np.sort(permutation), np.arange(count))
            or np.array_equal(permutation, np.arange(count))):
        raise ProtocolError('vacuous_permutation')
    relabeled = normalize_edges(permutation[edges])
    if np.array_equal(relabeled, edges) and np.array_equal(covariates[permutation], covariates):
        raise ProtocolError('vacuous_permutation')
    return relabeled


def episode_data(episode, data, smoke):
    key = episode['family'] + '_' + str(episode['seed'])
    edge_key = 'Stanford3_edges' if episode['family'] == 'Stanford3' else key + '_edges'
    edges = data[edge_key]
    covariates = data[key + '_x']
    assignment = data[key + '_z' + str(episode['mechanism'])]
    noise = data[key + '_noise']
    observed = data[key + '_y' + str(episode['mechanism'])]
    if smoke:
        covariates, assignment, noise = covariates[:64], assignment[:64], noise[:64]
        edges = edges[np.max(edges, axis=1) < 64]
        observed = potential_outcome(assignment, covariates, noise, edges, episode['mechanism'])
    if episode['kind'] == 'constant':
        observed = np.full(len(covariates), 3.25)
    permutation = np.arange(len(covariates))[::-1]
    if episode['kind'] == 'permutation':
        relabeled = require_nonvacuous_permutation(permutation, edges, covariates)
        edges, covariates, assignment, observed = relabeled, covariates[permutation], assignment[permutation], observed[permutation]
    return edges, covariates, assignment, observed, noise, permutation


def worst_case(episode):
    return {'ok': False, 'control': 0., 'error': 10., 'squared': 100., 'utility': 0.,
            'duration': 0., 'solution': None}


def aggregate(episodes, outcomes):
    cases = {}
    controls = {'constant': [], 'permutation': [], 'replay': []}
    for episode, outcome in zip(episodes, outcomes):
        if episode['kind'] == 'scientific':
            cases.setdefault((episode['family'], episode['mechanism']), []).append(outcome)
        else:
            controls[episode['kind']].append(outcome['control'] if outcome['ok'] else 0.)
    utilities, rmses, biases = [], [], []
    for rows in cases.values():
        utilities.append(float(np.mean([row['utility'] for row in rows])))
        rmses.append(math.sqrt(float(np.mean([row['squared'] for row in rows]))))
        biases.append(abs(float(np.mean([row['error'] for row in rows]))) if all(row['ok'] for row in rows) else 10.)
    constant, permutation, replay = (float(np.mean(controls[name])) for name in ('constant', 'permutation', 'replay'))
    metrics = dict(zip(METRICS, [.8 * float(np.mean(utilities)) + .1 * constant + .05 * permutation + .05 * replay,
                               float(np.mean(rmses)), float(np.mean(biases)),
                               float(np.mean([not row['ok'] for row in outcomes])),
                               .5 * constant + .25 * permutation + .25 * replay]))
    if not all(math.isfinite(value) for value in metrics.values()):
        raise ValueError('nonfinite aggregation')
    correct = all(row['ok'] for row in outcomes) and constant == permutation == replay == 1.
    return metrics, correct


def evidence(episodes, outcomes):
    records = []
    replay_result = next(row['control'] for episode, row in zip(episodes, outcomes) if episode['kind'] == 'replay')
    for seed in dict.fromkeys(episode['seed'] for episode in episodes):
        selected = [(episode, row) for episode, row in zip(episodes, outcomes) if episode['seed'] == seed]
        scientific = [row['utility'] for episode, row in selected if episode['kind'] == 'scientific']
        constant = next(row['control'] for episode, row in selected if episode['kind'] == 'constant')
        permuted = next(row['control'] for episode, row in selected if episode['kind'] == 'permutation')
        score = .8 * float(np.mean(scientific)) + .1 * constant + .05 * permuted + .05 * replay_result
        records.append({'seed': int(seed), 'score': score, 'correct': all(row['ok'] and (episode['kind'] == 'scientific' or row['control'] == 1.) for episode, row in selected),
                        'duration_seconds': sum(row['duration'] for episode, row in selected),
                        'solution': {'cases': [{'family': episode['family'], 'mechanism': episode['mechanism'],
                                               'kind': episode['kind'], 'completed': row['ok'],
                                               'validated': row['solution']} for episode, row in selected]}})
    return {'schema_version': 1, 'episodes': records}


def record_failure(failure):
    try:
        message = ('episode_failure component=' + bounded_failure_name(failure.get('component'), 'candidate')
                   + ' category=' + bounded_failure_name(failure.get('category'), 'unknown')
                   + ' operation=' + bounded_failure_name(failure.get('operation'), 'unknown'))
        for name in ('exit_status', 'observed_exit_status', 'signal', 'observed_bytes', 'retained_bytes'):
            value = failure.get(name)
            if type(value) is int and -(2**63) <= value < 2**63:
                message += ' ' + name + '=' + str(value)
        if 'truncated' in failure:
            message += ' truncated=' + str(int(failure['truncated'] is True))
        if 'capture_error' in failure:
            category = failure['capture_error']
            if category is None:
                category = 'none'
            if category not in ('none', 'reader_stopped_before_eof', 'stderr_capture_failed'):
                category = 'invalid_capture_diagnostic'
            message += ' capture_error=' + category
        print(message, file=sys.stderr, flush=True)
    except Exception:
        pass


def run(program_path, smoke):
    require_joint_workload_budget()
    manifest, data = load_resources()
    episodes = episode_plan(manifest, smoke)
    for profile, key in ((False, 'reset_sequence'), (True, 'smoke_reset_sequence')):
        expected = manifest['plan'][key]
        actual = [episode['seed'] for episode in episode_plan(manifest, profile)]
        if (any(type(seed) is not int for seed in expected) or expected != actual):
            raise ValueError('complete reset transcript mismatch')
    hard_deadline = min(START + WALL - STARTUP, START + 115) if smoke else START + WALL - STARTUP
    if len(episodes) != (5 if smoke else (161 if PLANE == 'search' else 625)):
        raise ValueError('episode plan mismatch')
    maximum_calls = (161 if PLANE == 'search' else 625) * (1 + MAX_CHUNKS + 1 + 1)
    candidate = Candidate(program_path, maximum_calls)
    baseline_directory = tempfile.TemporaryDirectory(prefix='gate-baseline-')
    baseline = ProcessChannel('baseline', '-', baseline_directory.name)
    reference = {}
    baseline_failed = False

    def episode_rpc(request, timeout):
        nonlocal baseline_failed
        try:
            return candidate.rpc(request, timeout)
        except (TimeoutError, ProtocolError):
            category = baseline.check()
            if category is not None:
                baseline_failed = category
                raise RequiredBaselineFailure(category) from None
            raise

    def evaluate_episode(episode, call, episode_deadline):
        nonlocal baseline_failed
        if baseline_failed:
            raise RequiredBaselineFailure(baseline_failed)
        edges, covariates, assignment, observed, noise, permutation = episode_data(episode, data, smoke)
        packed = encode_input(edges, covariates, assignment, observed)
        baseline_estimates = {}
        baseline_request = {'n': len(covariates), 'p': covariates.shape[1], 'm': len(edges),
                            'data': base64.b64encode(packed).decode('ascii')}
        for method_index, method in enumerate(BASELINES):
            method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_deadline,
                                                       methods_remaining=5 - method_index, work_seconds=WORK,
                                                       cleanup_seconds=.01)
            baseline_request['method'] = method
            try:
                value = baseline.exchange(baseline_request, method_deadline - time.monotonic())
                if (type(value) is not dict or set(value) != {'estimate'} or type(value['estimate']) not in (int, float)
                        or not math.isfinite(value['estimate'])):
                    raise RequiredBaselineFailure('baseline_result_failure')
                baseline_estimates[method] = value['estimate']
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                category = (error.category if isinstance(error, RequiredBaselineFailure) else
                            'baseline_timeout' if isinstance(error, TimeoutError) else 'baseline_result_failure')
                baseline_failed = category
                failure = RequiredBaselineFailure(category)
                try:
                    baseline.close(failed=True)
                except Exception:
                    failure.add_note('secondary baseline cleanup failure')
                raise failure from None
        method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_deadline,
                                                   methods_remaining=0, work_seconds=WORK, cleanup_seconds=.01)

        def candidate_call(request):
            nonlocal baseline_failed
            category = baseline.check()
            if category is not None:
                baseline_failed = category
                raise RequiredBaselineFailure(category)
            remaining = method_deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError()
            candidate.method_deadline = method_deadline
            previous = signal.signal(signal.SIGALRM, lambda signum, frame: (_ for _ in ()).throw(TimeoutError()))
            signal.setitimer(signal.ITIMER_REAL, remaining)
            try:
                response = call(request)
            except (TimeoutError, ProtocolError):
                category = baseline.check()
                if category is not None:
                    baseline_failed = category
                    raise RequiredBaselineFailure(category) from None
                raise
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
            category = baseline.check()
            if category is not None:
                baseline_failed = category
                raise RequiredBaselineFailure(category)
            return response

        total = math.ceil(len(packed) / CHUNK)
        if not 1 <= total <= MAX_CHUNKS:
            raise ValueError('chunk plan invalid')
        for index in range(total):
            response = candidate_call({'op': 'ingest', 'index': index, 'total': total, 'n': len(covariates),
                                       'p': covariates.shape[1], 'm': len(edges), 'dtype': 'packed-le', 'encoding': 'base64',
                                       'layout': input_layout(len(covariates), covariates.shape[1], len(edges)),
                                       'data': base64.b64encode(packed[index * CHUNK:(index + 1) * CHUNK]).decode('ascii')})
            if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
                raise ProtocolError('ingest_ack')
        response = candidate_call({'op': 'fit'})
        if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
            raise ProtocolError('fit_ack')
        values = prediction(candidate_call({'op': 'predict'}), len(covariates))
        if time.monotonic() > method_deadline:
            raise TimeoutError()
        contrast = float(np.mean(values[1] - values[2]))
        key = (episode['family'], episode['mechanism'], episode['seed'])
        control_success = 1.
        if episode['kind'] == 'scientific':
            truth = float(np.mean(potential_outcome(np.ones(len(covariates)), covariates, noise, edges, episode['mechanism'])
                                  - potential_outcome(np.zeros(len(covariates)), covariates, noise, edges, episode['mechanism'])))
            uncapped_error = contrast - truth
            reference[key] = values
        elif episode['kind'] == 'constant':
            truth, uncapped_error = 0., contrast
            control_success = float(abs(contrast) <= 1e-6)
        else:
            expected = reference.get(key)
            aligned = values[:, permutation] if episode['kind'] == 'permutation' else values
            control_success = float(expected is not None and np.allclose(aligned, expected, atol=1e-6, rtol=1e-6))
            truth, uncapped_error = None, 0.
        clipped = float(np.clip(uncapped_error, -10., 10.))
        solution = {'contrast': contrast, 'true_gate': truth, 'uncapped_error': uncapped_error,
                    'clipped': abs(uncapped_error) > 10., 'baseline_estimates': baseline_estimates,
                    'observed_fit_rmse': float(np.sqrt(np.mean((values[0] - observed)**2))),
                    'prediction_sha256': hashlib.sha256(values.astype('<f8').tobytes()).hexdigest(),
                    'control_success': bool(control_success)}
        graph = matrix_for(edges, len(covariates))
        degree = np.asarray(graph.sum(axis=1)).ravel()
        exposure = (graph @ assignment) / np.maximum(degree, 1)
        condition = float(np.linalg.cond(np.column_stack((np.ones(len(covariates)), covariates, assignment, exposure))))
        solution['exposure_support'] = {'minimum': float(exposure.min()), 'maximum': float(exposure.max()),
                                        'fraction_zero': float(np.mean(exposure == 0)),
                                        'fraction_one': float(np.mean(exposure == 1)),
                                        'linear_design_condition': condition if math.isfinite(condition) else None}
        return {'ok': bool(control_success), 'control': control_success, 'error': clipped, 'squared': clipped**2,
                'utility': 1. - clipped**2 / 100., 'duration': 0., 'solution': solution}

    try:
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline,
                              finish_reserve=FINISH, reset_timeout=RESET_TIMEOUT, episode_overhead=OVERHEAD,
                              rpc_cap=WORK + RESET_TIMEOUT, clock=time.monotonic, rpc=episode_rpc,
                              evaluate=evaluate_episode, worst_case=worst_case, record_failure=record_failure)
        category = baseline.check()
        if category is not None and not baseline_failed:
            baseline_failed = category
            complete = False
            duration = outcomes[-1]['duration']
            was_complete = outcomes[-1]['ok']
            outcomes[-1] = worst_case(episodes[-1])
            outcomes[-1]['duration'] = duration
            if was_complete:
                record_failure({'component': 'baseline', 'category': category, 'operation': 'baseline_worker'})
        metrics, correct = aggregate(episodes, outcomes)
        feasible = complete and not baseline_failed and time.monotonic() < hard_deadline and not smoke
        return metrics, bool(correct and complete), feasible, evidence(episodes, outcomes)
    except BrokerTransportFailure as failure:
        failure.metrics, _ = aggregate(episodes, failure.outcomes)
        failure.observations = evidence(episodes, failure.outcomes)
        raise
    finally:
        primary = sys.exception()
        cleanup_failure = None
        for component, cleanup in (
                ('candidate', candidate.close),
                ('baseline', lambda: baseline.close(failed=baseline_failed)),
                ('evaluator', baseline_directory.cleanup), ('evaluator', data.close)):
            try:
                cleanup()
            except Exception as failure:
                record_failure({'component': component, 'category': 'cleanup_failure', 'operation': 'cleanup'})
                if primary is not None:
                    primary.add_note('secondary cleanup failure')
                elif cleanup_failure is None:
                    cleanup_failure = failure
        if primary is None and cleanup_failure is not None:
            raise cleanup_failure


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    args = parser.parse_args()
    output = Path(args.results_dir)
    output.mkdir(parents=True, exist_ok=True)
    metrics = dict(zip(METRICS, [0., 10., 10., 1., 0.]))
    correct, feasible, observations, error = False, False, None, None
    try:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_AS, (8 * 1024**3, 8 * 1024**3))
        resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(WALL * 2), math.ceil(WALL * 2)))
        cpus = sorted(os.sched_getaffinity(0))[:2]
        os.sched_setaffinity(0, cpus)
        smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
        metrics, correct, feasible, observations = run(args.program_path, smoke)
    except Exception as failure:
        error = failure
        if isinstance(failure, BrokerTransportFailure):
            metrics = getattr(failure, 'metrics', metrics)
            observations = getattr(failure, 'observations', None)
        if PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                                  or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'):
            report_worker_exception(failure)
        else:
            print('EvaluationFailure: sealed evaluator failed', file=sys.stderr)
    (output / 'metrics.json').write_bytes(bounded_json_line(metrics))
    (output / 'correct.json').write_bytes(bounded_json_line({'correct': bool(correct)}))
    if observations is not None:
        encoded = bounded_json_line(observations)
        if len(encoded) > 16 * 1024**2:
            raise ValueError('evidence size limit')
        (output / 'evaluation_evidence.json').write_bytes(encoded)
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (output / 'qualification.json').write_bytes(bounded_json_line({'schema_version': 1, 'feasible': bool(feasible)}))
    return 1 if error is not None else 0


if __name__ == '__main__':
    sys.exit(main())
