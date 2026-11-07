"""Deterministic overlap-aware covariance candidate; finite-JSON handle API.

All requests and responses are objects. No additional response keys are allowed.
Every independent episode begins with reset; reset erases uploads, fits, contexts,
and RNG. Seeds are arbitrary nonnegative integers, never workload selectors.

reset: {op:'reset', seed:int} -> {ok:true}.
train_start: {op:'train_start', rows:int<=8192, columns:int<=1024,
 column_names:list[str] of length columns, training_steps:int in [1,100],
 max_queries:int<=8} -> {ok:true}. Allocates candidate-owned RAM only.
train_chunk: {op:'train_chunk', offset:int, shape:[r,columns], dtype:'<f8',
 encoding:'base64', data:str, mask_dtype:'|u1', mask:str} -> {ok:true}.
Chunks are sequential, r<=256, at most 32 chunks. data contains row-major
little-endian float64 normalized scores in [0,1]; mask is row-major uint8 0/1.
Unobserved cells contain zero, not NaN. Decode both; masked cells are unknown.
train_commit: {op:'train_commit'} -> {ok:true}; requires all rows uploaded.
fit: {op:'fit'} -> {ok:true}; learn only from the committed historical matrix.
start: {op:'start', availability:list[list[bool]], max_queries:int} -> {ok:true}.
Creates/replaces a batch of 1..128 independent new-model contexts; each mask has
columns entries. A true entry may be purchased once; no scores are provided.
select: {op:'select'} -> {indices:list[int]}, exactly one unqueried available
column per active row. Rows have enough available columns for max_queries+1.
observe: {op:'observe', indices:list[int], values:list[float]} -> {ok:true}.
Exactly the last selections and their purchased normalized scores are supplied.
Only completed observations can affect subsequent decisions. Never pool contexts.
predict: {op:'predict'} -> {predictions:list[list[float]]}, shape [batch,columns],
all entries finite numeric (not bool); evaluator clips to [0,1] and scores only
available unpurchased entries. No diagnostics, state flags, or artifact paths.

Calls follow reset, train_start, chunks, train_commit, fit, then repeated start /
(select,observe,[predict])* trajectories. Prediction checkpoints and workload are
operation-driven, not seed-driven. Fit allowance is advisory sweeps, not telemetry.
The candidate estimates overlap-shrunk covariance from historical observations,
tunes shrinkage and ridge on held-out historical rows, and greedily selects by
off-diagonal target-risk reduction. Selection never uses purchased score values.
No filesystem or network transport is part of this interface. Full messages,
including JSON framing, must be strictly below 64 MiB. Dependencies are preinstalled.
"""
import base64
import warnings
import numpy as np

_STATE = {}


def covariance_statistics(values, mask):
    train_scores = np.where(mask, values, np.nan)
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', RuntimeWarning)
        train_means = np.nanmean(train_scores, axis=0)
    train_means = np.where(np.isfinite(train_means), train_means, 0.5)
    observation_counts = np.isfinite(train_scores).astype(np.int64)
    overlap_counts = observation_counts.T @ observation_counts
    counts = observation_counts.sum(axis=0)
    centered = np.where(mask, values - train_means, 0.0)
    variances = np.sum(centered ** 2, axis=0) / np.maximum(counts - 1, 1)
    train_scales = np.sqrt(np.maximum(variances, 0.01 ** 2))
    standardized = centered / train_scales
    observed_float = observation_counts.astype(np.float64)
    pair_sums = standardized.T @ observed_float
    pair_products = standardized.T @ standardized
    pair_covariance = (pair_products - pair_sums * pair_sums.T /
                       np.maximum(overlap_counts, 1)) / np.maximum(overlap_counts - 1, 1)
    pair_covariance[overlap_counts < 3] = 0.0
    diagonal = variances / train_scales ** 2
    bounds = np.sqrt(np.outer(diagonal, diagonal))
    pair_covariance = np.clip(pair_covariance, -bounds, bounds)
    np.fill_diagonal(pair_covariance, diagonal)
    return train_means, train_scales, pair_covariance, overlap_counts, diagonal


