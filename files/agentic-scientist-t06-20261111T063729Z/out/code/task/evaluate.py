#!/usr/bin/env python3
"""Search-plane (development) evaluator: Bradley-Terry leaderboard data-removal sensitivity. Reads only resources/search.

Evaluator-owned exact Bradley-Terry refit verifies every candidate removal set.
The candidate only ever sees an anonymized comparison table and a target pair.
"""
import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "2"

import argparse
import base64
import collections
import hashlib
import importlib.util
import json
import math
import re
import resource
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import time

import numpy as np

T_START = time.monotonic()

# ----------------------------------------------------------------------------------------------
# Plane declaration (fixed before evaluation)
# ----------------------------------------------------------------------------------------------
PLANE = "search"
RESOURCE_ROOT = "resources/search"
SEEDS = [11, 12]
FAMILIES = ["crowd", "expert"]
FAMILY_METRIC = {"crowd": "score_crowd", "expert": "score_expert"}
CASES = [
    {"id": "C1", "family": "crowd", "table": "arena55k_table.npz", "kind": "top"},
    {"id": "C2", "family": "crowd", "table": "arena55k_table.npz", "kind": "mid"},
    {"id": "C3", "family": "expert", "table": "mtbench_human_table.npz", "kind": "top"},
    {"id": "C4", "family": "expert", "table": "mtbench_human_table.npz", "kind": "mid"},
    {"id": "C5", "family": "control", "table": "arena55k_table.npz", "kind": "perm_top", "real": "C1", "perm_salt": 5},
    {"id": "C6", "family": "control", "table": "mtbench_human_table.npz", "kind": "perm_top", "real": "C3", "perm_salt": 6},
]
COPY_PAIRS = [("C1", "C3"), ("C3", "C1")]
RESET_SEQUENCE = [11, 12, 11, 12, 11, 12, 11, 12, 11, 12, 11, 12]
SMOKE_RESET_SEQUENCE = [11, 11, 11, 11, 11, 11]
WALL_SECONDS = 3600.0
BASELINE_ALLOWANCE = 600.0
RESOURCE_SHA256 = {
    "arena55k_table.npz": "d88e6ce507318a5d17caa42d7dad279752c69a2834bcb0f9729c865bc527c197",
    "mtbench_human_table.npz": "cfdf9068591e9567fafdf185b934e7cc2ccac335f7eca66f9b24864c6fb32d27",
    "search_meta.json": "fae4bd10107029fc82491614f2d58903fbf8a2d1a997ebe93c95f8dc96f1106b"
}

SMOKE_MAX_MODELS = 10
SMOKE_ROWS = 2000
SMOKE_DRAWS = 3
FULL_DRAWS = 20
CHUNK_ROWS_FULL = 65536
CHUNK_ROWS_SMOKE = 512
MAX_CHUNKS = 4                       # declared maximum load_chunk calls per episode
RIDGE = 0.01
TIE_AS_HALF_WIN = True
CAP_FRACTION = 0.02
WIRE_LIMIT = 64 * 1024 * 1024
MAX_ROWS = MAX_CHUNKS * CHUNK_ROWS_FULL
EPISODE_RPCS = 1 + MAX_CHUNKS + 1    # reset + load_chunk* + analyze
MAX_CALLS = len(SEEDS) * len(CASES) * EPISODE_RPCS
RESET_TIMEOUT = 30.0
RPC_CAP = 120.0
STARTUP_ALLOWANCE = 120.0
FINISH_RESERVE = 30.0
EPISODE_OVERHEAD = 8.0               # candidate terminate(1)+kill(1)+reader close(1) + dispatch, doubled for margin
PERM_SEED = 20260211
CANDIDATE_AS_BYTES = 5 * 1024 ** 3
CANDIDATE_THREADS = 2
SMOKE = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
QUALIFICATION = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
DIAGNOSTIC_VISIBLE = PLANE == "search"
REPAIR_VISIBLE = PLANE == "search" and (QUALIFICATION or SMOKE)

METRIC_NAMES = ["combined_score", "flip_rate", "mean_budget_fraction", "score_crowd", "score_expert", "reference_random_score", "reference_influence_score", "control_gap_permuted_minus_real"]


# ----------------------------------------------------------------------------------------------
# Failure identity helpers
# ----------------------------------------------------------------------------------------------
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


