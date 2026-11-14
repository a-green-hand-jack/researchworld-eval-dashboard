"""Task-subsampling experiment (HELM-MMLU): how do requirements scale with the number of tasks n?
For each m, draw random m-subsets of the 57 subjects (without replacement), recompute everything (incl. who the contenders are)."""
import sys, os, time, warnings
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
from exp_utils import contender_rows
MS = [6, 12, 24, 40]; DRAWS = 60; RANKS = list(range(2, 12)); GS = (10, 100)
D = du.load_helm()
def one(args):
    m, b = args; warnings.simplefilter('ignore')
    rng = np.random.default_rng(5000 + 100 * m + b)
    cols = rng.choice(D['S'].shape[1], size=m, replace=False); S = D['S'][:, cols]
    out = []
    for rule in RULES:
        df = pd.DataFrame(contender_rows(S, rule, RANKS, gs=GS, tl=20.0))
        rec = dict(m=m, draw=b, rule=rule, gstar=df['gstar'].median(), gap=df['gap'].median())
        for g in GS: rec[f'K_{g}'] = df[f'K_{g}'].median(); rec[f'L1_{g}'] = df[f'L1_{g}'].median(); rec[f'feas_{g}'] = df[f'K_{g}'].notna().mean()
        out.append(rec)
    return out
if __name__ == '__main__':
    t0 = time.time()
    with Pool(14) as p: res = p.map(one, [(m, b) for m in MS for b in range(DRAWS)], chunksize=1)
    pd.DataFrame([r for o in res for r in o]).to_csv('results/subsample_helm.csv', index=False)
    print('done', round(time.time() - t0, 1), 's')
