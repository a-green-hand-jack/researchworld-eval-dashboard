"""All-pairs scan: minimum number of removed / flipped / added comparisons (K) that reverses each
pair's order, for every dataset.  Output: results/pairs_<dataset>.csv"""
import sys, time, numpy as np, pandas as pd
sys.path.insert(0, '/work/code')
from common import *
import loaders
from multiprocessing import Pool

PROCS = 36
which = sys.argv[1:] or ['arena55k', 'arena55k_notie', 'mtbench_human', 'mtbench_gpt4', 'arena50k_human', 'nba', 'judges']

def save(df, name):
    df.to_csv(f'{RES}/pairs_{name}.csv', index=False); print(name, len(df), flush=True)

def nba_job(a):
    yr, home = a
    b = loaders.nba_seasons(home=home)[yr]
    df = pair_scan(b, modes=('remove', 'flip'), procs=1)
    df['season'] = yr
    return df

t0 = time.time()
if 'arena55k' in which:
    save(pair_scan(loaders.arena55k(), nmin=500, procs=PROCS), 'arena55k')
if 'arena55k_notie' in which:
    save(pair_scan(loaders.arena55k(ties='drop'), nmin=500, procs=PROCS), 'arena55k_notie')
if 'arena140k' in which:
    save(pair_scan(loaders.arena140k(), nmin=500, procs=PROCS), 'arena140k')
if 'mtbench_human' in which:
    save(pair_scan(loaders.mtbench('human')), 'mtbench_human')
if 'mtbench_gpt4' in which:
    save(pair_scan(loaders.mtbench('gpt4')), 'mtbench_gpt4')
if 'arena50k_human' in which:
    save(pair_scan(loaders.arena_judged('human'), nmin=500, procs=PROCS), 'arena50k_human')
if 'judges' in which:
    for jd in loaders.JUDGES:
        df = pair_scan(loaders.arena_judged(jd), nmin=500, procs=PROCS); df['judge'] = jd
        save(df, 'judge_' + jd)
if 'nba' in which:
    seasons = sorted(loaders.nba_seasons().keys())
    with Pool(PROCS) as p:
        dfs = p.map(nba_job, [(y, True) for y in seasons])
    save(pd.concat(dfs), 'nba')
    with Pool(PROCS) as p:
        dfs = p.map(nba_job, [(y, False) for y in seasons])
    save(pd.concat(dfs), 'nba_nohome')
print('done', time.time() - t0)