def stabilize_covariance(statistics, overlap_penalty):
    _, _, pair_covariance, overlap_counts, diagonal = statistics
    with np.errstate(divide='ignore', invalid='ignore'):
        reliability = overlap_counts / (overlap_counts + overlap_penalty)
    reliability = np.where(overlap_counts > 0, reliability, 0.0)
    covariance = pair_covariance * reliability
    np.fill_diagonal(covariance, diagonal)
    covariance = (covariance + covariance.T) * 0.5
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    eigenvalue_floor = 1e-6
    covariance = (eigenvectors * np.maximum(eigenvalues, eigenvalue_floor)) @ eigenvectors.T
    restored_diagonal = np.maximum(diagonal, eigenvalue_floor)
    rescaling = np.sqrt(restored_diagonal / np.maximum(np.diag(covariance), eigenvalue_floor))
    covariance *= rescaling[:, None] * rescaling[None, :]
    return (covariance + covariance.T) * 0.5


def greedy_plan(covariance, ridge, query_pool_mask, target_mask, target_weights, budget):
    posterior_covariance = covariance.copy()
    selected_indices = []
    plan = []
    for _ in range(min(budget, int(np.sum(query_pool_mask)))):
        remaining_targets = target_mask.copy()
        remaining_targets[selected_indices] = False
        diagonal = np.maximum(np.diag(posterior_covariance), 0.0)
        gains = np.einsum('i,ij,ij->j', target_weights * remaining_targets,
                          posterior_covariance, posterior_covariance, optimize=True)
        gains -= target_weights * remaining_targets * diagonal ** 2
        gains = np.maximum(gains, 0.0) / (diagonal + ridge)
        legal = query_pool_mask.copy()
        legal[selected_indices] = False
        gains[~legal] = -np.inf
        candidate_index = int(np.argmax(gains))
        remaining_targets[candidate_index] = False
        gain = np.sum(target_weights[remaining_targets] * posterior_covariance[remaining_targets, candidate_index] ** 2) / (posterior_covariance[candidate_index, candidate_index] + ridge)
        if not np.isclose(gains[candidate_index], gain, rtol=1e-7, atol=1e-9):
            raise ArithmeticError('inconsistent off-diagonal acquisition')
        chosen_index = candidate_index
        covariance_column = posterior_covariance[:, chosen_index].copy()
        previous_risk = float(np.dot(target_weights[remaining_targets],
                                     np.diag(posterior_covariance)[remaining_targets]))
        posterior_covariance -= np.outer(covariance_column, covariance_column) / (posterior_covariance[chosen_index, chosen_index] + ridge)
        posterior_covariance = (posterior_covariance + posterior_covariance.T) * 0.5
        updated_risk = float(np.dot(target_weights[remaining_targets],
                                    np.diag(posterior_covariance)[remaining_targets]))
        if not np.isclose(previous_risk - updated_risk, gain, rtol=1e-6, atol=1e-9):
            raise ArithmeticError('inconsistent conditional risk reduction')
        selected_indices.append(chosen_index)
        plan.append(chosen_index)
    return plan


def conditional_prediction(mean, scales, covariance, ridge, selected_indices, observed_values):
    if not len(selected_indices):
        return mean.copy()
    selected_indices = np.asarray(selected_indices, dtype=np.int64)
    observed_standardized = (np.asarray(observed_values) - mean[selected_indices]) / scales[selected_indices]
    cross_covariance = covariance[:, selected_indices]
    query_covariance = covariance[np.ix_(selected_indices, selected_indices)]
    predicted_standardized = cross_covariance @ np.linalg.solve(query_covariance + ridge * np.eye(len(selected_indices)), observed_standardized)
    prediction = np.clip(mean + scales * predicted_standardized, 0.0, 1.0)
    prediction[selected_indices] = observed_values
    return prediction


