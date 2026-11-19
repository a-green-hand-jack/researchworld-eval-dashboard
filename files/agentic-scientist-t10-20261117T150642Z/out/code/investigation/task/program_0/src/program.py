"""CPU-only frozen-predictor mean interval; finite JSON RPC v1.

All request/response fields below are mandatory; extra fields are forbidden.
reset {op:"reset",seed:int} -> {ok:true}: clears buffers, fit and RNG. Accept
any nonnegative signed-64-bit seed; seeds do not identify workloads or planes.
update/start {op:"update",phase:"start",n:int,N:int,alpha:0.05,
 label_kind:"bernoulli"|"real",dtype:"<f8",encoding:"base64",shape:[2*n+N],
 total_bytes:8*(2*n+N),chunks:ceil(total_bytes/1048576)} ->
 {ok:true,transfer_id:str}. n,N>=8; logical input <=8 MiB, at most 8 chunks.
update/chunk {op:"update",phase:"chunk",transfer_id:str,index:int,data:str}
 -> {ok:true}. data is standard base64; indices must be sequential from zero.
 Decoded chunks are 1 MiB except the last. The ID is an opaque memory token,
 1..64 ASCII alphanumeric/underscore characters, never a filename or path.
update/commit {op:"update",phase:"commit",transfer_id:str} -> {ok:true}.
 Assembled little-endian float64 array contains y[n], p[n], u[N]: labeled
 outcomes, their frozen predictions, then unlabeled frozen predictions. Values
 must be finite; Bernoulli y is 0/1. Fits once and releases transfer buffers.
infer {op:"infer"} -> {lower:float,upper:float}. Endpoints and their width must
 be finite and ordered, within [0,1] for Bernoulli. Repeated infer is identical.

One reset, one start, 1..8 chunks, one commit, two infer calls per episode.
Only one transaction per reset. Workload shape/outcome type is supplied by
start, never inferred from seeds. All responses <=64 KiB; complete JSON lines
must be <64 MiB. No paths, private targets, population labels, baseline outputs,
extra labels, predictor retraining, or cross-episode state are permitted.
Constant scores require label-only fallback. Matched score interventions and
one trailing reset replay are evaluator-owned controls, not self-report gates.

Starter: degree-two ridge control variates with two-fold held-out residuals;
constant/rare inputs fall back to label-only (Clopper-Pearson for Bernoulli,
Student t otherwise). The cross-fit plug-in variance is only an asymptotic
proposal: fold dependence and selection need further theory and experiments.
This code makes no finite-sample coverage/novelty claim. Supported negative
results remain eligible. Publication still needs the task's complete paper,
official latest conference template/checklist, actual repeated-run uncertainty,
allowed consulted references, code and truthful failure/reproduction report.
"""

import base64
import math

import numpy as np
from scipy.stats import beta, t


_state = None


def _keys(value, expected):
    if type(value) is not dict or set(value) != set(expected.split()):
        raise ValueError("invalid fields")


def _label_only(outcomes, kind, alpha):
    count = len(outcomes)
    if kind == "bernoulli":
        successes = int(outcomes.sum())
        lower = 0.0 if successes == 0 else beta.ppf(alpha / 2, successes, count - successes + 1)
        upper = 1.0 if successes == count else beta.ppf(1 - alpha / 2, successes + 1, count - successes)
    else:
        radius = t.ppf(1 - alpha / 2, count - 1) * outcomes.std(ddof=1) / math.sqrt(count)
        lower, upper = outcomes.mean() - radius, outcomes.mean() + radius
    return {"lower": float(lower), "upper": float(upper)}


