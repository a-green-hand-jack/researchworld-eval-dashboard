"""Standalone CPU ranking sensitivity evaluator; no candidate self-report scoring."""
import argparse
import base64
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
import time

for thread_name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[thread_name] = '2'
import numpy as np
from scipy import sparse
from scipy.optimize import minimize
from scipy.special import expit

CHUNK = 8*1024*1024
CALLS_PER_EPISODE = 23
RIDGE = 0.001
FRACTIONS = [0.001,0.005,0.01]

PLANE = 'search'
SEEDS = [101, 307]
WALL = 7200

class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


def bounded_failure_name(value, fallback):
    import re
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


def describe_episode_failure(error, operation):
    # A finally-block cleanup exception may wrap the original required-worker failure.
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response",
                    "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category,
                    "operation": "baseline_worker"}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout",
            "operation": bounded_failure_name(operation, "unknown")}



def fail_required_baseline(category, cancel_work, record_failure):
    failure = RequiredBaselineFailure(category)
    try:
        record_failure(failure.category)
    except Exception:
        failure.add_note("baseline diagnostic recording failed")
    try:
        cancel_work()
    except Exception:
        failure.add_note("baseline cleanup failed")
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
        category = "baseline_timeout" if isinstance(error, TimeoutError) else "baseline_result_failure"
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


import collections
import os
import selectors
import sys
import threading


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
        self.reader = threading.Thread(target=self._drain, name="worker-stderr-reader")
        self.reader.start()

    def _accept(self, chunk):
        self.observed_bytes += len(chunk)
        for segment in chunk.splitlines(keepends=True):
            # Only LF ends a diagnostic line. splitlines also splits CR; accumulate it.
            complete = segment.endswith(b"\n")
            if not self.dropping_line:
                if len(self.pending) + len(segment) > self.LIMIT:
                    self.pending.clear()
                    self.dropping_line = True
                    self.truncated = True
                else:
                    self.pending.extend(segment)
            if complete:
                if not self.dropping_line:
                    line = bytes(self.pending).decode("utf-8", errors="replace")
                    size = len(line.encode("utf-8"))
                    if size <= self.LIMIT:
                        while self.retained_bytes + size > self.LIMIT:
                            self.retained_bytes -= len(self.lines.popleft().encode("utf-8"))
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
                self.capture_error = "reader_stopped_before_eof"
                self.truncated = True
        except (OSError, ValueError):
            self.capture_error = "stderr_capture_failed"
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
            # Do not close a stream concurrently with its owner or claim cleanup passed.
            raise RuntimeError("stderr reader cleanup unresolved")
        self.result = {
            "stderr": "".join(self.lines),
            "observed_bytes": self.observed_bytes,
            "retained_bytes": self.retained_bytes,
            "truncated": self.truncated,
            "capture_error": self.capture_error,
        }
        return dict(self.result)


def report_worker_exception(error):
    # Search-only entry point; the host sanitizes this untrusted diagnostic later.
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = "WorkerException"
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    # Drop an oversized message whole; never retain a potentially split credential.
    if len(message) > 2048 or len(message.encode("utf-8", errors="replace")) > 2048:
        message = "<exception message omitted: too large>"
    print(f"worker_exception type={name}\n{message}", file=sys.stderr, flush=True)


def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        episode_started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead

        current_operation = "reset"
        primary_failure = None

        def call(request):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
        finally:
            if isinstance(outcomes[index], dict):
                outcomes[index]['duration'] = max(0., clock() - episode_started)
    return outcomes, complete


def candidate_subprocess_settings(parent_environment):
    import sys

    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
    environment = {
        name: parent_environment[name]
        for name in runtime_names
        if name in parent_environment
    }
    environment.update(
        HOME="/nonexistent",
        PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONUNBUFFERED="1",
    )
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


def finite_budget_seconds(value):
    import math
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError("work allowance must be positive")
    return value


def require_joint_workload_budget(*, search, final):
    required = {}
    for plane, profile in (("search", search), ("final", final)):
        episodes, methods = profile["episode_count"], profile["method_count"]
        if any(type(count) is not int or count <= 0 for count in (episodes, methods)):
            raise ValueError("invalid episode or method count")
        times = {name: finite_budget_seconds(profile[name]) for name in (
            "wall_seconds", "startup_seconds", "reset_seconds", "cleanup_seconds", "finish_seconds"
        )}
        work = positive_work_seconds(profile["work_seconds"])
        needed = (times["startup_seconds"] + times["finish_seconds"]
                  + episodes * (times["reset_seconds"] + methods * (work + times["cleanup_seconds"])))
        finite_budget_seconds(needed)
        if needed > times["wall_seconds"]:
            raise ValueError(f"{plane} productive work exceeds the declared wall budget")
        required[plane] = needed
    return required


def require_productive_baseline(measured_seconds, *, minimum_seconds):
    try:
        measured = positive_work_seconds(measured_seconds)
        minimum = positive_work_seconds(minimum_seconds)
    except ValueError:
        raise ValueError("invalid productive baseline measurement") from None
    if measured < minimum:
        raise ValueError("productive baseline is shorter than its canonical minimum")


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid remaining method count")
    needed = (methods_remaining + 1) * (work + cleanup_seconds)
    if now + needed > episode_deadline:
        raise TimeoutError("insufficient matched method reservations")
    return now + work


