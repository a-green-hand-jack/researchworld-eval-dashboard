"""Independent offline evaluator. Candidate API is documented in starter program.py.

Scientific validity is integrity + fixed coverage + analytic controls, NOT high
empirical agreement. Search eligibility has no comparative performance cutoff.
Final correctness validates evidence completeness, not a positive reliability
claim. Paper/source review and uncertainty interpretation remain human evidence
obligations; black-box RPC cannot prove a hidden algorithm or a causal mechanism.
"""
import argparse
import base64
import collections
import ctypes
import decimal
import gzip
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
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

PLANE = 'search'
SEEDS = [1729, 2718]
WALL_SECONDS = 3600
RPC_BUDGET = 365
RESOURCE_HASHES = {'acs.json.gz': '0553011831ea29c4fdef6ff06d1bb9a591f6b3866edc4f219d1c58aa25784ffb', 'acs.py': '5946ac913930c464e35cbf6288b96746f232cded2966925be79b04e2d082907d', 'census-site-policy.html': '7c30344cf69af8da08b3ce1cc94df1631e73ffd63174aabd35661b979190e2a4', 'census-terms.html': 'ea341a21715ac0f31fe7d4d6f3b822217a2f773a6d4a89f9c49ff7ddcd0c5d74', 'dictionary2024.pdf': '929c2752995b0af1c16d5c64de8cdc43b4aa7d388ee2d45b4b4df90fecce1dff', 'folktables-LICENSE': '8bfa1347f5d0b17916acfc9c04abdfd884b8c730261260b14699a4833f93ed35', 'german.json.gz': 'd27a90376cdf052d97d8335eed208001101e2af688383ce29768e5a61e9a095a', 'provenance.json': 'dacbe14fcea581ef0bb831ba9983e88d91904eb357a5c9e777a603d06aabfea7', 'relshipp2024.json': '8f0e7392b196399e54e81855affb53f614f7539f0b4b5ccf32fbc4fd8ddfdf33'}
START_TIME = time.monotonic()
APPLICATION_LIMIT = 2*1024*1024
WIRE_LIMIT = 64*1024*1024
MAX_CHUNKS = 16
MAX_CHUNK_BYTES = 1048576
MAX_DOCUMENT_BYTES = 16*1024*1024
METRIC_NAMES = ['reference_fidelity','top3_overlap','signed_agreement','efficiency_error','control_pass_rate','failed_fraction','replay_error','wall_seconds']
if PLANE == 'search':
    METRIC_NAMES.insert(0,'combined_score')
for thread_variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[thread_variable] = '1'


def compact(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode('utf-8')


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = compact(value)+b'\n'
    if len(encoded) >= wire_limit:
        raise ProtocolFailure('message_limit')
    return encoded


def validate_message(value):
    try:
        bounded_json_line(value,APPLICATION_LIMIT)
        for direction in ('request','response'):
            bounded_json_line({'id':9223372036854775807,direction:value,'framing_reserve':'x'*65536},APPLICATION_LIMIT)
    except (ValueError,TypeError,OverflowError,RecursionError):
        raise ProtocolFailure('invalid_json_value') from None


class ProtocolFailure(RuntimeError):
    def __init__(self,category):
        self.category = bounded_failure_name(category,'invalid_response')
        super().__init__('candidate protocol failure')


class TransportFailure(ProtocolFailure):
    pass


def repair_mode():
    return PLANE == 'search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION') == '1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE') == '1')


