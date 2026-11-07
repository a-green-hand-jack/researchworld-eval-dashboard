"""Scientific output checks: graph replication and undefined-risk semantics."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
import pandas as pd
from gatebench.summarize import performance, summarize

class SummaryChecks(unittest.TestCase):
    def test_undefined_and_insufficient_intervals(self):
        f=pd.DataFrame({'error':[np.nan,np.nan],'valid':[False,False]})
        result=performance(f)
        self.assertEqual(result['undefined_count'],2)
        for key in ['rmse','rmse_lo','rmse_hi']:
            self.assertTrue(np.isnan(result[key]))
        single=performance(pd.DataFrame({'error':[1.],'valid':[True]}))
        self.assertEqual(single['rmse'],1.)
        self.assertTrue(np.isnan(single['rmse_lo']))
        self.assertTrue(np.isnan(single['rmse_hi']))

    def test_float_truth_is_not_graph_family_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);files=[]
            for seed,truth in [(1,2.),(2,np.nextafter(2.,3.))]:
                rows=[]
                for rep in range(3):
                    for model in ['naive','linear']:
                        error=.1*(rep+1) if model=='linear' else -.8+.1*rep
                        rows.append(dict(graph=f'regular_g{seed}',graph_kind='regular',graph_seed=seed,
                            n=2000,degree_target=80,cluster_size=32,design='bernoulli',p=.5,rho=0.,gamma=1.,
                            mechanism='cubic',model=model,truth=truth,replicate=rep,error=error,
                            valid=True,prediction_mse=1.+error**2,conditional_mse=error**2,conditional_bias=error))
                file=root/f'{seed}.parquet';pd.DataFrame(rows).to_parquet(file);files.append(file)
            summarize(files,root/'out')
            family=pd.read_csv(root/'out/performance_by_family.csv')
            pairs=pd.read_csv(root/'out/paired_by_family.csv')
            self.assertEqual(len(family),2)
            self.assertTrue((family.graphs==2).all())
            self.assertEqual(len(pairs),1)
            self.assertEqual(pairs.graphs.iloc[0],2)
            self.assertTrue((family.truth_max>family.truth_min).all())

if __name__=='__main__':
    unittest.main()
