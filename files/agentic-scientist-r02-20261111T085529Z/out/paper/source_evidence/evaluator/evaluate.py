#!/usr/bin/env python3
"""Conformal prediction-set reliability evaluator for compositional (softmax) outputs.

Plane: search (self-contained; reads only its own resource root).

The evaluator owns all data (in-memory NumPy synthetic generator), all labels, all
baselines, all controls and all scoring.  The candidate only sees calibration
probabilities + labels and unlabeled test probabilities through ``handle(request)``.
"""
import argparse
import base64
import collections
import hashlib
import importlib.util
import json
import math
import os
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

os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

import numpy as np  # noqa: E402

# ----------------------------------------------------------------------------
# Plane configuration (the only part that differs between the two evaluators)
# ----------------------------------------------------------------------------
PLANE = "search"
PLANE_WALL = 900.0
RESOURCE_ROOT = "resources/search"
SEEDS = [101, 102, 103]
CONTROL_PLAN = [("C1", "S1", 101), ("C2", "S1", 101), ("C3", "S1", 101)]
RESET_SEQUENCE = [s for _ in range(4) for s in SEEDS] + [c[2] for c in CONTROL_PLAN]
MAX_RPC = 105  # 15 episodes x (1 reset + 2 calibrate + 4 predict) declared maximum
METRIC_NAMES = ['combined_score', 'mean_marginal_coverage_gap_exchangeable', 'worst_slice_coverage_gap', 'mean_set_size_ratio', 'shift_coverage_gap', 'controls_passed_fraction', 'n_failed_episodes']

WIRE_LIMIT = 64 * 1024 * 1024
CHUNK_ROWS = 1000
MAX_CAL_CHUNKS = 2
MAX_TEST_CHUNKS = 4
OPS_PER_EPISODE = 1 + MAX_CAL_CHUNKS + MAX_TEST_CHUNKS  # reset + calibrate + predict
BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
MIN_SLICE_COUNT = 30
COVERAGE_Z = 3.0
NEAR_FULL_RATIO = 0.9
SMOKE_N_CAL = 100
SMOKE_N_TEST = 200
RAPS_LAMBDA = 0.01
BOOTSTRAP_B = 2000
BASELINE_NAMES = ("lac", "aps", "raps", "classwise", "uncalibrated_topmass", "full_set", "argmax_only")
SCORED_BASELINES = ("lac", "aps", "raps", "classwise")
CONTROL_NAMES = ("C1", "C2", "C3")

PROFILES = {
    "production": dict(wall=PLANE_WALL, startup=30.0, finish=15.0, reset=20.0, overhead=6.0,
                       rpc_cap=20.0, work=20.0, cleanup=6.0),
    "smoke": dict(wall=120.0, startup=10.0, finish=5.0, reset=10.0, overhead=4.0,
                  rpc_cap=10.0, work=10.0, cleanup=4.0),
}


# ----------------------------------------------------------------------------
# Failure identity helpers
# ----------------------------------------------------------------------------
class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