def candidate_subprocess_settings(parent_environment):
    runtime_names = ('PATH','LD_LIBRARY_PATH','LANG','LC_ALL','TZ','CUDA_VISIBLE_DEVICES',
                     'NVIDIA_VISIBLE_DEVICES','NVIDIA_DRIVER_CAPABILITIES','OMP_NUM_THREADS',
                     'OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS',
                     'XLA_PYTHON_CLIENT_PREALLOCATE','XLA_PYTHON_CLIENT_MEM_FRACTION','XLA_PYTHON_CLIENT_ALLOCATOR')
    environment = {name:parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
    for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        environment[name] = '2'
    return parent_environment.get('TASK_PYTHON',sys.executable),environment


def record_failure(failure):
    if PLANE == 'search':
        component = bounded_failure_name(failure.get('component'),'candidate')
        category = bounded_failure_name(failure.get('category'),'invalid_response')
        operation = bounded_failure_name(failure.get('operation'),'unknown')
        print(f'episode_failure component={component} category={category} operation={operation}'[:256],file=sys.stderr,flush=True)


def forward_failure_snapshot(snapshot, component):
    if repair_mode():
        if snapshot['stderr']:
            print(snapshot['stderr'],end='',file=sys.stderr,flush=True)
        print(f'worker_capture component={component} observed_bytes={snapshot["observed_bytes"]} retained_bytes={snapshot["retained_bytes"]} truncated={int(snapshot["truncated"])} capture_error={bounded_failure_name(snapshot["capture_error"],"none")}',file=sys.stderr,flush=True)


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if type(wall_seconds) not in (int,float) or not math.isfinite(wall_seconds) or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0:
        raise ValueError('invalid CPU budget')
    return math.ceil(wall_seconds*allowed_threads)


def kill_reap(process):
    if process.poll() is not None:
        return process.returncode
    try:
        os.killpg(process.pid,signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=1)
    return process.returncode


NATIVE_WORKER = r'''
import ctypes,importlib.util,json,os,resource,sys
resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,4*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(int(sys.argv[2]),int(sys.argv[2])+1))
resource.setrlimit(resource.RLIMIT_FSIZE,(16*1024*1024,16*1024*1024))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.umask(0o077)
allowed=sorted(os.sched_getaffinity(0))[:2]
os.sched_setaffinity(0,allowed)
libc=ctypes.CDLL(None,use_errno=True)
class Ruleset(ctypes.Structure):
    _fields_=[('handled_access_fs',ctypes.c_uint64)]
class Rule(ctypes.Structure):
    _fields_=[('allowed_access',ctypes.c_uint64),('parent_fd',ctypes.c_int)]
abi=libc.syscall(444,0,0,1)
if abi<1: raise RuntimeError('native isolation unavailable')
handled=(1<<13)-1
if abi>=2: handled|=1<<13
if abi>=3: handled|=1<<14
ruleset=Ruleset(handled)
descriptor=libc.syscall(444,ctypes.byref(ruleset),ctypes.sizeof(ruleset),0)
if descriptor<0: raise RuntimeError('native isolation failed')
paths=[os.getcwd(),sys.prefix,sys.base_prefix,'/usr/lib','/lib','/lib64','/etc/ld.so.cache','/dev/null','/dev/urandom']
for path in paths:
    if not os.path.exists(path):continue
    parent=os.open(path,os.O_PATH|os.O_CLOEXEC)
    access=(1<<0)|(1<<2)
    if os.path.isdir(path):access|=1<<3
    if path==os.getcwd():access=handled
    rule=Rule(access,parent)
    if libc.syscall(445,descriptor,1,ctypes.byref(rule),0)!=0:raise RuntimeError('native filesystem isolation failed')
    os.close(parent)
if libc.prctl(38,1,0,0,0)!=0 or libc.syscall(446,descriptor,0)!=0:raise RuntimeError('native filesystem isolation failed')
os.close(descriptor)
class Filter(ctypes.Structure):
    _fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
class Program(ctypes.Structure):
    _fields_=[('length',ctypes.c_ushort),('filters',ctypes.POINTER(Filter))]
instructions=[Filter(0x20,0,0,4),Filter(0x15,1,0,0xc000003e),Filter(0x06,0,0,0x80000000),Filter(0x20,0,0,0)]
instructions.extend([Filter(0x15,0,4,56),Filter(0x20,0,0,16),Filter(0x45,1,0,0x10000),Filter(0x06,0,0,0x00050001),Filter(0x06,0,0,0x7fff0000)])
instructions.extend([Filter(0x15,0,1,435),Filter(0x06,0,0,0x00050026)])
for syscall in [41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,57,58,59,101,165,166,272,308,310,311,322,323,437]:
    instructions.extend([Filter(0x15,0,1,syscall),Filter(0x06,0,0,0x00050001)])
instructions.append(Filter(0x06,0,0,0x7fff0000))
filters=(Filter*len(instructions))(*instructions)
program=Program(len(instructions),filters)
if libc.prctl(22,2,ctypes.byref(program))!=0:raise RuntimeError('native network isolation failed')
sys.path.insert(0,os.getcwd())
spec=importlib.util.spec_from_file_location('candidate',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    if len(line)>=2*1024*1024:raise ValueError('message limit')
    request=json.loads(line)
    response=module.handle(request)
    encoded=json.dumps(response,allow_nan=False,separators=(',',':')).encode()+b'\n'
    if len(encoded)>=2*1024*1024:raise ValueError('message limit')
    sys.stdout.buffer.write(encoded);sys.stdout.buffer.flush()
'''


class CandidateClient:
    def __init__(self,path):
        socket = os.environ.get('AGENTIC_CANDIDATE_SOCKET')
        fixed_proxy = str(path) == '/broker-code/candidate_proxy.py'
        if bool(socket) != fixed_proxy:
            raise RuntimeError('broker requires both fixed proxy and socket')
        self.broker = fixed_proxy and bool(socket)
        self.calls = 0
        self.process = None
        self.capture = None
        self.temporary = None
        self.path = path
        if self.broker:
            specification = importlib.util.spec_from_file_location('trusted_candidate_proxy',path)
            self.module = importlib.util.module_from_spec(specification)
            specification.loader.exec_module(self.module)
        else:
            self.temporary = tempfile.TemporaryDirectory(prefix='isolated-shap-')
            self.local = Path(self.temporary.name)/'program.py'
            total = 0
            for source in path.parent.rglob('*.py'):
                if source.is_symlink() or not source.is_file():
                    raise RuntimeError('unsafe native candidate source')
                content = source.read_bytes()
                total += len(content)
                if total > 16*1024*1024:
                    raise RuntimeError('native source bound')
                target = Path(self.temporary.name)/source.relative_to(path.parent)
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(content)
            self.local = Path(self.temporary.name)/path.name

    def start(self):
        interpreter,environment = candidate_subprocess_settings(os.environ)
        self.process = subprocess.Popen([interpreter,'-I','-u','-c',NATIVE_WORKER,str(self.local),str(cpu_limit_seconds(WALL_SECONDS,min(2,len(os.sched_getaffinity(0)))))],cwd=self.temporary.name,env=environment,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(),False)
        os.set_blocking(self.process.stdout.fileno(),False)

    def stop(self,failed=False):
        if self.process is None:
            return
        process,self.process = self.process,None
        primary = None
        try:
            kill_reap(process)
        except (OSError,subprocess.TimeoutExpired) as error:
            primary = error
        finally:
            for stream in (process.stdin,process.stdout):
                stream.close()
            snapshot = self.capture.close()
            self.capture = None
            if failed:
                forward_failure_snapshot(snapshot,'candidate')
        if primary is not None:
            raise RuntimeError('native cleanup failed') from primary

    def rpc(self,request,timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolFailure('rpc_limit')
        validate_message(request)
        if self.broker:
            previous = signal.getsignal(signal.SIGALRM)
            def alarm_handler(signum,frame):
                raise TimeoutError('candidate RPC timeout')
            signal.signal(signal.SIGALRM,alarm_handler)
            signal.setitimer(signal.ITIMER_REAL,timeout)
            try:
                response = self.module.handle(request)
            finally:
                signal.setitimer(signal.ITIMER_REAL,0)
                signal.signal(signal.SIGALRM,previous)
        else:
            if request['op'] == 'reset':
                self.stop()
                self.start()
            if self.process is None:
                raise TransportFailure('candidate_unavailable')
            deadline = time.monotonic()+timeout
            outgoing = memoryview(bounded_json_line(request,APPLICATION_LIMIT))
            received = bytearray()
            try:
                with selectors.DefaultSelector() as selector:
                    selector.register(self.process.stdin,selectors.EVENT_WRITE)
                    selector.register(self.process.stdout,selectors.EVENT_READ)
                    while True:
                        remaining = deadline-time.monotonic()
                        if remaining <= 0:
                            raise TimeoutError('candidate RPC timeout')
                        ready = selector.select(remaining)
                        if not ready:
                            raise TimeoutError('candidate RPC timeout')
                        for key,events in ready:
                            if key.fileobj is self.process.stdin:
                                try:
                                    amount = os.write(self.process.stdin.fileno(),outgoing[:65536])
                                except BrokenPipeError:
                                    raise TransportFailure('candidate_exit') from None
                                outgoing = outgoing[amount:]
                                if not outgoing:
                                    selector.unregister(self.process.stdin)
                            else:
                                chunk = os.read(self.process.stdout.fileno(),65536)
                                if not chunk:
                                    raise TransportFailure('candidate_exit')
                                received.extend(chunk)
                                if len(received) >= APPLICATION_LIMIT:
                                    raise ProtocolFailure('message_limit')
                                if b'\n' in received:
                                    line,extra = received.split(b'\n',1)
                                    if extra:
                                        raise ProtocolFailure('unsolicited_response')
                                    try:
                                        response = json.loads(line)
                                    except (ValueError,UnicodeError,RecursionError):
                                        raise ProtocolFailure('malformed_json') from None
                                    validate_message(response)
                                    return response
            except (TimeoutError,ProtocolFailure) as primary:
                try:
                    self.stop(failed=True)
                except (RuntimeError,OSError,subprocess.TimeoutExpired):
                    primary.add_note('secondary candidate cleanup failure')
                raise
        validate_message(response)
        return response

    def close(self):
        try:
            self.stop()
        finally:
            if self.temporary is not None:
                self.temporary.cleanup()


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
    if isinstance(error, ProtocolFailure):
        return {"component":"candidate","category":error.category,"operation":bounded_failure_name(operation,"unknown")}
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

        def call(request, deadline=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock(), float("inf") if deadline is None else deadline-clock())
                if timeout <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
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
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                if not episode.get('failure_emitted',False):
                    record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
            if isinstance(error, TransportFailure):
                raise
        finally:
            if type(outcomes[index]) is dict and 'duration' in outcomes[index]:
                outcomes[index]['duration'] = max(0.,clock()-episode_started)
    return outcomes, complete


def science():
    global np, shap, LogisticRegression, RandomForestClassifier, threadpool_limits
    import numpy as np
    import shap
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from threadpoolctl import threadpool_limits
    import scipy
    import pandas
    import folktables
    threadpool_limits(limits=1)


def normalized_raw(row,numeric):
    normalized = []
    for index,value in enumerate(row):
        if value is None or not str(value).strip():
            normalized.append(None)
        elif index in numeric:
            number = decimal.Decimal(str(value).strip())
            if not number.is_finite():
                normalized.append(None)
            else:
                normalized.append(['number','0' if number == 0 else format(number.normalize(),'f')])
        else:
            normalized.append(['text',' '.join(unicodedata.normalize('NFKC',str(value)).split())])
    return normalized


def content_digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def load_data(root,name):
    with gzip.open(root/f'{name}.json.gz','rt',encoding='utf-8') as stream:
        dataset = json.load(stream)
    seen = set()
    for record in dataset['records']:
        digest = content_digest(normalized_raw(record['raw'],set(dataset['numeric'])))
        if digest != record['content_sha256'] or digest in seen:
            raise RuntimeError('raw content integrity failed')
        seen.add(digest)
        if record['role'] not in ('train','validation','explanation') or type(record['y']) is not bool or not record['provenance']:
            raise RuntimeError('split manifest integrity failed')
    return dataset


def encode_dataset(dataset,smoke):
    training = [record for record in dataset['records'] if record['role']=='train']
    if smoke:
        training = training[:64]
    else:
        training = training[:20000]
    explanations = [record for record in dataset['records'] if record['role']=='explanation']
    validation = [record for record in dataset['records'] if record['role']=='validation']
    dimension = len(dataset['features'])
    numeric = set(dataset['numeric'])
    vocabularies = {}
    for column in range(dimension):
        if column not in numeric:
            vocabularies[column] = {value:index for index,value in enumerate(sorted({record['raw'][column] for record in training if record['raw'][column] is not None}))}
    def transform(records):
        matrix = np.zeros((len(records),dimension))
        for row_index,record in enumerate(records):
            for column,value in enumerate(record['raw']):
                matrix[row_index,column] = float(value) if column in numeric and value not in (None,'') else vocabularies.get(column,{}).get(value,-1) if column not in numeric else np.nan
        return matrix
    train = transform(training)
    medians = np.nanmedian(train,axis=0)
    medians = np.nan_to_num(medians)
    train = np.where(np.isfinite(train),train,medians)
    mean = train.mean(axis=0)
    scale = train.std(axis=0)
    scale[scale<1e-12] = 1
    def standardized(records):
        values = transform(records)
        return (np.where(np.isfinite(values),values,medians)-mean)/scale
    return (train-mean)/scale, np.array([record['y'] for record in training],dtype=int), standardized(explanations), standardized(validation), np.array([record['y'] for record in validation],dtype=int)


def predict(model,rows):
    rows = np.asarray(rows,dtype=np.float64)
    parameters = model['parameters']
    if model['kind'] in ('logistic','affine'):
        linear = rows@np.asarray(parameters['coef'])+parameters['intercept']
        return linear if model['kind']=='affine' else 1/(1+np.exp(-np.clip(linear,-700,700)))
    output = np.zeros(len(rows))
    converted = rows.astype(np.float32)
    for tree in parameters['trees']:
        left,right,features,thresholds,probabilities = (np.asarray(tree[key]) for key in ('left','right','feature','threshold','probability'))
        nodes = np.zeros(len(rows),dtype=np.int64)
        for depth in range(7):
            active = left[nodes]>=0
            if not active.any():
                break
            selected = nodes[active]
            nodes[active] = np.where(converted[active][np.arange(len(selected)),features[selected]] <= thresholds[selected],left[selected],right[selected])
        output += probabilities[nodes]
    return output/len(parameters['trees'])


def serialize_model(estimator,kind,background):
    if kind == 'logistic':
        parameters = {'coef':estimator.coef_[0].tolist(),'intercept':float(estimator.intercept_[0])}
    else:
        trees = []
        for member in estimator.estimators_:
            tree = member.tree_
            distribution = tree.value[:,0,:]
            trees.append({'left':tree.children_left.tolist(),'right':tree.children_right.tolist(),'feature':tree.feature.tolist(),'threshold':tree.threshold.tolist(),'probability':(distribution[:,1]/distribution.sum(axis=1)).tolist()})
        parameters = {'trees':trees}
    model = {'kind':kind,'dimension':background.shape[1],'background':background.tolist(),'parameters':parameters}
    if len(compact(model))>MAX_DOCUMENT_BYTES:
        raise RuntimeError('model serialization bound')
    return model


def library_kernel(model,queries,budget,seed,counter):
    def oracle(rows):
        counter[0] += len(rows)
        return predict(model,rows)
    state = np.random.get_state()
    try:
        np.random.seed(seed%(2**32))
        explainer = shap.KernelExplainer(oracle,np.asarray(model['background']),link='identity')
        values = explainer.shap_values(np.asarray(queries),nsamples=budget,l1_reg=0.0,silent=True)
        output = np.asarray(values,dtype=float)
        if output.shape != np.asarray(queries).shape or not np.isfinite(output).all():
            raise RuntimeError('invalid library reference')
        return output
    finally:
        np.random.set_state(state)


def exact_reference(model,queries,counter):
    dimension = model['dimension']
    background = np.asarray(model['background'])
    numbers = np.arange(1<<dimension,dtype=np.uint32)
    masks = ((numbers[:,None]>>np.arange(dimension))&1).astype(bool)
    references = []
    for query in queries:
        values = []
        for offset in range(0,len(masks),128):
            chunk = masks[offset:offset+128]
            hybrids = np.where(chunk[:,None,:],query,background[None,:,:])
            flattened = hybrids.reshape(-1,dimension)
            counter[0] += len(flattened)
            values.extend(predict(model,flattened).reshape(len(chunk),len(background)).mean(axis=1))
        values = np.asarray(values)
        reference = []
        sizes = masks.sum(axis=1)
        for feature in range(dimension):
            absent = numbers[~masks[:,feature]]
            weights = np.array([1/(dimension*math.comb(dimension-1,int(size))) for size in sizes[absent]])
            reference.append(float(np.dot(weights,values[absent|(1<<feature)]-values[absent])))
        references.append(reference)
    return np.asarray(references)


def run_stage(callback,seconds):
    def alarm_handler(signum,frame):
        raise TimeoutError('trusted method work timeout')
    previous = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM,alarm_handler)
    signal.setitimer(signal.ITIMER_REAL,seconds)
    started = time.monotonic()
    try:
        result = callback()
        duration = time.monotonic()-started
        if duration>seconds:
            raise TimeoutError('trusted method work timeout')
        return result,duration
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)


