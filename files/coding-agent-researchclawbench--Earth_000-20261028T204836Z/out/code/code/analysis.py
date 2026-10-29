import sys, json; sys.path.insert(0, '/work/code')
import numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import glambie_core as gc
from glambie_core import REGIONS, D
from combine import *
from run_all import run, global_series
OUT = '/work/outputs'; IMG = '/work/report/images'
import os; os.makedirs(IMG, exist_ok=True)
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'axes.grid': True,
                     'grid.color': '#e6e6e6', 'grid.linewidth': 0.6, 'figure.dpi': 130, 'savefig.bbox': 'tight'})
C = dict(mine='#1f4e8c', off='#d95f02', alt='#009e73', grav='#cc79a7', dem='#56b4e9', gray='#777777')
SHORT = {1:'Alaska',2:'W Canada & US',3:'Arctic Canada N',4:'Arctic Canada S',5:'Greenland per.',6:'Iceland',7:'Svalbard',
         8:'Scandinavia',9:'Russian Arctic',10:'North Asia',11:'Central Europe',12:'Caucasus & M. East',13:'Central Asia',
         14:'South Asia W',15:'South Asia E',16:'Low latitudes',17:'Southern Andes',18:'New Zealand',19:'Antarctic & Subant.'}
GT_PER_MM = 362.5
df = pd.read_csv(f'{OUT}/regional_calendar_years.csv'); g = pd.read_csv(f'{OUT}/global_calendar_years.csv')
off = {rid: pd.read_csv(f"{D}/results/calendar_years/{rid}_{REGIONS[rid]}.csv") for rid in REGIONS}
offg = pd.read_csv(D+'/results/calendar_years/0_global.csv')
yrs = g.start.values + 0.5   # mid-year

def period_stats(d, y0, y1):
    """mean annual rate over [y0,y1) calendar years with trend-correlated + random error handling, per region then global."""
    m = d[(d.start >= y0) & (d.start < y1)]
    N = m.groupby('region_id').size().iloc[0]
    rows = []
    for rid, x in m.groupby('region_id'):
        tr = x.gt_err_trend.mean(); rnd = np.sqrt(np.mean(np.maximum(x.gt_err**2 - x.gt_err_trend**2, 0))/N)
        rows.append(dict(region_id=rid, gt=x['gt'].mean(), err=np.sqrt(tr**2+rnd**2), area=x.area_km2.mean()))
    r = pd.DataFrame(rows)
    gl = dict(region_id=0, gt=r['gt'].sum(), err=np.sqrt((r.err**2).sum()), area=r.area.sum())
    r = pd.concat([r, pd.DataFrame([gl])], ignore_index=True)
    r['mwe'] = r['gt']*1000/r.area; r['mwe_err'] = r.err*1000/r.area
    return r

# ---------- Tables of period stats
periods = [(2000, 2024), (2000, 2012), (2012, 2024), (2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020), (2020, 2024)]
tabs = {}
for p in periods:
    t = period_stats(df, *p); t['period'] = f'{p[0]}-{p[1]-1}'; tabs[p] = t
allp = pd.concat(tabs.values()); allp.to_csv(f'{OUT}/period_rates.csv', index=False)
def offper(y0, y1):
    gt = {rid: off[rid].combined_gt[(off[rid].start_dates >= y0) & (off[rid].start_dates < y1)].mean() for rid in REGIONS}
    gt[0] = offg.combined_gt[(offg.start_dates >= y0) & (offg.start_dates < y1)].mean(); return gt
main = tabs[(2000, 2024)].set_index('region_id'); o_all = offper(2000, 2024)
tbl = pd.DataFrame({'region': [SHORT.get(i, 'Global') for i in main.index], 'area_km2': main.area.round(0),
                    'gt_yr': main['gt'].round(1), 'gt_err': main.err.round(1), 'mwe_yr': main.mwe.round(3), 'mwe_err': main.mwe_err.round(3),
                    'official_gt_yr': [round(o_all[i], 1) for i in main.index]}, index=main.index)