class CandidateRpcError(RuntimeError):
    """Explicit protocol failure of the candidate/transport with a fixed category."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "candidate_protocol_error")
        super().__init__("candidate protocol failure")


class IntegrityFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "integrity_failure")
        super().__init__("integrity check failed")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, CandidateRpcError):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
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


def require_joint_workload_budget(profile):
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


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


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
            except (TimeoutError, RequiredBaselineFailure, CandidateRpcError) as error:
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
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateRpcError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ----------------------------------------------------------------------------------------------
# Bounded worker stderr capture (candidate subprocess in native smoke mode)
# ----------------------------------------------------------------------------------------------
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


# ----------------------------------------------------------------------------------------------
# Bradley-Terry (logistic MLE, ties = half win, fixed ridge), exact trusted refit
# ----------------------------------------------------------------------------------------------
def outcome_scores(y):
    return np.where(y == 0, 1.0, np.where(y == 1, 0.0, 0.5))


def fit_bt(a, b, s, n_models, ridge=RIDGE, theta0=None, tol=1e-9, max_iter=80):
    M = int(n_models)
    th = np.zeros(M) if theta0 is None else np.array(theta0, dtype=np.float64)
    a = a.astype(np.intp)
    b = b.astype(np.intp)
    ab = a * M + b

    def objective(t):
        d = t[a] - t[b]
        return float(np.sum(np.logaddexp(0.0, d) - s * d) + 0.5 * ridge * float(t @ t))

    f = objective(th)
    for _ in range(max_iter):
        d = th[a] - th[b]
        p = 1.0 / (1.0 + np.exp(-d))
        r = p - s
        g = np.bincount(a, r, M) - np.bincount(b, r, M) + ridge * th
        if np.max(np.abs(g)) < tol:
            break
        w = p * (1.0 - p)
        H = np.bincount(ab, w, M * M).reshape(M, M)
        H = -(H + H.T)
        H[np.diag_indices(M)] += np.bincount(a, w, M) + np.bincount(b, w, M) + ridge
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            fn = objective(th - t * step)
            if fn <= f + 1e-12 * abs(f) or t < 1e-6:
                break
            t *= 0.5
        th = th - t * step
        f = fn
    if not np.all(np.isfinite(th)):
        raise FloatingPointError("nonfinite Bradley-Terry fit")
    return th


def influence_gaps(a, b, s, theta, hi, lo, n_models, ridge=RIDGE):
    """First-order change of theta[hi]-theta[lo] if each row were removed (negative = closes the gap)."""
    M = int(n_models)
    a = a.astype(np.intp)
    b = b.astype(np.intp)
    p = 1.0 / (1.0 + np.exp(-(theta[a] - theta[b])))
    w = p * (1.0 - p)
    H = np.bincount(a * M + b, w, M * M).reshape(M, M)
    H = -(H + H.T)
    H[np.diag_indices(M)] += np.bincount(a, w, M) + np.bincount(b, w, M) + ridge
    e = np.zeros(M)
    e[hi], e[lo] = 1.0, -1.0
    v = np.linalg.solve(H, e)
    return -(s - p) * (v[a] - v[b])


def case_target_pair(theta, kind):
    order = np.lexsort((np.arange(len(theta)), -theta))
    M = len(theta)
    if kind in ("top", "perm_top"):
        return int(order[0]), int(order[1])
    mid = M // 2          # ranks floor(M/2) and floor(M/2)+1 (1-indexed)
    return int(order[mid - 1]), int(order[mid])


# ----------------------------------------------------------------------------------------------
# Resources
# ----------------------------------------------------------------------------------------------
def source_dir():
    value = os.environ.get("TASK_SOURCE_DIR")
    return value if value else os.path.dirname(os.path.abspath(__file__))


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def resource_path(name):
    return os.path.join(source_dir(), RESOURCE_ROOT, name)


def verify_resources():
    for name, digest in RESOURCE_SHA256.items():
        path = resource_path(name)
        if not os.path.isfile(path) or file_sha256(path) != digest:
            raise IntegrityFailure("resource_checksum_mismatch")


def load_table(name):
    z = np.load(resource_path(name))
    table = {k: z[k] for k in ("a", "b", "y", "doc_hash")}
    table["n_models"] = int(z["n_models"])
    n = len(table["y"])
    if not (len(table["a"]) == len(table["b"]) == n == len(table["doc_hash"])) or n > MAX_ROWS:
        raise IntegrityFailure("table_shape_invalid")
    if int(max(table["a"].max(), table["b"].max())) >= table["n_models"] or int(table["y"].max()) > 2:
        raise IntegrityFailure("table_values_invalid")
    return table


def hash_set(array):
    return {bytes(row) for row in array}


def check_disjointness(tables):
    sets = {name: hash_set(t["doc_hash"]) for name, t in tables.items()}
    names = sorted(sets)
    for i, first in enumerate(names):
        for second in names[i + 1:]:
            if sets[first] & sets[second]:
                raise IntegrityFailure("content_overlap")


def smoke_reduce(table, rng_seed):
    """Deterministic ~SMOKE_ROWS-row subsample restricted to the most frequent models (same schema)."""
    a, b, y = table["a"], table["b"], table["y"]
    counts = np.bincount(np.concatenate([a, b]), minlength=table["n_models"])
    keep_models = np.sort(np.argsort(-counts, kind="stable")[:SMOKE_MAX_MODELS])
    in_set = np.zeros(table["n_models"], bool)
    in_set[keep_models] = True
    rows = np.flatnonzero(in_set[a] & in_set[b])
    rng = np.random.default_rng(rng_seed)
    if len(rows) > SMOKE_ROWS:
        rows = np.sort(rng.choice(rows, SMOKE_ROWS, replace=False))
    remap = -np.ones(table["n_models"], dtype=np.int64)
    remap[keep_models] = np.arange(len(keep_models))
    return {"a": remap[a[rows]].astype(np.uint16), "b": remap[b[rows]].astype(np.uint16), "y": y[rows],
            "doc_hash": table["doc_hash"][rows], "n_models": int(len(keep_models))}


class CaseData:
    """Evaluator-private state of one declared case (never sent to the candidate)."""

    def __init__(self, spec, base_table):
        self.id = spec["id"]
        self.family = spec["family"]
        self.kind = spec["kind"]
        self.real = spec.get("real")
        t = base_table
        self.a, self.b = t["a"].astype(np.int64), t["b"].astype(np.int64)
        self.M = t["n_models"]
        self.N = len(t["y"])
        y = t["y"].copy()
        self.nonvacuous = True
        self.perm_stats = None
        theta_real = fit_bt(self.a, self.b, outcome_scores(y), self.M)
        if self.kind == "perm_top":
            rng = np.random.default_rng(PERM_SEED + int(spec["perm_salt"]))
            perm = rng.permutation(self.N)
            y_perm = y[perm]
            frac = np.bincount(y, minlength=3) / self.N
            expected_moved = 1.0 - float(np.sum(frac ** 2))
            moved = float(np.mean(y_perm != y))
            theta_perm = fit_bt(self.a, self.b, outcome_scores(y_perm), self.M)
            ratio = float(np.std(theta_perm) / max(np.std(theta_real), 1e-12))
            self.nonvacuous = bool(moved >= 0.9 * expected_moved and ratio <= 0.5)
            self.perm_stats = (moved, expected_moved, ratio)
            y = y_perm
        self.y = y
        self.s = outcome_scores(y)
        self.theta = fit_bt(self.a, self.b, self.s, self.M)
        self.hi, self.lo = case_target_pair(self.theta, self.kind)
        self.cap = int(math.ceil(CAP_FRACTION * self.N))
        self.gap = float(self.theta[self.hi] - self.theta[self.lo])

    def flips(self, removed):
        removed = np.asarray(removed, dtype=np.int64)
        keep = np.ones(self.N, bool)
        keep[removed] = False
        th = fit_bt(self.a[keep], self.b[keep], self.s[keep], self.M, theta0=self.theta)
        return bool(th[self.hi] < th[self.lo])

    def score_of(self, k, flipped):
        if not flipped or k is None or k < 1 or k > self.cap:
            return 0.0
        return 1.0 - k / self.cap


def prefix_min_k(case, order, check_clock):
    n = min(case.cap, len(order))
    check_clock()
    if n < 1 or not case.flips(order[:n]):
        return None
    lo, hi = 0, n
    while hi - lo > 1:
        mid = (lo + hi) // 2
        check_clock()
        if case.flips(order[:mid]):
            hi = mid
        else:
            lo = mid
    return hi


def compute_baselines(case, draws, check_clock):
    """Evaluator-owned baselines B0-B3; scored with the same episode score."""
    out = {}
    check_clock()
    out["B0_empty_flip"] = case.flips(np.zeros(0, dtype=np.int64))
    scores = []
    flips = 0
    for d in range(draws):
        rng = np.random.default_rng(910000 + 1000 * (hash_case_id(case.id)) + d)
        order = rng.permutation(case.N)[:case.cap]
        k = prefix_min_k(case, order, check_clock)
        scores.append(case.score_of(k, k is not None))
        flips += int(k is not None)
    out["B1_score"] = float(np.mean(scores))
    out["B1_flips"] = flips
    out["B1_draws"] = draws
    gaps = influence_gaps(case.a, case.b, case.s, case.theta, case.hi, case.lo, case.M)
    order = np.argsort(gaps, kind="stable")[:case.cap]
    k = prefix_min_k(case, order, check_clock)
    out["B2_k"] = k
    out["B2_score"] = case.score_of(k, k is not None)
    s_opp = np.where(case.y == 0, case.a, np.where(case.y == 1, case.b, -1))
    s_los = np.where(case.y == 0, case.b, np.where(case.y == 1, case.a, -1))
    rows = np.flatnonzero(s_opp == case.hi)
    rows = rows[np.argsort(-case.theta[s_los[rows]], kind="stable")][:case.cap]
    k = prefix_min_k(case, rows, check_clock)
    out["B3_k"] = k
    out["B3_score"] = case.score_of(k, k is not None)
    return out


def hash_case_id(case_id):
    return int.from_bytes(hashlib.sha256(case_id.encode()).digest()[:2], "big")


# ----------------------------------------------------------------------------------------------
# Candidate payloads
# ----------------------------------------------------------------------------------------------
def encode_array(arr, dtype):
    little = np.asarray(arr).astype(dtype)
    return {"dtype": little.dtype.name, "shape": [int(little.shape[0])], "encoding": "base64-le",
            "data": base64.b64encode(little.tobytes()).decode("ascii")}


def episode_payload(case, case_index, seed, chunk_rows):
    rng = np.random.default_rng([case_index, int(seed), 91823])
    model_perm = rng.permutation(case.M)
    row_perm = rng.permutation(case.N)
    a = model_perm[case.a[row_perm]]
    b = model_perm[case.b[row_perm]]
    y = case.y[row_perm]
    n_chunks = int(math.ceil(case.N / chunk_rows))
    if n_chunks > MAX_CHUNKS:
        raise IntegrityFailure("too_many_chunks")
    chunks = []
    for i in range(n_chunks):
        sl = slice(i * chunk_rows, min((i + 1) * chunk_rows, case.N))
        chunks.append({"op": "load_chunk", "chunk_index": i, "n_chunks": n_chunks, "n_rows_total": int(case.N),
                       "n_models": int(case.M), "a": encode_array(a[sl], "<u2"), "b": encode_array(b[sl], "<u2"),
                       "y": encode_array(y[sl], "u1")})
    return chunks, row_perm, int(model_perm[case.hi]), int(model_perm[case.lo])


def analyze_request(case, hi, lo, deadline_seconds):
    return {"op": "analyze", "hi": hi, "lo": lo, "k_cap": int(case.cap), "tie_as_half_win": TIE_AS_HALF_WIN,
            "ridge": RIDGE, "deadline_seconds": float(max(1.0, math.floor(deadline_seconds)))}


def parse_removed(response, cap, n_rows):
    if type(response) is not dict or "removed" not in response or not set(response) <= {"removed", "diagnostics"}:
        raise CandidateRpcError("malformed_response")
    diag = response.get("diagnostics")
    if diag is not None:
        if type(diag) is not dict or len(diag) > 32:
            raise CandidateRpcError("malformed_response")
        for key, value in diag.items():
            if (type(key) is not str or len(key) > 80 or type(value) not in (int, float)
                    or not math.isfinite(value)):
                raise CandidateRpcError("malformed_response")
    rem = response["removed"]
    if (type(rem) is not dict or set(rem) != {"dtype", "shape", "encoding", "data"} or rem["dtype"] != "uint32"
            or rem["encoding"] != "base64-le" or type(rem["shape"]) is not list or len(rem["shape"]) != 1
            or type(rem["shape"][0]) is not int or not 0 <= rem["shape"][0] <= cap or type(rem["data"]) is not str):
        raise CandidateRpcError("malformed_response")
    k = rem["shape"][0]
    try:
        raw = base64.b64decode(rem["data"].encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError):
        raise CandidateRpcError("malformed_response") from None
    if len(raw) != 4 * k:
        raise CandidateRpcError("malformed_response")
    idx = np.frombuffer(raw, dtype="<u4").astype(np.int64)
    if k and (idx.max() >= n_rows or len(np.unique(idx)) != k):
        raise CandidateRpcError("malformed_response")
    return idx


def payload_preflight():
    """Serialize the largest production request/response with envelope, base64 and framing."""
    n = CHUNK_ROWS_FULL
    rng = np.random.default_rng(0)
    chunk = {"op": "load_chunk", "chunk_index": 0, "n_chunks": MAX_CHUNKS, "n_rows_total": MAX_ROWS, "n_models": 65535,
             "a": encode_array(rng.integers(0, 65535, n), "<u2"), "b": encode_array(rng.integers(0, 65535, n), "<u2"),
             "y": encode_array(rng.integers(0, 3, n), "u1")}
    bounded_json_line(chunk)
    cap = int(math.ceil(CAP_FRACTION * MAX_ROWS))
    reply = {"removed": encode_array(rng.permutation(MAX_ROWS)[:cap], "<u4"),
             "diagnostics": {"x%d" % i: 1.5 for i in range(32)}}
    bounded_json_line({"ok": True, "response": reply})
    bounded_json_line(analyze_request(type("C", (), {"cap": cap})(), 65535, 65534, 120.0))


# ----------------------------------------------------------------------------------------------
# Candidate transports
# ----------------------------------------------------------------------------------------------
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
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


RUNNER_SOURCE = r'''
import importlib.util, json, os, sys
proto = os.fdopen(os.dup(1), "w")
os.dup2(2, 1)
path = sys.argv[1]
REPAIR = len(sys.argv) > 2 and sys.argv[2] == "repair"
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
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
spec = importlib.util.spec_from_file_location("candidate_program", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin:
    try:
        reply = {"ok": True, "response": module.handle(json.loads(line))}
        text = json.dumps(reply, allow_nan=False, separators=(",", ":"))
    except BaseException as error:
        if REPAIR:
            report_worker_exception(error)
        name = type(error).__name__
        text = json.dumps({"ok": False, "error": name if name.isidentifier() and len(name) < 80 else "Error"})
    proto.write(text + "\n")
    proto.flush()
'''


class BrokerTransport:
    """Trusted in-process broker proxy: loaded only for the fixed proxy path with the socket signal."""

    def __init__(self, path):
        spec = importlib.util.spec_from_file_location("candidate_proxy", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle

    def call(self, request, timeout):
        box = {}
        done = threading.Event()

        def run():
            try:
                box["response"] = self.handle(request)
            except BaseException as error:        # noqa: BLE001 - classified below
                box["error"] = error
            finally:
                done.set()

        threading.Thread(target=run, daemon=True, name="broker-call").start()
        if not done.wait(timeout):
            raise TimeoutError("candidate rpc timeout")
        if "error" in box:
            if isinstance(box["error"], TimeoutError):
                raise TimeoutError("candidate rpc timeout")
            raise CandidateRpcError("transport_error")
        try:
            bounded_json_line(box["response"])
        except (ValueError, TypeError, OverflowError, RecursionError) as error:
            oversized = isinstance(error, ValueError) and "wire limit" in str(error)
            raise CandidateRpcError("oversized_response" if oversized else "malformed_response") from None
        return box["response"]

    def close(self):
        return None


class NativeTransport:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke runs)."""

    def __init__(self, program_path, hard_deadline):
        self.program_path = os.path.abspath(program_path)
        self.hard_deadline = hard_deadline
        self.proc = None
        self.capture = None
        self.buffer = b""
        self.stderr_snapshots = []
        self.workdir = tempfile.mkdtemp(prefix="cand_")

    def _start(self):
        python, env = candidate_subprocess_settings(os.environ)
        env["OMP_NUM_THREADS"] = env["OPENBLAS_NUM_THREADS"] = env["MKL_NUM_THREADS"] = str(CANDIDATE_THREADS)
        cpu = cpu_limit_seconds(max(60.0, self.hard_deadline - time.monotonic()), CANDIDATE_THREADS)

        def limits():
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
            resource.setrlimit(resource.RLIMIT_AS, (CANDIDATE_AS_BYTES, CANDIDATE_AS_BYTES))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

        self.proc = subprocess.Popen([python, "-c", RUNNER_SOURCE, self.program_path] + (["repair"] if REPAIR_VISIBLE else []), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, cwd=self.workdir,
                                     shell=False, start_new_session=True, preexec_fn=limits)
        self.capture = BoundedWorkerStderr(self.proc.stderr)
        self.buffer = b""

    def _stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            if proc.poll() is None:
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
                    proc.wait(timeout=1.0)
        finally:
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
            try:
                self.stderr_snapshots.append(self.capture.close())
            except RuntimeError:
                pass

    def call(self, request, timeout):
        if request.get("op") == "reset":
            self._stop()
            self._start()
        if self.proc is None or self.proc.poll() is not None:
            self._stop()
            raise CandidateRpcError("transport_closed")
        deadline = time.monotonic() + timeout
        try:
            self.proc.stdin.write(bounded_json_line(request))
            self.proc.stdin.flush()
        except (OSError, ValueError):
            self._stop()
            raise CandidateRpcError("transport_closed") from None
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._stop()
                    raise TimeoutError("candidate rpc timeout")
                if not selector.select(timeout=min(remaining, 0.5)):
                    continue
                chunk = os.read(fd, 1 << 20)
                if not chunk:
                    self._stop()
                    raise CandidateRpcError("transport_closed")
                self.buffer += chunk
                if len(self.buffer) >= WIRE_LIMIT:
                    self._stop()
                    raise CandidateRpcError("oversized_response")
        line, _, self.buffer = self.buffer.partition(b"\n")
        try:
            reply = json.loads(line.decode("utf-8"))
        except ValueError:
            self._stop()
            raise CandidateRpcError("malformed_response") from None
        if type(reply) is not dict or reply.get("ok") is not True or "response" not in reply:
            raise CandidateRpcError("candidate_exception")
        return reply["response"]

    def close(self):
        self._stop()
        try:
            os.rmdir(self.workdir)
        except OSError:
            pass


