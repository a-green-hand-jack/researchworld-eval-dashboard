"""CPU score-matrix prediction starter; only handle(request) is public.

All requests/responses are finite JSON objects. Additional response keys are forbidden.
All indices are zero-based, episode-local and opaque; no filenames or model IDs are used.
reset accepts ANY nonnegative integer seed and returns exactly {"ok": true}; it clears
all state. Seeds initialize randomness, never choose a workload or evaluation plane.

History upload (one per episode): upload_start fields shape=[M,N], dtype="float64",
byteorder="little", mask_dtype="uint8", encoding="base64", layout="values_then_mask",
nbytes=9*M*N, chunks=C. Bounds: 1<=M,N<=4096, 1<=C<=64, <=256 MiB logical data.
Returns {"ok": true}. upload_chunk fields index (sequential 0..C-1) and data (base64
string, <=4 MiB decoded). Returns {"ok": true}. upload_commit has no other fields,
returns {"ok": true}. Bytes are contiguous little-endian float64 [M,N] values then
uint8 [M,N] observed mask, row major. Missing entries are zero with mask=0. Scores
have already been normalized by public metric ranges to [0,1]. Buffers are private
memory, never shared files. At most one upload is live; outstanding transfer <=512 MiB.

fit fields rank (positive integer <=16), sweeps (positive integer <=50), ridge
(positive float). Returns {"ok": true}. These are requested settings, not scientific
evidence of internal computation. Training uses history only. Fit/preprocessing must
remain immutable until reset; no observations from new models may enter history.

begin fields trajectory (nonnegative int), queryable (distinct integer indices in
0..N-1, at least eight), budget=8. Returns {"ok": true}. Clears only the current
new-model observations, never fitted history. select has no other fields; returns
exactly {"index": int}, an available not-yet-selected queryable index. observe fields
index (the most recently selected index) and value (finite [0,1] score); returns
{"ok": true}. Only that score is authorized feedback. select/observe repeats eight
times; predict is called after 1,2,4,8 observations and returns exactly
{"predictions": [N finite floats in [0,1]]}. Predictions cover ALL N columns, including
unobserved ones; target membership and masks are never disclosed. Predict must not
consume future observations. A new begin discards the preceding trajectory state.

The same operations/settings apply in reduced smoke and all production workloads.
Evaluator-owned constant-history, independent-column permutation, constant/copy
baselines, and reset replay test this actual implementation under matched budgets.
Controls have no required direction of error change; null findings are legitimate.
No state flags, self-reported metrics, file outputs or undocumented response keys.
No adaptivity restriction: selection may be nonadaptive; inference uses observations.
Each complete JSON message must be strictly below 64 MiB (chunks target below 8 MiB).
"""
import base64
import math

import numpy as np


_state = {}


def _covariance_statistics(values, mask):
    numeric_mask = mask.astype(np.float64)
    masked_values = np.where(mask, values, 0.0)
    counts = numeric_mask.sum(axis=0)
    means = np.divide(masked_values.sum(axis=0), counts,
                      out=np.full(values.shape[1], 0.5), where=counts > 0)
    pair_counts = numeric_mask.T @ numeric_mask
    pair_sums = masked_values.T @ numeric_mask
    pair_products = masked_values.T @ masked_values
    pair_corrections = np.divide(pair_sums * pair_sums.T, pair_counts,
                                 out=np.zeros_like(pair_counts), where=pair_counts > 0)
    pairwise_covariance = np.divide(pair_products - pair_corrections, pair_counts - 1,
                                    out=np.zeros_like(pair_counts), where=pair_counts > 1)
    marginal_variances = np.maximum(np.diag(pairwise_covariance).copy(), 0.0)
    supported_variances = marginal_variances[counts > 1]
    fallback_variance = float(np.median(supported_variances)) if supported_variances.size else 0.01
    marginal_variances[counts < 2] = fallback_variance
    covariance_bounds = np.sqrt(np.outer(marginal_variances, marginal_variances))
    pairwise_covariance = np.clip(pairwise_covariance, -covariance_bounds, covariance_bounds)
    pairwise_covariance = (pairwise_covariance + pairwise_covariance.T) * 0.5
    return means, pairwise_covariance, pair_counts, marginal_variances


