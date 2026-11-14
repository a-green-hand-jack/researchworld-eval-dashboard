"""CPU-only saturation-aware skill candidate; finite-JSON handle API.

The starter's operations, inputs, response keys, and shapes are unchanged:
reset(seed) -> {ok: true}; train_start(rows, columns, column_names,
training_steps, max_queries) -> {ok: true}; sequential train_chunk(offset,
shape, dtype='<f8', encoding='base64', data, mask_dtype='|u1', mask) ->
{ok: true}; train_commit() -> {ok: true}; fit() -> {ok: true}.
start(availability, max_queries) -> {ok: true}; select() -> {indices: [...]};
observe(indices, values) -> {ok: true}; predict() -> {predictions: [[...]]}.

Training scores are normalized to [0,1]. Masked transport zeros are unknown.
Only historical rows and completed purchased observations inform learning.
Reset erases uploads, models, contexts, pending selections, and seed state.
There is no filesystem, network, diagnostic, or artifact transport.
"""

import base64
import math

import numpy as np


_STATE = {}


def weighted_pava(values, weights):
    block_values = []
    block_weights = []
    block_lengths = []
    for value, weight in zip(values, weights):
        block_values.append(float(value))
        block_weights.append(float(weight))
        block_lengths.append(1)
        while len(block_values) > 1 and block_values[-2] > block_values[-1]:
            merged_weight = block_weights[-2] + block_weights[-1]
            merged_value = (block_values[-2] * block_weights[-2]
                            + block_values[-1] * block_weights[-1]) / merged_weight
            merged_length = block_lengths[-2] + block_lengths[-1]
            block_values[-2:] = [merged_value]
            block_weights[-2:] = [merged_weight]
            block_lengths[-2:] = [merged_length]
    return np.repeat(np.asarray(block_values), block_lengths)


def fit_skill(train_scores, train_mask, steps):
    row_count, column_count = train_scores.shape
    support = train_mask.sum(axis=0)
    task_means = np.divide(np.where(train_mask, train_scores, 0.0).sum(axis=0),
                           np.maximum(support, 1))
    task_means[support == 0] = 0.5
    intercepts = task_means.copy()
    centered = np.where(train_mask, train_scores - task_means, 0.0)
    task_variance = (centered ** 2).sum(axis=0) / np.maximum(support, 1)
    loadings = np.sqrt(np.maximum(task_variance, 1e-6))
    loadings[support < 2] = 0.0
    skill_values = np.zeros(row_count)
    skill_ridge = 0.1
    supported_rows = train_mask.any(axis=1)
    for sweep in range(max(1, min(int(steps), 10))):
        for model_index in range(row_count):
            observed_columns = np.flatnonzero(train_mask[model_index])
            observed_loadings = loadings[observed_columns]
            centered_values = (train_scores[model_index, observed_columns]
                               - intercepts[observed_columns])
            skill_values[model_index] = np.dot(observed_loadings, centered_values) / (np.dot(observed_loadings, observed_loadings) + skill_ridge)
        if supported_rows.any():
            skill_center = float(np.mean(skill_values[supported_rows]))
            skill_scale = float(np.std(skill_values[supported_rows]))
            if skill_scale > 1e-8:
                skill_values = (skill_values - skill_center) / skill_scale
                intercepts += loadings * skill_center
                loadings *= skill_scale
        for task_index in range(column_count):
            observed_rows = train_mask[:, task_index]
            if support[task_index] < 2:
                loadings[task_index] = 0.0
                intercepts[task_index] = task_means[task_index]
                continue
            observed_skills = skill_values[observed_rows]
            observed_scores = train_scores[observed_rows, task_index]
            skill_mean = observed_skills.mean()
            score_mean = observed_scores.mean()
            centered_skills = observed_skills - skill_mean
            slope = np.dot(centered_skills, observed_scores - score_mean)
            slope /= np.dot(centered_skills, centered_skills) + 0.1
            loadings[task_index] = max(0.0, float(slope))
            intercepts[task_index] = score_mean - loadings[task_index] * skill_mean
    return task_means, intercepts, loadings, skill_values, task_variance


def make_skill_grid(skill_values, supported_rows):
    observed_skills = skill_values[supported_rows]
    if not observed_skills.size or np.ptp(observed_skills) < 1e-8:
        return np.array([-1.0, 0.0, 1.0]), np.array([0.0025, 0.995, 0.0025])
    lower = float(observed_skills.min())
    upper = float(observed_skills.max())
    padding = max(0.1, 0.1 * (upper - lower))
    skill_grid = np.unique(np.concatenate(([lower - padding],
                         np.quantile(observed_skills, np.linspace(0.0, 1.0, 63)),
                         [upper + padding])))
    right = np.clip(np.searchsorted(skill_grid, observed_skills), 1, len(skill_grid) - 1)
    fraction = ((observed_skills - skill_grid[right - 1])
                / (skill_grid[right] - skill_grid[right - 1]))
    prior_weights = np.full(len(skill_grid), 0.005 * len(observed_skills) / len(skill_grid))
    np.add.at(prior_weights, right - 1, 1.0 - fraction)
    np.add.at(prior_weights, right, fraction)
    prior_weights /= prior_weights.sum()
    return skill_grid, prior_weights


