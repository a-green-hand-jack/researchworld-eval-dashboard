"""All report figures (PNG) -> /work/report/images"""
import sys, json
sys.path.insert(0, '/work/code')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from glambie_lib import REGIONS, SHORT, reconcile_region

OUT = '/work/outputs'; M = f'{OUT}/main'; R = '/work/data/glambie/results'
IMG = '/work/report/images'
C = dict(DG='#2a78d6', ALT='#eb6834', GRAV='#1baf7a', HYB='#e87ba4', ink='#0b0b0b', off='#8a8984',
         grid='#e6e5e0', text2='#52514e')
GNAME = dict(DG='DEM diff. + glaciological', ALT='Altimetry', GRAV='Gravimetry', HYB='Hybrid')
FULL = {r: ' '.join(w.capitalize() for w in r.split('_')[1:]).replace('Us', 'US').replace('And', 'and') for r in REGIONS}
plt.rcParams.update({'font.size': 9, 'axes.edgecolor': '#9a9993', 'axes.linewidth': 0.6, 'axes.grid': True,
                     'grid.color': C['grid'], 'grid.linewidth': 0.6, 'axes.axisbelow': True, 'axes.spines.top': False,
                     'axes.spines.right': False, 'xtick.color': C['text2'], 'ytick.color': C['text2'],
                     'axes.labelcolor': '#2b2b2a', 'legend.frameon': False, 'figure.dpi': 150, 'savefig.dpi': 170,
                     'savefig.bbox': 'tight'})

cal = {r: pd.read_csv(f'{M}/calendar_{r}.csv', index_col=0).loc[2000:2023] for r in REGIONS}
hyd = {r: pd.read_csv(f'{M}/hydro_{r}.csv') for r in REGIONS}
ga = pd.read_csv(f'{OUT}/global_annual.csv', index_col=0)
og = pd.read_csv(f'{R}/calendar_years/0_global.csv'); og.index = og.start_dates.astype(int)
inv = pd.read_csv(f'{OUT}/input_inventory.csv')
inv['group'] = inv.source.map(dict(glaciological='DG', demdiff='DG', altimetry='ALT', gravimetry='GRAV', combined='HYB'))


def save(fig, name):
    fig.savefig(f'{IMG}/{name}.png'); plt.close(fig); print('saved', name)


# ------------------------------------------------------------ F1 data overview
fig, axs = plt.subplots(1, 2, figsize=(11, 5.2), gridspec_kw=dict(width_ratios=[1, 1.35]))
src_order = ['glaciological', 'demdiff', 'altimetry', 'gravimetry', 'combined']
ct = pd.crosstab(inv.region, inv.source).reindex(index=REGIONS, columns=src_order).fillna(0).astype(int)
ax = axs[0]
im = ax.imshow(ct.values, cmap='Blues', aspect='auto', vmin=0, vmax=ct.values.max() + 1)
for i in range(ct.shape[0]):
    for j in range(ct.shape[1]):
        v = ct.values[i, j]
        ax.text(j, i, str(v) if v else '–', ha='center', va='center', fontsize=8,
                color='white' if v > 4 else '#2b2b2a')
ax.set_xticks(range(len(src_order)), ['Glaciol.', 'DEM diff.', 'Altimetry', 'Gravimetry', 'Hybrid'], rotation=30)
ax.set_yticks(range(len(REGIONS)), [f'{SHORT[r]} – {FULL[r]}' for r in REGIONS], fontsize=7.5)
ax.grid(False)
ax.set_title('a  Solutions per region and method (n = %d)' % len(inv), loc='left', fontsize=10)
ax = axs[1]
years = np.arange(1999, 2025)
for g in ['DG', 'ALT', 'GRAV', 'HYB']:
    sub = inv[inv.group == g]
    cnt = [((sub.t0 <= y + 0.5) & (sub.t1 >= y + 0.5)).sum() for y in years]
    ax.plot(years + 0.5, cnt, color=C[g], lw=2, label=GNAME[g])
ax.set_xlim(1999.5, 2025.5)
ax.set_xlabel('Year'); ax.set_ylabel('Number of solutions covering the year')
ax.set_title('b  Temporal coverage of input solutions', loc='left', fontsize=10)
ax.legend(loc='center left', bbox_to_anchor=(0.0, 0.42))
save(fig, 'fig01_data_overview')

