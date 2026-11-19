"""Experiment 2: sweeps around the main result (target = runner-up, plus rank 5 for the breadth cap).
 (a) scaling in number of tasks m (random task subsets, 30 draws)
 (b) pool size N (top-N models by baseline mean)
 (c) cap on number of tasks touched (kmax)
 (d) cost model: L1 vs L2^2 (diminishing returns) vs item-weighted L1 (cost proportional to #test items of the task)
 (e) cross-rule spillover: optimum for rule A evaluated under rule B
 (f) calibration: per-task gains observed between OLL base models and their fine-tunes
Outputs results/exp2_*.csv
"""
import time, numpy as np, pandas as pd, multiprocessing as mp
import common as K, core as C
from exp1_main import solve_all, uniform_cost

SEED = 7
NPROC = 12
FAST = ['mean', 'trim25', 'median', 'max', 'min', 'geomean', 'harmonic', 'condorcet', 'plurality']  # borda handled separately (slow)

def scaling_job(a):
    ds, m, draw, seed = a
    cfg = K.DATASETS[ds]; D = K.load(ds, cfg['pool']); S0 = D['S']
    rng = np.random.default_rng(seed); cols = rng.choice(S0.shape[1], size=m, replace=False)
    S = S0[:, cols]
    # re-rank by the mean on the subset; targets = positions 2..3 under that ranking
    order = np.argsort(-S.mean(1), kind='stable'); S = S[order]
    rows = solve_all(S, [1, 2], K.RULES if ds != 'oll39' or m <= 20 else FAST)
    for r in rows: r.update(dataset=ds, m=m, draw=draw)
    return rows

def pool_job(a):
    ds, N = a
    D = K.load(ds, N); S = D['S']
    rows = solve_all(S, [1, 2, 3, 4], FAST if N > 300 and ds == 'oll39' else K.RULES)
    for r in rows: r.update(dataset=ds, pool=N)
    return rows

def kmax_job(a):
    ds, k = a
    cfg = K.DATASETS[ds]; D = K.load(ds, cfg['pool']); S = D['S']
    rows = []
    for rule in ('mean', 'trim25', 'median', 'borda', 'condorcet'):
        if rule == 'borda' and ds == 'oll39': continue
        rows += solve_all(S, [1, 4], [rule], kmax=k)
    for r in rows: r.update(dataset=ds, kmax=k)
    return rows

def cost_job(a):
    ds, variant = a
    cfg = K.DATASETS[ds]; D = K.load(ds, cfg['pool']); S = D['S']; n = D['n']; m = S.shape[1]
    rows = []
    if variant == 'L1': rows = solve_all(S, [1, 2, 3, 4], K.RULES if ds != 'oll39' else FAST)
    elif variant == 'L2':
        rows = solve_all(S, [1, 2, 3, 4], ['mean', 'max', 'min'], p=2)
    elif variant == 'items':
        cw = n / n.mean()      # cost per score point proportional to the number of test items of the task
        rows = solve_all(S, [1, 2, 3, 4], K.RULES if ds != 'oll39' else FAST, cw=cw)
    for r in rows: r.update(dataset=ds, variant=variant)
    return rows

def spill_job(ds):
    cfg = K.DATASETS[ds]; D = K.load(ds, cfg['pool']); S = D['S']; m = S.shape[1]
    rules = FAST + (['borda'] if ds != 'oll39' else [])
    rows = []
    for i in (1, 2, 3, 4):
        for a in rules:
            res = K.min_cost(S, i, a)
            if not res['feasible']: continue
            for b in rules:
                rows.append(dict(dataset=ds, target=i, opt_for=a, eval_under=b, eq_pp=100 * res['l1'] / m,
                                 rank_after=K.rank_under(S, i, res['d'], b), base_rank=K.baseline_rank(S, i, b)))
    return rows

def calibration():
    c = pd.read_parquet(f'{K.ROOT}/data/contents.parquet')
    c = c[~c.Flagged].drop_duplicates('fullname', keep='last').set_index('fullname')
    cols = K.OLL6
    pairs = c[(c['Base Model'] != c.index) & c['Base Model'].isin(c.index) & (c['Weight type'] == 'Original') & (~c['Merged'])]
    G = pd.DataFrame({k: pairs[k].values - c.loc[pairs['Base Model'], k].values for k in cols}, index=pairs.index)
    G['n_params_ratio'] = pairs['#Params (B)'].values / c.loc[pairs['Base Model'], '#Params (B)'].values
    G['base'] = pairs['Base Model'].values
    G.to_csv(f'{K.RES}/exp2_calibration_pairs.csv')
    return G

if __name__ == '__main__':
    t0 = time.time(); ss = np.random.SeedSequence(SEED); out = {}
    with mp.Pool(NPROC) as P:
        jobs = []
        for ds, ms in (('helm57', [5, 10, 20, 40, 57]), ('oll39', [5, 10, 20, 39])):
            for m in ms:
                for draw in range(30 if m < (57 if ds == 'helm57' else 39) else 1):
                    jobs.append((ds, m, draw, int(ss.spawn(1)[0].generate_state(1)[0])))
        out['scaling'] = sum(P.map(scaling_job, jobs, chunksize=1), []); print('scaling', round(time.time() - t0), flush=True)
        jobs = [('oll6', N) for N in (10, 30, 100, 300, 1000, 4496)] + [('oll39', N) for N in (10, 30, 100, 300, 1000, 4490)] + [('helm57', N) for N in (10, 20, 40, 79)]
        out['pool'] = sum(P.map(pool_job, jobs, chunksize=1), []); print('pool', round(time.time() - t0), flush=True)
        jobs = [(ds, k) for ds in K.DATASETS for k in (1, 2, 3, 5, 8, 12)]
        out['kmax'] = sum(P.map(kmax_job, jobs, chunksize=1), []); print('kmax', round(time.time() - t0), flush=True)
        jobs = [(ds, v) for ds in K.DATASETS for v in ('L1', 'L2', 'items')]
        out['cost'] = sum(P.map(cost_job, jobs, chunksize=1), []); print('cost', round(time.time() - t0), flush=True)
        out['spill'] = sum(P.map(spill_job, list(K.DATASETS)), []); print('spill', round(time.time() - t0), flush=True)
    for k, v in out.items(): pd.DataFrame(v).to_csv(f'{K.RES}/exp2_{k}.csv', index=False)
    G = calibration(); print('calibration pairs', len(G), 'done', round(time.time() - t0), 's')
