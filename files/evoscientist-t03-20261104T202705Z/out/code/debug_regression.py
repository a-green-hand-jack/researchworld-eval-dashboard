"""Offline loading and synthetic resume checks; no training or SHAP execution.
Run from /work: python debug_regression.py
"""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import experiment as e


class DebugRegression(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(dir=e.ROOT)
        self.addCleanup(tmp.cleanup)
        self.out = Path(tmp.name)
        for name, replacement in (
            ('OUT', self.out),
            ('fit_model', unittest.mock.Mock(side_effect=AssertionError('training forbidden'))),
            ('Game', unittest.mock.Mock(side_effect=AssertionError('SHAP forbidden'))),
        ):
            guard = patch.object(e, name, replacement)
            guard.start()
            self.addCleanup(guard.stop)

    def test_german_loading(self):
        expected = ['status', 'history', 'purpose', 'savings', 'employment',
                    'personal', 'debtors', 'property', 'other_installments',
                    'housing', 'job', 'telephone', 'foreign']
        read_csv = e.pd.read_csv
        for dtype in (None, 'object', 'string', 'category'):
            with self.subTest(dtype=dtype):
                def reader(*args, **kwargs):
                    df = read_csv(*args, **kwargs)
                    if dtype is not None:
                        for c in expected:
                            df[c] = df[c].astype(dtype)
                    return df
                with patch.object(e.pd, 'read_csv', side_effect=reader):
                    X, y, cg, tr, va, te, instances, bg, meta, transforms = e.load_data('german')
                self.assertEqual(meta['categorical'], expected)
                self.assertEqual(meta['d'], 20)
                self.assertEqual(X.shape, (1000, 61))
                self.assertTrue(e.np.isfinite(X).all())
                self.assertEqual((len(tr), len(va), len(te)), (600, 200, 200))
                self.assertEqual((len(instances), len(bg)), (30, 16))
                for feature, (imputer, transform) in zip(meta['features'], transforms):
                    categorical = feature in expected
                    self.assertEqual(imputer.strategy, 'most_frequent' if categorical else 'median')
                    self.assertIsInstance(transform, e.OneHotEncoder if categorical else e.StandardScaler)
                print(f'German dtype={dtype or "inferred"}: shape={X.shape}, categorical={len(expected)}')

    def test_other_dataset_loading(self):
        for name in ('pima', 'acs'):
            with self.subTest(dataset=name):
                X, _, _, _, _, _, _, _, meta, _ = e.load_data(name)
                self.assertTrue(e.np.isfinite(X).all())
                self.assertEqual(len(meta['categorical']), 0 if name == 'pima' else 7)
                print(f'{name}: shape={X.shape}, categorical={len(meta["categorical"])}')

    def test_existing_cell_validation(self):
        # Only synthetic existing files are used; loading/training is forbidden.
        cases = ['match', 'sensitivity_match', 'pilot', 'repetitions', 'rank',
                 'budget_axis', 'instances', 'budgets', 'report_n', 'report_repetitions',
                 'background', 'sensitivity_background', 'missing_background',
                 'missing_report', 'corrupt_report', 'missing_phi']
        with patch.object(e, 'load_data', side_effect=AssertionError('loading forbidden on skip')):
            for case in cases:
                with self.subTest(case=case):
                    sensitivity = case.startswith('sensitivity')
                    path = self.out / ('pima_lr_11_b16.npz' if sensitivity else 'pima_lr_11.npz')
                    shape = (2, 3, len(e.BUDGETS), 8)
                    if case == 'pilot': shape = (1, 1, len(e.BUDGETS), 8)
                    if case == 'repetitions': shape = (2, 1, len(e.BUDGETS), 8)
                    if case == 'rank': shape = shape[:3]
                    if case == 'budget_axis': shape = (2, 3, 1, 8)
                    saved = dict(phi=e.np.zeros(shape), instances=e.np.arange(1 if case == 'instances' else 2),
                                 budgets=[99] if case == 'budgets' else e.BUDGETS)
                    if case == 'missing_phi': del saved['phi']
                    e.np.savez(path, **saved)
                    report = dict(n=2, repetitions=3, background=16 if sensitivity else 8)
                    if case == 'report_n': report['n'] = 1
                    if case == 'report_repetitions': report['repetitions'] = 1
                    if case in ('background', 'sensitivity_background'): report['background'] = 4
                    if case == 'missing_background': del report['background']
                    sidecar = path.with_suffix('.json')
                    sidecar.write_text('{' if case == 'corrupt_report' else json.dumps(report))
                    if case == 'missing_report': sidecar.unlink()
                    before = {p.name: p.read_bytes() for p in self.out.iterdir()}
                    if case in ('match', 'sensitivity_match'):
                        self.assertEqual(e.run_cell('pima', 'lr', 11, n=2, reps=3, sensitivity=sensitivity),
                                         {'skip': str(path)})
                    else:
                        with self.assertRaisesRegex(ValueError, 'Cannot skip existing cell'):
                            e.run_cell('pima', 'lr', 11, n=2, reps=3, sensitivity=sensitivity)
                    self.assertEqual(before, {p.name: p.read_bytes() for p in self.out.iterdir()})
        print(f'Resume validation: {len(cases)} synthetic cases passed; files unchanged')


if __name__ == '__main__':
    unittest.main(verbosity=2)
