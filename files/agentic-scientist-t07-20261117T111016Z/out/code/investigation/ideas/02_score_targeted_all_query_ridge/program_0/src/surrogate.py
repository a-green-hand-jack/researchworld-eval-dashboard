"""Source-only low-rank fitting and design-based residual estimation.

Content-group sampling uses one uniformly chosen member per sampled group.
Singleton pilots ensure that every unqueried item has positive audit inclusion
probability. All random designs are independent of target responses.
"""

import numpy as np


def fit_surrogate(matrix, weights, max_rank=12):
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    item_means = weights @ matrix
    centered = (matrix - item_means) * np.sqrt(weights[:, None])
    gram = centered @ centered.T
    eigenvalues, eigenvectors = np.linalg.eigh(gram)
    order = np.argsort(eigenvalues)[::-1][:max_rank]
    order = order[eigenvalues[order] > 1e-10]
    item_loadings = centered.T @ eigenvectors[:, order]
    return item_means, item_loadings


def choose_pilots(item_loadings, item_groups, count):
    group_ids, group_counts = np.unique(item_groups, return_counts=True)
    singleton_groups = group_ids[group_counts == 1]
    eligible = np.flatnonzero(np.isin(item_groups, singleton_groups))
    if count > eligible.size:
        raise ValueError('not enough singleton pilot groups')
    pool = item_loadings[eligible]
    inverse = np.eye(pool.shape[1]) / 0.25
    selected = []
    unavailable = np.zeros(eligible.size, dtype=bool)
    for _ in range(count):
        transformed = pool @ inverse
        gains = np.sum(transformed * pool, axis=1)
        gains[unavailable] = -np.inf
        position = int(np.argmax(gains))
        selected.append(int(eligible[position]))
        unavailable[position] = True
        direction = transformed[position]
        inverse -= np.outer(direction, direction) / (1.0 + gains[position])
    return np.asarray(selected, dtype=int)


def make_design(item_loadings, item_groups, pilot_size, query_budget, seed):
    n_items = len(item_groups)
    pilot_indices = choose_pilots(item_loadings, item_groups, pilot_size)
    remaining_indices = np.setdiff1d(np.arange(n_items), pilot_indices)
    audit_size = query_budget - pilot_size
    if audit_size < 0:
        raise ValueError('pilot exceeds query budget')
    audit_rng = np.random.default_rng(seed)
    group_ids, group_counts = np.unique(item_groups, return_counts=True)
    if query_budget > group_ids.size:
        raise ValueError('budget exceeds distinct content groups')
    if np.all(group_counts == 1):
        audit_indices = audit_rng.choice(remaining_indices, size=audit_size, replace=False)
    else:
        pilot_groups = item_groups[pilot_indices]
        eligible_groups = group_ids[~np.isin(group_ids, pilot_groups)]
        sampled_groups = audit_rng.choice(eligible_groups, size=audit_size, replace=False)
        audit_indices = np.asarray([
            audit_rng.choice(np.flatnonzero(item_groups == group))
            for group in sampled_groups
        ], dtype=int)
    assert np.intersect1d(pilot_indices, audit_indices).size == 0
    observed_indices = np.concatenate((pilot_indices, audit_indices))
    assert observed_indices.size == query_budget
    assert np.unique(observed_indices).size == query_budget
    assert np.unique(item_groups[observed_indices]).size == query_budget
    return observed_indices


def freeze_surrogate(item_means, item_loadings, pilot_indices, pilot_answers, ridge):
    pilot_loadings = item_loadings[pilot_indices]
    pilot_centered = pilot_answers - item_means[pilot_indices]
    latent_coefficients = np.linalg.solve(pilot_loadings.T @ pilot_loadings + ridge * np.eye(pilot_loadings.shape[1]), pilot_loadings.T @ pilot_centered)
    frozen_predictions = np.clip(item_means + item_loadings @ latent_coefficients, 0.0, 1.0)
    frozen_predictions.setflags(write=False)
    return frozen_predictions


def estimate_parts(item_means, item_loadings, indices, pilot_size, answers,
                   ridge, item_groups):
    n_items = len(item_groups)
    pilot_indices = indices[:pilot_size]
    pilot_answers = answers[:pilot_size]
    frozen_predictions = freeze_surrogate(
        item_means, item_loadings, pilot_indices, pilot_answers, ridge)
    remaining_indices = np.setdiff1d(np.arange(n_items), pilot_indices)
    plugin_score = (pilot_answers.sum() + frozen_predictions[remaining_indices].sum()) / n_items
    audit_indices = indices[pilot_size:]
    audit_answers = answers[pilot_size:]
    if audit_indices.size == 0:
        return float(plugin_score), 0.0
    group_ids, group_counts = np.unique(item_groups, return_counts=True)
    if np.all(group_counts == 1):
        residual_correction = (remaining_indices.size / n_items) * np.mean(audit_answers - frozen_predictions[audit_indices])
    else:
        audit_group_sizes = group_counts[np.searchsorted(group_ids, item_groups[audit_indices])]
        remaining_group_count = group_ids.size - pilot_size
        residual_correction = (remaining_group_count / n_items) * np.mean(
            audit_group_sizes * (audit_answers - frozen_predictions[audit_indices]))
    return float(plugin_score), float(residual_correction)


