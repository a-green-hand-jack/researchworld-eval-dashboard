"""Source-tree regression checks; not run during the source-edit-only stage."""

import base64
import unittest
from unittest.mock import patch

import numpy as np

import program


class ControlStatisticsTests(unittest.TestCase):
    def make_controls(self, count, unlab_count):
        labeled_scores = np.linspace(-1.2, 1.4, count)
        unlabeled_scores = np.linspace(-1.1, 1.3, unlab_count)
        outcomes = 0.4 + 0.2 * labeled_scores + 0.1 * np.cos(3.0 * labeled_scores)
        fold_controls = []
        for fold_index, heldout_indices in enumerate(np.array_split(np.arange(count), 5)):
            slope = 0.03 * (fold_index + 1)
            heldout_prediction = slope * labeled_scores[heldout_indices] ** 2
            unlabeled_prediction = slope * unlabeled_scores ** 2
            fold_controls.append((heldout_indices, heldout_prediction, unlabeled_prediction))
        return outcomes, unlabeled_scores, fold_controls

    def test_five_unequal_offsets(self):
        offsets = np.array([-7.0, 0.0, 11.0, 2.5, -3.0])
        for count in (50, 53):
            outcomes, unlabeled_scores, template_controls = self.make_controls(count, 19)
            labeled_scores = np.linspace(-1.2, 1.4, count)
            base_controls = []
            rng = np.random.default_rng(12)
            for heldout_indices, _, _ in template_controls:
                training_indices = np.setdiff1d(np.arange(count), heldout_indices)
                control = program._select_control(
                    labeled_scores[training_indices], outcomes[training_indices],
                    count / unlabeled_scores.size, False, rng,
                )
                base_controls.append((
                    heldout_indices, control.predict(labeled_scores[heldout_indices]),
                    control.predict(unlabeled_scores),
                ))
            shifted_controls = [
                (indices, heldout + offset, unlabeled + offset)
                for (indices, heldout, unlabeled), offset in zip(base_controls, offsets)
            ]
            base_center, base_variance = program._control_statistics(
                outcomes, unlabeled_scores, base_controls,
            )
            shifted_center, shifted_variance = program._control_statistics(
                outcomes, unlabeled_scores, shifted_controls,
            )
            np.testing.assert_allclose(shifted_center, base_center, rtol=1e-10, atol=1e-10)
            np.testing.assert_allclose(shifted_variance, base_variance, rtol=1e-10, atol=1e-10)
            for bounded in (False, True):
                base_result = program._interval_from_statistics(
                    base_center, base_variance, count, 0.05, bounded,
                )
                shifted_result = program._interval_from_statistics(
                    shifted_center, shifted_variance, count, 0.05, bounded,
                )
                base_interval = np.array([base_result['lower'], base_result['upper']])
                shifted_interval = np.array([shifted_result['lower'], shifted_result['upper']])
                np.testing.assert_allclose(shifted_interval, base_interval, rtol=1e-10, atol=1e-10)

    def test_unequal_fold_formula_and_shared_pool_covariance(self):
        outcomes, unlabeled_scores, fold_controls = self.make_controls(53, 19)
        center, variance = program._control_statistics(outcomes, unlabeled_scores, fold_controls)
        expected_center = 0.0
        expected_labeled_variance = 0.0
        weights = []
        unlabeled_predictions = []
        incorrect_independent_variance = 0.0
        for indices, heldout, unlabeled in fold_controls:
            weight = indices.size / outcomes.size
            residuals = outcomes[indices] - heldout
            expected_center += weight * (residuals.mean() + unlabeled.mean())
            expected_labeled_variance += weight ** 2 * residuals.var(ddof=1) / indices.size
            incorrect_independent_variance += weight ** 2 * unlabeled.var(ddof=1) / unlabeled.size
            weights.append(weight)
            unlabeled_predictions.append(unlabeled)
        weights = np.asarray(weights)
        covariance = np.cov(np.asarray(unlabeled_predictions), ddof=1)
        expected_unlabeled_variance = weights @ covariance @ weights / unlabeled_scores.size
        np.testing.assert_allclose(center, expected_center)
        np.testing.assert_allclose(variance, expected_labeled_variance + expected_unlabeled_variance)
        self.assertGreater(expected_unlabeled_variance, incorrect_independent_variance)

    def test_zero_and_constant_controls(self):
        outcomes, unlabeled_scores, original_controls = self.make_controls(53, 19)
        zero_controls = [
            (indices, np.zeros(indices.size), np.zeros(unlabeled_scores.size))
            for indices, _, _ in original_controls
        ]
        constant_controls = [
            (indices, np.full(indices.size, 2.0), np.full(unlabeled_scores.size, 2.0))
            for indices, _, _ in original_controls
        ]
        zero_statistics = program._control_statistics(outcomes, unlabeled_scores, zero_controls)
        constant_statistics = program._control_statistics(outcomes, unlabeled_scores, constant_controls)
        np.testing.assert_allclose(zero_statistics, constant_statistics, rtol=1e-10, atol=1e-10)
        np.testing.assert_allclose(zero_statistics[0], outcomes.mean())
        expected_variance = sum(
            (indices.size / outcomes.size) ** 2 * outcomes[indices].var(ddof=1) / indices.size
            for indices, _, _ in zero_controls
        )
        np.testing.assert_allclose(zero_statistics[1], expected_variance)


