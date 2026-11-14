"""E4: other scale axes (depth, MLP width, d_mlp vs d_model).  Writes tables/e4_table.csv, figs/e4_arch.pdf"""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
import ana
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams.update({'font.size': 9, 'axes.spines.top': False, 'axes.spines.right': False, 'figure.dpi': 150})
d4 = ana.load('/work/results/e4_arch')
d1 = ana.load('/work/results/e1_width'); d1 = d1[(d1.seed < 4)].copy()   # same 4 seeds as E4
d1['layers'] = 1; d1['mlp_mult'] = 4
d4['layers'] = d4.layers.fillna(1); d4['mlp_mult'] = d4.mlp_mult.fillna(4)
df = pd.concat([d4, d1], ignore_index=True)
rng = np.random.default_rng(4)
def bm(x, n=3000):
    x = np.where(np.isnan(x), np.inf, np.asarray(x, float))
    b = np.array([np.median(x[rng.integers(0, len(x), len(x))]) for _ in range(n)])
    return np.percentile(b, [2.5, 97.5])
rows = []
for (arch, L, mm, wd, w), g in df.groupby(['arch', 'layers', 'mlp_mult', 'wd', 'width']):
    if arch == 'tf' and not ((L == 1 and mm == 4 and wd == 1.0 and w in (16, 24, 32, 64, 128)) or L > 1 or mm != 4):
        continue
    lo, hi = bm(g.t_gen.values)
    rows.append(dict(arch=arch, layers=int(L), mlp_mult=int(mm), wd=wd, width=int(w), P=int(g.P.iloc[0]), n=len(g), gen=int(g.gen.sum()),
                     t_fit=np.nanmedian(g.t_fit) if g.fit.any() else np.nan, t_gen=np.median(np.where(g.gen, g.t_gen, np.inf)), lo=lo, hi=hi,
                     va_fit=g.va_fit.median(), fin_va=g.fin_va.median()))
T = pd.DataFrame(rows); T.to_csv('/work/tables/e4_table.csv', index=False); print(T.to_string())
fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.5))
CAP = 30000
def runs(sel):
    return df[sel].sort_values('P')
def plot(a, sub, color, label, dx=1.0):
    ws = sorted(sub.P.unique()); meds = []
    for P in ws:
        g = sub[sub.P == P]
        ok_ = g[g.gen]; a.scatter([P * dx] * len(ok_), ok_.t_gen, s=6, color=color, alpha=.5)
        c_ = g[~g.gen]; a.scatter([P * dx] * len(c_), [CAP] * len(c_), s=9, marker='^', facecolors='none', edgecolors=color, lw=.7)
        meds.append(np.median(np.where(g.gen, g.t_gen, np.inf)))
    ok_ = [(P * dx, m) for P, m in zip(ws, meds) if np.isfinite(m)]
    if ok_:
        a.plot(*zip(*ok_), 'o-', color=color, ms=3, lw=1, label=label)
    else:
        a.plot([], [], 'o-', color=color, label=label)
for wd, c, dx in [(1.0, 'C0', 0.97), (5.0, 'C3', 1.03)]:
    plot(ax[0], runs((df.arch == 'mlp') & (df.wd == wd)), c, f'MLP wd={wd:g}', dx)
ax[0].set_title('MLP (2 hidden layers)', fontsize=8)
for L, c, dx in [(1, 'C0', 0.95), (2, 'C2', 1.0), (3, 'C3', 1.05)]:
    plot(ax[1], runs((df.arch == 'tf') & (df.layers == L) & (df.mlp_mult == 4) & (df.wd == 1.0) & df.width.isin([16, 24, 32, 64, 128] if L == 1 else [32, 64])), c, f'{L} layer(s)', dx)
ax[1].set_title('Transformer depth', fontsize=8)
for a in ax[:2]:
    a.set_xscale('log'); a.set_yscale('log'); a.set_xlabel('parameters P'); a.axhline(CAP, color='gray', ls=':', lw=.7); a.legend(frameon=False, fontsize=6, loc='lower left')
ax[0].set_ylabel(r'$t_{\rm gen}$ (steps); $\triangle$: not reached')
# (c) d_model vs d_mlp
cells = [(16, 4), (16, 16), (64, 1), (64, 4), (64, 16)]
for i, (w, mm) in enumerate(cells):
    g = df[(df.arch == 'tf') & (df.layers == 1) & (df.wd == 1.0) & (df.width == w) & (df.mlp_mult == mm)]
    ok_ = g[g.gen]; ax[2].scatter([i] * len(ok_), ok_.t_gen, s=8, color='C4', alpha=.6)
    c_ = g[~g.gen]; ax[2].scatter([i] * len(c_), [CAP] * len(c_), s=10, marker='^', facecolors='none', edgecolors='C4', lw=.7)
    m = np.median(np.where(g.gen, g.t_gen, np.inf))
    if np.isfinite(m): ax[2].plot([i - .25, i + .25], [m, m], 'k-', lw=1)
ax[2].set_xticks(range(len(cells))); ax[2].set_xticklabels([f'$d$={w}\n$d_{{mlp}}$={mm*w}\nP={int(df[(df.arch=="tf")&(df.layers==1)&(df.width==w)&(df.mlp_mult==mm)].P.iloc[0])//1000}k' for w, mm in cells], fontsize=5)
ax[2].set_yscale('log'); ax[2].axhline(CAP, color='gray', ls=':', lw=.7); ax[2].set_title(r'$d_{\rm model}$ vs $d_{\rm mlp}$ (1 layer)', fontsize=8)
plt.tight_layout(); plt.savefig('/work/figs/e4_arch.pdf'); plt.close()
