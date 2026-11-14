"""Self-contained offline score-matrix evaluator; no private targets cross RPC."""
import time
MODULE_START = time.monotonic()
import os
for _thread_name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_thread_name] = '1'
import argparse
import base64
import collections
import importlib.util
import json
import math
from pathlib import Path
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import numpy as np
ROLE_CORES = sorted(os.sched_getaffinity(0))
SOURCE_REVISION = '6dabbcc68c28ea5f180ce7df79347b3ca9cc6383'

PLANE = 'final'
RESOURCE_HASHES = {'dataset.json': '13251df8ce195ce059142fffcd9fc89a897c6a83ef8d6c146bd2af1037a088b0', 'manifest.json': 'f4e733a50eb2e6df59e71b19698bebcf8ceead3f665973ca9caf3a2c9f77d71f'}
RESET_SEQUENCE = [4001, 4001, 4009, 4009, 4021, 4021, 4001, 4001, 4009, 4009, 4021, 4021, 4001]
SMOKE_RESET_SEQUENCE = [4001, 4001, 4001]
WALL_SECONDS = 1800
STARTUP_SECONDS = 90
WORK_SECONDS = 30
RPC_BUDGET = 5772

BOOTSTRAP = "import os, sys, json, ctypes, resource, signal, importlib.util, contextlib, pathlib\n\n\ndef isolate(root, runtime, wall, cores):\n    resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 ** 3, 8 * 1024 ** 3))\n    resource.setrlimit(resource.RLIMIT_CPU, (wall * 3, wall * 3))\n    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))\n    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))\n    os.sched_setaffinity(0, set(cores))\n    libc = ctypes.CDLL(None, use_errno=True)\n    if libc.prctl(38, 1, 0, 0, 0) != 0:\n        raise RuntimeError('no_new_privs unavailable')\n    abi = libc.syscall(444, 0, 0, 1)\n    if abi < 3:\n        raise RuntimeError('Landlock ABI 3 required for private-data isolation')\n    class Ruleset(ctypes.Structure):\n        _fields_ = [('handled_access_fs', ctypes.c_uint64)]\n    class Rule(ctypes.Structure):\n        _pack_ = 1\n        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]\n    access = (1 << 15) - 1\n    ruleset = Ruleset(access)\n    descriptor = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)\n    if descriptor < 0:\n        raise RuntimeError('Landlock ruleset failed')\n    for path, rights in [(root, 13), (runtime, 13), ('/usr', 13), ('/lib', 13), ('/lib64', 13), ('/dev/null', 6), ('/dev/urandom', 4)]:\n        if not os.path.exists(path):\n            continue\n        opened = os.open(path, os.O_PATH | os.O_CLOEXEC)\n        rule = Rule(rights, opened)\n        outcome = libc.syscall(445, descriptor, 1, ctypes.byref(rule), 0)\n        os.close(opened)\n        if outcome != 0:\n            raise RuntimeError('Landlock path rule failed')\n    outcome = libc.syscall(446, descriptor, 0)\n    os.close(descriptor)\n    if outcome != 0:\n        raise RuntimeError('Landlock activation failed')\n    class Filter(ctypes.Structure):\n        _fields_ = [('code', ctypes.c_ushort), ('jt', ctypes.c_ubyte), ('jf', ctypes.c_ubyte), ('value', ctypes.c_uint32)]\n    class Program(ctypes.Structure):\n        _fields_ = [('length', ctypes.c_ushort), ('filters', ctypes.POINTER(Filter))]\n    instructions = [(0x20, 0, 0, 4), (0x15, 1, 0, 0xc000003e), (0x06, 0, 0, 0x80000000), (0x20, 0, 0, 0)]\n    denied = [41, 42, 49, 50, 53, 57, 58, 59, 62, 90, 91, 92, 93, 94, 101, 109, 112, 132, 155, 165, 166, 200, 203, 234, 235, 250, 260, 261, 268, 272, 280, 298, 304, 308, 310, 311, 321, 322, 323, 424, 425, 426, 427, 434, 438, 440, 452]\n    for number in denied:\n        instructions.extend([(0x15, 0, 1, number), (0x06, 0, 0, 0x00050001)])\n    instructions.extend([(0x15, 0, 1, 435), (0x06, 0, 0, 0x00050026), (0x15, 0, 4, 56), (0x20, 0, 0, 16), (0x45, 1, 0, 0x10000), (0x06, 0, 0, 0x00050001), (0x06, 0, 0, 0x7fff0000), (0x06, 0, 0, 0x7fff0000)])\n    filters = (Filter * len(instructions))(*(Filter(*item) for item in instructions))\n    program = Program(len(instructions), filters)\n    if libc.prctl(22, 2, ctypes.byref(program), 0, 0) != 0:\n        raise RuntimeError('seccomp activation failed')\n\n\ndef main():\n    path, root, runtime, wall, core_list, repair = sys.argv[1:]\n    isolate(root, runtime, int(wall), [int(value) for value in core_list.split(',')])\n    sys.path.insert(0, str(pathlib.Path(path).parent))\n    output = sys.stdout\n    with contextlib.redirect_stdout(sys.stderr):\n        spec = importlib.util.spec_from_file_location('candidate', path)\n        module = importlib.util.module_from_spec(spec)\n        spec.loader.exec_module(module)\n    for line in sys.stdin.buffer:\n        if len(line) >= 64 * 1024 * 1024:\n            raise ValueError('oversized request')\n        request = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')))\n        with contextlib.redirect_stdout(sys.stderr):\n            response = module.handle(request)\n        encoded = json.dumps(response, allow_nan=False, ensure_ascii=False, separators=(',', ':')) + '\\n'\n        if len(encoded.encode('utf-8')) >= 64 * 1024 * 1024:\n            raise ValueError('oversized response')\n        output.write(encoded)\n        output.flush()\n\n\ndef report_worker_exception(error):\n    name = type(error).__name__\n    if not name.isascii() or not name.isidentifier() or len(name) > 80:\n        name = 'WorkerException'\n    try:\n        message = str(error)\n    except Exception:\n        message = '<exception message unavailable>'\n    if len(message) > 2048 or len(message.encode('utf-8', errors='replace')) > 2048:\n        message = '<exception message omitted: too large>'\n    print(f'worker_exception type={name}\\n{message}', file=sys.stderr, flush=True)\n\ntry:\n    main()\nexcept Exception as error:\n    if sys.argv[-1] == 'repair':\n        report_worker_exception(error)\n    else:\n        print('candidate_worker_failure', file=sys.stderr, flush=True)\n    raise SystemExit(1)\n"


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
    def guarded(request):
        check()
        result = call(request)
        check()
        return result
    return guarded


