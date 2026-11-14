"""Paired design: the SAME targets (ranks 2..31 by arithmetic mean) evaluated under every rule -> paired comparisons across rules.
Outputs results/common_<bench>.csv ; paired tests are in 02c_paired_tests.py"""
import sys, os, time, warnings
import numpy as np, pandas as pd
from scipy.stats import wilcoxon
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import data_utils as du
from exp_utils import gstar_card, gstar_ord
GS = (10, 100); RK = range(2, 32); _B = {}
def init(bench):
    B = du.LOADERS[bench](); S = B['S']; mean = S.mean(axis=1)
    _B.update(b=B, S=S, mean=mean, order=np.argsort(-mean, kind='stable'))
    pool = du.pool_for_ordinal(B, mean); _B['pool'] = pool; _B['Sp'] = S[pool]
    _B['agg'] = {r: rule_scores(S, r) for r in CARDINAL}
def work(job):
    rule, rank = job; warnings.simplefilter('ignore')
    t_full = int(_B['order'][rank - 1]); S = _B['S']; row = dict(rule=rule, rank=rank, target=_B['b']['models'][t_full])
    if rule in CARDINAL:
        agg = _B['agg'][rule]; T = np.delete(agg, t_full).max(); riv = np.delete(S, t_full, axis=0)
        row['already_first'] = bool(agg[t_full] > T); row['gstar'] = gstar_card(S, t_full, rule, T)
        for g in GS:
            x = solve_cardinal(S[t_full], riv, rule, g, T=T); row[f'K_{g}'] = x['K']; row[f'L1_{g}'] = x['L1']
    else:
        Sp = _B['Sp']; t = int(np.where(_B['pool'] == t_full)[0][0])
        sc = rule_scores(Sp, rule); row['already_first'] = bool(sc[t] > np.delete(sc, t).max()); row['gstar'] = gstar_ord(Sp, t, rule)
        for g in GS:
            if np.isnan(row['gstar']) or g < row['gstar'] - 1e-9: row[f'K_{g}'] = np.nan; row[f'L1_{g}'] = np.nan; continue
            xk = solve_ordinal(Sp, t, rule, g, 'K', time_limit=60); xl = solve_ordinal(Sp, t, rule, g, 'L1', time_limit=60)
            row[f'K_{g}'] = xk['K']; row[f'L1_{g}'] = xl['L1']
    return row
if __name__ == '__main__':
    tests = []
    for bench in ['helm', 'ollb6', 'bbh24']:
        t0 = time.time(); init(bench)
        with Pool(20, initializer=init, initargs=(bench,)) as p: rows = p.map(work, [(r, k) for r in RULES for k in RK], chunksize=1)
        df = pd.DataFrame(rows); df.insert(0, 'bench', _B['b']['name']); df.to_csv(f'results/common_{bench}.csv', index=False)
        print(bench, 'done', round(time.time() - t0, 1))