# ------------------------------------------------------------ F2 example regions (group series)
fig, axs = plt.subplots(2, 2, figsize=(11, 6.8), sharex=True)
for ax, r in zip(axs.flat, ['1_alaska', '5_greenland_periphery', '13_central_asia', '19_antarctic_and_subantarctic']):
    h = hyd[r]; x = h.start + 0.5
    off = pd.read_csv(f'{R}/hydrological_years/{r}.csv')
    for g in ['DG', 'ALT', 'GRAV']:
        if f'{g}_mwe' in h:
            ax.plot(x, h[f'{g}_mwe'], color=C[g], lw=1.4, marker='o', ms=3, label=GNAME[g])
    ax.fill_between(x, h.mwe - h.sig, h.mwe + h.sig, color=C['ink'], alpha=0.10, lw=0)
    ax.plot(x, h.mwe, color=C['ink'], lw=2.2, label='This study (consensus ±1σ)')
    ax.plot(off.start_dates + 0.5, off.combined_mwe, color=C['off'], lw=1.4, ls='--', label='GlaMBIE official')
    ax.axhline(0, color='#9a9993', lw=0.6)
    ax.set_title(f'{SHORT[r]} – {FULL[r]}', loc='left', fontsize=10)
    ax.set_ylabel('m w.e. per hydrological year')
h_, l_ = axs[0, 0].get_legend_handles_labels()
fig.legend(h_, l_, ncol=5, fontsize=8, loc='lower center', bbox_to_anchor=(0.5, -0.03))
fig.subplots_adjust(bottom=0.1)
axs[1, 0].set_xlabel('Year'); axs[1, 1].set_xlabel('Year')
save(fig, 'fig02_example_regions_groups')

# ------------------------------------------------------------ F3 global time series
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.3))
ax = axs[0]
y = ga.index.values
ax.bar(y, ga['gt'], color=C['DG'], width=0.62, alpha=0.85, label='This study (annual)')
ax.errorbar(y, ga['gt'], yerr=ga.sig_gt, fmt='none', ecolor='#2b2b2a', elinewidth=0.8, capsize=0)
ax.plot(og.index, og.combined_gt, color=C['off'], lw=1.5, ls='--', marker='s', ms=3, label='GlaMBIE official')
ax.axhline(0, color='#9a9993', lw=0.6)
ax.set_ylabel('Global glacier mass change (Gt per year)'); ax.set_xlabel('Calendar year')
ax.set_title('a  Annual global mass change (±1σ)', loc='left', fontsize=10)
ax.legend(loc='lower left')
ax = axs[1]
cum = ga.cum_gt; s = ga.sig_cum_gt
xx = np.r_[1999.5, y + 0.5]
cc = np.r_[0, cum.values]; ss = np.r_[0, s.values]
ax.fill_between(xx, cc - ss, cc + ss, color=C['DG'], alpha=0.18, lw=0)
ax.plot(xx, cc, color=C['DG'], lw=2.2, label='This study (±1σ)')
ax.plot(np.r_[1999.5, og.index + 0.5], np.r_[0, og.combined_gt.cumsum().values], color=C['off'], lw=1.5, ls='--',
        label='GlaMBIE official')
ax.set_ylabel('Cumulative mass change since 1 Jan 2000 (Gt)'); ax.set_xlabel('Year')
ax.text(0.03, 0.30, f'2000–2023: {cc[-1]:.0f} ± {ss[-1]:.0f} Gt\n≈ {-cc[-1] / 362.5:.1f} ± {ss[-1] / 362.5:.1f} mm sea-level equivalent',
        transform=ax.transAxes, ha='left', va='top', fontsize=8.5, color='#2b2b2a')
ax.set_title('b  Cumulative global mass change', loc='left', fontsize=10)
ax.legend(loc='lower left')
save(fig, 'fig03_global_timeseries')

