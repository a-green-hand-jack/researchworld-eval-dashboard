#!/usr/bin/env python3
"""Development-only search evaluator for the width-scaling grokking task (self-contained)."""
import argparse
import base64
import collections
import hashlib
import importlib.util
import json
import math
import os
import queue
import re
import resource
import selectors
import signal
import subprocess
import sys
import tempfile
import threading
import time
import unicodedata

import numpy as np

BROKER_PROXY_PATH = "/broker-code/candidate_proxy.py"
WIRE_LIMIT = 64 * 1024 * 1024
STARTUP_ALLOWANCE = 120.0
FINISH_RESERVE = 60.0
EPISODE_OVERHEAD = 15.0
STDERR_REPAIR_MODES = ("AGENTIC_TASK_QUALIFICATION", "AGENTIC_TASK_DRAFT_SMOKE")
CANDIDATE_THREADS = "8"
SEC_PER_STEP_ESTIMATE = {16: 0.03, 32: 0.04, 64: 0.06, 128: 0.12, 256: 0.35}

PLANE = "search"
PRIMARY_SEEDS = [101, 102]
RESET_SEQUENCE = [101, 102, 101, 102, 101, 102, 101, 101]
SMOKE_RESET_SEQUENCE = [101, 101, 101]
WALL_CLOCK_SECONDS = 7200.0
MAX_RPC_CALLS = 400          # 8 episodes x (reset + load_train + 20 x (train + predict)) = 336, plus headroom
RESET_TIMEOUT = 180.0
RPC_TIMEOUT_CAP = 900.0
REFERENCE_RESERVE = 1500.0
FIT_THRESHOLD = 0.99
CONTROL_VAL_CEILING = 0.10
MIN_CHANGED_FRACTION = 0.9
METRIC_NAMES = ("combined_score", "final_val_acc_mean", "censored_fraction", "control_max_val_acc",
                "missing_episodes")


def run_reference_plan(wl, deadline, clock, failures, record_failure):
    """Search reference: control width, first search seed, same checkpoint plan."""
    if failures:
        return None
    curves, category = run_reference_width(wl, wl["seeds_used"][0], wl["control_width"], wl["n_checkpoints"],
                                           wl["probe_every"], deadline, clock)
    if category is not None:
        record_failure(category)
        return None
    steps = [(k + 1) * wl["probe_every"] for k in range(wl["n_checkpoints"])]
    fit, gen, gap, censored = delay_gap(steps, curves["train_acc"], curves["val_acc"], wl["max_steps"],
                                        wl["probe_every"])
    emit_search_line("search_reference width=%d fit=%s gen=%s gap=%.0f final_val=%.4f" % (
        wl["control_width"], fit, gen, gap, curves["val_acc"][-1]))
    return {"fit": fit, "gen": gen, "gap": gap}


def worst_case_metrics(n_episodes):
    return {"combined_score": 0.0, "final_val_acc_mean": 0.0, "censored_fraction": 1.0,
            "control_max_val_acc": 1.0, "missing_episodes": n_episodes}


def fatal_result(started, smoke):
    sequence = SMOKE_RESET_SEQUENCE if smoke else RESET_SEQUENCE
    elapsed = time.monotonic() - started
    episodes = [{"seed": s, "kind": "primary"} for s in dict.fromkeys(sequence)]
    outcomes = [{"score": 0.0, "duration": elapsed / len(episodes)} for _ in episodes]
    return {"metrics": worst_case_metrics(len(sequence)), "correct": False,
            "evidence": seed_evidence(episodes, outcomes, [False] * len(episodes)), "feasible": False}


def aggregate_plane(wl, episodes, outcomes, complete, reference, baseline_failures, elapsed, hard_deadline,
                    total_rpc, rpc_count, reset_log, sequence):
    prim = [i for i, e in enumerate(episodes) if e["kind"] == "primary"]
    ctrl = [i for i, e in enumerate(episodes) if e["kind"] != "primary"]
    n_p = len(prim)
    passed = [False] * len(episodes)
    for i in prim:
        passed[i] = outcomes[i]["complete"] and outcomes[i]["max_train"] >= FIT_THRESHOLD
    for i in ctrl:
        passed[i] = control_passes(outcomes[i])
    metrics = {
        "combined_score": seed_width_score(episodes, outcomes, wl),
        "final_val_acc_mean": weighted_mean([outcomes[i]["final_val"] for i in prim], [1.0 / n_p] * n_p),
        "censored_fraction": weighted_mean([1.0 if outcomes[i]["censored"] else 0.0 for i in prim],
                                           [1.0 / n_p] * n_p),
        "control_max_val_acc": max(outcomes[i]["max_val"] for i in ctrl),
        "missing_episodes": sum(1 for o in outcomes if not o["complete"]),
    }
    if tuple(metrics) != METRIC_NAMES or not all(math.isfinite(v) for v in metrics.values()):
        raise ValueError("invalid metric record")
    for i, (e, o) in enumerate(zip(episodes, outcomes)):
        emit_search_line("search_episode kind=%s seed=%d width=%d complete=%d fit=%s gen=%s gap=%.0f "
                         "score=%.4f final_val=%.4f max_val=%.4f" % (
                             e["kind"], e["seed"], e["width"], o["complete"], o["fit_step"], o["gen_step"],
                             o["gap"], o["score"], o["final_val"], o["max_val"]))
    within = elapsed <= WALL_CLOCK_SECONDS - STARTUP_ALLOWANCE
    ok_budget = within and rpc_count <= MAX_RPC_CALLS and reset_log == list(sequence)
    ok_run = complete and not baseline_failures and reference is not None
    correct = bool(ok_run and ok_budget and all(passed))
    return {"metrics": metrics, "correct": correct, "evidence": seed_evidence(episodes, outcomes, passed),
            "feasible": bool(ok_run and ok_budget)}



