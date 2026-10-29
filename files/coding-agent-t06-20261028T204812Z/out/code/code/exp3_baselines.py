"""Random-edit and heuristic baselines, and composition of the optimal edit sets.
For each dataset: target statement = dethrone observed #1 by its nearest challenger (the pair with min K_remove
among ranks 2..5).  Outputs results/baselines.csv and results/composition.csv"""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from common import *
import loaders, btlib
from multiprocessing import Pool

rng0 = 12345

def winner(b):
    return np.where(b.Y == 1.0, b.A, np.where(b.Y == 0.0, b.B, -1))

def loser(b):
    return np.where(b.Y == 1.0, b.B, np.where(b.Y == 0.0, b.A, -1))

def masks(b, i, j):
    win, los = winner(b), loser(b)
    tie = b.Y == 0.5
    inv = lambda m: m  # alias
    return {
        'remove': {
            'h2h (i beats j)': (win == i) & (los == j),
            'i wins vs anyone': (win == i),
            'i wins or j losses': (win == i) | (los == j),
            'all (influence-greedy)': None},
        'flip': {
            'h2h only': ((b.A == i) & (b.B == j)) | ((b.A == j) & (b.B == i)),
            'i-involving only': (b.A == i) | (b.B == i),
            'all (influence-greedy)': None},
        'add': {
            'h2h (j beats i)': (win == j) & (los == i),
            'target-only (j beats anyone)': (win == j),
            'all (influence-greedy)': None}}

def random_flip_prob(b, i, j, mode, K, trials, rng):
    """fraction of trials in which K random edits reverse the pair"""
    c = b.contrast(i, j); th0 = b.base_fit(); hit = 0
    for _ in range(trials):
        if mode == 'remove':
            w = b.W0 - rng.multivariate_hypergeometric(b.W0.astype(np.int64), min(K, b.n_total))
        elif mode == 'flip':
            # K random comparisons get a random different outcome (same pair)
            w = b.W0.copy()
            src = rng.multivariate_hypergeometric(b.W0.astype(np.int64), min(K, b.n_total))
            for cidx in np.where(src > 0)[0]:
                g = b.group[cidx]; idx = b._gorder[b._gstart[g]:b._gstart[g + 1]]
                alts = idx[idx != cidx]
                w[cidx] -= src[cidx]
                w[alts] += rng.multinomial(int(src[cidx]), np.ones(len(alts)) / len(alts))
        else:  # add: K naive votes 'j beats m' for random m (random rigging of the target)
            w = b.W0.copy()
            tab = -np.ones((b.m, b.m), int)
            for cidx in range(len(b.A)):
                if b.Y[cidx] == 1.0: tab[b.A[cidx], b.B[cidx]] = cidx
                elif b.Y[cidx] == 0.0: tab[b.B[cidx], b.A[cidx]] = cidx
            opp = np.array([m for m in range(b.m) if m != j])
            w[tab[j, opp]] += rng.multinomial(K, np.ones(len(opp)) / len(opp))
        hit += c @ b.fit(w, th0) <= 0
    return hit / trials

def run(name, b, modes, trials=200):
    rng = np.random.default_rng(rng0)
    r = b.ranking(); th = b.base_fit()
    zs = [(th[r[0]] - th[r[t]]) / b.class_effects(th, b.W0, b.contrast(r[0], r[t]))[1] for t in range(b.m)]
    tsig = next(t for t in range(1, b.m) if zs[t] >= 2)   # nearest challenger beaten at z>=2
    res = {m: [(b.attack(r[0], r[tsig], m)['K'], tsig)] for m in modes}
    brow, crow = [], []
    for m in modes:
        K, t = min(res['remove'] if m == 'remove' else res[m]); j = r[t]; i = r[0]
        out = b.attack(i, j, m)
        # composition of the optimal edit set (remove): relative to W0
        if m == 'remove':
            d = b.W0 - out['w']; win, los = winner(b), loser(b)
            cats = {'i beats j (h2h)': (win == i) & (los == j), 'j beats i (h2h)': (win == j) & (los == i),
                    'i beats third party': (win == i) & (los != j), 'third party beats j': (los == j) & (win != i),
                    'ties involving i or j': (b.Y == .5) & ((b.A == i) | (b.B == i) | (b.A == j) | (b.B == j)),
                    'other (neither i nor j)': (win != i) & (los != j) & (win != j) & (los != i) & ~((b.Y == .5) & ((b.A == i) | (b.B == i) | (b.A == j) | (b.B == j)))}
            tot = d.sum(); used = np.zeros(len(d), bool); rowc = dict(dataset=name, K=tot)
            for k, mk in cats.items():
                rowc[k] = d[mk & ~used].sum() / tot; used |= mk
            # share of ALL comparisons in each category (for reference)
            crow.append(rowc)
        for label, mk in masks(b, i, j)[m].items():
            if mk is None: K1 = out['K']
            else: K1 = b.attack(i, j, m, allowed=mk)['K']
            brow.append(dict(dataset=name, mode=m, statement=f'top1 vs rank {t+1} (z={zs[t]:.1f})', baseline=label, K=K1, K_star=out['K']))
        for mult in (0.5, 1, 2, 5, 10, 50):
            Kr = int(round(mult * out['K']))
            if Kr < 1: Kr = 1
            if Kr > b.n_total and m != 'add': continue
            p = random_flip_prob(b, i, j, m, Kr, trials if m != 'flip' or Kr < 3000 else 20, rng)
            brow.append(dict(dataset=name, mode=m, statement=f'top1 vs rank {t+1} (z={zs[t]:.1f})', baseline=f'random K={mult}xK*', K=Kr, K_star=out['K'], p_flip=p))
    print(name, flush=True)
    return brow, crow

def task(a):
    name, = a
    if name == 'arena55k': return run(name, loaders.arena55k(), ['remove', 'flip', 'add'], trials=100)
    if name == 'mtbench_human': return run(name, loaders.mtbench('human'), ['remove', 'flip', 'add'])
    if name == 'mtbench_gpt4': return run(name, loaders.mtbench('gpt4'), ['remove', 'flip', 'add'])
    if name.startswith('nba'):
        return run(name, loaders.nba_seasons()[int(name[3:])], ['remove', 'flip'])

if __name__ == '__main__':
    names = ['arena55k', 'mtbench_human', 'mtbench_gpt4'] + [f'nba{y}' for y in (1960, 1985, 2000, 2010, 2015)]
    with Pool(8) as p: outs = p.map(task, [(n,) for n in names])
    pd.DataFrame([r for o in outs for r in o[0]]).to_csv(f'{RES}/baselines.csv', index=False)
    pd.DataFrame([r for o in outs for r in o[1]]).to_csv(f'{RES}/composition.csv', index=False)