tbl['diff_gt_yr'] = (tbl['gt_yr'] - tbl.official_gt_yr).round(1)
tbl.to_csv(f'{OUT}/table_regional_2000_2023.csv'); print(tbl.to_string())
pt = pd.DataFrame({p: tabs[p].set_index('region_id').loc[0, ['gt', 'err', 'mwe']] for p in periods}).T; print(pt.round(2))
pt.to_csv(f'{OUT}/table_global_periods.csv')

# ---------- Fig 1 data overview: inventory
inv = []
for rid in REGIONS:
    for s in gc.load_solutions(rid):
        inv.append(dict(rid=rid, src=s['src'], name=s['name'], s0=s['s'].min(), s1=s['e'].max(), n=len(s['s']), res=np.median(s['e']-s['s'])))
inv = pd.DataFrame(inv); inv.to_csv(f'{OUT}/inventory.csv', index=False)
ct = inv.pivot_table(index='rid', columns='src', values='name', aggfunc='count', fill_value=0)[['glaciological', 'demdiff', 'altimetry', 'gravimetry', 'combined']]
fig, ax = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw={'width_ratios': [1, 1.25]})
im = ax[0].imshow(ct.values, cmap='Blues', aspect='auto', vmin=0, vmax=8)
ax[0].set_xticks(range(5)); ax[0].set_xticklabels(['Glaciol.', 'DEM diff.', 'Altimetry', 'Gravimetry', 'Combined'], rotation=30, ha='right')
ax[0].set_yticks(range(19)); ax[0].set_yticklabels([f'{i} {SHORT[i]}' for i in ct.index]); ax[0].grid(False)
for i in range(19):
    for j in range(5): ax[0].text(j, i, int(ct.values[i, j]), ha='center', va='center', color='white' if ct.values[i, j] > 4 else '#333', fontsize=8)
ax[0].set_title('(a) Number of submitted solutions (n=%d)' % len(inv))
cols = {'glaciological': C['dem'], 'demdiff': '#0072b2', 'altimetry': C['alt'], 'gravimetry': C['grav'], 'combined': C['gray']}
for k, (src, grp) in enumerate(inv.groupby('src')):
    pass
cov = inv.groupby('src').apply(lambda d: pd.Series({'min': d.s0.min(), 'p10': d.s0.quantile(.1)}), include_groups=False)
order = ['glaciological', 'combined', 'demdiff', 'altimetry', 'gravimetry']
for k, src in enumerate(order):
    d = inv[inv.src == src]
    cnt = np.array([((d.s0 <= t) & (d.s1 >= t + 1)).sum() for t in np.arange(1990, 2025)])
    ax[1].bar(np.arange(1990, 2025) + .5, cnt, bottom=0, width=0.0, color='none')
    ax[1].plot(np.arange(1990, 2025) + .5, cnt, color=cols[src], lw=1.8, label=src)
ax[1].axvspan(2000, 2024, color='#f3f3f3', zorder=0); ax[1].set_xlim(1990, 2025)
ax[1].set_xlabel('Year'); ax[1].set_ylabel('Solutions covering the full year'); ax[1].legend(frameon=False, ncol=2)
ax[1].set_title('(b) Temporal coverage of submissions (shaded = GlaMBIE period)')
fig.tight_layout(); fig.savefig(f'{IMG}/fig1_data_overview.png'); plt.close(fig)

