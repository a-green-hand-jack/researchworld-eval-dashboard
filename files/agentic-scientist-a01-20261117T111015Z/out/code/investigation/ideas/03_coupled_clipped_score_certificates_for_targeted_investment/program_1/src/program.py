"""CPU counterfactual support solver, exposed only through handle.

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

The solver exhausts <=6-column panels, uses sorted headroom for mean and
deterministic marginal-score greedy for larger median/trimmed panels. Complete
clipped-score sweeps share one support budget across all retained ranks.
Only reference bounds or exhaustive audits authorize optimal status; the new
envelope can otherwise tighten bounded lower bounds. No training-cost or
empirical performance claim is implied by these counterfactual calculations.
"""
import base64
import hashlib
import itertools
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


def aggregate_rows(values, rule):
    if rule == "mean":
        return np.mean(values, axis=1)
    if rule == "median":
        return np.median(values, axis=1)
    trim = values.shape[1] // 5
    return np.mean(np.sort(values, axis=1)[:, trim:values.shape[1]-trim], axis=1)


def trim_for_rule(task_count, rule):
    if rule == "mean":
        return 0
    if rule == "median":
        return (task_count - 1) // 2
    return task_count // 5


def reference_frontier(target_values, uplifted_values, trim_count):
    """Bound each retained rank by full uplift and its baseline k-rank shift.

    At most k changed entries move a retained rank by at most k baseline
    positions. A second bound uses total top-k headroom minus the baseline
    extremes, whose sums cannot decrease under coordinatewise uplift.
    """
    task_count = len(target_values)
    retained_count = task_count - 2 * trim_count
    baseline_sorted = np.sort(target_values)
    uplifted_sorted = np.sort(uplifted_values)
    shifted_ranks = np.arange(task_count)[None, :] + np.arange(task_count + 1)[:, None]
    baseline_limits = np.where(
        shifted_ranks < task_count,
        baseline_sorted[np.minimum(shifted_ranks, task_count - 1)],
        1.0,
    )
    rank_upper = np.minimum(baseline_limits, uplifted_sorted[None, :])
    reference_upper = np.mean(rank_upper[:, trim_count:task_count-trim_count], axis=1)
    gain_prefix = np.concatenate(([0.0], np.cumsum(np.sort(uplifted_values - target_values)[::-1])))
    removed_baseline = float(np.sum(baseline_sorted[:trim_count]))
    if trim_count:
        removed_baseline += float(np.sum(baseline_sorted[task_count-trim_count:]))
    sum_upper = (float(np.sum(target_values)) + gain_prefix - removed_baseline) / retained_count
    return np.minimum(reference_upper, sum_upper)


