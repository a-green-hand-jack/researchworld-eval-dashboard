#!/usr/bin/env python3
"""Trusted final evaluator for the few-item benchmark-prediction task.

The candidate (python_rpc_v1:handle) sees only the binary correct/incorrect matrix of SOURCE models
(opaque rows/columns), chooses at most k item columns, then receives each TARGET model's responses on
those columns only and predicts its full-benchmark accuracy.  Everything scored here is computed from
evaluator-held matrices; candidate-reported values are never used.

Episode plan (seed-major, then benchmark order, then split order, then the two negative controls):
  primary episode  = (seed, benchmark, split in [random_targets, strong_targets])
  control episode  = permuted_targets / constant_targets, matched to one real random_targets episode
Aggregation hierarchy (declared before evaluation): episode -> mean over seeds within
(benchmark, split) -> equal-weight mean over benchmarks within a split -> 0.5*random + 0.5*strong.
Episode utility u = 0.5*clip(1-2*MAE,0,1) + 0.5*(Spearman+1)/2; failed/missing episodes contribute
MAE=RMSE=1, Spearman=Kendall=-1, u=0 and keep their weight.
"""

import argparse
import base64
import collections
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import resource
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import time
import warnings

# Candidate threads/environment are derived from the parent environment captured before the
# evaluator pins its own (<=4) thread pools.
_PARENT_ENV = dict(os.environ)
for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "4"
os.environ["PYTHONHASHSEED"] = "0"

import numpy as np  # noqa: E402
from scipy import stats  # noqa: E402

_T0 = time.monotonic()

PLANE = "final"
RESOURCE_SUBDIR = "resources/final"
BENCH_NAMES = ['gpqa', 'med_qa', 'legalbench', 'mmlu', 'mmlu_pro']
BENCHMARK_SHA256 = {
    "gpqa": "240b27a3cafd6a508a3e0a13aa81d095c02bdb2e35a3c90a58e399331797c393",
    "med_qa": "e9aa206337e19cbf7c5b132248f9806b1c8f7bdd9660527ab697b10471832f7f",
    "legalbench": "2e6a14885365b9afb87bd9e668bedcdbf6d2f7047671628e54f2082d18b155ee",
    "mmlu": "d907b7ec000ac3cc76e89d6bed3984cca1c960040b8ddb106b0fe3faab217cfb",
    "mmlu_pro": "2a62e5bd5718af7762a59e96b38094fba94ced502d2370dec0762b3dc09345ba"
}
SEEDS = [9101, 9102, 9103]
RESET_SEQUENCE = [9101, 9101, 9101, 9101, 9101, 9101, 9101, 9101, 9101, 9101, 9102, 9102, 9102, 9102, 9102, 9102, 9102, 9102, 9102, 9102, 9103, 9103, 9103, 9103, 9103, 9103, 9103, 9103, 9103, 9103, 9101, 9101]
SMOKE_RESET_SEQUENCE = [9101, 9101, 9101, 9101]
CONTROL_BENCH = "mmlu_pro"
SMOKE_BENCH = "mmlu"
SMOKE_MAX_ITEMS = 200
WALL_SECONDS = 10800.0
BASELINE_BUDGET = 600.0
EPISODE_SECONDS = 180.0
MAX_CANDIDATE_RPC_CALLS = 160
BOOT_SEED = 20260101
METRIC_NAMES = ['combined_score', 'mae', 'rmse', 'spearman', 'kendall', 'mae_random_targets', 'mae_strong_targets', 'spearman_random_targets', 'spearman_strong_targets', 'delta_mae_vs_random_mean', 'delta_mae_vs_anchor_points', 'delta_mae_vs_irt_style', 'delta_score_vs_best_baseline', 'control_permuted_spearman_drop', 'control_permuted_mae_increase', 'control_constant_mae_delta', 'n_completed_episodes', 'n_failed_episodes', 'n_candidate_rpc_calls_observed', 'delta_score_vs_random_mean', 'delta_mae_vs_best_baseline', 'ci_lo_delta_mae_vs_random_mean', 'ci_hi_delta_mae_vs_random_mean', 'ci_lo_delta_mae_vs_best_baseline', 'ci_hi_delta_mae_vs_best_baseline', 'ci_lo_delta_score_vs_random_mean', 'ci_hi_delta_score_vs_random_mean', 'ci_lo_delta_score_vs_best_baseline', 'ci_hi_delta_score_vs_best_baseline']

# ---------------------------------------------------------------------------------------------
# Fixed, plane-independent protocol constants
# ---------------------------------------------------------------------------------------------
SPLITS = ("random_targets", "strong_targets")
SPLIT_WEIGHTS = (0.5, 0.5)
K_PRODUCTION = 100
K_SMOKE = 20
TARGET_FRACTION = 0.2
STRONG_QUANTILE = 0.7
MIN_SOURCES = 40
MIN_TARGETS = 5
SMOKE_MAX_MODELS = 100
WIRE_LIMIT = 64 * 1024 * 1024
CHUNK_MESSAGE_CAP = 8 * 1024 * 1024
MAX_LOAD_CHUNKS = 2
DTYPE_TAG = "uint8 bits"
ENCODING_TAG = "np.packbits axis=1 bitorder=big then base64"
PROXY_PATH = "/broker-code/candidate_proxy.py"
EVAL_THREADS = 4
CANDIDATE_THREADS = 8
CANDIDATE_MEMORY_BYTES = 16 * 1024 ** 3

STARTUP_ALLOWANCE = 120.0
FINISH_RESERVE = 60.0
RESET_TIMEOUT = 45.0
RPC_CAP = 120.0
CLEANUP_SECONDS = 8.0
EPISODE_OVERHEAD = 8.0
ESTIMATED_PRODUCTION_EPISODE_CLEANUP = 8.0

