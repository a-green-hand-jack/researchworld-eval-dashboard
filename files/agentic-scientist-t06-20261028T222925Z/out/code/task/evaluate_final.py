#!/usr/bin/env python3
"""Sealed final evaluator for t06: Bradley-Terry leaderboard-stability perturbation finding (self-contained).

CLI: python <this file> --program_path <candidate entrypoint file> --results_dir <dir>

Writes exactly metrics.json (declared scalar metrics), correct.json ({"correct": bool}),
evaluation_evidence.json (schema_version 1 per-seed records) and, only when
AGENTIC_TASK_QUALIFICATION=1, qualification.json.

Scientific workload (fixed before evaluation): for every declared case (dataset, perturbation,
target) and every declared seed, the candidate perturbation finder receives the case's
comparison rows inline over python_rpc_v1:handle (reset -> load_chunk x c -> propose) and returns
row indices to drop or flip.  The evaluator re-verifies every proposal with its own float64
ridge Bradley-Terry refit and scores the verified size against evaluator-run baselines
(AMIP one-step influence, direct-pair heuristic, random).  Candidate diagnostics are ignored.
"""
import argparse
import base64
import collections
import hashlib
import hmac
import importlib.util
import json
import math
import os
import re
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "2")

import numpy as np

# === PLANE CONFIG BEGIN ===
PLANE = "final"
PRIVATE_CONSTANT = b"t06-final-sealed-private-2026-10-28-bt-leaderboard-v1"
RESOURCE_SUBDIR = ("resources", "final")
RESOURCE_SHA256 = {   'arena140k_comparisons.json': '6c0e5a535b6c8799204db38787f1380c6016137fc457e8d66c3be3d4a2b56646',
    'mtbench_gpt4_pair_judgments.json': '1ab4e514c9bfcb04607e9013fc1bf10c4388f66818576c006c8edb0583eb4f38',
    'mtbench_human_judgments.json': 'd6b0e7aa60190eff05204c853117ea95b67a7de905acf2306ad83dcc90664d7f',
    'nba_2014_2015_games.json': '531ced26de8ebd85ffc7aecf4ae5eadfcb1904b6ef06980cbaa898a1d4aa8652',
    'search_content_hashes.json': '490894445fce4049549e97983d47ac01b02d216280515ae0f6eb600d22ca6025',
    'split_manifest.json': '385d455717cf6a3946c5eeb69d775aee9499e62c738cc3e34a1b1aa4774630a5'}
DATASETS = {
    # name: (file, kind, season filter or None)
    "arena140k": ("arena140k_comparisons.json", "comparisons", None),
    "mtbench_human": ("mtbench_human_judgments.json", "comparisons", None),
    "mtbench_gpt4": ("mtbench_gpt4_pair_judgments.json", "comparisons", None),
    "nba2014": ("nba_2014_2015_games.json", "nba", 2014),
    "nba2015": ("nba_2014_2015_games.json", "nba", 2015),
}
EXPECTED_SEASONS = {"nba_2014_2015_games.json": [2014, 2015]}
SEARCH_HASH_FILE = "search_content_hashes.json"
SEEDS = [101, 102, 103]
RESET_SEQUENCE = [101] * 17 + [102] * 17 + [103] * 17
SMOKE_RESET_SEQUENCE = [101] * 3
MAX_RPC_CALLS = 312
SMOKE_MAX_RPC_CALLS = 24
WALL_CLOCK_SECONDS = 5400.0
SETUP_BASELINE_SECONDS = 900.0


def _real(case_id, family, dataset, perturbation, target, weight):
    return {"id": case_id, "kind": "real", "family": family, "dataset": dataset,
            "perturbation": perturbation, "target": target, "weight": weight}


TOP1 = {"type": "top1"}


def _triple(prefix, family, dataset, k, weight):
    return [
        _real(f"{prefix}_drop_top1", family, dataset, "drop", TOP1, weight),
        _real(f"{prefix}_flip_top1", family, dataset, "flip", TOP1, weight),
        _real(f"{prefix}_drop_top{k}", family, dataset, "drop", {"type": "topk_set", "k": k}, weight),
    ]


CASES = (
    _triple("arena140k", "arena140k", "arena140k", 5, 0.2 / 3)
    + _triple("mtbench_human", "mtbench_human", "mtbench_human", 3, 0.2 / 3)
    + _triple("mtbench_gpt4", "mtbench_gpt4", "mtbench_gpt4", 3, 0.2 / 3)
    + _triple("nba2014", "nba", "nba2014", 5, 0.2 / 6)
    + _triple("nba2015", "nba", "nba2015", 5, 0.2 / 6)
    + [
        {"id": "synthetic_drop_top1", "kind": "synthetic", "family": "synthetic", "dataset": None,
         "perturbation": "drop", "target": TOP1, "weight": 0.1},
        {"id": "perm_arena140k_drop_top1", "kind": "permutation", "family": "permutation",
         "dataset": "arena140k", "ref_case": 0, "perturbation": "drop", "target": TOP1, "weight": 0.1},
    ]
)
SMOKE_CASES = [
    dict(_real("smoke_arena140k_sub20k_drop_top1", "arena140k", "arena140k", "drop", TOP1, 0.45), subset=20000),
    _real("smoke_mtbench_human_flip_top1", "mtbench_human", "mtbench_human", "flip", TOP1, 0.45),
    {"id": "smoke_synthetic_drop_top1", "kind": "synthetic", "family": "synthetic", "dataset": None,
     "perturbation": "drop", "target": TOP1, "weight": 0.1},
]
FAMILIES = ["arena140k", "mtbench_human", "mtbench_gpt4", "nba", "synthetic", "permutation"]
FAMILY_METRIC = {"arena140k": "arena140k_score", "mtbench_human": "mtbench_human_score",
                 "mtbench_gpt4": "mtbench_gpt4_score", "nba": "nba_score",
                 "synthetic": "synthetic_control_score", "permutation": "permutation_control_score"}
RATIO_METRICS = {"mean_log2_ratio_vs_amip": "amip", "mean_log2_ratio_vs_random": "random"}
FRACTION_METRICS = {}
for _fam in ("arena140k", "mtbench_human", "mtbench_gpt4", "nba"):
    FRACTION_METRICS[f"{_fam}_top1_drop_frac"] = ("candidate", _fam, "drop")
    FRACTION_METRICS[f"{_fam}_top1_flip_frac"] = ("candidate", _fam, "flip")
    FRACTION_METRICS[f"{_fam}_top1_drop_frac_amip"] = ("amip", _fam, "drop")
