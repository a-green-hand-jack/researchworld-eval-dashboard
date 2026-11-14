#!/usr/bin/env python3
"""Search-plane evaluator: confidence-interval width for a mean with fixed labels/unlabeled/predictor.

Protocol (declared before evaluation). One episode = one independent labeled/unlabeled draw =
reset + estimate (2 candidate RPCs). The evaluator draws n+N i.i.d. records with replacement from a
family pool (or an analytic synthetic generator) with evaluator-private RNG keyed on a private master
seed and (family, replicate), never on the candidate reset seed. Truth = pool mean of Y (analytic
for synthetic). Baselines (ppi_py 0.2.3): classical CLT, PPI (lam=1), PPI++ (power tuned).

Aggregation hierarchy (all weights fixed):
  episode  -> covered_e in {0,1}, W_e (candidate width), P_e (PPI++), C_e (classical), L_e (PPI lam=1).
              Invalid/missing/non-finite/timeout/baseline-failed episode: covered_e=0, W_e=10*C_e.
  family   -> rho_f = sum W_e / sum P_e over that family's main episodes; s_f = -log(clip(rho_f,1e-3,1e3)).
  plane    -> combined_score = mean over the 5 main families (weight 1/5 each) of s_f.
  controls (const / perm / shift) are aggregated separately and enter only `correct` (gate).
`correct` = integrity AND exact one-sided binomial coverage tests (pooled level 0.01, per family
Bonferroni 0.01/5, failed episodes are misses) AND all controls pass their declared behaviour.
"""
import time

_T0 = time.monotonic()

import argparse
import base64
import collections
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

import numpy as np

# ==== PLANE CONFIG (begin) ====
PLANE = "search"
RESOURCE_SUBDIR = "resources/search"
MASTER_SEED = 740112095
ALPHA = 0.05
# name -> (file, Y key, Yhat key, n, N)
POOLS = {
    "galaxies": ("galaxies.npz", "Y", "Yhat", 300, 5000),
    "forest": ("forest.npz", "Y", "Yhat", 100, 1000),
    "gene_expression": ("gene_expression.npz", "Y", "Yhat", 500, 10000),
    "alphafold": ("alphafold.npz", "Y", "Yhat", 300, 5000),
}
FILE_SHA256 = {
    "galaxies.npz": "7be1d40a049f524fc51e150281541359a47c5eca80343dfac5b1c457fd7eae99",
    "forest.npz": "9708f3be14850a55d03f88dad235c87b4a3b6c6e8cb81173cc580de8f7386ade",
    "gene_expression.npz": "72565d2d88ed6a16331b3423da5dee036e97f2220fad054eb139ced1942e3303",
    "alphafold.npz": "93f680d2f0d48844b96c4495efec1a3a84e8dd572ba3f17c4f07401ad20534f9",
}
MAIN_FAMILIES = ["galaxies", "forest", "gene_expression", "alphafold", "synthetic"]
CONTROL_BASES = ["galaxies", "gene_expression"]
REPS_MAIN = 60
REPS_CONTROL = 20
SEEDS = [1001, 1002, 1003, 1004, 1005]
SYNTH_REGIMES = [
    # (name, truth, builder spec) -- see synth_draw
    ("linear_calibrated", 1.0, dict(a=1.0, b=2.0, s=1.0, kind="linear", noise_hat=0.4)),
    ("nonlinear_miscalibrated", 1.0, dict(a=1.0, b=1.5, s=0.5, kind="exp", rate=0.9, noise_hat=0.05)),
    ("uninformative", 1.0, dict(a=1.0, b=1.5, s=1.0, kind="independent", noise_hat=1.0)),
    ("heteroscedastic", 1.0, dict(a=1.0, b=1.5, s=1.0, kind="hetero", rate=0.7, noise_hat=0.3)),
]
SYNTH_N = [200, 500]
SYNTH_BIG_N = [2000, 10000]
WALL_SECONDS = 3600.0
SMOKE_PLAN = [("galaxies", "main"), ("forest", "main"), ("gene_expression", "main"),
              ("alphafold", "main"), ("synthetic", "main"),
              ("galaxies", "const"), ("galaxies", "perm"), ("galaxies", "shift")]
