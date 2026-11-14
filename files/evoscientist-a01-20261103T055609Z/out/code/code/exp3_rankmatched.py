"""Experiment 3: rank-matched comparison + gap-normalised cost + breadth lower-bound check + calibration against observed fine-tuning gains.
For every rule, targets are the models at positions 2..11 of that rule's OWN baseline ordering (so every rule faces the same
'distance in ranks' to first place).  Scalar rules: order by aggregate; Borda: Borda total; plurality: #task wins;
condorcet: Copeland score (number of pairwise task-majority wins).
Outputs results/exp3_rankmatched.csv (point), exp3_rankmatched_reps.csv (task-bootstrap), exp3_gapnorm.csv
"""
import time, numpy as np, pandas as pd, multiprocessing as mp
import common as K, core as C
from exp1_main import solve_all, breadth_lb

SEED = 11; NPROC = 12; B = 30

def order_for(S, rule):
    n, m = S.shape
    if rule in ('geomean', 'harmonic'): S = S + K.PM_SHIFT
    f = K.scalar_agg(rule, m)
    if f is not None: a = f(S)
    elif rule == 'borda': a = C.borda_scores(S)
    elif rule == 'plurality': a = C.plurality_counts(S)
    else:
        a = np.array([((S[i][None, :] > S).sum(1) > (S[i][None, :] < S).sum(1)).sum() for i in range(n)], float)
    return np.argsort(-a, kind='stable'), a

def job(args):
    ds, kind, rep, seed, rules = args
    cfg = K.DATASETS[ds]; D = K.load(ds, cfg['pool']); S0 = D['S']; n, m = S0.shape
    S = S0
    if kind == 'task':
        S = S0[:, np.random.default_rng(seed).integers(0, m, size=m)]
    rows = []
    for r in rules:
        order, a = order_for(S, r)
        targets = [int(order[p - 1]) for p in K.TARGET_RANKS]
        for pos, i in zip(K.TARGET_RANKS, targets):
            res = K.min_cost(S, i, r)
            row = dict(dataset=ds, kind=kind, rep=rep, rule=r, pos=pos, target=i, feasible=res['feasible'], eq_pp=100 * res['l1'] / m if res['feasible'] else np.nan,
                       touched=res['touched'], opt=res.get('opt', True))
            if r in ('mean', 'trim25', 'median', 'max', 'min'):
                f = K.scalar_agg(r, m); ag = f(S); top = np.max(np.delete(ag, i)); row['gap'] = float(top - ag[i])
                if kind == 'point': row['lb_touched'] = breadth_lb(S[i], r, top) if r in ('mean', 'trim25', 'median') else np.nan
            rows.append(row)
    return rows

if __name__ == '__main__':
    t0 = time.time(); ss = np.random.SeedSequence(SEED).spawn(3 * B)
    jobs = []
    for ds in K.DATASETS:
        rules = K.RULES if ds != 'oll39' else [r for r in K.RULES if r != 'borda']
        jobs.append((ds, 'point', 0, 0, K.RULES))                               # point incl. borda everywhere
        for b in range(B): jobs.append((ds, 'task', b, int(ss[b].generate_state(1)[0]), [r for r in K.RULES if r != 'borda']))
    out = []
    with mp.Pool(NPROC) as P:
        for k, rows in enumerate(P.imap_unordered(job, jobs, chunksize=1)):
            out += rows; print(k, round(time.time() - t0), flush=True)
    df = pd.DataFrame(out)
    df[df.kind == 'point'].to_csv(f'{K.RES}/exp3_rankmatched.csv', index=False)
    df[df.kind == 'task'].to_csv(f'{K.RES}/exp3_rankmatched_reps.csv', index=False)
    print('done', round(time.time() - t0))