def replay_validation(values, mask, mean, scales, covariance, ridge, budget, fixed_target_mask):
    target_weights = scales ** 2
    gains_by_row = []
    plan_cache = {}
    checkpoints = {1, 2, 4, 8, budget}
    for row_index in range(len(values)):
        test_scores = np.where(mask[row_index], values[row_index], np.nan)
        row_gains = []
        for fixed_panel in (False, True):
            available = mask[row_index]
            if fixed_panel:
                query_pool_mask = available & ~fixed_target_mask
                assert not np.any(query_pool_mask & fixed_target_mask)
                paired_target_mask = fixed_target_mask & np.isfinite(test_scores)
                target_mask = paired_target_mask
            else:
                query_pool_mask = available.copy()
                target_mask = available.copy()
            effective_budget = min(budget, int(query_pool_mask.sum()), int(available.sum()) - 1)
            if effective_budget < 1 or not np.any(target_mask):
                continue
            cache_key = (query_pool_mask.tobytes(), target_mask.tobytes(), effective_budget)
            if cache_key not in plan_cache:
                plan_cache[cache_key] = greedy_plan(covariance, ridge, query_pool_mask,
                                                   target_mask, target_weights, effective_budget)
            plan = plan_cache[cache_key]
            selected_indices = np.array([], dtype=np.int64)
            for query_count in range(1, len(plan) + 1):
                if query_count not in checkpoints and query_count != len(plan):
                    continue
                selected_indices = np.asarray(plan[:query_count], dtype=np.int64)
                query_mask = np.zeros_like(available)
                query_mask[selected_indices] = True
                evaluation_mask = target_mask & ~query_mask & np.isfinite(test_scores)
                assert not np.any(query_mask & evaluation_mask)
                if not np.any(evaluation_mask):
                    continue
                prediction = conditional_prediction(mean, scales, covariance, ridge,
                                                    selected_indices, values[row_index, selected_indices])
                errors = prediction[evaluation_mask] - values[row_index, evaluation_mask]
                baseline_errors = mean[evaluation_mask] - values[row_index, evaluation_mask]
                row_gains.append(float(np.mean(errors ** 2 - baseline_errors ** 2)))
            if fixed_panel and len(selected_indices):
                audit_record = {}
                audit_record['selected_indices'] = selected_indices.tolist()
                audit_record['scored_target_indices'] = np.flatnonzero(evaluation_mask).tolist()
                plan_cache[('audit', row_index)] = audit_record
        if row_gains:
            gains_by_row.append(float(np.mean(row_gains)))
    if not gains_by_row:
        return np.inf
    uncertainty = np.std(gains_by_row, ddof=1) / np.sqrt(len(gains_by_row)) if len(gains_by_row) > 1 else 0.0
    return float(np.mean(gains_by_row) + 0.25 * uncertainty)