# ----------------------------------------------------------------------------------------------
# Aggregation (hierarchy fixed before evaluation)
# ----------------------------------------------------------------------------------------------
def mean(values):
    return float(sum(values) / len(values))


def aggregate(case_scores, ref_scores):
    """episode -> case (weight 1/|seeds|) -> family (equal weight) -> combined (equal weight)."""
    fam = {f: mean([case_scores[c["id"]] for c in CASES if c["family"] == f]) for f in FAMILIES}
    return fam, mean([fam[f] for f in FAMILIES])


def worst_case_metrics():
    m = {name: 0.0 for name in METRIC_NAMES}
    m["mean_budget_fraction"] = 1.0
    m["control_gap_permuted_minus_real"] = -1.0
    return m


def write_json(path, value):
    tmp = path + ".tmp"
    with open(tmp, "w") as handle:
        json.dump(value, handle, allow_nan=False)
    os.replace(tmp, path)


def say(line):
    if DIAGNOSTIC_VISIBLE:
        print(line[:256], file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------------------------
# Main evaluation
# ----------------------------------------------------------------------------------------------
def build_cases():
    tables = {}
    for spec in CASES:
        if spec["table"] not in tables:
            tables[spec["table"]] = load_table(spec["table"])
    check_disjointness(tables)
    cases = {}
    for spec in CASES:
        t = tables[spec["table"]]
        if SMOKE:
            t = smoke_reduce(t, 7 + hash_case_id(spec["table"]))
        cases[spec["id"]] = CaseData(spec, t)
    return cases


def run(program_path, results_dir):
    clock = time.monotonic
    hard_deadline = T_START + WALL_SECONDS - STARTUP_ALLOWANCE
    require_joint_workload_budget({
        "episode_count": len(SEEDS) * len(CASES), "method_count": 1, "wall_seconds": WALL_SECONDS,
        "startup_seconds": STARTUP_ALLOWANCE + BASELINE_ALLOWANCE, "reset_seconds": RESET_TIMEOUT,
        "cleanup_seconds": EPISODE_OVERHEAD, "finish_seconds": FINISH_RESERVE, "work_seconds": RPC_CAP + 30.0})
    payload_preflight()
    verify_resources()
    cases = build_cases()
    nonvacuous = all(c.nonvacuous for c in cases.values())
    for c in cases.values():
        say("case %s n=%d models=%d cap=%d gap=%.5f%s" % (
            c.id, c.N, c.M, c.cap, c.gap,
            "" if c.perm_stats is None else " perm moved=%.3f exp=%.3f std_ratio=%.3f nonvacuous=%d" % (
                c.perm_stats + (int(c.nonvacuous),))))

    # --- evaluator-owned baselines (before the first reset; failure is fail-fast) ---------------
    baseline_deadline = T_START + BASELINE_ALLOWANCE
    failures = []

    def check_clock():
        if clock() > baseline_deadline:
            raise TimeoutError()

    baselines = {}
    try:
        for cid, case in cases.items():
            baselines[cid] = compute_baselines(case, SMOKE_DRAWS if SMOKE else FULL_DRAWS, check_clock)
    except TimeoutError:
        fail_required_baseline("baseline_timeout", lambda: None, lambda cat: failures.append(cat))
    except (np.linalg.LinAlgError, FloatingPointError):
        fail_required_baseline("baseline_result_failure", lambda: None, lambda cat: failures.append(cat))
    empty_ok = all(not b["B0_empty_flip"] for b in baselines.values())
    for cid, b in baselines.items():
        say("baseline %s B1=%.4f(%d/%d flips) B2_k=%s B3_k=%s" % (
            cid, b["B1_score"], b["B1_flips"], b["B1_draws"], b["B2_k"], b["B3_k"]))

    # --- transport ---------------------------------------------------------------------------
    brokered = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET")) and program_path == BROKER_PROXY_PATH
    if program_path == BROKER_PROXY_PATH and not os.environ.get("AGENTIC_CANDIDATE_SOCKET"):
        raise IntegrityFailure("broker_signal_missing")
    transport = BrokerTransport(program_path) if brokered else NativeTransport(program_path, hard_deadline)

    episode_seeds = SEEDS[:1] if SMOKE else SEEDS
    episodes = [{"case": spec["id"], "case_index": ci, "seed": seed}
                for ci, spec in enumerate(CASES) for seed in episode_seeds]
    reset_sequence = list(SMOKE_RESET_SEQUENCE if SMOKE else RESET_SEQUENCE)
    if [e["seed"] for e in episodes] != reset_sequence:
        raise IntegrityFailure("reset_sequence_mismatch")
    chunk_rows = CHUNK_ROWS_SMOKE if SMOKE else CHUNK_ROWS_FULL
    counters = {"rpc": 0, "resets": 0}
    durations = [0.0] * len(episodes)
    index_of = {id(e): i for i, e in enumerate(episodes)}

    def rpc(request, timeout):
        if counters["rpc"] >= MAX_CALLS:
            raise CandidateRpcError("rpc_budget_exhausted")
        counters["rpc"] += 1
        if request.get("op") == "reset":
            counters["resets"] += 1
        return transport.call(request, timeout)

    def worst_case(_episode):
        return {"score": 0.0, "flip": False, "k": None, "frac": 1.0, "failed": True, "removed": None}

    def evaluate(episode, call, work_deadline):
        started = clock()
        try:
            case = cases[episode["case"]]
            chunks, row_perm, hi, lo = episode_payload(case, episode["case_index"], episode["seed"], chunk_rows)
            for chunk in chunks:
                response = call(chunk)
                if response != {"ok": True}:
                    raise CandidateRpcError("malformed_response")
            response = call(analyze_request(case, hi, lo, min(RPC_CAP, work_deadline - clock())))
            removed = parse_removed(response, case.cap, case.N)
            original = row_perm[removed]
            k = int(len(original))
            flipped = bool(k >= 1 and case.flips(original))
            score = case.score_of(k, flipped)
            return {"score": score, "flip": flipped, "k": k if flipped else None,
                    "frac": (k / case.cap) if flipped else 1.0, "failed": False, "removed": original}
        finally:
            durations[index_of[id(episode)]] = clock() - started

    def record_failure(failure):
        if DIAGNOSTIC_VISIBLE:
            say("episode_failure component=%s category=%s operation=%s" % (
                failure["component"], failure["category"], failure["operation"]))

    outcomes, complete = [worst_case(e) for e in episodes], False
    try:
        if failures:
            raise RequiredBaselineFailure(failures[0])
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT,
            episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP, clock=clock, rpc=rpc, evaluate=evaluate,
            worst_case=worst_case, record_failure=record_failure)
    finally:
        try:
            transport.close()
        except Exception:
            say("cleanup_failure component=candidate category=cleanup operation=close")
    snapshots = getattr(transport, "stderr_snapshots", [])
    return {"cases": cases, "baselines": baselines, "episodes": episodes, "outcomes": outcomes,
            "complete": complete, "empty_ok": empty_ok, "nonvacuous": nonvacuous, "durations": durations,
            "resets": counters["resets"], "snapshots": snapshots, "baseline_ok": not failures}