class ProtocolError(RuntimeError):
    pass


class ScientificInvalid(ProtocolError):
    pass


_describe_failure = describe_episode_failure


def describe_episode_failure(error, operation):
    if isinstance(error, ScientificInvalid):
        return {'component':'candidate','category':'scientific_invalid','operation':bounded_failure_name(operation,'unknown')}
    if isinstance(error, ProtocolError):
        return {'component':'candidate','category':'invalid_protocol','operation':bounded_failure_name(operation,'unknown')}
    return _describe_failure(error, operation)


def bounded_json_line(value, wire_limit=64*1024*1024):
    try:
        encoded = json.dumps(value,allow_nan=False,separators=(',',':')).encode('utf-8') + b'\n'
    except (ValueError,TypeError,RecursionError) as error:
        raise ProtocolError('invalid finite JSON message') from error
    if len(encoded) >= wire_limit:
        raise ProtocolError('wire size exceeded')
    return encoded


def preflight():
    raw = b'\xff' * CHUNK
    request = {'op':'import_chunk','index':7,'data':base64.b64encode(raw).decode()}
    response = {'data':base64.b64encode(raw).decode()}
    counts = {}
    for name, value in [('request',request),('response',response)]:
        counts[name] = len(bounded_json_line({'id':9223372036854775807,'request' if name=='request' else 'response':value}))
        if counts[name] >= 16*1024*1024:
            raise ValueError('wire preflight exceeded target')
    certificate = {'theta':[-sys.float_info.max]*256,'contender':255,'direction':[-sys.float_info.max]*256,
                   'influence':[-sys.float_info.max]*100000,'deletions':[[9007199254740991]*count for count in (100,500,1000)]}
    logical_output = bounded_json_line(certificate)[:-1]
    metadata = {'op':'import_start','n_rows':100000,'n_players':256,'regularization':RIDGE,'dtype':'<f8',
                'shape':[100000,4],'encoding':'base64','byte_order':'little','nbytes':3200000,'chunks':1}
    counts['metadata'] = len(bounded_json_line({'id':9223372036854775807,'request':metadata}))
    counts['maximum_certificate_logical'] = len(logical_output)
    counts['maximum_certificate_base64'] = 4*math.ceil(len(logical_output)/3)
    bounded_json_line({'id':9223372036854775807,'response':{'data':base64.b64encode(logical_output).decode()}})
    table = {'reset':1,'stale_export_chunk':1,'import_start':1,'import_chunk':8,'import_commit':1,
             'solve':1,'export_start':1,'export_chunk':8,'release':1}
    if sum(table.values()) != CALLS_PER_EPISODE:
        raise ValueError('RPC table mismatch')
    return {'wire_bytes':counts,'operations':table}


