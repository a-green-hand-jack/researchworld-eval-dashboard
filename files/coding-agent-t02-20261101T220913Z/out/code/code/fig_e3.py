"""E3: critical (memorise-first) size vs number of training pairs N.  Uses E3 runs + E1 (p=59, frac=.4)."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
import ana
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
d3 = ana.load('/work/results/e3_capacity')
d1 = ana.load('/work/results/e1_width'); d1 = d1[d1.width.isin([6, 8, 12, 16, 24, 32, 48])]
df = pd.concat([d3, d1], ignore_index=True)
df['logp'] = np.log2(df.p)
rng = np.random.default_rng(2)
THR = 0.5
cfgs = sorted(df.groupby(['p', 'frac']).size().index, key=lambda t: t[0] ** 2 * t[1])


def crossing(Ps, v, thr=THR):
    """smallest log P where median va_fit (ordered by increasing P) drops below thr, log-linear interp; nan if never / always."""
    lp = np.log(Ps)
    for i in range(1, len(v)):
        if v[i - 1] >= thr > v[i]:
            return float(np.exp(lp[i - 1] + (v[i - 1] - thr) / (v[i - 1] - v[i]) * (lp[i] - lp[i - 1])))
    return np.nan


def curve(g, resample):
    ws = sorted(g.width.unique()); Ps, vs = [], []
    for w in ws:
        x = g[g.width == w]
        # runs that never fit count as "va_fit = 1" (not memorise-first)
        v = np.where(x.fit, x.va_fit, 1.0)
        if resample:
            v = v[rng.integers(0, len(v), len(v))]
        Ps.append(x.P.iloc[0]); vs.append(np.median(v))
    return np.array(Ps), np.array(vs)


rows = []
for (p, frac) in cfgs:
    g = df[(df.p == p) & (df.frac == frac)]
    N = int(g.N.iloc[0])
    Ps, vs = curve(g, False)
    pstar = crossing(Ps, vs)
    bs = [crossing(*curve(g, True)) for _ in range(1000)]
    bs = np.array(bs)
    rows.append(dict(p=p, frac=frac, N=N, bits=N * np.log2(p), Pstar=pstar, lo=np.nanpercentile(bs, 2.5) if np.isfinite(bs).any() else np.nan,
                     hi=np.nanpercentile(bs, 97.5) if np.isfinite(bs).any() else np.nan, n_valid=int(np.isfinite(bs).sum()),
                     fit_frac_min=g.groupby('width').fit.mean().min()))
T = pd.DataFrame(rows); T['bits_per_param'] = T.bits / T.Pstar
T.to_csv('/work/tables/e3_table.csv', index=False); print(T.to_string())
# slopes
ok = T.dropna(subset=['Pstar'])
stats = {}
for xname in ['N', 'bits']:
    x = np.log(ok[xname].values)
    y = np.log(ok.Pstar.values)
    sl = np.polyfit(x, y, 1)[0]
    # bootstrap: resample seeds within each (config,width) then recompute P* and refit
    bsl = []
    for _ in range(1000):
        ps = []
        for (p, frac) in cfgs:
            g = df[(df.p == p) & (df.frac == frac)]
            ps.append(crossing(*curve(g, True)))
        ps = np.array(ps); m = np.isfinite(ps)
        if m.sum() >= 3:
            bsl.append(np.polyfit(np.log(T[xname].values[m]), np.log(ps[m]), 1)[0])
    stats[f'slope_Pstar_vs_{xname}'] = dict(slope=float(sl), lo=float(np.percentile(bsl, 2.5)), hi=float(np.percentile(bsl, 97.5)), n_cfg=int(len(ok)), nboot=len(bsl))
sens = {}
for thr in [0.3, 0.5, 0.7]:
    pts = []
    for (p, frac) in cfgs:
        g = df[(df.p == p) & (df.frac == frac)]
        pts.append((p, frac, int(g.N.iloc[0]), crossing(*curve(g, False), thr)))
    sens[str(thr)] = [dict(p=a, frac=b, N=c, Pstar=None if d != d else float(d)) for a, b, c, d in pts]
    ok_ = [(c, d) for a, b, c, d in pts if d == d]
    sens[str(thr)].append(dict(n_defined=len(ok_), slope=float(np.polyfit(np.log([x[0] for x in ok_]), np.log([x[1] for x in ok_]), 1)[0]) if len(ok_) >= 3 else None))
stats['threshold_sensitivity'] = sens
json.dump(stats, open('/work/tables/e3_stats.json', 'w'), indent=1); print(json.dumps(stats, indent=1))

fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.6))
for i, (p, frac) in enumerate(cfgs):
    g = df[(df.p == p) & (df.frac == frac)]
    Ps, vs = curve(g, False)
    N = int(g.N.iloc[0])
    ax[0].plot(Ps, vs, 'o-', ms=3, lw=1, color=f'C{i}', label=f'p={p}, frac={frac} (N={N})')
    ax[1].plot(N * np.log2(p) / Ps, vs, 'o-', ms=3, lw=1, color=f'C{i}')
ax[0].axhline(THR, color='gray', ls=':', lw=.7); ax[0].set_xscale('log'); ax[0].set_xlabel('parameters P'); ax[0].set_ylabel(r'median val acc at $t_{\rm fit}$'); h, l = ax[0].get_legend_handles_labels(); fig.legend(h, l, loc='upper center', ncol=3, frameon=False, fontsize=6.5, bbox_to_anchor=(0.5, 1.02))
from matplotlib.ticker import NullFormatter
ax[0].set_xticks([2e3, 5e3, 1e4, 3e4]); ax[0].set_xticklabels(['2k', '5k', '10k', '30k']); ax[0].xaxis.set_minor_formatter(NullFormatter())
ax[1].axhline(THR, color='gray', ls=':', lw=.7); ax[1].set_xscale('log'); ax[1].set_xlabel(r'$N\log_2 p\,/\,P$ (bits / parameter)'); ax[1].set_ylabel(r'median val acc at $t_{\rm fit}$')
Pmax = df.P.max()
Pmax_cfg = {k: df[(df.p == k[0]) & (df.frac == k[1])].P.max() for k in cfgs}
for i, (p, frac) in enumerate(cfgs):
    r = T[(T.p == p) & (T.frac == frac)].iloc[0]
    if np.isfinite(r.Pstar):
        ax[2].errorbar(r.N, r.Pstar, yerr=[[r.Pstar - r.lo], [r.hi - r.Pstar]], fmt='o', color=f'C{i}', ms=4, capsize=2, lw=1)
    else:
        ax[2].annotate('', xy=(r.N, Pmax_cfg[(p, frac)] * 1.6), xytext=(r.N, Pmax_cfg[(p, frac)]), arrowprops=dict(arrowstyle='->', color=f'C{i}', lw=1))
        ax[2].plot(r.N, Pmax_cfg[(p, frac)], 'o', mfc='none', color=f'C{i}', ms=4)
xs = np.array([ok.N.min() * .8, ok.N.max() * 1.2]); k = float(np.exp(np.mean(np.log(ok.Pstar) - np.log(ok.N))))
ax[2].plot(xs, k * xs, 'k:', lw=.8, label=r'$P^\ast\propto N$'); ax[2].set_xscale('log'); ax[2].set_yscale('log'); ax[2].set_xlabel('training pairs N'); ax[2].set_ylabel(r'crossing size $P^\ast$'); ax[2].legend(frameon=False, fontsize=6)
plt.tight_layout(rect=(0, 0, 1, 0.9)); plt.savefig('/work/figs/e3_capacity.pdf'); plt.close()