class CandidateFailure(RuntimeError):
    """Expected candidate-side protocol failure with a fixed category."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "candidate_failure")
        super().__init__("candidate failure")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, CandidateFailure):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
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


# ----------------------------------------------------------------------------
# Bounded worker stderr capture (used for the native smoke candidate subprocess)
# ----------------------------------------------------------------------------
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
        self.reader = threading.Thread(target=self._drain, name="worker-stderr-reader", daemon=True)
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
        self.result = {
            "stderr": "".join(self.lines),
            "observed_bytes": self.observed_bytes,
            "retained_bytes": self.retained_bytes,
            "truncated": self.truncated,
            "capture_error": self.capture_error,
        }
        return dict(self.result)


# ----------------------------------------------------------------------------
# Budget helpers
# ----------------------------------------------------------------------------
def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError("work allowance must be positive")
    return value


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def require_joint_workload_budget(*, episode_count, method_count, wall_seconds, startup_seconds,
                                  reset_seconds, cleanup_seconds, finish_seconds, work_seconds):
    if any(type(c) is not int or c <= 0 for c in (episode_count, method_count)):
        raise ValueError("invalid episode or method count")
    for v in (wall_seconds, startup_seconds, reset_seconds, cleanup_seconds, finish_seconds):
        finite_budget_seconds(v)
    work = positive_work_seconds(work_seconds)
    needed = (startup_seconds + finish_seconds
              + episode_count * (reset_seconds + method_count * (work + cleanup_seconds)))
    if needed > wall_seconds:
        raise ValueError("productive work exceeds the declared wall budget")
    return needed


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


def _reject_constant(name):
    raise ValueError("non-finite JSON constant")


def _no_duplicate_pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError("duplicate JSON key")
        out[key] = value
    return out


def strict_json_loads(text):
    return json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_no_duplicate_pairs)


# ----------------------------------------------------------------------------
# Candidate transports
# ----------------------------------------------------------------------------
NATIVE_RUNNER = r'''
import importlib.util, json, os, sys
out = os.fdopen(os.dup(1), "w", buffering=1, encoding="utf-8")
os.dup2(2, 1)
sys.stdout = sys.stderr
path = os.path.abspath(sys.argv[1])
repair = sys.argv[2] == "1"
sys.path.insert(0, os.path.dirname(path))
spec = importlib.util.spec_from_file_location("candidate_program", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
handle = mod.handle
for line in sys.stdin:
    try:
        resp = handle(json.loads(line))
        data = json.dumps(resp, allow_nan=False, separators=(",", ":"))
    except BaseException as error:
        if repair:
            msg = str(error)
            if len(msg) > 2048:
                msg = "<message omitted>"
            sys.stderr.write("worker_exception type=%s\n%s\n" % (type(error).__name__, msg))
        else:
            sys.stderr.write("worker_exception\n")
        sys.stderr.flush()
        data = json.dumps({"__runner_error__": 1})
    out.write(data + "\n")
    out.flush()
'''


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1")
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "4"
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke runs)."""

    def __init__(self, program_path, wall_seconds, repair_mode):
        self.program_path = os.path.abspath(program_path)
        self.cpu_seconds = cpu_limit_seconds(wall_seconds, 4)
        self.repair_mode = repair_mode
        self.proc = None
        self.capture = None
        self.snapshot = None
        self.rbuf = bytearray()
        self.cwd = tempfile.mkdtemp(prefix="cand_cwd_", dir="/tmp")

    def _limits(self):
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_seconds, self.cpu_seconds + 5))
        resource.setrlimit(resource.RLIMIT_AS, (8 << 30, 8 << 30))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    def start(self):
        self.stop()
        python, env = candidate_subprocess_settings(os.environ)
        self.proc = subprocess.Popen(
            [python, "-c", NATIVE_RUNNER, self.program_path, "1" if self.repair_mode else "0"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
            cwd=self.cwd, shell=False, start_new_session=True, preexec_fn=self._limits, close_fds=True)
        self.capture = BoundedWorkerStderr(self.proc.stderr)
        self.snapshot = None
        self.rbuf = bytearray()
        os.set_blocking(self.proc.stdin.fileno(), False)
        os.set_blocking(self.proc.stdout.fileno(), False)

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return self.snapshot
        try:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                pass
        finally:
            try:
                self.snapshot = self.capture.close()
            except RuntimeError:
                self.snapshot = {"stderr": "", "observed_bytes": 0, "retained_bytes": 0,
                                 "truncated": True, "capture_error": "cleanup_unresolved"}
        return self.snapshot

    def cleanup(self):
        self.stop()
        shutil.rmtree(self.cwd, ignore_errors=True)

    def call(self, request, timeout):
        if self.proc is None:
            raise CandidateFailure("transport_closed")
        deadline = time.monotonic() + timeout
        data = bounded_json_line(request)
        fd_in = self.proc.stdin.fileno()
        fd_out = self.proc.stdout.fileno()
        view = memoryview(data)
        try:
            with selectors.DefaultSelector() as sel:
                sel.register(fd_in, selectors.EVENT_WRITE)
                while len(view):
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        self.stop()
                        raise TimeoutError("candidate request timeout")
                    if not sel.select(timeout=min(remaining, .5)):
                        continue
                    try:
                        sent = os.write(fd_in, view[:65536])
                    except BlockingIOError:
                        continue
                    view = view[sent:]
            with selectors.DefaultSelector() as sel:
                sel.register(fd_out, selectors.EVENT_READ)
                while b"\n" not in self.rbuf:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        self.stop()
                        raise TimeoutError("candidate response timeout")
                    if not sel.select(timeout=min(remaining, .5)):
                        if self.proc.poll() is not None and not sel.select(timeout=0):
                            self.stop()
                            raise CandidateFailure("transport_closed")
                        continue
                    try:
                        chunk = os.read(fd_out, 1 << 20)
                    except BlockingIOError:
                        continue
                    if not chunk:
                        self.stop()
                        raise CandidateFailure("transport_closed")
                    self.rbuf.extend(chunk)
                    if len(self.rbuf) >= WIRE_LIMIT:
                        self.stop()
                        raise CandidateFailure("oversized_response")
        except TimeoutError:
            raise
        except (BrokenPipeError, OSError):
            self.stop()
            raise CandidateFailure("transport_closed") from None
        line, _, rest = bytes(self.rbuf).partition(b"\n")
        self.rbuf = bytearray(rest)
        try:
            response = strict_json_loads(line.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise CandidateFailure("malformed_response") from None
        if type(response) is dict and "__runner_error__" in response:
            raise CandidateFailure("candidate_exception")
        return response


class ProxyCandidate:
    """Harness broker proxy, loaded in-process (never re-isolated)."""

    def __init__(self, path):
        spec = importlib.util.spec_from_file_location("candidate_proxy", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.pending = None

    def call(self, request, timeout):
        deadline = time.monotonic() + timeout
        if self.pending is not None:
            self.pending.join(timeout=max(0.0, deadline - time.monotonic()))
            if self.pending.is_alive():
                raise TimeoutError("candidate still busy")
            self.pending = None
        payload = strict_json_loads(bounded_json_line(request).decode("utf-8"))
        box = {}

        def work():
            try:
                box["response"] = self.handle(payload)
            except BaseException:
                box["error"] = True

        thread = threading.Thread(target=work, name="candidate-call", daemon=True)
        thread.start()
        thread.join(timeout=max(0.0, deadline - time.monotonic()))
        if thread.is_alive():
            self.pending = thread
            raise TimeoutError("candidate response timeout")
        if "error" in box:
            raise CandidateFailure("candidate_exception")
        try:
            text = json.dumps(box["response"], allow_nan=False, separators=(",", ":"))
        except (TypeError, ValueError):
            raise CandidateFailure("malformed_response") from None
        if len(text.encode("utf-8")) >= WIRE_LIMIT:
            raise CandidateFailure("oversized_response")
        return strict_json_loads(text)

    def stop(self):
        return None

    def cleanup(self):
        return None


# ----------------------------------------------------------------------------
# Manifest, data generation, content hashes
# ----------------------------------------------------------------------------
def source_dir():
    return os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))


CASE_KEYS = {"id", "family", "exchangeable", "K", "alpha", "n_cal", "n_test", "signal", "temperature",
             "hetero_sigma", "prior_beta", "cal_prior", "test_prior", "test_signal_scale"}


def validate_manifest(manifest):
    if type(manifest) is not dict or manifest.get("schema_version") != 1 or manifest.get("plane") != PLANE:
        raise ValueError("invalid manifest header")
    cases = manifest.get("cases")
    if type(cases) is not list or not cases:
        raise ValueError("invalid manifest cases")
    seen = set()
    for case in cases:
        if type(case) is not dict or set(case) != CASE_KEYS:
            raise ValueError("invalid case keys")
        if not re.fullmatch(r"[A-Z][A-Z0-9]{0,7}", case["id"]) or case["id"] in seen:
            raise ValueError("invalid case id")
        seen.add(case["id"])
        K, nc, nt, a = case["K"], case["n_cal"], case["n_test"], case["alpha"]
        if not (type(K) is int and 2 <= K <= 100 and type(nc) is int and 1 <= nc <= MAX_CAL_CHUNKS * CHUNK_ROWS
                and type(nt) is int and 1 <= nt <= MAX_TEST_CHUNKS * CHUNK_ROWS
                and type(a) is float and 0.0 < a < 1.0 and type(case["exchangeable"]) is bool):
            raise ValueError("invalid case workload")
        for spec in (case["cal_prior"], case["test_prior"]):
            if spec.get("kind") not in ("balanced", "longtail"):
                raise ValueError("invalid prior")
    return manifest


def make_prior(spec, K):
    if spec["kind"] == "balanced":
        return np.full(K, 1.0 / K)
    w = float(spec["ratio"]) ** (-np.arange(K) / (K - 1.0))
    if spec.get("reverse"):
        w = w[::-1]
    return w / w.sum()


def case_hash32(case_id):
    return int.from_bytes(hashlib.sha256(case_id.encode("utf-8")).digest()[:4], "little")


def stream_rngs(seed, case_id, tag):
    ss = np.random.SeedSequence([int(seed), case_hash32(case_id), tag])
    return [np.random.default_rng(s) for s in ss.spawn(3)]


def softmax_rows(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def gen_split(rng, n, K, prior_true, prior_model, signal, hetero_sigma, beta, temperature):
    y = rng.choice(K, size=n, p=prior_true)
    if hetero_sigma > 0:
        d = np.exp(hetero_sigma * rng.standard_normal(n) - 0.5 * hetero_sigma ** 2)
    else:
        d = np.ones(n)
    z = rng.standard_normal((n, K))
    z[np.arange(n), y] += signal * d
    z += beta * np.log(prior_model)[None, :]
    p = softmax_rows(z / temperature)
    return p.astype(np.float32), y.astype(np.int16)


def gen_dataset(case, seed, smoke):
    K = case["K"]
    n_cal = SMOKE_N_CAL if smoke else case["n_cal"]
    n_test = SMOKE_N_TEST if smoke else case["n_test"]
    rng_cal, rng_test, _ = stream_rngs(seed, case["id"], 0xDA7A)
    pi_cal = make_prior(case["cal_prior"], K)
    pi_test = make_prior(case["test_prior"], K)
    pc, yc = gen_split(rng_cal, n_cal, K, pi_cal, pi_cal, case["signal"], case["hetero_sigma"],
                       case["prior_beta"], case["temperature"])
    pt, yt = gen_split(rng_test, n_test, K, pi_test, pi_cal, case["signal"] * case["test_signal_scale"],
                       case["hetero_sigma"], case["prior_beta"], case["temperature"])
    return {"pc": pc, "yc": yc, "pt": pt, "yt": yt, "K": K, "alpha": case["alpha"],
            "n_cal": n_cal, "n_test": n_test, "pi_cal": pi_cal}


def example_hashes(p32, y):
    q = np.ascontiguousarray(p32, dtype="<f4")
    yb = y.astype("<i2")
    return [hashlib.sha256(q[i].tobytes() + yb[i].tobytes()).digest()[:16] for i in range(len(y))]


def dataset_hashes(ds):
    return example_hashes(ds["pc"], ds["yc"]) + example_hashes(ds["pt"], ds["yt"])


def load_search_hashes(root):
    path = os.path.join(root, "search_example_hashes.json")
    with open(path, "r", encoding="utf-8") as handle:
        doc = strict_json_loads(handle.read())
    if (type(doc) is not dict or doc.get("schema_version") != 1 or doc.get("hash_bytes") != 16
            or type(doc.get("hex")) is not str or len(doc["hex"]) != 32 * doc.get("count", -1)):
        raise ValueError("invalid search hash list")
    raw = bytes.fromhex(doc["hex"])
    return {raw[i:i + 16] for i in range(0, len(raw), 16)}


# ----------------------------------------------------------------------------
# Conformal baselines (evaluator-owned; operate on the float32 wire values)
# ----------------------------------------------------------------------------
def conformal_quantile(scores, alpha):
    n = len(scores)
    k = math.ceil((n + 1) * (1.0 - alpha) - 1e-9)
    if n == 0 or k > n:
        return math.inf
    return float(np.sort(scores)[max(k, 1) - 1])


def sorted_desc(p):
    order = np.argsort(-p, axis=1, kind="stable")
    return order, np.take_along_axis(p, order, 1)


def unsort(values_sorted, order):
    out = np.empty_like(values_sorted)
    np.put_along_axis(out, order, values_sorted, 1)
    return out


def aps_like_scores(p, u, reg):
    order, ps = sorted_desc(p)
    cum_before = np.cumsum(ps, axis=1) - ps
    e_sorted = cum_before + u[:, None] * ps
    if reg is not None:
        e_sorted = e_sorted + reg[None, :]
    return unsort(e_sorted, order)


def baseline_sets(ds, rng):
    pc, yc, pt = ds["pc"].astype(np.float64), ds["yc"].astype(np.int64), ds["pt"].astype(np.float64)
    K, alpha = ds["K"], ds["alpha"]
    nc, nt = len(yc), len(pt)
    out = {}
    q = conformal_quantile(1.0 - pc[np.arange(nc), yc], alpha)
    out["lac"] = (1.0 - pt) <= q
    u_cal, u_test = rng.random(nc), rng.random(nt)
    e_cal = aps_like_scores(pc, u_cal, None)
    out["aps"] = aps_like_scores(pt, u_test, None) <= conformal_quantile(e_cal[np.arange(nc), yc], alpha)
    k_reg = min(5, max(1, K // 5))
    reg = RAPS_LAMBDA * np.maximum(0, np.arange(1, K + 1) - k_reg)
    r_cal = aps_like_scores(pc, u_cal, reg)
    out["raps"] = aps_like_scores(pt, u_test, reg) <= conformal_quantile(r_cal[np.arange(nc), yc], alpha)
    qc = np.full(K, math.inf)
    for c in range(K):
        sc = 1.0 - pc[yc == c, c]
        if len(sc):
            qc[c] = conformal_quantile(sc, alpha)
    out["classwise"] = (1.0 - pt) <= qc[None, :]
    order, ps = sorted_desc(pt)
    cum_before = np.cumsum(ps, axis=1) - ps
    out["uncalibrated_topmass"] = unsort(cum_before < (1.0 - alpha) - 1e-12, order)
    out["full_set"] = np.ones((nt, K), dtype=bool)
    am = np.zeros((nt, K), dtype=bool)
    am[np.arange(nt), np.argmax(pt, axis=1)] = True
    out["argmax_only"] = am
    return out


# ----------------------------------------------------------------------------
# Scoring
# ----------------------------------------------------------------------------
def clip01(x):
    return float(min(1.0, max(0.0, x)))


def score_sets(mask, y, probs, K, alpha):
    n = len(y)
    y = y.astype(np.int64)
    covered = mask[np.arange(n), y]
    cov = float(covered.mean())
    size = mask.sum(axis=1)
    size_ratio = float(size.mean() / K)
    marg_gap = max(0.0, (1.0 - alpha) - cov)
    gaps = []
    if K <= 10:
        for c in range(K):
            sel = y == c
            if sel.sum() >= MIN_SLICE_COUNT:
                gaps.append(max(0.0, (1.0 - alpha) - float(covered[sel].mean())))
    else:
        size_bin = np.digitize(size, [2, 4, 11, 31])
        pm = np.asarray(probs, dtype=np.float64).max(axis=1)
        diff_bin = np.searchsorted(np.quantile(pm, [.25, .5, .75]), pm, side="right")
        for bins in (size_bin, diff_bin):
            for b in np.unique(bins):
                sel = bins == b
                if sel.sum() >= MIN_SLICE_COUNT:
                    gaps.append(max(0.0, (1.0 - alpha) - float(covered[sel].mean())))
    slice_gap = max(gaps) if gaps else marg_gap
    loss = (0.5 * clip01(marg_gap / alpha) + 0.25 * clip01(slice_gap) + 0.25 * clip01(size_ratio))
    return {"cov": cov, "size_ratio": size_ratio, "marg_gap": clip01(marg_gap),
            "slice_gap": clip01(slice_gap), "loss": clip01(loss)}


def coverage_tolerance(alpha, n_cal, n_test, n_seeds):
    var = alpha * (1.0 - alpha) * (1.0 / (n_cal + 2.0) + 1.0 / n_test) / max(1, n_seeds)
    return COVERAGE_Z * math.sqrt(var)


def worst_outcome(episode):
    return {"ok": False, "kind": episode["kind"], "case": episode["case"], "seed": episode["seed"],
            "cov": 0.0, "size_ratio": 1.0, "marg_gap": 1.0, "slice_gap": 1.0, "loss": 1.0,
            "cov_shuffled": 0.0, "chance": 1.0, "change_frac": 0.0, "vacuous": False,
            "tol": 0.0, "n_test": 1, "K": 1, "target": 1.0, "mean_size": 0.0}


# ----------------------------------------------------------------------------
# Wire encoding
# ----------------------------------------------------------------------------
def encode_array(arr, dtype):
    arr = np.ascontiguousarray(arr, dtype=np.dtype(dtype).newbyteorder("<"))
    return {"dtype": np.dtype(dtype).name, "shape": list(arr.shape), "encoding": "base64_le",
            "data": base64.b64encode(arr.tobytes()).decode("ascii")}


def decode_mask(obj, rows, K):
    if (type(obj) is not dict or set(obj) != {"dtype", "shape", "encoding", "data"}
            or obj["dtype"] != "uint8" or obj["encoding"] != "packbits_base64"
            or obj["shape"] != [rows, K] or type(obj["data"]) is not str):
        raise CandidateFailure("malformed_response")
    try:
        raw = base64.b64decode(obj["data"].encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError):
        raise CandidateFailure("malformed_response") from None
    nbytes = (K + 7) // 8
    if len(raw) != rows * nbytes:
        raise CandidateFailure("malformed_response")
    bits = np.unpackbits(np.frombuffer(raw, dtype=np.uint8).reshape(rows, nbytes), axis=1)
    if bits[:, K:].any():
        raise CandidateFailure("malformed_response")
    return bits[:, :K].astype(bool)


def chunk_bounds(n):
    num = max(1, math.ceil(n / CHUNK_ROWS))
    return [(i * CHUNK_ROWS, min(n, (i + 1) * CHUNK_ROWS)) for i in range(num)]


# ----------------------------------------------------------------------------
# Episode execution
# ----------------------------------------------------------------------------
class Context:
    def __init__(self, cases, smoke):
        self.cases = {c["id"]: c for c in cases}
        self.smoke = smoke
        self.datasets = {}
        self.baseline_losses = {}

    def dataset(self, case_id, seed):
        key = (case_id, seed)
        if key not in self.datasets:
            self.datasets[key] = gen_dataset(self.cases[case_id], seed, self.smoke)
        return self.datasets[key]


def run_candidate_protocol(call, pc, yc, pt, K, alpha):
    n_cal, n_test = len(yc), len(pt)
    cal_chunks = chunk_bounds(n_cal)
    for i, (a, b) in enumerate(cal_chunks):
        response = call({"op": "calibrate", "chunk_index": i, "num_chunks": len(cal_chunks), "rows": b - a,
                         "K": K, "alpha": alpha, "n_cal": n_cal, "n_test": n_test,
                         "probs": encode_array(pc[a:b], "float32"), "labels": encode_array(yc[a:b], "int16")})
        try:
            require_reset_ack(response)
        except InvalidResetResponse:
            raise CandidateFailure("malformed_response") from None
    test_chunks = chunk_bounds(n_test)
    masks = []
    for i, (a, b) in enumerate(test_chunks):
        response = call({"op": "predict", "chunk_index": i, "num_chunks": len(test_chunks), "rows": b - a,
                         "K": K, "alpha": alpha, "n_cal": n_cal, "n_test": n_test,
                         "probs": encode_array(pt[a:b], "float32")})
        if type(response) is not dict or set(response) != {"sets"}:
            raise CandidateFailure("malformed_response")
        masks.append(decode_mask(response["sets"], b - a, K))
    return np.concatenate(masks, axis=0)


def evaluate_episode(episode, call, work_deadline, ctx):
    ds = ctx.dataset(episode["case"], episode["seed"])
    K, alpha = ds["K"], ds["alpha"]
    pc, yc, pt, yt = ds["pc"], ds["yc"], ds["pt"], ds["yt"]
    kind, seed, case_id = episode["kind"], episode["seed"], episode["case"]
    out = worst_outcome(episode)
    out.update(ok=True, vacuous=False, change_frac=0.0, cov_shuffled=0.0, chance=1.0)
    out.update(tol=coverage_tolerance(alpha, ds["n_cal"], ds["n_test"], 1), n_test=ds["n_test"], K=K,
               target=1.0 - alpha)
    if kind == "case":
        try:
            rng = stream_rngs(seed, case_id, 0xBA5E)[0]
            sets_b = baseline_sets(ds, rng)
            losses = {name: score_sets(mask, yt, pt, K, alpha)["loss"] for name, mask in sets_b.items()}
        except Exception:
            fail_required_baseline("baseline_result_failure", lambda: None, lambda category: None)
        if time.monotonic() > work_deadline:
            fail_required_baseline("baseline_timeout", lambda: None, lambda category: None)
        ctx.baseline_losses[(case_id, seed)] = losses
    cal_labels, cal_probs, test_probs, score_labels = yc, pc, pt, yt
    if kind == "C1":
        perm = stream_rngs(seed, case_id, 0xC1)[0].permutation(len(yc))
        cal_labels = yc[perm]
        out["change_frac"] = float(np.mean(cal_labels != yc))
        out["vacuous"] = bool(out["change_frac"] < 0.5 or np.array_equal(perm, np.arange(len(yc))))
    elif kind == "C2":
        perm = stream_rngs(seed, case_id, 0xC2)[0].permutation(len(yt))
        out["change_frac"] = float(np.mean(yt[perm] != yt))
        out["vacuous"] = bool(out["change_frac"] < 0.5 or np.array_equal(perm, np.arange(len(yt))))
    elif kind == "C3":
        uniform = np.full((1, K), 1.0 / K, dtype=np.float32)
        cal_probs = np.repeat(uniform, len(yc), axis=0)
        test_probs = np.repeat(uniform, len(pt), axis=0)
        score_labels = stream_rngs(seed, case_id, 0xC3)[0].choice(K, size=len(yt), p=ds["pi_cal"]).astype(np.int16)
    mask = run_candidate_protocol(call, cal_probs, cal_labels, test_probs, K, alpha)
    if time.monotonic() > work_deadline:
        raise TimeoutError("scoring deadline exceeded")
    scored = score_sets(mask, score_labels, test_probs, K, alpha)
    out.update(scored)
    out["mean_size"] = scored["size_ratio"] * K
    if kind == "C2":
        pi_hat = np.bincount(yt.astype(np.int64), minlength=K) / float(len(yt))
        out["chance"] = float((mask * pi_hat[None, :]).sum(axis=1).mean())
        out["cov_shuffled"] = float(mask[np.arange(len(yt)), yt[perm].astype(np.int64)].mean())
    return out


def control_verdicts(plan, outcomes):
    """Evaluator-owned expected behaviour, fixed before scoring (see contract)."""
    verdicts = {}
    for idx, ep in enumerate(plan):
        if ep["kind"] not in CONTROL_NAMES:
            continue
        o = outcomes[idx]
        m = next((outcomes[j] for j, e in enumerate(plan)
                  if e["kind"] == "case" and e["case"] == ep["case"] and e["seed"] == ep["seed"]), None)
        if not o["ok"] or m is None or not m["ok"]:
            verdicts[idx] = (False, "episode_incomplete")
            continue
        if o["vacuous"]:
            verdicts[idx] = (False, "vacuous_control")
            continue
        if ep["kind"] == "C1":
            passed = o["size_ratio"] >= 1.5 * m["size_ratio"] or o["size_ratio"] >= NEAR_FULL_RATIO
            verdicts[idx] = (bool(passed), "ok" if passed else "c1_sets_not_inflated")
        elif ep["kind"] == "C2":
            n_test = o["n_test"]
            tol = COVERAGE_Z * 0.5 / math.sqrt(n_test)
            passed = (o["cov_shuffled"] <= o["chance"] + tol
                      and (o["cov_shuffled"] <= m["cov"] - 0.1 or o["size_ratio"] >= NEAR_FULL_RATIO))
            verdicts[idx] = (bool(passed), "ok" if passed else "c2_shuffled_coverage_high")
        else:
            passed = o["cov"] >= o["target"] - o["tol"] and o["mean_size"] >= o["target"] * o["K"] - 1.0
            verdicts[idx] = (bool(passed), "ok" if passed else "c3_uniform_behaviour")
    return verdicts


# ----------------------------------------------------------------------------
# Scheduler (single deadline, global reset reservation)
# ----------------------------------------------------------------------------
def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead, work_cap,
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    durations = [0.0] * len(episodes)
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        started = clock()
        work_deadline = min(episode_deadline - episode_overhead, started + reset_timeout + work_cap)

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
            except (TimeoutError, RequiredBaselineFailure, CandidateFailure) as error:
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
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateFailure) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure, episode)
            except Exception:
                error.add_note("episode diagnostic recording failed")
        finally:
            durations[index] = max(0.0, clock() - started)
    return outcomes, durations, complete


# ----------------------------------------------------------------------------
# Aggregation: episode -> mean over seeds within case -> equal-weight mean over cases
# ----------------------------------------------------------------------------
def fixed_weight_mean(values):
    if not values or not all(math.isfinite(v) for v in values):
        raise ValueError("invalid contribution")
    weights = [1.0 / len(values)] * len(values)
    return sum(v * w for v, w in zip(values, weights))


def per_case_values(plan, outcomes, field):
    by_case = collections.OrderedDict()
    for ep, o in zip(plan, outcomes):
        if ep["kind"] == "case":
            by_case.setdefault(ep["case"], []).append(o[field])
    return by_case


def case_means(plan, outcomes, field):
    return {c: fixed_weight_mean(v) for c, v in per_case_values(plan, outcomes, field).items()}


def bootstrap_margin_interval(diffs_by_case):
    rng = np.random.default_rng(20260101)
    arrs = [np.asarray(v, dtype=np.float64) for v in diffs_by_case]
    total = np.zeros(BOOTSTRAP_B)
    for arr in arrs:
        idx = rng.integers(0, len(arr), size=(BOOTSTRAP_B, len(arr)))
        total += arr[idx].mean(axis=1)
    total /= len(arrs)
    return float(np.percentile(total, 2.5)), float(np.percentile(total, 97.5))


def aggregate(plan, outcomes, ctx, verdicts, flags):
    cases = ctx.cases
    loss_by_case = case_means(plan, outcomes, "loss")
    score = 1.0 - fixed_weight_mean(list(loss_by_case.values()))
    exch = [c for c in loss_by_case if cases[c]["exchangeable"]]
    shift = [c for c in loss_by_case if not cases[c]["exchangeable"]]
    marg = case_means(plan, outcomes, "marg_gap")
    slice_gap = case_means(plan, outcomes, "slice_gap")
    size = case_means(plan, outcomes, "size_ratio")
    cov = case_means(plan, outcomes, "cov")
    metrics = {
        "mean_marginal_coverage_gap_exchangeable": fixed_weight_mean([marg[c] for c in exch]) if exch else 0.0,
        "worst_slice_coverage_gap": fixed_weight_mean(list(slice_gap.values())),
        "mean_set_size_ratio": fixed_weight_mean(list(size.values())),
        "shift_coverage_gap": fixed_weight_mean([marg[c] for c in shift]) if shift else 0.0,
        "controls_passed_fraction": (sum(1 for v in verdicts.values() if v[0]) / len(verdicts)) if verdicts else 0.0,
        "n_failed_episodes": sum(1 for o in outcomes if not o["ok"]),
    }
    exch_ok = True
    for c in exch:
        case = cases[c]
        n_seeds = len(per_case_values(plan, outcomes, "cov")[c])
        n_cal = SMOKE_N_CAL if ctx.smoke else case["n_cal"]
        n_test = SMOKE_N_TEST if ctx.smoke else case["n_test"]
        tol = coverage_tolerance(case["alpha"], n_cal, n_test, n_seeds)
        if cov[c] < (1.0 - case["alpha"]) - tol:
            exch_ok = False
    controls_ok = bool(verdicts) and all(v[0] for v in verdicts.values())
    correct = bool(metrics["n_failed_episodes"] == 0 and flags["transcript_ok"] and flags["disjoint_ok"]
                   and controls_ok and exch_ok)
    if PLANE == "search":
        values = {"combined_score": score}
        values.update(metrics)
        return values, correct, {"cov": cov, "size": size, "slice_gap": slice_gap}
    # final plane: baselines evaluated on the same data with the same loss and hierarchy
    base_complete = all((c, s) in ctx.baseline_losses
                        for c, s in {(e["case"], e["seed"]) for e in plan if e["kind"] == "case"})
    if base_complete:
        base_scores = {}
        diffs_per_baseline = {}
        for name in SCORED_BASELINES:
            by_case = collections.OrderedDict()
            for ep in plan:
                if ep["kind"] == "case":
                    by_case.setdefault(ep["case"], []).append(1.0 - ctx.baseline_losses[(ep["case"], ep["seed"])][name])
            base_scores[name] = fixed_weight_mean([fixed_weight_mean(v) for v in by_case.values()])
            diffs_per_baseline[name] = by_case
        best_name = max(SCORED_BASELINES, key=lambda n: base_scores[n])
        best = base_scores[best_name]
        cand_by_case = collections.OrderedDict()
        for ep, o in zip(plan, outcomes):
            if ep["kind"] == "case":
                cand_by_case.setdefault(ep["case"], []).append(1.0 - o["loss"])
        diffs = [np.asarray(cand_by_case[c]) - np.asarray(diffs_per_baseline[best_name][c]) for c in cand_by_case]
        lo, hi = bootstrap_margin_interval(diffs)
        margin = score - best
    else:
        best, margin, lo, hi = 1.0, -1.0, -1.0, -1.0
    values = {"final_score": score}
    values.update(metrics)
    values.update({"best_baseline_score": best, "score_margin_vs_best_baseline": margin,
                   "score_margin_ci_lower": lo, "score_margin_ci_upper": hi})
    return values, correct, None


def worst_case_metrics():
    base = {"mean_marginal_coverage_gap_exchangeable": 1.0, "worst_slice_coverage_gap": 1.0,
            "mean_set_size_ratio": 1.0, "shift_coverage_gap": 1.0, "controls_passed_fraction": 0.0,
            "n_failed_episodes": 0}
    if PLANE == "search":
        out = {"combined_score": 0.0}
        out.update(base)
        return out
    out = {"final_score": 0.0}
    out.update(base)
    out.update({"best_baseline_score": 1.0, "score_margin_vs_best_baseline": -1.0,
                "score_margin_ci_lower": -1.0, "score_margin_ci_upper": -1.0})
    return out


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, sort_keys=False)
        handle.write("\n")


def build_evidence(plan, outcomes, durations, flags):
    records = []
    for seed in sorted({e["seed"] for e in plan}):
        idxs = [i for i, e in enumerate(plan) if e["seed"] == seed]
        case_scores = [1.0 - outcomes[i]["loss"] for i in idxs if plan[i]["kind"] == "case"]
        ok = all(outcomes[i]["ok"] for i in idxs) and flags["transcript_ok"] and flags["disjoint_ok"]
        records.append({"seed": int(seed), "score": float(sum(case_scores) / len(case_scores)),
                        "correct": bool(ok), "duration_seconds": float(sum(durations[i] for i in idxs))})
    return {"schema_version": 1, "episodes": records}


def write_results(results_dir, metrics, correct, evidence, feasible, qualification):
    os.makedirs(results_dir, exist_ok=True)
    names = list(METRIC_NAMES)
    if set(metrics) != set(names):
        raise RuntimeError("metric schema mismatch")
    if not all(isinstance(metrics[n], (int, float)) and math.isfinite(metrics[n]) for n in names):
        raise RuntimeError("non-finite metric")
    write_json(os.path.join(results_dir, "metrics.json"), {n: metrics[n] for n in names})
    write_json(os.path.join(results_dir, "correct.json"), {"correct": bool(correct)})
    if evidence is not None:
        write_json(os.path.join(results_dir, "evaluation_evidence.json"), evidence)
    if qualification:
        write_json(os.path.join(results_dir, "qualification.json"), {"schema_version": 1, "feasible": bool(feasible)})


# ----------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------
def build_plan(manifest, smoke):
    cases = manifest["cases"]
    case_list = cases[:1] if smoke else cases
    seeds = SEEDS[:1] if smoke else SEEDS
    plan = [{"kind": "case", "case": c["id"], "seed": s} for c in case_list for s in seeds]
    for control, case_id, seed in CONTROL_PLAN:
        if smoke and case_id != case_list[0]["id"]:
            continue
        plan.append({"kind": control, "case": case_id, "seed": SEEDS[0] if smoke else seed})
    return plan


def run(args):
    t0 = time.monotonic()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    repair_mode = PLANE == "search" and (smoke or qualification)
    brokered = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    if brokered != (args.program_path == BROKER_PROXY_PATH):
        raise RuntimeError("untrusted broker configuration")
    profile = PROFILES["smoke" if smoke else "production"]

    root = os.path.join(source_dir(), RESOURCE_ROOT)
    with open(os.path.join(root, "case_manifest.json"), "r", encoding="utf-8") as handle:
        manifest = validate_manifest(strict_json_loads(handle.read()))
    plan = build_plan(manifest, smoke)
    expected_resets = [e["seed"] for e in plan]
    if not smoke and expected_resets != RESET_SEQUENCE:
        raise RuntimeError("production plan differs from declared reset sequence")
    ctx = Context(manifest["cases"], smoke)

    # RPC operation-count table: reset + calibrate chunks + predict chunks per episode.
    table = collections.Counter()
    for e in plan:
        c = ctx.cases[e["case"]]
        n_cal = SMOKE_N_CAL if smoke else c["n_cal"]
        n_test = SMOKE_N_TEST if smoke else c["n_test"]
        table["reset"] += 1
        table["calibrate"] += len(chunk_bounds(n_cal))
        table["predict"] += len(chunk_bounds(n_test))
    if sum(table.values()) > MAX_RPC or max(len(chunk_bounds(c["n_cal"])) for c in manifest["cases"]) > MAX_CAL_CHUNKS:
        raise RuntimeError("RPC budget table exceeds declared maximum")
    require_joint_workload_budget(
        episode_count=len(plan), method_count=1, wall_seconds=profile["wall"],
        startup_seconds=profile["startup"], reset_seconds=profile["reset"],
        cleanup_seconds=profile["cleanup"], finish_seconds=profile["finish"], work_seconds=profile["work"])

    # Content-hash disjointness: inside this plane and (final) against the sealed search hash list.
    all_hashes = []
    for key in sorted({(e["case"], e["seed"]) for e in plan}):
        all_hashes.extend(dataset_hashes(ctx.dataset(*key)))
    disjoint_ok = len(set(all_hashes)) == len(all_hashes)
    if PLANE == "final":
        try:
            disjoint_ok = disjoint_ok and not (set(all_hashes) & load_search_hashes(root))
        except (OSError, ValueError):
            disjoint_ok = False

    if brokered:
        transport = ProxyCandidate(args.program_path)
    else:
        transport = NativeCandidate(args.program_path, profile["wall"], repair_mode)
    transcript = []
    counter = {"rpc": 0}

    def rpc(request, timeout):
        counter["rpc"] += 1
        if counter["rpc"] > MAX_RPC:
            raise RuntimeError("RPC budget exceeded")
        if request["op"] == "reset":
            transcript.append(request["seed"])
            if not brokered:
                transport.start()
        return transport.call(request, timeout)

    def record_failure(failure, episode):
        if PLANE != "search":
            return
        line = ("episode_failure case=%s seed=%d kind=%s component=%s category=%s operation=%s"
                % (episode["case"], episode["seed"], episode["kind"], failure["component"],
                   failure["category"], failure["operation"]))
        print(line[:256], file=sys.stderr, flush=True)
        if repair_mode and not brokered:
            snapshot = transport.stop()
            if snapshot and snapshot["stderr"]:
                print(snapshot["stderr"], file=sys.stderr, flush=True)

    try:
        outcomes, durations, complete = run_declared_episodes(
            plan, hard_deadline=t0 + profile["wall"] - profile["startup"], finish_reserve=profile["finish"],
            reset_timeout=profile["reset"], episode_overhead=profile["overhead"], work_cap=profile["work"],
            rpc_cap=profile["rpc_cap"], clock=time.monotonic, rpc=rpc,
            evaluate=lambda ep, call, deadline: evaluate_episode(ep, call, deadline, ctx),
            worst_case=worst_outcome, record_failure=record_failure)
    finally:
        transport.cleanup()
    flags = {"transcript_ok": transcript == expected_resets, "disjoint_ok": disjoint_ok}
    verdicts = control_verdicts(plan, outcomes)
    metrics, correct, summary = aggregate(plan, outcomes, ctx, verdicts, flags)
    if PLANE == "search":
        for c, v in summary["cov"].items():
            print("case %s coverage=%.4f size_ratio=%.4f slice_gap=%.4f"
                  % (c, v, summary["size"][c], summary["slice_gap"][c]), file=sys.stderr)
        for idx, (passed, reason) in verdicts.items():
            print("control %s passed=%s reason=%s" % (plan[idx]["kind"], passed, reason), file=sys.stderr)
        if not (flags["transcript_ok"] and flags["disjoint_ok"]):
            print("integrity transcript_ok=%s disjoint_ok=%s" % (flags["transcript_ok"], flags["disjoint_ok"]),
                  file=sys.stderr)
    feasible = bool(complete and not smoke and time.monotonic() - t0 <= PLANE_WALL
                    and flags["transcript_ok"] and flags["disjoint_ok"])
    write_results(args.results_dir, metrics, correct, build_evidence(plan, outcomes, durations, flags),
                  feasible, qualification)
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        return run(args)
    except BaseException as error:  # bounded diagnostic, non-zero exit
        name = type(error).__name__
        if not name.isascii() or not name.isidentifier() or len(name) > 80:
            name = "EvaluatorError"
        message = " ".join(str(error).split())[:300]
        print("evaluator_error type=%s message=%s" % (name, message), file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
