"""Fixed empirical-background estimation; diagnostics never extend RPC responses."""

import math

import numpy as np

from forest import exact_forest_shapley


class FrozenProbabilityGame:
    """Mask original supplied columns, without refitting or resampling background.

    The transport already applies frozen scalar preprocessing. It supplies no
    raw dataframe or pipeline; no claim about unobserved preprocessing is made.
    The cache is query-local, and contains only predictions requested here.
    """

    def __init__(self, model, query, predict):
        self.model = model
        self.query = np.array(query, dtype=np.float64, copy=True)
        self.background = np.array(model['background'], dtype=np.float64, copy=True)
        self.predict = predict
        self.dimension = model['dimension']
        self.cache = {}
        self.prediction_rows = 0
        self.unique_coalitions = 0

    def values(self, coalition_masks):
        coalition_masks = np.asarray(coalition_masks, dtype=np.uint32)
        missing = sorted(set(map(int, coalition_masks)) - self.cache.keys())
        for offset in range(0, len(missing), 128):
            chunk = np.asarray(missing[offset:offset + 128], dtype=np.uint32)
            included = ((chunk[:, None] >> np.arange(self.dimension)) & 1).astype(bool)
            hybrid = np.where(included[:, None, :], self.query, self.background[None, :, :])
            predictions = self.predict(self.model, hybrid.reshape(-1, self.dimension))
            means = predictions.reshape(len(chunk), len(self.background)).mean(axis=1)
            for mask, mean in zip(chunk, means):
                self.cache[int(mask)] = float(mean)
            self.prediction_rows += len(chunk) * len(self.background)
            self.unique_coalitions += len(chunk)
        return np.asarray([self.cache[int(mask)] for mask in coalition_masks])


def exact_shapley(game):
    """Exhaustive fixed-game solution, used only when the budget covers it.

    This is not an independent experimental reference for a deployment call.
    It neither supplies a table to a sampled call nor reuses another call's cache.
    """
    feature_count = game.dimension
    coalition_values = game.values(np.arange(1 << feature_count, dtype=np.uint32))
    reference_phi = np.zeros(feature_count)
    for coalition_mask in range(1 << feature_count):
        coalition_size = coalition_mask.bit_count()
        if coalition_size == feature_count:
            continue
        coalition_weight = 1.0 / (feature_count * math.comb(feature_count - 1, coalition_size))
        for feature_index in range(feature_count):
            if not coalition_mask & (1 << feature_index):
                reference_phi[feature_index] += coalition_weight * (coalition_values[coalition_mask | (1 << feature_index)] - coalition_values[coalition_mask])
    assert np.isclose(reference_phi.sum(), coalition_values[-1] - coalition_values[0], atol=1e-8)
    return reference_phi


def independent_paths(game, path_count, rng):
    """Complete uniform paths; no antithetic paths or adaptive stopping.

    Reusing a deterministic coalition value does not couple the independently
    sampled permutations. Each row, not each marginal, is a sampling unit.
    """
    feature_count = game.dimension
    permutations = np.asarray([rng.permutation(feature_count) for _ in range(path_count)])
    prefixes = np.bitwise_or.accumulate(np.left_shift(np.uint32(1), permutations.astype(np.uint32)), axis=1)
    masks = prefixes[:, :-1].reshape(-1)
    endpoints = game.values([0, (1 << feature_count) - 1])
    path_values = np.empty((path_count, feature_count + 1))
    path_values[:, 0] = endpoints[0]
    path_values[:, -1] = endpoints[1]
    path_values[:, 1:-1] = game.values(masks).reshape(path_count, feature_count - 1)
    path_marginals = np.empty((path_count, feature_count))
    np.put_along_axis(path_marginals, permutations, np.diff(path_values, axis=1), axis=1)
    if not np.all(np.abs(path_marginals) <= 1.0 + 1e-12):
        raise ValueError('probability marginal outside its bounded domain')
    if not np.allclose(path_marginals.sum(axis=1), endpoints[1] - endpoints[0], atol=1e-10, rtol=0):
        raise ValueError('incomplete permutation path')
    return path_marginals, masks