def clipped_frontier(target_values, uplifted_values, trim_count, frontier_key,
                     frontier_cache, completed_cutoffs, cutoff_deadline, sweep_limit):
    """Upper-bound a trimmed sum with complete shared-budget minimax sweeps.

    The sum L_q of the q smallest entries is max_t(q*t-sum((t-y)_+)).
    The retained sum L_(m-r)-L_r is min_a max_b of the hinge expression
    below. Moving max_support inside min_a gives an upper bound. For each
    a,b pair, a single top-k positive gain sum spends the support budget.
    All possible attacked entries are included as upper cutoffs. A minimum
    over any completed lower cutoffs is safe; a partial upper maximum is not.
    """
    task_count = len(target_values)
    retained_count = task_count - 2 * trim_count
    coupled_upper = frontier_cache.get(frontier_key, np.ones(task_count + 1)).copy()
    upper_cutoffs = np.unique(np.concatenate((target_values, uplifted_values, [0.0, 1.0])))
    baseline_sorted = np.sort(target_values)
    uplifted_sorted = np.sort(uplifted_values)
    initial_cutoffs = [0.0] if trim_count == 0 else [
        float(baseline_sorted[trim_count]),
        float(uplifted_sorted[trim_count]),
        float(baseline_sorted[trim_count-1]),
        float(uplifted_sorted[trim_count-1]),
    ]
    lower_cutoffs = list(dict.fromkeys(initial_cutoffs + upper_cutoffs.tolist()))
    finished = completed_cutoffs.setdefault(frontier_key, set())
    completed = 0
    for lower_cutoff in lower_cutoffs:
        if lower_cutoff in finished:
            continue
        if time.monotonic() >= cutoff_deadline:
            break
        if completed >= sweep_limit:
            break
        baseline_hinges = np.maximum(lower_cutoff - target_values, 0.0) - np.maximum(upper_cutoffs[:, None] - target_values[None, :], 0.0)
        uplift_hinges = np.maximum(lower_cutoff - uplifted_values, 0.0) - np.maximum(upper_cutoffs[:, None] - uplifted_values[None, :], 0.0)
        positive_gains = np.maximum(uplift_hinges - baseline_hinges, 0.0)
        gain_prefix = np.concatenate((np.zeros((len(upper_cutoffs), 1)), np.cumsum(np.sort(positive_gains, axis=1)[:, ::-1], axis=1)), axis=1)
        pair_baseline = (task_count - trim_count) * upper_cutoffs - trim_count * lower_cutoff + np.sum(baseline_hinges, axis=1)
        cutoff_upper = np.max(pair_baseline[:, None] + gain_prefix, axis=0) / retained_count
        coupled_upper = np.minimum(coupled_upper, cutoff_upper)
        frontier_cache[frontier_key] = coupled_upper.copy()
        finished.add(lower_cutoff)
        completed += 1
    return coupled_upper


def audit_small_panel(target_values, uplifted_values, rule, rival_max,
                      ordered, coupled_upper, reference_upper, roundoff_guard):
    task_count = len(target_values)
    exact_frontier = np.full(task_count + 1, -np.inf)
    selected_local = None
    for budget in range(task_count + 1):
        for support in itertools.combinations(ordered, budget):
            attacked_scores = target_values.copy()
            attacked_scores[list(support)] = uplifted_values[list(support)]
            exact_frontier[budget] = max(exact_frontier[budget], aggregate(attacked_scores, rule))
            verified_win = aggregate(attacked_scores, rule) > rival_max + 1e-10
            if verified_win and selected_local is None:
                selected_local = list(support)
    exact_frontier = np.maximum.accumulate(exact_frontier)
    assert np.all(coupled_upper + roundoff_guard >= exact_frontier)
    assert np.all(reference_upper + roundoff_guard >= exact_frontier)
    if selected_local is not None:
        minimum_support = len(selected_local)
        assert minimum_support == 0 or exact_frontier[minimum_support-1] <= rival_max + TOLERANCE
    return selected_local


