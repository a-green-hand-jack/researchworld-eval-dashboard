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


def _fit_residual_base(values, mask, rank, ridge, sweeps, rng):
    rank = min(rank, *values.shape)
    counts = mask.sum(axis=0)
    means = np.divide((values * mask).sum(axis=0), counts,
                      out=np.full(values.shape[1], 0.5), where=counts > 0)
    centered = values - means
    factors = rng.normal(0, .1, size=(values.shape[1], rank))
    latent = np.zeros((values.shape[0], rank))
    identity = ridge * np.eye(rank)
    for sweep in range(sweeps):
        for row in range(values.shape[0]):
            design = factors[mask[row]]
            latent[row] = np.linalg.solve(identity + design.T @ design,
                                          design.T @ centered[row, mask[row]])
        for column in range(values.shape[1]):
            design = latent[mask[:, column]]
            factors[column] = np.linalg.solve(identity + design.T @ design,
                                              design.T @ centered[mask[:, column], column])
    variance = np.divide((centered * centered * mask).sum(axis=0), counts,
                         out=np.zeros(values.shape[1]), where=counts > 0)
    return dict(means=means, factors=factors, ridge=ridge,
                scales=np.maximum(np.sqrt(variance), 0.025))


def _condition_base(model, selected_indices, observed_scores):
    factors, means = model['factors'], model['means']
    design = factors[selected_indices]
    latent = np.linalg.solve(model['ridge'] * np.eye(factors.shape[1]) + design.T @ design,
                             design.T @ (np.asarray(observed_scores) - means[selected_indices]))
    return np.clip(means + factors @ latent, 0, 1)


def _policy_index(model, selected_indices, available):
    factors = model['factors']
    covariance = np.linalg.inv(model['ridge'] * np.eye(factors.shape[1])
                               + factors[selected_indices].T @ factors[selected_indices])
    cross = factors @ covariance @ factors[available].T
    denominator = 1 + np.sum((factors[available] @ covariance) * factors[available], axis=1)
    gains = np.sum(cross * cross, axis=0) / denominator
    return int(available[int(np.argmax(gains))])


def _donor_predictions(model, donor_scores, selected_indices):
    predictions = np.broadcast_to(model['means'], donor_scores.shape).copy()
    anchor_scores = donor_scores[:, selected_indices]
    anchor_mask = np.isfinite(anchor_scores)
    patterns, pattern_ids = np.unique(anchor_mask, axis=0, return_inverse=True)
    for pattern_index, pattern in enumerate(patterns):
        donor_indices = np.flatnonzero(pattern_ids == pattern_index)
        if not pattern.any():
            continue
        anchors = np.asarray(selected_indices, dtype=int)[pattern]
        design = model['factors'][anchors]
        responses = anchor_scores[donor_indices][:, pattern] - model['means'][anchors]
        latent = np.linalg.solve(model['ridge'] * np.eye(design.shape[1]) + design.T @ design,
                                 design.T @ responses.T)
        predictions[donor_indices] += latent.T @ model['factors'].T
    return np.clip(predictions, 0, 1)


def _build_residual_bank(values, mask, pool_rows, inner_validation_rows,
                         rank, ridge, sweeps, rng):
    """Every donor is excluded from its fit, including within nested validation."""
    donor_pool = rng.permutation(pool_rows)[:128]
    folds = []
    for donor_rows in np.array_split(donor_pool, 2):
        fit_rows = np.setdiff1d(pool_rows, donor_rows)
        assert np.intersect1d(inner_validation_rows, fit_rows).size == 0
        assert np.intersect1d(inner_validation_rows, donor_rows).size == 0
        assert np.intersect1d(fit_rows, donor_rows).size == 0
        if donor_rows.size == 0 or fit_rows.size == 0:
            continue
        model = _fit_residual_base(values[fit_rows], mask[fit_rows], rank, ridge, sweeps, rng)
        donor_scores = np.where(mask[donor_rows], values[donor_rows], np.nan)
        folds.append(dict(model=model, scores=donor_scores))
    if not folds:
        return None
    return dict(folds=folds, scores=np.concatenate([fold['scores'] for fold in folds]), cache={})


def _bank_residuals(bank, selected_indices):
    key = tuple(selected_indices)
    if key not in bank['cache']:
        donor_target_scores = bank['scores']
        donor_base_predictions = np.concatenate([
            _donor_predictions(fold['model'], fold['scores'], selected_indices)
            for fold in bank['folds']])
        donor_residuals = donor_target_scores - donor_base_predictions
        usable_donors = np.isfinite(donor_target_scores) & np.isfinite(donor_base_predictions)
        donor_residuals[~usable_donors] = np.nan
        if len(bank['cache']) >= 8:
            del bank['cache'][next(iter(bank['cache']))]
        bank['cache'][key] = donor_residuals
    return bank['cache'][key]


