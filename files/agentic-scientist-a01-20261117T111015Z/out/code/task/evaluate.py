"""Self-contained sealed-plane evaluator; scientific inputs travel only as JSON.

The resource manifest freezes normalization, source provenance and cluster split.
No candidate-reported scientific metric or hidden-state assertion is accepted.
Worst cases and all aggregation weights are fixed before candidate execution.
"""
import argparse
import base64
import collections
import ctypes
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import re
import resource
import selectors
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

INVOCATION_STARTED = time.monotonic()

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
import numpy as np

PLANE = 'search'
SEEDS = [101, 103]
WALL_SECONDS = 900
TARGETS = 12
RPC_BUDGET = 1411
STARTUP_ALLOWANCE = 20.0
FINISH_RESERVE = 12.0
RESET_TIMEOUT = 1.5
RPC_CAP = 20.0
EPISODE_OVERHEAD = 2.0
WORK_SECONDS = TARGETS * (5.0 / 12)
CHUNK_BYTES = 1048576
WIRE_LIMIT = 64 * CHUNK_BYTES
TOLERANCE = 1e-10
METRIC_NAMES = ("combined_score", "correct", "feasible_rate", "mean_effort_fraction", "mean_verified_gap_fraction", "control_pass_rate")
CASES = ("ordinary", "constant", "copy", "permutation")
RULES = ("mean", "median", "trimmed")


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
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, ProtocolFailure):
            return {"component": "candidate", "category": context.category, "operation": bounded_failure_name(operation, "unknown")}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout", "operation": bounded_failure_name(operation, "unknown")}


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


class BrokerTransportFailure(RuntimeError):
    def __init__(self, operation):
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("broker_transport")


class ProtocolFailure(RuntimeError):
    def __init__(self, category="malformed_response"):
        self.category = bounded_failure_name(category, "malformed_response")
        super().__init__(self.category)


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
            raise RuntimeError("stderr reader cleanup unresolved")
        self.result = {"stderr": "".join(self.lines), "observed_bytes": self.observed_bytes,
                       "retained_bytes": self.retained_bytes, "truncated": self.truncated,
                       "capture_error": self.capture_error}
        return dict(self.result)


def report_worker_exception(error):
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = "WorkerException"
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    if len(message) > 2048 or len(message.encode("utf-8", errors="replace")) > 2048:
        message = "<exception message omitted: too large>"
    print(f"worker_exception type={name}\n{message}", file=sys.stderr, flush=True)


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ProtocolFailure("wire_limit")
    return encoded


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ProtocolFailure("duplicate_key")
        result[key] = value
    return result


def decode_json(data):
    try:
        value = json.loads(data, object_pairs_hook=unique_object,
                           parse_constant=lambda value: (_ for _ in ()).throw(ProtocolFailure("nonfinite_response")))
        bounded_json_line(value)
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError, OverflowError) as error:
        raise ProtocolFailure() from error


def require_keys(value, keys):
    if type(value) is not dict or set(value) != set(keys):
        raise ProtocolFailure()


def integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ProtocolFailure()
    return value


def normalized(value):
    if isinstance(value, str):
        return " ".join(unicodedata.normalize("NFKC", value).split())
    if isinstance(value, list):
        return [normalized(item) for item in value]
    if isinstance(value, dict):
        return {normalized(key): normalized(item) for key, item in sorted(value.items())}
    if isinstance(value, float):
        if not math.isfinite(value):
            return {"nonfinite": str(value)}
        return int(value) if value.is_integer() else value
    return value