class ProtocolFailure(RuntimeError):
    def __init__(self, category='malformed_response'):
        self.category = bounded_failure_name(category, 'malformed_response')
        super().__init__('candidate protocol failure')


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout,
                          episode_overhead, rpc_cap, clock, rpc, evaluate,
                          worst_case, record_failure):
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
            if clock() > episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure)
            except Exception:
                error.add_note('episode diagnostic recording failed')
        finally:
            episode['elapsed'] = max(0., clock() - episode_started)
    return outcomes, complete


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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds) or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError('invalid CPU budget')
    return math.ceil(wall_seconds * allowed_threads)


def fixed_weight_score(values, weights, worst_case=1.):
    if not values or len(values) != len(weights) or any(not math.isfinite(weight) or weight < 0 for weight in weights) or not math.isclose(sum(weights), 1., rel_tol=0, abs_tol=1e-12):
        raise ValueError('invalid fixed weights')
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError('nonfinite contribution')
    return sum(value * weight for value, weight in zip(retained, weights))


def require_controls(expected, completed):
    if set(expected) - set(completed):
        raise ProtocolFailure('missing_control')


def bounded_json_line(value, wire_limit=64 * 1024 * 1024):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':'), ensure_ascii=False).encode('utf-8') + b'\n'
    if len(encoded) >= wire_limit:
        raise ProtocolFailure('wire_limit')
    return encoded


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH', 'LD_LIBRARY_PATH', 'LANG', 'LC_ALL', 'TZ',
                     'CUDA_VISIBLE_DEVICES', 'NVIDIA_VISIBLE_DEVICES', 'NVIDIA_DRIVER_CAPABILITIES',
                     'OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE', 'XLA_PYTHON_CLIENT_MEM_FRACTION', 'XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent', PYTHONNOUSERSITE='1', PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1',
                       OMP_NUM_THREADS='3', OPENBLAS_NUM_THREADS='3', MKL_NUM_THREADS='3', NUMEXPR_NUM_THREADS='3')
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


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
                       'retained_bytes': self.retained_bytes, 'truncated': self.truncated, 'capture_error': self.capture_error}
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

import hashlib
import json
import math
import unicodedata

DROP_FIELDS = {'evaluation_time', 'kg_co2_emissions', 'mteb_version', 'model_name', 'model', 'model_id', 'model_revision', 'revision', 'timestamp', 'path', 'evaluation_time_per_sample', 'dataset_revision', 'dataset_id', 'date'}


def normalize_raw(value):
    if isinstance(value, dict):
        normalized = {key: normalize_raw(item) for key, item in sorted(value.items()) if key not in DROP_FIELDS}
        if 'mteb_dataset_name' in normalized:
            task_name = normalized.pop('mteb_dataset_name')
            if 'task_name' not in normalized:
                normalized['task_name'] = task_name
        return normalized
    if isinstance(value, list):
        return [normalize_raw(item) for item in value]
    if isinstance(value, str):
        return '\n'.join(line.rstrip() for line in unicodedata.normalize('NFC', value).replace('\r\n', '\n').split('\n'))
    if isinstance(value, float):
        if not math.isfinite(value):
            return None
        return int(value) if value.is_integer() else value
    return value


