"""Search-only, offline, evaluator-owned benchmark prediction experiment.

The sealed evaluator is a standalone copy, not an import of this module.
All controls, losses, fixed weights and budgets are specified before execution.
"""

import argparse
import base64
import collections
import ctypes
import errno
import hashlib
import importlib.util
import inspect
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

PLANE = 'search'
CASES = ['arc_challenge', 'ifeval', 'commonsense', 'gsm']
SEEDS = [101, 211]
WALL_SECONDS = 2700
STARTUP_SECONDS = 180
RPC_BUDGET = 700
METHOD_SECONDS = 20
RESOURCE_HASHES = {'commonsense.npz': '61ebe7ef736a79e09f611f8c98f7d1dac1896c046b113835a9c72ed307ae5165', 'ifeval_manifest.json': 'cce4b7a3aafa0e35ce67d1ba7991fa0aa6f330aad69616354987b6454d531fa9', 'commonsense_columns.jsonl': '6706b3742314a48d7735b2c817ac9b3e35b216bc2e427aaeb0876b8d534425b5', 'gsm_columns.jsonl': '92d0ed300cc45f09543524414d9dbe11916342e6c3bb2a6e7003bbdf378e659a', 'commonsense_manifest.json': '62eb4687b1e34702507acf3b9c4ba13be01475516925534a24752b22a37b9a5b', 'gsm_manifest.json': '8c158e58dea6893d6a1b289a07d194ae7ee4aa75c71d20fe8b4257ee91c6d508', 'ifeval_columns.jsonl': 'a1b4b2c26220ecfaa7c5c694b9dd6316622260990242b298736242b0ab2f8eaa', 'ifeval.npz': 'b5fd28eb3083a3af6a3dc5f16e1d180caa60c51e2c5bbd2944f2f3da9511dd19', 'gsm.npz': '8307c84e3ce1a7d39dc0fdd916fa0125c7107b0a4efd92501b24adaab49e422b', 'arc_challenge_manifest.json': '712236caa769ac9dee69e613f0eea0a696e41361e0a99ccae72903d71a5e9684', 'arc_challenge_columns.jsonl': '8b0cb07f0495cd4b112a7cf0a8db0897392fd0e6c9c10b25315f32ab9c27710c', 'arc_challenge.npz': '15387364d2f93105678a1bceb0b09da3769b829f0e5e61a769fa2bed269b83f1'}
METRICS = ['mae', 'rmse', 'spearman', 'kendall', 'uniform_mae', 'prior_mae',
           'anchor_mae', 'irt_mae', 'constant_mae', 'permuted_mae', 'control_correct', 'correct']
CONDITIONS = ['normal', 'constant', 'permuted']
WIRE_LIMIT = 64 * 1024 * 1024
OPERATING_LIMIT = 16 * 1024 * 1024
CHUNK_BYTES = 3 * 1024 * 1024
MAX_CHUNKS = 11
FINISH_RESERVE = 10
EPISODE_OVERHEAD = 7
RESET_TIMEOUT = 2


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ProtocolFailure('duplicate_key')
            result[key] = value
        return result
    def constant(value):
        raise ProtocolFailure('nonfinite_response')
    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise ProtocolFailure('invalid_json') from error


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
        envelope = json.dumps({'request': value}, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError) as error:
        raise ProtocolFailure('invalid_json_value') from error
    if max(len(encoded), len(envelope)) + 4096 >= min(wire_limit, OPERATING_LIMIT):
        raise ProtocolFailure('message_too_large')
    return encoded


class ProtocolFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'invalid_protocol')
        super().__init__('candidate protocol failure')


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
        if isinstance(context, ProtocolFailure):
            return {'component': 'candidate', 'category': context.category,
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


def record_failure(failure):
    if PLANE == 'search':
        line = 'episode_failure component={component} category={category} operation={operation}'.format(
            **{key: bounded_failure_name(failure.get(key), 'unknown')
               for key in ('component', 'category', 'operation')})
        if type(failure.get('exit_status')) is int:
            line += ' exit_status=' + str(max(-255, min(255, failure['exit_status'])))
        print(line[:256], file=sys.stderr, flush=True)


def repair_mode():
    return PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'
                                 or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')


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
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[name] = '4'
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


def isolate_native(allowed_directory):
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(38, 1, 0, 0, 0) != 0:
        raise OSError('no_new_privs unavailable')
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 1:
        raise OSError('Landlock unavailable; refusing unisolated candidate')
    handled = (1 << 13) - 1
    if abi >= 2:
        handled |= 1 << 13
    if abi >= 3:
        handled |= 1 << 14
    ruleset = ctypes.c_uint64(handled)
    descriptor = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
    if descriptor < 0:
        raise OSError('Landlock ruleset failed')
    class PathRule(ctypes.Structure):
        _pack_ = 1
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]
    readable = (1 << 0) | (1 << 2) | (1 << 3)
    paths = {str(Path(sys.base_prefix).resolve()), str(Path(sys.prefix).resolve()),
             '/usr', '/lib', '/lib64', '/etc/ld.so.cache', '/etc/localtime', '/dev/null', '/dev/urandom',
             str(Path(allowed_directory).resolve())}
    for name in paths:
        if not os.path.exists(name):
            continue
        access = handled if name == str(Path(allowed_directory).resolve()) else readable
        if not os.path.isdir(name):
            access &= ~((1 << 3) | (1 << 0))
        path_fd = os.open(name, os.O_PATH | os.O_CLOEXEC)
        rule = PathRule(access, path_fd)
        result = libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0)
        os.close(path_fd)
        if result != 0:
            os.close(descriptor)
            raise OSError('Landlock path rule failed')
    if libc.syscall(446, descriptor, 0) != 0:
        raise OSError('Landlock restriction failed')
    os.close(descriptor)
    seccomp = ctypes.CDLL('libseccomp.so.2')
    seccomp.seccomp_init.argtypes = [ctypes.c_uint32]
    seccomp.seccomp_init.restype = ctypes.c_void_p
    seccomp.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    seccomp.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    seccomp.seccomp_load.argtypes = [ctypes.c_void_p]
    seccomp.seccomp_release.argtypes = [ctypes.c_void_p]
    context = seccomp.seccomp_init(0x7fff0000)
    if not context:
        raise OSError('seccomp initialization failed')
    for name in ('socket', 'socketpair', 'connect', 'bind', 'listen', 'accept', 'accept4',
                 'ptrace', 'process_vm_readv', 'process_vm_writev', 'pidfd_getfd',
                 'mount', 'umount2', 'unshare', 'setns', 'bpf', 'io_uring_setup',
                 'kill', 'tkill', 'tgkill', 'pidfd_send_signal', 'rt_sigqueueinfo', 'rt_tgsigqueueinfo',
                 'prlimit64', 'sched_setaffinity', 'sched_setscheduler', 'sched_setparam',
                 'setpriority', 'setpgid', 'setsid', 'open_by_handle_at', 'keyctl', 'add_key', 'request_key'):
        number = seccomp.seccomp_syscall_resolve_name(name.encode())
        if number >= 0 and seccomp.seccomp_rule_add(context, 0x50000 | errno.EPERM, number, 0) != 0:
            raise OSError('seccomp rule failed')
    if seccomp.seccomp_load(context) != 0:
        raise OSError('seccomp restriction failed')
    seccomp.seccomp_release(context)