def solve(matrix, task_ids, decision, context, decision_deadline):
    panel_columns = decision["columns"]
    matrix_key = decision["matrix"]
    target_index = decision["target"]
    rule = decision["rule"]
    alpha = decision["alpha"]
    task_count = len(panel_columns)
    semantic_task_ids = sorted(task_ids[column] for column in panel_columns)
    frontier_key = (matrix_key, tuple(semantic_task_ids), target_index, rule, float(alpha))
    panel_key = (matrix_key, tuple(panel_columns), rule)
    if panel_key not in context["panels"]:
        row_scores = aggregate_rows(matrix[:, panel_columns], rule)
        best_index = int(np.argmax(row_scores))
        best_score = float(row_scores[best_index])
        second_score = float(np.partition(row_scores, len(row_scores)-2)[-2])
        context["panels"][panel_key] = (best_index, best_score, second_score)
    best_index, best_score, second_score = context["panels"][panel_key]
    rival_max = second_score if target_index == best_index else best_score
    winning_threshold = rival_max + TOLERANCE
    target_values = matrix[target_index, panel_columns].copy()
    uplifted_values = target_values + alpha * (1.0 - target_values)
    ordered = sorted(range(task_count), key=lambda index: task_ids[panel_columns[index]])
    roundoff_guard = 256.0 * np.finfo(np.float64).eps * max(1, task_count)
    result = {"id": decision["id"], "selected": [], "status": "bounded", "lower_bound": 0}

    def wins(selected_local):
        attacked_scores = target_values.copy()
        attacked_scores[selected_local] = uplifted_values[selected_local]
        verified_win = aggregate(attacked_scores, rule) > rival_max + 1e-10
        return verified_win

    trim_count = trim_for_rule(task_count, rule)
    reference_upper = reference_frontier(target_values, uplifted_values, trim_count)
    if task_count <= 6:
        coupled_upper = clipped_frontier(
            target_values, uplifted_values, trim_count, frontier_key,
            context["frontiers"], context["cutoffs"], decision_deadline, 2 * task_count + 2,
        )
        selected_local = audit_small_panel(
            target_values, uplifted_values, rule, rival_max, ordered,
            coupled_upper, reference_upper, roundoff_guard,
        )
        if selected_local is None:
            assert not wins(list(range(task_count)))
            result.update(status="infeasible", lower_bound=task_count+1)
            return result
        selected_original = [panel_columns[index] for index in selected_local]
        original_to_local = {column: index for index, column in enumerate(panel_columns)}
        assert wins([original_to_local[column] for column in selected_original])
        result.update(selected=selected_original, status="optimal", lower_bound=len(selected_local))
        return result

    if not wins(list(range(task_count))):
        result.update(status="infeasible", lower_bound=task_count+1)
        return result
    if wins([]):
        result.update(status="optimal")
        return result

    selected_local = list(ordered)
    heuristic_deadline = time.monotonic() + 0.65 * max(0.0, decision_deadline - time.monotonic())
    if rule == "mean":
        headroom_order = sorted(ordered, key=lambda index: (-(1-target_values[index]), task_ids[panel_columns[index]]))
        proposal = []
        for index in headroom_order:
            if wins(proposal):
                break
            proposal.append(index)
        if wins(proposal):
            selected_local = proposal
    else:
        proposal = []
        current = target_values.copy()
        while not wins(proposal):
            if time.monotonic() >= heuristic_deadline:
                break
            available = [index for index in ordered if index not in proposal]
            trials = np.tile(current, (len(available), 1))
            trials[np.arange(len(available)), available] = uplifted_values[available]
            trial_scores = aggregate_rows(trials, rule)
            index = available[int(np.argmax(trial_scores))]
            proposal.append(index)
            current[index] = uplifted_values[index]
        if wins(proposal):
            selected_local = proposal

    coupled_upper = clipped_frontier(
        target_values, uplifted_values, trim_count, frontier_key,
        context["frontiers"], context["cutoffs"], decision_deadline,
        max(1, min(2 * task_count + 2, decision["node_budget"] // task_count)),
    )
    full_panel_upper = np.minimum(reference_upper, coupled_upper)
    excluded_budgets = full_panel_upper + roundoff_guard <= winning_threshold
    excluded_prefix = np.logical_and.accumulate(excluded_budgets)
    lower_bound = int(np.count_nonzero(excluded_prefix))
    reference_excluded = reference_upper + roundoff_guard <= winning_threshold
    reference_lower_bound = int(np.count_nonzero(np.logical_and.accumulate(reference_excluded)))
    if lower_bound > len(selected_local):
        lower_bound = 0
        reference_lower_bound = 0
    selected_original = [panel_columns[index] for index in selected_local]
    assert wins(selected_local)
    result.update(selected=selected_original, lower_bound=lower_bound)
    if reference_lower_bound == len(selected_local):
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
        run_started = time.monotonic()
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
        output_reserve = min(1.0, max(0.01, 0.05 * work_seconds), 0.25 * work_seconds)
        work_deadline = run_started + work_seconds - output_reserve
        context = {"panels": {}, "frontiers": {}, "cutoffs": {}}
        plans = []
        decisions = request["decisions"]
        for decision_index, decision in enumerate(decisions):
            now = time.monotonic()
            remaining = len(decisions) - decision_index
            decision_deadline = min(work_deadline, now + max(0.0, work_deadline - now) / remaining)
            plans.append(solve(*matrices[decision["matrix"]], decision, context, decision_deadline))
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
