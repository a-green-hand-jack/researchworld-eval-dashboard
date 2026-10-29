#!/usr/bin/env python3
"""Sealed final evaluator: statistics-only prediction of random-walk cover time on small graphs.

Self-contained; reads only ``resources/final`` and never imports evaluate.py or search files.
The shared training pool and the search eval pool are regenerated from their non-secret seeds
(the search eval pool only as an isomorphism-dedup reference); the final eval pool comes from
privileged final data seeds and is made isomorphism-disjoint from both. The candidate
(``python_rpc_v1:handle``) fits on the training pool and predicts the final eval pool from six
graph statistics. Per episode the transcript is exactly reset, fit, predict, predict, predict
(main + permuted-feature control + reordered-copy control in an evaluator-private order).
Diagnostics stay sealed: no per-episode details are written to stderr.
"""

import os

for _thread_var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_thread_var, "2")

import argparse
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
import networkx as nx

PLANE = "final"
BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
WIRE_LIMIT = 64 * 1024 * 1024
LOG_CAP = math.log(1000.0)
ORDER_TOL = 1e-6

FAMILIES = (
    "path", "cycle", "star", "complete", "grid", "binary_tree", "lollipop",
    "random_tree", "erdos_renyi", "random_regular3",
)
DET_FAMILIES = FAMILIES[:7]
RANDOM_FAMILIES = FAMILIES[7:]
FEATURE_NAMES = ["n", "m", "mean_degree", "max_degree", "min_degree", "diameter"]
N_MIN, N_MAX = 5, 30
SPLIT_NAMES = {0: "train", 1: "search_eval", 2: "final_eval"}

PRODUCTION_RESET_SEQUENCE = (211, 212, 213)
SMOKE_RESET_SEQUENCE = (211,)
OPS_PER_EPISODE = 5  # reset, fit, predict x3
MAX_RPC_PRODUCTION = len(PRODUCTION_RESET_SEQUENCE) * OPS_PER_EPISODE  # 15
MAX_RPC_SMOKE = len(SMOKE_RESET_SEQUENCE) * OPS_PER_EPISODE  # 5

WALL_SECONDS = 600.0
STARTUP_ALLOWANCE = 40.0
SETUP_ALLOWANCE = 220.0
FINISH_RESERVE = 40.0
RESET_TIMEOUT = 5.0
FIT_TIMEOUT = 45.0
PREDICT_TIMEOUT = 10.0
EPISODE_OVERHEAD = 6.0  # stdin close/wait 1 s + SIGTERM wait 1 s + SIGKILL wait 1 s + stderr reader 1 s + bookkeeping
EPISODE_WORK = FIT_TIMEOUT + 3 * PREDICT_TIMEOUT
CANDIDATE_MEMORY_BYTES = 1536 * 1024 * 1024

CONFIG_KEYS = {
    "schema_version", "plane", "train_data_seed", "train_label_seed", "search_eval_data_seed",
    "final_eval_data_seed", "final_eval_label_seed", "sim_check_seed", "episode_salt", "bootstrap_seed",
    "bootstrap_reps", "smoke_bootstrap_reps", "train_random_per_family", "search_eval_random_per_family",
    "final_eval_random_per_family", "walks", "smoke_walks", "smoke_graphs_per_family",
}


# ----------------------------------------------------------------------------------------
# Required-worker failure identity helpers
# ----------------------------------------------------------------------------------------
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


def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


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


# ----------------------------------------------------------------------------------------
# Bounded stderr capture for the native candidate subprocess
# ----------------------------------------------------------------------------------------
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
    return PLANE == "search" and (
        os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1" or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    )


def emit_line(text):
    sys.stderr.write(text[:256].replace("\n", " ") + "\n")
    sys.stderr.flush()


# ----------------------------------------------------------------------------------------
# Generic helpers
# ----------------------------------------------------------------------------------------
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


def fixed_weight_mean(values):
    arr = np.asarray(values, dtype=float)
    if arr.size == 0 or not np.all(np.isfinite(arr)):
        raise ValueError("invalid aggregation input")
    return float(arr.mean())


def stable_int(text):
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "little")


def candidate_subprocess_settings(parent_environment):
    runtime_names = ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ")
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(
        HOME="/nonexistent",
        PYTHONNOUSERSITE="1",
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONUNBUFFERED="1",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        NUMEXPR_NUM_THREADS="1",
        CUDA_VISIBLE_DEVICES="",
    )
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


def require_plane_budget(episode_count):
    needed = STARTUP_ALLOWANCE + SETUP_ALLOWANCE + FINISH_RESERVE + episode_count * (
        RESET_TIMEOUT + EPISODE_WORK + EPISODE_OVERHEAD)
    if needed > WALL_SECONDS:
        raise ValueError("declared plane workload exceeds the wall budget")


# ----------------------------------------------------------------------------------------
# Graph synthesis
# ----------------------------------------------------------------------------------------
def make_graph(family, params, source_id, n, edges):
    edges = sorted({(min(u, v), max(u, v)) for u, v in edges if u != v})
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    return {"family": family, "params": params, "source_id": source_id, "n": n, "edges": edges, "adj": adj}


