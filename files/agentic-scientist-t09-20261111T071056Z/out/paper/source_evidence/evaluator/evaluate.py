#!/usr/bin/env python3
"""search-plane evaluator: regression-based GATE estimation under network interference.

Self-contained: needs only numpy/scipy, the search resource root (``resources/search``) and
the harness broker.  The evaluator generates every instance itself, keeps the interference
mechanism and the true GATE private, runs four evaluator-owned baselines, and sends the
candidate (through ``handle``) only the permitted dataset fields.  Per episode: exactly one
``reset`` followed by four ``estimate`` requests (primary dataset + three matched negative
controls, evaluator-private order), plus one mandatory trailing replay episode.

Aggregation (declared before evaluation): per primary episode e = min(|est-G|/|G|, 2);
a failed/missing episode takes e = 2 (signed +2, not covered, width 4); per-case RMSE over the
plane's seeds (equal seed weights); plane score = unweighted mean over the 8 cases (weight 1/8);
combined_score = -mean.  Controls and the replay never enter combined_score.
"""

import os

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ.setdefault(_name, "2")

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
from pathlib import Path

import numpy as np
import scipy.sparse as sp

PLANE = "search"
SEEDS = [101, 102, 103, 104, 105, 106, 107, 108]
WALL_SECONDS = 1800
MAX_CANDIDATE_RPC_CALLS = 400

BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
WIRE_LIMIT = 64 * 1024 * 1024
PAYLOAD_TARGET = 8 * 1024 * 1024
N_CASES = 8
OPS_PER_EPISODE = 5  # 1 reset + 4 estimate

STARTUP_ALLOWANCE = 30.0
FINISH_RESERVE = 20.0
RESET_TIMEOUT = 4.0
ESTIMATE_TIMEOUT = 3.0
SOFT_OP_SECONDS = 2.5
# terminate/kill/reap of the candidate (2 waits) + dispatch/bookkeeping/transition
EPISODE_OVERHEAD = 4.0
KILL_WAIT = 1.0

REL_CAP = 2.0
WIDTH_CAP = 4.0
CONST_ABS_WORST = 1.0e3
REPLAY_WORST = 1.0e3
CONST_TOL = 1.0e-4
REPLAY_TOL = 1.0e-6
ORACLE_SANITY_MAX = 1.0
GATE_FLOOR = 0.5

BASELINES = ("dim", "linear", "ht", "oracle")
OPS = ("primary", "perm_outcome", "perm_graph", "constant")
FAMILY_ID = {"sbm": 0, "ba": 1, "ws": 2}

METRIC_NAMES = (
    ["combined_score", "rmse_rel", "bias_rel_abs_mean", "ci_coverage", "ci_width_rel"]
    + [f"rmse_rel_case_{k}" for k in range(1, N_CASES + 1)]
    + ["baseline_dim_rmse_rel", "baseline_linear_rmse_rel", "baseline_ht_rmse_rel",
       "baseline_oracle_rmse_rel", "ratio_to_linear_baseline", "ratio_to_dim_baseline",
       "control_constant_max_abs_est", "control_permuted_outcome_mean_abs_rel_est",
       "control_permuted_graph_rmse_rel", "control_vacuity_violations",
       "missing_or_failed_episodes", "replay_abs_diff"]
)


# ----------------------------------------------------------------------------------------
# bounded budgets / scheduling helpers
# ----------------------------------------------------------------------------------------