# ------------------------------------------------------------ F4 regional small multiples
fig, axs = plt.subplots(5, 4, figsize=(12, 12.5), sharex=True)
for ax, r in zip(axs.flat, REGIONS):
    c = cal[r]; x = c.index.values
    o = pd.read_csv(f'{R}/calendar_years/{r}.csv'); o.index = o.start_dates.astype(int)
    ax.fill_between(x, c.mwe - c.sig, c.mwe + c.sig, color=C['DG'], alpha=0.2, lw=0)
    ax.plot(x, c.mwe, color=C['DG'], lw=1.6)
    ax.plot(o.index, o.combined_mwe, color=C['off'], lw=1.1, ls='--')
    ax.axhline(0, color='#9a9993', lw=0.6)
    ax.set_title(f'{SHORT[r]}  {FULL[r]}', loc='left', fontsize=8.5)
    ax.text(0.02, 0.04, f'{c.mwe.mean():.2f} m w.e./yr\n{c["gt"].mean():.1f} Gt/yr', transform=ax.transAxes,
            fontsize=7, color=C['text2'])
    ax.tick_params(labelsize=7)
ax = axs.flat[19]
ax.fill_between(ga.index, ga.mwe - ga.sig, ga.mwe + ga.sig, color=C['ink'], alpha=0.15, lw=0)
ax.plot(ga.index, ga.mwe, color=C['ink'], lw=1.8, label='This study ±1σ')
ax.plot(og.index, og.combined_mwe, color=C['off'], lw=1.1, ls='--', label='GlaMBIE official')
ax.axhline(0, color='#9a9993', lw=0.6)
ax.set_title('GLOBAL', loc='left', fontsize=8.5, fontweight='bold')
ax.legend(fontsize=7, loc='lower left')
ax.tick_params(labelsize=7)
for ax in axs[:, 0]:
    ax.set_ylabel('m w.e. yr⁻¹', fontsize=8)
save(fig, 'fig04_regional_timeseries')

# ------------------------------------------------------------ F5 regional rates, two periods
reg = pd.read_csv(f'{OUT}/regional_summary.csv')
order = reg.sort_values('rate_gt').index
fig, axs = plt.subplots(1, 2, figsize=(11.5, 5.8), sharey=True)
yy = np.arange(len(order))
ax = axs[0]
ax.barh(yy + 0.2, reg.loc[order, 'rate_0011'], height=0.38, color=C['DG'], label='2000–2011')
ax.barh(yy - 0.2, reg.loc[order, 'rate_1223'], height=0.38, color=C['ALT'], label='2012–2023')
ax.errorbar(reg.loc[order, 'rate_0011'], yy + 0.2, xerr=reg.loc[order, 'sig_0011'], fmt='none', ecolor='#2b2b2a', elinewidth=0.7)
ax.errorbar(reg.loc[order, 'rate_1223'], yy - 0.2, xerr=reg.loc[order, 'sig_1223'], fmt='none', ecolor='#2b2b2a', elinewidth=0.7)
ax.set_yticks(yy, [f'{reg.code[i]}' for i in order])
ax.invert_yaxis()
ax.set_xlabel('Mean mass-change rate (Gt yr⁻¹, ±1σ)')
ax.set_title('a  Regional mass-change rate', loc='left', fontsize=10)
ax.legend(loc='lower left')
ax = axs[1]
ax.barh(yy + 0.2, reg.loc[order, 'mwe_0011'], height=0.38, color=C['DG'], label='2000–2011')
ax.barh(yy - 0.2, reg.loc[order, 'mwe_1223'], height=0.38, color=C['ALT'], label='2012–2023')
ax.set_xlabel('Mean specific mass-change rate (m w.e. yr⁻¹)')
ax.set_title('b  Regional specific mass-change rate', loc='left', fontsize=10)
save(fig, 'fig05_regional_rates')

# ------------------------------------------------------------ F6 validation vs official
fig, axs = plt.subplots(1, 3, figsize=(13, 4.3))
xs, ys = [], []
for r in REGIONS:
    o = pd.read_csv(f'{R}/calendar_years/{r}.csv'); o.index = o.start_dates.astype(int)
    xs += list(o.combined_mwe.loc[2000:2023]); ys += list(cal[r].mwe)