def det_graph(family, params):
    if family == "path":
        n = params[0]
        edges = [(i, i + 1) for i in range(n - 1)]
    elif family == "cycle":
        n = params[0]
        edges = [(i, (i + 1) % n) for i in range(n)]
    elif family == "star":
        n = params[0]
        edges = [(0, i) for i in range(1, n)]
    elif family == "complete":
        n = params[0]
        edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    elif family == "binary_tree":
        n = params[0]
        edges = [((i - 1) // 2, i) for i in range(1, n)]
    elif family == "grid":
        a, b = params
        n = a * b
        edges = []
        for r in range(a):
            for c in range(b):
                v = r * b + c
                if c + 1 < b:
                    edges.append((v, v + 1))
                if r + 1 < a:
                    edges.append((v, v + b))
    elif family == "lollipop":
        k, length = params
        n = k + length
        edges = [(i, j) for i in range(k) for j in range(i + 1, k)]
        edges += [(i, i + 1) for i in range(k - 1, n - 1)]
    else:
        raise ValueError("unknown deterministic family")
    sid = family + ":" + "x".join(str(p) for p in params)
    return make_graph(family, list(params), sid, n, edges)


def det_catalogue():
    """Public deterministic catalogue: every declared shape with its fixed split."""
    out = []
    for family in ("path", "cycle", "star", "complete", "binary_tree"):
        for n in range(N_MIN, N_MAX + 1):
            out.append((family, (n,), SPLIT_NAMES[n % 3]))
    shapes = sorted(((a, b) for a in range(2, 6) for b in range(a, 3 * a + 1)
                     if N_MIN <= a * b <= N_MAX), key=lambda s: (s[0] * s[1], s[0]))
    for i, shape in enumerate(shapes):
        out.append(("grid", shape, SPLIT_NAMES[i % 3]))
    for n in range(N_MIN, N_MAX + 1):
        for k in sorted({math.ceil(n / 2), math.ceil(2 * n / 3)}):
            if k >= 3 and n - k >= 1:
                out.append(("lollipop", (k, n - k), SPLIT_NAMES[n % 3]))
    return out


def random_graph(family, data_seed, pool_tag, slot, attempt):
    rng = np.random.default_rng(np.random.SeedSequence(
        [int(data_seed), FAMILIES.index(family), stable_int(pool_tag) % (2 ** 32), slot, attempt]))
    sid = f"{family}:{pool_tag}:seed{data_seed}:slot{slot}:try{attempt}"
    if family == "random_tree":
        n = int(rng.integers(N_MIN, N_MAX + 1))
        seq = [int(x) for x in rng.integers(0, n, size=n - 2)]
        degree = [1] * n
        for x in seq:
            degree[x] += 1
        edges = []
        for x in seq:
            leaf = min(i for i in range(n) if degree[i] == 1)
            edges.append((leaf, x))
            degree[leaf] -= 1
            degree[x] -= 1
        u, v = [i for i in range(n) if degree[i] == 1]
        edges.append((u, v))
        return make_graph(family, [n], sid, n, edges)
    if family == "erdos_renyi":
        n = int(rng.integers(N_MIN, N_MAX + 1))
        lo = 2.0 * math.log(n) / n
        hi = max(0.5, lo)
        p = min(1.0, float(rng.uniform(lo, hi)) if hi > lo else lo)
        for _ in range(500):
            mask = np.triu(rng.random((n, n)) < p, 1)
            edges = [(int(i), int(j)) for i, j in zip(*np.nonzero(mask))]
            g = make_graph(family, [n, round(p, 6)], sid, n, edges)
            if is_connected(g):
                return g
        raise RuntimeError("erdos_renyi generation failed")
    if family == "random_regular3":
        n = 2 * int(rng.integers(3, N_MAX // 2 + 1))
        for _ in range(5000):
            stubs = np.repeat(np.arange(n), 3)
            rng.shuffle(stubs)
            pairs = stubs.reshape(-1, 2)
            if np.any(pairs[:, 0] == pairs[:, 1]):
                continue
            keyed = {(int(min(a, b)), int(max(a, b))) for a, b in pairs}
            if len(keyed) != len(pairs):
                continue
            g = make_graph(family, [n], sid, n, list(keyed))
            if is_connected(g):
                return g
        raise RuntimeError("random_regular3 generation failed")
    raise ValueError("unknown random family")


def bfs_distances(adj, source):
    n = len(adj)
    dist = [-1] * n
    dist[source] = 0
    queue = collections.deque([source])
    while queue:
        u = queue.popleft()
        for w in adj[u]:
            if dist[w] < 0:
                dist[w] = dist[u] + 1
                queue.append(w)
    return dist


def is_connected(g):
    return min(bfs_distances(g["adj"], 0)) >= 0


def graph_features(g):
    n = g["n"]
    m = len(g["edges"])
    degs = [len(a) for a in g["adj"]]
    diam = max(max(bfs_distances(g["adj"], s)) for s in range(n))
    return [float(n), float(m), 2.0 * m / n, float(max(degs)), float(min(degs)), float(diam)]


class IsoIndex:
    """Isomorphism-normalized content index: WL hash buckets confirmed by exact VF2."""

    def __init__(self):
        self.buckets = {}

    @staticmethod
    def key(g):
        if "wl" not in g:
            G = nx.Graph()
            G.add_nodes_from(range(g["n"]))
            G.add_edges_from(g["edges"])
            g["nx"] = G
            g["wl"] = nx.weisfeiler_lehman_graph_hash(G, iterations=3) + f":{g['n']}:{len(g['edges'])}"
        return g["wl"]

    def find(self, g):
        for other in self.buckets.get(self.key(g), ()):
            if nx.is_isomorphic(g["nx"], other["nx"]):
                return other
        return None

    def add(self, g):
        self.buckets.setdefault(self.key(g), []).append(g)


def smoke_subset(items, smoke, per_family):
    if not smoke or len(items) <= per_family:
        return list(items)
    idx = np.linspace(0, len(items) - 1, per_family).round().astype(int)
    return [items[i] for i in sorted(set(int(i) for i in idx))]


def build_pool(split, data_seed, random_per_family, smoke, per_family, catalogue_index, references):
    """Deterministic pool for one split; random graphs colliding with any reference are resampled."""
    pool = []
    own = IsoIndex()
    catalogue = det_catalogue()
    for family in DET_FAMILIES:
        items = [det_graph(f, p) for f, p, s in catalogue if f == family and s == split]
        for g in smoke_subset(items, smoke, per_family):
            g["pool"] = split
            pool.append(g)
            own.add(g)
    count = min(per_family, random_per_family) if smoke else random_per_family
    for family in RANDOM_FAMILIES:
        for slot in range(count):
            for attempt in range(1000):
                g = random_graph(family, data_seed, split, slot, attempt)
                if catalogue_index.find(g) or own.find(g) or any(r.find(g) for r in references):
                    continue
                g["pool"] = split
                pool.append(g)
                own.add(g)
                break
            else:
                raise RuntimeError("random graph dedup did not converge")
    for g in pool:
        if not is_connected(g) or not (N_MIN <= g["n"] <= N_MAX):
            raise RuntimeError("generated graph violates the declared domain")
        g["x"] = graph_features(g)
    return pool, own


def catalogue_iso_index():
    index = IsoIndex()
    for family, params, _split in det_catalogue():
        index.add(det_graph(family, params))
    return index


def cross_overlap_count(pool, index):
    return sum(1 for g in pool if index.find(g) is not None)


# ----------------------------------------------------------------------------------------
# Monte Carlo cover time and exact baselines
# ----------------------------------------------------------------------------------------
def simulate_cover_times(g, walks, rng):
    n = g["n"]
    m = len(g["edges"])
    deg = np.array([len(a) for a in g["adj"]], dtype=np.int64)
    nbr = np.zeros((n, int(deg.max())), dtype=np.int64)
    for v, a in enumerate(g["adj"]):
        nbr[v, :len(a)] = a
    cap = 40 * 2 * m * (n - 1)
    pos = rng.integers(0, n, size=walks)
    visited = np.zeros((walks, n), dtype=bool)
    visited[np.arange(walks), pos] = True
    count = np.ones(walks, dtype=np.int64)
    times = np.full(walks, cap, dtype=np.int64)
    idx = np.arange(walks)
    step = 0
    while idx.size and step < cap:
        step += 1
        p = pos[idx]
        newp = nbr[p, (rng.random(idx.size) * deg[p]).astype(np.int64)]
        pos[idx] = newp
        fresh = ~visited[idx, newp]
        visited[idx, newp] = True
        count[idx] += fresh
        done = count[idx] == n
        if done.any():
            times[idx[done]] = step
            idx = idx[~done]
    return times.astype(float), int(idx.size)


def label_graphs(graphs, walks, label_seed):
    capped = 0
    for g in graphs:
        rng = np.random.default_rng(np.random.SeedSequence([int(label_seed), stable_int(g["source_id"])]))
        times, c = simulate_cover_times(g, walks, rng)
        capped += c
        g["times"] = times
        g["c_hat"] = float(times.mean())
        g["se"] = float(times.std(ddof=1) / math.sqrt(walks))
    return capped


def harmonic(k):
    return sum(1.0 / i for i in range(1, k + 1))


def simulator_checks(walks, seed):
    """Closed-form checks: cycle n(n-1)/2, complete (n-1)H_{n-1}, path uniform start."""
    cases = [
        (det_graph("cycle", (12,)), 12 * 11 / 2.0),
        (det_graph("complete", (10,)), 9 * harmonic(9)),
        (det_graph("path", (10,)), 81.0 + sum(k * (9 - k) for k in range(10)) / 10.0),
    ]
    ok = True
    for i, (g, exact) in enumerate(cases):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), i]))
        times, capped = simulate_cover_times(g, walks, rng)
        se = times.std(ddof=1) / math.sqrt(walks)
        if capped or not math.isfinite(se) or abs(times.mean() - exact) > 4.0 * se:
            ok = False
    return ok