WORKER = r'''
import base64, ctypes, errno, importlib.util, json, math, os, resource, sys
root, program, wall = sys.argv[1], sys.argv[2], int(sys.argv[3])
repair = sys.argv[4] == '1'
def report_worker_exception(error):
 name = type(error).__name__
 if not name.isascii() or not name.isidentifier() or len(name)>80: name='WorkerException'
 try: message=str(error)
 except Exception: message='<exception message unavailable>'
 if len(message)>2048 or len(message.encode('utf-8',errors='replace'))>2048: message='<exception message omitted: too large>'
 print('worker_exception type='+name+'\n'+message,file=sys.stderr,flush=True)
os.chdir(root)
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(wall*2,wall*2))
resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024**2,16*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
libc=ctypes.CDLL(None,use_errno=True)
libc.prctl(38,1,0,0,0)
abi=libc.syscall(444,0,0,1)
if abi<1: raise RuntimeError('Landlock unavailable')
handled=(1<<13)-1
if abi>=2: handled|=1<<13
if abi>=3: handled|=1<<14
class Ruleset(ctypes.Structure): _fields_=[('handled',ctypes.c_uint64)]
class PathRule(ctypes.Structure):
 _pack_=1
 _fields_=[('allowed',ctypes.c_uint64),('parent',ctypes.c_int)]
ruleset=Ruleset(handled)
descriptor=libc.syscall(444,ctypes.byref(ruleset),ctypes.sizeof(ruleset),0)
if descriptor<0: raise RuntimeError('Landlock ruleset failed')
def allow(path,rights):
 if not os.path.exists(path): return
 opened=os.open(path,os.O_PATH|os.O_CLOEXEC)
 rule=PathRule(rights,opened)
 result=libc.syscall(445,descriptor,1,ctypes.byref(rule),0)
 os.close(opened)
 if result<0: raise RuntimeError('Landlock rule failed')
for path in ('/usr','/lib','/lib64',sys.prefix,sys.base_prefix): allow(path,1|4|8)
allow(root,1|4|8)
for path in ('/dev/null','/dev/urandom','/dev/random'): allow(path,2|4)
if libc.syscall(446,descriptor,0)<0: raise RuntimeError('Landlock enforcement failed')
os.close(descriptor)
seccomp=ctypes.CDLL('libseccomp.so.2')
seccomp.seccomp_init.argtypes=[ctypes.c_uint32];seccomp.seccomp_init.restype=ctypes.c_void_p
seccomp.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
seccomp.seccomp_load.argtypes=[ctypes.c_void_p]
seccomp.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
context=seccomp.seccomp_init(0x7fff0000)
for name in ('socket','socketpair','connect','bind','listen','accept','accept4','ptrace','process_vm_readv','process_vm_writev','mount','umount2','unshare','setns','bpf','keyctl','open_by_handle_at','pidfd_getfd','pidfd_open','pidfd_send_signal','kill','tkill','tgkill','rt_sigqueueinfo','rt_tgsigqueueinfo','io_uring_setup','execve','execveat','fork','vfork','chmod','fchmod','fchmodat','chown','fchown','lchown','fchownat','sched_setaffinity'):
 number=seccomp.seccomp_syscall_resolve_name(name.encode())
 if number>=0 and seccomp.seccomp_rule_add(context,0x50000|errno.EPERM,number,0): raise RuntimeError('seccomp rule failed')
class Comparison(ctypes.Structure):
 _fields_=[('argument',ctypes.c_uint),('operation',ctypes.c_int),('mask',ctypes.c_uint64),('value',ctypes.c_uint64)]
comparison=Comparison(0,7,0x10000,0)
number=seccomp.seccomp_syscall_resolve_name(b'clone')
if seccomp.seccomp_rule_add(context,0x50000|errno.EPERM,number,1,comparison): raise RuntimeError('clone rule failed')
number=seccomp.seccomp_syscall_resolve_name(b'clone3')
if number>=0 and seccomp.seccomp_rule_add(context,0x50000|errno.ENOSYS,number,0): raise RuntimeError('clone3 rule failed')
if seccomp.seccomp_load(context): raise RuntimeError('seccomp enforcement failed')
sys.path.insert(0,os.path.dirname(program))
spec=importlib.util.spec_from_file_location('candidate',program)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
for line in sys.stdin.buffer:
 request=json.loads(line)
 try:
  response=module.handle(request)
  encoded=json.dumps(response,allow_nan=False,separators=(',',':')).encode()+b'\n'
  if len(encoded)>=64*1024**2: raise ValueError('oversize response')
  sys.stdout.buffer.write(encoded);sys.stdout.buffer.flush()
 except Exception as error:
  if repair: report_worker_exception(error)
  else: print('candidate_operation_failure',file=sys.stderr,flush=True)
  sys.exit(3)
'''


class Client:
    def __init__(self, program, wall, max_calls):
        self.program = program
        self.wall = wall
        self.max_calls = max_calls
        self.calls = 0
        self.process = None
        self.capture = None
        self.directory = None
        self.buffer = bytearray()
        self.proxy = None
        broker = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        if broker or program == '/broker-code/candidate_proxy.py':
            if not broker or program != '/broker-code/candidate_proxy.py':
                raise ValueError('broker requires exact trusted proxy and socket')
            spec = importlib.util.spec_from_file_location('trusted_candidate_proxy',program)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle

    def start(self):
        self.close()
        self.directory = tempfile.TemporaryDirectory(prefix='candidate-native-')
        root = pathlib.Path(self.directory.name)
        source = pathlib.Path(self.program).resolve()
        total = 0
        files = list(source.parent.rglob('*'))
        if len(files)>1024:
            raise ProtocolError('candidate tree too large')
        for item in files:
            if item.is_symlink():
                raise ProtocolError('candidate symlink forbidden')
            if not item.is_file() or '__pycache__' in item.parts:
                continue
            total += item.stat().st_size
            if total>32*1024**2:
                raise ProtocolError('candidate source too large')
            destination = root / 'code' / item.relative_to(source.parent)
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(item,destination)
        interpreter, environment = candidate_subprocess_settings(os.environ)
        for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
            environment[name] = '2'
        repair = PLANE=='search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1')
        self.process = subprocess.Popen([interpreter,'-I','-u','-c',WORKER,str(root),str(root/'code'/source.name),str(self.wall),'1' if repair else '0'],
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=root,env=environment,
            start_new_session=True,shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdout.fileno(),False)
        os.set_blocking(self.process.stdin.fileno(),False)
        self.buffer.clear()

    def close(self, failed=False):
        if self.process is not None:
            process = self.process
            self.process = None
            try:
                os.killpg(process.pid,signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=.3)
            except subprocess.TimeoutExpired:
                pass
            try:
                os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=.5)
            snapshot = self.capture.close()
            if failed and PLANE=='search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1'):
                print('worker_capture observed_bytes=%d truncated=%s capture_error=%s' %
                      (snapshot['observed_bytes'],snapshot['truncated'],snapshot['capture_error']),file=sys.stderr)
                if snapshot['stderr']:
                    print(snapshot['stderr'],file=sys.stderr,end='')
            process.stdin.close(); process.stdout.close()
            self.capture = None
        if self.directory is not None:
            self.directory.cleanup(); self.directory = None

    def __call__(self, request, timeout):
        self.calls += 1
        if self.calls>self.max_calls:
            raise ProtocolError('RPC cap exceeded')
        encoded = bounded_json_line(request)
        if self.proxy is not None:
            with time_bound(time.monotonic()+timeout):
                response = self.proxy(request)
            bounded_json_line(response)
            return response
        deadline = time.monotonic()+timeout
        if request['op']=='reset':
            self.start()
        if self.process is None:
            raise ProtocolError('candidate transport unavailable')
        try:
            offset = 0
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin,selectors.EVENT_WRITE)
                while offset<len(encoded):
                    remaining = deadline-time.monotonic()
                    if remaining<=0 or not selector.select(remaining):
                        raise TimeoutError()
                    offset += os.write(self.process.stdin.fileno(),encoded[offset:offset+65536])
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout,selectors.EVENT_READ)
                while b'\n' not in self.buffer:
                    remaining = deadline-time.monotonic()
                    if remaining<=0 or not selector.select(remaining):
                        raise TimeoutError()
                    chunk = os.read(self.process.stdout.fileno(),65536)
                    if not chunk:
                        raise ProtocolError('candidate exited')
                    self.buffer.extend(chunk)
                    if len(self.buffer)>=64*1024**2:
                        raise ProtocolError('candidate response too large')
            line,_,extra = self.buffer.partition(b'\n'); self.buffer = bytearray(extra)
            try:
                response = json.loads(line,parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
                bounded_json_line(response)
                return response
            except (ValueError,TypeError,RecursionError) as error:
                raise ProtocolError('invalid JSON response') from error
        except (BrokenPipeError,OSError) as error:
            self.close(failed=True)
            raise ProtocolError('candidate transport error') from error
        except (TimeoutError,ProtocolError) as error:
            try:
                self.close(failed=True)
            except Exception:
                error.add_note('secondary candidate cleanup failure')
            raise


@contextlib.contextmanager
def time_bound(deadline):
    remaining = deadline-time.monotonic()
    if remaining<=0:
        raise TimeoutError()
    def expired(signum,frame):
        raise TimeoutError()
    previous_timer = signal.getitimer(signal.ITIMER_REAL)
    timer_started = time.monotonic()
    old = signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,min(remaining,previous_timer[0]) if previous_timer[0]>0 else remaining)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,old)
        if previous_timer[0]>0:
            signal.setitimer(signal.ITIMER_REAL,max(1e-6,previous_timer[0]-(time.monotonic()-timer_started)),previous_timer[1])