class Worker:
    def __init__(self, arguments, environment, *, cwd=None):
        self.process = subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, cwd=cwd, env=environment,
                                        shell=False, start_new_session=True, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.pending = bytearray()
        self.closed = False

    def exchange(self, request, *, timeout, poll=None):
        outgoing = memoryview(bounded_json_line(request))
        stop_at = time.monotonic() + timeout
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while True:
                if poll:
                    poll()
                remaining = stop_at - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError('worker response deadline')
                for key, mask in selector.select(min(.05, remaining)):
                    if key.fileobj is self.process.stdin:
                        try:
                            count = os.write(self.process.stdin.fileno(), outgoing[:65536])
                        except BrokenPipeError as error:
                            raise ProtocolFailure('worker_exit') from error
                        outgoing = outgoing[count:]
                        if not outgoing:
                            selector.unregister(self.process.stdin)
                    else:
                        chunk = os.read(self.process.stdout.fileno(), 65536)
                        if not chunk:
                            raise ProtocolFailure('worker_exit')
                        self.pending.extend(chunk)
                        if len(self.pending) >= OPERATING_LIMIT:
                            raise ProtocolFailure('message_too_large')
                        if b'\n' in self.pending:
                            line, extra = self.pending.split(b'\n', 1)
                            if extra or outgoing:
                                raise ProtocolFailure('unsolicited_response')
                            self.pending.clear()
                            value = strict_json(line)
                            bounded_json_line(value)
                            return value

    def close(self, failed=False):
        if self.closed:
            return
        self.closed = True
        process = self.process
        try:
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
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
        finally:
            process.stdin.close()
            process.stdout.close()
            snapshot = self.capture.close()
            if failed and repair_mode():
                if snapshot['stderr']:
                    print(snapshot['stderr'], file=sys.stderr, end='', flush=True)
                print('worker_capture observed_bytes={} retained_bytes={} truncated={} capture_error={}'.format(
                    snapshot['observed_bytes'], snapshot['retained_bytes'], int(snapshot['truncated']),
                    snapshot['capture_error'] or 'none'), file=sys.stderr, flush=True)


class Candidate:
    def __init__(self, program_path, smoke):
        path = str(Path(program_path).absolute())
        socket = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        self.proxy = None
        self.worker = None
        self.directory = None
        self.calls = 0
        if socket or path == '/broker-code/candidate_proxy.py':
            if not socket or path != '/broker-code/candidate_proxy.py':
                raise RuntimeError('broker requires both trusted proxy path and socket')
            specification = importlib.util.spec_from_file_location('trusted_candidate_proxy', path)
            module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.directory = tempfile.TemporaryDirectory(prefix='t07-native-')
            source = Path(path)
            shutil.copytree(source.parent, Path(self.directory.name) / 'code', symlinks=False)
            self.program = str(Path(self.directory.name) / 'code' / source.name)
            self.interpreter, self.environment = candidate_subprocess_settings(os.environ)
            self.runner_source = native_runner_source()
        self.smoke = smoke

    def call(self, request, *, timeout, poll=None):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolFailure('rpc_budget')
        bounded_json_line(request)
        if self.proxy:
            def alarm_handler(signum, frame):
                raise TimeoutError('proxy deadline')
            old_handler = signal.signal(signal.SIGALRM, alarm_handler)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                if poll:
                    poll()
                response = self.proxy(request)
                if poll:
                    poll()
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, old_handler)
            bounded_json_line(response)
            return strict_json(bounded_json_line(response))
        if request['op'] == 'reset':
            self.cleanup()
            self.worker = Worker([self.interpreter, '-I', '-c', self.runner_source,
                                  self.program, str(110 if self.smoke else WALL_SECONDS),
                                  '1' if repair_mode() else '0'], self.environment,
                                 cwd=self.directory.name)
        if self.worker is None:
            raise ProtocolFailure('worker_unavailable')
        try:
            return self.worker.exchange(request, timeout=timeout, poll=poll)
        except (TimeoutError, ProtocolFailure, RequiredBaselineFailure):
            self.cleanup(failed=True)
            raise

    def cleanup(self, failed=False):
        worker, self.worker = self.worker, None
        if worker:
            worker.close(failed=failed)

    def close(self):
        self.cleanup()
        if self.directory:
            self.directory.cleanup()


