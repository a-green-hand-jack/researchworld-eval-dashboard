"""Self-contained evaluator. Search is a completeness proxy, not a reliability target.

Scientific validity, search eligibility and publication claims are distinct. Missing
real cases retain fixed penalties; controls and required references cannot be waived.
Only evaluator-owned oracle traces, recomputed regressions and matched controls
support validity. No candidate internal-state or self-reported metric is trusted.
"""

import argparse
import base64
import collections
import ctypes
import decimal
import hashlib
import importlib.util
import json
import math
import os
import pathlib
import pickle
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

STARTED = time.monotonic()
sys.dont_write_bytecode = True
PLANE = "final"
WALL = 50400
SEEDS = [7301, 9109]
RPC_BUDGET = 10287
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
    resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(WALL), math.ceil(WALL) + 1))
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
for thread_name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[thread_name] = "1"
os.environ["NUMBA_NUM_THREADS"] = "1"

import numpy as np
import pandas as pd
import shap
from folktables import ACSIncome
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

METRICS = ("combined_score", "correct", "coverage", "repeat_agreement", "reference_fidelity",
           "local_accuracy_quality", "matched_budget_gain", "reference_resolution_quality", "control_pass_fraction")
QUALITY = ("repeat_agreement", "reference_fidelity", "local_accuracy_quality", "matched_budget_gain", "reference_resolution_quality")
FEATURES = ['AGEP', 'COW', 'SCHL', 'MAR', 'OCCP', 'POBP', 'RELP', 'WKHP', 'SEX', 'RAC1P']
CASES = [(dataset, family) for dataset in ("german", "acs") for family in ("logistic", "forest", "boosting")]
WIRE = 64 * 1024 * 1024


def bounded_json_line(value, wire_limit=WIRE):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":"), ensure_ascii=False).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ProtocolError("wire_limit")
    return encoded


def validate_wire(value):
    try:
        bounded_json_line(value, 60 * 1024 * 1024)
        bounded_json_line({"request": value, "response": value, "id": 9223372036854775807,
                           "protocol": "python_rpc_v1"})
    except (TypeError, ValueError, RecursionError, OverflowError):
        raise ProtocolError("invalid_json_value") from None


class ProtocolError(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_protocol")
        super().__init__("protocol failure")


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
        if isinstance(context, ProtocolError):
            return {"component": "candidate", "category": "malformed_response", "operation": bounded_failure_name(operation, "unknown")}
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


def finite_budget_seconds(value):
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
            "wall_seconds", "startup_seconds", "reset_seconds", "cleanup_seconds", "finish_seconds")}
        work = positive_work_seconds(profile["work_seconds"])
        needed = (times["startup_seconds"] + times["finish_seconds"]
                  + episodes * (times["reset_seconds"] + methods * (work + times["cleanup_seconds"])))
        if needed > times["wall_seconds"]:
            raise ValueError("productive work exceeds declared wall budget")
        required[plane] = needed
    return required


def reserved_method_deadline(*, now, episode_deadline, methods_remaining, work_seconds, cleanup_seconds):
    for value in (now, episode_deadline, cleanup_seconds):
        finite_budget_seconds(value)
    work = positive_work_seconds(work_seconds)
    if type(methods_remaining) is not int or methods_remaining < 0:
        raise ValueError("invalid remaining method count")
    if now + (methods_remaining + 1) * (work + cleanup_seconds) > episode_deadline:
        raise TimeoutError("insufficient matched method reservations")
    return now + work


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


def repair_mode():
    return PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                  or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


def emit_capture(snapshot, category, operation):
    if PLANE == "search":
        print(f"worker category={bounded_failure_name(category, 'worker_failure')} operation={operation} "
              f"observed_bytes={snapshot['observed_bytes']} retained_bytes={snapshot['retained_bytes']} "
              f"truncated={int(snapshot['truncated'])} capture_error={snapshot['capture_error'] or 'none'}", file=sys.stderr)
        if repair_mode() and snapshot["stderr"]:
            print(snapshot["stderr"], file=sys.stderr, end="")


def record_failure(failure):
    if PLANE == "search":
        print((f"episode_failure component={failure['component']} category={failure['category']} "
               f"operation={failure['operation']}")[:256], file=sys.stderr, flush=True)


def candidate_subprocess_settings(parent_environment):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES",
                     "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES", "OMP_NUM_THREADS",
                     "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
                     "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION", "XLA_PYTHON_CLIENT_ALLOCATOR")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