METRIC_NAMES = (
    ["combined_score"] + [FAMILY_METRIC[f] for f in FAMILIES]
    + [n + s for n in RATIO_METRICS for s in ("", "_ci_low", "_ci_high")]
    + list(FRACTION_METRICS)
    + ["failed_episode_fraction", "replay_match", "final_correct", "claim_supported"]
)
# === PLANE CONFIG END ===

# ---------------------------------------------------------------- public fixed constants
WIRE_LIMIT = 64 * 1024 * 1024
DESIGN_WIRE_TARGET = 12 * 1024 * 1024
BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
MAX_CHUNK_ROWS = 524288
MAX_CHUNKS = 4
MAX_CALLS_PER_EPISODE = 1 + MAX_CHUNKS + 1
ESTIMATOR = {"model": "bradley_terry", "ties": "half", "ridge": 0.1, "tol": 1e-6}
RIDGE = ESTIMATOR["ridge"]
RANK_TOL = ESTIMATOR["tol"]
GRAD_TOL = 1e-10
MAX_NEWTON_ITERS = 200
DEGENERATE_GAP = 10.0 * RANK_TOL
MIN_PLAYER_COMPARISONS = 50
SCORE_CLIP = 4.0
RANDOM_REPEATS = 20
RANDOM_MAJORITY = 10
SYNTHETIC_MAX_K = 8
SYNTHETIC_ATTEMPTS = 64
PERMUTATION_MAX_FIXED_FRACTION = 0.01
BOOTSTRAP_REPLICATES = 2000
MAX_DIAGNOSTICS = 32
DIAGNOSTIC_NAME = re.compile(r"[A-Za-z0-9_\-][A-Za-z0-9_.\-]{0,79}")

PRODUCTION_PROFILE = {
    "startup_allowance": 150.0, "finish_reserve": 60.0, "episode_work_seconds": 55.0,
    "propose_deadline_seconds": 45.0, "reset_timeout": 10.0, "episode_overhead": 10.0,
    "rpc_cap": 55.0,
}
SMOKE_PROFILE = {
    "startup_allowance": 5.0, "finish_reserve": 8.0, "episode_work_seconds": 10.0,
    "propose_deadline_seconds": 6.0, "reset_timeout": 6.0, "episode_overhead": 3.0,
    "rpc_cap": 10.0, "wall_clock_seconds": 118.0, "setup_baseline_seconds": 25.0,
}


# ---------------------------------------------------------------- generic helpers
def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


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
        if profile is None:
            continue
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


def require_controls(expected, completed):
    if set(expected) - set(completed):
        raise ValueError("required control did not complete")