IRT_DIMS = 3
IRT_ITERS = 200
BOOT_REPLICATES = 300

WORST = {"mae": 1.0, "rmse": 1.0, "spearman": -1.0, "kendall": -1.0, "u": 0.0}

SMOKE = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
QUALIFICATION = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
DIAGNOSTICS_VISIBLE = PLANE == "search" and (SMOKE or QUALIFICATION)


# ---------------------------------------------------------------------------------------------
# Required-worker failure identity and bounded diagnostics (shared recipes)
# ---------------------------------------------------------------------------------------------
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


class CandidateProtocolError(RuntimeError):
    """Expected candidate-side fault with a fixed category and operation name."""

    def __init__(self, category, operation):
        self.category = bounded_failure_name(category, "protocol_error")
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("candidate protocol error")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, CandidateProtocolError):
            op = context.operation if context.operation != "unknown" else bounded_failure_name(operation, "unknown")
            return {"component": "candidate", "category": context.category, "operation": op}
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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


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
        self.result = {
            "stderr": "".join(self.lines),
            "observed_bytes": self.observed_bytes,
            "retained_bytes": self.retained_bytes,
            "truncated": self.truncated,
            "capture_error": self.capture_error,
        }
        return dict(self.result)


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
        finite_budget_seconds(needed)
        if needed > times["wall_seconds"]:
            raise ValueError(f"{plane} productive work exceeds the declared wall budget")
        required[plane] = needed
    return required


