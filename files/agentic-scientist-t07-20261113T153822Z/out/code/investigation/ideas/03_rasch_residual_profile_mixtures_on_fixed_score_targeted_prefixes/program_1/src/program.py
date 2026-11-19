"""Score-targeted prefixes with group-balanced Rasch-residual mixtures.

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


def expit(values):
    return 1.0 / (1.0 + np.exp(-values))


def logit(values):
    return np.log(values) - np.log1p(-values)


def logsumexp(values, axis=None, keepdims=False):
    maximum = np.max(values, axis=axis, keepdims=True)
    result = maximum + np.log(np.exp(values - maximum).sum(axis=axis, keepdims=True))
    if keepdims:
        return result
    return np.squeeze(result, axis=axis)


def group_weights(source_groups):
    unique, group_inverse, group_counts = np.unique(source_groups, return_inverse=True, return_counts=True)
    return 1.0 / (len(unique) * group_counts[group_inverse])


def select_anchors(source, source_groups, seed, count, uniform=False):
    random = np.random.default_rng(seed)
    if uniform:
        query_order = random.permutation(source.shape[1])[:count]
    else:
        weights = group_weights(source_groups)
        source_scores = source.astype(np.float64)
        item_mean = weights @ source_scores
        full_scores = source_scores.mean(axis=1)
        centered = (source_scores - item_mean) * np.sqrt(weights[:, None])
        score_centered = (full_scores - weights @ full_scores) * np.sqrt(weights)
        score_covariance = centered.T @ score_centered
        noise = 0.1 * np.maximum(item_mean * (1.0 - item_mean), 0.05)
        conditional_variance = np.sum(centered * centered, axis=0) + noise
        factors = np.zeros((source.shape[1], count), dtype=np.float64)
        selected = np.zeros(source.shape[1], dtype=bool)
        query_order = np.empty(count, dtype=np.int64)
        for step in range(count):
            gains = score_covariance ** 2 / np.maximum(conditional_variance, 1e-12)
            gains[selected] = -np.inf
            current = int(np.argmax(gains))
            query_order[step] = current
            pivot = np.sqrt(max(conditional_variance[current], 1e-12))
            column = centered.T @ centered[:, current]
            if step:
                column -= factors[:, :step] @ factors[current, :step]
            column[current] += noise[current]
            column /= pivot
            score_covariance -= column * (score_covariance[current] / pivot)
            conditional_variance = np.maximum(conditional_variance - column ** 2, 1e-12)
            factors[:, step] = column
            selected[current] = True
    assert np.unique(query_order).size == query_order.size
    return query_order


def ridge_fit(features, target, strength):
    center = features.mean(axis=0)
    mean = float(target.mean())
    centered = features - center
    coefficient = np.linalg.solve(centered.T @ centered + strength * np.eye(features.shape[1]), centered.T @ (target - mean))
    return center, mean, coefficient


def fit_rasch(source_scores, source_groups):
    weights = group_weights(source_groups)
    source_ability = logit((source_scores.sum(axis=1) + 0.5) / (source_scores.shape[1] + 1.0))
    item_mean = np.clip(weights @ source_scores, 1e-4, 1.0 - 1e-4)
    item_difficulty = weights @ source_ability - logit(item_mean)
    for iteration in range(8):
        probabilities = expit(source_ability[:, None] - item_difficulty[None, :])
        gradient = weights @ (source_scores - probabilities) + 0.01 * item_difficulty
        curvature = weights @ (probabilities * (1.0 - probabilities)) + 0.01
        item_difficulty -= np.clip(gradient / curvature, -2.0, 2.0)
    rasch_probs = expit(source_ability[:, None] - item_difficulty[None, :])
    return rasch_probs


def make_profile(source_scores, rasch_probs, residual_weight):
    probability_floor = 1e-6
    profile_probs = np.clip((1.0 - residual_weight) * rasch_probs + residual_weight * source_scores, probability_floor, 1.0 - probability_floor)
    return profile_probs


def particle_prior(source_groups):
    unique, group_inverse, group_counts = np.unique(source_groups, return_inverse=True, return_counts=True)
    n_groups = len(unique)
    source_log_prior = -np.log(n_groups) - np.log(group_counts[group_inverse])
    offset_log_prior = np.log(np.array([1.0, 4.0, 6.0, 4.0, 1.0]) / 16.0)
    particle_log_prior = (source_log_prior[:, None] + offset_log_prior[None, :]).reshape(-1)
    assert np.isclose(np.exp(particle_log_prior).sum(), 1.0)
    group_mass = np.bincount(group_inverse, weights=np.exp(source_log_prior))
    assert np.allclose(group_mass, 1.0 / n_groups)
    return particle_log_prior


def make_particles(profile_probs, offset_scale):
    n_items = profile_probs.shape[1]
    ability_offsets = offset_scale * np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    particle_probs = expit(logit(profile_probs)[:, None, :] + ability_offsets[None, :, None]).reshape(-1, n_items)
    return particle_probs


def particle_summary(profile_probs, offset_scale, query_order):
    ability_offsets = offset_scale * np.array([-2.0, -1.0, 0.0, 1.0, 2.0])
    n_rows, n_items = profile_probs.shape
    selected_probs = expit(logit(profile_probs[:, query_order])[:, None, :] + ability_offsets[None, :, None]).reshape(-1, len(query_order))
    if offset_scale == 0.0:
        totals = np.repeat(profile_probs.sum(axis=1), 5)
    else:
        totals = np.zeros(n_rows * 5, dtype=np.float64)
        for start in range(0, n_items, 512):
            block = logit(profile_probs[:, start:start + 512])
            probabilities = expit(block[:, None, :] + ability_offsets[None, :, None])
            totals += probabilities.sum(axis=2).reshape(-1)
    return selected_probs, totals


def predict_summary(observed_probs, particle_log_prior, totals, n_items, observations):
    log_failure = np.log1p(-observed_probs)
    log_success = np.log(observed_probs)
    log_posterior = observations @ (log_success - log_failure).T
    log_posterior += log_failure.sum(axis=1)[None, :] + particle_log_prior[None, :]
    posterior_weights = np.exp(log_posterior - logsumexp(log_posterior, axis=1, keepdims=True))
    assert np.allclose(posterior_weights.sum(axis=1), 1.0)
    remaining_totals = totals - observed_probs.sum(axis=1)
    predictions = (observations.sum(axis=1) + posterior_weights @ remaining_totals) / n_items
    assert np.isfinite(predictions).all()
    return np.clip(predictions, 0.0, 1.0)


def predict_particles(particle_probs, particle_log_prior, totals, observed_indices, observations):
    assert np.unique(observed_indices).size == observed_indices.size
    n_items = particle_probs.shape[1]
    observed_probs = particle_probs[:, observed_indices]
    if len(observations) != 1:
        return predict_summary(observed_probs, particle_log_prior, totals, n_items, observations)
    observed_answers = observations[0]
    log_likelihood = (observed_answers[None, :] * np.log(observed_probs) + (1.0 - observed_answers[None, :]) * np.log1p(-observed_probs)).sum(axis=1)
    log_posterior = particle_log_prior + log_likelihood
    posterior_weights = np.exp(log_posterior - logsumexp(log_posterior))
    assert np.isclose(posterior_weights.sum(), 1.0)
    remaining_mask = np.ones(n_items, dtype=bool)
    remaining_mask[observed_indices] = False
    particle_prediction = (observed_answers.sum() + posterior_weights @ particle_probs[:, remaining_mask].sum(axis=1)) / n_items
    assert np.isfinite(particle_prediction)
    return np.clip(np.array([particle_prediction]), 0.0, 1.0)


def linear_predict(model, observations):
    center, mean, coefficient, shrinkage = model
    return np.clip(mean + shrinkage * ((observations - center) @ coefficient), 0.0, 1.0)


def grouped_mae(predictions, target, validation_groups):
    absolute_errors = np.abs(predictions - target[None, :]).mean(axis=0)
    group_mae = np.array([absolute_errors[validation_groups == group].mean() for group in np.unique(validation_groups)])
    validation_risk = group_mae.mean()
    return float(validation_risk)


def fit_models(source, source_groups, budgets, seed, uniform=False):
    target = source.mean(axis=1)
    strengths = (0.1, 1.0, 10.0)
    shrinkages = (0.0, 0.5, 1.0)
    residual_weight_grid = (0.0, 0.5, 0.75)
    offset_scale_grid = (0.0, 0.5)
    mixture_weight_grid = (0.0, 0.5, 1.0)
    configurations = [(residual_weight, offset_scale) for residual_weight in residual_weight_grid for offset_scale in offset_scale_grid]
    linear_configurations = [(strength, shrinkage) for strength in strengths for shrinkage in shrinkages]
    best_linear = [(1.0, 1.0)] * len(budgets)
    best_configuration = (0.0, 0.0, 0.0)
    unique_groups = np.unique(source_groups)
    if len(unique_groups) >= 2:
        random = np.random.default_rng(seed)
        fold_groups = np.array_split(random.permutation(unique_groups), min(3, len(unique_groups)))
        linear_oof = np.empty((len(linear_configurations), len(budgets), len(source)), dtype=np.float64)
        particle_oof = np.empty((len(configurations), len(budgets), len(source)), dtype=np.float64)
        for held_groups in fold_groups:
            validation_indices = np.flatnonzero(np.isin(source_groups, held_groups))
            fit_indices = np.flatnonzero(~np.isin(source_groups, held_groups))
            assert set(source_groups[fit_indices]).isdisjoint(set(source_groups[validation_indices]))
            fit_source = source[fit_indices].astype(np.float64)
            fit_groups = source_groups[fit_indices]
            linear_query_order = select_anchors(fit_source, fit_groups, seed, max(budgets), uniform)
            mixture_query_order = linear_query_order.copy()
            assert np.array_equal(linear_query_order, mixture_query_order)
            query_order = linear_query_order
            assert np.unique(query_order).size == query_order.size
            for budget_index, budget in enumerate(budgets):
                fit_features = fit_source[:, linear_query_order[:budget]]
                validation_features = source[validation_indices][:, linear_query_order[:budget]].astype(np.float64)
                for strength_index, strength in enumerate(strengths):
                    fitted = ridge_fit(fit_features, target[fit_indices], strength)
                    for shrinkage_index, shrinkage in enumerate(shrinkages):
                        config_index = strength_index * len(shrinkages) + shrinkage_index
                        linear_oof[config_index, budget_index, validation_indices] = linear_predict((*fitted, shrinkage), validation_features)
            rasch_probs = fit_rasch(fit_source, fit_groups)
            particle_log_prior = particle_prior(fit_groups)
            for residual_weight in residual_weight_grid:
                profile_probs = make_profile(fit_source, rasch_probs, residual_weight)
                for offset_scale in offset_scale_grid:
                    config_index = configurations.index((residual_weight, offset_scale))
                    selected_probs, totals = particle_summary(profile_probs, offset_scale, mixture_query_order)
                    for budget_index, budget in enumerate(budgets):
                        observations = source[validation_indices][:, mixture_query_order[:budget]].astype(np.float64)
                        particle_oof[config_index, budget_index, validation_indices] = predict_summary(selected_probs[:, :budget], particle_log_prior, totals, source.shape[1], observations)
        validation_weights = group_weights(source_groups)
        linear_prediction = np.empty((len(budgets), len(source)), dtype=np.float64)
        for budget_index, budget in enumerate(budgets):
            losses = np.sum((linear_oof[:, budget_index, :] - target[None, :]) ** 2 * validation_weights[None, :], axis=1)
            best_index = int(np.argmin(losses))
            best_linear[budget_index] = linear_configurations[best_index]
            linear_prediction[budget_index] = linear_oof[best_index, budget_index]
        best_risk = grouped_mae(linear_prediction, target, source_groups)
        for config_index, (residual_weight, offset_scale) in enumerate(configurations):
            particle_prediction = particle_oof[config_index]
            for mixture_weight in mixture_weight_grid:
                blended_prediction = (1.0 - mixture_weight) * linear_prediction + mixture_weight * particle_prediction
                validation_risk = grouped_mae(blended_prediction, target, source_groups)
                candidate = (mixture_weight, offset_scale, residual_weight)
                if validation_risk < best_risk - 1e-12 or (abs(validation_risk - best_risk) <= 1e-12 and candidate < best_configuration):
                    best_risk = validation_risk
                    best_configuration = candidate
    linear_query_order = select_anchors(source, source_groups, seed, max(budgets), uniform)
    mixture_query_order = linear_query_order.copy()
    assert np.array_equal(linear_query_order, mixture_query_order)
    query_order = linear_query_order
    assert np.unique(query_order).size == query_order.size
    models = {}
    for budget_index, budget in enumerate(budgets):
        strength, shrinkage = best_linear[budget_index]
        models[budget] = (*ridge_fit(source[:, query_order[:budget]].astype(np.float64), target, strength), shrinkage)
    mixture_weight, offset_scale, residual_weight = best_configuration
    particles = None
    if mixture_weight > 0.0:
        source_scores = source.astype(np.float64)
        rasch_probs = fit_rasch(source_scores, source_groups)
        profile_probs = make_profile(source_scores, rasch_probs, residual_weight)
        particle_probs = make_particles(profile_probs, offset_scale)
        particle_log_prior = particle_prior(source_groups)
        particles = (particle_probs, particle_log_prior, particle_probs.sum(axis=1))
    return query_order, models, mixture_weight, particles


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
        if len(shape) != 2 or not (1 <= shape[0] <= 512 and 1 <= shape[1] <= 16384):
            raise ValueError('invalid source shape')
        if request['encoding'] != 'base64' or request['dtype'] != 'uint8':
            raise ValueError('invalid source encoding')
        if request['offset'] != STATE['received'] or total != int(np.prod(shape)) or total > 8388608:
            raise ValueError('invalid source transfer')
        if request['offset'] == 0:
            STATE['buffer'] = bytearray(total)
            STATE['shape'] = shape
        elif shape != STATE['shape'] or total != len(STATE['buffer']):
            raise ValueError('inconsistent source shape')
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
        mode = request['mode']
        if mode not in ('primary', 'no_diversity', 'no_calibration'):
            raise ValueError('invalid mode')
        budgets = tuple(request['budgets'])
        if not budgets or any(type(budget) is not int or budget <= 0 or budget > source.shape[1] for budget in budgets) or tuple(sorted(set(budgets))) != budgets:
            raise ValueError('invalid budgets')
        source_groups = np.asarray(request['source_groups'])
        if source_groups.shape != (len(source),) or not np.issubdtype(source_groups.dtype, np.integer):
            raise ValueError('invalid source groups')
        anchors, models, mixture_weight, particles = fit_models(source, source_groups, budgets, STATE['seed'], mode == 'no_diversity')
        STATE['anchors'] = anchors
        STATE['models'] = models
        STATE['mixture_weight'] = mixture_weight
        STATE['particles'] = particles
        STATE['mode'] = mode
        STATE['budgets'] = budgets
        return {'anchors': anchors.tolist()}
    if operation == 'observe':
        budget = request['budget']
        if budget not in STATE['budgets'] or request['encoding'] != 'base64' or request['dtype'] != 'uint8':
            raise ValueError('invalid observation request')
        shape = request['shape']
        if len(shape) != 2 or shape[0] < 0 or shape[1] != budget:
            raise ValueError('invalid observation shape')
        observations = np.frombuffer(base64.b64decode(request['data'], validate=True), dtype=np.uint8).reshape(request['shape']).astype(float)
        if not np.isin(observations, [0, 1]).all():
            raise ValueError('invalid observations')
        query_order = STATE['anchors']
        assert np.unique(query_order).size == query_order.size
        linear_query_order = query_order[:budget]
        mixture_query_order = query_order[:budget]
        assert np.array_equal(linear_query_order, mixture_query_order)
        if STATE['mode'] == 'no_calibration':
            predictions = observations.mean(axis=1)
        else:
            linear_prediction = linear_predict(STATE['models'][budget], observations)
            mixture_weight = STATE['mixture_weight']
            if mixture_weight == 0.0:
                predictions = linear_prediction
            else:
                particle_probs, particle_log_prior, totals = STATE['particles']
                particle_prediction = predict_particles(particle_probs, particle_log_prior, totals, mixture_query_order, observations)
                blended_prediction = (1.0 - mixture_weight) * linear_prediction + mixture_weight * particle_prediction
                predictions = blended_prediction
        assert np.isfinite(predictions).all()
        predictions = np.clip(predictions, 0, 1).astype('<f8')
        return {'encoding': 'base64', 'dtype': '<f8', 'shape': [len(predictions)], 'data': base64.b64encode(predictions.tobytes()).decode('ascii')}
    if operation == 'release':
        STATE.clear()
        return {'ok': True}
    raise ValueError('unknown operation')