def matrix(rows, players):
    first,second = rows[:,0].astype(int),rows[:,1].astype(int)
    indices = np.repeat(np.arange(len(rows)),2)
    return sparse.csr_matrix((np.tile([1.,-1.],len(rows)),(indices,np.column_stack((first,second)).ravel())),shape=(len(rows),players))


def quantities(theta, design, outcome, weights=None):
    if weights is None:
        weights = np.ones(len(outcome))
    total = float(weights.sum())
    if total<=0:
        raise ValueError('empty retained sample')
    margin = design@theta
    probability = expit(margin)
    objective = np.dot(weights,np.logaddexp(0,margin)-outcome*margin)/total + RIDGE*np.dot(theta,theta)/2
    gradient = np.asarray(design.T@(weights*(probability-outcome))).ravel()/total + RIDGE*theta
    hessian = (design.T @ design.multiply((weights*probability*(1-probability)/total)[:,None])).toarray() + RIDGE*np.eye(len(theta))
    return objective,gradient,hessian


def trusted_fit(rows,players,deadline,weights=None):
    with time_bound(deadline):
        design = matrix(rows,players)
        def function(theta):
            objective,gradient,_ = quantities(theta,design,rows[:,2],weights)
            return objective,gradient
        result = minimize(function,np.zeros(players),jac=True,method='L-BFGS-B',options={'maxiter':1000,'gtol':1e-10,'ftol':1e-15,'maxls':40})
        theta = result.x-result.x.mean()
        if not np.isfinite(theta).all() or np.max(np.abs(quantities(theta,design,rows[:,2],weights)[1]))>2e-7:
            raise RuntimeError('fit residual failure')
        return theta


def ranking(theta):
    return np.lexsort((np.arange(len(theta)),-np.round(theta,8)))


def disruption(clean, perturbed):
    first,second = ranking(clean),ranking(perturbed)
    position = np.empty(len(second),dtype=int); position[second] = np.arange(len(second))
    ordered = position[first]
    inversions = sum(int(np.sum(ordered[index+1:]<value)) for index,value in enumerate(ordered))
    return inversions/(len(clean)*(len(clean)-1)/2),float(position[first[0]])/(len(clean)-1)


def require(condition):
    if not condition:
        raise ProtocolError('response or scientific certificate invalid')


def ack(response):
    require(type(response) is dict and set(response)=={'ok'} and response['ok'] is True)


def scientific_require(condition):
    if not condition:
        raise ScientificInvalid('scientific certificate invalid')