# ----------------------------------------------------------------------------- helpers

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
    """Malformed candidate response (schema, shape, range, size)."""


class CandidateRpcError(RuntimeError):
    """Candidate crashed or raised while handling a request."""

    def __init__(self, category):
        self.category = bounded_failure_name(category, "candidate_error")
        super().__init__("candidate rpc failed")


class FatalOperationalError(RuntimeError):
    """Broker/transport/budget failure that makes the remaining evidence unobtainable."""


def describe_episode_failure(error, operation):
    context = error
    for _ in range(8):
        if isinstance(context, InvalidResetResponse):
            return {"component": "candidate", "category": "invalid_reset_response", "operation": "reset"}
        if isinstance(context, RequiredBaselineFailure):
            return {"component": "baseline", "category": context.category, "operation": "baseline_worker"}
        if isinstance(context, CandidateProtocolError):
            return {"component": "candidate", "category": "malformed_response",
                    "operation": bounded_failure_name(operation, "unknown")}
        if isinstance(context, CandidateRpcError):
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


def require_joint_workload_budget(*, profile):
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


def bounded_json_line(value, wire_limit=WIRE_LIMIT):
    encoded = json.dumps(value, allow_nan=False, separators=(",", ":")).encode("utf-8") + b"\n"
    if len(encoded) >= wire_limit:
        raise ValueError("complete message exceeds wire limit")
    return encoded


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


def cpu_limit_seconds(wall_seconds, allowed_threads):
    if (type(wall_seconds) not in (int, float) or not math.isfinite(wall_seconds)
            or wall_seconds <= 0 or type(allowed_threads) is not int or allowed_threads <= 0):
        raise ValueError("invalid CPU budget")
    return math.ceil(wall_seconds * allowed_threads)


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
        self.result = {"stderr": "".join(self.lines), "observed_bytes": self.observed_bytes,
                       "retained_bytes": self.retained_bytes, "truncated": self.truncated,
                       "capture_error": self.capture_error}
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


def repair_mode():
    return PLANE == "search" and any(os.environ.get(name) == "1" for name in STDERR_REPAIR_MODES)


def emit_search_line(text):
    if PLANE == "search":
        print(text[:256].replace("\n", " "), file=sys.stderr, flush=True)


# ----------------------------------------------------------------------------- data

def op_label(op, p, a, b):
    if op != "add":
        raise ValueError("unsupported operation")
    return (a + b) % p


def build_task(op, p, frac, seed):
    a, b = np.meshgrid(np.arange(p), np.arange(p), indexing="ij")
    a, b = a.ravel(), b.ravel()
    label = op_label(op, p, a, b)
    perm = np.random.default_rng([seed, p, 7919]).permutation(p * p)
    ntrain = int(frac * p * p)
    train = np.sort(perm[:ntrain])
    val = np.sort(perm[ntrain:])
    query = np.random.default_rng([seed, p, 104729]).permutation(p * p)
    return {"p": p, "a": a, "b": b, "label": label, "train": train, "val": val, "query": query}


def row_digest(op, p, a, b, label):
    text = unicodedata.normalize("NFKC", f"{op}|{p}|{int(a)}|{int(b)}|{int(label)}")
    return hashlib.sha256(" ".join(text.split()).encode("utf-8")).digest()


def split_digest(task):
    h = hashlib.sha256()
    h.update(str(task["p"]).encode("ascii") + b"|")
    h.update(np.asarray(task["train"], dtype="<i8").tobytes())
    return h.hexdigest()


def check_split(op, task):
    idx_t, idx_v = task["train"], task["val"]
    ht = {row_digest(op, task["p"], task["a"][i], task["b"][i], task["label"][i]) for i in idx_t}
    hv = {row_digest(op, task["p"], task["a"][i], task["b"][i], task["label"][i]) for i in idx_v}
    if len(ht) != len(idx_t) or len(hv) != len(idx_v) or ht & hv:
        raise ValueError("normalized content overlap or duplication inside split")
    if len(idx_t) + len(idx_v) != task["p"] ** 2 or len(set(idx_t.tolist()) & set(idx_v.tolist())):
        raise ValueError("split is not a partition")
    return ht | hv


