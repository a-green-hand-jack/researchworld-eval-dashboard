"""Exact-refit, contrast-guided binary flips; CPU float64 and deterministic.

The entrypoint is self-contained Python (installed NumPy/SciPy are available); native
validation copies only this entrypoint into its private sandbox, not adjacent files.
Only handle(request)->finite JSON response is public. Extra response keys are forbidden.
A reset accepts ANY nonnegative integer seed (not bool) and returns exactly {"ok":true};
it clears all buffers, results and prior tokens. It does not choose dataset or workload.
Immediately after reset, analyze({"op":"analyze","token":"input"}) must return
exactly {"error":"no_data"}; no data or prior proposal may survive reset.

Upload protocol (all data inline; never paths):
 upload_start: token="input", dtype="<f8", shape=[n,4], byte_length=32*n,
 chunks=ceil(byte_length/1048576), participants=p, home=boolean. Response {"ok":true}.
 n<=524288, p in [2,256], chunks<=16; at most 16MiB decoded in-memory input.
 upload_chunk: token="input", index=0..chunks-1, encoding="base64", data=ASCII base64.
 Each chunk <=1048576 decoded bytes, in order. Response {"ok":true}.
 upload_commit: token="input". Response {"ok":true}. Columns are participant indices
 a,b (integers represented as float64), observed y in {0,.5,1}, home covariate z in
 {-1,0,1}. No home nuisance is fitted if home=false. Ties fit as fractional outcomes
 but cannot be flipped. Inputs are observed comparisons, not held-out targets.
 analyze: token="input", counts=[k1,k2,k3] positive nondecreasing exact edit budgets,
 audit_rows=list of 8 legal row indices, ridge=1.0, iterations=positive integer.
 The estimator minimizes SUM(logaddexp(0,x*theta)-y*x*theta)+ridge/2*||theta||^2,
 where x=e_a-e_b plus optional home coordinate z. Participant scores are centered.
 Returns {"token":"result","dtype":"<f8","shape":[L],"byte_length":8*L,"chunks":c}.
 download_chunk: token="result", index=0..c-1. Returns exactly
 {"index":index,"encoding":"base64","data":ASCII base64}, <=1MiB decoded/chunk.

Result layout, concatenated little-endian float64 (d=p+int(home)):
 fitted theta[d]; directional row influences[n]; audit derivatives[8,d] row-major;
 ordered distinct selected binary row indices[max(counts)] as exact integer-valued
 floats; predicted shifts[3,d] row-major for the nested prefixes of those indices.
 L=d+n+8*d+max(counts)+3*d. No other diagnostics or fields are accepted.
 Target contrast t=e_lower-e_upper: sort participant scores decreasing with index as
 tie-break, among adjacent pairs in top min(10,p) choose smallest score gap (first
 gap breaks ties). Influence for row r is (1-2*y_r)*x_r @ inverse(H) @ t;
 audit derivative is inverse(H) @ x_r (UNIT outcome change, including ties).
 H is exact regularized Hessian at fitted theta. Predictions sum signed row
 derivatives for each selected prefix. Selection may improve on the starter's greedy
 priorities; actual refits, not claimed sensitivities, determine score. Exact influence
 arithmetic is audited independently; nonlinear approximation error is reported, not
 an advantage threshold. No claim of superiority is necessary for search eligibility.
 No objective, reference fit, baseline output or control feedback is returned.

Operation order: reset, stale analyze, upload_start, chunks, upload_commit, analyze,
 download chunks. No export/import of persistent state, replay, filesystem sharing,
 or additional resets. All messages <64MiB including JSON/framing (local 8MiB cap).
 The runner owns resource limits. Internal iteration counts are advisory only.
"""
import base64
import math
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
from scipy.sparse import csr_matrix
from scipy.special import expit

_state = {}