def _profile_weights(donor_anchor_scores, observed_anchor_scores, anchor_scales,
                      selected_indices, bandwidth):
    common_mask = np.isfinite(donor_anchor_scores) & np.isfinite(observed_anchor_scores)[None, :]
    overlap_count = common_mask.sum(axis=1)
    differences = np.where(common_mask, donor_anchor_scores - observed_anchor_scores[None, :], 0.0)
    squared_distance = np.sum((differences / anchor_scales) ** 2, axis=1)
    squared_distance /= np.maximum(overlap_count, 1)
    neighbor_weights = np.exp(-0.5 * squared_distance / bandwidth ** 2)
    neighbor_weights *= overlap_count / max(len(selected_indices), 1)
    neighbor_weights[overlap_count == 0] = 0.0
    return neighbor_weights


def _bank_weights(bank, selected_indices, observed_anchor_scores, bandwidth):
    return np.concatenate([
        _profile_weights(fold['scores'][:, selected_indices], observed_anchor_scores,
                         fold['model']['scales'][selected_indices], selected_indices, bandwidth)
        for fold in bank['folds']])


def _weighted_median(residuals, weights):
    order = np.argsort(residuals, kind='stable')
    sorted_residuals, sorted_weights = residuals[order], weights[order]
    median_index = np.searchsorted(np.cumsum(sorted_weights), 0.5 * sorted_weights.sum(), side="left")
    return sorted_residuals[min(median_index, len(sorted_residuals) - 1)]


def _correct_target(base_prediction, residuals, target_weights, blend_strength, shrinkage_strength):
    weight_floor = 1e-12
    if target_weights.sum() <= weight_floor: return base_prediction
    effective_neighbors = target_weights.sum() ** 2 / max(np.dot(target_weights, target_weights), weight_floor)
    residual_correction = _weighted_median(residuals, target_weights)
    correction_weight = blend_strength * effective_neighbors / (effective_neighbors + shrinkage_strength)
    prediction = base_prediction + correction_weight * residual_correction
    return prediction


def _residual_summaries(donor_residuals, neighbor_weights):
    columns = donor_residuals.shape[1]
    medians, effective_counts = np.zeros(columns), np.zeros(columns)
    for target in range(columns):
        usable = np.isfinite(donor_residuals[:, target]) & (neighbor_weights > 0)
        target_weights = neighbor_weights[usable]
        weight_sum = target_weights.sum()
        if weight_sum <= 1e-12:
            continue
        medians[target] = _weighted_median(donor_residuals[usable, target], target_weights)
        effective_counts[target] = weight_sum ** 2 / max(np.dot(target_weights, target_weights), 1e-12)
    return medians, effective_counts