def score_run(result):
    cases, episodes, outcomes = result["cases"], result["episodes"], result["outcomes"]
    per_case = {spec["id"]: [] for spec in CASES}
    for e, o in zip(episodes, outcomes):
        per_case[e["case"]].append(o)
    case_score = {cid: mean([o["score"] for o in os_]) for cid, os_ in per_case.items()}
    case_failed = {cid: any(o["failed"] for o in os_) for cid, os_ in per_case.items()}
    fam, combined = aggregate({c: case_score[c] for c in case_score}, None)
    noncontrol = [o for e, o in zip(episodes, outcomes) if CASE_BY_ID[e["case"]]["family"] != "control"]
    flip_rate = mean([1.0 if o["flip"] else 0.0 for o in noncontrol])
    budget = mean([o["frac"] for o in noncontrol])
    base = result["baselines"]
    ref_rand_case = {c: base[c]["B1_score"] for c in base}
    ref_inf_case = {c: base[c]["B2_score"] for c in base}
    _, ref_rand = aggregate(ref_rand_case, None)
    _, ref_inf = aggregate(ref_inf_case, None)
    gaps = []
    gap_missing = False
    for spec in CASES:
        if spec["family"] == "control":
            if case_failed[spec["id"]] or case_failed[spec["real"]]:
                gap_missing = True
            gaps.append(case_score[spec["id"]] - case_score[spec["real"]])
    control_gap = -1.0 if gap_missing else mean(gaps)
    metrics = {"combined_score": combined, "flip_rate": flip_rate, "mean_budget_fraction": budget,
               FAMILY_METRIC[FAMILIES[0]]: fam[FAMILIES[0]], FAMILY_METRIC[FAMILIES[1]]: fam[FAMILIES[1]],
               "reference_random_score": ref_rand, "reference_influence_score": ref_inf,
               "control_gap_permuted_minus_real": control_gap}
    return metrics, case_score