def validate_certificate(value, rows, players, clean):
    require(type(value) is dict and set(value)=={'theta','contender','direction','influence','deletions'})
    theta = np.asarray(value['theta'],dtype=float)
    direction = np.asarray(value['direction'],dtype=float)
    influence = np.asarray(value['influence'],dtype=float)
    require(theta.shape==(players,) and direction.shape==(players,) and influence.shape==(len(rows),))
    require(np.isfinite(theta).all() and np.isfinite(direction).all() and np.isfinite(influence).all())
    scientific_require(abs(theta.mean())<1e-7)
    design = matrix(rows,players)
    _,gradient,hessian = quantities(theta,design,rows[:,2])
    scientific_require(np.max(np.abs(gradient))<2e-7 and np.max(np.abs(theta-clean))<2e-4)
    leader = int(ranking(clean)[0]); contender = value['contender']
    require(type(contender) is int and 0<=contender<players and contender!=leader)
    target = np.zeros(players); target[leader]=1; target[contender]=-1
    scientific_require(np.max(np.abs(hessian@direction-target))<2e-7)
    expected = (expit(design@theta)-rows[:,2])*(design@direction)
    scientific_require(np.max(np.abs(expected-influence))<2e-6)
    order = np.lexsort((rows[:,3],np.round(expected,10)))
    masks = value['deletions']
    require(type(masks) is list and len(masks)==3)
    for fraction,mask in zip(FRACTIONS,masks):
        require(type(mask) is list and all(type(key) is int for key in mask))
        expected_keys = [int(key) for key in rows[order[:int(fraction*len(rows))],3]]
        scientific_require(mask==expected_keys and len(set(mask))==len(mask))
    return theta,masks


def solve_candidate(call,rows,players,previous_token):
    probe = call({'op':'export_chunk','token':previous_token or 'invalid_initial_token','index':0})
    require(probe=={'error':'unknown_token'})
    raw = rows.astype('<f8').tobytes()
    chunks = math.ceil(len(raw)/CHUNK)
    ack(call({'op':'import_start','n_rows':len(rows),'n_players':players,'regularization':RIDGE,
              'dtype':'<f8','shape':[len(rows),4],'encoding':'base64','byte_order':'little','nbytes':len(raw),'chunks':chunks}))
    for index in range(chunks):
        ack(call({'op':'import_chunk','index':index,'data':base64.b64encode(raw[index*CHUNK:(index+1)*CHUNK]).decode()}))
    ack(call({'op':'import_commit'}))
    ack(call({'op':'solve','fractions':FRACTIONS,'max_iterations':100}))
    metadata = call({'op':'export_start'})
    require(type(metadata) is dict and set(metadata)=={'token','nbytes','chunks','encoding','dtype','shape','byte_order'})
    require(type(metadata['token']) is str and re.fullmatch('[a-zA-Z0-9_-]{1,80}',metadata['token']) is not None)
    require(type(metadata['nbytes']) is int and 0<metadata['nbytes']<=64*1024**2)
    require(type(metadata['chunks']) is int and 1<=metadata['chunks']<=8 and metadata['chunks']==math.ceil(metadata['nbytes']/CHUNK))
    require((metadata['encoding'],metadata['dtype'],metadata['shape'],metadata['byte_order'])==('base64','json',[],'none'))
    output = bytearray()
    for index in range(metadata['chunks']):
        response = call({'op':'export_chunk','token':metadata['token'],'index':index})
        require(type(response) is dict and set(response)=={'data'} and type(response['data']) is str)
        try:
            chunk = base64.b64decode(response['data'],validate=True)
        except ValueError as error:
            raise ProtocolError('invalid base64') from error
        require(len(chunk)==min(CHUNK,metadata['nbytes']-index*CHUNK))
        output.extend(chunk)
    require(len(output)==metadata['nbytes'])
    try:
        value = json.loads(output,parse_constant=lambda value: (_ for _ in ()).throw(ValueError()))
    except (ValueError,RecursionError) as error:
        raise ProtocolError('invalid certificate JSON') from error
    ack(call({'op':'release'}))
    return value,metadata['token']


