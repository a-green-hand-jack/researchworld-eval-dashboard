"""Historical-only missing-data factor analysis and target-risk selection.

Scores are standardized using observed training entries only. Zero-filled SVD
is an initializer, not a covariance estimate: every subsequent EM sufficient
statistic integrates missing scores through the latent posterior. Residuals
represent task-specific model variation, not additional measurement noise.
"""

import numpy as np


class ResidualCovariance:
    def __init__(self, rank=4, shrinkage=8.0, sweeps=30):
        self.rank = rank
        self.shrinkage = shrinkage
        self.sweeps = sweeps

    def fit(self, scores, observed_mask):
        observed_mask = np.asarray(observed_mask, dtype=bool)
        scores = np.asarray(scores, dtype=np.float64)
        rows, columns = scores.shape
        counts = observed_mask.sum(axis=0)
        offset = np.divide(
            np.where(observed_mask, scores, 0.0).sum(axis=0), counts,
            out=np.full(columns, 0.5), where=counts > 0,
        )
        centered = np.where(observed_mask, scores - offset, 0.0)
        variance = np.divide(
            (centered ** 2).sum(axis=0), counts,
            out=np.full(columns, 0.01), where=counts > 0,
        )
        scale = np.sqrt(np.maximum(variance, 0.0004))
        standardized = np.where(observed_mask, (scores - offset) / scale, 0.0)
        rank = max(1, min(self.rank, columns, max(1, rows - 1)))
        _, singular_values, right_vectors = np.linalg.svd(standardized, full_matrices=False)
        loadings = right_vectors[:rank].T * (singular_values[:rank] / np.sqrt(max(rows, 1)))
        residual = np.full(columns, 0.5)
        location = np.zeros(columns)
        identity = np.eye(rank)
        for _ in range(self.sweeps):
            precision = identity[None, :, :] + np.einsum(
                'mn,nr,ns->mrs', observed_mask, loadings / residual[:, None], loadings,
                optimize=True,
            )
            posterior_covariance = np.linalg.solve(
                precision, np.broadcast_to(identity, (rows, rank, rank)),
            )
            latent_rhs = np.where(observed_mask, standardized - location, 0.0) @ (loadings / residual[:, None])
            posterior_mean = np.einsum('mrs,ms->mr', posterior_covariance, latent_rhs)
            second_moment = posterior_covariance + np.einsum('mr,ms->mrs', posterior_mean, posterior_mean)
            augmented_mean = np.column_stack((np.ones(rows), posterior_mean))
            for task in range(columns):
                eligible = observed_mask[:, task]
                count = int(counts[task])
                if count == 0:
                    loadings[task] = 0.0
                    residual[task] = 1.0
                    continue
                sufficient = np.empty((rank + 1, rank + 1))
                sufficient[0, 0] = count
                sufficient[0, 1:] = posterior_mean[eligible].sum(axis=0)
                sufficient[1:, 0] = sufficient[0, 1:]
                sufficient[1:, 1:] = second_moment[eligible].sum(axis=0)
                response = standardized[eligible, task]
                cross = augmented_mean[eligible].T @ response
                regularizer = np.eye(rank + 1) * (1e-6 * max(count, 1))
                parameters = np.linalg.solve(sufficient + regularizer, cross)
                expected_error = float(response @ response - 2.0 * parameters @ cross + parameters @ sufficient @ parameters)
                location[task] = parameters[0]
                loadings[task] = parameters[1:]
                residual[task] = max(
                    0.015,
                    (max(expected_error, 0.0) + self.shrinkage * 0.2) / (count + self.shrinkage),
                )
        self.mean_ = offset + scale * location
        self.loadings_ = scale[:, None] * loadings
        self.residual_variance_ = np.maximum(scale ** 2 * residual, 1e-10)
        self.covariance_ = self.loadings_ @ self.loadings_.T + np.diag(self.residual_variance_)
        return self


def condition(covariance_model, observed_indices, observed_scores):
    train_mean = covariance_model.mean_
    target_indices = np.arange(len(train_mean))
    observed_indices = np.asarray(observed_indices, dtype=int)
    observed_scores = np.asarray(observed_scores, dtype=np.float64)
    if not len(observed_indices):
        return np.clip(train_mean.copy(), 0.0, 1.0)
    cross_covariance = covariance_model.covariance_[np.ix_(target_indices, observed_indices)]
    observed_covariance = covariance_model.covariance_[np.ix_(observed_indices, observed_indices)].copy()
    observed_covariance += np.eye(len(observed_indices)) * 1e-12
    conditional_mean = train_mean[target_indices] + cross_covariance @ np.linalg.solve(observed_covariance, observed_scores - train_mean[observed_indices])
    conditional_mean[observed_indices] = observed_scores
    return np.clip(conditional_mean, 0.0, 1.0)