NATIVE_RUNNER = r'''
import ctypes, importlib.util, json, os, pathlib, resource, sys
lib = ctypes.CDLL(None, use_errno=True)
def checked(value):
    if value < 0:
        raise OSError(ctypes.get_errno(), "sandbox setup failed")
    return value
checked(lib.prctl(38, 1, 0, 0, 0))
class Ruleset(ctypes.Structure):
    _fields_ = [("handled", ctypes.c_uint64)]
class PathRule(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed", ctypes.c_uint64), ("parent", ctypes.c_int)]
access = (1 << 15) - 1
ruleset = checked(lib.syscall(444, ctypes.byref(Ruleset(access)), 8, 0))
allowed = ["/usr", "/lib", "/lib64", "/bin", sys.prefix, sys.argv[1],
           "/etc/ld.so.cache", "/etc/localtime", "/dev/null", "/dev/urandom", "/dev/random"]
for path in allowed:
    if os.path.exists(path):
        descriptor = os.open(path, os.O_PATH | os.O_CLOEXEC)
        rights = (1 | 4 | 8) if os.path.isdir(path) else (1 | 4)
        checked(lib.syscall(445, ruleset, 1, ctypes.byref(PathRule(rights, descriptor)), 0))
        os.close(descriptor)
checked(lib.syscall(446, ruleset, 0))
os.close(ruleset)
class Filter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]
class Program(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filter", ctypes.POINTER(Filter))]
filters = [Filter(0x20, 0, 0, 4), Filter(0x15, 1, 0, 0xc000003e), Filter(0x06, 0, 0, 0x80000000), Filter(0x20, 0, 0, 0), Filter(0x35, 0, 1, 0x40000000), Filter(0x06, 0, 0, 0x80000000)]
for number in [41, 42, 43, 49, 50, 53, 56, 57, 58, 59, 101, 272, 288, 308, 310, 311, 322, 435]:
    filters.extend([Filter(0x15, 0, 1, number), Filter(0x06, 0, 0, 0x00050001)])
filters.append(Filter(0x06, 0, 0, 0x7fff0000))
array = (Filter * len(filters))(*filters)
checked(lib.prctl(22, 2, ctypes.byref(Program(len(filters), array)), 0, 0))
resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
resource.setrlimit(resource.RLIMIT_CPU, (int(sys.argv[2]), int(sys.argv[2]) + 1))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
os.chdir(sys.argv[1])
sys.path.insert(0, sys.argv[1])
spec = importlib.util.spec_from_file_location("candidate", os.path.join(sys.argv[1], "program.py"))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin.buffer:
    if len(line) >= 64 * 1024**2:
        raise ValueError("request too large")
    result = module.handle(json.loads(line))
    encoded = json.dumps(result, allow_nan=False, separators=(",", ":")).encode() + b"\n"
    if len(encoded) >= 64 * 1024**2:
        raise ValueError("response too large")
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()
'''


def exchange(process, request, deadline):
    payload = bounded_json_line(request)
    output = bytearray()
    offset = 0
    with selectors.DefaultSelector() as selector:
        selector.register(process.stdin, selectors.EVENT_WRITE)
        selector.register(process.stdout, selectors.EVENT_READ)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("transport deadline")
            for key, _ in selector.select(min(remaining, .1)):
                if key.fileobj is process.stdin:
                    try:
                        offset += os.write(process.stdin.fileno(), payload[offset:offset + 8192])
                    except BrokenPipeError:
                        raise ProtocolError("worker_exit") from None
                    if offset == len(payload):
                        selector.unregister(process.stdin)
                else:
                    chunk = os.read(process.stdout.fileno(), 8192)
                    if not chunk:
                        raise ProtocolError("worker_exit")
                    output.extend(chunk)
                    if len(output) >= 60 * 1024**2:
                        raise ProtocolError("wire_limit")
                    if b"\n" in output:
                        if output.count(b"\n") != 1 or not output.endswith(b"\n"):
                            raise ProtocolError("invalid_framing")
                        try:
                            response = json.loads(output, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
                            validate_wire(response)
                            return response
                        except (ValueError, UnicodeError, RecursionError):
                            raise ProtocolError("invalid_json") from None


def stop_process(process):
    if process is None:
        return
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=.5)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.wait(timeout=.5)
    for stream in (process.stdin, process.stdout):
        stream.close()


class Candidate:
    def __init__(self, path):
        self.path = path
        self.process = None
        self.capture = None
        self.scratch = None
        self.calls = 0
        self.proxy = None
        if path == "/broker-code/candidate_proxy.py":
            if not os.environ.get("AGENTIC_CANDIDATE_SOCKET"):
                raise RuntimeError("broker socket required")
            spec = importlib.util.spec_from_file_location("broker_proxy", path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.proxy = module.handle

    def close(self, failure=False, operation="unknown"):
        process, capture, scratch = self.process, self.capture, self.scratch
        self.process = self.capture = self.scratch = None
        try:
            if process is not None:
                try:
                    stop_process(process)
                finally:
                    snapshot = capture.close()
                if failure:
                    emit_capture(snapshot, "candidate_worker_failure", operation)
        finally:
            if scratch is not None:
                scratch.cleanup()

    def call(self, request, timeout):
        self.calls += 1
        if self.calls > RPC_BUDGET:
            raise ProtocolError("rpc_budget")
        validate_wire(request)
        if self.proxy is not None:
            previous = signal.getsignal(signal.SIGALRM)
            signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("rpc deadline")))
            signal.setitimer(signal.ITIMER_REAL, timeout)
            try:
                result = self.proxy(request)
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
                signal.signal(signal.SIGALRM, previous)
            validate_wire(result)
            return result
        deadline = time.monotonic() + timeout
        if request["op"] == "reset":
            self.close()
            self.scratch = tempfile.TemporaryDirectory(prefix="candidate-")
            destination = pathlib.Path(self.scratch.name)
            for source in pathlib.Path(self.path).parent.iterdir():
                if source.is_file() and not source.is_symlink():
                    shutil.copyfile(source, destination / ("program.py" if source == pathlib.Path(self.path) else source.name))
            interpreter, environment = candidate_subprocess_settings(os.environ)
            self.process = subprocess.Popen([interpreter, "-I", "-u", "-c", NATIVE_RUNNER,
                                             str(destination), str(math.ceil(WALL))],
                                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            env=environment, cwd=destination, start_new_session=True, shell=False)
            self.capture = BoundedWorkerStderr(self.process.stderr)
            os.set_blocking(self.process.stdin.fileno(), False)
            os.set_blocking(self.process.stdout.fileno(), False)
        if self.process is None:
            raise ProtocolError("candidate_not_running")
        try:
            return exchange(self.process, request, deadline)
        except (TimeoutError, ProtocolError) as error:
            try:
                self.close(failure=True, operation=request["op"])
            except Exception:
                error.add_note("secondary candidate cleanup failure")
                if PLANE == "search":
                    print("worker_cleanup_failure component=candidate category=cleanup_failed", file=sys.stderr)
            raise


