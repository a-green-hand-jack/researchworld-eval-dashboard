"""E2 (group transfer G1/G2, cost P4) and E0 (leakage) analyses.  python exp/analyze_e2.py  -> results/E2/*.csv
Unit of replication = held-out model; paired bootstrap over models, Holm within each declared family."""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A
from settings import mteb_setting
os.makedirs('results/E2', exist_ok=True)
pd.set_option('display.width', 220)


def pm_of(d):
    return A.per_model(A.load(f'results/{d}')) if glob.glob(f'results/{d}/rec_rep*.parquet') else None


# ---- G1 / G2 group transfer
rows = []
for d in sorted(glob.glob('results/A[12]_tgt*')):
    name = os.path.basename(d); m, grp = name.split('_tgt'); pm = pm_of(name)
    if pm is None: continue
    for tag, a_, b_ in (('G1 greedyAT vs random', ('greedyAT', 'fa'), ('random', 'fa')), ('G2 greedyAT vs greedyAcomp', ('greedyAT', 'fa'), ('greedyAcomp', 'fa'))):
        t = A.paired(pm, a_, b_, 'mse', ks=[k for k in (3, 8) if k in set(pm.k)]); t['test'] = tag; t['matrix'] = m; t['group'] = grp; t['family'] = 'G'; rows.append(t)
    # exploratory: each selector vs random at every k, FA inference and the mean predictor
    for s in sorted(set(pm.selector) - {'random'}):
        t = A.paired(pm, (s, 'fa'), ('random', 'fa'), 'mse'); t['test'] = f'explor {s} vs random'; t['matrix'] = m; t['group'] = grp; t['family'] = 'explor'; rows.append(t)
if rows:
    G = pd.concat(rows, ignore_index=True)
    for fam, ix in G.groupby('family').groups.items():
        if fam == 'G': G.loc[ix, 'p_adj'] = A.holm(G.loc[ix, 'p'].values)
    G.to_csv('results/E2/group_paired.csv', index=False)
    print(G[(G.family == 'G')][['matrix', 'group', 'test', 'k', 'diff', 'rel', 'lo', 'hi', 'p_adj', 'n_models']].round(4).to_string())

# ---- P4 cost
cr = []; cp = []
for m in ('A1', 'A2'):
    s = mteb_setting(m); total = float(np.nansum(s['cost']))
    parts = [pm_of(f'{m}_cost'), pm_of(f'{m}_costA')]
    parts = [p for p in parts if p is not None]
    if not parts: continue
    pm = pd.concat(parts, ignore_index=True).drop_duplicates(['model', 'k', 'selector', 'method'])
    mean0 = pm[(pm.selector == 'random') & (pm.method == 'mean')].groupby('model').mse.mean()
    res = {}
    for (sel, me), g in pm.groupby(['selector', 'method']):
        for f in (0.02, 0.05, 0.1, 0.2, 0.4):
            b = f * total
            out = {}
            for mod, gg in g.groupby('model'):
                ok = gg[gg.cost_S <= b]
                out[mod] = ok.sort_values('k').mse.iloc[-1] if len(ok) else mean0.get(mod, np.nan)
            res[(sel, me, f)] = pd.Series(out)
    for (sel, me, f), s_ in res.items():
        v = s_.dropna().values
        if len(v) < 3: continue
        idx = A.boot_idx(len(v), 2000, 0); bs = v[idx].mean(1)
        cr.append(dict(matrix=m, selector=sel, inference=me, budget_frac=f, budget_sec=f * total, rmse=np.sqrt(v.mean()), ci_lo=np.sqrt(np.percentile(bs, 2.5)), ci_hi=np.sqrt(np.percentile(bs, 97.5)), n_models=len(v)))
    for f in (0.05, 0.1, 0.2):
        for tag, a_, b_ in (('P4 greedyAcost vs greedyA (fa)', ('greedyAcost', 'fa', f), ('greedyA', 'fa', f)),
                            ('explor greedyAcost vs random (fa)', ('greedyAcost', 'fa', f), ('random', 'fa', f)),
                            ('explor greedyGaussCost vs greedyGauss (gcov)', ('greedyGaussCost', 'gcov', f), ('greedyGauss', 'gcov', f))):
            if a_ in res and b_ in res:
                d = (res[a_] - res[b_]).dropna(); v = d.values
                idx = A.boot_idx(len(v), 10000, 0); bs = v[idx].mean(1)
                p = 2 * min((bs <= 0).mean(), (bs >= 0).mean()); p = max(p, 1e-4)
                cp.append(dict(matrix=m, test=tag, budget_frac=f, diff=v.mean(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), p=p, rel=v.mean() / res[b_].mean(), n_models=len(v), family='P4' if tag.startswith('P4') else 'explor'))
if cr and cp:
    pd.DataFrame(cr).to_csv('results/E2/cost_curve.csv', index=False)
    C = pd.DataFrame(cp)
    ix = C.family == 'P4'; C.loc[ix, 'p_holm'] = A.holm(C.loc[ix, 'p'].values)
    C.to_csv('results/E2/cost_paired.csv', index=False)
    print(C.round(4).to_string())
    print(pd.DataFrame(cr).pivot_table(index=['matrix', 'selector', 'inference'], columns='budget_frac', values='rmse').round(3).to_string())

# ---- E0 leak
rows = []
for m in ('A1', 'A2'):
    a_, b_ = pm_of(m), pm_of(f'{m}_leak')
    if a_ is None or b_ is None: continue
    for sel, me in sorted(set(zip(b_.selector, b_.method))):
        if (sel, me) not in set(zip(a_.selector, a_.method)): continue
        x = a_[(a_.selector == sel) & (a_.method == me)].pivot(index='model', columns='k', values='mse')
        y = b_[(b_.selector == sel) & (b_.method == me)].pivot(index='model', columns='k', values='mse')
        com = x.index.intersection(y.index)
        for k in (3, 8, 20):
            if k in x.columns and k in y.columns:
                d = (y.loc[com, k] - x.loc[com, k]).dropna().values   # leak - clean (negative: leakage makes the error look smaller)
                idx = A.boot_idx(len(d), 4000, 0); bs = d[idx].mean(1)
                rows.append(dict(matrix=m, selector=sel, inference=me, k=k, rmse_clean=np.sqrt(x.loc[com, k].mean()), rmse_leak=np.sqrt(y.loc[com, k].mean()),
                                 diff_mse=d.mean(), lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), n_models=len(d)))
if rows:
    L = pd.DataFrame(rows); L.to_csv('results/E2/leak_paired.csv', index=False); print(L.round(4).to_string())
