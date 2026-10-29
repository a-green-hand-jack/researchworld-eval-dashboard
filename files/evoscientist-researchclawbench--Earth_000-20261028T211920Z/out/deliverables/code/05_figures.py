"""Generate all report figures (PNG) into report/images/."""
import sys, os, pickle, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import glambie_lib as L

OUT = os.path.join(L.ROOT, 'outputs'); IMG = os.path.join(L.ROOT, 'report', 'images')
os.makedirs(IMG, exist_ok=True)
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 110})
M = pickle.load(open(os.path.join(OUT, 'main_results.pkl'), 'rb'))
res, cal, glob_ = M['res'], M['cal'], M['glob']
inv = pd.read_csv(os.path.join(OUT, 'inventory.csv'))
og = pd.read_csv(os.path.join(L.RES, 'calendar_years', '0_global.csv'))
dirs = L.region_dirs()
COL = {'altimetry': '#1f77b4', 'gravimetry': '#2ca02c', 'demdiff_glac': '#d62728', 'hybrid': '#9467bd',
       'glaciological': '#ff7f0e', 'demdiff': '#d62728', 'combined': '#9467bd', 'consensus': 'k'}
LAB = {'altimetry': 'Altimetry', 'gravimetry': 'Gravimetry', 'demdiff_glac': 'DEM diff. + glaciological',
       'glaciological': 'Glaciological', 'demdiff': 'DEM differencing', 'combined': 'Hybrid'}

# ---------------------------------------------------------------- Fig 1: data overview
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw=dict(width_ratios=[1.1, 1]))
methods = ['glaciological', 'demdiff', 'altimetry', 'gravimetry', 'combined']
tab = inv.pivot_table(index='region_id', columns='method', values='dataset', aggfunc='count').reindex(columns=methods).fillna(0)
ax = axs[0]
bottom = np.zeros(len(tab))
for m in methods:
    ax.barh(tab.index, tab[m], left=bottom, color=COL[m], label=LAB[m])
    bottom += tab[m].values
ax.set_yticks(tab.index); ax.set_yticklabels([f'{i} {L.REGION_NAMES[i]}' for i in tab.index])
ax.invert_yaxis(); ax.set_xlabel('Number of submitted datasets'); ax.legend(frameon=False, loc='lower right')
ax.set_title(f'(a) Input datasets per region and method (N = {len(inv)} files)')
ax = axs[1]
yrs = np.arange(1995, 2025)
for m in methods:
    sub = inv[inv.method == m]
    cnt = [((sub.start <= y + 0.5) & (sub.end >= y + 0.5)).sum() for y in yrs]
    ax.plot(yrs, cnt, color=COL[m], lw=2, label=LAB[m])
ax.set_xlabel('Year'); ax.set_ylabel('Datasets covering year'); ax.set_title('(b) Temporal coverage of input datasets')
ax.axvspan(2000, 2024, color='0.93', zorder=0)
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig1_data_overview.png'), dpi=150); plt.close(fig)

