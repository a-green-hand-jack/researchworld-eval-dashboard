"""Self-contained evaluator; real-source episode plan and scalar validity, not claim endorsement."""
import argparse
import base64
import collections
import contextlib
import gzip
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
import unicodedata

STARTED = time.monotonic()
PLANE = 'final'
SEEDS = [1009, 1013, 1019]
WALL_SECONDS = 3600
RPC_BUDGET = 2033
WIRE_LIMIT = 64 * 1024 * 1024
MAX_CHUNKS = 32
CHUNK_ROWS = 256
BATCH_ROWS = 128
BASELINES = ['constant', 'copy', 'random_lowrank', 'medoid_ridge', 'selected_ridge']
METRIC_NAMES = ['combined_score', 'mteb_score', 'open_llm_score', 'permuted_score',
                'corruption_gap', 'constant_score', 'copy_score', 'random_lowrank_score',
                'medoid_ridge_score', 'selected_ridge_score', 'reset_replay_ok',
                'failed_episode_fraction', 'control_failure_fraction',
                'paired_gain_ci_low', 'paired_gain_ci_high', 'correct']
for thread_name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[thread_name] = '1'
import numpy as np


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    if len(encoded) >= wire_limit:
        raise ProtocolFailure('wire_limit')
    return encoded


def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError('invalid time allowance')
    return value


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    if finite_budget_seconds(work_seconds) == 0 or type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError('invalid method budget')
    if now + (methods_remaining + 1) * (work_seconds + cleanup_seconds) > episode_deadline:
        raise TimeoutError('insufficient matched method reservations')
    return now + work_seconds


def require_joint_workload_budget():
    for wall, startup, work in ((1800, 180, 8), (3600, 300, 16)):
        required = startup + 30 + 25 * (2 + 6 * (work + 0.05) + 1.5)
        if required > wall:
            raise ValueError('joint workload does not fit')


class ProtocolFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'protocol_failure')
        super().__init__('candidate protocol failed')


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
    for depth in range(8):
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
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        environment[name] = '3'
    return parent_environment.get('TASK_PYTHON', sys.executable), environment


NATIVE_RUNNER = r'''
import base64,ctypes,errno,importlib.util,json,math,os,resource,sys
resource.setrlimit(resource.RLIMIT_AS,(11*1024**3,11*1024**3))
cpu_seconds=math.ceil(float(sys.argv[3])*3)
resource.setrlimit(resource.RLIMIT_CPU,(cpu_seconds,cpu_seconds))
resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:3])
libc=ctypes.CDLL(None,use_errno=True)
class Ruleset(ctypes.Structure):
 _fields_=[('handled_access_fs',ctypes.c_uint64)]
class Beneath(ctypes.Structure):
 _pack_=1
 _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int)]
abi=libc.syscall(444,0,0,1)
if abi<1: raise RuntimeError('Landlock unavailable')
handled=(1<<13)-1
if abi>=2: handled|=1<<13
if abi>=3: handled|=1<<14
rules=Ruleset(handled)
fd=libc.syscall(444,ctypes.byref(rules),ctypes.sizeof(rules),0)
if fd<0: raise RuntimeError('Landlock ruleset failed')
read=(1<<0)|(1<<2)|(1<<3)
for path,rights in [(sys.prefix,read),(sys.base_prefix,read),('/usr',read),('/lib',read),('/lib64',read),(os.getcwd(),read),('/dev/null',(1<<1)|(1<<2)),('/dev/urandom',1<<2)]:
 if not os.path.exists(path): continue
 parent=os.open(path,os.O_PATH|os.O_CLOEXEC)
 rule=Beneath(rights,parent)
 if libc.syscall(445,fd,1,ctypes.byref(rule),0)<0: raise RuntimeError('Landlock path failed')
 os.close(parent)
if libc.prctl(38,1,0,0,0)<0 or libc.syscall(446,fd,0)<0: raise RuntimeError('Landlock enforcement failed')
os.close(fd)
class Filter(ctypes.Structure):
 _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint32)]
class Program(ctypes.Structure):
 _fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(Filter))]
filters=[Filter(0x20,0,0,4),Filter(0x15,1,0,0xc000003e),Filter(0x06,0,0,0x80000000),Filter(0x20,0,0,0)]
for number in (41,42,43,49,50,53,57,58,62,101,129,165,166,200,234,272,297,298,302,304,308,310,311,312,321,323,424,425,426,427,434,438,440):
 filters.extend([Filter(0x15,0,1,number),Filter(0x06,0,0,0x00050000|errno.EPERM)])
filters.extend([Filter(0x15,0,4,56),Filter(0x20,0,0,16),Filter(0x45,1,0,0x10000),Filter(0x06,0,0,0x00050000|errno.EPERM),Filter(0x20,0,0,0),Filter(0x15,0,1,435),Filter(0x06,0,0,0x00050000|errno.ENOSYS),Filter(0x45,0,1,0x40000000),Filter(0x06,0,0,0x00050000|errno.EPERM),Filter(0x06,0,0,0x7fff0000)])
array=(Filter*len(filters))(*filters);program=Program(len(filters),array)
if libc.prctl(22,2,ctypes.byref(program),0,0)<0: raise RuntimeError('Seccomp failed')
def report_worker_exception(error):
 name=type(error).__name__
 if not name.isascii() or not name.isidentifier() or len(name)>80: name='WorkerException'
 try: message=str(error)
 except Exception: message='<exception message unavailable>'
 if len(message)>2048 or len(message.encode('utf-8',errors='replace'))>2048: message='<exception message omitted: too large>'
 print('worker_exception type='+name+'\n'+message,file=sys.stderr,flush=True)
try:
 spec=importlib.util.spec_from_file_location('candidate',sys.argv[1]);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 for line in sys.stdin.buffer:
  if len(line)>=64*1024**2: raise ValueError('request too large')
  response=module.handle(json.loads(line))
  encoded=json.dumps(response,allow_nan=False,separators=(',',':')).encode()+b'\n'
  if len(encoded)>=64*1024**2: raise ValueError('response too large')
  sys.stdout.buffer.write(encoded);sys.stdout.buffer.flush()
except Exception as error:
 if sys.argv[2]=='repair':
  report_worker_exception(error)
 else: print('candidate_worker_failure',file=sys.stderr,flush=True)
 sys.exit(1)
'''


