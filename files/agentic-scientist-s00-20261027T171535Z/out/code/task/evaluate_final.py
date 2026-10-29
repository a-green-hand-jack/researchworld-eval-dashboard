#!/usr/bin/env python3
"""Sealed final-plane evaluator: random-walk cover-time prediction on small connected graphs.

Self-contained. Reads only ``resources/<plane>`` (resolved from TASK_SOURCE_DIR or the
directory of this file). The candidate is driven over ``handle(request)`` with the ops
reset / fit / predict. Ground truth is an evaluator-owned Monte Carlo estimate of the
start-averaged cover time; it never crosses the RPC boundary except for the plane's
training graphs.

Aggregation hierarchy (fixed before evaluation, equal weights):
  per-graph error min(|ln(pred/MC)|, 10)  ->  family mean over that family's test graphs
  ->  family-macro mean over the plane's test families  ->  mean over episodes (seeds)
  ->  combined_score = -macro_log_mae.
A failed/missing episode contributes the worst case (error 10, perm deviation 1e6) in the
original fixed denominator. perm_max_rel_dev is the max over episodes.
"""

import argparse
import collections
import hashlib
import importlib.util
import json
import math
import os
import selectors
import select
import signal
import subprocess
import sys
import tempfile
import threading
import time

_START = time.monotonic()

os.environ.setdefault("OPENBLAS_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", "2")
os.environ.setdefault("MKL_NUM_THREADS", "2")

# ----------------------------------------------------------------------------------------
# Plane constants (the search/final evaluators differ only in this block)
# ----------------------------------------------------------------------------------------
PLANE = "final"
WALL_SECONDS = 600.0
RESET_SEQUENCE = (201, 202, 203)
SMOKE_RESET_SEQUENCE = (201,)
MAX_RPC_CALLS = 24
MC_BUDGET_SECONDS = 150.0
ID_SEED = 9103
# Normalized content hashes of the (search-visible) search graphs; final graphs must be disjoint.
PRIOR_PLANE_HASHES = frozenset((
    "03b40294ec4bbdd0be33acd4bcbf3cf69c3323d3c026bf466c09f585c3f53c30",
    "056c94940d1d07b72b7792de06e9a786d2517f21e00be6a1648dab8b7fd72f40",
    "0b0a19534eba5c6f2820cc9c681c3d085a57d170e9439d78d72602c900f85cb9",
    "103920c6d7f5ed89a5d1c7820a160b1d9de3c5a976b40342f889cc420185d7b5",
    "17576eb293a46674fd220e79187b0cd6f9e56c1f76107c57896b873af04a6ef6",
    "204dc62754b72c15fe5c3e2603b99b9b099f26710daa3a182611c3067f5c4c4d",
    "38fa2e08f83c0540cd04e424ac8c7dea305a055dd364aba9f4cbeaf365143831",
    "39d8cce82be65d3aeb553bc011b16ebae3a5eae954817e7443ebe8a1c9021b39",
    "42af55ab2e55229f9fbd092301bd0ad32b7e973874282a406fbd4b552941d97f",
    "4cf73be7fe8944c6ab2fc4728ace8be7fc8303446173eafbcfaac78bcdaa037a",
    "525df129c0860a69a4f29d5d3117df9afc424f6016805cff4a9fbafd00cab3fe",
    "566e2d21feb08c8217131287a5e1c2e0ffe36e58522d4b77f0f2bd588d3af22e",
    "5b794d5243089fbe4097fc9390b1875cf859673c6a254ee07b23d3fb0e87cde2",
    "5c4d7dc8b3e155b1a17ef79af526492564419d771d55f274389a02a24f18ab3d",
    "6c3c4c80354b197675db8f324fa0692b522cf39cb096296baefde95904b9cc0c",
    "7448bcd2935fdf408f74d7432eb2ee963a5dbc19da6049c92d98545f7705d1f8",
    "82c07fc05f6a1a3943e7e640135f6d28c32070dd43a720924957880094f40604",
    "848f79083417a5e4696ca5d1e1bc5f01b2c0ad0790716329ea8c8de03e107212",
    "9446549577ba00f3775eb1e710864a0111326795987a4faccf2718805d4ba86a",
    "95c4371f011bad78affdde6513ebc34440d1926a42e97875d06a1acc59c34838",
    "9a0e97b7107f310e6683f16bacc48e578effafe92f4793b591c23f70648d17da",
    "a5eedc7a09fa579a2fd1d8fd9729732d2a72e143422728e6de8c9f30d01707e8",
    "a79292d83f0eb5e290f42fc84257595ea627e16488bf203d5965228682368dd0",
    "a9b3c269a24516bf97509c3eaa224e3fc515c1ab8cbe27b41a09f924b06a2338",
    "aca9501ed5aa381ea8be42437c660e09628366a61dceffde2d3028bdac3ff1b5",
    "acb7fb87f08bdce6e4358ac6db06bcb3a30d921acdb0a67048a73aeebe384fc4",
    "b24021e1aacfc07d4eb09c217844450fd57784bc1657992751124a089dc232be",
    "b2a8d469fca778296f261c2be4e8b972d01a44f9391814ebfaff875f53730d88",
    "b5bda14baee9360a1f679a50a97f4a71010dec3cfd05c5d623cb730ba15c599e",
    "b61d05f19092ddbd96c80abd3a41fa382eee065a3bf0309d8c225ab484f8c2f8",
    "bfdd44ac788e3816363e2353abe4694019aa703c3ea3fe3c07358a243669f7d1",
    "cc58ff05b0bab8d47a26dd02a3826f8f4738a397ed3d79fe4fc3f6fa6064b8bb",
    "cd230dc74c2f98883c617a0692f41d8bfeaf2bfed10d79dfeffbc55f5ecf9acc",
    "d32143be161fcd802c72fe63be1247103a85c322276cfc892fde484e7adef120",
    "f0bd55c521e58b08ec8724b5e307f212c196afae324850a771b0107da6324f78",
    "fd2e56a25c4ac604313f4c3a589d47381098822cc185c42f400404f47322989d",
))
# ----------------------------------------------------------------------------------------

