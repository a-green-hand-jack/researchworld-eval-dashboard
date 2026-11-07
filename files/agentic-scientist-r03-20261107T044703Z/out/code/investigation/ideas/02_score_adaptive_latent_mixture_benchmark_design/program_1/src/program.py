"""Deterministic CPU masked-factor starter; single-file finite-JSON handle API.

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
Configuration selection uses historical-row-disjoint replay, not outer labels.
The fitted Gaussian mixture is an approximate empirical-Bayes latent prior.
Internal replay diagnostics are not public-data experimental results.
No filesystem or network transport is part of this interface. Full messages,
including JSON framing, must be strictly below 64 MiB. Dependencies are preinstalled.
"""
import base64
import numpy as np

_STATE = {}


def factor_fit(train_scores, train_mask, latent_rank, steps, seed):
    task_residual_counts = train_mask.sum(axis=0)
    total_count = int(task_residual_counts.sum())
    global_mean = float(np.sum(np.where(train_mask, train_scores, 0.0)) / total_count) if total_count else 0.5
    task_means = np.divide(np.sum(np.where(train_mask, train_scores, 0.0), axis=0),
                           task_residual_counts, out=np.full(train_scores.shape[1], global_mean),
                           where=task_residual_counts > 0)
    model_factors = np.zeros((len(train_scores), latent_rank))
    task_loadings = np.zeros((train_scores.shape[1], latent_rank))
    factor_ridge = 0.05
    if latent_rank:
        random = np.random.default_rng(seed)
        filled = np.where(train_mask, train_scores - task_means, 0.0)
        projection_width = min(latent_rank + 4, min(train_scores.shape))
        projection = random.normal(size=(train_scores.shape[1], projection_width))
        basis, _ = np.linalg.qr(filled @ projection, mode='reduced')
        _, singular_values, right = np.linalg.svd(basis.T @ filled, full_matrices=False)
        task_loadings = right[:latent_rank].T * np.sqrt(np.maximum(singular_values[:latent_rank], 1e-8))
        for sweep in range(max(1, steps)):
            for model_index in range(len(train_scores)):
                observed_columns = np.flatnonzero(train_mask[model_index])
                observed_loadings = task_loadings[observed_columns]
                centered_observations = train_scores[model_index, observed_columns] - task_means[observed_columns]
                model_factors[model_index] = np.linalg.solve(observed_loadings.T @ observed_loadings + factor_ridge * np.eye(latent_rank), observed_loadings.T @ centered_observations)
            for task_index in range(train_scores.shape[1]):
                observed_rows = train_mask[:, task_index]
                observed_factors = model_factors[observed_rows]
                task_loadings[task_index] = np.linalg.solve(
                    observed_factors.T @ observed_factors + factor_ridge * np.eye(latent_rank),
                    observed_factors.T @ (train_scores[observed_rows, task_index] - task_means[task_index]))
        for model_index in range(len(train_scores)):
            observed_columns = np.flatnonzero(train_mask[model_index])
            observed_loadings = task_loadings[observed_columns]
            centered_observations = train_scores[model_index, observed_columns] - task_means[observed_columns]
            model_factors[model_index] = np.linalg.solve(observed_loadings.T @ observed_loadings + factor_ridge * np.eye(latent_rank), observed_loadings.T @ centered_observations)
    masked_residual = np.where(train_mask, train_scores - task_means - model_factors @ task_loadings.T, 0.0)
    pooled_variance = max(float(np.sum(masked_residual ** 2) / max(total_count, 1)), 1e-5)
    noise_prior_strength = 12.0
    noise_floor = max(1e-6, pooled_variance * 0.03)
    noise_variances = np.maximum((np.sum(masked_residual ** 2, axis=0) + noise_prior_strength * pooled_variance) / (task_residual_counts + noise_prior_strength), noise_floor)
    return {'mean': task_means, 'loadings': task_loadings, 'noise': noise_variances,
            'factors': model_factors, 'supported_rows': train_mask.any(axis=1)}


def regularized_covariance(centered, weights, pooled_covariance):
    latent_rank = centered.shape[1]
    component_covariance = (centered.T * weights) @ centered / max(float(weights.sum()), 1e-12)
    component_covariance = 0.85 * component_covariance + 0.15 * pooled_covariance
    covariance_ridge = max(float(np.trace(pooled_covariance)) / max(latent_rank, 1) * 0.02, 1e-5)
    component_covariance += covariance_ridge * np.eye(latent_rank)
    return component_covariance


