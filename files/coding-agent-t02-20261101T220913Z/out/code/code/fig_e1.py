"""Figures/tables for E1 (width sweep).  Writes figs/e1_*.pdf, tables/e1_table.tex, tables/e1_stats.json"""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
import ana
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
D = '/work/results/e1_width'
df = ana.load(D)
rng = np.random.default_rng(0)
widths = sorted(df.width.unique())
CAP = 30000.0


def med_inf(x):
    x = np.where(np.isnan(x), np.inf, x)
    return np.median(x)


def boot_med(x, n=4000):
    x = np.where(np.isnan(x), np.inf, np.asarray(x, float))
    b = np.array([np.median(x[rng.integers(0, len(x), len(x))]) for _ in range(n)])
    return np.percentile(b, [2.5, 97.5]), b


# per-width norms at t_gen
import os
norm_gen = {}
for _, r in df.iterrows():
    o = json.load(open(os.path.join(D, r.fn)))
    cv = o['curves']
    if r.gen:
        norm_gen.setdefault(r.width, []).append(cv['wnorm'][cv['step'].index(int(r.t_gen))])
rows = []
for w in widths:
    g = df[df.width == w]
    ci_fit, _ = boot_med(g.t_fit.values)
    ci_gen, _ = boot_med(g.t_gen.values)
    dly = (g.t_gen - g.t_fit).dropna()
    rows.append(dict(width=w, P=int(g.P.iloc[0]), n=len(g), fit=g.fit.mean(), gen=g.gen.mean(), t_fit=med_inf(g.t_fit.values),
                     t_fit_lo=ci_fit[0], t_fit_hi=ci_fit[1], t_gen=med_inf(g.t_gen.values), t_gen_lo=ci_gen[0], t_gen_hi=ci_gen[1],
                     delay_med=dly.median() if len(dly) else np.nan, va_fit=g.va_fit.median(), mem_first=g.mem_first.mean(),
                     fin_va=g.fin_va.median(), norm_gen=np.mean(norm_gen.get(w, [np.nan])), norm_gen_sd=np.std(norm_gen.get(w, [np.nan]), ddof=1) if len(norm_gen.get(w, [])) > 1 else np.nan,
                     ngen=len(norm_gen.get(w, []))))
T = pd.DataFrame(rows)
T.to_csv('/work/tables/e1_table.csv', index=False)
print(T.to_string())

# slope of median t_gen vs P, bootstrap over seeds (widths with majority generalising)
def slope_boot(wmin, n=2000, col='t_gen'):
    sub = df[df.width >= wmin]
    ws = sorted(sub.width.unique())
    groups = {w: np.where(np.isnan(sub[sub.width == w][col].values), np.inf, sub[sub.width == w][col].values) for w in ws}
    Ps = np.log([sub[sub.width == w].P.iloc[0] for w in ws])
    out = []
    for _ in range(n):
        m = [np.median(g[rng.integers(0, len(g), len(g))]) for g in groups.values()]
        if not np.all(np.isfinite(m)):
            continue
        out.append(np.polyfit(Ps, np.log(m), 1)[0])
    return np.mean(out), np.percentile(out, [2.5, 97.5]), len(out)
stats = {}
for wmin in [32, 64]:
    for col in ['t_gen', 't_fit']:
        s, ci, k = slope_boot(wmin, col=col)
        stats[f'slope_{col}_w>={wmin}'] = dict(slope=s, lo=ci[0], hi=ci[1], nboot_valid=k)
df['R'] = df.t_gen / df.t_fit
for wmin in [32, 64]:
    sub = df[df.width >= wmin]; ws = sorted(sub.width.unique())
    groups = {w: np.where(np.isnan(sub[sub.width == w].R.values), np.inf, sub[sub.width == w].R.values) for w in ws}
    Ps = np.log([sub[sub.width == w].P.iloc[0] for w in ws]); out = []
    for _ in range(2000):
        m = [np.median(g[rng.integers(0, len(g), len(g))]) for g in groups.values()]
        if np.all(np.isfinite(m)):
            out.append(np.polyfit(Ps, np.log(m), 1)[0])
    stats[f'slope_R_w>={wmin}'] = dict(slope=float(np.mean(out)), lo=float(np.percentile(out, 2.5)), hi=float(np.percentile(out, 97.5)), nboot_valid=len(out))
# norm invariance
ng = T[T.ngen >= 5]
stats['norm_gen_cv_across_widths'] = float(ng.norm_gen.std() / ng.norm_gen.mean())
stats['norm_gen_range'] = [float(ng.norm_gen.min()), float(ng.norm_gen.max())]
stats['norm_gen_over_sqrtP_range'] = [float((ng.norm_gen / np.sqrt(ng.P)).min()), float((ng.norm_gen / np.sqrt(ng.P)).max())]
json.dump(stats, open('/work/tables/e1_stats.json', 'w'), indent=1, default=float)
print(json.dumps(stats, indent=1, default=float))

# ---- Figure 1: example curves
fig, ax = plt.subplots(1, 4, figsize=(7.0, 1.9), sharey=True)
for a, w in zip(ax, [8, 16, 32, 128]):
    for seed, ls in [(0, '-'), (1, '--')]:
        fn = [f for f in df[(df.width == w) & (df.seed == seed)].fn][0]
        cv = json.load(open(f'{D}/{fn}'))['curves']
        a.plot(np.array(cv['step']) + 1, cv['tr_acc'], 'C0', ls=ls, lw=1)
        a.plot(np.array(cv['step']) + 1, cv['va_acc'], 'C3', ls=ls, lw=1)
    a.set_xscale('log'); a.set_title(f'd={w}  (P={int(df[df.width==w].P.iloc[0]):,})', fontsize=7); a.set_xlabel('step')