def digest(value):
    return hashlib.sha256(json.dumps(normalized(value), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def candidate_subprocess_settings(parent_environment):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES",
                     "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES", "OMP_NUM_THREADS",
                     "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                     "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION", "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


SANDBOX = r'''
import ctypes, errno, importlib.util, json, os, platform, resource, sys
libc = ctypes.CDLL(None, use_errno=True)
if platform.machine() != "x86_64":
    raise RuntimeError("native isolation requires Linux x86_64")
if libc.prctl(38, 1, 0, 0, 0):
    raise RuntimeError("no_new_privileges failed")
abi = libc.syscall(444, 0, 0, 1)
if abi < 1:
    raise RuntimeError("Landlock unavailable")
class Ruleset(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int)]
mask = (1 << 13)-1
if abi >= 2:
    mask |= 1 << 13
if abi >= 3:
    mask |= 1 << 14
ruleset = Ruleset(mask)
fd = libc.syscall(444, ctypes.byref(ruleset), ctypes.sizeof(ruleset), 0)
if fd < 0:
    raise RuntimeError("Landlock setup failed")
for path in __READ_PATHS__:
    if not os.path.exists(path):
        continue
    parent = os.open(path, os.O_PATH | os.O_CLOEXEC)
    access = 1 | 4 | (8 if os.path.isdir(path) else 0)
    rule = PathRule(access, parent)
    if libc.syscall(445, fd, 1, ctypes.byref(rule), 0):
        raise RuntimeError("Landlock path failed")
    os.close(parent)
parent = os.open(os.getcwd(), os.O_PATH | os.O_CLOEXEC)
rule = PathRule(1 | 4 | 8, parent)
if libc.syscall(445, fd, 1, ctypes.byref(rule), 0) or libc.syscall(446, fd, 0):
    raise RuntimeError("Landlock activation failed")
os.close(parent)
os.close(fd)
class Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint)]
class Program(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]
blocked = [41,42,43,44,45,46,47,49,50,53,56,57,58,59,62,101,112,165,166,200,234,272,288,308,310,311,321,322,435]
items = [Filter(0x20,0,0,4), Filter(0x15,1,0,0xc000003e), Filter(0x06,0,0,0x80000000), Filter(0x20,0,0,0)]
for syscall in blocked:
    items.extend([Filter(0x15,0,1,syscall), Filter(0x06,0,0,0x50000 | errno.EPERM)])
items.append(Filter(0x06,0,0,0x7fff0000))
filters = (Filter*len(items))(*items)
program = Program(len(items), filters)
if libc.prctl(22, 2, ctypes.byref(program), 0, 0):
    raise RuntimeError("seccomp activation failed")
resource.setrlimit(resource.RLIMIT_CPU, (__CPU__, __CPU__))
resource.setrlimit(resource.RLIMIT_AS, (4*1024**3, 4*1024**3))
resource.setrlimit(resource.RLIMIT_FSIZE, (32*1024**2, 32*1024**2))
resource.setrlimit(resource.RLIMIT_NOFILE, (64,64))
resource.setrlimit(resource.RLIMIT_CORE, (0,0))
specification = importlib.util.spec_from_file_location("candidate", "program.py")
module = importlib.util.module_from_spec(specification)
try:
    specification.loader.exec_module(module)
    while True:
        line = sys.stdin.buffer.readline(67108864)
        if not line:
            break
        if len(line) >= 67108864 or not line.endswith(b"\n"):
            raise ValueError("request bound")
        response = module.handle(json.loads(line))
        encoded = json.dumps(response, allow_nan=False, separators=(",", ":")).encode()+b"\n"
        if len(encoded) >= 67108864:
            raise ValueError("response bound")
        sys.stdout.buffer.write(encoded)
        sys.stdout.buffer.flush()
except Exception as error:
    if __REPAIR__:
        name = type(error).__name__
        message = str(error)
        if len(message.encode("utf-8",errors="replace")) > 2048:
            message = "<exception message omitted: too large>"
        print("worker_exception type="+name+"\n"+message, file=sys.stderr, flush=True)
    else:
        print("candidate_worker_failure", file=sys.stderr, flush=True)
    sys.exit(1)
'''


class Client:
    def __init__(self, program_path):
        self.process = None
        self.capture = None
        self.temp = None
        self.calls = 0
        self.program_path = program_path
        self.proxy = None
        self.cleanup_errors = []
        socket = os.environ.get("AGENTIC_CANDIDATE_SOCKET")
        fixed_path = program_path == "/broker-code/candidate_proxy.py"
        if bool(socket) != fixed_path:
            raise ValueError("broker mode requires both trusted signals")
        if not socket:
            if sys.platform != "linux" or os.uname().machine != "x86_64" or ctypes.CDLL(None,use_errno=True).syscall(444,0,0,1) < 1:
                raise RuntimeError("native isolation requires Linux x86_64 and Landlock ABI1+")
        if socket and fixed_path:
            spec = importlib.util.spec_from_file_location("trusted_candidate_proxy", program_path)
            self.proxy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self.proxy)

    def _start(self):
        self.temp = tempfile.TemporaryDirectory(prefix="candidate-isolated-")
        shutil.copyfile(self.program_path, Path(self.temp.name)/"program.py")
        interpreter, environment = candidate_subprocess_settings(os.environ)
        read_paths = ["/usr", "/lib", "/lib64", "/etc/ld.so.cache", "/etc/fonts", "/dev/null", "/dev/urandom", sys.prefix]
        repair = PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1" or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")
        script = SANDBOX.replace("__READ_PATHS__", repr(read_paths)).replace("__CPU__", str(math.ceil(WALL_SECONDS))).replace("__REPAIR__", repr(repair))
        self.process = subprocess.Popen([interpreter, "-I", "-u", "-c", script], shell=False,
                                        cwd=self.temp.name, env=environment, stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        self.capture = BoundedWorkerStderr(self.process.stderr)
        os.set_blocking(self.process.stdin.fileno(), False)
        os.set_blocking(self.process.stdout.fileno(), False)
        self.buffer = bytearray()

    def close(self, failed=False):
        process = self.process
        if process is None:
            return
        self.process = None
        try:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=.4)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=.4)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            snapshot = self.capture.close()
            repair = PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1" or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")
            if failed and repair:
                print("worker_capture component=candidate observed_bytes="+str(snapshot["observed_bytes"])+" retained_bytes="+str(snapshot["retained_bytes"])+" truncated="+str(int(snapshot["truncated"]))+" capture_error="+(snapshot["capture_error"] or "none"), file=sys.stderr)
                if snapshot["stderr"]:
                    print(snapshot["stderr"], file=sys.stderr, end="")
        except (OSError, RuntimeError, subprocess.TimeoutExpired):
            self.cleanup_errors.append("candidate_cleanup_failure")
        finally:
            for stream in (process.stdin, process.stdout):
                stream.close()
            self.temp.cleanup()

    def call(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolFailure("rpc_budget")
        data = bounded_json_line(request)
        bounded_json_line({"request": request, "rpc_id": 9999999, "protocol": "python_rpc_v1"})
        if self.proxy is not None:
            def alarm_handler(signum, frame):
                raise TimeoutError()
            previous = signal.signal(signal.SIGALRM,alarm_handler)
            signal.setitimer(signal.ITIMER_REAL,timeout)
            try:
                response = self.proxy.handle(request)
                try:
                    return decode_json(bounded_json_line(response))
                except (ValueError,TypeError,OverflowError,RecursionError) as error:
                    raise ProtocolFailure() from error
            except (ConnectionError,EOFError) as error:
                raise BrokerTransportFailure(request.get("op")) from error
            finally:
                signal.setitimer(signal.ITIMER_REAL,0)
                signal.signal(signal.SIGALRM,previous)
        if request.get("op") == "reset":
            self.close()
        if self.process is None:
            self._start()
        deadline = time.monotonic()+timeout
        sent = 0
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            selector.register(self.process.stdin, selectors.EVENT_WRITE)
            while True:
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    raise TimeoutError()
                for key, mask in selector.select(timeout=remaining):
                    if key.fileobj is self.process.stdin:
                        try:
                            sent += os.write(self.process.stdin.fileno(), data[sent:sent+65536])
                        except BrokenPipeError as error:
                            raise ProtocolFailure("candidate_exit") from error
                        if sent == len(data):
                            selector.unregister(self.process.stdin)
                    else:
                        chunk = os.read(self.process.stdout.fileno(), 65536)
                        if not chunk:
                            raise ProtocolFailure("candidate_exit")
                        self.buffer.extend(chunk)
                        if len(self.buffer) >= WIRE_LIMIT:
                            raise ProtocolFailure("wire_limit")
                        if b"\n" in self.buffer:
                            line, _, extra = self.buffer.partition(b"\n")
                            if extra or sent != len(data):
                                raise ProtocolFailure("unsolicited_output")
                            self.buffer.clear()
                            return decode_json(line)


def record_failure(failure):
    if type(failure) is not dict:
        failure = {"component":"baseline","category":bounded_failure_name(failure,"baseline_result_failure"),"operation":"baseline_worker"}
    if PLANE == "search":
        component = bounded_failure_name(failure.get("component"), "candidate")
        category = bounded_failure_name(failure.get("category"), "protocol_failure")
        operation = bounded_failure_name(failure.get("operation"), "unknown")
        print(f"episode_failure component={component} category={category} operation={operation}"[:256], file=sys.stderr, flush=True)


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout,
                          episode_overhead, rpc_cap, clock, rpc, evaluate, worst_case,
                          record_failure, cancel):
    candidate_deadline = hard_deadline-finish_reserve
    reset_slot = reset_timeout+episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock()+len(episodes)*reset_slot > candidate_deadline:
        raise TimeoutError("insufficient declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes)-index-1
        episode_deadline = candidate_deadline-remaining*reset_slot
        work_deadline = episode_deadline-episode_overhead
        current_operation = "reset"
        primary_failure = None
        def call(request, timeout=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline-clock(), timeout if timeout is not None else rpc_cap)
                if timeout <= 0:
                    raise TimeoutError()
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        started = clock()
        failed = False
        fatal_error = None
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline-clock())
            if timeout <= 0:
                raise TimeoutError()
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            outcome = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError()
            outcomes[index] = outcome
        except BrokerTransportFailure as error:
            failed = True
            fatal_error = error
            record_failure({"component":"broker","category":"broker_transport","operation":error.operation})
            raise
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolFailure) as error:
            failed = True
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            record_failure(failure)
        finally:
            try:
                cancel(failed)
            except Exception:
                if fatal_error is None:
                    raise
                fatal_error.add_note("secondary candidate cleanup failure")
                record_failure({"component":"candidate","category":"cleanup_failure","operation":"cleanup"})
            outcomes[index]["duration_seconds"] = max(0.0, clock()-started)
    return outcomes, complete


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    if any(not math.isfinite(value) or value < 0 for value in (now, episode_deadline, cleanup_seconds)) or not math.isfinite(work_seconds) or work_seconds <= 0 or type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid matched method reservation")
    if now+(methods_remaining+1)*(work_seconds+cleanup_seconds) > episode_deadline:
        raise TimeoutError("insufficient matched method reservations")
    return now+work_seconds


