"""Markdown tables for the report (outputs/tables.md)."""
import json, numpy as np, pandas as pd
RS = pd.read_csv('outputs/regional_summary.csv'); g = json.load(open('outputs/global_summary.json'))
G = pd.read_csv('outputs/global_calendar_years.csv', index_col=0)
og = pd.read_csv('data/glambie/results/calendar_years/0_global.csv'); og.index = np.floor(og.start_dates + 1e-6).astype(int)
L = []
L.append('### Table R1. Regional results (calendar years 2000–2023)\n')
L.append('| # | Region | Area 2000 (km²) | Groups | n | Rate (Gt yr⁻¹) | Rate (m w.e. yr⁻¹) | Cumulative (Gt) | 2000–2011 (Gt yr⁻¹) | 2012–2023 (Gt yr⁻¹) | GlaMBIE official (Gt yr⁻¹) | r vs official |')
L.append('|---|---|---|---|---|---|---|---|---|---|---|---|')
for _, r in RS.iterrows():
    L.append(f'| {r.region_id} | {r.region} | {r.area_2000_km2:,.0f} | {r.groups} | {r.n_datasets} | {r.rate_gt:.1f} ± {r.rate_gt_err:.1f} | {r.rate_mwe:.2f} ± {r.rate_mwe_err:.2f} | {r.cum_gt:.0f} ± {r.cum_gt_err:.0f} | {r.rate_2000_2011:.1f} ± {r.err_2000_2011:.1f} | {r.rate_2012_2023:.1f} ± {r.err_2012_2023:.1f} | {r.off_rate_gt:.1f} | {r.r_vs_official:.3f} |')
a = g['2000-2023']
L.append(f"| | **Global** | {G.area.iloc[0]:,.0f} | | {RS.n_datasets.sum()} | **{a['rate_gt']:.0f} ± {a['rate_err']:.0f}** | **{a['rate_mwe']:.2f} ± {a['rate_mwe_err']:.2f}** | **{a['cum_gt']:.0f} ± {a['cum_err']:.0f}** | {g['2000-2011']['rate_gt']:.0f} ± {g['2000-2011']['rate_err']:.0f} | {g['2012-2023']['rate_gt']:.0f} ± {g['2012-2023']['rate_err']:.0f} | {a['official_rate']:.0f} | {g['validation_global']['r']:.3f} |\n")
L.append('### Table R2. Global annual (calendar-year) mass change\n')
L.append('| Year | Mass change (Gt) | σ random | σ systematic | σ structural | σ total | m w.e. | SLE (mm) | GlaMBIE official (Gt) |')
L.append('|---|---|---|---|---|---|---|---|---|')
for y, r in G.iterrows():
    L.append(f'| {y} | {r["gt"]:.0f} | {r.gt_err_rand:.0f} | {r.gt_err_sys:.0f} | {r.gt_err_struct:.0f} | {r.gt_err_total:.0f} | {r.mwe:.2f} ± {r.mwe_err_total:.2f} | {r.sle_mm:.2f} ± {r.sle_mm_err:.2f} | {og.loc[y, "combined_gt"]:.0f} ± {og.loc[y, "combined_gt_errors"]:.0f} |')
L.append('\n### Table R3. Global period statistics\n')
L.append('| Period | Mean rate (Gt yr⁻¹) | Cumulative (Gt) | SLE (mm) | GlaMBIE official rate (Gt yr⁻¹) |')
L.append('|---|---|---|---|---|')
for k in ['2000-2023', '2000-2011', '2012-2023', '2000-2009', '2010-2019', '2000-2019', '2006-2016']:
    v = g[k]
    L.append(f"| {k} | {v['rate_gt']:.0f} ± {v['rate_err']:.0f} | {v['cum_gt']:.0f} ± {v['cum_err']:.0f} | {v['sle_mm']:.1f} ± {v['sle_err']:.1f} | {v['official_rate']:.0f} |")
VS = pd.read_csv('outputs/variants_summary.csv')
L.append('\n### Table R4. Sensitivity experiments (global, 2000–2023)\n')
L.append('| Variant | Mean rate (Gt yr⁻¹) | Δ cumulative vs main (%) | r vs main | r vs official |')
L.append('|---|---|---|---|---|')
for _, r in VS.iterrows():
    note = ' (7 single-group regions filled with main)' if r.variant == 'no_demdiff_glac' else ''
    L.append(f'| {r.variant}{note} | {r.global_rate_2000_2023:.1f} | {r.diff_vs_main_pct:+.1f} | {r.r_vs_main:.3f} | {r.r_vs_official:.3f} |')
open('outputs/tables.md', 'w').write('\n'.join(L))
print('\n'.join(L))
