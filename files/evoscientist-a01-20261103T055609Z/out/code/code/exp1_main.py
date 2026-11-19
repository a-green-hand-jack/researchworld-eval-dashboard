"""Experiment 1 (main): minimal targeted investment to reach weak rank 1, per dataset x rule x target.

Design A: target models = those ranked 2..11 by mean score on the (full) benchmark; same models for every rule.
Replicates (uncertainty): (a) task bootstrap  - resample the m tasks with replacement;
                          (b) score noise     - add N(0, slope_j^2 p(1-p)/n_j) to every score (re-measurement of the test items).
Outputs results/exp1_point.csv (original data, includes uniform-investment baseline and breadth lemma check)
        results/exp1_reps.csv  (replicates)
"""
import sys, time, numpy as np, pandas as pd, multiprocessing as mp
import common as K, core as C

SEED = 20261103
B_TASK, B_NOISE = 40, 40
NPROC = 12
TARGETS = K.TARGET_RANKS   # positions 2..11 in baseline mean ordering (1-indexed)

def noise_sd(D):
    S = D['S']; n = D['n']
    slope = K.OLL6_SLOPE if D['kind'] == 'oll6' else np.ones(S.shape[1])
    return slope[None, :] * np.sqrt(np.clip(S, 1e-4, 1 - 1e-4) * (1 - np.clip(S, 1e-4, 1 - 1e-4)) / n[None, :])

def uniform_cost(S, i, rule, ceil):
    """Smallest u with every task raised by min(u, headroom) so that i is weakly first (bisection). Returns L1 cost."""
    room = np.maximum(ceil - S[i], 0)
    ok = lambda u: K.rank_under(S, i, np.minimum(u, room), rule) == 1
    if K.baseline_rank(S, i, rule) == 1: return 0.0
    if not ok(1.0): return np.inf
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if ok(mid): hi = mid
        else: lo = mid
    return float(np.minimum(hi, room).sum())

def breadth_lb(s, rule, tau):
    """Lemma (trimmed mean): raising k<=t tasks gains at most k*(s_(m-t+k)-s_(t+1))/K.  Return smallest k consistent with closing the gap."""
    m = len(s)
    if rule not in ('mean', 'trim25', 'median'): return np.nan
    t = {'mean': 0, 'trim25': int(0.25 * m), 'median': C.median_t(m)}[rule]; Kk = m - 2 * t
    srt = np.sort(s); need = Kk * (tau - srt[t:m - t].mean())
    if need <= 0: return 0
    if t == 0: return 1
    for k in range(1, t + 1):
        if k * (srt[m - t + k - 1] - srt[t]) >= need - 1e-12: return k
    return t + 1

def solve_all(S, targets, rules, ceil=None, kmax=None, p=1, cw=None, with_uniform=False, with_lb=False):
    rows = []
    n, m = S.shape
    for ti, i in enumerate(targets):
        for r in rules:
            res = K.min_cost(S, i, r, ceil=ceil, kmax=kmax, p=p, cw=cw)
            row = dict(target=i, rule=r, base_rank=K.baseline_rank(S, i, r), feasible=res['feasible'],
                       cost=res['cost'], l1=res['l1'], touched=res['touched'], opt=res.get('opt', True), eq_pp=100.0 * res['l1'] / m if res['feasible'] else np.nan)
            if with_uniform:
                u = uniform_cost(S, i, r, np.ones(m) if ceil is None else ceil)
                row['uniform_eq_pp'] = 100.0 * u / m
            if with_lb and r in ('mean', 'trim25', 'median'):
                a = K.scalar_agg(r, m)(S); tau = float(np.max(np.delete(a, i)))
                row['lb_touched'] = breadth_lb(S[i], r, tau)
            rows.append(row)
    return rows

def job(args):
    ds, kind, rep, seed = args
    cfg = K.DATASETS[ds]; D = K.load(ds, cfg['pool']); S0 = D['S']; n, m = S0.shape
    targets = [t - 1 for t in TARGETS]            # indices (rows are sorted by baseline mean)
    rng = np.random.default_rng(seed)
    if kind == 'task':
        cols = rng.integers(0, m, size=m); S = S0[:, cols]
    elif kind == 'noise':
        S = np.clip(S0 + rng.normal(size=S0.shape) * noise_sd(D), 0, 1)
    else: S = S0
    rows = solve_all(S, targets, K.RULES, with_uniform=(kind == 'point'), with_lb=(kind == 'point'))
    for r in rows: r.update(dataset=ds, kind=kind, rep=rep, target_rank=r['target'] + 1)
    return rows

if __name__ == '__main__':
    t0 = time.time(); ss = np.random.SeedSequence(SEED)
    jobs = []
    for ds in K.DATASETS:
        jobs.append((ds, 'point', 0, 0))
        for rep, sd in enumerate(ss.spawn(B_TASK + B_NOISE)):
            kind = 'task' if rep < B_TASK else 'noise'
            jobs.append((ds, kind, rep if rep < B_TASK else rep - B_TASK, int(sd.generate_state(1)[0])))
    print(len(jobs), 'jobs'); out = []
    with mp.Pool(NPROC) as pool:
        for k, rows in enumerate(pool.imap_unordered(job, jobs, chunksize=1)):
            out.extend(rows)
            if k % 50 == 0: print(k, round(time.time() - t0), 's', flush=True)
    df = pd.DataFrame(out)
    df[df.kind == 'point'].to_csv(f'{K.RES}/exp1_point.csv', index=False)
    df[df.kind != 'point'].to_csv(f'{K.RES}/exp1_reps.csv', index=False)
    print('done', round(time.time() - t0), 's', df.shape)