def encode_int16(arr):
    arr = np.ascontiguousarray(arr, dtype="<i2")
    return {"dtype": "int16", "shape": list(arr.shape), "encoding": "base64-le",
            "data": base64.b64encode(arr.tobytes()).decode("ascii")}


def decode_predictions(obj, n, p):
    if (type(obj) is not dict or set(obj) != {"dtype", "shape", "encoding", "data"}
            or obj["dtype"] != "int16" or obj["encoding"] != "base64-le" or obj["shape"] != [n]
            or type(obj["data"]) is not str):
        raise CandidateProtocolError("bad prediction envelope")
    try:
        raw = base64.b64decode(obj["data"], validate=True)
    except ValueError:
        raise CandidateProtocolError("bad base64") from None
    if len(raw) != 2 * n:
        raise CandidateProtocolError("bad prediction length")
    preds = np.frombuffer(raw, dtype="<i2").astype(np.int64)
    if n and (preds.min() < 0 or preds.max() >= p):
        raise CandidateProtocolError("prediction out of range")
    return preds


def shuffled_labels(labels, seed, p, min_changed):
    for attempt in range(64):
        perm = np.random.default_rng([seed, p, 31337, attempt]).permutation(len(labels))
        shuffled = labels[perm]
        changed = float(np.mean(shuffled != labels))
        if changed >= min_changed:
            return shuffled, changed
    raise ValueError("vacuous label-shuffle control")


def workload_from_manifest(root, smoke):
    with open(os.path.join(root, "manifest.json"), "r", encoding="utf-8") as handle:
        man = json.load(handle)
    if man.get("schema_version") != 1 or man.get("plane") != PLANE or man.get("operation") != "add":
        raise ValueError("bad manifest")
    wl = {k: man[k] for k in ("operation", "train_fraction", "n_heads", "lr", "betas", "weight_decay",
                              "split_sha256")}
    prof = man["smoke"] if smoke else man["full"]
    wl.update(modulus=prof["modulus"], widths=list(prof["widths"]), max_steps=prof["max_steps"],
              probe_every=prof["probe_every"], seeds=list(man["seeds"]),
              control_width=prof["control_width"], digests=man["split_sha256"][prof["key"]])
    if wl["max_steps"] % wl["probe_every"]:
        raise ValueError("probe interval must divide the step limit")
    wl["n_checkpoints"] = wl["max_steps"] // wl["probe_every"]
    return wl


# ----------------------------------------------------------------------------- metrics

def accuracy_curves(task, preds):
    correct = preds == task["label"][task["query"]]
    ok = np.zeros(task["p"] ** 2, dtype=bool)
    ok[task["query"]] = correct
    return float(ok[task["train"]].mean()), float(ok[task["val"]].mean())


def auc_score(steps, accs):
    steps = np.asarray(steps, dtype=float)
    accs = np.asarray(accs, dtype=float)
    if len(steps) < 2:
        return float(accs[-1])
    return float(np.trapezoid(accs, steps) / (steps[-1] - steps[0]))


def first_step(steps, accs, thr):
    for s, a in zip(steps, accs):
        if a >= thr:
            return int(s)
    return None


def delay_gap(steps, train_acc, val_acc, max_steps, probe_every):
    fit, gen = first_step(steps, train_acc, FIT_THRESHOLD), first_step(steps, val_acc, FIT_THRESHOLD)
    if fit is None or gen is None:
        return fit, gen, float(max_steps), True
    return fit, gen, float(max(gen - fit, probe_every)), False


def make_outcome(steps, train_acc, val_acc, wl, duration):
    fit, gen, gap, censored = delay_gap(steps, train_acc, val_acc, wl["max_steps"], wl["probe_every"])
    out = {"complete": True, "score": auc_score(steps, val_acc), "fit_step": fit, "gen_step": gen,
           "gap": gap, "censored": censored, "final_val": float(val_acc[-1]),
           "max_val": float(max(val_acc)), "max_train": float(max(train_acc)), "duration": float(duration)}
    if not all(math.isfinite(out[k]) for k in ("score", "gap", "final_val", "max_val", "max_train")):
        raise CandidateProtocolError("non-finite metric")
    return out


def worst_case_outcome(episode, wl):
    return {"complete": False, "score": 0.0, "fit_step": None, "gen_step": None,
            "gap": float(wl["max_steps"]), "censored": True, "final_val": 0.0,
            "max_val": 1.0, "max_train": 0.0, "duration": 0.0}


def control_passes(outcome):
    return outcome["complete"] and outcome["max_val"] <= CONTROL_VAL_CEILING


