"""H3 analysis: linear-Gaussian FA vs nonlinear imputers, mixture, adaptivity. python exp/analyze_h3.py -> results/H3/h3_paired.csv
Unit = held-out model (mean over reps/folds); paired bootstrap over models; diff = a - b (negative: a better). Holm over the family (all rows, k in 3,8,12)."""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
import analysis as A
pd.set_option('display.width', 220)
CMP = [('FA vs ExtraTrees', ('greedyAcomp', 'fa'), ('greedyAcomp', 'extratrees')),
       ('FA vs kernel ridge', ('greedyAcomp', 'fa'), ('greedyAcomp', 'kernelridge')),
       ('FA vs mixture FA (prior weights)', ('greedyAcomp', 'fa'), ('greedyAcomp', 'mfa')),
       ('FA-selected vs KRR-selected (FA inference)', ('greedyAcomp', 'fa'), ('wrapKRR', 'fa')),
       ('KRR inference: FA-selected vs KRR-selected', ('greedyAcomp', 'kernelridge'), ('wrapKRR', 'kernelridge')),
       ('mixture: adaptive vs nonadaptive selection', ('mixAdaptive', 'mfa'), ('mixNonadaptive', 'mfa'))]
rows = []
for d in sorted(glob.glob('results/H3/*/')):
    m = os.path.basename(d.rstrip('/'))
    df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(d + 'h3_rep*.parquet'))], ignore_index=True)
    pm = df.groupby(['model', 'k', 'selector', 'method']).mse.mean().reset_index()
    kk = df.groupby('method').K.mean() if 'K' in df else None
    for tag, a, b in CMP:
        t = A.paired(pm, a, b, 'mse', ks=[k for k in (3, 8, 12) if k in set(pm.k)])
        t['test'] = tag; t['matrix'] = m; t['n_reps'] = df.rep.nunique(); rows.append(t)
    Kd = df[(df.method == 'mfa') & (df.selector == 'greedyAcomp')].groupby(['rep', 'fold']).K.first().value_counts().sort_index().to_dict()
    print(m, 'chosen mixture K (counts over rep x fold):', Kd)
G = pd.concat(rows, ignore_index=True); G['p_adj'] = A.holm(G.p.values)
G.to_csv('results/H3/h3_paired.csv', index=False)
print(G[['matrix', 'test', 'k', 'diff', 'rel', 'lo', 'hi', 'p_adj', 'n_models']].round(4).to_string(index=False))

# ---- H3r (k = 3, 8, 12) and H3k (k = 20, 30): does the selection gain over random survive nonlinear inference? 5 reps x 20 random draws per fold
rows = []; means = []
for m in sorted({os.path.basename(d.rstrip('/')) for d in glob.glob('results/H3r/*/') + glob.glob('results/H3k/*/')}):
    fs = [f for r_ in ('H3r', 'H3k') for f in sorted(glob.glob(f'results/{r_}/{m}/h3_rep*.parquet'))]
    df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    nrep = df.groupby('k').rep.nunique()
    pm = df.groupby(['model', 'k', 'selector', 'method']).mse.mean().reset_index()
    for meth in ('fa', 'extratrees', 'kernelridge'):
        ks = sorted(k for k in set(pm.k) if nrep[k] == 5)             # only k with all 5 repetitions
        t = A.paired(pm, ('greedyAcomp', meth), ('random', meth), 'mse', ks=ks)
        t['test'] = f'{meth}: greedyAcomp vs random'; t['matrix'] = m; t['n_reps'] = 5; rows.append(t)
        for sel in ('greedyAcomp', 'random'):
            for k in ks:
                v = pm[(pm.method == meth) & (pm.selector == sel) & (pm.k == k)].mse.values
                bi = A.boot_idx(len(v)); bm = v[bi].mean(1)
                means.append(dict(matrix=m, inference=meth, selector=sel, k=k, metric='mse', mean=v.mean(), ci_lo=np.percentile(bm, 2.5), ci_hi=np.percentile(bm, 97.5), n_models=len(v)))
R = pd.concat(rows, ignore_index=True); R['p_adj'] = A.holm(R.p.values)
R.to_csv('results/H3r/h3r_paired.csv', index=False)
pd.DataFrame(means).to_csv('results/H3r/h3r_means.csv', index=False)
print(R[['matrix', 'test', 'k', 'diff', 'rel', 'lo', 'hi', 'p_adj', 'n_models']].round(4).to_string(index=False))
