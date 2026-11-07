"""Exact leading-order oracle width ratios for analytically tractable DGPs."""
import pandas as pd
rows=[]
for d,vm,ve,scalar_signal in [
 ('linear',.8**2/12,.2**2,.8**2/12),
 ('quadratic',4/45,.15**2,0),
 ('no_signal',0,.2**2,0),
 ('heavy_tail',4/45,3*.15**2,0),
 ('bernoulli_quadratic',.9**2*4/45,.35*.65-.9**2*4/45,0),
 ('bounded_quadratic',.95**2*4/45,.025**2/3,0)]:
 for r in [.1,1]:
  label=vm+ve; scalar=label-scalar_signal/(1+r); oracle=ve+vm*r/(1+r)
  rows.append((d,r,vm,ve,(oracle/scalar)**.5,(oracle/label)**.5))
pd.DataFrame(rows,columns=['scenario','n_over_N','conditional_mean_variance','mean_conditional_variance','oracle_width_ratio_to_scalar','oracle_width_ratio_to_label']).to_csv('results/theory.csv',index=False)