def max_hitting_time(g):
    n = g["n"]
    A = np.zeros((n, n))
    for u, v in g["edges"]:
        A[u, v] = A[v, u] = 1.0
    P = A / A.sum(axis=1, keepdims=True)
    best = 0.0
    for target in range(n):
        keep = [i for i in range(n) if i != target]
        M = np.eye(n - 1) - P[np.ix_(keep, keep)]
        h = np.linalg.solve(M, np.ones(n - 1))
        best = max(best, float(h.max()))
    return best


def baseline_predictions(train, evals):
    """Evaluator-owned baselines on eval graphs; raises RequiredBaselineFailure if invalid."""
    Xtr = np.array([[1.0, math.log(g["x"][0]), math.log(g["x"][1])] for g in train])
    ytr = np.log(np.array([g["c_hat"] for g in train]))
    beta = np.linalg.solve(Xtr.T @ Xtr + 1e-8 * np.eye(3), Xtr.T @ ytr)
    constant = float(np.exp(ytr.mean()))
    out = {k: [] for k in ("aklrr", "feige_lead", "best_bound", "matthews_ref", "ols_ref", "constant")}
    for g in evals:
        n, m = g["x"][0], g["x"][1]
        aklrr = 2.0 * m * (n - 1.0)
        feige = 4.0 / 27.0 * n ** 3
        out["aklrr"].append(aklrr)
        out["feige_lead"].append(feige)
        out["best_bound"].append(min(aklrr, feige))
        out["matthews_ref"].append(max_hitting_time(g) * harmonic(int(n) - 1))
        out["ols_ref"].append(float(np.exp(beta @ np.array([1.0, math.log(n), math.log(m)]))))
        out["constant"].append(constant)
    for values in out.values():
        arr = np.asarray(values, dtype=float)
        if not np.all(np.isfinite(arr)) or np.any(arr <= 0):
            raise RequiredBaselineFailure("baseline_nonfinite")
    if not np.all(np.isfinite(beta)):
        raise RequiredBaselineFailure("baseline_ols_singular")
    return {k: np.asarray(v, dtype=float) for k, v in out.items()}


