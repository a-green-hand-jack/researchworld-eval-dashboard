#!/usr/bin/env python3
"""Sealed final evaluator: cold-start benchmark-subset selection + score imputation.

Self-contained: reads only resources/final (MTEB-style final partition, Open LLM Leaderboard, HELM Lite).
Candidate interface: python_rpc_v1:handle. Writes metrics.json (declared final metrics), correct.json,
optional evaluation_evidence.json and, only when AGENTIC_TASK_QUALIFICATION=1, qualification.json.
Final diagnostics are sealed: failures print only a fixed category on stderr.
"""
PLANE = "final"
WALL_CLOCK = 5400.0
BASELINE_ALLOWANCE_SECONDS = 480.0
MAX_CANDIDATE_RPC_CALLS = 406
FINAL_SEEDS = (201, 202, 203)
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
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
import time

import numpy as np

T0 = time.monotonic()
WIRE_LIMIT = 64 * 1024 * 1024
PROXY_PATH = "/broker-code/candidate_proxy.py"
STARTUP_ALLOWANCE = 150.0      # broker/container startup + imports, subtracted from the plane ceiling
FINISH_RESERVE = 20.0          # output writing
BASELINE_ALLOWANCE = None      # set per plane below
RESET_TIMEOUT = 20.0
RPC_CAP = 60.0
EPISODE_WORK_CAP = 85.0        # per-episode candidate work allowance (matched across all episodes/controls)
EPISODE_OVERHEAD = 6.0         # candidate terminate(1)+kill/reap(1) + stderr teardown(1) + dispatch/bookkeeping(3)
CHUNK_TARGET_BYTES = 2 * 1024 * 1024
ROWS_PER_CHUNK_MAX = 4096
PREDICT_BATCH = 64
SMOKE_ROWS_PER_CHUNK = 16
SMOKE_PREDICT_BATCH = 4
BASELINE_DRAWS = 5
COMPLETION_RANK = 5
COMPLETION_ITERS = 40
RIDGE_GRID = (1e-3, 1e-2, 1e-1, 1.0)   # multiples of the number of history rows
GREEDY_LAMBDA = 0.05                   # multiple of the number of history rows
# family -> (max history chunks, max predict batches): declared maxima used for the RPC budget
FAMILY_LIMITS = {"mteb": (4, 4), "oll": (4, 6), "helm": (2, 2)}
SMOKE = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
QUALIFICATION = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
DIAG_VISIBLE = PLANE == "search" and (SMOKE or QUALIFICATION)


