"""Ablations on 150 random Arena-55k pairs (n>=500 comparisons): ridge strength, one-shot vs iterative search, linearised estimate."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from common import *
import loaders
from multiprocessing import Pool
_S = {}
def job(a):
    lam, i, j = a
    b = _S[lam]; th = b.base_fit()
    if th[i] < th[j]: i, j = j, i
    c = b.contrast(i, j); _, se = b.class_effects(th, b.W0, c); n = b.comparisons_per_model()
    h2h = b.W0[((b.A == i) & (b.B == j)) | ((b.A == j) & (b.B == i))].sum()
    row = dict(lam=lam, i=i, j=j, z=(c @ th) / se, n_ij=n[i] + n[j] - h2h)
    for m in ('remove', 'flip', 'add'):
        r = b.attack(i, j, m); row['K_' + m] = r['K']; row['Klin_' + m] = r['K_lin']
        if lam == 1e-3: row['K1shot_' + m] = b.one_shot(i, j, m)
    return row
if __name__ == '__main__':
    lams = [1e-3, 1e-2, 1e-1, 1.0, 10.0]
    for l in lams: _S[l] = loaders.arena55k(lam=l)
    b = _S[1e-3]; n = b.comparisons_per_model(); ids = [k for k in range(b.m) if n[k] >= 500]
    rng = np.random.default_rng(5)
    allp = [(i, j) for i in ids for j in ids if i < j]
    sel = [allp[k] for k in rng.choice(len(allp), 150, replace=False)]
    with Pool(8) as p: rows = p.map(job, [(l, i, j) for l in lams for i, j in sel], chunksize=4)
    pd.DataFrame(rows).to_csv(f'{RES}/ablate_lambda.csv', index=False); print('done')
