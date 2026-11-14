"""Numerical invariants for ties and the declared one-percentage-point bin."""
import numpy as np
from benchsmall.metrics import metrics as original
from rank_metrics import metrics
truth=np.array([.2,.2,.4,.5]);pred=np.array([.1,.10000000000000002,.2,.3])
a=metrics(truth,pred);b=metrics(truth,pred+.1)
for key in ['spearman','kendall_tau_b','prediction_tie_pairs','close_pair_inversion','wide_pair_inversion']:
 np.testing.assert_allclose(a[key],b[key],equal_nan=True,rtol=0,atol=0)
assert a['prediction_tie_pairs']==1 and a['spearman']==1 and a['kendall_tau_b']==1
boundary=metrics(np.array([.3,.29]),np.array([.4,.5]))
assert boundary['close_pair_count']==1 and boundary['wide_pair_count']==0
rng=np.random.default_rng(61)
y=rng.random(27);p=rng.random(27)*1.1-.05
for key in ['mae_pp','rmse_pp','bias_pp','p90_abs_error_pp','out_of_range_fraction']:
 assert metrics(y,p)[key]==original(y,p)[key]
print('Canonical ties preserve common-constant ranks and exact1pp bins; unrounded score errors unchanged.')