def combine_prediction(plugin_score, residual_correction, correction_weight):
    raw_prediction = plugin_score + correction_weight * residual_correction
    return float(np.clip(raw_prediction, 0.0, 1.0))


def uniform_predictions(answers, indices, item_groups):
    group_ids, group_counts = np.unique(item_groups, return_counts=True)
    if len(indices) == 0:
        raise ValueError('uniform prediction requires positive budget')
    sampled_sizes = group_counts[np.searchsorted(group_ids, item_groups[indices])]
    predictions = (answers @ sampled_sizes) * (
        group_ids.size / (len(indices) * len(item_groups)))
    return np.clip(predictions, 0.0, 1.0)


def make_validation_folds(matrix, source_weights, source_groups, seed):
    groups = np.unique(source_groups)
    if groups.size < 3:
        return []
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(groups)
    heldout_count = max(1, groups.size // 5)
    folds = []
    for fold_index in range(2):
        validation_groups = shuffled[
            fold_index * heldout_count:(fold_index + 1) * heldout_count]
        fit_indices = np.flatnonzero(~np.isin(source_groups, validation_groups))
        validation_indices = np.flatnonzero(np.isin(source_groups, validation_groups))
        if validation_indices.size > 32:
            validation_indices = np.sort(rng.choice(validation_indices, 32, replace=False))
        fit_groups = source_groups[fit_indices]
        assert set(fit_groups).isdisjoint(validation_groups)
        fitting_weights = source_weights[fit_indices]
        validation_weights = source_weights[validation_indices]
        validation_weights = validation_weights / validation_weights.sum()
        model = fit_surrogate(matrix[fit_indices], fitting_weights)
        folds.append((model, matrix[validation_indices], validation_weights))
    return folds


def tune_configuration(folds, item_groups, budget, pilot_candidates, seed):
    """Every loss below uses source validation rows, never target histories."""
    correction_grid = np.array([0.0, 0.25, 0.5, 0.75, 1.0])
    best_loss = np.inf
    best_config = None
    design_cache = {}
    for pilot_size in sorted(set(pilot_candidates)):
        rank_candidates = (0,) if pilot_size == 0 else (1, 4, 12)
        for rank in rank_candidates:
            ridge_candidates = (0.25,) if rank == 0 else (0.05, 0.25, 1.0)
            for ridge in ridge_candidates:
                inner_validation_mae = np.zeros(correction_grid.size)
                for fold_index, (model, validation, weights) in enumerate(folds):
                    item_means, loadings = model
                    item_loadings = loadings[:, :rank]
                    truths = validation.mean(axis=1)
                    for repetition in range(2):
                        cache_key = (fold_index, pilot_size, repetition)
                        if cache_key not in design_cache:
                            design_cache[cache_key] = make_design(
                                loadings, item_groups, pilot_size, budget,
                                seed + 1009 * fold_index + 7919 * repetition)
                    pilot_indices = design_cache[(fold_index, pilot_size, 0)][:pilot_size]
                    pilot_loadings = item_loadings[pilot_indices]
                    pilot_centered = validation[:, pilot_indices] - item_means[pilot_indices]
                    coefficients = np.linalg.solve(
                        pilot_loadings.T @ pilot_loadings + ridge * np.eye(item_loadings.shape[1]),
                        pilot_loadings.T @ pilot_centered.T)
                    frozen = np.clip(item_means + coefficients.T @ item_loadings.T, 0.0, 1.0)
                    remaining = np.setdiff1d(np.arange(len(item_groups)), pilot_indices)
                    plugins = (validation[:, pilot_indices].sum(axis=1)
                               + frozen[:, remaining].sum(axis=1)) / len(item_groups)
                    for repetition in range(2):
                        indices = design_cache[(fold_index, pilot_size, repetition)]
                        audit_indices = indices[pilot_size:]
                        group_ids, group_counts = np.unique(item_groups, return_counts=True)
                        audit_sizes = group_counts[np.searchsorted(group_ids, item_groups[audit_indices])]
                        residuals = (group_ids.size - pilot_size) / len(item_groups) * np.mean(
                            audit_sizes * (validation[:, audit_indices] - frozen[:, audit_indices]), axis=1)
                        predictions = np.clip(plugins[:, None] + residuals[:, None] * correction_grid, 0.0, 1.0)
                        inner_validation_mae += weights @ np.abs(predictions - truths[:, None])
                inner_validation_mae /= 2 * len(folds)
                correction_weight = correction_grid[int(np.argmin(inner_validation_mae))]
                loss = float(np.min(inner_validation_mae))
                if loss < best_loss:
                    best_loss = loss
                    best_config = dict(pilot_size=pilot_size, rank=rank, ridge=ridge,
                                       correction_weight=float(correction_weight))
    return best_config