def copy_control(result):
    """Apply the candidate's removal set for a real top case to the other design's top case (evaluator side)."""
    cases, episodes, outcomes = result["cases"], result["episodes"], result["outcomes"]
    trials = flips = 0
    for src_id, dst_id in COPY_PAIRS:
        src, dst = cases[src_id], cases[dst_id]
        for e, o in zip(episodes, outcomes):
            if e["case"] != src_id or o["removed"] is None or len(o["removed"]) == 0:
                continue
            mapped = (o["removed"].astype(np.float64) * dst.N / src.N).astype(np.int64)
            mapped = mapped[mapped < dst.N]
            _, first = np.unique(mapped, return_index=True)
            mapped = mapped[np.sort(first)][:dst.cap]
            trials += 1
            flips += int(dst.flips(mapped))
    return trials, flips


def finalize(result, results_dir, duration):
    metrics, case_score = score_run(result)
    if any(not math.isfinite(v) for v in metrics.values()):
        raise IntegrityFailure("nonfinite_metric")
    trials, flips = copy_control(result) if result["baseline_ok"] else (0, 0)
    correct = bool(result["baseline_ok"] and result["empty_ok"] and result["nonvacuous"]
                   and result["resets"] == len(result["episodes"]))
    feasible = bool(correct and result["complete"] and not SMOKE and duration <= WALL_SECONDS - FINISH_RESERVE)
    for e, o in zip(result["episodes"], result["outcomes"]):
        say("episode case=%s seed=%d flip=%d k=%s frac=%.5f score=%.5f failed=%d" % (
            e["case"], e["seed"], int(o["flip"]), o["k"], o["frac"], o["score"], int(o["failed"])))
    say("controls empty_ok=%d nonvacuous=%d copy_flips=%d/%d complete=%d" % (
        int(result["empty_ok"]), int(result["nonvacuous"]), flips, trials, int(result["complete"])))
    write_results(results_dir, metrics, correct, feasible, result, duration)
    if REPAIR_VISIBLE and not result["complete"]:
        for snap in result["snapshots"]:
            if snap.get("stderr"):
                sys.stderr.write(snap["stderr"][:4096])