def attach_prior(fitted, components, steps, seed):
    model = {key: value for key, value in fitted.items() if key not in ('factors', 'supported_rows')}
    factors = fitted['factors'][fitted['supported_rows']]
    latent_rank = model['loadings'].shape[1]
    if not latent_rank or len(factors) < 2:
        model.update(weights=np.ones(1), means=np.zeros((1, latent_rank)),
                     covariances=np.eye(latent_rank)[None, :, :])
        return model
    center = factors.mean(axis=0)
    pooled_covariance = (factors - center).T @ (factors - center) / len(factors)
    covariance = regularized_covariance(factors - center, np.ones(len(factors)), pooled_covariance)
    components = min(components, max(1, len(factors) // 12))
    random = np.random.default_rng(seed)
    centers = [factors[int(random.integers(len(factors)))].copy()]
    while len(centers) < components:
        distances = np.min(np.sum((factors[:, None, :] - np.asarray(centers)[None, :, :]) ** 2, axis=2), axis=1)
        if float(distances.sum()) <= 1e-15:
            break
        centers.append(factors[int(random.choice(len(factors), p=distances / distances.sum()))].copy())
    components = len(centers)
    component_means = np.asarray(centers) if components > 1 else center[None, :]
    component_covariances = np.repeat(covariance[None, :, :], components, axis=0)
    component_weights = np.full(components, 1.0 / components)
    if components > 1:
        for iteration in range(max(2, min(steps, 12))):
            log_responsibilities = np.empty((len(factors), components))
            for component_index in range(components):
                displacement = factors - component_means[component_index]
                cholesky = np.linalg.cholesky(component_covariances[component_index])
                whitened = np.linalg.solve(cholesky, displacement.T).T
                log_responsibilities[:, component_index] = (np.log(component_weights[component_index])
                    - np.log(np.diag(cholesky)).sum() - 0.5 * np.sum(whitened ** 2, axis=1))
            responsibilities = np.exp(log_responsibilities - log_responsibilities.max(axis=1, keepdims=True))
            responsibilities /= responsibilities.sum(axis=1, keepdims=True)
            masses = responsibilities.sum(axis=0)
            component_weights = (masses + 0.5) / (len(factors) + 0.5 * components)
            for component_index in range(components):
                weights = responsibilities[:, component_index]
                component_means[component_index] = weights @ factors / max(float(masses[component_index]), 1e-12)
                component_covariances[component_index] = regularized_covariance(
                    factors - component_means[component_index], weights, pooled_covariance)
    model.update(weights=component_weights, means=component_means, covariances=component_covariances)
    return model


def new_posterior(model):
    return {'log_weights': np.log(model['weights']).copy(), 'means': model['means'].copy(),
            'covariances': model['covariances'].copy()}


def posterior_weights(posterior):
    component_log_weights = posterior['log_weights']
    component_weights = np.exp(component_log_weights - np.max(component_log_weights))
    component_weights /= component_weights.sum()
    return component_weights


def update_posterior(model, posterior, column, observed_value):
    component_means = posterior['means']
    component_covariances = posterior['covariances']
    component_log_weights = posterior['log_weights']
    loading = model['loadings'][column]
    projected_covariances = component_covariances @ loading
    predictive_variances = np.maximum(projected_covariances @ loading + model['noise'][column], 1e-12)
    component_predictive_means = model['mean'][column] + component_means @ loading
    innovation = observed_value - component_predictive_means
    component_log_weights += -0.5 * (np.log(predictive_variances) + innovation ** 2 / predictive_variances)
    component_weights = np.exp(component_log_weights - np.max(component_log_weights))
    component_weights /= component_weights.sum()
    posterior['log_weights'] = np.log(np.maximum(component_weights, 1e-300))
    component_gains = projected_covariances / predictive_variances[:, None]
    component_means += component_gains * innovation[:, None]
    component_covariances -= np.einsum('ki,kj,k->kij', projected_covariances, projected_covariances, 1.0 / predictive_variances)
    component_covariances[:] = 0.5 * (component_covariances + component_covariances.transpose(0, 2, 1))


def predictive_moments(model, posterior):
    component_weights = posterior_weights(posterior)
    component_predictions = model['mean'][None, :] + posterior['means'] @ model['loadings'].T
    component_variances = np.einsum('ti,kij,tj->kt', model['loadings'], posterior['covariances'], model['loadings']) + model['noise'][None, :]
    mixture_mean = component_weights @ component_predictions
    mixture_variance = component_weights @ (component_variances + component_predictions ** 2) - mixture_mean ** 2
    return mixture_mean, np.maximum(mixture_variance, 0.0)


def latent_covariance(posterior):
    weights = posterior_weights(posterior)
    center = weights @ posterior['means']
    return (np.einsum('k,kij->ij', weights, posterior['covariances'])
            + (posterior['means'].T * weights) @ posterior['means'] - np.outer(center, center))


def target_risk(posterior, target_gram, target_noise):
    return max(float(np.sum(latent_covariance(posterior) * target_gram.T)) + target_noise, 0.0)


def quadrature_gain(model, posterior, candidate_index, target_mask, order=3):
    target_loadings = model['loadings'][target_mask]
    target_gram = target_loadings.T @ target_loadings
    target_noise = float(model['noise'][target_mask].sum())
    current_target_risk = target_risk(posterior, target_gram, target_noise)
    if order == 3:
        quadrature_nodes, quadrature_weights = np.polynomial.hermite.hermgauss(3)
    else:
        quadrature_nodes, quadrature_weights = np.polynomial.hermite.hermgauss(order)
    quadrature_weights /= np.sqrt(np.pi)
    component_weights = posterior_weights(posterior)
    loading = model['loadings'][candidate_index]
    expected_target_risk = 0.0
    for component_index, component_weight in enumerate(component_weights):
        predictive_mean = model['mean'][candidate_index] + posterior['means'][component_index] @ loading
        predictive_variance = max(float(loading @ posterior['covariances'][component_index] @ loading) + model['noise'][candidate_index], 1e-12)
        quadrature_values = predictive_mean + np.sqrt(2.0 * predictive_variance) * quadrature_nodes
        for quadrature_value, quadrature_weight in zip(quadrature_values, quadrature_weights):
            simulated = {key: value.copy() for key, value in posterior.items()}
            update_posterior(model, simulated, candidate_index, float(quadrature_value))
            posterior_target_risk = target_risk(simulated, target_gram, target_noise)
            expected_target_risk += component_weight * quadrature_weight * posterior_target_risk
    risk_reduction = current_target_risk - expected_target_risk
    return float(risk_reduction)


def select_index(model, context, fixed_targets=None):
    availability, queried = context['availability'], context['queried']
    legal = np.flatnonzero(availability & ~queried)
    if not len(legal):
        raise ValueError('no available unqueried benchmark')
    posterior = context['posterior']
    target_mask = availability & ~queried
    if fixed_targets is not None:
        target_mask = fixed_targets.copy()
    loadings = model['loadings']
    covariance = latent_covariance(posterior)
    target_gram = loadings[target_mask].T @ loadings[target_mask]
    projected = loadings @ covariance
    signal_variances = np.sum(projected * loadings, axis=1)
    _, variances = predictive_moments(model, posterior)
    gains = np.sum((projected @ target_gram) * projected, axis=1)
    gains -= target_mask * signal_variances ** 2
    gains /= np.maximum(variances, 1e-12)
    order = legal[np.argsort(-gains[legal], kind='stable')]
    if len(model['weights']) == 1:
        return int(order[0])
    best_index, best_gain = int(order[0]), -np.inf
    for candidate_index in order[:8]:
        target_mask = availability & ~queried
        if fixed_targets is not None:
            target_mask = fixed_targets.copy()
        target_mask[candidate_index] = False
        gain = quadrature_gain(model, posterior, int(candidate_index), target_mask)
        if gain > best_gain + 1e-14 or (abs(gain - best_gain) <= 1e-14 and candidate_index < best_index):
            best_index, best_gain = int(candidate_index), gain
    return best_index


def make_context(model, availability_row):
    return {'availability': np.asarray(availability_row, dtype=bool).copy(),
            'queried': np.zeros(len(availability_row), dtype=bool),
            'observed': np.zeros(len(availability_row)), 'posterior': new_posterior(model), 'count': 0}


def observe_context(model, context, column, value):
    update_posterior(model, context['posterior'], column, value)
    context['queried'][column] = True
    context['observed'][column] = value
    context['count'] += 1


def predict_context(model, context):
    prediction, _ = predictive_moments(model, context['posterior'])
    prediction = np.clip(prediction, 0.0, 1.0)
    prediction[context['queried']] = context['observed'][context['queried']]
    return prediction


def replay_loss(model, historical_scores, historical_mask, validation_indices, budget,
                seed, mode='adaptive', fixed_panel=False, matched_model=None):
    random = np.random.default_rng(seed)
    row_losses, matched_losses = [], []
    for row_index in validation_indices:
        availability = historical_mask[row_index].copy()
        fixed_targets = None
        if fixed_panel:
            observed_columns = np.flatnonzero(availability)
            shuffled = random.permutation(observed_columns)
            fixed_targets = np.zeros_like(availability)
            fixed_targets[shuffled[len(shuffled) // 2:]] = True
            availability &= ~fixed_targets
        context = make_context(model, availability)
        planning = make_context(model, availability)
        matched_context = make_context(matched_model, availability) if matched_model is not None else None
        feasible_budget = min(budget, int(availability.sum()) - (0 if fixed_panel else 1))
        checkpoints = {0, min(1, feasible_budget), min(2, feasible_budget), min(4, feasible_budget), feasible_budget}
        losses, paired_losses = [], []
        for completed in range(max(0, feasible_budget) + 1):
            if completed in checkpoints:
                query_mask = context['queried']
                validation_targets = historical_mask[row_index] & ~query_mask
                if fixed_targets is not None:
                    validation_targets = fixed_targets
                if validation_targets.any():
                    prediction = predict_context(model, context)
                    row_loss = np.mean((prediction[validation_targets] - historical_scores[row_index, validation_targets]) ** 2)
                    losses.append(float(row_loss))
                    if matched_context is not None:
                        paired_prediction = predict_context(matched_model, matched_context)
                        paired_losses.append(float(np.mean((paired_prediction[validation_targets] - historical_scores[row_index, validation_targets]) ** 2)))
            if completed == max(0, feasible_budget):
                break
            if mode == 'random':
                column = int(random.choice(np.flatnonzero(availability & ~context['queried'])))
            elif mode == 'frozen':
                column = select_index(model, planning, fixed_targets)
                planning_value = predictive_moments(model, planning['posterior'])[0][column]
                observe_context(model, planning, column, float(planning_value))
            else:
                column = select_index(model, context, fixed_targets)
            value = float(historical_scores[row_index, column])
            observe_context(model, context, column, value)
            if matched_context is not None:
                observe_context(matched_model, matched_context, column, value)
        if losses:
            row_losses.append(float(np.mean(losses)))
        if paired_losses:
            matched_losses.append(float(np.mean(paired_losses)))
    return (float(np.mean(row_losses)) if row_losses else float('inf'),
            float(np.mean(matched_losses)) if matched_losses else None)


def learn(historical_scores, historical_mask, steps, seed, budget):
    random = np.random.default_rng(seed)
    eligible = np.flatnonzero(historical_mask.sum(axis=1) >= 2)
    validation_count = min(12, max(1, len(eligible) // 5)) if len(eligible) >= 5 else 0
    validation_indices = random.permutation(eligible)[:validation_count]
    inner_train_indices = np.setdiff1d(np.arange(len(historical_scores)), validation_indices)
    assert not np.intersect1d(inner_train_indices, validation_indices).size
    inner_train_mask = historical_mask[inner_train_indices]
    maximum_rank = max(0, min(len(inner_train_indices), historical_scores.shape[1]) - 1)
    configurations = [(0, 1)]
    proposed = [(1, 1), (3, 1), (3, 2), (6, 1), (6, 2), (6, 4)]
    for rank, components in proposed[:max(1, min(steps, len(proposed)))]:
        configuration = (min(rank, maximum_rank), components)
        if configuration[0] and configuration not in configurations:
            configurations.append(configuration)
    configuration_losses, fitted_ranks, inner_models = {}, {}, {}
    if validation_count:
        for configuration in configurations:
            rank, components = configuration
            if rank not in fitted_ranks:
                fitted_ranks[rank] = factor_fit(historical_scores[inner_train_indices], inner_train_mask,
                                              rank, min(steps, 5), seed)
            model = attach_prior(fitted_ranks[rank], components, steps, seed)
            inner_models[configuration] = model
            loss, _ = replay_loss(model, historical_scores, historical_mask, validation_indices, budget, seed)
            configuration_losses[configuration] = loss
        selected_configuration = min(configuration_losses, key=configuration_losses.get)
    else:
        selected_configuration = (0, 1)
    diagnostics = {'configuration_losses': configuration_losses, 'selected': selected_configuration,
                   'validation_rows': validation_indices.tolist(), 'split': 'row-disjoint, not family-disjoint'}
    if validation_count:
        rank, _ = selected_configuration
        chosen = inner_models[selected_configuration]
        single = attach_prior(fitted_ranks[rank], 1, steps, seed)
        diagnostic_rows = validation_indices[:4]
        comparisons = {}
        for fixed_panel in (False, True):
            for mode in ('adaptive', 'frozen', 'random'):
                comparisons[(fixed_panel, mode)] = replay_loss(
                    chosen, historical_scores, historical_mask, diagnostic_rows, budget, seed,
                    mode=mode, fixed_panel=fixed_panel, matched_model=single)
        comparisons['single_adaptive'] = replay_loss(single, historical_scores, historical_mask,
                                                     diagnostic_rows, budget, seed)[0]
        available = historical_mask[diagnostic_rows[0]].copy()
        context = make_context(chosen, available)
        column = select_index(chosen, context)
        available[column] = False
        comparisons['quadrature_3_vs_9'] = (
            quadrature_gain(chosen, context['posterior'], column, available),
            quadrature_gain(chosen, context['posterior'], column, available, order=9))
        gaussian_context = make_context(single, historical_mask[diagnostic_rows[0]])
        gaussian_column = select_index(single, gaussian_context)
        gaussian_targets = gaussian_context['availability'].copy()
        gaussian_targets[gaussian_column] = False
        loading = single['loadings'][gaussian_column]
        projected = single['covariances'][0] @ loading
        predictive_variance = float(loading @ projected) + single['noise'][gaussian_column]
        target_loadings = single['loadings'][gaussian_targets]
        analytic_gain = float(np.sum((target_loadings @ projected) ** 2) / predictive_variance)
        gaussian_mean = predictive_moments(single, gaussian_context['posterior'])[0][gaussian_column]
        low_posterior = new_posterior(single)
        high_posterior = new_posterior(single)
        update_posterior(single, low_posterior, gaussian_column, float(gaussian_mean - np.sqrt(predictive_variance)))
        update_posterior(single, high_posterior, gaussian_column, float(gaussian_mean + np.sqrt(predictive_variance)))
        covariance_difference = float(np.linalg.norm(low_posterior['covariances'] - high_posterior['covariances']))
        comparisons['gaussian_analytic_vs_quadrature'] = (
            analytic_gain, quadrature_gain(single, gaussian_context['posterior'], gaussian_column, gaussian_targets))
        comparisons['gaussian_score_independent_covariance_difference'] = covariance_difference
        diagnostics['internal_replay_only'] = comparisons
    rank, components = selected_configuration
    refitted = factor_fit(historical_scores, historical_mask, rank, min(steps, 8), seed)
    return attach_prior(refitted, components, steps, seed), diagnostics


def handle(request):
    operation = request['op']
    if operation == 'reset':
        _STATE.clear()
        _STATE['seed'] = request['seed']
        return {'ok': True}
    if operation == 'train_start':
        _STATE.update(values=np.zeros((request['rows'], request['columns'])),
                      mask=np.zeros((request['rows'], request['columns']), dtype=bool),
                      offset=0, steps=request['training_steps'], budget=request['max_queries'])
    elif operation == 'train_chunk':
        shape = tuple(request['shape'])
        values = np.frombuffer(base64.b64decode(request['data']), dtype='<f8').reshape(shape)
        mask = np.frombuffer(base64.b64decode(request['mask']), dtype='u1').reshape(shape).astype(bool)
        offset = request['offset']
        _STATE['values'][offset:offset + shape[0]] = values
        _STATE['mask'][offset:offset + shape[0]] = mask
        _STATE['offset'] += shape[0]
    elif operation == 'train_commit':
        if _STATE['offset'] != len(_STATE['values']):
            raise ValueError('incomplete training upload')
    elif operation == 'fit':
        model, diagnostics = learn(_STATE['values'], _STATE['mask'], _STATE['steps'],
                                   _STATE['seed'], _STATE['budget'])
        _STATE.update(model=model, diagnostics=diagnostics)
    elif operation == 'start':
        availability = np.asarray(request['availability'], dtype=bool)
        def new_context(availability_row):
            return make_context(_STATE['model'], availability_row)
        contexts = [new_context(availability_row) for availability_row in availability]
        _STATE.update(contexts=contexts, active_budget=request['max_queries'])
        _STATE.pop('pending', None)
    elif operation == 'select':
        if 'pending' in _STATE:
            raise ValueError('selection awaiting observation')
        if any(context['count'] >= _STATE['active_budget'] for context in _STATE['contexts']):
            raise ValueError('query budget exhausted')
        indices = [select_index(_STATE['model'], context) for context in _STATE['contexts']]
        _STATE['pending'] = indices
        return {'indices': indices}
    elif operation == 'observe':
        if request['indices'] != _STATE['pending']:
            raise ValueError('unexpected observation')
        if len(request['values']) != len(_STATE['contexts']):
            raise ValueError('observation shape mismatch')
        for context, column, value in zip(_STATE['contexts'], request['indices'], request['values']):
            observe_context(_STATE['model'], context, column, float(value))
        del _STATE['pending']
    elif operation == 'predict':
        predictions = [predict_context(_STATE['model'], context).tolist() for context in _STATE['contexts']]
        return {'predictions': predictions}
    else:
        raise ValueError('unknown operation')
    return {'ok': True}