def native_entry(program, wall, repair):
    resource.setrlimit(resource.RLIMIT_AS, (16 * 1024**3, 16 * 1024**3))
    cpu_seconds = math.ceil(wall * 4)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
    resource.setrlimit(resource.RLIMIT_FSIZE, (16 * 1024**2, 16 * 1024**2))
    resource.setrlimit(resource.RLIMIT_NOFILE, (128, 128))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    directory = str(Path(program).resolve().parent)
    os.environ['TMPDIR'] = directory
    isolate_native(directory)
    specification = importlib.util.spec_from_file_location('candidate', program)
    module = importlib.util.module_from_spec(specification)
    sys.path.insert(0, directory)
    try:
        specification.loader.exec_module(module)
        while True:
            line = sys.stdin.buffer.readline(OPERATING_LIMIT)
            if not line:
                break
            if not line.endswith(b'\n'):
                raise ProtocolFailure('message_too_large')
            response = module.handle(strict_json(line))
            sys.stdout.buffer.write(bounded_json_line(response))
            sys.stdout.buffer.flush()
    except Exception as error:
        if repair:
            report_worker_exception(error)
        else:
            print('candidate_worker_failure', file=sys.stderr, flush=True)
        raise SystemExit(1)


def native_runner_source():
    imports = 'import base64, ctypes, errno, importlib.util, json, math, os, resource, sys\nfrom pathlib import Path\n'
    constants = 'WIRE_LIMIT=67108864\nOPERATING_LIMIT=16777216\n'
    functions = (bounded_failure_name, ProtocolFailure, strict_json, bounded_json_line,
                 report_worker_exception, isolate_native, native_entry)
    entry = '\ntry:\n    native_entry(sys.argv[1], int(sys.argv[2]), sys.argv[3] == "1")\nexcept Exception as error:\n    if sys.argv[3] == "1":\n        report_worker_exception(error)\n    else:\n        print("candidate_worker_failure", file=sys.stderr, flush=True)\n    raise SystemExit(1)\n'
    return imports + constants + '\n\n'.join(inspect.getsource(function) for function in functions) + entry


def ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise ProtocolFailure('invalid_ack')


def fixed_weight_score(values, weights, worst_case):
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(weight) or weight < 0 for weight in weights)
            or not math.isclose(sum(weights), 1, rel_tol=0, abs_tol=1e-12)):
        raise ValueError('invalid predeclared aggregation weights')
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError('nonfinite contribution')
    return sum(value * weight for value, weight in zip(retained, weights))


def weights_for(groups):
    import numpy as np
    unique, inverse, counts = np.unique(groups, return_inverse=True, return_counts=True)
    return 1 / (len(unique) * counts[inverse])


def checkpoint_metrics(predictions, truth, groups):
    import numpy as np
    from scipy.stats import kendalltau, spearmanr
    weights = weights_for(groups)
    difference = np.asarray(predictions) - truth
    group_predictions = [float(np.mean(np.asarray(predictions)[groups == group])) for group in np.unique(groups)]
    group_truth = [float(np.mean(truth[groups == group])) for group in np.unique(groups)]
    if len(set(group_predictions)) < 2 or len(set(group_truth)) < 2:
        spearman, kendall = -1., -1.
    else:
        spearman = float(spearmanr(group_predictions, group_truth).statistic)
        kendall = float(kendalltau(group_predictions, group_truth).statistic)
        spearman = spearman if math.isfinite(spearman) else -1.
        kendall = kendall if math.isfinite(kendall) else -1.
    return dict(mae=float(weights @ np.abs(difference)), rmse=float(np.sqrt(weights @ difference**2)),
                spearman=spearman, kendall=kendall)


def anchor_order(source, groups, weights, budget):
    import numpy as np
    representatives = np.unique(groups, return_index=True)[1]
    centered = source.T.astype(float) - (weights @ source)[:, None]
    embedded = centered * np.sqrt(weights)
    lengths = np.linalg.norm(embedded, axis=1)
    embedded /= np.maximum(lengths[:, None], 1e-12)
    first = int(representatives[np.argmin(np.sum((embedded[representatives] - embedded.mean(axis=0))**2, axis=1))])
    chosen = [first]
    nearest = np.sum((embedded - embedded[first])**2, axis=1)
    for _ in range(1, budget):
        available = np.array([index for index in representatives if groups[index] not in {groups[item] for item in chosen}])
        selected = int(available[np.argmax(nearest[available])])
        chosen.append(selected)
        nearest = np.minimum(nearest, np.sum((embedded - embedded[selected])**2, axis=1))
    return chosen, embedded


