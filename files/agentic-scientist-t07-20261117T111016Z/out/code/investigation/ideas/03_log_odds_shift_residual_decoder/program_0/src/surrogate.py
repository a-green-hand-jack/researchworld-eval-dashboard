"""Source-only score-targeted design and all-query score regression."""

import numpy as np


def fit_score_model(source_matrix, source_weights):
    source_matrix = np.asarray(source_matrix, dtype=np.float64)
    source_weights = np.asarray(source_weights, dtype=np.float64)
    if (source_matrix.ndim != 2 or source_weights.shape != (source_matrix.shape[0],)
            or not np.all(np.isfinite(source_weights))
            or np.any(source_weights < 0) or source_weights.sum() <= 0):
        raise ValueError('invalid source weights or matrix')
    row_order = sorted(range(source_matrix.shape[0]),
                       key=lambda index: (source_matrix[index].tobytes(),
                                          float(source_weights[index])))
    source_matrix = source_matrix[row_order]
    source_weights = source_weights[row_order]
    source_weights = source_weights / source_weights.sum()
    source_item_means = source_weights @ source_matrix
    source_full_scores = source_matrix.mean(axis=1)
    source_score_mean = float(source_weights @ source_full_scores)
    weighted_responses = np.sqrt(source_weights)[:, None] * (source_matrix - source_item_means)
    weighted_scores = np.sqrt(source_weights) * (source_full_scores - source_score_mean)
    score_covariance = weighted_responses.T @ weighted_scores
    item_variance = np.einsum('ij,ij->j', weighted_responses, weighted_responses)
    return dict(source_item_means=source_item_means,
                source_score_mean=source_score_mean,
                weighted_responses=weighted_responses,
                score_covariance=score_covariance, item_variance=item_variance,
                cross_covariance_cache={})


def select_score_path(model, item_groups, max_budget, ridge):
    item_groups = np.asarray(item_groups)
    weighted_responses = model['weighted_responses']
    score_covariance = model['score_covariance']
    item_variance = model['item_variance']
    if not np.isfinite(ridge) or ridge <= 0:
        raise ValueError('ridge must be positive')
    if not 0 <= max_budget <= np.unique(item_groups).size:
        raise ValueError('invalid design size')
    selection_order = []
    used_content_mask = np.zeros(item_groups.size, dtype=bool)
    cross_columns = np.empty((item_groups.size, max_budget), dtype=np.float64)
    for prefix_size in range(max_budget):
        if not selection_order:
            conditional_score_covariance = score_covariance.copy()
            conditional_item_variance = item_variance + ridge
        else:
            selected_cross_covariance = cross_columns[:, :prefix_size]
            selected_covariance = selected_cross_covariance[selection_order].copy()
            selected_covariance = (selected_covariance + selected_covariance.T) * 0.5
            selected_covariance += ridge * np.eye(prefix_size)
            selected_score_covariance = score_covariance[selection_order]
            conditional_score_covariance = score_covariance - selected_cross_covariance @ np.linalg.solve(selected_covariance, selected_score_covariance)
            conditional_item_variance = item_variance + ridge - np.einsum('ij,ji->i', selected_cross_covariance, np.linalg.solve(selected_covariance, selected_cross_covariance.T))
        selection_gain = conditional_score_covariance ** 2 / np.maximum(conditional_item_variance, 1e-12)
        selection_gain[used_content_mask] = -np.inf
        selected_item = int(np.argmax(selection_gain))
        if not np.isfinite(selection_gain[selected_item]):
            raise ValueError('no legal finite acquisition')
        selection_order.append(selected_item)
        used_content_mask |= item_groups == item_groups[selected_item]
        if prefix_size + 1 < max_budget:
            cache = model['cross_covariance_cache']
            if selected_item not in cache:
                cache[selected_item] = weighted_responses.T @ weighted_responses[:, selected_item]
            cross_columns[:, prefix_size] = cache[selected_item]
    selection_order = np.asarray(selection_order, dtype=int)
    for budget in range(max_budget + 1):
        query_items = selection_order[:budget]
        assert np.unique(item_groups[query_items]).size == budget
    return selection_order