def transfer_select(conditional_covariance, available, observed):
    candidate_indices = np.asarray(sorted(set(available) - set(observed)), dtype=int)
    transfer_covariance = conditional_covariance[np.ix_(candidate_indices, candidate_indices)].copy()
    candidate_variance = np.maximum(np.diag(transfer_covariance).copy(), 1e-12)
    target_weights = np.ones(len(candidate_indices))
    np.fill_diagonal(transfer_covariance, 0.0)
    transfer_gain = np.sum(target_weights[:, None] * transfer_covariance ** 2, axis=0) / candidate_variance
    unavailable_targets = np.asarray(sorted(set(range(len(conditional_covariance))) - set(available) - set(observed)), dtype=int)
    if len(unavailable_targets):
        target_covariance = conditional_covariance[np.ix_(unavailable_targets, candidate_indices)]
        transfer_gain += np.sum(target_covariance ** 2, axis=0) / candidate_variance
    chosen_index = candidate_indices[int(np.argmax(transfer_gain))]
    return int(chosen_index)


def reveal_covariance(conditional_covariance, chosen_index):
    selected_covariance = conditional_covariance[:, chosen_index].copy()
    selected_variance = max(float(conditional_covariance[chosen_index, chosen_index]), 1e-12)
    conditional_covariance -= np.outer(selected_covariance, selected_covariance) / selected_variance
    conditional_covariance[chosen_index, :] = 0.0
    conditional_covariance[:, chosen_index] = 0.0


def tune_fit(scores, observed_mask, seed, sweeps):
    """Tune on held-out historical models, then refit on all uploaded models.

    This split is internal validation, not the harness's outer test split.
    Validation target folds are fixed across configurations and cannot be
    probed. Neither target values nor target masks enter a model fit.
    """
    rng = np.random.default_rng(seed)
    rows, columns = scores.shape
    if rows < 8 or columns < 2:
        covariance_model = ResidualCovariance(rank=2, shrinkage=8.0, sweeps=sweeps)
        train_scores, train_observed_mask = scores, observed_mask
        covariance_model.fit(train_scores, train_observed_mask)
        return covariance_model
    permutation = rng.permutation(rows)
    validation_count = min(32, max(2, rows // 5))
    validation_model_ids = permutation[:validation_count]
    train_model_ids = permutation[validation_count:]
    assert set(train_model_ids).isdisjoint(validation_model_ids)
    train_scores = scores[train_model_ids]
    train_observed_mask = observed_mask[train_model_ids]
    audit_target_mask = np.zeros(columns, dtype=bool)
    audit_target_mask[rng.permutation(columns)[:max(1, columns // 3)]] = True
    best = None
    for rank in (2, 4, 8):
        if rank > max(2, min(len(train_model_ids) - 1, columns)):
            continue
        for shrinkage in (2.0, 12.0):
            covariance_model = ResidualCovariance(rank=rank, shrinkage=shrinkage, sweeps=min(sweeps, 12))
            covariance_model.fit(train_scores, train_observed_mask)
            errors = []
            for model_id in validation_model_ids:
                validation_observed_mask = observed_mask[model_id]
                fixed_target_mask = validation_observed_mask & audit_target_mask
                available = np.flatnonzero(validation_observed_mask & ~audit_target_mask).tolist()
                if not available or not np.any(fixed_target_mask):
                    continue
                observed = []
                values = []
                queried_mask = np.zeros(columns, dtype=bool)
                conditional_covariance = covariance_model.covariance_.copy()
                budget = min(8, len(available))
                row_errors = []
                for count in range(1, budget + 1):
                    chosen_index = transfer_select(conditional_covariance, available, observed)
                    observed.append(chosen_index)
                    values.append(float(scores[model_id, chosen_index]))
                    queried_mask[chosen_index] = True
                    assert not np.any(queried_mask & audit_target_mask)
                    reveal_covariance(conditional_covariance, chosen_index)
                    if count in (1, 2, 4, 8) or count == budget:
                        prediction = condition(covariance_model, observed, values)
                        row_errors.append(float(np.mean(np.abs(prediction[fixed_target_mask] - scores[model_id, fixed_target_mask]))))
                errors.append(float(np.mean(row_errors)))
            loss = float(np.mean(errors)) if errors else float('inf')
            configuration = (loss, rank, shrinkage)
            if best is None or configuration < best:
                best = configuration
    _, rank, shrinkage = best
    covariance_model = ResidualCovariance(rank=rank, shrinkage=shrinkage, sweeps=sweeps)
    covariance_model.fit(scores, observed_mask)
    return covariance_model