xs, ys = np.array(xs), np.array(ys)
ax = axs[0]
ax.scatter(xs, ys, s=9, color=C['DG'], alpha=0.55, lw=0)
lim = [min(xs.min(), ys.min()) - 0.2, max(xs.max(), ys.max()) + 0.2]
ax.plot(lim, lim, color=C['off'], lw=1, ls='--'); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('GlaMBIE official (m w.e. yr⁻¹)'); ax.set_ylabel('This study (m w.e. yr⁻¹)')
r_ = np.corrcoef(xs, ys)[0, 1]
ax.text(0.04, 0.92, f'456 region-years\nr = {r_:.3f}\nRMSD = {np.sqrt(np.mean((xs - ys) ** 2)):.3f} m w.e.\nbias = {np.mean(ys - xs):+.3f} m w.e.',
        transform=ax.transAxes, va='top', fontsize=8)
ax.set_title('a  Regional annual specific mass change', loc='left', fontsize=10)
ax = axs[1]
ax.errorbar(og.combined_gt, ga['gt'], xerr=og.combined_gt_errors, yerr=ga.sig_gt, fmt='o', ms=4, color=C['DG'],
            ecolor='#b9b8b2', elinewidth=0.7)
lim = [-650, 50]
ax.plot(lim, lim, color=C['off'], lw=1, ls='--'); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('GlaMBIE official (Gt yr⁻¹)'); ax.set_ylabel('This study (Gt yr⁻¹)')
r_ = np.corrcoef(og.combined_gt, ga['gt'])[0, 1]
ax.text(0.04, 0.92, f'r = {r_:.3f}\nRMSD = {np.sqrt(np.mean((og.combined_gt - ga["gt"]) ** 2)):.1f} Gt\nbias = {np.mean(ga["gt"] - og.combined_gt):+.1f} Gt',
        transform=ax.transAxes, va='top', fontsize=8)
ax.set_title('b  Global annual mass change', loc='left', fontsize=10)
ax = axs[2]
comp = pd.read_csv(f'{OUT}/comparison_official.csv')
comp = comp[comp.region != 'GLOBAL']
ax.scatter(comp.official_mwe, comp.mine_mwe, s=28, color=C['DG'], zorder=3)
for _, rr in comp.iterrows():
    ax.annotate(rr.region, (rr.official_mwe, rr.mine_mwe), fontsize=6.5, xytext=(3, -3), textcoords='offset points', color=C['text2'])
lim = [-1.15, -0.05]
ax.plot(lim, lim, color=C['off'], lw=1, ls='--'); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('GlaMBIE official 2000–2023 (m w.e. yr⁻¹)'); ax.set_ylabel('This study 2000–2023 (m w.e. yr⁻¹)')
ax.set_title('c  Regional mean rates 2000–2023', loc='left', fontsize=10)
save(fig, 'fig06_validation_official')

# ------------------------------------------------------------ F7 LOGO & hybrid
logo = pd.read_csv(f'{OUT}/leave_one_group_out.csv')
hyb = pd.read_csv(f'{OUT}/hybrid_comparison.csv')
fig, axs = plt.subplots(1, 2, figsize=(12, 5.2))
ax = axs[0]
regs = list(dict.fromkeys(logo.region))
for g, dx in zip(['DG', 'ALT', 'GRAV'], [-0.22, 0, 0.22]):
    sub = logo[logo.group == g]
    yv = [regs.index(x) + dx for x in sub.region]
    ax.errorbar(sub.mean_diff_mwe, yv, xerr=sub.sig_diff, fmt='o', ms=4.5, color=C[g], ecolor=C[g], elinewidth=0.8,
                label=GNAME[g])
ax.axvline(0, color='#9a9993', lw=0.8)
ax.set_yticks(range(len(regs)), regs); ax.invert_yaxis()
ax.set_xlabel('Group estimate − consensus of the other groups (m w.e. yr⁻¹, ±1σ)')
ax.set_title('a  Leave-one-group-out consistency', loc='left', fontsize=10)
ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=3, fontsize=7.5)
ax = axs[1]
h = hyb[hyb.kind == 'annual']
auths = ['Dussaillant et al.', 'Huss et al.', 'Box et al.', 'Palsson et al.']
cols = [C['DG'], C['ALT'], C['GRAV'], C['HYB']]
for a_, cc_ in zip(auths, cols):
    sub = h[h.author == a_]
    ax.scatter(sub.recon_mean, sub.hybrid_mean, s=26, color=cc_, label=f'{a_} (n={len(sub)})', zorder=3)