def fit_curves(train_scores, train_mask, steps):
    task_means, intercepts, loadings, skill_values, task_variance = fit_skill(
        train_scores, train_mask, steps)
    skill_grid, prior_weights = make_skill_grid(skill_values, train_mask.any(axis=1))
    support = train_mask.sum(axis=0)
    linear_grid = np.clip(intercepts[None, :] + skill_grid[:, None] * loadings[None, :], 0.0, 1.0)
    curve_grid = linear_grid.copy()
    linear_residuals = np.zeros(train_scores.shape[1])
    monotone_residuals = np.zeros(train_scores.shape[1])
    for task_index in range(train_scores.shape[1]):
        observed_rows = np.flatnonzero(train_mask[:, task_index])
        if not observed_rows.size:
            curve_grid[:, task_index] = task_means[task_index]
            continue
        observed_skills = skill_values[observed_rows]
        observed_scores = train_scores[observed_rows, task_index]
        order = np.argsort(observed_skills, kind='stable')
        sorted_skills, starts, sorted_weights = np.unique(
            observed_skills[order], return_index=True, return_counts=True)
        sorted_scores = np.add.reduceat(observed_scores[order], starts) / sorted_weights
        fitted_values = weighted_pava(sorted_scores, sorted_weights)
        curve_grid[:, task_index] = np.interp(skill_grid, sorted_skills, fitted_values)
        linear_curve = linear_grid[:, task_index]
        curve_weight = min(0.9, len(observed_rows) / (len(observed_rows) + 50.0))
        if len(sorted_skills) < 3:
            curve_weight = 0.0
        curve_grid[:, task_index] = curve_weight * curve_grid[:, task_index] + (1.0 - curve_weight) * linear_curve
        linear_fitted = np.interp(observed_skills, skill_grid, linear_curve)
        monotone_fitted = np.interp(observed_skills, skill_grid, curve_grid[:, task_index])
        linear_residuals[task_index] = np.mean((observed_scores - linear_fitted) ** 2)
        monotone_residuals[task_index] = np.mean((observed_scores - monotone_fitted) ** 2)
    residuals = {
        'task_mean': task_variance,
        'linear_skill': linear_residuals,
        'monotone_skill': np.maximum(monotone_residuals, 0.5 * linear_residuals),
    }
    variances = {}
    for name, raw in residuals.items():
        pooled = float(np.dot(support, raw) / max(int(support.sum()), 1))
        pooled = max(pooled, 1e-4)
        variances[name] = np.maximum((support * raw + 20.0 * pooled) / (support + 20.0), 1e-5)
    return {
        'skill_grid': skill_grid,
        'prior': prior_weights,
        'curves': {
            'task_mean': np.broadcast_to(task_means, curve_grid.shape).copy(),
            'linear_skill': linear_grid,
            'monotone_skill': curve_grid,
        },
        'variances': variances,
        'task_means': task_means,
    }


def normal_cdf(values):
    flat_values = np.asarray(values, dtype=float).ravel()
    result = np.fromiter((0.5 * math.erfc(-float(value) / math.sqrt(2.0))
                          for value in flat_values), dtype=float, count=flat_values.size)
    return result.reshape(values.shape)


def make_likelihoods(curve_grid, noise_variances, bin_count):
    bin_likelihoods = np.empty((curve_grid.shape[1], len(curve_grid), bin_count))
    for task_index in range(curve_grid.shape[1]):
        deviation = math.sqrt(float(noise_variances[task_index]))
        lower = float(curve_grid[:, task_index].min()) - 2.0 * deviation
        upper = float(curve_grid[:, task_index].max()) + 2.0 * deviation
        edges = np.linspace(lower, upper, bin_count + 1)
        edges[0], edges[-1] = -np.inf, np.inf
        cdf_values = normal_cdf((edges[None, :] - curve_grid[:, task_index, None]) / deviation)
        bin_likelihoods[task_index] = np.maximum(cdf_values[:, 1:] - cdf_values[:, :-1], 0.0)
        bin_likelihoods[task_index] /= np.maximum(
            bin_likelihoods[task_index].sum(axis=1, keepdims=True), 1e-300)
    return bin_likelihoods