def _prepare_residual_correction(values, mask, rank, ridge, sweeps, seed):
    """Bounded nested historical calibration; never receives a new-model score.

    Predeclared local grid: bandwidth (.35, .75, 1.5), shrinkage (4, 16),
    blend (0, .25, .5, 1). At most 512 rows / approximately 196608 cells,
    128 donors, 16 validation rows, two outer folds and two donor folds.
    Auxiliary ALS fits use at most 12 sweeps; the incumbent fit is untouched.
    Validation compares all methods on the same finite unqueried cells at
    budgets 1, 2, 4, 8. Diagnostic results are private, not RPC extensions.
    """
    candidate_blends = (0.0, 0.25, 0.5, 1.0)
    candidate_bandwidths = (0.35, 0.75, 1.5)
    candidate_shrinkages = (4.0, 16.0)
    inactive = dict(bank=None, blend=0.0, bandwidth=0.75, shrinkage=16.0, diagnostics={})
    if values.shape[0] < 12 or values.shape[1] < 2:
        return inactive
    rng = np.random.default_rng(np.random.SeedSequence([seed, 391939]))
    row_limit = min(512, max(64, 196608 // values.shape[1]))
    pool_rows = rng.permutation(values.shape[0])[:row_limit]
    eligible = pool_rows[mask[pool_rows].sum(axis=1) >= 3]
    validation_count = min(16, eligible.size, max(2, pool_rows.size // 4))
    if validation_count < 4:
        return inactive
    validation_rows = eligible[:validation_count]
    auxiliary_sweeps = min(sweeps, 12)
    error_sums = np.zeros((len(candidate_bandwidths), len(candidate_shrinkages), len(candidate_blends)))
    unconditional_errors = np.zeros((len(candidate_shrinkages), len(candidate_blends)))
    direct_errors = np.zeros(len(candidate_bandwidths))
    base_error, target_count = 0.0, 0
    coverage_sum, effective_sum = np.zeros(len(candidate_bandwidths)), np.zeros(len(candidate_bandwidths))
    for inner_validation_rows in np.array_split(validation_rows, 2):
        fit_rows = np.setdiff1d(pool_rows, inner_validation_rows)
        assert np.intersect1d(inner_validation_rows, fit_rows).size == 0
        model = _fit_residual_base(values[fit_rows], mask[fit_rows], rank, ridge, auxiliary_sweeps, rng)
        bank = _build_residual_bank(values, mask, fit_rows, inner_validation_rows,
                                    rank, ridge, auxiliary_sweeps, rng)
        if bank is None:
            return inactive
        for validation_row in inner_validation_rows:
            available = np.flatnonzero(mask[validation_row]).tolist()
            selected_indices, observed_scores = [], []
            for query_count in range(1, min(8, len(available) - 1) + 1):
                remaining = [index for index in available if index not in selected_indices]
                chosen = _policy_index(model, selected_indices, remaining)
                selected_indices.append(chosen)
                observed_scores.append(float(values[validation_row, chosen]))
                if query_count not in (1, 2, 4, 8):
                    continue
                targets = mask[validation_row].copy()
                targets[selected_indices] = False
                truth = values[validation_row, targets]
                base_prediction = _condition_base(model, selected_indices, observed_scores)
                base_error += np.abs(base_prediction[targets] - truth).sum()
                target_count += truth.size
                donor_residuals = _bank_residuals(bank, selected_indices)
                unconditional_median, unconditional_count = _residual_summaries(
                    donor_residuals, np.ones(donor_residuals.shape[0]))
                for shrinkage_index, shrinkage_strength in enumerate(candidate_shrinkages):
                    delta = unconditional_median * unconditional_count / (unconditional_count + shrinkage_strength)
                    for blend_index, blend in enumerate(candidate_blends):
                        prediction = np.clip(base_prediction + blend * delta, 0, 1)
                        unconditional_errors[shrinkage_index, blend_index] += np.abs(prediction[targets] - truth).sum()
                for bandwidth_index, bandwidth in enumerate(candidate_bandwidths):
                    neighbor_weights = _bank_weights(bank, selected_indices, np.asarray(observed_scores), bandwidth)
                    medians, effective_counts = _residual_summaries(donor_residuals, neighbor_weights)
                    coverage_sum[bandwidth_index] += np.count_nonzero(effective_counts[targets])
                    effective_sum[bandwidth_index] += effective_counts[targets].sum()
                    direct_median, direct_count = _residual_summaries(bank['scores'], neighbor_weights)
                    direct_prediction = np.where(direct_count > 0, direct_median, base_prediction)
                    direct_errors[bandwidth_index] += np.abs(direct_prediction[targets] - truth).sum()
                    for shrinkage_index, shrinkage_strength in enumerate(candidate_shrinkages):
                        delta = medians * effective_counts / (effective_counts + shrinkage_strength)
                        for blend_index, blend in enumerate(candidate_blends):
                            prediction = np.clip(base_prediction + blend * delta, 0, 1)
                            error_sums[bandwidth_index, shrinkage_index, blend_index] += np.abs(
                                prediction[targets] - truth).sum()
    if target_count == 0:
        return inactive
    inner_mae = np.full(len(candidate_blends), np.inf)
    best_parameters = [(0.75, 16.0)] * len(candidate_blends)
    for bandwidth_index, bandwidth in enumerate(candidate_bandwidths):
        for shrinkage_index, shrinkage_strength in enumerate(candidate_shrinkages):
            errors = error_sums[bandwidth_index, shrinkage_index] / target_count
            for blend_index, error in enumerate(errors):
                if error < inner_mae[blend_index]:
                    inner_mae[blend_index] = error
                    best_parameters[blend_index] = (bandwidth, shrinkage_strength)
    inner_mae[0] = base_error / target_count
    inner_mae[np.abs(inner_mae - inner_mae[0]) <= 1e-12] = inner_mae[0]
    blend_strength = candidate_blends[int(np.argmin(inner_mae))]
    bandwidth, shrinkage_strength = best_parameters[int(np.argmin(inner_mae))]
    diagnostics = dict(base_mae=base_error / target_count, local_mae=inner_mae.tolist(),
                       unconditional_mae=(unconditional_errors / target_count).tolist(),
                       direct_mae=(direct_errors / target_count).tolist(), target_count=target_count,
                       coverage=(coverage_sum / target_count).tolist(),
                       effective_counts=(effective_sum / target_count).tolist(),
                       validation_rows=validation_count, auxiliary_rows=pool_rows.size)
    bank = None
    if blend_strength > 0:
        bank = _build_residual_bank(values, mask, pool_rows, np.array([], dtype=int),
                                    rank, ridge, auxiliary_sweeps, rng)
    return dict(bank=bank, blend=blend_strength, bandwidth=bandwidth,
                shrinkage=shrinkage_strength, diagnostics=diagnostics)


def _apply_residual_correction(base_prediction, selected_indices, observed_scores, correction):
    if not selected_indices or correction['blend'] == 0.0 or correction['bank'] is None:
        return base_prediction
    bank = correction['bank']
    donor_residuals = _bank_residuals(bank, selected_indices)
    neighbor_weights = _bank_weights(bank, selected_indices, np.asarray(observed_scores), correction['bandwidth'])
    predictions = base_prediction.copy()
    selected = set(selected_indices)
    for target in range(predictions.size):
        if target in selected:
            continue
        usable = np.isfinite(donor_residuals[:, target]) & (neighbor_weights > 0)
        predictions[target] = _correct_target(base_prediction[target], donor_residuals[usable, target],
                                               neighbor_weights[usable], correction['blend'], correction['shrinkage'])
    return np.clip(predictions, 0, 1)


def handle(request):
    operation = request['op']
    if operation == 'reset':
        seed = request['seed']
        if type(seed) is not int or seed < 0:
            raise ValueError('invalid seed')
        _state.clear()
        _state['rng'] = np.random.default_rng(seed)
        _state['residual_seed'] = seed
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
        counts = mask.sum(axis=0)
        means = np.divide((values * mask).sum(axis=0), counts,
                          out=np.full(values.shape[1], 0.5), where=counts > 0)
        centered = values - means
        factors = _state['rng'].normal(0, .1, size=(values.shape[1], rank))
        latent = np.zeros((values.shape[0], rank))
        identity = ridge * np.eye(rank)
        for sweep in range(sweeps):
            for row in range(values.shape[0]):
                design = factors[mask[row]]
                latent[row] = np.linalg.solve(identity + design.T @ design, design.T @ centered[row, mask[row]])
            for column in range(values.shape[1]):
                design = latent[mask[:, column]]
                factors[column] = np.linalg.solve(identity + design.T @ design, design.T @ centered[mask[:, column], column])
        _state.update(means=means, factors=factors, ridge=ridge)
        _state['correction'] = _prepare_residual_correction(
            values, mask, rank, ridge, sweeps, _state['residual_seed'])
        return {'ok': True}
    if operation == 'begin':
        _state['available'] = sorted(request['queryable'])
        _state['observed'] = []
        _state['scores'] = []
        _state['pending'] = None
        return {'ok': True}
    if operation == 'select':
        factors = _state['factors']
        observed = _state['observed']
        available = [index for index in _state['available'] if index not in observed]
        covariance = np.linalg.inv(_state['ridge'] * np.eye(factors.shape[1]) + factors[observed].T @ factors[observed])
        cross = factors @ covariance @ factors[available].T
        denominator = 1 + np.sum((factors[available] @ covariance) * factors[available], axis=1)
        gains = np.sum(cross * cross, axis=0) / denominator
        chosen = int(available[int(np.argmax(gains))])
        _state['pending'] = chosen
        return {'index': chosen}
    if operation == 'observe':
        if request['index'] != _state['pending']:
            raise ValueError('observation without selection')
        _state['observed'].append(request['index'])
        _state['scores'].append(float(request['value']))
        _state['pending'] = None
        return {'ok': True}
    if operation == 'predict':
        factors, means = _state['factors'], _state['means']
        observed = _state['observed']
        design = factors[observed]
        latent = np.linalg.solve(_state['ridge'] * np.eye(factors.shape[1]) + design.T @ design,
                                 design.T @ (np.asarray(_state['scores']) - means[observed]))
        base_prediction = np.clip(means + factors @ latent, 0, 1)
        predictions = _apply_residual_correction(base_prediction, observed, _state['scores'], _state['correction'])
        return {'predictions': predictions.tolist()}
    raise ValueError('unsupported operation')