hp = hyb[(hyb.kind != 'annual') & hyb.author.isin(['Miles et al.', 'Colgan et al.'])]
ax.scatter(hp.recon_mean, hp.hybrid_mean, s=30, marker='D', color='#6250d6', label='Miles / Colgan (multi-annual)', zorder=3)
lim = [-1.1, 0]
ax.plot(lim, lim, color=C['off'], lw=1, ls='--'); ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('This study, mean over common years (m w.e. yr⁻¹)')
ax.set_ylabel('Hybrid solution (held out), same years (m w.e. yr⁻¹)')
ax.set_title('b  Comparison with withheld hybrid estimates', loc='left', fontsize=10)
ax.legend(fontsize=7.5, loc='upper left')
save(fig, 'fig07_logo_hybrid')

# ------------------------------------------------------------ F8 sensitivity
sens = pd.read_csv(f'{OUT}/sensitivity_summary.csv')
labels = {'main': 'Main configuration', 'group_w_invvar': 'Inverse-variance group weights',
          'within_w_per_solution': 'Equal weight per solution (not per team)',
          'monthly_err_independent': 'Monthly errors independent', 'gravimetry_all_regions': 'Gravimetry in all regions',
          'gravimetry_none': 'No gravimetry', 'no_altimetry': 'No altimetry in combination',
          'density_800': 'Density 800 kg m⁻³', 'density_900': 'Density 900 kg m⁻³',
          'offset_constant_per_dataset': 'Constant DEM offset per dataset', 'extension_nearest': 'Nearest-period extension (DG)',
          'glaciological_level': 'Glaciological series also define level', 'tau_zero': 'τ = 0 (no representativeness error)'}
gp = pd.read_csv(f'{OUT}/global_period_summary.csv').set_index('period')
fig, ax = plt.subplots(figsize=(9, 5.2))
yy = np.arange(len(sens))
mrate, msig = gp.loc['2000-2023', 'rate'], gp.loc['2000-2023', 'sig_rate']
ax.axvspan(mrate - msig, mrate + msig, color=C['DG'], alpha=0.12, lw=0, label='Main ±1σ')
ax.scatter(sens.mean_2000_2011, yy, marker='<', s=30, color=C['GRAV'], label='2000–2011', zorder=3)
ax.scatter(sens.mean_2012_2023, yy, marker='>', s=30, color=C['ALT'], label='2012–2023', zorder=3)
ax.scatter(sens.mean_2000_2023, yy, s=40, color=C['DG'], label='2000–2023', zorder=4)
ax.axvline(og.combined_gt.mean(), color=C['off'], ls='--', lw=1.2, label='GlaMBIE official 2000–2023')
ax.set_yticks(yy, [labels.get(e, e) for e in sens.experiment]); ax.invert_yaxis()
ax.set_xlabel('Global mean mass-change rate (Gt yr⁻¹)')
ax.set_title('Sensitivity of the global estimate to methodological choices', loc='left', fontsize=10)
ax.legend(fontsize=7.5, loc='upper center', bbox_to_anchor=(0.4, -0.12), ncol=5)
save(fig, 'fig08_sensitivity')

# ------------------------------------------------------------ F9 variability diagnostics
cvv = pd.read_csv(f'{OUT}/cv_variability.csv')
vc = pd.read_csv(f'{OUT}/variability_consistency.csv')
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.3))
ax = axs[0]
for v, cc_, lab in [('both', C['DG'], 'WGMS + sine-wave (FE mean)'), ('wgms', C['ALT'], 'WGMS anomalies only'),
                    ('zemp', C['GRAV'], 'Sine-wave series only')]:
    s_ = cvv[cvv['var'] == v].groupby('k').err_rate.apply(lambda x: np.sqrt(np.mean(x ** 2)))
    ax.plot(s_.index, s_.values, marker='o', color=cc_, lw=2, label=lab)