# ---------- Fig 2 examples of group series & combination (Alaska, Svalbard, Central Asia, Southern Andes)
store = pd.read_pickle(f'{OUT}/store_calendar.pkl')
fig, axs = plt.subplots(2, 2, figsize=(11, 6.6), sharex=True)
for ax, rid in zip(axs.ravel(), [1, 7, 13, 17]):
    r = store[rid]; x = 2000.5 + np.arange(24)
    for gname, col, lab in [('demdiff_and_glaciological', C['dem'], 'DEM+glaciol.'), ('altimetry', C['alt'], 'Altimetry'), ('gravimetry', C['grav'], 'Gravimetry')]:
        if gname in r['groups']:
            ax.plot(x, r['groups'][gname]['y'], color=col, lw=1.1, marker='o', ms=2.5, label=lab, alpha=.9)
    m = r['mu']; e = r['err']
    ax.fill_between(x, m-e, m+e, color=C['mine'], alpha=.2, lw=0)
    ax.plot(x, m, color=C['mine'], lw=2.2, label='Combined (this study)')
    ax.plot(x, off[rid].combined_mwe, color=C['off'], lw=1.4, ls='--', label='Official GlaMBIE')
    ax.set_title(f'{rid} {SHORT[rid]}'); ax.set_ylabel('m w.e. yr$^{-1}$'); ax.axhline(0, color='k', lw=.5)
axs[0, 0].legend(frameon=False, fontsize=7.5, ncol=2, loc='lower left')
fig.tight_layout(); fig.savefig(f'{IMG}/fig2_group_combination_examples.png'); plt.close(fig)

# ---------- Fig 3 all regions mwe vs official
fig, axs = plt.subplots(5, 4, figsize=(13, 13), sharex=True)
for ax, rid in zip(axs.ravel(), REGIONS):
    m = df[df.region_id == rid]
    ax.fill_between(yrs, m.mwe-m.mwe_err, m.mwe+m.mwe_err, color=C['mine'], alpha=.2, lw=0)
    ax.plot(yrs, m.mwe, color=C['mine'], lw=1.8)
    o = off[rid]; ax.plot(yrs, o.combined_mwe, color=C['off'], lw=1.2, ls='--')
    rm = np.sqrt(np.mean((m.mwe.values-o.combined_mwe.values)**2)); ax.axhline(0, color='k', lw=.4)
    ax.set_title(f'{rid} {SHORT[rid]}  (RMSD {rm:.2f})', fontsize=8.5)
ax = axs.ravel()[-1]; ax.axis('off')
ax.plot([], [], color=C['mine'], lw=2, label='This study ± 1σ'); ax.plot([], [], color=C['off'], ls='--', label='Official GlaMBIE'); ax.legend(frameon=False, loc='center')
for ax in axs[:, 0]: ax.set_ylabel('m w.e. yr$^{-1}$')
fig.tight_layout(); fig.savefig(f'{IMG}/fig3_regional_timeseries.png'); plt.close(fig)

# ---------- Fig 4 global series & cumulative
fig, ax = plt.subplots(1, 3, figsize=(13, 4.2))
ax[0].fill_between(yrs, g['gt']-g.gt_err, g['gt']+g.gt_err, color=C['mine'], alpha=.2, lw=0)
ax[0].plot(yrs, g['gt'], color=C['mine'], lw=2, label='This study ± 1σ')
ax[0].fill_between(yrs, offg.combined_gt-offg.combined_gt_errors, offg.combined_gt+offg.combined_gt_errors, color=C['off'], alpha=.12, lw=0)
ax[0].plot(yrs, offg.combined_gt, color=C['off'], ls='--', lw=1.4, label='Official GlaMBIE ± 1σ')
ax[0].set_ylabel('Gt yr$^{-1}$'); ax[0].set_title('(a) Global annual mass change'); ax[0].legend(frameon=False, fontsize=8)
cum = np.cumsum(g['gt']); cumo = np.cumsum(offg.combined_gt)
ax[1].plot(g.end, cum, color=C['mine'], lw=2, label='This study'); ax[1].plot(offg.end_dates, cumo, color=C['off'], ls='--', label='Official')
ax[1].set_title('(b) Cumulative mass change 2000–2023'); ax[1].set_ylabel('Gt'); ax[1].legend(frameon=False)
sec = ax[1].secondary_yaxis('right', functions=(lambda v: -v/GT_PER_MM, lambda v: -v*GT_PER_MM)); sec.set_ylabel('Sea-level equivalent (mm)')
ax[2].bar(yrs, g.mwe, width=.8, color=C['mine'], alpha=.85); ax[2].errorbar(yrs, g.mwe, g.mwe_err, fmt='none', ecolor='#333', lw=.8)
ax[2].set_title('(c) Global specific mass change'); ax[2].set_ylabel('m w.e. yr$^{-1}$')
for a in ax: a.set_xlabel('Calendar year')
fig.tight_layout(); fig.savefig(f'{IMG}/fig4_global.png'); plt.close(fig)

