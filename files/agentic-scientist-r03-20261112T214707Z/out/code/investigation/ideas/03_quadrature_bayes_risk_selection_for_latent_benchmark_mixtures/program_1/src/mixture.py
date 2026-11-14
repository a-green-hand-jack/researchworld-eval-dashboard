"""Historical-only latent mixtures with validation-gated quadrature L1 selection."""

from functools import lru_cache
import math
import time

import numpy as np


_ERFC = np.vectorize(math.erfc, otypes=[np.float64])


def normal_cdf(values):
    return 0.5 * _ERFC(-np.asarray(values, dtype=np.float64) / math.sqrt(2.0))


def normal_pdf(values):
    values = np.asarray(values, dtype=np.float64)
    return np.exp(-0.5 * values ** 2) / math.sqrt(2.0 * math.pi)


def bounded_mixture_median(component_weight, component_mean, conditional_std):
    component_weight = np.asarray(component_weight, dtype=np.float64)
    component_mean = np.asarray(component_mean, dtype=np.float64)
    conditional_std = np.maximum(np.asarray(conditional_std, dtype=np.float64), 1e-7)
    if component_mean.shape[-2] == 1:
        return np.clip(component_mean[..., 0, :], 0.0, 1.0)
    lower_bound = np.zeros(component_mean.shape[:-2] + component_mean.shape[-1:])
    upper_bound = np.ones_like(lower_bound)
    for _ in range(25):
        midpoint = (lower_bound + upper_bound) * 0.5
        posterior_cdf = np.sum(
            component_weight[..., :, None] * normal_cdf(
                (midpoint[..., None, :] - component_mean) / conditional_std[..., None, :]),
            axis=-2,
        )
        lower_bound = np.where(posterior_cdf < 0.5, midpoint, lower_bound)
        upper_bound = np.where(posterior_cdf >= 0.5, midpoint, upper_bound)
    return np.clip((lower_bound + upper_bound) * 0.5, 0.0, 1.0)


def mixture_absolute_risk(component_weight, component_mean, conditional_std):
    component_weight = np.asarray(component_weight, dtype=np.float64)
    component_mean = np.asarray(component_mean, dtype=np.float64)
    conditional_std = np.maximum(np.asarray(conditional_std, dtype=np.float64), 1e-7)
    posterior_median = bounded_mixture_median(component_weight, component_mean, conditional_std)
    if component_mean.ndim == 2:
        standardized = (posterior_median[None, :] - component_mean) / conditional_std[None, :]
        component_risk = 2.0 * conditional_std[None, :] * normal_pdf(standardized) + (component_mean - posterior_median[None, :]) * (1.0 - 2.0 * normal_cdf(standardized))
        return np.sum(component_weight[:, None] * component_risk, axis=0)
    standardized = (posterior_median[..., None, :] - component_mean) / conditional_std[..., None, :]
    component_risk = (
        2.0 * conditional_std[..., None, :] * normal_pdf(standardized)
        + (component_mean - posterior_median[..., None, :]) * (1.0 - 2.0 * normal_cdf(standardized))
    )
    return np.sum(component_weight[..., :, None] * component_risk, axis=-2)


@lru_cache(maxsize=4)
def quadrature_rule(quadrature_order):
    nodes, weights = np.polynomial.hermite.hermgauss(quadrature_order)
    nodes.setflags(write=False)
    weights.setflags(write=False)
    return nodes, weights


def clone_conditioned_row(row_state, chosen_index, query_value, gaussian_module):
    hypothetical_row = MixtureRow.__new__(MixtureRow)
    hypothetical_row.model = row_state.model
    hypothetical_row.component_weight = row_state.component_weight.copy()
    hypothetical_row.component_mean = row_state.component_mean.copy()
    hypothetical_row.within_covariance = row_state.within_covariance.copy()
    hypothetical_row.panel_covariance = row_state.panel_covariance.copy()
    hypothetical_row.observed = row_state.observed.copy()
    hypothetical_row.values = row_state.values.copy()
    hypothetical_row.selection_diagnostics = row_state.selection_diagnostics.copy()
    hypothetical_row.reveal(chosen_index, query_value, gaussian_module)
    return hypothetical_row