STARTUP_ALLOWANCE = 20.0
FINISH_RESERVE = 5.0
RESET_TIMEOUT = 20.0
RPC_CAP = 45.0
EPISODE_WORK_SECONDS = 45.0
# candidate terminate(2)+kill(2) waits + stderr teardown(1) + bookkeeping(1)
EPISODE_OVERHEAD = 6.0
MC_WALKS = 300
SMOKE_MC_WALKS = 20
VALIDATION_WALKS_PER_START = 300
ERR_CLIP = 10.0
PERM_TOL = 1e-6
PERM_DEV_WORST = 1e6
MC_SE_WORST = 1e6
WIRE_LIMIT = 64 * 1024 * 1024
ENVELOPE_ALLOWANCE = 4096
CHUNK = 16
PROXY_PATH = "/broker-code/candidate_proxy.py"
METRIC_NAMES = (
    "combined_score", "macro_log_mae", "bound_macro_log_mae", "const_macro_log_mae",
    "shuffle_macro_log_mae", "improvement_vs_bound", "perm_max_rel_dev", "mc_rel_se_median",
)


# ----------------------------------------------------------------------------------------
# Generic bounded helpers
# ----------------------------------------------------------------------------------------
def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) + ENVELOPE_ALLOWANCE >= wire_limit:
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


def fixed_weight_score(values, weights, worst_case):
    if (not values or len(values) != len(weights)
            or any(not math.isfinite(w) or w < 0 for w in weights)
            or not math.isclose(sum(weights), 1.0, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("invalid predeclared aggregation weights")
    retained = [worst_case if value is None else value for value in values]
    if not all(math.isfinite(value) for value in retained):
        raise ValueError("nonfinite contribution")
    return sum(value * weight for value, weight in zip(retained, weights))


def candidate_subprocess_settings(parent_environment):
    runtime_names = (
        "PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ",
        "CUDA_VISIBLE_DEVICES", "NVIDIA_VISIBLE_DEVICES", "NVIDIA_DRIVER_CAPABILITIES",
        "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS",
        "XLA_PYTHON_CLIENT_PREALLOCATE", "XLA_PYTHON_CLIENT_MEM_FRACTION",
        "XLA_PYTHON_CLIENT_ALLOCATOR",
    )
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
    )
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


# ----------------------------------------------------------------------------------------
# Failure identity helpers
# ----------------------------------------------------------------------------------------
class InvalidResetResponse(RuntimeError):
    pass


def require_reset_ack(response):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise InvalidResetResponse("invalid reset response")


def bounded_failure_name(value, fallback):
    import re
    return value if isinstance(value, str) and re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) else fallback


class RequiredBaselineFailure(RuntimeError):
    def __init__(self, category):
        self.category = bounded_failure_name(category, "invalid_baseline_diagnostic")
        super().__init__("required baseline failed")


