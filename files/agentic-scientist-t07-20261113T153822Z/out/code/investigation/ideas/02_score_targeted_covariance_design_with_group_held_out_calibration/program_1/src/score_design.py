"""Source-only score design using a regularized linear covariance proxy.

This is not an exact Bernoulli posterior or an unbiased estimator. Opaque
source partitions are not verified model genealogies. Internal source-group
comparisons are not independent target evidence or distribution-free intervals.
"""

import numpy as np


def group_weights(source_groups):
    unique_groups, group_inverse, group_sizes = np.unique(source_groups, return_inverse=True, return_counts=True)
    row_weights = 1.0 / (len(unique_groups) * group_sizes[group_inverse])
    return row_weights


class SourceFactors:
    def __init__(self, source_scores, source_groups, balanced=True):
        self.row_weights = group_weights(source_groups) if balanced else np.full(len(source_scores), 1.0 / len(source_scores))
        source_scores = np.asarray(source_scores, dtype=np.float64)
        full_scores = source_scores.mean(axis=1)
        self.item_mean = self.row_weights @ source_scores
        self.score_mean = float(self.row_weights @ full_scores)
        root_weights = np.sqrt(self.row_weights)
        weighted_centered_items = (source_scores - self.item_mean) * root_weights[:, None]
        weighted_centered_scores = (full_scores - self.score_mean) * root_weights
        score_covariance = weighted_centered_items.T @ weighted_centered_scores
        self.items = weighted_centered_items
        self.score_covariance = score_covariance
        self.item_variance = np.einsum('ij,ij->j', weighted_centered_items, weighted_centered_items)
        self.cross_columns = {}

    def cross_column(self, item):
        if item not in self.cross_columns:
            self.cross_columns[item] = self.items.T @ self.items[:, item]
        return self.cross_columns[item]

    def order(self, count, ridge, selector='score'):
        weighted_centered_items = self.items
        score_covariance = self.score_covariance
        selected_items = []
        variance_floor = 1e-12
        for step in range(count):
            if not selected_items:
                conditional_score_covariance = score_covariance.copy()
                conditional_item_variance = self.item_variance.copy()
            else:
                if len(selected_items) == 1 and selected_items[0] not in self.cross_columns:
                    candidate_cross_covariance = weighted_centered_items.T @ weighted_centered_items[:, selected_items]
                    self.cross_columns[selected_items[0]] = candidate_cross_covariance[:, 0]
                else:
                    candidate_cross_covariance = np.column_stack([self.cross_column(item) for item in selected_items])
                selected_system = candidate_cross_covariance[selected_items] + ridge * np.eye(len(selected_items))
                conditional_score_covariance = score_covariance - candidate_cross_covariance @ np.linalg.solve(selected_system, score_covariance[selected_items])
                previous_items = selected_items[:-1]
                if previous_items:
                    conditional_cross = candidate_cross_covariance[:, -1] - candidate_cross_covariance[:, :-1] @ np.linalg.solve(
                        selected_system[:-1, :-1], candidate_cross_covariance[previous_items, -1])
                else:
                    conditional_cross = candidate_cross_covariance[:, -1]
                conditional_item_variance = conditional_item_variance - conditional_cross ** 2 / max(
                    conditional_item_variance[selected_items[-1]] + ridge, variance_floor)
            conditional_gain = conditional_score_covariance ** 2 / np.maximum(conditional_item_variance + ridge, variance_floor)
            if selector == 'd_optimal':
                conditional_gain = conditional_item_variance.copy()
            conditional_gain[selected_items] = -np.inf
            next_item = int(np.argmax(conditional_gain))
            selected_items.append(next_item)
        return np.asarray(selected_items, dtype=np.int64)