# ==== PLANE CONFIG (end) ====

PROXY_PATH = "/broker-code/candidate_proxy.py"
CONTROL_TYPES = ["const", "perm", "shift"]
RESET_TIMEOUT = 4.0
RPC_CAP = 3.0
STARTUP_ALLOWANCE = 60.0
FINISH_RESERVE = 15.0
BROKER_OVERHEAD = 1.0
NATIVE_OVERHEAD = 3.0
SMOKE_WALL = 110.0
SMOKE_STARTUP = 5.0
SMOKE_FINISH = 5.0
WIRE_LIMIT = 64 * 1024 * 1024
FAIL_WIDTH_FACTOR = 10.0
RHO_CLIP = (1e-3, 1e3)
MAIN_LEVEL = 0.01
CONTROL_LEVEL = 0.01 / 3
NOMINAL = 1.0 - ALPHA
CONST_TOL = 0.05
SHIFT_TOL = 0.10
PERM_MAX_ABS_CORR = 0.05
PERM_MIN_MOVED = 0.99


# ---------------------------------------------------------------- failure identity helpers
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
    """Expected candidate-side transport failure (crash, closed channel, raised exception)."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "candidate_rpc_error")
        super().__init__("candidate rpc failed")


class ProtocolError(RuntimeError):
    """Explicit response-validation failure with a fixed category."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "malformed_response")
        super().__init__("protocol violation")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, ProtocolError):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
        if isinstance(context, CandidateRpcError):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
        context = context.__context__
        if context is None:
            break
    return {"component": "candidate", "category": "timeout",
            "operation": bounded_failure_name(operation, "unknown")}


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


# ---------------------------------------------------------------- budget / wire helpers
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
    finite_budget_seconds(needed)
    if needed > times["wall_seconds"]:
        raise ValueError("productive work exceeds the declared wall budget")
    return needed


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
            try:
                require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            except CandidateRpcError as error:
                primary_failure = describe_episode_failure(error, "reset")
                raise
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse,
                ProtocolError, CandidateRpcError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure, index)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ---------------------------------------------------------------- data and draws
def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_pools(root):
    pools = {}
    for name, (fname, ykey, hkey, n, big_n) in POOLS.items():
        path = os.path.join(root, fname)
        if sha256_file(path) != FILE_SHA256[fname]:
            raise RuntimeError("resource checksum mismatch")
        with np.load(path, allow_pickle=False) as data:
            y = np.asarray(data[ykey], dtype=np.float64)
            yhat = np.asarray(data[hkey], dtype=np.float64)
        if y.shape != yhat.shape or y.ndim != 1 or not (np.all(np.isfinite(y)) and np.all(np.isfinite(yhat))):
            raise RuntimeError("invalid pool")
        sd = float(y.std())
        pools[name] = {"y": y, "yhat": yhat, "n": n, "N": big_n, "truth": float(y.mean()),
                       "sd": sd if sd > 0 else 1.0, "family_index": list(POOLS).index(name)}
    return pools


def make_perm_pool(pool, family_index):
    """Permute Yhat across pool records; reject vacuous permutations (redraw, bounded)."""
    rng = np.random.default_rng([MASTER_SEED, family_index, 777])
    m = pool["y"].size
    last = None
    for _ in range(20):
        perm = rng.permutation(m)
        moved = float(np.mean(perm != np.arange(m)))
        yhat_p = pool["yhat"][perm]
        if pool["yhat"].std() > 0 and yhat_p.std() > 0:
            corr = float(np.corrcoef(pool["y"], yhat_p)[0, 1])
        else:
            corr = 1.0
        last = yhat_p
        if moved >= PERM_MIN_MOVED and abs(corr) < PERM_MAX_ABS_CORR:
            return yhat_p, True
    return last, False