class CandidateProtocolError(RuntimeError):
    """Expected candidate-side protocol failure with a fixed bounded category."""

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
            episode_work_deadline = min(work_deadline, clock() + EPISODE_WORK_SECONDS)
            value = evaluate(episode, call, episode_work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse, CandidateProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ----------------------------------------------------------------------------------------
# Candidate transports
# ----------------------------------------------------------------------------------------
_NATIVE_RUNNER = r'''
import importlib.util, json, os, sys
_out = os.fdopen(os.dup(1), "w", buffering=1)
os.dup2(2, 1)
sys.stdout = sys.stderr
_path = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(_path)))
_spec = importlib.util.spec_from_file_location("candidate_program", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
for _line in sys.stdin:
    _resp = _mod.handle(json.loads(_line))
    _out.write(json.dumps(_resp, allow_nan=False, separators=(",", ":")) + "\n")
    _out.flush()
'''


def _reject_constant(_name):
    raise ValueError("nonfinite JSON constant")


def _decode_response(raw):
    try:
        value = json.loads(raw.decode("utf-8"), parse_constant=_reject_constant)
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise CandidateProtocolError("malformed_response") from None
    if type(value) is not dict:
        raise CandidateProtocolError("malformed_response")
    return value


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke path)."""

    def __init__(self, program_path):
        self.program_path = os.path.abspath(program_path)
        self.proc = None
        self.capture = None
        self.rbuf = bytearray()
        self.workdir = tempfile.mkdtemp(prefix="cand_")
        self.snapshot = None
        self.cleanup_error = False

    def start(self):
        self.stop()
        python, env = candidate_subprocess_settings(os.environ)
        cpu = cpu_limit_seconds(WALL_SECONDS, 1)

        def limits():
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
            resource.setrlimit(resource.RLIMIT_AS, (6 << 30, 6 << 30))
            resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))

        self.proc = subprocess.Popen(
            [python, "-I", "-c", _NATIVE_RUNNER, self.program_path],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, cwd=self.workdir, shell=False, start_new_session=True, preexec_fn=limits,
        )
        self.capture = BoundedWorkerStderr(self.proc.stderr)
        os.set_blocking(self.proc.stdin.fileno(), False)
        os.set_blocking(self.proc.stdout.fileno(), False)
        self.rbuf = bytearray()
        self.snapshot = None

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return self.snapshot
        try:
            try:
                proc.stdin.close()
            except OSError:
                pass
            for sig, wait in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
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
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.stdout.close()
            except OSError:
                pass
        finally:
            try:
                self.snapshot = self.capture.close()
            except RuntimeError:
                self.snapshot = {"stderr": "", "observed_bytes": 0, "retained_bytes": 0,
                                 "truncated": True, "capture_error": "cleanup_unresolved"}
                self.cleanup_error = True
            self.capture = None
        return self.snapshot

    def _send(self, data, deadline):
        fd = self.proc.stdin.fileno()
        view = memoryview(data)
        while len(view):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("send timeout")
            _, w, _ = select.select([], [fd], [], min(remaining, 0.5))
            if not w:
                continue
            try:
                sent = os.write(fd, view[:65536])
            except BlockingIOError:
                continue
            except (BrokenPipeError, OSError):
                raise CandidateProtocolError("candidate_exit") from None
            view = view[sent:]

    def _read_line(self, deadline):
        fd = self.proc.stdout.fileno()
        while True:
            i = self.rbuf.find(b"\n")
            if i >= 0:
                line = bytes(self.rbuf[:i])
                del self.rbuf[:i + 1]
                return line
            if len(self.rbuf) + ENVELOPE_ALLOWANCE >= WIRE_LIMIT:
                raise CandidateProtocolError("response_too_large")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("read timeout")
            r, _, _ = select.select([fd], [], [], min(remaining, 0.5))
            if not r:
                continue
            try:
                chunk = os.read(fd, 1 << 20)
            except BlockingIOError:
                continue
            except OSError:
                raise CandidateProtocolError("candidate_exit") from None
            if not chunk:
                raise CandidateProtocolError("candidate_exit")
            self.rbuf.extend(chunk)

    def call(self, request, timeout):
        deadline = time.monotonic() + timeout
        data = bounded_json_line(request)
        try:
            if request.get("op") == "reset" or self.proc is None:
                self.start()
            self._send(data, deadline)
            return _decode_response(self._read_line(deadline))
        except BaseException:
            self.stop()
            raise


class BrokeredCandidate:
    """Trusted broker proxy loaded in-process (production search/final)."""

    def __init__(self, path):
        self.path = path
        self.handle = None
        self.thread = None

    def _load(self):
        spec = importlib.util.spec_from_file_location("candidate_proxy", self.path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle

    def stop(self):
        return None

    def call(self, request, timeout):
        deadline = time.monotonic() + timeout
        bounded_json_line(request)
        if self.handle is None:
            self._load()
        if self.thread is not None and self.thread.is_alive():
            self.thread.join(max(deadline - time.monotonic(), 0))
            if self.thread.is_alive():
                raise TimeoutError("previous call still running")
        box = {}

        def run():
            try:
                box["value"] = self.handle(request)
            except BaseException as error:  # noqa: BLE001 - reported only as a category
                box["error"] = type(error).__name__

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        thread.join(max(deadline - time.monotonic(), 0))
        if thread.is_alive():
            self.thread = thread
            raise TimeoutError("rpc timeout")
        if "error" in box:
            raise CandidateProtocolError("candidate_error")
        try:
            encoded = json.dumps(box["value"], allow_nan=False, separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError, RecursionError):
            raise CandidateProtocolError("malformed_response") from None
        if len(encoded) + ENVELOPE_ALLOWANCE >= WIRE_LIMIT:
            raise CandidateProtocolError("response_too_large")
        value = json.loads(encoded.decode("utf-8"))
        if type(value) is not dict:
            raise CandidateProtocolError("malformed_response")
        return value


# ----------------------------------------------------------------------------------------
# Data, Monte Carlo ground truth, controls
# ----------------------------------------------------------------------------------------
def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", PLANE)


def graph_hash(n, edges):
    import networkx as nx
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from(edges)
    wl = nx.weisfeiler_lehman_graph_hash(g, iterations=4, digest_size=16)
    return hashlib.sha256(f"wl4:{wl}:{g.number_of_nodes()}:{g.number_of_edges()}".encode()).hexdigest()


def is_connected(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    seen = {0}
    stack = [0]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    return len(seen) == n


def load_graphs(smoke):
    root = resource_root()
    splits = {}
    for split in ("train", "test"):
        with open(os.path.join(root, f"{split}_graphs.json"), "r", encoding="utf-8") as handle:
            doc = json.load(handle)
        if doc.get("schema_version") != 1 or doc.get("plane") != PLANE or doc.get("split") != split:
            raise RuntimeError("resource manifest mismatch")
        splits[split] = doc
    if splits["train"]["mc_seed"] != splits["test"]["mc_seed"]:
        raise RuntimeError("resource manifest mismatch")
    seen_hash = {}
    for split in ("train", "test"):
        for g in splits[split]["graphs"]:
            n = g["n"]
            edges = [tuple(e) for e in g["edges"]]
            if not (6 <= n <= 30) or len(set(edges)) != len(edges) or any(
                    not (0 <= u < v < n) for u, v in edges) or not is_connected(n, edges):
                raise RuntimeError("invalid graph in resources")
            if graph_hash(n, edges) != g["content_hash"]:
                raise RuntimeError("content hash mismatch")
            if g["content_hash"] in seen_hash:
                raise RuntimeError("duplicate normalized graph content within plane")
            seen_hash[g["content_hash"]] = split
            if g["content_hash"] in PRIOR_PLANE_HASHES:
                raise RuntimeError("normalized graph content overlaps another plane")
    out = {}
    for split in ("train", "test"):
        graphs = splits[split]["graphs"]
        if smoke:
            graphs = [g for g in graphs if g["smoke"]]
        out[split] = graphs
    return out, splits["train"]["mc_seed"]


def simulate_cover(np, n, edges, per_start, rng, deadline):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    deg = np.array([len(a) for a in adj], dtype=np.int64)
    nbr = np.zeros((n, int(deg.max())), dtype=np.int64)
    for i, a in enumerate(adj):
        nbr[i, :len(a)] = a
    walks = n * per_start
    ids = np.arange(walks)
    pos = np.repeat(np.arange(n), per_start)
    vis = np.zeros((walks, n), dtype=bool)
    vis[ids, pos] = True
    cnt = np.ones(walks, dtype=np.int64)
    times = np.zeros(walks, dtype=np.float64)
    step = 0
    while ids.size:
        step += 1
        pos = nbr[pos, (rng.random(ids.size) * deg[pos]).astype(np.int64)]
        row = np.arange(ids.size)
        fresh = ~vis[row, pos]
        vis[row, pos] = True
        cnt += fresh
        done = cnt == n
        if done.any():
            times[ids[done]] = step
            keep = ~done
            ids, pos, vis, cnt = ids[keep], pos[keep], vis[keep], cnt[keep]
        if (step & 255) == 0 and time.monotonic() > deadline:
            raise TimeoutError("mc deadline")
    return times


def exact_cover_times(np, n, edges):
    """Exact E_v[cover time] for every start v (subset DP + linear solves), n <= 8."""
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)
    full = (1 << n) - 1
    value = {}
    for mask in range(full - 1, 0, -1):
        members = [v for v in range(n) if mask >> v & 1]
        index = {v: i for i, v in enumerate(members)}
        a = np.eye(len(members))
        b = np.ones(len(members))
        for v in members:
            d = len(adj[v])
            for w in adj[v]:
                if mask >> w & 1:
                    a[index[v], index[w]] -= 1.0 / d
                else:
                    nxt = mask | (1 << w)
                    b[index[v]] += (0.0 if nxt == full else value[(nxt, w)]) / d
        x = np.linalg.solve(a, b)
        for v in members:
            value[(mask, v)] = float(x[index[v]])
    return [value[(1 << v, v)] if n > 1 else 0.0 for v in range(n)]


def validate_simulator(np, deadline):
    """Scientific validity: exact DP matches closed forms, and the MC simulator matches the DP."""
    def path(n):
        return [(i, i + 1) for i in range(n - 1)]

    def cycle(n):
        return [(i, i + 1) for i in range(n - 1)] + [(0, n - 1)]

    def complete(n):
        return [(i, j) for i in range(n) for j in range(i + 1, n)]

    def star(n):
        return [(0, i) for i in range(1, n)]

    ex = exact_cover_times(np, 6, path(6))
    if abs(ex[0] - 25.0) > 1e-8 or abs(ex[5] - 25.0) > 1e-8:
        return False
    ex = exact_cover_times(np, 7, cycle(7))
    if max(abs(x - 21.0) for x in ex) > 1e-8:
        return False
    h5 = sum(1.0 / k for k in range(1, 6))
    ex = exact_cover_times(np, 6, complete(6))
    if max(abs(x - 5 * h5) for x in ex) > 1e-8:
        return False
    cases = [(6, path(6)), (7, cycle(7)), (6, complete(6)), (6, star(6)),
             (6, [(0, 1), (0, 2), (1, 2), (2, 3), (3, 4), (4, 5)])]
    for i, (n, edges) in enumerate(cases):
        exact = sum(exact_cover_times(np, n, edges)) / n
        rng = np.random.default_rng([987654, i])
        times = simulate_cover(np, n, edges, VALIDATION_WALKS_PER_START, rng, deadline)
        se = float(times.std(ddof=1) / math.sqrt(times.size))
        if abs(float(times.mean()) - exact) > 4.5 * se:
            return False
    return True


def derangement(np, k, rng):
    for _ in range(10000):
        perm = rng.permutation(k)
        if k >= 2 and all(int(perm[i]) != i for i in range(k)):
            return [int(x) for x in perm]
    raise RuntimeError("could not build a derangement")


def relabeled_copy(np, n, edges, rng):
    """Randomly relabeled, edge-shuffled copy; rejects a vacuous (identical) control."""
    original = [list(e) for e in edges]
    for _ in range(1000):
        perm = rng.permutation(n)
        if all(int(perm[i]) == i for i in range(n)):
            continue
        copy = []
        for u, v in edges:
            a, b = int(perm[u]), int(perm[v])
            copy.append([a, b] if rng.random() < 0.5 else [b, a])
        order = rng.permutation(len(copy))
        copy = [copy[int(i)] for i in order]
        if copy != original:
            return copy
    raise RuntimeError("vacuous permutation control")


class Context:
    pass


def prepare(np, smoke):
    graphs, mc_seed = load_graphs(smoke)
    ctx = Context()
    ctx.train, ctx.test = graphs["train"], graphs["test"]
    if not ctx.train or not ctx.test:
        raise RuntimeError("empty split")
    deadline = time.monotonic() + MC_BUDGET_SECONDS
    walks = SMOKE_MC_WALKS if smoke else MC_WALKS

    def record(category):
        record_text(f"baseline_failure category={category}")

    def abort(category):
        fail_required_baseline(category, lambda: None, record)

    try:
        valid = validate_simulator(np, deadline)
    except TimeoutError:
        abort("baseline_timeout")
    if not valid:
        abort("baseline_validation_failure")
    for split, lst, offset in (("train", ctx.train, 0), ("test", ctx.test, 100000)):
        for g in lst:
            n = g["n"]
            per_start = max(1, math.ceil(walks / n))
            rng = np.random.default_rng([mc_seed, offset + g["index"]])
            try:
                times = simulate_cover(np, n, [tuple(e) for e in g["edges"]], per_start, rng, deadline)
            except TimeoutError:
                abort("baseline_timeout")
            g["target"] = float(times.mean())
            g["se"] = float(times.std(ddof=1) / math.sqrt(times.size)) if times.size > 1 else 0.0
            if not (math.isfinite(g["target"]) and g["target"] > 0 and math.isfinite(g["se"])):
                abort("baseline_result_failure")
    ctx.bound = [2.0 * len(g["edges"]) * (g["n"] - 1) for g in ctx.test]
    logs = [math.log(g["target"]) for g in ctx.train]
    ctx.const = math.exp(sum(logs) / len(logs))
    ctx.families = sorted({g["family"] for g in ctx.test})
    ctx.test_targets = [g["target"] for g in ctx.test]
    ctx.mc_rel_se_median = float(np.median([g["se"] / g["target"] for g in ctx.test]))
    drng = np.random.default_rng([mc_seed, 555])
    ctx.derangement = derangement(np, len(ctx.test), drng)
    shuffled = [ctx.test_targets[j] for j in ctx.derangement]
    if shuffled == ctx.test_targets or len(set(ctx.test_targets)) < 2:
        raise RuntimeError("vacuous shuffled-target control")
    return ctx


def macro_error(ctx, predictions):
    """Family-macro mean of clipped per-graph |ln(pred/target)|; predictions aligned with ctx.test."""
    per_family = collections.defaultdict(list)
    for g, target, pred in zip(ctx.test, ctx.test_targets, predictions):
        if pred is None or not (math.isfinite(pred) and pred > 0):
            err = ERR_CLIP
        else:
            err = min(abs(math.log(pred / target)), ERR_CLIP)
        per_family[g["family"]].append(err)
    means = [sum(per_family[f]) / len(per_family[f]) for f in ctx.families]
    return sum(means) / len(means)


def graph_payload(gid, n, edges):
    return {"id": int(gid), "n": int(n), "edges": [[int(u), int(v)] for u, v in edges]}


def parse_predictions(response, ids):
    if type(response) is not dict or set(response) != {"predictions"}:
        raise CandidateProtocolError("malformed_response")
    preds = response["predictions"]
    if type(preds) is not dict or set(preds) != {str(i) for i in ids}:
        raise CandidateProtocolError("malformed_response")
    out = {}
    for key, value in preds.items():
        if type(value) not in (int, float) or not math.isfinite(value) or not (0 < value < 1e300):
            raise CandidateProtocolError("malformed_response")
        out[int(key)] = float(value)
    return out


def chunks(items, size=CHUNK):
    return [items[i:i + size] for i in range(0, len(items), size)]


def planned_rpc_counts(train_count, test_count, episodes):
    """Operation-count table: reset, fit chunks, predict chunks, permuted-control predict chunks."""
    fit = len(chunks(list(range(train_count))))
    pred = len(chunks(list(range(test_count))))
    return {"reset": episodes, "fit": episodes * fit, "predict": episodes * pred,
            "predict_permuted": episodes * pred}


def run_episode(np, ctx, episode, call, work_deadline):
    index = episode["index"]
    rng = np.random.default_rng([ID_SEED, index])
    train_order = [int(i) for i in rng.permutation(len(ctx.train))]
    ids = [int(i) for i in rng.permutation(len(ctx.train) + 2 * len(ctx.test))]
    train_ids, test_ids, perm_ids = (ids[:len(ctx.train)], ids[len(ctx.train):len(ctx.train) + len(ctx.test)],
                                     ids[len(ctx.train) + len(ctx.test):])
    fit_items = []
    for pos, gi in enumerate(train_order):
        g = ctx.train[gi]
        item = graph_payload(train_ids[pos], g["n"], g["edges"])
        item["target"] = g["target"]
        item["se"] = g["se"]
        fit_items.append(item)
    for part in chunks(fit_items):
        response = call({"op": "fit", "graphs": part})
        if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
            raise CandidateProtocolError("malformed_response")
    test_order = [int(i) for i in rng.permutation(len(ctx.test))]
    pred_items = [graph_payload(test_ids[pos], ctx.test[gi]["n"], ctx.test[gi]["edges"])
                  for pos, gi in enumerate(test_order)]
    got = {}
    for part in chunks(pred_items):
        got.update(parse_predictions(call({"op": "predict", "graphs": part}), [p["id"] for p in part]))
    original = [None] * len(ctx.test)
    for pos, gi in enumerate(test_order):
        original[gi] = got[test_ids[pos]]
    perm_order = [int(i) for i in rng.permutation(len(ctx.test))]
    perm_items = [graph_payload(perm_ids[pos], ctx.test[gi]["n"],
                                relabeled_copy(np, ctx.test[gi]["n"], ctx.test[gi]["edges"], rng))
                  for pos, gi in enumerate(perm_order)]
    got_perm = {}
    for part in chunks(perm_items):
        got_perm.update(parse_predictions(call({"op": "predict", "graphs": part}), [p["id"] for p in part]))
    permuted = [None] * len(ctx.test)
    for pos, gi in enumerate(perm_order):
        permuted[gi] = got_perm[perm_ids[pos]]
    dev = max(abs(a - b) / max(abs(a), abs(b), 1e-300) for a, b in zip(original, permuted))
    macro = macro_error(ctx, original)
    shuffled = macro_error_shuffled(ctx, original)
    return {"complete": True, "macro": macro, "shuffle": shuffled, "perm": dev}


def macro_error_shuffled(ctx, predictions):
    saved = ctx.test_targets
    try:
        ctx.test_targets = [saved[j] for j in ctx.derangement]
        return macro_error(ctx, predictions)
    finally:
        ctx.test_targets = saved


# ----------------------------------------------------------------------------------------
# Diagnostics (search plane only; final stays sealed)
# ----------------------------------------------------------------------------------------
def record_text(text):
    if PLANE == "search":
        print(text[:256], file=sys.stderr, flush=True)


_candidate_client = None
_DIAG_FLAGS = (os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
               or os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1")


def record_failure(failure):
    record_text("episode_failure component=%s category=%s operation=%s" % (
        failure["component"], failure["category"], failure["operation"]))
    if PLANE == "search" and _DIAG_FLAGS and _candidate_client is not None:
        snapshot = _candidate_client.stop()
        if snapshot and snapshot.get("stderr"):
            print(snapshot["stderr"], file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------------
def preflight_payloads():
    """Serialize the largest representative production request/response (UTF-8 JSON bytes)."""
    full = [(i, j) for i in range(30) for j in range(i + 1, 30)]
    graphs = []
    for k in range(CHUNK):
        item = graph_payload(10 ** 6 + k, 30, full)
        item["target"] = 123456.789012345678
        item["se"] = 123.456789012345678
        graphs.append(item)
    request = bounded_json_line({"op": "fit", "graphs": graphs})
    response = bounded_json_line({"predictions": {str(10 ** 6 + k): 123456.789012345678 for k in range(CHUNK)}})
    for size in (len(request), len(response)):
        if size + ENVELOPE_ALLOWANCE >= WIRE_LIMIT:
            raise ValueError("payload preflight failed")
    return len(request), len(response)


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, sort_keys=True)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    global _candidate_client

    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    sequence = list(SMOKE_RESET_SEQUENCE if smoke else RESET_SEQUENCE)
    episodes = [{"seed": int(s), "index": i} for i, s in enumerate(sequence)]
    weights = [1.0 / len(episodes)] * len(episodes)
    hard_deadline = _START + WALL_SECONDS - STARTUP_ALLOWANCE
    clock = time.monotonic

    preflight_payloads()
    require_joint_workload_budget(plane_profile={
        "episode_count": len(episodes), "method_count": 1, "wall_seconds": WALL_SECONDS,
        "startup_seconds": STARTUP_ALLOWANCE + MC_BUDGET_SECONDS, "reset_seconds": RESET_TIMEOUT,
        "cleanup_seconds": EPISODE_OVERHEAD, "finish_seconds": FINISH_RESERVE,
        "work_seconds": EPISODE_WORK_SECONDS})

    brokered = (bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET")) and args.program_path == PROXY_PATH)
    _candidate_client = BrokeredCandidate(PROXY_PATH) if brokered else NativeCandidate(args.program_path)

    import numpy as np

    baseline_failed = None
    ctx = None
    try:
        ctx = prepare(np, smoke)
    except RequiredBaselineFailure as error:
        baseline_failed = error
    if ctx is not None:
        counts = planned_rpc_counts(len(ctx.train), len(ctx.test), len(episodes))
        total_calls = sum(counts.values())
        if total_calls > MAX_RPC_CALLS or (not smoke and total_calls != MAX_RPC_CALLS):
            raise RuntimeError("RPC budget table does not match declared maximum")

    rpc_calls = 0

    def rpc(request, timeout):
        nonlocal rpc_calls
        rpc_calls += 1
        if rpc_calls > MAX_RPC_CALLS:
            raise RuntimeError("RPC budget exceeded")
        return _candidate_client.call(request, timeout)

    durations = [0.0] * len(episodes)
    episode_clock = {}

    def worst_case(episode):
        return {"complete": False, "macro": ERR_CLIP, "shuffle": ERR_CLIP, "perm": PERM_DEV_WORST}

    def evaluate(episode, call, work_deadline):
        episode_clock[episode["index"]] = clock()
        try:
            if baseline_failed is not None:
                raise RequiredBaselineFailure(baseline_failed.category)
            return run_episode(np, ctx, episode, call, work_deadline)
        finally:
            durations[episode["index"]] = clock() - episode_clock[episode["index"]]

    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE,
            reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP,
            clock=clock, rpc=rpc, evaluate=evaluate, worst_case=worst_case,
            record_failure=record_failure)
    except TimeoutError:
        outcomes, complete = [worst_case(e) for e in episodes], False
        record_text("episode_failure component=evaluator category=insufficient_time operation=schedule")
    finally:
        try:
            _candidate_client.stop()
        except Exception:
            record_text("cleanup_failure component=candidate category=cleanup operation=stop")

    def values(key):
        return [o[key] if o["complete"] else None for o in outcomes]

    macro = fixed_weight_score(values("macro"), weights, ERR_CLIP)
    shuffle = fixed_weight_score(values("shuffle"), weights, ERR_CLIP)
    perm = max(o["perm"] for o in outcomes)
    if baseline_failed is not None or ctx is None:
        bound_macro = const_macro = ERR_CLIP
        mc_se = MC_SE_WORST
    else:
        bound_macro = macro_error(ctx, ctx.bound)
        const_macro = macro_error(ctx, [ctx.const] * len(ctx.test))
        mc_se = ctx.mc_rel_se_median
    metrics = {
        "combined_score": -macro,
        "macro_log_mae": macro,
        "bound_macro_log_mae": bound_macro,
        "const_macro_log_mae": const_macro,
        "shuffle_macro_log_mae": shuffle,
        "improvement_vs_bound": bound_macro - macro,
        "perm_max_rel_dev": perm,
        "mc_rel_se_median": mc_se,
    }
    if tuple(metrics) != METRIC_NAMES and set(metrics) != set(METRIC_NAMES):
        raise RuntimeError("metric schema mismatch")
    if not all(math.isfinite(v) for v in metrics.values()):
        raise RuntimeError("nonfinite metric")
    integrity = (complete and baseline_failed is None and all(
        o["complete"] and o["perm"] <= PERM_TOL for o in outcomes))
    correct = integrity
    if PLANE == "final":
        correct = integrity and macro < bound_macro
    finished = clock()

    records = []
    for i, (episode, o) in enumerate(zip(episodes, outcomes)):
        ep_ok = o["complete"] and o["perm"] <= PERM_TOL and baseline_failed is None
        if PLANE == "final":
            ep_ok = ep_ok and o["macro"] < bound_macro
        records.append({"seed": episode["seed"], "score": -float(o["macro"]),
                        "correct": bool(ep_ok), "duration_seconds": float(max(durations[i], 0.0))})

    os.makedirs(args.results_dir, exist_ok=True)
    write_json(os.path.join(args.results_dir, "metrics.json"), metrics)
    write_json(os.path.join(args.results_dir, "correct.json"), {"correct": bool(correct)})
    write_json(os.path.join(args.results_dir, "evaluation_evidence.json"),
               {"schema_version": 1, "episodes": records})
    if qualification:
        feasible = bool(complete and baseline_failed is None and not smoke and finished <= hard_deadline)
        write_json(os.path.join(args.results_dir, "qualification.json"),
                   {"schema_version": 1, "feasible": feasible})


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001
        name = type(error).__name__
        name = name if name.isascii() and name.isidentifier() and len(name) <= 80 else "Error"
        if PLANE == "search":
            message = str(error).replace("\n", " ")[:160]
            print(f"evaluator_error type={name} message={message}"[:256], file=sys.stderr, flush=True)
        else:
            print(f"evaluator_error type={name}", file=sys.stderr, flush=True)
        sys.exit(1)
