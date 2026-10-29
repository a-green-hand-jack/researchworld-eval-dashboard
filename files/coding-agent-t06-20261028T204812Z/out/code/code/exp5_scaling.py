"""Subsample Arena-55k / MT-Bench-human to size n and attack FIXED pairs (defined on the full data):
P_sig = #1 vs nearest challenger beaten at z>=2; P_mid = ranks 5 vs 10.  results/scaling_<ds>.csv"""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from common import *
import loaders, btlib
from multiprocessing import Pool
_S = {}
def pairs_of(b0):
    th = b0.base_fit(); r = b0.ranking()
    zs = [(th[r[0]] - th[r[t]]) / b0.class_effects(th, b0.W0, b0.contrast(r[0], r[t]))[1] for t in range(b0.m)]
    tsig = next(t for t in range(1, b0.m) if zs[t] >= 2)
    return {'P_sig': (r[0], r[tsig]), 'P_mid': (r[min(4, b0.m - 3)], r[min(9, b0.m - 1)])}
def job(a):
    n, rep = a
    b0 = _S['b']; rng = np.random.default_rng(777 + 1000 * n + rep)
    w = btlib.subsample_weights(b0, n, rng) if n < b0.n_total else b0.W0.copy()
    b = btlib.with_weights(b0, w); th = b.base_fit(); nn = b.comparisons_per_model(); out = []
    for pname, (i, j) in _S['pairs'].items():
        if th[i] <= th[j]: out.append(dict(n=n, rep=rep, pair=pname, reversed=True)); continue
        c = b.contrast(i, j); se = np.sqrt(c @ np.linalg.solve(b.hess(th, b.W0), c))
        h2h = b.W0[((b.A == i) & (b.B == j)) | ((b.A == j) & (b.B == i))].sum()
        row = dict(n=n, rep=rep, pair=pname, reversed=False, z=(c @ th) / se, n_ij=nn[i] + nn[j] - h2h)
        for m in ('remove', 'flip', 'add'): row['K_' + m] = b.attack(i, j, m)['K']
        out.append(row)
    return out
if __name__ == '__main__':
    for name, b0, sizes, reps in [('arena55k', loaders.arena55k(), [1000, 2000, 4000, 8000, 16000, 32000, 57477], 100),
                                  ('mtbench_human', loaders.mtbench('human'), [300, 600, 1200, 2400, 3355], 100)]:
        _S['b'] = b0; _S['pairs'] = pairs_of(b0)
        print(name, {k: (b0.names[i], b0.names[j]) for k, (i, j) in _S['pairs'].items()})
        jobs = [(n, r) for n in sizes for r in (range(reps) if n < b0.n_total else range(1))]
        with Pool(36) as p: rows = p.map(job, jobs, chunksize=1)
        pd.DataFrame([r for rr in rows for r in rr]).to_csv(f'{RES}/scaling_{name}.csv', index=False); print(name, flush=True)