def predict_score(model, query_items, target_answers, ridge, blend_weight):
    query_items = np.asarray(query_items, dtype=int)
    target_answers = np.asarray(target_answers, dtype=np.float64)
    if target_answers.ndim != 2 or target_answers.shape[1] != query_items.size:
        raise ValueError('invalid answer shape')
    source_item_means = model['source_item_means']
    source_score_mean = model['source_score_mean']
    if query_items.size == 0:
        return np.full(target_answers.shape[0], source_score_mean, dtype=np.float64)
    target_answers, history_inverse = np.unique(target_answers, axis=0, return_inverse=True)
    weighted_responses = model['weighted_responses'][:, query_items]
    selected_covariance = weighted_responses.T @ weighted_responses + ridge * np.eye(query_items.size)
    score_covariance = model['score_covariance']
    observed_residuals = target_answers - source_item_means[query_items]
    score_coefficients = np.linalg.solve(selected_covariance, score_covariance[query_items])
    ridge_prediction = source_score_mean + observed_residuals @ score_coefficients
    offset_prediction = source_score_mean + observed_residuals.mean(axis=1)
    predictions = np.clip(blend_weight * ridge_prediction + (1.0 - blend_weight) * offset_prediction, 0.0, 1.0)
    if not np.all(np.isfinite(predictions)):
        raise ValueError('nonfinite prediction')
    return predictions[history_inverse]


def validation_prefixes(max_budget):
    if max_budget == 0:
        return []
    prefixes = (2, 5) if max_budget <= 5 else (5, 10, 25)
    return sorted({min(budget, max_budget) for budget in prefixes} | {max_budget})


def tune_configuration(source_matrix, source_weights, source_groups, item_groups,
                       max_budget, seed, training_steps, cv_settings):
    fallback = (0.05, 1.0)
    group_ids = np.unique(source_groups)
    settings = [(ridge, blend) for blend in (1.0, 0.5, 0.0)
                for ridge in (0.05, 0.01, 0.2)]
    settings = settings[:max(0, int(cv_settings))]
    path_allowance = max(0, int(training_steps) - 1)
    ridge_limit = min(3, path_allowance // 2)
    allowed_ridges = (0.05, 0.01, 0.2)[:ridge_limit]
    settings = [setting for setting in settings if setting[0] in allowed_ridges]
    if group_ids.size < 3 or not settings or max_budget == 0:
        return fallback
    shuffled_groups = np.random.default_rng(seed).permutation(group_ids)
    prefixes = validation_prefixes(max_budget)
    grouped_validation_mae = np.zeros(len(settings), dtype=np.float64)
    evaluated_groups = 0
    for fold_index in range(2):
        held_out_groups = shuffled_groups[fold_index::2]
        validation_rows = np.flatnonzero(np.isin(source_groups, held_out_groups))
        fit_rows = np.flatnonzero(~np.isin(source_groups, held_out_groups))
        assert set(source_groups[fit_rows]).isdisjoint(source_groups[validation_rows])
        if source_weights[fit_rows].sum() <= 0:
            return fallback
        fold_model = fit_score_model(source_matrix[fit_rows], source_weights[fit_rows])
        fold_orders = {}
        validation_truth = source_matrix[validation_rows].mean(axis=1)
        validation_group_ids = source_groups[validation_rows]
        for setting_index, (ridge, blend_weight) in enumerate(settings):
            if ridge not in fold_orders:
                fold_order = select_score_path(fold_model, item_groups, max_budget, ridge)
                fold_orders[ridge] = fold_order
            fold_order = fold_orders[ridge]
            prefix_errors = np.zeros(validation_rows.size, dtype=np.float64)
            for budget in prefixes:
                validation_predictions = predict_score(fold_model, fold_order[:budget], source_matrix[validation_rows][:, fold_order[:budget]], ridge, blend_weight)
                prefix_errors += np.abs(validation_predictions - validation_truth) / len(prefixes)
            for group_id in held_out_groups:
                members = validation_group_ids == group_id
                group_weights = source_weights[validation_rows][members]
                if group_weights.sum() <= 0:
                    return fallback
                group_weights = group_weights / group_weights.sum()
                grouped_validation_mae[setting_index] += float(group_weights @ prefix_errors[members])
        evaluated_groups += held_out_groups.size
    grouped_validation_mae /= evaluated_groups
    if not np.all(np.isfinite(grouped_validation_mae)):
        raise ValueError('nonfinite source validation loss')
    best_setting = settings[int(np.argmin(grouped_validation_mae))]
    return best_setting
