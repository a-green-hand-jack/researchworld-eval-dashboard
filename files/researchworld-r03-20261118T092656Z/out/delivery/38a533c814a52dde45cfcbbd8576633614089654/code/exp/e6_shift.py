"""E6: shift (random / temporal / leave-family-out) and stopping rules (model-based vs split-conformal).
usage: python exp/e6_shift.py SETTING OUT [--rep R]
Per split: history is divided into proper-train (75%) and calibration (25%) models; the predictor is fitted on
proper-train only; calibration residuals give the conformal quantile; test models are the shifted block.
Rows: (split, fold, selector/method, k): predicted RMSE (model-based), conformal quantiles, test statistics."""
import sys, os, argparse, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
from settings import mteb_setting, llm_setting
from infer import Ctx, GaussPred
import fa as FA, bselect as SEL
from mteb_matrix import load_long

ap = argparse.ArgumentParser()
ap.add_argument('setting'); ap.add_argument('out'); ap.add_argument('--rep', type=int, default=0)
ap.add_argument('--kgrid', default='1,2,3,4,5,6,8,10,12,15,20,30,40'); ap.add_argument('--alpha', type=float, default=0.1)
ap.add_argument('--max_models', type=int, default=0)
a = ap.parse_args()
LLM = a.setting in ('OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH')
s = llm_setting(a.setting) if LLM else mteb_setting(a.setting)
if LLM and a.max_models and len(s['X']) > a.max_models:
    M0 = len(s['X'])
    sub = np.sort(np.random.default_rng([a.rep, 5]).choice(len(s['X']), a.max_models, replace=False))
    s = {k: (v[sub] if isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == len(s['X']) else v) for k, v in s.items()}
    s['models'] = [s['models'][i] for i in sub]
    for k_ in ('groups', 'date'):                # the filter above skips Arrow arrays: subset those still at full length
        if len(s[k_]) == M0: s[k_] = np.asarray(s[k_])[sub]
X, obs = s['X'], s['obs']; M, N = X.shape
if LLM:
    date = s['date']; fam = np.asarray(s['groups'])
else:
    meta = pd.read_parquet('data/mteb_models.parquet'); prim = load_long()[['model', 'revision']].drop_duplicates()
    meta = prim.merge(meta, on=['model', 'revision'], how='left').set_index('model').loc[s['models']]
    date = pd.to_datetime(meta.release_date, errors='coerce').values.astype('datetime64[D]').astype(float)
    fam = np.array([m.split('__')[0] for m in s['models']])
rng = np.random.default_rng([a.rep, 77])
kgrid = [int(x) for x in a.kgrid.split(',')]
dense = obs.all()


def splits():
    perm = rng.permutation(M)
    for i, te in enumerate(np.array_split(perm, 5)):
        yield 'random', i, te
    ok = np.where(~np.isnan(date))[0]; o = ok[np.argsort(date[ok], kind='stable')]
    blocks = np.array_split(o, 5)
    for i in range(1, 5):                        # forward chaining: test block i, history = earlier blocks only
        yield 'temporal', i, blocks[i], np.concatenate(blocks[:i])
    fams = rng.permutation(np.unique(fam)); fold_of = {f: i % 5 for i, f in enumerate(fams)}
    fo = np.array([fold_of[f] for f in fam])
    for i in range(5):
        yield 'family', i, np.where(fo == i)[0]