def baseline_compute(request):
    import numpy as np
    from scipy.special import expit
    from threadpoolctl import threadpool_limits
    threadpool_limits(4)
    source = np.asarray(request['source'], dtype=np.uint8)
    target = np.asarray(request['target'], dtype=np.uint8)
    groups = np.asarray(request['item_groups'])
    source_weights = np.asarray(request['source_weights'])
    target_groups = np.asarray(request['target_groups'])
    truth = target.mean(axis=1)
    budgets = request['budgets']
    work = request['work_seconds']
    rng = np.random.default_rng(request['seed'])
    start = time.monotonic()
    stop_at = start + 4 * work + 1
    output = {}
    stored_predictions = {}
    times = {}
    representatives = np.unique(groups, return_index=True)[1]
    group_mass = np.bincount(groups) / source.shape[1]
    uniform = rng.permutation(representatives)[:max(budgets)]
    for method_index, name in enumerate(('uniform', 'prior', 'anchor', 'irt')):
        begin = time.monotonic()
        deadline = reserved_method_deadline(now=begin, episode_deadline=stop_at,
                                            methods_remaining=3-method_index,
                                            work_seconds=work, cleanup_seconds=0)
        def baseline_alarm(signum, frame):
            raise TimeoutError('baseline method deadline')
        signal.signal(signal.SIGALRM, baseline_alarm)
        signal.setitimer(signal.ITIMER_REAL, max(.001, deadline-time.monotonic()))
        def check():
            if time.monotonic() >= deadline:
                raise TimeoutError('baseline work deadline')
        predictions = []
        prediction_values = []
        if name == 'anchor':
            selected, embedding = anchor_order(source, groups, source_weights, max(budgets))
        elif name == 'irt':
            scores = np.clip(source_weights @ source, .005, .995)
            difficulty = -np.log(scores / (1-scores))
            ability = np.zeros(source.shape[0])
            for _ in range(200):
                check()
                probability = expit(ability[:, None] - difficulty)
                curvature = probability * (1-probability)
                ability += np.clip(((source-probability).sum(axis=1)-ability)
                                   / (curvature.sum(axis=1)+1), -1, 1)
                probability = expit(ability[:, None] - difficulty)
                curvature = probability * (1-probability)
                difficulty += np.clip(((source_weights[:, None] * (probability-source)).sum(axis=0) - .01*difficulty)
                                      / ((source_weights[:, None]*curvature).sum(axis=0)+.01), -1, 1)
                shift = float(source_weights @ ability)
                ability -= shift
                difficulty -= shift
        for budget in budgets:
            check()
            if name == 'prior':
                estimate = np.full(len(target), float(source_weights @ source.mean(axis=1)))
            elif name == 'uniform':
                items = uniform[:budget]
                estimate = np.clip((target[:, items] * group_mass[groups[items]]).sum(axis=1) * len(representatives)/budget, 0, 1)
            elif name == 'anchor':
                items = selected[:budget]
                assignments = np.argmax(embedding @ embedding[items].T, axis=1)
                cluster_weights = np.bincount(assignments, minlength=budget) / source.shape[1]
                estimate = target[:, items] @ cluster_weights
            else:
                items = uniform[:budget]
                target_ability = np.zeros(len(target))
                for _ in range(40):
                    check()
                    probability = expit(target_ability[:, None] - difficulty[items])
                    target_ability += np.clip(((target[:, items]-probability).sum(axis=1)-target_ability)
                                             / ((probability*(1-probability)).sum(axis=1)+1), -1, 1)
                estimate = expit(target_ability[:, None] - difficulty).mean(axis=1)
            predictions.append(checkpoint_metrics(estimate, truth, target_groups)['mae'])
            prediction_values.append(estimate.tolist())
        check()
        output[name + '_mae'] = predictions
        stored_predictions[name + '_mae'] = prediction_values
        times[name] = time.monotonic() - begin
        signal.setitimer(signal.ITIMER_REAL, 0)
    return {'metrics': output, 'predictions': stored_predictions, 'productive_seconds': times}


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
    if now + (methods_remaining+1) * (work+cleanup_seconds) > episode_deadline + 1e-6:
        raise TimeoutError('insufficient matched method reservations')
    return now + work


