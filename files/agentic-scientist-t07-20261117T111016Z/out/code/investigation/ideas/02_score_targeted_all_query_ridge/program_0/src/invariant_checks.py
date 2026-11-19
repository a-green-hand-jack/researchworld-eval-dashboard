"""Opt-in unit checks, deliberately not executed during candidate preparation."""

import unittest
from unittest.mock import patch

import numpy as np
import surrogate


class FrozenAuditChecks(unittest.TestCase):
    def test_audit_labels_cannot_change_frozen_predictions(self):
        means = np.linspace(0.1, 0.9, 8)
        loadings = np.column_stack((means / 3, means[::-1] / 5))
        indices = np.array([1, 4, 0, 7])
        groups = np.arange(8)
        frozen_calls = []
        original = surrogate.freeze_surrogate

        def record_freeze(*arguments):
            frozen = original(*arguments)
            frozen_calls.append(frozen.copy())
            self.assertFalse(frozen.flags.writeable)
            return frozen

        with patch.object(surrogate, 'freeze_surrogate', side_effect=record_freeze):
            first = surrogate.estimate_parts(
                means, loadings, indices, 2, np.array([1., 0., 0., 0.]), 0.25, groups)
            second = surrogate.estimate_parts(
                means, loadings, indices, 2, np.array([1., 0., 1., 1.]), 0.25, groups)
        np.testing.assert_array_equal(frozen_calls[0], frozen_calls[1])
        self.assertEqual(first[0], second[0])
        self.assertAlmostEqual(second[1] - first[1], 6 / 8)

    def test_budget_disjointness_and_replay(self):
        groups = np.arange(25)
        loadings = np.column_stack((np.linspace(-1, 1, 25), np.ones(25)))
        first = surrogate.make_design(loadings, groups, 2, 12, 101)
        replay = surrogate.make_design(loadings, groups, 2, 12, 101)
        np.testing.assert_array_equal(first, replay)
        for budget in (3, 5, 10, 12):
            selected = first[:budget]
            self.assertEqual(np.unique(selected).size, budget)
            self.assertEqual(np.intersect1d(selected[:2], selected[2:]).size, 0)

    def test_unqueried_labels_are_not_inputs(self):
        groups = np.arange(8)
        indices = np.array([0, 3, 5])
        first_target = np.zeros(8)
        second_target = first_target.copy()
        second_target[[1, 2, 4, 6, 7]] = 1
        means = np.full(8, 0.4)
        loadings = np.ones((8, 1)) / 4
        first = surrogate.estimate_parts(
            means, loadings, indices, 1, first_target[indices], 0.25, groups)
        second = surrogate.estimate_parts(
            means, loadings, indices, 1, second_target[indices], 0.25, groups)
        self.assertEqual(first, second)

    def test_exact_raw_unbiasedness_by_enumeration(self):
        means = np.array([0.2, 0.7, 0.4, 0.8, 0.3])
        loadings = np.ones((5, 1)) / 4
        target = np.array([1., 0., 1., 0., 1.])
        estimates = []
        for audit_item in range(1, 5):
            indices = np.array([0, audit_item])
            plugin, correction = surrogate.estimate_parts(
                means, loadings, indices, 1, target[indices], 0.25, np.arange(5))
            estimates.append(plugin + correction)
        self.assertAlmostEqual(np.mean(estimates), target.mean())

    def test_duplicate_group_correction_without_identical_label_assumption(self):
        groups = np.array([0, 1, 1, 2, 2, 2])
        means = np.linspace(0.1, 0.8, 6)
        target = np.array([1., 0., 1., 1., 0., 0.])
        loadings = np.ones((6, 1)) / 3
        expectation = 0.0
        for group in (1, 2):
            members = np.flatnonzero(groups == group)
            for audit_item in members:
                indices = np.array([0, audit_item])
                plugin, correction = surrogate.estimate_parts(
                    means, loadings, indices, 1, target[indices], 0.25, groups)
                expectation += (plugin + correction) / (2 * len(members))
        self.assertAlmostEqual(expectation, target.mean())
        indices = surrogate.make_design(loadings, groups, 1, 3, 211)
        self.assertEqual(np.unique(groups[indices]).size, 3)

    def test_constant_sources_and_census(self):
        for value in (0., 1.):
            matrix = np.full((4, 25), value)
            means, loadings = surrogate.fit_surrogate(matrix, np.full(4, 0.25))
            self.assertEqual(loadings.shape, (25, 0))
            groups = np.arange(25)
            indices = surrogate.make_design(loadings, groups, 2, 25, 101)
            target = np.arange(25) % 2
            plugin, correction = surrogate.estimate_parts(
                means, loadings, indices, 2, target[indices], 0.25, groups)
            self.assertAlmostEqual(plugin + correction, target.mean())

    def test_uniform_tiny_budget(self):
        values = np.array([[0., 1.], [1., 1.]])
        estimates = surrogate.uniform_predictions(values, np.array([2, 4]), np.arange(25))
        np.testing.assert_allclose(estimates, values.mean(axis=1))


if __name__ == '__main__':
    unittest.main()
