"""Synthetic latent-factor experiment: s_mj = clip(60 + theta_m + b_j + sigma * eps_mj, 0, 100); vary idiosyncratic sd sigma and n.
Shows how the dependence of the requirements on the rule changes with the task-specific variation (where the conclusions flip)."""
import sys, os, time, warnings
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
from exp_utils import contender_rows, additive_residual_sd
M = 80; NS = [12, 57]; SIGMAS = [1, 2, 4, 8, 16]; REPS = 40; RANKS = list(range(2, 12)); GS = (10, 100)
def gen(n, sigma, rng):
    th = rng.normal(0, 10, M); b = rng.normal(0, 8, n)
    return np.clip(60 + th[:, None] + b[None, :] + sigma * rng.normal(size=(M, n)), 0, 100)
def one(args):
    n, sigma, rep = args; warnings.simplefilter('ignore')
    rng = np.random.default_rng(777 + 1000 * n + 10 * sigma + rep * 7919 % 100003)
    S = gen(n, sigma, rng); out = []
    for rule in RULES:
        df = pd.DataFrame(contender_rows(S, rule, RANKS, gs=GS, tl=20.0))
        rec = dict(n=n, sigma=sigma, rep=rep, rule=rule, gstar=df['gstar'].median(), gap=df['gap'].median())
        for g in GS: rec[f'K_{g}'] = df[f'K_{g}'].median(); rec[f'L1_{g}'] = df[f'L1_{g}'].median(); rec[f'feas_{g}'] = df[f'K_{g}'].notna().mean()
        out.append(rec)
    return out
if __name__ == '__main__':
    t0 = time.time()
    anch = {}
    for k, f in du.LOADERS.items():
        try: B = f(); anch[B['name']] = additive_residual_sd(B['S'][:2000] if B['S'].shape[0] > 2000 else B['S'])
        except Exception as e: print('skip', k, e)
    pd.Series(anch, name='additive_residual_sd').to_csv('results/additive_residual_sd.csv'); print(anch)
    with Pool(14) as p: res = p.map(one, [(n, s, r) for n in NS for s in SIGMAS for r in range(REPS)], chunksize=1)
    pd.DataFrame([r for o in res for r in o]).to_csv('results/synthetic.csv', index=False)
    print('done', round(time.time() - t0, 1), 's')
