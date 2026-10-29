"""All report figures (PNG) -> report/images/"""
import sys, json, warnings
sys.path.insert(0, 'code'); warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import recon
from recon import REGIONS, LABELS

IMG = 'report/images'
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
COL = {'altimetry': '#1f77b4', 'gravimetry': '#2ca02c', 'demdiff_and_glaciological': '#d62728', 'demdiff': '#d62728',
       'glaciological': '#ff7f0e', 'combined': '#7f7f7f', 'consensus': 'k', 'official': '#9467bd'}
GNAME = {'altimetry': 'Altimetry', 'gravimetry': 'Gravimetry', 'demdiff_and_glaciological': 'DEM diff. + glaciological'}
years = np.arange(2000, 2024)

inv = pd.read_csv('outputs/input_inventory.csv')
G = pd.read_csv('outputs/global_calendar_years.csv', index_col=0)
RS = pd.read_csv('outputs/regional_summary.csv')
gsum = json.load(open('outputs/global_summary.json'))
off = {}
for rid, name in REGIONS.items():
    o = pd.read_csv(f'{recon.RES}/calendar_years/{rid}_{name}.csv'); o.index = np.floor(o.start_dates + 1e-6).astype(int); off[rid] = o.loc[years]
og = pd.read_csv(f'{recon.RES}/calendar_years/0_global.csv'); og.index = np.floor(og.start_dates + 1e-6).astype(int); og = og.loc[years]
cal = {rid: pd.read_csv(f'outputs/calendar_years/{rid}_{n}.csv', index_col=0) for rid, n in REGIONS.items()}
hy = {rid: pd.read_csv(f'outputs/hydrological_years/{rid}_{n}.csv', index_col=0) for rid, n in REGIONS.items()}

# ---------------------------------------------------------------- Fig 1: data overview
fig = plt.figure(figsize=(11, 8.5))
ax = fig.add_axes([0.2, 0.08, 0.55, 0.88])
y = 0; yt, yl = [], []
srcs = ['altimetry', 'gravimetry', 'demdiff', 'glaciological', 'combined']
for rid in REGIONS:
    sub = inv[inv.region_id == rid].copy()
    sub['o'] = sub.source.map({s: i for i, s in enumerate(srcs)}); sub = sub.sort_values(['o', 'dataset'])
    y0 = y
    for _, r in sub.iterrows():
        d = pd.read_csv(r.file)
        excluded = (r.source == 'combined') or (r.source == 'gravimetry' and rid in recon.GRAV_EXCLUDED)
        for _, q in d.iterrows():
            ax.plot([max(q.start_dates, 1999.5), min(q.end_dates, 2024.9)], [y, y], color=COL[r.source], lw=2.2 if q.end_dates - q.start_dates > 1.01 else 1.2,
                    alpha=0.25 if excluded else 0.9, solid_capstyle='butt')
        y += 1
    yt.append((y0 + y - 1) / 2); yl.append(f'{rid}. {LABELS[rid]}')
    ax.axhline(y - 0.5 + 0.5, color='0.8', lw=0.5)
    y += 1.5
ax.set_yticks(yt); ax.set_yticklabels(yl, fontsize=7.5); ax.invert_yaxis(); ax.set_xlim(1999.5, 2025)
ax.set_xlabel('Year'); ax.set_title('Temporal coverage of the 257 input solutions (faded = not used in consensus)', fontsize=9)
for s in srcs:
    ax.plot([], [], color=COL[s], lw=3, label={'demdiff': 'DEM differencing', 'combined': 'hybrid'}.get(s, s))
