"""Report measured decomposition agreement without treating Monte Carlo as exact."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
p=argparse.ArgumentParser();p.add_argument('--root',default='.')
a=p.parse_args();root=Path(a.root).resolve();notes=root/('analysis' if (root/'code').exists() else 'notes')
d=pd.read_csv(root/'results/diagnostics/diagnostics_by_graph.csv')
matched={('no_interference','linear'),('linear','linear'),('quadratic','quadratic'),('cubic','cubic'),('twohop','twohop'),('threshold','threshold_oracle')}
selected=d[[tuple(x) in matched for x in d[['mechanism','model']].to_numpy()]]
# Zero-support or occasionally unsupported cells still retain their exact
# nonzero conditional-bias components; no estimable filtering is imposed.
rows=[]
for label,g in [('all_regressions',d[~d.model.isin(['ht','hajek'])]),('matched_controls',selected)]:
    for metric in ['mse_identity_residual','bias_identity_residual']:
        finite=np.isfinite(g[metric])&np.isfinite(g[metric+'_mcse'])&(g[metric+'_mcse']>0)
        z=g.loc[finite,metric]/g.loc[finite,metric+'_mcse']
        rows.append(dict(scope=label,metric=metric,groups=len(g),groups_with_finite_se=int(finite.sum()),
                         max_abs_standardized_residual=float(abs(z).max()),
                         fraction_outside_pointwise_95=float((abs(z)>1.96).mean()),
                         interpretation='Descriptive multiple pointwise Monte Carlo checks, dependent across methods/mechanisms. Not an independence test or multiplicity-adjusted rejection rule.'))
pd.DataFrame(rows).to_csv(root/'results/diagnostics/decomposition_check.csv',index=False)
key=(d.graph_kind=='regular')&(d.n==2000)&(d.degree_target.isin([4,20,80]))&(d.design=='bernoulli')&(d.p==.5)&(d.rho==0)&(d.mechanism=='linear')&(d.model=='linear')
cols=['graph','degree_target','replicates','oracle_variance','assignment_bias_squared','mse_identity_residual','mse_identity_residual_mcse','mse_identity_residual_lo','mse_identity_residual_hi']
d.loc[key,cols].to_csv(root/'results/diagnostics/decomposition_selected_graphs.csv',index=False)
(notes/'decomposition_check.json').write_text(json.dumps(rows,indent=2))
print('Recorded finite-Monte-Carlo decomposition diagnostics')