# resolution summary figure
fig, ax = plt.subplots(figsize=(7, 3.6))
inv['res_class'] = np.where(inv.median_dt <= 0.09, 'monthly', np.where(inv.median_dt <= 1.001, 'annual', 'multi-annual'))
t2 = inv.pivot_table(index='method', columns='res_class', values='dataset', aggfunc='count').reindex(methods).fillna(0)
t2 = t2.reindex(columns=['monthly', 'annual', 'multi-annual']).fillna(0)
t2.plot(kind='bar', stacked=True, ax=ax, color=['#4c72b0', '#55a868', '#c44e52'])
ax.set_xticklabels([LAB[m] for m in t2.index], rotation=0); ax.set_ylabel('Number of datasets'); ax.set_xlabel('')
ax.set_title('Temporal resolution of the input datasets'); ax.legend(frameon=False, title='Resolution')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig2_resolution.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 3: example region workflow (Alaska)
def plot_region_workflow(rid, fname):
    r = res[rid]; st = r['starts']; x = np.where(st + 1 <= 2024.3, st + 0.5, np.nan)
    fig, axs = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
    ax = axs[0]
    for ds in r['datasets']:
        if 'hy' not in ds or ds['group'] == 'hybrid':
            continue
        c = COL[ds['method']]
        lw = 0.8 if ds['kind'] == 'annual' else 1.4
        ls = '-' if ds['kind'] == 'annual' else '--'
        if ds['method'] == 'glaciological':
            continue
        ok = np.isfinite(ds['hy']) & (ds.get('extrap', np.zeros(len(st))) == 0) if 'extrap' in ds else np.isfinite(ds['hy'])
        ax.plot(x[ok], ds['hy'][ok], ls, color=c, lw=lw, alpha=0.7)
    ax.plot(x, r['glac_ref'] + np.nanmean(r['mwe']), ':', color=COL['glaciological'], lw=1.5,
            label='Glaciological variability reference (anomaly + mean)')
    for m in ['demdiff', 'altimetry', 'gravimetry']:
        ax.plot([], [], color=COL[m], label=LAB[m] + ' datasets')
    ax.plot([], [], 'k--', lw=1.4, label='trend datasets (temporally downscaled)')
    ax.set_ylabel('Mass change (m w.e. yr$^{-1}$)'); ax.legend(frameon=False, fontsize=7.5, ncol=2)
    ax.set_title(f'(a) {L.REGION_NAMES[rid]}: individual datasets at annual (hydrological-year) resolution')
    ax.set_xlim(1999.5, 2024.5)
    ax = axs[1]
    for g, v in r['groups'].items():
        ax.fill_between(x, v['mwe'] - v['err'], v['mwe'] + v['err'], color=COL[g], alpha=0.15)
        ax.plot(x, v['mwe'], color=COL[g], lw=1.5, label=LAB[g])
    ax.errorbar(x, r['mwe'], yerr=r['err'], color='k', lw=2, capsize=2, label='Consensus estimate')
    ax.set_ylabel('Mass change (m w.e. yr$^{-1}$)'); ax.set_xlabel('Time (hydrological years plotted at their mid-point)')
    ax.set_title('(b) Data-group solutions and regional consensus (±1σ)'); ax.legend(frameon=False, fontsize=8, ncol=2)
    fig.tight_layout(); fig.savefig(os.path.join(IMG, fname), dpi=150); plt.close(fig)

plot_region_workflow(1, 'fig3_workflow_alaska.png')

# ---------------------------------------------------------------- Fig 4: regional small multiples (hydro years, per group)
fig, axs = plt.subplots(5, 4, figsize=(15, 16), sharex=True)
for k, rid in enumerate(range(1, 20)):
    ax = axs.flat[k]; r = res[rid]; x = np.where(r['starts'] + 1 <= 2024.3, r['starts'] + 0.5, np.nan)
    for g, v in r['groups'].items():
        ax.plot(x, v['mwe'], color=COL[g], lw=1.1, alpha=0.9)
    ax.fill_between(x, r['mwe'] - r['err'], r['mwe'] + r['err'], color='0.6', alpha=0.4)
    ax.plot(x, r['mwe'], 'k', lw=1.6)
    oh = pd.read_csv(os.path.join(L.RES, 'hydrological_years', os.path.basename(dirs[rid]) + '.csv'))
    ax.plot((oh.start_dates + oh.end_dates) / 2, oh.combined_mwe, color='orange', lw=1, ls='--')
    ax.axhline(0, color='0.7', lw=0.6)
    ax.set_xlim(1999.5, 2024.5)
    ax.set_title(f'{rid}. {L.REGION_NAMES[rid]}', fontsize=9)
    if k % 4 == 0:
        ax.set_ylabel('m w.e. yr$^{-1}$')
ax = axs.flat[19]; ax.axis('off')
for g in ['altimetry', 'gravimetry', 'demdiff_glac']:
    ax.plot([], [], color=COL[g], label=LAB[g])
