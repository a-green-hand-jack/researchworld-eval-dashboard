"""Cross-fitted evaluation over held-out models: python exp/run_cv.py --setting A1 --rep 0 --out results/A1
One invocation = one repetition (a fresh random partition of eligible models into folds)."""
import sys, os, argparse, time, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
from settings import mteb_setting, llm_setting
from infer import Ctx
import protocol as P

ap = argparse.ArgumentParser()
ap.add_argument('--setting', required=True); ap.add_argument('--rep', type=int, default=0)
ap.add_argument('--nfold', type=int, default=5); ap.add_argument('--out', required=True)
ap.add_argument('--selectors', default='greedyA,greedyD,greedyAcomp,greedyGauss,covered,central,pivqr,leverage,fwdreg')
ap.add_argument('--methods', default='mean,fa,fa_pcv,gcov,meanz,ridge,knn,softimpute')
ap.add_argument('--n_random', type=int, default=100); ap.add_argument('--n_random_decision', type=int, default=10)
ap.add_argument('--nmin', type=int, default=0, help='min observed benchmarks for a model to be a test model')
ap.add_argument('--rank_nfold', type=int, default=5); ap.add_argument('--max_models', type=int, default=0)
ap.add_argument('--kgrid', default='1,2,3,4,5,6,8,10,12,15,20,30,40')
ap.add_argument('--no_cluster', action='store_true')
ap.add_argument('--target_group', default='', help='task type of the target group (group transfer: observed set from other groups)')
ap.add_argument('--group_kfold', action='store_true', help='folds = groups of families (no family split between history and test)')
ap.add_argument('--leak', action='store_true', help='E0 ablation: the test models stay in the history (transductive fit, standardisation, rank and tuning)')
ap.add_argument('--cost', action='store_true', help='pass measured median evaluation_time as the per-benchmark cost')
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
s = llm_setting(a.setting) if a.setting in ('OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH') else mteb_setting(a.setting, col=os.environ.get('MTEB_SCORE_COL', 'main_score'))
X, obs = s['X'], s['obs']
M, N = X.shape
dense = obs.all()
selectors = [x for x in a.selectors.split(',') if x]
if dense and 'covered' in selectors:
    selectors.remove('covered')           # all coverages equal: undefined in a complete block
elig = np.where(obs.sum(1) >= (a.nmin or (3 if dense else 40)))[0]
rng = np.random.default_rng(1000 * (hash(a.setting) % 1000) + a.rep) if False else np.random.default_rng([a.rep, sum(map(ord, a.setting))])
if a.max_models:
    elig = rng.permutation(elig)[:a.max_models]
perm = rng.permutation(elig)
if a.group_kfold:
    g = np.asarray(s['groups']); ug = rng.permutation(np.unique(g[elig]))
    gfold = {u: i % a.nfold for i, u in enumerate(ug)}
    fo = np.array([gfold[x] for x in g[elig]])
    folds = [elig[fo == i] for i in range(a.nfold)]
    if a.max_models:
        folds = [f[:max(1, a.max_models // a.nfold)] for f in folds]
else:
    folds = np.array_split(perm, a.nfold)
kgrid = [int(x) for x in a.kgrid.split(',')]
recs, info = [], []
for fi, te in enumerate(folds):
    t0 = time.time()
    tr = np.setdiff1d(np.arange(M), te)
    if a.group_kfold:                      # history excludes every model of the test families
        tr = np.setdiff1d(tr, np.where(np.isin(np.asarray(s['groups']), np.asarray(s['groups'])[te]))[0])
    if a.leak:
        tr = np.arange(M)
    obs_tr = obs[tr]
    keep = obs_tr.sum(0) >= min(15, max(3, len(tr) // 4))     # benchmarks need history observations to be standardised
    cols = np.where(keep)[0]
    ctx = Ctx(X[np.ix_(tr, cols)], obs_tr[:, cols], rank_nfold=a.rank_nfold, seed=a.rep * 100 + fi,
              ranks=tuple(r for r in ((0, 1, 2, 3, 4, 6, 8, 12, 16, 24) if dense else (0, 1, 2, 3, 4, 6, 8)) if r <= max(1, len(cols) // 2)))
    tgt = None
    if a.target_group:
        tgt = np.where(s['ttype'][cols] == a.target_group)[0]
        assert len(tgt) >= 5, 'target group too small'
    meths = P.build_methods(ctx, rng, tuple(a.methods.split(',')))
    Xte = (X[np.ix_(te, cols)] - ctx.m) / ctx.sd
    ote = obs[np.ix_(te, cols)]
    rr = P.eval_fold(ctx, Xte, ote, selectors, meths, kgrid, rng, n_random=a.n_random,
                     n_random_decision=a.n_random_decision, cluster=not a.no_cluster, rawsd=ctx.sd * 100,
                     target=tgt, sel_cost=(s['cost'][cols] if a.cost else None))
    for r in rr:
        r['rep'] = a.rep; r['fold'] = fi; r['model'] = int(te[r['model']])
    recs.extend(rr)
    ev = np.sort(np.linalg.eigvalsh(ctx.par['Lam'].T @ ctx.par['Lam']))[::-1] if ctx.r else []
    info.append(dict(rep=a.rep, fold=fi, M=int(ctx.M), N=int(ctx.N), r=int(ctx.r),
                     rank_scores={int(k): float(v) for k, v in ctx.rank_scores.items()},
                     r_pcv=int(getattr(meths.get('fa_pcv'), 'r', -1)), eig=[float(e) for e in ev],
                     psi_mean=float(ctx.par['psi'].mean()), ridge_lam=getattr(meths.get('ridge'), 'lam', None),
                     knn_K=getattr(meths.get('knn'), 'K', None), si_lam=getattr(meths.get('softimpute'), 'lam', None),
                     secs=time.time() - t0))
    np.savez(f"{a.out}/fit_rep{a.rep}_fold{fi}.npz", Lam=ctx.par['Lam'], psi=ctx.par['psi'], mu=ctx.par['mu'], cols=cols, sd=ctx.sd, te=te)
    print(a.setting, a.rep, fi, 'r=', ctx.r, 'secs', round(time.time() - t0), flush=True)
pd.DataFrame(recs).to_parquet(f"{a.out}/rec_rep{a.rep}.parquet")
json.dump(info, open(f"{a.out}/info_rep{a.rep}.json", 'w'))