def load_data(smoke):
    root = pathlib.Path(os.environ.get('TASK_SOURCE_DIR',pathlib.Path(__file__).resolve().parent))/'resources'/PLANE
    datasets = {}
    for family in ('arena','nba'):
        manifest = json.loads((root/(family+'_manifest.json')).read_text())
        raw = (root/(family+'.json')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=manifest['payload_sha256'] or manifest['plane']!=PLANE:
            raise ValueError('resource integrity failed')
        payload = json.loads(raw)
        if manifest['cross_plane_content_intersection']!=0 or manifest['cross_plane_source_id_intersection']!=0:
            raise ValueError('content split audit failed')
        for record in payload['provenance']:
            code = hashlib.sha256(json.dumps(['split-v1-20261027',family,record['group']],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
            if (int(code,16)%100<30)!=(PLANE=='search'):
                raise ValueError('split membership failed')
        rows = np.array(payload['rows'],dtype=np.float64)
        groups = np.array([record['group'] for record in payload['provenance']])
        players = len(payload['participants'])
        if smoke:
            exposure = np.bincount(rows[:,:2].astype(int).ravel(),minlength=players)
            selected = [int(np.argmax(exposure))]
            while len(selected)<min(12,players):
                neighbor = np.isin(rows[:,0],selected)^np.isin(rows[:,1],selected)
                candidates = np.bincount(rows[neighbor,:2].astype(int).ravel(),minlength=players)
                candidates[selected] = -1
                if candidates.max()<=0:
                    break
                selected.append(int(np.argmax(candidates)))
            selected = sorted(selected)
            keep = np.isin(rows[:,0],selected)&np.isin(rows[:,1],selected)
            rows,groups = rows[keep][:1024],groups[keep][:1024]
            mapping = {old:new for new,old in enumerate(selected)}
            rows[:,0] = [mapping[int(value)] for value in rows[:,0]]
            rows[:,1] = [mapping[int(value)] for value in rows[:,1]]
            players = len(selected)
        if not 2<=players<=256 or not 100<=len(rows)<=100000 or len(set(rows[:,3]))!=len(rows):
            raise ValueError('invalid observed data shape')
        datasets[family] = (rows,players,groups)
    return datasets


METRICS = ['combined_score','random_baseline_score','disagreement_baseline_score','paired_gain_vs_random',
           'paired_gain_vs_disagreement','mean_leader_rank_drop','control_pass_rate','completion_rate','correct']
if PLANE=='final':
    METRICS += ['paired_gain_random_ci_low','paired_gain_random_ci_high','paired_gain_disagreement_ci_low','paired_gain_disagreement_ci_high']


def worst_case(episode):
    return {'combined_score':0.,'random_baseline_score':1.,'disagreement_baseline_score':1.,
            'paired_gain_vs_random':-1.,'paired_gain_vs_disagreement':-1.,'mean_leader_rank_drop':0.,
            'control_pass_rate':0.,'completion_rate':0.,'correct':0.,'controls':[False]*4,
            'solution':None,'duration':0.}


def record_failure(failure):
    if PLANE=='search':
        if type(failure) is str:
            failure = {'component':'baseline','category':bounded_failure_name(failure,'baseline_result_failure'),'operation':'baseline_worker'}
        print('episode_failure component=%s category=%s operation=%s' %
              tuple(bounded_failure_name(failure.get(key),'unknown') for key in ('component','category','operation')),file=sys.stderr)


def final_uncertainty(outcomes,episodes,datasets,deadline,smoke):
    bootstrap = np.random.default_rng(709237)
    seeds = list(dict.fromkeys(episode['seed'] for episode in episodes))
    intervals = {}
    for name,short in [('paired_gain_vs_random','random'),('paired_gain_vs_disagreement','disagreement')]:
        means = [sum(outcomes[index][name] for index,episode in enumerate(episodes) if episode['seed']==seed)/4 for seed in seeds]
        samples = bootstrap.choice(means,size=(8 if smoke else 256,len(seeds)),replace=True).mean(axis=1)
        intervals['paired_gain_'+short+'_ci_low'] = float(np.quantile(samples,.025))
        intervals['paired_gain_'+short+'_ci_high'] = float(np.quantile(samples,.975))
    group_results = {}
    valid = True
    for family in ('arena','nba'):
        index = next(index for index,episode in enumerate(episodes) if episode['family']==family and not episode['permuted'])
        solution = outcomes[index]['solution']
        rows,players,groups = datasets[family]
        unique,inverse = np.unique(groups,return_inverse=True)
        records = []
        for repetition in range(2 if smoke else 32):
            result = {'candidate':0.,'random':1.,'disagreement':1.,'gain_random':-1.,'gain_disagreement':-1.,'complete':False}
            if solution is not None:
                weights = np.bincount(bootstrap.integers(0,len(unique),size=len(unique)),minlength=len(unique))[inverse].astype(float)
                try:
                    clean = trusted_fit(rows,players,deadline,weights)
                    for method in ('candidate','random','disagreement'):
                        scores = []
                        for mask in solution[method+'_masks']:
                            retained = weights.copy(); retained[np.isin(rows[:,3],mask)] = 0
                            fitted = trusted_fit(rows,players,deadline,retained)
                            scores.append(disruption(clean,fitted)[0])
                        result[method] = sum(scores)/3
                    result['gain_random'] = result['candidate']-result['random']
                    result['gain_disagreement'] = result['candidate']-result['disagreement']
                    result['complete'] = True
                except (TimeoutError,RuntimeError):
                    result.update(candidate=0.,random=1.,disagreement=1.,gain_random=-1.,gain_disagreement=-1.,complete=False)
                    valid = False
            else:
                valid = False
            records.append(result)
        group_results[family] = records
    return intervals,group_results,valid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path',required=True)
    parser.add_argument('--results_dir',required=True)
    arguments = parser.parse_args()
    started = time.monotonic()
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1'
    qualification = os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1'
    wall = 120 if smoke else WALL
    startup = 8 if smoke else 120
    finish = 5 if smoke else 90
    hard_deadline = started+wall-startup
    seeds = SEEDS[:1] if smoke else SEEDS
    episodes = [{'seed':seed,'family':family,'permuted':permuted} for seed in seeds for family in ('arena','nba') for permuted in (False,True)]
    metrics = {name:0. for name in METRICS}
    metrics.update(random_baseline_score=1.,disagreement_baseline_score=1.,paired_gain_vs_random=-1.,paired_gain_vs_disagreement=-1.)
    if PLANE=='final':
        metrics.update(paired_gain_random_ci_low=-1.,paired_gain_random_ci_high=1.,paired_gain_disagreement_ci_low=-1.,paired_gain_disagreement_ci_high=1.)
    result_directory = pathlib.Path(arguments.results_dir)
    result_directory.mkdir(parents=True,exist_ok=True)
    client = None
    complete = False
    outcomes = [worst_case(episode) for episode in episodes]
    intervals = {}; group_results = {}; uncertainty_valid = PLANE=='search'
    try:
        payload_preflight = preflight()
        with time_bound(hard_deadline-finish):
            datasets = load_data(smoke)
        method_work = 3. if smoke else (60. if PLANE=='search' else 180.)
        overhead = 3.
        reset_timeout = 3. if smoke else 10.
        profile = {'episode_count':len(episodes),'method_count':5,'wall_seconds':wall,'startup_seconds':startup,
                   'reset_seconds':reset_timeout,'cleanup_seconds':.6,'finish_seconds':finish,'work_seconds':method_work}
        needed = startup+finish+len(episodes)*(reset_timeout+5*(method_work+.6))
        if needed>wall:
            raise ValueError('joint method work cannot fit plane budget')
        client = Client(arguments.program_path,wall,len(episodes)*CALLS_PER_EPISODE)
        previous_token = None
        matched = {}
        baseline_failed = False
        def evaluate(episode,call,global_deadline):
            nonlocal previous_token,baseline_failed
            if baseline_failed:
                raise RequiredBaselineFailure('baseline_result_failure')
            begin = time.monotonic()
            deadline = min(global_deadline,begin+5*(method_work+.6)+1.)
            rows,players,groups = datasets[episode['family']]
            canonical = rows
            if episode['permuted']:
                permutation = np.arange(len(rows)-1,-1,-1)
                require(not np.array_equal(permutation,np.arange(len(rows))))
                rows = rows[permutation].copy()
                require(rows.tobytes()!=canonical.tobytes())
            def baseline_fit(data,limit,weights=None):
                nonlocal baseline_failed
                try:
                    return trusted_fit(data,players,limit,weights)
                except (TimeoutError,RuntimeError) as error:
                    category = 'baseline_timeout' if isinstance(error,TimeoutError) else 'baseline_result_failure'
                    baseline_failed = True
                    raise RequiredBaselineFailure(category) from None
            shared_deadline = reserved_method_deadline(now=time.monotonic(),episode_deadline=deadline,methods_remaining=4,work_seconds=method_work,cleanup_seconds=.6)
            clean = baseline_fit(canonical,shared_deadline)
            controls = [False]*4
            design = matrix(canonical,players)
            constant_gradient = quantities(np.zeros(players),design,canonical[:,2])[1]
            if np.max(np.abs(constant_gradient))>2e-7:
                constant = {'theta':[0.]*players,'contender':int(ranking(clean)[1]),'direction':[0.]*players,
                            'influence':[0.]*len(rows),'deletions':[[],[],[]]}
                try:
                    validate_certificate(constant,canonical,players,clean)
                except ScientificInvalid:
                    controls[1] = True
            method_masks = {}
            curves = {}; leader_curves = {}
            rng = np.random.default_rng(episode['seed'])
            random_order = rng.permutation(len(canonical))
            margins = design@clean
            losses = np.logaddexp(0,margins)-canonical[:,2]*margins
            disagreement_order = np.lexsort((canonical[:,3],-losses))
            orders = {'random':random_order,'disagreement':disagreement_order}
            for method_index,method in enumerate(('random','disagreement','copy','candidate')):
                method_deadline = reserved_method_deadline(now=time.monotonic(),episode_deadline=deadline,methods_remaining=3-method_index,work_seconds=method_work,cleanup_seconds=.6)
                with time_bound(method_deadline):
                    if method=='candidate':
                        value,previous_token = solve_candidate(call,rows,players,previous_token)
                        try:
                            theta,masks = validate_certificate(value,rows,players,clean)
                        except (TypeError,ValueError,IndexError,OverflowError) as error:
                            raise ProtocolError('malformed certificate') from error
                        controls[2] = True
                    elif method=='copy':
                        masks = [[],[],[]]
                    else:
                        masks = [[int(key) for key in canonical[orders[method][:int(fraction*len(canonical))],3]] for fraction in FRACTIONS]
                    method_masks[method] = masks
                    scores = []; drops = []
                    for mask in masks:
                        retained = canonical[~np.isin(canonical[:,3],mask)]
                        if method=='candidate':
                            try:
                                fitted = trusted_fit(retained,players,method_deadline)
                            except RuntimeError as error:
                                raise ProtocolError('candidate perturbation refit invalid') from error
                        else:
                            fitted = baseline_fit(retained,method_deadline)
                        score,drop = disruption(clean,fitted)
                        scores.append(score); drops.append(drop)
                    curves[method] = scores; leader_curves[method] = drops
            controls[0] = curves['copy']==[0.,0.,0.] and leader_curves['copy']==[0.,0.,0.]
            key = (episode['seed'],episode['family'])
            if not episode['permuted']:
                matched[key] = {'theta':theta,'masks':method_masks['candidate'],'curves':curves['candidate']}
            else:
                reference = matched.get(key)
                controls[3] = reference is not None and bool(np.max(np.abs(theta-reference['theta']))<2e-5) and all(set(first)==set(second) for first,second in zip(method_masks['candidate'],reference['masks'])) and bool(np.max(np.abs(np.array(curves['candidate'])-reference['curves']))<1e-8)
            result = worst_case(episode)
            result.update(combined_score=sum(curves['candidate'])/3,random_baseline_score=sum(curves['random'])/3,
                disagreement_baseline_score=sum(curves['disagreement'])/3,
                paired_gain_vs_random=sum(first-second for first,second in zip(curves['candidate'],curves['random']))/3,
                paired_gain_vs_disagreement=sum(first-second for first,second in zip(curves['candidate'],curves['disagreement']))/3,
                mean_leader_rank_drop=sum(leader_curves['candidate'])/3,completion_rate=1.,controls=controls,duration=time.monotonic()-begin,
                solution={'family':episode['family'],'permuted':episode['permuted'],'curves':curves,'candidate_masks':method_masks['candidate'],
                          'random_masks':method_masks['random'],'disagreement_masks':method_masks['disagreement'],'clean_scores':clean.tolist()})
            return result
        def record_episode_failure(failure):
            record_failure(failure)
            try:
                client.close(failed=True)
            except (OSError,RuntimeError,TimeoutError):
                if PLANE=='search':
                    print('cleanup_failure component=candidate category=cleanup_failure operation=cleanup',file=sys.stderr)
        outcomes,complete = run_declared_episodes(episodes,hard_deadline=hard_deadline,finish_reserve=finish,
            reset_timeout=reset_timeout,episode_overhead=overhead,rpc_cap=(10. if smoke else 300.),
            clock=time.monotonic,rpc=client,evaluate=evaluate,worst_case=worst_case,record_failure=record_episode_failure)
        for index,episode in enumerate(episodes):
            if not episode['permuted']:
                outcomes[index]['controls'][3] = outcomes[index+1]['controls'][3]
            outcomes[index]['control_pass_rate'] = sum(outcomes[index]['controls'])/4
            outcomes[index]['correct'] = float(outcomes[index]['completion_rate']==1 and all(outcomes[index]['controls']))
        if PLANE=='final':
            intervals,group_results,uncertainty_valid = final_uncertainty(outcomes,episodes,datasets,hard_deadline-finish,smoke)
        for name in METRICS:
            if name in outcomes[0]:
                metrics[name] = sum(outcome[name] for outcome in outcomes)/len(outcomes)
        metrics.update(intervals)
        correct = complete and uncertainty_valid and all(outcome['correct']==1 for outcome in outcomes)
        metrics['correct'] = float(correct)
        if time.monotonic()>hard_deadline:
            complete = False; metrics['correct'] = 0.
    except Exception as error:
        metrics['correct'] = 0.
        if PLANE=='search':
            message = str(error).replace('\n',' ')[:180]
            print('evaluator_exception type=%s message=%s' % (type(error).__name__,message),file=sys.stderr)
        else:
            print('evaluator_exception type=%s message=sealed' % type(error).__name__,file=sys.stderr)
        write_results(result_directory,metrics,False,qualification,False)
        raise
    finally:
        if client is not None:
            client.close()
    if time.monotonic()>hard_deadline:
        complete = False
        metrics['correct'] = 0.
    feasible = complete and uncertainty_valid and all(all(outcome['controls']) for outcome in outcomes) and time.monotonic()<=hard_deadline and not smoke
    write_results(result_directory,metrics,bool(metrics['correct']),qualification,feasible)
    records = []
    for seed in seeds:
        indices = [index for index,episode in enumerate(episodes) if episode['seed']==seed]
        solution = {'cases':[outcomes[index]['solution'] for index in indices],
                    'controls':[outcomes[index]['controls'] for index in indices]}
        if PLANE=='final':
            solution['conditional_group_bootstrap'] = group_results
        records.append({'seed':seed,'score':sum(outcomes[index]['combined_score'] for index in indices)/4,
            'correct':all(bool(outcomes[index]['correct']) for index in indices) and uncertainty_valid,
            'duration_seconds':sum(outcomes[index]['duration'] for index in indices),'solution':solution})
    evidence = {'schema_version':1,'episodes':records}
    encoded = json.dumps(evidence,allow_nan=False,separators=(',',':')).encode()
    if len(encoded)<=16*1024**2:
        (result_directory/'evaluation_evidence.json').write_bytes(encoded)


def write_results(directory,metrics,correct,qualification,feasible):
    if set(metrics)!=set(METRICS) or not all(type(value) in (int,float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError('invalid metric aggregation')
    (directory/'metrics.json').write_text(json.dumps(metrics,allow_nan=False)+'\n')
    (directory/'correct.json').write_text(json.dumps({'correct':bool(correct)})+'\n')
    if qualification:
        (directory/'qualification.json').write_text(json.dumps({'schema_version':1,'feasible':bool(feasible)})+'\n')


if __name__=='__main__':
    try:
        main()
    except Exception:
        sys.exit(1)
