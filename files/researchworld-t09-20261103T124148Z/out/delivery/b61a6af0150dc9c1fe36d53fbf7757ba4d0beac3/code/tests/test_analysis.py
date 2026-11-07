"""Check uncertainty for independent streams and exact support coupling."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
from gatebench.summarize import KEYS

spec = importlib.util.spec_from_file_location('claim_analysis', Path(__file__).resolve().parents[1]/'scripts/analyze_results.py')
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class ClaimAnalysisChecks(unittest.TestCase):
    def test_noise_panels_are_independent_even_when_replicate_labels_match(self):
        rows = []
        for rho, master, error, se in [(0., 2202601, .2, .03), (1., 2202602, .5, .04)]:
            row = {k: np.nan for k in KEYS}
            row.update(graph='fixed', graph_kind='regular', graph_seed=201, n=2000,
                       degree_target=20, cluster_size=32, design='bernoulli', p=.5,
                       rho=rho, gamma=1., mechanism='linear', model='linear',
                       panel='core' if rho == 0 else 'noise', master_seed=master,
                       defined_fraction=1., valid_fraction=1.)
            for metric, error_name in [('bias','bias_mcse'), ('mse','mse_mcse'), ('rmse','rmse_mcse'),
                                      ('prediction_mse_mean','prediction_mse_mcse'),
                                      ('prediction_mean_mse_mean','prediction_mean_mse_mcse'),
                                      ('oracle_variance_mean','oracle_variance_mcse')]:
                row[metric]=error; row[error_name]=se
            rows.append(row)
        result=analysis.independent_contrasts(pd.DataFrame(rows))
        self.assertEqual(len(result),1)
        self.assertAlmostEqual(result.delta_mse.iloc[0],.3)
        # Independent .03 and .04 standard errors give .05, not cancellation.
        self.assertAlmostEqual(result.delta_mse_mcse.iloc[0],.05)
        self.assertNotEqual(result.master_a.iloc[0], result.master_b.iloc[0])

    def test_shared_hidden_tail_data_obey_pointwise_risk_bound(self):
        rows=[]
        for rep,estimate in enumerate([1.,2.,4.]):
            for mechanism,truth in [('linear',2.),('hidden_tail',3.)]:
                row={k:np.nan for k in KEYS}
                row.update(graph='fixed',graph_kind='regular',graph_seed=201,n=2000,
                           degree_target=80,cluster_size=32,design='bernoulli',p=.5,rho=0.,gamma=1.,
                           model='linear',mechanism=mechanism,pairing_id=str(rep),
                           estimate=estimate,truth=truth,error=estimate-truth,tail_active=0)
                rows.append(row)
        result=analysis.coupling(pd.DataFrame(rows))[0]
        self.assertEqual(result['max_estimate_difference_on_identical_data'],0.)
        self.assertEqual(result['empirical_two_risk_bound'],.25)
        self.assertGreaterEqual(max(result['linear_squared_error'],result['tail_squared_error']),.25)


if __name__=='__main__':
    unittest.main()
