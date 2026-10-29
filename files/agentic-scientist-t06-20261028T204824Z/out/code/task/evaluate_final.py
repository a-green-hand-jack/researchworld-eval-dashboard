#!/usr/bin/env python3
"""Sealed final evaluator: Bradley-Terry leaderboard sensitivity on held-out data families.

Self-contained trusted evaluator reading only the final resource root.  Same trusted refit,
scoring hierarchy and output files as the search evaluator, over sealed final cases and seeds.
"""
import argparse
import base64
import collections
import csv
import hashlib
import importlib.util
import json
import math
import os
import re
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np

_T0 = time.monotonic()

# ----------------------------------------------------------------------------------------
# Constants shared by the protocol (identical in smoke, search and final).
# ----------------------------------------------------------------------------------------
WIRE_LIMIT = 64 * 1024 * 1024
BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
LADDER = ((1, 1000), (1, 400), (1, 200), (1, 100), (1, 50))  # 0.1%, 0.25%, 0.5%, 1%, 2%
N_LEVELS = len(LADDER)
RIDGE = 1e-3
BT_TOL = 1e-10
BT_MAXIT = 100
RANDOM_DRAWS = 20
CROSSCHECK_TOL = 1e-5
STARTUP_ALLOWANCE = 120.0
FINISH_RESERVE = 60.0
RESET_TIMEOUT = 30.0
RPC_CAP = 30.0
TERM_WAIT = 1.0
KILL_WAIT = 1.0
STDERR_CLOSE_WAIT = 1.0
BOOKKEEPING = 2.0
EPISODE_OVERHEAD = TERM_WAIT + KILL_WAIT + STDERR_CLOSE_WAIT + BOOKKEEPING  # 5 s
CANDIDATE_THREADS = 2
TARGET_TEXT = ("make the competitor ranked first by the evaluator Bradley-Terry fit on the "
               "unedited data lose rank 1 after the edits")
MODES = ("drop", "flip")


