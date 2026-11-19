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

Panel statistics are shared within each run. Full-panel rank-window bounds
certify lower budgets; all reported witnesses are checked directly. Small
panels are exhaustive, and larger unresolved panels receive deadline-limited
deterministic refinement. These counterfactuals are not training measurements.
"""
import base64
import hashlib
import json
import math
import random
import time

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


def retained_indices(task_count, rule):
    if rule == "mean":
        return np.arange(task_count)
    if rule == "median":
        return np.arange((task_count - 1) // 2, task_count // 2 + 1)
    trim = task_count // 5
    return np.arange(trim, task_count - trim)


def rank_bound(baseline_sorted, uplifted_sorted, retained_ranks, task_budget):
    task_count = len(baseline_sorted)
    extended_baseline = np.concatenate((baseline_sorted, [np.inf]))
    rank_upper = np.minimum(uplifted_sorted[retained_ranks], extended_baseline[np.minimum(retained_ranks + task_budget, task_count)])
    optimistic_aggregate = float(np.mean(rank_upper))
    return optimistic_aggregate


def attacked_values(context, selected_local):
    attacked_scores = context["target_values"].copy()
    attacked_scores[selected_local] += context["alpha"] * (1.0 - attacked_scores[selected_local])
    return attacked_scores


def winning(context, selected_local):
    return aggregate(attacked_values(context, selected_local), context["rule"]) > context["threshold"] + context["guard"]


def publish(context):
    result = context["result"]
    selected_local = context["best"]
    attacked_scores = attacked_values(context, selected_local)
    rule = context["rule"]
    rival_max = context["rival_max"]
    lower_bound = result["lower_bound"]
    panel_columns = context["panel_columns"]
    verified_win = aggregate(attacked_scores, rule) > rival_max + 1e-10
    if not verified_win or not winning(context, selected_local):
        result.update(selected=[], status="bounded")
        return
    selected_original = [panel_columns[index] for index in selected_local]
    result.update(selected=selected_original, status="bounded")
    if verified_win and lower_bound == len(selected_local):
        result["status"] = "optimal"


def consider(context, selected_local):
    selected_local = sorted(selected_local, key=lambda index: context["task_ids"][context["panel_columns"][index]])
    if len(selected_local) < len(context["best"]) and winning(context, selected_local):
        context["best"] = selected_local
        publish(context)


def prefix_witness(context, order):
    lower = context["result"]["lower_bound"]
    upper = min(len(order), len(context["best"]) - 1)
    if upper < lower or not winning(context, order[:upper]):
        return
    while lower < upper:
        middle = (lower + upper) // 2
        if winning(context, order[:middle]):
            upper = middle
        else:
            lower = middle + 1
    consider(context, order[:upper])


def solve(matrix, task_ids, decision, panel_cache, statistics_cache, search_deadline):
    result = {"id": decision["id"], "selected": [], "status": "bounded", "lower_bound": 0}
    if time.monotonic() >= search_deadline:
        return result, None
    columns = decision["columns"]
    panel_columns = sorted(columns)
    matrix_key = decision["matrix"]
    rule = decision["rule"]
    task_count = len(panel_columns)
    retained_ranks = retained_indices(task_count, rule)
    panel_key = (matrix_key, tuple(sorted(columns)), rule)
    if panel_key not in panel_cache:
        panel_cache[panel_key] = np.sort(matrix[:, panel_columns], axis=1)
        rows = panel_cache[panel_key]
        row_aggregates = np.mean(rows[:, retained_ranks], axis=1)
        largest_row = int(np.argmax(row_aggregates))
        largest_value = float(row_aggregates[largest_row])
        other_aggregates = row_aggregates.copy()
        other_aggregates[largest_row] = -np.inf
        second_value = float(np.max(other_aggregates))
        statistics_cache[panel_key] = (largest_row, largest_value, second_value)
    largest_row, largest_value, second_value = statistics_cache[panel_key]
    target = decision["target"]
    rival_max = second_value if target == largest_row else largest_value
    target_values = matrix[target, panel_columns].copy()
    alpha = decision["alpha"]
    baseline_sorted = panel_cache[panel_key][target]
    uplifted_sorted = np.sort(target_values + alpha * (1.0 - target_values))
    threshold = rival_max + TOLERANCE
    guard = 32.0 * np.finfo(np.float64).eps * (task_count + 1)
    full_value = aggregate(target_values + alpha * (1.0 - target_values), rule)
    if full_value < threshold - guard:
        result.update(status="infeasible", lower_bound=task_count + 1)
        return result, None
    ordered = sorted(range(task_count), key=lambda index: (target_values[index], task_ids[panel_columns[index]]))
    semantic_order = sorted(range(task_count), key=lambda index: task_ids[panel_columns[index]])
    context = dict(result=result, target_values=target_values, alpha=alpha, rule=rule,
                   threshold=threshold, rival_max=rival_max, guard=guard,
                   task_ids=task_ids, panel_columns=panel_columns,
                   retained_ranks=retained_ranks, ordered=ordered,
                   semantic_order=semantic_order, best=semantic_order.copy(),
                   expanded_nodes=0, search_queue=None)
    if winning(context, []):
        context["best"] = []
        publish(context)
        return result, None
    if full_value <= threshold + guard:
        return result, None
    mean_gain_prefix = np.concatenate(([0.0], np.cumsum(np.sort(alpha * (1.0 - target_values))[::-1])))
    baseline_mean = float(np.mean(target_values))

    def upper_bound(task_budget):
        bound = rank_bound(baseline_sorted, uplifted_sorted, retained_ranks, task_budget)
        if rule == "mean":
            bound = min(bound, baseline_mean + float(mean_gain_prefix[task_budget]) / task_count)
        return bound

    lower, upper = 0, task_count
    while lower < upper:
        task_budget = (lower + upper) // 2
        if upper_bound(task_budget) + guard <= threshold:
            lower = task_budget + 1
        else:
            upper = task_budget
    result["lower_bound"] = lower
    publish(context)
    if task_count <= 6:
        best_count = task_count + 1
        possible_count = task_count + 1
        for subset_mask in range(1 << task_count):
            selected_local = [index for index in semantic_order if subset_mask & (1 << index)]
            score = aggregate(attacked_values(context, selected_local), rule)
            if score + guard > threshold:
                possible_count = min(possible_count, len(selected_local))
            if score > threshold + guard and len(selected_local) < best_count:
                best_count = len(selected_local)
                context["best"] = selected_local
        result["lower_bound"] = possible_count
        publish(context)
        return result, None
    if rule == "mean":
        prefix_witness(context, ordered)
        return result, None
    else:
        first_rank = int(retained_ranks[0])
        last_rank = int(retained_ranks[-1])
        starts = sorted(set([0, first_rank, last_rank, first_rank // 2,
                             max(0, first_rank - 1), min(task_count - 1, first_rank + 1)]))
        for start in starts:
            order = ordered[start:] + list(reversed(ordered[:start]))
            prefix_witness(context, order)
        context["initial_starts"] = starts
    if result["status"] == "optimal":
        return result, None
    return result, context


def improve(context, decision, search_deadline):
    task_count = len(context["target_values"])
    ordered = context["ordered"]
    expanded_nodes = context["expanded_nodes"]
    if context["search_queue"] is None:
        first_rank = int(context["retained_ranks"][0])
        starts = sorted(range(task_count), key=lambda start: (abs(start - first_rank), start))
        search_queue = [("delete", None), ("greedy", None), ("delete", None)]
        search_queue.extend(("window", start) for start in reversed(starts)
                            if start not in context["initial_starts"])
    else:
        search_queue = context["search_queue"]
    while search_queue and expanded_nodes < decision['node_budget']:
        if time.monotonic() >= search_deadline:
            break
        operation, start = search_queue.pop()
        if operation == "window":
            order = ordered[start:] + list(reversed(ordered[:start]))
            prefix_witness(context, order)
            expanded_nodes += 1
        elif operation == "delete":
            selected_local = context["best"].copy()
            for index in list(reversed(selected_local)):
                if time.monotonic() >= search_deadline or expanded_nodes >= decision["node_budget"]:
                    break
                trial = [other for other in selected_local if other != index]
                expanded_nodes += 1
                if winning(context, trial):
                    selected_local = trial
                    consider(context, trial)
                if len(selected_local) == context["result"]["lower_bound"]:
                    break
        else:
            selected_local = []
            available = context["semantic_order"].copy()
            while available and len(selected_local) < len(context["best"]) - 1:
                if time.monotonic() >= search_deadline or expanded_nodes >= decision["node_budget"]:
                    break
                current = attacked_values(context, selected_local)
                choices = []
                for index in available:
                    if time.monotonic() >= search_deadline or expanded_nodes >= decision["node_budget"]:
                        break
                    trial = current.copy()
                    trial[index] += context["alpha"] * (1.0 - trial[index])
                    choices.append((-aggregate(trial, context["rule"]), context["task_ids"][context["panel_columns"][index]], index))
                    expanded_nodes += 1
                if not choices:
                    break
                index = min(choices)[2]
                selected_local.append(index)
                available.remove(index)
                if winning(context, selected_local):
                    consider(context, selected_local)
                    break
        if context["result"]["status"] == "optimal":
            search_queue.clear()
            break
    context["expanded_nodes"] = expanded_nodes
    context["search_queue"] = search_queue
    publish(context)


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
        deadline = time.monotonic() + request['work_seconds']
        output_reserve = min(work_seconds * 0.1, max(0.05, work_seconds * 0.02))
        search_deadline = deadline - output_reserve
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
        panel_cache = {}
        statistics_cache = {}
        plans = []
        unresolved = []
        for decision in request["decisions"]:
            result, context = solve(*matrices[decision["matrix"]], decision,
                                    panel_cache, statistics_cache, search_deadline)
            plans.append(result)
            if context is not None:
                unresolved.append((context, decision))
        for position, (context, decision) in enumerate(unresolved):
            if time.monotonic() >= search_deadline:
                break
            remaining = len(unresolved) - position
            decision_deadline = time.monotonic() + max(0.0, search_deadline - time.monotonic()) / remaining
            improve(context, decision, decision_deadline)
        for context, decision in unresolved:
            publish(context)
        panel_cache.clear()
        statistics_cache.clear()
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
