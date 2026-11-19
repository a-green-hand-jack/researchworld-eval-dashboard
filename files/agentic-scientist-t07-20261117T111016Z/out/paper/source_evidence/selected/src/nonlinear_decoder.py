import functools

import numpy as np

from surrogate import (
    fit_score_model,
    predict_score,
    select_score_path,
    tune_configuration,
    validation_prefixes,
)


def sigmoid(values):
    return 1.0 / (1.0 + np.exp(-np.clip(values, -50.0, 50.0)))


def infer_shifts(query_logits, observed_values, shift_penalty):
    observed_values = np.asarray(observed_values, dtype=np.float64)
    if not np.isfinite(shift_penalty) or shift_penalty <= 0:
        raise ValueError('shift penalty must be positive')
    if observed_values.ndim != 2 or observed_values.shape[1] != query_logits.size:
        raise ValueError('invalid shift observations')
    shifts = np.zeros(observed_values.shape[0], dtype=np.float64)
    if shifts.size == 0 or query_logits.size == 0:
        return shifts
    lower_bounds = np.full(shifts.size, -20.0)
    upper_bounds = np.full(shifts.size, 20.0)
    for iteration in range(64):
        query_probabilities = sigmoid(query_logits[None, :] + shifts[:, None])
        shift_gradient = (query_probabilities - observed_values).sum(axis=1) + shift_penalty * shifts
        shift_hessian = (query_probabilities * (1.0 - query_probabilities)).sum(axis=1) + shift_penalty
        converged = np.abs(shift_gradient) < 1e-10
        if np.all(converged):
            break
        previous_shifts = shifts.copy()
        lower_bounds = np.where(shift_gradient < 0.0, shifts, lower_bounds)
        upper_bounds = np.where(shift_gradient > 0.0, shifts, upper_bounds)
        shifts = np.clip(shifts - shift_gradient / np.maximum(shift_hessian, 1e-12), -20.0, 20.0)
        outside_bracket = (shifts < lower_bounds) | (shifts > upper_bounds)
        shifts = np.where(outside_bracket, (lower_bounds + upper_bounds) * 0.5, shifts)
        shifts = np.where(converged, previous_shifts, shifts)
    if not np.all(np.isfinite(shifts)):
        raise ValueError('nonfinite ability shift')
    return shifts


def score_curve(item_logits, shifts):
    full_score_curve = np.zeros(shifts.size, dtype=np.float64)
    for start in range(0, item_logits.size, 1024):
        item_probabilities = sigmoid(shifts[:, None] + item_logits[None, start:start + 1024])
        full_score_curve += item_probabilities.sum(axis=1)
    full_score_curve /= item_logits.size
    return full_score_curve


def make_item_logits(source_item_means):
    clipped_item_means = np.clip(source_item_means, 1e-4, 1.0 - 1e-4)
    item_logits = np.log(clipped_item_means) - np.log1p(-clipped_item_means)
    return item_logits


def fit_residual_basis(item_logits, source_matrix, source_weights, query_items,
                       shift_penalty):
    source_shifts = infer_shifts(item_logits[query_items], source_matrix[:, query_items], shift_penalty)
    source_curve_scores = score_curve(item_logits, source_shifts)
    source_query_probabilities = sigmoid(item_logits[query_items][None, :] + source_shifts[:, None])
    source_score_residuals = source_matrix.mean(axis=1) - source_curve_scores
    source_query_residuals = source_matrix[:, query_items] - source_query_probabilities
    residual_feature_mean = source_weights @ source_query_residuals
    residual_score_mean = float(source_weights @ source_score_residuals)
    centered_query_residuals = source_query_residuals - residual_feature_mean
    weighted_query_residuals = np.sqrt(source_weights)[:, None] * centered_query_residuals
    weighted_score_residuals = np.sqrt(source_weights) * (source_score_residuals - residual_score_mean)
    residual_covariance = weighted_query_residuals.T @ weighted_query_residuals
    residual_cross_covariance = weighted_query_residuals.T @ weighted_score_residuals
    return dict(feature_mean=residual_feature_mean, score_mean=residual_score_mean,
                covariance=residual_covariance, cross_covariance=residual_cross_covariance)


def fit_residual_coefficients(basis, query_items, residual_ridge):
    if residual_ridge is None:
        return 0.0, np.zeros(query_items.size, dtype=np.float64)
    if not np.isfinite(residual_ridge) or residual_ridge <= 0:
        raise ValueError('residual ridge must be positive')
    residual_covariance = basis['covariance']
    residual_cross_covariance = basis['cross_covariance']
    residual_coefficients = np.linalg.solve(residual_covariance + residual_ridge * np.eye(query_items.size), residual_cross_covariance)
    residual_intercept = basis['score_mean'] - basis['feature_mean'] @ residual_coefficients
    return float(residual_intercept), residual_coefficients


