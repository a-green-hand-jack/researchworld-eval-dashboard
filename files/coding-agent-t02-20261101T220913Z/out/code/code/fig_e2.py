"""E2 figure/stats: weight-decay clock t_gen ~ 1/(lr*wd), and invariance of norm at t_gen across (lr, wd, width)."""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
import ana
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import NullFormatter, FixedLocator, FixedFormatter
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
D = '/work/results/e2_clock'
df = ana.load(D)
df['prod'] = df.lr * df.wd
rng = np.random.default_rng(1)
rows = []
for _, r in df.iterrows():
    cv = json.load(open(f'{D}/{r.fn}'))['curves']
    rows.append(cv['wnorm'][cv['step'].index(int(r.t_gen))] if r.gen else np.nan)
df['norm_gen'] = rows
df['clock_const'] = df.t_gen * df['prod']
df['delay_const'] = (df.t_gen - df.t_fit) * df['prod']
stats = {}
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.1))
cols = {32: 'C0', 64: 'C2', 128: 'C3'}
for w, g in df.groupby('width'):
    gg = g[g.gen]
    ax[0].scatter(gg['prod'], gg.t_gen, s=6, color=cols[w], alpha=.5)
    m = gg.groupby('prod').t_gen.median()
    ax[0].plot(m.index, m.values, 'o-', color=cols[w], ms=3, lw=1, label=f'd={w}')
    # slope with bootstrap over seeds (fit on per-condition medians)
    conds = sorted(gg['prod'].unique())
    groups = [g[g['prod'] == c].t_gen.values for c in conds]
    # conditions where all seeds generalised only
    keep = [i for i, v in enumerate(groups) if np.all(np.isfinite(v)) and len(v) > 0]
    xs = np.log(np.array(conds)[keep]); sl = []
    if len(keep) < 3:
        stats[f'slope_d{w}'] = dict(note='fewer than 3 fully-uncensored conditions; slope not estimated', n_runs=int(len(g)), n_gen=int(g.gen.sum()))
        stats[f'clockconst_d{w}'] = dict(median=float(gg.clock_const.median()))
        stats[f'norm_gen_d{w}'] = dict(mean=float(gg.norm_gen.mean()), sd=float(gg.norm_gen.std()), min=float(gg.norm_gen.min()), max=float(gg.norm_gen.max()))
        continue
    for _ in range(2000):
        ys = [np.log(np.median(groups[i][rng.integers(0, len(groups[i]), len(groups[i]))])) for i in keep]
        sl.append(np.polyfit(xs, ys, 1)[0])
    stats[f'slope_d{w}'] = dict(mean=float(np.mean(sl)), lo=float(np.percentile(sl, 2.5)), hi=float(np.percentile(sl, 97.5)), n_conditions=len(keep),
                                n_runs=int(len(g)), n_gen=int(g.gen.sum()))
    stats[f'clockconst_d{w}'] = dict(median=float(gg.clock_const.median()), q25=float(gg.clock_const.quantile(.25)), q75=float(gg.clock_const.quantile(.75)))
    stats[f'norm_gen_d{w}'] = dict(mean=float(gg.norm_gen.mean()), sd=float(gg.norm_gen.std()), min=float(gg.norm_gen.min()), max=float(gg.norm_gen.max()))
# censored (never reached val>=0.99 in 30k steps) runs drawn as open triangles at the cap
for w, g in df.groupby('width'):
    gc = g[~g.gen]
    ax[0].scatter(gc['prod'], [30000] * len(gc), s=8, marker='^', facecolors='none', edgecolors=cols[w], lw=.7)
