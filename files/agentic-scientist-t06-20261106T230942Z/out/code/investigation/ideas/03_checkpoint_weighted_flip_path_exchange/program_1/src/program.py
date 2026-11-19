"""Exact-refit binary flips with bounded checkpoint-local path refinement.

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
import time
import numpy as np
from scipy.linalg import cho_factor, cho_solve
from scipy.optimize import minimize
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


def _select_flips(model, theta, counts, contrast, baseline_factor):
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
    incumbent_path = max(beam + [fixed], key=lambda node: tuple(node["quality"]))["rows"]
    return _refine_flip_path(model, incumbent_path, counts, theta, baseline_factor,
                             quality, upper, lower, scale)


class _PathSearchExhausted(RuntimeError):
    pass


def _verify_checkpoint_locality():
    current_path = [0, 1, 2, 3]
    checkpoints = [1, 2, 2, 4]

    def full_checkpoint_keys(path):
        return {budget: tuple(sorted(path[:budget])) for budget in checkpoints}

    current_keys = full_checkpoint_keys(current_path)
    for left in range(len(current_path)):
        for right in range(left + 1, len(current_path)):
            proposal_path = current_path.copy()
            proposal_path[left], proposal_path[right] = proposal_path[right], proposal_path[left]
            affected_checkpoints = [budget for budget in checkpoints if left < budget <= right]
            local_keys = current_keys.copy()
            for budget in affected_checkpoints:
                local_keys[budget] = tuple(sorted(proposal_path[:budget]))
            full_keys = full_checkpoint_keys(proposal_path)
            assert local_keys == full_keys
            assert set(affected_checkpoints) == {
                budget for budget in checkpoints if current_keys[budget] != full_keys[budget]
            }
    for position in range(len(current_path)):
        replacement_row = 4
        proposal_path = current_path.copy()
        proposal_path[position] = replacement_row
        affected_checkpoints = [budget for budget in checkpoints if budget > position]
        local_keys = current_keys.copy()
        for budget in affected_checkpoints:
            local_keys[budget] = tuple(sorted(proposal_path[:budget]))
        full_keys = full_checkpoint_keys(proposal_path)
        assert local_keys == full_keys
        assert set(affected_checkpoints) == {
            budget for budget in checkpoints if current_keys[budget] != full_keys[budget]
        }


def _refine_flip_path(model, incumbent_path, checkpoints, baseline_theta, baseline_factor,
                      quality, upper, lower, scale):
    rows = model.data
    baseline_rows = rows
    ridge = model.ridge
    checkpoints = [int(budget) for budget in checkpoints]
    incumbent_path = [int(row_id) for row_id in incumbent_path]
    current_path = incumbent_path
    prefix_theta_cache = {}
    prefix_quality_cache = {}
    current_checkpoint_scores = {}
    last_checkpoint_scores = {}
    affected_checkpoints = checkpoints
    exact_refit_count = 0
    exact_refit_cap = len(set(checkpoints))
    proposal_count = 0
    proposal_cap = 128
    deadline = None
    incumbent_value = current_value = (-math.inf, -math.inf, -math.inf)

    def refit_flip_prefix(baseline_rows, prefix, ridge):
        if baseline_rows is not model.data or ridge != model.ridge:
            raise ValueError("prefix fit must preserve the original fixed-ridge objective")
        subset = np.asarray(prefix, dtype=int)
        flip_types = (2 * model.inverse[subset]
                      + (baseline_rows[subset, 2] == 1).astype(int))
        flipped = np.bincount(flip_types, minlength=len(model.capacity))
        return model.fit(flipped, initial=baseline_theta)

    def score_prefix_path(path, checkpoints, baseline_theta):
        nonlocal exact_refit_count, last_checkpoint_scores
        checkpoint_scores = current_checkpoint_scores.copy()
        for budget in dict.fromkeys(affected_checkpoints):
            cache_key = tuple(sorted(path[:budget]))
            if cache_key not in prefix_theta_cache:
                if exact_refit_count >= exact_refit_cap:
                    raise _PathSearchExhausted("exact-refit cap")
                if deadline is not None and time.monotonic() >= deadline:
                    raise _PathSearchExhausted("optional-search deadline")
                prefix_theta_cache[cache_key] = refit_flip_prefix(baseline_rows, path[:budget], ridge=ridge)
                exact_refit_count += 1
            fitted_theta = prefix_theta_cache[cache_key]
            if not np.isfinite(fitted_theta).all():
                raise ValueError("nonfinite prefix fit")
            if cache_key not in prefix_quality_cache:
                prefix_quality_cache[cache_key] = quality(fitted_theta)
            checkpoint_scores[budget] = prefix_quality_cache[cache_key]
        complete_value = np.sum([checkpoint_scores[budget] for budget in checkpoints], axis=0)
        if not np.isfinite(complete_value).all():
            raise ValueError("nonfinite complete-path score")
        last_checkpoint_scores = checkpoint_scores
        return tuple(complete_value)

    selected_path = incumbent_path
    assert len(selected_path) == len(set(selected_path))
    assert all(0 <= row_id < len(rows) for row_id in selected_path)
    assert len(selected_path) >= max(checkpoints, default=0)
    assert all(rows[row_id, 2] in (0, 1) for row_id in selected_path)

    try:
        incumbent_value = score_prefix_path(incumbent_path, checkpoints, baseline_theta)
        current_value = incumbent_value
        current_checkpoint_scores = last_checkpoint_scores
        _verify_checkpoint_locality()
        exact_refit_cap += 72 if model.dimension <= 64 else 24
        deadline = time.monotonic() + 2.0
        eligible_rows = np.flatnonzero(rows[:, 2] != .5)
        row_types = 2 * model.inverse + (rows[:, 2] == 1).astype(int)
        path_positions = np.arange(len(current_path))
        sweep_positions = set(np.linspace(0, len(current_path) - 1,
                                         num=min(24, len(current_path)), dtype=int).tolist())
        for budget in checkpoints:
            sweep_positions.update(position for position in (budget - 1, budget)
                                   if 0 <= position < len(current_path))
        sweep_positions = sorted(sweep_positions)
        position_cursor = 0

        while proposal_count < proposal_cap and time.monotonic() < deadline:
            if exact_refit_count >= exact_refit_cap:
                break
            selected_types = row_types[np.asarray(current_path, dtype=int)]
            unused = np.ones(len(rows), dtype=bool)
            unused[current_path] = False
            unused_rows = eligible_rows[unused[eligible_rows]]
            first_unused = np.full(len(model.capacity), len(rows), dtype=int)
            np.minimum.at(first_unused, row_types[unused_rows], unused_rows)
            replacement_rows = np.sort(first_unused[first_unused < len(rows)])
            replacement_types = row_types[replacement_rows]
            checkpoint_gains = {}
            for budget in dict.fromkeys(checkpoints):
                cache_key = tuple(sorted(current_path[:budget]))
                checkpoint_theta = prefix_theta_cache[cache_key]
                probability = expit((checkpoint_theta[lower] - checkpoint_theta[upper]) / scale)
                gap_weight = probability * (1 - probability) / scale
                gradient = np.zeros(model.dimension)
                np.add.at(gradient, lower, gap_weight)
                np.add.at(gradient, upper, -gap_weight)
                direction = cho_solve(baseline_factor, gradient, check_finite=False)
                group_gain = model.project(direction)
                checkpoint_gains[budget] = np.column_stack((group_gain, -group_gain)).ravel()

            accepted = False
            for offset in range(len(sweep_positions)):
                if proposal_count >= proposal_cap or time.monotonic() >= deadline:
                    break
                position = sweep_positions[(position_cursor + offset) % len(sweep_positions)]
                selected_type = selected_types[position]
                swap_gain = np.zeros(len(current_path))
                crosses_checkpoint = np.zeros(len(current_path), dtype=bool)
                replacement_gain = np.zeros(len(replacement_rows))
                for budget in checkpoints:
                    type_gain = checkpoint_gains[budget]
                    crossing = (path_positions < budget) != (position < budget)
                    sign = 1 if position < budget else -1
                    swap_gain[crossing] += sign * (type_gain[selected_types[crossing]]
                                                   - type_gain[selected_type])
                    crosses_checkpoint |= crossing
                    if budget > position:
                        replacement_gain += type_gain[replacement_types] - type_gain[selected_type]

                proposals = []
                valid_swap = crosses_checkpoint & (selected_types != selected_type)
                if np.any(valid_swap):
                    partner = int(np.argmax(np.where(valid_swap, swap_gain, -np.inf)))
                    left, right = sorted((position, partner))
                    proposal_path = current_path.copy()
                    proposal_path[left], proposal_path[right] = proposal_path[right], proposal_path[left]
                    affected_checkpoints = [budget for budget in checkpoints if left < budget <= right]
                    proposals.append((proposal_path, affected_checkpoints))
                valid_replacement = replacement_types != selected_type
                if np.any(valid_replacement):
                    replacement_index = int(np.argmax(np.where(valid_replacement, replacement_gain, -np.inf)))
                    replacement_row = int(replacement_rows[replacement_index])
                    if replacement_row in current_path:
                        raise ValueError("duplicate-row replacement")
                    proposal_path = current_path.copy()
                    proposal_path[position] = replacement_row
                    affected_checkpoints = [budget for budget in checkpoints if budget > position]
                    proposals.append((proposal_path, affected_checkpoints))

                best_value = current_value
                best_path = None
                best_scores = None
                for proposal_path, proposal_checkpoints in proposals:
                    if proposal_count >= proposal_cap or time.monotonic() >= deadline:
                        break
                    proposal_count += 1
                    affected_checkpoints = proposal_checkpoints
                    proposal_value = score_prefix_path(proposal_path, checkpoints, baseline_theta)
                    if proposal_value > best_value:
                        best_value = proposal_value
                        best_path = proposal_path
                        best_scores = last_checkpoint_scores
                if best_path is not None:
                    proposal_path = best_path
                    proposal_value = best_value
                    if proposal_value > current_value:
                        current_path = proposal_path
                        current_value = proposal_value
                        current_checkpoint_scores = best_scores
                        position_cursor = (position_cursor + offset + 1) % len(sweep_positions)
                        accepted = True
                        break
            if not accepted:
                break
    except Exception:
        pass

    selected_path = current_path if current_value > incumbent_value else incumbent_path
    assert len(selected_path) == len(set(selected_path))
    assert all(0 <= row_id < len(rows) for row_id in selected_path)
    assert len(selected_path) >= max(checkpoints, default=0)
    assert all(rows[row_id, 2] in (0, 1) for row_id in selected_path)
    return np.asarray(selected_path, dtype=int)


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
