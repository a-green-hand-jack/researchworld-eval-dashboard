"""Offline, evaluator-owned post-selection reporting experiment.

Run with --program_path ENTRYPOINT --results_dir DIRECTORY. Final is standalone.
Scientific validity has no superiority threshold; publication claims require analysis.
"""
import argparse
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
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

PLANE = 'search'
SEEDS = [101, 211, 307]
REPLICATES = 256
WALL_SECONDS = 21600
RPC_BUDGET = 50
DEFAULT_PROMPT = 'Answer the multiple-choice question. Return only the correct option letter A through J.'
WIRE_LIMIT = 64 * 1024 * 1024
INLINE_LIMIT = 8 * 1024 * 1024
METRICS = ('combined_score report_mse reuse_mse full_budget_naive_mse honest_half_mse fixed_prompt_mse random_prompt_mse selected_accuracy report_bias signed_optimism coverage interval_width decision_reversal_rate failure_rate control_failure_rate replay_discrepancy correct').split()
ORDINARY = METRICS[1:-2]
STARTED = time.monotonic()
FAILURE_RECORDED = False

class ProtocolFailure(RuntimeError):
    pass

class TransportFailure(RuntimeError):
    pass

class CandidateCallInterrupted(BaseException):
    def __init__(self,failure):
        self.failure=failure

class InvalidResetResponse(RuntimeError):
    pass

def require_reset_ack(response):
    if type(response) is not dict or set(response) != {'ok'} or response['ok'] is not True:
        raise InvalidResetResponse('invalid reset response')

def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,79}', value) else fallback

class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, 'invalid_baseline_diagnostic')
        super().__init__('required baseline failed')

def describe_episode_failure(error, operation):
    context = error
    for unused in range(8):
        if isinstance(context, InvalidResetResponse):
            return {'component':'candidate','category':'invalid_reset_response','operation':'reset'}
        if isinstance(context, RequiredBaselineFailure):
            return {'component':'baseline','category':context.category,'operation':'baseline_worker'}
        if isinstance(context, ProtocolFailure):
            return {'component':'candidate','category':'malformed_response','operation':bounded_failure_name(operation,'unknown')}
        if isinstance(context, TransportFailure):
            return {'component':'candidate','category':'transport_failure','operation':bounded_failure_name(operation,'unknown')}
        context = context.__context__
        if context is None:
            break
    return {'component':'candidate','category':'timeout','operation':bounded_failure_name(operation,'unknown')}

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
    global FAILURE_RECORDED
    if FAILURE_RECORDED:
        return
    FAILURE_RECORDED=True
    if isinstance(failure,str):
        failure = {'component':'baseline','category':failure,'operation':'baseline_worker'}
    parts = [bounded_failure_name(failure.get(name),'unknown') for name in ['component','category','operation']]
    print('episode_failure component=%s category=%s operation=%s' % tuple(parts), file=sys.stderr, flush=True)

def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(',', ':')).encode('utf-8') + b'\n'
    except (TypeError,ValueError,RecursionError,OverflowError) as error:
        raise ProtocolFailure('invalid finite JSON value') from error
    if len(encoded) >= min(wire_limit, INLINE_LIMIT):
        raise ProtocolFailure('complete message exceeds wire limit')
    return encoded

def no_duplicates(pairs):
    result = {}
    for key,value in pairs:
        if key in result:
            raise ProtocolFailure('duplicate JSON key')
        result[key] = value
    return result

def decode(data):
    try:
        value = json.loads(data, object_pairs_hook=no_duplicates, parse_constant=lambda value: (_ for _ in ()).throw(ProtocolFailure('nonfinite JSON')))
        bounded_json_line(value)
        return value
    except (ValueError,TypeError,RecursionError) as error:
        raise ProtocolFailure('invalid JSON') from error

class BoundedWorkerStderr:
    LIMIT = 4096
    def __init__(self,stream):
        self.stream = stream
        self.fd = stream.fileno()
        os.set_blocking(self.fd,False)
        self.lines = collections.deque()
        self.pending = bytearray()
        self.dropping_line = False
        self.observed_bytes = 0
        self.retained_bytes = 0
        self.truncated = False
        self.capture_error = None
        self.stop = threading.Event()
        self.result = None
        self.reader = threading.Thread(target=self._drain,name='worker-stderr-reader')
        self.reader.start()
    def _accept(self,chunk):
        self.observed_bytes += len(chunk)
        for segment in chunk.splitlines(keepends=True):
            complete = segment.endswith(b'\n')
            if not self.dropping_line:
                if len(self.pending)+len(segment)>self.LIMIT:
                    self.pending.clear()
                    self.dropping_line=True
                    self.truncated=True
                else:
                    self.pending.extend(segment)
            if complete:
                if not self.dropping_line:
                    line=bytes(self.pending).decode('utf-8',errors='replace')
                    size=len(line.encode('utf-8'))
                    if size<=self.LIMIT:
                        while self.retained_bytes+size>self.LIMIT:
                            self.retained_bytes-=len(self.lines.popleft().encode('utf-8'))
                            self.truncated=True
                        self.lines.append(line)
                        self.retained_bytes+=size
                    else:
                        self.truncated=True
                self.pending.clear()
                self.dropping_line=False
    def _drain(self):
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(self.fd,selectors.EVENT_READ)
                while not self.stop.is_set():
                    if not selector.select(timeout=.05):
                        continue
                    try:
                        chunk=os.read(self.fd,8192)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        return
                    self._accept(chunk)
                self.capture_error='reader_stopped_before_eof'
                self.truncated=True
        except (OSError,ValueError):
            self.capture_error='stderr_capture_failed'
            self.truncated=True
        finally:
            if self.pending or self.dropping_line:
                self.truncated=True
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
        self.result={'stderr':''.join(self.lines),'observed_bytes':self.observed_bytes,'retained_bytes':self.retained_bytes,'truncated':self.truncated,'capture_error':self.capture_error}
        return dict(self.result)

def repair_mode():
    return PLANE=='search' and (os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1' or os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1')

def report_worker_exception(error):
    name=type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name)>80:
        name='WorkerException'
    try:
        message=str(error)
    except Exception:
        message='<exception message unavailable>'
    if len(message)>2048 or len(message.encode('utf-8',errors='replace'))>2048:
        message='<exception message omitted: too large>'
    print(f'worker_exception type={name}\n{message}',file=sys.stderr,flush=True)
    trace=error.__traceback__
    for unused in range(12):
        if trace is None:
            break
        function=trace.tb_frame.f_code.co_name
        if not function.isascii() or not function.isidentifier() or len(function)>80:
            function='unknown'
        print(f'worker_exception_frame function={function} line={trace.tb_lineno}',file=sys.stderr,flush=True)
        trace=trace.tb_next