def quadrature_transfer_gain(row_state, chosen_index, quadrature_order, gaussian_module):
    nodes, weights = quadrature_rule(quadrature_order)
    query_variance = max(float(row_state.within_covariance[chosen_index, chosen_index]), 1e-12)
    component_query_mean = row_state.component_mean[:, chosen_index]
    query_values = component_query_mean[:, None] + np.sqrt(2.0 * query_variance) * nodes[None, :]
    outcome_weights = row_state.component_weight[:, None] * weights[None, :] / np.sqrt(np.pi)
    prior_std = np.sqrt(np.maximum(np.diag(row_state.within_covariance), 1e-14))
    prior_risk = mixture_absolute_risk(row_state.component_weight, row_state.component_mean, prior_std)
    expected_posterior_risk = np.zeros_like(prior_risk)
    posterior_weights = []
    posterior_means = []
    posterior_stds = []
    for query_value, outcome_weight in zip(query_values.ravel(), outcome_weights.ravel()):
        hypothetical_row = clone_conditioned_row(row_state, chosen_index, float(query_value), gaussian_module)
        posterior_std = np.sqrt(np.maximum(np.diag(hypothetical_row.within_covariance), 1e-14))
        if len(row_state.component_weight) == 1:
            expected_posterior_risk += outcome_weight * mixture_absolute_risk(hypothetical_row.component_weight, hypothetical_row.component_mean, posterior_std)
        else:
            posterior_weights.append(hypothetical_row.component_weight)
            posterior_means.append(hypothetical_row.component_mean)
            posterior_stds.append(posterior_std)
    if posterior_weights:
        posterior_risks = mixture_absolute_risk(
            np.asarray(posterior_weights), np.asarray(posterior_means), np.asarray(posterior_stds),
        )
        expected_posterior_risk = np.sum(outcome_weights.reshape(-1, 1) * posterior_risks, axis=0)
    target_mask = np.ones(len(prior_risk), dtype=bool)
    target_mask[np.asarray(row_state.observed + [chosen_index], dtype=int)] = False
    return float(np.sum((prior_risk - expected_posterior_risk)[target_mask]))