def synth_draw(regime, n, big_n, rng):
    """Known-truth synthetic draw. Returns (y_l, yhat_l, yhat_u, truth)."""
    name, truth, spec = regime
    m = n + big_n
    z = rng.standard_normal(m)
    eps = rng.standard_normal(m)
    eta = rng.standard_normal(m)
    kind = spec["kind"]
    if kind == "hetero":
        y = spec["a"] + spec["b"] * z + np.exp(spec["rate"] * z) * eps * spec["s"]
        # E[exp(rate*Z) * eps] = 0, so the mean stays a.
        yhat = spec["a"] + spec["b"] * z + spec["noise_hat"] * eta
    elif kind == "exp":
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yhat = np.exp(spec["rate"] * z) + spec["noise_hat"] * eta
    elif kind == "cubic":
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yhat = 0.5 * z ** 3 + 0.2 * z + spec["noise_hat"] * eta
    elif kind == "independent":
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yhat = spec["a"] + spec["b"] * eta
    else:
        y = spec["a"] + spec["b"] * z + spec["s"] * eps
        yhat = spec["a"] + spec["b"] * z + spec["noise_hat"] * eta
    return y[:n], yhat[:n], yhat[n:], truth


def make_plan(smoke):
    """Ordered declared episode list (one reset each)."""
    plan = []
    if smoke:
        for group, kind in SMOKE_PLAN:
            plan.append({"group": group if kind == "main" else f"{group}_{kind}",
                         "base": group, "kind": kind, "rep": 0})
    else:
        for j in range(REPS_MAIN):
            for fam in MAIN_FAMILIES:
                plan.append({"group": fam, "base": fam, "kind": "main", "rep": j})
            if j < REPS_CONTROL:
                for base in CONTROL_BASES:
                    for kind in CONTROL_TYPES:
                        plan.append({"group": f"{base}_{kind}", "base": base, "kind": kind, "rep": j})
    for i, ep in enumerate(plan):
        ep["seed"] = SEEDS[0] if smoke else SEEDS[i % len(SEEDS)]
    return plan


def reset_sequence(smoke):
    return [ep["seed"] for ep in make_plan(smoke)]