ax.plot([], [], 'k', lw=1.6, label='This study: consensus (±1σ shaded)')
ax.plot([], [], color='orange', ls='--', label='GlaMBIE (2024) published consensus')
ax.legend(frameon=False, loc='center', fontsize=9)
fig.suptitle('Regional specific mass change per hydrological year: data groups and consensus', y=0.995, fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig4_regional_timeseries.png'), dpi=130); plt.close(fig)

# ---------------------------------------------------------------- Fig 5: global annual + cumulative
g = glob_[(glob_.start_dates >= 2000) & (glob_.start_dates <= 2023)].copy()
o = og[(og.start_dates >= 2000) & (og.start_dates <= 2023)]
fig, axs = plt.subplots(2, 2, figsize=(12, 8))
ax = axs[0, 0]
ax.bar(g.start_dates + 0.5, g['gt'], width=0.7, color='#3b6fb6', yerr=g.gt_err, capsize=2, label='This study (±1σ)')
ax.plot(o.start_dates + 0.5, o.combined_gt, 'o-', color='orange', ms=3, lw=1, label='GlaMBIE (2024)')
ax.set_ylabel('Mass change (Gt yr$^{-1}$)'); ax.set_title('(a) Global annual glacier mass change (calendar years)')
ax.legend(frameon=False)
ax = axs[0, 1]
ax.bar(g.start_dates + 0.5, g.mwe, width=0.7, color='#6a9fd8', yerr=g.mwe_err, capsize=2, label='This study')
ax.plot(o.start_dates + 0.5, o.combined_mwe, 'o-', color='orange', ms=3, lw=1, label='GlaMBIE (2024)')
ax.set_ylabel('Specific mass change (m w.e. yr$^{-1}$)'); ax.set_title('(b) Global specific mass change')
ax.legend(frameon=False)
ax = axs[1, 0]
cum = np.r_[0, np.cumsum(g['gt'])]; cerr = np.r_[0, np.sqrt(np.cumsum(g.gt_err ** 2))]
t = np.r_[2000, g.end_dates]
ax.fill_between(t, cum - cerr, cum + cerr, color='#3b6fb6', alpha=0.25)
ax.plot(t, cum, color='#3b6fb6', lw=2, label='This study')
ocum = np.r_[0, np.cumsum(o.combined_gt)]; ocerr = np.r_[0, np.sqrt(np.cumsum(o.combined_gt_errors ** 2))]
ax.fill_between(t, ocum - ocerr, ocum + ocerr, color='orange', alpha=0.15)
ax.plot(t, ocum, color='orange', lw=1.5, ls='--', label='GlaMBIE (2024)')
ax.set_ylabel('Cumulative mass change (Gt)'); ax.set_title('(c) Cumulative global mass change since 1 Jan 2000')
sec = ax.secondary_yaxis('right', functions=(lambda v: -v / 362.5, lambda v: -v * 362.5))
sec.set_ylabel('Sea-level contribution (mm)')
ax.legend(frameon=False, loc='lower left')
ax = axs[1, 1]
sr = pd.read_csv(os.path.join(OUT, 'summary_rates_2000_2023.csv'))
sr = sr[sr.region_id > 0].sort_values('cum_gt')
ax.barh([f'{r.region_id}. {r.region}' for r in sr.itertuples()], -sr.cum_gt, xerr=sr.cum_gt_err, color='#c44e52', capsize=2)
ax.invert_yaxis(); ax.set_xlabel('Cumulative mass loss 2000–2023 (Gt)'); ax.set_title('(d) Regional contributions to the global loss')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig5_global_timeseries.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 6: regional mean rates (mwe and Gt)
sr = pd.read_csv(os.path.join(OUT, 'summary_rates_2000_2023.csv'))
sr = sr[sr.region_id > 0]
cmpreg = pd.read_csv(os.path.join(OUT, 'compare_official_regional.csv'))
fig, axs = plt.subplots(1, 2, figsize=(12, 5.5), sharey=True)
y = np.arange(19)
ax = axs[0]
ax.barh(y - 0.2, sr.mean_mwe_yr, height=0.4, xerr=sr.mean_mwe_yr_err, color='#3b6fb6', label='This study', capsize=2)
ax.barh(y + 0.2, cmpreg.off_mean_mwe, height=0.4, color='orange', label='GlaMBIE (2024)')
ax.set_yticks(y); ax.set_yticklabels([f'{i}. {L.REGION_NAMES[i]}' for i in sr.region_id]); ax.invert_yaxis()
ax.set_xlabel('Mean specific mass change 2000–2023 (m w.e. yr$^{-1}$)'); ax.legend(frameon=False)
ax.set_title('(a) Specific mass-change rate')
ax = axs[1]
ax.barh(y - 0.2, sr.mean_gt_yr, height=0.4, xerr=sr.mean_gt_yr_err, color='#3b6fb6', capsize=2)
ax.barh(y + 0.2, cmpreg.off_mean_gt, height=0.4, color='orange')
ax.set_xlabel('Mean mass change 2000–2023 (Gt yr$^{-1}$)'); ax.set_title('(b) Total mass-change rate')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig6_regional_rates.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 7: validation vs official
ann = pd.read_csv(os.path.join(OUT, 'compare_official_annual.csv'))
fig, axs = plt.subplots(1, 3, figsize=(15, 4.8))
ax = axs[0]
sc = ax.scatter(ann.off_mwe, ann.ours_mwe, c=ann.region_id, cmap='tab20', s=10)
lim = [-4, 1.5]; ax.plot(lim, lim, 'k-', lw=0.8); ax.set_xlim(lim); ax.set_ylim(lim)
r_ = np.corrcoef(ann.off_mwe, ann.ours_mwe)[0, 1]; rm = np.sqrt(np.mean((ann.off_mwe - ann.ours_mwe) ** 2))
ax.set_xlabel('GlaMBIE (2024) (m w.e. yr$^{-1}$)'); ax.set_ylabel('This study (m w.e. yr$^{-1}$)')
ax.set_title(f'(a) Regional annual values (n={len(ann)}), r={r_:.3f}, RMSD={rm:.2f}')
ax = axs[1]
ax.errorbar(cmpreg.off_mean_gt, cmpreg.ours_mean_gt, yerr=sr.mean_gt_yr_err.values, fmt='o', ms=4, color='#3b6fb6')
for rr in cmpreg.itertuples():
    ax.annotate(str(rr.region_id), (rr.off_mean_gt, rr.ours_mean_gt), fontsize=7, xytext=(3, 3), textcoords='offset points')
lim = [-65, 2]; ax.plot(lim, lim, 'k-', lw=0.8); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('GlaMBIE (2024) mean 2000–2023 (Gt yr$^{-1}$)'); ax.set_ylabel('This study (Gt yr$^{-1}$)')
ax.set_title('(b) Regional mean rates')
ax = axs[2]
gm = pd.read_csv(os.path.join(OUT, 'compare_official_global_annual.csv'))
ax.errorbar(gm.combined_gt, gm['gt'], xerr=gm.combined_gt_errors, yerr=gm.gt_err, fmt='o', ms=4, color='#3b6fb6', alpha=0.8)
for rr in gm.itertuples():
    ax.annotate(str(int(rr.start_dates))[2:], (rr.combined_gt, rr.gt), fontsize=6.5, xytext=(2, 2), textcoords='offset points')
lim = [-650, -50]; ax.plot(lim, lim, 'k-', lw=0.8); ax.set_xlim(lim); ax.set_ylim(lim)
r2 = np.corrcoef(gm.combined_gt, gm['gt'])[0, 1]
ax.set_xlabel('GlaMBIE (2024) global (Gt yr$^{-1}$)'); ax.set_ylabel('This study global (Gt yr$^{-1}$)')
ax.set_title(f'(c) Global annual values, r={r2:.3f}')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig7_validation_official.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 8: hybrid comparison
hyb = pd.read_csv(os.path.join(OUT, 'validation_hybrid_regional.csv'))
gh = pd.read_csv(os.path.join(OUT, 'validation_hybrid_global.csv'))
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
ax = axs[0]
mk = {'DUS-combined': 'o', 'Huss': 's', 'ArcticInSituvGRACE': '^', 'Box2018': 'v', 'Colgan2015': 'D', 'Miles2021': 'P',
      'Iceland-mb-group': 'X'}
for key, m in mk.items():
    s = hyb[hyb.dataset.str.startswith(key)]
    ax.scatter(s.hybrid_mean, s.ours_mean, marker=m, s=25, label=key, alpha=0.8)
lim = [-1.2, 0.05]; ax.plot(lim, lim, 'k-', lw=0.8); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('Hybrid estimate, mean over overlap (m w.e. yr$^{-1}$)'); ax.set_ylabel('This study (m w.e. yr$^{-1}$)')
ax.legend(frameon=False, fontsize=7); ax.set_title('(a) Regional mean rates vs. hybrid estimates (not used)')
ax = axs[1]
ax.fill_between(gh.start_dates + 0.5, gh['gt'] - gh.gt_err, gh['gt'] + gh.gt_err, color='#3b6fb6', alpha=0.25)
ax.plot(gh.start_dates + 0.5, gh['gt'], color='#3b6fb6', lw=2, label='This study (±1σ)')
if 'DUS-combined_gt' in gh:
    ax.plot(gh.start_dates + 0.5, gh['DUS-combined_gt'], 'o-', color='#9467bd', ms=3, lw=1, label='Dussaillant et al. (hybrid)')
if 'Huss_gt' in gh:
    s = gh[gh.start_dates <= 2020]
    ax.plot(s.start_dates + 0.5, s['Huss_gt'], 's-', color='#8c564b', ms=3, lw=1, label='Huss et al. (hybrid)')
ax.set_ylabel('Global mass change (Gt yr$^{-1}$)'); ax.set_title('(b) Global series vs. hybrid estimates')
ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig8_validation_hybrid.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 9: LOGO + inter-group offsets
logo = pd.read_csv(os.path.join(OUT, 'validation_logo.csv'))
fig, axs = plt.subplots(1, 2, figsize=(12, 4.6))
ax = axs[0]
bins = np.linspace(-4, 4, 33)
for gname in ['altimetry', 'gravimetry', 'demdiff_glac']:
    s = logo[logo.group == gname]
    ax.hist(s.z, bins=bins, histtype='step', lw=1.6, color=COL[gname], density=True, label=f'{LAB[gname]} (n={len(s)})')
zz = np.linspace(-4, 4, 200); ax.plot(zz, np.exp(-zz ** 2 / 2) / np.sqrt(2 * np.pi), 'k--', lw=1, label='N(0,1)')
ax.set_xlabel('Normalised difference z (withheld group − other groups)'); ax.set_ylabel('Density')
ax.set_title(f'(a) Leave-one-group-out consistency: SD(z)={logo.z.std():.2f}, |z|<1: {100*(logo.z.abs()<1).mean():.0f}%')
ax.legend(frameon=False, fontsize=7.5)
ax = axs[1]
cg = pd.read_csv(os.path.join(OUT, 'hydrological_years', os.listdir(os.path.join(OUT, 'hydrological_years'))[0]))
rows = []
for rid, r in res.items():
    G = r['groups']
    if 'demdiff_glac' not in G:
        continue
    for gname in ['altimetry', 'gravimetry']:
        if gname in G:
            d = G[gname]['mwe'] - G['demdiff_glac']['mwe']
            ok = np.isfinite(d)
            if ok.sum() >= 3:
                se = np.sqrt(np.nanmean(G[gname]['err'][ok] ** 2 + G['demdiff_glac']['err'][ok] ** 2) / ok.sum())
                rows.append(dict(rid=rid, g=gname, d=np.mean(d[ok]), se=se))
dd = pd.DataFrame(rows)
for k, gname in enumerate(['altimetry', 'gravimetry']):
    s = dd[dd.g == gname]
    ax.errorbar(s.rid + (k - 0.5) * 0.3, s.d, yerr=s.se, fmt='o', color=COL[gname], label=f'{LAB[gname]} − DEM/glac.', capsize=2)
ax.axhline(0, color='k', lw=0.7); ax.set_xticks(range(1, 20))
ax.set_xlabel('RGI region'); ax.set_ylabel('Mean difference (m w.e. yr$^{-1}$)')
ax.set_title('(b) Mean offset relative to DEM diff. + glaciological')
ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig9_consistency.png'), dpi=150); plt.close(fig)
dd.to_csv(os.path.join(OUT, 'group_offsets_vs_demdiff.csv'), index=False)

# ---------------------------------------------------------------- Fig 10: sensitivity + literature
sens = pd.read_csv(os.path.join(OUT, 'sensitivity_global.csv'))
lit = pd.read_csv(os.path.join(OUT, 'validation_literature.csv'))
fig, axs = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw=dict(width_ratios=[1.2, 1]))
ax = axs[0]
y = np.arange(len(sens))
ax.barh(y, sens.mean_gt, xerr=sens.total_err / 24, color=['k'] + ['#7f9fc6'] * (len(sens) - 1), capsize=2)
ax.axvline(sens.mean_gt.iloc[0], color='k', lw=0.7, ls='--')
ax.axvline(og[(og.start_dates >= 2000) & (og.start_dates <= 2023)].combined_gt.mean(), color='orange', lw=1.2, label='GlaMBIE (2024)')
ax.set_yticks(y); ax.set_yticklabels(sens.variant, fontsize=8); ax.invert_yaxis()
ax.set_xlim(-300, -220); ax.set_xlabel('Mean global mass change 2000–2023 (Gt yr$^{-1}$)')
ax.set_title('(a) Sensitivity to methodological choices'); ax.legend(frameon=False, fontsize=8)
ax = axs[1]
y = np.arange(len(lit))
ax.errorbar(lit.ref_gt_yr, y - 0.15, xerr=lit.ref_err_1sigma, fmt='s', color='0.4', label='Published estimate (1σ)', capsize=2)
ax.errorbar(lit.ours_gt_yr, y + 0.15, xerr=lit.ours_err, fmt='o', color='#3b6fb6', label='This study (1σ)', capsize=2)
ax.plot(lit.glambie2024_gt_yr, y, 'x', color='orange', label='GlaMBIE (2024)')
ax.set_yticks(y); ax.set_yticklabels(lit.reference, fontsize=8); ax.invert_yaxis()
ax.set_xlabel('Global mass change (Gt yr$^{-1}$)'); ax.set_title('(b) Comparison with literature estimates')
ax.legend(frameon=False, fontsize=7.5, loc='lower left')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig10_sensitivity_literature.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 11: acceleration by region
rt = pd.read_csv(os.path.join(OUT, 'regional_trends.csv'))
fig, axs = plt.subplots(1, 2, figsize=(12, 5))
ax = axs[0]
y = np.arange(19)
ax.barh(y - 0.2, rt.p1_mwe, height=0.4, color='#9ecae1', label='2000–2011')
ax.barh(y + 0.2, rt.p2_mwe, height=0.4, color='#08519c', label='2012–2023')
ax.set_yticks(y); ax.set_yticklabels([f'{i}. {L.REGION_NAMES[i]}' for i in rt.region_id]); ax.invert_yaxis()
ax.set_xlabel('Mean specific mass change (m w.e. yr$^{-1}$)'); ax.legend(frameon=False); ax.set_title('(a) Two-period comparison')
ax = axs[1]
ax.errorbar(rt.slope_mwe * 10, y, xerr=rt.se_mwe * 10 * 1.96, fmt='o', color='#08519c', capsize=2)
ax.axvline(0, color='k', lw=0.7)
ax.set_yticks(y); ax.set_yticklabels([]); ax.invert_yaxis()
ax.set_xlabel('Linear trend of annual mass change (m w.e. yr$^{-1}$ per decade, 95% CI)')
ax.set_title('(b) Trend in annual mass change (negative = accelerating loss)')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig11_acceleration.png'), dpi=150); plt.close(fig)

# ---------------------------------------------------------------- Fig 12: uncertainty budget
vs = json.load(open(os.path.join(OUT, 'validation_summary.json')))['variance_share']
fig, ax = plt.subplots(figsize=(7, 4.5))
items = sorted(vs.items(), key=lambda kv: -kv[1])
ax.barh([k for k, _ in items], [100 * v for _, v in items], color='#8172b2'); ax.invert_yaxis()
ax.set_xlabel('Share of global error variance, cumulative 2000–2023 (%)')
ax.set_title('Contribution of regions to the global uncertainty')
fig.tight_layout(); fig.savefig(os.path.join(IMG, 'fig12_uncertainty_budget.png'), dpi=150); plt.close(fig)
print('figures written:', sorted(os.listdir(IMG)))