def target_curve_features(item_logits, query_items, target_answers, shift_penalty):
    target_shifts = infer_shifts(item_logits[query_items], target_answers, shift_penalty)
    target_curve_scores = score_curve(item_logits, target_shifts)
    target_query_probabilities = sigmoid(item_logits[query_items][None, :] + target_shifts[:, None])
    target_query_residuals = target_answers - target_query_probabilities
    return target_curve_scores, target_query_residuals


def nonlinear_prediction(target_features, residual_intercept, residual_coefficients):
    target_curve_scores, target_query_residuals = target_features
    nonlinear_predictions = target_curve_scores + residual_intercept + target_query_residuals @ residual_coefficients
    return nonlinear_predictions


def fit_incumbent(source_matrix, source_weights, source_groups, item_groups,
                  max_budget, seed, training_steps=7, cv_settings=9):
    ridge, blend_weight = tune_configuration(
        source_matrix, source_weights, source_groups, item_groups, max_budget,
        seed, training_steps, cv_settings)
    score_model = fit_score_model(source_matrix, source_weights)
    selection_order = select_score_path(score_model, item_groups, max_budget, ridge)
    score_model['cross_covariance_cache'].clear()
    return dict(model=score_model, ridge=ridge, blend_weight=blend_weight,
                selection_order=selection_order)