# ---------- Fig 5 regional contributions
mm = main.drop(0).copy(); mm['name'] = [SHORT[i] for i in mm.index]; mm['off'] = [o_all[i] for i in mm.index]
mm = mm.sort_values('gt')
fig, ax = plt.subplots(1, 2, figsize=(11.5, 5))
yy = np.arange(len(mm)); ax[0].barh(yy+.2, mm['gt'], .4, xerr=mm.err, color=C['mine'], label='This study', error_kw=dict(lw=.8))
ax[0].barh(yy-.2, mm.off, .4, color=C['off'], alpha=.8, label='Official'); ax[0].set_yticks(yy); ax[0].set_yticklabels(mm.name)
ax[0].set_xlabel('Gt yr$^{-1}$ (2000–2023 mean)'); ax[0].set_title('(a) Regional mass change'); ax[0].legend(frameon=False)
mm2 = mm.sort_values('mwe'); yy = np.arange(len(mm2)); ax[1].barh(yy, mm2.mwe, color=C['mine'], xerr=mm2.mwe_err, error_kw=dict(lw=.8))
ax[1].set_yticks(yy); ax[1].set_yticklabels(mm2.name); ax[1].set_xlabel('m w.e. yr$^{-1}$'); ax[1].set_title('(b) Regional specific mass change')
fig.tight_layout(); fig.savefig(f'{IMG}/fig5_regional_rates.png'); plt.close(fig)

# ---------- Fig 6 validation vs official
fig, ax = plt.subplots(1, 3, figsize=(13, 4.2))
x = np.concatenate([off[r].combined_mwe.values for r in REGIONS]); y = df.sort_values(['region_id', 'start']).mwe.values
ax[0].scatter(x, y, s=8, alpha=.5, color=C['mine']); lim = [-3.5, 1.5]; ax[0].plot(lim, lim, 'k', lw=.6); ax[0].set_xlim(lim); ax[0].set_ylim(lim)
r2 = np.corrcoef(x, y)[0, 1]**2; ax[0].set_title(f'(a) Regional annual specific mass change\n(n={len(x)}, $R^2$={r2:.2f}, RMSD={np.sqrt(np.mean((x-y)**2)):.2f} m w.e.)', fontsize=9)
ax[0].set_xlabel('Official (m w.e.)'); ax[0].set_ylabel('This study (m w.e.)')
xo = np.concatenate([off[r].combined_gt.values for r in REGIONS]); yo = df.sort_values(['region_id', 'start'])['gt'].values
ax[1].scatter(xo, yo, s=8, alpha=.5, color=C['mine']); l2 = [-250, 100]; ax[1].plot(l2, l2, 'k', lw=.6); ax[1].set_xlim(l2); ax[1].set_ylim(l2)
ax[1].set_title(f'(b) Regional annual mass change\n($R^2$={np.corrcoef(xo, yo)[0, 1]**2:.2f}, RMSD={np.sqrt(np.mean((xo-yo)**2)):.1f} Gt)', fontsize=9)
ax[1].set_xlabel('Official (Gt yr$^{-1}$)'); ax[1].set_ylabel('This study (Gt yr$^{-1}$)')
ax[2].scatter(offg.combined_gt, g['gt'], color=C['mine'], s=18); l3 = [-600, -50]; ax[2].plot(l3, l3, 'k', lw=.6); ax[2].set_xlim(l3); ax[2].set_ylim(l3)
ax[2].set_title(f'(c) Global annual mass change\n(r={np.corrcoef(offg.combined_gt, g["gt"])[0, 1]:.2f}, RMSD={np.sqrt(np.mean((offg.combined_gt-g["gt"])**2)):.0f} Gt)', fontsize=9)
ax[2].set_xlabel('Official (Gt yr$^{-1}$)'); ax[2].set_ylabel('This study (Gt yr$^{-1}$)')
fig.tight_layout(); fig.savefig(f'{IMG}/fig6_validation.png'); plt.close(fig)