def check_deadline(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError()


def aggregate_rows(values, rule):
    if rule == "mean":
        return np.mean(values, axis=-1)
    if rule == "median":
        return np.median(values, axis=-1)
    trim = values.shape[-1]//5
    return np.mean(np.sort(values, axis=-1)[..., trim:values.shape[-1]-trim], axis=-1)


def load_resources(root):
    manifest = json.loads((root/"manifest.json").read_text())
    encoded = (root/"records.json").read_bytes()
    if hashlib.sha256(encoded).hexdigest() != manifest["data_sha256"]:
        raise ValueError("resource digest mismatch")
    if manifest["disjoint_content_verified"] is not True or not re.fullmatch("[0-9a-f]{64}",manifest["other_content_hashes_commitment_sha256"]):
        raise ValueError("normalized raw-content split attestation missing")
    data = json.loads(encoded)
    panels = {"helm": [], "openllm": [], "bbh": []}
    identifiers = {name: [] for name in panels}
    cluster_ids = {name: [] for name in panels}
    seen_hashes = set()
    bbh_tasks = None
    for record in data["records"]:
        hashes = []
        if record["family"] == "helm":
            for task, raw in record["raw"].items():
                hashes.append(digest({"subject": task, "settings": raw["settings"], "cells": raw["cells"][1:]}))
            scores = {task: record["raw"][task]["cells"][1]["value"] for task in data["helm_tasks"]}
            hashes.append(digest({"tasks": scores, "settings": {"family": "helm", "release": "v1.13.0"}}))
            row = [scores[task] for task in data["helm_tasks"]]
        else:
            raw = record["raw"]
            settings = {key: raw[key] for key in ("Precision", "Weight type", "Chat Template", "Architecture")}
            hashes.append(digest({"tasks": {task: raw[task] for task in data["openllm_tasks"]}, "settings": settings}))
            row = [raw[task] for task in data["openllm_tasks"]]
            if record["results"] is not None:
                result = record["results"]["raw"]
                tasks = record["results"]["bbh_tasks"]
                if bbh_tasks is not None and tasks != bbh_tasks:
                    raise ValueError("BBH task panel mismatch")
                bbh_tasks = tasks
                bbh = {task: result["results"][task]["acc_norm,none"] for task in tasks}
                settings = {key: result["config"].get(key) for key in ("random_seed", "numpy_seed", "torch_seed", "fewshot_seed", "model_dtype")}
                hashes.append(digest({"tasks": bbh, "settings": settings}))
                hashes.append(digest({"results": result["results"], "configs": result.get("configs"), "task_hashes": result.get("task_hashes")}))
                if result["config"].get("model_sha") != raw["Model sha"]:
                    raise ValueError("BBH revision mismatch")
                panels["bbh"].append([bbh[task] for task in tasks])
                identifiers["bbh"].append(record["id"])
                cluster_ids["bbh"].append(record["cluster"])
        if sorted(hashes) != sorted(record["content_hashes"]):
            raise ValueError("normalized raw content digest mismatch")
        seen_hashes.update(hashes)
        panels[record["family"]].append(row)
        identifiers[record["family"]].append(record["id"])
        cluster_ids[record["family"]].append(record["cluster"])
    if seen_hashes != set(manifest["own_content_hashes"]):
        raise ValueError("raw split manifest mismatch")
    tasks = {"helm": data["helm_tasks"], "openllm": data["openllm_tasks"], "bbh": bbh_tasks}
    for name, rows in panels.items():
        matrix = np.asarray(rows, dtype="<f8")
        if matrix.ndim != 2 or matrix.shape[0] < 13 or not 1 <= matrix.shape[1] <= 100 or matrix.shape[0] > 10000 or not np.all(np.isfinite(matrix)) or np.min(matrix) < 0 or np.max(matrix) > 1:
            raise ValueError("required public panel unavailable")
        panels[name] = {"values": matrix, "task_ids": tasks[name], "identifiers": identifiers[name], "clusters": cluster_ids[name]}
    return panels


def select_targets(matrix, count, seed):
    excluded = set()
    for rule in RULES:
        scores = aggregate_rows(matrix, rule)
        excluded.update(np.flatnonzero(scores >= np.max(scores)-TOLERANCE).tolist())
    order = sorted((index for index in range(len(matrix)) if index not in excluded),
                   key=lambda index: (float(np.mean(matrix[index])), index))
    if len(order) < count:
        raise ValueError("insufficient nonleading target strata")
    rng = np.random.default_rng(seed)
    targets = []
    for band in np.array_split(np.array(order), count):
        targets.append(int(band[int(rng.integers(len(band)))]))
    return targets


def prepare_episode(episode, panels, smoke):
    family, case, seed = episode["family"], episode["case"], episode["seed"]
    names = [family]+(["bbh"] if family == "openllm" else [])
    matrices = {}
    base = {}
    target_rows = {}
    count = 2 if smoke else TARGETS
    for name in names:
        source = panels[name]
        values = source["values"]
        task_ids = list(source["task_ids"])
        if smoke:
            values = values[:min(len(values),40), :6]
            task_ids = task_ids[:6]
        else:
            values = values.copy()
        target_rows[name] = select_targets(values, count, seed)
        base[name] = (values.copy(), list(task_ids))
        if case == "constant":
            values = np.ones_like(values)
        elif case == "permutation":
            order = np.arange(values.shape[1])[::-1]
            if np.array_equal(order, np.arange(values.shape[1])) or np.array_equal(values[:,order],values):
                raise ProtocolFailure("vacuous_permutation")
            values = values[:, order]
            task_ids = [task_ids[index] for index in order]
        matrices[name] = {"values": np.ascontiguousarray(values,dtype="<f8"), "task_ids": task_ids}
    decisions = []
    roles = []
    for panel in ("primary", "auxiliary"):
        for slot in range(count):
            name = family
            if panel == "auxiliary" and family == "openllm" and slot % 2:
                name = "bbh"
            task_ids = matrices[name]["task_ids"]
            selected_ids = base[name][1] if panel == "primary" or name == "bbh" else sorted(base[name][1])[:6]
            columns = [index for index,task in enumerate(task_ids) if task in set(selected_ids)]
            for rule in RULES:
                for alpha in (.25,.5,1.0):
                    decisions.append({"id": str(len(decisions)), "matrix": name,
                                      "target": target_rows[name][slot], "columns": columns,
                                      "rule": rule, "alpha": 0.0 if case == "copy" else alpha,
                                      "node_budget": 20000})
                    roles.append({"panel":panel,"slot":slot,"alpha":alpha,"cluster":panels[name]["clusters"][target_rows[name][slot]]})
    blobs = []
    specifications = []
    offset = 0
    for name, matrix in matrices.items():
        data = matrix["values"].tobytes()
        blobs.append(data)
        specifications.append({"key":name,"shape":list(matrix["values"].shape),"offset":offset,"task_ids":matrix["task_ids"]})
        offset += len(data)
    blob = b"".join(blobs)
    if not 0 < len(blob) <= 64*CHUNK_BYTES:
        raise ValueError("logical input exceeds declared maximum")
    return {"matrices":matrices,"base":base,"decisions":decisions,"roles":roles,"specifications":specifications,"blob":blob}


def decision_context(prepared, decision):
    matrix = prepared["matrices"][decision["matrix"]]["values"][:,decision["columns"]]
    target = decision["target"]
    scores = aggregate_rows(matrix, decision["rule"])
    rivals = np.delete(scores,target)
    return {"values":matrix[target].copy(),"threshold":float(np.max(rivals))+TOLERANCE,
            "rule":decision["rule"],"alpha":decision["alpha"],"columns":decision["columns"]}


def wins(context, selected):
    values = context["values"].copy()
    values[selected] += context["alpha"]*(1-values[selected])
    return float(aggregate_rows(values,context["rule"])) > context["threshold"]


def verified_bound(context, deadline):
    size = len(context["values"])
    if not wins(context,list(range(size))):
        return size+1
    if size <= 6:
        for count in range(size+1):
            for selected in itertools.combinations(range(size),count):
                check_deadline(deadline)
                if wins(context,list(selected)):
                    return count
    gains = np.sort(context["alpha"]*(1-context["values"]))[::-1]
    if context["rule"] == "mean":
        order = np.argsort(-(context["alpha"]*(1-context["values"])),kind="stable")
        for count in range(size+1):
            if wins(context,order[:count].tolist()):
                return count
        return size+1
    factor = 1.0
    if context["rule"] == "median" and size%2 == 0:
        factor = .5
    if context["rule"] == "trimmed":
        factor = 1.0/(size-2*(size//5))
    initial = float(aggregate_rows(context["values"],context["rule"]))
    for count in range(size+1):
        if initial+factor*float(np.sum(gains[:count])) > context["threshold"]-1e-12:
            return count
    return 0


def baseline_plan(context, kind, rng, deadline):
    size = len(context["values"])
    if kind == "zero":
        return []
    if not wins(context,list(range(size))):
        return []
    if kind == "random":
        order = rng.permutation(size).tolist()
        selected = []
        for column in order:
            check_deadline(deadline)
            if wins(context,selected):
                break
            selected.append(column)
        return selected
    selected = []
    current = context["values"].copy()
    while not wins(context,selected):
        check_deadline(deadline)
        available = [column for column in range(size) if column not in selected]
        trials = np.repeat(current[None,:], len(available), axis=0)
        positions = np.arange(len(available))
        trials[positions,available] += context["alpha"]*(1-trials[positions,available])
        gains = aggregate_rows(trials,context["rule"])
        column = available[int(np.argmax(gains))]
        selected.append(column)
        current[column] += context["alpha"]*(1-current[column])
    return selected


def transfer(prepared, call, deadline):
    def timed(request):
        check_deadline(deadline)
        return call(request,timeout=max(.001,deadline-time.monotonic()))
    blob = prepared["blob"]
    chunks = math.ceil(len(blob)/CHUNK_BYTES)
    for index in range(chunks):
        data = blob[index*CHUNK_BYTES:(index+1)*CHUNK_BYTES]
        request = {"op":"upload","index":index,"total":chunks,"total_bytes":len(blob),
                   "shape":[len(blob)//8],"dtype":"float64","byte_order":"little","encoding":"base64",
                   "length":len(data),"sha256":hashlib.sha256(data).hexdigest(),"data":base64.b64encode(data).decode("ascii")}
        response = timed(request)
        if type(response) is not dict or response != {"ok":True} or type(response["ok"]) is not bool:
            raise ProtocolFailure()
    remaining_seconds = deadline-time.monotonic()
    if remaining_seconds <= 0:
        raise TimeoutError()
    result = timed({"op":"run","matrices":prepared["specifications"],"decisions":prepared["decisions"],
                    "work_seconds":remaining_seconds})
    require_keys(result,("chunks","total_bytes","sha256"))
    count = integer(result["chunks"],1,16)
    total_bytes = integer(result["total_bytes"],1,16*CHUNK_BYTES)
    if count != math.ceil(total_bytes/CHUNK_BYTES) or type(result["sha256"]) is not str or not re.fullmatch("[0-9a-f]{64}",result["sha256"]):
        raise ProtocolFailure()
    pieces = []
    for index in range(count):
        response = timed({"op":"read","index":index})
        require_keys(response,("index","encoding","length","sha256","data"))
        if integer(response["index"],0,15) != index or response["encoding"] != "base64" or type(response["data"]) is not str:
            raise ProtocolFailure()
        length = integer(response["length"],1,CHUNK_BYTES)
        if len(response["data"]) != 4*math.ceil(length/3):
            raise ProtocolFailure()
        try:
            data = base64.b64decode(response["data"],validate=True)
        except ValueError as error:
            raise ProtocolFailure() from error
        if len(data) != length or hashlib.sha256(data).hexdigest() != response["sha256"]:
            raise ProtocolFailure("chunk_integrity")
        pieces.append(data)
    output = b"".join(pieces)
    if len(output) != total_bytes or hashlib.sha256(output).hexdigest() != result["sha256"]:
        raise ProtocolFailure("transfer_integrity")
    response = timed({"op":"release"})
    if type(response) is not dict or response != {"ok":True} or type(response["ok"]) is not bool:
        raise ProtocolFailure()
    parsed = decode_json(output)
    require_keys(parsed,("plans",))
    if type(parsed["plans"]) is not list or len(parsed["plans"]) != len(prepared["decisions"]):
        raise ProtocolFailure()
    return parsed["plans"]


def score_plans(prepared, plans, contexts, bounds, baselines, deadline):
    details = []
    valid = True
    primary = []
    control = []
    signatures = []
    for index, (decision, plan, context, lower) in enumerate(zip(prepared["decisions"],plans,contexts,bounds)):
        check_deadline(deadline)
        require_keys(plan,("id","selected","status","lower_bound"))
        if plan["id"] != decision["id"] or type(plan["selected"]) is not list or plan["status"] not in ("bounded","optimal","infeasible"):
            raise ProtocolFailure()
        columns = decision["columns"]
        size = len(columns)
        lower_claim = integer(plan["lower_bound"],0,size+1)
        selected = plan["selected"]
        for column in selected:
            integer(column,0,prepared["matrices"][decision["matrix"]]["values"].shape[1]-1)
        if len(set(selected)) != len(selected) or not set(selected) <= set(columns):
            raise ProtocolFailure("illegal_intervention")
        positions = [columns.index(column) for column in selected]
        feasible = wins(context,positions)
        claim_valid = lower_claim <= lower
        if plan["status"] == "infeasible":
            claim_valid = lower == size+1 and not selected and lower_claim == size+1
        elif plan["status"] == "optimal":
            claim_valid = feasible and len(selected) == lower and lower_claim == lower
        valid = valid and claim_valid
        utility = 1-len(selected)/size if feasible and claim_valid else 0.0
        effort = len(selected)/size if feasible and claim_valid else 1.0
        gap = (len(selected)-lower)/size if feasible and claim_valid else (0.0 if lower == size+1 and claim_valid else 1.0)
        upper = len(selected) if feasible else size+1
        role = prepared["roles"][index]
        if role["panel"] == "primary":
            primary.append((utility,float(feasible and claim_valid),effort,gap))
        audit_pass = claim_valid
        control.append(float(audit_pass))
        ids = prepared["matrices"][decision["matrix"]]["task_ids"]
        signatures.append((plan["status"],lower_claim,tuple(sorted(ids[column] for column in selected))))
        reference = {}
        for kind in ("zero","random","greedy"):
            subset = baselines[kind][index]
            reference[kind] = {"feasible":wins(context,subset),"effort_fraction":len(subset)/size if wins(context,subset) else 1.0}
        details.append({"id":decision["id"],"panel":role["panel"],"slot":role["slot"],"cluster":role["cluster"],
                        "rule":decision["rule"],"alpha":role["alpha"],"selected":selected,
                        "status":plan["status"],"verified_feasible":feasible,"lower":lower,"upper":upper,
                        "normalized_lift":float(np.sum(context["alpha"]*(1-context["values"])[positions])),
                        "utility":utility,"effort_fraction":effort,"gap_fraction":gap,"baseline":reference,
                        "exact_audit_pass":audit_pass})
    mean_primary = np.mean(primary,axis=0).tolist()
    return {"utility":mean_primary[0],"feasible":mean_primary[1],"effort":mean_primary[2],"gap":mean_primary[3],
            "control":float(np.mean(control)),"valid":bool(valid),"details":details,"signature":signatures,"duration_seconds":0.0}


def worst_case(episode):
    return {"utility":0.0,"feasible":0.0,"effort":1.0,"gap":1.0,"control":0.0,
            "valid":False,"details":[],"signature":None,"duration_seconds":0.0}


def evaluate_episode(episode, call, deadline, panels, smoke):
    prepared = prepare_episode(episode,panels,smoke)
    work = 1.0 if smoke else WORK_SECONDS
    cleanup = .05
    check_deadline(deadline)
    contexts = [decision_context(prepared,decision) for decision in prepared["decisions"]]
    reference_deadline = min(deadline, time.monotonic()+(2.0 if not smoke else .8))
    try:
        bounds = [verified_bound(context,reference_deadline) for context in contexts]
    except TimeoutError as error:
        raise RequiredBaselineFailure("baseline_timeout") from error
    baselines = {}
    baseline_seconds = {}
    methods = ("zero","random","greedy","candidate")
    for index, method in enumerate(methods):
        method_deadline = reserved_method_deadline(now=time.monotonic(),episode_deadline=deadline,
                             methods_remaining=len(methods)-index-1,work_seconds=work,cleanup_seconds=cleanup)
        if method == "candidate":
            plans = transfer(prepared,call,method_deadline)
        else:
            rng = np.random.default_rng(episode["seed"])
            try:
                productive_started = time.monotonic()
                baselines[method] = [baseline_plan(context,method,rng,method_deadline) for context in contexts]
                baseline_seconds[method] = time.monotonic()-productive_started
                check_deadline(method_deadline)
            except TimeoutError as error:
                raise RequiredBaselineFailure("baseline_timeout") from error
    outcome = score_plans(prepared,plans,contexts,bounds,baselines,deadline)
    outcome["baseline_productive_seconds"] = baseline_seconds
    return outcome


def fixed_mean(values):
    if not values or not all(type(value) in (int,float) and math.isfinite(value) for value in values):
        raise ValueError("nonfinite fixed contribution")
    return sum(values)/len(values)


def aggregate_outcomes(episodes, outcomes):
    primary = list(zip(episodes[:-1],outcomes[:-1]))
    replay_ok = outcomes[0]["valid"] and outcomes[-1]["valid"] and outcomes[0]["signature"] == outcomes[-1]["signature"]
    all_valid = all(outcome["valid"] for outcome in outcomes) and replay_ok
    ordinary = [outcome for episode,outcome in primary if episode["case"] == "ordinary"]
    controls = [outcome for episode,outcome in primary if episode["case"] != "ordinary"]
    by_key = {(episode["family"],episode["case"],episode["seed"]):outcome for episode,outcome in primary}
    seeds = sorted({episode["seed"] for episode,outcome in primary})
    permutation_ok = True
    for family in ("helm","openllm"):
        for seed in seeds:
            original = by_key[(family,"ordinary",seed)]
            permuted = by_key[(family,"permutation",seed)]
            if not original["details"] or not permuted["details"]:
                permutation_ok = False
                continue
            for left,right in zip(original["details"],permuted["details"]):
                if left["panel"] == "auxiliary" and left["exact_audit_pass"]:
                    if left["verified_feasible"] != right["verified_feasible"] or left["upper"] != right["upper"] or left["lower"] != right["lower"]:
                        permutation_ok = False
                        permuted["control"] = 0.0
    expected = {(family,case,seed) for family in ("helm","openllm") for case in CASES[1:] for seed in seeds}
    completed = {key for key,value in by_key.items() if key[1] != "ordinary" and value["valid"]}
    controls_ok = not (expected-completed) and all(outcome["control"] == 1.0 for outcome in controls) and permutation_ok
    scores = []
    for family in ("helm","openllm"):
        scores.append(.7*fixed_mean([by_key[(family,"ordinary",seed)]["utility"] for seed in seeds])+
                      sum(.1*fixed_mean([by_key[(family,case,seed)]["control"] for seed in seeds]) for case in CASES[1:]))
    correct = bool(all_valid and controls_ok)
    metrics = {"combined_score":fixed_mean(scores),"correct":float(correct),
               "feasible_rate":fixed_mean([value["feasible"] for value in ordinary]),
               "mean_effort_fraction":fixed_mean([value["effort"] for value in ordinary]),
               "mean_verified_gap_fraction":fixed_mean([value["gap"] for value in ordinary]),
               "control_pass_rate":fixed_mean([value["control"] for value in controls])}
    return metrics,correct


def preflight(smoke):
    for target_count, episode_count, wall_seconds in ((12, 17, 900), (24, 25, 1800)):
        work_seconds = target_count * (5.0 / 12)
        required = STARTUP_ALLOWANCE+FINISH_RESERVE+episode_count*(RESET_TIMEOUT+EPISODE_OVERHEAD+4*(work_seconds+.05)+3.0)
        if required > wall_seconds:
            raise ValueError("joint production workload reservations exceed deadline")
    episodes = 9 if smoke else 8*len(SEEDS)+1
    work = 1.0 if smoke else WORK_SECONDS
    wall = 120.0 if smoke else WALL_SECONDS
    needed = STARTUP_ALLOWANCE+FINISH_RESERVE+episodes*(RESET_TIMEOUT+EPISODE_OVERHEAD+4*(work+.05)+(1.0 if smoke else 3.0))
    if needed > wall:
        raise ValueError("joint productive workload reservations exceed deadline")
    maximum = b"x"*CHUNK_BYTES
    encoded = base64.b64encode(maximum).decode("ascii")
    request = {"op":"upload","index":63,"total":64,"total_bytes":64*CHUNK_BYTES,"shape":[8388608],
               "dtype":"float64","byte_order":"little","encoding":"base64","length":CHUNK_BYTES,
               "sha256":"f"*64,"data":encoded}
    response = {"index":15,"encoding":"base64","length":CHUNK_BYTES,"sha256":"f"*64,"data":encoded}
    sizes = [len(bounded_json_line(value)) for value in (request,response,
              {"request":request,"rpc_id":9999999,"protocol":"python_rpc_v1"},
              {"response":response,"rpc_id":9999999,"protocol":"python_rpc_v1"})]
    if max(sizes) >= WIRE_LIMIT:
        raise ValueError("wire preflight failed")
    maximum_decision = {"id":"9"*8,"matrix":"m"*80,"target":9999,"columns":list(range(100)),
                        "rule":"trimmed","alpha":.25,"node_budget":20000}
    maximum_run = {"op":"run","work_seconds":19.999999999999996,"matrices":[{"key":"m"*80,"shape":[10000,100],"offset":64000000,
                    "task_ids":["学"*128+str(index) for index in range(100)]} for _ in range(2)],
                   "decisions":[maximum_decision for _ in range(432)]}
    bounded_json_line({"request":maximum_run,"rpc_id":9999999,"protocol":"python_rpc_v1"})
    maximum_plans = {"plans":[{"id":"9"*8,"selected":list(range(100)),"status":"infeasible","lower_bound":101} for _ in range(432)]}
    bounded_json_line(maximum_plans)
    trace = [operation for _ in range(episodes) for operation in
             (["reset"]+["upload"]*64+["run"]+["read"]*16+["release"])]
    counts = dict(collections.Counter(trace))
    if sum(counts.values()) > RPC_BUDGET or not smoke and sum(counts.values()) != RPC_BUDGET:
        raise ValueError("operation-count budget mismatch")
    return counts


def paired_intervals(entries):
    result = []
    rng = np.random.default_rng(48271)
    for entry in entries:
        if entry["case"] != "ordinary":
            continue
        rows = [row for row in entry["decisions"] if row["panel"] == "primary"]
        if not rows:
            result.append({"family":entry["family"],"complete":False})
            continue
        for rule in RULES:
            for alpha in (.25,.5,1.0):
                selected = [row for row in rows if row["rule"] == rule and row["alpha"] == alpha]
                clusters = sorted({row["cluster"] for row in selected})
                for baseline in ("random","greedy"):
                    differences = {cluster:fixed_mean([row["effort_fraction"]-row["baseline"][baseline]["effort_fraction"]
                                   for row in selected if row["cluster"] == cluster]) for cluster in clusters}
                    values = np.array([differences[cluster] for cluster in clusters])
                    replicates = np.mean(values[rng.integers(0,len(values),size=(200,len(values)))],axis=1)
                    result.append({"family":entry["family"],"rule":rule,"alpha":alpha,"baseline":baseline,
                                   "complete":True,"mean_effort_difference":float(np.mean(values)),
                                   "conditional_cluster_percentile_95":[float(value) for value in np.quantile(replicates,[.025,.975])]})
    return result


def evidence_records(episodes,outcomes):
    records = []
    for seed in sorted({episode["seed"] for episode in episodes[:-1]}):
        selected = [(episode,outcome) for episode,outcome in zip(episodes[:-1],outcomes[:-1]) if episode["seed"] == seed]
        entries = []
        scores = []
        for episode,outcome in selected:
            entries.append({"family":episode["family"],"case":episode["case"],"valid":outcome["valid"],"decisions":outcome["details"],
                            "baseline_productive_seconds":outcome.get("baseline_productive_seconds")})
            scores.append((.7 if episode["case"] == "ordinary" else .1)*(outcome["utility"] if episode["case"] == "ordinary" else outcome["control"])/2)
        records.append({"seed":seed,"score":sum(scores),"correct":all(outcome["valid"] and (episode["case"] == "ordinary" or outcome["control"] == 1.0) for episode,outcome in selected),
                        "duration_seconds":sum(outcome["duration_seconds"] for _,outcome in selected),
                        "solution":{"episodes":entries,"paired_intervals":paired_intervals(entries)}})
    replay_duration = outcomes[-1]["duration_seconds"]
    records[0]["duration_seconds"] += replay_duration
    records[0]["correct"] = records[0]["correct"] and outcomes[-1]["valid"] and outcomes[0]["signature"] == outcomes[-1]["signature"]
    return {"schema_version":1,"episodes":records}


def write_outputs(directory, metrics, correct, feasible, evidence=None):
    directory.mkdir(parents=True,exist_ok=True)
    if set(metrics) != set(METRIC_NAMES) or not all(type(value) in (int,float) and math.isfinite(value) for value in metrics.values()):
        raise ValueError("invalid scalar result schema")
    (directory/"metrics.json").write_bytes(bounded_json_line(metrics))
    (directory/"correct.json").write_bytes(bounded_json_line({"correct":bool(correct)}))
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        (directory/"qualification.json").write_bytes(bounded_json_line({"schema_version":1,"feasible":bool(feasible)}))
    else:
        (directory/"qualification.json").unlink(missing_ok=True)
    (directory/"evaluation_evidence.json").unlink(missing_ok=True)
    if evidence is not None:
        encoded = bounded_json_line(evidence)
        if len(encoded) <= 16*CHUNK_BYTES:
            (directory/"evaluation_evidence.json").write_bytes(encoded)


def main():
    started = INVOCATION_STARTED
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path",required=True)
    parser.add_argument("--results_dir",required=True)
    args = parser.parse_args()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    hard_deadline = started+(120 if smoke else WALL_SECONDS)-STARTUP_ALLOWANCE
    results = Path(args.results_dir)
    worst = {"combined_score":0.0,"correct":0.0,"feasible_rate":0.0,"mean_effort_fraction":1.0,"mean_verified_gap_fraction":1.0,"control_pass_rate":0.0}
    client = None
    try:
        preflight(smoke)
        root = Path(os.environ.get("TASK_SOURCE_DIR",Path(__file__).resolve().parent))/"resources"/PLANE
        panels = load_resources(root)
        seeds = SEEDS[:1] if smoke else SEEDS
        episodes = [{"family":family,"case":case,"seed":seed} for family in ("helm","openllm") for case in CASES for seed in seeds]
        episodes.append(dict(episodes[0]))
        client = Client(args.program_path)
        work = 1.0 if smoke else WORK_SECONDS
        episode_cap = 4*(work+.05)+(1.0 if smoke else 3.0)+EPISODE_OVERHEAD
        def evaluate(episode,call,deadline):
            return evaluate_episode(episode,call,min(deadline,time.monotonic()+episode_cap),panels,smoke)
        outcomes,complete = run_declared_episodes(episodes,hard_deadline=hard_deadline,finish_reserve=FINISH_RESERVE,
                              reset_timeout=RESET_TIMEOUT,episode_overhead=EPISODE_OVERHEAD,rpc_cap=RPC_CAP,
                              clock=time.monotonic,rpc=client.call,evaluate=evaluate,worst_case=worst_case,
                              record_failure=record_failure,cancel=lambda failed:client.close(failed=failed))
        metrics,correct = aggregate_outcomes(episodes,outcomes)
        elapsed = time.monotonic()-started+STARTUP_ALLOWANCE
        cpu = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu_seconds = cpu.ru_utime+cpu.ru_stime+children.ru_utime+children.ru_stime
        feasible = bool(complete and not client.cleanup_errors and elapsed < (120 if smoke else WALL_SECONDS) and cpu_seconds <= 2*WALL_SECONDS and client.calls <= RPC_BUDGET)
        correct = bool(correct and feasible)
        metrics["correct"] = float(correct)
        write_outputs(results,metrics,correct,feasible and not smoke,evidence_records(episodes,outcomes))
        return 0
    except Exception as error:
        if client is not None:
            try:
                client.close(failed=True)
            except Exception:
                error.add_note("secondary candidate cleanup failure")
                record_failure({"component":"candidate","category":"cleanup_failure","operation":"cleanup"})
        write_outputs(results,worst,False,False)
        name = type(error).__name__
        message = str(error) if PLANE == "search" else "sealed evaluator failure"
        if len(message.encode("utf-8",errors="replace")) > 180:
            message = "exception message omitted"
        print((name+": "+message)[:256],file=sys.stderr)
        return 1
    finally:
        if client is not None:
            client.close()


if __name__ == "__main__":
    raise SystemExit(main())