def simultaneous_certificate(path_marginals, alpha=0.05):
    """At most alpha unconditional wrong-certificate probability per fixed call.

    The bound is on independent complete-path means, never regression estimates.
    It is not a conditional-on-acceptance guarantee. Strict separation rejects
    ties, with original column order breaking estimate ties deterministically.
    """
    path_count, feature_count = path_marginals.shape
    if path_count < 2 or not 0 < alpha < 1:
        raise ValueError('certificate requires two paths and valid alpha')
    estimate = path_marginals.mean(axis=0)
    sample_variance = path_marginals.var(axis=0, ddof=1)
    log_term = np.log(4.0 * feature_count / alpha)
    radius = np.sqrt(2.0 * sample_variance * log_term / path_count) + 14.0 * log_term / (3.0 * (path_count - 1))
    magnitude_lower = np.maximum(0.0, np.abs(estimate) - radius)
    magnitude_upper = np.abs(estimate) + radius
    order = np.argsort(-np.abs(estimate), kind='stable')
    selected = order[:min(3, feature_count - 1)]
    excluded = order[min(3, feature_count - 1):]
    topk_certified = bool(magnitude_lower[selected].min() > magnitude_upper[excluded].max())
    signs_certified = bool(np.all(np.abs(estimate[selected]) > radius[selected]))
    certified = topk_certified and signs_certified
    return estimate, radius, certified


def sampled_kernel_masks(feature_count, count, rng):
    """Kernel-distributed subsets with complement pairing only for regression."""
    sizes = np.arange(1, feature_count)
    probabilities = 1.0 / (sizes * (feature_count - sizes))
    probabilities /= probabilities.sum()
    masks = np.empty(count, dtype=np.uint32)
    full = (1 << feature_count) - 1
    for offset in range(0, count, 2):
        size = int(rng.choice(sizes, p=probabilities))
        selected = rng.choice(feature_count, size=size, replace=False)
        mask = sum(1 << int(feature) for feature in selected)
        masks[offset] = mask
        if offset + 1 < count:
            masks[offset + 1] = full ^ mask
    return masks


def kernel_regression(game, masks, path_mask_count):
    """Importance-weight the path/kernel mixture for the SHAP kernel objective.

    Path prefixes are uniform conditional on size, but not kernel-distributed
    across sizes. Their dependence is irrelevant to the point regression; no
    certificate is constructed from these fitted coefficients.
    """
    feature_count = game.dimension
    design = ((masks[:, None] >> np.arange(feature_count)) & 1).astype(float)
    sizes = design.sum(axis=1).astype(int)
    possible_sizes = np.arange(1, feature_count)
    size_probabilities = 1.0 / (possible_sizes * (feature_count - possible_sizes))
    size_probabilities /= size_probabilities.sum()
    kernel_probability = size_probabilities[sizes - 1]
    path_fraction = path_mask_count / len(masks)
    mixture_probability = path_fraction / (feature_count - 1) + (1.0 - path_fraction) * kernel_probability
    root_weights = np.sqrt(kernel_probability / mixture_probability)
    empty, full = game.values([0, (1 << feature_count) - 1])
    delta = full - empty
    target = game.values(masks) - empty - sizes * delta / feature_count
    basis = np.zeros((feature_count, feature_count - 1))
    for column in range(feature_count - 1):
        scale = math.sqrt((column + 1) * (column + 2))
        basis[:column + 1, column] = 1.0 / scale
        basis[column + 1, column] = -(column + 1) / scale
    coefficients = np.linalg.lstsq((design @ basis) * root_weights[:, None], target * root_weights, rcond=1e-12)[0]
    estimate = np.full(feature_count, delta / feature_count) + basis @ coefficients
    estimate += (delta - estimate.sum()) / feature_count
    return estimate


def explain_fixed_game(model, query, budget, rng, predict):
    """Spend at most the requested nontrivial-coalition sampling budget.

    One quarter of a nonexhaustive budget is reserved for a fixed number of
    independent paths when two paths fit. All sampled masks also enter the
    probability-scale Kernel SHAP point estimate. Return the path mean only
    when its signed top-k certificate passes; otherwise retain regression.
    Certificate decisions and costs are internal, not extra RPC fields.
    """
    if model['kind'] == 'forest':
        return exact_forest_shapley(model, query)
    game = FrozenProbabilityGame(model, query, predict)
    feature_count = game.dimension
    if model['kind'] == 'affine':
        return np.asarray(model['parameters']['coef']) * (game.query - game.background.mean(axis=0))
    if budget >= (1 << feature_count) - 2:
        return exact_shapley(game)
    path_count = budget // (4 * (feature_count - 1))
    path_masks = np.empty(0, dtype=np.uint32)
    path_estimate = None
    certified = False
    if path_count >= 2:
        path_marginals, path_masks = independent_paths(game, path_count, rng)
        path_estimate, radius, certified = simultaneous_certificate(path_marginals)
    remaining = budget - len(path_masks)
    kernel_masks = sampled_kernel_masks(feature_count, remaining, rng)
    masks = np.concatenate((path_masks, kernel_masks))
    if certified:
        return path_estimate
    return kernel_regression(game, masks, len(path_masks))