# ---------- hydrological group-level validation table + figure
dh = pd.read_csv(f'{OUT}/regional_hydrological_years.csv')
rows = []
for rid in REGIONS:
    o = gc.official(rid); y0 = o.start_dates.iloc[0]; T = len(o)
    r = run_region(rid, y0, T, allowed_groups(rid))
    row = dict(rid=rid)
    d = r['mu']-o.combined_mwe.values; row.update(comb_rmsd=np.sqrt(np.nanmean(d**2)), comb_bias=np.nanmean(d), comb_r=np.corrcoef(r['mu'], o.combined_mwe)[0, 1])
    for gname, short in [('demdiff_and_glaciological', 'dem'), ('altimetry', 'alt'), ('gravimetry', 'grav')]:
        if gname in r['groups']:
            a = r['groups'][gname]['y']; b = o[gname+'_mwe'].values; ok = np.isfinite(a) & np.isfinite(b)
            if ok.sum() > 3:
                row[short+'_rmsd'] = np.sqrt(np.mean((a[ok]-b[ok])**2)); row[short+'_r'] = np.corrcoef(a[ok], b[ok])[0, 1]; row[short+'_bias'] = np.mean(a[ok]-b[ok])
    rows.append(row)
hv = pd.DataFrame(rows).set_index('rid'); hv.to_csv(f'{OUT}/validation_hydrological.csv'); print(hv.round(2).to_string())
print('medians', hv.median().round(3).to_dict())
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for short, col, lab in [('dem', C['dem'], 'DEM + glaciological'), ('alt', C['alt'], 'Altimetry'), ('grav', C['grav'], 'Gravimetry')]:
    v = hv[short+'_rmsd'].dropna(); ax[0].scatter(v.index, v.values, color=col, s=28, label=lab)
ax[0].scatter(hv.index, hv.comb_rmsd, color='k', marker='_', s=120, label='Combined')
ax[0].set_xticks(hv.index); ax[0].set_xlabel('GlaMBIE region'); ax[0].set_ylabel('RMSD vs official (m w.e. yr$^{-1}$)'); ax[0].legend(frameon=False, fontsize=8); ax[0].set_title('(a) Group and combined series, hydrological years')
ax[1].bar(hv.index, hv.comb_bias, color=np.where(hv.comb_bias > 0, '#b2182b', '#2166ac')); ax[1].set_xticks(hv.index); ax[1].set_xlabel('GlaMBIE region')
ax[1].set_ylabel('Mean bias, combined (m w.e. yr$^{-1}$)'); ax[1].set_title('(b) Mean bias of combined series vs official'); ax[1].axhline(0, color='k', lw=.6)
fig.tight_layout(); fig.savefig(f'{IMG}/fig7_validation_groups.png'); plt.close(fig)

# ---------- Fig 8 inter-method comparison of rates 2003-2019 (hydrological, common windows)
rows = []
for rid in REGIONS:
    r = store[rid]
    for gname, gg in r['groups'].items():
        rows.append(dict(rid=rid, g=gname, y=gg['y'], na=gg['na']))
def paired(rid, gname, a, b):
    """mean rates of group gname and of the DEM+glaciological group over the years a..b-1 where gname is finite"""
    R = store[rid]['groups']
    if gname not in R: return np.nan, np.nan
    y = R[gname]['y'][a-2000:b-2000]; d = R['demdiff_and_glaciological']['y'][a-2000:b-2000]
    ok = np.isfinite(y) & np.isfinite(d) & (R[gname]['na'][a-2000:b-2000] > 0)
    return (y[ok].mean(), d[ok].mean()) if ok.sum() >= 4 else (np.nan, np.nan)