def _regularize_covariance(statistics, shrinkage_strength, variance_floor):
    if not math.isfinite(shrinkage_strength) or shrinkage_strength <= 0 or variance_floor <= 0:
        raise ValueError('invalid covariance regularization')
    means, raw_covariance, pair_counts, marginal_variances = statistics
    pairwise_covariance = raw_covariance.copy()
    pairwise_covariance *= pair_counts / (pair_counts + shrinkage_strength)
    np.fill_diagonal(pairwise_covariance, marginal_variances)
    pairwise_covariance = (pairwise_covariance + pairwise_covariance.T) * 0.5
    eigenvalues, eigenvectors = np.linalg.eigh(pairwise_covariance)
    score_covariance = (eigenvectors * np.maximum(eigenvalues, variance_floor)) @ eigenvectors.T
    diagonal_scale = np.sqrt(np.maximum(marginal_variances, variance_floor)
                             / np.maximum(np.diag(score_covariance), variance_floor))
    score_covariance *= diagonal_scale[:, None] * diagonal_scale[None, :]
    score_covariance = (score_covariance + score_covariance.T) * 0.5
    return means.copy(), score_covariance


def _select_transfer(posterior_covariance, available, selected_mask, variance_floor):
    candidates = np.flatnonzero(available & ~selected_mask)
    if not candidates.size:
        raise ValueError('no available query')
    unqueried_indices = np.flatnonzero(~selected_mask)
    if candidates.size <= 64:
        transfer_gains = []
        for candidate in candidates:
            remaining_targets = np.setdiff1d(unqueried_indices, [candidate])
            transfer_gain = np.sum(posterior_covariance[remaining_targets, candidate] ** 2) / max(posterior_covariance[candidate, candidate], variance_floor)
            transfer_gains.append(transfer_gain)
        return int(candidates[int(np.argmax(transfer_gains))])
    covariance_columns = posterior_covariance[np.ix_(unqueried_indices, candidates)]
    candidate_variances = posterior_covariance[candidates, candidates]
    transfer_gains = np.maximum(np.sum(covariance_columns ** 2, axis=0)
                                - candidate_variances ** 2, 0.0)
    transfer_gains /= np.maximum(candidate_variances, variance_floor)
    return int(candidates[int(np.argmax(transfer_gains))])


def _condition(posterior_mean, posterior_covariance, candidate, observed_score, variance_floor):
    covariance_column = posterior_covariance[:, candidate].copy()
    observation_variance = max(float(posterior_covariance[candidate, candidate]), variance_floor)
    posterior_mean += covariance_column * (observed_score - posterior_mean[candidate]) / observation_variance
    posterior_covariance -= np.outer(covariance_column, covariance_column) / observation_variance
    posterior_covariance[:] = (posterior_covariance + posterior_covariance.T) * 0.5
    np.fill_diagonal(posterior_covariance, np.maximum(np.diag(posterior_covariance), 0.0))
    posterior_mean[candidate] = observed_score
    posterior_covariance[candidate, :] = 0.0
    posterior_covariance[:, candidate] = 0.0


