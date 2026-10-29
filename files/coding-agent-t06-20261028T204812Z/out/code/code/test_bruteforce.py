"""Sanity check: greedy+refit witness vs exhaustive search over removal sets on tiny BT instances."""
import sys, itertools, numpy as np
sys.path.insert(0, '/work/code')
from btlib import build_board

def compositions(K, caps):
    # all r with sum r = K, 0<=r<=caps (recursive)
    def rec(i, left):
        if i == len(caps) - 1:
            if left <= caps[i]: yield (left,)
            return
        for x in range(min(left, caps[i]) + 1):
            for rest in rec(i + 1, left - x): yield (x,) + rest
    yield from rec(0, K)

rng = np.random.default_rng(0)
res = []
for inst in range(40):
    m = 4
    theta = rng.normal(0, 0.5, m)
    a, b, y = [], [], []
    for i in range(m):
        for j in range(i + 1, m):
            n = rng.poisson(6)
            for _ in range(n):
                p = 1 / (1 + np.exp(-(theta[i] - theta[j])))
                a.append(i); b.append(j); y.append(float(rng.random() < p))
    bd = build_board(list(range(m)), a, b, y, outcomes=(0.0, 1.0), lam=1e-2)
    th = bd.base_fit(); r = bd.ranking(); i, j = r[0], r[1]
    out = bd.attack(i, j, 'remove')
    if not out['feasible'] or out['K'] > 7: continue
    # exhaustive: smallest K' with any removal set flipping
    nz = np.where(bd.W0 > 0)[0]; caps = [int(bd.W0[c]) for c in nz]
    c = bd.contrast(i, j); best = None
    for K in range(1, out['K'] + 1):
        found = False
        for rr in compositions(K, caps):
            w = bd.W0.copy(); w[nz] -= np.array(rr)
            if c @ bd.fit(w, th) <= 0: found = True; break
        if found: best = K; break
    res.append((out['K'], best, out['K_lin']))
    print(inst, 'greedy K', out['K'], 'exhaustive K', best, 'K_lin', out['K_lin'], flush=True)
res = np.array(res)
print('instances', len(res), 'greedy==exhaustive in', int((res[:, 0] == res[:, 1]).sum()))