def write_results(results_dir, metrics, correct, feasible, result, duration):
    os.makedirs(results_dir, exist_ok=True)
    assert set(metrics) == set(METRIC_NAMES)
    write_json(os.path.join(results_dir, "metrics.json"), {k: float(metrics[k]) for k in METRIC_NAMES})
    write_json(os.path.join(results_dir, "correct.json"), {"correct": bool(correct)})
    seeds = sorted(set(e["seed"] for e in result["episodes"]))
    records = []
    for seed in seeds:
        idx = [i for i, e in enumerate(result["episodes"]) if e["seed"] == seed]
        per_case = {}
        for i in idx:
            per_case.setdefault(result["episodes"][i]["case"], []).append(result["outcomes"][i]["score"])
        cs = {spec["id"]: mean(per_case[spec["id"]]) for spec in CASES}
        _, seed_score = aggregate(cs, None)
        records.append({"seed": int(seed), "score": float(seed_score), "correct": bool(correct),
                        "duration_seconds": float(sum(result["durations"][i] for i in idx))})
    write_json(os.path.join(results_dir, "evaluation_evidence.json"), {"schema_version": 1, "episodes": records})
    if QUALIFICATION:
        write_json(os.path.join(results_dir, "qualification.json"), {"schema_version": 1, "feasible": bool(feasible)})