def _validation_loss(means, covariance, values, mask, query_pool, audit_targets, variance_floor):
    assert set(query_pool).isdisjoint(audit_targets)
    model_losses = []
    for validation_scores, observed in zip(values, mask):
        test_scores = np.where(observed, validation_scores, np.nan)
        audit_observed = np.isfinite(test_scores[audit_targets])
        available = np.zeros(means.size, dtype=bool)
        available[query_pool] = observed[query_pool]
        budget = min(8, int(available.sum()))
        if budget == 0 or not audit_observed.any():
            continue
        posterior_mean = means.copy()
        posterior_covariance = covariance.copy()
        selected_mask = np.zeros(means.size, dtype=bool)
        selected_indices = []
        checkpoint_losses = []
        for step in range(1, budget + 1):
            candidate = _select_transfer(posterior_covariance, available, selected_mask, variance_floor)
            selected_indices.append(candidate)
            selected_mask[candidate] = True
            _condition(posterior_mean, posterior_covariance, candidate,
                       float(test_scores[candidate]), variance_floor)
            if step in (1, 2, 4, 8):
                predictions = np.clip(posterior_mean, 0.0, 1.0)
                audit_errors = predictions[audit_targets][audit_observed] - test_scores[audit_targets][audit_observed]
                checkpoint_losses.append(float(np.mean(np.abs(audit_errors))))
        assert len(selected_indices) == budget
        assert len(set(selected_indices)) == budget
        assert set(selected_indices).issubset(query_pool)
        model_losses.append(float(np.mean(checkpoint_losses)))
    return float(np.mean(model_losses)) if model_losses else math.inf