class LatentMixture:
    def __init__(self, base, component_count=1, regularization=2.0,
                 selector='variance', prediction_kind='median', adaptive=True):
        self.base = base
        self.mean_ = base.mean_.copy()
        self.component_count = component_count
        self.regularization = regularization
        self.selector = selector
        self.incumbent_selector = selector
        self.quadrature_order = 3
        self.shortlist_size = 4
        self.prediction_kind = prediction_kind
        self.adaptive = adaptive
        self.component_weight_ = np.ones(1)
        self.component_mean_ = self.mean_[None, :].copy()
        self.within_covariance_ = base.covariance_.copy()
        self.covariance_ = base.covariance_.copy()
        self.validation_records_ = []
        self.validation_choice_ = None

    def fit_profiles(self, historical_scores, historical_mask, sweeps):
        if self.component_count == 1:
            return self
        loadings = self.base.loadings_
        residual = self.base.residual_variance_
        rank = loadings.shape[1]
        informative_ids = np.flatnonzero(historical_mask.any(axis=1))
        if len(informative_ids) < max(16, 4 * self.component_count):
            raise ValueError('insufficient informative historical rows')
        grams = []
        right_sides = []
        quadratic_terms = []
        normalizers = []
        for model_index in informative_ids:
            observed_indices = np.flatnonzero(historical_mask[model_index])
            row_loadings = loadings[observed_indices]
            row_residual = residual[observed_indices]
            centered_scores = historical_scores[model_index, observed_indices] - self.mean_[observed_indices]
            grams.append(row_loadings.T @ (row_loadings / row_residual[:, None]))
            right_sides.append(row_loadings.T @ (centered_scores / row_residual))
            quadratic_terms.append(float(np.sum(centered_scores ** 2 / row_residual)))
            normalizers.append(float(np.log(row_residual).sum() + len(observed_indices) * math.log(2.0 * math.pi)))
        grams = np.asarray(grams)
        right_sides = np.asarray(right_sides)
        quadratic_terms = np.asarray(quadratic_terms)
        normalizers = np.asarray(normalizers)
        identity = np.eye(rank)
        initial_means = np.linalg.solve(grams + identity, right_sides[..., None])[..., 0]
        distance = np.sum((initial_means - initial_means.mean(axis=0)) ** 2, axis=1)
        centers = [initial_means[int(np.argmax(distance))].copy()]
        for _ in range(1, self.component_count):
            distance = np.min(np.sum((initial_means[:, None, :] - np.asarray(centers)[None, :, :]) ** 2, axis=2), axis=1)
            centers.append(initial_means[int(np.argmax(distance))].copy())
        centers = np.asarray(centers)
        for _ in range(6):
            assignment = np.argmin(np.sum((initial_means[:, None, :] - centers[None, :, :]) ** 2, axis=2), axis=1)
            for component_index in range(self.component_count):
                eligible = assignment == component_index
                if eligible.any():
                    centers[component_index] = initial_means[eligible].mean(axis=0)
        component_weight = np.full(self.component_count, 1.0 / self.component_count)
        tau_squared = 0.5
        em_likelihood = []
        for _ in range(max(1, min(sweeps, 12))):
            precision = grams + identity / tau_squared
            latent_covariances = np.linalg.solve(precision, np.broadcast_to(identity, precision.shape))
            latent_rhs = right_sides[:, None, :] + centers[None, :, :] / tau_squared
            latent_means = np.einsum('mrs,mgs->mgr', latent_covariances, latent_rhs)
            log_determinant = np.linalg.slogdet(precision)[1] + rank * math.log(tau_squared)
            marginal_quadratic = quadratic_terms[:, None] + np.sum(centers ** 2, axis=1)[None, :] / tau_squared
            marginal_quadratic -= np.sum(latent_rhs * latent_means, axis=2)
            log_responsibility = np.log(np.maximum(component_weight, 1e-300))[None, :] - 0.5 * (
                normalizers[:, None] + log_determinant[:, None] + marginal_quadratic
            )
            row_maximum = log_responsibility.max(axis=1, keepdims=True)
            responsibility = np.exp(log_responsibility - row_maximum)
            row_mass = responsibility.sum(axis=1, keepdims=True)
            responsibility /= row_mass
            em_likelihood.append(float(np.sum(row_maximum + np.log(row_mass))))
            mass = responsibility.sum(axis=0)
            first_moment = np.zeros_like(centers)
            second_moment = np.zeros((self.component_count, rank, rank))
            for row_index in range(len(informative_ids)):
                latent_covariance = latent_covariances[row_index]
                for component_index in range(self.component_count):
                    latent_mean = latent_means[row_index, component_index]
                    latent_second_moment = latent_covariance + np.outer(latent_mean, latent_mean)
                    weight = responsibility[row_index, component_index]
                    first_moment[component_index] += weight * latent_mean
                    second_moment[component_index] += weight * latent_second_moment
            centers = first_moment / (mass[:, None] + self.regularization)
            expected_distance = np.trace(second_moment, axis1=1, axis2=2)
            expected_distance -= 2.0 * np.sum(centers * first_moment, axis=1)
            expected_distance += mass * np.sum(centers ** 2, axis=1)
            numerator = expected_distance.sum() + self.regularization * (np.sum(centers ** 2) + rank)
            denominator = rank * (len(informative_ids) + self.component_count + self.regularization)
            tau_squared = float(np.clip(numerator / denominator, 0.08, 2.5))
            component_weight = (mass + 1.0) / (len(informative_ids) + self.component_count)
        self.component_weight_ = component_weight
        self.component_mean_ = self.mean_[None, :] + centers @ loadings.T
        self.within_covariance_ = tau_squared * (loadings @ loadings.T) + np.diag(residual)
        self.mean_ = component_weight @ self.component_mean_
        centered = self.component_mean_ - self.mean_[None, :]
        self.covariance_ = self.within_covariance_ + (centered.T * component_weight) @ centered
        self.latent_centers_ = centers
        self.tau_squared_ = tau_squared
        self.em_likelihood_ = em_likelihood
        if not all(np.isfinite(array).all() for array in (
                self.component_weight_, self.component_mean_, self.within_covariance_, self.covariance_)):
            raise ValueError('nonfinite latent mixture')
        return self