def fixed_weight_score(values, weights, worst_case):
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(w) or w < 0 for w in weights)
            or not math.isclose(sum(weights), 1.0, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("invalid predeclared aggregation weights")
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError("nonfinite contribution")
    return sum(value * weight for value, weight in zip(retained, weights))


def derive_seed(label):
    digest = hmac.new(PRIVATE_CONSTANT, label.encode("utf-8"), hashlib.sha256).digest()
    return int.from_bytes(digest[:8], "little")


def private_rng(label):
    return np.random.default_rng(derive_seed(label))


def encode_array(values, dtype):
    arr = np.ascontiguousarray(np.asarray(values, dtype=np.dtype(dtype).newbyteorder("<")))
    return {"dtype": dtype, "shape": [int(arr.shape[0])], "encoding": "base64",
            "byte_order": "little", "data": base64.b64encode(arr.tobytes()).decode("ascii")}


# ---------------------------------------------------------------- required-worker failure identity
class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


class CandidateProtocolError(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "candidate_protocol_error")
        super().__init__("candidate protocol failure")


class BudgetViolation(CandidateProtocolError):
    pass


def bounded_failure_name(value, fallback):
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
        if isinstance(context, CandidateProtocolError):
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


# ---------------------------------------------------------------- bounded stderr capture
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


def repair_diagnostics_enabled():
    return PLANE == "search" and (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
                                  or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


def search_stderr(line):
    if PLANE == "search":
        print(line[:256], file=sys.stderr, flush=True)


# ---------------------------------------------------------------- Bradley-Terry estimator
def pair_stats(p, a, b, y):
    idx = a.astype(np.int64) * p + b.astype(np.int64)
    count = np.bincount(idx, minlength=p * p).reshape(p, p).astype(np.float64)
    won = np.bincount(idx, weights=y, minlength=p * p).reshape(p, p)
    lost = np.bincount(idx, weights=1.0 - y, minlength=p * p).reshape(p, p)
    return won + lost.T, count + count.T


def bt_objective(S, theta):
    d = theta[:, None] - theta[None, :]
    return -float((S * np.logaddexp(0.0, -d)).sum()) - 0.5 * RIDGE * float(theta @ theta)


def fit_bt(S, N, theta0=None):
    """Ridge BT MLE (ties = half wins, sum-to-zero implied by the ridge); damped Newton, float64."""
    p = S.shape[0]
    theta = np.zeros(p) if theta0 is None else np.array(theta0, dtype=np.float64)
    score = S.sum(axis=1)
    value = bt_objective(S, theta)
    for _ in range(MAX_NEWTON_ITERS):
        d = theta[:, None] - theta[None, :]
        prob = 1.0 / (1.0 + np.exp(-d))
        grad = score - (N * prob).sum(axis=1) - RIDGE * theta
        if float(np.max(np.abs(grad))) < GRAD_TOL:
            return theta
        weight = N * prob * (1.0 - prob)
        hess = -weight
        hess[np.diag_indices(p)] += weight.sum(axis=1) + RIDGE
        step = np.linalg.solve(hess, grad)
        t = 1.0
        while True:
            candidate = theta + t * step
            cand_value = bt_objective(S, candidate)
            if cand_value >= value - 1e-12 * max(1.0, abs(value)) or t < 1e-10:
                break
            t *= 0.5
        theta, value = candidate, cand_value
    d = theta[:, None] - theta[None, :]
    grad = score - (N / (1.0 + np.exp(-d))).sum(axis=1) - RIDGE * theta
    if float(np.max(np.abs(grad))) < 1e-7:
        return theta
    raise RuntimeError("bt fit did not converge")


def neg_hessian(N, theta):
    p = theta.shape[0]
    d = theta[:, None] - theta[None, :]
    prob = 1.0 / (1.0 + np.exp(-d))
    weight = N * prob * (1.0 - prob)
    hess = -weight
    hess[np.diag_indices(p)] += weight.sum(axis=1) + RIDGE
    return hess


class Case:
    """Evaluator-held case: rows in candidate-visible order plus fixed reference fit."""

    def __init__(self, spec, a, b, y, extra_view=None):
        self.spec = spec
        self.a = a.astype(np.int32)
        self.b = b.astype(np.int32)
        self.y = y.astype(np.float64)
        self.n = int(a.shape[0])
        self.p = int(max(int(a.max()), int(b.max())) + 1)
        self.view = extra_view  # permutation control: candidate row i -> original row view[i]
        self.S0, self.N0 = pair_stats(self.p, self.a, self.b, self.y)
        self.theta0 = fit_bt(self.S0, self.N0)
        order = np.argsort(-self.theta0, kind="stable")
        self.order = order
        target = spec["target"]
        if target["type"] == "top1":
            self.k = 1
        else:
            self.k = int(target["k"])
        if not 1 <= self.k < self.p:
            raise RuntimeError("invalid target k")
        self.top_set = np.zeros(self.p, dtype=bool)
        self.top_set[order[:self.k]] = True
        self.leader = int(order[self.k - 1])
        self.challenger = int(order[self.k])
        self.gap = float(self.theta0[self.leader] - self.theta0[self.challenger])
        self.flippable = self.y != 0.5
        self.baseline = None
        self.baseline_failure = None
        self.self_check_ok = False
        self.k_exact = None

    def margin_changed(self, theta):
        inside = theta[self.top_set]
        outside = theta[~self.top_set]
        return bool(float(outside.max()) > float(inside.min()) + RANK_TOL)

    def perturbed_theta(self, idx):
        idx = np.asarray(idx, dtype=np.int64)
        if idx.size == 0:
            return fit_bt(self.S0, self.N0, self.theta0)
        a, b, y = self.a[idx].astype(np.int64), self.b[idx].astype(np.int64), self.y[idx]
        p = self.p
        lin = a * p + b
        if self.spec["perturbation"] == "drop":
            cnt = np.bincount(lin, minlength=p * p).reshape(p, p).astype(np.float64)
            won = np.bincount(lin, weights=y, minlength=p * p).reshape(p, p)
            lost = np.bincount(lin, weights=1.0 - y, minlength=p * p).reshape(p, p)
            S = self.S0 - won - lost.T
            N = self.N0 - cnt - cnt.T
        else:
            delta = np.bincount(lin, weights=1.0 - 2.0 * y, minlength=p * p).reshape(p, p)
            S = self.S0 + delta - delta.T
            N = self.N0
        S = np.maximum(S, 0.0)
        N = np.maximum(N, 0.0)
        return fit_bt(S, N, self.theta0)

    def verifies(self, idx):
        return self.margin_changed(self.perturbed_theta(idx))

    def eligible(self):
        if self.spec["perturbation"] == "drop":
            return np.arange(self.n, dtype=np.int64)
        return np.flatnonzero(self.flippable).astype(np.int64)


def smallest_verifying_prefix(order, check, cap, deadline):
    n = min(int(len(order)), int(cap))
    if n <= 0:
        return None
    k, last_fail = 1, 0
    while True:
        if time.monotonic() > deadline:
            raise TimeoutError("baseline deadline")
        if check(k):
            break
        last_fail = k
        if k >= n:
            return None
        k = min(2 * k, n)
    lo, hi = last_fail, k
    while hi - lo > 1:
        if time.monotonic() > deadline:
            raise TimeoutError("baseline deadline")
        mid = (lo + hi) // 2
        if check(mid):
            hi = mid
        else:
            lo = mid
    return hi


def amip_order(case):
    hess = neg_hessian(case.N0, case.theta0)
    c = np.zeros(case.p)
    c[case.leader] = 1.0
    c[case.challenger] = -1.0
    v = np.linalg.solve(hess, c)
    elig = case.eligible()
    a, b, y = case.a[elig], case.b[elig], case.y[elig]
    dv = v[a] - v[b]
    if case.spec["perturbation"] == "drop":
        resid = y - 1.0 / (1.0 + np.exp(-(case.theta0[a] - case.theta0[b])))
        delta_margin = -resid * dv
    else:
        delta_margin = (1.0 - 2.0 * y) * dv
    return elig[np.argsort(delta_margin, kind="stable")]


def heuristic_order(case):
    elig = case.eligible()
    a, b, y = case.a[elig], case.b[elig], case.y[elig]
    lead = case.leader
    win_a = (a == lead) & (y == 1.0)
    win_b = (b == lead) & (y == 0.0)
    wins = win_a | win_b
    opponent = np.where(a == lead, b, a)
    first = elig[wins & (opponent == case.challenger)]
    rest_mask = wins & (opponent != case.challenger)
    rest = elig[rest_mask]
    rest_strength = case.theta0[opponent[rest_mask]]
    rest = rest[np.lexsort((rest, -rest_strength))]
    return np.concatenate([np.sort(first), rest])


def random_k(case, deadline):
    elig = case.eligible()
    cap = len(elig) // 2

    def check(k):
        rng = private_rng(f"random-baseline:{case.spec['id']}:{k}")
        hits = 0
        for r in range(RANDOM_REPEATS):
            pick = rng.choice(elig, size=k, replace=False)
            if case.verifies(pick):
                hits += 1
            if hits >= RANDOM_MAJORITY or hits + (RANDOM_REPEATS - r - 1) < RANDOM_MAJORITY:
                break
        return hits >= RANDOM_MAJORITY

    return smallest_verifying_prefix(elig, check, cap, deadline)


def run_baselines(case, deadline):
    censored = case.n + 1
    amip = amip_order(case)
    k_amip = smallest_verifying_prefix(amip, lambda k: case.verifies(amip[:k]), len(amip), deadline)
    heur = heuristic_order(case)
    k_heur = smallest_verifying_prefix(heur, lambda k: case.verifies(heur[:k]), len(heur), deadline)
    k_rand = random_k(case, deadline)
    out = {"amip": censored if k_amip is None else k_amip,
           "heuristic": censored if k_heur is None else k_heur,
           "random": censored if k_rand is None else k_rand}
    out["ref"] = min(out["amip"], out["heuristic"])
    return out


def self_check(case):
    """Null control (empty perturbation keeps target), copy control (independent refit), gap."""
    if case.gap <= DEGENERATE_GAP:
        return False
    if case.verifies(np.zeros(0, dtype=np.int64)):
        return False
    rev = np.arange(case.n)[::-1]
    S, N = pair_stats(case.p, case.a[rev], case.b[rev], case.y[rev])
    theta = fit_bt(S, N)
    if not np.array_equal(np.argsort(-theta, kind="stable")[:case.k + 1], case.order[:case.k + 1]):
        return False
    return bool(float(np.max(np.abs(theta - case.theta0))) < 1e-7)


# ---------------------------------------------------------------- synthetic planted control
def synthetic_rows(rng):
    pairs = [(0, 1), (0, 2), (1, 2)]
    a, b, y = [], [], []
    for i, j in pairs:
        n = int(rng.integers(50, 81))
        if (i, j) == (0, 1):
            wins = n // 2 + int(rng.integers(1, 4))
        else:
            wins = int(round(n * float(rng.uniform(0.55, 0.70))))
        for t in range(n):
            a.append(i); b.append(j); y.append(1.0 if t < wins else 0.0)
    return np.array(a), np.array(b), np.array(y)


def brute_force_min_drop(case, max_k, deadline):
    """Exact minimal drop size by enumerating per-(pair, winner) class counts (BT depends only on them)."""
    classes = []
    for i in range(case.p):
        for j in range(i + 1, case.p):
            for winner in (i, j):
                rows = np.flatnonzero(((case.a == i) & (case.b == j) & (case.y == (1.0 if winner == i else 0.0)))
                                      | ((case.a == j) & (case.b == i) & (case.y == (1.0 if winner == j else 0.0))))
                if rows.size:
                    classes.append(np.sort(rows))
    caps = [len(c) for c in classes]

    def compositions(total, start):
        if start == len(classes) - 1:
            if total <= caps[start]:
                yield (total,)
            return
        for take in range(min(total, caps[start]) + 1):
            for rest in compositions(total - take, start + 1):
                yield (take,) + rest

    for total in range(1, max_k + 1):
        for comp in compositions(total, 0):
            if time.monotonic() > deadline:
                raise TimeoutError("synthetic brute force deadline")
            idx = np.concatenate([classes[c][:t] for c, t in enumerate(comp) if t] or [np.zeros(0, np.int64)])
            if case.verifies(idx):
                return total
    return None


def build_synthetic(spec, deadline):
    for attempt in range(SYNTHETIC_ATTEMPTS):
        rng = private_rng(f"synthetic:{spec['id']}:{attempt}")
        a, b, y = synthetic_rows(rng)
        perm_players = rng.permutation(3)
        order = rng.permutation(a.shape[0])
        a, b, y = perm_players[a][order], perm_players[b][order], y[order]
        try:
            case = Case(spec, a, b, y)
        except RuntimeError:
            continue
        if case.gap <= DEGENERATE_GAP:
            continue
        k_exact = brute_force_min_drop(case, SYNTHETIC_MAX_K, deadline)
        if k_exact is not None and k_exact >= 2:
            case.k_exact = int(k_exact)
            return case
    return None


# ---------------------------------------------------------------- resources and split integrity
def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, *RESOURCE_SUBDIR)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def nba_key(game_id, date, ta, pa, tb, pb):
    lo, hi = sorted([(ta, pa), (tb, pb)])
    text = f"nba|{game_id}|{date}|{lo[0]}:{lo[1]}|{hi[0]}:{hi[1]}"
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


HEX64 = re.compile(r"[0-9a-f]{64}")


def load_resources(root):
    integrity = {"ok": True, "residual_overlap": 0, "excluded": 0}
    for name, digest in RESOURCE_SHA256.items():
        path = os.path.join(root, name)
        if os.path.islink(path) or not os.path.isfile(path) or sha256_file(path) != digest:
            raise RuntimeError("resource checksum mismatch")
    with open(os.path.join(root, "split_manifest.json"), encoding="utf-8") as f:
        manifest = json.load(f)
    if (manifest.get("plane") != PLANE or manifest.get("cross_plane_residual_content_overlap") != 0
            or manifest.get("cross_plane_source_id_overlap") != 0):
        integrity["ok"] = False
    search_hashes = None
    if SEARCH_HASH_FILE is not None:
        with open(os.path.join(root, SEARCH_HASH_FILE), encoding="utf-8") as f:
            search_hashes = set(json.load(f)["content_sha256"])
    raw = {}
    for fname in sorted({spec[0] for spec in DATASETS.values()}):
        with open(os.path.join(root, fname), encoding="utf-8") as f:
            data = json.load(f)
        n = len(data["outcome2"])
        cols = ["player_a", "player_b", "outcome2", "row_id", "content_sha256"]
        if any(len(data[c]) != n for c in cols):
            raise RuntimeError("resource column length mismatch")
        hashes = data["content_sha256"]
        if not all(isinstance(h, str) and HEX64.fullmatch(h) for h in hashes):
            raise RuntimeError("resource content hash malformed")
        if "season" in data:
            for i in range(n):
                if nba_key(data["row_id"][i], data["date"][i], data["team_a"][i], data["pts_a"][i],
                           data["team_b"][i], data["pts_b"][i]) != hashes[i]:
                    integrity["ok"] = False
                    break
            if sorted(set(data["season"])) != EXPECTED_SEASONS.get(fname):
                integrity["ok"] = False
        keep = np.ones(n, dtype=bool)
        if search_hashes is not None:
            overlap = np.array([h in search_hashes for h in hashes], dtype=bool)
            integrity["excluded"] += int(overlap.sum())
            keep &= ~overlap
            residual = sum(1 for h, k in zip(hashes, keep) if k and h in search_hashes)
            integrity["residual_overlap"] += residual
        y2 = np.array(data["outcome2"], dtype=np.int64)
        if not np.isin(y2, [0, 1, 2]).all():
            raise RuntimeError("resource outcome malformed")
        raw[fname] = {
            "a": np.array(data["player_a"], dtype=np.int64)[keep],
            "b": np.array(data["player_b"], dtype=np.int64)[keep],
            "y": (y2 / 2.0)[keep],
            "season": np.array(data["season"], dtype=np.int64)[keep] if "season" in data else None,
        }
    if integrity["residual_overlap"] != 0:
        integrity["ok"] = False
    return raw, integrity


def filter_min_comparisons(a, b):
    keep = np.ones(a.shape[0], dtype=bool)
    size = int(max(a.max(), b.max())) + 1
    while True:
        cnt = np.bincount(np.concatenate([a[keep], b[keep]]), minlength=size)
        good = cnt >= MIN_PLAYER_COMPARISONS
        new_keep = keep & good[a] & good[b]
        if int(new_keep.sum()) == int(keep.sum()):
            return keep
        keep = new_keep


def dataset_rows(raw, name, subset=None):
    fname, _kind, season = DATASETS[name]
    data = raw[fname]
    a, b, y = data["a"], data["b"], data["y"]
    if season is not None:
        m = data["season"] == season
        a, b, y = a[m], b[m], y[m]
    order = private_rng(f"rows:{name}").permutation(a.shape[0])
    a, b, y = a[order], b[order], y[order]
    if subset is not None:
        a, b, y = a[:subset], b[:subset], y[:subset]
    keep = filter_min_comparisons(a, b)
    a, b, y = a[keep], b[keep], y[keep]
    players, inverse = np.unique(np.concatenate([a, b]), return_inverse=True)
    relabel = private_rng(f"players:{name}:{subset}").permutation(players.shape[0])
    a2 = relabel[inverse[:a.shape[0]]]
    b2 = relabel[inverse[a.shape[0]:]]
    return a2, b2, y


def control_permutation(n, label):
    for attempt in range(16):
        perm = private_rng(f"perm:{label}:{attempt}").permutation(n)
        fixed = int((perm == np.arange(n)).sum())
        if n > 1 and fixed < n and fixed <= PERMUTATION_MAX_FIXED_FRACTION * n:
            return perm
    return None


# ---------------------------------------------------------------- candidate transports
NATIVE_RUNNER = r"""
import importlib.util, json, os, sys
proto = os.fdopen(os.dup(1), "w", encoding="utf-8")
os.dup2(2, 1)
sys.stdout = sys.stderr
path = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
spec = importlib.util.spec_from_file_location("candidate_program", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
handle = module.handle
while True:
    line = sys.stdin.readline()
    if not line:
        break
    try:
        out = json.dumps(handle(json.loads(line)), allow_nan=False, separators=(",", ":"))
    except Exception as error:
        out = json.dumps({"__runner_error__": type(error).__name__[:80]})
    proto.write(out + "\n")
    proto.flush()
"""


def candidate_subprocess_settings(parent_environment):
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


def _reject_constant(_token):
    raise ValueError("nonfinite JSON constant")


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess; restarted at every reset."""

    def __init__(self, program_path, cpu_seconds):
        self.program_path = os.path.abspath(program_path)
        self.cpu_seconds = cpu_seconds
        self.proc = None
        self.stderr = None
        self.workdir = tempfile.mkdtemp(prefix="t06-candidate-")
        self.last_stderr = None

    def _limits(self):
        import resource
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_seconds, self.cpu_seconds + 5))
        resource.setrlimit(resource.RLIMIT_AS, (4 * 1024 ** 3, 4 * 1024 ** 3))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    def start(self):
        self.stop()
        interpreter, env = candidate_subprocess_settings(os.environ)
        self.proc = subprocess.Popen(
            [interpreter, "-I", "-B", "-c", NATIVE_RUNNER, self.program_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.workdir, env=env, shell=False, start_new_session=True,
            preexec_fn=self._limits, close_fds=True)
        self.stderr = BoundedWorkerStderr(self.proc.stderr)
        self.buffer = bytearray()
        os.set_blocking(self.proc.stdout.fileno(), False)

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        for sig, wait in ((signal.SIGTERM, 1.0), (signal.SIGKILL, 1.0)):
            if proc.poll() is not None:
                break
            try:
                os.killpg(proc.pid, sig)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.wait(timeout=wait)
            except subprocess.TimeoutExpired:
                pass
        for stream in (proc.stdin, proc.stdout):
            try:
                stream.close()
            except Exception:
                pass
        if self.stderr is not None:
            try:
                self.last_stderr = self.stderr.close()
            except RuntimeError:
                self.last_stderr = None
            self.stderr = None

    def __call__(self, request, timeout):
        deadline = time.monotonic() + timeout
        if request.get("op") == "reset":
            self.start()
        if self.proc is None or self.proc.poll() is not None:
            raise CandidateProtocolError("candidate_exited")
        line = bounded_json_line(request)
        try:
            self.proc.stdin.write(line)
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            self.stop()
            raise CandidateProtocolError("candidate_exited")
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as sel:
            sel.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.stop()
                    raise TimeoutError("candidate rpc timeout")
                if not sel.select(timeout=min(remaining, 0.5)):
                    if self.proc.poll() is not None:
                        self.stop()
                        raise CandidateProtocolError("candidate_exited")
                    continue
                try:
                    chunk = os.read(fd, 1 << 20)
                except BlockingIOError:
                    continue
                if not chunk:
                    self.stop()
                    raise CandidateProtocolError("candidate_exited")
                self.buffer.extend(chunk)
                if len(self.buffer) >= WIRE_LIMIT:
                    self.stop()
                    raise BudgetViolation("wire_limit_exceeded")
        pos = self.buffer.index(b"\n")
        raw, self.buffer = bytes(self.buffer[:pos + 1]), self.buffer[pos + 1:]
        if len(raw) >= WIRE_LIMIT:
            raise BudgetViolation("wire_limit_exceeded")
        try:
            response = json.loads(raw, parse_constant=_reject_constant)
        except ValueError:
            raise CandidateProtocolError("malformed_response")
        if isinstance(response, dict) and "__runner_error__" in response:
            raise CandidateProtocolError("candidate_exception")
        return response

    def close(self):
        self.stop()
        try:
            os.rmdir(self.workdir)
        except OSError:
            pass


class ProxyCandidate:
    """Trusted harness proxy loaded in-process; calls bounded by a daemon worker thread."""

    def __init__(self, path):
        spec = importlib.util.spec_from_file_location("candidate_proxy", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.last_stderr = None

    def __call__(self, request, timeout):
        bounded_json_line(request)
        box = {}
        done = threading.Event()

        def run():
            try:
                box["value"] = self.handle(request)
            except BaseException as error:  # noqa: BLE001 - proxy failure is a candidate failure
                box["error"] = error
            finally:
                done.set()

        threading.Thread(target=run, name="candidate-rpc", daemon=True).start()
        if not done.wait(timeout):
            raise TimeoutError("candidate rpc timeout")
        if "error" in box:
            raise CandidateProtocolError("candidate_exception")
        response = box.get("value")
        try:
            bounded_json_line(response)
        except ValueError:
            raise BudgetViolation("wire_limit_exceeded")
        except TypeError:
            raise CandidateProtocolError("malformed_response")
        return json.loads(json.dumps(response, allow_nan=False))

    def close(self):
        pass


class Transport:
    """Counts every RPC against the declared budget and records the broker-visible reset transcript."""

    def __init__(self, backend, max_calls):
        self.backend = backend
        self.max_calls = max_calls
        self.calls = 0
        self.resets = []
        self.violation = False
        self.max_request_bytes = 0

    def __call__(self, request, timeout):
        if self.calls >= self.max_calls:
            self.violation = True
            raise BudgetViolation("rpc_budget_exceeded")
        size = len(bounded_json_line(request))
        self.max_request_bytes = max(self.max_request_bytes, size)
        self.calls += 1
        if request.get("op") == "reset":
            self.resets.append(request["seed"])
        try:
            return self.backend(request, timeout)
        except BudgetViolation:
            self.violation = True
            raise


def make_backend(program_path, cpu_seconds):
    socket_signal = os.environ.get("AGENTIC_CANDIDATE_SOCKET")
    if socket_signal or program_path == BROKER_PROXY_PATH:
        if not socket_signal or program_path != BROKER_PROXY_PATH:
            raise RuntimeError("brokered mode requires both the proxy path and the socket signal")
        return ProxyCandidate(BROKER_PROXY_PATH)
    return NativeCandidate(program_path, cpu_seconds)


# ---------------------------------------------------------------- candidate response validation
def decode_indices(response, case, max_size):
    if type(response) is not dict or "indices" not in response or not set(response) <= {"indices", "diagnostics"}:
        raise CandidateProtocolError("malformed_response")
    if "diagnostics" in response:
        diag = response["diagnostics"]
        if (type(diag) is not dict or len(diag) > MAX_DIAGNOSTICS
                or any(not isinstance(k, str) or not DIAGNOSTIC_NAME.fullmatch(k)
                       or type(v) not in (int, float) or not math.isfinite(v) for k, v in diag.items())):
            raise CandidateProtocolError("malformed_response")
    arr = response["indices"]
    if (type(arr) is not dict or set(arr) != {"dtype", "shape", "encoding", "byte_order", "data"}
            or arr["dtype"] != "int32" or arr["encoding"] != "base64" or arr["byte_order"] != "little"
            or type(arr["shape"]) is not list or len(arr["shape"]) != 1 or type(arr["shape"][0]) is not int
            or not isinstance(arr["data"], str)):
        raise CandidateProtocolError("malformed_response")
    try:
        blob = base64.b64decode(arr["data"].encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError):
        raise CandidateProtocolError("malformed_response")
    if len(blob) != 4 * arr["shape"][0]:
        raise CandidateProtocolError("malformed_response")
    idx = np.frombuffer(blob, dtype="<i4").astype(np.int64)
    if idx.size > max_size or (idx.size and (idx[0] < 0 or idx[-1] >= case.n)):
        raise CandidateProtocolError("malformed_indices")
    if idx.size > 1 and not bool(np.all(np.diff(idx) > 0)):
        raise CandidateProtocolError("malformed_indices")
    if case.view is not None:
        idx = np.sort(case.view[idx])
    if case.spec["perturbation"] == "flip" and idx.size and not bool(case.flippable[idx].all()):
        raise CandidateProtocolError("malformed_indices")
    return idx


def candidate_rows(case):
    if case.view is None:
        return case.a, case.b, case.y
    return case.a[case.view], case.b[case.view], case.y[case.view]


def make_episode_evaluator(cases, profile):
    def evaluate(episode, call, work_deadline):
        case = cases[episode["case"]]
        if case is None:
            raise RequiredBaselineFailure("case_setup_failure")
        if case.baseline_failure is not None:
            raise RequiredBaselineFailure(case.baseline_failure)
        a, b, y = candidate_rows(case)
        n_chunks = max(1, math.ceil(case.n / MAX_CHUNK_ROWS))
        token = hmac.new(PRIVATE_CONSTANT, f"token:{case.spec['id']}".encode(), hashlib.sha256).hexdigest()[:24]
        for chunk in range(n_chunks):
            lo, hi = chunk * MAX_CHUNK_ROWS, min(case.n, (chunk + 1) * MAX_CHUNK_ROWS)
            ack = call({"op": "load_chunk", "case_token": token, "chunk_index": chunk, "n_chunks": n_chunks,
                        "row_offset": lo, "n_rows_total": case.n, "n_players": case.p,
                        "player_a": encode_array(a[lo:hi], "int32"),
                        "player_b": encode_array(b[lo:hi], "int32"),
                        "outcome": encode_array(y[lo:hi], "float32")})
            if type(ack) is not dict or set(ack) != {"ok"} or ack["ok"] is not True:
                raise CandidateProtocolError("malformed_response")
        response = call({"op": "propose", "perturbation": case.spec["perturbation"],
                         "target": dict(case.spec["target"]), "estimator": dict(ESTIMATOR),
                         "max_size": case.n, "deadline_seconds": profile["propose_deadline_seconds"]})
        idx = decode_indices(response, case, case.n)
        if time.monotonic() > work_deadline:
            raise TimeoutError("episode work deadline")
        try:
            verified = bool(idx.size > 0 and case.verifies(idx))
        except RuntimeError:
            verified = False
        digest = hashlib.sha256(idx.astype("<i8").tobytes()).hexdigest()
        return {"status": "ok", "verified": verified, "k": int(idx.size), "digest": digest}
    return evaluate


def worst_case_record(_episode):
    return {"status": "failed", "verified": False, "k": None, "digest": None}


# ---------------------------------------------------------------- scheduler
def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
    episode_work_seconds, rpc_cap, clock, rpc, evaluate, worst_case, record_failure,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    durations = [0.0 for _ in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    for index, episode in enumerate(episodes):
        started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = min(episode_deadline - episode_overhead, started + episode_work_seconds)

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
            if not isinstance(error, (CandidateProtocolError, RequiredBaselineFailure)):
                complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            outcomes[index] = dict(worst_case(episode), status=(
                "malformed" if failure["category"].startswith("malformed") else "failed"),
                category=failure["category"])
            try:
                record_failure(index, episode, failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
        durations[index] = max(0.0, clock() - started)
    return outcomes, durations, complete


# ---------------------------------------------------------------- scoring
def clip(value, lo, hi):
    return float(min(hi, max(lo, value)))


def episode_score(case, record, records_by_key, episode):
    if case is None:
        return -SCORE_CLIP
    kind = case.spec["kind"]
    if record["status"] != "ok" or not record["verified"]:
        return -SCORE_CLIP
    k = record["k"]
    if kind == "real":
        if case.baseline is None:
            return -SCORE_CLIP
        return clip(math.log2(case.baseline["ref"] / k), -SCORE_CLIP, SCORE_CLIP)
    if kind == "synthetic":
        return clip(math.log2(case.k_exact / k), -SCORE_CLIP, 0.0)
    ref = records_by_key.get((case.spec["ref_case"], episode["seed"]))
    if ref is None or ref["status"] != "ok" or not ref["verified"]:
        return -SCORE_CLIP
    return -min(SCORE_CLIP, abs(math.log2(k / ref["k"])))


def episode_fraction(case, record):
    if case is None or record["status"] != "ok" or not record["verified"]:
        return 1.0
    return min(1.0, record["k"] / case.n)


def baseline_fraction(case, name):
    if case is None or case.baseline is None:
        return 1.0
    return min(1.0, case.baseline[name] / case.n)


def percentile_ci(values, label):
    values = np.asarray(values, dtype=np.float64)
    rng = private_rng(label)
    draws = rng.integers(0, values.size, size=(BOOTSTRAP_REPLICATES, values.size))
    means = values[draws].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def write_json(path, value):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(value, f, allow_nan=False, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    os.replace(tmp, path)


def worst_case_metrics():
    out = {}
    for name in METRIC_NAMES:
        if name.endswith("_frac") or "_frac_" in name or name == "failed_episode_fraction":
            out[name] = 1.0
        elif name in ("replay_match", "final_correct", "claim_supported"):
            out[name] = 0.0
        else:
            out[name] = -SCORE_CLIP
    return out


def write_results(results_dir, metrics, correct, qualification, evidence):
    if set(metrics) != set(METRIC_NAMES) or not all(
            type(v) is float and math.isfinite(v) for v in metrics.values()):
        raise RuntimeError("metric schema violation")
    write_json(os.path.join(results_dir, "metrics.json"), metrics)
    write_json(os.path.join(results_dir, "correct.json"), {"correct": bool(correct)})
    if evidence is not None:
        write_json(os.path.join(results_dir, "evaluation_evidence.json"), evidence)
    if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
        write_json(os.path.join(results_dir, "qualification.json"),
                   {"schema_version": 1, "feasible": bool(qualification)})


# ---------------------------------------------------------------- main evaluation
def evaluate_plane(program_path, results_dir, started):
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    profile = dict(PRODUCTION_PROFILE)
    if smoke:
        profile.update(SMOKE_PROFILE)
        wall = SMOKE_PROFILE["wall_clock_seconds"]
        setup_seconds = SMOKE_PROFILE["setup_baseline_seconds"]
        specs, sequence, max_calls = SMOKE_CASES, SMOKE_RESET_SEQUENCE, SMOKE_MAX_RPC_CALLS
    else:
        wall, setup_seconds = WALL_CLOCK_SECONDS, SETUP_BASELINE_SECONDS
        specs, sequence, max_calls = CASES, RESET_SEQUENCE, MAX_RPC_CALLS
    hard_deadline = started + wall - profile["startup_allowance"]
    setup_deadline = started + setup_seconds
    if not math.isclose(sum(s["weight"] for s in specs), 1.0, abs_tol=1e-12):
        raise RuntimeError("invalid predeclared weights")

    # Episode plan: seed-major over the fixed case order, then one trailing replay of case 0.
    seeds_in_order = list(dict.fromkeys(sequence))
    episodes = []
    for seed in seeds_in_order:
        for ci in range(len(specs)):
            episodes.append({"case": ci, "seed": seed, "replay": False})
    if [e["seed"] for e in episodes] != list(sequence):
        raise RuntimeError("episode plan does not match the declared reset sequence")
    episodes.append({"case": 0, "seed": sequence[0], "replay": True})
    expected_resets = list(sequence) + [sequence[0]]
    if len(episodes) * MAX_CALLS_PER_EPISODE > max_calls:
        raise RuntimeError("declared RPC budget does not cover the episode plan")
    require_joint_workload_budget(**{PLANE: {
        "episode_count": len(episodes), "method_count": 1, "wall_seconds": wall,
        "startup_seconds": profile["startup_allowance"] + setup_seconds,
        "reset_seconds": profile["reset_timeout"], "cleanup_seconds": profile["episode_overhead"],
        "finish_seconds": profile["finish_reserve"], "work_seconds": profile["episode_work_seconds"]},
        ("final" if PLANE == "search" else "search"): None})

    # Setup: resources, split integrity, cases, self-checks, baselines (before any candidate work).
    raw, integrity = load_resources(resource_root())
    cases = []
    controls_nonvacuous = True
    self_checks_ok = True
    feasible = True
    for spec in specs:
        if time.monotonic() > setup_deadline:
            feasible = False
        case = None
        try:
            if spec["kind"] == "real":
                a, b, y = dataset_rows(raw, spec["dataset"], spec.get("subset"))
                case = Case(spec, a, b, y)
            elif spec["kind"] == "synthetic":
                case = build_synthetic(spec, setup_deadline)
                if case is None:
                    controls_nonvacuous = False
            else:
                ref = cases[spec["ref_case"]]
                perm = None if ref is None else control_permutation(ref.n, spec["id"])
                if perm is None:
                    controls_nonvacuous = False
                else:
                    case = Case(spec, ref.a, ref.b, ref.y, extra_view=perm)
        except TimeoutError:
            feasible = False
            case = None
        if case is None:
            self_checks_ok = False
            cases.append(None)
            continue
        case.self_check_ok = self_check(case)
        if not case.self_check_ok:
            self_checks_ok = False
        if spec["kind"] == "real":
            try:
                if time.monotonic() > setup_deadline:
                    raise TimeoutError("baseline allowance exhausted")
                case.baseline = run_baselines(case, setup_deadline)
            except TimeoutError:
                case.baseline_failure = "baseline_timeout"
                feasible = False
            except (RuntimeError, np.linalg.LinAlgError):
                case.baseline_failure = "baseline_result_failure"
            if case.baseline_failure is not None:
                search_stderr(f"baseline_failure case={spec['id']} component=baseline "
                              f"category={case.baseline_failure} operation=baseline_worker")
        cases.append(case)
        if case.view is not None or spec["kind"] == "real":
            a_v, b_v, y_v = candidate_rows(case)
            probe = {"op": "load_chunk", "case_token": "x" * 24, "chunk_index": 0, "n_chunks": 1,
                     "row_offset": 0, "n_rows_total": case.n, "n_players": case.p,
                     "player_a": encode_array(a_v[:MAX_CHUNK_ROWS], "int32"),
                     "player_b": encode_array(b_v[:MAX_CHUNK_ROWS], "int32"),
                     "outcome": encode_array(y_v[:MAX_CHUNK_ROWS], "float32")}
            reply = {"indices": encode_array(np.arange(case.n), "int32"),
                     "diagnostics": {f"d{i:02d}": -1.0e300 for i in range(MAX_DIAGNOSTICS)}}
            for message in (probe, reply):
                if len(bounded_json_line(message)) >= DESIGN_WIRE_TARGET:
                    raise RuntimeError("wire preflight exceeds the design target")
            if math.ceil(case.n / MAX_CHUNK_ROWS) > MAX_CHUNKS:
                raise RuntimeError("case exceeds the declared chunk bound")

    cpu_seconds = cpu_limit_seconds(profile["reset_timeout"] + profile["episode_work_seconds"]
                                    + profile["episode_overhead"], 2)
    backend = make_backend(program_path, cpu_seconds)
    transport = Transport(backend, max_calls)
    failures = []

    def record_failure(index, episode, failure):
        failures.append(failure)
        spec = specs[episode["case"]]
        search_stderr(f"episode_failure index={index} case={spec['id']} seed={episode['seed']} "
                      f"component={failure['component']} category={failure['category']} "
                      f"operation={failure['operation']}")

    try:
        records, durations, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=profile["finish_reserve"],
            reset_timeout=profile["reset_timeout"], episode_overhead=profile["episode_overhead"],
            episode_work_seconds=profile["episode_work_seconds"], rpc_cap=profile["rpc_cap"],
            clock=time.monotonic, rpc=transport, evaluate=make_episode_evaluator(cases, profile),
            worst_case=worst_case_record, record_failure=record_failure)
    finally:
        if failures and repair_diagnostics_enabled() and getattr(backend, "last_stderr", None):
            sys.stderr.write(backend.last_stderr["stderr"][-4096:])
        backend.close()
    if not complete:
        feasible = False

    # Aggregation hierarchy: seed mean per case (equal weights) -> fixed case weights -> plane score.
    primary = [(e, r) for e, r in zip(episodes, records) if not e["replay"]]
    by_key = {(e["case"], e["seed"]): r for e, r in primary}
    case_scores, case_fracs = [], []
    for ci, spec in enumerate(specs):
        vals, fracs = [], []
        for seed in seeds_in_order:
            ep = {"case": ci, "seed": seed}
            vals.append(episode_score(cases[ci], by_key[(ci, seed)], by_key, ep))
            fracs.append(episode_fraction(cases[ci], by_key[(ci, seed)]))
        case_scores.append(float(np.mean(vals)))
        case_fracs.append(float(np.mean(fracs)))
    combined = fixed_weight_score(case_scores, [s["weight"] for s in specs], -SCORE_CLIP)
    metrics = {"combined_score": float(combined)}
    for fam in FAMILIES:
        members = [ci for ci, s in enumerate(specs) if s["family"] == fam]
        if not members:
            metrics[FAMILY_METRIC[fam]] = -SCORE_CLIP
            continue
        w = sum(specs[ci]["weight"] for ci in members)
        metrics[FAMILY_METRIC[fam]] = float(sum(specs[ci]["weight"] * case_scores[ci] for ci in members) / w)
    failed = sum(1 for _e, r in primary if r["status"] != "ok")
    metrics["failed_episode_fraction"] = float(failed / len(primary))
    replay = records[-1]
    first = by_key[(0, sequence[0])]
    replay_match = (replay["status"] == "ok" and first["status"] == "ok"
                    and replay["digest"] == first["digest"] and replay["verified"] == first["verified"])
    metrics["replay_match"] = 1.0 if replay_match else 0.0
    for name, (source, fam, pert) in FRACTION_METRICS.items():
        members = [ci for ci, s in enumerate(specs) if s["kind"] == "real" and s["family"] == fam
                   and s["perturbation"] == pert and s["target"]["type"] == "top1"]
        if not members:
            metrics[name] = 1.0
        elif source == "candidate":
            metrics[name] = float(np.mean([case_fracs[ci] for ci in members]))
        else:
            metrics[name] = float(np.mean([baseline_fraction(cases[ci], source) for ci in members]))

    malformed = any(r["status"] == "malformed" for r in records)
    gates = {
        "a_self_checks": self_checks_ok and controls_nonvacuous,
        "b_transcript": transport.resets == expected_resets,
        "c_accounted": len(records) == len(episodes),
        "d_wellformed": not malformed,
        "e_replay": replay_match,
        "f_budget": (not transport.violation) and transport.calls <= max_calls,
        "g_split": bool(integrity["ok"]),
    }
    correct = all(gates.values())
    if PLANE == "final":
        real = [ci for ci, s in enumerate(specs) if s["kind"] == "real"]
        for name, source in RATIO_METRICS.items():
            per_case = []
            for ci in real:
                vals = []
                for seed in seeds_in_order:
                    r = by_key[(ci, seed)]
                    c = cases[ci]
                    if c is None or c.baseline is None or r["status"] != "ok" or not r["verified"]:
                        vals.append(-SCORE_CLIP)
                    else:
                        vals.append(clip(math.log2(c.baseline[source] / r["k"]), -SCORE_CLIP, SCORE_CLIP))
                per_case.append(float(np.mean(vals)))
            metrics[name] = float(np.mean(per_case))
            lo, hi = percentile_ci(per_case, f"bootstrap:{name}")
            metrics[name + "_ci_low"] = lo
            metrics[name + "_ci_high"] = hi
        metrics["final_correct"] = 1.0 if correct else 0.0
        metrics["claim_supported"] = 1.0 if (correct and metrics["mean_log2_ratio_vs_amip_ci_low"] > 0) else 0.0

    # Per-seed evidence (replay folded into its seed; predeclared case weights; failures retained).
    evidence_records = []
    for seed in seeds_in_order:
        idxs = [i for i, e in enumerate(episodes) if e["seed"] == seed]
        seed_scores = [episode_score(cases[ci], by_key[(ci, seed)], by_key, {"case": ci, "seed": seed})
                       for ci in range(len(specs))]
        seed_score = fixed_weight_score(seed_scores, [s["weight"] for s in specs], -SCORE_CLIP)
        seed_ok = correct and all(records[i]["status"] == "ok" for i in idxs)
        solution = {specs[ci]["id"]: (by_key[(ci, seed)]["k"] if by_key[(ci, seed)]["verified"] else None)
                    for ci in range(len(specs))}
        evidence_records.append({"seed": int(seed), "score": float(seed_score), "correct": bool(seed_ok),
                                 "duration_seconds": float(sum(durations[i] for i in idxs)),
                                 "solution": {"verified_k": solution}})
    evidence = {"schema_version": 1, "episodes": evidence_records}
    qualification = feasible and not smoke and time.monotonic() <= hard_deadline
    if PLANE == "search" and not correct:
        search_stderr("search_gates " + " ".join(f"{k}={'pass' if v else 'fail'}" for k, v in gates.items()))
    write_results(results_dir, {k: float(metrics[k]) for k in METRIC_NAMES}, correct, qualification, evidence)


def main(argv=None):
    started = time.monotonic()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args(argv)
    os.makedirs(args.results_dir, exist_ok=True)
    try:
        evaluate_plane(args.program_path, args.results_dir, started)
    except Exception as error:  # noqa: BLE001
        name = type(error).__name__
        if not name.isascii() or not name.isidentifier() or len(name) > 80:
            name = "EvaluatorException"
        line = f"evaluator_error category=evaluator_exception type={name}"
        if repair_diagnostics_enabled():
            try:
                message = str(error)
            except Exception:  # noqa: BLE001
                message = "<exception message unavailable>"
            if len(message) > 200 or len(message.encode("utf-8", errors="replace")) > 200:
                message = "<exception message omitted: too large>"
            line += f" message={message}"
        print(line, file=sys.stderr, flush=True)
        try:
            write_results(args.results_dir, worst_case_metrics(), False, False, None)
        except Exception:
            pass
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