def fixed_weight_score(values, weights, worst_case):
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(w) or w < 0 for w in weights)
            or not math.isclose(sum(weights), 1.0, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("invalid predeclared aggregation weights")
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError("nonfinite contribution")
    return sum(value * weight for value, weight in zip(retained, weights))


def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure, episode_seconds, durations,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = min(candidate_deadline - remaining * reset_slot, started + episode_seconds)
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
            except (TimeoutError, RequiredBaselineFailure, CandidateProtocolError) as error:
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
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(index, failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
        durations[index] = max(0.0, clock() - started)
    return outcomes, complete


# ---------------------------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------------------------
def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, RESOURCE_SUBDIR)


_MATRIX_CACHE = {}


def load_matrix(name, smoke):
    """Hash-verified, cleaned uint8 response matrix (models x items)."""
    key = (name, smoke)
    if key in _MATRIX_CACHE:
        return _MATRIX_CACHE[key]
    import joblib
    path = os.path.join(resource_root(), name + ".jbl")
    with open(path, "rb") as handle:
        blob = handle.read()
    if hashlib.sha256(blob).hexdigest() != BENCHMARK_SHA256[name]:
        raise RuntimeError("resource checksum mismatch")
    raw = np.asarray(joblib.load(io.BytesIO(blob)))
    if raw.ndim != 2:
        raise RuntimeError("unexpected matrix rank")
    if not set(np.unique(raw).tolist()).issubset({0, 1}):
        raise RuntimeError("matrix is not binary")
    matrix = raw.astype(np.uint8)
    matrix = matrix[matrix.mean(axis=1) > 1e-8]
    _, first = np.unique(matrix, axis=0, return_index=True)  # identical models would leak across the split
    matrix = matrix[np.sort(first)]
    if smoke:
        matrix = matrix[:SMOKE_MAX_MODELS, :SMOKE_MAX_ITEMS]
    _MATRIX_CACHE[key] = matrix
    return matrix


def make_rng(seed, bench_index, split_index, salt):
    return np.random.default_rng([int(seed), int(bench_index), int(split_index), int(salt)])


def build_episode(bench, split, seed, smoke):
    bench_index = BENCH_NAMES.index(bench)
    split_index = SPLITS.index(split)
    matrix = load_matrix(bench, smoke)
    n_models = matrix.shape[0]
    n_targets = max(MIN_TARGETS, int(round(TARGET_FRACTION * n_models)))
    scores = matrix.mean(axis=1)
    rng = make_rng(seed, bench_index, split_index, 1)
    if split == "random_targets":
        order = rng.permutation(n_models)
        targets, sources = order[:n_targets], order[n_targets:]
    else:
        threshold = np.quantile(scores, STRONG_QUANTILE)
        pool = np.flatnonzero(scores >= threshold)
        sources = np.flatnonzero(scores < threshold)
        n_targets = min(n_targets, len(pool))
        targets = rng.choice(pool, size=n_targets, replace=False)
    if len(sources) < MIN_SOURCES or len(targets) < MIN_TARGETS:
        raise RuntimeError("split too small")
    prng = make_rng(seed, bench_index, split_index, 2)
    sources = sources[prng.permutation(len(sources))]
    targets = targets[prng.permutation(len(targets))]
    col = make_rng(seed, bench_index, 0, 3).permutation(matrix.shape[1])  # same column order for both splits
    src = np.ascontiguousarray(matrix[sources][:, col])
    tgt = np.ascontiguousarray(matrix[targets][:, col])
    return {"bench": bench, "split": split, "seed": seed, "bench_index": bench_index,
            "split_index": split_index, "src": src, "tgt": tgt,
            "truth": tgt.astype(np.float64).mean(axis=1)}


# ---------------------------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------------------------
def spearman_corr(a, b):
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    if len(a) < 2:
        return 0.0
    ra, rb = stats.rankdata(a), stats.rankdata(b)
    if np.ptp(ra) == 0 or np.ptp(rb) == 0:
        return 0.0
    value = float(np.corrcoef(ra, rb)[0, 1])
    return value if math.isfinite(value) else 0.0


def kendall_corr(a, b):
    if len(a) < 2 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return 0.0
    value = float(stats.kendalltau(a, b).statistic)
    return value if math.isfinite(value) else 0.0


def utility(mae, rho):
    return 0.5 * min(max(1.0 - 2.0 * mae, 0.0), 1.0) + 0.5 * (rho + 1.0) / 2.0


def episode_metrics(pred, truth):
    pred = np.asarray(pred, dtype=np.float64)
    err = pred - truth
    mae = float(np.mean(np.abs(err)))
    rho = spearman_corr(pred, truth)
    return {"mae": mae, "rmse": float(np.sqrt(np.mean(err ** 2))), "spearman": rho,
            "kendall": kendall_corr(pred, truth), "u": utility(mae, rho)}


# ---------------------------------------------------------------------------------------------
# Trusted baselines (evaluator-owned reimplementations; upstream benchpred is not imported)
# ---------------------------------------------------------------------------------------------
def baseline_rng(ep, salt):
    return make_rng(ep["seed"], ep["bench_index"], ep["split_index"], 100 + salt)


def baseline_random_mean(ep, k):
    rng = baseline_rng(ep, 0)
    idx = rng.choice(ep["src"].shape[1], size=k, replace=False)
    return ep["tgt"][:, idx].astype(np.float64).mean(axis=1)


def baseline_source_mean_constant(ep, k):
    return np.full(ep["tgt"].shape[0], float(ep["src"].astype(np.float64).mean()))


def _kmeans_medoids(features, k, seed):
    from sklearn.cluster import KMeans
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        km = KMeans(n_clusters=k, n_init=1, max_iter=50, tol=1e-3, random_state=seed).fit(features)
    d2 = ((features - km.cluster_centers_[km.labels_]) ** 2).sum(axis=1)
    anchors, weights = [], []
    for c in range(k):
        members = np.flatnonzero(km.labels_ == c)
        if len(members) == 0:
            continue
        anchors.append(int(members[np.argmin(d2[members])]))
        weights.append(len(members))
    return np.array(anchors), np.array(weights, dtype=np.float64)


def baseline_anchor_points(ep, k):
    seed = int(baseline_rng(ep, 1).integers(0, 2 ** 31 - 1))
    feats = ep["src"].T.astype(np.float32)
    anchors, weights = _kmeans_medoids(feats, k, seed)
    weights = weights / weights.sum()
    return ep["tgt"][:, anchors].astype(np.float64) @ weights


def _sigmoid(z):
    return 0.5 * (1.0 + np.tanh(0.5 * z))


def _irt_fit(S, rng):
    """Multidimensional logistic IRT, P(correct)=sigmoid(theta_i . a_j + b_j), SVD-initialised Adam fit."""
    n, m = S.shape
    S = S.astype(np.float32)
    p0 = np.clip(S.mean(axis=0), 0.02, 0.98)
    b = np.log(p0 / (1 - p0)).astype(np.float32)
    U, sv, Vt = np.linalg.svd(S - S.mean(axis=0), full_matrices=False)
    root = np.sqrt(np.float32(n))
    th = (U[:, :IRT_DIMS] * np.sqrt(root)).astype(np.float32)
    A = (Vt[:IRT_DIMS] * sv[:IRT_DIMS, None] / np.sqrt(root) / root).astype(np.float32)
    params = [th, A, b]
    mom = [np.zeros_like(p) for p in params]
    var = [np.zeros_like(p) for p in params]
    lr, b1, b2, lam = 0.03, 0.9, 0.999, 0.1
    for t in range(1, IRT_ITERS + 1):
        G = (_sigmoid(th @ A + b) - S) / np.float32(n * m)
        grads = [G @ A.T + lam * th / n, th.T @ G + lam * A / m, G.sum(axis=0)]
        for i, (p, g) in enumerate(zip(params, grads)):
            mom[i] = b1 * mom[i] + (1 - b1) * g
            var[i] = b2 * var[i] + (1 - b2) * g * g
            p -= lr * (mom[i] / (1 - b1 ** t)) / (np.sqrt(var[i] / (1 - b2 ** t)) + 1e-8)
    return th, A, b


def _irt_ability(Asel, bsel, y):
    """Ridge-regularised logistic MLE of one target's ability (Newton, prior precision 1)."""
    d = Asel.shape[0]
    theta = np.zeros(d)
    for _ in range(20):
        p = _sigmoid(theta @ Asel + bsel)
        grad = Asel @ (p - y) + theta
        hess = (Asel * (p * (1 - p))) @ Asel.T + np.eye(d)
        step = np.linalg.solve(hess, grad)
        theta = theta - np.clip(step, -2.0, 2.0)
        if np.max(np.abs(step)) < 1e-6:
            break
    return theta


def baseline_irt_style(ep, k):
    rng = baseline_rng(ep, 2)
    th, A, b = _irt_fit(ep["src"], rng)
    feats = np.concatenate([A.T, b[:, None]], axis=1).astype(np.float64)
    feats = (feats - feats.mean(axis=0)) / (feats.std(axis=0) + 1e-8)
    anchors, _ = _kmeans_medoids(feats, k, int(rng.integers(0, 2 ** 31 - 1)))
    A64, b64 = A.astype(np.float64), b.astype(np.float64)
    preds = []
    for row in ep["tgt"][:, anchors].astype(np.float64):
        theta = _irt_ability(A64[:, anchors], b64[anchors], row)
        preds.append(float(_sigmoid(theta @ A64 + b64).mean()))
    return np.clip(np.array(preds), 0.0, 1.0)


BASELINE_FUNCTIONS = collections.OrderedDict([
    ("random_mean", baseline_random_mean),
    ("anchor_points_kmeans", baseline_anchor_points),
    ("irt_style", baseline_irt_style),
    ("source_mean_constant", baseline_source_mean_constant),
])
REQUIRED_BASELINES = ("random_mean", "anchor_points_kmeans")
EXPECTED_BASELINE_ERRORS = (np.linalg.LinAlgError, ValueError, RuntimeError, TimeoutError, MemoryError)


def run_baselines(primary, k, deadline, record_baseline_failure):
    """Compute every baseline before any candidate reset.  Returns {key: {name: pred or None}}."""
    results = {}
    for ep in primary:
        key = (ep["bench"], ep["split"], ep["seed"])
        results[key] = {}
        for name, fn in BASELINE_FUNCTIONS.items():
            try:
                if time.monotonic() > deadline:
                    raise TimeoutError()
                pred = np.asarray(fn(ep, k), dtype=np.float64)
                if pred.shape != (ep["tgt"].shape[0],) or not np.all(np.isfinite(pred)):
                    raise RuntimeError("invalid baseline output")
                results[key][name] = np.clip(pred, 0.0, 1.0)
            except EXPECTED_BASELINE_ERRORS as error:
                category = "baseline_timeout" if isinstance(error, TimeoutError) else "baseline_result_failure"
                record_baseline_failure(name, category)
                if name in REQUIRED_BASELINES:
                    raise RequiredBaselineFailure(category) from None
                results[key][name] = None
    return results


# ---------------------------------------------------------------------------------------------
# Wire protocol
# ---------------------------------------------------------------------------------------------
def pack_bits(rows):
    return base64.b64encode(np.packbits(np.ascontiguousarray(rows, dtype=np.uint8), axis=1, bitorder="big").tobytes()).decode("ascii")


def bounded_json_size(value, wire_limit=WIRE_LIMIT):
    try:
        encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    except (TypeError, ValueError):
        raise CandidateProtocolError("non_finite_or_non_json", "unknown") from None
    if len(encoded) >= wire_limit:
        raise CandidateProtocolError("message_too_large", "unknown")
    return len(encoded)


def load_chunk_plan(n_rows, n_items):
    row_bytes = (n_items + 7) // 8
    per_chunk = max(1, (CHUNK_MESSAGE_CAP - 4096) * 3 // 4 // row_bytes)
    chunks = []
    start = 0
    while start < n_rows:
        count = min(per_chunk, n_rows - start)
        chunks.append((start, count))
        start += count
    return chunks


def episode_rpc_counts(max_chunks=MAX_LOAD_CHUNKS):
    return {"reset": 1, "load_source": max_chunks, "select": 1, "predict": 1}


def plan_rpc_total(n_episodes, max_chunks=MAX_LOAD_CHUNKS):
    return n_episodes * sum(episode_rpc_counts(max_chunks).values())


def build_load_requests(ep, episode_id, task_id, k):
    src = ep["src"]
    plan = load_chunk_plan(src.shape[0], src.shape[1])
    if len(plan) > MAX_LOAD_CHUNKS:
        raise RuntimeError("source matrix needs more chunks than declared")
    requests = []
    for index, (start, count) in enumerate(plan):
        requests.append({
            "op": "load_source", "task_id": task_id, "episode_id": episode_id,
            "n_source_models": int(src.shape[0]), "n_items": int(src.shape[1]), "k": int(k),
            "split": ep["split"], "n_chunks": len(plan), "chunk_index": index,
            "row_start": int(start), "row_count": int(count), "dtype": DTYPE_TAG,
            "shape": [int(count), int(src.shape[1])], "encoding": ENCODING_TAG,
            "data_b64": pack_bits(src[start:start + count]),
        })
    return requests


def validate_indices(response, k, n_items):
    if type(response) is not dict or set(response) != {"indices"}:
        raise CandidateProtocolError("malformed_response", "select")
    idx = response["indices"]
    if type(idx) is not list or not 1 <= len(idx) <= k:
        raise CandidateProtocolError("malformed_response", "select")
    if any(type(i) is not int or not 0 <= i < n_items for i in idx) or len(set(idx)) != len(idx):
        raise CandidateProtocolError("malformed_response", "select")
    return list(idx)


def validate_predictions(response, n_targets):
    if type(response) is not dict or set(response) != {"predictions"}:
        raise CandidateProtocolError("malformed_response", "predict")
    pred = response["predictions"]
    if type(pred) is not list or len(pred) != n_targets:
        raise CandidateProtocolError("malformed_response", "predict")
    if any(type(p) not in (int, float) or not math.isfinite(p) or not 0.0 <= p <= 1.0 for p in pred):
        raise CandidateProtocolError("malformed_response", "predict")
    return np.array(pred, dtype=np.float64)


def derangement(n, rng):
    order = rng.permutation(n)
    out = np.empty(n, dtype=np.int64)
    out[order] = np.roll(order, -1)
    return out


def control_rows(kind, ep, idx, seed_rng):
    """Target response rows (on the selected columns) sent for a negative-control episode.

    Returns (rows, valid).  `valid` is False for a vacuous control.
    """
    rows = ep["tgt"][:, idx]
    if kind == "permuted_targets":
        perm = derangement(rows.shape[0], seed_rng)
        if np.any(perm == np.arange(len(perm))):
            return rows, False
        changed = sum(not np.array_equal(rows[perm[i]], rows[i]) for i in range(len(perm)))
        return rows[perm], changed >= 2
    if kind == "constant_targets":
        const = (ep["src"][:, idx].astype(np.float64).mean(axis=0) >= 0.5).astype(np.uint8)
        return np.tile(const, (rows.shape[0], 1)), True
    raise RuntimeError("unknown control")


def candidate_episode(episode, ep, call, work_deadline, k, episode_id, task_id):
    for request in build_load_requests(ep, episode_id, task_id, k):
        bounded_json_size(request, CHUNK_MESSAGE_CAP)
        if call(request) != {"ok": True}:
            raise CandidateProtocolError("malformed_response", "load_source")
    n_items = ep["src"].shape[1]
    idx = validate_indices(call({"op": "select", "episode_id": episode_id, "k": int(k)}), k, n_items)
    if time.monotonic() > work_deadline:
        raise TimeoutError("episode work budget exhausted")
    kind = episode["control"]
    valid = True
    if kind is None:
        rows = ep["tgt"][:, idx]
    else:
        rows, valid = control_rows(kind, ep, idx, make_rng(episode["seed"], ep["bench_index"], ep["split_index"], 7))
    request = {"op": "predict", "episode_id": episode_id, "indices": idx, "n_targets": int(rows.shape[0]),
               "dtype": DTYPE_TAG, "shape": [int(rows.shape[0]), len(idx)], "encoding": ENCODING_TAG,
               "data_b64": pack_bits(rows)}
    bounded_json_size(request, CHUNK_MESSAGE_CAP)
    pred = validate_predictions(call(request), rows.shape[0])
    return {"complete": True, "pred": pred, "valid": valid}


# ---------------------------------------------------------------------------------------------
# Candidate transports
# ---------------------------------------------------------------------------------------------
_WORKER_SOURCE = r'''
import importlib.util, json, os, sys
def main():
    path = sys.argv[1]
    out = os.fdopen(os.dup(1), "wb")
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec = importlib.util.spec_from_file_location("candidate_program", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    handle = module.handle
    for line in sys.stdin.buffer:
        try:
            response = handle(json.loads(line))
            data = json.dumps(response, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
        except BaseException as error:
            name = type(error).__name__
            sys.stderr.write("worker_exception type=%s\n" % (name if name.isidentifier() else "WorkerException"))
            sys.stderr.flush()
            data = b'{"__worker_error__":true}\n'
        out.write(data)
        out.flush()
main()
'''


class RpcTimeout(TimeoutError):
    pass


class BrokeredTransport:
    """In-process call of the harness-owned proxy (trusted path, never re-isolated)."""

    def __init__(self, handle):
        self.handle = handle
        self.failure_stderr = None

    def request(self, request, timeout):
        def on_alarm(signum, frame):
            raise RpcTimeout("candidate rpc timeout")
        previous = signal.signal(signal.SIGALRM, on_alarm)
        signal.setitimer(signal.ITIMER_REAL, max(timeout, 0.001))
        try:
            response = self.handle(request)
        except TimeoutError:
            raise
        except Exception:
            raise CandidateProtocolError("candidate_exception", request.get("op", "unknown")) from None
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
        return response

    def close(self):
        pass


class NativeTransport:
    """Untrusted smoke candidate: killable, resource-limited, no-network-env subprocess."""

    def __init__(self, program_path):
        self.program_path = os.path.abspath(program_path)
        self.proc = None
        self.stderr = None
        self.workdir = tempfile.mkdtemp(prefix="cand_")
        self.buffer = bytearray()
        self.failure_stderr = None

    def _spawn(self, episode_seconds):
        interpreter = _PARENT_ENV.get("TASK_PYTHON", sys.executable)
        names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ", "CUDA_VISIBLE_DEVICES",
                 "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES")
        env = {n: _PARENT_ENV[n] for n in names if n in _PARENT_ENV}
        env.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                   PYTHONUNBUFFERED="1", OMP_NUM_THREADS=str(CANDIDATE_THREADS),
                   OPENBLAS_NUM_THREADS=str(CANDIDATE_THREADS), MKL_NUM_THREADS=str(CANDIDATE_THREADS),
                   NUMEXPR_NUM_THREADS=str(CANDIDATE_THREADS))
        cpu = cpu_limit_seconds(episode_seconds + RESET_TIMEOUT, CANDIDATE_THREADS)

        def limits():
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
            resource.setrlimit(resource.RLIMIT_AS, (CANDIDATE_MEMORY_BYTES, CANDIDATE_MEMORY_BYTES))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        self.proc = subprocess.Popen(
            [interpreter, "-c", _WORKER_SOURCE, self.program_path], shell=False, cwd=self.workdir, env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            start_new_session=True, preexec_fn=limits, close_fds=True)
        self.stderr = BoundedWorkerStderr(self.proc.stderr)
        os.set_blocking(self.proc.stdin.fileno(), False)
        os.set_blocking(self.proc.stdout.fileno(), False)
        self.buffer = bytearray()

    def _terminate(self):
        proc, self.proc = self.proc, None
        snapshot = None
        if proc is not None:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass
                try:
                    proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    pass
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
        if self.stderr is not None:
            try:
                snapshot = self.stderr.close()
            except RuntimeError:
                snapshot = None
            self.stderr = None
        return snapshot

    def request(self, request, timeout):
        deadline = time.monotonic() + timeout
        if request.get("op") == "reset":
            self._terminate()
            self._spawn(EPISODE_SECONDS)
        if self.proc is None or self.proc.poll() is not None:
            self._fail()
            raise CandidateProtocolError("transport_error", request.get("op", "unknown"))
        data = json.dumps(request, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
        if len(data) >= WIRE_LIMIT:
            raise CandidateProtocolError("message_too_large", request.get("op", "unknown"))
        try:
            self._send(data, deadline)
            line = self._read_line(deadline)
        except TimeoutError:
            self._fail()
            raise
        except OSError:
            self._fail()
            raise CandidateProtocolError("transport_error", request.get("op", "unknown")) from None
        try:
            response = json.loads(line)
        except ValueError:
            raise CandidateProtocolError("malformed_response", request.get("op", "unknown")) from None
        if type(response) is dict and response.get("__worker_error__") is True:
            raise CandidateProtocolError("candidate_exception", request.get("op", "unknown"))
        return response

    def _send(self, data, deadline):
        view = memoryview(data)
        with selectors.DefaultSelector() as selector:
            selector.register(self.proc.stdin, selectors.EVENT_WRITE)
            while view:
                left = deadline - time.monotonic()
                if left <= 0:
                    raise TimeoutError("candidate rpc timeout")
                if not selector.select(timeout=min(left, 0.5)):
                    continue
                try:
                    sent = os.write(self.proc.stdin.fileno(), view[:65536])
                except BlockingIOError:
                    continue
                view = view[sent:]

    def _read_line(self, deadline):
        with selectors.DefaultSelector() as selector:
            selector.register(self.proc.stdout, selectors.EVENT_READ)
            while True:
                newline = self.buffer.find(b"\n")
                if newline >= 0:
                    line = bytes(self.buffer[:newline])
                    del self.buffer[:newline + 1]
                    return line
                if len(self.buffer) >= WIRE_LIMIT:
                    raise CandidateProtocolError("message_too_large", "unknown")
                left = deadline - time.monotonic()
                if left <= 0:
                    raise TimeoutError("candidate rpc timeout")
                if not selector.select(timeout=min(left, 0.5)):
                    continue
                try:
                    chunk = os.read(self.proc.stdout.fileno(), 1 << 20)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise BrokenPipeError()
                self.buffer.extend(chunk)

    def _fail(self):
        self.failure_stderr = self._terminate()

    def close(self):
        self._terminate()
        try:
            os.rmdir(self.workdir)
        except OSError:
            pass


def open_transport(program_path):
    brokered_env = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    if program_path == PROXY_PATH:
        if not brokered_env:
            raise RuntimeError("broker proxy path requires the broker socket signal")
        spec = importlib.util.spec_from_file_location("candidate_proxy", PROXY_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return BrokeredTransport(module.handle)
    return NativeTransport(program_path)


# ---------------------------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------------------------
def hierarchy(values, benches, seeds):
    """values[(bench, split, seed)] -> float; episode->seeds->benchmarks->split weights."""
    per_split = []
    for split in SPLITS:
        bench_means = [float(np.mean([values[(b, split, s)] for s in seeds])) for b in benches]
        per_split.append(float(np.mean(bench_means)))
    return fixed_weight_score(per_split, SPLIT_WEIGHTS, 0.0), dict(zip(SPLITS, per_split))


def finite_or_raise(metrics):
    for name, value in metrics.items():
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise RuntimeError("nonfinite metric")
    return metrics


def worst_case_metrics():
    base = {name: 0.0 for name in METRIC_NAMES}
    base.update(combined_score=0.0, mae=1.0, rmse=1.0, spearman=-1.0, kendall=-1.0,
                mae_random_targets=1.0, mae_strong_targets=1.0,
                spearman_random_targets=-1.0, spearman_strong_targets=-1.0)
    return base


def bootstrap_deltas(records, benches, seeds, best_name, replicates):
    """Paired hierarchical bootstrap: benchmarks, seeds, then target models are resampled."""
    rng = np.random.default_rng([BOOT_SEED])
    comparisons = {"random_mean": "random_mean", "best": best_name}
    out = {f"{kind}_{ref}": [] for kind in ("mae", "score") for ref in comparisons}

    def cell(key, idx):
        rec = records[key]
        truth = rec["truth"][idx]
        if rec["cand"] is None:
            cand = (1.0, 0.0)
        else:
            m = episode_metrics(rec["cand"][idx], truth)
            cand = (m["mae"], m["u"])
        refs = {}
        for ref, name in comparisons.items():
            m = episode_metrics(rec["baselines"][name][idx], truth)
            refs[ref] = (m["mae"], m["u"])
        return cand, refs

    for _ in range(replicates):
        acc = {k: [] for k in out}
        for split in SPLITS:
            vals = {k: [] for k in out}
            for b in rng.integers(0, len(benches), len(benches)):
                cells = {k: [] for k in out}
                for s in rng.integers(0, len(seeds), len(seeds)):
                    key = (benches[b], split, seeds[s])
                    n = len(records[key]["truth"])
                    cand, refs = cell(key, rng.integers(0, n, n))
                    for ref in comparisons:
                        cells[f"mae_{ref}"].append(refs[ref][0] - cand[0])
                        cells[f"score_{ref}"].append(cand[1] - refs[ref][1])
                for k in out:
                    vals[k].append(float(np.mean(cells[k])))
            for k in out:
                acc[k].append(float(np.mean(vals[k])))
        for k in out:
            out[k].append(0.5 * acc[k][0] + 0.5 * acc[k][1])
    result = {}
    for k, v in out.items():
        lo, hi = np.percentile(v, [2.5, 97.5])
        result[k] = (float(lo), float(hi))
    return result


# ---------------------------------------------------------------------------------------------
# Main evaluation
# ---------------------------------------------------------------------------------------------
def build_plan(smoke):
    benches = [SMOKE_BENCH] if smoke else list(BENCH_NAMES)
    seeds = [SEEDS[0]] if smoke else list(SEEDS)
    control_bench = SMOKE_BENCH if smoke else CONTROL_BENCH
    plan = []
    for seed in seeds:
        for bench in benches:
            for split in SPLITS:
                plan.append({"seed": seed, "bench": bench, "split": split, "control": None})
    for kind in ("permuted_targets", "constant_targets"):
        plan.append({"seed": seeds[0], "bench": control_bench, "split": "random_targets", "control": kind})
    for index, episode in enumerate(plan):
        episode["episode_id"] = "e%02d" % index
        episode["task_id"] = "t%d" % BENCH_NAMES.index(episode["bench"])
    return plan, benches, seeds


def emit_failure_line(index, failure):
    return None


def write_outputs(results_dir, metrics, correct, feasible, evidence):
    os.makedirs(results_dir, exist_ok=True)
    declared = set(METRIC_NAMES)
    if set(metrics) != declared:
        raise RuntimeError("metric names do not match declaration")
    finite_or_raise(metrics)
    with open(os.path.join(results_dir, "metrics.json"), "w") as handle:
        json.dump({name: float(metrics[name]) for name in METRIC_NAMES}, handle, allow_nan=False)
    with open(os.path.join(results_dir, "correct.json"), "w") as handle:
        json.dump({"correct": bool(correct)}, handle)
    if QUALIFICATION:
        with open(os.path.join(results_dir, "qualification.json"), "w") as handle:
            json.dump({"schema_version": 1, "feasible": bool(feasible)}, handle)
    if evidence is not None:
        with open(os.path.join(results_dir, "evaluation_evidence.json"), "w") as handle:
            json.dump({"schema_version": 1, "episodes": evidence}, handle, allow_nan=False)


def seed_evidence(seeds, plan, outcomes, durations, per_episode_u, correct_by_seed, override_duration=None):
    records = []
    for seed in seeds:
        us = [per_episode_u[i] for i, e in enumerate(plan) if e["seed"] == seed and e["control"] is None]
        dur = override_duration if override_duration is not None else sum(
            durations[i] for i, e in enumerate(plan) if e["seed"] == seed)
        records.append({"seed": int(seed), "score": float(np.mean(us)) if us else 0.0,
                        "correct": bool(correct_by_seed[seed]), "duration_seconds": float(max(dur, 0.0))})
    return records


def evaluate_plane(program_path, results_dir):
    smoke = SMOKE
    plan, benches, seeds = build_plan(smoke)
    k = K_SMOKE if smoke else K_PRODUCTION
    declared = SMOKE_RESET_SEQUENCE if smoke else RESET_SEQUENCE
    if [e["seed"] for e in plan] != list(declared):
        raise RuntimeError("episode plan does not match the declared reset sequence")
    if not smoke:
        require_joint_workload_budget(
            search={"episode_count": len(plan), "method_count": 1, "wall_seconds": WALL_SECONDS,
                    "startup_seconds": STARTUP_ALLOWANCE + BASELINE_BUDGET, "reset_seconds": RESET_TIMEOUT,
                    "cleanup_seconds": CLEANUP_SECONDS, "finish_seconds": FINISH_RESERVE,
                    "work_seconds": EPISODE_SECONDS},
            final={"episode_count": len(plan), "method_count": 1, "wall_seconds": WALL_SECONDS,
                   "startup_seconds": STARTUP_ALLOWANCE + BASELINE_BUDGET, "reset_seconds": RESET_TIMEOUT,
                   "cleanup_seconds": CLEANUP_SECONDS, "finish_seconds": FINISH_RESERVE,
                   "work_seconds": EPISODE_SECONDS})
    rpc_cap_total = plan_rpc_total(len(plan))
    if not smoke and rpc_cap_total != MAX_CANDIDATE_RPC_CALLS:
        raise RuntimeError("rpc table does not match the declared budget")

    hard_deadline = _T0 + WALL_SECONDS - STARTUP_ALLOWANCE
    started = time.monotonic()
    primary_plan = [e for e in plan if e["control"] is None]
    episodes = {}
    for e in plan:
        key = (e["bench"], e["split"], e["seed"])
        if key not in episodes:
            episodes[key] = build_episode(e["bench"], e["split"], e["seed"], smoke)
    # Payload preflight: every complete load/select/predict message must stay below the cap.
    for key, ep in episodes.items():
        for req in build_load_requests(ep, "e00", "t0", k):
            bounded_json_size(req, CHUNK_MESSAGE_CAP)
        n_t, n_i = ep["tgt"].shape[0], min(k, ep["src"].shape[1])
        bounded_json_size({"op": "predict", "episode_id": "e00", "indices": list(range(n_i)), "n_targets": n_t,
                           "dtype": DTYPE_TAG, "shape": [n_t, n_i], "encoding": ENCODING_TAG,
                           "data_b64": pack_bits(ep["tgt"][:, :n_i])}, CHUNK_MESSAGE_CAP)
        bounded_json_size({"predictions": [0.123456789012345678] * n_t})

    failures_seen = []

    def record_baseline_failure(name, category):
        failures_seen.append(category)

    seed_correct = {s: False for s in seeds}
    try:
        baselines = run_baselines([episodes[(e["bench"], e["split"], e["seed"])] for e in primary_plan], k,
                                  _T0 + BASELINE_BUDGET, record_baseline_failure)
    except RequiredBaselineFailure:
        elapsed = time.monotonic() - _T0
        write_outputs(results_dir, worst_case_metrics(), False, False,
                      seed_evidence(seeds, plan, None, [0.0] * len(plan), {i: 0.0 for i in range(len(plan))},
                                    seed_correct, override_duration=elapsed))
        return

    transport = open_transport(program_path)
    rpc_count = [0]
    cap_per_run = rpc_cap_total

    def rpc(request, timeout):
        rpc_count[0] += 1
        if rpc_count[0] > cap_per_run:
            raise CandidateProtocolError("rpc_budget", request.get("op", "unknown"))
        bounded_json_size(request)
        try:
            response = transport.request(request, timeout)
        except RpcTimeout:
            raise TimeoutError("candidate rpc timeout") from None
        if request.get("op") != "reset":
            bounded_json_size(response)
        return response

    def evaluate(episode, call, work_deadline):
        ep = episodes[(episode["bench"], episode["split"], episode["seed"])]
        return candidate_episode(episode, ep, call, work_deadline, k, episode["episode_id"], episode["task_id"])

    def record_failure(index, failure):
        emit_failure_line(index, failure)
        transport.failure_stderr = None

    durations = [0.0] * len(plan)
    try:
        outcomes, complete = run_declared_episodes(
            plan, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT,
            episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP, clock=time.monotonic, rpc=rpc,
            evaluate=evaluate, worst_case=lambda e: {"complete": False, "pred": None, "valid": False},
            record_failure=record_failure, episode_seconds=EPISODE_SECONDS, durations=durations)
    finally:
        transport.close()

    # ---- scoring (evaluator-owned) ----
    per_u, per_cell = {}, {m: {} for m in ("mae", "rmse", "spearman", "kendall", "u")}
    records = {}
    cand_available = {}
    for i, e in enumerate(plan):
        if e["control"] is not None:
            continue
        key = (e["bench"], e["split"], e["seed"])
        ep = episodes[key]
        out = outcomes[i]
        if out["complete"]:
            m = episode_metrics(out["pred"], ep["truth"])
        else:
            m = dict(WORST)
        for name in per_cell:
            per_cell[name][key] = m[name]
        per_u[i] = m["u"]
        records[key] = {"truth": ep["truth"], "cand": out["pred"] if out["complete"] else None,
                        "baselines": baselines[key], "metrics": m}
        cand_available[key] = out["complete"]

    metrics = {}
    aggregated, by_split = {}, {}
    for name in ("mae", "rmse", "spearman", "kendall", "u"):
        aggregated[name], by_split[name] = hierarchy(per_cell[name], benches, seeds)
    metrics.update(combined_score=aggregated["u"], mae=aggregated["mae"], rmse=aggregated["rmse"],
                   spearman=aggregated["spearman"], kendall=aggregated["kendall"],
                   mae_random_targets=by_split["mae"]["random_targets"],
                   mae_strong_targets=by_split["mae"]["strong_targets"],
                   spearman_random_targets=by_split["spearman"]["random_targets"],
                   spearman_strong_targets=by_split["spearman"]["strong_targets"])

    base_u, base_mae, base_ok = {}, {}, {}
    for name in BASELINE_FUNCTIONS:
        ok = all(baselines[(e["bench"], e["split"], e["seed"])].get(name) is not None for e in primary_plan)
        base_ok[name] = ok
        if ok:
            u_vals, mae_vals = {}, {}
            for key, rec in records.items():
                bm = episode_metrics(rec["baselines"][name], rec["truth"])
                u_vals[key], mae_vals[key] = bm["u"], bm["mae"]
            base_u[name] = hierarchy(u_vals, benches, seeds)[0]
            base_mae[name] = hierarchy(mae_vals, benches, seeds)[0]
    for name, metric in (("random_mean", "delta_mae_vs_random_mean"), ("anchor_points_kmeans", "delta_mae_vs_anchor_points"),
                         ("irt_style", "delta_mae_vs_irt_style")):
        metrics[metric] = (base_mae[name] - aggregated["mae"]) if base_ok[name] else 0.0
    best_name = max(base_u, key=lambda n: base_u[n])
    metrics["delta_score_vs_best_baseline"] = aggregated["u"] - base_u[best_name]

    # negative controls: contrast against the matched real episode
    controls_ok = True
    real_key = (plan[-1]["bench"], "random_targets", plan[-1]["seed"])
    ctrl = {}
    for i, e in enumerate(plan):
        if e["control"] is None:
            continue
        out = outcomes[i]
        if not out["complete"] or not out["valid"] or not complete_primary(outcomes, plan, real_key):
            controls_ok = False
            continue
        ctrl[e["control"]] = episode_metrics(out["pred"], episodes[real_key]["truth"])
    real_m = records[real_key]["metrics"]
    metrics["control_permuted_spearman_drop"] = (real_m["spearman"] - ctrl["permuted_targets"]["spearman"]) if "permuted_targets" in ctrl else 0.0
    metrics["control_permuted_mae_increase"] = (ctrl["permuted_targets"]["mae"] - real_m["mae"]) if "permuted_targets" in ctrl else 0.0
    metrics["control_constant_mae_delta"] = (ctrl["constant_targets"]["mae"] - real_m["mae"]) if "constant_targets" in ctrl else 0.0

    n_done = sum(1 for o in outcomes if o["complete"])
    metrics["n_completed_episodes"] = float(n_done)
    metrics["n_failed_episodes"] = float(len(plan) - n_done)
    metrics["n_candidate_rpc_calls_observed"] = float(rpc_count[0])

    boot = bootstrap_deltas(records, benches, seeds, best_name, BOOT_REPLICATES)
    for kind, label in (("mae", "delta_mae"), ("score", "delta_score")):
        for ref, ref_label in (("random_mean", "random_mean"), ("best", "best_baseline")):
            lo, hi = boot[f"{kind}_{ref}"]
            metrics[f"ci_lo_{label}_vs_{ref_label}"] = lo
            metrics[f"ci_hi_{label}_vs_{ref_label}"] = hi
    metrics["delta_score_vs_random_mean"] = aggregated["u"] - base_u["random_mean"]
    metrics["delta_mae_vs_best_baseline"] = base_mae[best_name] - aggregated["mae"]

    all_complete = complete and n_done == len(plan)
    correct = bool(all_complete and controls_ok and all(base_ok[n] for n in REQUIRED_BASELINES)
                   and all(math.isfinite(v) for v in metrics.values()))
    feasible = bool(correct and not smoke and time.monotonic() <= hard_deadline)
    correct_by_seed = {s: all(outcomes[i]["complete"] for i, e in enumerate(plan) if e["seed"] == s) and correct
                       for s in seeds}
    evidence = seed_evidence(seeds, plan, outcomes, durations, per_u, correct_by_seed)
    write_outputs(results_dir, metrics, correct, feasible, evidence)


def complete_primary(outcomes, plan, key):
    for i, e in enumerate(plan):
        if e["control"] is None and (e["bench"], e["split"], e["seed"]) == key:
            return outcomes[i]["complete"]
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        evaluate_plane(args.program_path, args.results_dir)
    except BaseException as error:
        name = type(error).__name__
        if not name.isidentifier() or not name.isascii():
            name = "EvaluatorError"
        message = ""
        print(("evaluator_exception type=%s message=%s" % (name, message))[:300], file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