class MixtureRow:
    def __init__(self, model):
        self.model = model
        self.component_weight = model.component_weight_.copy()
        self.component_mean = model.component_mean_.copy()
        self.within_covariance = model.within_covariance_.copy()
        self.panel_covariance = model.covariance_.copy()
        self.observed = []
        self.values = []
        self.selection_diagnostics = {'calls': 0, 'failures': 0, 'unchanged': 0, 'seconds': 0.0}

    def reveal(self, chosen_index, observed_value, gaussian_module):
        component_weight = self.component_weight
        component_mean = self.component_mean
        within_covariance = self.within_covariance
        selected_covariance = within_covariance[:, chosen_index].copy()
        within_variance = max(float(within_covariance[chosen_index, chosen_index]), 1e-12)
        conditioning_gain = selected_covariance / within_variance
        log_component_weight = np.log(np.maximum(component_weight, 1e-300)) - 0.5 * (observed_value - component_mean[:, chosen_index]) ** 2 / within_variance
        component_weight = np.exp(log_component_weight - np.max(log_component_weight))
        component_weight /= component_weight.sum()
        component_mean += (observed_value - component_mean[:, chosen_index])[:, None] * conditioning_gain[None, :]
        within_covariance -= np.outer(selected_covariance, selected_covariance) / within_variance
        within_covariance[chosen_index, :] = 0.0
        within_covariance[:, chosen_index] = 0.0
        component_mean[:, chosen_index] = observed_value
        self.component_weight = component_weight
        self.observed.append(chosen_index)
        self.values.append(observed_value)
        if not self.model.adaptive:
            gaussian_module.reveal_covariance(self.panel_covariance, chosen_index)

    def total_covariance(self):
        component_weight = self.component_weight
        component_mean = self.component_mean
        within_covariance = self.within_covariance
        mixture_center = component_mean - np.sum(component_weight[:, None] * component_mean, axis=0)
        mixture_covariance = within_covariance + (mixture_center.T * component_weight) @ mixture_center
        return mixture_covariance

    def select(self, available, gaussian_module):
        mixture_covariance = self.total_covariance() if self.model.adaptive else self.panel_covariance
        if self.model.selector == 'variance':
            return gaussian_module.transfer_select(mixture_covariance, available, self.observed)
        candidate_indices = np.asarray(sorted(set(available) - set(self.observed)), dtype=int)
        observed_indices = np.asarray(self.observed, dtype=int)
        target_variance = np.maximum(np.diag(mixture_covariance), 0.0)
        candidate_variance = np.maximum(target_variance[candidate_indices], 1e-12)
        post_variance = np.maximum(target_variance[:, None] - mixture_covariance[:, candidate_indices] ** 2 / candidate_variance[None, :], 0.0)
        absolute_gain = np.sqrt(target_variance[:, None]) - np.sqrt(post_variance)
        absolute_gain[candidate_indices, np.arange(len(candidate_indices))] = 0.0
        absolute_gain[observed_indices, :] = 0.0
        surrogate_gain = absolute_gain.sum(axis=0)
        chosen_index = int(candidate_indices[int(np.argmax(surrogate_gain))])
        if self.model.selector != 'quadrature':
            return chosen_index
        incumbent_column = (
            gaussian_module.transfer_select(mixture_covariance, available, self.observed)
            if self.model.incumbent_selector == 'variance' else chosen_index
        )
        if len(candidate_indices) == 1:
            return int(incumbent_column)
        started = time.perf_counter()
        self.selection_diagnostics['calls'] += 1
        shortlist_size = self.model.shortlist_size
        quadrature_order = self.model.quadrature_order
        shortlist = candidate_indices[np.argsort(-surrogate_gain, kind='stable')[:shortlist_size]]
        shortlist = np.unique(np.append(shortlist, incumbent_column))
        try:
            with np.errstate(over='raise', invalid='raise', divide='raise'):
                integrated_gains = np.asarray([quadrature_transfer_gain(self, int(column), quadrature_order, gaussian_module) for column in shortlist])
            if not np.all(np.isfinite(integrated_gains)):
                self.selection_diagnostics['failures'] += 1
                return int(incumbent_column)
            selected_column = int(shortlist[int(np.argmax(integrated_gains))])
            self.selection_diagnostics['unchanged'] += int(selected_column == incumbent_column)
            return int(shortlist[int(np.argmax(integrated_gains))])
        except (ValueError, FloatingPointError, OverflowError, np.linalg.LinAlgError):
            self.selection_diagnostics['failures'] += 1
            return int(incumbent_column)
        finally:
            self.selection_diagnostics['seconds'] += time.perf_counter() - started

    def predict(self, gaussian_module, prediction_kind=None):
        if self.model.component_count == 1:
            return gaussian_module.condition(self.model.base, self.observed, self.values)
        component_weight = self.component_weight
        component_mean = self.component_mean
        kind = self.model.prediction_kind if prediction_kind is None else prediction_kind
        if kind == 'mean':
            prediction = np.clip(component_weight @ component_mean, 0.0, 1.0)
        else:
            conditional_std = np.sqrt(np.maximum(np.diag(self.within_covariance), 1e-14))
            prediction = bounded_mixture_median(component_weight, component_mean, conditional_std)
        prediction[self.observed] = self.values
        return prediction