class ScorePredictor:
    def __init__(self, ridge, budgets, selector='score', seed=0, balanced=True, factors=None):
        self.ridge = float(ridge)
        self.budgets = tuple(budgets)
        self.selector = selector
        self.seed = seed
        self.balanced = balanced
        self.factors = factors

    def fit(self, source_scores, source_groups):
        if self.factors is None:
            self.factors = SourceFactors(source_scores, source_groups, self.balanced)
        if self.selector == 'uniform':
            self.anchors = np.random.default_rng(self.seed).permutation(source_scores.shape[1])[:max(self.budgets)]
        else:
            self.anchors = self.factors.order(max(self.budgets), self.ridge, self.selector)
        self.models = {}
        ridge = self.ridge
        score_covariance = self.factors.score_covariance
        for budget in self.budgets:
            selected_items = self.anchors[:budget]
            selected_columns = self.factors.items[:, selected_items]
            selected_covariance = selected_columns.T @ selected_columns
            coefficients = np.linalg.solve(selected_covariance + ridge * np.eye(len(selected_items)), score_covariance[selected_items])
            self.models[budget] = coefficients
        return self

    def raw_predictions(self, source_scores, budget):
        selected_items = self.anchors[:budget]
        return self.factors.score_mean + (source_scores[:, selected_items] - self.factors.item_mean[selected_items]) @ self.models[budget]

    def predict_row(self, observed_scores, budget, calibration):
        selected_items = self.anchors[:budget]
        item_mean = self.factors.item_mean
        score_mean = self.factors.score_mean
        coefficients = self.models[budget]
        raw_score = score_mean + (observed_scores - item_mean[selected_items]) @ coefficients
        calibration_intercept, calibration_slope = calibration[budget]
        calibrated_score = calibration_intercept + calibration_slope * raw_score
        return float(np.clip(calibrated_score, 0.0, 1.0))

    def compact(self):
        self.factors.items = None
        self.factors.cross_columns.clear()


def affine_calibration(raw_predictions, true_scores, source_groups):
    weights = group_weights(source_groups)
    prediction_mean = float(weights @ raw_predictions)
    score_mean = float(weights @ true_scores)
    centered = raw_predictions - prediction_mean
    variance = float(weights @ (centered ** 2))
    if variance <= 1e-12:
        return 0.0, 1.0
    fitted_slope = float(weights @ (centered * (true_scores - score_mean))) / variance
    calibration_slope = max(0.0, fitted_slope)
    return score_mean - calibration_slope * prediction_mean, calibration_slope


def grouped_error(predictions, true_scores, groups):
    absolute_error = np.abs(predictions - true_scores)
    return float(np.mean([absolute_error[groups == group].mean() for group in np.unique(groups)]))


def tune_source(source_scores, source_groups, budgets, seed):
    unique_groups = np.unique(source_groups)
    identity = {budget: (0.0, 1.0) for budget in budgets}
    if len(unique_groups) < 6:
        return {selector: (0.025, identity.copy()) for selector in ('score', 'uniform')}
    random = np.random.default_rng(seed)
    group_order = random.permutation(unique_groups)
    partition = {int(group): position % 6 for position, group in enumerate(group_order)}
    partitions = np.asarray([partition[int(group)] for group in source_groups])
    strengths = (0.025, 0.1)
    true_scores = source_scores.mean(axis=1)
    records = {}
    for selector in ('score', 'uniform'):
        for ridge in strengths:
            records[selector, ridge] = {
                'raw': {budget: np.empty(len(source_scores)) for budget in budgets},
                'identity': {budget: np.empty(len(source_scores)) for budget in budgets},
                'affine': {budget: np.empty(len(source_scores)) for budget in budgets}}
    validation_mask = partitions % 2 == 0
    for fold in range(3):
        validation_rows = np.flatnonzero(partitions == 2 * fold)
        calibration_rows = np.flatnonzero(partitions == 2 * fold + 1)
        fit_rows = np.flatnonzero((partitions != 2 * fold) & (partitions != 2 * fold + 1))
        assert set(source_groups[fit_rows]).isdisjoint(source_groups[calibration_rows])
        assert set(source_groups[fit_rows]).isdisjoint(source_groups[validation_rows])
        assert set(source_groups[calibration_rows]).isdisjoint(source_groups[validation_rows])
        factors = SourceFactors(source_scores[fit_rows], source_groups[fit_rows])
        omitted_rows = np.concatenate((calibration_rows, validation_rows))
        for ridge in strengths:
            for selector in ('score', 'uniform'):
                fold_predictor = ScorePredictor(ridge, budgets, selector, seed, factors=factors)
                fold_predictor.fit(source_scores[fit_rows], source_groups[fit_rows])
                record = records[selector, ridge]
                for budget in budgets:
                    raw = fold_predictor.raw_predictions(source_scores[omitted_rows], budget)
                    record['raw'][budget][omitted_rows] = raw
                    calibration_raw = raw[:len(calibration_rows)]
                    validation_raw = raw[len(calibration_rows):]
                    intercept, slope = affine_calibration(calibration_raw, true_scores[calibration_rows], source_groups[calibration_rows])
                    record['identity'][budget][validation_rows] = np.clip(validation_raw, 0.0, 1.0)
                    record['affine'][budget][validation_rows] = np.clip(intercept + slope * validation_raw, 0.0, 1.0)
    configurations = {}
    for selector in ('score', 'uniform'):
        best = None
        for ridge in strengths:
            record = records[selector, ridge]
            choices = {}
            total_loss = 0.0
            for budget in budgets:
                losses = [(grouped_error(record[option][budget][validation_mask], true_scores[validation_mask], source_groups[validation_mask]), option != 'identity', option)
                          for option in ('identity', 'affine')]
                loss, unused_affine_flag, option = min(losses)
                choices[budget] = option
                total_loss += loss
            if best is None or total_loss < best[0]:
                best = (total_loss, ridge, choices)
        unused_loss, ridge, choices = best
        calibration = {}
        for budget in budgets:
            calibration[budget] = (affine_calibration(records[selector, ridge]['raw'][budget], true_scores, source_groups)
                                   if choices[budget] == 'affine' else (0.0, 1.0))
        configurations[selector] = ridge, calibration
    return configurations