def learn(values, mask, steps, seed, budget):
    random = np.random.default_rng(seed)
    row_count, column_count = values.shape
    eligible = np.flatnonzero(mask.sum(axis=1) >= 3)
    best_penalty, best_ridge = 16.0, 0.2
    use_mean = False
    if row_count >= 12 and len(eligible) >= 4 and column_count >= 2:
        validation_count = min(32, max(2, row_count // 5), len(eligible))
        validation_indices = random.permutation(eligible)[:validation_count]
        training_mask = np.ones(row_count, dtype=bool)
        training_mask[validation_indices] = False
        statistics = covariance_statistics(values[training_mask], mask[training_mask])
        inner_mean, inner_scales = statistics[:2]
        task_order = random.permutation(column_count)
        fixed_target_mask = np.zeros(column_count, dtype=bool)
        fixed_target_mask[task_order[:max(1, column_count // 2)]] = True
        best_objective = 0.0
        use_mean = True
        penalties = (0.0, 16.0, 64.0) if steps >= 3 else (16.0,)
        for overlap_penalty in penalties:
            covariance = stabilize_covariance(statistics, overlap_penalty)
            for ridge in (0.02, 0.2, 1.0):
                objective = replay_validation(values[validation_indices], mask[validation_indices],
                                              inner_mean, inner_scales, covariance, ridge,
                                              budget, fixed_target_mask)
                if objective < best_objective:
                    best_objective = objective
                    best_penalty, best_ridge = overlap_penalty, ridge
                    use_mean = False
    statistics = covariance_statistics(values, mask)
    mean, scales = statistics[:2]
    if use_mean:
        covariance = np.diag(np.maximum(statistics[4], 1e-6))
    else:
        covariance = stabilize_covariance(statistics, best_penalty)
    return mean, scales, covariance, best_ridge


def handle(request):
    operation = request['op']
    if operation == 'reset':
        _STATE.clear()
        _STATE['seed'] = request['seed']
        return {'ok': True}
    if operation == 'train_start':
        seed = _STATE['seed']
        _STATE.clear()
        _STATE['seed'] = seed
        _STATE.update(values=np.zeros((request['rows'], request['columns'])),
                      mask=np.zeros((request['rows'], request['columns']), dtype=bool),
                      offset=0, steps=request['training_steps'],
                      budget=request['max_queries'])
    elif operation == 'train_chunk':
        shape = tuple(request['shape'])
        values = np.frombuffer(base64.b64decode(request['data']), dtype='<f8').reshape(shape)
        mask = np.frombuffer(base64.b64decode(request['mask']), dtype='u1').reshape(shape).astype(bool)
        offset = request['offset']
        if offset != _STATE['offset']:
            raise ValueError('nonsequential training upload')
        _STATE['values'][offset:offset + shape[0]] = values
        _STATE['mask'][offset:offset + shape[0]] = mask
        _STATE['offset'] += shape[0]
    elif operation == 'train_commit':
        if _STATE['offset'] != len(_STATE['values']):
            raise ValueError('incomplete training upload')
    elif operation == 'fit':
        mean, scales, covariance, ridge = learn(_STATE['values'], _STATE['mask'],
                                               _STATE['steps'], _STATE['seed'], _STATE['budget'])
        _STATE.update(mean=mean, scales=scales, covariance=covariance, ridge=ridge)
    elif operation == 'start':
        _STATE['available'] = np.array(request['availability'], dtype=bool)
        _STATE['queried'] = np.zeros_like(_STATE['available'])
        _STATE['observed'] = np.zeros(_STATE['available'].shape)
        _STATE['plans'] = {}
        _STATE['context_budget'] = request['max_queries']
        _STATE.pop('pending', None)
    elif operation == 'select':
        indices = []
        for row in range(len(_STATE['available'])):
            available = _STATE['available'][row]
            cache_key = available.tobytes()
            if cache_key not in _STATE['plans']:
                _STATE['plans'][cache_key] = greedy_plan(
                    _STATE['covariance'], _STATE['ridge'], available, available,
                    _STATE['scales'] ** 2, _STATE['context_budget'])
            query_count = int(np.sum(_STATE['queried'][row]))
            indices.append(int(_STATE['plans'][cache_key][query_count]))
        _STATE['pending'] = indices
        return {'indices': indices}
    elif operation == 'observe':
        if request['indices'] != _STATE['pending']:
            raise ValueError('unexpected observation')
        for row, (column, value) in enumerate(zip(request['indices'], request['values'])):
            if not _STATE['available'][row, column] or _STATE['queried'][row, column]:
                raise ValueError('unavailable or repeated observation')
            _STATE['queried'][row, column] = True
            _STATE['observed'][row, column] = value
        _STATE.pop('pending')
    elif operation == 'predict':
        predictions = []
        for row in range(len(_STATE['available'])):
            selected_indices = np.flatnonzero(_STATE['queried'][row])
            prediction = conditional_prediction(
                _STATE['mean'], _STATE['scales'], _STATE['covariance'], _STATE['ridge'],
                selected_indices, _STATE['observed'][row, selected_indices])
            predictions.append(prediction.tolist())
        return {'predictions': predictions}
    else:
        raise ValueError('unknown operation')
    return {'ok': True}