def candidate_subprocess_settings(parent_environment):
    runtime_names=('PATH','LD_LIBRARY_PATH','LANG','LC_ALL','TZ','CUDA_VISIBLE_DEVICES','NVIDIA_VISIBLE_DEVICES','NVIDIA_DRIVER_CAPABILITIES','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS','XLA_PYTHON_CLIENT_PREALLOCATE','XLA_PYTHON_CLIENT_MEM_FRACTION','XLA_PYTHON_CLIENT_ALLOCATOR')
    environment={name:parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME='/nonexistent',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1')
    environment.update(OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',MKL_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
    return parent_environment.get('TASK_PYTHON',sys.executable),environment

def record_rpc_failure(error,request,started,timeout,call_index):
    try:
        operation=bounded_failure_name(request.get('op'),'unknown')
        if isinstance(error,(TimeoutError,RequiredBaselineFailure,ProtocolFailure,TransportFailure)):
            failure=describe_episode_failure(error,operation)
        else:
            failure={'component':'candidate','category':'rpc_exception','operation':operation}
        record_failure(failure)
        print('rpc_failure component=%s category=%s operation=%s elapsed_ms=%d allowance_ms=%d call_index=%d' % (failure['component'],failure['category'],failure['operation'],max(0,int((time.monotonic()-started)*1000)),max(0,int(timeout*1000)),call_index),file=sys.stderr,flush=True)
        if repair_mode():
            report_worker_exception(error)
    except Exception:
        error.add_note('RPC diagnostic recording failed')

NATIVE_WORKER = r'''
import ctypes, errno, importlib.util, json, os, pathlib, resource, sys
resource.setrlimit(resource.RLIMIT_AS,(8*1024**3,8*1024**3))
resource.setrlimit(resource.RLIMIT_CPU,(__CPU__,__CPU__))
resource.setrlimit(resource.RLIMIT_FSIZE,(1024*1024,1024*1024))
resource.setrlimit(resource.RLIMIT_NOFILE,(64,64))
resource.setrlimit(resource.RLIMIT_NPROC,(32,32))
resource.setrlimit(resource.RLIMIT_CORE,(0,0))
os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:2])
libc=ctypes.CDLL(None,use_errno=True)
class Ruleset(ctypes.Structure):
    _fields_=[('handled',ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_=1
    _fields_=[('allowed',ctypes.c_uint64),('parent_fd',ctypes.c_int32)]
handled=(1<<14)-1
rules=Ruleset(handled)
descriptor=libc.syscall(444,ctypes.byref(rules),ctypes.sizeof(rules),0)
if descriptor<0:
    raise RuntimeError('Landlock unavailable; refusing unsafe native execution')
read_access=(1<<0)|(1<<2)|(1<<3)
roots=[str(pathlib.Path(sys.argv[1]).parent),sys.prefix,'/usr','/lib','/lib64','/etc/ld.so.cache','/dev/null','/dev/urandom']
for root in dict.fromkeys(roots):
    if not os.path.exists(root):
        continue
    parent=os.open(root,os.O_PATH|os.O_CLOEXEC)
    access=read_access if os.path.isdir(root) else (1<<2)
    rule=PathRule(access,parent)
    if libc.syscall(445,descriptor,1,ctypes.byref(rule),0)<0:
        raise RuntimeError('Landlock rule failed')
    os.close(parent)
if libc.prctl(38,1,0,0,0) or libc.syscall(446,descriptor,0):
    raise RuntimeError('Landlock restriction failed')
os.close(descriptor)
sec=ctypes.CDLL('libseccomp.so.2')
sec.seccomp_init.argtypes=[ctypes.c_uint32]
sec.seccomp_init.restype=ctypes.c_void_p
sec.seccomp_syscall_resolve_name.argtypes=[ctypes.c_char_p]
sec.seccomp_rule_add.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint]
sec.seccomp_load.argtypes=[ctypes.c_void_p]
sec.seccomp_release.argtypes=[ctypes.c_void_p]
context=sec.seccomp_init(0x7fff0000)
for name in ['socket','socketpair','connect','bind','listen','accept','accept4','ptrace','process_vm_readv','process_vm_writev','kill','tkill','tgkill','execve','execveat','fork','vfork','mount','unshare','setns','setsid','setpgid','sched_setaffinity','truncate','ftruncate']:
    number=sec.seccomp_syscall_resolve_name(name.encode())
    if number>=0 and sec.seccomp_rule_add(context,0x50000|errno.EPERM,number,0):
        raise RuntimeError('seccomp rule failed')
class ArgumentComparison(ctypes.Structure):
    _fields_=[('argument',ctypes.c_uint),('operation',ctypes.c_uint),('mask',ctypes.c_uint64),('value',ctypes.c_uint64)]
comparison=ArgumentComparison(0,7,0x10000,0)
sec.seccomp_rule_add_array.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_int,ctypes.c_uint,ctypes.POINTER(ArgumentComparison)]
if sec.seccomp_rule_add_array(context,0x50000|errno.EPERM,sec.seccomp_syscall_resolve_name(b'clone'),1,ctypes.byref(comparison)):
    raise RuntimeError('seccomp clone restriction failed')
clone3=sec.seccomp_syscall_resolve_name(b'clone3')
if clone3>=0 and sec.seccomp_rule_add(context,0x50000|errno.ENOSYS,clone3,0):
    raise RuntimeError('seccomp clone3 restriction failed')
if sec.seccomp_load(context):
    raise RuntimeError('seccomp restriction failed')
sec.seccomp_release(context)
sys.path.insert(0,str(pathlib.Path(sys.argv[1]).parent))
spec=importlib.util.spec_from_file_location('candidate',sys.argv[1])
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    request=json.loads(line)
    response=module.handle(request)
    encoded=json.dumps(response,allow_nan=False,separators=(',',':')).encode()+b'\n'
    if len(encoded)>=8*1024*1024:
        raise ValueError('response too large')
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''

class PipeWorker:
    def __init__(self,command,environment,cwd=None):
        self.process=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=environment,cwd=cwd,start_new_session=True,shell=False,bufsize=0)
        self.stderr=BoundedWorkerStderr(self.process.stderr)
        self.pending=bytearray()
        self.closed=False
        self.cleanup_error=None
        os.set_blocking(self.process.stdout.fileno(),False)
        os.set_blocking(self.process.stdin.fileno(),False)
    def read(self,timeout):
        deadline=time.monotonic()+timeout
        while True:
            if b'\n' in self.pending:
                line,rest=self.pending.split(b'\n',1)
                self.pending=bytearray(rest)
                return decode(line)
            if len(self.pending)>=INLINE_LIMIT:
                raise ProtocolFailure('oversize response')
            remaining=deadline-time.monotonic()
            if remaining<=0:
                raise TimeoutError()
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdout,selectors.EVENT_READ)
                if not selector.select(remaining):
                    raise TimeoutError()
            chunk=os.read(self.process.stdout.fileno(),65536)
            if not chunk:
                raise ProtocolFailure('worker closed response stream')
            self.pending.extend(chunk)
    def call(self,request,timeout):
        started=time.monotonic()
        payload=memoryview(bounded_json_line(request))
        while payload:
            remaining=timeout-(time.monotonic()-started)
            if remaining<=0:
                raise TimeoutError()
            with selectors.DefaultSelector() as selector:
                selector.register(self.process.stdin,selectors.EVENT_WRITE)
                if not selector.select(remaining):
                    raise TimeoutError()
            try:
                written=os.write(self.process.stdin.fileno(),payload)
            except BrokenPipeError as error:
                raise ProtocolFailure('worker closed input stream') from error
            payload=payload[written:]
        return self.read(max(.001,timeout-(time.monotonic()-started)))
    def close(self,failed=False,component='candidate'):
        if self.closed:
            if self.cleanup_error is not None:
                raise self.cleanup_error
            return
        errors=[]
        snapshot=None
        def terminate(kind):
            try:
                os.killpg(self.process.pid,kind)
            except ProcessLookupError:
                pass
            except OSError as error:
                errors.append(error)
        try:
            if self.process.poll() is None:
                terminate(signal.SIGTERM)
                try:
                    self.process.wait(timeout=.5)
                except (subprocess.TimeoutExpired,OSError) as error:
                    if not isinstance(error,subprocess.TimeoutExpired):
                        errors.append(error)
            terminate(signal.SIGKILL)
            try:
                self.process.wait(timeout=.5)
            except (subprocess.TimeoutExpired,OSError) as error:
                errors.append(error)
        finally:
            for stream in [self.process.stdin,self.process.stdout]:
                try:
                    stream.close()
                except Exception as error:
                    errors.append(error)
            try:
                snapshot=self.stderr.close()
            except Exception as error:
                errors.append(error)
            self.closed=True
            if errors:
                self.cleanup_error=RuntimeError('worker cleanup failed')
        if failed:
            code=self.process.returncode
            print('worker_failure component=%s exit=%d signal=%d' % (component,code if code is not None and code>=0 else -1,-code if code is not None and code<0 else 0),file=sys.stderr,flush=True)
        if failed and repair_mode() and snapshot is not None:
            print('worker_capture component=%s bytes=%d truncated=%d capture_error=%s' % (component,snapshot['observed_bytes'],snapshot['truncated'],snapshot['capture_error'] or 'none'),file=sys.stderr)
            if snapshot['stderr']:
                print(snapshot['stderr'],file=sys.stderr,end='')
        if self.cleanup_error is not None:
            print('worker_cleanup_failure component='+component,file=sys.stderr,flush=True)
            raise self.cleanup_error from errors[0]

def bounded_candidate_dispatch(call,request,*,timeout,check_required):
    if type(timeout) not in (int,float) or not math.isfinite(timeout) or timeout<=0:
        raise TimeoutError('invalid RPC allowance')
    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError('candidate dispatch requires the evaluator main thread')
    deadline=time.monotonic()+timeout
    previous_handler=signal.getsignal(signal.SIGALRM)
    if signal.getitimer(signal.ITIMER_REAL)!=(0.0,0.0):
        raise RuntimeError('candidate dispatch timer already in use')
    def poll(unused_signal=None,unused_frame=None):
        signal.setitimer(signal.ITIMER_REAL,0)
        try:
            check_required()
            remaining=deadline-time.monotonic()
            if remaining<=0:
                raise TimeoutError('candidate RPC deadline exceeded')
        except (TimeoutError,RequiredBaselineFailure) as error:
            if repair_mode():
                frame=unused_frame
                for unused in range(12):
                    if frame is None:
                        break
                    function=frame.f_code.co_name
                    if not function.isascii() or not function.isidentifier() or len(function)>80:
                        function='unknown'
                    print('rpc_interrupted_frame function=%s line=%d' % (function,frame.f_lineno),file=sys.stderr,flush=True)
                    frame=frame.f_back
            raise CandidateCallInterrupted(error) from None
        signal.setitimer(signal.ITIMER_REAL,min(.02,remaining))
    signal.signal(signal.SIGALRM,poll)
    try:
        poll()
        response=call(request)
        signal.setitimer(signal.ITIMER_REAL,0)
        check_required()
        if time.monotonic()>deadline:
            raise TimeoutError('late candidate RPC response')
        return response
    except CandidateCallInterrupted as interruption:
        raise interruption.failure from None
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous_handler)

class Candidate:
    def __init__(self,path,baseline=None):
        self.calls=0
        self.worker=None
        self.directory=None
        self.proxy=None
        self.baseline=baseline
        self.transport_failed=False
        broker_path=path=='/broker-code/candidate_proxy.py'
        broker_socket=bool(os.environ.get('AGENTIC_CANDIDATE_SOCKET'))
        if broker_path and broker_socket:
            spec=importlib.util.spec_from_file_location('trusted_candidate_proxy',path)
            self.proxy=importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.proxy)
        else:
            self.directory=tempfile.TemporaryDirectory(prefix='report-candidate-')
            self.path=Path(self.directory.name)/'code'/Path(path).name
            self.path.parent.mkdir()
            shutil.copyfile(Path(path).resolve(),self.path)
            self.interpreter,self.environment=candidate_subprocess_settings(os.environ)
    def call(self,request,timeout):
        self.calls+=1
        if self.calls>RPC_BUDGET:
            raise ProtocolFailure('RPC budget exceeded')
        bounded_json_line(request)
        if self.proxy is not None:
            if self.transport_failed:
                raise TransportFailure('broker transport unavailable')
            started=time.monotonic()
            try:
                def invoke(value):
                    result=self.proxy.handle(value)
                    bounded_json_line(result)
                    return result
                response=bounded_candidate_dispatch(invoke,request,timeout=timeout,check_required=self.check_required if request['op']!='reset' else lambda:None)
            except RequiredBaselineFailure as error:
                record_rpc_failure(error,request,started,timeout,self.calls)
                raise
            except TimeoutError as error:
                record_rpc_failure(error,request,started,timeout,self.calls)
                raise
            except (OSError,EOFError) as error:
                self.transport_failed=True
                failure=TransportFailure('broker transport failed')
                record_rpc_failure(failure,request,started,timeout,self.calls)
                raise failure from error
            except Exception as error:
                record_rpc_failure(error,request,started,timeout,self.calls)
                raise
            if repair_mode() and request['op']=='reset':
                print('rpc_reset_completed elapsed_ms=%d call_index=%d' % (max(0,int((time.monotonic()-started)*1000)),self.calls),file=sys.stderr,flush=True)
            return response
        if request['op']=='reset':
            if self.worker is not None:
                self.worker.close()
            script=NATIVE_WORKER.replace('__CPU__',str(math.ceil(WALL_SECONDS*2)))
            self.worker=PipeWorker([self.interpreter,'-I','-u','-c',script,str(self.path)],self.environment,self.directory.name)
        try:
            return bounded_candidate_dispatch(lambda value:self.worker.call(value,timeout),request,timeout=timeout,check_required=self.check_required if request['op']!='reset' else lambda:None)
        except RequiredBaselineFailure as error:
            try:
                self.worker.close(failed=True)
            except Exception:
                error.add_note('candidate cleanup failed')
            raise
        except (ProtocolFailure,TimeoutError) as error:
            try:
                self.worker.close(failed=True)
            except Exception:
                error.add_note('candidate cleanup failed')
            raise
    def check_required(self):
        if self.baseline is not None:
            category=self.baseline.status()
            if category is not None:
                self.baseline.fail(category)
    def close(self):
        try:
            if self.worker is not None:
                self.worker.close()
        finally:
            if self.directory is not None:
                self.directory.cleanup()

def inference_worker(root):
    import resource
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    resource.setrlimit(resource.RLIMIT_CPU,(WALL_SECONDS*6,WALL_SECONDS*6))
    resource.setrlimit(resource.RLIMIT_AS,(20*1024**3,20*1024**3))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    torch.set_num_threads(2)
    torch.set_num_interop_threads(1)
    torch.manual_seed(0)
    torch.use_deterministic_algorithms(True)
    model=AutoModelForCausalLM.from_pretrained(str(Path(root)/'model'),local_files_only=True,torch_dtype=torch.float32,attn_implementation='sdpa').eval()
    tokenizer=AutoTokenizer.from_pretrained(str(Path(root)/'model'),local_files_only=True)
    tokenizer.padding_side='left'
    tokenizer.pad_token=tokenizer.eos_token
    print(json.dumps({'ready':True}),flush=True)
    cache={}
    generated_calls=0
    generated_tokens=0
    for line in sys.stdin.buffer:
        request=decode(line)
        rows=request['rows']
        prompts=request['prompts']
        predictions=[[-1]*len(prompts) for row in rows]
        missing=[]
        for row_index,row in enumerate(rows):
            question=row['question']+'\n'+'\n'.join(chr(65+index)+'. '+option for index,option in enumerate(row['options']))
            for arm,prompt in enumerate(prompts):
                key=(row['content_hash'],prompt)
                if key in cache:
                    predictions[row_index][arm]=cache[key]
                else:
                    text=tokenizer.apply_chat_template([{'role':'user','content':prompt+'\n\n'+question}],tokenize=False,add_generation_prompt=True)
                    tokens=tokenizer(text,add_special_tokens=False)['input_ids']
                    if len(tokens)>2044:
                        cache[key]=-1
                        continue
                    missing.append((row_index,arm,key,tokens))
        missing.sort(key=lambda item:len(item[3]))
        for offset in range(0,len(missing),8):
            batch=missing[offset:offset+8]
            if generated_calls+len(batch)>16*2048:
                raise RuntimeError('inference call ceiling')
            inputs=tokenizer.pad({'input_ids':[item[3] for item in batch]},padding=True,return_tensors='pt')
            with torch.inference_mode():
                legal_tokens=[]
                for item in batch:
                    legal=[]
                    for letter in range(len(rows[item[0]]['options'])):
                        encoded=tokenizer.encode(chr(65+letter),add_special_tokens=False)
                        if len(encoded)!=1:
                            raise RuntimeError('answer-letter tokenization unsupported')
                        legal.append(encoded[0])
                    legal_tokens.append(legal)
                output=model.generate(**inputs,do_sample=False,max_new_tokens=1,pad_token_id=tokenizer.pad_token_id,use_cache=True,prefix_allowed_tokens_fn=lambda batch_index,input_ids:legal_tokens[batch_index])
            generated_calls+=len(batch)
            generated_tokens+=len(batch)*(output.shape[1]-inputs['input_ids'].shape[1])
            if generated_tokens>16*2048*4:
                raise RuntimeError('inference token ceiling')
            for item,sequence in zip(batch,output):
                text=tokenizer.decode(sequence[inputs['input_ids'].shape[1]:],skip_special_tokens=True).strip()
                match=re.fullmatch(r'([A-J])(?:[.\s]*)',text)
                answer=ord(match.group(1))-65 if match else -1
                cache[item[2]]=answer
                predictions[item[0]][item[1]]=answer
        print(json.dumps({'predictions':predictions},separators=(',',':')),flush=True)

class Baseline:
    def __init__(self,root,deadline):
        environment={name:os.environ[name] for name in ['PATH','LD_LIBRARY_PATH','LANG','LC_ALL','TZ'] if name in os.environ}
        environment.update(HOME='/nonexistent',PYTHONNOUSERSITE='1',PYTHONDONTWRITEBYTECODE='1',PYTHONUNBUFFERED='1',OMP_NUM_THREADS='6',OPENBLAS_NUM_THREADS='6',MKL_NUM_THREADS='6',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
        for name in ['AGENTIC_TASK_DRAFT_SMOKE','AGENTIC_TASK_QUALIFICATION']:
            if os.environ.get(name)=='1':
                environment[name]='1'
        self.worker=PipeWorker([sys.executable,'-I','-u',str(Path(__file__).resolve()),'--inference_worker',str(root)],environment)
        self.failure=None
        try:
            if self.worker.read(min(45,deadline-time.monotonic()))!={'ready':True}:
                raise ProtocolFailure('invalid baseline readiness')
        except (TimeoutError,ProtocolFailure) as error:
            self.failure='baseline_timeout' if isinstance(error,TimeoutError) else self.status() or 'baseline_result_failure'
            record_failure(self.failure)
            try:
                self.worker.close(failed=True,component='baseline')
            except Exception:
                error.add_note('baseline cleanup failed')
    def status(self):
        if self.failure:
            return self.failure
        code=self.worker.process.poll()
        return None if code is None else ('baseline_signal' if code<0 else 'baseline_exit')
    def fail(self,category):
        self.failure=category
        fail_required_baseline(category,lambda:self.worker.close(failed=True,component='baseline'),record_failure)
    def call(self,request,timeout):
        category=self.status()
        if category:
            self.fail(category)
        try:
            result=self.worker.call(request,timeout)
            category=self.status()
            if category:
                self.fail(category)
            return result
        except (TimeoutError,ProtocolFailure) as error:
            if isinstance(error,ProtocolFailure) and self.worker.process.poll() is None:
                try:
                    self.worker.process.wait(timeout=.05)
                except subprocess.TimeoutExpired:
                    pass
            self.fail(self.status() or ('baseline_timeout' if isinstance(error,TimeoutError) else 'baseline_result_failure'))
    def close(self):
        self.worker.close(component='baseline')

def normalized(text):
    return ' '.join(unicodedata.normalize('NFKC',text).split())

def digest(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def load_resources(root,smoke):
    runtime=json.loads((root/'runtime_manifest.json').read_text())
    for relative,expected in runtime['sha256'].items():
        path=root/relative
        checksum=hashlib.sha256()
        with path.open('rb') as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):
                checksum.update(block)
        if checksum.hexdigest()!=expected:
            raise RuntimeError('immutable resource checksum mismatch')
    manifest=json.loads((root/'split_manifest.json').read_text())
    rows=json.loads((root/('smoke_examples.json' if smoke and PLANE=='final' else 'examples.json')).read_text())
    other_stems=set(manifest['other_stem_hashes'])
    other_content=set(manifest['other_content_hashes'])
    seen=set()
    for row in rows:
        stem=digest(normalized(row['question']))
        content=digest([normalized(row['question']),sorted(map(normalized,row['options']))])
        if stem!=row['stem_hash'] or content!=row['content_hash'] or stem in seen or stem in other_stems or content in other_content:
            raise RuntimeError('normalized raw-content split audit failed')
        seen.add(stem)
    return rows,json.loads((root/'synthetic_manifest.json').read_text())

def validate_plan(response,request):
    if type(response) is not dict or set(response)!={'prompts','selection','report','weights','tie_order'}:
        raise ProtocolFailure('invalid plan keys')
    prompts=response['prompts']
    if type(prompts) is not list or len(prompts)!=16 or any(type(prompt) is not str for prompt in prompts) or len(set(prompts))!=16 or prompts[0]!=DEFAULT_PROMPT:
        raise ProtocolFailure('invalid prompt bank')
    for prompt in prompts:
        try:
            byte_length=len(prompt.encode('utf-8'))
        except UnicodeError as error:
            raise ProtocolFailure('invalid prompt Unicode') from error
        if not 1<=byte_length<=4096 or any(ord(char)<32 and char not in '\n\t' for char in prompt):
            raise ProtocolFailure('invalid prompt text')
        if re.search(r'(?:[0-9a-f]{32,}|https?://|question_id|answer_index)',prompt,re.I):
            raise ProtocolFailure('example-specific prompt lookup forbidden')
    keys=[slot['key'] for slot in request['slots']]
    selection,report=response['selection'],response['report']
    if any(type(part) is not list or any(type(key) is not str for key in part) for part in [selection,report]):
        raise ProtocolFailure('invalid partition')
    if not len(keys)/4<=len(selection)<=3*len(keys)/4 or not report or len(selection)+len(report)!=len(keys) or len(set(selection+report))!=len(keys) or set(selection+report)!=set(keys):
        raise ProtocolFailure('partition is not exhaustive and disjoint')
    weights=response['weights']
    if type(weights) is not list or len(weights)!=len(report) or any(type(weight) not in (int,float) or not math.isfinite(weight) or not math.isclose(weight,1/len(report),rel_tol=0,abs_tol=1e-12) for weight in weights):
        raise ProtocolFailure('report weights must be uniform')
    order=response['tie_order']
    if type(order) is not list or any(type(arm) is not int for arm in order) or sorted(order)!=list(range(request['arms'])):
        raise ProtocolFailure('invalid tie order')
    return response

def wilson(mean,count):
    variance=mean*(1-mean)/count+1.959963984540054**2/(4*count*count)
    denominator=1+1.959963984540054**2/count
    center=(mean+1.959963984540054**2/(2*count))/denominator
    half=1.959963984540054*math.sqrt(max(0,variance))/denominator
    return center-half,center+half

def estimate(matrix,selection,report,order,weights=None):
    import numpy as np
    means=matrix[selection].mean(axis=0)
    winner=max(order,key=lambda arm:means[arm])
    reported=float(matrix[report,winner].mean()) if weights is None else float(np.dot(matrix[report,winner],weights))
    return winner,reported,float(means[winner]),wilson(reported,len(report))

def summarize(matrix,truth,selection,report,order,random_arm):
    import numpy as np
    size,arms=matrix.shape
    indices=list(range(size))
    candidate=estimate(matrix,selection,report,order,[1/len(report)]*len(report))
    winner,reported,reused,interval=candidate
    full=estimate(matrix,indices,indices,list(range(arms)))
    half=estimate(matrix,indices[:size//2],indices[size//2:],list(range(arms)))
    fixed=float(matrix[:,0].mean())
    random=float(matrix[:,random_arm].mean())
    target=float(truth[winner])
    result={
        'report_mse':(reported-target)**2,'reuse_mse':(reused-target)**2,
        'full_budget_naive_mse':(full[1]-float(truth[full[0]]))**2,
        'honest_half_mse':(half[1]-float(truth[half[0]]))**2,
        'fixed_prompt_mse':(fixed-float(truth[0]))**2,
        'random_prompt_mse':(random-float(truth[random_arm]))**2,
        'selected_accuracy':target,'report_bias':reported-target,'signed_optimism':reused-target,
        'coverage':float(interval[0]<=target<=interval[1]),'interval_width':interval[1]-interval[0],
        'decision_reversal_rate':float((reported-fixed)*(target-float(truth[0]))<0),
        'failure_rate':0.0,'control_failure_rate':0.0}
    return result,{'winner':winner,'report':reported,'target':target,'reuse':reused,'interval':list(interval),'full_naive':[full[0],full[1],float(truth[full[0]])],'honest_half':[half[0],half[1],float(truth[half[0]])],'fixed':[fixed,float(truth[0])],'random':[random_arm,random,float(truth[random_arm])]}

EXPECTED_CONTROLS={'constant','copy_arm','copy_report','permuted_input'}

def controls(matrix,selection,report,order,permuted,effective_changes):
    import numpy as np
    completed=set()
    observations={}
    for name,transformed in [('constant',np.zeros_like(matrix)),('copy_arm',np.repeat(matrix[:,:1],matrix.shape[1],axis=1))]:
        winner,value,reused,interval=estimate(transformed,selection,report,order)
        if winner!=order[0] or not np.all(transformed==transformed[:,:1]):
            raise ProtocolFailure('constant/copy-arm control failed')
        completed.add(name)
        observations[name]={'winner':winner,'report':value,'reuse':reused}
    copied=estimate(matrix,selection,selection,order)
    if not set(selection).intersection(selection) or copied[1]!=copied[2]:
        raise ProtocolFailure('copy-report independence control failed')
    completed.add('copy_report')
    observations['copy_report']={'report':copied[1],'independence_audit_passed':False}
    if effective_changes<2 or permuted.shape!=matrix.shape:
        raise ProtocolFailure('vacuous permutation control')
    shuffled=estimate(permuted,selection,report,order)
    observations['permuted_input']={'winner':shuffled[0],'report':shuffled[1],'changed_assignments':effective_changes}
    completed.add('permuted_input')
    if EXPECTED_CONTROLS-completed:
        raise ProtocolFailure('missing control')
    return observations

def worst_case(episode):
    values={name:1.0 for name in ORDINARY}
    for name in ['selected_accuracy','coverage']:
        values[name]=0.0
    solution={'case':episode['family']+str(episode['n'])+'K'+str(episode['arms']),'metrics':values,'details':[],'completed_controls':[]}
    return {'metrics':values,'solution':solution,'duration':0.0,'valid':False}

def average(values):
    if not values:
        raise RuntimeError('empty fixed aggregation')
    if not all(math.isfinite(float(value)) for value in values):
        raise RuntimeError('nonfinite contribution')
    return math.fsum(values)/len(values)

def reserved_method_deadline(*,now,episode_deadline,methods_remaining,work_seconds,cleanup_seconds):
    needed=(methods_remaining+1)*(work_seconds+cleanup_seconds)
    if work_seconds<=0 or now+needed>episode_deadline:
        raise TimeoutError('insufficient matched method reservations')
    return now+work_seconds

def run_declared_episodes(episodes,*,hard_deadline,finish_reserve,reset_timeout,episode_overhead,rpc_cap,clock,rpc,evaluate,worst_case,record_failure,startup_reset_timeout=None):
    global FAILURE_RECORDED
    candidate_deadline=hard_deadline-finish_reserve
    reset_slot=reset_timeout+episode_overhead
    first_reset_timeout=reset_timeout if startup_reset_timeout is None else startup_reset_timeout
    outcomes=[worst_case(episode) for episode in episodes]
    if clock()+len(episodes)*reset_slot+max(0,first_reset_timeout-reset_timeout)>candidate_deadline:
        raise TimeoutError('insufficient time for declared reset reservations')
    complete=True
    for index,episode in enumerate(episodes):
        FAILURE_RECORDED=False
        remaining=len(episodes)-index-1
        future_reserve=sum(reset_slot+item.get('work_seconds',0)+item.get('method_reserve',0) for item in episodes[index+1:])
        episode_deadline=candidate_deadline-future_reserve
        work_deadline=episode_deadline-episode_overhead
        current_operation='reset'
        primary_failure=None
        episode_started=clock()
        def call(request):
            nonlocal current_operation,primary_failure
            current_operation=request.get('op','unknown')
            try:
                timeout=min(rpc_cap,work_deadline-clock())
                if timeout<=0:
                    raise TimeoutError('episode work budget exhausted')
                return rpc(request,timeout=timeout)
            except (TimeoutError,RequiredBaselineFailure,ProtocolFailure,TransportFailure) as error:
                if primary_failure is None:
                    primary_failure=describe_episode_failure(error,current_operation)
                raise
        try:
            timeout=min(first_reset_timeout if index==0 else reset_timeout,work_deadline-clock())
            if timeout<=0:
                raise TimeoutError('episode reset budget exhausted')
            require_reset_ack(rpc({'op':'reset','seed':episode['seed']},timeout=timeout))
            value=evaluate(episode,call,work_deadline)
            if clock()>episode_deadline:
                raise TimeoutError('episode cleanup deadline exceeded')
            outcomes[index]=value
        except (TimeoutError,RequiredBaselineFailure,InvalidResetResponse,ProtocolFailure,TransportFailure) as error:
            complete=False
            failure=primary_failure or describe_episode_failure(error,current_operation)
            try:
                record_failure(failure)
            except Exception:
                error.add_note('episode diagnostic recording failed')
            if isinstance(error,TransportFailure):
                outcomes[index]['duration']=max(0,clock()-episode_started)
                error.outcomes=outcomes
                raise
        outcomes[index]['duration']=max(0,clock()-episode_started)
    return outcomes,complete

def preflight(smoke):
    size=256
    slots=[{'key':'f'*64,'stratum':'x'*80} for unused in range(size)]
    request={'op':'update','arms':16,'slots':slots,'confidence':.95}
    response={'prompts':['\U00010000'*1023+chr(0x10000+index) for index in range(16)],'selection':['f'*64]*64,'report':['f'*64]*192,'weights':[1/192]*192,'tie_order':list(range(16))}
    for value in [request,response,{'id':9223372036854775807,'request':request,'response':response,'metadata':'x'*4096}]:
        bounded_json_line(value)
    episode_count=2 if smoke else 8*len(SEEDS)
    operation_table={'reset':episode_count+1,'update':episode_count+1,'export_start':0,'export_chunk':0,'import_start':0,'import_chunk':0,'import_commit':0}
    if sum(operation_table.values())>RPC_BUDGET or (not smoke and sum(operation_table.values())!=RPC_BUDGET):
        raise RuntimeError('operation count budget mismatch')
    for count,wall,pool in [(25,21600,2048),(41,43200,4096)]:
        required=60+8+count*(20+4+5+6*1.1)+pool*16*.55+(count//2)*30
        if required>wall:
            raise RuntimeError('joint productive workload cannot fit')

def plan_episodes(smoke):
    if smoke:
        primary=[{'family':family,'n':16,'arms':2,'seed':SEEDS[0],'reps':4,'audit':16} for family in ['S','R']]
    else:
        primary=[{'family':family,'n':size,'arms':arms,'seed':seed,'reps':REPLICATES,'audit':512} for family in ['S','R'] for size in [64,256] for arms in [1,16] for seed in SEEDS]
    return primary+[dict(primary[0],replay=True)]

def experiment(rows,synthetic_manifest,baseline,smoke):
    import numpy as np
    bank=None
    first=None
    replay_match=False
    def evaluate(episode,call,deadline):
        nonlocal bank,first,replay_match
        size,arms,seed=episode['n'],episode['arms'],episode['seed']
        generator=np.random.default_rng(seed)
        selected=generator.permutation(len(rows))[:size+episode['audit']]
        items=[rows[int(index)] for index in selected]
        if episode['family']=='S':
            slots=[{'key':digest(['slot',index]),'stratum':'unlabelled'} for index in range(size)]
        else:
            slots=[{'key':row['content_hash'],'stratum':row['category']} for row in items[:size]]
        request={'op':'update','arms':arms,'slots':slots,'confidence':.95}
        guarded=guard_required_baseline(call,baseline.status,lambda:baseline.worker.close(failed=True,component='baseline'),record_failure)
        response=validate_plan(guarded(request),request)
        if bank is None:
            bank=response['prompts']
        elif response['prompts']!=bank:
            raise ProtocolFailure('prompt bank must be immutable across all workloads')
        lookup={slot['key']:index for index,slot in enumerate(slots)}
        selection=[lookup[key] for key in response['selection']]
        report=[lookup[key] for key in response['report']]
        order=response['tie_order']
        random_arm=int(np.random.default_rng(seed+823).integers(arms))
        measured=[]
        details=[]
        if episode['family']=='S':
            hashes=[]
            for regime in range(4):
                generator=np.random.default_rng(np.random.SeedSequence([seed,size,arms,regime]))
                truth=np.full(arms,.6) if regime//2==0 else np.linspace(.4,.8,arms)
                correlation=.1 if regime%2==0 else .9
                aggregate=hashlib.sha256()
                regime_values=[]
                control_values=[]
                for repeat in range(episode['reps']):
                    if time.monotonic()+7>deadline:
                        raise TimeoutError()
                    raw=generator.random((size,17),dtype=np.float64)
                    aggregate.update(raw.tobytes())
                    uniforms=np.where(raw[:,:1]<correlation,raw[:,:1]/correlation,raw[:,1:arms+1])
                    matrix=(uniforms<truth).astype(np.float64)
                    permuted=np.roll(matrix,1,axis=0)
                    control_value=controls(matrix,selection,report,order,permuted,int(np.count_nonzero(np.any(raw!=np.roll(raw,1,axis=0),axis=1))))
                    control_values.append(control_value['permuted_input']['report'])
                    value,detail=summarize(matrix,truth,selection,report,order,random_arm)
                    measured.append(value)
                    regime_values.append(value)
                hashes.append(aggregate.hexdigest())
                details.append({'regime':regime,'metrics':{name:average([value[name] for value in regime_values]) for name in ORDINARY},'permutation_report_mean':average(control_values),'copy_report_independence_audit_passed':False,'report_mse_standard_error':float(np.std([value['report_mse'] for value in regime_values],ddof=1)/math.sqrt(len(regime_values)))})
            expected=synthetic_manifest['episodes'][f"{seed}-{size}-{arms}-{episode['reps']}"]
            if hashes!=expected:
                raise RuntimeError('synthetic raw-content hash audit failed')
        else:
            inference_deadline=min(deadline-8,time.monotonic()+episode['work_seconds'])
            predictions=baseline.call({'rows':[{key:row[key] for key in ['question','options','content_hash']} for row in items],'prompts':bank[:arms]},timeout=max(.001,inference_deadline-time.monotonic()))
            if type(predictions) is not dict or set(predictions)!={'predictions'}:
                baseline.fail('baseline_result_failure')
            outputs=np.asarray(predictions['predictions'])
            if outputs.shape!=(len(items),arms) or outputs.dtype.kind not in 'iu' or np.any((outputs< -1)|(outputs>9)):
                baseline.fail('baseline_result_failure')
            labels=np.asarray([row['answer_index'] for row in items])
            matrix=(outputs[:size]==labels[:size,None]).astype(np.float64)
            truth=(outputs[size:]==labels[size:,None]).mean(axis=0)
            changed=None
            for shift in range(1,size):
                candidate=np.roll(labels[:size],shift)
                if np.count_nonzero(candidate!=labels[:size])>=2:
                    changed=candidate
                    break
            if changed is None:
                raise ProtocolFailure('vacuous answer permutation')
            control_values=controls(matrix,selection,report,order,(outputs[:size]==changed[:,None]).astype(np.float64),int(np.count_nonzero(changed!=labels[:size])))
            for remaining in range(5,-1,-1):
                reserved_method_deadline(now=time.monotonic(),episode_deadline=deadline,methods_remaining=remaining,work_seconds=1,cleanup_seconds=.1)
            value,detail=summarize(matrix,truth,selection,report,order,random_arm)
            measured.append(value)
            differences=(outputs[size:,detail['winner']]==labels[size:]).astype(float)-(outputs[size:,0]==labels[size:]).astype(float)
            subject_indices=collections.defaultdict(list)
            for index,row in enumerate(items[size:]):
                subject_indices[row['category']].append(index)
            generator=np.random.default_rng(seed+76531)
            subjects=sorted(subject_indices)
            bootstrap=[]
            for repeat in range(200):
                if time.monotonic()+7>deadline:
                    raise TimeoutError()
                sample=generator.choice(subjects,len(subjects),replace=True)
                indices=[index for subject in sample for index in subject_indices[subject]]
                bootstrap.append(float(differences[indices].mean()))
            label_marginals=np.bincount(labels[:size],minlength=10)/size
            permutation_null=[float(sum(np.count_nonzero(outputs[:size,arm]==label)*label_marginals[label]/size for label in range(10))) for arm in range(arms)]
            detail.update(paired_subject_bootstrap_interval=np.quantile(bootstrap,[.025,.975]).tolist(),invalid_answer_count=int(np.count_nonzero(outputs<0)),audit_size=len(items)-size,controls=control_values,permutation_null_by_arm=permutation_null)
            details=[detail]
        category=baseline.status()
        if category is not None:
            baseline.fail(category)
        metrics={name:average([value[name] for value in measured]) for name in ORDINARY}
        solution={'case':episode['family']+str(size)+'K'+str(arms),'plan_hash':digest(response),'metrics':metrics,'details':details,'completed_controls':sorted(EXPECTED_CONTROLS)}
        signature=digest({'response':response,'metrics':metrics,'details':details})
        if first is None:
            first=signature
        if episode.get('replay'):
            replay_match=first==signature
        return {'metrics':metrics,'solution':solution,'duration':0.0,'valid':True}
    return evaluate,lambda:replay_match

def validated_evidence_bytes(evidence):
    def number(value):
        try:
            return type(value) in (int,float) and math.isfinite(value)
        except OverflowError:
            return False
    def inline(value,depth=1):
        if depth>12:
            raise ValueError('evidence nesting limit')
        if type(value) is dict:
            if not all(type(key) is str for key in value):
                raise ValueError('invalid evidence JSON key')
            for item in value.values():
                inline(item,depth+1)
        elif type(value) is list:
            for item in value:
                inline(item,depth+1)
        elif value is not None and type(value) not in (str,bool) and not number(value):
            raise ValueError('invalid evidence JSON value')
    if type(evidence) is not dict or set(evidence)!={'schema_version','episodes'} or type(evidence['schema_version']) is not int or evidence['schema_version']!=1:
        raise ValueError('invalid evidence envelope')
    records=evidence['episodes']
    if type(records) is not list or not 1<=len(records)<=10000:
        raise ValueError('invalid evidence episode count')
    seeds=set()
    timeseries_count=0
    required={'seed','score','correct','duration_seconds'}
    optional={'solution','candidate_diagnostics','candidate_timeseries'}
    def name(value):
        return type(value) is str and re.fullmatch(r'[A-Za-z0-9_-][A-Za-z0-9_.-]{0,79}',value) is not None
    for record in records:
        if type(record) is not dict or not required<=set(record) or set(record)-required-optional:
            raise ValueError('invalid evidence record schema')
        seed=record['seed']
        if type(seed) is not int or not -(2**63)<=seed<2**63 or seed in seeds:
            raise ValueError('invalid or duplicate evidence seed')
        seeds.add(seed)
        if not number(record['score']) or type(record['correct']) is not bool or not number(record['duration_seconds']) or record['duration_seconds']<0:
            raise ValueError('invalid evidence measurements')
        if 'candidate_diagnostics' in record:
            diagnostics=record['candidate_diagnostics']
            if type(diagnostics) is not dict or not all(name(key) and number(value) for key,value in diagnostics.items()):
                raise ValueError('invalid candidate diagnostics')
        if 'candidate_timeseries' in record:
            series=record['candidate_timeseries']
            if type(series) is not list:
                raise ValueError('invalid candidate timeseries')
            timeseries_count+=len(series)
            if timeseries_count>100000:
                raise ValueError('evidence timeseries limit')
            for row in series:
                if type(row) is not dict or set(row)!={'series_name','step','value'} or not name(row['series_name']) or type(row['step']) is not int or row['step']<0 or not number(row['value']):
                    raise ValueError('invalid candidate timeseries row')
    inline(evidence)
    encoded=json.dumps(evidence,allow_nan=False,separators=(',',':')).encode('utf-8')+b'\n'
    if len(encoded)>16*1024*1024:
        raise ValueError('evidence size limit')
    json.loads(encoded,object_pairs_hook=no_duplicates)
    return encoded

def write_results(directory,metrics,correct,feasible,evidence=None):
    directory.mkdir(parents=True,exist_ok=True)
    if set(metrics)!=set(METRICS) or not all(type(value) in (int,float) and math.isfinite(value) for value in metrics.values()):
        raise RuntimeError('invalid metric schema')
    (directory/'metrics.json').write_bytes(bounded_json_line(metrics))
    (directory/'correct.json').write_bytes(bounded_json_line({'correct':bool(correct)}))
    if os.environ.get('AGENTIC_TASK_QUALIFICATION')=='1':
        (directory/'qualification.json').write_bytes(bounded_json_line({'schema_version':1,'feasible':bool(feasible)}))
    if evidence is not None:
        encoded=validated_evidence_bytes(evidence)
        descriptor=os.open(directory/'evaluation_evidence.json',os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
        with os.fdopen(descriptor,'wb') as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise ValueError('evidence output must be a regular file')
            stream.write(encoded)

def main():
    import resource
    resource.setrlimit(resource.RLIMIT_CPU,(WALL_SECONDS*6,WALL_SECONDS*6))
    resource.setrlimit(resource.RLIMIT_AS,(4*1024**3,32*1024**3))
    os.sched_setaffinity(0,sorted(os.sched_getaffinity(0))[:6])
    for variable in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:
        os.environ[variable]='6'
    parser=argparse.ArgumentParser()
    parser.add_argument('--program_path',required=True)
    parser.add_argument('--results_dir',required=True)
    arguments=parser.parse_args()
    smoke=os.environ.get('AGENTIC_TASK_DRAFT_SMOKE')=='1'
    hard_deadline=STARTED+(140 if smoke else WALL_SECONDS-60)
    candidate=None
    baseline=None
    episodes=plan_episodes(smoke)
    outcomes=[worst_case(episode) for episode in episodes]
    complete=False
    replay=False
    unexpected=None
    try:
        preflight(smoke)
        root=Path(os.environ.get('TASK_SOURCE_DIR',str(Path(__file__).resolve().parent)))/'resources'/PLANE
        rows,manifest=load_resources(root,smoke)
        import numpy as np
        planned_cache=set()
        for episode in episodes:
            episode['method_reserve']=.8 if smoke else 11.6
            if episode['family']=='S':
                episode['work_seconds']=.5 if smoke else 20
            else:
                indices=np.random.default_rng(episode['seed']).permutation(len(rows))[:episode['n']+episode['audit']]
                cells={(int(index),arm) for index in indices for arm in range(episode['arms'])}
                episode['work_seconds']=.55*len(cells-planned_cache)+10
                planned_cache.update(cells)
        if time.monotonic()+8+sum(24+episode['work_seconds']+episode['method_reserve'] for episode in episodes)>hard_deadline:
            raise TimeoutError('joint workload reservations cannot fit')
        baseline=Baseline(root,hard_deadline-35)
        candidate=Candidate(arguments.program_path,baseline)
        evaluate,replay_status=experiment(rows,manifest,baseline,smoke)
        outcomes,complete=run_declared_episodes(episodes,hard_deadline=hard_deadline,finish_reserve=8,reset_timeout=20,episode_overhead=4,rpc_cap=5,clock=time.monotonic,rpc=candidate.call,evaluate=evaluate,worst_case=worst_case,record_failure=record_failure)
        replay=replay_status() and outcomes[-1]['valid']
    except TransportFailure as error:
        outcomes=getattr(error,'outcomes',outcomes)
        unexpected=error
        record_failure(describe_episode_failure(error,'setup'))
    except (RequiredBaselineFailure,TimeoutError,ProtocolFailure) as error:
        record_failure(describe_episode_failure(error,'setup'))
    except Exception as error:
        unexpected=error
    finally:
        for worker in [candidate,baseline]:
            if worker is not None:
                try:
                    worker.close()
                except Exception as error:
                    was_complete=complete
                    complete=False
                    print('worker_cleanup_failure component='+('candidate' if worker is candidate else 'baseline'),file=sys.stderr,flush=True)
                    if unexpected is None and was_complete:
                        unexpected=error
    if not replay:
        duration=outcomes[0]['duration']
        observations=outcomes[0]['solution']
        outcomes[0]=worst_case(episodes[0])
        outcomes[0]['solution'].update({key:value for key,value in observations.items() if key!='metrics'})
        outcomes[0]['solution']['replay_valid']=False
        outcomes[0]['duration']=duration
    primary=outcomes[:-1]
    metrics={name:average([outcome['metrics'][name] for outcome in primary]) for name in ORDINARY}
    metrics['combined_score']=1-metrics['report_mse']
    metrics['replay_discrepancy']=float(not replay)
    feasible=complete and time.monotonic()<=hard_deadline and not smoke
    correct=complete and replay and all(outcome['valid'] for outcome in primary) and time.monotonic()<=hard_deadline
    metrics['correct']=float(correct)
    records=[]
    for seed in dict.fromkeys(episode['seed'] for episode in episodes[:-1]):
        members=[outcome for episode,outcome in zip(episodes[:-1],primary) if episode['seed']==seed]
        records.append({'seed':seed,'score':1-average([outcome['metrics']['report_mse'] for outcome in members]),'correct':all(outcome['valid'] for outcome in members) and (replay or seed!=SEEDS[0]),'duration_seconds':math.fsum(outcome['duration'] for outcome in members)+(outcomes[-1]['duration'] if seed==SEEDS[0] else 0),'solution':{'cases':[outcome['solution'] for outcome in members]}})
    write_results(Path(arguments.results_dir),metrics,correct,feasible,{'schema_version':1,'episodes':records})
    if unexpected is not None:
        if repair_mode():
            report_worker_exception(unexpected)
        elif PLANE=='search':
            name=bounded_failure_name(type(unexpected).__name__.lower(),'evaluator_error')
            message='unexpected evaluator failure'
            print('evaluator_exception type='+name+' message='+message,file=sys.stderr)
        else:
            print('evaluator_exception type=evaluator_error message=sealed',file=sys.stderr)
        return 1
    return 0

if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--inference_worker':
        try:
            inference_worker(sys.argv[2])
        except Exception as error:
            if repair_mode():
                report_worker_exception(error)
            else:
                print('baseline_worker_failure',file=sys.stderr,flush=True)
            raise SystemExit(1)
    else:
        try:
            status=main()
        except Exception as error:
            name=bounded_failure_name(type(error).__name__.lower(),'evaluator_error')
            print('evaluator_exception type='+name+' message=output_or_setup_failure',file=sys.stderr)
            status=1
        raise SystemExit(status)