def _fit(values, settings):
    count, unlab_count = settings["n"], settings["N"]
    outcomes, predictions, unlab = np.split(values, [count, 2 * count])
    if not np.isfinite(values).all() or len(unlab) != unlab_count:
        raise ValueError("invalid values")
    kind, alpha = settings["label_kind"], settings["alpha"]
    if kind == "bernoulli" and not np.isin(outcomes, [0, 1]).all():
        raise ValueError("invalid outcomes")
    scale = float(unlab.std())
    if scale < 1e-12 or predictions.std() < 1e-12 or (
        kind == "bernoulli" and min(outcomes.sum(), count - outcomes.sum()) < 10
    ):
        return _label_only(outcomes, kind, alpha)
    location = unlab.mean()
    scores, unlab_scores = (predictions - location) / scale, (unlab - location) / scale
    features = np.column_stack([scores, scores**2])
    unlab_features = np.column_stack([unlab_scores, unlab_scores**2])
    order = _state["rng"].permutation(count)
    residuals, averaged_unlab = np.empty(count), np.zeros(unlab_count)
    for held in (order[: count // 2], order[count // 2 :]):
        train = np.setdiff1d(np.arange(count), held)
        design = features[train] - features[train].mean(axis=0)
        centered = outcomes[train] - outcomes[train].mean()
        coefficients = np.linalg.solve(design.T @ design + 0.1 * np.eye(2), design.T @ centered)
        residuals[held] = outcomes[held] - features[held] @ coefficients
        averaged_unlab += (len(held) / count) * (unlab_features @ coefficients)
    center = residuals.mean() + averaged_unlab.mean()
    variance = residuals.var(ddof=1) / count + averaged_unlab.var(ddof=1) / unlab_count
    radius = t.ppf(1 - alpha / 2, max(2, count // 2 - 3)) * math.sqrt(variance)
    lower, upper = float(center - radius), float(center + radius)
    if kind == "bernoulli":
        lower, upper = max(0.0, lower), min(1.0, upper)
    return {"lower": lower, "upper": upper}


def handle(request):
    """Dispatch the exact reset/update/infer protocol in the module docstring."""
    global _state
    if type(request) is not dict:
        raise ValueError("invalid request")
    operation = request.get("op")
    if operation == "reset":
        _keys(request, "op seed")
        seed = request["seed"]
        if type(seed) is not int or not 0 <= seed < 2**63:
            raise ValueError("invalid seed")
        _state = {"rng": np.random.default_rng(seed), "phase": "reset"}
        return {"ok": True}
    if _state is None:
        raise ValueError("reset required")
    if operation == "infer":
        _keys(request, "op")
        if _state["phase"] != "fitted":
            raise ValueError("commit required")
        return dict(_state["interval"])
    if operation != "update":
        raise ValueError("unsupported operation")
    phase = request.get("phase")
    if phase == "start":
        _keys(request, "op phase n N alpha label_kind dtype encoding shape total_bytes chunks")
        count, unlab_count = request["n"], request["N"]
        if any(type(value) is not int or value < 8 for value in (count, unlab_count)):
            raise ValueError("invalid shape")
        length = 8 * (2 * count + unlab_count)
        if (_state["phase"] != "reset" or length > 8 * 1024**2
                or request["dtype"] != "<f8" or request["encoding"] != "base64"
                or request["shape"] != [2 * count + unlab_count]
                or type(request["total_bytes"]) is not int or request["total_bytes"] != length
                or type(request["chunks"]) is not int or request["chunks"] != math.ceil(length / 1024**2)
                or type(request["alpha"]) not in (int, float) or request["alpha"] != 0.05
                or request["label_kind"] not in ("bernoulli", "real")):
            raise ValueError("invalid transfer")
        _state.update(phase="buffer", settings=dict(request), buffer=bytearray(), next_index=0)
        return {"ok": True, "transfer_id": "buffer"}
    if _state["phase"] != "buffer" or request.get("transfer_id") != "buffer":
        raise ValueError("invalid transfer state")
    if phase == "chunk":
        _keys(request, "op phase transfer_id index data")
        index, settings = request["index"], _state["settings"]
        if type(index) is not int or index != _state["next_index"] or index >= settings["chunks"]:
            raise ValueError("invalid index")
        if type(request["data"]) is not str or len(request["data"]) > 1398104:
            raise ValueError("invalid base64")
        decoded = base64.b64decode(request["data"], validate=True)
        expected = min(1024**2, settings["total_bytes"] - len(_state["buffer"]))
        if len(decoded) != expected:
            raise ValueError("invalid chunk length")
        _state["buffer"].extend(decoded)
        _state["next_index"] += 1
        return {"ok": True}
    if phase == "commit":
        _keys(request, "op phase transfer_id")
        settings = _state["settings"]
        if len(_state["buffer"]) != settings["total_bytes"] or _state["next_index"] != settings["chunks"]:
            raise ValueError("incomplete transfer")
        interval = _fit(np.frombuffer(_state["buffer"], dtype="<f8"), settings)
        _state.pop("buffer")
        _state.pop("settings")
        _state.update(phase="fitted", interval=interval)
        return {"ok": True}
    raise ValueError("invalid phase")