# ----------------------------------------------------------------------------- failure identity
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
    """Explicit candidate protocol failure with a fixed category (never derived from message text)."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "protocol_error")
        super().__init__("candidate protocol failure")


class VacuousControl(RuntimeError):
    pass


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, VacuousControl):
            return {"component": "evaluator", "category": "vacuous_control",
                    "operation": bounded_failure_name(operation, "unknown")}
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
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure, work_cap=None,
):
    candidate_deadline = hard_deadline - finish_reserve
    reset_slot = reset_timeout + episode_overhead
    outcomes = [worst_case(episode) for episode in episodes]
    if clock() + len(episodes) * reset_slot > candidate_deadline:
        raise TimeoutError("insufficient time for declared reset reservations")
    complete = True
    flags = [False] * len(episodes)
    durations = [0.0] * len(episodes)
    for index, episode in enumerate(episodes):
        started = clock()
        remaining = len(episodes) - index - 1
        episode_deadline = candidate_deadline - remaining * reset_slot
        work_deadline = episode_deadline - episode_overhead
        if work_cap is not None:
            work_deadline = min(work_deadline, started + work_cap)
            episode_deadline = min(episode_deadline, work_deadline + episode_overhead)

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
            flags[index] = True
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse,
                CandidateProtocolError, VacuousControl) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            try:
                record_failure(episode, failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
        durations[index] = max(0.0, clock() - started)
    return outcomes, complete, flags, durations


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


# ----------------------------------------------------------------------------- candidate transport
RUNNER = r'''
import sys, os, json, resource, importlib.util
cpu, diag = int(sys.argv[2]), sys.argv[3] == "1"
try:
    resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    resource.setrlimit(resource.RLIMIT_AS, (8 << 30, 8 << 30))
except (ValueError, OSError):
    pass
proto = os.fdopen(os.dup(1), "w", buffering=1)
os.dup2(2, 1)
sys.stdout = sys.stderr
path = sys.argv[1]
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
spec = importlib.util.spec_from_file_location("candidate_program", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for line in sys.stdin:
    try:
        req = json.loads(line)
        resp = mod.handle(req)
        out = json.dumps({"ok": True, "response": resp}, allow_nan=False, separators=(",", ":"))
    except BaseException as exc:
        if diag:
            name = type(exc).__name__
            if not (name.isascii() and name.isidentifier() and len(name) <= 80):
                name = "WorkerException"
            try:
                msg = str(exc)
            except Exception:
                msg = "<exception message unavailable>"
            if len(msg) > 2048:
                msg = "<exception message omitted: too large>"
            print("worker_exception type=%s\n%s" % (name, msg), file=sys.stderr, flush=True)
        out = json.dumps({"ok": False}, separators=(",", ":"))
    proto.write(out + "\n")
    proto.flush()
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
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        environment[name] = "2"   # candidate BLAS threads <= 2; the evaluator itself runs single-threaded
    environment.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
                       PYTHONUNBUFFERED="1")
    return parent_environment.get("TASK_PYTHON", sys.executable), environment


class NativeTransport:
    """Smoke-mode transport: untrusted candidate in a killable, resource-limited subprocess."""

    def __init__(self, program_path, clock):
        self.program_path = os.path.abspath(program_path)
        self.clock = clock
        self.proc = None
        self.stderr_capture = None
        self.last_stderr = None
        self.buffer = b""
        self.cwd = tempfile.mkdtemp(prefix="cand_cwd_")
        self.cpu_limit = cpu_limit_seconds(RESET_TIMEOUT + EPISODE_WORK_CAP + 10.0, 2)

    def _stop(self):
        proc = self.proc
        self.proc = None
        if proc is None:
            return
        try:
            try:
                proc.stdin.close()
            except Exception:
                pass
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
            try:
                proc.stdout.close()
            except Exception:
                pass
            if self.stderr_capture is not None:
                try:
                    self.last_stderr = self.stderr_capture.close()
                except RuntimeError:
                    self.last_stderr = None
                self.stderr_capture = None

    def _start(self):
        self._stop()
        python, env = candidate_subprocess_settings(os.environ)
        self.proc = subprocess.Popen(
            [python, "-c", RUNNER, self.program_path, str(self.cpu_limit), "1" if DIAG_VISIBLE else "0"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=self.cwd, env=env, shell=False, start_new_session=True, close_fds=True)
        self.stderr_capture = BoundedWorkerStderr(self.proc.stderr)
        self.buffer = b""

    def request(self, request, timeout):
        deadline = self.clock() + timeout
        try:
            if request.get("op") == "reset" or self.proc is None:
                self._start()
            line = json.dumps(request, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
            if len(line) >= WIRE_LIMIT:
                raise ValueError("request exceeds wire limit")
            try:
                self.proc.stdin.write(line)
                self.proc.stdin.flush()
            except (BrokenPipeError, OSError):
                raise CandidateProtocolError("candidate_exited") from None
            with selectors.DefaultSelector() as selector:
                selector.register(self.proc.stdout, selectors.EVENT_READ)
                while b"\n" not in self.buffer:
                    remaining = deadline - self.clock()
                    if remaining <= 0:
                        raise TimeoutError("candidate response timeout")
                    if not selector.select(timeout=min(remaining, 0.5)):
                        continue
                    chunk = os.read(self.proc.stdout.fileno(), 1 << 20)
                    if not chunk:
                        raise CandidateProtocolError("candidate_exited")
                    self.buffer += chunk
                    if len(self.buffer) > WIRE_LIMIT + 1024:
                        raise CandidateProtocolError("response_too_large")
            raw, _, self.buffer = self.buffer.partition(b"\n")
            if len(raw) >= WIRE_LIMIT:
                raise CandidateProtocolError("response_too_large")
            try:
                message = json.loads(raw.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                raise CandidateProtocolError("malformed_response") from None
            if type(message) is not dict or message.get("ok") is not True or "response" not in message:
                raise CandidateProtocolError("candidate_exception")
            return message["response"]
        except (TimeoutError, CandidateProtocolError):
            self._stop()
            raise

    def close(self):
        self._stop()
        shutil.rmtree(self.cwd, ignore_errors=True)

    def diagnostics(self):
        snap = self.last_stderr
        if snap and snap.get("stderr"):
            return snap
        return None


class BrokeredTransport:
    """Production transport: the harness proxy runs in-process; its `handle` talks to the isolated candidate."""

    def __init__(self, clock):
        spec = importlib.util.spec_from_file_location("candidate_proxy", PROXY_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.handle = module.handle
        self.clock = clock

    def request(self, request, timeout):
        bounded_json_line(request)
        box = {}

        def work():
            try:
                box["response"] = self.handle(json.loads(json.dumps(request)))
            except BaseException as exc:  # noqa: BLE001 - classified below by fixed category only
                box["error"] = exc

        thread = threading.Thread(target=work, daemon=True)
        thread.start()
        thread.join(timeout=max(timeout, 0.001))
        if thread.is_alive():
            raise TimeoutError("candidate response timeout")
        if "error" in box:
            if isinstance(box["error"], TimeoutError):
                raise TimeoutError("candidate response timeout")
            raise CandidateProtocolError("transport_failure")
        response = box["response"]
        try:
            bounded_json_line(response)
        except (TypeError, ValueError):
            raise CandidateProtocolError("malformed_response") from None
        return response

    def close(self):
        pass

    def diagnostics(self):
        return None


# ----------------------------------------------------------------------------- data
class Dataset:
    def __init__(self, family, root, stem, smoke):
        z = np.load(os.path.join(root, stem + ".npz"))
        with open(os.path.join(root, stem + "_manifest.json"), "r", encoding="utf-8") as handle:
            man = json.load(handle)
        values, observed, role = z["values"].astype(np.float64), z["observed"].astype(bool), z["role"]
        models = man["models"]
        if len(models) != len(role) or values.shape != observed.shape or values.shape[1] != len(man["columns"]):
            raise ValueError("manifest/array mismatch")
        if [int(m["role"]) for m in models] != [int(r) for r in role]:
            raise ValueError("manifest role mismatch")
        for key in ("content_sha256", "family", "group"):
            a = {m[key] for m in models if m["role"] == 0}
            b = {m[key] for m in models if m["role"] == 1}
            if a & b:
                raise ValueError("history/held-out overlap")
        hist = np.flatnonzero(role == 0)
        held = np.flatnonzero(role == 1)
        cols = np.arange(values.shape[1])
        if smoke:
            hist, cols = hist[:40], cols[:20]
            held = np.array([i for i in held if observed[i][cols].sum() >= 6][:10], dtype=int)
        self.family = family
        self.rows_per_chunk = SMOKE_ROWS_PER_CHUNK if smoke else ROWS_PER_CHUNK_MAX
        self.rows_per_chunk = max(1, min(self.rows_per_chunk, CHUNK_TARGET_BYTES // (5 * len(cols))))
        self.batch = SMOKE_PREDICT_BATCH if smoke else PREDICT_BATCH
        self.Xh = np.where(observed[np.ix_(hist, cols)], values[np.ix_(hist, cols)], 0.0)
        self.Oh = observed[np.ix_(hist, cols)]
        self.Yt = np.where(observed[np.ix_(held, cols)], values[np.ix_(held, cols)], 0.0)
        self.Ot = observed[np.ix_(held, cols)]
        self.M, self.N = self.Xh.shape
        self.Mt = self.Yt.shape[0]
        count = self.Oh.sum(0)
        if self.M < 5 or self.Mt < 2 or (count < 5).any():
            raise ValueError("dataset too small")
        self.mean = (self.Xh * self.Oh).sum(0) / count
        var = (((self.Xh - self.mean) ** 2) * self.Oh).sum(0) / count
        self.std = np.sqrt(var)
        if (self.std < 1e-8).any():
            raise ValueError("degenerate column")
        self.Zh = (self.Xh - self.mean) / self.std
        self.Zt = (self.Yt - self.mean) / self.std
        self.n_chunks = math.ceil(self.M / self.rows_per_chunk)
        self.n_batches = math.ceil(self.Mt / self.batch)
        limits = FAMILY_LIMITS[family]
        if not smoke and (self.n_chunks > limits[0] or self.n_batches > limits[1]):
            raise ValueError("declared chunk/batch maxima exceeded")
        self.manifest_meta = {"revision": man["revision"], "n_models": len(models)}
        self._base = None

    # ---- wire encoding
    def history_message(self, chunk):
        lo = chunk * self.rows_per_chunk
        hi = min(self.M, lo + self.rows_per_chunk)
        values = np.ascontiguousarray(self.Xh[lo:hi].astype("<f4"))
        mask = np.ascontiguousarray(self.Oh[lo:hi].astype(np.uint8))
        return {"op": "load_history", "chunk_index": chunk, "n_chunks": self.n_chunks, "row_start": lo,
                "n_rows": hi - lo, "n_cols": self.N, "dtype": "float32", "byte_order": "little",
                "layout": "row_major", "shape": [hi - lo, self.N],
                "values_b64": base64.b64encode(values.tobytes()).decode("ascii"),
                "mask_b64": base64.b64encode(mask.tobytes()).decode("ascii")}

    def predict_message(self, batch, selected, obs_values, obs_mask):
        lo = batch * self.batch
        hi = min(self.Mt, lo + self.batch)
        v = np.ascontiguousarray(obs_values[lo:hi].astype("<f4"))
        m = np.ascontiguousarray(obs_mask[lo:hi].astype(np.uint8))
        return {"op": "predict", "batch_index": batch, "n_batches": self.n_batches, "n_models": hi - lo,
                "selected": list(selected), "dtype": "float32", "byte_order": "little",
                "layout": "row_major", "shape": [hi - lo, len(selected)],
                "observed_values_b64": base64.b64encode(v.tobytes()).decode("ascii"),
                "observed_mask_b64": base64.b64encode(m.tobytes()).decode("ascii")}

    # ---- evaluator-owned controls
    def observations(self, selected, case):
        sel = np.asarray(selected)
        true_v, true_m = self.Yt[:, sel], self.Ot[:, sel]
        if case == "real":
            return true_v, true_m
        if case == "perm":
            order = sorted(range(self.Mt), key=lambda i: hashlib.sha256(
                ("perm|%s|%d" % (self.family, i)).encode()).hexdigest())
            perm = np.empty(self.Mt, dtype=int)
            for j, i in enumerate(order):
                perm[i] = order[(j + 1) % self.Mt]
            if (perm == np.arange(self.Mt)).any():
                raise VacuousControl("identity permutation")
            pv, pm = true_v[perm], true_m[perm]
            if np.array_equal(pv, true_v) and np.array_equal(pm, true_m):
                raise VacuousControl("permuted observations equal true")
            return pv, pm
        if case == "const":
            cv = np.tile(self.mean[sel], (self.Mt, 1))
            if np.array_equal(cv, true_v) or np.ptp(true_v, axis=0).max() <= 0:
                raise VacuousControl("constant control equals true")
            return cv, np.ones_like(true_m)
        raise ValueError("unknown case")

    def nrmse(self, pred_z, cells):
        counts = cells.sum(1)
        use = counts > 0
        if not use.any():
            raise ValueError("no scored cells")
        msq = (((pred_z - self.Zt) ** 2) * cells).sum(1)[use] / counts[use]
        return float(np.sqrt(msq.mean()))

    # ---- baselines
    def baselines(self, deadline, clock):
        if self._base is not None:
            return self._base
        def check():
            if clock() > deadline:
                raise TimeoutError("baseline deadline")
        r = min(COMPLETION_RANK, self.N - 1) if self.N > 1 else 1
        Z = np.where(self.Oh, self.Zh, 0.0)
        for _ in range(COMPLETION_ITERS if not self.Oh.all() else 1):
            U, s, Vt = np.linalg.svd(Z, full_matrices=False)
            low = (U[:, :r] * s[:r]) @ Vt[:r]
            Z = np.where(self.Oh, self.Zh, low)
        check()
        self._base = {"Zc": Z, "random": {}, "greedy_order": None, "greedy": {}}
        return self._base

    def ridge_predict(self, selected, deadline, clock):
        Zc = self.baselines(deadline, clock)["Zc"]
        sel = np.asarray(selected)
        X, Y = Zc[:, sel], Zc
        mx, my = X.mean(0), Y.mean(0)
        Xc, Yc = X - mx, Y - my
        U, s, Vt = np.linalg.svd(Xc, full_matrices=False)
        UtY = U.T @ Yc
        best = None
        for g in RIDGE_GRID:
            lam = g * self.M
            d = s ** 2 / (s ** 2 + lam)
            h = (U ** 2) @ d
            loo = (Yc - U @ (d[:, None] * UtY)) / (1.0 - h)[:, None]
            err = float(np.mean(loo ** 2))
            if best is None or err < best[0]:
                best = (err, lam)
        lam = best[1]
        W = Vt.T @ ((s / (s ** 2 + lam))[:, None] * UtY)
        obs = np.where(self.Ot[:, sel], (self.Yt[:, sel] - self.mean[sel]) / self.std[sel], mx)
        return my + (obs - mx) @ W

    def random_predictions(self, k, deadline, clock):
        base = self.baselines(deadline, clock)
        if k not in base["random"]:
            preds = []
            for draw in range(BASELINE_DRAWS):
                seed = int(hashlib.sha256(("rk|%s|%d|%d" % (self.family, k, draw)).encode()).hexdigest()[:8], 16)
                sel = np.random.default_rng(seed).choice(self.N, size=k, replace=False)
                preds.append(self.ridge_predict(sel, deadline, clock))
            base["random"][k] = preds
        return base["random"][k]

    def greedy_predictions(self, k, deadline, clock):
        base = self.baselines(deadline, clock)
        if base["greedy_order"] is None:
            Zc = base["Zc"]
            lam = GREEDY_LAMBDA * self.M
            order = []
            for _ in range(min(20, self.N)):
                best = None
                for j in range(self.N):
                    if j in order:
                        continue
                    cand = order + [j]
                    X = Zc[:, cand] - Zc[:, cand].mean(0)
                    Yc = Zc - Zc.mean(0)
                    U, s, Vt = np.linalg.svd(X, full_matrices=False)
                    d = s ** 2 / (s ** 2 + lam)
                    h = (U ** 2) @ d
                    loo = (Yc - U @ (d[:, None] * (U.T @ Yc))) / (1.0 - h)[:, None]
                    rest = np.ones(self.N, dtype=bool)
                    rest[cand] = False
                    err = float(np.mean(loo[:, rest] ** 2)) if rest.any() else float(np.mean(loo ** 2))
                    if best is None or err < best[0] - 1e-15:
                        best = (err, j)
                    if clock() > deadline:
                        raise TimeoutError("baseline deadline")
                order.append(best[1])
            base["greedy_order"] = order
        if k not in base["greedy"]:
            base["greedy"][k] = self.ridge_predict(base["greedy_order"][:k], deadline, clock)
        return base["greedy"][k]

    def cells(self, selected):
        c = self.Ot.copy()
        c[:, list(selected)] = False
        return c


def decode_predictions(response, n_models, n_cols):
    allowed = {"predictions_b64", "dtype", "shape", "encoding", "byte_order", "layout"}
    if type(response) is not dict or "predictions_b64" not in response or not set(response) <= allowed:
        raise CandidateProtocolError("malformed_response")
    if response.get("dtype", "float32") != "float32" or response.get("byte_order", "little") != "little" \
            or response.get("encoding", "base64") != "base64" or response.get("layout", "row_major") != "row_major":
        raise CandidateProtocolError("malformed_response")
    shape = response.get("shape", [n_models, n_cols])
    if type(shape) is not list or shape != [n_models, n_cols] or any(type(x) is not int for x in shape):
        raise CandidateProtocolError("malformed_response")
    blob = response["predictions_b64"]
    if type(blob) is not str:
        raise CandidateProtocolError("malformed_response")
    try:
        raw = base64.b64decode(blob.encode("ascii"), validate=True)
    except (ValueError, UnicodeEncodeError):
        raise CandidateProtocolError("malformed_response") from None
    if len(raw) != n_models * n_cols * 4:
        raise CandidateProtocolError("malformed_response")
    arr = np.frombuffer(raw, dtype="<f4").astype(np.float64).reshape(n_models, n_cols)
    if not np.isfinite(arr).all():
        raise CandidateProtocolError("nonfinite_prediction")
    return arr


def validate_selection(response, k, n_cols):
    if type(response) is not dict or set(response) != {"selected"}:
        raise CandidateProtocolError("malformed_response")
    sel = response["selected"]
    if type(sel) is not list or len(sel) != k or any(type(x) is not int for x in sel) \
            or len(set(sel)) != k or any(x < 0 or x >= n_cols for x in sel):
        raise CandidateProtocolError("invalid_selection")
    return sel


def run_episode_body(dataset, episode, call, work_deadline, clock):
    for chunk in range(dataset.n_chunks):
        require_reset_ack_like(call(dataset.history_message(chunk)), "load_history")
    k = episode["k"]
    selected = validate_selection(call({"op": "select", "k": k, "n_cols": dataset.N}), k, dataset.N)
    obs_values, obs_mask = dataset.observations(selected, episode["case"])
    preds = np.zeros((dataset.Mt, dataset.N))
    for batch in range(dataset.n_batches):
        message = dataset.predict_message(batch, selected, obs_values, obs_mask)
        lo = batch * dataset.batch
        hi = min(dataset.Mt, lo + dataset.batch)
        preds[lo:hi] = decode_predictions(call(message), hi - lo, dataset.N)
    pred_z = (preds - dataset.mean) / dataset.std
    if not np.isfinite(pred_z).all():
        raise CandidateProtocolError("nonfinite_prediction")
    cells = dataset.cells(selected)
    cand = dataset.nrmse(pred_z, cells)
    mean_b = dataset.nrmse(np.zeros_like(pred_z), cells)
    rand = float(np.mean([dataset.nrmse(p, cells) for p in dataset.random_predictions(k, work_deadline + EPISODE_OVERHEAD + 60, clock)]))
    greedy = dataset.nrmse(dataset.greedy_predictions(k, work_deadline + EPISODE_OVERHEAD + 60, clock), cells)
    vals = (cand, mean_b, rand, greedy)
    if not all(math.isfinite(v) for v in vals) or min(mean_b, rand, greedy) <= 0:
        raise CandidateProtocolError("nonfinite_metric")
    skill = lambda b: float(np.clip(1.0 - cand / b, -1.0, 1.0))
    return {"ok": True, "nrmse": cand, "skill_mean": skill(mean_b), "skill_random": skill(rand),
            "skill_greedy": skill(greedy), "nrmse_mean_base": mean_b}


def require_reset_ack_like(response, op):
    if type(response) is not dict or set(response) != {"ok"} or response["ok"] is not True:
        raise CandidateProtocolError("invalid_ack")


def worst_outcome(dataset):
    full = dataset.nrmse(np.zeros((dataset.Mt, dataset.N)), dataset.Ot)
    return {"ok": False, "nrmse": 2.0 * full, "skill_mean": -1.0, "skill_random": -1.0,
            "skill_greedy": -1.0, "nrmse_mean_base": full}


def mean_of(values):
    values = list(values)
    return float(sum(values) / len(values))


def rpc_ops_for(episode_family):
    chunks, batches = FAMILY_LIMITS[episode_family]
    return {"reset": 1, "load_history": chunks, "select": 1, "predict": batches}


def declared_rpc_budget(plan):
    total = 0
    for episode in plan:
        total += sum(rpc_ops_for(episode["family"]).values())
    total += sum(rpc_ops_for(plan[0]["family"]).values())   # one permitted trailing replay of the first seed
    return total


def make_evaluation_evidence(seed_records):
    return {"schema_version": 1, "episodes": seed_records}


def write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle, allow_nan=False, separators=(",", ":"))


def preflight_wire(datasets):
    """Serialize the largest representative messages (history chunk, predict request/response) of each family."""
    sizes = {}
    for name, ds in datasets.items():
        k = min(20, ds.N)
        selected = list(range(k))
        ov, om = ds.observations(selected, "real")
        hist = len(bounded_json_line(ds.history_message(0)))
        pred = len(bounded_json_line(ds.predict_message(0, selected, ov, om)))
        n = min(ds.batch, ds.Mt)
        response = {"predictions_b64": base64.b64encode(np.zeros((n, ds.N), dtype="<f4").tobytes()).decode("ascii"),
                    "dtype": "float32", "shape": [n, ds.N], "encoding": "base64"}
        resp = len(bounded_json_line(response))
        sizes[name] = (hist, pred, resp)
    return sizes


# ----------------------------------------------------------------------------- shared aggregation
def real_curve(plan, outcomes, field, family):
    by_k = collections.defaultdict(dict)
    for ep, out in zip(plan, outcomes):
        if ep["case"] == "real" and ep["family"] == family:
            by_k[ep["k"]][ep["seed"]] = out[field]
    return {k: mean_of(seeds.values()) for k, seeds in sorted(by_k.items())}


def family_value(plan, outcomes, field, family):
    return mean_of(real_curve(plan, outcomes, field, family).values())


def paired_control(plan, outcomes, flags, family, case):
    """Per control episode: (ctrl nrmse, matched real nrmse, gap); failed pair -> gap -1.0 (finite worst case)."""
    rows = []
    for i, ep in enumerate(plan):
        if ep["case"] != case or ep["family"] != family:
            continue
        j = next(j for j, e in enumerate(plan) if e["case"] == "real" and e["family"] == family
                 and e["seed"] == ep["seed"] and e["k"] == ep["k"])
        gap = outcomes[i]["nrmse"] - outcomes[j]["nrmse"] if (flags[i] and flags[j]) else -1.0
        rows.append((outcomes[i]["nrmse"], outcomes[j]["nrmse"], gap, ep["seed"]))
    return rows


def seed_evidence(plan, outcomes, flags, durations):
    records = []
    for seed in sorted({ep["seed"] for ep in plan}):
        idx = [i for i, ep in enumerate(plan) if ep["seed"] == seed]
        ok = all(flags[i] for i in idx)
        for i in idx:
            if plan[i]["case"] in ("perm", "const"):
                j = next(j for j in idx if plan[j]["case"] == "real" and plan[j]["family"] == plan[i]["family"]
                         and plan[j]["k"] == plan[i]["k"])
                ok = ok and outcomes[j]["nrmse"] < outcomes[i]["nrmse"]
        reals = [outcomes[i]["skill_mean"] for i in idx if plan[i]["case"] == "real"]
        records.append({"seed": int(seed), "score": float(mean_of(reals)), "correct": bool(ok),
                        "duration_seconds": float(sum(durations[i] for i in idx))})
    return records


def make_transport(program_path, clock):
    brokered_env = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    if program_path == PROXY_PATH:
        if not brokered_env:
            raise RuntimeError("broker proxy path without broker socket")
        return BrokeredTransport(clock), True
    return NativeTransport(program_path, clock), False


def run_plane(args):
    clock = time.monotonic
    hard_deadline = T0 + WALL_CLOCK - STARTUP_ALLOWANCE
    plan = build_plan()
    datasets = load_datasets(resource_root())
    budget = declared_rpc_budget(plan)
    if budget > MAX_CANDIDATE_RPC_CALLS:
        raise RuntimeError("declared RPC budget exceeds contract ceiling")
    if not SMOKE:
        require_joint_workload_budget({
            "episode_count": len(plan), "method_count": 1, "wall_seconds": WALL_CLOCK,
            "startup_seconds": STARTUP_ALLOWANCE + BASELINE_ALLOWANCE_SECONDS, "reset_seconds": RESET_TIMEOUT,
            "cleanup_seconds": EPISODE_OVERHEAD, "finish_seconds": FINISH_RESERVE, "work_seconds": EPISODE_WORK_CAP})
    preflight_wire(datasets)
    worst = [worst_outcome(datasets[ep["family"]]) for ep in plan]
    transport = None
    complete, outcomes, flags, durations = False, worst, [False] * len(plan), [0.0] * len(plan)
    baselines_ok = True
    reserve_for_episodes = len(plan) * (RESET_TIMEOUT + EPISODE_WORK_CAP + EPISODE_OVERHEAD) + FINISH_RESERVE
    baseline_deadline = hard_deadline - reserve_for_episodes
    try:
        for ep in plan:                      # required evaluator-owned baselines, preflighted before candidate work
            ds = datasets[ep["family"]]
            ds.random_predictions(ep["k"], baseline_deadline, clock)
            ds.greedy_predictions(ep["k"], baseline_deadline, clock)
    except (TimeoutError, ValueError, FloatingPointError, np.linalg.LinAlgError):
        baselines_ok = False
        try:
            fail_required_baseline("baseline_result_failure", lambda: None,
                                   lambda c: print("baseline_failure category=%s" % c, file=sys.stderr, flush=True)
                                   if PLANE == "search" else None)
        except RequiredBaselineFailure:
            pass
    if baselines_ok:
        transport, brokered = make_transport(args.program_path, clock)
        counter = {"n": 0}

        def rpc(request, timeout):
            counter["n"] += 1
            if counter["n"] > MAX_CANDIDATE_RPC_CALLS:
                raise RuntimeError("candidate RPC cap exceeded")
            return transport.request(request, timeout)

        def evaluate(episode, call, work_deadline):
            return run_episode_body(datasets[episode["family"]], episode, call, work_deadline, clock)

        def record_failure(episode, failure):
            if PLANE == "search":
                stderr_failure(episode, failure)
                diag = transport.diagnostics()
                if DIAG_VISIBLE and diag:
                    sys.stderr.write(diag["stderr"][:4096] + ("\n" if not diag["stderr"].endswith("\n") else ""))
                    sys.stderr.flush()

        try:
            outcomes, complete, flags, durations = run_declared_episodes(
                plan, hard_deadline=hard_deadline, finish_reserve=FINISH_RESERVE, reset_timeout=RESET_TIMEOUT,
                episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_CAP, clock=clock, rpc=rpc, evaluate=evaluate,
                worst_case=lambda ep: worst_outcome(datasets[ep["family"]]),
                record_failure=record_failure, work_cap=EPISODE_WORK_CAP)
        finally:
            try:
                transport.close()
            except Exception:
                pass
    metrics, correct = aggregate(plan, outcomes, flags)
    if not baselines_ok or not complete:
        correct = False
    os.makedirs(args.results_dir, exist_ok=True)
    write_json(os.path.join(args.results_dir, "metrics.json"), metrics)
    write_json(os.path.join(args.results_dir, "correct.json"), {"correct": bool(correct)})
    records = seed_evidence(plan, outcomes, flags, durations)
    if not baselines_ok:
        elapsed = max(0.0, clock() - T0)
        records = [{"seed": r["seed"], "score": -1.0, "correct": False, "duration_seconds": elapsed} for r in records]
    write_json(os.path.join(args.results_dir, "evaluation_evidence.json"), make_evaluation_evidence(records))
    if QUALIFICATION:
        write_json(os.path.join(args.results_dir, "qualification.json"),
                   {"schema_version": 1, "feasible": bool(baselines_ok and complete and not SMOKE)})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args()
    try:
        run_plane(args)
    except SystemExit:
        raise
    except BaseException as error:  # noqa: BLE001
        name = type(error).__name__
        message = str(error).replace("\n", " ")[:200] if PLANE == "search" else ""
        print(("evaluator_error type=%s %s" % (name, message))[:256], file=sys.stderr, flush=True)
        sys.exit(1)



# ----------------------------------------------------------------------------- plane-specific: final
FAMILIES = ("mteb", "oll", "helm")
MTEB_KS = (2, 5, 10, 20)
METRIC_NAMES = (
    "final_score", "final_nrmse", "final_skill_vs_random_selection", "final_skill_vs_greedy_ridge",
    "final_nrmse_mteb", "final_nrmse_oll", "final_nrmse_helm",
    "final_nrmse_mteb_k2", "final_nrmse_mteb_k5", "final_nrmse_mteb_k10", "final_nrmse_mteb_k20",
    "final_permuted_control_gap")


def build_plan():
    if SMOKE:
        seeds, cases = (FINAL_SEEDS[0],), (("real", "mteb", 2), ("perm", "mteb", 2))
    else:
        seeds = FINAL_SEEDS
        cases = (("real", "mteb", 2), ("real", "mteb", 5), ("real", "mteb", 10), ("real", "mteb", 20),
                 ("perm", "mteb", 10), ("const", "mteb", 10),
                 ("real", "oll", 1), ("real", "oll", 2), ("real", "oll", 3), ("perm", "oll", 2),
                 ("real", "helm", 2), ("real", "helm", 3), ("real", "helm", 5), ("perm", "helm", 3))
    return [{"seed": seed, "case": case, "family": family, "k": k, "name": "%s_%s_k%d" % (case, family, k)}
            for seed in seeds for case, family, k in cases]


def load_datasets(root):
    needed = {ep["family"] for ep in build_plan()}
    stems = {"mteb": "mteb_final", "oll": "oll_final", "helm": "helm_final"}
    return {f: Dataset(f, root, stems[f], SMOKE) for f in FAMILIES if f in needed}


def aggregate(plan, outcomes, flags):
    """Hierarchy: seeds (equal) -> k grid (equal) -> dataset families (1/3 each) -> final_score; controls weight 0."""
    fams = [f for f in FAMILIES if any(ep["family"] == f for ep in plan)]

    def over(field):
        return mean_of(family_value(plan, outcomes, field, f) for f in fams)

    metrics = {"final_score": over("skill_mean"), "final_nrmse": over("nrmse"),
               "final_skill_vs_random_selection": over("skill_random"),
               "final_skill_vs_greedy_ridge": over("skill_greedy")}
    for f in FAMILIES:
        metrics["final_nrmse_" + f] = family_value(plan, outcomes, "nrmse", f) if f in fams else 0.0
    curve = real_curve(plan, outcomes, "nrmse", "mteb")
    for k in MTEB_KS:
        metrics["final_nrmse_mteb_k%d" % k] = float(curve.get(k, 0.0))      # absent only in the reduced smoke profile
    gaps, controls_ok = [], True
    for f in fams:
        perm = paired_control(plan, outcomes, flags, f, "perm")
        gaps.append(mean_of(r[2] for r in perm))
        controls_ok = controls_ok and mean_of(r[1] for r in perm) < mean_of(r[0] for r in perm)
    metrics["final_permuted_control_gap"] = mean_of(gaps)
    const = paired_control(plan, outcomes, flags, "mteb", "const")
    if const:
        controls_ok = controls_ok and mean_of(r[1] for r in const) < mean_of(r[0] for r in const)
    correct = bool(all(flags) and controls_ok and metrics["final_score"] > 0.0
                   and metrics["final_skill_vs_random_selection"] > 0.0)
    if not all(math.isfinite(metrics[n]) for n in METRIC_NAMES):
        raise ValueError("nonfinite metric")
    return {n: float(metrics[n]) for n in METRIC_NAMES}, correct


def resource_root():
    base = os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "resources", "final")


if __name__ == "__main__":
    main()