class _ComparisonModel:
    def __init__(self, data, participants, home, ridge, iterations):
        self.data = data
        self.participants = participants
        self.home = home
        self.dimension = participants + int(home)
        self.ridge = ridge
        self.iterations = max(80, iterations)
        groups, self.inverse = np.unique(data[:, [0, 1, 3]], axis=0, return_inverse=True)
        self.first = groups[:, 0].astype(int)
        self.second = groups[:, 1].astype(int)
        self.home_value = groups[:, 2]
        self.multiplicity = np.bincount(self.inverse, minlength=len(groups)).astype(float)
        self.wins = np.bincount(self.inverse, weights=data[:, 2], minlength=len(groups))
        eligible = np.flatnonzero(data[:, 2] != .5)
        type_ids = 2 * self.inverse[eligible] + (data[eligible, 2] == 1).astype(int)
        self.capacity = np.bincount(type_ids, minlength=2 * len(groups))
        self.rows_by_type = eligible[np.argsort(type_ids, kind="stable")]
        self.offsets = np.concatenate(([0], np.cumsum(self.capacity)))
        self.empty = np.zeros_like(self.capacity)

    def project(self, vector):
        projection = vector[self.first] - vector[self.second]
        if self.home:
            projection = projection + self.home_value * vector[-1]
        return projection

    def transpose(self, values):
        result = np.zeros(self.dimension)
        result[:self.participants] = (
            np.bincount(self.first, weights=values, minlength=self.participants)
            - np.bincount(self.second, weights=values, minlength=self.participants)
        )
        if self.home:
            result[-1] = np.dot(self.home_value, values)
        return result

    def hessian(self, theta):
        probability = expit(self.project(theta))
        weight = self.multiplicity * probability * (1 - probability)
        diagonal = np.zeros(self.dimension)
        diagonal[:self.participants] = (
            np.bincount(self.first, weights=weight, minlength=self.participants)
            + np.bincount(self.second, weights=weight, minlength=self.participants)
        )
        hessian = np.diag(diagonal + self.ridge)
        np.add.at(hessian, (self.first, self.second), -weight)
        np.add.at(hessian, (self.second, self.first), -weight)
        if self.home:
            cross = (
                np.bincount(self.first, weights=weight * self.home_value, minlength=self.participants)
                - np.bincount(self.second, weights=weight * self.home_value, minlength=self.participants)
            )
            hessian[:self.participants, -1] = cross
            hessian[-1, :self.participants] = cross
            hessian[-1, -1] += np.dot(weight, self.home_value ** 2)
        return hessian

    def fit(self, flipped, initial=None):
        wins = self.wins + flipped[0::2] - flipped[1::2]

        def objective(theta):
            logits = self.project(theta)
            value = np.sum(self.multiplicity * np.logaddexp(0, logits) - wins * logits)
            value += self.ridge * np.dot(theta, theta) / 2
            gradient = self.transpose(self.multiplicity * expit(logits) - wins) + self.ridge * theta
            return value, gradient

        theta = np.zeros(self.dimension) if initial is None else initial.copy()
        converged = False
        for iteration in range(min(self.iterations, 50)):
            value, gradient = objective(theta)
            if np.max(np.abs(gradient)) <= 1e-9:
                converged = True
                break
            factor = cho_factor(self.hessian(theta), lower=True, check_finite=False)
            step = cho_solve(factor, gradient, check_finite=False)
            decrement = float(np.dot(gradient, step))
            step_size = 1.0
            for backtrack in range(30):
                proposal = theta - step_size * step
                proposal[:self.participants] -= proposal[:self.participants].mean()
                proposal_value, proposal_gradient = objective(proposal)
                if proposal_value <= value - 1e-4 * step_size * decrement + 1e-12 * max(1, abs(value)):
                    theta = proposal
                    break
                step_size *= .5
            else:
                break
            if np.max(np.abs(proposal_gradient)) <= 1e-9:
                converged = True
                break
        if not converged:
            fitted = minimize(objective, theta, jac=True, method="L-BFGS-B",
                              options={"maxiter": self.iterations, "gtol": 1e-9,
                                       "ftol": 1e-15, "maxls": 40})
            theta = fitted.x
            for polish in range(5):
                value, gradient = objective(theta)
                if np.max(np.abs(gradient)) <= 1e-9:
                    break
                factor = cho_factor(self.hessian(theta), lower=True, check_finite=False)
                proposal = theta - cho_solve(factor, gradient, check_finite=False)
                proposal_value, proposal_gradient = objective(proposal)
                if proposal_value > value + 1e-12 * max(1, abs(value)):
                    break
                theta = proposal
        theta[:self.participants] -= theta[:self.participants].mean()
        if not np.isfinite(theta).all() or np.max(np.abs(objective(theta)[1])) > 1e-6:
            raise ValueError("BT fit did not converge")
        return theta

    def propose(self, flipped, direction, budget):
        group_gain = self.project(direction)
        type_gain = np.column_stack((group_gain, -group_gain)).ravel()
        available = self.capacity - flipped
        eligible_types = np.flatnonzero(available)
        next_rows = self.rows_by_type[self.offsets[eligible_types] + flipped[eligible_types]]
        order = eligible_types[np.lexsort((next_rows, -type_gain[eligible_types]))]
        capacities = available[order]
        preceding = np.cumsum(capacities) - capacities
        taking = np.minimum(capacities, np.maximum(0, budget - preceding))
        proposed = flipped.copy()
        proposed[order] += taking
        active = np.flatnonzero(taking)
        row_blocks = [self.rows_by_type[
            self.offsets[order[position]] + flipped[order[position]]:
            self.offsets[order[position]] + proposed[order[position]]
        ] for position in active]
        rows = np.concatenate(row_blocks) if row_blocks else np.empty(0, dtype=int)
        if len(rows) != budget:
            raise ValueError("insufficient binary outcomes")
        return proposed, rows