def normalize(value):
    text = " ".join(unicodedata.normalize("NFKC", str(value)).split())
    if not text:
        return "<MISSING>"
    try:
        number = decimal.Decimal(text)
        if number.is_finite():
            return "0" if number == 0 else format(number.normalize(), "f")
    except decimal.InvalidOperation:
        pass
    return text


def content_hash(values):
    return hashlib.sha256(json.dumps([normalize(value) for value in values], ensure_ascii=False,
                                    separators=(",", ":")).encode()).hexdigest()


def load_data(root):
    data = json.loads((root / "data.json").read_text())
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest["content_overlap"] != 0 or manifest["acs_features"] != FEATURES:
        raise ValueError("invalid split manifest")
    for dataset, groups in data.items():
        seen = set()
        identifiers = set()
        for role, entries in groups.items():
            for entry in entries:
                raw = entry["raw"]
                fields = raw[:20] if dataset == "german" else [raw[column] for column in FEATURES]
                digest = content_hash(fields)
                raw_fields = fields if dataset == "german" else [raw[column if column != 'RELP' else 'RELSHIPP'] for column in FEATURES]
                if content_hash(raw_fields) != entry["raw_predictor_hash"]:
                    raise ValueError("raw predictor integrity failure")
                if digest != entry["predictor_hash"] or digest in seen or entry["source_id"] in identifiers:
                    raise ValueError("content/provenance integrity failure")
                expected_plane = "search" if int(digest[:8], 16) % 100 < 40 else "final"
                bucket = int(digest[8:16], 16) % 100
                expected_role = "train" if bucket < 60 else ("validation" if bucket < 80 else "explain")
                if expected_plane != PLANE or expected_role != role:
                    raise ValueError("split membership failure")
                seen.add(digest)
                identifiers.add(entry["source_id"])
    return data


def arrays(entries, dataset):
    if dataset == "german":
        numeric = [1, 4, 7, 10, 12, 15, 17]
        rows = [[float(value) if index in numeric else value for index, value in enumerate(entry["raw"][:20])]
                for entry in entries]
        return np.array(rows, dtype=object), np.array([int(entry["raw"][20]) == 2 for entry in entries])
    frame = pd.DataFrame([entry["raw"] for entry in entries]).apply(pd.to_numeric, errors="coerce")
    values, labels, _ = ACSIncome.df_to_numpy(frame)
    if len(values) != len(entries) or values.shape[1] != 10:
        raise ValueError("ACSIncome definition mismatch")
    return values, labels


def oracle(model, explained, background, masks, counters):
    masks = np.asarray(masks, dtype=int)
    results = []
    for offset in range(0, len(masks), 64):
        batch = masks[offset:offset + 64]
        masked = np.where(batch[:, None, :], explained[None, None, :], background[None, :, :])
        predictions = model.predict_proba(masked.reshape(-1, len(explained)))[:, 1]
        results.extend(predictions.reshape(len(batch), len(background)).mean(axis=1).tolist())
        counters["coalitions"] += len(batch)
        counters["masked_rows"] += len(batch) * len(background)
    return np.asarray(results, dtype=float)


def shap_reference(model, explained, background, budget, seed):
    np.random.seed(seed % 2**32)
    counters = {"prediction_rows": 0, "cpu_seconds": 0.0}
    def predict(rows):
        counters["prediction_rows"] += len(rows)
        return model.predict_proba(rows)[:, 1]
    started = time.process_time()
    explainer = shap.KernelExplainer(predict, background, link="identity")
    result = np.asarray(explainer.shap_values(explained[None, :], nsamples=budget - 2,
                                             l1_reg=0, silent=True)).reshape(-1)
    counters["cpu_seconds"] = time.process_time() - started
    counters["coalitions"] = int(getattr(explainer, "nsamplesAdded", 0)) + 2
    if result.shape != explained.shape or not np.isfinite(result).all():
        raise RuntimeError("reference output invalid")
    return result, counters


def exact_reference(model, explained, background, counters):
    features = len(explained)
    masks = ((np.arange(2**features)[:, None] >> np.arange(features)) & 1)
    values = oracle(model, explained, background, masks, counters)
    attribution = np.zeros(features)
    for feature in range(features):
        for subset in range(2**features):
            if not subset & (1 << feature):
                size = int(subset.bit_count())
                attribution[feature] += (values[subset | (1 << feature)] - values[subset]) / (features * math.comb(features - 1, size))
    return attribution