def finite_budget_seconds(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        raise ValueError("invalid time allowance")
    return value


def positive_work_seconds(value):
    if finite_budget_seconds(value) == 0:
        raise ValueError("work allowance must be positive")
    return value


def require_plane_budget(profile):
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


# ----------------------------------------------------------------------------------------
# required-worker failure identity
# ----------------------------------------------------------------------------------------

class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


class InvalidCandidateResponse(RuntimeError):
    def __init__(self, category="malformed_response"):
        self.category = category
        super().__init__("invalid candidate response")


class TransportFailure(RuntimeError):
    pass


def bounded_failure_name(value, fallback):
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response",
                    "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category,
                    "operation": "baseline_worker"}
        if isinstance(context, InvalidCandidateResponse):
            return {"component": "candidate", "category": context.category,
                    "operation": bounded_failure_name(operation, "unknown")}
        if isinstance(context, TransportFailure):
            return {"component": "candidate", "category": "transport_failure",
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


def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
    rpc_caps, clock, rpc, evaluate, worst_case, record_failure,
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
                timeout = min(rpc_caps.get(current_operation, rpc_caps["default"]),
                              work_deadline - clock())
                if timeout <= 0:
                    raise TimeoutError("episode work budget exhausted")
                return rpc(request, timeout=timeout)
            except (TimeoutError, RequiredBaselineFailure, TransportFailure) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        try:
            timeout = min(reset_timeout, rpc_caps["reset"], work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            current_operation = "reset"
            require_reset_ack(rpc({"op": "reset", "seed": episode["seed"]}, timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse,
                TransportFailure) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ----------------------------------------------------------------------------------------
# bounded worker stderr capture (candidate subprocess, native smoke only)
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


# ----------------------------------------------------------------------------------------
# candidate transports
# ----------------------------------------------------------------------------------------

# Runner executed inside the isolated native-smoke subprocess.  It imports the candidate file,
# speaks one JSON object per line on a private duplicate of stdout, and sends everything the
# candidate prints to stderr.  argv: <candidate path> <repair flag>
_RUNNER = r'''
import importlib.util, json, os, sys
_out = os.fdopen(os.dup(1), "w", buffering=1)
sys.stdout = sys.stderr
_path, _repair = sys.argv[1], sys.argv[2] == "1"
sys.path.insert(0, os.path.dirname(_path))
_spec = importlib.util.spec_from_file_location("candidate_program", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

def _report(error):
    if not _repair:
        print("worker_exception category=candidate_exception", file=sys.stderr, flush=True)
        return
    name = type(error).__name__
    if not name.isascii() or not name.isidentifier() or len(name) > 80:
        name = "WorkerException"
    try:
        message = str(error)
    except Exception:
        message = "<exception message unavailable>"
    if len(message) > 2048 or len(message.encode("utf-8", errors="replace")) > 2048:
        message = "<exception message omitted: too large>"
    print("worker_exception type=%s\n%s" % (name, message), file=sys.stderr, flush=True)

for _line in sys.stdin:
    try:
        _resp = _mod.handle(json.loads(_line))
        _text = json.dumps(_resp, allow_nan=False, separators=(",", ":"))
    except BaseException as _error:
        _report(_error)
        _text = json.dumps({"__error__": "candidate_exception"})
    _out.write(_text + "\n")
    _out.flush()
'''


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


class NativeCandidate:
    """Killable, resource-limited, filesystem-neutral subprocess transport (smoke only)."""

    CANDIDATE_THREADS = 4
    ADDRESS_SPACE = 10 * 1024 ** 3

    def __init__(self, program_path, repair_mode):
        self.program_path = str(program_path)
        self.repair_mode = repair_mode
        self.proc = None
        self.stderr = None
        self.workdir = tempfile.TemporaryDirectory(prefix="cand_")
        self.last_snapshot = None
        self.kept_stderr = []
        self.buffer = b""

    def _spawn(self):
        interpreter, environment = candidate_subprocess_settings(os.environ)
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
                     "NUMEXPR_NUM_THREADS"):
            environment[name] = str(self.CANDIDATE_THREADS)
        self.proc = subprocess.Popen(
            [interpreter, "-I", "-B", "-c", _RUNNER, self.program_path, "1" if self.repair_mode else "0"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.workdir.name, env=environment, shell=False, start_new_session=True,
            close_fds=True)
        self.stderr = BoundedWorkerStderr(self.proc.stderr)
        self.buffer = b""
        try:
            limit = cpu_limit_seconds(WALL_SECONDS, self.CANDIDATE_THREADS)
            resource.prlimit(self.proc.pid, resource.RLIMIT_CPU, (limit, limit))
            resource.prlimit(self.proc.pid, resource.RLIMIT_AS, (self.ADDRESS_SPACE, self.ADDRESS_SPACE))
        except (OSError, ValueError):
            pass
        os.set_blocking(self.proc.stdin.fileno(), False)
        os.set_blocking(self.proc.stdout.fileno(), False)

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass
        try:
            proc.wait(timeout=KILL_WAIT)
        except subprocess.TimeoutExpired:
            pass
        for stream in (proc.stdin, proc.stdout):
            try:
                stream.close()
            except OSError:
                pass
        try:
            self.last_snapshot = self.stderr.close()
        except RuntimeError:
            self.last_snapshot = None
        if self.last_snapshot and self.last_snapshot["stderr"] and len(self.kept_stderr) < 4:
            self.kept_stderr.append(self.last_snapshot["stderr"])
        self.stderr = None

    def _send(self, data, deadline):
        fd = self.proc.stdin.fileno()
        view = memoryview(data)
        with selectors.DefaultSelector() as sel:
            sel.register(fd, selectors.EVENT_WRITE)
            while len(view):
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("send timeout")
                if not sel.select(timeout=min(remaining, 0.2)):
                    continue
                try:
                    written = os.write(fd, view[:65536])
                except BlockingIOError:
                    continue
                except (BrokenPipeError, OSError):
                    raise TransportFailure("candidate pipe closed") from None
                view = view[written:]

    def _receive(self, deadline):
        fd = self.proc.stdout.fileno()
        with selectors.DefaultSelector() as sel:
            sel.register(fd, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                if len(self.buffer) > WIRE_LIMIT:
                    raise InvalidCandidateResponse("malformed_response")
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("response timeout")
                if not sel.select(timeout=min(remaining, 0.2)):
                    continue
                try:
                    chunk = os.read(fd, 1 << 20)
                except BlockingIOError:
                    continue
                except OSError:
                    raise TransportFailure("candidate pipe closed") from None
                if not chunk:
                    raise TransportFailure("candidate exited")
                self.buffer += chunk
        line, _, rest = self.buffer.partition(b"\n")
        self.buffer = rest
        return line

    def call(self, request, timeout):
        deadline = time.monotonic() + timeout
        try:
            if request.get("op") == "reset":
                self.stop()
                self._spawn()
            elif self.proc is None:
                raise TransportFailure("candidate not running")
            self._send(bounded_json_line(request), deadline)
            line = self._receive(deadline)
        except (TimeoutError, TransportFailure, InvalidCandidateResponse):
            self.stop()
            raise
        try:
            return json.loads(line, parse_constant=_reject_constant)
        except ValueError:
            raise InvalidCandidateResponse("malformed_response") from None

    def close(self):
        self.stop()
        self.workdir.cleanup()


def _reject_constant(_name):
    raise ValueError("non-finite JSON constant")


class BrokeredCandidate:
    """Trusted in-process broker proxy (never re-isolated, never executed as a child)."""

    def __init__(self, proxy_path):
        spec = importlib.util.spec_from_file_location("candidate_proxy", proxy_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.last_snapshot = None

    def call(self, request, timeout):
        box = {}

        def target():
            try:
                box["response"] = self.handle(request)
            except BaseException as error:  # relayed as a fixed category only
                box["error"] = type(error).__name__

        worker = threading.Thread(target=target, name="proxy-call", daemon=True)
        worker.start()
        worker.join(timeout)
        if worker.is_alive():
            raise TimeoutError("proxy response timeout")
        if "error" in box:
            raise TransportFailure("proxy call failed")
        return box["response"]

    def close(self):
        pass


# ----------------------------------------------------------------------------------------
# synthetic instance generation (evaluator-private)
# ----------------------------------------------------------------------------------------

def canonical_edges(u, v, n):
    u = np.asarray(u, dtype=np.int64)
    v = np.asarray(v, dtype=np.int64)
    lo, hi = np.minimum(u, v), np.maximum(u, v)
    keep = lo != hi
    keys = np.unique(lo[keep] * n + hi[keep])
    return np.column_stack([keys // n, keys % n]).astype(np.int32)


def gen_sbm(rng, n, blocks, deg_in, deg_out):
    size = n // blocks
    if size * blocks != n:
        raise ValueError("n must be divisible by blocks")
    labels = np.repeat(np.arange(blocks), size)
    p_in = min(1.0, deg_in / (size - 1))
    p_out = min(1.0, deg_out / (n - size))
    rows, cols = [], []
    for i0 in range(0, n, 500):
        i1 = min(n, i0 + 500)
        draw = rng.random((i1 - i0, n))
        thr = np.where(labels[i0:i1, None] == labels[None, :], p_in, p_out)
        mask = (draw < thr) & (np.arange(n)[None, :] > np.arange(i0, i1)[:, None])
        r, c = np.nonzero(mask)
        rows.append(r + i0)
        cols.append(c)
    return canonical_edges(np.concatenate(rows), np.concatenate(cols), n), labels.astype(np.int32)


def gen_ba(rng, n, m):
    targets = list(range(m))
    repeated = []
    us, vs = [], []
    for src in range(m, n):
        us.extend([src] * m)
        vs.extend(targets)
        repeated.extend(targets)
        repeated.extend([src] * m)
        chosen = set()
        while len(chosen) < m:
            chosen.add(repeated[int(rng.integers(len(repeated)))])
        targets = sorted(chosen)
    return canonical_edges(us, vs, n)


def gen_ws(rng, n, k, beta):
    adj = [set() for _ in range(n)]
    for u in range(n):
        for j in range(1, k // 2 + 1):
            v = (u + j) % n
            adj[u].add(v)
            adj[v].add(u)
    for j in range(1, k // 2 + 1):
        for u in range(n):
            v = (u + j) % n
            if rng.random() < beta and v in adj[u]:
                while True:
                    w = int(rng.integers(n))
                    if w != u and w not in adj[u]:
                        break
                adj[u].discard(v)
                adj[v].discard(u)
                adj[u].add(w)
                adj[w].add(u)
    us = [u for u in range(n) for v in adj[u] if u < v]
    vs = [v for u in range(n) for v in adj[u] if u < v]
    return canonical_edges(us, vs, n)


def adjacency(n, edges):
    if len(edges) == 0:
        return sp.csr_matrix((n, n))
    u, v = edges[:, 0].astype(np.int64), edges[:, 1].astype(np.int64)
    rows, cols = np.concatenate([u, v]), np.concatenate([v, u])
    return sp.csr_matrix((np.ones(len(rows)), (rows, cols)), shape=(n, n))


def two_hop(adj):
    a2 = (adj @ adj).tocsr()
    a2.data[:] = 1.0
    a2 = (a2 - a2.multiply(adj)).tocsr()
    a2 = (a2 - sp.diags(a2.diagonal())).tocsr()
    a2.eliminate_zeros()
    return a2


class Graph:
    def __init__(self, n, edges, need_two_hop):
        self.n = n
        self.adj = adjacency(n, edges)
        self.deg = np.asarray(self.adj.sum(axis=1)).ravel()
        self.adj2 = two_hop(self.adj) if need_two_hop else None
        self.deg2 = np.asarray(self.adj2.sum(axis=1)).ravel() if need_two_hop else None


def mean_outcome(mech, x, g, z):
    """Noise-free potential-outcome mean for assignment vector ``z`` (privileged)."""
    own = (mech["tau0"] + mech["tau1"] * x[:, 0]) * z
    base = mech["intercept"] + x @ np.asarray(mech["beta"]) + own
    form = mech["form"]
    count = g.adj @ z
    e1 = count / np.maximum(g.deg, 1.0)
    if form == "fraction":
        extra = mech["gamma"] * e1
    elif form == "fraction_2hop":
        e2 = (g.adj2 @ z) / np.maximum(g.deg2, 1.0)
        extra = mech["gamma"] * e1 + mech["gamma2"] * e2
    elif form == "sigmoid":
        extra = mech["gamma"] / (1.0 + np.exp(-mech["steepness"] * (e1 - mech["center"])))
    elif form == "count_deg":
        extra = mech["kappa"] * count * np.sqrt(mech["m_ref"] / np.maximum(g.deg, 1.0))
    else:
        raise ValueError("unknown mechanism form")
    return base + extra


def sha(*chunks):
    h = hashlib.sha256()
    for chunk in chunks:
        h.update(chunk)
    return h.hexdigest()


def graph_hash(n, edges):
    return sha(np.int64(n).tobytes(), np.ascontiguousarray(edges, dtype="<i4").tobytes())


def triple_hash(ghash, z, y):
    return sha(ghash.encode(), np.ascontiguousarray(z, dtype="u1").tobytes(),
               np.round(np.asarray(y) * 1e6).astype("<i8").tobytes())


class Instance:
    pass


def generate_instance(spec, seed, n):
    graph_spec, design_spec, mech = spec["graph"], spec["design"], spec["mech"]
    family = graph_spec["family"]
    fid = FAMILY_ID[family]
    grng = np.random.default_rng([seed, fid, n, 1])
    crng = np.random.default_rng([seed, fid, n, 2])
    nrng = np.random.default_rng([seed, fid, n, 4])
    trng = np.random.default_rng([seed, int(spec["id"]), n, 3])
    labels = None
    if family == "sbm":
        edges, labels = gen_sbm(grng, n, graph_spec["blocks"], graph_spec["deg_in"], graph_spec["deg_out"])
    elif family == "ba":
        edges = gen_ba(grng, n, graph_spec["m"])
    elif family == "ws":
        edges = gen_ws(grng, n, graph_spec["k"], graph_spec["rewire"])
    else:
        raise ValueError("unknown graph family")
    x = crng.standard_normal((n, 2))
    if labels is not None:
        x[:, 0] += 0.5 * crng.standard_normal(graph_spec["blocks"])[labels]
    noise = nrng.standard_normal(n) * mech["sigma"]
    g = Graph(n, edges, mech["form"] == "fraction_2hop")
    p = float(design_spec["p"])
    cluster_labels = None
    if design_spec["kind"] == "bernoulli":
        z = (trng.random(n) < p).astype(np.uint8)
    elif design_spec["kind"] == "cluster":
        if labels is None:
            raise ValueError("cluster design requires block labels")
        k_total = int(graph_spec["blocks"])
        treated = trng.permutation(k_total)[: int(round(k_total * p))]
        z = np.isin(labels, treated).astype(np.uint8)
        cluster_labels = labels
    else:
        raise ValueError("unknown design")
    zf = z.astype(np.float64)
    y = mean_outcome(mech, x, g, zf) + noise
    ones, zeros = np.ones(n), np.zeros(n)
    gate = float(np.mean(mean_outcome(mech, x, g, ones) - mean_outcome(mech, x, g, zeros)))
    inst = Instance()
    inst.spec, inst.seed, inst.n = spec, seed, n
    inst.edges, inst.x, inst.z, inst.y, inst.labels = edges, x, z, y, cluster_labels
    inst.graph, inst.gate, inst.p, inst.design_kind = g, gate, p, design_spec["kind"]
    inst.graph_hash = graph_hash(n, edges)
    inst.triple_hash = triple_hash(inst.graph_hash, z, y)
    return inst


# ----------------------------------------------------------------------------------------
# negative controls (evaluator-owned, matched format/size/budget)
# ----------------------------------------------------------------------------------------

def check_control_vacuity(inst, controls):
    """Return the set of vacuous control names (empty when all controls are non-vacuous)."""
    bad = set()
    y = inst.y
    perm = controls["perm_outcome"]["y"]
    index = controls["perm_outcome"]["perm"]
    if (not np.array_equal(np.sort(perm), np.sort(y)) or np.array_equal(perm, y)
            or float(np.mean(index != np.arange(len(index)))) < 0.99):
        bad.add("perm_outcome")
    keys = inst.edges[:, 0].astype(np.int64) * inst.n + inst.edges[:, 1]
    new_edges = controls["perm_graph"]["edges"]
    new_keys = new_edges[:, 0].astype(np.int64) * inst.n + new_edges[:, 1]
    shared = np.intersect1d(keys, new_keys).size / max(len(keys), 1)
    if shared >= 0.10 or len(new_edges) != len(inst.edges):
        bad.add("perm_graph")
    const = controls["constant"]["y"]
    if float(np.ptp(const)) != 0.0 or float(np.ptp(y)) == 0.0:
        bad.add("constant")
    return bad


def make_controls(inst, rng, perm=None, relabel=None):
    n = inst.n
    controls = {}
    for _ in range(8):
        pi = rng.permutation(n) if perm is None else perm
        controls["perm_outcome"] = {"perm": pi, "y": inst.y[pi]}
        sigma = rng.permutation(n) if relabel is None else relabel
        controls["perm_graph"] = {
            "edges": canonical_edges(sigma[inst.edges[:, 0]], sigma[inst.edges[:, 1]], n)}
        controls["constant"] = {"y": np.full(n, round(float(np.mean(inst.y)), 6))}
        bad = check_control_vacuity(inst, controls)
        if not bad or perm is not None or relabel is not None:
            return controls, bad
    return controls, bad


_DTYPE_NAMES = {"int32": "<i4", "float64": "<f8", "uint8": "u1"}


def encode_array(array, dtype):
    a = np.ascontiguousarray(array, dtype=np.dtype(_DTYPE_NAMES[dtype]))
    return {"dtype": dtype, "shape": list(a.shape), "encoding": "base64-le",
            "data": base64.b64encode(a.tobytes()).decode("ascii")}


REQUEST_KEYS = {"op", "n", "edges", "covariates", "treatment", "outcomes", "design", "workload"}
DESIGN_KEYS = {"kind", "probability", "cluster_labels"}
WORKLOAD_KEYS = {"max_op_seconds", "ci_level"}


def build_request(inst, edges, y):
    request = {
        "op": "estimate", "n": int(inst.n),
        "edges": encode_array(edges, "int32"),
        "covariates": encode_array(inst.x, "float64"),
        "treatment": encode_array(inst.z, "uint8"),
        "outcomes": encode_array(y, "float64"),
        "design": {"kind": inst.design_kind, "probability": float(inst.p),
                   "cluster_labels": None if inst.labels is None else encode_array(inst.labels, "int32")},
        "workload": {"max_op_seconds": SOFT_OP_SECONDS, "ci_level": 0.95},
    }
    if (set(request) != REQUEST_KEYS or set(request["design"]) != DESIGN_KEYS
            or set(request["workload"]) != WORKLOAD_KEYS):
        raise ValueError("candidate request schema violation")
    return request


# ----------------------------------------------------------------------------------------
# evaluator-owned baselines
# ----------------------------------------------------------------------------------------

def _ols_gate(feature_fn, inst, extra=None):
    g = inst.graph
    zf = inst.z.astype(np.float64)
    design = feature_fn(g, inst.x, zf)
    beta, *_ = np.linalg.lstsq(design, inst.y, rcond=None)
    ones, zeros = np.ones(inst.n), np.zeros(inst.n)
    pred1 = feature_fn(g, inst.x, ones) @ beta
    pred0 = feature_fn(g, inst.x, zeros) @ beta
    return float(np.mean(pred1 - pred0))


def _linear_features(g, x, z):
    e1 = (g.adj @ z) / np.maximum(g.deg, 1.0)
    return np.column_stack([np.ones(len(z)), z, e1, x])


def _oracle_features_for(mech):
    form = mech["form"]

    def features(g, x, z):
        count = g.adj @ z
        e1 = count / np.maximum(g.deg, 1.0)
        cols = [np.ones(len(z)), z, x[:, 0], x[:, 1], z * x[:, 0]]
        if form == "fraction":
            cols.append(e1)
        elif form == "fraction_2hop":
            cols.extend([e1, (g.adj2 @ z) / np.maximum(g.deg2, 1.0)])
        elif form == "sigmoid":
            cols.append(1.0 / (1.0 + np.exp(-mech["steepness"] * (e1 - mech["center"]))))
        elif form == "count_deg":
            cols.append(count * np.sqrt(mech["m_ref"] / np.maximum(g.deg, 1.0)))
        return np.column_stack(cols)

    return features


def baseline_dim(inst):
    t = inst.z == 1
    return float(inst.y[t].mean() - inst.y[~t].mean())


def baseline_ht(inst):
    g = inst.graph
    z = inst.z.astype(np.float64)
    closed_treated = z + g.adj @ z
    size = g.deg + 1.0
    all_treated = (closed_treated == size)
    all_control = (closed_treated == 0)
    p = inst.p
    if inst.design_kind == "bernoulli":
        log_pi1 = size * math.log(p)
        log_pi0 = size * math.log(1.0 - p)
    else:
        k_total = int(inst.spec["graph"]["blocks"])
        k = int(round(k_total * p))
        member = sp.csr_matrix((np.ones(inst.n), (np.arange(inst.n), inst.labels)), shape=(inst.n, k_total))
        s = np.asarray(((g.adj + sp.identity(inst.n)) @ member > 0).sum(axis=1)).ravel().astype(int)
        log_pi1 = np.full(inst.n, -np.inf)
        log_pi0 = np.full(inst.n, -np.inf)
        for size_s in np.unique(s):
            sel = s == size_s
            j = np.arange(int(size_s))
            if size_s <= k:
                log_pi1[sel] = np.sum(np.log((k - j) / (k_total - j)))
            if size_s <= k_total - k:
                log_pi0[sel] = np.sum(np.log((k_total - k - j) / (k_total - j)))
    terms = np.zeros(inst.n)
    t1 = all_treated & np.isfinite(log_pi1)
    t0 = all_control & np.isfinite(log_pi0)
    terms[t1] += inst.y[t1] * np.exp(-log_pi1[t1])
    terms[t0] -= inst.y[t0] * np.exp(-log_pi0[t0])
    return float(terms.mean())


def compute_baselines(inst, record_failure):
    estimates = {}
    runners = {
        "dim": lambda: baseline_dim(inst),
        "linear": lambda: _ols_gate(_linear_features, inst),
        "ht": lambda: baseline_ht(inst),
        "oracle": lambda: _ols_gate(_oracle_features_for(inst.spec["mech"]), inst),
    }
    failed = 0
    for name in BASELINES:
        try:
            try:
                with np.errstate(divide="raise", over="raise", invalid="raise"):
                    value = float(runners[name]())
            except (np.linalg.LinAlgError, FloatingPointError, ValueError, ZeroDivisionError,
                    OverflowError, MemoryError):
                fail_required_baseline("baseline_result_failure", lambda: None,
                                       lambda category: record_failure(
                                           {"component": "baseline", "category": category,
                                            "operation": "baseline_worker"}))
            if not math.isfinite(value):
                fail_required_baseline("baseline_result_failure", lambda: None,
                                       lambda category: record_failure(
                                           {"component": "baseline", "category": category,
                                            "operation": "baseline_worker"}))
            estimates[name] = value
        except RequiredBaselineFailure:
            estimates[name] = None
            failed += 1
    return estimates, failed


# ----------------------------------------------------------------------------------------
# response validation and per-episode records
# ----------------------------------------------------------------------------------------

def _finite_number(value):
    return type(value) in (int, float) and math.isfinite(value) and abs(value) < 1e15


def validate_estimate_response(response):
    if type(response) is not dict:
        raise InvalidCandidateResponse("malformed_response")
    if "__error__" in response:
        raise InvalidCandidateResponse("candidate_exception")
    required = {"estimate", "ci_low", "ci_high"}
    if not required <= set(response) or set(response) - required - {"diagnostics"}:
        raise InvalidCandidateResponse("malformed_response")
    if not all(_finite_number(response[k]) for k in required):
        raise InvalidCandidateResponse("malformed_response")
    est, lo, hi = float(response["estimate"]), float(response["ci_low"]), float(response["ci_high"])
    if not lo <= est <= hi:
        raise InvalidCandidateResponse("malformed_response")
    if "diagnostics" in response:
        diag = response["diagnostics"]
        if type(diag) is not dict:
            raise InvalidCandidateResponse("malformed_response")
        try:
            if len(json.dumps(diag, allow_nan=False).encode("utf-8")) > 4096:
                raise InvalidCandidateResponse("malformed_response")
        except (TypeError, ValueError):
            raise InvalidCandidateResponse("malformed_response") from None
    return est, lo, hi


def new_record(ep):
    return {"seed": ep["seed"], "case": ep["case"], "kind": ep["kind"], "gate": None,
            "primary": None, "ctrl": {"constant": None, "perm_outcome": None, "perm_graph": None},
            "base": {name: None for name in BASELINES}, "vacuity": 0, "ok_ops": 0,
            "integrity": 0, "baseline_failed": 0, "duration": 0.0}


# ----------------------------------------------------------------------------------------
# aggregation
# ----------------------------------------------------------------------------------------

def rel_error(est, gate):
    if est is None or gate is None:
        return REL_CAP
    return min(abs(est - gate) / abs(gate), REL_CAP)


def signed_error(est, gate):
    if est is None or gate is None:
        return REL_CAP
    return float(np.clip((est - gate) / abs(gate), -REL_CAP, REL_CAP))


def plane_rmse(primary, getter):
    """Per-case RMSE over seeds, then unweighted mean over the 8 cases."""
    per_case = []
    for case in range(1, N_CASES + 1):
        values = [rel_error(getter(r), r["gate"]) for r in primary if r["case"] == case]
        per_case.append(math.sqrt(sum(v * v for v in values) / len(values)))
    return sum(per_case) / len(per_case), per_case


def aggregate(records, replay_record, first_record):
    primary = [r for r in records if r["kind"] == "primary"]
    rmse, per_case = plane_rmse(primary, lambda r: None if r["primary"] is None else r["primary"][0])
    bias, cover, width = [], [], []
    perm_rel = []
    for case in range(1, N_CASES + 1):
        rs = [r for r in primary if r["case"] == case]
        bias.append(abs(sum(signed_error(None if r["primary"] is None else r["primary"][0], r["gate"])
                            for r in rs) / len(rs)))
        c, w, pr = [], [], []
        for r in rs:
            if r["primary"] is None or r["gate"] is None:
                c.append(0.0)
                w.append(WIDTH_CAP)
            else:
                _, lo, hi = r["primary"]
                c.append(1.0 if lo <= r["gate"] <= hi else 0.0)
                w.append(min((hi - lo) / abs(r["gate"]), WIDTH_CAP))
            pe = r["ctrl"]["perm_outcome"]
            pr.append(REL_CAP if pe is None or r["gate"] is None else min(abs(pe) / abs(r["gate"]), REL_CAP))
        cover.append(sum(c) / len(c))
        width.append(sum(w) / len(w))
        perm_rel.append(sum(pr) / len(pr))
    base = {}
    for name in BASELINES:
        base[name], _ = plane_rmse(primary, lambda r, name=name: r["base"][name])
    graph_rmse, _ = plane_rmse(primary, lambda r: r["ctrl"]["perm_graph"])
    const_vals = [CONST_ABS_WORST if r["ctrl"]["constant"] is None else abs(r["ctrl"]["constant"])
                  for r in records]
    if (replay_record["primary"] is None or first_record["primary"] is None):
        replay_diff = REPLAY_WORST
    else:
        replay_diff = abs(replay_record["primary"][0] - first_record["primary"][0])
    failed = sum(1 for r in primary if r["ok_ops"] < len(OPS))
    metrics = {
        "combined_score": -rmse, "rmse_rel": rmse,
        "bias_rel_abs_mean": sum(bias) / len(bias),
        "ci_coverage": sum(cover) / len(cover),
        "ci_width_rel": sum(width) / len(width),
        "baseline_dim_rmse_rel": base["dim"], "baseline_linear_rmse_rel": base["linear"],
        "baseline_ht_rmse_rel": base["ht"], "baseline_oracle_rmse_rel": base["oracle"],
        "ratio_to_linear_baseline": rmse / max(base["linear"], 1e-9),
        "ratio_to_dim_baseline": rmse / max(base["dim"], 1e-9),
        "control_constant_max_abs_est": max(const_vals),
        "control_permuted_outcome_mean_abs_rel_est": sum(perm_rel) / len(perm_rel),
        "control_permuted_graph_rmse_rel": graph_rmse,
        "control_vacuity_violations": float(sum(r["vacuity"] for r in records)),
        "missing_or_failed_episodes": float(failed),
        "replay_abs_diff": replay_diff,
    }
    for k, value in enumerate(per_case, start=1):
        metrics[f"rmse_rel_case_{k}"] = value
    if set(metrics) != set(METRIC_NAMES) or not all(math.isfinite(v) for v in metrics.values()):
        raise ValueError("invalid metric record")
    return {name: float(metrics[name]) for name in METRIC_NAMES}


# ----------------------------------------------------------------------------------------
# setup / main
# ----------------------------------------------------------------------------------------

def load_resources(root):
    with open(root / "case_specs.json", "r", encoding="utf-8") as handle:
        specs = json.load(handle)
    with open(root / "manifest.json", "r", encoding="utf-8") as handle:
        manifest = json.load(handle)
    if specs.get("plane") != PLANE or manifest.get("plane") != PLANE or len(specs["cases"]) != N_CASES:
        raise ValueError("resource plane mismatch")
    index = {(e["case"], e["seed"], e["n"]): e for e in manifest["instances"]}
    return specs, index


def build_episodes(smoke):
    seeds = SEEDS[:1] if smoke else SEEDS
    episodes = [{"seed": s, "case": c, "kind": "primary"} for s in seeds for c in range(1, N_CASES + 1)]
    episodes.append({"seed": seeds[0], "case": 1, "kind": "replay"})
    for ep in episodes:
        ep["record"] = new_record(ep)
    return episodes


def expected_reset_sequence(smoke):
    seeds = SEEDS[:1] if smoke else SEEDS
    return [s for s in seeds for _ in range(N_CASES)] + [seeds[0]]


def atomic_write_json(path, value):
    tmp = path.with_name(path.name + ".tmp")
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False)
    os.replace(tmp, path)


def evidence_records(episodes):
    by_seed = collections.OrderedDict()
    for ep in episodes:
        r = ep["record"]
        by_seed.setdefault(r["seed"], []).append(r)
    out = []
    for seed, recs in by_seed.items():
        prim = [r for r in recs if r["kind"] == "primary"]
        errs = [rel_error(None if r["primary"] is None else r["primary"][0], r["gate"]) for r in prim]
        out.append({
            "seed": int(seed),
            "score": float(-sum(errs) / len(errs)),
            "correct": bool(all(r["ok_ops"] >= len(OPS) for r in recs)),
            "duration_seconds": float(sum(r["duration"] for r in recs)),
        })
    return out


def run(args):
    t0 = time.monotonic()
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    repair_visible = PLANE == "search" and (smoke or qualification)
    root = Path(os.environ.get("TASK_SOURCE_DIR") or Path(__file__).resolve().parent) / "resources" / PLANE
    specs, manifest_index = load_resources(root)
    n = int(specs["n_smoke"] if smoke else specs["n_production"])
    episodes = build_episodes(smoke)
    expected_seq = expected_reset_sequence(smoke)
    expected_rpcs = len(episodes) * OPS_PER_EPISODE
    if expected_rpcs > MAX_CANDIDATE_RPC_CALLS:
        raise ValueError("declared transcript exceeds the RPC budget")
    require_plane_budget({
        "episode_count": len(episodes), "method_count": 1,
        "wall_seconds": WALL_SECONDS, "startup_seconds": STARTUP_ALLOWANCE,
        "reset_seconds": RESET_TIMEOUT, "cleanup_seconds": EPISODE_OVERHEAD - KILL_WAIT,
        "finish_seconds": FINISH_RESERVE, "work_seconds": 4 * ESTIMATE_TIMEOUT + 3.0})

    state = {"idx": -1, "rpc_count": 0, "reset_log": [], "snapshot_note": None}
    failures = []

    def record_failure(failure):
        failures.append(failure)
        line = ("episode_failure plane=%s component=%s category=%s operation=%s" % (
            PLANE, bounded_failure_name(failure.get("component"), "unknown"),
            bounded_failure_name(failure.get("category"), "unknown"),
            bounded_failure_name(failure.get("operation"), "unknown")))
        print(line[:256], file=sys.stderr, flush=True)

    # ---- setup: instances, controls, baselines (all evaluator-owned, before candidate work)
    prepared = {}
    max_request_bytes = 0
    for ep in episodes:
        key = (ep["case"], ep["seed"])
        rec = ep["record"]
        if key not in prepared:
            spec = specs["cases"][ep["case"] - 1]
            inst = generate_instance(spec, ep["seed"], n)
            controls, bad = make_controls(inst, np.random.default_rng([ep["seed"], ep["case"], n, 9]))
            order = [OPS[i] for i in np.random.default_rng([ep["seed"], ep["case"], n, 7]).permutation(len(OPS))]
            entry = manifest_index.get((ep["case"], ep["seed"], n))
            integrity = 0
            if (entry is None or entry["graph_sha256"] != inst.graph_hash
                    or entry["triple_sha256"] != inst.triple_hash):
                integrity += 1
            if not (math.isfinite(inst.gate) and abs(inst.gate) >= GATE_FLOOR):
                integrity += 1
            prepared[key] = {"inst": inst, "controls": controls, "bad": bad, "order": order,
                             "integrity": integrity, "baselines": None, "base_failed": 0}
            if ep["kind"] == "primary":
                est, failed = compute_baselines(inst, record_failure)
                prepared[key]["baselines"], prepared[key]["base_failed"] = est, failed
        item = prepared[key]
        rec["gate"] = item["inst"].gate
        rec["integrity"] = item["integrity"]
        rec["vacuity"] = len(item["bad"])
        if item["baselines"] is not None:
            rec["base"] = dict(item["baselines"])
            rec["baseline_failed"] = item["base_failed"]
    if len({(p["inst"].triple_hash) for p in prepared.values()}) != len(prepared):
        for ep in episodes:
            ep["record"]["integrity"] += 1
    biggest = max(prepared.values(), key=lambda p: len(p["inst"].edges))
    probe = bounded_json_line(build_request(biggest["inst"], biggest["inst"].edges, biggest["inst"].y))
    max_request_bytes = len(probe)
    if max_request_bytes >= PAYLOAD_TARGET:
        raise ValueError("largest request exceeds the internal payload target")
    del probe

    # ---- transport
    program_path = str(args.program_path)
    if os.environ.get("AGENTIC_CANDIDATE_SOCKET") and program_path == BROKER_PROXY_PATH:
        transport = BrokeredCandidate(BROKER_PROXY_PATH)
    else:
        transport = NativeCandidate(Path(program_path).resolve(), repair_visible)

    def rpc(request, timeout):
        if request.get("op") == "reset":
            state["idx"] += 1
            state["reset_log"].append(request["seed"])
        state["rpc_count"] += 1
        if state["rpc_count"] > MAX_CANDIDATE_RPC_CALLS:
            raise TransportFailure("rpc budget exhausted")
        bounded_json_line(request)
        started = time.monotonic()
        try:
            return transport.call(request, timeout)
        finally:
            idx = min(max(state["idx"], 0), len(episodes) - 1)
            episodes[idx]["record"]["duration"] += time.monotonic() - started

    def evaluate(ep, call, work_deadline):
        item = prepared[(ep["case"], ep["seed"])]
        inst, controls, rec = item["inst"], item["controls"], ep["record"]
        for op_name in item["order"]:
            if op_name in item["bad"]:
                record_failure({"component": "evaluator", "category": "vacuous_control",
                                "operation": "control_check"})
                continue
            if op_name == "primary":
                request = build_request(inst, inst.edges, inst.y)
            elif op_name == "perm_outcome":
                request = build_request(inst, inst.edges, controls["perm_outcome"]["y"])
            elif op_name == "perm_graph":
                request = build_request(inst, controls["perm_graph"]["edges"], inst.y)
            else:
                request = build_request(inst, inst.edges, controls["constant"]["y"])
            try:
                est, lo, hi = validate_estimate_response(call(request))
            except InvalidCandidateResponse as error:
                record_failure({"component": "candidate", "category": error.category,
                                "operation": "estimate"})
                continue
            rec["ok_ops"] += 1
            if op_name == "primary":
                rec["primary"] = (est, lo, hi)
            else:
                rec["ctrl"][op_name] = est
        return rec

    hard_deadline = t0 + WALL_SECONDS - STARTUP_ALLOWANCE
    try:
        _, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE,
            reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD,
            rpc_caps={"reset": RESET_TIMEOUT, "estimate": ESTIMATE_TIMEOUT, "default": ESTIMATE_TIMEOUT},
            clock=time.monotonic, rpc=rpc, evaluate=evaluate,
            worst_case=lambda ep: ep["record"], record_failure=record_failure)
    finally:
        transport.close()
    if repair_visible and failures:
        for text in getattr(transport, "kept_stderr", []):
            sys.stderr.write(text)
        sys.stderr.flush()

    records = [ep["record"] for ep in episodes]
    primary_records = records[:-1]
    metrics = aggregate(records, records[-1], records[0])
    transcript_ok = state["reset_log"] == expected_seq
    baseline_ok = all(r["baseline_failed"] == 0 for r in primary_records)
    integrity_ok = all(r["integrity"] == 0 for r in records)
    constant_ok = metrics["control_constant_max_abs_est"] <= CONST_TOL
    replay_tol = REPLAY_TOL * max(1.0, abs(records[0]["primary"][0]) if records[0]["primary"] else 1.0)
    correct = bool(
        transcript_ok and state["rpc_count"] <= MAX_CANDIDATE_RPC_CALLS
        and metrics["missing_or_failed_episodes"] == 0 and records[-1]["ok_ops"] == len(OPS)
        and baseline_ok and integrity_ok
        and metrics["baseline_oracle_rmse_rel"] <= ORACLE_SANITY_MAX
        and metrics["control_vacuity_violations"] == 0 and constant_ok
        and metrics["replay_abs_diff"] <= replay_tol)
    feasible = bool((not smoke) and complete and transcript_ok
                    and state["rpc_count"] <= MAX_CANDIDATE_RPC_CALLS
                    and time.monotonic() - t0 <= WALL_SECONDS - STARTUP_ALLOWANCE)

    results = Path(args.results_dir)
    results.mkdir(parents=True, exist_ok=True)
    atomic_write_json(results / "metrics.json", metrics)
    atomic_write_json(results / "correct.json", {"correct": correct})
    atomic_write_json(results / "evaluation_evidence.json",
                      {"schema_version": 1, "episodes": evidence_records(episodes)})
    if qualification:
        atomic_write_json(results / "qualification.json", {"schema_version": 1, "feasible": feasible})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        run(args)
    except SystemExit:
        raise
    except BaseException as error:
        name = type(error).__name__
        if not (name.isascii() and name.isidentifier() and len(name) <= 80):
            name = "Exception"
        detail = ""
        if PLANE == "search":
            detail = " " + " ".join(str(error).split())[:160]
        print(("evaluator_error plane=%s type=%s%s" % (PLANE, name, detail))[:256], file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