ax.set_xlabel('Amplitude factor k applied to glaciological anomalies')
ax.set_ylabel('RMSE of held-out pentad rate (m w.e. yr⁻¹)')
ax.set_title('a  Leave-one-pentad-out prediction of DEM differencing', loc='left', fontsize=10)
ax.legend(fontsize=7.5)
ax = axs[1]
sub = vc[vc.group == 'GRAV'].copy()
used = ['ALA', 'ACN', 'ACS', 'ISL', 'SJM', 'RUA', 'SAN']
sub['used'] = sub.region.isin(used)
sub = sub.sort_values('r_annual')
ax.barh(sub.region, sub.r_annual, color=[C['GRAV'] if u else '#c3c2b7' for u in sub.used], height=0.6, label='annual')
ax.scatter(sub.r_3yr, sub.region, color=C['ink'], s=16, zorder=3, label='3-year means')
ax.axvline(0, color='#9a9993', lw=0.6)
ax.set_xlabel('Correlation with glaciological anomalies')
ax.set_title('b  Gravimetry vs glaciological variability\n(green: gravimetry used; grey: excluded)', loc='left', fontsize=10)
ax.legend(fontsize=7.5, loc='lower right')
save(fig, 'fig09_variability_diagnostics')

# ------------------------------------------------------------ F10 uncertainty budget
fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.5))
ax = axs[0]
ub = pd.DataFrame({SHORT[r]: dict(rand=cal[r].sig_rand.mean(), sys=cal[r].sig_sys.mean()) for r in REGIONS}).T
ub = ub.loc[[SHORT[r] for r in REGIONS]]
x = np.arange(len(ub))
ax.bar(x - 0.2, ub['rand'], width=0.38, color=C['DG'], label='Random (year-to-year independent)')
ax.bar(x + 0.2, ub['sys'], width=0.38, color=C['ALT'], label='Systematic (temporally correlated)')
ax.set_xticks(x, ub.index, rotation=60, fontsize=7.5)
ax.set_ylabel('Mean annual 1σ (m w.e.)')
ax.set_title('a  Regional uncertainty components', loc='left', fontsize=10)
ax.legend(fontsize=7.5)
ax = axs[1]
ax.plot(ga.index, ga.sig_rand_gt, color=C['DG'], lw=2, label='Random')
ax.plot(ga.index, ga.sig_sys_gt, color=C['ALT'], lw=2, label='Systematic')
ax.plot(ga.index, ga.sig_gt, color=C['ink'], lw=2, label='Total (this study)')
ax.plot(og.index, og.combined_gt_errors, color=C['off'], lw=1.4, ls='--', label='GlaMBIE official total')
ax.set_ylabel('Global annual 1σ (Gt)'); ax.set_xlabel('Calendar year')
ax.set_title('b  Global annual uncertainty through time', loc='left', fontsize=10)
ax.legend(fontsize=7.5)
save(fig, 'fig10_uncertainty_budget')

# ------------------------------------------------------------ F11 literature comparison
lit = pd.read_csv(f'{OUT}/literature_comparison.csv')
fig, ax = plt.subplots(figsize=(8, 3.8))
yy = np.arange(len(lit))
ax.errorbar(lit.value, yy - 0.18, xerr=lit.sig95, fmt='s', color=C['ALT'], ms=5, label='Published (95% CI)')
ax.errorbar(lit.this_study, yy + 0.0, xerr=lit.this_study_sig95, fmt='o', color=C['DG'], ms=5, label='This study (95% CI)')
ax.scatter(lit.glambie_official, yy + 0.18, marker='D', color=C['off'], s=22, label='GlaMBIE official (central)', zorder=3)
ax.set_yticks(yy, [f'{s}\n{p}' for s, p in zip(lit.study, lit.period)], fontsize=8)
ax.invert_yaxis()
ax.set_xlabel('Global glacier mass-change rate (Gt yr⁻¹)')
ax.set_title('Comparison with previous global assessments', loc='left', fontsize=10)
ax.legend(fontsize=7.5, loc='upper center', bbox_to_anchor=(0.5, -0.16), ncol=3)
save(fig, 'fig11_literature')
