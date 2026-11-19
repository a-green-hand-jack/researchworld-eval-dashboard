"""Regression: noncontiguous prompt IDs survive on both dependence axes."""
import sys,tempfile,pathlib
sys.path.insert(0,'scripts')
import numpy as np
import pandas as pd
from analyze_disjoint import export_dependence
ids=[0,1,2,9,10,13,14,15]
scores=np.random.default_rng(812).integers(0,2,size=(40,len(ids)))
with tempfile.TemporaryDirectory() as folder:
 out=pathlib.Path(folder);export_dependence(scores,ids,out)
 for metric,expected in [('covariance',np.cov(scores,rowvar=False)),('correlation',np.corrcoef(scores,rowvar=False))]:
  actual=pd.read_csv(out/f'candidate-{metric}.csv',index_col='candidate_id')
  assert actual.index.tolist()==ids
  assert actual.columns.astype(int).tolist()==ids
  assert np.allclose(actual.to_numpy(),expected)
  assert np.isclose(actual.loc[9,'14'],expected[3,6])
print('PASS: both dependence axes preserve actual noncontiguous candidate IDs and mapped values')
