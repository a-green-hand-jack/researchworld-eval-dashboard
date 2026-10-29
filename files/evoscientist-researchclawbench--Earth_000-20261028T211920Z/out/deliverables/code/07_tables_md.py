"""Produce Markdown tables used in the report (outputs/tables_md.md)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pandas as pd, numpy as np
import glambie_lib as L
OUT = os.path.join(L.ROOT, 'outputs')
s = pd.read_csv(os.path.join(OUT, 'summary_rates_2000_2023.csv'))
c = pd.read_csv(os.path.join(OUT, 'compare_official_regional.csv'))
inv = pd.read_csv(os.path.join(OUT, 'inventory.csv'))
res = pd.read_pickle(os.path.join(OUT, 'main_results.pkl'))['res']
lines = []
lines.append('| RGI | Region | Area 2000 (km²) | Groups used | Rate (m w.e. yr⁻¹) | Rate (Gt yr⁻¹) | Cumulative 2000–2023 (Gt) | GlaMBIE-2024 rate (Gt yr⁻¹) | r (annual) |')
lines.append('|---|---|---|---|---|---|---|---|---|')
ab = {'altimetry': 'A', 'gravimetry': 'G', 'demdiff_glac': 'D'}
for r in s.itertuples():
    if r.region_id == 0:
        continue
    cc = c[c.region_id == r.region_id].iloc[0]
    grp = '+'.join(ab[g] for g in res[r.region_id]['groups'])
    lines.append(f'| {r.region_id} | {r.region} | {r.area_2000:,.0f} | {grp} | {r.mean_mwe_yr:.2f} ± {r.mean_mwe_yr_err:.2f} | '
                 f'{r.mean_gt_yr:.1f} ± {r.mean_gt_yr_err:.1f} | {r.cum_gt:,.0f} ± {r.cum_gt_err:,.0f} | {cc.off_mean_gt:.1f} | {cc.r:.2f} |')
r = s[s.region_id == 0].iloc[0]
lines.append(f'| – | **Global** | {r.area_2000:,.0f} | – | **{r.mean_mwe_yr:.2f} ± {r.mean_mwe_yr_err:.2f}** | **{r.mean_gt_yr:.1f} ± {r.mean_gt_yr_err:.1f}** | '
             f'**{r.cum_gt:,.0f} ± {r.cum_gt_err:,.0f}** | -272.6 | 0.97 |')
lines.append('')
g = pd.read_csv(os.path.join(OUT, 'global_table_for_report.csv'))
lines.append('| Year | Mass change (Gt) | Specific mass change (m w.e.) | GlaMBIE-2024 (Gt) |')
lines.append('|---|---|---|---|')
for r in g.itertuples():
    lines.append(f'| {int(r.start_dates)} | {r.gt:.0f} ± {r.gt_err:.0f} | {r.mwe:.2f} ± {r.mwe_err:.2f} | {r.combined_gt:.0f} ± {r.combined_gt_errors:.0f} |')
open(os.path.join(OUT, 'tables_md.md'), 'w').write('\n'.join(lines))
print('\n'.join(lines))