ax[0].set_ylabel('accuracy'); ax[0].plot([], [], 'C0', label='train'); ax[0].plot([], [], 'C3', label='val'); ax[0].legend(frameon=False, fontsize=6, loc='center left')
plt.tight_layout(); plt.savefig('/work/figs/e1_curves.pdf'); plt.close()

# ---- Figure 2: summary vs P
fsp_fit, fsp_gen, norm_fit = {}, {}, {}
for _, r in df.iterrows():
    cv = json.load(open(f'{D}/{r.fn}'))['curves']
    if r.fit: 
        fsp_fit.setdefault(r.width, []).append(cv['fsp'][cv['step'].index(int(r.t_fit))]); norm_fit.setdefault(r.width, []).append(cv['wnorm'][cv['step'].index(int(r.t_fit))])
    if r.gen: fsp_gen.setdefault(r.width, []).append(cv['fsp'][cv['step'].index(int(r.t_gen))])
fig, ax = plt.subplots(2, 3, figsize=(7.0, 4.0))
P = T.P.values
a = ax[0, 0]
for col, c, lab in [('t_fit', 'C0', r'$t_{\rm fit}$'), ('t_gen', 'C3', r'$t_{\rm gen}$')]:
    m = np.minimum(T[col].values, CAP * 1.3)
    lo, hi = np.minimum(T[col + '_lo'].fillna(CAP * 1.3).values, CAP * 1.3), np.minimum(T[col + '_hi'].fillna(CAP * 1.3).values, CAP * 1.3)
    a.errorbar(P, m, yerr=[np.maximum(m - lo, 0), np.maximum(hi - m, 0)], fmt='o-', color=c, ms=3, lw=1, capsize=1.5, label=lab)
a.axhline(CAP, color='gray', ls=':', lw=.7); a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel('parameters P'); a.set_ylabel('steps (median, 95% CI)'); a.legend(frameon=False, fontsize=6)
a.text(1.2e3, 1.4e4, 'budget (30k)', fontsize=5.5, color='gray')
a = ax[0, 1]
dl = df.assign(D=np.where(df.gen, df.t_gen - df.t_fit, np.nan))
for w in widths:
    g = dl[dl.width == w]; Pw = g.P.iloc[0]
    ok_ = g.D.dropna(); a.scatter([Pw] * len(ok_), ok_, s=5, color='C1', alpha=.6)
    cens = g[~g.gen]; a.scatter([Pw] * len(cens), [30000] * len(cens), s=8, marker='^', facecolors='none', edgecolors='C1', lw=.6)
meds = dl.groupby('width').apply(lambda g: np.median(np.where(g.gen, g.t_gen - g.t_fit, np.inf)))
mw = [w for w in widths if np.isfinite(meds[w])]
a.plot([df[df.width == w].P.iloc[0] for w in mw], [meds[w] for w in mw], 'k-', lw=1, label='median (all runs; censored=$\\infty$)')
a.axhline(30000, color='gray', ls=':', lw=.7); a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel('parameters P'); a.set_ylabel(r'delay $t_{\rm gen}-t_{\rm fit}$ (steps)'); a.legend(frameon=False, fontsize=5.5, loc='lower left')
a = ax[0, 2]
a.plot(P, T.gen, 'o-', color='C3', ms=3, lw=1, label=r'reached val$\geq$0.99'); a.plot(P, T.mem_first, 's--', color='C2', ms=3, lw=1, label=r'memorise-first (val$<$0.5 at $t_{\rm fit}$)'); a.set_xscale('log'); a.set_xlabel('parameters P'); a.set_ylabel('fraction of 8 seeds'); a.legend(frameon=False, fontsize=5.5, loc='lower right')
a = ax[1, 0]
for w in widths:
    g = df[df.width == w]
    a.scatter([g.P.iloc[0]] * len(g), g.va_fit, s=5, color='C1', alpha=.6)
a.plot(P, T.va_fit, 'k-', lw=1); a.set_xscale('log'); a.set_xlabel('parameters P'); a.set_ylabel(r'val acc at $t_{\rm fit}$'); a.axhline(0.5, color='gray', ls=':', lw=.7)
a = ax[1, 1]
a.errorbar(P, T.norm_gen, yerr=T.norm_gen_sd, fmt='o-', color='C4', ms=3, lw=1, capsize=1.5, label=r'at $t_{\rm gen}$')
a.plot(P, [np.mean(norm_fit[w]) for w in widths], 's-', color='C0', ms=3, lw=1, label=r'at $t_{\rm fit}$')
a.plot(P, [df[df.width == w].apply(lambda r: json.load(open(f'{D}/{r.fn}'))['curves']['wnorm'][0], axis=1).mean() for w in widths], 'k--', lw=1, label='at init')
a.set_xscale('log'); a.set_xlabel('parameters P'); a.set_ylabel(r'parameter L2 norm $\|\theta\|$'); a.set_ylim(0, None); a.legend(frameon=False, fontsize=5.5, loc='upper left')
a = ax[1, 2]
a.plot(P, [np.mean(fsp_fit[w]) for w in widths], 's-', color='C0', ms=3, lw=1, label=r'at $t_{\rm fit}$')
wg = sorted(fsp_gen); a.plot([T[T.width == w].P.iloc[0] for w in wg], [np.mean(fsp_gen[w]) for w in wg], 'o-', color='C4', ms=3, lw=1, label=r'at $t_{\rm gen}$')
a.set_xscale('log'); a.set_xlabel('parameters P'); a.set_ylabel('top-5 Fourier energy of embedding'); a.set_ylim(0, 1.02); a.legend(frameon=False, fontsize=5.5)
plt.tight_layout(); plt.savefig('/work/figs/e1_summary.pdf'); plt.close()