def raw_hash(value):
    data = json.dumps(normalize_raw(value), sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def score_cells(task, document):
    if 'Classification' in task:
        metrics = ['accuracy']
    elif 'Clustering' in task:
        metrics = ['v_measure']
    elif task.startswith('STS') or task in ('SICK-R', 'BIOSSES', 'SummEval'):
        metrics = ['cosine_spearman', 'cos_sim_spearman', 'spearman']
    elif 'Reranking' in task or task in ('AskUbuntuDupQuestions', 'SciDocsRR', 'StackOverflowDupQuestions'):
        metrics = ['map']
    elif task in ('TwitterSemEval2015', 'TwitterURLCorpus', 'SprintDuplicateQuestions'):
        return {}
    else:
        metrics = ['ndcg_at_10']
    output = {}
    scores = document.get('scores', document)
    for split in ('test', 'validation', 'dev'):
        entries = scores.get(split)
        if entries is None:
            continue
        if isinstance(entries, dict):
            if any(key in entries for key in metrics):
                entries = [entries]
            elif 'en' in entries:
                entries = [entries['en']]
            else:
                continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            languages = entry.get('languages', ['eng-Latn'])
            subset = entry.get('hf_subset', 'default')
            if languages != ['eng-Latn'] or subset not in ('default', 'en', 'eng', 'en-en'):
                continue
            for metric in metrics:
                value = entry.get(metric)
                if type(value) not in (int, float) or not math.isfinite(value):
                    continue
                main = entry.get('main_score', value)
                if type(main) not in (int, float) or not math.isfinite(main) or abs(main - value) > 1e-5:
                    continue
                signed = 'spearman' in metric
                if not (-1 if signed else 0) <= value <= 1:
                    continue
                canonical_metric = 'cosine_spearman' if metric == 'cos_sim_spearman' else metric
                context = [task, 'eng-Latn', split, canonical_metric, document.get('dataset_revision')]
                key = json.dumps(context, separators=(',', ':'))
                normalized = (float(value) + 1) / 2 if signed else float(value)
                if key in output and output[key] != normalized:
                    raise ValueError('ambiguous compatible score')
                output[key] = normalized
                break
    return output

import numpy as np


def means(matrix, mask):
    return np.divide((matrix * mask).sum(axis=0), mask.sum(axis=0), out=np.full(matrix.shape[1], .5), where=mask.sum(axis=0) > 0)


def factor_fit(matrix, mask, rank, ridge, sweeps, seed, check=lambda: None):
    offset = means(matrix, mask)
    centered = matrix - offset
    rng = np.random.default_rng(seed)
    rows, columns = matrix.shape
    latent = rng.normal(0, .05, (rows, rank))
    factors = rng.normal(0, .05, (columns, rank))
    identity = np.eye(rank) * ridge
    for sweep in range(sweeps):
        check()
        for index in range(rows):
            observed = mask[index]
            design = factors[observed]
            latent[index] = np.linalg.solve(design.T @ design + identity, design.T @ centered[index, observed])
        for index in range(columns):
            observed = mask[:, index]
            design = latent[observed]
            factors[index] = np.linalg.solve(design.T @ design + identity, design.T @ centered[observed, index])
    return offset, factors


def tune_fit(matrix, mask, seed, sweeps=30, check=lambda: None):
    rng = np.random.default_rng(seed)
    validation = (rng.random(mask.shape) < .1) & mask
    train_mask = mask & ~validation
    best = None
    for rank in (2, 4):
        for ridge in (.1, 1.):
            offset, factors = factor_fit(matrix, train_mask, rank, ridge, min(8, sweeps), seed, check)
            errors = []
            for row in range(len(matrix)):
                check()
                observed = np.flatnonzero(train_mask[row])
                prediction = condition(offset, factors, ridge, observed, matrix[row, observed])
                errors.extend(abs(prediction[validation[row]] - matrix[row, validation[row]]))
            loss = float(np.mean(errors)) if errors else 1.
            item = (loss, rank, ridge)
            if best is None or item < best:
                best = item
    _, rank, ridge = best
    offset, factors = factor_fit(matrix, mask, rank, ridge, sweeps, seed, check)
    return offset, factors, ridge


def condition(offset, factors, ridge, columns, values):
    if len(columns) == 0:
        return offset.copy()
    design = factors[np.asarray(columns, dtype=int)]
    latent = np.linalg.solve(design.T @ design + np.eye(factors.shape[1]) * ridge, design.T @ (np.asarray(values) - offset[columns]))
    return np.clip(offset + factors @ latent, 0, 1)


def information_select(factors, ridge, available, observed):
    design = factors[np.asarray(observed, dtype=int)]
    covariance = np.linalg.inv(design.T @ design + np.eye(factors.shape[1]) * ridge)
    options = sorted(set(available) - set(observed))
    return max(options, key=lambda index: (float(factors[index] @ covariance @ factors[index]), -index))

def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('nonfinite JSON')
    return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)


class Candidate:
    def __init__(self, program_path, wall_seconds, rpc_budget):
        self.path = str(Path(program_path).absolute())
        socket = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        fixed = program_path == '/broker-code/candidate_proxy.py'
        if bool(socket) != fixed:
            raise ValueError('broker requires fixed proxy path and socket together')
        self.proxy = None
        self.process = None
        self.capture = None
        self.temporary = None
        self.resets = []
        self.counts = collections.Counter()
        self.rpc_budget = rpc_budget
        self.snapshot = None
        self.exit_status = None
        self.wall_seconds = wall_seconds
        self.buffer = bytearray()
        self.method_deadline = None
        if fixed and socket:
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', self.path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle
        else:
            self.temporary = tempfile.TemporaryDirectory(prefix='candidate-isolated-')
            self.root = Path(self.temporary.name)
            source = Path(self.path).parent
            destination = self.root / 'code'
            destination.mkdir()
            size = 0
            entries = 0
            copy_deadline = time.monotonic() + 5
            for item in source.rglob('*'):
                entries += 1
                if entries > 2048 or time.monotonic() >= copy_deadline:
                    raise ValueError('candidate source copy budget exceeded')
                if item.is_symlink():
                    raise ValueError('candidate symlinks forbidden')
                if item.is_file() and '__pycache__' not in item.parts:
                    size += item.stat().st_size
                    if size > 32 * 1024 * 1024:
                        raise ValueError('candidate code copy exceeds limit')
                    copied = destination / item.relative_to(source)
                    copied.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(item, copied)
            self.copied_path = destination / Path(self.path).name

    def start(self):
        self.stop()
        interpreter, environment = candidate_subprocess_settings(os.environ)
        executable = shutil.which(interpreter, path=environment.get('PATH'))
        if executable is None:
            raise ValueError('candidate interpreter unavailable')
        prefix = Path(executable).absolute().parent.parent
        if not (prefix / 'pyvenv.cfg').is_file() and str(prefix) not in ('/usr', '/usr/local'):
            raise ValueError('unsupported isolated interpreter layout')
        runtime = str(prefix)
        allowed = ROLE_CORES
        if len(allowed) < 4:
            raise ValueError('native evaluator requires four assigned CPU cores')
        cores = allowed[-3:]
        repair = 'repair' if PLANE == 'search' and (os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1' or os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1') else 'sealed'
        self.process = subprocess.Popen([interpreter, '-I', '-B', '-u', '-c', BOOTSTRAP,
                                         str(self.copied_path), str(self.root), runtime,
                                         str(self.wall_seconds), ','.join(map(str, cores)), repair],
                                        shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, cwd=self.root, env=environment,
                                        start_new_session=True, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.buffer.clear()
        self.snapshot = None
        self.exit_status = None

    def stop(self):
        if self.process is None:
            return
        process, capture = self.process, self.capture
        self.process = None
        if process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=.2)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=.2)
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.exit_status = process.returncode
        process.stdin.close()
        process.stdout.close()
        self.snapshot = capture.close()

    def rpc(self, request, *, timeout):
        operation = request['op']
        if operation == 'reset':
            self.method_deadline = None
        if self.method_deadline is not None:
            timeout = min(timeout, self.method_deadline - time.monotonic())
        if timeout <= 0:
            raise TimeoutError('method work deadline')
        self.counts[operation] += 1
        if sum(self.counts.values()) > self.rpc_budget:
            raise ProtocolFailure('rpc_budget')
        if operation == 'reset':
            self.resets.append(request['seed'])
        encoded = bounded_json_line(request)
        deadline = time.monotonic() + timeout
        if self.proxy is not None:
            def expired(signum, frame):
                raise TimeoutError('proxy RPC deadline')
            previous = signal.signal(signal.SIGALRM, expired)
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                result = self.proxy(request)
                try:
                    bounded_json_line(result)
                except (TypeError, ValueError, RecursionError):
                    raise ProtocolFailure() from None
                return result
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
        try:
            if operation == 'reset':
                self.start()
            if self.process is None:
                raise ProtocolFailure('candidate_exit')
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                offset = 0
                while offset < len(encoded):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('candidate write timeout')
                    try:
                        offset += os.write(self.process.stdin.fileno(), encoded[offset:offset + 65536])
                    except BlockingIOError:
                        pass
                selector.unregister(self.process.stdin)
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b'\n' not in self.buffer:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError('candidate response timeout')
                    chunk = os.read(self.process.stdout.fileno(), 65536)
                    if not chunk:
                        status = self.process.poll()
                        raise ProtocolFailure('candidate_signal' if status is not None and status < 0 else 'candidate_exit')
                    self.buffer.extend(chunk)
                    if len(self.buffer) >= 64 * 1024 * 1024:
                        raise ProtocolFailure('wire_limit')
                line, separator, tail = self.buffer.partition(b'\n')
                self.buffer = bytearray(tail)
            try:
                result = strict_json(line)
                bounded_json_line(result)
            except (ValueError, TypeError, RecursionError):
                raise ProtocolFailure() from None
            if time.monotonic() > deadline:
                raise TimeoutError('candidate response late')
            return result
        except (TimeoutError, ProtocolFailure, BrokenPipeError) as error:
            try:
                self.stop()
            except (RuntimeError, subprocess.TimeoutExpired):
                error.add_note('candidate cleanup failed')
            if isinstance(error, BrokenPipeError):
                raise ProtocolFailure('candidate_exit') from None
            raise

    def close(self):
        try:
            self.stop()
        finally:
            if self.temporary is not None:
                self.temporary.cleanup()