def validation_replay(model, scores, observed_mask, validation_model_ids,
                      audit_target_mask, gaussian_module):
    started = time.perf_counter()
    columns = scores.shape[1]
    records = []
    for model_id in validation_model_ids:
        validation_scores = scores[model_id]
        validation_observed_mask = observed_mask[model_id]
        fixed_target_mask = validation_observed_mask & audit_target_mask
        query_candidates = np.flatnonzero(validation_observed_mask & ~audit_target_mask)
        if not len(query_candidates) or not np.any(fixed_target_mask):
            continue
        row = MixtureRow(model)
        queried_mask = np.zeros(columns, dtype=bool)
        budget = min(8, len(query_candidates))
        row_errors = []
        mean_errors = []
        checkpoints = []
        for count in range(1, budget + 1):
            chosen_index = row.select(query_candidates, gaussian_module)
            row.reveal(chosen_index, float(validation_scores[chosen_index]), gaussian_module)
            queried_mask[chosen_index] = True
            assert not np.any(queried_mask & audit_target_mask)
            if count in (1, 2, 4, 8) or count == budget:
                prediction = row.predict(gaussian_module)
                validation_mae = np.mean(np.abs(prediction[fixed_target_mask] - validation_scores[fixed_target_mask]))
                mean_prediction = row.predict(gaussian_module, prediction_kind='mean')
                row_errors.append(float(validation_mae))
                mean_errors.append(float(np.mean(np.abs(mean_prediction[fixed_target_mask] - validation_scores[fixed_target_mask]))))
                checkpoints.append(count)
        records.append({
            'model_id': int(model_id), 'target_count': int(fixed_target_mask.sum()),
            'budgets': checkpoints, 'checkpoint_mae': row_errors,
            'mean_checkpoint_mae': mean_errors, 'mae': float(np.mean(row_errors)),
            'mean_mae': float(np.mean(mean_errors)), 'queries': row.observed.copy(),
            'selection_diagnostics': row.selection_diagnostics.copy(),
        })
    row_losses = np.asarray([record['mae'] for record in records])
    return {
        'component_count': model.component_count, 'rank': model.base.rank,
        'shrinkage': model.base.shrinkage, 'regularization': model.regularization,
        'selector': model.selector, 'adaptive': model.adaptive,
        'prediction_kind': model.prediction_kind, 'rows': records,
        'loss': float(row_losses.mean()) if len(row_losses) else float('inf'),
        'seconds': time.perf_counter() - started,
    }


def paired_summary(differences):
    differences = np.asarray(differences, dtype=np.float64)
    standard_error = float(np.std(differences, ddof=1) / np.sqrt(len(differences)))
    return {'paired_delta': float(differences.mean()),
            'paired_standard_error': standard_error, 'row_count': len(differences)}


