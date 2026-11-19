"""Deterministic CPU counterfactual support solver, exposed only through handle.

Native smoke copies this entrypoint only; keep source self-contained apart from
installed packages. All requests/responses are finite JSON objects; additional response fields are
forbidden. Each episode starts reset(seed: nonnegative integer), response
{"ok": true}; any valid seed is supported and never chooses a workload. Reset
clears uploaded values, results and all RNG state. No training is performed.

upload accepts index (0-based integer), total (1..64), total_bytes (1..67108864),
shape ([number of float64 values]), dtype="float64", byte_order="little",
encoding="base64", length (decoded bytes <=1048576), sha256 (chunk hex digest),
and data (base64 string). Chunks must arrive in index order; upload index zero
starts candidate-owned in-memory transfer. Response: {"ok": true}. The logical
value is concatenated little-endian float64 matrices, never a shared file.

run accepts matrices: list of {key: string, shape:[rows, columns], offset: byte
integer, task_ids: unique strings}, and decisions: list of {id: string,
matrix: key, target: row integer, columns: unique column integers, rule:
"mean"|"median"|"trimmed", alpha: float in [0,1], node_budget: positive integer}.
At most 432 decisions, 10000 rows and 100 columns per matrix. Inputs are public
scores in [0,1]; target and rivals are all visible. Only the target may change:
x[j] becomes x[j]+alpha*(1-x[j]) on selected columns. Rivals are fixed. Columns
list the intervention/aggregation panel; selected indices are ORIGINAL matrix
column indices, not positions in that list. Strict first means aggregate exceeds
all rivals by >1e-10. All tasks have equal weight; trimmed drops floor(0.2*m)
values from EACH end; even median averages the two middle values. Task IDs have
semantic identity under joint permutations. Seeds are RNG initialization only.
node_budget is advisory; external wall and RPC limits are enforced independently.
run also accepts work_seconds: positive finite seconds remaining in the matched
method reservation after uploads. It is plane-independent, excludes no transport
or output cost, and is a snapshot, not an extension of the enforced deadline.
Solvers may divide it across the supplied decisions and reserve output time;
never infer workload or evaluation identity from a seed.

run response is {"chunks": integer 1..16, "total_bytes": integer 1..16777216,
"sha256": hex digest}. Results are UTF-8 JSON {"plans": list} in decision order.
Each plan has EXACT keys id, selected (unique column integers), status
("bounded", "optimal", or "infeasible"), lower_bound (integer 0..m+1).
No candidate scores, internal state claims or diagnostics are accepted. Bounded
plans can be non-winning, including empty, with conservative lower_bound=0;
this reports an unresolved interval, not infeasibility. Optimal claims need an
independently verifiable certificate: conservative full-panel reference bounds
or exhaustive <=6-column audit. Infeasible means even all allowed uplifts cannot
win, uses selected=[] and lower_bound=m+1. Do not claim unverified exactness.

read(index: output chunk integer) returns EXACT {index, encoding:"base64",
length: decoded byte integer <=1048576, sha256: hex digest, data: base64}.
All complete JSON messages, including framing, must be strictly below 64 MiB.
release() clears transfer/results and returns {"ok":true}. No export/import of
hidden solver state exists. Sequence: reset, 1..64 uploads, run, 1..16 reads,
release. Maximum 83 calls per episode. There are no filesystem RPC fields.

This starter exhausts <=6-column panels, solves mean via sorted headroom, and
uses deterministic marginal-score greedy for larger median/trimmed panels.
These are transparent reference choices, not claims of novel optimization or
real training effects. Improve the actual solver, not method-name aliases.
"""
import base64
import hashlib
import itertools
import json
import math
import random

import numpy as np

_state = {}
TOLERANCE = 1e-10
CHUNK_BYTES = 1048576


def aggregate(values, rule):
    if rule == "mean":
        return float(np.mean(values))
    ordered = np.sort(values)
    if rule == "median":
        return float(np.median(ordered))
    trim = len(ordered) // 5
    return float(np.mean(ordered[trim:len(ordered)-trim]))


