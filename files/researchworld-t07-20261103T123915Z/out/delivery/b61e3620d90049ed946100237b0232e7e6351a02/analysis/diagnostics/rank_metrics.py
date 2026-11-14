"""Numerically canonical rank diagnostics; raw score-error calculations retained.

Round only ranking/tie quantities to12 decimals, far below any true-score grid
step. The motivating invariant is equal ranks after adding a common constant.
"""
import numpy as np
from scipy.stats import spearmanr,kendalltau

def metrics(truth,pred,decimals=12):
 y=np.asarray(truth);p=np.asarray(pred);error=p-y
 yr=np.round(y,decimals);pr=np.round(p,decimals)
 i,j=np.triu_indices(len(y),1);dy=np.round(yr[i]-yr[j],decimals);dp=pr[i]-pr[j]
 close=(np.abs(dy)>0)&(np.abs(dy)<=.01);wide=np.abs(dy)>.01
 rank_valid=len(np.unique(yr))>1 and len(np.unique(pr))>1
 def fraction(mask):return float(np.mean(dy[mask]*dp[mask]<0)) if np.any(mask) else float('nan')
 return {'n_targets':len(y),'mae_pp':float(np.abs(error).mean()*100),'rmse_pp':float(np.sqrt(np.mean(error**2))*100),
  'bias_pp':float(error.mean()*100),'p90_abs_error_pp':float(np.quantile(np.abs(error),.9)*100),
  'out_of_range_fraction':float(np.mean((p<0)|(p>1))),
  'spearman':float(spearmanr(yr,pr).statistic) if rank_valid else float('nan'),
  'kendall_tau_b':float(kendalltau(yr,pr,variant='b').statistic) if rank_valid else float('nan'),
  'rank_undefined':not rank_valid,'prediction_tie_pairs':int(np.sum(dp==0)),
  'truth_tie_pairs':int(np.sum(dy==0)),'close_pair_count':int(close.sum()),'wide_pair_count':int(wide.sum()),
  'close_pair_inversion':fraction(close),'wide_pair_inversion':fraction(wide),
  'close_pair_predicted_tie_fraction':float(np.mean(dp[close]==0)) if close.any() else float('nan'),
  'wide_pair_predicted_tie_fraction':float(np.mean(dp[wide]==0)) if wide.any() else float('nan')}
