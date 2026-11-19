"""Source-only low-rank anchors and uniform-complement residual auditing.

Finite JSON RPC, handle(request)->dict; extra response fields are forbidden.
Every episode: reset, source_chunk (1..2 calls), fit, observe (8,16,32), release.
No files, target IDs, benchmark identities, or private target scores are provided.
Seeds initialize randomness only; arbitrary nonnegative integer seeds are valid.

reset: {op:'reset',seed:int} -> {ok:true}. Clears all buffers and fitted state.
source_chunk: {op,encoding:'base64',dtype:'uint8',shape:[S,N],offset:int,
total_bytes:S*N,chunk_count:int,data:str} -> {ok:true}. C-order contiguous bytes,
in order, at most two chunks, each <=4194304 decoded bytes; S<=512,N<=16384.
The first chunk allocates candidate-owned RAM; no filesystem exchange exists.
fit: {op,mode:'primary'|'no_diversity'|'no_calibration',budgets:[8,16,32],
source_groups:[int]*S} -> {anchors:[int]*32}. Requires complete source bytes.
Anchors are distinct indices in [0,N), ordered nested prefixes for each budget.
Opaque source groups permit source-only grouped CV; target data never calibrates.
observe: {op,budget:int,encoding:'base64',dtype:'uint8',shape:[T,budget],
data:str} -> {encoding:'base64',dtype:'<f8',shape:[T],data:str}.
Input contains ONLY cumulative queried target correctness bits, C-order. Each
checkpoint supplies the complete legal prefix (not additional target queries).
Prediction bytes are finite little-endian float64 probabilities in [0,1].
Targets have no persistent identities: identical queried rows must receive equal
predictions. Evaluator may supply matched constant/copied/permuted observations.
No response flag or internal-state claim contributes to scientific validity.
release: {op:'release'} -> {ok:true}. Releases source and fit RAM. No other ops.

The editable directory may contain method/paper sources. Research conclusions,
PDF/template compliance, genuine ablation interpretation and novelty require
human-readable evidence beyond these operational prediction metrics. Search is
development-only: no comparative baseline threshold is an eligibility gate.
"""

import base64
import numpy as np

STATE = {}


def low_rank_items(source, seed):
    item_mean = source.mean(axis=0)
    centered = source.astype(np.float64) - item_mean
    max_rank = min(16, source.shape[0] - 1, source.shape[1])
    if max_rank < 1:
        return item_mean, np.empty((source.shape[1], 0))
    if source.shape[0] <= 64:
        values, vectors = np.linalg.eigh(centered @ centered.T)
        directions = vectors[:, -max_rank:][:, ::-1]
    else:
        rng = np.random.default_rng(seed)
        width = min(max_rank + 8, source.shape[0], source.shape[1])
        basis, _ = np.linalg.qr(centered @ rng.standard_normal((source.shape[1], width)), mode='reduced')
        for iteration in range(2):
            basis, _ = np.linalg.qr(centered @ (centered.T @ basis), mode='reduced')
        projected = basis.T @ centered
        values, vectors = np.linalg.eigh(projected @ projected.T)
        directions = basis @ vectors[:, -max_rank:][:, ::-1]
    item_loadings = centered.T @ directions / np.sqrt(max(1, source.shape[0] - 1))
    return item_mean, item_loadings


def select_anchors(item_loadings, count, ridge, seed, uniform=False):
    rng = np.random.default_rng(seed)
    if uniform:
        return rng.choice(len(item_loadings), size=count, replace=False)
    inverse = np.eye(item_loadings.shape[1]) / ridge
    chosen = []
    leverage = np.einsum('ij,ij->i', item_loadings @ inverse, item_loadings)
    for step in range(count):
        leverage[chosen] = -np.inf
        index = int(np.argmax(leverage))
        chosen.append(index)
        direction = inverse @ item_loadings[index]
        denominator = 1.0 + item_loadings[index] @ direction
        inverse -= np.outer(direction, direction) / denominator
        leverage -= (item_loadings @ direction) ** 2 / denominator
    return np.asarray(chosen, dtype=np.int64)


def query_order(anchor_indices, n_items, seed):
    remaining_indices = np.setdiff1d(np.arange(n_items), anchor_indices)
    audit_budget = 32 - len(anchor_indices)
    rng = np.random.default_rng(seed)
    audit_indices = rng.choice(remaining_indices, size=audit_budget, replace=False)
    assert set(anchor_indices).isdisjoint(audit_indices)
    return np.concatenate((anchor_indices, audit_indices)), remaining_indices


def frozen_predictions(item_mean, item_loadings, anchor_indices, anchor_answers, ridge):
    anchor_loadings = item_loadings[anchor_indices]
    anchor_precision = anchor_loadings.T @ anchor_loadings + ridge * np.eye(anchor_loadings.shape[1])
    if anchor_answers.ndim == 1:
        latent_state = np.linalg.solve(anchor_precision, anchor_loadings.T @ (anchor_answers - item_mean[anchor_indices]))
        item_predictions = np.clip(item_mean + item_loadings @ latent_state, 0.0, 1.0)
    else:
        latent_state = np.linalg.solve(anchor_precision, anchor_loadings.T @ (anchor_answers - item_mean[anchor_indices]).T)
        item_predictions = np.clip(item_mean + (item_loadings @ latent_state).T, 0.0, 1.0)
    return item_predictions