def per_graph_errors(pred, labels):
    """e = min(|ln pred - ln C|, ln 1000); NaN/invalid predictions take the worst case."""
    pred = np.asarray(pred, dtype=float)
    with np.errstate(divide="ignore", invalid="ignore"):
        err = np.abs(np.log(pred) - np.log(labels))
    err = np.where(np.isfinite(err) & (pred > 0), np.minimum(err, LOG_CAP), LOG_CAP)
    return err


def episode_score(errors, families):
    """graph -> family (equal weight) -> episode (equal weight over the ten families)."""
    fam = np.asarray(families)
    return fixed_weight_mean([errors[fam == f].mean() for f in FAMILIES]), {
        f: float(errors[fam == f].mean()) for f in FAMILIES}


# ----------------------------------------------------------------------------------------
# Candidate transports
# ----------------------------------------------------------------------------------------
RUNNER = r'''
import importlib.util, json, os, sys
def main():
    proto = sys.stdout
    sys.stdout = sys.stderr
    verbose = len(sys.argv) > 2 and sys.argv[2] == "1"
    def report(tag, error):
        name = type(error).__name__
        if not name.isascii() or not name.isidentifier() or len(name) > 80:
            name = "WorkerException"
        line = tag + " type=" + name
        if verbose:
            try:
                message = str(error)
            except Exception:
                message = "<exception message unavailable>"
            if len(message.encode("utf-8", errors="replace")) > 2048:
                message = "<exception message omitted: too large>"
            line += "\n" + message
        print(line, file=sys.stderr, flush=True)
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(sys.argv[1])))
        spec = importlib.util.spec_from_file_location("candidate_program", sys.argv[1])
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        handle = module.handle
    except BaseException as error:
        report("candidate_load_failed", error)
        sys.exit(3)
    for line in sys.stdin:
        try:
            response = handle(json.loads(line))
            data = json.dumps(response, allow_nan=False, separators=(",", ":"))
        except Exception as error:
            report("candidate_exception", error)
            data = json.dumps({"__candidate_error__": True})
        proto.write(data + "\n")
        proto.flush()
main()
'''


