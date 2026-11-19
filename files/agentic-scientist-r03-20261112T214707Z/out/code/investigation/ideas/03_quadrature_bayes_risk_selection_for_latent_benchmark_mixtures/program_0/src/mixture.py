"""Historical-only latent mixtures and moment-matched L1 transfer selection."""

import math

import numpy as np


_ERFC = np.vectorize(math.erfc, otypes=[np.float64])


def normal_cdf(values):
    return 0.5 * _ERFC(-np.asarray(values, dtype=np.float64) / math.sqrt(2.0))


class LatentMixture:
    def __init__(self, base, component_count=1, regularization=2.0,
                 selector='variance', prediction_kind='median', adaptive=True):
        self.base = base
        self.mean_ = base.mean_.copy()
        self.component_count = component_count
        self.regularization = regularization
        self.selector = selector
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
        chosen_index = candidate_indices[int(np.argmax(absolute_gain.sum(axis=0)))]
        return int(chosen_index)

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
            lower_bound = np.zeros(component_mean.shape[1])
            upper_bound = np.ones(component_mean.shape[1])
            for _ in range(25):
                midpoint = (lower_bound + upper_bound) * 0.5
                posterior_cdf = np.sum(component_weight[:, None] * normal_cdf((midpoint[None, :] - component_mean) / conditional_std[None, :]), axis=0)
                lower_bound = np.where(posterior_cdf < 0.5, midpoint, lower_bound)
                upper_bound = np.where(posterior_cdf >= 0.5, midpoint, upper_bound)
            prediction = np.clip((lower_bound + upper_bound) * 0.5, 0.0, 1.0)
        prediction[self.observed] = self.values
        return prediction


def validation_replay(model, scores, observed_mask, validation_model_ids,
                      audit_target_mask, gaussian_module):
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
        })
    row_losses = np.asarray([record['mae'] for record in records])
    return {
        'component_count': model.component_count, 'rank': model.base.rank,
        'shrinkage': model.base.shrinkage, 'regularization': model.regularization,
        'selector': model.selector, 'adaptive': model.adaptive,
        'prediction_kind': model.prediction_kind, 'rows': records,
        'loss': float(row_losses.mean()) if len(row_losses) else float('inf'),
    }


def paired_summary(differences):
    differences = np.asarray(differences, dtype=np.float64)
    standard_error = float(np.std(differences, ddof=1) / np.sqrt(len(differences)))
    return {'paired_delta': float(differences.mean()),
            'paired_standard_error': standard_error, 'row_count': len(differences)}


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
    assert set(train_model_ids).isdisjoint(validation_model_ids)
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
    for component_count in (1, 2, 4):
        for regularization in ((2.0,) if component_count == 1 else (2.0, 8.0)):
            model = LatentMixture(best_base, component_count, regularization)
            try:
                model.fit_profiles(train_scores, train_observed_mask, sweeps)
            except (ValueError, np.linalg.LinAlgError) as error:
                records.append({'component_count': component_count, 'regularization': regularization,
                                'skipped': str(error)})
                continue
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
    final_base = gaussian_module.ResidualCovariance(rank=best_base.rank, shrinkage=best_base.shrinkage, sweeps=sweeps)
    final_base.fit(scores, observed_mask)
    result = LatentMixture(final_base, chosen_record['component_count'], chosen_record['regularization'], chosen_record['selector'])
    try:
        result.fit_profiles(scores, observed_mask, sweeps)
    except (ValueError, np.linalg.LinAlgError) as error:
        result = LatentMixture(final_base)
        result.validation_choice_ = {'component_count': 1, 'selector': 'variance', 'fallback': str(error)}
    else:
        result.validation_choice_ = {key: value for key, value in chosen_record.items() if key != 'rows'}
    result.validation_records_ = records
    result.validation_split_ = {
        'train_model_ids': train_model_ids.tolist(), 'validation_model_ids': validation_model_ids.tolist(),
        'audit_target_indices': np.flatnonzero(audit_target_mask).tolist(),
        'selection_rule': 'MAE improvement over incumbent exceeding max(0.0001, 0.5 paired SE); not a significance test',
    }
    return result