def solve(matrix, task_ids, decision):
    columns = decision["columns"]
    values = matrix[:, columns]
    target = decision["target"]
    rule = decision["rule"]
    alpha = decision["alpha"]
    target_values = values[target].copy()
    rival_values = np.delete(values, target, axis=0)
    if rule == "mean":
        rivals = np.mean(rival_values, axis=1)
    elif rule == "median":
        rivals = np.median(rival_values, axis=1)
    else:
        trim = values.shape[1] // 5
        rivals = np.mean(np.sort(rival_values, axis=1)[:, trim:values.shape[1]-trim], axis=1)
    threshold = float(np.max(rivals)) + TOLERANCE
    def wins(selected):
        updated = target_values.copy()
        updated[selected] += alpha * (1-updated[selected])
        return aggregate(updated, rule) > threshold
    size = len(columns)
    result = {"id": decision["id"], "selected": [], "status": "bounded", "lower_bound": 0}
    if not wins(list(range(size))):
        result.update(status="infeasible", lower_bound=size+1)
        return result
    ordered = sorted(range(size), key=lambda index: task_ids[columns[index]])
    if size <= 6:
        for count in range(size+1):
            for selected in itertools.combinations(ordered, count):
                if wins(list(selected)):
                    result.update(selected=[columns[index] for index in selected], status="optimal", lower_bound=count)
                    return result
    if rule == "mean":
        order = sorted(range(size), key=lambda index: (-(1-target_values[index]), task_ids[columns[index]]))
        selected = []
        for index in order:
            if wins(selected):
                break
            selected.append(index)
        result.update(selected=[columns[index] for index in selected], status="optimal", lower_bound=len(selected))
        return result
    selected = []
    current = target_values.copy()
    while not wins(selected):
        available = [index for index in ordered if index not in selected]
        def key(index):
            trial = current.copy()
            trial[index] += alpha * (1-trial[index])
            return (-aggregate(trial, rule), task_ids[columns[index]])
        index = min(available, key=key)
        selected.append(index)
        current[index] += alpha * (1-current[index])
    result["selected"] = [columns[index] for index in selected]
    return result


def handle(request):
    operation = request["op"]
    if operation == "reset":
        seed = request["seed"]
        if type(seed) is not int or seed < 0:
            raise ValueError("invalid seed")
        _state.clear()
        _state.update(seed=seed, chunks=[], output=None)
        random.seed(seed)
        return {"ok": True}
    if operation == "upload":
        index, total = request["index"], request["total"]
        if request["dtype"] != "float64" or request["byte_order"] != "little" or request["encoding"] != "base64":
            raise ValueError("invalid encoding")
        if not 1 <= total <= 64 or not 1 <= request["total_bytes"] <= 64*CHUNK_BYTES:
            raise ValueError("invalid transfer bound")
        data = base64.b64decode(request["data"], validate=True)
        if len(data) != request["length"] or len(data) > CHUNK_BYTES or hashlib.sha256(data).hexdigest() != request["sha256"]:
            raise ValueError("invalid chunk")
        if index == 0:
            _state["chunks"] = []
            _state["transfer"] = (total, request["total_bytes"], request["shape"])
        if index != len(_state["chunks"]) or _state["transfer"] != (total, request["total_bytes"], request["shape"]):
            raise ValueError("invalid chunk order")
        _state["chunks"].append(data)
        return {"ok": True}
    if operation == "run":
        work_seconds = request["work_seconds"]
        if type(work_seconds) not in (int, float) or not math.isfinite(work_seconds) or work_seconds <= 0:
            raise ValueError("invalid work budget")
        total, total_bytes, shape = _state["transfer"]
        blob = b"".join(_state["chunks"])
        if len(_state["chunks"]) != total or len(blob) != total_bytes or shape != [total_bytes//8] or total_bytes % 8:
            raise ValueError("incomplete transfer")
        matrices = {}
        for specification in request["matrices"]:
            rows, columns = specification["shape"]
            if not 2 <= rows <= 10000 or not 1 <= columns <= 100:
                raise ValueError("invalid matrix dimensions")
            matrix = np.frombuffer(blob, dtype="<f8", count=rows*columns, offset=specification["offset"]).reshape(rows, columns)
            if not np.all(np.isfinite(matrix)) or np.any(matrix < 0) or np.any(matrix > 1):
                raise ValueError("invalid scores")
            matrices[specification["key"]] = (matrix, specification["task_ids"])
        if not 1 <= len(request["decisions"]) <= 432:
            raise ValueError("invalid decision count")
        plans = [solve(*matrices[decision["matrix"]], decision) for decision in request["decisions"]]
        output = json.dumps({"plans": plans}, allow_nan=False, separators=(",", ":")).encode()
        if not 1 <= len(output) <= 16*CHUNK_BYTES:
            raise ValueError("output too large")
        _state["output"] = output
        return {"chunks": math.ceil(len(output)/CHUNK_BYTES), "total_bytes": len(output), "sha256": hashlib.sha256(output).hexdigest()}
    if operation == "read":
        index = request["index"]
        output = _state["output"]
        if type(index) is not int or not 0 <= index < math.ceil(len(output)/CHUNK_BYTES):
            raise ValueError("invalid output index")
        data = output[index*CHUNK_BYTES:(index+1)*CHUNK_BYTES]
        return {"index": index, "encoding": "base64", "length": len(data), "sha256": hashlib.sha256(data).hexdigest(), "data": base64.b64encode(data).decode("ascii")}
    if operation == "release":
        seed = _state["seed"]
        _state.clear()
        _state["seed"] = seed
        return {"ok": True}
    raise ValueError("unknown operation")