@contextlib.contextmanager
def timed(deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError()
    def expired(signum, frame):
        raise TimeoutError()
    previous = signal.signal(signal.SIGALRM, expired)
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    began = time.monotonic()
    if previous_timer[0] > 0:
        remaining = min(remaining, previous_timer[0])
    signal.setitimer(signal.ITIMER_REAL, remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        if previous_timer[0] > 0:
            signal.setitimer(signal.ITIMER_REAL, max(.000001, previous_timer[0] - (time.monotonic() - began)), previous_timer[1])


class RPC:
    def __init__(self, path):
        socket = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        proxy = str(path) == '/broker-code/candidate_proxy.py'
        if bool(socket) != proxy:
            raise ValueError('broker requires both trusted signals')
        self.proxy = None
        self.path = path
        self.process = None
        self.directory = None
        self.capture = None
        self.calls = 0
        self.resets = []
        self.failure = None
        self.failure_operation = None
        if proxy:
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy', path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle

    def _start(self):
        self.directory = tempfile.TemporaryDirectory(prefix='score-candidate-')
        copied = Path(self.directory.name) / 'program.py'
        shutil.copyfile(self.path, copied, follow_symlinks=False)
        interpreter, environment = candidate_subprocess_settings(os.environ)
        repair = PLANE == 'search' and (os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1' or
                                        os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1')
        self.process = subprocess.Popen([interpreter, '-I', '-u', '-c', NATIVE_RUNNER,
                                         str(copied), 'repair' if repair else 'sealed', str(WALL_SECONDS)],
                                        cwd=self.directory.name, env=environment, shell=False,
                                        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, start_new_session=True, bufsize=0)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdout.fileno(), False)
        os.set_blocking(self.process.stdin.fileno(), False)
        self.buffer = bytearray()

    def close(self):
        if self.process is not None:
            process = self.process
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=.4)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=.4)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            snapshot = self.capture.close()
            if self.failure is not None and PLANE == 'search' and (
                    os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1' or
                    os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1'):
                print('worker_capture component=candidate category=' + self.failure +
                      ' operation=' + bounded_failure_name(self.failure_operation, 'unknown') +
                      ' exit_status=' + str(process.returncode) +
                      ' observed_bytes=' + str(snapshot['observed_bytes']) +
                      ' retained_bytes=' + str(snapshot['retained_bytes']) +
                      ' truncated=' + str(int(snapshot['truncated'])) +
                      ' capture_error=' + bounded_failure_name(snapshot['capture_error'], 'none'), file=sys.stderr)
                if snapshot['stderr']:
                    print(snapshot['stderr'], file=sys.stderr, end='')
            process.stdin.close()
            process.stdout.close()
            self.process = None
            self.capture = None
        if self.directory is not None:
            self.directory.cleanup()
            self.directory = None
        self.failure = None
        self.failure_operation = None

    def call(self, request, timeout):
        if self.calls >= RPC_BUDGET:
            raise ProtocolFailure('rpc_budget')
        self.calls += 1
        encoded = bounded_json_line(request)
        if request['op'] == 'reset':
            self.resets.append(request['seed'])
        deadline = time.monotonic() + timeout
        try:
            if self.proxy is not None:
                with timed(deadline):
                    response = self.proxy(request)
                bounded_json_line(response)
                return response
            if request['op'] == 'reset':
                self.close()
            if self.process is None:
                self._start()
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin, selectors.EVENT_WRITE)
                sent = 0
                while sent < len(encoded):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    try:
                        sent += os.write(self.process.stdin.fileno(), encoded[sent:sent + 65536])
                    except BlockingIOError:
                        continue
                selector.unregister(self.process.stdin)
                selector.register(self.process.stdout, selectors.EVENT_READ)
                while b'\n' not in self.buffer:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise TimeoutError()
                    try:
                        chunk = os.read(self.process.stdout.fileno(), 65536)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        raise ProtocolFailure('candidate_exit')
                    self.buffer.extend(chunk)
                    if len(self.buffer) >= WIRE_LIMIT:
                        raise ProtocolFailure('wire_limit')
                line, separator, remainder = self.buffer.partition(b'\n')
                self.buffer = bytearray(remainder)
                try:
                    response = json.loads(line, object_pairs_hook=unique_json_pairs,
                                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                except (ValueError, UnicodeError):
                    raise ProtocolFailure('malformed_json') from None
                bounded_json_line(response)
                return response
        except BrokenPipeError:
            self.failure = 'candidate_exit'
            self.failure_operation = request['op']
            raise ProtocolFailure('candidate_exit') from None
        except (TimeoutError, ProtocolFailure) as error:
            self.failure = 'timeout' if isinstance(error, TimeoutError) else error.category
            self.failure_operation = request['op']
            raise


def unique_json_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolFailure('duplicate_json_key')
        result[key] = value
    return result


def record_failure(failure):
    if PLANE == 'search':
        print(('episode_failure component=' + bounded_failure_name(failure['component'], 'unknown') +
               ' category=' + bounded_failure_name(failure['category'], 'unknown') +
               ' operation=' + bounded_failure_name(failure['operation'], 'unknown'))[:256], file=sys.stderr)


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete = True
    for index, episode in enumerate(episodes):
        episode_started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = min(episode_deadline - episode_overhead, clock() + episode['allowance'])
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
            outcomes[index]['duration'] = max(0., clock() - episode_started)
            record_failure(failure)
    return outcomes, complete


def canonical_hash(value):
    normalized = ' '.join(unicodedata.normalize('NFKC', json.dumps(value, sort_keys=True,
                         ensure_ascii=False, allow_nan=False, separators=(',', ':'))).split())
    return hashlib.sha256(normalized.encode()).hexdigest()


def load_resources():
    root = Path(os.environ.get('TASK_SOURCE_DIR', str(Path(__file__).resolve().parent))) / 'resources' / PLANE
    with gzip.open(root / 'pool.json.gz', 'rt', encoding='utf-8') as stream:
        pool = json.load(stream)
    audit = json.loads((root / 'audit.json').read_text())
    plan = json.loads((root / 'plan.json').read_text())
    if pool['schema_version'] != 1 or any(audit['cross_plane_intersections'].values()):
        raise ValueError('invalid disjointness audit')
    for row in pool['rows']:
        if canonical_hash({'source_schema': row['source'], 'scores': row['scores']}) != row['example_hash']:
            raise ValueError('example integrity failure')
    own = {'examples': {row['example_hash'] for row in pool['rows']},
           'documents': {item['doc_hash'] for row in pool['rows'] for item in row['provenance']},
           'ids': {' '.join(unicodedata.normalize('NFKC', row['id']).split()).lower().replace('__', '/') for row in pool['rows']},
           'families': {row['family'] for row in pool['rows']}}
    if {key: len(value) for key, value in own.items()} != audit['own_counts']:
        raise ValueError('manifest integrity failure')
    return pool['rows'], plan


def normalized_model_id(identifier):
    return ' '.join(unicodedata.normalize('NFKC', identifier).split()).lower().replace('__', '/')


def split_components(rows, split):
    if split not in ('model', 'family'):
        raise ValueError('invalid split')
    parents = list(range(len(rows)))
    def root(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index
    owners = {}
    for index, row in enumerate(rows):
        links = [('alias', normalized_model_id(row['id'])), ('example', row['example_hash'])]
        links.extend(('document', item['doc_hash']) for item in row['provenance'])
        if split == 'family':
            links.append(('family', row['family']))
        for link in links:
            if link in owners:
                parents[root(index)] = root(owners[link])
            else:
                owners[link] = index
    groups = collections.defaultdict(set)
    names = collections.defaultdict(list)
    for index, row in enumerate(rows):
        component = root(index)
        groups[component].add(row['group'])
        names[component].append(row['source'] + '/' + row['id'])
    if any(len(group) != 1 for group in groups.values()):
        raise ValueError('supplied group fragments a connected component')
    labels = {component: min(members) for component, members in names.items()}
    return [labels[root(index)] for index in range(len(rows))]


def require_disjoint_rows(train, test, split):
    def identities(roster):
        result = {
            'aliases': {normalized_model_id(row['id']) for row in roster},
            'examples': {row['example_hash'] for row in roster},
            'documents': {item['doc_hash'] for row in roster for item in row['provenance']},
        }
        if split == 'family':
            result['families'] = {row['family'] for row in roster}
        return result
    historical, held_out = identities(train), identities(test)
    if any(historical[key] & held_out[key] for key in historical):
        raise ValueError('historical/test normalized content or group overlap')


def build_case(rows, source, split, seed, smoke):
    components = split_components(rows, split)
    source_rows = [(row, component) for row, component in zip(rows, components) if row['source'] == source]
    keys = sorted({component for row, component in source_rows})
    random = np.random.default_rng(seed)
    random.shuffle(keys)
    historical = set(keys[:max(1, int(.7 * len(keys)))])
    train = [row for row, component in source_rows if component in historical]
    test = [row for row, component in source_rows if component not in historical]
    require_disjoint_rows(train, test, split)
    coverage = collections.Counter(column for row in train for column in row['scores'])
    if source == 'mteb':
        columns = sorted(column for column, count in coverage.items() if count >= 20)
        checkpoints = [1, 2, 4, 8]
        minimum = 9
        if len(columns) < 12:
            raise ValueError('insufficient real MTEB historical support')
    else:
        columns = ['IFEval Raw', 'BBH Raw', 'MATH Lvl 5 Raw', 'GPQA Raw', 'MUSR Raw', 'MMLU-PRO Raw']
        checkpoints = [1, 2, 3]
        minimum = 4
    if smoke:
        if source == 'mteb':
            columns = sorted(sorted(columns, key=lambda column: (-coverage[column], column))[:12])
        train = sorted(train, key=lambda row: (-sum(column in row['scores'] for column in columns), row['id']))[:32]
    test = [row for row in test if sum(column in row['scores'] for column in columns) >= minimum]
    if smoke:
        test = test[:4]
    if not train or not test or len(train) > 8192 or len(columns) > 1024:
        raise ValueError('unsupported real-source case shape')
    def array(roster):
        mask = np.array([[column in row['scores'] for column in columns] for row in roster], dtype=bool)
        values = np.array([[row['scores'].get(column, 0.0) for column in columns] for row in roster], dtype='<f8')
        return values, mask
    values, mask = array(train)
    targets, available = array(test)
    return {'values': values, 'mask': mask, 'targets': targets, 'available': available,
            'columns': columns, 'checkpoints': checkpoints, 'families': [row['family'] for row in test],
            'roster_hash': canonical_hash({'train': [row['id'] for row in train], 'test': [row['id'] for row in test], 'columns': columns})}


def permute_training(values, mask, seed):
    transformed = values.copy()
    random = np.random.default_rng(seed + 7919)
    altered = 0
    permutations = []
    disrupted = False
    for column in range(values.shape[1]):
        indices = np.flatnonzero(mask[:, column])
        original = values[indices, column]
        if len(indices) < 2 or np.ptp(original) == 0:
            continue
        order = random.permutation(len(indices))
        shift = int(random.integers(1, len(indices)))
        source_indices = np.empty(len(indices), dtype=int)
        source_indices[order] = np.roll(order, shift)
        transformed[indices, column] = original[source_indices]
        if np.array_equal(transformed[indices, column], original):
            transformed[indices, column] = np.roll(original, 1)
            source_indices = np.roll(np.arange(len(indices)), 1)
        if np.array_equal(transformed[indices, column], original):
            raise ProtocolFailure('vacuous_control')
        correspondence = np.full(len(values), -1, dtype=int)
        correspondence[indices] = indices[source_indices]
        for previous in permutations:
            common = (previous >= 0) & (correspondence >= 0)
            if common.sum() >= 2 and np.any(previous[common] != correspondence[common]):
                disrupted = True
        permutations.append(correspondence)
        altered += 1
    if altered < 2 or not disrupted or np.array_equal(transformed, values):
        raise ProtocolFailure('vacuous_control')
    return transformed


def ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise ProtocolFailure('malformed_ack')


def upload_request(values, mask, offset):
    chunk = np.ascontiguousarray(values[offset:offset + CHUNK_ROWS], dtype='<f8')
    flags = np.ascontiguousarray(mask[offset:offset + CHUNK_ROWS], dtype='u1')
    return {'op': 'train_chunk', 'offset': offset, 'shape': list(chunk.shape), 'dtype': '<f8',
            'encoding': 'base64', 'data': base64.b64encode(chunk.tobytes()).decode('ascii'),
            'mask_dtype': '|u1', 'mask': base64.b64encode(flags.tobytes()).decode('ascii')}


def check_deadline(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError()


def factor_fit(values, mask, rank, steps, deadline):
    mean = np.sum(values * mask, axis=0) / np.maximum(mask.sum(axis=0), 1)
    centered = values - mean
    with timed(deadline):
        _, singular, right = np.linalg.svd(np.where(mask, centered, 0.0), full_matrices=False)
    factors = right[:rank].T * np.sqrt(np.maximum(singular[:rank], 1e-8))
    latent = np.zeros((len(values), rank))
    regularizer = np.eye(rank) * .1
    for sweep in range(steps):
        check_deadline(deadline)
        for row in range(len(values)):
            selected = factors[mask[row]]
            latent[row] = np.linalg.solve(selected.T @ selected + regularizer,
                                          selected.T @ centered[row, mask[row]])
        for column in range(values.shape[1]):
            selected = latent[mask[:, column]]
            factors[column] = np.linalg.solve(selected.T @ selected + regularizer,
                                              selected.T @ centered[mask[:, column], column])
    return mean, factors


def reference_fit(values, mask, steps, seed, deadline):
    random = np.random.default_rng(seed)
    validation = (random.random(mask.shape) < .1) & mask
    fitting = mask & ~validation
    best = None
    for rank in (1, 2, 4, 8):
        if rank > min(values.shape) - 1:
            continue
        mean, factors = factor_fit(values, fitting, rank, min(steps, 4), deadline)
        losses = []
        for row in range(len(values)):
            selected = factors[fitting[row]]
            latent = np.linalg.solve(selected.T @ selected + np.eye(rank) * .1,
                                     selected.T @ (values[row, fitting[row]] - mean[fitting[row]]))
            losses.extend(np.abs((mean + factors @ latent - values[row])[validation[row]]))
        loss = float(np.mean(losses)) if losses else 1.0
        if best is None or loss < best[0]:
            best = (loss, rank)
    return factor_fit(values, mask, best[1], min(steps, 8), deadline)


def predict_factors(mean, factors, queried, observations):
    selected = factors[queried]
    latent = np.linalg.solve(selected.T @ selected + np.eye(factors.shape[1]) * .1,
                             selected.T @ (observations - mean[queried]))
    return mean + factors @ latent


def curve_score(predictions, targets, available, queried):
    remaining = available & ~queried
    errors = np.abs(np.clip(predictions, 0, 1) - targets)
    return 1 - (errors * remaining).sum(axis=1) / remaining.sum(axis=1)


def run_baseline(name, case, seed, steps, deadline):
    values, mask = case['values'], case['mask']
    targets, available = case['targets'], case['available']
    mean = np.sum(values * mask, axis=0) / np.maximum(mask.sum(axis=0), 1)
    factors = None
    covariance = None
    ridge = .1
    if name == 'random_lowrank':
        mean, factors = reference_fit(values, mask, steps, seed, deadline)
    if name in ('medoid_ridge', 'selected_ridge'):
        centered = np.where(mask, values - mean, 0.0)
        covariance = centered.T @ centered / max(1, len(values) - 1)
        validation_rows = np.arange(len(values)) % 5 == 0
        fitting = ~validation_rows
        training_mean = np.sum(values[fitting] * mask[fitting], axis=0) / np.maximum(mask[fitting].sum(axis=0), 1)
        centered_train = np.where(mask[fitting], values[fitting] - training_mean, 0.0)
        training_covariance = centered_train.T @ centered_train / max(1, fitting.sum() - 1)
        losses = []
        for penalty in (.01, .1, 1.0):
            residuals = []
            for row in np.flatnonzero(validation_rows):
                present = np.flatnonzero(mask[row])
                if len(present) < 2:
                    continue
                selected = present[:1]
                prediction = training_mean + training_covariance[:, selected] @ np.linalg.solve(
                    training_covariance[np.ix_(selected, selected)] + np.eye(len(selected)) * penalty,
                    values[row, selected] - training_mean[selected])
                residuals.extend(np.abs(prediction[present[1:]] - values[row, present[1:]]))
            losses.append(float(np.mean(residuals)) if residuals else 1.)
        ridge = (.01, .1, 1.0)[int(np.argmin(losses))]
        deviation = np.sqrt(np.maximum(np.diag(covariance), 1e-12))
        correlation = covariance / np.outer(deviation, deviation)
        medoid_order = np.argsort(-np.sum(np.abs(correlation), axis=1), kind='stable')
    random = np.random.default_rng(seed)
    queried = np.zeros_like(available)
    checkpoints = []
    for step in range(1, max(case['checkpoints']) + 1):
        check_deadline(deadline)
        predictions = np.tile(mean, (len(targets), 1))
        for row in range(len(targets)):
            legal = np.flatnonzero(available[row] & ~queried[row])
            if name == 'medoid_ridge':
                column = next(int(column) for column in medoid_order if column in legal)
            elif name == 'selected_ridge':
                selected = np.flatnonzero(queried[row])
                conditional = covariance.copy()
                if len(selected):
                    conditional -= covariance[:, selected] @ np.linalg.solve(
                        covariance[np.ix_(selected, selected)] + np.eye(len(selected)) * ridge,
                        covariance[selected, :])
                reduction = np.sum(conditional[np.ix_(legal, legal)] ** 2, axis=0) / (np.diag(conditional)[legal] + ridge)
                column = int(legal[np.argmax(reduction)])
            else:
                column = int(random.choice(legal))
            queried[row, column] = True
            selected = np.flatnonzero(queried[row])
            observations = targets[row, selected]
            if name == 'copy':
                predictions[row] += float(np.mean(observations - mean[selected]))
            elif name == 'random_lowrank':
                predictions[row] = predict_factors(mean, factors, selected, observations)
            elif covariance is not None:
                predictions[row] += covariance[:, selected] @ np.linalg.solve(
                    covariance[np.ix_(selected, selected)] + np.eye(len(selected)) * ridge,
                    observations - mean[selected])
        if step in case['checkpoints']:
            checkpoints.append(curve_score(predictions, targets, available, queried))
    scores = np.mean(checkpoints, axis=0)
    if not np.isfinite(scores).all():
        raise RequiredBaselineFailure('baseline_result_failure')
    return {'score': float(scores.mean()), 'rows': scores.tolist(),
            'curve': [float(np.mean(checkpoint)) for checkpoint in checkpoints]}


def run_candidate(case, call, steps):
    values, mask = case['values'], case['mask']
    ack(call({'op': 'train_start', 'rows': len(values), 'columns': values.shape[1],
              'column_names': case['columns'], 'training_steps': steps,
              'max_queries': max(case['checkpoints'])}))
    for offset in range(0, len(values), CHUNK_ROWS):
        ack(call(upload_request(values, mask, offset)))
    ack(call({'op': 'train_commit'}))
    ack(call({'op': 'fit'}))
    batch_scores, curves, trace = [], [], []
    for offset in range(0, len(case['targets']), BATCH_ROWS):
        targets = case['targets'][offset:offset + BATCH_ROWS]
        available = case['available'][offset:offset + BATCH_ROWS]
        queried = np.zeros_like(available)
        ack(call({'op': 'start', 'availability': available.tolist(), 'max_queries': max(case['checkpoints'])}))
        checkpoints = []
        batch_trace = []
        for step in range(1, max(case['checkpoints']) + 1):
            response = call({'op': 'select'})
            if type(response) is not dict or set(response) != {'indices'}:
                raise ProtocolFailure('malformed_selection')
            indices = response['indices']
            if type(indices) is not list or len(indices) != len(targets):
                raise ProtocolFailure('malformed_selection')
            for row, column in enumerate(indices):
                if type(column) is not int or not 0 <= column < values.shape[1] or not available[row, column] or queried[row, column]:
                    raise ProtocolFailure('illegal_query')
                queried[row, column] = True
            observations = [float(targets[row, column]) for row, column in enumerate(indices)]
            ack(call({'op': 'observe', 'indices': indices, 'values': observations}))
            batch_trace.append({'step': step, 'indices': indices})
            if step in case['checkpoints']:
                response = call({'op': 'predict'})
                if type(response) is not dict or set(response) != {'predictions'}:
                    raise ProtocolFailure('malformed_prediction')
                raw = response['predictions']
                if type(raw) is not list or len(raw) != len(targets) or any(
                        type(row) is not list or len(row) != values.shape[1] or
                        any(type(value) not in (int, float) for value in row) for row in raw):
                    raise ProtocolFailure('malformed_prediction')
                try:
                    predictions = np.array(raw, dtype=np.float64)
                except (OverflowError, ValueError):
                    raise ProtocolFailure('nonfinite_prediction') from None
                if not np.isfinite(predictions).all():
                    raise ProtocolFailure('nonfinite_prediction')
                checkpoints.append(curve_score(predictions, targets, available, queried))
                batch_trace[-1]['predictions'] = np.clip(predictions, 0, 1)
        batch_scores.extend(np.mean(checkpoints, axis=0).tolist())
        curves.append(np.array(checkpoints))
        trace.append(batch_trace)
    curve = np.concatenate(curves, axis=1).mean(axis=1).tolist()
    return {'score': float(np.mean(batch_scores)), 'rows': batch_scores, 'curve': curve, 'trace': trace}


def same_trace(left, right):
    if len(left) != len(right):
        return False
    for first, second in zip(left, right):
        if len(first) != len(second):
            return False
        for before, after in zip(first, second):
            if before['indices'] != after['indices'] or before['step'] != after['step']:
                return False
            if 'predictions' in before and not np.allclose(before['predictions'], after['predictions'], rtol=0, atol=1e-10):
                return False
    return True


def worst_case(episode):
    return {'score': 0., 'ok': False, 'duration': 0., 'baselines': {name: {'score': 0., 'rows': [], 'curve': []} for name in BASELINES},
            'rows': [], 'curve': [], 'families': [], 'trace': []}


def bootstrap_gain(episodes, outcomes, seeds):
    primary = [(episode, outcome) for episode, outcome in zip(episodes, outcomes) if not episode['control'] and not episode['replay']]
    if any(not outcome['ok'] for episode, outcome in primary):
        return -1., 1.
    random = np.random.default_rng(24681357)
    family_sets = {source: sorted({family for episode, outcome in primary if episode['source'] == source for family in outcome['families']})
                   for source in ('mteb', 'open_llm')}
    samples = []
    for draw in range(200):
        source_values = []
        for source in ('mteb', 'open_llm'):
            families = family_sets[source]
            counts = collections.Counter(random.choice(families, size=len(families), replace=True).tolist())
            contributions = []
            for episode, outcome in primary:
                if episode['source'] != source:
                    continue
                weights = np.array([counts[family] for family in outcome['families']], dtype=float)
                gains = np.array(outcome['rows']) - np.array(outcome['baselines']['random_lowrank']['rows'])
                contributions.append(float(np.dot(gains, weights) / weights.sum()) if weights.sum() else 0.)
            source_values.append(float(np.mean(contributions)))
        samples.append(float(np.mean(source_values)))
    low, high = np.quantile(samples, [.025, .975])
    return float(low), float(high)


def aggregate(episodes, outcomes, replay_ok, seeds):
    actual = [outcome for episode, outcome in zip(episodes, outcomes) if not episode['control'] and not episode['replay']]
    controls = [outcome for episode, outcome in zip(episodes, outcomes) if episode['control'] and not episode['replay']]
    metrics = {name: 0. for name in METRIC_NAMES}
    metrics['combined_score'] = float(np.mean([outcome['score'] for outcome in actual]))
    metrics['permuted_score'] = float(np.mean([outcome['score'] for outcome in controls]))
    for source in ('mteb', 'open_llm'):
        metrics[source + '_score'] = float(np.mean([outcome['score'] for episode, outcome in zip(episodes, outcomes)
                                                   if episode['source'] == source and not episode['control'] and not episode['replay']]))
    for name in BASELINES:
        metrics[name + '_score'] = float(np.mean([outcome['baselines'][name]['score'] for outcome in actual]))
    metrics['corruption_gap'] = float(np.mean([before['score'] - after['score'] if before['ok'] and after['ok'] else -1.
                                              for before, after in zip(actual, controls)]))
    metrics['reset_replay_ok'] = float(replay_ok)
    metrics['failed_episode_fraction'] = sum(not outcome['ok'] for outcome in outcomes) / len(outcomes)
    metrics['control_failure_fraction'] = (sum(not outcome['ok'] for outcome in controls) + int(not replay_ok)) / (len(controls) + 1)
    metrics['paired_gain_ci_low'], metrics['paired_gain_ci_high'] = bootstrap_gain(episodes, outcomes, seeds)
    metrics['correct'] = float(all(outcome['ok'] for outcome in outcomes) and replay_ok)
    if not all(type(value) in (int, float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError('nonfinite aggregate')
    return metrics


def empty_metrics():
    metrics = {name: 0. for name in METRIC_NAMES}
    metrics.update(corruption_gap=-1., failed_episode_fraction=1., control_failure_fraction=1.,
                   paired_gain_ci_low=-1., paired_gain_ci_high=1.)
    return metrics


def write_results(directory, metrics, feasible, evidence=None):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'metrics.json').write_bytes(bounded_json_line(metrics))
    (directory / 'correct.json').write_bytes(bounded_json_line({'correct': bool(metrics['correct'])}))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1':
        (directory / 'qualification.json').write_bytes(bounded_json_line({'schema_version': 1, 'feasible': bool(feasible)}))
    if evidence is not None:
        encoded = bounded_json_line(evidence)
        if len(encoded) <= 16 * 1024 * 1024:
            (directory / 'evaluation_evidence.json').write_bytes(encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path', required=True)
    parser.add_argument('--results_dir', required=True)
    arguments = parser.parse_args()
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1'
    ceiling = 120 if smoke else WALL_SECONDS
    hard_deadline = STARTED + ceiling - (5 if smoke else 30)
    metrics = empty_metrics()
    rpc = None
    try:
        require_joint_workload_budget()
        rows, plan = load_resources()
        seeds = SEEDS[:1] if smoke else SEEDS
        episodes = []
        for source in ('mteb', 'open_llm'):
            for split in ('model', 'family'):
                for control in (False, True):
                    for seed in seeds:
                        episodes.append({'source': source, 'split': split, 'seed': seed, 'control': control,
                                         'replay': False, 'allowance': 10 if smoke else (62 if PLANE == 'search' else 124)})
        episodes.append(dict(episodes[0], replay=True))
        expected_resets = [episode['seed'] for episode in episodes]
        profile = plan['smoke' if smoke else 'production']
        if profile['reset_sequence'] != expected_resets or plan['rpc_budget'] != RPC_BUDGET:
            raise ValueError('frozen plan mismatch')
        cache = {}
        first_trace = None
        replay_ok = False
        rpc = RPC(arguments.program_path)
        def evaluate_episode(episode, call, deadline):
            nonlocal first_trace, replay_ok
            began = time.monotonic()
            key = (episode['source'], episode['split'], episode['seed'])
            if key not in cache:
                cache[key] = build_case(rows, *key, smoke)
            case = dict(cache[key])
            roster = profile['cases'][episode['source'] + '/' + episode['split'] + '/' + str(episode['seed'])]
            if case['roster_hash'] != roster['roster_hash']:
                raise ValueError('frozen roster mismatch')
            if episode['control']:
                case['values'] = permute_training(case['values'], case['mask'], episode['seed'])
            steps = 2 if smoke else 100
            work = .9 if smoke else (8 if PLANE == 'search' else 16)
            baselines = {}
            for index, name in enumerate(BASELINES):
                method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                            methods_remaining=5 - index, work_seconds=work,
                                                            cleanup_seconds=.05)
                try:
                    with timed(method_deadline):
                        baselines[name] = run_baseline(name, case, episode['seed'], steps, method_deadline)
                except TimeoutError:
                    raise RequiredBaselineFailure('baseline_timeout') from None
            method_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                        methods_remaining=0, work_seconds=work, cleanup_seconds=.05)
            def bounded_call(request):
                check_deadline(method_deadline)
                with timed(method_deadline):
                    return call(request)
            result = run_candidate(case, bounded_call, steps)
            if episode['replay']:
                replay_ok = first_trace is not None and same_trace(first_trace, result['trace'])
                if not replay_ok:
                    raise ProtocolFailure('reset_replay_mismatch')
            elif key == ('mteb', 'model', seeds[0]) and not episode['control']:
                first_trace = result['trace']
            result.update(ok=True, baselines=baselines, families=case['families'], duration=time.monotonic() - began)
            return result
        def episode_failure(failure):
            if failure['component'] == 'candidate':
                rpc.failure = failure['category']
                rpc.failure_operation = failure['operation']
            record_failure(failure)
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=5, reset_timeout=2,
            episode_overhead=1.5, rpc_cap=60 if not smoke else 5, clock=time.monotonic,
            rpc=rpc.call, evaluate=evaluate_episode, worst_case=worst_case, record_failure=episode_failure)
        reset_ok = rpc.resets == expected_resets
        rpc.close()
        metrics = aggregate(episodes, outcomes, replay_ok, seeds)
        metrics['correct'] = float(bool(metrics['correct']) and complete and reset_ok and time.monotonic() <= hard_deadline)
        evidence = {'schema_version': 1, 'episodes': []}
        for seed in seeds:
            selected = [(episode, outcome) for episode, outcome in zip(episodes, outcomes) if episode['seed'] == seed]
            actual = [outcome for episode, outcome in selected if not episode['control'] and not episode['replay']]
            evidence['episodes'].append({'seed': seed, 'score': float(np.mean([outcome['score'] for outcome in actual])),
                                         'correct': bool(all(outcome['ok'] for episode, outcome in selected)),
                                         'duration_seconds': sum(outcome['duration'] for episode, outcome in selected),
                                         'solution': {'cases': [{'source': episode['source'], 'split': episode['split'],
                                                                'control': episode['control'], 'replay': episode['replay'],
                                                                'score': outcome['score'], 'completed': outcome['ok'],
                                                                'curve': outcome['curve'],
                                                                'baselines': {name: outcome['baselines'][name]['score'] for name in BASELINES}}
                                                               for episode, outcome in selected]}})
        feasible = complete and reset_ok and not smoke and time.monotonic() <= hard_deadline
        write_results(Path(arguments.results_dir), metrics, feasible, evidence)
    except Exception as error:
        metrics = empty_metrics()
        write_results(Path(arguments.results_dir), metrics, False)
        name = bounded_failure_name(type(error).__name__.lower(), 'evaluator_error')
        print('evaluator_exception type=' + name + ' message=evaluation_incomplete', file=sys.stderr)
        return 1
    finally:
        if rpc is not None:
            rpc.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