def configure(fitted, configuration):
    name, multiplier, bin_count = configuration
    curve_grid = fitted['curves'][name]
    noise_variances = np.maximum(multiplier * fitted['variances'][name], 1e-5)
    return {
        'name': name,
        'skill_grid': fitted['skill_grid'],
        'curve_grid': curve_grid,
        'prior': fitted['prior'],
        'noise_variances': noise_variances,
        'bin_likelihoods': make_likelihoods(curve_grid, noise_variances, bin_count),
        'task_means': fitted['task_means'],
    }


def new_context(model, availability):
    prior_weights = model['prior']
    context = {
        'availability': np.asarray(availability, dtype=bool).copy(),
        'queried': np.zeros(len(availability), dtype=bool),
        'observed': np.zeros(len(availability)),
        'log_posterior': np.log(prior_weights),
    }
    context["posterior"] = prior_weights.copy()
    return context


def update_context(model, context, task_index, observed_value):
    curve_grid = model['curve_grid']
    noise_variances = model['noise_variances']
    log_posterior = context['log_posterior'].copy()
    log_posterior -= 0.5 * ((observed_value - curve_grid[:, task_index]) ** 2 / noise_variances[task_index] + np.log(noise_variances[task_index]))
    posterior = np.exp(log_posterior - np.max(log_posterior))
    if not np.isfinite(posterior).all() or posterior.sum() <= 0:
        posterior = model['prior'].copy()
        log_posterior = np.log(posterior)
    posterior /= posterior.sum()
    context['posterior'] = posterior
    context['log_posterior'] = log_posterior - np.max(log_posterior)
    context['queried'][task_index] = True
    context['observed'][task_index] = float(observed_value)


def predict_context(model, context):
    posterior = context['posterior']
    curve_grid = model['curve_grid']
    queried = context['queried']
    observed_values = context['observed']
    prediction = posterior @ curve_grid
    prediction = np.clip(np.where(np.isfinite(prediction), prediction, model['task_means']), 0.0, 1.0)
    prediction[queried] = observed_values[queried]
    return prediction


def transfer_gain_for_candidate(model, posterior, availability, queried, candidate_index):
    curve_grid = model['curve_grid']
    bin_likelihoods = model['bin_likelihoods']
    probability_floor = 1e-300
    target_mask = availability & ~queried
    target_mask[candidate_index] = False
    target_curves = curve_grid[:, target_mask]
    if target_curves.shape[1] == 0:
        return 0.0
    joint_bin_weights = posterior[:, None] * bin_likelihoods[candidate_index]
    bin_probabilities = joint_bin_weights.sum(axis=0)
    bin_posterior_means = joint_bin_weights.T @ target_curves / np.maximum(bin_probabilities[:, None], probability_floor)
    current_target_mean = posterior @ target_curves
    transfer_gain = np.sum(bin_probabilities[:, None] * (bin_posterior_means - current_target_mean[None, :]) ** 2) / target_curves.shape[1]
    return max(0.0, float(transfer_gain))


def select_context(model, context, frozen=False, target_panel=None, shortlist_size=8):
    availability = context['availability']
    queried = context['queried']
    candidates = np.flatnonzero(availability & ~queried)
    if not candidates.size:
        raise ValueError('no available unqueried benchmark')
    if model['name'] == 'task_mean' or len(candidates) == 1:
        return int(candidates[0])
    posterior = model['prior'] if frozen else context['posterior']
    score_availability = availability if target_panel is None else np.asarray(target_panel, dtype=bool)
    if len(candidates) > 24:
        skill_grid = model['skill_grid']
        centered_skill = skill_grid - posterior @ skill_grid
        curve_grid = model['curve_grid']
        centered_curves = curve_grid - posterior @ curve_grid
        skill_covariance = (posterior * centered_skill) @ centered_curves
        curve_variance = posterior @ (centered_curves ** 2)
        target_energy = np.sum(skill_covariance[score_availability & ~queried] ** 2)
        own_energy = np.where(score_availability, skill_covariance ** 2, 0.0)
        proxy = (skill_covariance ** 2 * np.maximum(target_energy - own_energy, 0.0)
                 / np.maximum(curve_variance + model['noise_variances'], 1e-12))
        order = np.lexsort((candidates, -proxy[candidates]))
        candidates = np.sort(candidates[order[:shortlist_size]])
    best_index = int(candidates[0])
    best_gain = -1.0
    for candidate_index in candidates:
        gain = transfer_gain_for_candidate(model, posterior, score_availability, queried, candidate_index)
        if gain > best_gain + 1e-14:
            best_gain = gain
            best_index = int(candidate_index)
    return best_index


