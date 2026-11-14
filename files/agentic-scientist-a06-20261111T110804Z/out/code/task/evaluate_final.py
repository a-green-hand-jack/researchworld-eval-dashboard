#!/usr/bin/env python3
"""Sealed final-plane evaluator: selection-aware score reporting after prompt/pipeline search.

The evaluator owns every world (synthetic latent-difficulty worlds and cached real
MMLU-Pro x 24-prompt-config outcome tensors), both searchers, the truth, and the
baselines.  The candidate only receives the search-time evaluation log of one
replication and reports (estimate, lower, upper) for the fresh-question accuracy of
the selected configuration.  Score = negative mean interval score at level 0.90.
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
import subprocess
import sys
import threading
import time
from statistics import NormalDist

import numpy as np

# ---- PLANE BLOCK BEGIN ----
PLANE = "final"
SEEDS = (9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108)
CASE_ORDER = ("P1", "P2", "P3", "P4", "P5", "P6", "N1", "N2", "Z1")
REAL_PRIMARY = ("P3", "P4", "P5", "P6")
RNG_ENTROPY = 0xF1A2A101
WALL_CLOCK = 9000.0
CANDIDATE_CAP = 5400.0
RPC_CALL_CAP = 2110
SMOKE_SEED = 9101
# ---- PLANE BLOCK END ----

SYN_PRIMARY = ("P1", "P2")
FAMILY_WEIGHTS = {"synthetic": 0.4, "real": 0.6}
LEVEL = 0.90
ALPHA = 1.0 - LEVEL
WORST_IS = 20.0  # declared worst case: width 1, |bias| 1, truth missed
Z90 = NormalDist().inv_cdf(0.95)
WIRE_LIMIT = 64 * 1024 * 1024
PROXY_PATH = "/broker-code/candidate_proxy.py"
N_CONFIG_REAL = 24
RESAMPLE_B = 100
SYN_RHO = 0.5
SYN_SPREAD_SD = 0.03

STARTUP_ALLOWANCE = 120.0
FINISH_RESERVE = 30.0
RESET_TIMEOUT = 20.0
RPC_CAP = 10.0
EPISODE_OVERHEAD = 8.0  # candidate terminate+kill/reap (4) + bookkeeping/transition (4)

METRIC_NAMES = (
    "combined_score", "mean_interval_score", "coverage", "mean_width", "signed_bias", "rmse",
    "naive_baseline_score", "bonferroni_baseline_score", "resample_baseline_score",
    "naive_signed_bias", "null_control_abs_bias", "null_control_coverage",
    "constant_control_error", "completed_replication_fraction",
)

CASES = {
    "P1": dict(world="syn", searcher="exhaustive", K=32, N=150, R=30),
    "P2": dict(world="syn", searcher="halving", K=32, N=150, R=30),
    "P3": dict(world="real", searcher="exhaustive", K=24, N=200, R=30),
    "P4": dict(world="real", searcher="halving", K=24, N=200, R=30),
    "P5": dict(world="real", searcher="exhaustive", K=24, N=60, R=30),
    "P6": dict(world="real", searcher="exhaustive", K=24, N=600, R=30),
    "N1": dict(world="syn_null", searcher="exhaustive", K=32, N=150, R=30),
    "N2": dict(world="real_null", searcher="exhaustive", K=24, N=200, R=30),
    "Z1": dict(world="const", searcher="exhaustive", K=8, N=100, R=10),
}
SMOKE_N = {"syn": 40, "syn_null": 40, "real": 30, "real_null": 30, "const": 20}
SMOKE_POOL = 150
SMOKE_R = 2


def case_params(name, smoke):
    p = dict(CASES[name])
    if smoke:
        p["R"] = SMOKE_R
        p["N"] = SMOKE_N[p["world"]]
        if name == "P5":
            p["N"] = 20
    return p


def declared_reset_sequence(smoke):
    if smoke:
        return [SMOKE_SEED for _ in CASE_ORDER]
    return [seed for seed in SEEDS for _ in CASE_ORDER]


# ---------------------------------------------------------------- helpers (required-worker identity)
class InvalidResetResponse(RuntimeError):
    pass


class CandidateTransportError(RuntimeError):
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
        if isinstance(context, CandidateTransportError):
            return {"component": "candidate", "category": "transport_failure",
                    "operation": bounded_failure_name(operation, "unknown")}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout",
            "operation": bounded_failure_name(operation, "unknown")}


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


def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


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


def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure, outcomes=None,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    if outcomes is None:
        outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    progress = {"resets": 0}
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
            except (TimeoutError, RequiredBaselineFailure, CandidateTransportError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            progress["resets"] += 1
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateTransportError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure, index)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete, progress["resets"]


# ---------------------------------------------------------------- candidate transport
def native_environment(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
    environment = {name: parent_environment[name] for name in runtime_names if name in parent_environment}
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1", OMP_NUM_THREADS="4", OPENBLAS_NUM_THREADS="4",
                       MKL_NUM_THREADS="4")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


NATIVE_RUNNER = r'''
import importlib.util, json, os, sys
path = sys.argv[1]
proto = os.fdopen(os.dup(1), "w")
sys.stdout = sys.stderr
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
spec = importlib.util.spec_from_file_location("candidate_program", path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
for line in sys.stdin:
    request = json.loads(line)
    response = module.handle(request)
    proto.write(json.dumps(response, allow_nan=False, separators=(",", ":")) + "\n")
    proto.flush()
'''


class BrokeredClient:
    """In-process trusted proxy; each call runs in a daemon thread bounded by a timeout."""

    def __init__(self):
        spec = importlib.util.spec_from_file_location("candidate_proxy", PROXY_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._handle = module.handle
        self._busy = None

    def call(self, request, timeout):
        if self._busy is not None and self._busy.is_alive():
            raise TimeoutError("candidate still busy")
        box = {}

        def work():
            try:
                box["value"] = self._handle(request)
            except BaseException as error:  # noqa: BLE001 - normalized below
                box["error"] = type(error).__name__

        thread = threading.Thread(target=work, daemon=True)
        self._busy = thread
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            raise TimeoutError("candidate call timed out")
        if "error" in box:
            raise CandidateTransportError("candidate call failed")
        return box["value"]

    def close(self):
        return None


class NativeClient:
    """Untrusted candidate file in a killable, resource-limited subprocess."""

    def __init__(self, program_path, wall_seconds):
        self.program_path = os.path.abspath(program_path)
        self.cpu_limit = cpu_limit_seconds(wall_seconds, 4)
        self.proc = None
        self.stderr = None
        self.buffer = b""
        self.stderr_snapshots = []

    def _spawn(self):
        self._stop()
        python, env = native_environment(os.environ)
        cpu = self.cpu_limit

        def limits():
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 5))
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            resource.setrlimit(resource.RLIMIT_AS, (8 << 30, 8 << 30))

        workdir = "/tmp"
        self.proc = subprocess.Popen(
            [python, "-I", "-c", NATIVE_RUNNER, self.program_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, cwd=workdir, shell=False, start_new_session=True, preexec_fn=limits, close_fds=True)
        self.stderr = BoundedWorkerStderr(self.proc.stderr)
        self.buffer = b""

    def _stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            if proc.poll() is None:
                try:
                    os.killpg(proc.pid, 9)
                except OSError:
                    proc.kill()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
        finally:
            if self.stderr is not None:
                try:
                    self.stderr_snapshots.append(self.stderr.close())
                except RuntimeError:
                    pass
                self.stderr = None

    def call(self, request, timeout):
        if request.get("op") == "reset":
            self._spawn()
        if self.proc is None or self.proc.poll() is not None:
            raise CandidateTransportError("candidate process not running")
        data = bounded_json_line(request)
        deadline = time.monotonic() + timeout
        try:
            os.set_blocking(self.proc.stdin.fileno(), True)
            self.proc.stdin.write(data)
            self.proc.stdin.flush()
        except OSError:
            raise CandidateTransportError("candidate pipe closed") from None
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    self._stop()
                    raise TimeoutError("candidate call timed out")
                if not selector.select(timeout=min(remaining, 0.5)):
                    continue
                chunk = os.read(fd, 1 << 20)
                if not chunk:
                    self._stop()
                    raise CandidateTransportError("candidate exited")
                self.buffer += chunk
                if len(self.buffer) > WIRE_LIMIT:
                    self._stop()
                    raise CandidateTransportError("candidate response too large")
        line, _, self.buffer = self.buffer.partition(b"\n")
        try:
            return json.loads(line.decode("utf-8"), parse_constant=_reject_constant)
        except (ValueError, UnicodeDecodeError):
            return {"__malformed__": True}

    def close(self):
        self._stop()


def _reject_constant(name):
    raise ValueError("non-finite constant")


# ---------------------------------------------------------------- statistics
def wilson(p, n, z):
    n = float(n)
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt(max(p * (1.0 - p) / n + z * z / (4.0 * n * n), 0.0)) / denom
    lo = max(0.0, min(center - half, p))
    hi = min(1.0, max(center + half, p))
    return lo, hi


def interval_score(lower, upper, y):
    return (upper - lower) + (2.0 / ALPHA) * max(lower - y, 0.0) + (2.0 / ALPHA) * max(y - upper, 0.0)


def encode_array(array, dtype):
    arr = np.ascontiguousarray(np.asarray(array).astype(dtype).astype(np.dtype(dtype).newbyteorder("<")))
    return {"dtype": dtype, "shape": list(arr.shape), "encoding": "base64-little-endian-c-order",
            "data": base64.b64encode(arr.tobytes()).decode("ascii")}


def parse_response(response):
    if type(response) is not dict or set(response) != {"estimate", "lower", "upper"}:
        return None
    values = []
    for key in ("estimate", "lower", "upper"):
        v = response[key]
        if type(v) not in (int, float) or not math.isfinite(v):
            return None
        values.append(float(v))
    est, lo, hi = values
    if not (0.0 <= lo <= est <= hi <= 1.0):
        return None
    try:
        bounded_json_line(response)
    except ValueError:
        return None
    return est, lo, hi


# ---------------------------------------------------------------- searchers
def run_search(X, searcher):
    """Return (question_idx, config_idx, outcome, selected) for outcome matrix X[N, K]."""
    N, K = X.shape
    if searcher == "exhaustive":
        qi = np.repeat(np.arange(N, dtype=np.uint16), K)
        ci = np.tile(np.arange(K, dtype=np.uint8), N)
        out = X.reshape(-1).astype(np.uint8)
        return qi, ci, out, int(np.argmax(X.sum(axis=0)))
    rounds = max(1, math.ceil(math.log2(K)))
    budget = N * K
    survivors = np.arange(K)
    done = 0
    sums = np.zeros(K, dtype=np.int64)
    qs, cs, outs = [], [], []
    for _ in range(rounds):
        if len(survivors) == 1:
            break
        n_new = max(1, budget // (rounds * len(survivors)))
        upto = min(N, done + n_new)
        if upto > done:
            block = X[done:upto][:, survivors]
            qs.append(np.repeat(np.arange(done, upto, dtype=np.uint16), len(survivors)))
            cs.append(np.tile(survivors.astype(np.uint8), upto - done))
            outs.append(block.reshape(-1).astype(np.uint8))
            sums[survivors] += block.sum(axis=0, dtype=np.int64)
            done = upto
        keep = max(1, math.ceil(len(survivors) / 2))
        order = sorted((int(k) for k in survivors), key=lambda k: (-int(sums[k]), k))
        survivors = np.array(sorted(order[:keep]))
    return np.concatenate(qs), np.concatenate(cs), np.concatenate(outs), int(survivors[0])


def baseline_reports(qi, ci, out, selected, N, K, rng):
    """Evaluator-owned reporters computed from the same log the candidate receives."""
    obs = np.zeros((N, K), dtype=bool)
    vals = np.zeros((N, K), dtype=np.float64)
    obs[qi, ci] = True
    vals[qi, ci] = out
    n_sel = int(obs[:, selected].sum())
    p = float(vals[:, selected].sum() / n_sel)
    naive = (p,) + wilson(p, n_sel, Z90)
    z_bonf = NormalDist().inv_cdf(1.0 - ALPHA / (2.0 * K))
    bonf = (p,) + wilson(p, n_sel, z_bonf)
    half = N // 2
    ranks = rng.random((RESAMPLE_B, N)).argsort(axis=1).argsort(axis=1)
    A = (ranks < half).astype(np.float64)
    Bm = 1.0 - A
    obsf = obs.astype(np.float64)
    cA, sA, cB, sB = A @ obsf, A @ vals, Bm @ obsf, Bm @ vals
    meanA = np.where(cA > 0, sA / np.maximum(cA, 1.0), -np.inf)
    pick = np.argmax(meanA, axis=1)
    rows = np.arange(RESAMPLE_B)
    ok = (cA[rows, pick] > 0) & (cB[rows, pick] > 0)
    gap = (sA[rows, pick] / np.maximum(cA[rows, pick], 1.0) - sB[rows, pick] / np.maximum(cB[rows, pick], 1.0))[ok]
    g = float(gap.mean()) if gap.size else 0.0
    est = min(1.0, max(0.0, p - g / math.sqrt(2.0)))  # half-sample gap scaled to full-sample SE
    resample = (est,) + wilson(est, n_sel, Z90)
    return naive, bonf, resample


# ---------------------------------------------------------------- resources / episodes
def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", PLANE)


def load_real_pool(smoke):
    root = resource_root()
    with open(os.path.join(root, "manifest.json"), "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    with np.load(os.path.join(root, "outcomes.npz"), allow_pickle=False) as data:
        Y = np.array(data["outcomes"], dtype=np.uint8)
        subject = np.array(data["subject_code"], dtype=np.uint8)
    hashes = manifest["pool_content_hashes"]
    demo_hashes = manifest["demo_content_hashes"]
    audit = manifest["audit"]
    if manifest.get("plane") != PLANE:
        raise ValueError("resource plane mismatch")
    if Y.ndim != 2 or Y.shape[1] != N_CONFIG_REAL or Y.shape[0] != len(hashes) or subject.shape != (Y.shape[0],):
        raise ValueError("outcome tensor shape mismatch")
    if not np.isin(Y, (0, 1)).all():
        raise ValueError("outcome tensor must be binary")
    if len(set(hashes)) != len(hashes) or set(hashes) & set(demo_hashes):
        raise ValueError("content hash audit failed")
    if audit.get("cross_plane_overlap") != 0 or audit.get("demo_overlap") != 0:
        raise ValueError("recorded hash audit not clean")
    if smoke:
        Y, subject = Y[:SMOKE_POOL], subject[:SMOKE_POOL]
    return Y, subject


def syn_world(rng, K, null):
    base = float(rng.uniform(0.25, 0.75))
    if null:
        p = np.full(K, base)
    else:
        p = np.clip(base + rng.normal(0.0, SYN_SPREAD_SD, K), 0.02, 0.98)
    return p


def syn_outcomes(rng, p, N):
    K = len(p)
    thr = np.array([NormalDist().inv_cdf(float(x)) for x in p])
    u = rng.standard_normal(N)
    e = rng.standard_normal((N, K))
    return (math.sqrt(SYN_RHO) * u[:, None] + math.sqrt(1.0 - SYN_RHO) * e < thr[None, :]).astype(np.uint8)


def random_derangement_rows(rng, n_rows, K):
    perm = np.argsort(rng.random((n_rows, K)), axis=1)  # random orderings
    shift = rng.integers(1, K, size=n_rows)
    pos = np.argsort(perm, axis=1)
    new_pos = (pos + shift[:, None]) % K
    out = np.take_along_axis(perm, new_pos, axis=1)  # out[i, c] = config that column c reads (single K-cycle)
    return out


def build_episode(index, seed, case, smoke, pool):
    params = case_params(case, smoke)
    K, N, R, world, searcher = params["K"], params["N"], params["R"], params["world"], params["searcher"]
    case_idx = CASE_ORDER.index(case)
    base_seq = [RNG_ENTROPY, int(seed), case_idx, 1 if smoke else 0]
    valid_control = True
    Ypool = subj_pool = None
    if world in ("real", "real_null"):
        Ypool, subj_pool = pool
        if world == "real_null":
            rng_p = np.random.default_rng(np.random.SeedSequence(base_seq + [999]))
            der = random_derangement_rows(rng_p, Ypool.shape[0], Ypool.shape[1])
            if (der == np.arange(Ypool.shape[1])[None, :]).any():
                valid_control = False
            Y2 = np.take_along_axis(Ypool, der, axis=1)
            # spread of per-config pool accuracy must collapse to the null sampling noise implied by the
            # within-question variance over configs (or at least halve the original spread)
            acc0, acc1 = Ypool.mean(axis=0), Y2.mean(axis=0)
            noise = math.sqrt(float(Ypool.astype(np.float64).var(axis=1).mean()) / Ypool.shape[0])
            if float(acc1.std()) > max(0.5 * float(acc0.std()), 1.5 * noise):
                valid_control = False
            Ypool = Y2
    reps = []
    for r in range(R):
        rng = np.random.default_rng(np.random.SeedSequence(base_seq + [r]))
        if world in ("syn", "syn_null"):
            p = syn_world(rng, K, null=(world == "syn_null"))
            X = syn_outcomes(rng, p, N)
            subj = np.zeros(N, dtype=np.uint8)
            truth_of = lambda sel, p=p: float(p[sel])
        elif world == "const":
            X = np.zeros((N, K), dtype=np.uint8)
            subj = np.zeros(N, dtype=np.uint8)
            truth_of = lambda sel: 0.0
        else:
            n_pool = Ypool.shape[0]
            sample = rng.choice(n_pool, size=N, replace=False)
            perm = rng.permutation(K)
            rest = np.ones(n_pool, dtype=bool)
            rest[sample] = False
            X = Ypool[sample][:, perm]
            subj = subj_pool[sample]
            rest_acc = Ypool[rest].mean(axis=0)[perm]
            truth_of = lambda sel, rest_acc=rest_acc: float(rest_acc[sel])
        qi, ci, out, sel = run_search(X, searcher)
        naive, bonf, resample = baseline_reports(qi, ci, out, sel, N, K, rng)
        reps.append(dict(qi=qi, ci=ci, out=out, sel=sel, subj=subj, truth=truth_of(sel),
                         naive=naive, bonf=bonf, resample=resample))
    return dict(index=index, seed=int(seed), case=case, params=params, reps=reps, valid_control=valid_control)


def build_request(ep, rep):
    params = ep["params"]
    return {
        "op": "report",
        "n_questions": params["N"],
        "n_configs": params["K"],
        "level": LEVEL,
        "searcher": params["searcher"],
        "selected_config": int(rep["sel"]),
        "log": {
            "question_idx": encode_array(rep["qi"], "uint16"),
            "config_idx": encode_array(rep["ci"], "uint8"),
            "outcome": encode_array(rep["out"], "uint8"),
        },
        "subject_code": encode_array(rep["subj"], "uint8"),
    }


def score_reporter(report, truth):
    est, lo, hi = report
    return dict(IS=interval_score(lo, hi, truth), cov=float(lo <= truth <= hi), width=hi - lo,
                bias=est - truth, sq=(est - truth) ** 2, abs_est=abs(est))


WORST_REP = dict(IS=WORST_IS, cov=0.0, width=1.0, bias=1.0, sq=1.0, abs_est=1.0)
REP_KEYS = tuple(WORST_REP)


def episode_record(ep, cand_rows, valid_flags):
    """Episode value = equal-weight mean over its declared replications."""
    R = len(ep["reps"])
    rec = {k: float(np.mean([cand_rows[i][k] for i in range(R)])) for k in REP_KEYS}
    for name in ("naive", "bonf", "resample"):
        rows = [score_reporter(rep[name], rep["truth"]) for rep in ep["reps"]]
        rec[name + "_IS"] = float(np.mean([x["IS"] for x in rows]))
        rec[name + "_bias"] = float(np.mean([x["bias"] for x in rows]))
    rec["valid_fraction"] = float(np.mean(valid_flags))
    rec["valid_count"] = int(sum(valid_flags))
    rec["reps"] = R
    rec["naive_bias_list"] = [score_reporter(rep["naive"], rep["truth"])["bias"] for rep in ep["reps"]]
    return rec


def worst_case_record(ep):
    R = len(ep["reps"])
    return episode_record(ep, [WORST_REP] * R, [False] * R)


# ---------------------------------------------------------------- aggregation
def case_value(records, case, key):
    vals = [r[key] for r in records if r["case"] == case]
    return float(np.mean(vals)) if vals else None


def plane_value(records, key, cases_present):
    syn = [case_value(records, c, key) for c in SYN_PRIMARY if c in cases_present]
    real = [case_value(records, c, key) for c in REAL_PRIMARY if c in cases_present]
    syn_v = float(np.mean(syn))
    real_v = float(np.mean(real))
    return FAMILY_WEIGHTS["synthetic"] * syn_v + FAMILY_WEIGHTS["real"] * real_v


def aggregate(records):
    cases = set(CASE_ORDER)
    pv = lambda key: plane_value(records, key, cases)
    mean_is = pv("IS")
    ctrl_cases = ("N1", "N2")
    metrics = {
        "combined_score": -mean_is,
        "mean_interval_score": mean_is,
        "coverage": pv("cov"),
        "mean_width": pv("width"),
        "signed_bias": pv("bias"),
        "rmse": math.sqrt(pv("sq")),
        "naive_baseline_score": -pv("naive_IS"),
        "bonferroni_baseline_score": -pv("bonf_IS"),
        "resample_baseline_score": -pv("resample_IS"),
        "naive_signed_bias": pv("naive_bias"),
        "null_control_abs_bias": float(np.mean([abs(case_value(records, c, "bias")) for c in ctrl_cases])),
        "null_control_coverage": float(np.mean([case_value(records, c, "cov") for c in ctrl_cases])),
        "constant_control_error": case_value(records, "Z1", "abs_est"),
        "completed_replication_fraction": float(sum(r["valid_count"] for r in records) / sum(r["reps"] for r in records)),
    }
    metrics["combined_score"] = -metrics["mean_interval_score"]
    return {k: float(v) for k, v in metrics.items()}


def seed_scores(records):
    out = {}
    for seed in sorted({r["seed"] for r in records}):
        sub = [r for r in records if r["seed"] == seed]
        out[seed] = -plane_value(sub, "IS", set(CASE_ORDER))
    return out


def controls_valid(records, episodes):
    ok = all(ep["valid_control"] for ep in episodes)
    for case in ("N1", "N2"):
        bias = np.array([b for r in records if r["case"] == case for b in r["naive_bias_list"]], dtype=float)
        if bias.size < 2:
            ok = False
            continue
        lower = float(bias.mean() - 1.96 * bias.std(ddof=1) / math.sqrt(bias.size))
        if not lower > 0.0:
            ok = False
    return ok


def z1_integrity(records):
    z = [r for r in records if r["case"] == "Z1"]
    err = float(np.mean([r["abs_est"] for r in z]))
    cov = float(np.mean([r["cov"] for r in z]))
    return err <= 0.05 and cov >= 0.9


def payload_preflight():
    """Serialize the largest planned request and the response; all must stay below 64 MiB."""
    big = {"op": "report", "n_questions": 1000, "n_configs": 64, "level": LEVEL, "searcher": "exhaustive",
           "selected_config": 63,
           "log": {"question_idx": encode_array(np.arange(64000) % 1000, "uint16"),
                   "config_idx": encode_array(np.arange(64000) % 64, "uint8"),
                   "outcome": encode_array(np.ones(64000), "uint8")},
           "subject_code": encode_array(np.zeros(1000), "uint8")}
    size = len(bounded_json_line(big))
    bounded_json_line({"estimate": 0.5, "lower": 0.25, "upper": 0.75})
    return size


def rpc_budget(episodes):
    resets = len(episodes)
    reports = sum(len(ep["reps"]) for ep in episodes)
    replay = 1 + max(len(ep["reps"]) for ep in episodes)  # permitted trailing replay of the first seed
    return {"reset": resets, "report": reports, "replay_allowance": replay,
            "total": resets + reports + replay}


# ---------------------------------------------------------------- main
def write_json(path, value):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, sort_keys=True)
    os.replace(tmp, path)


def run(args, process_start):
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    drafting = smoke or qualification
    hard_deadline = process_start + WALL_CLOCK - STARTUP_ALLOWANCE
    brokered = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET")) and args.program_path == PROXY_PATH
    if not brokered and not os.path.isfile(args.program_path):
        raise FileNotFoundError("candidate program not found")

    sequence = declared_reset_sequence(smoke)
    episodes_decl = [dict(seed=SMOKE_SEED if smoke else seed, case=case)
                     for seed in ((SMOKE_SEED,) if smoke else SEEDS) for case in CASE_ORDER]
    assert [e["seed"] for e in episodes_decl] == sequence
    pool = load_real_pool(smoke)
    preflight_bytes = payload_preflight()
    episodes = [build_episode(i, e["seed"], e["case"], smoke, pool) for i, e in enumerate(episodes_decl)]
    budget = rpc_budget(episodes)
    if not smoke and budget["total"] > RPC_CALL_CAP:
        raise ValueError("declared RPC budget exceeds contract cap")
    setup_done = time.monotonic()
    candidate_hard = min(hard_deadline, setup_done + CANDIDATE_CAP + FINISH_RESERVE)
    if setup_done + len(episodes) * (RESET_TIMEOUT + EPISODE_OVERHEAD) + FINISH_RESERVE > hard_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")

    client = BrokeredClient() if brokered else NativeClient(args.program_path, WALL_CLOCK)
    rpc_count = {"n": 0}
    budget_violation = {"v": False}

    def rpc(request, timeout):
        rpc_count["n"] += 1
        if rpc_count["n"] > (budget["total"] if smoke else RPC_CALL_CAP):
            budget_violation["v"] = True
            raise CandidateTransportError("rpc budget exceeded")
        bounded_json_line(request)
        return client.call(request, timeout)

    durations = {}
    state = {"failed_lines": 0}

    def record_failure(failure, index):
        parts = [f"episode_failure component={failure['component']} category={failure['category']}"
                 f" operation={failure['operation']}"]
        if PLANE == "search":
            parts.append(f"episode={index}")
        print(" ".join(parts)[:256], file=sys.stderr, flush=True)

    def evaluate_episode(episode, call, work_deadline):
        ep = episodes[episode["index"]]
        t0 = time.monotonic()
        rows, valid = [], []
        invalid_noted = False
        try:
            for rep in ep["reps"]:
                response = call(build_request(ep, rep))
                parsed = parse_response(response)
                if parsed is None:
                    rows.append(dict(WORST_REP))
                    valid.append(False)
                    if not invalid_noted:
                        invalid_noted = True
                        record_failure({"component": "candidate", "category": "malformed_response",
                                        "operation": "report"}, ep["index"])
                else:
                    rows.append(score_reporter(parsed, rep["truth"]))
                    valid.append(True)
        finally:
            durations[ep["index"]] = time.monotonic() - t0
        return episode_record(ep, rows, valid)

    ep_inputs = [dict(seed=ep["seed"], case=ep["case"], index=ep["index"]) for ep in episodes]
    outcomes = [worst_case_record(ep) for ep in episodes]
    complete, resets_done, fatal = False, 0, False
    try:
        outcomes, complete, resets_done = run_declared_episodes(
            ep_inputs, hard_deadline=candidate_hard, finish_reserve=FINISH_RESERVE,
            reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP,
            clock=time.monotonic, rpc=rpc, evaluate=evaluate_episode,
            worst_case=lambda e: worst_case_record(episodes[e["index"]]), record_failure=record_failure,
            outcomes=outcomes)
    except (OSError, EOFError, TimeoutError):
        fatal = True
        print("episode_failure component=broker category=fatal_transport operation=schedule",
              file=sys.stderr, flush=True)
    finally:
        try:
            client.close()
        except Exception:  # noqa: BLE001 - cleanup failure is secondary
            pass
        if drafting and PLANE == "search" and isinstance(client, NativeClient):
            for snap in client.stderr_snapshots:
                if snap["stderr"]:
                    sys.stderr.write(snap["stderr"])
                    sys.stderr.flush()

    records = []
    for ep, rec in zip(episodes, outcomes):
        rec = dict(rec)
        rec.update(case=ep["case"], seed=ep["seed"])
        records.append(rec)
    metrics = aggregate(records)
    if not all(math.isfinite(v) for v in metrics.values()):
        raise ValueError("non-finite metric")
    resets_ok = resets_done == len(episodes) and not fatal
    ctrl_ok = controls_valid(records, episodes)
    z1_ok = z1_integrity(records)
    correct = bool(resets_ok and ctrl_ok and z1_ok and not budget_violation["v"] and preflight_bytes < WIRE_LIMIT)

    os.makedirs(args.results_dir, exist_ok=True)
    write_json(os.path.join(args.results_dir, "metrics.json"), {k: metrics[k] for k in METRIC_NAMES})
    write_json(os.path.join(args.results_dir, "correct.json"), {"correct": correct})
    if qualification:
        feasible = bool((not smoke) and complete and resets_ok and not budget_violation["v"])
        write_json(os.path.join(args.results_dir, "qualification.json"), {"schema_version": 1, "feasible": feasible})

    scores = seed_scores(records)
    seed_records = []
    for seed, score in scores.items():
        idxs = [i for i, ep in enumerate(episodes) if ep["seed"] == seed]
        sub = [records[i] for i in idxs]
        seed_ok = all(r["valid_count"] == r["reps"] for r in sub)
        solution = {r["case"]: {"cand_IS": r["IS"], "naive_IS": r["naive_IS"], "bonferroni_IS": r["bonf_IS"],
                                "resample_IS": r["resample_IS"], "coverage": r["cov"], "width": r["width"],
                                "bias": r["bias"], "naive_bias": r["naive_bias"]} for r in sub}
        seed_records.append({"seed": int(seed), "score": float(score), "correct": bool(seed_ok),
                             "duration_seconds": float(sum(durations.get(i, 0.0) for i in idxs)),
                             "solution": solution})
    write_json(os.path.join(args.results_dir, "evaluation_evidence.json"),
               {"schema_version": 1, "episodes": seed_records})


def main():
    process_start = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        run(args, process_start)
    except BaseException as error:  # noqa: BLE001 - bounded report then non-zero exit
        if isinstance(error, SystemExit):
            raise
        name = type(error).__name__
        name = name if name.isascii() and name.isidentifier() and len(name) <= 80 else "Exception"
        print(f"evaluator_error type={name}", file=sys.stderr, flush=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
