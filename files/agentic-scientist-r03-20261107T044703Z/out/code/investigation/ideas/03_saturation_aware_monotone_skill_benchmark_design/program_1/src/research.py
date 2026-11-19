"""Optional internal controls and verification snippets; never called by RPC.

These are prospective computations, not executed results. The interface does
not expose fixed target panels, families, scientific controls, or diagnostics.
"""

import numpy as np

from program import (configure, fit_curves, make_likelihoods, new_context,
                     predict_context, select_context, transfer_gain_for_candidate,
                     update_context, weighted_pava)


def fixed_panel_controls(historical_scores, historical_mask, seed=17,
                         max_queries=8, steps=6, validation_count=12):
    """Compare selectors on a disjoint historical panel and predictors on queries.

    Target values are used only for scoring, never for model fitting, posterior
    updates, candidate shortlists, or query selection. Target *identities* are
    supplied only to this internal historical control, not to the RPC candidate.
    """
    random = np.random.default_rng(seed)
    eligible = np.flatnonzero(historical_mask.sum(axis=1) >= 3)
    holdout_count = min(validation_count, len(eligible) // 5,
                        max(0, len(historical_scores) - 3))
    if holdout_count == 0:
        return []
    validation_indices = np.sort(random.permutation(eligible)[:holdout_count])
    inner_train_indices = np.setdiff1d(np.arange(len(historical_scores)), validation_indices)
    assert not np.intersect1d(inner_train_indices, validation_indices).size
    fitted = fit_curves(historical_scores[inner_train_indices],
                         historical_mask[inner_train_indices], min(steps, 6))
    models = {name: configure(fitted, (name, 1.5, 17))
              for name in ('task_mean', 'linear_skill', 'monotone_skill')}
    records = []
    for row_index in validation_indices:
        columns = random.permutation(np.flatnonzero(historical_mask[row_index]))
        target_panel = np.zeros(historical_scores.shape[1], dtype=bool)
        target_panel[columns[:max(1, len(columns) // 2)]] = True
        query_panel = historical_mask[row_index] & ~target_panel
        feasible_budget = min(max_queries, int(query_panel.sum()))
        random_order = random.permutation(np.flatnonzero(query_panel))
        for selector in ('adaptive', 'frozen', 'random'):
            contexts = {name: new_context(model, query_panel)
                        for name, model in models.items()}
            for budget in range(feasible_budget + 1):
                for name, model in models.items():
                    prediction = predict_context(model, contexts[name])
                    loss = np.mean((prediction[target_panel]
                                    - historical_scores[row_index, target_panel]) ** 2)
                    records.append({'row': int(row_index), 'budget': budget,
                                    'selector': selector, 'predictor': name,
                                    'mse': float(loss)})
                if budget == feasible_budget:
                    continue
                if selector == 'random':
                    task_index = int(random_order[budget])
                else:
                    task_index = select_context(models['monotone_skill'],
                        contexts['monotone_skill'], frozen=(selector == 'frozen'),
                        target_panel=target_panel)
                for name, model in models.items():
                    update_context(model, contexts[name], task_index,
                                   historical_scores[row_index, task_index])
    return records


def paired_row_bootstrap(records, first, second, budget, seed=17, replicates=2000):
    """Row-paired MSE improvement (second minus first), conditional on this split.

    Each method is (selector, predictor). Intervals are not training-split or
    family-cluster intervals, and no interval is meaningful without real runs.
    """
    first_losses = {record['row']: record['mse'] for record in records
                    if (record['selector'], record['predictor']) == first
                    and record['budget'] == budget}
    second_losses = {record['row']: record['mse'] for record in records
                     if (record['selector'], record['predictor']) == second
                     and record['budget'] == budget}
    rows = sorted(first_losses.keys() & second_losses.keys())
    if not rows:
        return None
    gains = np.asarray([second_losses[row] - first_losses[row] for row in rows])
    random = np.random.default_rng(seed)
    bootstrap_means = np.asarray([np.mean(random.choice(gains, len(gains), replace=True))
                                  for replicate in range(replicates)])
    return {'rows': len(rows), 'mean_gain': float(gains.mean()),
            'low': float(np.quantile(bootstrap_means, 0.025)),
            'high': float(np.quantile(bootstrap_means, 0.975))}


def verify_working_identities():
    """Unexecuted assertions for finite-bin algebra, not public-data evidence."""
    skill_grid = np.linspace(-1.0, 1.0, 33)
    prior = np.exp(-0.5 * (skill_grid / 0.5) ** 2)
    prior /= prior.sum()
    slopes = np.array([0.12, 0.2, 0.1])
    curve_grid = 0.5 + skill_grid[:, None] * slopes
    noise_variances = np.array([0.01, 0.02, 0.005])
    likelihoods = make_likelihoods(curve_grid, noise_variances, 18)
    assert np.all(likelihoods >= 0.0)
    assert np.allclose(likelihoods.sum(axis=2), 1.0, atol=1e-12)
    model = {'name': 'linear_skill', 'skill_grid': skill_grid,
             'curve_grid': curve_grid, 'noise_variances': noise_variances,
             'prior': prior, 'bin_likelihoods': likelihoods,
             'task_means': np.full(3, 0.5)}
    available = np.ones(3, dtype=bool)
    queried = np.zeros(3, dtype=bool)
    coarse_model = dict(model)
    coarse_model['bin_likelihoods'] = likelihoods.reshape(3, 33, 9, 2).sum(axis=3)
    assert np.allclose(coarse_model['bin_likelihoods'],
                       make_likelihoods(curve_grid, noise_variances, 9), atol=1e-12)
    for candidate_index in range(3):
        fine_gain = transfer_gain_for_candidate(model, prior, available, queried, candidate_index)
        coarse_gain = transfer_gain_for_candidate(coarse_model, prior, available, queried, candidate_index)
        assert fine_gain >= -1e-12
        assert fine_gain + 1e-12 >= coarse_gain
        joint = prior[:, None] * likelihoods[candidate_index]
        bin_probability = joint.sum(axis=0)
        bin_posterior = joint / np.maximum(bin_probability[None, :], 1e-300)
        target_mask = np.arange(3) != candidate_index
        target_curves = curve_grid[:, target_mask]
        current_mean = prior @ target_curves
        posterior_means = bin_posterior.T @ target_curves
        prior_variance = np.mean(prior @ ((target_curves - current_mean) ** 2))
        within_bin_variance = np.sum(bin_posterior[:, :, None]
            * (target_curves[:, None, :] - posterior_means[None, :, :]) ** 2, axis=0)
        remaining_variance = np.mean(bin_probability @ within_bin_variance)
        assert np.isclose(fine_gain, prior_variance - remaining_variance, atol=1e-12)
        posterior_skill_mean = bin_posterior.T @ skill_grid
        scalar_gain = np.sum(bin_probability * (posterior_skill_mean - prior @ skill_grid) ** 2)
        affine_gain = np.mean(slopes[target_mask] ** 2) * scalar_gain
        assert np.isclose(fine_gain, affine_gain, atol=1e-12)
    context = new_context(model, available)
    untouched_context = new_context(model, available)
    posterior_before = context['posterior'].copy()
    selected = select_context(model, context)
    assert np.array_equal(context['posterior'], posterior_before)
    update_context(model, context, selected, 0.83)
    assert np.isfinite(context['posterior']).all()
    assert np.isclose(context['posterior'].sum(), 1.0)
    assert predict_context(model, context)[selected] == 0.83
    assert np.array_equal(untouched_context['posterior'], prior)
    assert transfer_gain_for_candidate(model, prior, np.array([True, False, False]),
                                       queried, 0) == 0.0
    values = np.array([3.0, 1.0, 2.0, 0.0])
    weights = np.array([1.0, 2.0, 1.0, 1.0])
    pooled = weighted_pava(values, weights)
    assert np.all(np.diff(pooled) >= 0.0)
    assert np.isclose(np.dot(pooled, weights), np.dot(values, weights))


def verify_mask_and_degenerate_histories():
    """Unexecuted assertions covering ignored zeros, ties, and unsupported tasks."""
    scores = np.array([[0.2, 0.4, 0.0], [0.3, 0.0, 0.0],
                       [0.6, 0.7, 0.0], [0.8, 0.9, 0.0]])
    mask = np.array([[True, True, False], [True, False, False],
                     [True, True, False], [True, True, False]])
    altered_scores = np.where(mask, scores, 123.0)
    first = fit_curves(scores, mask, 3)
    second = fit_curves(altered_scores, mask, 3)
    for name in ('task_mean', 'linear_skill', 'monotone_skill'):
        assert np.allclose(first['curves'][name], second['curves'][name])
        assert np.all(np.diff(first['curves'][name], axis=0) >= -1e-12)
        assert np.all(first['curves'][name][:, 2] == 0.5)
        assert np.all(first['variances'][name] > 0.0)
    for degenerate_mask in (np.zeros((4, 3), dtype=bool), np.ones((4, 3), dtype=bool)):
        fitted = fit_curves(np.full((4, 3), 0.5), degenerate_mask, 2)
        model = configure(fitted, ('monotone_skill', 1.5, 9))
        context = new_context(model, np.ones(3, dtype=bool))
        assert np.isfinite(predict_context(model, context)).all()
        assert np.isclose(model['prior'].sum(), 1.0)