ax.legend(loc='lower left', fontsize=7, frameon=False, ncol=1, bbox_to_anchor=(1.01, 0.0))
ax2 = fig.add_axes([0.82, 0.55, 0.16, 0.38])
cnt = inv.groupby('source').size().reindex(srcs)
ax2.barh(range(len(srcs)), cnt.values, color=[COL[s] for s in srcs]); ax2.set_yticks(range(len(srcs)))
ax2.set_yticklabels(['Altimetry', 'Gravimetry', 'DEM diff.', 'Glaciological', 'Hybrid'], fontsize=7.5); ax2.invert_yaxis()
for i, v in enumerate(cnt.values): ax2.text(v + 1, i, str(v), va='center', fontsize=7)
ax2.set_xlabel('No. of solutions', fontsize=8); ax2.set_title('Solutions per method', fontsize=8)
fig.savefig(f'{IMG}/fig1_data_overview.png', dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 2: global series
fig, axs = plt.subplots(1, 2, figsize=(12, 4.3))
ax = axs[0]
ax.bar(years, G['gt'], yerr=G.gt_err_total, color='#4c72b0', alpha=0.85, capsize=2, error_kw=dict(lw=0.7), label='This study (±1σ total)')
ax.plot(years, og.combined_gt, 'o-', color=COL['official'], ms=3, lw=1, label='GlaMBIE (2024) official')
ax.axhline(0, color='k', lw=0.5)
ax.set_ylabel('Annual mass change (Gt yr$^{-1}$)'); ax.set_title('a) Global glacier mass change, calendar years')
ax.legend(frameon=False, fontsize=8, loc='lower left')
ax = axs[1]
cum = np.concatenate([[0], np.cumsum(G['gt'].values)]); t = np.arange(2000, 2025)
# cumulative uncertainty
ce = [0]
for i in range(1, 25):
    sl = slice(2000, 1999 + i)
    e = np.sqrt(sum((np.sqrt(np.sum(cal[r].loc[sl, 'gt_err_rand'] ** 2)) ** 2 + np.sum(cal[r].loc[sl, 'gt_err_sys']) ** 2 + np.sum(cal[r].loc[sl, 'gt_err_struct']) ** 2) for r in REGIONS))
    ce.append(e)
ce = np.array(ce)
ax.fill_between(t, cum - ce, cum + ce, color='#4c72b0', alpha=0.25)
ax.plot(t, cum, color='#4c72b0', lw=2, label=f'This study: {cum[-1]:.0f} ± {ce[-1]:.0f} Gt')
oc = np.concatenate([[0], np.cumsum(og.combined_gt.values)])
ax.plot(t, oc, '--', color=COL['official'], lw=1.5, label=f'GlaMBIE official: {oc[-1]:.0f} Gt')
dus = pd.read_csv('outputs/hybrid_dussaillant_global.csv', index_col=0)
dc = np.concatenate([[0], np.cumsum(dus.dus_global_gt.values)])
ax.plot(t, dc, ':', color='0.4', lw=1.5, label=f'Hybrid (Dussaillant et al.): {dc[-1]:.0f} Gt')
ax.set_ylabel('Cumulative mass change since 1 Jan 2000 (Gt)'); ax.set_title('b) Cumulative global mass change')
sec = ax.secondary_yaxis('right', functions=(lambda x: -x / 362.5, lambda x: -x * 362.5)); sec.set_ylabel('Sea-level contribution (mm)')
ax.legend(frameon=False, fontsize=8, loc='lower left')
fig.tight_layout(); fig.savefig(f'{IMG}/fig2_global_timeseries.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 3: regional grids (HY, m w.e.)
fig, axs = plt.subplots(5, 4, figsize=(13, 14), sharex=True)
for ax, rid in zip(axs.flat, REGIONS):
    h = hy[rid]; s = recon.hy_start(rid); x = h.index + s + 0.5
    for g in ['altimetry', 'gravimetry', 'demdiff_and_glaciological']:
        if g + '_mwe' in h:
            m = h[g + '_covered'].astype(bool)
            ax.plot(x[m], h.loc[m, g + '_mwe'], 'o', ms=2.2, color=COL[g], alpha=0.75)
    ax.fill_between(x, h.mwe - h.mwe_err, h.mwe + h.mwe_err, color='0.6', alpha=0.35, lw=0)
    ax.plot(x, h.mwe, color='k', lw=1.2)
    o = pd.read_csv(f'{recon.RES}/hydrological_years/{rid}_{REGIONS[rid]}.csv')
    ax.plot(o.start_dates + 0.5, o.combined_mwe, '--', color=COL['official'], lw=1)
    ax.axhline(0, color='k', lw=0.4)
    ax.set_title(f'{rid}. {LABELS[rid]}', fontsize=8.5); ax.set_xlim(1999.5, 2024.8)
    ax.tick_params(labelsize=7)
ax = axs.flat[19]; ax.axis('off')
for g in GNAME: ax.plot([], [], 'o', color=COL[g], label=GNAME[g] + ' (group)')
ax.plot([], [], 'k-', label='Consensus (this study) ±1σ'); ax.plot([], [], '--', color=COL['official'], label='GlaMBIE official')
ax.legend(loc='center', frameon=False, fontsize=8.5)
for a in axs[:, 0]: a.set_ylabel('m w.e. yr$^{-1}$', fontsize=8)
fig.suptitle('Regional specific mass change per hydrological year: data-group estimates and reconciled consensus', y=0.995, fontsize=10)
fig.tight_layout(); fig.savefig(f'{IMG}/fig3_regional_timeseries.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 4: regional rates
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2))
idx = np.arange(19); lab = [f'{r}. {LABELS[r]}' for r in RS.region_id]
ax = axs[0]
ax.barh(idx - 0.2, RS.rate_gt, xerr=RS.rate_gt_err, height=0.4, color='#4c72b0', label='This study', error_kw=dict(lw=0.7, capsize=1.5))
ax.barh(idx + 0.2, RS.off_rate_gt, height=0.4, color=COL['official'], alpha=0.6, label='GlaMBIE official')
ax.set_yticks(idx); ax.set_yticklabels(lab, fontsize=7.5); ax.invert_yaxis(); ax.set_xlabel('Mean mass change 2000–2023 (Gt yr$^{-1}$)')
ax.legend(frameon=False, fontsize=8); ax.set_title('a) Total mass change rate')
ax = axs[1]
ax.barh(idx - 0.2, RS.rate_mwe, xerr=RS.rate_mwe_err, height=0.4, color='#4c72b0', error_kw=dict(lw=0.7, capsize=1.5))
ax.barh(idx + 0.2, RS.off_rate_mwe, height=0.4, color=COL['official'], alpha=0.6)
ax.set_yticks(idx); ax.set_yticklabels([]); ax.invert_yaxis(); ax.set_xlabel('Mean specific mass change 2000–2023 (m w.e. yr$^{-1}$)')
ax.set_title('b) Specific mass change rate')
fig.tight_layout(); fig.savefig(f'{IMG}/fig4_regional_rates.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 5: validation vs official
fig, axs = plt.subplots(1, 3, figsize=(13, 4.2))
ax = axs[0]
allx, ally = [], []
cm = plt.get_cmap('tab20')
for i, rid in enumerate(REGIONS):
    ax.scatter(off[rid].combined_mwe, cal[rid].mwe, s=6, color=cm(i % 20), alpha=0.8)
    allx += list(off[rid].combined_mwe); ally += list(cal[rid].mwe)
allx, ally = np.array(allx), np.array(ally)
lim = [-4, 1.5]; ax.plot(lim, lim, 'k-', lw=0.6); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('GlaMBIE official (m w.e. yr$^{-1}$)'); ax.set_ylabel('This study (m w.e. yr$^{-1}$)')
ax.set_title(f'a) Regional calendar years (n={len(allx)})\nr={np.corrcoef(allx, ally)[0,1]:.3f}, RMSD={np.sqrt(np.mean((allx-ally)**2)):.3f} m w.e.', fontsize=8.5)
ax = axs[1]
ax.errorbar(og.combined_gt, G['gt'], xerr=og.combined_gt_errors, yerr=G.gt_err_total, fmt='o', ms=3, color='#4c72b0', elinewidth=0.5)
for yy in years: ax.annotate(str(yy)[2:], (og.combined_gt[yy], G['gt'][yy]), fontsize=5.5, xytext=(2, 2), textcoords='offset points')
lim = [-650, 50]; ax.plot(lim, lim, 'k-', lw=0.6); ax.set_xlim(lim); ax.set_ylim(lim)
v = gsum['validation_global']
ax.set_xlabel('GlaMBIE official (Gt yr$^{-1}$)'); ax.set_ylabel('This study (Gt yr$^{-1}$)')
ax.set_title(f'b) Global annual mass change\nr={v["r"]:.3f}, RMSD={v["rmsd_gt"]:.0f} Gt, bias={v["bias_gt"]:.0f} Gt', fontsize=8.5)
ax = axs[2]
ax.errorbar(RS.off_rate_gt, RS.rate_gt, yerr=RS.rate_gt_err, fmt='o', ms=4, color='#4c72b0', elinewidth=0.7)
for _, r in RS.iterrows(): ax.annotate(str(r.region_id), (r.off_rate_gt, r.rate_gt), fontsize=7, xytext=(3, 2), textcoords='offset points')
lim = [-65, 2]; ax.plot(lim, lim, 'k-', lw=0.6); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('GlaMBIE official (Gt yr$^{-1}$)'); ax.set_ylabel('This study (Gt yr$^{-1}$)'); ax.set_title('c) Regional mean rates 2000–2023', fontsize=8.5)
fig.tight_layout(); fig.savefig(f'{IMG}/fig5_validation_official.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 6: data-group agreement
A = pd.read_csv('outputs/group_agreement.csv')
regs = A.region_id.unique()
fig, ax = plt.subplots(figsize=(10, 4.2))
offs = {'altimetry': -0.22, 'gravimetry': 0, 'demdiff_and_glaciological': 0.22}
for j, rid in enumerate(regs):
    sub = A[A.region_id == rid]
    for _, r in sub.iterrows():
        ax.errorbar(j + offs[r.group], r.mean_mwe, yerr=r.err_mwe, fmt='o', color=COL[r.group], ms=4, elinewidth=1)
    ax.plot([j - 0.35, j + 0.35], [sub.combined_mean.iloc[0]] * 2, 'k-', lw=1.5)
ax.set_xticks(range(len(regs)))
ax.set_xticklabels([f'{r}. {LABELS[r]}\n({A[A.region_id==r].first.iloc[0]}–{A[A.region_id==r]["last"].iloc[0]+1})' for r in regs], rotation=45, ha='right', fontsize=7)
for g in GNAME: ax.errorbar([], [], yerr=[], fmt='o', color=COL[g], label=GNAME[g])
ax.plot([], [], 'k-', label='Consensus'); ax.legend(frameon=False, fontsize=7.5, ncol=4)
ax.set_ylabel('Mean specific mass change over\ncommon period (m w.e. yr$^{-1}$)'); ax.axhline(0, color='k', lw=0.4)
ax.set_title('Agreement of data groups over their common (hydrological-year) period', fontsize=9)
fig.tight_layout(); fig.savefig(f'{IMG}/fig6_group_agreement.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 7: sensitivity
VS = pd.read_csv('outputs/variants_summary.csv')
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
ax = axs[0]
for v in VS.variant:
    if v == 'no_demdiff_glac':
        continue
    d = pd.read_csv(f'outputs/variants/{v}_calendar_gt.csv', index_col=0)
    c = np.concatenate([[0], np.cumsum(d.global_gt.values)])
    ax.plot(np.arange(2000, 2025), c, lw=2.2 if v == 'main' else 1, color='k' if v == 'main' else None, label=v)
ax.plot(np.arange(2000, 2025), oc, '--', color=COL['official'], lw=1.5, label='GlaMBIE official')
ax.set_ylabel('Cumulative global mass change (Gt)'); ax.legend(fontsize=6.5, frameon=False, ncol=2); ax.set_title('a) Sensitivity of global cumulative change to method choices', fontsize=9)
ax = axs[1]
L = pd.read_csv('outputs/leave_one_group_out.csv')
regsL = L.region_id.unique()
for j, rid in enumerate(regsL):
    sub = L[L.region_id == rid]
    ax.errorbar(j, 0, yerr=sub.main_err.iloc[0] / np.sqrt(24 / 3), fmt='none', color='0.5', capsize=3)
    for _, r in sub.iterrows():
        ax.plot(j + offs[r.left_out], r.diff_mwe, 'o', color=COL[r.left_out], ms=5)
ax.axhline(0, color='k', lw=0.5)
ax.set_xticks(range(len(regsL))); ax.set_xticklabels([f'{r}. {LABELS[r]}' for r in regsL], rotation=45, ha='right', fontsize=7)
for g in GNAME: ax.plot([], [], 'o', color=COL[g], label='without ' + GNAME[g])
ax.legend(frameon=False, fontsize=7); ax.set_ylabel('Change in 2000–2023 mean (m w.e. yr$^{-1}$)')
ax.set_title('b) Leave-one-data-group-out test', fontsize=9)
fig.tight_layout(); fig.savefig(f'{IMG}/fig7_sensitivity.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 8: hybrid comparison
H = pd.read_csv('outputs/hybrid_comparison.csv')
fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
ax = axs[0]
mk = {'Dussaillant et al.': 'o', 'Huss et al.': 's', 'Box et al.': '^', 'Colgan et al.': 'D', 'Miles et al.': 'v', 'Palsson et al.': 'P'}
for a, sub in H.groupby('author'):
    ax.scatter(sub.consensus_mean, sub.hybrid_mean, marker=mk.get(a, 'o'), s=22, label=a, alpha=0.8)
lim = [-1.2, 0.05]; ax.plot(lim, lim, 'k-', lw=0.6); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('Consensus (this study), m w.e. yr$^{-1}$'); ax.set_ylabel('Hybrid estimate, m w.e. yr$^{-1}$')
ax.legend(frameon=False, fontsize=7); ax.set_title('a) Mean rates over each hybrid period (all regions)', fontsize=9)
ax = axs[1]
ann = H[H.type == 'annual']
data = [ann[ann.author == a].r.dropna().values for a in ['Dussaillant et al.', 'Huss et al.', 'Box et al.']]
ax.boxplot(data, tick_labels=['Dussaillant', 'Huss', 'Box'], widths=0.5)
for i, d in enumerate(data): ax.scatter(np.full(len(d), i + 1) + np.random.default_rng(1).uniform(-0.1, 0.1, len(d)), d, s=10, color='0.3')
ax.set_ylabel('Correlation of annual series with consensus'); ax.set_title('b) Interannual agreement with hybrid datasets', fontsize=9)
fig.tight_layout(); fig.savefig(f'{IMG}/fig8_hybrid_comparison.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 9: two-period comparison
fig, ax = plt.subplots(figsize=(10, 4.2))
w = 0.38
ax.bar(idx - w / 2, RS.rate_2000_2011, w, yerr=RS.err_2000_2011, color='#9ecae1', label='2000–2011', error_kw=dict(lw=0.6, capsize=1.5))
ax.bar(idx + w / 2, RS.rate_2012_2023, w, yerr=RS.err_2012_2023, color='#08519c', label='2012–2023', error_kw=dict(lw=0.6, capsize=1.5))
ax.set_xticks(idx); ax.set_xticklabels([f'{r}' for r in RS.region_id]); ax.set_xlabel('GTN-G region')
ax.set_ylabel('Mean mass change (Gt yr$^{-1}$)'); ax.legend(frameon=False)
g1, g2 = gsum['2000-2011'], gsum['2012-2023']
ax.set_title(f'Regional mass change in two 12-yr periods; global: {g1["rate_gt"]:.0f}±{g1["rate_err"]:.0f} → {g2["rate_gt"]:.0f}±{g2["rate_err"]:.0f} Gt yr$^{{-1}}$', fontsize=9)
fig.tight_layout(); fig.savefig(f'{IMG}/fig9_two_periods.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 10: method illustration (Alaska)
rid = 1; s = recon.hy_start(rid)
anom, clim = recon.seasonal_cycle(rid)
fig, axs = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
ax = axs[0]
for ds in recon.list_datasets(rid):
    if ds['source'] == 'combined':
        continue
    p = recon.process_dataset(ds, rid, recon.DEFAULT_CFG, anom, clim)
    c = COL[ds['source']]
    if p['annual'] is not None:
        a = p['annual']; ax.plot(a.index + s + 0.5, a.v, '-', color=c, lw=0.7, alpha=0.6)
    for t in p['trend']:
        ax.plot([t['m0'] / 12, t['m1'] / 12], [t['mwe'] / t['L']] * 2, '-', color=c, lw=2.5, alpha=0.8)
for sname in ['altimetry', 'gravimetry', 'demdiff', 'glaciological']:
    ax.plot([], [], color=COL[sname], label=sname)
ax.plot([], [], 'k-', lw=2.5, label='thick bars: multi-annual rates'); ax.legend(frameon=False, fontsize=7.5, ncol=5)
ax.set_ylabel('m w.e. yr$^{-1}$'); ax.set_title('a) Alaska: homogenised input solutions (annual aggregates and multi-annual rates)', fontsize=9)
ax.set_ylim(-4, 2.5)
ax = axs[1]
h = hy[rid]; x = h.index + s + 0.5
for g in GNAME:
    if g + '_mwe' in h:
        m = h[g + '_covered'].astype(bool)
        ax.plot(x, h[g + '_mwe'], ':', color=COL[g], lw=0.8)
        ax.plot(x[m], h.loc[m, g + '_mwe'], 'o-', color=COL[g], ms=3, lw=1, label=GNAME[g])
ax.fill_between(x, h.mwe - h.mwe_err, h.mwe + h.mwe_err, color='0.6', alpha=0.35, lw=0)
ax.plot(x, h.mwe, 'k-', lw=2, label='Consensus ±1σ')
ax.legend(frameon=False, fontsize=7.5, ncol=4); ax.set_ylabel('m w.e. yr$^{-1}$'); ax.set_xlabel('Year')
ax.set_title('b) Calibrated data-group series (solid: years with own level information; dotted: variability-extended) and consensus', fontsize=9)
fig.tight_layout(); fig.savefig(f'{IMG}/fig10_method_alaska.png'); plt.close(fig)

# ---------------------------------------------------------------- Fig 11: uncertainty budget + regional share
fig, axs = plt.subplots(1, 2, figsize=(12, 4.2))
ax = axs[0]
ax.stackplot(years, G.gt_err_rand ** 2, G.gt_err_sys ** 2, G.gt_err_struct ** 2, labels=['random (variability)', 'systematic (level)', 'structural (method choice)'],
             colors=['#a6cee3', '#1f78b4', '#fb9a99'])
ax.plot(years, og.combined_gt_errors ** 2, 'k--', lw=1, label='GlaMBIE official (variance)')
ax.set_ylabel('Variance of global annual change (Gt$^2$)'); ax.legend(frameon=False, fontsize=7.5); ax.set_title('a) Uncertainty budget (global, annual)', fontsize=9)
ax = axs[1]
order = RS.sort_values('cum_gt').region_id.values
bp = np.zeros(24); bn = np.zeros(24)
cmap = plt.get_cmap('tab20')
for i, rid in enumerate(order):
    v = -cal[rid].loc[years, 'gt'].values
    vp = np.clip(v, 0, None); vn = np.clip(v, None, 0)
    ax.bar(years, vp, bottom=bp, color=cmap(i % 20), width=0.85, label=f'{rid}')
    ax.bar(years, vn, bottom=bn, color=cmap(i % 20), width=0.85)
    bp += vp; bn += vn
ax.plot(years, -G['gt'], 'k_', ms=8, mew=2, label='net')
ax.axhline(0, color='k', lw=0.5)
ax.set_ylabel('Mass loss (Gt yr$^{-1}$)'); ax.set_title('b) Regional contributions to global annual mass loss', fontsize=9)
ax.legend(ncol=7, fontsize=6, frameon=False, title='region', title_fontsize=6.5, loc='upper left')
fig.tight_layout(); fig.savefig(f'{IMG}/fig11_uncertainty_contributions.png'); plt.close(fig)
print('figures done')