def baseline_work(request):
    science()
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:1])
    resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
    resource.setrlimit(resource.RLIMIT_CPU,(cpu_limit_seconds(WALL_SECONDS,1),cpu_limit_seconds(WALL_SECONDS,1)+1))
    smoke = request['smoke']
    if request['case']=='controls':
        return control_baseline(request)
    settings = request['settings']
    work = request['work_seconds']
    dataset_name,kind = request['case'].split('_',1)
    root = Path(request['root'])
    def train():
        dataset = load_data(root,dataset_name)
        train_rows,labels,explanations,validation,targets = encode_dataset(dataset,smoke)
        if len(np.unique(labels))!=2:
            raise RuntimeError('training classes absent')
        if kind=='logistic':
            estimator = LogisticRegression(max_iter=500,random_state=request['seed'],solver='lbfgs',tol=1e-7)
        else:
            estimator = RandomForestClassifier(n_estimators=4 if smoke else 64,max_depth=6,random_state=request['seed'],n_jobs=1)
        estimator.fit(train_rows,labels)
        background = train_rows[:settings['background']]
        queries = explanations[:settings['instances']]
        model = serialize_model(estimator,kind,background)
        probe = np.concatenate([queries,background])
        if not np.allclose(predict(model,probe),estimator.predict_proba(probe)[:,1],rtol=1e-9,atol=1e-10):
            raise RuntimeError('safe model serialization mismatch')
        accuracy = float(np.mean(estimator.predict(validation)==targets))
        diagnostics = {'validation_accuracy':accuracy,'fit_iterations':int(estimator.n_iter_[0]) if kind=='logistic' else 0,'fit_converged':bool(kind!='logistic' or estimator.n_iter_[0]<500)}
        return model,queries,diagnostics
    (model,queries,diagnostics),training_seconds = run_stage(train,work)
    counters = {'reference':[0],'standard':[0],'multistart':[0]}
    def references():
        if model['dimension']<=10:
            values = exact_reference(model,queries,counters['reference'])
            return values,np.zeros_like(values)
        budget = 64 if smoke else 4096
        first = library_kernel(model,queries,budget,request['seed']+100000,counters['reference'])
        second = library_kernel(model,queries,budget,request['seed']+200000,counters['reference'])
        return (first+second)/2,abs(first-second)/2
    (references,uncertainty),reference_seconds = run_stage(references,work)
    def standard():
        return [library_kernel(model,queries,budget,request['seed']+300000+index,counters['standard']).tolist() for index,budget in enumerate(settings['budgets'])]
    standard_values,standard_seconds = run_stage(standard,work)
    def multistart():
        outputs = []
        for index,budget in enumerate(settings['budgets']):
            first = library_kernel(model,queries,max(1,budget//2),request['seed']+400000+2*index,counters['multistart'])
            second = library_kernel(model,queries,max(1,budget//2),request['seed']+400001+2*index,counters['multistart'])
            outputs.append(((first+second)/2).tolist())
        return outputs
    multistart_values,multistart_seconds = run_stage(multistart,work)
    return {'model':model,'queries':queries.tolist(),'reference':references.tolist(),'reference_uncertainty':uncertainty.tolist(),'standard':standard_values,'multistart':multistart_values,'diagnostics':diagnostics,
            'productive_seconds':{'training':training_seconds,'reference':reference_seconds,'standard':standard_seconds,'multistart':multistart_seconds},'prediction_rows':{key:value[0] for key,value in counters.items()}}


class BaselineWorker:
    def __init__(self,request,deadline):
        self.deadline = deadline
        environment = {name:os.environ[name] for name in ('PATH','LD_LIBRARY_PATH','LANG','LC_ALL','TZ') if name in os.environ}
        environment.update(HOME='/nonexistent',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',WORKER_REPAIR_MODE='1' if repair_mode() else '0')
        for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
            environment[name] = '1'
        self.process = subprocess.Popen([sys.executable,'-I',str(Path(__file__).resolve()),'--baseline-worker'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment,start_new_session=True,shell=False)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        self.request = compact(request)
        self.returncode = None
        self.done = False
        self.last_category = None

    def cancel(self):
        if not self.done:
            self.returncode = kill_reap(self.process)
        self.done = True

    def result(self,timeout):
        self.process.stdin.write(self.request)
        self.process.stdin.close()
        output = bytearray()
        deadline = time.monotonic()+timeout
        os.set_blocking(self.process.stdout.fileno(),False)
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout,selectors.EVENT_READ)
            while True:
                remaining = deadline-time.monotonic()
                if remaining<=0 or not selector.select(remaining):
                    self.last_category = 'baseline_timeout'
                    raise TimeoutError('baseline worker deadline')
                chunk = os.read(self.process.stdout.fileno(),65536)
                if not chunk:
                    break
                output.extend(chunk)
                if len(output)>16*1024*1024:
                    self.last_category = 'baseline_result_failure'
                    raise RuntimeError('baseline result exceeds bound')
        try:
            self.process.wait(timeout=max(.001,deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            self.last_category = 'baseline_timeout'
            raise TimeoutError('baseline worker deadline') from None
        stdout = bytes(output)
        self.done = True
        self.returncode = self.process.returncode
        if self.returncode != 0:
            self.last_category = 'baseline_signal' if self.returncode<0 else 'baseline_exit'
            raise RequiredBaselineFailure(self.last_category)
        try:
            result = json.loads(stdout)
        except (ValueError,UnicodeError):
            self.last_category = 'baseline_result_failure'
            raise RuntimeError('invalid baseline worker result') from None
        if type(result) is not dict:
            self.last_category = 'baseline_result_failure'
            raise RuntimeError('invalid baseline worker result')
        return result

    def close(self,failed):
        try:
            self.cancel()
        finally:
            snapshot = self.capture.close()
            if failed:
                forward_failure_snapshot(snapshot,'baseline')
                if repair_mode() and self.returncode is not None:
                    print(f'baseline_status exit={self.returncode if self.returncode>=0 else 0} signal={-self.returncode if self.returncode<0 else 0}',file=sys.stderr,flush=True)
            for stream in (self.process.stdin,self.process.stdout):
                if stream is not None and not stream.closed:
                    stream.close()


def fixture_models(settings):
    background = np.array([[((row+2*column)%9)/10 for column in range(4)] for row in range(settings['background'])])
    queries = np.array([[.9,.2,.8,.1],[.1,.8,.2,.9]])
    coefficients = np.array([.07,-.11,.16,.03])
    permutation = np.array([2,0,3,1])
    if np.array_equal(permutation,np.arange(4)) or np.allclose(coefficients,coefficients[permutation]):
        raise RuntimeError('vacuous permutation')
    expected = (queries-background.mean(axis=0))*coefficients
    if np.allclose(expected[0],expected[1]) or np.allclose(expected,expected[:,permutation]):
        raise RuntimeError('uninformative control fixture')
    models = [
        {'kind':'affine','dimension':4,'background':background.tolist(),'parameters':{'coef':[0.,0.,0.,0.],'intercept':.4}},
        {'kind':'affine','dimension':4,'background':background.tolist(),'parameters':{'coef':coefficients.tolist(),'intercept':.4}},
        {'kind':'affine','dimension':4,'background':background[:,permutation].tolist(),'parameters':{'coef':coefficients[permutation].tolist(),'intercept':.4}}]
    return models,[queries.tolist(),queries.tolist(),queries[:,permutation].tolist()],[np.zeros_like(expected).tolist(),expected.tolist(),expected[:,permutation].tolist()],permutation.tolist()


def control_baseline(request):
    settings = request['settings']
    models,queries,expected,permutation = fixture_models(settings)
    budget = 16 if request['smoke'] else 64
    work = request['work_seconds']
    counter = [0]
    def references():
        return [exact_reference(model,np.asarray(inputs),counter).tolist() for model,inputs in zip(models,queries)]
    actual,reference_seconds = run_stage(references,work)
    if not np.allclose(actual,expected,atol=1e-10,rtol=0):
        raise RuntimeError('analytic fixture reference mismatch')
    def standard():
        return [[library_kernel(model,inputs,budget,request['seed']+index*10+repeat,counter).tolist() for repeat in range(2)] for index,(model,inputs) in enumerate(zip(models,queries))]
    standards,standard_seconds = run_stage(standard,work)
    def multistart():
        return [[((library_kernel(model,inputs,budget//2,request['seed']+100+index*10+repeat*2,counter)+library_kernel(model,inputs,budget//2,request['seed']+101+index*10+repeat*2,counter))/2).tolist() for repeat in range(2)] for index,(model,inputs) in enumerate(zip(models,queries))]
    multis,multi_seconds = run_stage(multistart,work)
    if not all(np.allclose(values,np.asarray(expected[index])[None,:,:],atol=1e-7,rtol=0) for method in (standards,multis) for index,values in enumerate(method)):
        raise RuntimeError('required control baseline invalid')
    return {'models':models,'queries':queries,'expected':expected,'permutation':permutation,'standard':standards,'multistart':multis,'prediction_rows':counter[0],
            'productive_seconds':{'reference':reference_seconds,'standard':standard_seconds,'multistart':multi_seconds}}


def expect_ack(response):
    if type(response) is not dict or set(response)!={'ok'} or response['ok'] is not True:
        raise ProtocolFailure('invalid_ack')


def upload_model(call,model,token):
    document = compact(model)
    if not 1<=len(document)<=MAX_DOCUMENT_BYTES:
        raise RuntimeError('model bound exceeded')
    expect_ack(call({'op':'model_start','token':token,'nbytes':len(document),'sha256':hashlib.sha256(document).hexdigest(),
                     'encoding':'base64','dtype':'uint8','shape':[len(document)],'content_type':'application/json'}))
    for index,offset in enumerate(range(0,len(document),MAX_CHUNK_BYTES)):
        expect_ack(call({'op':'model_chunk','token':token,'index':index,'data':base64.b64encode(document[offset:offset+MAX_CHUNK_BYTES]).decode('ascii')}))
    expect_ack(call({'op':'model_commit','token':token}))


def explain(call,queries,budget,dimension):
    response = call({'op':'explain','queries':queries,'budget':budget})
    if type(response) is not dict or set(response)!={'attributions'}:
        raise ProtocolFailure('invalid_explanation_fields')
    values = response['attributions']
    if type(values) is not list or len(values)!=len(queries) or any(type(row) is not list or len(row)!=dimension for row in values):
        raise ProtocolFailure('invalid_attribution_shape')
    if any(type(value) not in (float,int) or abs(value)>1000000 or not math.isfinite(value) for row in values for value in row):
        raise ProtocolFailure('invalid_attribution_value')
    return values


def agreement(values,reference,delta):
    values = np.asarray(values,dtype=float)
    reference = np.asarray(reference,dtype=float)
    error = np.abs(values-reference).sum(axis=-1)
    scale = np.maximum(np.abs(reference).sum(axis=-1),.001)
    fidelity = 1/(1+error/scale)
    def top3(row):
        return set(sorted(range(len(row)),key=lambda index:(-abs(row[index]),index))[:min(3,len(row))])
    overlap = np.array([len(top3(row)&top3(target))/min(3,len(row)) for row,target in zip(values,reference)])
    sign = lambda array: np.where(abs(array)<=1e-8,0,np.sign(array))
    signed = (sign(values)==sign(reference)).mean(axis=-1)
    efficiency = np.minimum(1,abs(values.sum(axis=-1)-delta)/np.maximum(abs(delta),.001))
    return np.column_stack([fidelity,overlap,signed,efficiency])


def initial_outcome(episode,settings):
    cells = [[[None for instance in range(settings['instances'])] for repeat in range(settings['repetitions'])] for budget in settings['budgets']]
    repeat_pairs = [[[None for instance in range(settings['instances'])] for pair in range(math.comb(settings['repetitions'],2))] for budget in settings['budgets']]
    return {'case':episode['case'],'seed':episode['seed'],'replay':episode['replay'],'cells':cells,'repeat_pairs':repeat_pairs,'controls':[0.,0.,0.,0.],
            'completed_controls':[],'valid':False,'operational':False,'duration':0.,'solution':None}


def empirical_summary(outcome,settings):
    metrics = np.zeros((len(settings['budgets']),settings['repetitions'],settings['instances'],4))
    metrics[:,:,:,3] = 1
    for budget_index,repetitions in enumerate(outcome['cells']):
        for repeat_index,instances in enumerate(repetitions):
            for instance_index,value in enumerate(instances):
                if value is not None:
                    metrics[budget_index,repeat_index,instance_index] = value
    pair_metrics = np.zeros((len(settings['budgets']),math.comb(settings['repetitions'],2),settings['instances'],2))
    for budget_index,pairs in enumerate(outcome['repeat_pairs']):
        for pair_index,instances in enumerate(pairs):
            for instance_index,value in enumerate(instances):
                if value is not None:
                    pair_metrics[budget_index,pair_index,instance_index] = value
    summary = metrics.mean(axis=(0,1,2))
    summary[1:3] = .5*summary[1:3]+.5*pair_metrics.mean(axis=(0,1,2))
    return summary


def check_interrupted_agreement():
    for repetitions in (2,4,6):
        settings = {'instances':2,'repetitions':repetitions,'budgets':[64,256]}
        for completed in range(repetitions+1):
            outcome = initial_outcome({'case':'fixture','seed':0,'replay':False},settings)
            for repeat_index in range(completed):
                outcome['cells'][0][repeat_index] = [[1.,1.,1.,0.] for instance in range(2)]
                for previous in range(repeat_index):
                    pair_index = repeat_index*(repeat_index-1)//2+previous
                    outcome['repeat_pairs'][0][pair_index] = [[1.,1.] for instance in range(2)]
            summary = empirical_summary(outcome,settings)
            reference_fraction = completed/repetitions
            pair_fraction = math.comb(completed,2)/math.comb(repetitions,2)
            expected = [reference_fraction/2,(reference_fraction+pair_fraction)/4,
                        (reference_fraction+pair_fraction)/4,1-reference_fraction/2]
            if not np.allclose(summary,expected,atol=1e-12,rtol=0):
                raise RuntimeError('interrupted agreement weights changed')


def evaluate_episode(episode,call,deadline,*,settings,root,work_seconds,smoke):
    outcome = episode['outcome']
    started = time.monotonic()
    worker = None
    primary = None
    try:
        required_work = 5*work_seconds+5
        if time.monotonic()+required_work>deadline:
            raise TimeoutError('insufficient matched method allowances')
        worker_deadline = min(deadline-work_seconds-3,time.monotonic()+4*work_seconds+2)
        worker = BaselineWorker({'case':episode['case'],'seed':episode['seed'],'root':str(root),'settings':settings,'smoke':smoke,'work_seconds':work_seconds},worker_deadline)
        def record_baseline(category):
            worker.last_category = category
            record_failure({'component':'baseline','category':category,'operation':'baseline_worker'})
            episode['failure_emitted'] = True
        baseline = collect_required_baseline(worker.result,deadline=worker_deadline,clock=time.monotonic,cancel_work=worker.cancel,record_failure=record_baseline)
        worker.close(False)
        worker = None
        candidate_deadline = reserved_method_deadline(now=time.monotonic(),episode_deadline=deadline,methods_remaining=0,work_seconds=work_seconds,cleanup_seconds=3)
        remaining_explanations = 6 if episode['case']=='controls' else len(settings['budgets'])*settings['repetitions']
        def candidate_call(request):
            nonlocal remaining_explanations
            usable_seconds = candidate_deadline-time.monotonic()
            if usable_seconds<=0:
                raise TimeoutError('candidate method allowance exhausted')
            if request['op']=='explain':
                request = dict(request,workload={'usable_seconds':usable_seconds,'remaining_explanations':remaining_explanations})
                remaining_explanations -= 1
            return call(request,deadline=candidate_deadline)
        if episode['case']=='controls':
            models = baseline['models']
            inputs = baseline['queries']
            expected = np.asarray(baseline['expected'])
            returned = []
            for model_index,model in enumerate(models):
                upload_model(candidate_call,model,f'model{model_index}')
                predictions = [explain(candidate_call,inputs[model_index],16 if smoke else 64,4) for repeat in range(2)]
                returned.append(predictions)
                if model_index==0:
                    outcome['controls'][0] = float(np.allclose(predictions,0,atol=1e-7,rtol=0))
                    outcome['completed_controls'].append('constant')
                if model_index==1:
                    outcome['controls'][3] = float(np.allclose(predictions,expected[1][None,:,:],atol=1e-7,rtol=0))
                    outcome['completed_controls'].append('additive')
                    copy = np.repeat(expected[1,:1],len(expected[1]),axis=0)
                    stable_copy = np.allclose(copy,np.repeat(copy[:1],len(copy),axis=0),atol=0,rtol=0)
                    reject_copy = not np.allclose(copy,expected[1],atol=1e-7,rtol=0)
                    outcome['controls'][1] = float(stable_copy and reject_copy)
                    outcome['completed_controls'].append('copy')
                if model_index==2:
                    permutation = np.asarray(baseline['permutation'])
                    inverse = np.argsort(permutation)
                    outcome['controls'][2] = float(np.allclose(np.asarray(predictions)[:,:,inverse],expected[1][None,:,:],atol=1e-7,rtol=0) and np.allclose(np.asarray(predictions)[:,:,inverse],np.asarray(returned[1]),atol=1e-7,rtol=0))
                    outcome['completed_controls'].append('permuted_input')
            if set(outcome['completed_controls']) != {'constant','copy','permuted_input','additive'}:
                raise ProtocolFailure('missing_control')
            outcome['solution'] = {'controls':outcome['controls'],'attributions':returned,'baseline':baseline}
            outcome['valid'] = all(value==1 for value in outcome['controls'])
            outcome['operational'] = outcome['valid']
        else:
            model = baseline['model']
            queries = baseline['queries']
            reference = np.asarray(baseline['reference'])
            delta = predict(model,queries)-predict(model,model['background']).mean()
            upload_model(candidate_call,model,'model0')
            attributions = []
            for budget_index,budget in enumerate(settings['budgets']):
                repetitions = []
                for repeat_index in range(settings['repetitions']):
                    values = explain(candidate_call,queries,budget,model['dimension'])
                    repetitions.append(values)
                    measurements = agreement(values,reference,delta)
                    for instance_index,value in enumerate(measurements):
                        outcome['cells'][budget_index][repeat_index][instance_index] = value.tolist()
                    for previous in range(repeat_index):
                        pair_index = repeat_index*(repeat_index-1)//2+previous
                        outcome['repeat_pairs'][budget_index][pair_index] = agreement(values,repetitions[previous],delta)[:,1:3].tolist()
                attributions.append(repetitions)
            baseline_metrics = {name:[agreement(values,reference,delta).mean(axis=0).tolist() for values in baseline[name]] for name in ('standard','multistart')}
            instance_values = np.array(outcome['cells'])[:,:,:,0].mean(axis=(0,1))
            generator = np.random.default_rng(84017)
            bootstraps = instance_values[generator.integers(len(instance_values),size=(1000,len(instance_values)))].mean(axis=1)
            outcome['solution'] = {'attributions':attributions,'reference':baseline['reference'],'reference_uncertainty':baseline['reference_uncertainty'],'standard':baseline['standard'],'multistart':baseline['multistart'],'baseline_metrics':baseline_metrics,
                                   'fidelity_instance_bootstrap_ci95':np.quantile(bootstraps,[.025,.975]).tolist(),'model_diagnostics':baseline['diagnostics'],'productive_seconds':baseline['productive_seconds'],'prediction_rows':baseline['prediction_rows']}
            outcome['valid'] = True
            outcome['operational'] = True
        if time.monotonic()>candidate_deadline:
            raise TimeoutError('candidate method allowance exhausted')
        return outcome
    except (TimeoutError,RequiredBaselineFailure,ProtocolFailure,InvalidResetResponse) as error:
        primary = error
        raise
    finally:
        if worker is not None:
            try:
                worker.close(primary is not None)
            except (OSError,RuntimeError,subprocess.TimeoutExpired) as cleanup_error:
                if primary is None:
                    raise
                primary.add_note('secondary baseline cleanup failure')
        outcome['duration'] = time.monotonic()-started
        if primary is not None:
            outcome['valid'] = False
            outcome['operational'] = False


def production_counts(plane):
    seed_count = 2 if plane=='search' else 3
    explanation_calls = 8 if plane=='search' else 18
    empirical_episodes = 4*seed_count+1
    table = {'empirical':{'episodes':empirical_episodes,'reset':1,'model_start':1,'model_chunk':MAX_CHUNKS,'model_commit':1,'explain':explanation_calls},
             'controls':{'episodes':seed_count,'reset':1,'model_start':3,'model_chunk':3*MAX_CHUNKS,'model_commit':3,'explain':6}}
    total = sum(row['episodes']*sum(value for key,value in row.items() if key!='episodes') for row in table.values())
    return table,total


def preflight():
    for plane,expected in [('search',365),('final',664)]:
        table,total = production_counts(plane)
        if total!=expected or total>10000000:
            raise RuntimeError('RPC preflight mismatch')
        mock_count = 0
        for row in table.values():
            for episode in range(row['episodes']):
                mock_count += 1
                for transfer in range(row['model_start']):
                    mock_count += 1
                    for chunk in range(MAX_CHUNKS):
                        mock_count += 1
                    mock_count += 1
                mock_count += row['explain']
        if mock_count!=total:
            raise RuntimeError('maximum protocol trace mismatch')
    if production_counts(PLANE)[1]!=RPC_BUDGET:
        raise RuntimeError('RPC declaration mismatch')
    chunk = {'op':'model_chunk','token':'a'*64,'index':15,'data':base64.b64encode(b'\xff'*MAX_CHUNK_BYTES).decode()}
    messages = [chunk,{'ok':True},{'attributions':[[1000000.0]*20]*16},
                {'op':'explain','queries':[[-1.7976931348623157e308]*20]*16,'budget':8192,'workload':{'usable_seconds':10800.0,'remaining_explanations':18}},
                {'op':'model_start','token':'a'*64,'nbytes':MAX_DOCUMENT_BYTES,'sha256':'f'*64,'encoding':'base64','dtype':'uint8','shape':[MAX_DOCUMENT_BYTES],'content_type':'application/json'}]
    for message in messages:
        validate_message(message)
        bounded_json_line({'id':9223372036854775807,'request':message})
        bounded_json_line({'id':9223372036854775807,'response':message})
    if len(chunk['data'])!=4*((MAX_CHUNK_BYTES+2)//3):
        raise RuntimeError('base64 expansion mismatch')
    tree = {'left':[126]*127,'right':[126]*127,'feature':[19]*127,'threshold':[-1.7976931348623157e308]*127,'probability':[.9999999999999999]*127}
    representative = {'kind':'forest','dimension':20,'background':[[-1.7976931348623157e308]*20]*16,'parameters':{'trees':[tree]*64}}
    if len(compact(representative))>MAX_DOCUMENT_BYTES:
        raise RuntimeError('largest model bound')
    raw = b'x'*MAX_DOCUMENT_BYTES
    reconstructed = hashlib.sha256()
    for index,offset in enumerate(range(0,len(raw),MAX_CHUNK_BYTES)):
        message = {'op':'model_chunk','token':'a'*64,'index':index,'data':base64.b64encode(raw[offset:offset+MAX_CHUNK_BYTES]).decode()}
        validate_message(message)
        reconstructed.update(base64.b64decode(message['data']))
    if reconstructed.digest()!=hashlib.sha256(raw).digest():
        raise RuntimeError('maximum upload mock integrity')
    require_joint_workload_budget(search={'episode_count':11,'method_count':5,'wall_seconds':3600,'startup_seconds':300,'reset_seconds':5,'cleanup_seconds':1.2,'finish_seconds':90,'work_seconds':50},
                                  final={'episode_count':16,'method_count':5,'wall_seconds':10800,'startup_seconds':600,'reset_seconds':5,'cleanup_seconds':1.2,'finish_seconds':90,'work_seconds':110})


def verify_resources(root):
    for filename,expected in RESOURCE_HASHES.items():
        path = root/filename
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('frozen resource integrity failed')
    provenance = json.loads((root/'provenance.json').read_text())
    if provenance['cross_plane_retained_content_intersection']!=0:
        raise RuntimeError('split content overlap')


def make_episodes(seeds,settings):
    episodes = [{'case':case,'seed':seed,'replay':False} for case in ('german_logistic','german_forest','acs_logistic','acs_forest','controls') for seed in seeds]
    episodes.append({'case':'german_logistic','seed':seeds[0],'replay':True})
    for episode in episodes:
        episode['outcome'] = initial_outcome(episode,settings)
    return episodes


def aggregate(outcomes,settings,complete,elapsed):
    primary = [outcome for outcome in outcomes if not outcome['replay']]
    empirical = [outcome for outcome in primary if outcome['case']!='controls']
    controls = [outcome for outcome in primary if outcome['case']=='controls']
    empirical_metrics = np.mean([empirical_summary(outcome,settings) for outcome in empirical],axis=0)
    control_pass = float(np.mean([outcome['controls'] for outcome in controls]))
    first = outcomes[0]
    replay = outcomes[-1]
    replay_error = 1.
    if first['valid'] and replay['valid'] and first['solution'] is not None and replay['solution'] is not None:
        replay_error = float(min(1,np.max(abs(np.asarray(first['solution']['attributions'])-np.asarray(replay['solution']['attributions'])))))
    metrics = dict(zip(('reference_fidelity','top3_overlap','signed_agreement','efficiency_error'),map(float,empirical_metrics)))
    metrics.update(control_pass_rate=control_pass,failed_fraction=float(sum(not outcome['valid'] for outcome in primary)/len(primary)),replay_error=replay_error,wall_seconds=float(elapsed))
    if PLANE=='search':
        metrics['combined_score'] = .8*metrics['reference_fidelity']+.2*control_pass
    if not complete or not all(outcome['operational'] for outcome in outcomes):
        metrics['wall_seconds'] = float(WALL_SECONDS)
    correct = bool(complete and all(outcome['valid'] for outcome in outcomes) and control_pass==1 and replay_error<=1e-10)
    return metrics,correct


def evidence_records(outcomes,settings):
    records = []
    for seed in dict.fromkeys(outcome['seed'] for outcome in outcomes):
        selected = [outcome for outcome in outcomes if outcome['seed']==seed]
        primary = [outcome for outcome in selected if not outcome['replay']]
        empirical = [outcome for outcome in primary if outcome['case']!='controls']
        controls = [outcome for outcome in primary if outcome['case']=='controls']
        score = .8*float(np.mean([empirical_summary(outcome,settings)[0] for outcome in empirical]))+.2*float(np.mean([outcome['controls'] for outcome in controls]))
        seed_correct = all(outcome['valid'] for outcome in selected)
        replays = [outcome for outcome in selected if outcome['replay']]
        if seed_correct and replays:
            first = primary[0]['solution']['attributions']
            repeated = replays[0]['solution']['attributions']
            seed_correct = bool(np.max(abs(np.asarray(first)-np.asarray(repeated)))<=1e-10)
        records.append({'seed':seed,'score':score,'correct':bool(seed_correct),
                        'duration_seconds':float(sum(outcome['duration'] for outcome in selected)),
                        'solution':{'cases':[{'case':outcome['case'],'replay':outcome['replay'],'complete':outcome['operational'],'cells':outcome['cells'] if outcome['case']!='controls' else None,'repeat_pairs':outcome['repeat_pairs'] if outcome['case']!='controls' else None,'observations':outcome['solution']} for outcome in selected]}})
    return records


def write_results(directory,metrics,correct,feasible,evidence=None):
    if set(metrics)!=set(METRIC_NAMES) or any(type(value) not in (int,float) or not math.isfinite(value) for value in metrics.values()):
        raise RuntimeError('invalid evaluator scalar schema')
    directory.mkdir(parents=True,exist_ok=True)
    (directory/'metrics.json').write_bytes(compact(metrics)+b'\n')
    (directory/'correct.json').write_bytes(compact({'correct':bool(correct)})+b'\n')
    if os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1':
        (directory/'qualification.json').write_bytes(compact({'schema_version':1,'feasible':bool(feasible)})+b'\n')
    if evidence is not None:
        encoded = compact({'schema_version':1,'episodes':evidence})
        if len(encoded)>16*1024*1024:
            raise RuntimeError('evidence size bound')
        (directory/'evaluation_evidence.json').write_bytes(encoded+b'\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--program_path',required=True,type=Path)
    parser.add_argument('--results_dir',required=True,type=Path)
    arguments = parser.parse_args()
    smoke = os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1'
    settings = {'instances':2 if smoke else 8 if PLANE=='search' else 16,'background':4 if smoke else 16,
                'repetitions':2 if smoke else 4 if PLANE=='search' else 6,'budgets':[16] if smoke else [64,256] if PLANE=='search' else [64,256,1024]}
    seeds = SEEDS[:1] if smoke else SEEDS
    plane_wall = 120 if smoke else WALL_SECONDS
    startup_allowance = 5 if smoke else 300 if PLANE=='search' else 600
    hard_deadline = START_TIME+plane_wall-startup_allowance
    finish_reserve = 5 if smoke else 90
    work_seconds = 2.5 if smoke else 50 if PLANE=='search' else 110
    episodes = make_episodes(seeds,settings)
    outcomes = [episode['outcome'] for episode in episodes]
    client = None
    try:
        preflight()
        root = Path(os.environ.get('TASK_SOURCE_DIR',str(Path(__file__).resolve().parent)))/'resources'/PLANE
        verify_resources(root)
        science()
        check_interrupted_agreement()
        client = CandidateClient(arguments.program_path)
        outcomes,complete = run_declared_episodes(episodes,hard_deadline=hard_deadline,finish_reserve=finish_reserve,reset_timeout=5,episode_overhead=6,
                    rpc_cap=work_seconds,clock=time.monotonic,rpc=client.rpc,
                    evaluate=lambda episode,call,deadline:evaluate_episode(episode,call,deadline,settings=settings,root=root,work_seconds=work_seconds,smoke=smoke),
                    worst_case=lambda episode:episode['outcome'],record_failure=record_failure)
        client.close()
        client = None
        elapsed = time.monotonic()-START_TIME
        metrics,correct = aggregate(outcomes,settings,complete,elapsed)
        feasible = not smoke and complete and all(outcome['operational'] for outcome in outcomes) and metrics['replay_error']<=1e-10 and elapsed<=WALL_SECONDS-startup_allowance
        write_results(arguments.results_dir,metrics,correct,feasible,evidence_records(outcomes,settings))
    except Exception as error:
        if client is not None:
            try:
                client.close()
            except (OSError,RuntimeError,subprocess.TimeoutExpired):
                error.add_note('secondary candidate cleanup failure')
            client = None
        metrics = {name:0. for name in METRIC_NAMES}
        for name in ('efficiency_error','failed_fraction','replay_error'):
            metrics[name] = 1.
        metrics['wall_seconds'] = float(WALL_SECONDS)
        if 'np' in globals():
            metrics,_ = aggregate(outcomes,settings,False,float(WALL_SECONDS))
        write_results(arguments.results_dir,metrics,False,False)
        if PLANE=='search':
            name = bounded_failure_name(type(error).__name__.lower(),'evaluator_exception')
            print(f'evaluator_exception type={name} message=evaluation_failed',file=sys.stderr,flush=True)
        else:
            print('evaluator_exception type=runtime_error message=sealed_evaluation_failed',file=sys.stderr,flush=True)
        raise SystemExit(1) from None
    finally:
        if client is not None:
            client.close()


if __name__=='__main__':
    if len(sys.argv)==2 and sys.argv[1]=='--baseline-worker':
        try:
            request = json.load(sys.stdin)
            result = baseline_work(request)
            sys.stdout.buffer.write(compact(result)+b'\n')
            sys.stdout.buffer.flush()
        except Exception as error:
            if PLANE=='search' and os.environ.get('WORKER_REPAIR_MODE')=='1':
                report_worker_exception(error)
            else:
                print('baseline_worker_failure',file=sys.stderr,flush=True)
            raise SystemExit(1) from None
    else:
        main()
