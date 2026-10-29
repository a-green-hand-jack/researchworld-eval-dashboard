"""Sensitivity experiments: re-run the full reconciliation with alternative choices."""
import sys, json; sys.path.insert(0, '/work/code')
import numpy as np, pandas as pd
from run_reconciliation import run

EXPS = {
    'main': {},
    'group_w_invvar': dict(group_weights='invvar'),
    'within_w_per_solution': dict(within_weights='solution'),
    'monthly_err_independent': dict(monthly_err='indep'),
    'gravimetry_all_regions': dict(use_grav=True),
    'gravimetry_none': dict(use_grav=False),
    'no_altimetry': dict(drop_groups=('ALT',)),
    'density_800': dict(rho=0.800),
    'density_900': dict(rho=0.900),
    'offset_constant_per_dataset': dict(offset_model='constant'),
    'extension_nearest': dict(extend='nearest'),
    'glaciological_level': dict(glac_level=True),
    'tau_zero': dict(tau=0.0),
}
rows = []
for name, o in EXPS.items():
    hy, cal, g, metas = run(o, tag=f'sens_{name}', save=True)
    a = g.loc[2000:2011, 'gt'].mean(); b = g.loc[2012:2023, 'gt'].mean()
    rows.append(dict(experiment=name, mean_2000_2023=g['gt'].mean(), mean_2000_2011=a, mean_2012_2023=b,
                     mean_2000_2019=g.loc[2000:2019, 'gt'].mean(), y2023=g.loc[2023, 'gt'],
                     cum=g['gt'].sum(), mean_annual_sig=g.sig_gt.mean()))
    print(rows[-1], flush=True)
df = pd.DataFrame(rows)
df.to_csv('/work/outputs/sensitivity_summary.csv', index=False)
print(df.round(1).to_string())