def paired_group_summary(candidate_prediction, baseline_prediction, heldout_true_score, heldout_groups):
    paired_absolute_error_delta = np.abs(candidate_prediction - heldout_true_score) - np.abs(baseline_prediction - heldout_true_score)
    heldout_group_error = np.array([paired_absolute_error_delta[heldout_groups == group].mean() for group in np.unique(heldout_groups)])
    mean_delta = float(heldout_group_error.mean())
    standard_error = (float(heldout_group_error.std(ddof=1) / np.sqrt(len(heldout_group_error)))
                      if len(heldout_group_error) > 1 else None)
    return {'group_deltas': heldout_group_error, 'mean_delta': mean_delta,
            'group_standard_error': standard_error,
            'uncertainty_scope': 'descriptive outer-source groups, not target confidence'}


def anchor_control(factors, heldout_scores, budgets):
    second_moment = factors.item_variance + factors.item_mean ** 2
    centroid_cross = factors.items.T @ factors.items.mean(axis=1) + factors.item_mean * factors.item_mean.mean()
    distance = np.full(len(second_moment), np.inf)
    assignments = np.zeros(len(second_moment), dtype=np.int64)
    chosen = []
    next_item = int(np.argmin(second_moment - 2 * centroid_cross))
    predictions = {}
    for step in range(max(budgets)):
        chosen.append(next_item)
        cross = factors.cross_column(next_item) + factors.item_mean * factors.item_mean[next_item]
        current_distance = np.maximum(second_moment + second_moment[next_item] - 2 * cross, 0.0)
        closer = current_distance < distance
        assignments[closer] = step
        distance = np.minimum(distance, current_distance)
        if len(chosen) in budgets:
            weights = np.bincount(assignments, minlength=len(chosen)) / len(assignments)
            predictions[len(chosen)] = heldout_scores[:, chosen] @ weights
        available_distance = distance.copy()
        available_distance[chosen] = -np.inf
        next_item = int(np.argmax(available_distance))
    return predictions


def rasch_control(source_scores, source_groups, heldout_scores, anchors, budgets):
    """Local fixed-discrimination Rasch control, not the harness IRT baseline."""
    weights = group_weights(source_groups)
    difficulties = np.zeros(source_scores.shape[1])
    source_means = np.clip(source_scores.mean(axis=1), 0.01, 0.99)
    abilities = np.log(source_means / (1 - source_means))
    for iteration in range(10):
        probability = 1 / (1 + np.exp(-np.clip(abilities[:, None] - difficulties, -30, 30)))
        curvature = probability * (1 - probability)
        abilities += np.clip(((source_scores - probability).sum(axis=1) - abilities) / (curvature.sum(axis=1) + 1.0), -1.0, 1.0)
        difficulties += np.clip((weights @ (probability - source_scores) - 0.01 * difficulties) / (weights @ curvature + 0.01), -1.0, 1.0)
    results = {}
    for budget in budgets:
        selected = anchors[:budget]
        target_abilities = np.full(len(heldout_scores), float(weights @ abilities))
        for iteration in range(12):
            probability = 1 / (1 + np.exp(-np.clip(target_abilities[:, None] - difficulties[selected], -30, 30)))
            target_abilities += np.clip(((heldout_scores[:, selected] - probability).sum(axis=1) - 0.25 * target_abilities)
                                        / ((probability * (1 - probability)).sum(axis=1) + 0.25), -1.0, 1.0)
        results[budget] = np.mean(1 / (1 + np.exp(-np.clip(target_abilities[:, None] - difficulties, -30, 30))), axis=1)
    return results