class NativeTransport:
    """Untrusted candidate in a fresh, killable, resource-limited subprocess per episode."""

    def __init__(self, program_path):
        self.program_path = os.path.abspath(program_path)
        self.proc = None
        self.stderr = None
        self.workdir = None
        self.buffer = bytearray()

    def _limits(self):
        cpu = cpu_limit_seconds(RESET_TIMEOUT + EPISODE_WORK + EPISODE_OVERHEAD, 1)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
        resource.setrlimit(resource.RLIMIT_AS, (CANDIDATE_MEMORY_BYTES, CANDIDATE_MEMORY_BYTES))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    def _spawn(self):
        self.end_episode()
        python, env = candidate_subprocess_settings(os.environ)
        self.workdir = tempfile.TemporaryDirectory(prefix="cand_")
        self.proc = subprocess.Popen(
            [python, "-I", "-c", RUNNER, self.program_path, "1" if repair_diagnostics_enabled() else "0"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.workdir.name, env=env, shell=False, start_new_session=True,
            preexec_fn=self._limits, close_fds=True)
        self.stderr = BoundedWorkerStderr(self.proc.stderr)
        self.buffer = bytearray()
        os.set_blocking(self.proc.stdout.fileno(), False)

    def rpc(self, request, timeout):
        if request.get("op") == "reset":
            self._spawn()
        if self.proc is None or self.proc.poll() is not None:
            raise CandidateProtocolError("candidate_exit")
        deadline = time.monotonic() + timeout
        data = bounded_json_line(request)
        try:
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            raise CandidateProtocolError("candidate_exit") from None
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._kill()
                    raise TimeoutError("candidate response timeout")
                if not selector.select(timeout=min(remaining, 0.25)):
                    continue
                try:
                    chunk = os.read(fd, 1 << 20)
                except BlockingIOError:
                    continue
                if not chunk:
                    raise CandidateProtocolError("candidate_exit")
                self.buffer.extend(chunk)
                if len(self.buffer) >= WIRE_LIMIT:
                    self._kill()
                    raise CandidateProtocolError("oversized_response")
        line, _, rest = bytes(self.buffer).partition(b"\n")
        self.buffer = bytearray(rest)
        try:
            value = json.loads(line.decode("utf-8"), parse_constant=_reject_constant)
        except (ValueError, UnicodeDecodeError, RecursionError):
            raise CandidateProtocolError("malformed_response") from None
        if value == {"__candidate_error__": True}:
            raise CandidateProtocolError("candidate_exception")
        return value

    def _kill(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                self.proc.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                pass

    def end_episode(self):
        """Bounded cleanup; returns the stderr snapshot (or None)."""
        snapshot = None
        if self.proc is not None:
            try:
                self.proc.stdin.close()
            except OSError:
                pass
            for sig in (None, signal.SIGTERM, signal.SIGKILL):
                if self.proc.poll() is not None:
                    break
                if sig is not None:
                    try:
                        os.killpg(self.proc.pid, sig)
                    except OSError:
                        pass
                try:
                    self.proc.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    pass
            try:
                snapshot = self.stderr.close()
            except RuntimeError:
                snapshot = None
            try:
                self.proc.stdout.close()
            except OSError:
                pass
            self.proc = None
        if self.workdir is not None:
            self.workdir.cleanup()
            self.workdir = None
        return snapshot

    def close(self):
        return self.end_episode()


def _reject_constant(token):
    raise ValueError("non-finite JSON constant")


class BrokerTransportError(Exception):
    """Fatal broker/transport failure: propagates as an evaluator operational error."""


class BrokerTransport:
    """Trusted harness proxy, loaded and called in-process (never re-isolated)."""

    def __init__(self, program_path):
        spec = importlib.util.spec_from_file_location("candidate_proxy", program_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.poisoned = False

    def rpc(self, request, timeout):
        bounded_json_line(request)
        if self.poisoned and request.get("op") != "reset":
            raise CandidateProtocolError("transport_unusable")
        box = {}

        def target():
            try:
                box["value"] = self.handle(request)
            except Exception as error:  # proxy-reported candidate failure
                box["error"] = error

        worker = threading.Thread(target=target, daemon=True)
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            self.poisoned = True
            raise TimeoutError("candidate response timeout")
        if "error" in box:
            if isinstance(box["error"], TimeoutError):
                raise TimeoutError("candidate response timeout")
            if isinstance(box["error"], (OSError, EOFError)):
                # Broker/transport failure is operational, never a scored candidate failure.
                self.poisoned = True
                raise BrokerTransportError("broker_transport_failure") from None
            raise CandidateProtocolError("candidate_exception")
        self.poisoned = False
        value = box.get("value")
        try:
            bounded_json_line(value)
            return json.loads(json.dumps(value, allow_nan=False))
        except (TypeError, ValueError, OverflowError, RecursionError):
            raise CandidateProtocolError("malformed_response") from None

    def end_episode(self):
        return None

    def close(self):
        return None


def make_transport(program_path):
    socket_set = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    is_proxy = program_path == BROKER_PROXY_PATH
    if socket_set or is_proxy:
        if not (socket_set and is_proxy):
            raise RuntimeError("brokered mode requires both the candidate socket and the fixed proxy path")
        return BrokerTransport(program_path)
    if not os.path.isfile(program_path):
        raise FileNotFoundError("candidate entrypoint not found")
    return NativeTransport(program_path)


# ----------------------------------------------------------------------------------------
# Episode scheduling and candidate protocol
# ----------------------------------------------------------------------------------------
def validate_fit(response):
    if type(response) is not dict or response.get("ok") is not True or not set(response) <= {"ok", "method"}:
        raise CandidateProtocolError("malformed_response")
    if "method" in response and (type(response["method"]) is not str or len(response["method"]) > 256):
        raise CandidateProtocolError("malformed_response")


def validate_predict(response, rows):
    if type(response) is not dict or set(response) != {"pred"} or type(response["pred"]) is not list:
        raise CandidateProtocolError("malformed_response")
    pred = response["pred"]
    if len(pred) != rows or any(type(v) not in (int, float) for v in pred):
        raise CandidateProtocolError("malformed_response")
    values = []
    for v in pred:
        try:
            number = float(v)
        except (OverflowError, TypeError, ValueError):
            raise CandidateProtocolError("malformed_response") from None
        if not math.isfinite(number):
            raise CandidateProtocolError("malformed_response")
        values.append(number)
    arr = np.array(values, dtype=float)
    return np.where(arr > 0, arr, np.nan)


def control_permutation(X, rng):
    """Derangement moving every row and changing the feature vector of >= 80% of rows."""
    G = len(X)
    rows = [tuple(r) for r in X]
    for _ in range(100):
        perm = rng.permutation(G)
        if G < 2 or np.any(perm == np.arange(G)):
            continue
        changed = sum(rows[i] != rows[perm[i]] for i in range(G))
        if changed >= 0.8 * G:
            return perm
    return None


def run_declared_episodes(episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
                          rpc_cap, clock, rpc, evaluate, worst_case, record_failure, end_episode):
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
        started = clock()

        def call(request, op_cap=rpc_cap):
            nonlocal current_operation, primary_failure
            current_operation = request.get("op", "unknown")
            try:
                timeout = min(op_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, CandidateProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        snapshot = None
        try:
            try:
                timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode reset budget exhausted")
                require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
                value = evaluate(episode, call, work_deadline)
                if clock() > episode_deadline:
                    raise TimeoutError("episode cleanup deadline exceeded")
                outcomes[index] = value
            finally:
                try:
                    snapshot = end_episode()
                except Exception:
                    snapshot = None
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure, snapshot)
            except Exception:
                error.add_note("episode diagnostic recording failed")
        outcomes[index]["duration_seconds"] = max(0.0, clock() - started)
    return outcomes, complete


# ----------------------------------------------------------------------------------------
# Plane evaluation
# ----------------------------------------------------------------------------------------
def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", "final")


def load_config():
    with open(os.path.join(resource_root(), "plane_config.json"), "r", encoding="utf-8") as handle:
        cfg = json.load(handle)
    if type(cfg) is not dict or set(cfg) != CONFIG_KEYS or cfg["plane"] != "final" or cfg["schema_version"] != 1:
        raise ValueError("invalid final plane configuration")
    return cfg


def metric_names():
    names = ["combined_score", "final_main_log_err", "final_main_log_err_ci_low", "final_main_log_err_ci_high",
             "final_main_log_err_seed_range", "best_bound_log_err", "aklrr_log_err", "feige_lead_log_err",
             "matthews_ref_log_err", "ols_ref_log_err", "constant_log_err", "permuted_feature_log_err",
             "order_invariance_max_rel_diff"]
    # Plane-level point deltas are exact differences of reported errors; only their CIs are exported.
    for delta in ("delta_vs_best_bound", "delta_vs_ols_ref", "delta_permuted_minus_main"):
        names += [f"{delta}_ci_low", f"{delta}_ci_high"]
    names += [f"final_log_err_{f}" for f in FAMILIES]
    for f in FAMILIES:
        names += [f"delta_vs_best_bound_{f}", f"delta_vs_best_bound_{f}_ci_low", f"delta_vs_best_bound_{f}_ci_high"]
    names += ["mc_rel_se_median", "capped_walks", "iso_overlap_count", "feature_collision_count", "failed_episodes"]
    return names


class PairedBootstrap:
    """Two-level bootstrap: graphs resampled within family; each graph's walk times resampled.

    The same resamples are shared by every predictor (paired comparisons).
    """

    def __init__(self, evals, families, reps, seed):
        rng = np.random.default_rng(np.random.SeedSequence([int(seed), 1]))
        self.fam = np.asarray(families)
        self.log_labels = np.empty((reps, len(evals)))
        for j, g in enumerate(evals):
            times = g["times"]
            draws = rng.integers(0, len(times), size=(reps, len(times)))
            self.log_labels[:, j] = np.log(times[draws].mean(axis=1))
        self.select = {f: rng.choice(np.nonzero(self.fam == f)[0], size=(reps, int(np.sum(self.fam == f))))
                       for f in FAMILIES}

    def _errors(self, pred):
        pred = np.asarray(pred, dtype=float)
        with np.errstate(divide="ignore", invalid="ignore"):
            logp = np.where(pred > 0, np.log(pred), np.nan)
        err = np.abs(logp[None, :] - self.log_labels)
        return np.where(np.isfinite(err), np.minimum(err, LOG_CAP), LOG_CAP)

    def family_errors(self, preds):
        """Per-family bootstrap errors averaged over episodes: {family: (reps,)}."""
        out = {f: 0.0 for f in FAMILIES}
        for pred in preds:
            err = self._errors(pred)
            for f in FAMILIES:
                out[f] = out[f] + np.take_along_axis(err, self.select[f], axis=1).mean(axis=1)
        return {f: out[f] / len(preds) for f in FAMILIES}

    def plane_errors(self, preds):
        fam = self.family_errors(preds)
        return sum(fam[f] for f in FAMILIES) / len(FAMILIES)


def percentile_ci(samples):
    lo, hi = np.percentile(np.asarray(samples, dtype=float), [2.5, 97.5])
    return float(lo), float(hi)


def evaluate_plane(program_path, smoke):
    t0 = time.monotonic()
    hard_deadline = t0 + WALL_SECONDS - STARTUP_ALLOWANCE
    sequence = SMOKE_RESET_SEQUENCE if smoke else PRODUCTION_RESET_SEQUENCE
    rpc_budget = MAX_RPC_SMOKE if smoke else MAX_RPC_PRODUCTION
    require_plane_budget(len(sequence))
    cfg = load_config()
    walks = cfg["smoke_walks"] if smoke else cfg["walks"]
    per_family = cfg["smoke_graphs_per_family"]

    # Payload preflight: representative maximal messages (generous row counts) must fit the wire.
    big_rows = [[30.0, 435.0, 29.0, 29.0, 29.0, 29.0]] * 512
    bounded_json_line({"op": "fit", "feature_names": FEATURE_NAMES, "X": big_rows, "y": [1.0e9] * 512,
                       "y_se": [1.0e9] * 512, "n_walks": 4096})
    bounded_json_line({"op": "predict", "X": big_rows})
    bounded_json_line({"pred": [1.2345678901234567e308] * 512})

    # Evaluator-owned data, labels and baselines (before any candidate contact).
    cat_index = catalogue_iso_index()
    train, train_index = build_pool("train", cfg["train_data_seed"], cfg["train_random_per_family"],
                                    smoke, per_family, cat_index, [])
    search_ref, search_index = build_pool("search_eval", cfg["search_eval_data_seed"],
                                          cfg["search_eval_random_per_family"], smoke, per_family, cat_index,
                                          [train_index])
    evals, _eval_index = build_pool("final_eval", cfg["final_eval_data_seed"], cfg["final_eval_random_per_family"],
                                    smoke, per_family, cat_index, [train_index, search_index])
    # Residual overlap (e.g. a deterministic final graph that cannot be resampled) invalidates the plane.
    overlap = (cross_overlap_count(search_ref, train_index) + cross_overlap_count(evals, train_index)
               + cross_overlap_count(evals, search_index))
    sim_ok = simulator_checks(walks, cfg["sim_check_seed"])
    capped = label_graphs(train, walks, cfg["train_label_seed"])
    capped += label_graphs(evals, walks, cfg["final_eval_label_seed"])
    feats_all = collections.Counter(tuple(g["x"]) for g in train + evals)
    collisions = sum(1 for g in evals if feats_all[tuple(g["x"])] > 1)
    labels = np.array([g["c_hat"] for g in evals])
    families = [g["family"] for g in evals]
    if set(families) != set(FAMILIES):
        raise RuntimeError("eval pool lacks a declared family")
    X_eval = [list(g["x"]) for g in evals]
    G = len(evals)

    baseline_failure = None
    try:
        if not sim_ok:
            raise RequiredBaselineFailure("simulator_check_failed")
        baselines = baseline_predictions(train, evals)
    except RequiredBaselineFailure as failure:
        baseline_failure = failure.category
        baselines = None
    fit_request = {"op": "fit", "feature_names": list(FEATURE_NAMES), "X": [list(g["x"]) for g in train],
                   "y": [g["c_hat"] for g in train], "y_se": [g["se"] for g in train], "n_walks": int(walks)}
    bounded_json_line(fit_request)

    transport = make_transport(program_path)
    rpc_count = [0]

    def rpc(request, timeout):
        if rpc_count[0] >= rpc_budget:
            raise CandidateProtocolError("rpc_budget_exhausted")
        rpc_count[0] += 1
        return transport.rpc(request, timeout)

    def worst_case(episode):
        return {"seed": episode["seed"], "ok": False, "main_err": np.full(G, LOG_CAP),
                "perm_err": np.full(G, LOG_CAP), "order_diff": 1.0, "perm_vacuous": True,
                "nonconstant": False, "positive": False}

    def evaluate_episode(episode, call, work_deadline):
        if baseline_failure is not None:
            raise RequiredBaselineFailure(baseline_failure)
        rng = np.random.default_rng(np.random.SeedSequence([int(cfg["episode_salt"]), int(episode["seed"]),
                                                            int(episode["index"])]))
        validate_fit(call(fit_request, FIT_TIMEOUT))
        main_order = rng.permutation(G)
        reorder = rng.permutation(G)
        for _ in range(100):
            if G < 2 or not np.array_equal(reorder, main_order):
                break
            reorder = rng.permutation(G)
        perm = control_permutation(X_eval, rng)
        perm_src = perm if perm is not None else np.arange(G)
        perm_order = rng.permutation(G)
        plans = [("main", main_order, main_order), ("reorder", reorder, reorder),
                 ("perm", perm_order, perm_src[perm_order])]
        preds = {}
        for slot in rng.permutation(3):
            name, graph_rows, feature_rows = plans[int(slot)]
            got = validate_predict(call({"op": "predict", "X": [X_eval[int(i)] for i in feature_rows]},
                                        PREDICT_TIMEOUT), G)
            out = np.full(G, np.nan)
            out[graph_rows] = got
            preds[name] = out
        main, reord = preds["main"], preds["reorder"]
        # Pure-function check: the reordered copy, and every permuted-control row (which carries the
        # feature vector of graph perm_src[i]), must reproduce the main prediction for those features.
        perm_expect = main[perm_src]
        with np.errstate(invalid="ignore"):
            rel = np.concatenate([
                np.abs(main - reord) / np.maximum(np.abs(main), np.abs(reord)),
                np.abs(preds["perm"] - perm_expect) / np.maximum(np.abs(preds["perm"]), np.abs(perm_expect))])
        rel = np.where(np.isfinite(rel), rel, 1.0)
        distinct = [(i, j) for i in range(G) for j in range(i + 1, G) if X_eval[i] != X_eval[j]]
        nonconstant = any(np.isfinite(main[i]) and np.isfinite(main[j])
                          and abs(main[i] - main[j]) > 1e-9 * max(main[i], main[j]) for i, j in distinct)
        return {"seed": episode["seed"], "ok": True, "main_pred": main, "perm_pred": preds["perm"],
                "main_err": per_graph_errors(main, labels),
                "perm_err": per_graph_errors(preds["perm"], labels), "order_diff": float(min(1.0, rel.max())),
                "perm_vacuous": perm is None, "nonconstant": bool(nonconstant),
                "positive": bool(np.all(np.isfinite(main)))}

    def record_failure(failure, snapshot):
        # Sealed plane: failure details are retained only as worst-case contributions.
        return None

    episodes = [{"seed": int(s), "index": i} for i, s in enumerate(sequence)]
    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT,
            episode_overhead=EPISODE_OVERHEAD, rpc_cap=FIT_TIMEOUT, clock=time.monotonic, rpc=rpc,
            evaluate=evaluate_episode, worst_case=worst_case, record_failure=record_failure,
            end_episode=transport.end_episode)
    finally:
        transport.close()

    # Aggregation: graph -> family -> episode -> plane (equal weights; failures retained at worst case).
    main_scores = [episode_score(o["main_err"], families)[0] for o in outcomes]
    perm_scores = [episode_score(o["perm_err"], families)[0] for o in outcomes]
    fam_scores = [episode_score(o["main_err"], families)[1] for o in outcomes]
    main_err = fixed_weight_mean(main_scores)
    metrics = {"combined_score": -main_err, "final_main_log_err": main_err,
               "final_main_log_err_seed_range": float(max(main_scores) - min(main_scores))}
    base_err, base_fam = {}, {}
    for key in ("best_bound", "aklrr", "feige_lead", "matthews_ref", "ols_ref", "constant"):
        if baselines:
            base_err[key], base_fam[key] = episode_score(per_graph_errors(baselines[key], labels), families)
        else:
            base_err[key], base_fam[key] = LOG_CAP, {f: LOG_CAP for f in FAMILIES}
        metrics[f"{key}_log_err"] = base_err[key]
    metrics["permuted_feature_log_err"] = fixed_weight_mean(perm_scores)
    metrics["order_invariance_max_rel_diff"] = float(max(o["order_diff"] for o in outcomes))
    for f in FAMILIES:
        metrics[f"final_log_err_{f}"] = fixed_weight_mean([fs[f] for fs in fam_scores])
        metrics[f"delta_vs_best_bound_{f}"] = metrics[f"final_log_err_{f}"] - base_fam["best_bound"][f]

    # Uncertainty: paired two-level bootstrap (evaluator-private fixed seed).
    reps = cfg["smoke_bootstrap_reps"] if smoke else cfg["bootstrap_reps"]
    boot = PairedBootstrap(evals, families, reps, cfg["bootstrap_seed"])

    def worst_preds():
        return np.full(G, np.nan)

    cand_preds = [o.get("main_pred", worst_preds()) for o in outcomes]
    perm_preds = [o.get("perm_pred", worst_preds()) for o in outcomes]
    cand_fam = boot.family_errors(cand_preds)
    cand_plane = sum(cand_fam[f] for f in FAMILIES) / len(FAMILIES)
    if baselines:
        best_fam = boot.family_errors([baselines["best_bound"]])
        best_plane = sum(best_fam[f] for f in FAMILIES) / len(FAMILIES)
        ols_plane = boot.plane_errors([baselines["ols_ref"]])
    else:
        best_fam = {f: np.full(reps, LOG_CAP) for f in FAMILIES}
        best_plane = ols_plane = np.full(reps, LOG_CAP)
    perm_plane = boot.plane_errors(perm_preds)
    metrics["final_main_log_err_ci_low"], metrics["final_main_log_err_ci_high"] = percentile_ci(cand_plane)
    for name, samples in (("delta_vs_best_bound", cand_plane - best_plane),
                          ("delta_vs_ols_ref", cand_plane - ols_plane),
                          ("delta_permuted_minus_main", perm_plane - cand_plane)):
        metrics[f"{name}_ci_low"], metrics[f"{name}_ci_high"] = percentile_ci(samples)
    for f in FAMILIES:
        lo, hi = percentile_ci(cand_fam[f] - best_fam[f])
        metrics[f"delta_vs_best_bound_{f}_ci_low"], metrics[f"delta_vs_best_bound_{f}_ci_high"] = lo, hi

    failed = sum(1 for o in outcomes if not o["ok"])
    metrics["failed_episodes"] = float(failed)
    metrics["mc_rel_se_median"] = float(np.median([g["se"] / g["c_hat"] for g in evals]))
    metrics["capped_walks"] = float(capped)
    metrics["iso_overlap_count"] = float(overlap)
    metrics["feature_collision_count"] = float(collisions)
    metrics = {k: float(metrics[k]) for k in metric_names()}
    if not all(math.isfinite(v) for v in metrics.values()):
        raise RuntimeError("non-finite metric")

    plane_valid = sim_ok and baseline_failure is None and overlap == 0 and complete and failed == 0
    episode_valid = [o["ok"] and o["positive"] and o["order_diff"] <= ORDER_TOL and not o["perm_vacuous"]
                     and o["nonconstant"] for o in outcomes]
    correct = bool(plane_valid and all(episode_valid) and rpc_count[0] == rpc_budget)
    evidence = make_evaluation_evidence([
        {"seed": int(o["seed"]), "score": -float(s), "correct": bool(plane_valid and v),
         "duration_seconds": float(o["duration_seconds"])}
        for o, s, v in zip(outcomes, main_scores, episode_valid)])
    feasible = bool((not smoke) and complete and baseline_failure is None and time.monotonic() <= hard_deadline)
    return metrics, correct, evidence, feasible


def make_evaluation_evidence(seed_records):
    return {"schema_version": 1, "episodes": seed_records}


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description="Sealed final evaluator: cover-time prediction from graph statistics")
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    try:
        metrics, correct, evidence, feasible = evaluate_plane(args.program_path, smoke)
        os.makedirs(args.results_dir, exist_ok=True)
        write_json(os.path.join(args.results_dir, "metrics.json"), metrics)
        write_json(os.path.join(args.results_dir, "correct.json"), {"correct": bool(correct)})
        write_json(os.path.join(args.results_dir, "evaluation_evidence.json"), evidence)
        if os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1":
            write_json(os.path.join(args.results_dir, "qualification.json"),
                       {"schema_version": 1, "feasible": bool(feasible)})
    except Exception:
        emit_line("evaluator_error sealed_final_failure")
        sys.exit(1)


if __name__ == "__main__":
    main()
