"""Exact interventional Shapley values of the uploaded empirical forest game."""

import math

import numpy as np


def compile_leaf_constraints(tree, dimension):
    """Intersect repeated splits into lower-exclusive, upper-inclusive bounds."""
    leaves = []
    stack = [(0, np.full(dimension, -np.inf), np.full(dimension, np.inf), ())]
    while stack:
        node, lower_bounds, upper_bounds, used = stack.pop()
        if tree['left'][node] < 0:
            used_features = np.asarray(sorted(used), dtype=np.int64)
            leaves.append((used_features, lower_bounds[used_features],
                           upper_bounds[used_features], float(tree['probability'][node])))
            continue
        feature = int(tree['feature'][node])
        threshold = float(tree['threshold'][node])
        next_used = used if feature in used else used + (feature,)
        left_upper = upper_bounds.copy()
        left_upper[feature] = min(left_upper[feature], threshold)
        if lower_bounds[feature] < left_upper[feature]:
            stack.append((int(tree['left'][node]), lower_bounds, left_upper, next_used))
        right_lower = lower_bounds.copy()
        right_lower[feature] = max(right_lower[feature], threshold)
        if right_lower[feature] < upper_bounds[feature]:
            stack.append((int(tree['right'][node]), right_lower, upper_bounds, next_used))
    return leaves


def literal_beta_tables(dimension):
    """Integrate each required positive or negative literal's marginal."""
    positive_beta = np.zeros((dimension + 1, dimension + 1), dtype=np.float64)
    negative_beta = np.zeros_like(positive_beta)
    for positive_count in range(dimension + 1):
        for negative_count in range(dimension + 1 - positive_count):
            if positive_count:
                positive_beta[positive_count, negative_count] = 1.0 / (positive_count * math.comb(positive_count + negative_count, positive_count))
            if negative_count:
                negative_beta[positive_count, negative_count] = 1.0 / (negative_count * math.comb(positive_count + negative_count, positive_count))
    return positive_beta, negative_beta


def exact_forest_shapley(model, query):
    """Sum leaf-literal games without sampling or enumerating coalitions.

    Each background row defines a game by choosing query or background values
    independently for each original feature group. A leaf is a conjunction of
    required inclusions and exclusions; both-pass features are dummy players.
    Average these exact games over every supplied row and tree. Compilation and
    all intermediates are local to this call; no query or coalition cache lives
    across calls. Float32 overflow to negative infinity also preserves traversal
    semantics when a path has no lower constraint.
    """
    query_values = np.asarray(query, dtype=np.float32)
    background_values = np.asarray(model['background'], dtype=np.float32)
    dimension = model['dimension']
    positive_beta, negative_beta = literal_beta_tables(dimension)
    forest_phi = np.zeros(dimension, dtype=np.float64)
    for tree in model['parameters']['trees']:
        tree_phi = np.zeros(dimension, dtype=np.float64)
        leaves = compile_leaf_constraints(tree, dimension)
        for used_features, lower_bounds, upper_bounds, leaf_probability in leaves:
            if not len(used_features):
                continue
            query_pass = (query_values[used_features] > lower_bounds) & (query_values[used_features] <= upper_bounds)
            background_pass = (background_values[:, used_features] > lower_bounds) & (background_values[:, used_features] <= upper_bounds)
            query_pass |= np.isneginf(lower_bounds) & (query_values[used_features] <= upper_bounds)
            background_pass |= np.isneginf(lower_bounds) & (background_values[:, used_features] <= upper_bounds)
            positive_required = query_pass[None, :] & ~background_pass
            negative_required = ~query_pass[None, :] & background_pass
            viable_rows = np.all(query_pass[None, :] | background_pass, axis=1)
            positive_counts = positive_required.sum(axis=1)
            negative_counts = negative_required.sum(axis=1)
            leaf_delta = positive_required * positive_beta[positive_counts, negative_counts][:, None] - negative_required * negative_beta[positive_counts, negative_counts][:, None]
            leaf_delta[~viable_rows] = 0.0
            tree_phi[used_features] += leaf_probability * leaf_delta.mean(axis=0)
        forest_phi += tree_phi
    return forest_phi / len(model['parameters']['trees'])
