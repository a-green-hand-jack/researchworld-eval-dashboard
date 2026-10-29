"""Headline statements with bootstrap uncertainty.
Per dataset instance and per bootstrap replicate (replicate 0 = observed data) compute, for the
replicate's own ranking, the minimum K (remove / flip / add) that
  top1 : dethrones the #1 model (best over challengers ranked 2..5)
  topk : changes membership of the top-k set, k in {3,5,10} (pairs within 3 ranks of the boundary)
  adj  : swaps some adjacent pair among the top 10
Also stores bootstrap displacement (number of comparisons that differ between replicate and data)
and whether the replicate changes the observed top-1."""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from common import *
import loaders, btlib
from multiprocessing import Pool

B = int(sys.argv[2]) if len(sys.argv) > 2 else 200
PROCS = 36
_S = {}

def statements(b, modes):
    th = b.base_fit(); r = b.ranking(); out = {}
    def K(i, j, m): return b.attack(i, j, m)['K']
    for m in modes:
        ks = [(K(r[0], r[t], m), t + 1) for t in range(1, min(5, b.m))]
        k1, ch = min(ks)
        out[f'top1_{m}'] = k1; out[f'top1_chal_{m}'] = ch
        for k in (3, 5, 10):
            if b.m <= k + 1: continue
            best = np.inf
            for a in range(max(0, k - 3), k):
                for c in range(k, min(b.m, k + 3)):
                    best = min(best, K(r[a], r[c], m))
            out[f'top{k}_{m}'] = best
        out[f'adj_{m}'] = min(K(r[t], r[t + 1], m) for t in range(0, min(10, b.m - 1)))
    c = b.contrast(r[0], r[1]); _, se = b.class_effects(th, b.W0, c)
    # 'significant lead': nearest-ranked challenger that the #1 model beats at z>=2
    for t in range(1, b.m):
        c2 = b.contrast(r[0], r[t]); _, se2 = b.class_effects(th, b.W0, c2)
        if (c2 @ th) / se2 >= 2: break
    else: t = None
    if t is not None:
        out['sig_rank'] = t + 1; out['sig_z'] = (c2 @ th) / se2
        for m in modes: out[f'sig_{m}'] = K(r[0], r[t], m)
    out['z12'] = (c @ th) / se; out['N'] = b.n_total; out['top1'] = b.names[r[0]]
    return out

def job(rep):
    b0 = _S['board']; modes = _S['modes']
    if rep == 0:
        b = b0; disp = 0; same = True; flip12 = False
    else:
        rng = np.random.default_rng(1000 + rep + _S['seed'])
        w = btlib.bootstrap_weights(b0, rng); b = btlib.with_weights(b0, w)
        disp = float(np.maximum(b0.W0 - w, 0).sum())
        th = b.base_fit(); r0 = b0.ranking(); r1 = b.ranking()
        same = bool(r1[0] == r0[0]); flip12 = bool(th[r0[1]] > th[r0[0]])
    row = statements(b, modes); row.update(rep=rep, disp=disp, top1_same=same, pair12_flip=flip12)
    return row

def run(name, board, modes=('remove', 'flip', 'add'), B=B, procs=PROCS, seed=0):
    _S.update(board=board, modes=modes, seed=seed)
    with Pool(procs) as p:
        rows = p.map(job, range(B + 1), chunksize=1)
    df = pd.DataFrame(rows); df['dataset'] = name
    df.to_csv(f'{RES}/boot_{name}.csv', index=False); print(name, flush=True)
    return df

if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'main'
    t0 = time.time()
    if which == 'main':
        run('arena55k', loaders.arena55k())
        run('arena55k_notie', loaders.arena55k(ties='drop'))
        run('mtbench_human', loaders.mtbench('human'))
        run('mtbench_gpt4', loaders.mtbench('gpt4'))
        run('arena50k_human', loaders.arena_judged('human'))
    elif which == 'extra':
        run('arena140k', loaders.arena140k())
    elif which == 'judges':
        for jd in loaders.JUDGES:
            run('judge_' + jd, loaders.arena_judged(jd), B=min(B, 100))
    elif which == 'nba':
        seasons = loaders.nba_seasons()
        for yr, b in seasons.items():
            _S.update(board=b, modes=('remove', 'flip'), seed=yr)
            with Pool(PROCS) as p: rows = p.map(job, range(B + 1), chunksize=1)
            df = pd.DataFrame(rows); df['dataset'] = f'nba{yr}'; df.to_csv(f'{RES}/boot_nba{yr}.csv', index=False)
        print('nba done')
    print('time', time.time() - t0)