def validate_quadrature_selector(model, incumbent_record, scores, observed_mask,
                                validation_model_ids, audit_target_mask, gaussian_module):
    incumbent_selector = incumbent_record['selector']
    model.incumbent_selector = incumbent_selector
    model.selector = 'quadrature'
    try:
        quadrature_record = validation_replay(
            model, scores, observed_mask, validation_model_ids, audit_target_mask, gaussian_module,
        )
    finally:
        model.selector = incumbent_selector
    quadrature_model_ids = [row['model_id'] for row in quadrature_record['rows']]
    incumbent_model_ids = [row['model_id'] for row in incumbent_record['rows']]
    assert quadrature_model_ids == incumbent_model_ids
    for quadrature_row, incumbent_row in zip(quadrature_record['rows'], incumbent_record['rows']):
        assert quadrature_row['budgets'] == incumbent_row['budgets']
        assert quadrature_row['target_count'] == incumbent_row['target_count']
    quadrature_row_mae = [row['mae'] for row in quadrature_record['rows']]
    incumbent_row_mae = [row['mae'] for row in incumbent_record['rows']]
    paired_delta = np.asarray(quadrature_row_mae) - np.asarray(incumbent_row_mae)
    paired_standard_error = float('inf')
    if paired_delta.size > 1:
        paired_standard_error = np.std(paired_delta, ddof=1) / np.sqrt(paired_delta.size)
    use_quadrature = paired_delta.size > 1 and np.mean(paired_delta) + paired_standard_error < 0.0
    failure_count = sum(row['selection_diagnostics']['failures'] for row in quadrature_record['rows'])
    use_quadrature = bool(use_quadrature and np.isfinite(paired_delta).all() and failure_count == 0)
    matching_queries = sum(
        sum(new_column == old_column for new_column, old_column in zip(new_row['queries'], old_row['queries']))
        for new_row, old_row in zip(quadrature_record['rows'], incumbent_record['rows'])
    )
    quadrature_record.update({
        'ablation': 'quadrature_minus_incumbent_same_fitted_distribution',
        'incumbent_selector': incumbent_selector, 'quadrature_order': model.quadrature_order,
        'shortlist_size': model.shortlist_size, 'use_quadrature': use_quadrature,
        'paired_delta': float(np.mean(paired_delta)) if paired_delta.size else float('inf'),
        'paired_standard_error': float(paired_standard_error), 'row_count': int(paired_delta.size),
        'paired_row_deltas': paired_delta.tolist(), 'failure_count': failure_count,
        'matching_queries': matching_queries,
        'query_count': sum(len(row['queries']) for row in quadrature_record['rows']),
        'incumbent_seconds': incumbent_record['seconds'],
    })
    return quadrature_record, use_quadrature