def penalty_outputs(results_dir, duration, category):
    """Operational/integrity failure: predeclared finite worst-case metrics, correct false."""
    os.makedirs(results_dir, exist_ok=True)
    metrics = worst_case_metrics()
    write_json(os.path.join(results_dir, "metrics.json"), {k: float(metrics[k]) for k in METRIC_NAMES})
    write_json(os.path.join(results_dir, "correct.json"), {"correct": False})
    records = [{"seed": int(s), "score": 0.0, "correct": False, "duration_seconds": float(duration / len(SEEDS))}
               for s in SEEDS]
    write_json(os.path.join(results_dir, "evaluation_evidence.json"), {"schema_version": 1, "episodes": records})
    if QUALIFICATION:
        write_json(os.path.join(results_dir, "qualification.json"), {"schema_version": 1, "feasible": False})
    say("evaluation_failure category=%s" % bounded_failure_name(category, "unknown"))


CASE_BY_ID = {spec["id"]: spec for spec in CASES}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    started = time.monotonic()
    try:
        result = run(args.program_path, args.results_dir)
        finalize(result, args.results_dir, time.monotonic() - started)
    except (RequiredBaselineFailure, IntegrityFailure, TimeoutError) as error:
        category = getattr(error, "category", "timeout")
        penalty_outputs(args.results_dir, time.monotonic() - started, category)
    except Exception as error:      # noqa: BLE001 - bounded diagnostic then non-zero exit
        message = str(error).replace("\n", " ")[:160] if PLANE == "search" else "evaluation failed"
        print("evaluator_exception type=%s message=%s" % (type(error).__name__[:60], message), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