def _incumbent_flips(model, theta, counts, contrast, baseline_factor):
    participants = model.participants
    baseline_rank = np.lexsort((np.arange(participants), -theta[:participants]))
    baseline_position = np.empty(participants, dtype=int)
    baseline_position[baseline_rank] = np.arange(participants)
    first_position, second_position = np.triu_indices(participants, 1)
    upper = baseline_rank[first_position]
    lower = baseline_rank[second_position]
    covariance = cho_solve(baseline_factor, np.eye(model.dimension), check_finite=False)
    variance = covariance[upper, upper] + covariance[lower, lower] - 2 * covariance[upper, lower]
    scale = np.maximum(.25 * np.sqrt(np.maximum(variance, 0)), 1e-4)
    baseline_direction = cho_solve(baseline_factor, contrast, check_finite=False)
    baseline_gain = (1 - 2 * model.data[:, 2]) * model.project(baseline_direction)[model.inverse]
    eligible_rows = np.flatnonzero(model.data[:, 2] != .5)
    fixed_order = eligible_rows[np.lexsort((eligible_rows, -baseline_gain[eligible_rows]))]

    def quality(current_theta):
        current_rank = np.lexsort((np.arange(participants), -current_theta[:participants]))
        current_position = np.empty(participants, dtype=int)
        current_position[current_rank] = np.arange(participants)
        displacement = int(np.abs(current_position - baseline_position).sum())
        inversions = int((current_position[upper] > current_position[lower]).sum())
        potential = float(expit((current_theta[lower] - current_theta[upper]) / scale).sum())
        return np.array([displacement, inversions, potential])

    initial = {"flipped": model.empty, "theta": theta, "rows": np.empty(0, dtype=int),
               "quality": np.zeros(3), "count": 0}
    fixed = initial
    beam = [initial]

    for count in counts:
        fixed_rows = fixed_order[:count]
        fixed_types = (2 * model.inverse[fixed_rows]
                       + (model.data[fixed_rows, 2] == 1).astype(int))
        fixed_counts = np.bincount(fixed_types, minlength=len(model.capacity))
        fixed_theta = model.fit(fixed_counts, initial=fixed["theta"]) if count != fixed["count"] else fixed["theta"]
        fixed = {"flipped": fixed_counts, "theta": fixed_theta, "rows": fixed_rows,
                 "quality": fixed["quality"] + quality(fixed_theta), "count": count}
        candidates = [fixed]
        for node in beam:
            factor = cho_factor(model.hessian(node["theta"]), lower=True, check_finite=False)
            inverse_hessian = cho_solve(factor, np.eye(model.dimension), check_finite=False)
            current_variance = (inverse_hessian[upper, upper] + inverse_hessian[lower, lower]
                                - 2 * inverse_hessian[upper, lower])
            gap = node["theta"][upper] - node["theta"][lower]
            priority = gap / np.sqrt(np.maximum(current_variance, 1e-12))
            unresolved = np.flatnonzero(gap >= 0)
            nearest = unresolved[np.argsort(priority[unresolved], kind="stable")[:6]]
            directions = [baseline_direction, cho_solve(factor, contrast, check_finite=False)]
            for pair_index in nearest:
                directions.append(inverse_hessian[:, lower[pair_index]] - inverse_hessian[:, upper[pair_index]])
            proposed_counts = []
            for direction in directions:
                flipped, rows = model.propose(node["flipped"], direction, count - node["count"])
                if any(np.array_equal(flipped, previous) for previous in proposed_counts):
                    continue
                proposed_counts.append(flipped)
                current_theta = model.fit(flipped, initial=node["theta"]) if len(rows) else node["theta"]
                candidates.append({"flipped": flipped, "theta": current_theta,
                                   "rows": np.concatenate((node["rows"], rows)),
                                   "quality": node["quality"] + quality(current_theta), "count": count})
        candidates.sort(key=lambda node: tuple(node["quality"]), reverse=True)
        beam = []
        for candidate in candidates:
            if any(np.array_equal(candidate["rows"], previous["rows"]) for previous in beam):
                continue
            beam.append(candidate)
            if len(beam) == 2:
                break
    return max(beam + [fixed], key=lambda node: tuple(node["quality"]))["rows"]


