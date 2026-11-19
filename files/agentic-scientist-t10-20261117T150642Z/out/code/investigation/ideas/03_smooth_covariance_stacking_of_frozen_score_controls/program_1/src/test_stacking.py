"""Source-only regression tests for the live covariance stack; not run in staging."""

import base64
import unittest
from unittest import mock

import numpy as np

import program


class IdentityBase:
    def __init__(self, bounded):
        self.bounded = bounded

    def fit(self, scores, outcomes):
        return self

    def predict(self, scores):
        return np.asarray(scores, dtype=float)


class ZeroBase(IdentityBase):
    def predict(self, scores):
        return np.zeros(scores.size)


class ReverseBase(IdentityBase):
    def predict(self, scores):
        return 1.0 - scores


class CovarianceStackTests(unittest.TestCase):
    def setUp(self):
        self.scores = np.linspace(-1.0, 1.0, 39)
        self.outcomes = 0.4 * self.scores + 0.2 * self.scores ** 2

    def test_live_normal_equations_and_single_finite_n_penalty(self):
        captured = []
        original_moments = program._stack_moments

        def capture_moments(batches):
            moments = original_moments(batches)
            captured.append(moments)
            return moments

        sample_ratio = 2.5
        with mock.patch.object(program, '_stack_moments', side_effect=capture_moments), mock.patch.object(
            program, '_fit_control', side_effect=AssertionError('scaled base used')
        ):
            control = program._fit_stacked_control(
                self.scores, self.outcomes, sample_ratio, False, np.random.default_rng(31)
            )
        self.assertIsInstance(control, program.StackedControl)
        stack_gram, stack_cross_covariance = captured[0]
        variance_floor = 1e-12 * np.trace(stack_gram)
        ridge_penalty = (2.0 / self.outcomes.size) * np.diag(np.maximum(np.diag(stack_gram), variance_floor))
        stack_system = (1.0 + sample_ratio) * stack_gram + ridge_penalty
        control_weights = control.control_weights
        np.testing.assert_allclose(stack_system @ control_weights, stack_cross_covariance, rtol=1e-10, atol=1e-12)
        unscaled_bases = np.column_stack([base.predict(self.scores) for base in control.calibrators])
        expected = unscaled_bases @ np.linalg.solve(stack_system, stack_cross_covariance)
        np.testing.assert_allclose(control.predict(self.scores), expected)
        self.assertGreater(np.linalg.norm(expected - expected / (1.0 + sample_ratio)), 1e-6)

    def test_single_active_control_and_collinearity(self):
        sample_ratio = 0.75
        for nonlinear_type in (ZeroBase, IdentityBase):
            with self.subTest(nonlinear_type=nonlinear_type.__name__), mock.patch.object(
                program, 'AffineCalibrator', IdentityBase
            ), mock.patch.object(program, 'ScoreCalibrator', nonlinear_type):
                control = program._fit_stacked_control(
                    self.scores, self.outcomes, sample_ratio, False, np.random.default_rng(7)
                )
                inner_folds = np.array_split(np.random.default_rng(7).permutation(self.scores.size), 3)
                batches = [
                    (np.column_stack([self.scores[indices], nonlinear_type(False).predict(self.scores[indices])]),
                     self.outcomes[indices])
                    for indices in inner_folds
                ]
                stack_gram, cross_covariance = program._stack_moments(batches)
                ridge = (2.0 / self.outcomes.size) * np.diag(
                    np.maximum(np.diag(stack_gram), 1e-12 * np.trace(stack_gram))
                )
                np.testing.assert_allclose(
                    control.control_weights,
                    np.linalg.solve((1.0 + sample_ratio) * stack_gram + ridge, cross_covariance),
                )
                self.assertTrue(np.isfinite(control.predict(self.scores)).all())
                if nonlinear_type is ZeroBase:
                    expected = cross_covariance[0] / ((1.0 + sample_ratio + 2.0 / self.outcomes.size) * stack_gram[0, 0])
                    np.testing.assert_allclose(control.control_weights, [expected, 0.0])

    def test_zero_scale_and_constant_score_controls(self):
        with mock.patch.object(program, 'AffineCalibrator', ZeroBase), mock.patch.object(
            program, 'ScoreCalibrator', ZeroBase
        ):
            control = program._fit_stacked_control(
                self.scores, self.outcomes, 0.5, False, np.random.default_rng(2)
            )
        np.testing.assert_array_equal(control.predict(self.scores), np.zeros(self.scores.size))
        self.assertEqual((control.lower_bound, control.upper_bound), (0.0, 0.0))
        control = program._fit_stacked_control(
            np.ones(self.scores.size), self.outcomes, 0.5, False, np.random.default_rng(2)
        )
        np.testing.assert_array_equal(control.predict(self.scores), np.zeros(self.scores.size))

    def test_live_negative_weight_from_negative_covariance(self):
        scores = np.linspace(0.0, 1.0, 39)
        outcomes = (scores < 0.5).astype(float)
        with mock.patch.object(program, 'AffineCalibrator', IdentityBase), mock.patch.object(
            program, 'ScoreCalibrator', ZeroBase
        ):
            control = program._fit_stacked_control(
                scores, outcomes, 0.5, True, np.random.default_rng(5)
            )
        self.assertLess(control.control_weights[0], 0.0)
        self.assertEqual(control.control_weights[1], 0.0)
        self.assertEqual(control.lower_bound, control.control_weights[0])
        self.assertEqual(control.upper_bound, 0.0)
        np.testing.assert_allclose(control.predict(scores), control.control_weights[0] * scores)

    def test_signed_control_is_not_clipped_and_certificate_uses_range(self):
        scores = np.linspace(0.0, 1.0, 11)
        control = program.StackedControl([IdentityBase(True), ReverseBase(True)], [-2.0, 1.5])
        prediction = control.predict(scores)
        np.testing.assert_allclose(prediction, 1.5 - 3.5 * scores)
        self.assertEqual((control.lower_bound, control.upper_bound), (-2.0, 1.5))
        self.assertLess(prediction.min(), 0.0)
        self.assertGreater(prediction.max(), 1.0)
        outcomes = np.arange(scores.size) % 2
        residual_radius = program.bounded_mean_radius(
            outcomes - prediction, -control.upper_bound, 1.0 - control.lower_bound, 0.01
        )
        control_radius = program.bounded_mean_radius(
            prediction, control.lower_bound, control.upper_bound, 0.01
        )
        self.assertTrue(np.isfinite(residual_radius + control_radius))
        original_radius = program.bounded_mean_radius
        recorded_bounds = []

        def radius_spy(values, lower, upper, error_probability):
            recorded_bounds.append((lower, upper))
            return original_radius(values, lower, upper, error_probability)

        with mock.patch.object(program, '_fit_stacked_control', return_value=control), mock.patch.object(
            program, 'bounded_mean_radius', side_effect=radius_spy
        ):
            center, variance, certificate_radius = program._crossfit_controls(
                outcomes, scores, scores, 0.05, True, np.random.default_rng(3)
            )
        self.assertEqual(recorded_bounds, [(-1.5, 3.0), (-2.0, 1.5)] * 5)
        self.assertTrue(np.isfinite([center, variance, certificate_radius]).all())

    def test_inner_fits_share_splits_exclude_validation_and_refit(self):
        records = []
        affine_type, nonlinear_type = program.AffineCalibrator, program.ScoreCalibrator

        class RecordingAffine(affine_type):
            def fit(self, scores, outcomes):
                self.record = ['affine', scores.copy(), outcomes.copy(), []]
                records.append(self.record)
                return super().fit(scores, outcomes)

            def predict(self, scores):
                self.record[3].append(scores.copy())
                return super().predict(scores)

        class RecordingNonlinear(nonlinear_type):
            def fit(self, scores, outcomes):
                self.record = ['nonlinear', scores.copy(), outcomes.copy(), []]
                records.append(self.record)
                return super().fit(scores, outcomes)

            def predict(self, scores):
                self.record[3].append(scores.copy())
                return super().predict(scores)

        with mock.patch.object(program, 'AffineCalibrator', RecordingAffine), mock.patch.object(
            program, 'ScoreCalibrator', RecordingNonlinear
        ):
            control = program._fit_stacked_control(
                self.scores, self.outcomes, 0.5, False, np.random.default_rng(12)
            )
        self.assertIsInstance(control, program.StackedControl)
        self.assertEqual(len(records), 8)
        for record_index in range(0, 6, 2):
            affine_record, nonlinear_record = records[record_index:record_index + 2]
            np.testing.assert_array_equal(affine_record[1], nonlinear_record[1])
            np.testing.assert_array_equal(affine_record[2], nonlinear_record[2])
            np.testing.assert_array_equal(affine_record[3][0], nonlinear_record[3][0])
            self.assertEqual(np.intersect1d(affine_record[1], affine_record[3][0]).size, 0)
            self.assertEqual(affine_record[1].size + affine_record[3][0].size, self.scores.size)
        for record in records[-2:]:
            np.testing.assert_array_equal(record[1], self.scores)
            np.testing.assert_array_equal(record[2], self.outcomes)

    def test_outer_heldout_labels_and_unlabeled_pool_never_enter_fitting(self):
        original_fit = program._fit_stacked_control
        records = []
        unlabeled = np.linspace(2.0, 3.0, 47)

        def fit_spy(training_scores, training_y, sample_ratio, bounded, rng):
            fitted = original_fit(training_scores, training_y, sample_ratio, bounded, rng)
            record = [training_scores.copy(), training_y.copy(), sample_ratio, []]
            records.append(record)

            class PredictionRecorder:
                def predict(self, scores):
                    record[3].append(scores.copy())
                    return fitted.predict(scores)

            return PredictionRecorder()

        with mock.patch.object(program, '_fit_stacked_control', side_effect=fit_spy):
            program._crossfit_controls(
                self.outcomes, self.scores, unlabeled, 0.05, False, np.random.default_rng(51)
            )
        self.assertEqual(len(records), 5)
        for training_scores, training_y, sample_ratio, predictions in records:
            heldout_scores, shared_pool = predictions
            self.assertEqual(np.intersect1d(training_scores, heldout_scores).size, 0)
            self.assertEqual(np.intersect1d(training_scores, unlabeled).size, 0)
            np.testing.assert_array_equal(shared_pool, unlabeled)
            np.testing.assert_allclose(training_y, 0.4 * training_scores + 0.2 * training_scores ** 2)
            self.assertEqual(training_scores.size + heldout_scores.size, self.scores.size)
            self.assertEqual(sample_ratio, self.scores.size / unlabeled.size)

    def test_within_fold_moment_invariance_on_live_validation_predictions(self):
        original_moments = program._stack_moments
        captured_batches = []

        def capture_batches(batches):
            captured_batches.extend(batches)
            return original_moments(batches)

        with mock.patch.object(program, '_stack_moments', side_effect=capture_batches):
            program._fit_stacked_control(
                self.scores, self.outcomes, 0.3, False, np.random.default_rng(10)
            )
        shifted_batches = [
            (controls + np.array([3.0 * (fold_index + 1), -2.0 * fold_index]), outcomes)
            for fold_index, (controls, outcomes) in enumerate(captured_batches)
        ]
        original_gram, original_cross = original_moments(captured_batches)
        shifted_gram, shifted_cross = original_moments(shifted_batches)
        np.testing.assert_allclose(shifted_gram, original_gram, rtol=1e-10, atol=1e-12)
        np.testing.assert_allclose(shifted_cross, original_cross, rtol=1e-10, atol=1e-12)

    def test_whole_interval_offset_invariance_equal_and_unequal_folds(self):
        for count in (30, 33):
            with self.subTest(count=count):
                scores = np.linspace(-1.0, 1.0, count)
                outcomes = 0.4 * scores + 0.2 * scores ** 2
                unlabeled = np.linspace(-1.1, 1.1, 47)
                folds = np.array_split(np.random.default_rng(19).permutation(count), 5)
                fold_controls, shifted_controls = [], []
                for fold_index, heldout in enumerate(folds):
                    training = np.setdiff1d(np.arange(count), heldout)
                    control = program._fit_stacked_control(
                        scores[training], outcomes[training], count / unlabeled.size,
                        False, np.random.default_rng(40 + fold_index),
                    )
                    heldout_prediction = control.predict(scores[heldout])
                    unlabeled_prediction = control.predict(unlabeled)
                    fold_controls.append((heldout, heldout_prediction, unlabeled_prediction))
                    offset = [1.5, -2.0, 4.0, -0.75, 0.125][fold_index]
                    shifted_controls.append((heldout, heldout_prediction + offset, unlabeled_prediction + offset))
                original_center, original_variance = program._control_statistics(outcomes, unlabeled, fold_controls)
                shifted_center, shifted_variance = program._control_statistics(outcomes, unlabeled, shifted_controls)
                np.testing.assert_allclose(shifted_center, original_center, rtol=1e-10, atol=1e-12)
                np.testing.assert_allclose(shifted_variance, original_variance, rtol=1e-10, atol=1e-12)
                for bounded in (False, True):
                    original_interval = program._interval_from_statistics(original_center, original_variance, count, 0.05, bounded)
                    shifted_interval = program._interval_from_statistics(shifted_center, shifted_variance, count, 0.05, bounded)
                    np.testing.assert_allclose(
                        [shifted_interval['lower'], shifted_interval['upper']],
                        [original_interval['lower'], original_interval['upper']], rtol=1e-10, atol=1e-12,
                    )