rows = []
for sp in splits():
    typ, fi, te = sp[:3]
    hist = sp[3] if len(sp) > 3 else np.setdiff1d(np.arange(M), te)
    if typ == 'family':
        hist = np.setdiff1d(np.arange(M), te)
    if len(te) < 5 or len(hist) < 25:
        continue
    h = rng.permutation(hist); ncal = max(len(h) // 4, 8); cal, pt = h[:ncal], h[ncal:]
    keep = np.where(obs[pt].sum(0) >= 15)[0]
    ctx = Ctx(X[np.ix_(pt, keep)], obs[np.ix_(pt, keep)], rank_nfold=3, seed=fi,
              ranks=tuple(r for r in ((0, 1, 2, 3, 4, 6, 8, 12) if dense else (0, 1, 2, 3, 4, 6)) if r <= max(1, len(keep) // 2)))
    gp = GaussPred(ctx, 0.2)
    Z = lambda rows_: (X[np.ix_(rows_, keep)] - ctx.m) / ctx.sd
    Xc_, Xt_ = Z(cal), Z(te); Oc, Ot = obs[np.ix_(cal, keep)], obs[np.ix_(te, keep)]
    cands = np.arange(len(keep))
    k0 = float(np.mean([np.sqrt((Xt_[i, Ot[i]] ** 2).mean()) for i in range(len(te)) if Ot[i].sum() > 0]))   # mean-predictor RMSE on the test block
    for sel, meth in (('greedyA', 'fa'), ('greedyGauss', 'gcov'), ('random', 'fa')):
        if sel == 'greedyA': order = SEL.greedy_design(ctx.par, cands, max(kgrid), 'A_all')
        elif sel == 'greedyGauss': order = SEL.greedy_gauss(gp.Sigma, cands, max(kgrid))
        for k in kgrid:
            def evaluate(Xs_, Os_, orderS):
                rm, res, var = [], [], []
                for i in range(len(Xs_)):
                    S = orderS(i)[:k]
                    S = S[Os_[i, S]]
                    T = np.setdiff1d(np.where(Os_[i])[0], S)
                    if len(T) < 3: continue
                    if meth == 'fa':
                        yh = FA.predict_fa(ctx.par, S, Xs_[i, S][None, :])[0]; v = FA.predicted_mse(ctx.par, S, np.arange(len(keep)))
                    else:
                        yh = gp.predict(S, Xs_[i, S]); v = gp.cond_var(S)
                    e = yh[T] - Xs_[i, T]
                    rm.append(np.sqrt((e ** 2).mean())); res.append(np.abs(e)); var.append(np.sqrt(v[T]))
                return np.array(rm), res, var
            if sel == 'random':
                rr = np.random.default_rng([a.rep, fi, k, 5])
                perms = [rr.permutation(len(keep)) for _ in range(10)]
                outc = [evaluate(Xc_, Oc, lambda i, p=p: p) for p in perms]; outt = [evaluate(Xt_, Ot, lambda i, p=p: p) for p in perms]
                rmc = np.concatenate([o[0] for o in outc]); resc = sum([o[1] for o in outc], []); varc = sum([o[2] for o in outc], [])
                rmt = np.concatenate([o[0] for o in outt]); rest = sum([o[1] for o in outt], []); vart = sum([o[2] for o in outt], [])
            else:
                rmc, resc, varc = evaluate(Xc_, Oc, lambda i: order)
                rmt, rest, vart = evaluate(Xt_, Ot, lambda i: order)
            if len(rmc) == 0 or len(rmt) == 0: continue
            n = len(rmc); qlev = min(np.ceil((n + 1) * (1 - a.alpha)) / n, 1.0)
            q_model = np.quantile(rmc, qlev)
            pooled_c = np.concatenate(resc); q_tgt = np.quantile(pooled_c, min(np.ceil((len(pooled_c) + 1) * (1 - a.alpha)) / len(pooled_c), 1.0))
            pooled_t = np.concatenate(rest); sdt = np.concatenate(vart)
            z = 1.6449
            rows.append(dict(setting=a.setting, split=typ, fold=fi, selector=sel, method=meth, k=k, n_cal=len(rmc), n_test=len(rmt),
                             pred_rmse=float(np.sqrt(np.mean(np.concatenate([v ** 2 for v in varc])))),
                             q_model=float(q_model), q_tgt=float(q_tgt),
                             test_rmse_mean=float(rmt.mean()), test_rmse_q90=float(np.quantile(rmt, 1 - a.alpha)),
                             cal_rmse_mean=float(rmc.mean()), test_rmse_k0=k0,
                             cov_conf=float((pooled_t <= q_tgt).mean()), cov_gauss=float((pooled_t <= z * sdt).mean()),
                             cov_model_conf=float((rmt <= q_model).mean()),
                             frac_models_below={str(e): float((rmt <= e).mean()) for e in (0.4, 0.5, 0.6, 0.7)}))
    print(typ, fi, 'r=', ctx.r, flush=True)
os.makedirs(a.out, exist_ok=True)
df = pd.DataFrame(rows); df['frac_models_below'] = df.frac_models_below.map(json.dumps)
df.to_parquet(f"{a.out}/e6_{a.setting}_rep{a.rep}.parquet")