def _choose_shrinkage(values, mask, variance_floor, rng):
    rows, columns = values.shape
    fallback_strength = max(8.0, 0.1 * rows)
    if rows < 8 or columns < 3:
        return fallback_strength
    row_order = rng.permutation(rows)
    validation_count = min(32, max(2, rows // 5))
    validation_indices = row_order[:validation_count]
    train_indices = row_order[validation_count:]
    assert set(train_indices).isdisjoint(validation_indices)
    eligible_columns = np.flatnonzero(mask[train_indices].sum(axis=0) >= 2)
    if eligible_columns.size < 3:
        return fallback_strength
    column_indices = np.sort(rng.choice(eligible_columns, size=min(192, eligible_columns.size), replace=False))
    training_scores = values[np.ix_(train_indices, column_indices)].copy()
    training_mask = mask[np.ix_(train_indices, column_indices)]
    statistics = _covariance_statistics(training_scores, training_mask)
    validation_values = values[np.ix_(validation_indices, column_indices)]
    validation_mask = mask[np.ix_(validation_indices, column_indices)]
    column_order = rng.permutation(column_indices.size)
    audit_count = max(1, column_indices.size // 3)
    audit_targets = np.sort(column_order[:audit_count])
    query_pool = np.sort(column_order[audit_count:])
    training_count = train_indices.size
    strengths = sorted(set((2.0, max(8.0, 0.1 * training_count),
                            max(32.0, 0.5 * training_count),
                            max(128.0, 2.0 * training_count),
                            max(1e6, 1e4 * training_count))), reverse=True)
    best_loss = math.inf
    best_strength = fallback_strength
    for shrinkage_strength in strengths:
        means, covariance = _regularize_covariance(statistics, shrinkage_strength, variance_floor)
        loss = _validation_loss(means, covariance, validation_values, validation_mask,
                                query_pool, audit_targets, variance_floor)
        if loss < best_loss - 1e-12:
            best_loss = loss
            best_strength = shrinkage_strength * rows / training_count
    return best_strength


def handle(request):
    operation = request['op']
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or seed < 0:
            raise ValueError('invalid seed')
        _state.clear()
        _state['rng'] = np.random.default_rng(seed)
        return {'ok': True}
    if operation == 'upload_start':
        rows, columns = request['shape']
        if (any(type(count) is not int or not 1 <= count <= 4096 for count in [rows, columns])
                or request['nbytes'] != 9 * rows * columns or request['nbytes'] > 256 * 1024**2
                or not 1 <= request['chunks'] <= 64
                or [request[key] for key in ['dtype', 'byteorder', 'mask_dtype', 'encoding', 'layout']]
                != ['float64', 'little', 'uint8', 'base64', 'values_then_mask']):
            raise ValueError('invalid upload')
        _state['upload'] = bytearray()
        _state['metadata'] = dict(request)
        _state['next_chunk'] = 0
        return {'ok': True}
    if operation == 'upload_chunk':
        metadata = _state['metadata']
        if request['index'] != _state['next_chunk'] or request['index'] >= metadata['chunks']:
            raise ValueError('invalid chunk order')
        decoded = base64.b64decode(request['data'], validate=True)
        if len(decoded) > 4 * 1024**2 or len(_state['upload']) + len(decoded) > metadata['nbytes']:
            raise ValueError('invalid chunk size')
        _state['upload'].extend(decoded)
        _state['next_chunk'] += 1
        return {'ok': True}
    if operation == 'upload_commit':
        metadata = _state['metadata']
        if len(_state['upload']) != metadata['nbytes'] or _state['next_chunk'] != metadata['chunks']:
            raise ValueError('incomplete upload')
        rows, columns = metadata['shape']
        count = rows * columns
        _state['values'] = np.frombuffer(_state['upload'], dtype='<f8', count=count).reshape(rows, columns).copy()
        _state['mask'] = np.frombuffer(_state['upload'], dtype='u1', offset=8*count).reshape(rows, columns).copy()
        if (not np.isfinite(_state['values']).all() or not np.isin(_state['mask'], [0, 1]).all()
                or np.any((_state['values'] < 0) | (_state['values'] > 1))):
            raise ValueError('invalid history')
        del _state['upload']
        return {'ok': True}
    if operation == 'fit':
        values, mask = _state['values'], _state['mask'].astype(bool)
        rank = min(int(request['rank']), *values.shape)
        ridge = float(request['ridge'])
        sweeps = int(request['sweeps'])
        if not 1 <= rank <= 16 or not 1 <= sweeps <= 50 or not math.isfinite(ridge) or ridge <= 0:
            raise ValueError('invalid fitting settings')
        variance_floor = max(1e-10, min(1e-6, ridge * 1e-6))
        shrinkage_strength = _choose_shrinkage(values, mask, variance_floor, _state['rng'])
        means, score_covariance = _regularize_covariance(
            _covariance_statistics(values, mask), shrinkage_strength, variance_floor)
        means.setflags(write=False)
        score_covariance.setflags(write=False)
        _state.update(means=means, score_covariance=score_covariance,
                      variance_floor=variance_floor)
        return {'ok': True}
    if operation == 'begin':
        queryable = request['queryable']
        columns = _state['means'].size
        budget = request['budget']
        if (budget != 8 or len(queryable) < budget or len(set(queryable)) != len(queryable)
                or any(type(index) is not int or not 0 <= index < columns for index in queryable)):
            raise ValueError('invalid query pool')
        available = np.zeros(columns, dtype=bool)
        available[queryable] = True
        _state['available'] = available
        _state['budget'] = budget
        _state['selected_mask'] = np.zeros(columns, dtype=bool)
        _state['posterior_mean'] = _state['means'].copy()
        _state['posterior_covariance'] = _state['score_covariance'].copy()
        _state['observed'] = []
        _state['pending'] = None
        return {'ok': True}
    if operation == 'select':
        if _state['pending'] is not None or len(_state['observed']) >= _state['budget']:
            raise ValueError('invalid selection transition')
        chosen = _select_transfer(_state['posterior_covariance'], _state['available'],
                                  _state['selected_mask'], _state['variance_floor'])
        _state['pending'] = chosen
        return {'index': chosen}
    if operation == 'observe':
        if _state['pending'] is None or request['index'] != _state['pending']:
            raise ValueError('observation without selection')
        candidate = request['index']
        observed_score = float(request['value'])
        if not math.isfinite(observed_score) or not 0 <= observed_score <= 1:
            raise ValueError('invalid observation')
        _condition(_state['posterior_mean'], _state['posterior_covariance'],
                   candidate, observed_score, _state['variance_floor'])
        _state['selected_mask'][candidate] = True
        _state['observed'].append(candidate)
        selected_indices = _state['observed']
        assert len(set(selected_indices)) == len(selected_indices)
        if len(selected_indices) == _state['budget']:
            budget = _state['budget']
            assert len(selected_indices) == budget
            assert len(set(selected_indices)) == budget
        _state['pending'] = None
        return {'ok': True}
    if operation == 'predict':
        if _state['pending'] is not None:
            raise ValueError('prediction before observation')
        return {'predictions': np.clip(_state['posterior_mean'], 0, 1).tolist()}
    raise ValueError('unsupported operation')