pg = [paired(r, 'gravimetry', 2003, 2020) for r in REGIONS]; pa = [paired(r, 'altimetry', 2011, 2019) for r in REGIONS]
cmpd = pd.DataFrame({'rid': list(REGIONS), 'grav': [x[0] for x in pg], 'dem_grav': [x[1] for x in pg], 'alt': [x[0] for x in pa], 'dem_alt': [x[1] for x in pa]})
cmpd['area'] = [df[(df.region_id == r)].area_km2.mean() for r in REGIONS]
fig, ax = plt.subplots(1, 2, figsize=(10, 4.4))
for a, (k, ref, col, lab, ttl) in zip(ax, [('grav', 'dem_grav', C['grav'], 'Gravimetry', '(a) 2003–2019'), ('alt', 'dem_alt', C['alt'], 'Altimetry', '(b) 2011–2018')]):
    v = cmpd.dropna(subset=[k, ref]); a.scatter(v[ref], v[k], color=col, s=np.sqrt(v.area)/4)
    for _, rr in v.iterrows(): a.annotate(SHORT[int(rr.rid)], (rr[ref], rr[k]), fontsize=6.5, xytext=(3, 3), textcoords='offset points')
    lim = [-1.4, 0.2]; a.plot(lim, lim, 'k', lw=.6); a.set_xlim(lim); a.set_ylim(lim); a.set_xlabel('DEM + glaciological group (m w.e. yr$^{-1}$)'); a.set_ylabel(lab + ' group (m w.e. yr$^{-1}$)')
    a.set_title(ttl+f' (n={len(v)}, mean diff {np.mean(v[k]-v[ref]):+.2f})', fontsize=9)
fig.tight_layout(); fig.savefig(f'{IMG}/fig8_intermethod.png'); plt.close(fig)
cmpd.to_csv(f'{OUT}/intermethod_rates.csv', index=False)
print(cmpd.round(2).to_string())

# ---------- Fig 9 sensitivity experiments
def glob_stats(d):
    gg = global_series(d); return gg
exps = {}
def addexp(name, **kw):
    d, _ = run('calendar', **kw); gg = global_series(d); exps[name] = gg
addexp('Base')
addexp('No gravimetry', allow_fn=lambda r: allowed_groups(r)-{'gravimetry'})
addexp('No altimetry', allow_fn=lambda r: allowed_groups(r)-{'altimetry'})
addexp('DEM+glaciol. only', allow_fn=lambda r: {'demdiff_and_glaciological'})
addexp('GRACE in all regions', allow_fn=lambda r: allowed_groups(r)|{'gravimetry'})
addexp('Include Box (GRACE-mixed) series', exclude=())
gc.RHO_CONV = 0.90; addexp('Density 900 kg m$^{-3}$'); gc.RHO_CONV = 0.85
gc.RHO_CONV = 0.80; addexp('Density 800 kg m$^{-3}$'); gc.RHO_CONV = 0.85
srows = []
for k, v in exps.items():
    a = v[(v.start >= 2000)]; r1 = v[(v.start < 2012)]['gt'].mean(); r2 = v[(v.start >= 2012)]['gt'].mean()
    srows.append(dict(experiment=k, mean_2000_2023=a['gt'].mean(), mean_2000_2011=r1, mean_2012_2023=r2, ratio=r2/r1, rmsd_vs_base=np.sqrt(np.mean((a['gt'].values-exps['Base']['gt'].values)**2))))
sens = pd.DataFrame(srows); sens.to_csv(f'{OUT}/sensitivity_global.csv', index=False); print(sens.round(2).to_string())
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.2))
for k, v in exps.items():
    ax[0].plot(yrs, v['gt'], lw=2 if k == 'Base' else 1, color=C['mine'] if k == 'Base' else None, label=k, alpha=1 if k == 'Base' else .8)
