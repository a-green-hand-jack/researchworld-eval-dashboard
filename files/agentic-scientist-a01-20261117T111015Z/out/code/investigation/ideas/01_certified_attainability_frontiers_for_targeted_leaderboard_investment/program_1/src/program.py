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

This candidate exhausts <=6-column panels and uses an order-statistic dominance
bound on larger panels. The bound relies on a COMMON alpha and the stated
headroom response, not arbitrary task-specific ceilings. It covers conventional
even medians as well as odd medians and the documented trimmed mean. Every
returned winning support is checked after saturation. Unattainability is checked
with all tasks changed; near floating-point certificate boundaries the status
stays bounded. Support is not a measured training cost or a causal effect.

The interface has no Borda rule, adjustable winning margin, data-download or
paper-export operation. Those parts of the research idea are not implemented;
only supplied matrices, task identities, and documented decisions are used.
"""
import base64
import hashlib
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


def aggregate_rows(values, rule):
    if rule == "mean":
        return np.mean(values, axis=1)
    if rule == "median":
        return np.median(values, axis=1)
    trim = values.shape[1] // 5
    return np.mean(np.sort(values, axis=1)[:, trim:values.shape[1]-trim], axis=1)


def saturated_scores(target_scores, selected_tasks, response_cap):
    attacked_scores = target_scores.copy()
    selected_tasks = list(selected_tasks)
    attacked_scores[selected_tasks] = target_scores[selected_tasks] + response_cap * (1.0 - target_scores[selected_tasks])
    return attacked_scores


def verify_winning_support(score_matrix, target_index, selected_tasks, response_cap, rule, required_margin):
    """Recompute the witness on the actual panel, with all rivals unchanged."""
    selected_tasks = list(selected_tasks)
    if len(set(selected_tasks)) != len(selected_tasks):
        return False
    if any(index < 0 or index >= score_matrix.shape[1] for index in selected_tasks):
        return False
    attacked_scores = saturated_scores(score_matrix[target_index], selected_tasks, response_cap)
    rival_scores = np.delete(aggregate_rows(score_matrix, rule), target_index)
    return aggregate(attacked_scores, rule) > float(np.max(rival_scores)) + required_margin


def trim_count(task_count, rule):
    if rule == "mean":
        return 0
    if rule == "median":
        return (task_count - 1) // 2
    return task_count // 5


def dominant_support_order(target_scores, task_ids, columns, rule):
    """Return prefixes maximizing the aggregate at each support budget.

    Write the rule as the mean of middle n-2r order statistics. For median,
    r=floor((n-1)/2), retaining TWO values for even n. Sort the baseline x.
    With f(x)=x+alpha*(1-x), f is increasing and f(x)-x is decreasing.

    First, an optimum never needs to change the r smallest baseline scores.
    If a changed index a<r exists, exchange it with the smallest unchanged
    index b>=r. All intervening indices >=r are changed and have f(x)>=f(x_a).
    If f(x_a)<=x_b, a is among the bottom r: undoing its uplift costs nothing.
    Otherwise b is among the bottom r, and the exchange replaces the pair
    (x_b,f(x_a)) by (x_a,f(x_b)): only an ignored low value falls, while the
    high value rises. Neither case decreases the middle sum. For k>n-r,
    changing every index >=r already achieves the full-support aggregate.

    Fixing these bottom r scores leaves the sum of the smallest n-2r values
    in the remaining n-r. If a<b are eligible and only b is changed, changing
    a instead replaces (x_a,f(x_b)) by (f(x_a),x_b). Both the minimum and the
    total of this pair weakly increase. Consequently every lower partial sum
    of the full vector weakly increases, even after adjoining other scores.
    Repeated exchanges give the prefix r,...,r+k-1. Thus its value is also a
    full-panel upper bound for EVERY support of size at most k. This proof
    does not apply to arbitrary response caps, task weights or Borda ranks.
    """
    ordered = sorted(range(len(columns)), key=lambda index: (target_scores[index], task_ids[columns[index]]))
    return ordered[trim_count(len(columns), rule):]


def exhaustive_support(target_scores, task_ids, columns, response_cap, rule, threshold):
    """Audit every support on the small panels allowed by the RPC contract."""
    task_count = len(columns)
    ordered = sorted(range(task_count), key=lambda index: task_ids[columns[index]])
    best = None
    minimum_task_budget = np.inf
    for subset_mask in range(1 << task_count):
        selected_tasks = [ordered[position] for position in range(task_count) if subset_mask & (1 << position)]
        if len(selected_tasks) >= minimum_task_budget:
            continue
        attacked_scores = saturated_scores(target_scores, selected_tasks, response_cap)
        if aggregate(attacked_scores, rule) > threshold:
            best = selected_tasks
            minimum_task_budget = len(selected_tasks)
    return best


def solve(matrix, task_ids, decision):
    columns = decision["columns"]
    values = matrix[:, columns]
    target = decision["target"]
    rule = decision["rule"]
    alpha = decision["alpha"]
    target_values = values[target].copy()
    rivals = np.delete(aggregate_rows(values, rule), target)
    threshold = float(np.max(rivals)) + TOLERANCE

    def wins(selected):
        return aggregate(saturated_scores(target_values, selected, alpha), rule) > threshold

    size = len(columns)
    result = {"id": decision["id"], "selected": [], "status": "bounded", "lower_bound": 0}
    if wins([]):
        result.update(status="optimal")
        return result
    if not wins(list(range(size))):
        result.update(status="infeasible", lower_bound=size+1)
        return result

    order = dominant_support_order(target_values, task_ids, columns, rule)
    selected_tasks = []
    lower_bound = 1
    roundoff_guard = 32 * np.finfo(np.float64).eps * max(1, size)
    for count, index in enumerate(order, start=1):
        selected_tasks.append(index)
        frontier_value = aggregate(saturated_scores(target_values, selected_tasks, alpha), rule)
        if frontier_value > threshold:
            break
        if frontier_value + roundoff_guard <= threshold:
            lower_bound = count + 1

    if size <= 6:
        audited_tasks = exhaustive_support(target_values, task_ids, columns, alpha, rule, threshold)
        if audited_tasks is not None:
            selected_tasks = audited_tasks
            lower_bound = len(audited_tasks)

    if not wins(selected_tasks):
        selected_tasks = list(range(size))
        for index in sorted(selected_tasks, key=lambda index: task_ids[columns[index]]):
            trial = [chosen for chosen in selected_tasks if chosen != index]
            if wins(trial):
                selected_tasks = trial

    witness_verified = verify_winning_support(values, target, selected_tasks, alpha, rule, TOLERANCE)
    if not witness_verified:
        return result
    lower_bound = min(lower_bound, len(selected_tasks))
    result.update(selected=[columns[index] for index in selected_tasks], lower_bound=lower_bound)
    if lower_bound == len(selected_tasks):
        result["status"] = "optimal"
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