def incumbent_path_cost(source_groups, max_budget, training_steps, cv_settings):
    if np.unique(source_groups).size < 3 or max_budget == 0:
        return 1
    settings = [(ridge, blend) for blend in (1.0, 0.5, 0.0)
                for ridge in (0.05, 0.01, 0.2)][:max(0, int(cv_settings))]
    ridge_limit = min(3, max(0, int(training_steps) - 1) // 2)
    allowed_ridges = (0.05, 0.01, 0.2)[:ridge_limit]
    used_ridges = {ridge for ridge, blend in settings if ridge in allowed_ridges}
    return 1 + 2 * len(used_ridges)


def decoder_settings(cv_settings):
    nonlinear_weight_candidates = (0.0, 0.5, 1.0)
    candidates = [(1.0, 0.05, nonlinear_weight_candidates[0])]
    for shift_penalty, residual_ridge in ((1.0, 0.05), (0.1, 0.05),
                                           (1.0, 0.01), (1.0, None)):
        for nonlinear_weight in nonlinear_weight_candidates[1:]:
            candidates.append((shift_penalty, residual_ridge, nonlinear_weight))
    return candidates[:max(1, min(9, int(cv_settings)))]


def tune_decoder(source_matrix, source_weights, source_groups, item_groups,
                 max_budget, seed, candidates, fit_incumbent):
    group_ids = np.unique(source_groups)
    fallback = candidates[0]
    if group_ids.size < 6 or len(candidates) < 2 or max_budget == 0:
        return fallback
    prefixes = validation_prefixes(max_budget)
    shuffled_groups = np.random.default_rng(seed + 7919).permutation(group_ids)
    validation_losses = np.zeros(len(candidates), dtype=np.float64)
    for fold_index in range(2):
        held_out_groups = shuffled_groups[fold_index::2]
        validation_rows = np.flatnonzero(np.isin(source_groups, held_out_groups))
        fit_rows = np.flatnonzero(~np.isin(source_groups, held_out_groups))
        assert set(source_groups[fit_rows]).isdisjoint(source_groups[validation_rows])
        if source_weights[fit_rows].sum() <= 0:
            return fallback
        fold_source_weights = source_weights[fit_rows] / source_weights[fit_rows].sum()
        fold_incumbent = fit_incumbent(source_matrix[fit_rows], fold_source_weights, source_groups[fit_rows], item_groups, max_budget, seed)
        item_logits = make_item_logits(fold_incumbent['model']['source_item_means'])
        validation_truth = source_matrix[validation_rows].mean(axis=1)
        prefix_errors = np.zeros((len(candidates), validation_rows.size), dtype=np.float64)
        for budget in prefixes:
            fold_query_items = fold_incumbent['selection_order'][:budget]
            validation_answers = source_matrix[validation_rows][:, fold_query_items]
            target_answers, history_inverse = np.unique(validation_answers, axis=0, return_inverse=True)
            incumbent_predictions = predict_score(
                fold_incumbent['model'], fold_query_items, target_answers,
                fold_incumbent['ridge'], fold_incumbent['blend_weight'])
            if budget == item_groups.size:
                exact_predictions = validation_answers.mean(axis=1)
                prefix_errors += np.abs(exact_predictions - validation_truth)[None, :] / len(prefixes)
                continue
            basis_cache = {}
            target_cache = {}
            prediction_cache = {}
            for setting_index, (shift_penalty, residual_ridge, nonlinear_weight) in enumerate(candidates):
                if nonlinear_weight == 0.0:
                    predictions = incumbent_predictions
                else:
                    if shift_penalty not in basis_cache:
                        basis_cache[shift_penalty] = fit_residual_basis(
                            item_logits, source_matrix[fit_rows], fold_source_weights,
                            fold_query_items, shift_penalty)
                        target_cache[shift_penalty] = target_curve_features(
                            item_logits, fold_query_items, target_answers, shift_penalty)
                    decoder_key = (shift_penalty, residual_ridge)
                    if decoder_key not in prediction_cache:
                        residual_intercept, residual_coefficients = fit_residual_coefficients(
                            basis_cache[shift_penalty], fold_query_items, residual_ridge)
                        prediction_cache[decoder_key] = nonlinear_prediction(
                            target_cache[shift_penalty], residual_intercept, residual_coefficients)
                    nonlinear_predictions = prediction_cache[decoder_key]
                    predictions = np.clip((1.0 - nonlinear_weight) * incumbent_predictions + nonlinear_weight * nonlinear_predictions, 0.0, 1.0)
                prefix_errors[setting_index] += np.abs(predictions[history_inverse] - validation_truth) / len(prefixes)
        for group_id in held_out_groups:
            members = source_groups[validation_rows] == group_id
            group_weights = source_weights[validation_rows][members]
            if group_weights.sum() <= 0:
                return fallback
            group_weights = group_weights / group_weights.sum()
            validation_losses += prefix_errors[:, members] @ group_weights / group_ids.size
    if not np.all(np.isfinite(validation_losses)):
        raise ValueError('nonfinite decoder validation loss')
    return candidates[int(np.argmin(validation_losses))]


def fit_candidate(source_matrix, source_weights, source_groups, item_groups,
                  max_budget, seed, training_steps, cv_settings):
    incumbent_model = fit_incumbent(source_matrix, source_weights, source_groups,
                                    item_groups, max_budget, seed,
                                    training_steps, cv_settings)
    row_order = sorted(range(source_matrix.shape[0]),
                       key=lambda index: (source_matrix[index].tobytes(),
                                          float(source_weights[index]),
                                          int(source_groups[index])))
    source_matrix = source_matrix[row_order]
    source_weights = source_weights[row_order]
    source_weights = source_weights / source_weights.sum()
    source_groups = source_groups[row_order]
    selection_order = incumbent_model['selection_order']
    for budget in range(max_budget + 1):
        query_items = selection_order[:budget]
        assert np.unique(item_groups[query_items]).size == query_items.size
    candidates = decoder_settings(cv_settings)
    chosen_setting = candidates[0]
    deployment_cost = incumbent_path_cost(source_groups, max_budget, training_steps, cv_settings)
    fold_training_steps = min(7, max(0, int(training_steps) - deployment_cost) // 2)
    if fold_training_steps >= 3 and np.unique(source_groups).size >= 6:
        fold_fitter = functools.partial(fit_incumbent, training_steps=fold_training_steps,
                                        cv_settings=cv_settings)
        chosen_setting = tune_decoder(
            source_matrix, source_weights, source_groups, item_groups, max_budget,
            seed, candidates, fold_fitter)
    return dict(incumbent=incumbent_model, selection_order=selection_order,
                source_matrix=source_matrix, source_weights=source_weights,
                item_groups=item_groups,
                item_logits=make_item_logits(incumbent_model['model']['source_item_means']),
                setting=chosen_setting, decoder_cache={})


def predict_candidate(model, query_items, target_answers):
    query_items = np.asarray(query_items, dtype=int)
    target_answers = np.asarray(target_answers, dtype=np.float64)
    if target_answers.ndim != 2 or target_answers.shape[1] != query_items.size:
        raise ValueError('invalid answer shape')
    incumbent = model['incumbent']
    source_score_mean = incumbent['model']['source_score_mean']
    if query_items.size == 0:
        return np.full(target_answers.shape[0], source_score_mean, dtype=np.float64)
    item_groups = model['item_groups']
    assert np.unique(item_groups[query_items]).size == query_items.size
    assert np.array_equal(query_items, model['selection_order'][:query_items.size])
    target_answers, history_inverse = np.unique(target_answers, axis=0, return_inverse=True)
    incumbent_predictions = predict_score(incumbent['model'], query_items, target_answers,
                                          incumbent['ridge'], incumbent['blend_weight'])
    shift_penalty, residual_ridge, nonlinear_weight = model['setting']
    if nonlinear_weight == 0.0:
        predictions = incumbent_predictions
    else:
        cache_key = tuple(query_items.tolist())
        if cache_key not in model['decoder_cache']:
            basis = fit_residual_basis(model['item_logits'], model['source_matrix'],
                                       model['source_weights'], query_items, shift_penalty)
            model['decoder_cache'][cache_key] = fit_residual_coefficients(
                basis, query_items, residual_ridge)
        residual_intercept, residual_coefficients = model['decoder_cache'][cache_key]
        target_features = target_curve_features(model['item_logits'], query_items,
                                                target_answers, shift_penalty)
        nonlinear_predictions = nonlinear_prediction(target_features, residual_intercept,
                                                       residual_coefficients)
        predictions = np.clip((1.0 - nonlinear_weight) * incumbent_predictions + nonlinear_weight * nonlinear_predictions, 0.0, 1.0)
    if not np.all(np.isfinite(predictions)):
        raise ValueError('nonfinite prediction')
    return predictions[history_inverse]