ax[0].plot(yrs, offg.combined_gt, 'k--', lw=1.2, label='Official'); ax[0].set_ylabel('Gt yr$^{-1}$'); ax[0].set_title('(a) Global annual mass change'); ax[0].legend(frameon=False, fontsize=6.5, ncol=2)
ss = sens.set_index('experiment'); yy = np.arange(len(ss))
ax[1].barh(yy, ss.mean_2000_2023, color=[C['mine'] if k == 'Base' else '#9aa7b8' for k in ss.index]); ax[1].set_yticks(yy); ax[1].set_yticklabels(ss.index, fontsize=8)
ax[1].axvline(o_all[0], color=C['off'], ls='--', label='Official'); ax[1].set_xlim(-300, -200); ax[1].set_xlabel('Gt yr$^{-1}$, 2000–2023 mean'); ax[1].legend(frameon=False); ax[1].set_title('(b) Sensitivity of the 2000–2023 mean'); ax[1].invert_yaxis()
fig.tight_layout(); fig.savefig(f'{IMG}/fig9_sensitivity.png'); plt.close(fig)

# ---------- Fig 10 acceleration: regional contributions per period (stacked)
pp = [(2000, 2005), (2005, 2010), (2010, 2015), (2015, 2020), (2020, 2024)]
M = np.array([[tabs[p].set_index('region_id').loc[r, 'gt'] for p in pp] for r in REGIONS])
top = [1, 5, 17, 19, 3, 9, 13, 4, 7]
fig, ax = plt.subplots(1, 2, figsize=(11.5, 4.3))
bottom = np.zeros(len(pp)); cm = plt.get_cmap('tab20')
labs = [f'{p[0]}–{p[1]-1}' for p in pp]
rest = M[[i-1 for i in REGIONS if i not in top]].sum(0)
for k, r in enumerate(top):
    ax[0].bar(labs, -M[r-1], bottom=bottom, color=cm(k), label=SHORT[r], width=.65); bottom += -M[r-1]
ax[0].bar(labs, -rest, bottom=bottom, color='#bbbbbb', label='Other', width=.65)
ax[0].set_ylabel('Mass loss (Gt yr$^{-1}$)'); ax[0].legend(frameon=False, fontsize=6.5, ncol=2); ax[0].set_title('(a) Regional contributions to global loss')
mwe_p = np.array([[tabs[p].set_index('region_id').loc[r, 'mwe'] for p in pp] for r in REGIONS])
im = ax[1].imshow(mwe_p, cmap='RdBu', vmin=-1.6, vmax=1.6, aspect='auto'); ax[1].set_xticks(range(len(pp))); ax[1].set_xticklabels(labs, rotation=20)
ax[1].set_yticks(range(19)); ax[1].set_yticklabels([SHORT[r] for r in REGIONS], fontsize=7); ax[1].grid(False)
for i in range(19):
    for j in range(len(pp)): ax[1].text(j, i, f'{mwe_p[i, j]:.2f}', ha='center', va='center', fontsize=6.5)
ax[1].set_title('(b) Specific mass change (m w.e. yr$^{-1}$)'); plt.colorbar(im, ax=ax[1], shrink=.8)
fig.tight_layout(); fig.savefig(f'{IMG}/fig10_periods.png'); plt.close(fig)
pd.DataFrame(mwe_p, index=[SHORT[r] for r in REGIONS], columns=labs).round(3).to_csv(f'{OUT}/table_mwe_5yr.csv')

# global linear trend
t = g.start.values; sl = np.polyfit(t, g['gt'].values, 1)
res = g['gt'].values - np.polyval(sl, t); se = np.sqrt(np.sum(res**2)/(len(t)-2)/np.sum((t-t.mean())**2))
slo = np.polyfit(t, offg.combined_gt.values, 1)
print('trend', sl[0], se, 'official', slo[0])
json.dump(dict(trend_gt_yr2=sl[0], trend_se=se, off_trend=slo[0], cum_gt=float(cum.iloc[-1]), cum_off=float(cumo.iloc[-1]),
               corr_global=float(np.corrcoef(offg.combined_gt, g['gt'])[0, 1])), open(f'{OUT}/misc_stats.json', 'w'))