def replay_loss(model, historical_scores, historical_mask, validation_indices, max_queries):
    row_losses = []
    for row_index in validation_indices:
        context = new_context(model, historical_mask[row_index])
        feasible_budget = min(max_queries, max(0, int(historical_mask[row_index].sum()) - 1))
        checkpoints = {min(feasible_budget, checkpoint) for checkpoint in (1, 2, 4, max_queries)}
        losses = []
        for query_count in range(feasible_budget + 1):
            if query_count in checkpoints:
                prediction = predict_context(model, context)
                query_mask = context['queried']
                validation_targets = historical_mask[row_index] & ~query_mask
                if validation_targets.any():
                    row_loss = np.mean((prediction[validation_targets] - historical_scores[row_index, validation_targets]) ** 2)
                    losses.append(float(row_loss))
            if query_count < feasible_budget:
                task_index = select_context(model, context)
                update_context(model, context, task_index, historical_scores[row_index, task_index])
        if losses:
            row_losses.append(float(np.mean(losses)))
    return float(np.mean(row_losses)) if row_losses else float('inf')


def learn(historical_scores, historical_mask, steps, seed, max_queries):
    historical_mask = np.asarray(historical_mask, dtype=bool) & np.isfinite(historical_scores)
    historical_scores = np.where(historical_mask, np.clip(historical_scores, 0.0, 1.0), 0.0)
    random = np.random.default_rng(seed)
    eligible = np.flatnonzero(historical_mask.sum(axis=1) >= 2)
    validation_limit = 6 if historical_scores.shape[1] > 256 else 12
    validation_count = min(validation_limit, len(eligible) // 5, max(0, len(historical_scores) - 3))
    configuration_names = ("task_mean", "linear_skill", "monotone_skill")
    selected_configuration = ('linear_skill', 1.5, 17)
    configuration_losses = {}
    if validation_count:
        validation_indices = np.sort(random.permutation(eligible)[:validation_count])
        inner_train_indices = np.setdiff1d(np.arange(len(historical_scores)), validation_indices)
        assert not np.intersect1d(inner_train_indices, validation_indices).size
        inner_train_mask = historical_mask[inner_train_indices]
        fitted = fit_curves(historical_scores[inner_train_indices], inner_train_mask, min(steps, 6))
        for name in configuration_names:
            settings = [(1.0, 9)] if name == 'task_mean' else [
                (multiplier, bins) for multiplier in (0.75, 1.5, 3.0) for bins in (9, 17)]
            for multiplier, bins in settings:
                configuration = (name, multiplier, bins)
                model = configure(fitted, configuration)
                configuration_losses[configuration] = replay_loss(
                    model, historical_scores, historical_mask, validation_indices, max_queries)
        selected_configuration = min(configuration_losses, key=configuration_losses.get)
    elif len(historical_scores) < 3 or not historical_mask.any():
        selected_configuration = ('task_mean', 1.0, 9)
    fitted = fit_curves(historical_scores, historical_mask, steps)
    model = configure(fitted, selected_configuration)
    model['configuration'] = selected_configuration
    model['validation_losses'] = configuration_losses
    return model


def handle(request):
    operation = request['op']
    if operation == 'reset':
        _STATE.clear()
        _STATE['seed'] = request['seed']
        return {'ok': True}
    if operation == 'train_start':
        seed = _STATE.get('seed', 0)
        _STATE.clear()
        _STATE.update(seed=seed,
                      values=np.zeros((request['rows'], request['columns'])),
                      mask=np.zeros((request['rows'], request['columns']), dtype=bool),
                      offset=0, steps=request['training_steps'],
                      training_queries=int(request.get('max_queries', 8)))
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
        _STATE['model'] = learn(_STATE['values'], _STATE['mask'], _STATE['steps'],
                                _STATE['seed'], _STATE['training_queries'])
    elif operation == 'start':
        _STATE['contexts'] = [new_context(_STATE['model'], availability)
                              for availability in request['availability']]
        _STATE['pending'] = None
    elif operation == 'select':
        indices = [select_context(_STATE['model'], context) for context in _STATE['contexts']]
        _STATE['pending'] = indices
        return {'indices': indices}
    elif operation == 'observe':
        if request['indices'] != _STATE['pending']:
            raise ValueError('unexpected observation')
        if len(request['values']) != len(_STATE['contexts']):
            raise ValueError('unexpected observation count')
        for context, task_index, value in zip(_STATE['contexts'], request['indices'], request['values']):
            update_context(_STATE['model'], context, task_index, value)
        _STATE['pending'] = None
    elif operation == 'predict':
        return {'predictions': [predict_context(_STATE['model'], context).tolist()
                                for context in _STATE['contexts']]}
    else:
        raise ValueError('unknown operation')
    return {'ok': True}
