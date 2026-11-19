#!/usr/bin/env python3
"""Self-contained final evaluator: single-run reliability diagnostic for stochastic Kernel SHAP.

The evaluator owns datasets, models, the Kernel SHAP sampler (and its coalition budget), the
rerun-based labels, all baselines and the label-permuted-pairing control.  The candidate sees
only one assessed Kernel SHAP run per explained instance through ``handle`` and returns r_hat.
"""
import argparse
import base64
import collections
import hashlib
import importlib.util
import itertools
import json
import math
import os
import resource
import selectors
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata
import warnings
from math import comb

_T0 = time.monotonic()
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# @@CONFIG_BEGIN
PLANE = 'final'
WALL_CLOCK_SECONDS = 4500
MAX_CANDIDATE_RPC_CALLS = 74  # 2 per episode (reset + diagnose) + 2 for the one permitted trailing replay
SEEDS = [9001, 9002]
DATASET_ORDER = ['acs_income', 'gmsc', 'german_B']
DATASETS = {
    'acs_income': dict(features=['AGEP', 'COW', 'SCHL', 'MAR', 'OCCP', 'POBP', 'RELP', 'WKHP', 'SEX', 'RAC1P'], cat=set(['COW', 'MAR', 'RELP', 'RAC1P', 'SEX']), d=10),
    'gmsc': dict(features=['RevolvingUtilizationOfUnsecuredLines', 'age', 'NumberOfTime30-59DaysPastDueNotWorse', 'DebtRatio', 'MonthlyIncome', 'NumberOfOpenCreditLinesAndLoans', 'NumberOfTimes90DaysLate', 'NumberRealEstateLoansOrLines', 'NumberOfTime60-89DaysPastDueNotWorse', 'NumberOfDependents'], cat=set([]), d=10),
    'german_B': dict(features=['A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'A13', 'A14', 'A15', 'A16', 'A17', 'A18', 'A19', 'A20'], cat=set(['A1', 'A3', 'A4', 'A6', 'A7', 'A9', 'A10', 'A12', 'A14', 'A15', 'A17', 'A19', 'A20']), d=20),
}
DECLARED_RESET_SEQUENCE = [9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9001, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002, 9002]
METRIC_NAMES = ['combined_score', 'skill_vs_always_reliable', 'skill_vs_constant_half', 'skill_vs_gap_heuristic', 'control_permuted_score', 'spearman_r_hat_vs_label', 'mean_label_low_budget', 'mean_label_high_budget', 'skill_vs_always_reliable_ci_low', 'skill_vs_constant_half_ci_low', 'skill_vs_gap_heuristic_ci_low', 'combined_minus_control_ci_low']
# @@CONFIG_END

PROXY_PATH = "/broker-code/candidate_proxy.py"
WIRE_LIMIT = 64 * 1024 * 1024
FAMILIES = ("logreg", "random_forest", "mlp")
BUDGET_MULTS = (4, 16)
K_TOP = 3
N_BACKGROUND = 32
EVAL_THREADS = 4
CANDIDATE_THREADS = 2

SMOKE = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
QUALIFICATION = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
REPAIR_VISIBLE = PLANE == "search" and (SMOKE or QUALIFICATION)

if SMOKE:
    N_INST, N_RERUNS, N_DERANGE, ROW_CAP, N_BOOT = 4, 2, 8, 2000, 20
    WALL_SECONDS, STARTUP_ALLOWANCE, FINISH_RESERVE = 120.0, 15.0, 8.0
    RESET_TIMEOUT, RPC_CAP, EPISODE_OVERHEAD = 15.0, 15.0, 6.0
    EVAL_WORK_ESTIMATE, CLEANUP_SECONDS = 10.0, 6.0
else:
    N_INST, N_RERUNS, N_DERANGE, ROW_CAP, N_BOOT = 20, 8, 20, None, 200
    WALL_SECONDS, STARTUP_ALLOWANCE, FINISH_RESERVE = float(WALL_CLOCK_SECONDS), 60.0, 30.0
    RESET_TIMEOUT, RPC_CAP, EPISODE_OVERHEAD = 30.0, 40.0, 8.0
    # conservative evaluator-side seconds per episode (calibrated from smoke timing); cleanup = candidate
    # terminate(2)+kill/reap(2)+bookkeeping, doubled for margin
    EVAL_WORK_ESTIMATE, CLEANUP_SECONDS = 30.0, 8.0

# ----------------------------------------------------------------------------------------
# Required-worker failure identity helpers (bounded categories only)
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
    """Explicit candidate protocol failure with a fixed category and operation name."""

    def __init__(self, category, operation):
        self.category = bounded_failure_name(category, "candidate_error")
        self.operation = bounded_failure_name(operation, "unknown")
        super().__init__("candidate protocol failure")


class FatalTransportError(RuntimeError):
    """Broker/transport failure that makes further candidate work impossible."""


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, CandidateProtocolError):
            return {"component": "candidate", "category": context.category, "operation": context.operation}
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
# Budget / scheduling helpers
# ----------------------------------------------------------------------------------------

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


def rpc_operation_counts(episodes):
    """Operation-count table: per episode 1 reset + 1 diagnose; one permitted trailing replay."""
    table = {"reset": episodes, "diagnose": episodes, "replay_reset": 1, "replay_diagnose": 1}
    return table, sum(table.values())


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
        now = clock()
        # equal fair share of the remaining plane time (unused time rolls over), never starving
        # the reset reservation of later episodes
        fair_deadline = now + (candidate_deadline - now) / (len(episodes) - index)
        episode_deadline = min(candidate_deadline - remaining * reset_slot, fair_deadline)
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
                record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ----------------------------------------------------------------------------------------
# Bounded worker stderr capture (candidate subprocess diagnostics)
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
# Candidate transport
# ----------------------------------------------------------------------------------------

_RUNNER = r'''
import importlib.util, json, os, sys

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
    print("worker_exception type=%s\n%s" % (name, message), file=sys.stderr, flush=True)

proto = os.fdopen(os.dup(1), "w", buffering=1)
os.dup2(2, 1)
sys.stdout = sys.stderr
path = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
try:
    spec = importlib.util.spec_from_file_location("candidate_program", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
except BaseException as error:
    report_worker_exception(error)
    sys.exit(3)
for line in sys.stdin:
    try:
        response = mod.handle(json.loads(line))
        proto.write(json.dumps(response, allow_nan=False, separators=(",", ":")) + "\n")
    except BaseException as error:
        report_worker_exception(error)
        proto.write(json.dumps({"__candidate_error__": True}) + "\n")
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
    environment.update(
        HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke runs)."""

    def __init__(self, program_path, clock):
        self.program_path = program_path
        self.clock = clock
        self.proc = None
        self.capture = None
        self.stderr_snapshot = None
        self.workdir = tempfile.mkdtemp(prefix="cand_")
        self.cpu_limit = cpu_limit_seconds(WALL_SECONDS, CANDIDATE_THREADS)

    def _limits(self):
        resource.setrlimit(resource.RLIMIT_CPU, (self.cpu_limit, self.cpu_limit))
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
        resource.setrlimit(resource.RLIMIT_AS, (12 << 30, 12 << 30))

    def stop(self):
        proc, self.proc = self.proc, None
        if proc is None:
            return
        try:
            for sig, wait in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 2.0)):
                if proc.poll() is not None:
                    break
                try:
                    os.killpg(proc.pid, sig)
                except ProcessLookupError:
                    break
                try:
                    proc.wait(timeout=wait)
                except subprocess.TimeoutExpired:
                    pass
            for stream in (proc.stdin, proc.stdout):
                try:
                    stream.close()
                except OSError:
                    pass
        finally:
            if self.capture is not None:
                try:
                    self.stderr_snapshot = self.capture.close()
                except RuntimeError:
                    self.stderr_snapshot = None
                self.capture = None

    def start(self):
        self.stop()
        python, env = candidate_subprocess_settings(os.environ)
        env["OMP_NUM_THREADS"] = env["OPENBLAS_NUM_THREADS"] = env["MKL_NUM_THREADS"] = str(CANDIDATE_THREADS)
        self.proc = subprocess.Popen(
            [python, "-c", _RUNNER, self.program_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, env=env, cwd=self.workdir, shell=False, start_new_session=True,
            close_fds=True, preexec_fn=self._limits)
        self.capture = BoundedWorkerStderr(self.proc.stderr)
        os.set_blocking(self.proc.stdout.fileno(), False)
        os.set_blocking(self.proc.stdin.fileno(), False)

    def call(self, request, timeout):
        op = request.get("op", "unknown")
        if op == "reset":
            self.start()
        if self.proc is None:
            raise CandidateProtocolError("candidate_not_running", op)
        deadline = self.clock() + timeout
        data = bounded_json_line(request)
        try:
            self._send(data, deadline)
            line = self._recv(deadline)
        except TimeoutError:
            self.stop()
            raise
        except (BrokenPipeError, OSError):
            self.stop()
            raise CandidateProtocolError("candidate_crash", op) from None
        if line is None:
            self.stop()
            raise CandidateProtocolError("candidate_crash", op)
        try:
            response = json.loads(line)
        except ValueError:
            self.stop()
            raise CandidateProtocolError("malformed_response", op) from None
        if type(response) is dict and response.get("__candidate_error__") is True:
            raise CandidateProtocolError("candidate_exception", op)
        return response

    def _send(self, data, deadline):
        fd = self.proc.stdin.fileno()
        view = memoryview(data)
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_WRITE)
            while view:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError("candidate write timeout")
                if not selector.select(timeout=min(remaining, 0.5)):
                    continue
                try:
                    written = os.write(fd, view[:65536])
                except BlockingIOError:
                    continue
                view = view[written:]

    def _recv(self, deadline):
        fd = self.proc.stdout.fileno()
        buf = bytearray()
        with selectors.DefaultSelector() as selector:
            selector.register(fd, selectors.EVENT_READ)
            while True:
                remaining = deadline - self.clock()
                if remaining <= 0:
                    raise TimeoutError("candidate response timeout")
                if not selector.select(timeout=min(remaining, 0.5)):
                    if self.proc.poll() is not None and not buf:
                        return None
                    continue
                try:
                    chunk = os.read(fd, 1 << 20)
                except BlockingIOError:
                    continue
                if not chunk:
                    return None
                buf.extend(chunk)
                if len(buf) >= WIRE_LIMIT:
                    raise CandidateProtocolError("response_too_large", "unknown")
                if b"\n" in chunk:
                    return bytes(buf).split(b"\n", 1)[0]

    def close(self):
        self.stop()
        shutil.rmtree(self.workdir, ignore_errors=True)


class BrokeredCandidate:
    """Trusted harness proxy loaded in-process; only after BOTH broker signals are verified."""

    def __init__(self, clock):
        spec = importlib.util.spec_from_file_location("candidate_proxy", PROXY_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.clock = clock
        self.stuck = None
        self.stderr_snapshot = None

    def call(self, request, timeout):
        op = request.get("op", "unknown")
        deadline = self.clock() + timeout
        if self.stuck is not None and self.stuck.is_alive():
            self.stuck.join(timeout=max(0.0, deadline - self.clock()))
            if self.stuck.is_alive():
                raise TimeoutError("previous candidate call still running")
        self.stuck = None
        bounded_json_line(request)
        box = {}

        def work():
            try:
                box["response"] = self.handle(request)
            except BaseException as error:  # noqa: BLE001 - reported with a fixed category only
                box["error"] = error

        thread = threading.Thread(target=work, name="broker-call", daemon=True)
        thread.start()
        thread.join(timeout=max(0.0, deadline - self.clock()))
        if thread.is_alive():
            self.stuck = thread
            raise TimeoutError("candidate response timeout")
        if "error" in box:
            if isinstance(box["error"], (BrokenPipeError, ConnectionError, EOFError)):
                raise FatalTransportError("broker transport failure") from None
            raise CandidateProtocolError("candidate_exception", op) from None
        response = box["response"]
        try:
            bounded_json_line(response)
        except (TypeError, ValueError):
            raise CandidateProtocolError("malformed_response", op) from None
        return response

    def close(self):
        pass


# ----------------------------------------------------------------------------------------
# Data, models and Kernel SHAP (evaluator-owned)
# ----------------------------------------------------------------------------------------

def rng_for(*parts):
    digest = hashlib.sha256(repr(parts).encode("utf-8")).digest()
    return np.random.default_rng(np.random.SeedSequence(int.from_bytes(digest[:16], "little")))


def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", PLANE)


def record_hash(fields):
    return hashlib.sha256("\x1f".join(fields).encode("utf-8")).hexdigest()


def hashset_digest(hashes):
    return hashlib.sha256("\n".join(sorted(hashes)).encode()).hexdigest()


class DataStore:
    def __init__(self):
        self.root = resource_root()
        with open(os.path.join(self.root, "manifest.json"), encoding="utf-8") as handle:
            self.manifest = json.load(handle)
        self.cache = {}
        self.all_hashes = {}

    def dataset(self, name):
        if name in self.cache:
            return self.cache[name]
        spec = DATASETS[name]
        entry = self.manifest["datasets"][name]
        df = pd.read_csv(os.path.join(self.root, entry["file"]), dtype=str, keep_default_na=False)
        hashes = [record_hash(list(row)) for row in df.itertuples(index=False, name=None)]
        if (len(df) != entry["n_rows"] or len(set(hashes)) != len(hashes)
                or hashset_digest(hashes) != entry["hashset_sha256"]):
            raise RuntimeError("dataset integrity check failed")
        self.all_hashes[name] = hashes
        label = df.pop("label").astype(int).to_numpy()
        if ROW_CAP is not None:
            df, label = df.iloc[:ROW_CAP].reset_index(drop=True), label[:ROW_CAP]
        feats = list(df.columns)
        if feats != spec["features"]:
            raise RuntimeError("dataset schema mismatch")
        self.cache[name] = (df, label)
        return self.cache[name]

    def check_final_disjointness(self):
        """Final plane: zero normalized-record overlap with the search records (hash list in manifest)."""
        for name in DATASETS:
            self.dataset(name)
        mine = {h for hashes in self.all_hashes.values() for h in hashes}
        search = set(self.manifest["search_record_hashes"])
        if hashset_digest(search) != self.manifest["search_record_hashes_sha256"] or mine & search:
            raise RuntimeError("search/final normalized content overlap")


class Prep:
    """Train-only preprocessing: median imputation + standardisation, one-hot groups per feature."""

    def __init__(self, df, spec, train_idx):
        self.spec = spec
        train = df.iloc[train_idx]
        self.numeric = {}
        self.levels = {}
        for col in spec["features"]:
            if col in spec["cat"]:
                self.levels[col] = sorted(set(train[col]))
            else:
                values = pd.to_numeric(train[col], errors="coerce").to_numpy(dtype=float)
                med = float(np.nanmedian(values))
                filled = np.where(np.isnan(values), med, values)
                sd = float(filled.std())
                self.numeric[col] = (med, float(filled.mean()), sd if sd > 0 else 1.0)
        self.group_of_col = []
        for j, col in enumerate(spec["features"]):
            width = len(self.levels[col]) if col in spec["cat"] else 1
            self.group_of_col.extend([j] * width)
        self.group_of_col = np.array(self.group_of_col, dtype=np.int64)

    def transform(self, df):
        blocks = []
        for col in self.spec["features"]:
            if col in self.spec["cat"]:
                blocks.append(np.stack([(df[col].to_numpy() == lv).astype(float) for lv in self.levels[col]], axis=1))
            else:
                med, mean, sd = self.numeric[col]
                values = pd.to_numeric(df[col], errors="coerce").to_numpy(dtype=float)
                values = np.where(np.isnan(values), med, values)
                blocks.append(((values - mean) / sd)[:, None])
        return np.hstack(blocks)


def make_model(family, state):
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.neural_network import MLPClassifier
    if family == "logreg":
        return LogisticRegression(max_iter=1000)
    if family == "random_forest":
        return RandomForestClassifier(n_estimators=100, n_jobs=EVAL_THREADS, random_state=state)
    if family == "mlp":
        return MLPClassifier(hidden_layer_sizes=(64,), max_iter=200, random_state=state)
    raise RuntimeError("unknown family")


class EpisodeFactory:
    """Per-(dataset, seed) split/preprocessing and per-(dataset, family, seed) model caches."""

    def __init__(self, store):
        self.store = store
        self.splits = {}
        self.models = {}

    def split(self, name, seed):
        key = (name, seed)
        if key not in self.splits:
            df, label = self.store.dataset(name)
            n = len(df)
            perm = rng_for("split", name, seed).permutation(n)
            ntr = int(round(0.7 * n))
            tr, te = np.sort(perm[:ntr]), np.sort(perm[ntr:])
            prep = Prep(df, DATASETS[name], tr)
            Xtr, Xte = prep.transform(df.iloc[tr]), prep.transform(df.iloc[te])
            rng = rng_for("background", name, seed)
            bg = Xtr[rng.choice(len(Xtr), size=N_BACKGROUND, replace=False)]
            inst = rng_for("instances", name, seed).choice(len(Xte), size=N_INST, replace=False)
            self.splits[key] = dict(prep=prep, Xtr=Xtr, ytr=label[tr], Xte=Xte, yte=label[te], bg=bg, inst=inst)
        return self.splits[key]

    def model(self, name, family, seed):
        key = (name, family, seed)
        if key not in self.models:
            sp = self.split(name, seed)
            state = int(rng_for("model", name, family, seed).integers(2 ** 31 - 1))
            model = make_model(family, state)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(sp["Xtr"], sp["ytr"])
            self.models[key] = model
        return self.models[key]


def kernel_coalitions(d, budget, rng):
    """Kernel SHAP coalition set: size-class enumeration while affordable, kernel-weighted paired sampling
    for the rest.  Returns (masks bool [B, d], weights float64 [B] summing to 1).  Complement pairs adjacent."""
    n_sizes = d // 2
    n_paired = (d - 1) // 2
    sizes = np.arange(1, n_sizes + 1)
    w = (d - 1) / (sizes * (d - sizes))
    w[:n_paired] *= 2.0
    w = w / w.sum()
    masks, weights = [], []
    left, first, enum_mass = budget, 0, 0.0
    rem = w.copy()
    for idx in range(n_sizes):
        s = idx + 1
        paired = idx < n_paired
        cnt = comb(d, s) * (2 if paired else 1)
        if cnt <= left and left * rem[idx] / cnt >= 1 - 1e-8:
            for subset in itertools.combinations(range(d), s):
                m = np.zeros(d, dtype=bool)
                m[list(subset)] = True
                masks.append(m)
                weights.append(w[idx] / cnt)
                if paired:
                    masks.append(~m)
                    weights.append(w[idx] / cnt)
            left -= cnt
            enum_mass += w[idx]
            first = idx + 1
            rem = np.zeros_like(w)
            if first < n_sizes:
                rem[first:] = w[first:] / w[first:].sum()
        else:
            break
    if left > 0 and first < n_sizes:
        p = w[first:] / w[first:].sum()
        classes = rng.choice(len(p), size=left, p=p) + first
        sampled = []
        for c in classes:
            if len(sampled) >= left:
                break
            m = np.zeros(d, dtype=bool)
            m[rng.permutation(d)[:c + 1]] = True
            sampled.append(m)
            if c < n_paired and len(sampled) < left:
                sampled.append(~m)
        masks.extend(sampled)
        weights.extend([(1.0 - enum_mass) / len(sampled)] * len(sampled))
    masks = np.array(masks, dtype=bool)
    weights = np.array(weights, dtype=np.float64)
    if len(masks) != budget:
        raise RuntimeError("coalition budget not met")
    return masks, weights


def solve_phi(Z, w, v, v0, v1):
    total = v1 - v0
    A = Z[:, :-1] - Z[:, -1:]
    t = (v - v0) - Z[:, -1] * total
    sw = np.sqrt(w)
    sol = np.linalg.lstsq(A * sw[:, None], t * sw, rcond=None)[0]
    return np.append(sol, total - sol.sum())


def top_k(a, k=K_TOP):
    return np.argsort(-np.abs(a), kind="stable")[:k]


def jaccard(a, b):
    c = len(set(a.tolist()) & set(b.tolist()))
    return c / (2 * K_TOP - c)


def coalition_values(model, x, bg, group_of_col, masks):
    out = np.empty(len(masks))
    colmask = masks[:, group_of_col]
    step = max(1, 40000 // len(bg))
    for start in range(0, len(masks), step):
        cm = colmask[start:start + step]
        hybrid = np.where(cm[:, None, :], x[None, None, :], bg[None, :, :])
        proba = model.predict_proba(hybrid.reshape(-1, hybrid.shape[-1]))[:, 1]
        out[start:start + step] = proba.reshape(len(cm), len(bg)).mean(axis=1)
    return out


def split_half_gap_reliability(Z, w, v, v0, v1):
    """Evaluator-owned reference diagnostic from the assessed run only (map fixed before scoring):
    z = (|phi|_(3) - |phi|_(4)) / sqrt(se_(3)^2 + se_(4)^2), se_j = |phi_A,j - phi_B,j| / 2 over the two
    complement-pair block halves; r = 0.5 + 0.5 * tanh(z)."""
    B = len(Z)
    half = (np.arange(B) // 2) % 2 == 0
    phi = solve_phi(Z, w, v, v0, v1)
    pa = solve_phi(Z[half], w[half], v[half], v0, v1)
    pb = solve_phi(Z[~half], w[~half], v[~half], v0, v1)
    se = np.abs(pa - pb) / 2.0
    order = np.argsort(-np.abs(phi), kind="stable")
    j3, j4 = order[K_TOP - 1], order[K_TOP]
    gap = abs(phi[j3]) - abs(phi[j4])
    z = gap / (math.sqrt(se[j3] ** 2 + se[j4] ** 2) + 1e-12)
    return float(0.5 + 0.5 * math.tanh(z))


def make_derangements(n, count):
    rng = np.random.default_rng(7919)
    out = []
    while len(out) < count:
        perm = rng.permutation(n)
        if not np.any(perm == np.arange(n)):
            out.append(perm)
    return out


def check_derangements(perms, n):
    for perm in perms:
        if (sorted(perm.tolist()) != list(range(n)) or np.any(perm == np.arange(n))
                or np.array_equal(perm, np.arange(n))):
            raise RuntimeError("vacuous permutation control")


def encode_array(arr, dtype, **extra):
    arr = np.ascontiguousarray(arr, dtype=dtype)
    out = {"dtype": np.dtype(dtype).name, "encoding": "base64"}
    out.update(extra)
    out["shape"] = list(arr.shape)
    out["data"] = base64.b64encode(arr.tobytes()).decode("ascii")
    return out


def build_instance(masks, weights, values, v0, v1):
    d = masks.shape[1]
    packed = np.packbits(masks.astype(np.uint8), axis=1, bitorder="little")
    return {
        "masks": encode_array(packed, "uint8", bitorder="little", unpacked_shape=[int(masks.shape[0]), int(d)]),
        "weights": encode_array(weights, "<f8", byteorder="little"),
        "values": encode_array(values, "<f8", byteorder="little"),
        "anchors": {"empty": float(v0), "full": float(v1)},
    }


def episode_ground_truth(ep, factory, deadline, clock):
    """Trusted evaluator work: model, assessed run + reruns per instance, label, gap heuristic."""
    sp = factory.split(ep["dataset"], ep["seed"])
    if clock() > deadline:
        raise TimeoutError()
    model = factory.model(ep["dataset"], ep["family"], ep["seed"])
    d = DATASETS[ep["dataset"]]["d"]
    budget = ep["mult"] * d
    gcol = sp["prep"].group_of_col
    bg = sp["bg"]
    v0 = float(model.predict_proba(bg)[:, 1].mean())
    instances, labels, gaps = [], [], []
    for i, row in enumerate(sp["inst"]):
        if clock() > deadline:
            raise TimeoutError()
        x = sp["Xte"][row]
        v1 = float(model.predict_proba(x[None, :])[0, 1])
        runs = []
        for r in range(N_RERUNS + 1):
            rng = rng_for("run", ep["seed"], ep["dataset"], ep["family"], ep["mult"], i, r)
            runs.append(kernel_coalitions(d, budget, rng))
        allm = np.concatenate([m for m, _ in runs])
        packed = np.packbits(allm, axis=1, bitorder="little")
        void = np.ascontiguousarray(packed).view(np.dtype((np.void, packed.shape[1]))).ravel()
        _, first_idx, inverse = np.unique(void, return_index=True, return_inverse=True)
        uvals = coalition_values(model, x, bg, gcol, allm[first_idx])
        vals = uvals[inverse.ravel()].reshape(N_RERUNS + 1, budget)
        if not np.all(np.isfinite(vals)):
            raise RuntimeError("non-finite coalition values")
        phis = []
        for r, (m, w) in enumerate(runs):
            phi = solve_phi(m.astype(float), w, vals[r], v0, v1)
            if not np.all(np.isfinite(phi)):
                raise RuntimeError("non-finite attribution")
            phis.append(phi)
        ref = top_k(phis[0])
        labels.append(float(np.mean([jaccard(ref, top_k(p)) for p in phis[1:]])))
        m0, w0 = runs[0]
        gaps.append(split_half_gap_reliability(m0.astype(float), w0, vals[0], v0, v1))
        instances.append(build_instance(m0, w0, vals[0], v0, v1))
    return {"instances": instances, "labels": np.array(labels), "gap": np.array(gaps), "d": d, "budget": budget}


def rank_corr(a, b):
    from scipy.stats import rankdata
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        return 0.0
    c = float(np.corrcoef(rankdata(a), rankdata(b))[0, 1])
    return c if math.isfinite(c) else 0.0


def worst_case_record(n=None):
    n = N_INST if n is None else n
    return {"cand_se": np.ones(n), "always_se": np.zeros(n), "half_se": np.zeros(n), "gap_se": np.zeros(n),
            "ctrl_se": np.zeros(n), "spearman": -1.0, "label": np.zeros(n), "ok": False}


def episode_record(truth, r, perms):
    y = truth["labels"]
    record = {
        "cand_se": (r - y) ** 2,
        "always_se": (1.0 - y) ** 2,
        "half_se": (0.5 - y) ** 2,
        "gap_se": (truth["gap"] - y) ** 2,
        "ctrl_se": np.mean([(r[p] - y) ** 2 for p in perms], axis=0),
        "spearman": rank_corr(r, y),
        "label": y.copy(),
        "ok": True,
    }
    for key, value in record.items():
        if key != "ok" and not np.all(np.isfinite(value)):
            raise RuntimeError("non-finite episode record")
    return record


def validate_diagnose_response(response, n):
    if type(response) is not dict or set(response) != {"r_hat"} or type(response["r_hat"]) is not list \
            or len(response["r_hat"]) != n:
        raise CandidateProtocolError("malformed_response", "diagnose")
    out = []
    for value in response["r_hat"]:
        if type(value) not in (int, float) or not math.isfinite(value) or value < 0.0 or value > 1.0:
            raise CandidateProtocolError("malformed_response", "diagnose")
        out.append(float(value))
    return np.array(out)


# ----------------------------------------------------------------------------------------
# Aggregation (declared hierarchy: instance -> episode -> cell(seeds) -> dataset(cells) -> plane)
# ----------------------------------------------------------------------------------------

def episode_scalars(record):
    return {
        "cand": float(np.mean(record["cand_se"])), "always": float(np.mean(record["always_se"])),
        "half": float(np.mean(record["half_se"])), "gap": float(np.mean(record["gap_se"])),
        "ctrl": float(np.mean(record["ctrl_se"])), "spearman": float(record["spearman"]),
        "label": float(np.mean(record["label"])),
    }


def aggregate(episodes, records, field, mult=None, seed=None):
    """Equal-weight mean over instances, then seeds within a cell, cells within a dataset, datasets."""
    per_dataset = []
    for name in DATASET_ORDER:
        cells = collections.OrderedDict()
        for ep, rec in zip(episodes, records):
            if ep["dataset"] != name or (mult is not None and ep["mult"] != mult):
                continue
            if seed is not None and ep["seed"] != seed:
                continue
            cells.setdefault((ep["family"], ep["mult"]), []).append(episode_scalars(rec)[field])
        if cells:
            per_dataset.append(float(np.mean([np.mean(v) for v in cells.values()])))
    return float(np.mean(per_dataset))


def plane_metrics(episodes, records, **filters):
    a = lambda f, **kw: aggregate(episodes, records, f, **filters, **kw)  # noqa: E731
    cand = a("cand")
    return {
        "combined_score": 1.0 - cand,
        "skill_vs_always_reliable": a("always") - cand,
        "skill_vs_constant_half": a("half") - cand,
        "skill_vs_gap_heuristic": a("gap") - cand,
        "control_permuted_score": 1.0 - a("ctrl"),
        "spearman_r_hat_vs_label": a("spearman"),
        "mean_label_low_budget": aggregate(episodes, records, "label", mult=BUDGET_MULTS[0], **filters),
        "mean_label_high_budget": aggregate(episodes, records, "label", mult=BUDGET_MULTS[1], **filters),
    }


def bootstrap_ci_low(episodes, records, n_boot):
    """Paired bootstrap (instances within episodes, seeds within cells, cells within datasets).
    Returns 2.5th percentiles of the three skills and of (combined_score - control_permuted_score)."""
    rng = np.random.default_rng(424242)
    stack = [np.stack([r["cand_se"], r["always_se"], r["half_se"], r["gap_se"], r["ctrl_se"]]) for r in records]
    layout = collections.OrderedDict()
    for idx, ep in enumerate(episodes):
        layout.setdefault(ep["dataset"], collections.OrderedDict()).setdefault((ep["family"], ep["mult"]), []).append(idx)
    draws = []
    for _ in range(n_boot):
        per_dataset = []
        for cells in layout.values():
            keys = list(cells)
            vals = []
            for ci in rng.integers(len(keys), size=len(keys)):
                eps = cells[keys[ci]]
                seed_means = []
                for si in rng.integers(len(eps), size=len(eps)):
                    arr = stack[eps[si]]
                    cols = rng.integers(arr.shape[1], size=arr.shape[1])
                    seed_means.append(arr[:, cols].mean(axis=1))
                vals.append(np.mean(seed_means, axis=0))
            per_dataset.append(np.mean(vals, axis=0))
        m = np.mean(per_dataset, axis=0)
        draws.append([m[1] - m[0], m[2] - m[0], m[3] - m[0], m[4] - m[0]])
    lows = np.percentile(np.array(draws), 2.5, axis=0)
    return [float(x) for x in lows]


# ----------------------------------------------------------------------------------------
# Evaluator main
# ----------------------------------------------------------------------------------------

def build_episodes():
    cells = [(ds, fam, mult) for ds in DATASET_ORDER for fam in FAMILIES for mult in BUDGET_MULTS]
    episodes = [{"seed": s, "dataset": ds, "family": fam, "mult": mult} for s in SEEDS for ds, fam, mult in cells]
    for i, e in enumerate(episodes):
        e["i"] = i
    if [e["seed"] for e in episodes] != list(DECLARED_RESET_SEQUENCE):
        raise RuntimeError("episode plan does not match the declared reset sequence")
    if SMOKE:
        episodes = [episodes[0], episodes[len(cells) - 1]]
    return episodes


def emit_search_line(text):
    if PLANE == "search":
        print(text[:256], file=sys.stderr, flush=True)


def metric_names():
    return list(METRIC_NAMES)


def worst_case_metrics():
    base = {"combined_score": 0.0, "skill_vs_always_reliable": -1.0, "skill_vs_constant_half": -1.0,
            "skill_vs_gap_heuristic": -1.0, "control_permuted_score": 1.0, "spearman_r_hat_vs_label": -1.0,
            "mean_label_low_budget": 0.0, "mean_label_high_budget": 0.0}
    if PLANE == "final":
        base.update({"skill_vs_always_reliable_ci_low": -1.0, "skill_vs_constant_half_ci_low": -1.0,
                     "skill_vs_gap_heuristic_ci_low": -1.0, "combined_minus_control_ci_low": -1.0})
    return base


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, sort_keys=True)


def write_results(results_dir, metrics, correct, feasible, evidence):
    names = metric_names()
    if set(metrics) != set(names) or not all(math.isfinite(float(v)) for v in metrics.values()):
        raise RuntimeError("metric schema violation")
    os.makedirs(results_dir, exist_ok=True)
    write_json(os.path.join(results_dir, "metrics.json"), {k: float(metrics[k]) for k in names})
    write_json(os.path.join(results_dir, "correct.json"), {"correct": bool(correct)})
    if evidence:
        write_json(os.path.join(results_dir, "evaluation_evidence.json"), {"schema_version": 1, "episodes": evidence})
    if QUALIFICATION:
        write_json(os.path.join(results_dir, "qualification.json"), {"schema_version": 1, "feasible": bool(feasible)})


def preflight(episodes, rpc_cap_total):
    """Largest production request/response must serialize strictly below the wire limit; budget checks."""
    d_max = max(spec["d"] for spec in DATASETS.values())
    b_max = max(BUDGET_MULTS) * d_max
    rng = np.random.default_rng(0)
    masks = rng.random((b_max, d_max)) < 0.5
    inst = build_instance(masks, rng.random(b_max), rng.random(b_max), 0.3, 0.7)
    request = {"op": "diagnose", "workload": {"n_features": d_max, "n_masks": b_max, "family": "random_forest",
                                               "k": K_TOP, "n_instances": 20}, "instances": [inst] * 20}
    request_bytes = len(bounded_json_line(request))
    response_bytes = len(bounded_json_line({"r_hat": [0.123456789012345678] * 20}))
    _, total = rpc_operation_counts(len(episodes))
    if total > rpc_cap_total and not SMOKE:
        raise RuntimeError("operation-count table exceeds the RPC budget")
    require_joint_workload_budget(plane_profile=dict(
        wall_seconds=WALL_SECONDS, startup_seconds=STARTUP_ALLOWANCE, reset_seconds=RESET_TIMEOUT,
        cleanup_seconds=CLEANUP_SECONDS, finish_seconds=FINISH_RESERVE, episode_count=len(episodes),
        method_count=1, work_seconds=EVAL_WORK_ESTIMATE + RPC_CAP))
    return request_bytes, response_bytes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    clock = time.monotonic
    hard_deadline = _T0 + WALL_SECONDS - STARTUP_ALLOWANCE
    episodes = build_episodes()
    rpc_cap_total = MAX_CANDIDATE_RPC_CALLS
    if SMOKE:
        rpc_cap_total = 2 * len(episodes) + 2
    preflight(episodes, rpc_cap_total)

    brokered_path = os.path.abspath(args.program_path) == PROXY_PATH
    brokered_env = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    if brokered_path and not brokered_env:
        raise RuntimeError("broker proxy path without broker socket")
    if brokered_path:
        transport = BrokeredCandidate(clock)
    else:
        transport = NativeCandidate(os.path.abspath(args.program_path), clock)

    store = DataStore()
    for name in DATASET_ORDER:
        store.dataset(name)
    if PLANE == "final":
        store.check_final_disjointness()
    factory = EpisodeFactory(store)
    perms = make_derangements(N_INST, N_DERANGE)
    control_ok = True
    try:
        check_derangements(perms, N_INST)
    except RuntimeError:
        control_ok = False

    state = {"calls": 0, "resets": [], "fatal": False, "baseline_failed": False, "durations": {}}
    failures = []

    def rpc(request, timeout):
        if state["calls"] + 1 > rpc_cap_total:
            raise FatalTransportError("rpc call cap reached")
        state["calls"] += 1
        if request.get("op") == "reset":
            state["resets"].append(request["seed"])
        try:
            return transport.call(request, timeout)
        except FatalTransportError:
            state["fatal"] = True
            raise

    def record_failure(failure):
        failures.append(failure)
        line = "episode_failure index=%d component=%s category=%s operation=%s" % (
            len(failures), failure["component"], failure["category"], failure["operation"])
        emit_search_line(line)
        if PLANE == "final":
            print("episode_failure component=%s category=%s operation=%s" % (
                failure["component"], failure["category"], failure["operation"]), file=sys.stderr, flush=True)

    def evaluate(episode, call, work_deadline):
        started = clock()
        try:
            try:
                truth = episode_ground_truth(episode, factory, work_deadline, clock)
            except TimeoutError:
                fail_required_baseline("baseline_timeout", lambda: None, lambda category: None)
            except (RuntimeError, np.linalg.LinAlgError, FloatingPointError):
                fail_required_baseline("baseline_result_failure", lambda: None, lambda category: None)
            request = {"op": "diagnose",
                       "workload": {"n_features": truth["d"], "n_masks": truth["budget"],
                                    "family": episode["family"], "k": K_TOP, "n_instances": N_INST},
                       "instances": truth["instances"]}
            response = call(request)
            r = validate_diagnose_response(response, N_INST)
            try:
                return episode_record(truth, r, perms)
            except RuntimeError:
                fail_required_baseline("baseline_result_failure", lambda: None, lambda category: None)
        finally:
            state["durations"][episode["i"]] = clock() - started

    outcomes = [worst_case_record() for _ in episodes]
    complete = False
    transport_failed = False
    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT,
            episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP, clock=clock, rpc=rpc, evaluate=evaluate,
            worst_case=lambda episode: worst_case_record(), record_failure=record_failure)
    except FatalTransportError:
        transport_failed = True
        print("fatal_transport_failure", file=sys.stderr, flush=True)
    finally:
        snapshot = getattr(transport, "stderr_snapshot", None)
        try:
            transport.close()
        except Exception:
            pass
        snapshot = getattr(transport, "stderr_snapshot", None) or snapshot
        if REPAIR_VISIBLE and snapshot and snapshot.get("stderr") and (failures or transport_failed):
            sys.stderr.write(snapshot["stderr"])
            sys.stderr.flush()

    # keep the records of episodes that actually completed even after a fatal failure; others stay worst-case
    transcript_ok = state["resets"] == [e["seed"] for e in episodes]
    well_formed = all(rec["ok"] for rec in outcomes)
    wall_ok = clock() <= _T0 + WALL_SECONDS - STARTUP_ALLOWANCE + 1e-9
    correct = bool(complete and not transport_failed and transcript_ok and well_formed and control_ok
                   and state["calls"] <= rpc_cap_total and wall_ok)

    if transport_failed or not control_ok:
        metrics = worst_case_metrics()
    else:
        metrics = plane_metrics(episodes, outcomes)
        if PLANE == "final":
            try:
                lows = bootstrap_ci_low(episodes, outcomes, N_BOOT)
            except (ValueError, FloatingPointError):
                lows = [-1.0] * 4
            metrics.update({"skill_vs_always_reliable_ci_low": lows[0], "skill_vs_constant_half_ci_low": lows[1],
                            "skill_vs_gap_heuristic_ci_low": lows[2], "combined_minus_control_ci_low": lows[3]})
    metrics = {k: (float(v) if math.isfinite(v) else worst_case_metrics()[k]) for k, v in metrics.items()}

    evidence = []
    if not transport_failed and control_ok:
        durations = [state["durations"].get(e["i"], 0.0) for e in episodes]
        for seed in SEEDS:
            idx = [i for i, e in enumerate(episodes) if e["seed"] == seed]
            if not idx:
                continue
            sub_eps = [episodes[i] for i in idx]
            sub_recs = [outcomes[i] for i in idx]
            # each seed's own score uses the same hierarchy restricted to that seed's episodes
            score = 1.0 - aggregate(sub_eps, sub_recs, "cand")
            evidence.append({"seed": int(seed), "score": float(score),
                             "correct": bool(correct and all(outcomes[i]["ok"] for i in idx)),
                             "duration_seconds": float(sum(durations[i] for i in idx))})
    feasible = bool(correct and not SMOKE and complete)
    write_results(args.results_dir, metrics, correct, feasible, evidence)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001
        name = type(error).__name__
        name = name if name.isascii() and name.isidentifier() and len(name) <= 80 else "EvaluatorError"
        try:
            message = str(error)[:200].replace("\n", " ")
        except Exception:
            message = "unavailable"
        print("evaluator_error type=%s message=%s" % (name, message if PLANE == "search" else "sealed"),
              file=sys.stderr, flush=True)
        sys.exit(1)