def _select_flips(model, theta, counts, contrast, baseline_factor):
    incumbent_path = _incumbent_flips(model, theta, counts, contrast, baseline_factor)
    baseline_rows = model.data
    baseline_theta = theta
    rows = baseline_rows
    ridge = model.ridge
    participants = model.participants
    checkpoints = [int(count) for count in counts]
    beam_width = 4
    fit_limit = 192
    proposal_limit = 160
    fits_used = 0
    proposals_used = 0
    warm_theta = baseline_theta
    fit_cache = {b"": baseline_theta}
    baseline_rank = np.lexsort((np.arange(participants), -baseline_theta[:participants]))
    baseline_position = np.empty(participants, dtype=int)
    baseline_position[baseline_rank] = np.arange(participants)
    first_position, second_position = np.triu_indices(participants, 1)
    upper = baseline_rank[first_position]
    lower = baseline_rank[second_position]
    covariance = cho_solve(baseline_factor, np.eye(model.dimension), check_finite=False)
    variance = covariance[upper, upper] + covariance[lower, lower] - 2 * covariance[upper, lower]
    scale = np.maximum(.25 * np.sqrt(np.maximum(variance, 0)), 1e-4)
    baseline_direction = cho_solve(baseline_factor, contrast, check_finite=False)
    type_ids = np.arange(len(model.capacity))
    group_ids = type_ids // 2
    design_rows = [type_ids, type_ids]
    design_columns = [model.first[group_ids], model.second[group_ids]]
    design_values = [np.ones(len(type_ids)), -np.ones(len(type_ids))]
    if model.home:
        design_rows.append(type_ids)
        design_columns.append(np.full(len(type_ids), participants))
        design_values.append(model.home_value[group_ids])
    row_design = csr_matrix((np.concatenate(design_values),
                             (np.concatenate(design_rows), np.concatenate(design_columns))),
                            shape=(len(type_ids), model.dimension))
    current_outcome = (type_ids % 2).astype(float)

    class SearchLimit(Exception):
        pass

    def canonical_key(prefix):
        return np.sort(np.asarray(prefix, dtype=np.int32)).tobytes()

    def refit_flip_prefix(baseline_rows, candidate_prefix, ridge):
        nonlocal fits_used
        if ridge != model.ridge:
            raise ValueError("ridge changed during search")
        key = canonical_key(candidate_prefix)
        if key not in fit_cache:
            if fits_used >= fit_limit:
                raise SearchLimit("exact refit cap")
            selected_types = (2 * model.inverse[candidate_prefix]
                              + (baseline_rows[candidate_prefix, 2] == 1).astype(int))
            flipped = np.bincount(selected_types, minlength=len(model.capacity))
            if np.any(flipped > model.capacity):
                raise ValueError("flip capacity exceeded")
            fits_used += 1
            fitted = model.fit(flipped, initial=warm_theta)
            if not np.isfinite(fitted).all():
                raise ValueError("nonfinite search refit")
            fit_cache[key] = fitted
        return fit_cache[key]

    def quality(current_theta):
        current_rank = np.lexsort((np.arange(participants), -current_theta[:participants]))
        current_position = np.empty(participants, dtype=int)
        current_position[current_rank] = np.arange(participants)
        displacement = int(np.abs(current_position - baseline_position).sum())
        inversions = int((current_position[upper] > current_position[lower]).sum())
        potential = float(expit((current_theta[lower] - current_theta[upper]) / scale).sum())
        return np.array([displacement, inversions, potential])

    def crossing_proposals(node, remaining, limit=4):
        nonlocal proposals_used
        if remaining <= 0:
            return []
        if proposals_used >= proposal_limit:
            raise SearchLimit("contrast proposal cap")
        proposals_used += 1
        factor = cho_factor(model.hessian(node["theta"]), lower=True, check_finite=False)
        inverse_hessian = cho_solve(factor, np.eye(model.dimension), check_finite=False)
        current_rank = np.lexsort((np.arange(participants), -node["theta"][:participants]))
        current_position = np.empty(participants, dtype=int)
        current_position[current_rank] = np.arange(participants)
        unresolved = np.flatnonzero(current_position[upper] < current_position[lower])
        if not len(unresolved):
            return []
        gaps = node["theta"][upper] - node["theta"][lower]
        current_variance = (inverse_hessian[upper, upper] + inverse_hessian[lower, lower]
                            - 2 * inverse_hessian[upper, lower])
        priority = gaps / np.sqrt(np.maximum(current_variance, 1e-12))
        ranked = unresolved[np.argsort(priority[unresolved], kind="stable")]
        adjacent = ranked[second_position[ranked] - first_position[ranked] == 1][:6]
        nonadjacent = ranked[second_position[ranked] - first_position[ranked] > 1][:6]
        shortlist = list(dict.fromkeys(np.concatenate((ranked[:4], adjacent, nonadjacent)).tolist()))
        available = model.capacity - node["flipped"]
        available_types = np.flatnonzero(available)
        next_rows = np.full(len(available), len(rows), dtype=int)
        next_rows[available_types] = model.rows_by_type[
            model.offsets[available_types] + node["flipped"][available_types]]
        proposals = []
        for pair_index in shortlist:
            pair_contrast = np.zeros(model.dimension)
            pair_contrast[upper[pair_index]] = 1.0
            pair_contrast[lower[pair_index]] = -1.0
            contrast_solution = cho_solve(factor, pair_contrast, check_finite=False)
            contrast_solution[:participants] -= contrast_solution[:participants].mean()
            flip_effect = (1.0 - 2.0 * current_outcome) * (row_design @ contrast_solution)
            beneficial = np.flatnonzero((available > 0) & (flip_effect < 0))
            if not len(beneficial):
                continue
            ordered = beneficial[np.lexsort((next_rows[beneficial], flip_effect[beneficial]))]
            capacities = available[ordered]
            preceding = np.cumsum(capacities) - capacities
            taking = np.minimum(capacities, np.maximum(0, remaining - preceding))
            candidate_ids = np.repeat(ordered, taking)
            crossing_gain = np.cumsum(-flip_effect[candidate_ids])
            current_gap = max(0.0, float(gaps[pair_index]))
            crossing_positions = np.flatnonzero(crossing_gain > current_gap)
            if len(crossing_positions):
                length = int(crossing_positions[0]) + 1
                estimated_cost = float(length)
            else:
                length = min(len(candidate_ids), max(1, remaining // 2))
                estimated_cost = len(candidate_ids) * current_gap / max(float(crossing_gain[-1]), 1e-15)
            direction = -contrast_solution
            flipped, batch = model.propose(node["flipped"], direction, length)
            progress = float(crossing_gain[length - 1]) / max(current_gap, 1e-15)
            proposals.append({"flipped": flipped, "batch": batch, "direction": direction,
                              "target": int(pair_index), "estimated_cost": estimated_cost,
                              "progress": progress, "partial": not len(crossing_positions)})
        proposals.sort(key=lambda proposal: (proposal["estimated_cost"],
                                               -proposal["progress"], proposal["target"]))
        chosen = proposals[:limit]
        if limit > 1 and chosen and chosen[0]["partial"]:
            best = chosen[0]
            flipped, batch = model.propose(node["flipped"], best["direction"], remaining)
            chosen = chosen[:limit - 1] + [dict(best, flipped=flipped, batch=batch)]
        return chosen

    def extend_node(node, proposal):
        nonlocal warm_theta
        candidate_prefix = np.concatenate((node["rows"], proposal["batch"]))
        warm_theta = node["theta"]
        candidate_theta = refit_flip_prefix(baseline_rows, candidate_prefix, ridge=ridge)
        return {"rows": candidate_prefix, "theta": candidate_theta,
                "flipped": proposal["flipped"], "count": len(candidate_prefix),
                "quality": node["quality"], "target": proposal["target"]}

    def complete_checkpoint(node, proposal, count):
        current = extend_node(node, proposal)
        for transition in range(2):
            remaining = count - current["count"]
            if remaining <= 0:
                break
            refreshed = crossing_proposals(current, remaining, limit=1)
            if refreshed:
                continuation = refreshed[0]
                direction = continuation["direction"]
            else:
                factor = cho_factor(model.hessian(current["theta"]), lower=True, check_finite=False)
                direction = cho_solve(factor, contrast, check_finite=False)
                continuation = {"target": current["target"]}
            if transition == 1 or not refreshed:
                flipped, batch = model.propose(current["flipped"], direction, remaining)
                continuation = dict(continuation, flipped=flipped, batch=batch)
            current = extend_node(current, continuation)
        if current["count"] != count:
            raise ValueError("incomplete checkpoint")
        current["quality"] = node["quality"] + quality(current["theta"])
        return current

    def select_checkpoint_beam(candidate_states, beam_width):
        ordered = sorted(candidate_states, key=lambda state: tuple(state["quality"]), reverse=True)
        unique = []
        seen = set()
        for state in ordered:
            key = canonical_key(state["rows"])
            if key not in seen:
                seen.add(key)
                unique.append(state)
        selected = unique[:min(2, beam_width)]
        targets = {state["target"] for state in selected}
        for state in unique[len(selected):]:
            if len(selected) >= beam_width:
                break
            if state["target"] not in targets:
                selected.append(state)
                targets.add(state["target"])
        for state in unique:
            if len(selected) >= beam_width:
                break
            if not any(state is previous for previous in selected):
                selected.append(state)
        return selected

    def search_crossings():
        initial = {"flipped": model.empty, "theta": baseline_theta,
                   "rows": np.empty(0, dtype=int), "quality": np.zeros(3),
                   "count": 0, "target": -1}
        beam = [initial]
        for count in checkpoints:
            candidate_states = []
            for node in beam:
                remaining = count - node["count"]
                if remaining == 0:
                    candidate_states.append(dict(node, quality=node["quality"] + quality(node["theta"])))
                    continue
                proposals = crossing_proposals(node, remaining)
                factor = cho_factor(model.hessian(node["theta"]), lower=True, check_finite=False)
                directions = [baseline_direction, cho_solve(factor, contrast, check_finite=False)]
                for direction_index, direction in enumerate(directions):
                    flipped, batch = model.propose(node["flipped"], direction, remaining)
                    proposals.append({"flipped": flipped, "batch": batch, "target": -1 - direction_index})
                seen = set()
                for proposal in proposals:
                    key = canonical_key(np.concatenate((node["rows"], proposal["batch"])))
                    if key in seen:
                        continue
                    seen.add(key)
                    candidate_states.append(complete_checkpoint(node, proposal, count))
            beam = select_checkpoint_beam(candidate_states, beam_width=beam_width)
            if not beam:
                raise ValueError("empty checkpoint beam")
        return max(beam, key=lambda state: tuple(state["quality"]))["rows"]

    def score_prefix_path(path, checkpoints, baseline_theta):
        nonlocal warm_theta
        warm_theta = baseline_theta
        total = np.zeros(3)
        for count in checkpoints:
            fitted = refit_flip_prefix(baseline_rows, path[:count], ridge=ridge)
            total += quality(fitted)
            warm_theta = fitted
        return tuple(total)

    try:
        crossing_path = search_crossings()
        portfolio_paths = [incumbent_path, crossing_path]
        path_scores = [score_prefix_path(path, checkpoints, baseline_theta) for path in portfolio_paths]
        path_scores = [sum(score > other for other in path_scores) for score in path_scores]
        selected_path = portfolio_paths[int(np.argmax(path_scores))]
    except (SearchLimit, ValueError, FloatingPointError, np.linalg.LinAlgError):
        selected_path = incumbent_path
    flip_order = [int(row_id) for row_id in selected_path]
    assert len(flip_order) == max(checkpoints)
    assert len(flip_order) == len(set(flip_order))
    assert all(0 <= row_id < len(rows) for row_id in flip_order)
    assert all(rows[row_id, 2] in (0.0, 1.0) for row_id in flip_order)
    return np.asarray(flip_order, dtype=int)


def handle(request):
    global _state
    operation = request["op"]
    if operation == "reset":
        if type(request["seed"]) is not int or request["seed"] < 0:
            raise ValueError("invalid seed")
        _state = {"seed": request["seed"]}
        return {"ok": True}
    if operation == "upload_start":
        if request["dtype"] != "<f8" or request["shape"][1] != 4 or not 0 < request["byte_length"] <= 16 * 1048576:
            raise ValueError("invalid upload")
        _state.update(meta=dict(request), buffer=bytearray(), ordinal=0)
        return {"ok": True}
    if operation == "upload_chunk":
        if request["index"] != _state["ordinal"] or request["encoding"] != "base64":
            raise ValueError("chunk order")
        block = base64.b64decode(request["data"], validate=True)
        if len(block) > 1048576 or len(_state["buffer"]) + len(block) > _state["meta"]["byte_length"]:
            raise ValueError("chunk bounds")
        _state["buffer"].extend(block)
        _state["ordinal"] += 1
        return {"ok": True}
    if operation == "upload_commit":
        metadata = _state["meta"]
        if len(_state["buffer"]) != metadata["byte_length"] or _state["ordinal"] != metadata["chunks"]:
            raise ValueError("incomplete upload")
        _state["data"] = np.frombuffer(bytes(_state.pop("buffer")), dtype="<f8").reshape(metadata["shape"])
        return {"ok": True}
    if operation == "analyze":
        if "data" not in _state or request["token"] != "input":
            return {"error": "no_data"}
        data = _state["data"]
        metadata = _state["meta"]
        participants = metadata["participants"]
        dimension = participants + int(metadata["home"])
        model = _ComparisonModel(data, participants, metadata["home"], request["ridge"], request["iterations"])
        theta = model.fit(model.empty)
        hessian = model.hessian(theta)
        factor = cho_factor(hessian, lower=True, check_finite=False)
        rank = np.lexsort((np.arange(participants), -theta[:participants]))
        adjacent = rank[:min(10, participants)]
        position = int(np.argmin(theta[adjacent[:-1]] - theta[adjacent[1:]]))
        contrast = np.zeros(dimension)
        contrast[adjacent[position + 1]] = 1
        contrast[adjacent[position]] = -1
        direction = cho_solve(factor, contrast, check_finite=False)
        influences = (1 - 2 * data[:, 2]) * model.project(direction)[model.inverse]
        selected = _select_flips(model, theta, request["counts"], contrast, factor)
        audit_indices = np.asarray(request["audit_rows"], dtype=int)
        audit_data = data[audit_indices]
        audit_design = np.zeros((len(audit_indices), dimension))
        np.add.at(audit_design, (np.arange(len(audit_indices)), audit_data[:, 0].astype(int)), 1)
        np.add.at(audit_design, (np.arange(len(audit_indices)), audit_data[:, 1].astype(int)), -1)
        if metadata["home"]:
            audit_design[:, -1] = audit_data[:, 3]
        audits = cho_solve(factor, audit_design.T, check_finite=False).T
        predictions = []
        for count in request["counts"]:
            subset = selected[:count]
            group_changes = np.bincount(model.inverse[subset], weights=1 - 2 * data[subset, 2],
                                        minlength=len(model.multiplicity))
            predictions.append(cho_solve(factor, model.transpose(group_changes), check_finite=False))
        result = np.concatenate([theta, influences, audits.ravel(), selected.astype(float), np.asarray(predictions).ravel()]).astype("<f8").tobytes()
        if len(result) > 16 * 1048576:
            raise ValueError("result too large")
        _state["result"] = result
        return {"token": "result", "dtype": "<f8", "shape": [len(result) // 8], "byte_length": len(result), "chunks": math.ceil(len(result) / 1048576)}
    if operation == "download_chunk":
        index = request["index"]
        result = _state["result"]
        return {"index": index, "encoding": "base64", "data": base64.b64encode(result[index * 1048576:(index + 1) * 1048576]).decode("ascii")}
    raise ValueError("unknown operation")