def episode_workload(ep, pools, perm_pools):
    """Deterministic evaluator-private draw for an episode. Returns dict of arrays and truth."""
    base, kind, rep = ep["base"], ep["kind"], ep["rep"]
    if base == "synthetic":
        rng = np.random.default_rng([MASTER_SEED, 9999, rep])
        j = rep
        regime = SYNTH_REGIMES[j % len(SYNTH_REGIMES)]
        n = SYNTH_N[(j // 4) % 2]
        big_n = SYNTH_BIG_N[(j // 8) % 2]
        y_l, h_l, h_u, truth = synth_draw(regime, n, big_n, rng)
        return {"y_l": y_l, "h_l": h_l, "h_u": h_u, "truth": truth, "n": n, "N": big_n,
                "sd": 1.0}
    pool = pools[base]
    n, big_n = pool["n"], pool["N"]
    rng = np.random.default_rng([MASTER_SEED, pool["family_index"], rep])
    idx = rng.integers(0, pool["y"].size, n + big_n)
    y = pool["y"][idx]
    truth = pool["truth"]
    if kind == "perm":
        yhat = perm_pools[base][0][idx]
    else:
        yhat = pool["yhat"][idx]
    if kind == "const":
        yhat = np.full(n + big_n, float(pool["yhat"].mean()))
    if kind == "shift":
        shift = 5.0 * pool["sd"]
        y = y + shift
        yhat = yhat + shift
        truth = truth + shift
    return {"y_l": y[:n], "h_l": yhat[:n], "h_u": yhat[n:], "truth": truth, "n": n,
            "N": big_n, "sd": pool["sd"]}


def compute_baselines(work):
    import ppi_py
    y, hl, hu = work["y_l"], work["h_l"], work["h_u"]

    def width(ci):
        lo, hi = (float(np.ravel(v)[0]) for v in ci)
        w = hi - lo
        if not (math.isfinite(lo) and math.isfinite(hi) and math.isfinite(w) and w >= 0):
            raise ArithmeticError("non-finite baseline")
        return w

    try:
        c = width(ppi_py.classical_mean_ci(y, alpha=ALPHA))
        lam1 = width(ppi_py.ppi_mean_ci(y, hl, hu, alpha=ALPHA, lam=1))
        with np.errstate(all="ignore"):
            try:
                pp = width(ppi_py.ppi_mean_ci(y, hl, hu, alpha=ALPHA))
            except ArithmeticError:
                if np.ptp(np.concatenate([hl, hu])) != 0:
                    raise
                # Exactly constant predictor: the tuning ratio is 0/0; PPI++ is its limit lam=0.
                pp = width(ppi_py.ppi_mean_ci(y, hl, hu, alpha=ALPHA, lam=0))
        return {"C": c, "L": lam1, "P": pp, "failed": False}
    except (ArithmeticError, ValueError, RuntimeError, FloatingPointError):
        fallback = 2 * 1.959963984540054 * work["sd"] / math.sqrt(work["n"])
        return {"C": fallback, "L": fallback, "P": fallback, "failed": True}


def encode_array(arr):
    data = np.ascontiguousarray(arr, dtype="<f8")
    return {"dtype": "float64", "shape": [int(data.size)], "encoding": "base64-le",
            "data": base64.b64encode(data.tobytes()).decode("ascii")}


def estimate_request(work):
    return {"op": "estimate", "n": int(work["n"]), "N": int(work["N"]), "alpha": ALPHA,
            "Y_labeled": encode_array(work["y_l"]), "Yhat_labeled": encode_array(work["h_l"]),
            "Yhat_unlabeled": encode_array(work["h_u"])}


def preflight_wire():
    """Serialize largest representative request/response; assert both below the wire limit."""
    big_n = max([p[4] for p in POOLS.values()] + SYNTH_BIG_N)
    big_labeled = max([p[3] for p in POOLS.values()] + SYNTH_N)
    rng = np.random.default_rng(1)
    junk = lambda k: rng.standard_normal(k) * 1e300  # long-repr, full-entropy float64 payload
    request = {"op": "estimate", "n": big_labeled, "N": big_n, "alpha": ALPHA,
               "Y_labeled": encode_array(junk(big_labeled)), "Yhat_labeled": encode_array(junk(big_labeled)),
               "Yhat_unlabeled": encode_array(junk(big_n))}
    response = {"lo": -1.2345678901234567e-300, "hi": 1.2345678901234567e+300}
    return len(bounded_json_line(request)), len(bounded_json_line(response))


# ---------------------------------------------------------------- candidate transports
RUNNER = r'''
import sys, json, os, importlib.util, resource
def report(error, diag):
    if not diag:
        print("worker_exception category=candidate_exception", file=sys.stderr, flush=True)
        return
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = "WorkerException"
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    if len(message) > 2048:
        message = "<exception message omitted: too large>"
    print("worker_exception type=%s\n%s" % (name, message), file=sys.stderr, flush=True)
def main():
    path, cpu, mem, diag = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4] == "1"
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (mem, mem))
    out, inp = sys.stdout.buffer, sys.stdin.buffer
    sys.stdout = sys.stderr
    try:
        spec = importlib.util.spec_from_file_location("candidate_program", path)
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
        spec.loader.exec_module(module)
        handle = module.handle
    except Exception as error:
        report(error, diag)
        sys.exit(3)
    for line in inp:
        try:
            response = handle(json.loads(line))
            data = json.dumps(response, allow_nan=False, separators=(",", ":")).encode("utf-8")
        except Exception as error:
            report(error, diag)
            sys.exit(3)
        out.write(data + b"\n")
        out.flush()
main()
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
    environment["OMP_NUM_THREADS"] = "1"
    environment["OPENBLAS_NUM_THREADS"] = "1"
    environment["MKL_NUM_THREADS"] = "1"
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke only)."""

    def __init__(self, program_path, clock, diag):
        self.program_path = os.path.abspath(program_path)
        self.clock = clock
        self.diag = diag
        self.proc = None
        self.stderr = None
        self.workdir = tempfile.mkdtemp(prefix="cand_")
        self.last_stderr = ""
        self.buffer = b""

    def start(self):
        self.stop()
        interpreter, env = candidate_subprocess_settings(os.environ)
        cpu = cpu_limit_seconds(SMOKE_WALL, 2)
        mem = 6 * 1024 ** 3
        self.proc = subprocess.Popen(
            [interpreter, "-I", "-c", RUNNER, self.program_path, str(cpu), str(mem),
             "1" if self.diag else "0"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.workdir, env=env, shell=False, start_new_session=True, close_fds=True)
        self.stderr = BoundedWorkerStderr(self.proc.stderr)
        os.set_blocking(self.proc.stdout.fileno(), False)
        os.set_blocking(self.proc.stdin.fileno(), False)
        self.buffer = b""

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
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
        finally:
            if self.stderr is not None:
                try:
                    self.last_stderr = self.stderr.close()["stderr"]
                except RuntimeError:
                    self.last_stderr = ""
                self.stderr = None

    def call(self, request, timeout):
        if request.get("op") == "reset":
            self.start()
        if self.proc is None:
            raise CandidateRpcError("candidate_not_running")
        deadline = self.clock() + timeout
        data = bounded_json_line(request)
        try:
            self._write(data, deadline)
            return self._read(deadline)
        except TimeoutError:
            self.stop()
            raise
        except CandidateRpcError:
            self.stop()
            raise

    def _write(self, data, deadline):
        view = memoryview(data)
        fd = self.proc.stdin.fileno()
        with selectors.DefaultSelector() as sel:
            sel.register(fd, selectors.EVENT_WRITE)
            while view:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError("candidate write timeout")
                if not sel.select(timeout=min(remaining, 0.2)):
                    continue
                try:
                    sent = os.write(fd, view[:65536])
                except BlockingIOError:
                    continue
                except (BrokenPipeError, OSError):
                    raise CandidateRpcError("candidate_closed_channel") from None
                view = view[sent:]

    def _read(self, deadline):
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as sel:
            sel.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError("candidate read timeout")
                if not sel.select(timeout=min(remaining, 0.2)):
                    continue
                try:
                    chunk = os.read(fd, 1 << 20)
                except BlockingIOError:
                    continue
                except OSError:
                    raise CandidateRpcError("candidate_closed_channel") from None
                if not chunk:
                    raise CandidateRpcError("candidate_crash")
                self.buffer += chunk
                if len(self.buffer) >= WIRE_LIMIT:
                    raise CandidateRpcError("response_too_large")
        line, _, self.buffer = self.buffer.partition(b"\n")
        try:
            return json.loads(line, parse_constant=_reject_constant)
        except ValueError:
            raise CandidateRpcError("malformed_json") from None


def _reject_constant(token):
    raise ValueError("non-finite JSON constant")


class BrokerCandidate:
    """In-process trusted broker proxy (production). Calls proxy.handle with a bounded wait."""

    def __init__(self, handle):
        self.handle = handle
        self.busy = None

    def call(self, request, timeout):
        if self.busy is not None and self.busy.is_alive():
            self.busy.join(timeout)
            if self.busy.is_alive():
                raise TimeoutError("previous candidate call still running")
        box = {}

        def run():
            try:
                box["response"] = self.handle(request)
            except BaseException as error:  # noqa: BLE001 - classified below
                box["error"] = error

        worker = threading.Thread(target=run, name="broker-call", daemon=True)
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            self.busy = worker
            raise TimeoutError("candidate call timeout")
        self.busy = None
        if "error" in box:
            if isinstance(box["error"], TimeoutError):
                raise TimeoutError("candidate call timeout") from None
            raise CandidateRpcError("candidate_rpc_error") from None
        return box["response"]


def validate_estimate_response(response):
    if type(response) is not dict or set(response) != {"lo", "hi"}:
        raise ProtocolError("malformed_response")
    lo, hi = response["lo"], response["hi"]
    converted = []
    for value in (lo, hi):
        if type(value) not in (int, float):
            raise ProtocolError("nonfinite_response")
        try:
            value = float(value)
        except (OverflowError, ValueError):
            raise ProtocolError("nonfinite_response") from None
        if not math.isfinite(value):
            raise ProtocolError("nonfinite_response")
        converted.append(value)
    lo, hi = converted
    if lo > hi:
        raise ProtocolError("reversed_interval")
    # The width must stay finite (and summable across episodes) to be a valid contribution.
    if not math.isfinite(hi - lo) or hi - lo > 1e150:
        raise ProtocolError("nonfinite_response")
    try:
        bounded_json_line(response)
    except ValueError:
        raise ProtocolError("response_too_large") from None
    return float(lo), float(hi)


# ---------------------------------------------------------------- statistics
def binom_cdf(k, n, p):
    from scipy.stats import binom
    return float(binom.cdf(k, n, p))


def coverage_not_rejected(covered, level):
    n = len(covered)
    if n == 0:
        return False
    return binom_cdf(int(sum(covered)), n, NOMINAL) >= level


def family_score(sum_w, sum_ref):
    if not (math.isfinite(sum_w) and math.isfinite(sum_ref)) or sum_ref <= 0:
        return -math.log(FAIL_WIDTH_FACTOR)
    rho = min(max(sum_w / sum_ref, RHO_CLIP[0]), RHO_CLIP[1])
    return -math.log(rho)


def require_controls(expected, completed):
    if set(expected) - set(completed):
        raise ValueError("required control did not complete")


def aggregate(plan, records, perm_valid):
    """Deterministic aggregation. Returns (metrics_dict, correct, internals)."""
    fam_eps = {f: [r for e, r in zip(plan, records) if e["group"] == f and e["kind"] == "main"]
               for f in MAIN_FAMILIES}
    s_ppi, s_cls, s_l1, cov_f = {}, {}, {}, {}
    for f, eps in fam_eps.items():
        sw = sum(r["W"] for r in eps)
        s_ppi[f] = family_score(sw, sum(r["P"] for r in eps))
        s_cls[f] = family_score(sw, sum(r["C"] for r in eps))
        s_l1[f] = family_score(sw, sum(r["L"] for r in eps))
        cov_f[f] = float(np.mean([r["covered"] for r in eps])) if eps else 0.0
    main_all = [r for eps in fam_eps.values() for r in eps]
    cov_pooled = float(np.mean([r["covered"] for r in main_all])) if main_all else 0.0
    combined = float(np.mean([s_ppi[f] for f in MAIN_FAMILIES]))

    # --- controls (gate only)
    main_w = {(e["base"], e["rep"]): r["W"] for e, r in zip(plan, records) if e["kind"] == "main"}
    expected_groups, completed_groups = set(), set()
    control_ok = {}
    for kind in CONTROL_TYPES:
        pairs = [(e, r) for e, r in zip(plan, records) if e["kind"] == kind]
        for e, r in pairs:
            expected_groups.add(e["group"])
        for g in {e["group"] for e, _ in pairs}:
            if all(r["ok"] for e, r in pairs if e["group"] == g):
                completed_groups.add(g)
        ok = bool(pairs) and coverage_not_rejected([r["covered"] for _, r in pairs], CONTROL_LEVEL)
        if kind in ("const", "perm") and pairs:
            mean_log = float(np.mean([math.log(max(r["W"], 1e-300) / r["C"]) if r["C"] > 0 else 0.0
                                      for _, r in pairs]))
            ok = ok and mean_log >= -CONST_TOL
        if kind == "perm":
            ok = ok and perm_valid
        if kind == "shift" and pairs:
            diffs = []
            for e, r in pairs:
                ref = main_w.get((e["base"], e["rep"]))
                if ref is None or ref <= 0 or r["W"] <= 0:
                    diffs.append(math.log(FAIL_WIDTH_FACTOR))
                else:
                    diffs.append(abs(math.log(r["W"] / ref)))
            ok = ok and float(np.mean(diffs)) <= SHIFT_TOL
        control_ok[kind] = ok
    try:
        require_controls(expected_groups, completed_groups)
        controls_complete = True
    except ValueError:
        controls_complete = False
    controls_passed = float(all(control_ok.values()) and controls_complete and len(control_ok) == 3)

    n_failed = sum(1 for r in records if not r["ok"])
    internals = {"fam_eps": fam_eps, "cov_f": cov_f, "s_ppi": s_ppi, "controls_ok": control_ok,
                 "cov_pooled": cov_pooled, "combined": combined, "controls_passed": controls_passed,
                 "n_failed": n_failed}
    metrics = {
        "combined_score": combined,
        "coverage_pooled": cov_pooled,
        "coverage_min_family": float(min(cov_f.values())),
    }
    for f in MAIN_FAMILIES:
        metrics[f"log_ratio_vs_ppi_family_{f}"] = float(s_ppi[f])
    metrics["log_ratio_vs_classical_mean"] = float(np.mean([s_cls[f] for f in MAIN_FAMILIES]))
    metrics["log_ratio_vs_ppi_lambda1_mean"] = float(np.mean([s_l1[f] for f in MAIN_FAMILIES]))
    metrics["controls_passed"] = controls_passed
    metrics["n_failed_episodes"] = int(n_failed)
    return metrics, internals


def coverage_valid(internals):
    pooled = [r["covered"] for eps in internals["fam_eps"].values() for r in eps]
    if not coverage_not_rejected(pooled, MAIN_LEVEL):
        return False
    level = MAIN_LEVEL / len(MAIN_FAMILIES)
    return all(coverage_not_rejected([r["covered"] for r in eps], level)
               for eps in internals["fam_eps"].values())


# ==== PLANE METRICS (begin) ====
def plane_metrics(base_metrics, internals, correct):
    return base_metrics
# ==== PLANE METRICS (end) ====


def per_seed_evidence(plan, records, durations, correct):
    out = []
    for seed in sorted({e["seed"] for e in plan}):
        idx = [i for i, e in enumerate(plan) if e["seed"] == seed]
        scores = []
        for f in MAIN_FAMILIES:
            eps = [records[i] for i in idx if plan[i]["group"] == f and plan[i]["kind"] == "main"]
            if eps:
                scores.append(family_score(sum(r["W"] for r in eps), sum(r["P"] for r in eps)))
        out.append({"seed": int(seed), "score": float(np.mean(scores)) if scores else 0.0,
                    "correct": bool(correct),
                    "duration_seconds": float(sum(durations[i] for i in idx))})
    return {"schema_version": 1, "episodes": out}


# ---------------------------------------------------------------- main
def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, sort_keys=True)


def resolve_source_dir():
    return os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))


def run(program_path, results_dir, clock=time.monotonic):
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    diag_visible = PLANE == "search" and (smoke or qualification)
    socket_set = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    brokered = socket_set and program_path == PROXY_PATH
    if socket_set != (program_path == PROXY_PATH):
        raise RuntimeError("inconsistent broker signals")
    os.makedirs(results_dir, exist_ok=True)

    plan = make_plan(smoke)
    declared_resets = reset_sequence(smoke)
    rpc_budget = 2 * len(plan)  # per episode: 1 reset + 1 estimate; no replay is used
    wall = SMOKE_WALL if smoke else WALL_SECONDS
    startup = SMOKE_STARTUP if smoke else STARTUP_ALLOWANCE
    finish = SMOKE_FINISH if smoke else FINISH_RESERVE
    overhead = BROKER_OVERHEAD if brokered else NATIVE_OVERHEAD
    if not smoke:
        require_joint_workload_budget(plane_profile={
            "episode_count": len(plan), "method_count": 1, "wall_seconds": WALL_SECONDS,
            "startup_seconds": STARTUP_ALLOWANCE, "reset_seconds": RESET_TIMEOUT,
            "cleanup_seconds": 0.5, "finish_seconds": FINISH_RESERVE, "work_seconds": RPC_CAP})
    hard_deadline = _T0 + wall - startup
    request_bytes, response_bytes = preflight_wire()

    root = os.path.join(resolve_source_dir(), RESOURCE_SUBDIR)
    pools = load_pools(root)
    perm_pools, perm_flags = {}, []
    for base in CONTROL_BASES:
        perm_pools[base] = make_perm_pool(pools[base], pools[base]["family_index"])
        perm_flags.append(perm_pools[base][1])
    perm_valid = all(perm_flags)

    # Baselines for every declared draw are computed before the first reset.
    works, baselines = [], []
    for ep in plan:
        work = episode_workload(ep, pools, perm_pools)
        works.append(work)
        baselines.append(compute_baselines(work))

    if brokered:
        spec = importlib.util.spec_from_file_location("candidate_proxy", PROXY_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        transport = BrokerCandidate(module.handle)
    else:
        transport = NativeCandidate(program_path, clock, diag_visible)

    state = {"rpc_calls": 0, "resets": [], "starts": {}, "durations": {}, "current": -1}
    failures = {}

    def rpc(request, timeout):
        state["rpc_calls"] += 1
        if state["rpc_calls"] > rpc_budget:
            raise RuntimeError("candidate RPC budget exceeded")
        if request.get("op") == "reset":
            state["resets"].append(request["seed"])
            state["current"] += 1
            state["starts"][state["current"]] = clock()
        return transport.call(request, timeout)

    index_of = {id(ep): i for i, ep in enumerate(plan)}

    def worst_case_record(ep):
        i = index_of[id(ep)]
        c = baselines[i]["C"]
        return {"covered": 0, "W": FAIL_WIDTH_FACTOR * c, "C": c, "P": baselines[i]["P"],
                "L": baselines[i]["L"], "ok": False}

    def evaluate_episode(ep, call, work_deadline):
        i = index_of[id(ep)]
        if baselines[i]["failed"]:
            raise RequiredBaselineFailure("baseline_result_failure")
        request = estimate_request(works[i])
        bounded_json_line(request)
        response = call(request)
        lo, hi = validate_estimate_response(response)
        state["durations"][i] = clock() - state["starts"][i]
        truth = works[i]["truth"]
        return {"covered": int(lo <= truth <= hi), "W": hi - lo, "C": baselines[i]["C"],
                "P": baselines[i]["P"], "L": baselines[i]["L"], "ok": True}

    def record_failure(failure, index):
        if index in state["starts"]:
            state["durations"][index] = max(0.0, clock() - state["starts"][index])
        failures[index] = failure
        if PLANE == "search":
            line = ("episode_failed idx=%d component=%s category=%s operation=%s"
                    % (index, failure["component"], failure["category"], failure["operation"]))
        else:
            line = "episode_failed category=%s" % failure["category"]
        print(line[:256], file=sys.stderr, flush=True)
        if diag_visible and isinstance(transport, NativeCandidate):
            transport.stop()
            snapshot = transport.last_stderr
            if snapshot:
                sys.stderr.write(snapshot if snapshot.endswith("\n") else snapshot + "\n")
                sys.stderr.flush()

    try:
        records, complete = run_declared_episodes(
            plan, hard_deadline=hard_deadline, finish_reserve=finish, reset_timeout=RESET_TIMEOUT,
            episode_overhead=overhead, rpc_cap=RPC_CAP, clock=clock, rpc=rpc,
            evaluate=evaluate_episode, worst_case=worst_case_record, record_failure=record_failure)
    finally:
        if isinstance(transport, NativeCandidate):
            transport.stop()
            shutil.rmtree(transport.workdir, ignore_errors=True)

    for r in records:
        if not all(math.isfinite(r[k]) for k in ("W", "C", "P", "L")):
            raise RuntimeError("nonfinite episode contribution")
    durations = [state["durations"].get(i, 0.0) for i in range(len(plan))]

    base_metrics, internals = aggregate(plan, records, perm_valid)
    transcript_ok = state["resets"] == declared_resets
    integrity = (transcript_ok and state["rpc_calls"] <= rpc_budget
                 and request_bytes < WIRE_LIMIT and response_bytes < WIRE_LIMIT)
    correct = bool(integrity and coverage_valid(internals) and internals["controls_passed"] == 1.0)
    metrics = plane_metrics(base_metrics, internals, correct)
    for key, value in metrics.items():
        if not math.isfinite(float(value)):
            raise RuntimeError("nonfinite metric")
    elapsed = clock() - _T0
    write_json(os.path.join(results_dir, "metrics.json"), metrics)
    write_json(os.path.join(results_dir, "correct.json"), {"correct": correct})
    write_json(os.path.join(results_dir, "evaluation_evidence.json"),
               per_seed_evidence(plan, records, durations, correct))
    if qualification:
        feasible = bool((not smoke) and complete and transcript_ok and elapsed <= WALL_SECONDS)
        write_json(os.path.join(results_dir, "qualification.json"),
                   {"schema_version": 1, "feasible": feasible})
    return metrics, correct


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        run(args.program_path, args.results_dir)
    except Exception as error:  # noqa: BLE001 - bounded diagnostic then non-zero exit
        name = type(error).__name__
        message = str(error).replace("\n", " ")[:200]
        sys.stderr.write(f"evaluator_error type={name} message={message}"[:300] + "\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