def source_audit(source_scores, source_groups, budgets, seed):
    unique_groups = np.unique(source_groups)
    if len(unique_groups) < 8:
        return {'limitation': 'Fewer than eight groups: predetermined ridge, identity calibration; no nested outer assessment.'}
    shuffled = np.random.default_rng(seed).permutation(unique_groups)
    outer_groups = shuffled[:max(2, len(shuffled) // 4)]
    outer_mask = np.isin(source_groups, outer_groups)
    train_scores, train_groups = source_scores[~outer_mask], source_groups[~outer_mask]
    heldout_scores, heldout_groups = source_scores[outer_mask], source_groups[outer_mask]
    heldout_true_score = heldout_scores.mean(axis=1)
    assert set(train_groups).isdisjoint(heldout_groups)
    configurations = tune_source(train_scores, train_groups, budgets, seed)
    ridge, calibration = configurations['score']
    factors = SourceFactors(train_scores, train_groups)
    primary = ScorePredictor(ridge, budgets, seed=seed, factors=factors).fit(train_scores, train_groups)
    d_optimal = ScorePredictor(ridge, budgets, 'd_optimal', seed, factors=factors).fit(train_scores, train_groups)
    unweighted = ScorePredictor(ridge, budgets, seed=seed, balanced=False).fit(train_scores, train_groups)
    uniform_ridge, uniform_calibration = configurations['uniform']
    uniform = ScorePredictor(uniform_ridge, budgets, 'uniform', seed, factors=factors).fit(train_scores, train_groups)
    anchor_predictions = anchor_control(factors, heldout_scores, budgets)
    rasch_predictions = rasch_control(train_scores, train_groups, heldout_scores, primary.anchors, budgets)
    diagnostics = {'scope': 'One untouched outer source-group holdout; no target results.', 'budgets': {}}
    for budget in budgets:
        raw = primary.raw_predictions(heldout_scores, budget)
        intercept, slope = calibration[budget]
        candidate = np.clip(intercept + slope * raw, 0.0, 1.0)
        uniform_intercept, uniform_slope = uniform_calibration[budget]
        controls = {
            'uniform_mean': heldout_scores[:, uniform.anchors[:budget]].mean(axis=1),
            'source_mean': np.full(len(heldout_scores), factors.score_mean),
            'anchor_farthest_first': anchor_predictions[budget],
            'local_rasch_1pl': rasch_predictions[budget],
            'no_diversity': np.clip(uniform_intercept + uniform_slope * uniform.raw_predictions(heldout_scores, budget), 0.0, 1.0),
            'no_calibration': np.clip(raw, 0.0, 1.0)}
        comparisons = {name: paired_group_summary(candidate, baseline, heldout_true_score, heldout_groups)
                       for name, baseline in controls.items()}
        for name, predictor in (('d_optimal_raw', d_optimal), ('unweighted_raw', unweighted)):
            comparisons[name] = paired_group_summary(np.clip(raw, 0.0, 1.0),
                                                     np.clip(predictor.raw_predictions(heldout_scores, budget), 0.0, 1.0),
                                                     heldout_true_score, heldout_groups)
        diagnostics['budgets'][budget] = comparisons
    return diagnostics


def fit_candidate(source_scores, source_groups, budgets, seed, mode):
    source_groups = np.asarray(source_groups)
    if source_groups.shape != (len(source_scores),) or not np.issubdtype(source_groups.dtype, np.integer):
        raise ValueError('invalid source groups')
    if not budgets or min(budgets) <= 0 or list(budgets) != sorted(set(budgets)) or max(budgets) > source_scores.shape[1]:
        raise ValueError('budgets must be increasing distinct feasible prefixes')
    if mode not in ('primary', 'no_diversity', 'no_calibration'):
        raise ValueError('unknown fitting mode')
    if not len(source_scores):
        raise ValueError('empty source')
    diagnostics = source_audit(source_scores, source_groups, budgets, seed) if mode == 'primary' else {'scope': 'Control episode; outer audit omitted.'}
    if len(np.unique(source_groups)) < 8:
        configurations = {selector: (0.025, {budget: (0.0, 1.0) for budget in budgets}) for selector in ('score', 'uniform')}
    else:
        configurations = tune_source(source_scores, source_groups, budgets, seed)
    selector = 'uniform' if mode == 'no_diversity' else 'score'
    ridge, calibration = configurations[selector]
    if mode == 'no_calibration':
        calibration = {budget: (0.0, 1.0) for budget in budgets}
    predictor = ScorePredictor(ridge, budgets, selector, seed).fit(source_scores, source_groups)
    predictor.compact()
    return predictor, calibration, diagnostics