def weighted_mean(values, weights):
    if (not values or len(values) != len(weights) or any(not math.isfinite(w) or w < 0 for w in weights)
            or not math.isclose(sum(weights), 1.0, rel_tol=0, abs_tol=1e-12)):
        raise ValueError("invalid predeclared aggregation weights")
    if not all(math.isfinite(v) for v in values):
        raise ValueError("nonfinite contribution")
    return sum(v * w for v, w in zip(values, weights))


def seed_width_score(episodes, outcomes, wl):
    """Equal-weight mean over seeds, then equal-weight mean over widths (hierarchy declared up front)."""
    widths, seeds = wl["widths"], wl["seeds_used"]
    per_width = []
    for w in widths:
        vals = [outcomes[i]["score"] for i, e in enumerate(episodes) if e["kind"] == "primary" and e["width"] == w]
        if len(vals) != len(seeds):
            raise ValueError("episode plan does not cover seeds")
        per_width.append(weighted_mean(vals, [1.0 / len(seeds)] * len(seeds)))
    return weighted_mean(per_width, [1.0 / len(widths)] * len(widths))


# ----------------------------------------------------------------------------- reference trainer

def reference_worker(spec):
    """Evaluator-owned stock trainer run in a separate process; prints one JSON line on stdout."""
    import torch
    import torch.nn as nn

    torch.set_num_threads(max(1, min(8, len(os.sched_getaffinity(0)))))
    p, d, heads = spec["modulus"], spec["width"], spec["n_heads"]
    task = build_task(spec["operation"], p, spec["train_fraction"], spec["seed"])

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.embed = nn.Embedding(p + 1, d)
            self.pos = nn.Parameter(torch.randn(3, d) * 0.02)
            self.qkv = nn.Linear(d, 3 * d, bias=False)
            self.proj = nn.Linear(d, d, bias=False)
            self.fc1 = nn.Linear(d, 4 * d)
            self.fc2 = nn.Linear(4 * d, d)
            self.unembed = nn.Linear(d, p, bias=False)
            nn.init.normal_(self.embed.weight, std=1.0 / math.sqrt(d))

        def forward(self, x):
            z = self.embed(x) + self.pos
            b, t, dd = z.shape
            q, k, v = self.qkv(z).view(b, t, 3, heads, dd // heads).permute(2, 0, 3, 1, 4)
            a = nn.functional.scaled_dot_product_attention(q, k, v).transpose(1, 2).reshape(b, t, dd)
            z = z + self.proj(a)
            z = z + self.fc2(torch.relu(self.fc1(z)))
            return self.unembed(z[:, -1])

    torch.manual_seed(spec["seed"])
    model = Net()
    opt = torch.optim.AdamW(model.parameters(), lr=spec["lr"], betas=tuple(spec["betas"]),
                            weight_decay=spec["weight_decay"])
    toks = np.stack([task["a"], task["b"], np.full(p * p, p)], axis=1)
    x_all = torch.from_numpy(toks.astype(np.int64))
    y_all = torch.from_numpy(task["label"].astype(np.int64))
    tr = torch.from_numpy(task["train"])
    xt, yt = x_all[tr], y_all[tr]
    train_acc, val_acc = [], []
    vi = torch.from_numpy(task["val"])
    for _ in range(spec["n_checkpoints"]):
        for _ in range(spec["probe_every"]):
            loss = nn.functional.cross_entropy(model(xt), yt)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
        with torch.no_grad():
            pred = model(x_all).argmax(-1)
        train_acc.append(float((pred[tr] == y_all[tr]).float().mean()))
        val_acc.append(float((pred[vi] == y_all[vi]).float().mean()))
    sys.stdout.write(json.dumps({"train_acc": train_acc, "val_acc": val_acc}) + "\n")
    sys.stdout.flush()


def run_reference_width(wl, seed, width, n_checkpoints, probe_every, deadline, clock):
    """Run one reference width in a killable process group; returns (curves|None, category)."""
    spec = {"modulus": wl["modulus"], "operation": wl["operation"], "train_fraction": wl["train_fraction"],
            "seed": seed, "width": width, "n_heads": wl["n_heads"], "lr": wl["lr"], "betas": wl["betas"],
            "weight_decay": wl["weight_decay"], "n_checkpoints": n_checkpoints, "probe_every": probe_every}
    env = {k: os.environ[k] for k in ("PATH", "LD_LIBRARY_PATH", "LANG", "LC_ALL", "TZ") if k in os.environ}
    env.update(HOME="/nonexistent", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.Popen([sys.executable, os.path.abspath(__file__), "--reference-worker", json.dumps(spec)],
                            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, shell=False, start_new_session=True)
    capture = BoundedWorkerStderr(proc.stderr)
    chunks = []

    def pump():
        chunks.append(proc.stdout.read(1 << 20))

    reader = threading.Thread(target=pump, daemon=True)
    reader.start()
    category = None
    try:
        remaining = deadline - clock()
        if remaining <= 0:
            category = "baseline_timeout"
        else:
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                category = "baseline_timeout"
        if category is None and proc.returncode != 0:
            category = "baseline_signal" if proc.returncode < 0 else "baseline_exit"
    finally:
        if proc.poll() is None:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass
        reader.join(timeout=2)
        snapshot = None
        try:
            snapshot = capture.close()
        except RuntimeError:
            pass
    if category is not None:
        if repair_mode() and snapshot and snapshot["stderr"]:
            print(snapshot["stderr"], file=sys.stderr, flush=True)
        return None, category
    try:
        data = json.loads(chunks[0].decode("utf-8"))
        ta, va = data["train_acc"], data["val_acc"]
        if (len(ta) != n_checkpoints or len(va) != n_checkpoints
                or not all(isinstance(v, float) and math.isfinite(v) for v in ta + va)):
            raise ValueError("bad reference output")
    except (ValueError, KeyError, IndexError, TypeError):
        return None, "baseline_result_failure"
    return {"train_acc": ta, "val_acc": va}, None


# ----------------------------------------------------------------------------- candidate transport

_RUNNER = r'''
import importlib.util, json, os, sys
path = sys.argv[1]
out = os.fdopen(os.dup(1), "w", buffering=1)
sys.stdout = sys.stderr
sys.path.insert(0, os.path.dirname(path))
spec = importlib.util.spec_from_file_location("candidate_program", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
for line in sys.stdin:
    try:
        resp = mod.handle(json.loads(line))
        text = json.dumps({"response": resp}, allow_nan=False, separators=(",", ":"))
    except BaseException:
        text = json.dumps({"error": "candidate_exception"})
    out.write(text + "\n")
'''


class NativeCandidate:
    """Untrusted candidate in a killable, resource-limited subprocess (native smoke only)."""

    def __init__(self, program_path, wall_seconds):
        self.program_path = program_path
        self.wall_seconds = wall_seconds
        self.proc = None
        self.lines = None
        self.tmp = None

    def _spawn(self):
        self.close()
        python, env = candidate_subprocess_settings(os.environ)
        env["OMP_NUM_THREADS"] = env.get("OMP_NUM_THREADS", CANDIDATE_THREADS)
        self.tmp = tempfile.TemporaryDirectory(prefix="cand-")
        self.proc = subprocess.Popen([python, "-c", _RUNNER, self.program_path], stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env,
                                     cwd=self.tmp.name, shell=False, start_new_session=True)
        limit = cpu_limit_seconds(self.wall_seconds, int(CANDIDATE_THREADS))
        try:
            resource.prlimit(self.proc.pid, resource.RLIMIT_CPU, (limit, limit))
            resource.prlimit(self.proc.pid, resource.RLIMIT_CORE, (0, 0))
        except (OSError, ValueError):
            pass
        self.lines = queue.Queue()
        proc = self.proc

        def pump():
            try:
                while True:
                    line = proc.stdout.readline(WIRE_LIMIT + 1)
                    if not line:
                        break
                    if len(line) > WIRE_LIMIT or not line.endswith(b"\n"):
                        self.lines.put(b"")
                        break
                    self.lines.put(line)
            except (OSError, ValueError):
                pass
            self.lines.put(None)

        threading.Thread(target=pump, daemon=True).start()

    def close(self):
        proc, self.proc = self.proc, None
        if proc is not None:
            for sig, wait in ((signal.SIGTERM, 2), (signal.SIGKILL, 2)):
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
                except (OSError, ValueError):
                    pass
        if self.tmp is not None:
            self.tmp.cleanup()
            self.tmp = None

    def rpc(self, request, timeout):
        if request.get("op") == "reset" or self.proc is None:
            self._spawn()
        data = bounded_json_line(request)
        deadline = time.monotonic() + timeout
        errors = []

        def send():
            try:
                self.proc.stdin.write(data)
                self.proc.stdin.flush()
            except (OSError, ValueError) as error:
                errors.append(error)

        sender = threading.Thread(target=send, daemon=True)
        sender.start()
        sender.join(timeout=max(0.0, deadline - time.monotonic()))
        if sender.is_alive():
            self.close()
            raise TimeoutError("candidate request not consumed")
        if errors:
            self.close()
            raise CandidateRpcError("candidate_exit")
        try:
            line = self.lines.get(timeout=max(0.0, deadline - time.monotonic()))
        except queue.Empty:
            self.close()
            raise TimeoutError("candidate response timeout") from None
        if line is None:
            self.close()
            raise CandidateRpcError("candidate_exit")
        try:
            msg = json.loads(line)
        except ValueError:
            self.close()
            raise CandidateProtocolError("unparseable response") from None
        if type(msg) is not dict or "response" not in msg:
            raise CandidateRpcError("candidate_exception")
        return msg["response"]


class BrokerCandidate:
    """Trusted fixed proxy loaded in-process; calls run in a thread so a timeout can be normalized."""

    def __init__(self, handle):
        self.handle = handle

    def close(self):
        pass

    def rpc(self, request, timeout):
        box = {}

        def run():
            try:
                box["response"] = self.handle(request)
            except BaseException as error:  # candidate failures are episode-level, sanitized
                box["error"] = type(error).__name__

        thread = threading.Thread(target=run, daemon=True)
        thread.start()
        thread.join(timeout=max(0.0, timeout))
        if thread.is_alive():
            raise TimeoutError("candidate response timeout")
        if "error" in box:
            raise CandidateRpcError("candidate_exception")
        return box["response"]


def make_candidate(program_path, wall_seconds):
    has_socket = bool(os.environ.get("AGENTIC_CANDIDATE_SOCKET"))
    is_proxy = program_path == BROKER_PROXY_PATH
    if has_socket != is_proxy:
        raise ValueError("brokered mode requires both the socket signal and the fixed proxy path")
    if is_proxy:
        spec = importlib.util.spec_from_file_location("candidate_proxy", program_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return BrokerCandidate(module.handle)
    return NativeCandidate(os.path.abspath(program_path), wall_seconds)


# ----------------------------------------------------------------------------- scheduler

def run_declared_episodes(
    episodes, *, hard_deadline, finish_reserve, reset_timeout, episode_overhead,
    rpc_cap, clock, rpc, evaluate, worst_case, record_failure, reset_request,
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
            except (TimeoutError, RequiredBaselineFailure, CandidateRpcError, CandidateProtocolError) as error:
                if primary_failure is None:
                    primary_failure = describe_episode_failure(error, current_operation)
                raise

        started = clock()
        try:
            timeout = min(reset_timeout, rpc_cap, work_deadline - clock())
            if timeout <= 0:
                raise TimeoutError("episode reset budget exhausted")
            require_reset_ack(rpc(reset_request(episode), timeout=timeout))
            value = evaluate(episode, call, work_deadline)
            if clock() > episode_deadline:
                raise TimeoutError("episode cleanup deadline exceeded")
            value["duration"] = float(clock() - started)
            outcomes[index] = value
        except (TimeoutError, RequiredBaselineFailure, InvalidResetResponse,
                CandidateRpcError, CandidateProtocolError) as error:
            complete = False
            failure = primary_failure or describe_episode_failure(error, current_operation)
            outcomes[index] = dict(outcomes[index], duration=float(clock() - started))
            try:
                record_failure(failure)
            except Exception:
                error.add_note("episode diagnostic recording failed")
    return outcomes, complete


# ----------------------------------------------------------------------------- evaluation

def reset_request_for(episode, wl):
    return {"op": "reset", "seed": episode["seed"], "modulus": wl["modulus"], "operation": wl["operation"],
            "d_model": episode["width"], "n_heads": wl["n_heads"], "learning_rate": wl["lr"],
            "betas": list(wl["betas"]), "weight_decay": wl["weight_decay"], "full_batch": True,
            "max_steps": wl["max_steps"]}


def build_episodes(wl, smoke):
    episodes = []
    for width in wl["widths"]:
        for seed in wl["seeds_used"]:
            episodes.append({"kind": "primary", "seed": seed, "width": width})
    cseed = wl["seeds_used"][0]
    episodes.append({"kind": "control_shuffle", "seed": cseed, "width": wl["control_width"]})
    episodes.append({"kind": "control_zero", "seed": cseed, "width": wl["control_width"]})
    return episodes


def rpc_calls_per_episode(wl):
    # reset + load_train + n_checkpoints x (train + predict); controls use the same call counts
    return 2 + 2 * wl["n_checkpoints"]


def preflight(wl, episodes, sequence, tasks):
    p = wl["modulus"]
    ntrain = len(tasks[wl["seeds_used"][0]]["train"])
    # largest request / response, fully serialized (UTF-8 JSON bytes, base64, envelope, framing)
    rows = np.zeros((ntrain, 3), dtype=np.int64)
    pairs = np.zeros((p * p, 2), dtype=np.int64)
    worst_logits = np.zeros((p * p, p), dtype="<f4")
    biggest = max(
        len(bounded_json_line({"op": "load_train", "rows": encode_int16(rows)})),
        len(bounded_json_line({"op": "predict", "pairs": encode_int16(pairs)})),
        len(bounded_json_line({"ok": True, "predictions": encode_int16(np.zeros(p * p))})),
        len(bounded_json_line({"ok": True, "logits": {"dtype": "float32", "shape": [p * p, p],
                                                      "encoding": "base64-le", "data": base64.b64encode(
                                                          worst_logits.tobytes()).decode("ascii")}})))
    if biggest >= WIRE_LIMIT:
        raise ValueError("message exceeds wire limit")
    if [e["seed"] for e in episodes] != list(sequence):
        raise ValueError("episode plan differs from the declared reset sequence")
    total = len(episodes) * rpc_calls_per_episode(wl)
    if total > MAX_RPC_CALLS:
        raise ValueError("production RPC count exceeds the declared budget")
    return total


def evaluate_episode_factory(wl, tasks, shuffle_info):
    p = wl["modulus"]
    interval = wl["probe_every"]

    def evaluate(episode, call, work_deadline):
        task = tasks[episode["seed"]]
        train = task["train"]
        labels = task["label"][train].copy()
        if episode["kind"] == "control_shuffle":
            labels = shuffle_info["labels"]
        rows = np.stack([task["a"][train], task["b"][train], labels], axis=1)
        response = call({"op": "load_train", "rows": encode_int16(rows)})
        if type(response) is not dict or response != {"ok": True}:
            raise CandidateProtocolError("bad load_train response")
        qa = task["a"][task["query"]]
        qb = task["b"][task["query"]]
        query = {"op": "predict", "pairs": encode_int16(np.stack([qa, qb], axis=1))}
        steps, train_acc, val_acc = [], [], []
        for k in range(1, wl["n_checkpoints"] + 1):
            n = 0 if episode["kind"] == "control_zero" else interval
            response = call({"op": "train", "steps": n})
            if type(response) is not dict or response != {"ok": True}:
                raise CandidateProtocolError("bad train response")
            response = call(query)
            if type(response) is not dict or set(response) != {"ok", "predictions"} or response["ok"] is not True:
                raise CandidateProtocolError("bad predict response")
            preds = decode_predictions(response["predictions"], p * p, p)
            tr, va = accuracy_curves(task, preds)
            steps.append(k * interval)
            train_acc.append(tr)
            val_acc.append(va)
        out = make_outcome(steps, train_acc, val_acc, wl, 0.0)
        out["curve"] = (steps, train_acc, val_acc)
        return out

    return evaluate


def write_results(results_dir, metrics, correct, evidence, feasible, qualification):
    os.makedirs(results_dir, exist_ok=True)

    def dump(name, obj):
        with open(os.path.join(results_dir, name), "w", encoding="utf-8") as handle:
            json.dump(obj, handle, allow_nan=False)

    dump("metrics.json", metrics)
    dump("correct.json", {"correct": bool(correct)})
    if evidence is not None:
        dump("evaluation_evidence.json", {"schema_version": 1, "episodes": evidence})
    if qualification:
        dump("qualification.json", {"schema_version": 1, "feasible": bool(feasible)})


def seed_evidence(episodes, outcomes, passed):
    """One record per seed: mean primary score, all-episodes-valid flag, summed measured duration."""
    records = []
    for seed in dict.fromkeys(e["seed"] for e in episodes):
        idx = [i for i, e in enumerate(episodes) if e["seed"] == seed]
        prim = [outcomes[i]["score"] for i in idx if episodes[i]["kind"] == "primary"]
        records.append({"seed": int(seed),
                        "score": float(sum(prim) / len(prim)) if prim else 0.0,
                        "correct": bool(all(passed[i] for i in idx)),
                        "duration_seconds": float(sum(outcomes[i]["duration"] for i in idx))})
    return records


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if argv and argv[0] == "--reference-worker":
        try:
            reference_worker(json.loads(argv[1]))
        except Exception as error:
            if repair_mode():
                report_worker_exception(error)
            else:
                print("worker_failure", file=sys.stderr)
            raise SystemExit(1)
        return 0
    started = time.monotonic()
    parser = argparse.ArgumentParser()
    parser.add_argument("--program_path", required=True)
    parser.add_argument("--results_dir", required=True)
    args = parser.parse_args(argv)
    smoke = os.environ.get("AGENTIC_TASK_DRAFT_SMOKE") == "1"
    qualification = os.environ.get("AGENTIC_TASK_QUALIFICATION") == "1"
    try:
        result = run_plane(args.program_path, started, smoke)
    except FatalOperationalError:
        emit_search_line("search_fatal category=operational_failure")
        result = fatal_result(started, smoke)
    except Exception as error:
        name = type(error).__name__
        text = f"evaluator_error type={name}"
        if PLANE == "search":
            text += " message=" + str(error)[:160].replace("\n", " ")
        print(text[:256], file=sys.stderr, flush=True)
        return 1
    write_results(args.results_dir, result["metrics"], result["correct"], result["evidence"],
                  result["feasible"] and not smoke, qualification)
    return 0


def run_plane(program_path, started, smoke):
    root = os.path.join(os.environ.get("TASK_SOURCE_DIR") or os.path.dirname(os.path.abspath(__file__)),
                        "resources", PLANE)
    wl = workload_from_manifest(root, smoke)
    wl["seeds_used"] = [PRIMARY_SEEDS[0]] if smoke else list(PRIMARY_SEEDS)
    if not smoke and sorted(wl["seeds"]) != sorted(PRIMARY_SEEDS):
        raise ValueError("manifest seeds differ from the declared protocol")
    sequence = SMOKE_RESET_SEQUENCE if smoke else RESET_SEQUENCE
    tasks = {}
    for seed in wl["seeds_used"]:
        task = build_task(wl["operation"], wl["modulus"], wl["train_fraction"], seed)
        check_split(wl["operation"], task)
        if split_digest(task) != wl["digests"][str(seed)]:
            raise ValueError("split manifest digest mismatch")
        tasks[seed] = task
    episodes = build_episodes(wl, smoke)
    total_rpc = preflight(wl, episodes, sequence, tasks)
    ctrl_task = tasks[wl["seeds_used"][0]]
    shuffled, changed = shuffled_labels(ctrl_task["label"][ctrl_task["train"]], wl["seeds_used"][0],
                                        wl["modulus"], MIN_CHANGED_FRACTION)
    shuffle_info = {"labels": shuffled, "changed": changed}
    if changed < MIN_CHANGED_FRACTION or np.array_equal(shuffled, ctrl_task["label"][ctrl_task["train"]]):
        raise ValueError("vacuous control")
    est = sum(wl["max_steps"] * SEC_PER_STEP_ESTIMATE.get(e["width"], 0.35)
              for e in episodes if e["kind"] != "control_zero") / len(episodes)
    reference_reserve = REFERENCE_RESERVE
    require_joint_workload_budget(profile={
        "episode_count": len(episodes), "method_count": 1, "wall_seconds": WALL_CLOCK_SECONDS,
        "startup_seconds": STARTUP_ALLOWANCE, "reset_seconds": 30.0, "cleanup_seconds": EPISODE_OVERHEAD,
        "finish_seconds": FINISH_RESERVE + reference_reserve, "work_seconds": max(est, 1.0)})
    hard_deadline = started + WALL_CLOCK_SECONDS - STARTUP_ALLOWANCE
    clock = time.monotonic

    baseline_failures = []

    def record_baseline(category):
        baseline_failures.append(category)
        emit_search_line(f"search_baseline_failure category={category}")

    # trivial baselines (evaluator-owned sanity of the split): chance, majority, train lookup table
    task0 = ctrl_task
    p = wl["modulus"]
    lookup_val = float(np.mean(task0["label"][task0["val"]] == np.bincount(
        task0["label"][task0["train"]], minlength=p).argmax()))
    if 1.0 / p > 0.5 or lookup_val > CONTROL_VAL_CEILING + 0.05:
        raise ValueError("trivial baselines unexpectedly strong; split is not usable")
    # cheap early sanity run of the reference trainer (tiny workload, same code path)
    sanity_wl = dict(wl, modulus=13)
    _, category = run_reference_width(sanity_wl, 1, 16, 1, 5, min(hard_deadline - FINISH_RESERVE, clock() + 120), clock)
    if category is not None:
        record_baseline(category)

    candidate = make_candidate(program_path, WALL_CLOCK_SECONDS)
    rpc_count = 0
    reset_log = []

    def rpc(request, timeout):
        nonlocal rpc_count
        if rpc_count >= MAX_RPC_CALLS:
            raise FatalOperationalError("rpc budget exhausted")
        rpc_count += 1
        if request.get("op") == "reset":
            reset_log.append(request["seed"])
        try:
            bounded_json_line(request)
            response = candidate.rpc(request, timeout)
            bounded_json_line(response)
        except ValueError:
            raise CandidateProtocolError("non-json or oversized response") from None
        return response

    def record_failure(failure):
        emit_search_line("search_episode_failure component=%s category=%s operation=%s" % (
            failure["component"], failure["category"], failure["operation"]))

    evaluate = evaluate_episode_factory(wl, tasks, shuffle_info)
    try:
        outcomes, complete = run_declared_episodes(
            episodes, hard_deadline=hard_deadline - reference_reserve, finish_reserve=FINISH_RESERVE,
            reset_timeout=RESET_TIMEOUT, episode_overhead=EPISODE_OVERHEAD, rpc_cap=RPC_TIMEOUT_CAP,
            clock=clock, rpc=rpc, evaluate=evaluate, worst_case=lambda e: worst_case_outcome(e, wl),
            record_failure=record_failure, reset_request=lambda e: reset_request_for(e, wl))
    finally:
        candidate.close()
    if reset_log != list(sequence):
        complete = False
    reference = run_reference_plan(wl, hard_deadline - FINISH_RESERVE, clock, baseline_failures, record_baseline)
    return aggregate_plane(wl, episodes, outcomes, complete, reference, baseline_failures,
                           clock() - started, hard_deadline, total_rpc, rpc_count, reset_log, sequence)


if __name__ == "__main__":
    sys.exit(main())