class StackProtocolTests(unittest.TestCase):
    def episode(self, outcomes, scores, unlabeled, kind, seed=90):
        self.assertEqual(program.handle({'op': 'reset', 'seed': seed}), {'ok': True})
        values = np.concatenate([outcomes, scores, unlabeled]).astype('<f8')
        payload = values.tobytes()
        response = program.handle({
            'op': 'update', 'phase': 'start', 'n': outcomes.size, 'N': unlabeled.size,
            'alpha': 0.05, 'label_kind': kind, 'dtype': '<f8', 'encoding': 'base64',
            'shape': [values.size], 'total_bytes': len(payload), 'chunks': 1,
        })
        self.assertEqual(set(response), {'ok', 'transfer_id'})
        self.assertIs(response['ok'], True)
        self.assertIsInstance(response['transfer_id'], str)
        self.assertEqual(program.handle({
            'op': 'update', 'phase': 'chunk', 'transfer_id': response['transfer_id'],
            'index': 0, 'data': base64.b64encode(payload).decode('ascii'),
        }), {'ok': True})
        self.assertEqual(program.handle({
            'op': 'update', 'phase': 'commit', 'transfer_id': response['transfer_id'],
        }), {'ok': True})
        interval = program.handle({'op': 'infer'})
        self.assertEqual(interval, program.handle({'op': 'infer'}))
        self.assertEqual(set(interval), {'lower', 'upper'})
        self.assertTrue(all(type(value) is float and np.isfinite(value) for value in interval.values()))
        self.assertLessEqual(interval['lower'], interval['upper'])
        return interval

    def test_constant_scores_rare_outcomes_and_minimum_sample_fallback(self):
        for count, kind, constant in ((8, 'real', True), (31, 'bernoulli', True), (31, 'bernoulli', False)):
            outcomes = np.arange(count, dtype=float) / count if kind == 'real' else (np.arange(count) == 0).astype(float)
            scores = np.ones(count) if constant else np.linspace(0.0, 1.0, count)
            interval = self.episode(outcomes, scores, np.linspace(0.0, 1.0, 41), kind)
            self.assertEqual(interval, program._label_only(outcomes, kind, 0.05))
        outcomes = (np.arange(32) % 2).astype(float)
        interval = self.episode(outcomes, np.linspace(0.0, 1.0, 32), np.ones(41), 'bernoulli')
        self.assertEqual(interval, program._label_only(outcomes, 'bernoulli', 0.05))

    def test_reset_replay_isolated_state_and_nonfallback_bounded_endpoints(self):
        outcomes = (np.arange(32) % 2).astype(float)
        scores = 0.15 + 0.6 * outcomes + 0.05 * np.sin(np.arange(32))
        unlabeled = np.linspace(0.0, 1.0, 43)
        original = self.episode(outcomes, scores, unlabeled, 'bernoulli', seed=62)
        self.assertGreaterEqual(original['lower'], 0.0)
        self.assertLessEqual(original['upper'], 1.0)
        self.episode(np.arange(17, dtype=float), np.linspace(-1.0, 1.0, 17), unlabeled, 'real', seed=9)
        replay = self.episode(outcomes, scores, unlabeled, 'bernoulli', seed=62)
        self.assertEqual(original, replay)
        self.assertIn('certificate', program._state)
        self.assertEqual(program.handle({'op': 'reset', 'seed': 62}), {'ok': True})
        self.assertEqual(set(program._state), {'rng', 'phase'})
        with self.assertRaises(ValueError):
            program.handle({'op': 'infer'})


if __name__ == '__main__':
    unittest.main()