ax[0].set_xscale('log'); ax[0].set_yscale('log'); ax[0].set_xlabel(r'lr$\times$wd'); ax[0].set_ylabel(r'$t_{\rm gen}$ (steps)'); ax[0].legend(frameon=False, fontsize=6)
xx = np.array([2.5e-4, 4e-3]); ax[0].plot(xx, 4.7 / xx, 'k:', lw=.8)
ax[0].text(3e-4, 3000, r'slope $-1$', fontsize=6)
# panel 2: t_gen*lr*wd per condition
for w, g in df.groupby('width'):
    gg = g[g.gen]
    ax[1].scatter(gg['prod'], gg.clock_const, s=6, color=cols[w], alpha=.5)
    m = gg.groupby('prod').clock_const.median(); ax[1].plot(m.index, m.values, 'o-', color=cols[w], ms=3, lw=1)
ax[1].set_xscale('log'); ax[1].set_xlabel(r'lr$\times$wd'); ax[1].set_ylabel(r'$t_{\rm gen}\cdot$lr$\cdot$wd'); ax[1].set_ylim(0, None)
# panel 3: norm at t_gen
for w, g in df.groupby('width'):
    gg = g[g.gen]
    ax[2].scatter(gg['prod'], gg.norm_gen, s=6, color=cols[w], alpha=.5)
    m = gg.groupby('prod').norm_gen.mean(); ax[2].plot(m.index, m.values, 'o-', color=cols[w], ms=3, lw=1)
ax[2].set_xscale('log'); ax[2].set_xlabel(r'lr$\times$wd'); ax[2].set_ylabel(r'$\|\theta\|$ at $t_{\rm gen}$'); ax[2].set_ylim(0, None)
for a in ax:
    a.set_xticks([5e-4, 1e-3, 2e-3, 4e-3]); a.set_xticklabels(['5e-4', '1e-3', '2e-3', '4e-3']); a.xaxis.set_minor_formatter(NullFormatter())
    a.xaxis.set_minor_locator(FixedLocator([]))
plt.tight_layout(); plt.savefig('/work/figs/e2_clock.pdf'); plt.close()
# per-condition table
tab = df.groupby(['width', 'lr', 'wd']).agg(n=('seed', 'size'), gen=('gen', 'sum'), t_fit=('t_fit', 'median'), t_gen=('t_gen', 'median'), clock=('clock_const', 'median'),
                                          norm_gen=('norm_gen', 'mean'), norm_sd=('norm_gen', 'std'), va_fit=('va_fit', 'median')).reset_index()
tab.to_csv('/work/tables/e2_table.csv', index=False)
# is norm at t_gen different between conditions? ANOVA-style: variance of condition means relative to total
allg = df[df.gen]
stats['norm_gen_all'] = dict(mean=float(allg.norm_gen.mean()), sd=float(allg.norm_gen.std()), cv=float(allg.norm_gen.std() / allg.norm_gen.mean()),
                             min=float(allg.norm_gen.min()), max=float(allg.norm_gen.max()), n=int(len(allg)))
# rank correlation of t_gen with 1/(lr wd) pooled within width 128 and 64
from scipy import stats as st
for w in [32, 64, 128]:
    g = allg[allg.width == w]
    stats[f'spearman_tgen_vs_prod_d{w}'] = float(st.spearmanr(g['prod'], g.t_gen)[0])
# lr vs wd separately: regression log t_gen ~ a log lr + b log wd (+ width fixed effects)
g = allg[allg.width >= 64].copy(); X = np.column_stack([np.log(g.lr), np.log(g.wd)] + [(g.width == w).astype(float) for w in [64, 128]])
y = np.log(g.t_gen.values)
beta, *_ = np.linalg.lstsq(X, y, rcond=None)
res = y - X @ beta; n, k = X.shape
cov = np.linalg.inv(X.T @ X) * (res @ res) / (n - k)
stats['loglog_regression'] = dict(lr_coef=float(beta[0]), lr_se=float(np.sqrt(cov[0, 0])), wd_coef=float(beta[1]), wd_se=float(np.sqrt(cov[1, 1])), n=int(n))
json.dump(stats, open('/work/tables/e2_stats.json', 'w'), indent=1)
print(tab.to_string()); print(json.dumps(stats, indent=1))
