"""Measurement-noise robustness (HELM-MMLU): parametric bootstrap of the score matrix.
Each model x subject accuracy p (observed) is re-drawn as Binomial(n_eval, p)/n_eval (n_eval from HELM); every statistic
is recomputed on each draw, INCLUDING which model is the rank-r contender.
Outputs results/noise_helm_draws.csv (per draw x rule: median over contenders ranks 2..11) and results/noise_helm_winner.csv."""
import sys, os, time, warnings
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
from exp_utils import contender_rows
B = 100; RANKS = list(range(2, 12)); GS = (10, 100)
D = du.load_helm()

def one(b):
    warnings.simplefilter('ignore')
    rng = np.random.default_rng(1000 + b)
    p = np.clip(D['S'] / 100.0, 0.0, 1.0)
    S = rng.binomial(D['neval'].astype(int), p) / D['neval'] * 100.0
    out = []; win = []
    for rule in RULES:
        rows = contender_rows(S, rule, RANKS, gs=GS, tl=30.0)
        df = pd.DataFrame(rows)
        rec = dict(draw=b, rule=rule, gstar=df['gstar'].median(), gap=df['gap'].median())
        for g in GS:
            rec[f'K_{g}'] = df[f'K_{g}'].median(); rec[f'L1_{g}'] = df[f'L1_{g}'].median(); rec[f'feas_{g}'] = df[f'K_{g}'].notna().mean()
        out.append(rec)
        win.append(dict(draw=b, rule=rule, winner=int(np.argmax(rule_scores(S, rule)))))
    return out, win

if __name__ == '__main__':
    t0 = time.time()
    with Pool(20) as p: res = p.map(one, range(B), chunksize=1)
    pd.DataFrame([r for o, _ in res for r in o]).to_csv('results/noise_helm_draws.csv', index=False)
    W = pd.DataFrame([r for _, w in res for r in w])
    obs = {r: int(np.argmax(rule_scores(D['S'], r))) for r in RULES}
    W['obs_winner'] = W['rule'].map(obs); W['same'] = W['winner'] == W['obs_winner']
    W['winner_name'] = W['winner'].map(lambda i: D['models'][i])
    W.to_csv('results/noise_helm_winner.csv', index=False)
    print('done', round(time.time() - t0, 1), 's')