class ControlFittingTests(unittest.TestCase):
    def test_finite_sample_multiplier_applied_once(self):
        scores = np.linspace(-1.0, 1.0, 24)
        outcomes = 2.0 + 3.0 * scores
        sample_ratio = 0.25
        control = program._fit_control('affine', scores, outcomes, sample_ratio, False)
        np.testing.assert_allclose(control.control_weight, 1.0 / (1.0 + sample_ratio))
        np.testing.assert_allclose(control.predict(scores), outcomes / (1.0 + sample_ratio))

    def test_degenerate_control(self):
        scores = np.ones(12)
        outcomes = np.linspace(0.0, 1.0, 12)
        for family in ('zero', 'affine', 'nonlinear'):
            control = program._fit_control(family, scores, outcomes, 1.0, True)
            np.testing.assert_array_equal(control.predict(scores), np.zeros(scores.size))

    def test_identical_inner_splits_and_refit(self):
        scores = np.arange(12, dtype=float)
        outcomes = np.sin(scores)
        calls = []

        def zero_fit(family, training_scores, training_y, sample_ratio, bounded):
            calls.append((family, training_scores.copy(), training_y.copy()))
            return program.FittedControl()

        with patch.object(program, '_fit_control', side_effect=zero_fit):
            selected = program._select_control(scores, outcomes, 0.5, False, np.random.default_rng(9))
        self.assertEqual(len(calls), 10)
        self.assertEqual(calls[-1][0], 'zero')
        np.testing.assert_array_equal(calls[-1][1], scores)
        np.testing.assert_array_equal(calls[-1][2], outcomes)
        for fold_index in range(3):
            for family_index in (1, 2):
                np.testing.assert_array_equal(calls[fold_index][1], calls[3 * family_index + fold_index][1])
                np.testing.assert_array_equal(calls[fold_index][2], calls[3 * family_index + fold_index][2])
        np.testing.assert_array_equal(selected.predict(scores), np.zeros(scores.size))

    def test_outer_training_boundary(self):
        scores = np.arange(23, dtype=float)
        outcomes = 0.2 * scores + np.cos(scores)
        unlabeled_scores = np.arange(100, 117, dtype=float)
        seed = 42
        expected_folds = np.array_split(np.random.default_rng(seed).permutation(scores.size), 5)
        calls = []

        def record_selection(training_scores, training_y, sample_ratio, bounded, rng):
            calls.append((training_scores.copy(), training_y.copy(), sample_ratio))
            return program.FittedControl()

        with patch.object(program, '_select_control', side_effect=record_selection):
            program._crossfit_controls(outcomes, scores, unlabeled_scores, 0.05, False,
                                       np.random.default_rng(seed))
        self.assertEqual(len(calls), 5)
        for heldout_indices, (training_scores, training_y, sample_ratio) in zip(expected_folds, calls):
            training_indices = np.setdiff1d(np.arange(scores.size), heldout_indices)
            np.testing.assert_array_equal(training_scores, scores[training_indices])
            np.testing.assert_array_equal(training_y, outcomes[training_indices])
            self.assertEqual(sample_ratio, outcomes.size / unlabeled_scores.size)


class RpcTests(unittest.TestCase):
    def episode(self, outcomes, scores, unlabeled_scores, kind, seed=19):
        self.assertEqual(program.handle({'op': 'reset', 'seed': seed}), {'ok': True})
        values = np.concatenate([outcomes, scores, unlabeled_scores]).astype('<f8')
        payload = values.tobytes()
        start = program.handle({
            'op': 'update', 'phase': 'start', 'n': outcomes.size, 'N': unlabeled_scores.size,
            'alpha': 0.05, 'label_kind': kind, 'dtype': '<f8', 'encoding': 'base64',
            'shape': [values.size], 'total_bytes': len(payload), 'chunks': 1,
        })
        self.assertEqual(set(start), {'ok', 'transfer_id'})
        self.assertEqual(program.handle({
            'op': 'update', 'phase': 'chunk', 'transfer_id': start['transfer_id'],
            'index': 0, 'data': base64.b64encode(payload).decode('ascii'),
        }), {'ok': True})
        self.assertEqual(program.handle({
            'op': 'update', 'phase': 'commit', 'transfer_id': start['transfer_id'],
        }), {'ok': True})
        interval = program.handle({'op': 'infer'})
        self.assertEqual(set(interval), {'lower', 'upper'})
        self.assertEqual(interval, program.handle({'op': 'infer'}))
        self.assertTrue(all(type(value) is float and np.isfinite(value) for value in interval.values()))
        self.assertTrue(np.isfinite(interval['upper'] - interval['lower']))
        self.assertLessEqual(interval['lower'], interval['upper'])
        if kind == 'bernoulli':
            self.assertGreaterEqual(interval['lower'], 0.0)
            self.assertLessEqual(interval['upper'], 1.0)
        return interval

    def test_small_samples_constant_scores_and_replay(self):
        for count in (8, 9, 23):
            scores = np.linspace(-1.0, 1.0, count)
            unlabeled_scores = np.linspace(-1.3, 1.2, 17)
            for kind in ('real', 'bernoulli'):
                outcomes = np.sin(scores) if kind == 'real' else (scores > 0.0).astype(float)
                first = self.episode(outcomes, scores, unlabeled_scores, kind, 2**63 - 1)
                replay = self.episode(outcomes, scores, unlabeled_scores, kind, 2**63 - 1)
                self.assertEqual(first, replay)
                for constant_labeled in (False, True):
                    fallback_scores = np.ones(count) if constant_labeled else scores
                    fallback_unlabeled = unlabeled_scores if constant_labeled else np.ones(17)
                    fallback = self.episode(outcomes, fallback_scores, fallback_unlabeled, kind)
                    self.assertEqual(fallback, program._label_only(outcomes, kind, 0.05))

    def test_invalid_transition(self):
        program.handle({'op': 'reset', 'seed': 0})
        with self.assertRaises(ValueError):
            program.handle({'op': 'infer'})


if __name__ == '__main__':
    unittest.main()