# ----------------------------------------------------------------------------------------
# Failure-identity helpers (copied from the shared recipe).
# ----------------------------------------------------------------------------------------
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
    """Expected candidate/transport failure with a fixed bounded category."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "protocol_error")
        super().__init__("candidate protocol failure")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, CandidateProtocolError):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout",
            "operation": bounded_failure_name(operation, "unknown")}


def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError("work allowance must be positive")
    return value


def require_joint_workload_budget(*, plane_profile):
    profile = plane_profile
    episodes, methods = profile["episode_count"], profile["method_count"]
    if any(type(count) is not int or count <= 0 for count in (episodes, methods)):
        raise ValueError("invalid episode or method count")
    times = {name: finite_budget_seconds(profile[name]) for name in (
        "wall_seconds", "startup_seconds", "reset_seconds", "cleanup_seconds", "finish_seconds")}
    work = positive_work_seconds(profile["work_seconds"])
    needed = (times["startup_seconds"] + times["finish_seconds"]
              + episodes * (times["reset_seconds"] + methods * (work + times["cleanup_seconds"])))
    if needed > times["wall_seconds"]:
        raise ValueError("productive work exceeds the declared wall budget")
    return needed


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


def state_free_rpc_counts(episodes):
    """Operation-count table: each episode is one reset plus N_LEVELS propose calls."""
    return {"reset": episodes, "propose": episodes * N_LEVELS}


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
                record_failure(failure, index)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


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


PLANE = "final"
WALL_SECONDS = 14400.0
MAX_RPC_CALLS = 320
PRIMARY_SEEDS = (201, 202, 203)
CONTROL_SEED = 201
PLAN_SEED = 20261028
FAMILY_WEIGHTS = {"crowd": 0.25, "expert_human": 0.25, "llm_judge": 0.25, "sports": 0.25}
SMOKE_ROWS = 1500
SMOKE_CASE_NAMES = ("arena_F_drop", "mtb_human_flip")
METRIC_NAMES = ("combined_score", "score_crowd", "score_expert_human", "score_llm_judge", "score_sports",
                "flip_rate_crowd_drop", "flip_rate_crowd_flip",
                "flip_rate_expert_human_drop", "flip_rate_expert_human_flip",
                "flip_rate_llm_judge_drop", "flip_rate_llm_judge_flip",
                "flip_rate_sports_drop", "flip_rate_sports_flip",
                "score_random", "score_winrate", "score_influence", "score_constant",
                "margin_vs_best_baseline", "perm_control_abs_gap", "valid_proposal_rate")
CASE_SPECS = []
for _name, _family, _source in (("arena_F", "crowd", "arena_F"), ("mtb_human", "expert_human", "mtb_human"),
                                ("mtb_gpt4", "llm_judge", "mtb_gpt4")):
    for _mode in MODES:
        CASE_SPECS.append({"name": "%s_%s" % (_name, _mode), "family": _family, "source": _source, "mode": _mode})
for _season in (2008, 2012, 2015):
    for _mode in MODES:
        CASE_SPECS.append({"name": "nba_%d_%s" % (_season, _mode), "family": "sports",
                           "source": "nba:%d" % _season, "mode": _mode})
for _i, _spec in enumerate(CASE_SPECS):
    _spec["id"] = _i
RESET_SEQUENCE = [s for _ in CASE_SPECS for s in PRIMARY_SEEDS + (CONTROL_SEED,)]
SMOKE_RESET_SEQUENCE = [PRIMARY_SEEDS[0], CONTROL_SEED] * len(SMOKE_CASE_NAMES)


# ----------------------------------------------------------------------------------------
# Trusted Bradley-Terry fitter (single source of truth for ranks, gaps and success).
# ----------------------------------------------------------------------------------------
def pair_counts(a, b, y, k):
    """W[i, j] = wins of i over j; a tie contributes half a win to each side."""
    w = np.zeros(k * k)
    m = y == 1
    if m.any():
        w += np.bincount(a[m] * k + b[m], minlength=k * k)
    m = y == -1
    if m.any():
        w += np.bincount(b[m] * k + a[m], minlength=k * k)
    m = y == 0
    if m.any():
        t = np.bincount(a[m] * k + b[m], minlength=k * k).reshape(k, k)
        w += 0.5 * (t + t.T).reshape(-1)
    return w.reshape(k, k)


def _log_lik(theta, w):
    d = theta[:, None] - theta[None, :]
    return float(np.sum(w * -np.logaddexp(0.0, -d)) - 0.5 * RIDGE * float(theta @ theta))


def fit_bt(w, theta0=None):
    """Ridge-penalised BT MLE by damped Newton on the pair-win matrix; returns (theta, -Hessian)."""
    k = w.shape[0]
    n = w + w.T
    theta = np.zeros(k) if theta0 is None else np.array(theta0, dtype=float)
    f_old = _log_lik(theta, w)
    for _ in range(BT_MAXIT):
        p = 1.0 / (1.0 + np.exp(-(theta[:, None] - theta[None, :])))
        g = (w - n * p).sum(1) - RIDGE * theta
        h = n * p * (1.0 - p)
        a_mat = np.diag(h.sum(1) + RIDGE) - h
        if float(np.max(np.abs(g))) < BT_TOL:
            return theta, a_mat
        step = np.linalg.solve(a_mat, g)
        t = 1.0
        while True:
            cand = theta + t * step
            f_new = _log_lik(cand, w)
            if f_new >= f_old - 1e-12 * max(1.0, abs(f_old)) or t < 1e-6:
                break
            t *= 0.5
        theta, f_old = cand, f_new
    raise RuntimeError("bt_nonconvergence")


def top_and_gap(theta):
    top = int(np.argmax(theta))
    rest = np.delete(theta, top)
    return top, float(theta[top] - rest.max())


def reference_fit(a, b, y, k):
    """Independent row-level L-BFGS fit used only as a cross-check of fit_bt."""
    from scipy.optimize import minimize
    yv = (y + 1) / 2.0

    def nll(theta):
        d = theta[a] - theta[b]
        val = np.sum(yv * np.logaddexp(0.0, -d) + (1 - yv) * np.logaddexp(0.0, d)) + 0.5 * RIDGE * theta @ theta
        p = 1.0 / (1.0 + np.exp(-d))
        r = p - yv
        grad = np.bincount(a, weights=r, minlength=k) - np.bincount(b, weights=r, minlength=k) + RIDGE * theta
        return val, grad

    res = minimize(nll, np.zeros(k), jac=True, method="L-BFGS-B", options={"maxiter": 5000, "gtol": 1e-11, "ftol": 1e-15})
    return res.x


def edited_counts(case, idx, mode):
    k = case["K"]
    w = case["W"].copy()
    if idx.size == 0:
        return w
    a, b, y = case["a"][idx], case["b"][idx], case["y"][idx]
    w -= pair_counts(a, b, y, k)
    if mode == "flip":
        w += pair_counts(a, b, -y, k)
    return w


def verify_edit(case, idx, mode):
    """Trusted refit after applying a validated edit set. Returns (u, displaced)."""
    theta, _ = fit_bt(edited_counts(case, idx, mode), case["theta"])
    gap_after = float(theta[case["top"]] - np.delete(theta, case["top"]).max())
    if gap_after < 0.0:
        return 1.0, True
    return float(min(1.0, max(0.0, 1.0 - gap_after / case["gap"]))), False


def budget_for(n, level):
    num, den = LADDER[level]
    return max(1, -(-(n * num) // den))


def validate_indices(resp, k, n, decisive=None):
    if type(resp) is not dict or set(resp) != {"indices"}:
        return None
    v = resp["indices"]
    if type(v) is not list or len(v) > k:
        return None
    for i in v:
        if type(i) is not int or i < 0 or i >= n:
            return None
    if len(set(v)) != len(v):
        return None
    if decisive is not None and any(not decisive[i] for i in v):
        return None
    return np.array(v, dtype=np.int64)


# ----------------------------------------------------------------------------------------
# Evaluator-owned baselines (never contacting the candidate).
# ----------------------------------------------------------------------------------------
def edit_pool(case, mode):
    return np.arange(case["n"]) if mode == "drop" else np.flatnonzero(case["y"] != 0)


def baseline_winrate(case, k, mode):
    a, b, y, top, rival = case["a"], case["b"], case["y"], case["top"], case["rival"]
    wins = ((a == top) & (y == 1)) | ((b == top) & (y == -1))
    vs_rival = (a == rival) | (b == rival)
    order = np.concatenate([np.flatnonzero(wins & vs_rival), np.flatnonzero(wins & ~vs_rival)])
    return order[:k]


def baseline_influence(case, k, mode):
    a, b, y, theta = case["a"], case["b"], case["y"], case["theta"]
    e = np.zeros(case["K"])
    e[case["top"]], e[case["rival"]] = 1.0, -1.0
    v = np.linalg.solve(case["A"], e)
    p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
    yv = (y + 1) / 2.0
    s = v[a] - v[b]
    if mode == "drop":
        effect = -s * (yv - p)
    else:
        effect = np.where(y != 0, s * ((1.0 - yv) - yv), np.inf)
    order = np.lexsort((np.arange(case["n"]), effect))
    return order[:k][np.isfinite(effect[order[:k]])]


def baseline_scores(case, plan_seed):
    """Mean score per ladder level for random / winrate / influence / constant baselines."""
    mode = case["mode"]
    pool = edit_pool(case, mode)
    out = {"random": [], "winrate": [], "influence": [], "constant": []}
    for level in range(N_LEVELS):
        k = min(budget_for(case["n"], level), pool.size)
        draws = []
        for d in range(RANDOM_DRAWS):
            rng = np.random.default_rng([plan_seed, 17, case["rng_id"], level, d])
            draws.append(verify_edit(case, rng.choice(pool, size=k, replace=False), mode)[0])
        out["random"].append(float(np.mean(draws)))
        out["winrate"].append(verify_edit(case, baseline_winrate(case, k, mode), mode)[0])
        out["influence"].append(verify_edit(case, baseline_influence(case, k, mode), mode)[0])
        empty = verify_edit(case, np.zeros(0, dtype=np.int64), mode)[0]
        first_k = verify_edit(case, pool[:k], mode)[0]
        out["constant"].append(0.5 * (empty + first_k))
    return out


# ----------------------------------------------------------------------------------------
# Data loading helpers and case construction.
# ----------------------------------------------------------------------------------------
def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", PLANE)


def read_table(name, required):
    path = os.path.join(resource_root(), name)
    with open(path, newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows or any(c not in rows[0] for c in required):
        raise RuntimeError("resource_schema_mismatch")
    return rows


def outcomes_of(rows):
    y = np.array([int(r["outcome"]) for r in rows], dtype=np.int64)
    if not np.isin(y, (-1, 0, 1)).all():
        raise RuntimeError("resource_outcome_invalid")
    return y


def build_case(index, spec, raw, smoke):
    names_a, names_b, y = raw["a"], raw["b"], raw["y"]
    n = len(y)
    if smoke and n > SMOKE_ROWS:
        sel = np.sort(np.random.default_rng([PLAN_SEED, 99, spec["id"]]).choice(n, SMOKE_ROWS, replace=False))
        names_a = [names_a[i] for i in sel]
        names_b = [names_b[i] for i in sel]
        y = y[sel]
        n = len(y)
    uniq = sorted(set(names_a) | set(names_b))
    k = len(uniq)
    ids = np.random.default_rng([PLAN_SEED, 5, spec["id"]]).permutation(k)  # anonymising relabelling
    lookup = {name: int(ids[i]) for i, name in enumerate(uniq)}
    a = np.array([lookup[x] for x in names_a], dtype=np.int64)
    b = np.array([lookup[x] for x in names_b], dtype=np.int64)
    if k < 2 or n < 20 or (a == b).any() or not (y != 0).any():
        raise RuntimeError("case_degenerate")
    w = pair_counts(a, b, y, k)
    theta, a_mat = fit_bt(w)
    top, gap = top_and_gap(theta)
    rival = int(np.argsort(-theta)[1])
    if not gap > 1e-9:
        raise RuntimeError("baseline_gap_not_positive")
    case = {"index": index, "rng_id": spec["id"], "name": spec["name"], "family": spec["family"], "mode": spec["mode"],
            "n": n, "K": k, "a": a, "b": b, "y": y, "W": w, "theta": theta, "A": a_mat,
            "top": top, "rival": rival, "gap": gap}
    case["ks"] = [budget_for(n, j) for j in range(N_LEVELS)]
    pool = edit_pool(case, spec["mode"])
    if pool.size < case["ks"][-1]:
        raise RuntimeError("edit_pool_too_small")
    case["primary_view"] = {"a": a, "b": b, "y": y, "rows": None}
    case["control_view"] = make_control_view(case)
    for view in (case["primary_view"], case["control_view"]):
        if view is not None:
            view["enc"] = {"model_a": encode_array(view["a"], "<i2", "int16"),
                           "model_b": encode_array(view["b"], "<i2", "int16"),
                           "outcome": encode_array(view["y"], "i1", "int8")}
    return case


def encode_array(arr, np_dtype, name):
    raw = np.ascontiguousarray(arr.astype(np_dtype)).tobytes()
    return {"dtype": name, "shape": [int(arr.size)], "encoding": "base64-le",
            "data": base64.b64encode(raw).decode("ascii")}


def permutation_is_vacuous(rp, lp):
    n, k = rp.size, lp.size
    if float(np.mean(rp == np.arange(n))) > 0.05:
        return True
    return int(np.sum(lp != np.arange(k))) < max(2, -(-k // 2))


def make_control_view(case):
    """Row-shuffled, label-relabelled copy of the same data; None if no non-vacuous draw is found."""
    n, k = case["n"], case["K"]
    for attempt in range(50):
        rng = np.random.default_rng([PLAN_SEED, 7, case["rng_id"], attempt])
        rp, lp = rng.permutation(n), rng.permutation(k)
        if not permutation_is_vacuous(rp, lp):
            return {"a": lp[case["a"][rp]], "b": lp[case["b"][rp]], "y": case["y"][rp], "rows": rp}
    return None


def make_request(case, view, mode, k):
    return {"op": "propose", "mode": mode, "budget": int(k), "n_models": int(case["K"]),
            "n_comparisons": int(case["n"]), "target": TARGET_TEXT,
            "model_a": view["enc"]["model_a"], "model_b": view["enc"]["model_b"],
            "outcome": view["enc"]["outcome"]}


def crosscheck_fit(cases):
    """Compare the trusted fitter with an independent L-BFGS fit on a small slice of real data."""
    case = min(cases, key=lambda c: (c["K"], c["n"]))
    m = min(case["n"], 600)
    a, b, y = case["a"][:m], case["b"][:m], case["y"][:m]
    ref = reference_fit(a, b, y, case["K"])
    theta, _ = fit_bt(pair_counts(a, b, y, case["K"]))
    if float(np.max(np.abs(ref - theta))) > CROSSCHECK_TOL:
        raise RuntimeError("bt_crosscheck_failed")
    return True


def payload_preflight(cases):
    """Serialise the largest representative requests/responses and assert the wire limit."""
    sizes = []
    for case in cases:
        sizes.append(len(bounded_json_line(make_request(case, case["primary_view"], case["mode"], case["ks"][-1]))))
    n_worst = 57477  # largest declared Arena table
    rng = np.random.default_rng([PLAN_SEED, 3])
    fake = {"enc": {"model_a": encode_array(rng.integers(0, 128, n_worst), "<i2", "int16"),
                    "model_b": encode_array(rng.integers(0, 128, n_worst), "<i2", "int16"),
                    "outcome": encode_array(rng.integers(-1, 2, n_worst), "i1", "int8")}}
    fake_case = {"K": 128, "n": n_worst}
    sizes.append(len(bounded_json_line(make_request(fake_case, fake, "drop", budget_for(n_worst, N_LEVELS - 1)))))
    k_max = budget_for(n_worst, N_LEVELS - 1)
    sizes.append(len(bounded_json_line({"indices": list(range(n_worst - k_max, n_worst))})))
    sizes.append(len(bounded_json_line({"ok": True})))
    return max(sizes)


# ----------------------------------------------------------------------------------------
# Final-plane sources: Arena partition F (crowd), MT-Bench human (expert), MT-Bench GPT-4 pairs
# (LLM judge), NBA 2008/2012/2015 (sports).  Search-plane content hashes are excluded.
# ----------------------------------------------------------------------------------------
_EXCLUDED = []


def excluded_hashes():
    if not _EXCLUDED:
        with open(os.path.join(resource_root(), "search_exclusion_hashes.txt"), encoding="utf-8") as handle:
            _EXCLUDED.append({line.strip() for line in handle if line.strip()})
    return _EXCLUDED[0]


def require_no_overlap(rows, columns):
    blocked = excluded_hashes()
    for column in columns:
        if any(r[column] in blocked for r in rows):
            raise RuntimeError("search_final_content_overlap")


def raw_source(source):
    if source == "arena_F":
        rows = read_table("arena_final.csv", ("model_a", "model_b", "outcome", "first_turn_hash",
                                              "prompt_hash", "row_hash"))
        if any(int(r["first_turn_hash"][:2], 16) % 2 != 1 for r in rows):
            raise RuntimeError("partition_violation")
        require_no_overlap(rows, ("first_turn_hash", "prompt_hash", "row_hash"))
        return {"a": [r["model_a"] for r in rows], "b": [r["model_b"] for r in rows], "y": outcomes_of(rows)}
    if source in ("mtb_human", "mtb_gpt4"):
        rows = read_table("mtbench_human.csv" if source == "mtb_human" else "mtbench_gpt4.csv",
                          ("model_a", "model_b", "outcome", "question_hash", "row_hash"))
        require_no_overlap(rows, ("question_hash", "row_hash"))
        return {"a": [r["model_a"] for r in rows], "b": [r["model_b"] for r in rows], "y": outcomes_of(rows)}
    if source.startswith("nba:"):
        season = source.split(":")[1]
        rows = [r for r in read_table("nba_final.csv", ("season", "team_a", "team_b", "outcome", "row_hash"))
                if r["season"] == season]
        if len({r["row_hash"] for r in rows}) != len(rows):
            raise RuntimeError("duplicate_games")
        require_no_overlap(rows, ("row_hash",))
        return {"a": [r["team_a"] for r in rows], "b": [r["team_b"] for r in rows], "y": outcomes_of(rows)}
    raise RuntimeError("unknown_source")


def load_cases(smoke):
    cache, cases = {}, []
    specs = [s for s in CASE_SPECS if not smoke or s["name"] in SMOKE_CASE_NAMES]
    for position, spec in enumerate(specs):
        if spec["source"] not in cache:
            cache[spec["source"]] = raw_source(spec["source"])
        cases.append(build_case(position, spec, cache[spec["source"]], smoke))
    return cases


def PLANE_EXTRA_METRICS(cases, episodes, outcomes, family, combined, baseline_totals, prim):
    out = {"margin_vs_best_baseline": combined - max(baseline_totals["random"], baseline_totals["winrate"],
                                                     baseline_totals["influence"])}
    for fam in FAMILY_WEIGHTS:
        for mode in MODES:
            vals = [float(o["disp"][-1]) for c in cases if c["family"] == fam and c["mode"] == mode
                    for o in prim[c["index"]].values()]
            out["flip_rate_%s_%s" % (fam, mode)] = mean_or_zero(vals)
    return out


# ----------------------------------------------------------------------------------------
# Candidate transport: trusted in-process broker proxy, or killable native subprocess.
# ----------------------------------------------------------------------------------------
RUNNER = r'''
import importlib.util, json, os, resource, sys
def main():
    path, cpu, mem = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out = os.fdopen(os.dup(1), "wb", buffering=0)
    os.dup2(2, 1)
    sys.stdout = sys.stderr
    sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
    spec = importlib.util.spec_from_file_location("candidate_program", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for line in sys.stdin.buffer:
        try:
            data = json.dumps(module.handle(json.loads(line)), allow_nan=False, separators=(",", ":")).encode()
        except BaseException as error:
            if os.environ.get("TASK_WORKER_DIAG") == "1":
                print("worker_exception type=%s" % type(error).__name__, file=sys.stderr, flush=True)
            data = b'{"__candidate_exception__":true}'
        out.write(data + b"\n")
main()
'''


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
    )
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    threads = str(CANDIDATE_THREADS)
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1", OMP_NUM_THREADS=threads, OPENBLAS_NUM_THREADS=threads,
                       MKL_NUM_THREADS=threads, NUMEXPR_NUM_THREADS=threads)
    return parent_environment.get("TASK_PYTHON") or sys.executable, environment


def _reject_constant(token):
    raise ValueError("non-finite JSON constant")


class CandidateClient:
    def __init__(self, program_path, trusted, diag):
        self.program_path = program_path if trusted else os.path.abspath(program_path)
        self.trusted = trusted
        self.diag = diag
        self.rpc_count = 0
        self.proc = None
        self.capture = None
        self.last_snapshot = None
        self.cleanup_note = None
        self.handle = None
        self.starts = []
        self.workdir = None
        if trusted:
            spec = importlib.util.spec_from_file_location("broker_candidate_proxy", program_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.handle = module.handle
        else:
            self.workdir = tempfile.mkdtemp(prefix="cand_")

    # -- native worker lifecycle -------------------------------------------------------
    def _spawn(self):
        python, env = candidate_subprocess_settings(os.environ)
        if self.diag:
            env["TASK_WORKER_DIAG"] = "1"
        cpu = cpu_limit_seconds(WALL_SECONDS, CANDIDATE_THREADS)
        self.proc = subprocess.Popen(
            [python, "-c", RUNNER, self.program_path, str(cpu), str(8 * 1024 ** 3)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
            cwd=self.workdir, shell=False, close_fds=True, start_new_session=True)
        self.capture = BoundedWorkerStderr(self.proc.stderr)
        os.set_blocking(self.proc.stdin.fileno(), False)
        os.set_blocking(self.proc.stdout.fileno(), False)

    def stop_worker(self):
        proc, capture = self.proc, self.capture
        self.proc = self.capture = None
        if proc is None:
            return
        try:
            for sig, wait in ((signal.SIGTERM, TERM_WAIT), (signal.SIGKILL, KILL_WAIT)):
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    proc.wait(timeout=wait)
                    break
                except subprocess.TimeoutExpired:
                    continue
        finally:
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
            try:
                self.last_snapshot = capture.close()
            except RuntimeError:
                self.cleanup_note = "stderr_cleanup_unresolved"

    def cleanup(self):
        self.stop_worker()
        if self.workdir:
            shutil.rmtree(self.workdir, ignore_errors=True)
            self.workdir = None

    def forwarded_stderr(self):
        snap = self.last_snapshot
        return snap["stderr"] if snap else ""

    # -- RPC -----------------------------------------------------------------------------
    def rpc(self, request, timeout):
        self.rpc_count += 1
        if self.rpc_count > MAX_RPC_CALLS:
            raise RuntimeError("rpc_budget_exceeded")
        if request.get("op") == "reset":
            self.starts.append(time.monotonic())
        if self.trusted:
            return self._call_trusted(request, timeout)
        if request.get("op") == "reset":
            self.stop_worker()
            self._spawn()
        return self._call_native(request, timeout)

    def _call_trusted(self, request, timeout):
        box = {}

        def target():
            try:
                box["response"] = self.handle(request)
            except BaseException:
                box["error"] = True

        thread = threading.Thread(target=target, daemon=True)
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            raise TimeoutError("candidate call timed out")
        if "error" in box:
            raise CandidateProtocolError("candidate_exception")
        try:
            return json.loads(json.dumps(box["response"], allow_nan=False), parse_constant=_reject_constant)
        except (TypeError, ValueError):
            raise CandidateProtocolError("malformed_response") from None

    def _call_native(self, request, timeout):
        if self.proc is None:
            raise CandidateProtocolError("worker_not_running")
        payload = bounded_json_line(request)
        deadline = time.monotonic() + timeout
        stdin_fd, stdout_fd = self.proc.stdin.fileno(), self.proc.stdout.fileno()
        view, sent, buf, done = memoryview(payload), 0, bytearray(), False
        selector = selectors.DefaultSelector()
        try:
            selector.register(stdin_fd, selectors.EVENT_WRITE)
            selector.register(stdout_fd, selectors.EVENT_READ)
            while not done:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self.stop_worker()
                    raise TimeoutError("candidate call timed out")
                for key, _ in selector.select(min(remaining, 0.25)):
                    if key.fd == stdin_fd:
                        try:
                            sent += os.write(stdin_fd, view[sent:sent + 65536])
                        except BlockingIOError:
                            continue
                        except OSError:
                            self.stop_worker()
                            raise CandidateProtocolError("transport_closed") from None
                        if sent >= len(payload):
                            selector.unregister(stdin_fd)
                    else:
                        try:
                            chunk = os.read(stdout_fd, 1 << 20)
                        except BlockingIOError:
                            continue
                        if not chunk:
                            self.stop_worker()
                            raise CandidateProtocolError("transport_closed")
                        buf += chunk
                        if len(buf) >= WIRE_LIMIT:
                            self.stop_worker()
                            raise CandidateProtocolError("response_too_large")
                        if b"\n" in chunk:
                            done = True
        finally:
            selector.close()
        try:
            response = json.loads(bytes(buf).split(b"\n", 1)[0].decode("utf-8"), parse_constant=_reject_constant)
        except (UnicodeDecodeError, ValueError):
            raise CandidateProtocolError("malformed_response") from None
        if type(response) is dict and "__candidate_exception__" in response:
            raise CandidateProtocolError("candidate_exception")
        return response

    def episode_durations(self, end):
        bounds = self.starts + [end]
        return [bounds[i + 1] - bounds[i] for i in range(len(self.starts))]


# ----------------------------------------------------------------------------------------
# Episodes, scoring and aggregation.
# ----------------------------------------------------------------------------------------
def worst_case_outcome(episode):
    return {"u": [0.0] * N_LEVELS, "disp": [False] * N_LEVELS, "valid": 0, "complete": False}


def evaluate_episode(cases, episode, call, work_deadline, clock):
    case = cases[episode["case"]]
    view = case["control_view"] if episode["kind"] == "control" else case["primary_view"]
    if view is None:  # vacuous control: rejected, never scored
        return worst_case_outcome(episode)
    mode = case["mode"]
    decisive = (view["y"] != 0) if mode == "flip" else None
    us, disp, valid = [], [], 0
    for level, k in enumerate(case["ks"]):
        if clock() > work_deadline:
            raise TimeoutError("episode work budget exhausted")
        response = call(make_request(case, view, mode, k))
        idx = validate_indices(response, k, case["n"], decisive)
        if idx is None:
            us.append(0.0)
            disp.append(False)
            continue
        original = idx if view["rows"] is None else view["rows"][idx]
        u, shown = verify_edit(case, original, mode)
        us.append(u)
        disp.append(shown)
        valid += 1
    return {"u": us, "disp": disp, "valid": valid, "complete": True}


def mean_or_zero(values):
    values = list(values)
    return float(sum(values) / len(values)) if values else 0.0


def family_hierarchy(case_scores, cases):
    """case_scores: {case_index: score}; levels->seeds are already averaged. Returns (family, total)."""
    family = {}
    for name in FAMILY_WEIGHTS:
        family[name] = mean_or_zero(case_scores[c["index"]] for c in cases
                                    if c["family"] == name and c["index"] in case_scores)
    total = float(sum(FAMILY_WEIGHTS[f] * family[f] for f in FAMILY_WEIGHTS))
    return family, total


def aggregate(cases, episodes, outcomes, base):
    seeds_run = sorted({e["seed"] for e in episodes if e["kind"] == "primary"})
    prim = collections.defaultdict(dict)
    control = {}
    for e, o in zip(episodes, outcomes):
        if e["kind"] == "primary":
            prim[e["case"]][e["seed"]] = o
        else:
            control[e["case"]] = o
    case_scores = {ci: mean_or_zero(mean_or_zero(o["u"]) for o in seeds.values()) for ci, seeds in prim.items()}
    family, combined = family_hierarchy(case_scores, cases)
    metrics = {"combined_score": combined}
    baseline_totals = {}
    for key in ("random", "winrate", "influence", "constant"):
        _, total = family_hierarchy({c["index"]: mean_or_zero(base[c["index"]][key]) for c in cases}, cases)
        baseline_totals[key] = total
        metrics["score_" + key] = total
    gaps = []
    for ci, o in control.items():
        if not o["complete"]:
            gaps.append(1.0)  # predeclared worst case of a failed/vacuous control
        else:
            primary = prim[ci].get(CONTROL_SEED)
            gaps.append(abs((mean_or_zero(primary["u"]) if primary else 0.0) - mean_or_zero(o["u"])))
    metrics["perm_control_abs_gap"] = mean_or_zero(gaps) if gaps else 1.0
    declared_calls = len(episodes) * N_LEVELS
    metrics["valid_proposal_rate"] = float(sum(o["valid"] for o in outcomes) / declared_calls)
    metrics.update(PLANE_EXTRA_METRICS(cases, episodes, outcomes, family, combined, baseline_totals, prim))
    for f in FAMILY_WEIGHTS:
        metrics["score_" + f] = family[f]
    seed_records = {}
    for s in seeds_run:
        seed_case = {e["case"]: mean_or_zero(o["u"]) for e, o in zip(episodes, outcomes)
                     if e["kind"] == "primary" and e["seed"] == s}
        seed_records[s] = family_hierarchy(seed_case, cases)[1]
    return metrics, seed_records, case_scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    diag = PLANE == "search" and (smoke or qualification)
    trusted = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET")) and args.program_path == BROKER_PROXY_PATH
    clock = time.monotonic
    hard_deadline = _T0 + WALL_SECONDS - STARTUP_ALLOWANCE

    # ---- trusted setup: data, fitter cross-check, baselines, controls, preflight ----
    cases = load_cases(smoke)
    crosscheck_fit(cases)
    base = {c["index"]: baseline_scores(c, PLAN_SEED) for c in cases}
    wire_bytes = payload_preflight(cases)
    if wire_bytes >= WIRE_LIMIT:
        raise RuntimeError("payload_preflight_failed")
    episodes = []
    seeds = PRIMARY_SEEDS[:1] if smoke else PRIMARY_SEEDS
    for c in cases:
        for s in seeds:
            episodes.append({"case": c["index"], "kind": "primary", "seed": s})
        episodes.append({"case": c["index"], "kind": "control", "seed": CONTROL_SEED})
    expected = SMOKE_RESET_SEQUENCE if smoke else RESET_SEQUENCE
    if [e["seed"] for e in episodes] != list(expected):
        raise RuntimeError("reset_sequence_mismatch")
    counts = state_free_rpc_counts(len(episodes))
    if not smoke and counts["reset"] + counts["propose"] > MAX_RPC_CALLS:
        raise RuntimeError("rpc_budget_preflight_failed")
    require_joint_workload_budget(plane_profile={
        "episode_count": len(episodes), "method_count": 1, "wall_seconds": WALL_SECONDS,
        "startup_seconds": STARTUP_ALLOWANCE, "reset_seconds": RESET_TIMEOUT,
        "cleanup_seconds": EPISODE_OVERHEAD, "finish_seconds": FINISH_RESERVE,
        "work_seconds": N_LEVELS * RPC_CAP})

    client = CandidateClient(args.program_path, trusted, diag)

    def record_failure(failure, index):
        if PLANE != "search":
            return
        episode = episodes[index]
        if not client.trusted:
            client.stop_worker()
        line = ("episode_failure episode=%d case=%d kind=%s component=%s category=%s operation=%s"
                % (index, episode["case"], episode["kind"], failure["component"],
                   bounded_failure_name(failure["category"], "unknown"),
                   bounded_failure_name(failure["operation"], "unknown")))
        print(line[:256], file=sys.stderr, flush=True)
        if diag and client.forwarded_stderr():
            sys.stderr.write(client.forwarded_stderr())
            sys.stderr.flush()

    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE,
            reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP,
            clock=clock, rpc=client.rpc,
            evaluate=lambda ep, call, deadline: evaluate_episode(cases, ep, call, deadline, clock),
            worst_case=worst_case_outcome, record_failure=record_failure)
    finally:
        end = clock()
        durations = client.episode_durations(end)
        client.cleanup()
    if len(durations) != len(episodes):
        durations = (durations + [0.0] * len(episodes))[:len(episodes)]

    metrics, seed_scores, case_scores = aggregate(cases, episodes, outcomes, base)
    ordered = {name: metrics[name] for name in METRIC_NAMES}
    if set(metrics) != set(METRIC_NAMES) or not all(math.isfinite(v) for v in ordered.values()):
        raise RuntimeError("metric_schema_mismatch")
    controls_ok = all(c["control_view"] is not None for c in cases)
    within_deadline = clock() <= hard_deadline
    correct = bool(complete and controls_ok and within_deadline
                   and sum(o["valid"] for o in outcomes) >= 1)

    records = []
    for s, score in sorted(seed_scores.items()):
        mine = [i for i, e in enumerate(episodes) if e["seed"] == s]
        records.append({"seed": int(s), "score": float(score),
                        "correct": bool(all(outcomes[i]["complete"] for i in mine)),
                        "duration_seconds": float(max(0.0, sum(durations[i] for i in mine)))})
    os.makedirs(args.results_dir, exist_ok=True)

    def write_json(name, value):
        with open(os.path.join(args.results_dir, name), "w", encoding="utf-8") as handle:
            json.dump(value, handle, allow_nan=False, sort_keys=True)

    write_json("metrics.json", ordered)
    write_json("correct.json", {"correct": correct})
    if records:
        write_json("evaluation_evidence.json", {"schema_version": 1, "episodes": records})
    if qualification:
        write_json("qualification.json", {"schema_version": 1,
                                          "feasible": bool(not smoke and complete and controls_ok and within_deadline)})


def entry():
    try:
        main()
    except SystemExit:
        raise
    except Exception as error:
        name = type(error).__name__
        if not (name.isascii() and name.isidentifier() and len(name) <= 80):
            name = "EvaluatorError"
        if PLANE == "search":
            message = str(error).replace("\n", " ")[:200]
            print("evaluator_error type=%s message=%s" % (name, message), file=sys.stderr)
        else:
            print("evaluator_error type=%s" % name, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    entry()
