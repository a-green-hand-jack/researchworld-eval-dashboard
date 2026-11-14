"""E5: causal norm intervention (rescale all parameters by c at first train-fit)."""
import sys, os, json, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
import ana
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
d5 = ana.load('/work/results/e5_rescale')
d1 = ana.load('/work/results/e1_width'); d1 = d1[(d1.seed < 4) & d1.width.isin([24, 32, 64, 128])].copy(); d1['rescale'] = 1.0
df = pd.concat([d5, d1], ignore_index=True)
def norm_at(r, key):
    D = '/work/results/e5_rescale' if r.rescale != 1.0 else '/work/results/e1_width'
    cv = json.load(open(f'{D}/{r.fn}'))['curves']
    return cv['wnorm'][cv['step'].index(int(r[key]))] if r[key] == r[key] else np.nan
df['norm_gen'] = df.apply(lambda r: norm_at(r, 't_gen'), axis=1)
df['norm_fit'] = df.apply(lambda r: norm_at(r, 't_fit'), axis=1)
df['delay'] = df.t_gen - df.t_fit
rng = np.random.default_rng(3)
rows = []
for (w, c), g in df.groupby(['width', 'rescale']):
    rows.append(dict(width=w, c=c, n=len(g), gen=int(g.gen.sum()), t_fit=g.t_fit.median(), t_gen=g.t_gen.median(), delay=g.delay.median(),
                     norm_gen=g.norm_gen.mean(), norm_gen_sd=g.norm_gen.std(), va_fit=g.va_fit.median()))
T = pd.DataFrame(rows).sort_values(['width', 'c']); T.to_csv('/work/tables/e5_table.csv', index=False); print(T.to_string())
# paired log-ratio of delay vs c=1 (same seed => same init/split/trajectory until intervention), bootstrap over seeds
stats = {}
for w in [24, 32, 64, 128]:
    base = df[(df.width == w) & (df.rescale == 1.0)].set_index('seed').delay
    for c in [0.6, 0.8, 1.2, 1.4]:
        x = df[(df.width == w) & (df.rescale == c)].set_index('seed').delay
        idx = base.index.intersection(x.index)
        lr_ = np.log((x[idx] / base[idx]).dropna().values.astype(float))
        if len(lr_) < 2:
            continue
        bs = [np.mean(lr_[rng.integers(0, len(lr_), len(lr_))]) for _ in range(4000)]
        stats[f'd{w}_c{c}'] = dict(mean_log_ratio=float(lr_.mean()), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), n=int(len(lr_)),
                                  n_censored=int(len(idx) - len(lr_)))
# pooled slope: log(delay) ~ log(c) with width fixed effects
g = df.dropna(subset=['delay']); g = g[g.delay > 0]
X = np.column_stack([np.log(g.rescale)] + [(g.width == w).astype(float) for w in [24, 32, 64, 128]]); y = np.log(g.delay.values)
beta, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ beta; cov = np.linalg.inv(X.T @ X) * (res @ res) / (len(y) - X.shape[1])
stats['pooled_logdelay_vs_logc'] = dict(slope=float(beta[0]), se=float(np.sqrt(cov[0, 0])), n=int(len(y)))
json.dump(stats, open('/work/tables/e5_stats.json', 'w'), indent=1); print(json.dumps(stats, indent=1))
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.1))
cols = {24: 'C1', 32: 'C0', 64: 'C2', 128: 'C3'}
for w, g in df.groupby('width'):
    m = g.groupby('rescale').delay.median(); ax[0].plot(m.index, m.values, 'o-', ms=3, lw=1, color=cols[w], label=f'd={w}')
    ax[0].scatter(g.rescale, g.delay, s=5, color=cols[w], alpha=.4)
    m = g.groupby('rescale').norm_gen.mean(); ax[1].plot(m.index, m.values, 'o-', ms=3, lw=1, color=cols[w])
    m = (g.norm_fit * g.rescale).groupby(g.rescale).mean(); ax[2].plot(m.index, m.values, 'o-', ms=3, lw=1, color=cols[w])
ax[0].set_yscale('log'); ax[0].set_xlabel('rescale factor $c$ at $t_{\\rm fit}$'); ax[0].set_ylabel(r'delay $t_{\rm gen}-t_{\rm fit}$'); ax[0].legend(frameon=False, fontsize=6)
ax[1].set_xlabel('rescale factor $c$'); ax[1].set_ylabel(r'$\|\theta\|$ at $t_{\rm gen}$'); ax[1].set_ylim(0, None)
ax[2].set_xlabel('rescale factor $c$'); ax[2].set_ylabel(r'$\|\theta\|$ just after rescale'); ax[2].set_ylim(0, None)
plt.tight_layout(); plt.savefig('/work/figs/e5_rescale.pdf'); plt.close()
