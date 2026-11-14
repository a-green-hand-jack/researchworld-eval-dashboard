"""Main experiment: minimum targeted investment to reach first place, per benchmark x rule x contender rank.

For benchmark b, rule A and rank r (2..R): target = model ranked r-th under A (within the rule's pool),
  gap     : aggregate gap to the current best rival (cardinal rules; in aggregate units)
  gstar   : smallest per-task gain cap g for which ANY plan wins (monotonicity => iff the all-in plan wins; bisection)
  K_g     : minimum breadth (#tasks touched) under per-task gain cap g, for g in G
  L1_g    : minimum magnitude (total score points gained) under cap g
Usage: python code/02_main.py [helm|ollb6|bbh24 ...]       -> results/main_<bench>.csv
"""
import sys, os, time, warnings
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib
from lib import *
import data_utils as du

G = [2, 5, 10, 20, 50, 100]
RMAX = {'cardinal': 31, 'ordinal': 21}
TL = 60.0
RES = os.path.join(du.ROOT, 'results'); os.makedirs(RES, exist_ok=True)
_B = {}

def init(bench):
    _B['b'] = du.LOADERS[bench]()
    B = _B['b']; S = B['S']
    mean = S.mean(axis=1)
    pool = du.pool_for_ordinal(B, mean)
    _B['pool'] = pool; _B['Sp'] = S[pool]
    _B['agg'] = {r: rule_scores(S, r) for r in CARDINAL}
    _B['aggp'] = {r: rule_scores(_B['Sp'], r) for r in ORDINAL}

def gstar(S, t, rule, riv_T=None):
    a = S[t]
    def wins(g):
        d = np.minimum(g, UB - a)
        if rule in CARDINAL:
            x = a + d
            return rule_scores(x[None], rule)[0] >= riv_T + EPS - 1e-12
        return is_first(S, t, rule, d)
    if not wins(UB): return np.nan
    lo, hi = 0.0, UB
    if wins(0.0): return 0.0
    for _ in range(40):
        m = 0.5 * (lo + hi)
        if wins(m): hi = m
        else: lo = m
    return hi

def work(job):
    rule, rank = job
    warnings.simplefilter('ignore')
    B = _B['b']; S = B['S']
    row = dict(bench=B['name'], rule=rule, rank=rank)
    if rule in CARDINAL:
        agg = _B['agg'][rule]; order = np.argsort(-agg, kind='stable'); t = int(order[rank - 1])
        T = np.delete(agg, t).max()
        row.update(target=B['models'][t], M=S.shape[0], n=S.shape[1], agg_t=agg[t], agg_best_rival=T, gap=T - agg[t])
        row['gstar'] = gstar(S, t, rule, T)
        riv = np.delete(S, t, axis=0)
        for g in G:
            r = solve_cardinal(S[t], riv, rule, g, T=T)
            row[f'K_{g}'] = r['K']; row[f'L1_{g}'] = r['L1']; row[f'opt_{g}'] = True
    else:
        Sp = _B['Sp']; agg = _B['aggp'][rule]; order = np.argsort(-agg, kind='stable'); t = int(order[rank - 1])
        row.update(target=B['models'][_B['pool'][t]], M=Sp.shape[0], n=Sp.shape[1], agg_t=agg[t],
                   agg_best_rival=np.delete(agg, t).max(), gap=np.delete(agg, t).max() - agg[t])
        row['gstar'] = gstar(Sp, t, rule)
        for g in G:
            if np.isnan(row['gstar']) or g < row['gstar'] - 1e-9:
                row[f'K_{g}'] = np.nan; row[f'L1_{g}'] = np.nan; row[f'opt_{g}'] = True; continue
            rk = solve_ordinal(Sp, t, rule, g, 'K', time_limit=TL)
            rl = solve_ordinal(Sp, t, rule, g, 'L1', time_limit=TL)
            row[f'K_{g}'] = rk['K']; row[f'L1_{g}'] = rl['L1']; row[f'opt_{g}'] = bool(rk.get('optimal', False) and rl.get('optimal', False))
    return row

if __name__ == '__main__':
    benches = sys.argv[1:] or ['helm', 'ollb6']
    for bench in benches:
        t0 = time.time(); init(bench)
        jobs = [(r, k) for r in CARDINAL for k in range(2, RMAX['cardinal'] + 1)] + \
               [(r, k) for r in ORDINAL for k in range(2, RMAX['ordinal'] + 1)]
        with Pool(20, initializer=init, initargs=(bench,)) as p: rows = p.map(work, jobs, chunksize=1)
        df = pd.DataFrame(rows); df.to_csv(os.path.join(RES, f'main_{bench}.csv'), index=False)
        print(bench, 'done', len(df), 'rows', round(time.time() - t0, 1), 's;',
              'non-optimal MILPs:', int((~df[[f'opt_{g}' for g in G]].all(axis=1)).sum()))
