"""Independent small-game checks, runnable only in a later authorized stage.

Run from the candidate directory with: python src/validate_forest.py
These routines are not called by the RPC and were not run during preparation.
"""

import itertools
import math

import numpy as np

from forest import exact_forest_shapley
from program import predict
from reliability import explain_fixed_game


def independent_forest_value(model, rows):
    """Scalar traversal independent of both leaf algebra and vector predictor."""
    predictions = []
    for row in rows:
        rounded = np.asarray(row, dtype=np.float32).astype(np.float64)
        total = 0.0
        for tree in model['parameters']['trees']:
            node = 0
            while tree['left'][node] >= 0:
                feature = tree['feature'][node]
                node = tree['left'][node] if rounded[feature] <= tree['threshold'][node] else tree['right'][node]
            total += tree['probability'][node]
        predictions.append(total / len(model['parameters']['trees']))
    return np.asarray(predictions, dtype=np.float64)


def independently_exhaustive_shapley(model, query):
    """Enumerate coalition games and average all permutation marginals."""
    dimension = model['dimension']
    background = np.asarray(model['background'], dtype=np.float64)
    coalition_values = np.empty(1 << dimension, dtype=np.float64)
    for mask in range(1 << dimension):
        hybrid = background.copy()
        for feature in range(dimension):
            if mask & (1 << feature):
                hybrid[:, feature] = query[feature]
        coalition_values[mask] = independent_forest_value(model, hybrid).mean()
    estimate = np.zeros(dimension, dtype=np.float64)
    for permutation in itertools.permutations(range(dimension)):
        mask = 0
        for feature in permutation:
            next_mask = mask | (1 << feature)
            estimate[feature] += coalition_values[next_mask] - coalition_values[mask]
            mask = next_mask
    estimate /= math.factorial(dimension)
    return estimate, coalition_values[-1] - coalition_values[0]


def validation_fixtures():
    repeated_tree = {
        'left': [1, 2, -1, 4, -1, -1, 7, -1, -1],
        'right': [6, 3, -1, 5, -1, -1, 8, -1, -1],
        'feature': [0, 0, -2, 1, -2, -2, 0, -2, -2],
        'threshold': [0.0, -1.0, -2.0, 0.5, -2.0, -2.0, -0.5, -2.0, -2.0],
        'probability': [0.0, 0.0, 0.1, 0.0, 0.35, 0.8, 0.0, 0.99, 0.9],
    }
    boundary_tree = {
        'left': [1, -1, 3, -1, -1],
        'right': [2, -1, 4, -1, -1],
        'feature': [2, -2, 1, -2, -2],
        'threshold': [0.1, -2.0, 0.5, -2.0, -2.0],
        'probability': [0.0, 0.2, 0.0, 0.7, 0.95],
    }
    constant_tree = {
        'left': [-1], 'right': [-1], 'feature': [-2],
        'threshold': [-2.0], 'probability': [0.37],
    }
    mixed_tree = {
        'left': [1, 2, 3, -1, -1, -1, -1],
        'right': [6, 5, 4, -1, -1, -1, -1],
        'feature': [0, 1, 2, -2, -2, -2, -2],
        'threshold': [0.0, 0.0, 0.0, -2.0, -2.0, -2.0, -2.0],
        'probability': [0.0, 0.0, 0.0, 0.85, 0.1, 0.2, 0.3],
    }
    background = [[-2.0, 0.0, 0.1], [-1.0, 0.5, -0.5],
                  [0.0, 1.0, 0.0], [0.25, -1.0, 0.3]]
    queries = [[-1.0, 0.5, 0.1], [0.0, 0.5, 0.0],
               [0.25, -1.0, 0.3], [-0.25, 0.75, -0.5],
               [0.5, -0.5, 0.5],
               [np.nextafter(0.0, 1.0), np.nextafter(0.5, 1.0),
                np.nextafter(0.1, -np.inf)],
               [-1e100, 0.5, 0.1], [1e100, 0.5, 0.1]]
    for trees in ([constant_tree], [repeated_tree], [boundary_tree], [mixed_tree],
                  [repeated_tree, boundary_tree, constant_tree, mixed_tree]):
        for rows in (background, background[:1], [background[2]] * 3):
            model = {'kind': 'forest', 'dimension': 3, 'background': rows,
                     'parameters': {'trees': trees}}
            for query in queries:
                yield model, np.asarray(query, dtype=np.float64)
            for row in rows:
                identical = dict(model, background=[row, row])
                yield identical, np.asarray(row, dtype=np.float64)


def validate_exact_forest():
    for model, query in validation_fixtures():
        exhaustive_estimate, endpoint_difference = independently_exhaustive_shapley(model, query)
        tree_estimate = exact_forest_shapley(model, query)
        assert np.allclose(tree_estimate, exhaustive_estimate, atol=1e-10, rtol=1e-10)
        assert np.isclose(tree_estimate.sum(), endpoint_difference, atol=1e-10, rtol=1e-10)
        assert np.allclose(predict(model, [query]), independent_forest_value(model, [query]), atol=1e-15, rtol=1e-15)
        background = np.asarray(model['background'], dtype=np.float64)
        assert np.allclose(predict(model, background), independent_forest_value(model, background), atol=1e-15, rtol=1e-15)
        rng = np.random.default_rng(1729)
        first_repeat = explain_fixed_game(model, query, 1, rng, predict)
        second_repeat = explain_fixed_game(model, query, 1, rng, predict)
        assert np.array_equal(first_repeat, second_repeat)
        assert np.array_equal(first_repeat, tree_estimate)
        for budget in (2, 6, 8192):
            assert np.array_equal(explain_fixed_game(model, query, budget, rng, predict), tree_estimate)
        replay_rng = np.random.default_rng(1729)
        assert np.array_equal(rng.random(8), replay_rng.random(8))
        if np.all(background == query):
            assert np.array_equal(tree_estimate, np.zeros(model['dimension']))


if __name__ == '__main__':
    validate_exact_forest()