def baseline_entry(repair):
    resource.setrlimit(resource.RLIMIT_AS, (12 * 1024**3, 12 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (WALL_SECONDS * 4, WALL_SECONDS * 4))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    try:
        request = strict_json(sys.stdin.buffer.readline(OPERATING_LIMIT))
        result = baseline_compute(request)
        sys.stdout.buffer.write(bounded_json_line(result))
        sys.stdout.buffer.flush()
    except Exception as error:
        signal.setitimer(signal.ITIMER_REAL, 0)
        if repair:
            report_worker_exception(error)
        else:
            print('baseline_worker_failure', file=sys.stderr, flush=True)
        raise SystemExit(124 if isinstance(error, TimeoutError) else 1)


def load_case(root, case, smoke):
    import numpy as np
    for suffix in ('.npz', '_manifest.json', '_columns.jsonl'):
        name = case + suffix
        path = root / name
        if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest() != RESOURCE_HASHES[name]:
            raise ValueError('resource integrity failure')
    manifest = json.loads((root / (case + '_manifest.json')).read_text())
    with np.load(root / (case + '.npz'), allow_pickle=False) as payload:
        data = {name: payload[name].copy() for name in payload.files}
    source, target = data['source'], data['target']
    if (source.ndim != 2 or target.ndim != 2 or source.shape[1] != target.shape[1]
            or not 1 <= source.shape[0] <= 512 or not 1 <= target.shape[0] <= 512
            or not 250 <= source.shape[1] <= 65536
            or not np.isin(source, [0, 1]).all() or not np.isin(target, [0, 1]).all()
            or len(np.unique(data['source_groups'])) < 8 or len(np.unique(data['target_groups'])) < 5
            or set(data['source_groups']) & set(data['target_groups'])
            or len(np.unique(data['item_groups'])) < 25):
        raise ValueError('invalid frozen case')
    if len(manifest['source_rows']) != len(source) or len(manifest['target_rows']) != len(target):
        raise ValueError('row provenance mismatch')
    if smoke:
        data['source'] = source[:12, :80]
        data['target'] = target[:8, :80]
        data['source_groups'] = data['source_groups'][:12]
        data['target_groups'] = data['target_groups'][:8]
        data['item_groups'] = np.unique(data['item_groups'][:80], return_inverse=True)[1]
    data['source_weights'] = weights_for(data['source_groups'])
    return data


def preflight_messages():
    largest_request = {'op': 'upload_chunk', 'index': 10, 'offset': 10*CHUNK_BYTES,
                       'data': base64.b64encode(b'\xff' * CHUNK_BYTES).decode()}
    sizes = [len(bounded_json_line(largest_request))]
    sizes.append(len(bounded_json_line(dict(op='upload_start', shape=[512, 65536], dtype='uint8',
        encoding='base64', byte_order='na', total_bytes=33554432, chunks=11,
        item_groups=list(range(65536)), source_groups=list(range(512)),
        source_weights=[1/65537]*511+[1-511/65537], target_count=513, max_budget=25))))
    sizes.append(len(bounded_json_line({'op': 'observe', 'items': list(range(25)), 'values': [[1]*25]*513})))
    responses = [{'ok': True}, {'items': list(range(65511, 65536))}, {'predictions': [2.2250738585072014e-308]*513}]
    response_size = max(len(bounded_json_line(response)) for response in responses)
    trace = collections.Counter()
    for operation, count in [('reset', 1), ('upload_start', 1), ('upload_chunk', MAX_CHUNKS),
                             ('upload_commit', 1), ('fit', 1), ('select', 3), ('observe', 3),
                             ('update', 3), ('predict', 3), ('close', 1)]:
        for _ in range(count):
            trace[operation] += 1
    if sum(trace.values()) != 28:
        raise ValueError('invalid RPC preflight')
    return dict(request_bytes=max(sizes), response_bytes=response_size, extra_envelope_framing_bytes=4096,
                operation_counts=dict(trace), calls_per_episode=sum(trace.values()))


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes)*reset_slot > candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        episode_started = clock()
        remaining = len(episodes)-index-1
        episode_deadline = candidate_deadline - remaining*reset_slot
        work_deadline = episode_deadline - episode_overhead
        current_operation = 'reset'
        primary_failure = None
        def call(request, timeout_override=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get('op', 'unknown')
            try:
                timeout = min(rpc_cap, work_deadline-clock())
                if timeout_override is not None:
                    timeout = min(timeout, timeout_override)
                if timeout <= 0:
                    raise TimeoutError('episode work budget exhausted')
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline-clock())
            if timeout <= 0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc({'op': 'reset', 'seed': episode['seed']}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            complete = False
            outcomes[index]['duration'] = max(0., clock()-episode_started)
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                if not episode.get('failure_recorded', False):
                    record_failure(failure)
            except Exception:
                error.add_note('episode diagnostic recording failed')
    return outcomes, complete


def worst_case(episode):
    return dict(mae=1., rmse=1., spearman=-1., kendall=-1., uniform_mae=1., prior_mae=1.,
                anchor_mae=1., irt_mae=1., control=False, completed=False, signature=None,
                solution=None, duration=0.)


def episode_list(cases, seeds):
    episodes = [dict(case=case, condition=condition, seed=seed, replay=False)
                for case in cases for condition in CONDITIONS for seed in seeds]
    episodes.append(dict(case=cases[0], condition='normal', seed=seeds[0], replay=True))
    return episodes


def execute_episode(episode, call, work_deadline, *, data, client, budgets, work_seconds, smoke):
    import numpy as np
    begin = time.monotonic()
    source = data['source'].copy()
    target = data['target']
    groups = data['item_groups']
    rng = np.random.default_rng(episode['seed'])
    if episode['condition'] == 'permuted':
        original = source.copy()
        for row in range(len(source)):
            offset = int(rng.integers(1, source.shape[1]))
            order = np.roll(np.arange(source.shape[1]), offset)
            if np.any(order == np.arange(source.shape[1])):
                raise ProtocolFailure('vacuous_permutation')
            source[row] = source[row, order]
        if np.array_equal(source, original):
            raise ProtocolFailure('vacuous_permutation')
    extended = np.vstack([target, target[0]])
    permutation = np.random.default_rng(episode['seed']).permutation(len(extended))
    extended = extended[permutation]
    copy_positions = [int(np.flatnonzero(permutation == value)[0]) for value in (0, len(target))]
    real_positions = np.array([int(np.flatnonzero(permutation == value)[0]) for value in range(len(target))])
    baseline = None
    baseline_metrics = {name: [1.]*len(budgets) for name in ('uniform_mae', 'prior_mae', 'anchor_mae', 'irt_mae')}
    operation = 'upload_start'
    primary = None
    baseline_recorded = False
    signature = hashlib.sha256()
    outcomes = []
    solutions = []
    candidate_deadline = min(work_deadline - (4*work_seconds+3 if episode['condition'] == 'normal' and not episode['replay'] else 0),
                             begin+work_seconds)
    if candidate_deadline <= begin:
        raise TimeoutError('insufficient matched method reservations')
    def baseline_failure(category):
        nonlocal baseline_recorded
        if not baseline_recorded:
            failure = dict(component='baseline', category=category, operation='baseline_worker')
            status = baseline.process.poll() if baseline else None
            if status is not None:
                failure['exit_status'] = status
            record_failure(failure)
            episode['failure_recorded'] = True
            baseline_recorded = True
    def baseline_status():
        if baseline is None:
            return None
        status = baseline.process.poll()
        if status is None or status == 0:
            return None
        return 'baseline_timeout' if status == 124 else 'baseline_signal' if status < 0 else 'baseline_exit'
    def poll():
        category = baseline_status()
        if category:
            fail_required_baseline(category, lambda: baseline.close(failed=True), baseline_failure)
    def productive_call(request):
        nonlocal operation, primary
        operation = request['op']
        try:
            poll()
            remaining = candidate_deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError('candidate work deadline')
            response = call(request, timeout_override=min(remaining, 30))
            poll()
            signature.update(bounded_json_line(response))
            return response
        except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
            primary = error
            raise
    try:
        raw = source.tobytes(order='C')
        chunk_size = max(1, math.ceil(len(raw)/2)) if smoke else CHUNK_BYTES
        chunks = math.ceil(len(raw)/chunk_size)
        if chunks > MAX_CHUNKS:
            raise ProtocolFailure('upload_bound')
        ack(productive_call(dict(op='upload_start', shape=list(source.shape), dtype='uint8',
            encoding='base64', byte_order='na', total_bytes=len(raw), chunks=chunks,
            item_groups=groups.tolist(), source_weights=data['source_weights'].tolist(),
            source_groups=np.unique(data['source_groups'], return_inverse=True)[1].tolist(),
            target_count=len(extended), max_budget=max(budgets))))
        for index in range(chunks):
            offset = index*chunk_size
            ack(productive_call(dict(op='upload_chunk', index=index, offset=offset,
                                    data=base64.b64encode(raw[offset:offset+chunk_size]).decode())))
        ack(productive_call({'op': 'upload_commit'}))
        ack(productive_call(dict(op='fit', training_steps=200, cv_settings=4)))
        previous = []
        control = True
        for budget in budgets:
            response = productive_call({'op': 'select', 'budget': budget})
            if type(response) is not dict or set(response) != {'items'}:
                raise ProtocolFailure('invalid_selection')
            items = response['items']
            if (type(items) is not list or len(items) != budget
                    or any(type(item) is not int or not 0 <= item < source.shape[1] for item in items)
                    or len({int(groups[item]) for item in items}) != budget or items[:len(previous)] != previous):
                raise ProtocolFailure('invalid_selection')
            previous = items
            values = extended[:, items].copy()
            if episode['condition'] == 'constant':
                values.fill(0)
            ack(productive_call({'op': 'observe', 'items': items, 'values': values.tolist()}))
            ack(productive_call({'op': 'update'}))
            response = productive_call({'op': 'predict'})
            if type(response) is not dict or set(response) != {'predictions'}:
                raise ProtocolFailure('invalid_predictions')
            predictions = response['predictions']
            if (type(predictions) is not list or len(predictions) != len(extended)
                    or any(type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1 for value in predictions)):
                raise ProtocolFailure('invalid_predictions')
            history_predictions = {}
            for history, prediction in zip(values, predictions):
                key = tuple(history)
                if key in history_predictions and abs(prediction-history_predictions[key]) > 1e-10:
                    control = False
                history_predictions[key] = prediction
            control &= abs(predictions[copy_positions[0]]-predictions[copy_positions[1]]) <= 1e-10
            prediction_array = np.array(predictions)[real_positions]
            outcomes.append(checkpoint_metrics(prediction_array, target.mean(axis=1), data['target_groups']))
            solutions.append(dict(budget=budget, items=items, predictions=prediction_array.tolist(),
                                  references=target.mean(axis=1).tolist(),
                                  lineage_groups=data['target_groups'].tolist()))
        ack(productive_call({'op': 'close'}))
        if episode['condition'] == 'normal' and not episode['replay']:
            interpreter, environment = candidate_subprocess_settings(os.environ)
            baseline = Worker([interpreter, '-I', str(Path(__file__).resolve()), '--baseline_worker',
                               '--repair' if repair_mode() else '--sealed'], environment)
            payload = dict(source=source.tolist(), target=target.tolist(), item_groups=groups.tolist(),
                           source_weights=data['source_weights'].tolist(), target_groups=data['target_groups'].tolist(),
                           seed=episode['seed'], budgets=budgets, work_seconds=work_seconds)
            baseline_end = min(work_deadline, time.monotonic()+4*work_seconds+2)
            def result(timeout):
                try:
                    value = baseline.exchange(payload, timeout=timeout)
                except ProtocolFailure as error:
                    try:
                        status = baseline.process.wait(timeout=.2)
                    except subprocess.TimeoutExpired:
                        status = None
                    category = 'baseline_timeout' if status == 124 else 'baseline_signal' if status is not None and status < 0 else 'baseline_exit' if status else 'baseline_result_failure'
                    fail_required_baseline(category, lambda: baseline.close(failed=True), baseline_failure)
                if (type(value) is not dict or set(value) != {'metrics', 'predictions', 'productive_seconds'}
                        or set(value['metrics']) != set(baseline_metrics)):
                    raise RuntimeError('invalid baseline result')
                for values in value['metrics'].values():
                    if len(values) != len(budgets) or any(not math.isfinite(value) for value in values):
                        raise RuntimeError('invalid baseline metric')
                try:
                    status = baseline.process.wait(timeout=min(.5, max(.001, timeout)))
                except subprocess.TimeoutExpired as error:
                    raise RuntimeError('baseline did not terminate') from error
                if status != 0:
                    fail_required_baseline('baseline_signal' if status < 0 else 'baseline_exit',
                                           lambda: baseline.close(failed=True), baseline_failure)
                for name, predictions in value['predictions'].items():
                    if name not in baseline_metrics or len(predictions) != len(budgets):
                        raise RuntimeError('invalid baseline predictions')
                    for index, prediction in enumerate(predictions):
                        if len(prediction) != len(target) or not all(type(number) in (int, float) and math.isfinite(number) and 0 <= number <= 1 for number in prediction):
                            raise RuntimeError('invalid baseline predictions')
                        measured = checkpoint_metrics(np.array(prediction), target.mean(axis=1), data['target_groups'])['mae']
                        if not math.isclose(measured, value['metrics'][name][index], abs_tol=1e-12):
                            raise RuntimeError('baseline metric mismatch')
                return value
            computed = collect_required_baseline(result, deadline=baseline_end, clock=time.monotonic,
                cancel_work=lambda: baseline.close(failed=True), record_failure=baseline_failure)
            baseline_metrics = computed['metrics']
            for index, solution in enumerate(solutions):
                solution['baseline_predictions'] = {name: values[index] for name, values in computed['predictions'].items()}
        aggregate = {name: fixed_weight_score([result[name] for result in outcomes], [1/len(budgets)]*len(budgets),
                                            -1 if name in ('spearman', 'kendall') else 1)
                     for name in ('mae', 'rmse', 'spearman', 'kendall')}
        aggregate.update({name: sum(values)/len(values) for name, values in baseline_metrics.items()})
        aggregate.update(control=bool(control), completed=True, signature=signature.hexdigest(),
                         solution=solutions, duration=time.monotonic()-begin)
        return aggregate
    except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
        if primary is None:
            primary = error
        error.operation = operation
        raise
    finally:
        try:
            client.cleanup(failed=primary is not None)
        except Exception:
            if primary is None:
                raise
        if baseline:
            try:
                baseline.close(failed=primary is not None)
            except Exception:
                if primary is None:
                    raise


def aggregate_results(episodes, outcomes, complete):
    normal = [value for episode, value in zip(episodes, outcomes) if episode['condition'] == 'normal' and not episode['replay']]
    result = {name: sum(value[name] for value in normal)/len(normal)
              for name in ('mae', 'rmse', 'spearman', 'kendall', 'uniform_mae', 'prior_mae', 'anchor_mae', 'irt_mae')}
    controls = all(value['control'] and value['completed'] for value in outcomes)
    first, replay = outcomes[0]['solution'], outcomes[-1]['solution']
    replay_matches = first is not None and replay is not None and len(first) == len(replay)
    if replay_matches:
        replay_matches = all(reference['items'] == repeated['items']
            and len(reference['predictions']) == len(repeated['predictions'])
            and all(abs(float(left)-float(right)) <= 1e-10
                    for left, right in zip(reference['predictions'], repeated['predictions']))
            for reference, repeated in zip(first, replay))
    controls &= replay_matches
    for condition in ('constant', 'permuted'):
        values = [value['mae'] if value['completed'] and value['control'] else 1.
                  for episode, value in zip(episodes, outcomes) if episode['condition'] == condition]
        result[condition+'_mae'] = sum(values)/len(values)
    result['control_correct'] = float(controls)
    result['correct'] = float(complete and controls)
    if PLANE == 'search':
        result['combined_score'] = 1-result['mae']
    return result


def paired_uncertainty(episodes, outcomes, loaded, cases):
    import numpy as np
    rng = np.random.default_rng(1729)
    names = ['uniform_mae', 'prior_mae', 'anchor_mae', 'irt_mae']
    distributions = {name: [] for name in names}
    points = {name: [] for name in names}
    failed = 0
    for case in cases:
        groups = loaded[case]['target_groups']
        unique = np.unique(groups)
        cells = [value for episode, value in zip(episodes, outcomes)
                 if episode['case'] == case and episode['condition'] == 'normal' and not episode['replay']]
        differences = {name: np.zeros(len(unique)) for name in names}
        for cell in cells:
            if not cell['completed']:
                failed += 1
                continue
            for checkpoint in cell['solution']:
                truth = np.array(checkpoint['references'])
                candidate_errors = np.abs(np.array(checkpoint['predictions'])-truth)
                for name in names:
                    baseline_errors = np.abs(np.array(checkpoint['baseline_predictions'][name])-truth)
                    for index, group in enumerate(unique):
                        differences[name][index] += float(np.mean((candidate_errors-baseline_errors)[groups == group])) / (len(cells)*len(cell['solution']))
        sampled = rng.integers(0, len(unique), size=(200, len(unique)))
        for name in names:
            points[name].append(float(differences[name].mean()))
            distributions[name].append(differences[name][sampled].mean(axis=1))
    return dict(policy='paired lineage-block bootstrap; checkpoints/seeds retained within groups; equal case weights; 200 draws; fixed failure differences 1-1=0; conditional on fixed cases',
                failed_normal_cells=failed,
                comparisons={name: dict(candidate_minus_baseline_mae=float(np.mean(points[name])),
                    lower_95=float(np.quantile(np.mean(distributions[name], axis=0), .025)),
                    upper_95=float(np.quantile(np.mean(distributions[name], axis=0), .975))) for name in names})


def write_results(directory, metrics, feasible):
    directory.mkdir(parents=True, exist_ok=True)
    expected = set(METRICS + (['combined_score'] if PLANE == 'search' else []))
    if set(metrics) != expected or not all(type(value) in (int, float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError('invalid metric schema')
    (directory / 'metrics.json').write_text(json.dumps(metrics, allow_nan=False))
    (directory / 'correct.json').write_text(json.dumps({'correct': bool(metrics['correct'])}))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (directory / 'qualification.json').write_text(json.dumps({'schema_version': 1, 'feasible': bool(feasible)}))


def main():
    started = time.monotonic()
    resource.setrlimit(resource.RLIMIT_AS, (12*1024**3, 16*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (WALL_SECONDS*4, WALL_SECONDS*4))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    if hasattr(os, 'sched_getaffinity'):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:4])
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    cases, seeds = (CASES[:1], SEEDS[:1]) if smoke else (CASES, SEEDS)
    episodes = episode_list(cases, seeds)
    budgets = [2, 5] if smoke else [5, 10, 25]
    work = 8 if smoke else METHOD_SECONDS
    ceiling = 120 if smoke else WALL_SECONDS
    startup = 5 if smoke else STARTUP_SECONDS
    hard_deadline = started + ceiling - startup
    root = Path(os.environ.get('TASK_SOURCE_DIR', str(Path(__file__).resolve().parent))) / 'resources' / PLANE
    destination = Path(arguments.results_dir)
    outcomes = [worst_case(episode) for episode in episodes]
    client = None
    complete = False
    try:
        counts = preflight_messages()
        if len(episode_list(CASES, SEEDS))*counts['calls_per_episode'] != RPC_BUDGET:
            raise ValueError('RPC budget does not match complete maximum-size trace')
        production_count = len(episode_list(CASES, SEEDS))
        normal_count = len(CASES)*len(SEEDS)
        required_seconds = (STARTUP_SECONDS + FINISH_RESERVE + production_count*(RESET_TIMEOUT+EPISODE_OVERHEAD+METHOD_SECONDS)
                            + normal_count*(4*METHOD_SECONDS+3))
        if required_seconds > WALL_SECONDS:
            raise ValueError('joint matched-method workload infeasible')
        loaded = {case: load_case(root, case, smoke) for case in cases}
        client = Candidate(arguments.program_path, smoke)
        def evaluate(episode, call, deadline):
            return execute_episode(episode, call, deadline, data=loaded[episode['case']], client=client,
                                   budgets=budgets, work_seconds=work, smoke=smoke)
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline,
            finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD,
            rpc_cap=30, clock=time.monotonic, rpc=client.call, evaluate=evaluate,
            worst_case=worst_case, record_failure=record_failure)
        metrics = aggregate_results(episodes, outcomes, complete)
        feasible = complete and not smoke and time.monotonic() < hard_deadline
        records = []
        uncertainty = paired_uncertainty(episodes, outcomes, loaded, cases)
        for seed in seeds:
            selected = [index for index, episode in enumerate(episodes) if episode['seed'] == seed]
            normals = [outcomes[index] for index in selected if episodes[index]['condition'] == 'normal' and not episodes[index]['replay']]
            solutions = [dict(case=episodes[index]['case'], condition=episodes[index]['condition'],
                              replay=episodes[index]['replay'], checkpoints=outcomes[index]['solution'])
                         for index in selected]
            records.append(dict(seed=seed, score=1-sum(value['mae'] for value in normals)/len(normals),
                                correct=bool(metrics['correct']), duration_seconds=sum(outcomes[index]['duration'] for index in selected),
                                solution=dict(episodes=solutions, paired_mae_uncertainty=uncertainty)))
        evidence = json.dumps({'schema_version': 1, 'episodes': records}, allow_nan=False, separators=(',', ':')).encode()
        if time.monotonic() >= hard_deadline:
            metrics['correct'] = 0.
            feasible = False
            for record in records:
                record['correct'] = False
            evidence = json.dumps({'schema_version': 1, 'episodes': records}, allow_nan=False, separators=(',', ':')).encode()
        write_results(destination, metrics, feasible)
        if len(evidence) <= 16*1024**2:
            (destination / 'evaluation_evidence.json').write_bytes(evidence)
    except Exception as error:
        metrics = aggregate_results(episodes, outcomes, False)
        write_results(destination, metrics, False)
        if PLANE == 'search':
            print(f'evaluator_exception type={type(error).__name__[:80]} message=scaffold_execution_failed', file=sys.stderr)
        else:
            print('evaluator_exception category=sealed_execution_failure', file=sys.stderr)
        raise SystemExit(1)
    finally:
        if client:
            pending_error = sys.exc_info()[0] is not None
            try:
                client.close()
            except Exception:
                print('evaluator_exception type=CleanupFailure message=bounded_cleanup_failed', file=sys.stderr)
                if not pending_error:
                    write_results(destination, aggregate_results(episodes, outcomes, False), False)
                    raise SystemExit(1)


if __name__ == '__main__':
    if '--baseline_worker' in sys.argv:
        baseline_entry('--repair' in sys.argv)
    else:
        main()