METRIC_NAMES = ('combined_score', 'candidate_mae', 'historical_mean_mae', 'observed_copy_mae',
                'random_lowrank_mae', 'greedy_ridge_mae', 'permuted_mae', 'permutation_gap', 'correct')
MAX_CHUNKS = 8
CHUNK_BYTES = 4 * 1024 * 1024
EXPECTED_CONTROLS = {'constant', 'copy', 'permuted', 'reset_replay'}


def check_deadline(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError('work deadline')


def ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise ProtocolFailure()


def encode_prediction(values):
    vector = np.asarray(values, dtype='<f4')
    return {'encoding': 'base64', 'dtype': '<f4', 'shape': [len(vector)], 'data': base64.b64encode(vector.tobytes()).decode('ascii')}


def decode_prediction(value, columns):
    if type(value) is not dict or set(value) != {'encoding', 'dtype', 'shape', 'data'} or value['encoding'] != 'base64' or value['dtype'] != '<f4' or value['shape'] != [columns] or type(value['data']) is not str or len(value['data']) != 4 * math.ceil(4 * columns / 3):
        raise ProtocolFailure()
    try:
        data = base64.b64decode(value['data'], validate=True)
    except ValueError:
        raise ProtocolFailure() from None
    if len(data) != columns * 4:
        raise ProtocolFailure()
    vector = np.frombuffer(data, dtype='<f4').astype(float)
    if not np.isfinite(vector).all() or (vector < 0).any() or (vector > 1).any():
        raise ProtocolFailure()
    return vector


def parse_step(response, available, selected, columns, checkpoint, terminal):
    if type(response) is not dict or set(response) != {'column', 'prediction'}:
        raise ProtocolFailure()
    next_column = response['column']
    if terminal:
        if next_column is not None:
            raise ProtocolFailure('illegal_selection')
    elif type(next_column) is not int or next_column not in available or next_column in selected:
        raise ProtocolFailure('illegal_selection')
    if checkpoint:
        prediction = decode_prediction(response['prediction'], columns)
    else:
        if response['prediction'] is not None:
            raise ProtocolFailure()
        prediction = None
    return next_column, prediction


def upload(call, matrix, mask):
    rows, columns = matrix.shape
    data = matrix.astype('<f4').tobytes() + mask.astype('u1').tobytes()
    if len(data) > 32 * 1024 * 1024:
        raise ValueError('historical logical value exceeds limit')
    ack(call({'op': 'upload_start', 'shape': [rows, columns], 'dtype': '<f4', 'encoding': 'base64',
              'mask_encoding': 'uint8', 'total_bytes': len(data), 'max_chunks': MAX_CHUNKS,
              'chunk_bytes': CHUNK_BYTES, 'tasks': ['t' + str(index) for index in range(columns)]}))
    for index, offset in enumerate(range(0, len(data), CHUNK_BYTES)):
        if index >= MAX_CHUNKS:
            raise ValueError('too many upload chunks')
        ack(call({'op': 'upload_chunk', 'index': index, 'offset': offset,
                  'data': base64.b64encode(data[offset:offset + CHUNK_BYTES]).decode('ascii')}))
    ack(call({'op': 'upload_commit'}))


def operation_counts(rows, k_max):
    return {'reset': 1, 'upload_start': 1, 'upload_chunk': MAX_CHUNKS, 'upload_commit': 1,
            'fit': 1, 'row_start': rows, 'observe': rows * k_max}


def payload_preflight():
    requests = []
    maximum = np.ones((220, 128), dtype='<f4')
    upload(lambda request: requests.append(request) or {'ok': True}, maximum, maximum.astype(bool))
    requests += [{'op': 'upload_chunk', 'index': 7, 'offset': 7 * CHUNK_BYTES,
                  'data': base64.b64encode(b'\xff' * CHUNK_BYTES).decode('ascii')},
                 {'op': 'reset', 'seed': (1 << 63) - 1}, {'op': 'fit', 'sweeps': 30},
                 {'op': 'row_start', 'row': 'r219', 'available': list(range(128)), 'k_max': 8, 'checkpoints': [1, 2, 4, 8]},
                 {'op': 'observe', 'column': 127, 'value': 0.12345678912345678}]
    responses = [{'ok': True}, {'column': 127, 'prediction': encode_prediction(np.linspace(0, 1, 128))},
                 {'column': None, 'prediction': None}]
    for value in requests + responses:
        raw = bounded_json_line(value)
        framed = bounded_json_line({'request_id': (1 << 63) - 1, 'payload': value, 'protocol': 'python_rpc_v1'})
        if len(raw) + 65536 >= 64 * 1024 * 1024 or len(framed) + 65536 >= 64 * 1024 * 1024:
            raise ValueError('complete RPC preflight exceeds limit')
    return max(len(bounded_json_line(value)) for value in requests), max(len(bounded_json_line(value)) for value in responses)


def load_resources(smoke):
    task_root = Path(os.environ.get('TASK_SOURCE_DIR', Path(__file__).resolve().parent))
    root = task_root / 'resources' / PLANE
    loaded = {}
    for name, expected in RESOURCE_HASHES.items():
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError('invalid frozen resource')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('frozen resource integrity mismatch')
        loaded[name] = strict_json(data)
    rows = loaded['dataset.json']['rows']
    for row in rows:
        documents = row['documents']
        if raw_hash({task: item['document'] for task, item in documents.items()}) != row['row_content_sha256']:
            raise ValueError('raw example digest mismatch')
        cells = {}
        for task, item in documents.items():
            if raw_hash(item['document']) != item['content_sha256']:
                raise ValueError('raw document digest mismatch')
            cells.update(score_cells(task, item['document']))
        row['cells'] = cells
    manifest = loaded['manifest.json']
    if manifest['source_revision'] != SOURCE_REVISION:
        raise ValueError('wrong source revision')
    profiles = manifest['smoke' if smoke else 'production']
    for plan in profiles:
        training = [rows[index] for index in plan['train']]
        test = [rows[index] for index in plan['test']]
        if {row['component'] for row in training} & {row['component'] for row in test}:
            raise ValueError('within-case identity overlap')
        if plan['case'] == 'family_disjoint' and {row['family'] for row in training} & {row['family'] for row in test}:
            raise ValueError('within-case family overlap')
        train_hashes = {item['content_sha256'] for row in training for item in row['documents'].values()}
        if any(item['content_sha256'] in train_hashes for row in test for item in row['documents'].values()):
            raise ValueError('within-case raw document overlap')
        columns = plan['columns']
        matrix = np.zeros((len(training), len(columns)))
        mask = np.zeros_like(matrix, dtype=bool)
        targets = np.zeros((len(test), len(columns)))
        target_mask = np.zeros_like(targets, dtype=bool)
        for collection, array, observed in ((training, matrix, mask), (test, targets, target_mask)):
            for row_index, row in enumerate(collection):
                for column_index, column in enumerate(columns):
                    if column in row['cells']:
                        array[row_index, column_index] = row['cells'][column]
                        observed[row_index, column_index] = True
        if not smoke:
            expected_rows = 24 if PLANE == 'search' else 48
            if len(training) < 64 or len(test) != expected_rows or len(columns) != 48:
                raise ValueError('production coverage violation')
            if plan['case'] == 'family_disjoint' and len({row['family'] for row in test}) < 3:
                raise ValueError('too few held-out families')
        if not mask.any(axis=0).all():
            raise ValueError('unsupported column')
        audit = set(plan['audit'])
        for observed in target_mask:
            queryable = set(np.flatnonzero(observed)) - audit
            required_audit = 2 if smoke else 4
            if len(queryable) < plan['checkpoints'][-1] or sum(observed[index] for index in audit) < required_audit or (not smoke and observed.sum() < 16):
                raise ValueError('held-out availability violation')
        plan.update(matrix=matrix, mask=mask, targets=targets, target_mask=target_mask,
                    families=[row['family'] for row in test])
    return profiles


def permute_history(matrix, mask, seed):
    rng = np.random.default_rng(seed + 76543)
    transformed = matrix.copy()
    effective = []
    mappings = []
    for column in range(matrix.shape[1]):
        indices = np.flatnonzero(mask[:, column])
        if len(indices) < 2 or np.unique(matrix[indices, column]).size < 2:
            continue
        for attempt in range(64):
            order = rng.permutation(indices)
            shifted = np.roll(order, 1)
            if not np.array_equal(matrix[shifted, column], matrix[order, column]):
                transformed[order, column] = matrix[shifted, column]
                mapping = dict(zip(order.tolist(), shifted.tolist()))
                if any(left == right for left, right in mapping.items()):
                    raise ValueError('identity permutation')
                mappings.append(tuple(sorted(mapping.items())))
                effective.append(column)
                break
        else:
            raise ValueError('vacuous permutation')
        if not np.array_equal(np.sort(matrix[indices, column]), np.sort(transformed[indices, column])):
            raise ValueError('permutation marginal mismatch')
    if len(effective) < 2 or len(set(mappings)) < 2 or np.array_equal(transformed, matrix):
        raise ValueError('ineffective correlation control')
    if not np.allclose(means(matrix, mask), means(transformed, mask), rtol=0, atol=1e-12):
        raise ValueError('constant control changed')
    return transformed


def row_average(values, families, case):
    if case == 'family_disjoint':
        unique = sorted(set(families))
        family_values = [fixed_weight_score([values[index] for index, family in enumerate(families) if family == selected],
                                            [1 / families.count(selected)] * families.count(selected)) for selected in unique]
        return fixed_weight_score(family_values, [1 / len(unique)] * len(unique))
    return fixed_weight_score(values, [1 / len(values)] * len(values))


def losses(prediction, target, observed, selected, audit):
    remaining = observed.copy()
    remaining[list(selected)] = False
    common = observed.copy()
    common[:] = False
    common[list(audit)] = observed[list(audit)]
    if not remaining.any() or not common.any():
        raise ValueError('empty fixed target set')
    return float(np.mean(abs(prediction[remaining] - target[remaining]))), float(np.mean(abs(prediction[common] - target[common])))


def aggregate_rows(per_row, plan):
    return row_average(per_row, plan['families'], plan['case'])


def native_random(plan, matrix, seed, deadline, sweeps):
    check = lambda: check_deadline(deadline)
    offset, factors, ridge = tune_fit(matrix, plan['mask'], seed, sweeps, check)
    rng = np.random.default_rng(seed)
    values = []
    audits = []
    records = []
    for row, target in enumerate(plan['targets']):
        check()
        available = sorted(set(np.flatnonzero(plan['target_mask'][row]).tolist()) - set(plan['audit']))
        order = rng.permutation(available).tolist()[:plan['checkpoints'][-1]]
        checkpoints, common = [], []
        for count in plan['checkpoints']:
            selected = order[:count]
            prediction = condition(offset, factors, ridge, selected, target[selected])
            loss, audit = losses(prediction, target, plan['target_mask'][row], selected, plan['audit'])
            checkpoints.append(loss)
            common.append(audit)
            records.append({'row': row, 'k': count, 'mae': loss, 'audit_mae': audit})
        values.append(fixed_weight_score(checkpoints, [1 / len(checkpoints)] * len(checkpoints)))
        audits.append(fixed_weight_score(common, [1 / len(common)] * len(common)))
    return {'loss': aggregate_rows(values, plan), 'audit': aggregate_rows(audits, plan), 'records': records}


def native_ridge(plan, matrix, deadline):
    check = lambda: check_deadline(deadline)
    check()
    offset = means(matrix, plan['mask'])
    centered = (matrix - offset) * plan['mask']
    columns = matrix.shape[1]
    correlation = np.zeros((columns, columns))
    for left in range(columns):
        check()
        for right in range(columns):
            overlap = plan['mask'][:, left] & plan['mask'][:, right]
            count = int(overlap.sum())
            if count >= 4:
                first, second = matrix[overlap, left], matrix[overlap, right]
                first, second = first - first.mean(), second - second.mean()
                denominator = np.linalg.norm(first) * np.linalg.norm(second)
                if denominator > 1e-12:
                    correlation[left, right] = float(first @ second / denominator) * count / (count + 10)
    values, audits, records = [], [], []
    for row, target in enumerate(plan['targets']):
        available = sorted(set(np.flatnonzero(plan['target_mask'][row]).tolist()) - set(plan['audit']))
        selected, coverage, checkpoints, common = [], np.zeros(columns), [], []
        for count in range(1, plan['checkpoints'][-1] + 1):
            check()
            chosen = max((column for column in available if column not in selected), key=lambda column: (float(np.maximum(coverage, correlation[column] ** 2).sum()), -column))
            selected.append(chosen)
            coverage = np.maximum(coverage, correlation[chosen] ** 2)
            if count not in plan['checkpoints']:
                continue
            prediction = offset.copy()
            for column in range(columns):
                observed = plan['mask'][:, column]
                design = centered[observed][:, selected]
                weights = np.linalg.solve(design.T @ design + np.eye(count) * .1, design.T @ centered[observed, column])
                prediction[column] += (target[selected] - offset[selected]) @ weights
            prediction = np.clip(prediction, 0, 1)
            loss, audit = losses(prediction, target, plan['target_mask'][row], selected, plan['audit'])
            checkpoints.append(loss)
            common.append(audit)
            records.append({'row': row, 'k': count, 'mae': loss, 'audit_mae': audit})
        values.append(fixed_weight_score(checkpoints, [1 / len(checkpoints)] * len(checkpoints)))
        audits.append(fixed_weight_score(common, [1 / len(common)] * len(common)))
    return {'loss': aggregate_rows(values, plan), 'audit': aggregate_rows(audits, plan), 'records': records}


def candidate_rollout(plan, matrix, call, deadline, sweeps):
    def bounded_call(request):
        check_deadline(deadline)
        return call(request)
    upload(bounded_call, matrix, plan['mask'])
    ack(bounded_call({'op': 'fit', 'sweeps': sweeps}))
    offset = means(matrix, plan['mask'])
    row_losses, mean_losses, copy_losses, audit_losses = [], [], [], []
    transcript = []
    for row, target in enumerate(plan['targets']):
        check_deadline(deadline)
        available = sorted(set(np.flatnonzero(plan['target_mask'][row]).tolist()) - set(plan['audit']))
        maximum = plan['checkpoints'][-1]
        response = bounded_call({'op': 'row_start', 'row': 'r' + str(row), 'available': available,
                                 'k_max': maximum, 'checkpoints': plan['checkpoints']})
        selected = []
        pending, unused = parse_step(response, available, selected, len(target), False, False)
        checkpoints, mean_points, copy_points, common = [], [], [], []
        for count in range(1, maximum + 1):
            check_deadline(deadline)
            selected.append(pending)
            response = bounded_call({'op': 'observe', 'column': pending, 'value': float(target[pending])})
            checkpoint = count in plan['checkpoints']
            pending, prediction = parse_step(response, available, selected, len(target), checkpoint, count == maximum)
            if checkpoint:
                loss, audit = losses(prediction, target, plan['target_mask'][row], selected, plan['audit'])
                mean_loss, mean_audit = losses(offset, target, plan['target_mask'][row], selected, plan['audit'])
                copied = np.full(len(target), float(np.mean(target[selected])))
                copy_loss, copy_audit = losses(copied, target, plan['target_mask'][row], selected, plan['audit'])
                if not np.all(copied == copied[0]):
                    raise ValueError('copy control implementation failure')
                checkpoints.append(loss)
                mean_points.append(mean_loss)
                copy_points.append(copy_loss)
                common.append(audit)
                transcript.append({'row': row, 'k': count, 'selected': list(selected), 'prediction': prediction.tolist(),
                                   'mae': loss, 'audit_mae': audit, 'mean_mae': mean_loss, 'copy_mae': copy_loss, 'mean_audit_mae': mean_audit, 'copy_audit_mae': copy_audit})
        weight = [1 / len(checkpoints)] * len(checkpoints)
        row_losses.append(fixed_weight_score(checkpoints, weight))
        mean_losses.append(fixed_weight_score(mean_points, weight))
        copy_losses.append(fixed_weight_score(copy_points, weight))
        audit_losses.append(fixed_weight_score(common, weight))
    return {'losses': [aggregate_rows(row_losses, plan), aggregate_rows(mean_losses, plan), aggregate_rows(copy_losses, plan)],
            'audit': aggregate_rows(audit_losses, plan), 'transcript': transcript}


def replay_equal(first, replay):
    if first is None or replay is None or len(first) != len(replay):
        return False
    for left, right in zip(first, replay):
        if left['selected'] != right['selected'] or left['k'] != right['k'] or left['row'] != right['row']:
            return False
        if not np.allclose(left['prediction'], right['prediction'], rtol=0, atol=1e-6):
            return False
    return True


def worst_case(episode):
    return {'losses': [1.] * 5, 'audit': 1., 'baseline_audit': [1., 1.], 'transcript': None, 'baseline_records': None, 'complete': False, 'duration': 0.}


def record_failure(failure):
    if PLANE != 'search':
        return
    component = bounded_failure_name(failure.get('component'), 'candidate')
    category = bounded_failure_name(failure.get('category'), 'protocol_failure')
    operation = bounded_failure_name(failure.get('operation'), 'unknown')
    print(f'episode_failure component={component} category={category} operation={operation}', file=sys.stderr, flush=True)


def plane_metrics(outcomes, episodes, complete):
    original = [value for value, episode in zip(outcomes, episodes) if episode['arm'] == 'original' and not episode['replay']]
    permuted = [value for value, episode in zip(outcomes, episodes) if episode['arm'] == 'permuted']
    weight = [1 / len(original)] * len(original)
    baseline_losses = [fixed_weight_score([value['losses'][index] for value in original], weight) for index in range(5)]
    permutation_loss = fixed_weight_score([value['losses'][0] for value in permuted], weight)
    completed = {'constant', 'copy', 'permuted'} if complete and all(value['complete'] for value in outcomes) else set()
    first = outcomes[0]['transcript']
    reproduced = replay_equal(first, outcomes[-1]['transcript'])
    if reproduced:
        completed.add('reset_replay')
    try:
        require_controls(EXPECTED_CONTROLS, completed)
        valid = True
    except ProtocolFailure:
        valid = False
    candidate, historical, copied, random_loss, ridge_loss = baseline_losses
    metrics = dict(zip(METRIC_NAMES, [1 - candidate, candidate, historical, copied, random_loss, ridge_loss,
                                           permutation_loss, permutation_loss - candidate, int(valid)]))
    if not all(type(value) in (int, float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError('invalid metric aggregation')
    return metrics, valid


def make_evidence(outcomes, episodes):
    records = []
    seeds = list(dict.fromkeys(episode['seed'] for episode in episodes))
    for seed in seeds:
        selected = [(outcome, episode) for outcome, episode in zip(outcomes, episodes) if episode['seed'] == seed]
        primary = [outcome['losses'][0] for outcome, episode in selected if episode['arm'] == 'original' and not episode['replay']]
        score = 1 - fixed_weight_score(primary, [1 / len(primary)] * len(primary))
        valid = all(outcome['complete'] for outcome, episode in selected)
        if seed == episodes[0]['seed']:
            valid = valid and replay_equal(outcomes[0]['transcript'], outcomes[-1]['transcript'])
        cases = []
        for outcome, episode in selected:
            plan = episode['plan']
            cases.append({'case': plan['case'], 'arm': episode['arm'], 'replay': episode['replay'],
                          'families': plan['families'], 'losses': outcome['losses'], 'audit_mae': outcome['audit'],
                          'baseline_audit': outcome['baseline_audit'], 'complete': outcome['complete'],
                          'observations': outcome['transcript'], 'baselines': outcome['baseline_records']})
        records.append({'seed': seed, 'score': score, 'correct': bool(valid),
                        'duration_seconds': sum(episode.get('elapsed', 0.) for outcome, episode in selected),
                        'solution': {'cases': cases}})
    return {'schema_version': 1, 'episodes': records}


def write_results(directory, metrics, correct, feasible, evidence=None):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'metrics.json').write_bytes(bounded_json_line(metrics))
    (directory / 'correct.json').write_bytes(bounded_json_line({'correct': bool(correct)}))
    if evidence is not None:
        data = bounded_json_line(evidence, 16 * 1024 * 1024)
        (directory / 'evaluation_evidence.json').write_bytes(data)
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (directory / 'qualification.json').write_bytes(bounded_json_line({'schema_version': 1, 'feasible': bool(feasible)}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    args = parser.parse_args()
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    wall = 120 if smoke else WALL_SECONDS
    startup = 15 if smoke else STARTUP_SECONDS
    hard_deadline = MODULE_START + wall - startup
    finish_reserve = 5 if smoke else 20
    work_seconds = 5 if smoke else WORK_SECONDS
    metrics = dict(zip(METRIC_NAMES, [0., 1., 1., 1., 1., 1., 1., 0., 0]))
    correct, feasible, client, evidence = False, False, None, None
    try:
        for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
            if os.environ.get(name) != '1':
                raise ValueError('evaluator thread policy not initialized')
        profiles = dict(search={'episode_count': 13, 'method_count': 3, 'wall_seconds': 900, 'startup_seconds': 60,
                                'reset_seconds': 4, 'cleanup_seconds': 1, 'finish_seconds': 20, 'work_seconds': 15},
                        final={'episode_count': 13, 'method_count': 3, 'wall_seconds': 1800, 'startup_seconds': 90,
                               'reset_seconds': 4, 'cleanup_seconds': 1, 'finish_seconds': 20, 'work_seconds': 30})
        require_joint_workload_budget(**profiles)
        payload_preflight()
        plans = load_resources(smoke)
        episodes = []
        for plan in plans:
            for arm in ('original', 'permuted'):
                episodes.append({'seed': plan['seed'], 'plan': plan, 'arm': arm, 'replay': False})
        episodes.append(dict(episodes[0], replay=True))
        expected_sequence = SMOKE_RESET_SEQUENCE if smoke else RESET_SEQUENCE
        if [episode['seed'] for episode in episodes] != expected_sequence:
            raise ValueError('declared episode sequence mismatch')
        budget = sum(sum(operation_counts(len(episode['plan']['test']), episode['plan']['checkpoints'][-1]).values()) for episode in episodes)
        if budget > RPC_BUDGET or (not smoke and budget != RPC_BUDGET):
            raise ValueError('operation table budget mismatch')
        client = Candidate(args.program_path, wall, RPC_BUDGET)
        if client.proxy is None:
            if len(ROLE_CORES) < 4:
                raise ValueError('native smoke needs four assigned CPU cores')
            os.sched_setaffinity(0, {ROLE_CORES[0]})
        resource.setrlimit(resource.RLIMIT_AS, (8 * 1024 ** 3, 8 * 1024 ** 3))
        cpu = cpu_limit_seconds(WALL_SECONDS, 1)
        current_soft, current_hard = resource.getrlimit(resource.RLIMIT_CPU)
        if current_hard != resource.RLIM_INFINITY:
            cpu = min(cpu, current_hard)
        role_hard = cpu_limit_seconds(WALL_SECONDS, 3)
        if current_hard != resource.RLIM_INFINITY:
            role_hard = min(role_hard, current_hard)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, role_hard))

        def evaluate(episode, scheduler_call, episode_deadline):
            started = time.monotonic()
            plan = episode['plan']
            matrix = plan['matrix'] if episode['arm'] == 'original' else permute_history(plan['matrix'], plan['mask'], episode['seed'])
            sweeps = 3 if smoke else 30
            primary = None
            operation = 'baseline_worker'
            try:
                random_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_deadline,
                                                           methods_remaining=2, work_seconds=work_seconds, cleanup_seconds=1)
                try:
                    random_result = native_random(plan, matrix, episode['seed'], random_deadline, sweeps)
                except TimeoutError:
                    raise RequiredBaselineFailure('baseline_timeout') from None
                ridge_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_deadline,
                                                          methods_remaining=1, work_seconds=work_seconds, cleanup_seconds=1)
                try:
                    ridge_result = native_ridge(plan, matrix, ridge_deadline)
                except TimeoutError:
                    raise RequiredBaselineFailure('baseline_timeout') from None
                candidate_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=episode_deadline,
                                                              methods_remaining=0, work_seconds=work_seconds, cleanup_seconds=1)
                def candidate_call(request):
                    nonlocal operation
                    operation = request['op']
                    remaining = candidate_deadline - time.monotonic()
                    if remaining <= 0:
                        raise TimeoutError('candidate method deadline')
                    return scheduler_call(request)
                client.method_deadline = candidate_deadline
                value = candidate_rollout(plan, matrix, candidate_call, candidate_deadline, sweeps)
                value.update(losses=value['losses'] + [random_result['loss'], ridge_result['loss']],
                             baseline_audit=[random_result['audit'], ridge_result['audit']],
                             baseline_records={'random_lowrank': random_result['records'], 'greedy_ridge': ridge_result['records']},
                             complete=True, duration=time.monotonic() - started)
                return value
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                primary = error
                if not isinstance(error, RequiredBaselineFailure):
                    error.operation_at_failure = operation
                raise
            finally:
                try:
                    client.stop()
                except (RuntimeError, subprocess.TimeoutExpired) as error:
                    if primary is not None:
                        primary.add_note('secondary cleanup failure')
                    else:
                        raise ProtocolFailure('cleanup_failure') from None

        def failure_log(failure):
            record_failure(failure)
            snapshot = client.snapshot
            if PLANE == 'search' and snapshot is not None and (os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1' or os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'):
                if snapshot['stderr']:
                    print(snapshot['stderr'], file=sys.stderr, end='', flush=True)
                print('worker_capture observed_bytes={} retained_bytes={} truncated={} capture_error={} exit_status={}'.format(
                    snapshot['observed_bytes'], snapshot['retained_bytes'], int(snapshot['truncated']),
                    bounded_failure_name(snapshot['capture_error'], 'none'), client.exit_status), file=sys.stderr, flush=True)

        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline, finish_reserve=finish_reserve,
                                                  reset_timeout=2, episode_overhead=2, rpc_cap=work_seconds,
                                                  clock=time.monotonic, rpc=client.rpc, evaluate=evaluate,
                                                  worst_case=worst_case, record_failure=failure_log)
        complete = complete and client.resets == expected_sequence and time.monotonic() < hard_deadline - finish_reserve
        metrics, correct = plane_metrics(outcomes, episodes, complete)
        feasible = complete and not smoke
        check_deadline(hard_deadline)
        evidence = make_evidence(outcomes, episodes)
        if PLANE == 'search':
            print('search_evidence ' + json.dumps({'episodes': len(episodes), 'complete': complete,
                                                   'audit_mae': [outcome['audit'] for outcome in outcomes],
                                                   'rpc_calls': sum(client.counts.values())}, separators=(',', ':'), allow_nan=False), file=sys.stderr)
    except Exception as error:
        metrics['correct'] = 0
        write_results(Path(args.results_dir), metrics, False, False)
        if PLANE == 'search':
            name = type(error).__name__
            message = str(error)
            if len(message.encode('utf-8', errors='replace')) > 512:
                message = '<message omitted>'
            print(f'evaluator_exception type={name} message={message}', file=sys.stderr, flush=True)
        else:
            print('evaluator_exception type=' + type(error).__name__[:80] + ' message=sealed_failure', file=sys.stderr, flush=True)
        raise SystemExit(1) from None
    finally:
        if client is not None:
            client.close()
    write_results(Path(args.results_dir), metrics, correct, feasible, evidence)


if __name__ == '__main__':
    main()