def tune_fit(scores, observed_mask, seed, sweeps, gaussian_module):
    """Select on fixed historical audit cells only; no outer-row data enter fit."""
    def fallback(reason):
        result = LatentMixture(gaussian_module.tune_fit(scores, observed_mask, seed, sweeps))
        result.validation_choice_ = {'component_count': 1, 'selector': 'variance', 'fallback': reason}
        return result

    rows, columns = scores.shape
    if rows < 8 or columns < 2:
        return fallback('small historical matrix')
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(rows)
    validation_count = min(32, max(2, rows // 5))
    validation_model_ids = permutation[:validation_count]
    train_model_ids = permutation[validation_count:]
    assert not np.intersect1d(train_model_ids, validation_model_ids).size
    train_scores = scores[train_model_ids]
    train_observed_mask = observed_mask[train_model_ids]
    audit_target_mask = np.zeros(columns, dtype=bool)
    audit_target_mask[rng.permutation(columns)[:max(1, columns // 3)]] = True
    eligible_validation_ids = [model_id for model_id in validation_model_ids
                               if np.any(observed_mask[model_id] & audit_target_mask)
                               and np.any(observed_mask[model_id] & ~audit_target_mask)]
    if len(eligible_validation_ids) < 6:
        return fallback('fewer than six usable held-out historical rows')
    records = []
    best_base = None
    best_base_record = None
    for rank in (2, 4, 8):
        if rank > max(2, min(len(train_model_ids) - 1, columns)):
            continue
        for shrinkage in (2.0, 12.0):
            base = gaussian_module.ResidualCovariance(rank=rank, shrinkage=shrinkage, sweeps=min(sweeps, 12))
            base.fit(train_scores, train_observed_mask)
            model = LatentMixture(base)
            record = validation_replay(model, scores, observed_mask, validation_model_ids, audit_target_mask, gaussian_module)
            records.append(record)
            if np.isfinite(record['loss']) and (best_base_record is None or record['loss'] < best_base_record['loss']):
                best_base, best_base_record = base, record
    if best_base is None:
        return fallback('invalid Gaussian validation')
    baseline_losses = np.asarray([row['mae'] for row in best_base_record['rows']])
    chosen_record = best_base_record
    single_component_records = {'variance': best_base_record}
    best_mixture_model = None
    best_mixture_record = None
    profile_models = {(1, 2.0): LatentMixture(best_base)}
    for component_count in (1, 2, 4):
        for regularization in ((2.0,) if component_count == 1 else (2.0, 8.0)):
            model = LatentMixture(best_base, component_count, regularization)
            try:
                model.fit_profiles(train_scores, train_observed_mask, sweeps)
            except (ValueError, np.linalg.LinAlgError) as error:
                records.append({'component_count': component_count, 'regularization': regularization,
                                'skipped': str(error)})
                continue
            profile_models[(component_count, regularization)] = model
            for selector in ('variance', 'sqrt'):
                if component_count == 1 and selector == 'variance':
                    continue
                model.selector = selector
                record = validation_replay(model, scores, observed_mask, validation_model_ids, audit_target_mask, gaussian_module)
                differences = np.asarray([row['mae'] for row in record['rows']]) - baseline_losses
                record.update(paired_summary(differences))
                paired_se = record['paired_standard_error']
                if component_count == 1:
                    single_component_records[selector] = record
                else:
                    matched_single = single_component_records[selector]
                    assert [row['model_id'] for row in record['rows']] == [row['model_id'] for row in matched_single['rows']]
                    record['mixture_minus_single_same_selector'] = paired_summary([
                        mixture_row['mae'] - single_row['mae']
                        for mixture_row, single_row in zip(record['rows'], matched_single['rows'])
                    ])
                    record['median_minus_mean_same_queries'] = paired_summary([
                        row['mae'] - row['mean_mae'] for row in record['rows']
                    ])
                records.append(record)
                if component_count > 1 and (best_mixture_record is None or record['loss'] < best_mixture_record['loss']):
                    best_mixture_model = model
                    best_mixture_record = record
                improvement_margin = max(0.0001, 0.5 * paired_se)
                if np.isfinite(record['loss']) and record['loss'] < chosen_record['loss'] and record['loss'] < best_base_record['loss'] - improvement_margin:
                    chosen_record = record
    if best_mixture_model is not None:
        best_mixture_model.selector = best_mixture_record['selector']
        best_mixture_model.adaptive = False
        blind_record = validation_replay(best_mixture_model, scores, observed_mask, validation_model_ids, audit_target_mask, gaussian_module)
        blind_record['ablation'] = 'value_blind_panel_same_mixture'
        blind_record['blind_minus_adaptive_same_predictor'] = paired_summary([
            blind_row['mae'] - adaptive_row['mae']
            for blind_row, adaptive_row in zip(blind_record['rows'], best_mixture_record['rows'])
        ])
        records.append(blind_record)
        best_mixture_model.adaptive = True
    incumbent_selector = chosen_record['selector']
    selected_training_model = profile_models[(chosen_record['component_count'], chosen_record['regularization'])]
    selected_training_model.selector = incumbent_selector
    selector_diagnostics = {'use_quadrature': False, 'incumbent_selector': incumbent_selector}
    try:
        quadrature_record, use_quadrature = validate_quadrature_selector(
            selected_training_model, chosen_record, scores, observed_mask,
            validation_model_ids, audit_target_mask, gaussian_module,
        )
    except (AssertionError, ValueError, FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
        selector_diagnostics['fallback'] = str(error)
    else:
        records.append(quadrature_record)
        selector_diagnostics = {key: value for key, value in quadrature_record.items() if key != 'rows'}
        if use_quadrature:
            chosen_record = quadrature_record
    final_base = gaussian_module.ResidualCovariance(rank=best_base.rank, shrinkage=best_base.shrinkage, sweeps=sweeps)
    final_base.fit(scores, observed_mask)
    result = LatentMixture(final_base, chosen_record['component_count'], chosen_record['regularization'], chosen_record['selector'])
    result.incumbent_selector = incumbent_selector
    try:
        result.fit_profiles(scores, observed_mask, sweeps)
    except (ValueError, np.linalg.LinAlgError) as error:
        result = LatentMixture(final_base)
        result.validation_choice_ = {'component_count': 1, 'selector': 'variance', 'fallback': str(error)}
    else:
        result.validation_choice_ = {key: value for key, value in chosen_record.items() if key != 'rows'}
    result.validation_records_ = records
    selector_diagnostics['applied_after_refit'] = result.selector == 'quadrature'
    result.validation_selector_ = selector_diagnostics
    result.validation_split_ = {
        'train_model_ids': train_model_ids.tolist(), 'validation_model_ids': validation_model_ids.tolist(),
        'audit_target_indices': np.flatnonzero(audit_target_mask).tolist(),
        'selection_rule': 'MAE improvement over incumbent exceeding max(0.0001, 0.5 paired SE); not a significance test',
        'quadrature_selection_rule': 'same fitted predictor; mean paired row MAE delta plus one paired SE < 0; reject numerical failures',
    }
    return result
