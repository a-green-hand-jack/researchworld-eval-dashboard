#!/usr/bin/env python3
"""Render the report from analysis outputs and a narrative template."""
from pathlib import Path
import json
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
O=ROOT/'outputs'
f=json.loads((O/'findings.json').read_text())
s=pd.read_csv(O/'regional_period_summary.csv')
c=pd.read_csv(O/'covariance_sensitivity.csv')
g=pd.read_csv(O/'global_annual_2000_2023.csv')

def table(headers,rows):
 return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(map(str,r))+' |' for r in rows])
regional=table(['ID / region','Mean Gt yr⁻¹ ± 95%','Mean m w.e. yr⁻¹ ± 95%','Cumulative Gt','Global loss share','Later − earlier Gt yr⁻¹'],[[('Global' if r.region_id==0 else f'{int(r.region_id):02d} {r.region_name}'),f'{r.mean_gt_per_year:.2f} ± {r.mean_gt_ci95_independent:.2f}',f'{r.mean_mwe_per_year:.3f} ± {r.mean_mwe_ci95_independent:.3f}',f'{r.total_gt:,.1f}',f'{r.global_loss_share_pct:.2f}%',f'{r.late_minus_early_gt_per_year:+.2f}'] for r in s.itertuples()])
annual=table(['Year','Mass change (Gt)','95% half-width (Gt)','Specific change (m w.e.)','95% half-width (m w.e.)'],[[int(r.year),f'{r.mass_change_gt:.2f}',f'{r.mass_change_gt_ci95:.2f}',f'{r.specific_change_mwe:.3f}',f'{r.specific_change_mwe_ci95:.3f}'] for r in g.itertuples()])
covtable=table(['Error correlation scenario','Mean loss, 95% half-width (Gt yr⁻¹)','Increase in loss, 95% half-width (Gt yr⁻¹)','95% Fieller interval for percentage increase'],[[r.scenario,f'{r.mean_gt_ci95:.1f}',f'{r.late_minus_early_ci95:.1f}',f'[{r.increase_percent_ci95_fieller_lower:.1f}%, {r.increase_percent_ci95_fieller_upper:.1f}%]'] for r in c.itertuples()])
parts={'REGION_TABLE':regional,'GLOBAL_ANNUAL_TABLE':annual,'COVARIANCE_TABLE':covtable}
text=(ROOT/'code/report_template.md').read_text()
for k,v in parts.items():text=text.replace('{{'+k+'}}',v)
assert '{{' not in text
(ROOT/'report/report.md').write_text(text)
print(f'Wrote report/report.md: {len(text.split())} words')