def residual_estimate(anchor_answers, item_predictions, remaining_indices, audit_indices,
                      audit_answers, correction_weight):
    n_items = len(item_predictions)
    base_score = (anchor_answers.sum() + item_predictions[remaining_indices].sum()) / n_items
    residual_correction = (remaining_indices.size / n_items) * np.mean(audit_answers - item_predictions[audit_indices])
    estimate = base_score + correction_weight * residual_correction
    residuals = audit_answers - item_predictions[audit_indices]
    variance = 0.0 if len(audit_indices) == len(remaining_indices) else (
        (remaining_indices.size / n_items) ** 2
        * (1.0 - len(audit_indices) / remaining_indices.size)
        * np.var(residuals, ddof=1) / len(audit_indices))
    return estimate, variance


def validation_partition(groups, seed):
    rng = np.random.default_rng(seed)
    unique_groups = np.unique(groups)
    if len(unique_groups) < 2:
        return None
    shuffled_groups = rng.permutation(unique_groups)
    validation_group_set = shuffled_groups[:max(1, len(unique_groups) // 4)]
    validation_mask = np.isin(groups, validation_group_set)
    train_indices = np.flatnonzero(~validation_mask)
    validation_indices = np.flatnonzero(validation_mask)
    if len(train_indices) < 3:
        return None
    if len(validation_indices) > 64:
        validation_indices = np.sort(rng.choice(validation_indices, size=64, replace=False))
    train_groups = groups[train_indices]
    validation_groups = groups[validation_indices]
    assert set(train_groups).isdisjoint(validation_groups)
    return train_indices, validation_indices


def paired_group_interval(method_absolute_error, baseline_absolute_error, test_groups, seed):
    paired_error_difference = method_absolute_error - baseline_absolute_error
    unique_test_groups = np.unique(test_groups)
    rng = np.random.default_rng(seed)
    group_sums = np.asarray([paired_error_difference[test_groups == group].sum() for group in unique_test_groups])
    group_sizes = np.asarray([np.sum(test_groups == group) for group in unique_test_groups])
    replicates = []
    for repetition in range(256):
        bootstrap_groups = rng.choice(unique_test_groups, size=len(unique_test_groups), replace=True)
        positions = np.searchsorted(unique_test_groups, bootstrap_groups)
        replicates.append(group_sums[positions].sum() / group_sizes[positions].sum())
    return tuple(float(value) for value in np.quantile(replicates, [0.025, 0.975]))


def tune_configuration(source, groups, seed, uniform):
    partition = validation_partition(groups, seed)
    fallback = (4, 1.0, 4, (0.5, 0.5, 0.5))
    if partition is None:
        return fallback, {'status': 'insufficient_source_groups'}
    train_indices, validation_indices = partition
    item_mean, loadings = low_rank_items(source[train_indices], seed)
    validation = source[validation_indices]
    target = validation.mean(axis=1)
    n_items = source.shape[1]
    best = None
    ranks = sorted(set(min(rank, loadings.shape[1]) for rank in (4, 8, 16)))
    for rank in ranks:
        item_loadings = loadings[:, :rank]
        for ridge in (0.1, 1.0, 10.0):
            for anchor_count in (2, 4, 6):
                anchor_indices = select_anchors(item_loadings, anchor_count, ridge, seed, uniform)
                anchor_answers = validation[:, anchor_indices].astype(np.float64)
                item_predictions = frozen_predictions(item_mean, item_loadings, anchor_indices, anchor_answers, ridge)
                remaining_indices = np.setdiff1d(np.arange(n_items), anchor_indices)
                base = (anchor_answers.sum(axis=1) + item_predictions[:, remaining_indices].sum(axis=1)) / n_items
                corrections = []
                for query_seed in range(3):
                    order, _ = query_order(anchor_indices, n_items, seed + 104729 * (query_seed + 1))
                    seed_corrections = []
                    for budget in (8, 16, 32):
                        audit_indices = order[anchor_count:budget]
                        residual = validation[:, audit_indices] - item_predictions[:, audit_indices]
                        seed_corrections.append((len(remaining_indices) / n_items) * residual.mean(axis=1))
                    corrections.append(seed_corrections)
                corrections = np.asarray(corrections)
                weights = []
                losses = []
                absolute_errors = []
                baseline_errors = []
                for checkpoint, budget in enumerate((8, 16, 32)):
                    candidates = []
                    for weight in (0.0, 0.5, 1.0):
                        estimates = np.clip(base + weight * corrections[:, checkpoint], 0.0, 1.0)
                        error = estimates - target
                        absolute_error = np.abs(error).mean(axis=0)
                        loss = float(absolute_error.mean() + 0.25 * np.sqrt(np.mean(error ** 2)))
                        candidates.append((loss, weight, absolute_error))
                    chosen = candidates[2] if budget == n_items else min(candidates, key=lambda candidate: (candidate[0], candidate[1]))
                    losses.append(chosen[0])
                    weights.append(chosen[1])
                    absolute_errors.append(chosen[2])
                    baseline_errors.append(candidates[0][2])
                key = (float(np.mean(losses)), rank, ridge, anchor_count, tuple(weights))
                if best is None or key < best[0]:
                    best = (key, np.mean(absolute_errors, axis=0), np.mean(baseline_errors, axis=0))
    key, method_error, baseline_error = best
    interval = paired_group_interval(method_error, baseline_error, groups[validation_indices], seed)
    return (key[1], key[2], key[3], key[4]), {
        'status': 'source_group_holdout_only',
        'validation_rows': len(validation_indices),
        'validation_groups': len(np.unique(groups[validation_indices])),
        'selected_vs_weight_zero_mae_interval': interval,
        'post_selection_interval': True,
    }


def fit_models(source, groups, seed, uniform):
    configuration, validation = tune_configuration(source, groups, seed, uniform)
    rank, ridge, anchor_count, weights = configuration
    item_mean, loadings = low_rank_items(source, seed)
    item_loadings = loadings[:, :rank]
    anchor_indices = select_anchors(item_loadings, anchor_count, ridge, seed, uniform)
    order, remaining_indices = query_order(anchor_indices, source.shape[1], seed + 32452843)
    return order, {
        'item_mean': item_mean,
        'item_loadings': item_loadings,
        'anchor_indices': anchor_indices,
        'remaining_indices': remaining_indices,
        'ridge': ridge,
        'weights': dict(zip((8, 16, 32), weights)),
        'source_validation': validation,
    }


def handle(request):
    operation = request['op']
    if operation == 'reset':
        if type(request['seed']) is not int or request['seed'] < 0:
            raise ValueError('invalid seed')
        STATE.clear()
        STATE['seed'] = request['seed']
        STATE['received'] = 0
        return {'ok': True}
    if operation == 'source_chunk':
        shape = request['shape']
        total = request['total_bytes']
        if request['offset'] != STATE['received'] or total != int(np.prod(shape)) or total > 8388608:
            raise ValueError('invalid source transfer')
        if request['offset'] == 0:
            STATE['buffer'] = bytearray(total)
            STATE['shape'] = shape
        chunk = base64.b64decode(request['data'], validate=True)
        offset = STATE['received']
        if not chunk or len(chunk) > 4194304 or offset + len(chunk) > total:
            raise ValueError('invalid chunk')
        STATE['buffer'][offset:offset + len(chunk)] = chunk
        STATE['received'] += len(chunk)
        return {'ok': True}
    if operation == 'fit':
        source = np.frombuffer(STATE['buffer'], dtype=np.uint8).reshape(STATE['shape'])
        if STATE['received'] != source.size or not np.isin(source, [0, 1]).all():
            raise ValueError('incomplete or invalid source')
        groups = np.asarray(request['source_groups'])
        if groups.shape != (len(source),) or source.shape[1] < 32:
            raise ValueError('invalid source groups or item count')
        anchors, models = fit_models(source, groups, STATE['seed'], request['mode'] == 'no_diversity')
        STATE['anchors'] = anchors
        STATE['models'] = models
        STATE['mode'] = request['mode']
        return {'anchors': anchors.tolist()}
    if operation == 'observe':
        budget = request['budget']
        observations = np.frombuffer(base64.b64decode(request['data'], validate=True), dtype=np.uint8).reshape(request['shape']).astype(float)
        if STATE['mode'] == 'no_calibration':
            predictions = observations.mean(axis=1)
        else:
            model = STATE['models']
            anchor_indices = model['anchor_indices']
            anchor_count = len(anchor_indices)
            audit_indices = STATE['anchors'][anchor_count:budget]
            assert set(anchor_indices).isdisjoint(audit_indices)
            predictions = np.empty(len(observations), dtype=np.float64)
            for row, answers in enumerate(observations):
                item_predictions = frozen_predictions(model['item_mean'], model['item_loadings'],
                                                      anchor_indices, answers[:anchor_count], model['ridge'])
                correction_weight = 1.0 if budget == len(item_predictions) else model['weights'][budget]
                predictions[row], variance = residual_estimate(
                    answers[:anchor_count], item_predictions, model['remaining_indices'],
                    audit_indices, answers[anchor_count:budget], correction_weight)
        predictions = np.clip(predictions, 0, 1).astype('<f8')
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [len(predictions)], 'data': base64.b64encode(predictions.tobytes()).decode('ascii')}
    if operation == 'release':
        STATE.clear()
        return {'ok': True}
    raise ValueError('unknown operation')