def prepare_case(config):
    started = time.monotonic()
    data = load_data(pathlib.Path(config["root"]))
    dataset, family = config["case"]
    seed = config["seed"]
    train, labels = arrays(data[dataset]["train"], dataset)
    validation, validation_labels = arrays(data[dataset]["validation"], dataset)
    heldout, heldout_labels = arrays(data[dataset]["explain"], dataset)
    if config["smoke"]:
        train, labels = train[:200], labels[:200]
    numeric = [1, 4, 7, 10, 12, 15, 17] if dataset == "german" else [0, 7]
    categorical = [index for index in range(train.shape[1]) if index not in numeric]
    preprocessing = ColumnTransformer([
        ("numeric", make_pipeline(SimpleImputer(strategy="median"), StandardScaler()), numeric),
        ("categorical", OneHotEncoder(handle_unknown="ignore", sparse_output=False), categorical)])
    estimator = {"logistic": lambda: LogisticRegression(C=1, max_iter=200, random_state=seed),
                 "forest": lambda: RandomForestClassifier(n_estimators=64, max_depth=6, n_jobs=1, random_state=seed),
                 "boosting": lambda: GradientBoostingClassifier(n_estimators=64, max_depth=3, random_state=seed)}[family]()
    model = make_pipeline(preprocessing, estimator)
    fit_started = time.process_time()
    model.fit(train, labels)
    fit_cpu = time.process_time() - fit_started
    confidence = model.predict_proba(heldout)[:, 1]
    order = []
    strata = [np.where(heldout_labels == label)[0] for label in (False, True)]
    strata = [indices[np.argsort(confidence[indices], kind="stable")] for indices in strata]
    for index in range(config["inputs"]):
        indices = strata[index % 2]
        order.append(int(indices[min(len(indices) - 1, (index // 2 + 1) * len(indices) // (config["inputs"] // 2 + 2))]))
    if len(set(order)) != len(order):
        raise RuntimeError("nonunique explained inputs")
    generator = np.random.default_rng(seed)
    background_indices = generator.permutation(len(train))
    cells = []
    for background_size in config["backgrounds"]:
        background = train[background_indices[:background_size]]
        for input_index, selected in enumerate(order):
            explained = heldout[selected]
            refs, reference_counters = [], []
            for repeat in range(2):
                value, counts = shap_reference(model, explained, background, config["reference_budget"], seed + 100 * input_index + repeat)
                refs.append(value)
                reference_counters.append(counts)
            deployments_and_counts = [shap_reference(model, explained, background, budget, seed + 2000 + input_index)
                                      for budget in config["budgets"]]
            deployments = [pair[0] for pair in deployments_and_counts]
            exact_counts = {"coalitions": 0, "masked_rows": 0}
            exact = exact_reference(model, explained, background, exact_counts) if dataset == "acs" else None
            cells.append({"input_index": input_index, "source_id": data[dataset]["explain"][selected]["source_id"],
                          "input": explained, "background": background, "references": refs,
                          "deployments": deployments, "reference_counts": reference_counters,
                          "deployment_counts": [pair[1] for pair in deployments_and_counts],
                          "exact": exact, "exact_counts": exact_counts})
    return {"model": model, "cells": cells, "validation_accuracy": float(accuracy_score(validation_labels, model.predict(validation))),
            "fit_cpu_seconds": fit_cpu, "training_rows": len(train), "validation_rows": len(validation), "selection_rows": len(heldout),
            "fitted_model_sha256": hashlib.sha256(pickle.dumps(model, protocol=5)).hexdigest(),
            "setup_seconds": time.monotonic() - started}


def baseline_worker(config, deadline):
    interpreter, environment = candidate_subprocess_settings(os.environ)
    if repair_mode():
        environment["AGENTIC_TASK_DRAFT_SMOKE"] = "1"
    process = subprocess.Popen([interpreter, "-I", "-u", str(pathlib.Path(__file__).resolve()), "--baseline-worker"],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               env=environment, start_new_session=True, shell=False)
    capture = BoundedWorkerStderr(process.stderr)
    os.set_blocking(process.stdin.fileno(), False)
    os.set_blocking(process.stdout.fileno(), False)
    category = None
    status = None
    try:
        try:
            reply = exchange(process, config, deadline)
            process.wait(timeout=max(.001, min(1, deadline - time.monotonic())))
        except TimeoutError:
            category = "baseline_timeout"
        except subprocess.TimeoutExpired:
            category = "baseline_timeout"
        except ProtocolError as error:
            status = process.poll()
            if status is None:
                try:
                    status = process.wait(timeout=.1)
                except subprocess.TimeoutExpired:
                    pass
            category = ("baseline_signal" if status is not None and status < 0 else
                        ("baseline_exit" if error.category == "worker_exit" else "baseline_result_failure"))
        if category is None:
            status = process.returncode
            if status != 0:
                category = "baseline_signal" if status < 0 else "baseline_exit"
            elif type(reply) is not dict or set(reply) != {"bundle"}:
                category = "baseline_result_failure"
        if category is not None:
            raise RequiredBaselineFailure(category)
        return pickle.loads(base64.b64decode(reply["bundle"], validate=True))
    finally:
        primary = sys.exception()
        try:
            try:
                stop_process(process)
            finally:
                snapshot = capture.close()
        except Exception:
            if primary is not None:
                primary.add_note("secondary baseline cleanup failure")
                raise primary from None
            raise RequiredBaselineFailure("baseline_result_failure") from None
        if category is not None:
            emit_capture(snapshot, category, "baseline_worker")
            if PLANE == "search":
                print(f"baseline_status exit={status if status is not None and status >= 0 else -1} signal={-status if status is not None and status < 0 else 0}", file=sys.stderr)


def checked_regression(masks, values):
    total = values[1] - values[0]
    design = masks[2:, :-1] - masks[2:, -1:]
    target = values[2:] - values[0] - masks[2:, -1] * total
    partial = np.linalg.lstsq(design, target, rcond=1e-10)[0]
    return np.append(partial, total - partial.sum())


def explain(call, model, explained, background, budget, stream, counters):
    started = time.monotonic()
    response = call({"op": "start", "features": len(explained), "budget": budget, "stream": stream,
                     "input": explained.tolist(), "background": background.tolist(),
                     "output": "positive_probability", "value_function": "interventional_grouped"})
    if type(response) is not dict or set(response) != {"masks"}:
        raise ProtocolError("mask_schema")
    try:
        masks = np.asarray(response["masks"])
    except (ValueError, TypeError):
        raise ProtocolError("mask_values") from None
    if (masks.shape != (budget, len(explained)) or masks.dtype.kind not in "iu"
            or not np.isin(masks, [0, 1]).all() or masks[0].any() or not masks[1].all()
            or np.any(masks[2:].sum(axis=1) == 0) or np.any(masks[2:].sum(axis=1) == len(explained))):
        raise ProtocolError("mask_values")
    values = oracle(model, explained, background, masks, counters)
    result = call({"op": "observe", "values": values.tolist()})
    if type(result) is not dict or set(result) != {"phi"}:
        raise ProtocolError("attribution_schema")
    if type(result["phi"]) is not list or any(type(value) not in (int, float) for value in result["phi"]):
        raise ProtocolError("attribution_values")
    try:
        attribution = np.asarray(result["phi"], dtype=float)
    except (TypeError, ValueError):
        raise ProtocolError("attribution_values") from None
    if attribution.shape != explained.shape or not np.isfinite(attribution).all() or np.abs(attribution).max() > 1e6:
        raise ProtocolError("attribution_values")
    expected = checked_regression(masks.astype(float), values)
    if not np.allclose(attribution, expected, rtol=1e-6, atol=1e-7):
        raise ProtocolError("regression_mismatch")
    trace_hash = hashlib.sha256(bounded_json_line({"masks": masks.tolist(), "values": values.tolist(), "phi": attribution.tolist()})).hexdigest()
    counters.setdefault("trace_hashes", []).append(trace_hash)
    if "first_trace" not in counters:
        counters["first_trace"] = {"masks": masks.tolist(), "values": values.tolist(), "phi": attribution.tolist()}
    return attribution, float(abs(attribution.sum() - (values[1] - values[0]))), time.monotonic() - started, trace_hash


def similarity(first, second):
    return float(1 / (1 + np.abs(first - second).sum() / max(1e-8, np.abs(second).sum())))


def agreements(first, second):
    count = min(3, len(first))
    first_order = np.argsort(-np.abs(first), kind="stable")
    second_order = np.argsort(-np.abs(second), kind="stable")
    top = len(set(first_order[:count]) & set(second_order[:count])) / count
    first_rank = np.argsort(first_order)
    second_rank = np.argsort(second_order)
    rank = 1 - float(np.abs(first_rank - second_rank).sum()) / max(1, len(first)**2 // 2)
    signs = lambda values: np.where(np.abs(values) <= 1e-8, 0, np.sign(values))
    sign = float(np.mean(signs(first) == signs(second)))
    return {"top_k": top, "rank": rank, "sign": sign, "discrepancy_quality": similarity(first, second)}


def scientific_case(episode, call, deadline, config):
    work = config["method_seconds"]
    baseline_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                methods_remaining=1, work_seconds=work, cleanup_seconds=2)
    bundle = baseline_worker({**config, "case": episode["case"], "seed": episode["seed"]}, baseline_deadline)
    candidate_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                 methods_remaining=0, work_seconds=work, cleanup_seconds=2)
    def bounded_call(request):
        if time.monotonic() >= candidate_deadline:
            raise TimeoutError("candidate method budget")
        return call(request, candidate_deadline)
    cells = []
    trace = []
    totals = {"coalitions": 0, "masked_rows": 0}
    stream = 0
    for source in bundle["cells"]:
        if time.monotonic() >= candidate_deadline:
            raise TimeoutError("candidate method budget")
        explained, background = source["input"], source["background"]
        refs = source["references"]
        reference = source["exact"] if source["exact"] is not None else (refs[0] + refs[1]) / 2
        rungs, agreement_values, fidelities, local_values = [], [], [], []
        for budget in config["budgets"]:
            repeats = []
            durations, residuals = [], []
            for _ in range(config["repeats"]):
                attribution, residual, duration, digest = explain(bounded_call, bundle["model"], explained, background, budget, stream, totals)
                stream += 1
                trace.append(digest)
                repeats.append(attribution)
                durations.append(duration)
                residuals.append(residual)
                local_values.append(1 / (1 + residual / 1e-6))
                fidelities.append(similarity(attribution, reference) if source["exact"] is not None
                                  else .5 * (similarity(attribution, refs[0]) + similarity(attribution, refs[1])))
            pairs = [agreements(repeats[first], repeats[second]) for first in range(len(repeats)) for second in range(first)]
            agreement_values.extend(value["top_k"] for value in pairs)
            rungs.append({"budget": budget, "phi": [value.tolist() for value in repeats], "pair_agreement": pairs,
                          "duration_seconds": durations, "local_residual": residuals})
        averaged = []
        average_durations = []
        for _ in range(4):
            attribution, _, duration, digest = explain(bounded_call, bundle["model"], explained, background, config["budgets"][0], stream, totals)
            stream += 1
            trace.append(digest)
            averaged.append(attribution)
            average_durations.append(duration)
        paired_gain = similarity(np.mean(averaged, axis=0), reference) - similarity(np.array(rungs[1]["phi"][0]), reference)
        metrics = {"repeat_agreement": float(np.mean(agreement_values)), "reference_fidelity": float(np.mean(fidelities)),
                   "local_accuracy_quality": float(np.mean(local_values)), "matched_budget_gain": paired_gain,
                   "reference_resolution_quality": similarity(refs[0], refs[1])}
        cells.append({"input_index": source["input_index"], "background_size": len(background),
                      "references": [value.tolist() for value in refs],
                      "reference_counts": source["reference_counts"], "exact_counts": source["exact_counts"],
                      "baseline_counts": source["deployment_counts"],
                      "exact": None if source["exact"] is None else source["exact"].tolist(),
                      "baseline": [value.tolist() for value in source["deployments"]],
                      "rungs": rungs, "matched_average": np.mean(averaged, axis=0).tolist(),
                      "matched_average_duration_seconds": average_durations, "metrics": metrics})
    values = {key: float(np.mean([cell["metrics"][key] for cell in cells])) for key in QUALITY}
    intervals = {}
    generator = np.random.default_rng(812)
    for key in QUALITY:
        per_input = [np.mean([cell["metrics"][key] for cell in cells if cell["input_index"] == index]) for index in range(config["inputs"])]
        samples = [float(np.mean(generator.choice(per_input, len(per_input)))) for _ in range(200)]
        intervals[key] = np.quantile(samples, [.025, .975]).tolist()
    return {"metrics": values, "valid": True, "scientific": 1.0, "slots": case_slots(config, episode["case"][0]),
            "trace": trace, "solution": {"case": list(episode["case"]), "cells": cells, "input_cluster_intervals": intervals,
                                        "validation_accuracy": bundle["validation_accuracy"], "oracle_counts": totals,
                                        "fit_cpu_seconds": bundle["fit_cpu_seconds"], "training_rows": bundle["training_rows"],
                                        "validation_rows": bundle["validation_rows"], "selection_rows": bundle["selection_rows"],
                                        "fitted_model_sha256": bundle["fitted_model_sha256"]}}


class AdditiveModel:
    def __init__(self, constant=False, permutation=None):
        self.constant = constant
        self.permutation = permutation

    def predict_proba(self, rows):
        rows = np.asarray(rows, dtype=float)
        if self.permutation is not None:
            rows = rows[:, np.argsort(self.permutation)]
        values = np.full(len(rows), .4) if self.constant else .15 + rows @ np.array([.03, .05, .07, .09, .11, .13])
        return np.column_stack((1 - values, values))


def controls(episode, call, deadline, config):
    background = np.array([[0., .2, .4, .1, .3, .5], [.1, .3, .2, .4, .2, .1], [.2, .1, .3, .2, .5, .4], [.3, .4, .1, .3, .1, .2]])
    inputs = [np.array([.9, .8, .7, .6, .5, .4]), np.array([.1, .3, .9, .2, .8, .7])]
    permutation = np.array([5, 1, 2, 3, 4, 0])
    if np.array_equal(permutation, np.arange(6)):
        raise ValueError("vacuous permutation")
    exact = [(explained - background.mean(axis=0)) * np.array([.03, .05, .07, .09, .11, .13]) for explained in inputs]
    if np.allclose(exact[0], exact[1]) or np.allclose(exact[0][permutation], exact[0]):
        raise ValueError("vacuous copy/permutation")
    stream = 0
    traces = {}
    counts = {"coalitions": 0, "masked_rows": 0}
    passed = {"constant": True, "copy": True, "permutation": True}
    for branch_index, branch in enumerate(("normal", "constant", "permutation")):
        branch_deadline = reserved_method_deadline(now=time.monotonic(), episode_deadline=deadline,
                                                   methods_remaining=2 - branch_index,
                                                   work_seconds=config["method_seconds"] / 3, cleanup_seconds=1)
        model = AdditiveModel(branch == "constant", permutation if branch == "permutation" else None)
        for index, explained in enumerate(inputs):
            active_input = explained[permutation] if branch == "permutation" else explained
            active_background = background[:, permutation] if branch == "permutation" else background
            reference = exact_reference(model, active_input, active_background, counts)
            expected = np.zeros(6) if branch == "constant" else (exact[index][permutation] if branch == "permutation" else exact[index])
            if not np.allclose(reference, expected, atol=1e-10):
                raise RequiredBaselineFailure("baseline_result_failure")
            for budget in config["budgets"]:
                for repeat in range(config["repeats"]):
                    def bounded_call(request):
                        return call(request, branch_deadline)
                    attribution, residual, _, _ = explain(bounded_call, model, active_input, active_background, budget, stream, counts)
                    stream += 1
                    traces[(branch, index, budget, repeat)] = attribution
                    if branch == "constant":
                        passed["constant"] &= bool(np.allclose(attribution, 0, atol=1e-7) and residual < 1e-6)
                    elif branch == "permutation":
                        passed["permutation"] &= bool(np.allclose(attribution[np.argsort(permutation)], exact[index], rtol=1e-5, atol=1e-6))
                    else:
                        passed["copy"] &= bool(np.allclose(attribution, exact[index], rtol=1e-5, atol=1e-6))
    copied = traces[("normal", 0, config["budgets"][0], 0)]
    passed["copy"] &= bool(np.array_equal(copied, copied.copy()) and not np.allclose(copied, exact[1], rtol=1e-5, atol=1e-6))
    return {"metrics": {}, "valid": all(passed.values()), "scientific": 0.0,
            "controls": {key: float(value) for key, value in passed.items()}, "slots": control_slots(config),
            "solution": {"controls": {key: bool(value) for key, value in passed.items()}, "exact": [value.tolist() for value in exact],
                         "copy_target_discrepancy": float(np.abs(copied - exact[1]).sum()), "oracle_counts": counts,
                         "probes": [{"branch": key[0], "input_index": key[1], "budget": key[2], "repeat": key[3], "phi": value.tolist()}
                                    for key, value in traces.items()]}}


def case_slots(config, dataset):
    return config["inputs"] * len(config["backgrounds"]) * (2 * config["repeats"] + 4 + 4 + int(dataset == "acs"))


def control_slots(config):
    return 3 * 2 * 2 * config["repeats"] + 6 + 3


def worst_case(episode):
    return {"metrics": {key: (-1.0 if key == "matched_budget_gain" else 0.0) for key in QUALITY},
            "valid": False, "scientific": 0.0, "slots": 0,
            "controls": {"constant": 0.0, "copy": 0.0, "permutation": 0.0}, "trace": [], "solution": {"failed": True}}


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes) - index - 1
        episode_deadline = min(candidate_deadline - remaining * reset_slot, clock() + episode["seconds"])
        work_deadline = episode_deadline - episode_overhead
        current_operation = "reset"
        primary_failure = None
        started = clock()
        def call(request, method_deadline=None):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(rpc_cap, work_deadline - clock())
                if method_deadline is not None:
                    timeout = min(timeout, method_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode work exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, ProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset exhausted")
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if not value["valid"]:
                record_failure({"component": "evaluator", "category": "control_failed", "operation": "controls"})
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, ProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            outcomes[index]["failure_category"] = failure["category"]
            record_failure(failure)
        outcomes[index]["duration_seconds"] = max(0, clock() - started)
    return outcomes, complete


def profile(smoke):
    return {"smoke": smoke, "inputs": 1 if smoke else (6 if PLANE == "search" else 12),
            "backgrounds": [4] if smoke else [8, 32], "budgets": [32, 128] if smoke else [64, 256],
            "repeats": 2 if smoke else (3 if PLANE == "search" else 6),
            "reference_budget": 128 if smoke else 2048,
            "method_seconds": 9 if smoke else (260 if PLANE == "search" else 1400)}


def episode_plan(smoke):
    cases = [CASES[0], ("controls", "controls")] if smoke else CASES + [("controls", "controls")]
    seeds = SEEDS[:1] if smoke else SEEDS
    episodes = [{"seed": seed, "case": case, "replay": False,
                 "seconds": 32 if smoke else (600 if PLANE == "search" else 3200)} for seed in seeds for case in cases]
    episodes.append({**episodes[0], "replay": True})
    return episodes


def compute_rpc_counts(episodes, config):
    rows = []
    for episode in episodes:
        if episode["case"][0] == "controls":
            runs = 3 * 2 * 2 * config["repeats"]
        else:
            runs = config["inputs"] * len(config["backgrounds"]) * (2 * config["repeats"] + 4)
        rows.append({"reset": 1, "start": runs, "observe": runs})
    return rows


def preflight():
    maximum_request = {"op": "start", "features": 20, "budget": 256, "stream": 2**63 - 1,
                       "input": ["Ａ" * 256] * 20, "background": [[-1.7976931348623157e308] * 20] * 32,
                       "output": "positive_probability", "value_function": "interventional_grouped"}
    maximum_masks = {"masks": [[1] * 20 for _ in range(256)]}
    maximum_values = {"op": "observe", "values": [1.7976931348623157e308] * 256}
    maximum_result = {"phi": [-1.7976931348623157e308] * 20}
    for value in (maximum_request, maximum_masks, maximum_values, maximum_result):
        validate_wire(value)
    for plane, seeds, inputs, repeats, cap in [("search", [1103], 6, 3, 1760), ("final", [7301, 9109], 12, 6, 10287)]:
        case_calls = 1 + 2 * inputs * 2 * (2 * repeats + 4)
        controls_calls = 1 + 2 * 3 * 2 * 2 * repeats
        total = len(seeds) * (6 * case_calls + controls_calls) + case_calls
        if total != cap:
            raise ValueError("RPC table mismatch")
    profiles = {"search": {"episode_count": 8, "method_count": 2, "wall_seconds": 5400, "startup_seconds": 120,
                            "reset_seconds": 8, "cleanup_seconds": 2, "finish_seconds": 30, "work_seconds": 260},
                "final": {"episode_count": 15, "method_count": 2, "wall_seconds": 50400, "startup_seconds": 120,
                           "reset_seconds": 8, "cleanup_seconds": 2, "finish_seconds": 30, "work_seconds": 1400}}
    require_joint_workload_budget(**profiles)


def aggregate(episodes, outcomes, config):
    real = [value for episode, value in zip(episodes, outcomes) if episode["case"][0] != "controls" and not episode["replay"]]
    suites = [value for episode, value in zip(episodes, outcomes) if episode["case"][0] == "controls"]
    original, replay = outcomes[0], outcomes[-1]
    replay_ok = bool(original["scientific"] and replay["scientific"] and original["trace"] == replay["trace"])
    category_values = [float(np.mean([value.get("controls", {}).get(category, 0) for value in suites]))
                       for category in ("constant", "copy", "permutation")]
    category_values.append(float(replay_ok))
    control_fraction = float(np.mean(category_values))
    scientific = float(np.mean([value["scientific"] for value in real]))
    denominator = sum(control_slots(config) if episode["case"][0] == "controls" else case_slots(config, episode["case"][0])
                      for episode in episodes)
    metrics = {"combined_score": .5 * scientific + .5 * control_fraction,
               "coverage": sum(value["slots"] for value in outcomes) / denominator,
               "control_pass_fraction": control_fraction}
    metrics.update({key: float(np.mean([value["metrics"][key] for value in real])) for key in QUALITY})
    integrity = not any(value.get("failure_category") in ("invalid_reset_response", "malformed_response") for value in outcomes)
    baseline_ok = not any(value.get("failure_category", "").startswith("baseline_") for value in outcomes)
    correct = bool(integrity and baseline_ok and all(value["valid"] for value in suites) and replay_ok)
    if PLANE == "final":
        correct &= all(value["valid"] for value in real)
    metrics["correct"] = int(correct)
    if set(metrics) != set(METRICS) or not all(math.isfinite(value) for value in metrics.values()):
        raise ValueError("metric contract failure")
    return metrics, correct


def write_outputs(directory, metrics, correct, feasible, episodes=None, outcomes=None):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "metrics.json").write_bytes(bounded_json_line(metrics))
    (directory / "correct.json").write_bytes(bounded_json_line({"correct": bool(correct)}))
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        (directory / "qualification.json").write_bytes(bounded_json_line({"schema_version": 1, "feasible": bool(feasible)}))
    if episodes is not None:
        records = []
        for seed in SEEDS:
            selected = [(episode, value) for episode, value in zip(episodes, outcomes) if episode["seed"] == seed]
            if not selected:
                continue
            seed_real = [value["scientific"] for episode, value in selected if episode["case"][0] != "controls" and not episode["replay"]]
            seed_controls = [value for episode, value in selected if episode["case"][0] == "controls"]
            replay_passed = bool(outcomes[0]["scientific"] and outcomes[-1]["scientific"] and outcomes[0]["trace"] == outcomes[-1]["trace"])
            seed_control_score = (sum(float(np.mean([value.get("controls", {}).get(key, 0) for value in seed_controls]))
                                      for key in ("constant", "copy", "permutation")) + int(replay_passed)) / 4
            records.append({"seed": seed, "score": .5 * float(np.mean(seed_real)) + .5 * seed_control_score,
                            "correct": bool(all(value["valid"] for _, value in selected) and replay_passed),
                            "duration_seconds": sum(value["duration_seconds"] for _, value in selected),
                            "solution": {f"case_{index}": {"case": list(episode["case"]), "replay": episode["replay"],
                                                          "completed": bool(value["valid"]), **value["solution"]}
                                         for index, (episode, value) in enumerate(selected)}})
        encoded = bounded_json_line({"schema_version": 1, "episodes": records}, 16 * 1024**2)
        (directory / "evaluation_evidence.json").write_bytes(encoded)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    arguments = parser.parse_args()
    directory = pathlib.Path(arguments.results_dir)
    candidate = None
    try:
        preflight()
        smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
        config = profile(smoke)
        root = pathlib.Path(os.environ.get("TASK_SOURCE_DIR", pathlib.Path(__file__).resolve().parent)) / "resources" / PLANE
        load_data(root)
        config["root"] = str(root)
        episodes = episode_plan(smoke)
        counts = compute_rpc_counts(episode_plan(False), profile(False))
        if sum(sum(row.values()) for row in counts) != RPC_BUDGET:
            raise ValueError("production RPC budget mismatch")
        hard_deadline = STARTED + (112 if smoke else WALL - 120)
        candidate = Candidate(arguments.program_path)
        def evaluate(episode, call, deadline):
            if episode["case"][0] == "controls":
                return controls(episode, call, deadline, config)
            return scientific_case(episode, call, deadline, config)
        outcomes, complete = run_declared_episodes(episodes, hard_deadline=hard_deadline, finish_reserve=5 if smoke else 30,
                                                  reset_timeout=4 if smoke else 8, episode_overhead=3,
                                                  rpc_cap=8 if smoke else 30, clock=time.monotonic, rpc=candidate.call,
                                                  evaluate=evaluate, worst_case=worst_case, record_failure=record_failure)
        candidate.close()
        metrics, correct = aggregate(episodes, outcomes, config)
        feasible = complete and not smoke and all(value["valid"] for value in outcomes) and time.monotonic() < hard_deadline
        write_outputs(directory, metrics, correct, feasible, episodes, outcomes)
    except Exception as error:
        metrics = {key: (-1.0 if key == "matched_budget_gain" else 0.0) for key in METRICS}
        write_outputs(directory, metrics, False, False)
        if PLANE == "search":
            name = type(error).__name__[:80]
            print(f"evaluator_exception type={name} message=bounded_evaluator_failure", file=sys.stderr)
        else:
            print("evaluator_exception type=EvaluationFailure message=sealed_evaluator_failure", file=sys.stderr)
        raise SystemExit(1) from None
    finally:
        if candidate is not None:
            candidate.close()


if __name__ == "__main__":
    if "--baseline-worker" in sys.argv:
        try:
            resource.setrlimit(resource.RLIMIT_AS, (4 * 1024**3, 4 * 1024**3))
            resource.setrlimit(resource.RLIMIT_CPU, (math.ceil(WALL), math.ceil(WALL) + 1))
            config = json.loads(sys.stdin.buffer.readline(WIRE))
            bundle = prepare_case(config)
            encoded = base64.b64encode(pickle.dumps(bundle, protocol=5)).decode("ascii")
            sys.stdout.buffer.write(bounded_json_line({"bundle": encoded}))
            sys.stdout.buffer.flush()
        except Exception as error:
            if repair_mode():
                report_worker_exception(error)
            else:
                print("baseline_worker_failure", file=sys.stderr, flush=True)
            raise SystemExit(1) from None
    else:
        main()
