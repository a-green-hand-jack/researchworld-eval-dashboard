"""H3: is the linear-Gaussian latent model as accurate as nonlinear imputers, and does adaptivity help?
python exp/e_h3.py SETTING OUT --rep R [--ks 3,8,12]    (dense matrices; same fold protocol as run_cv.py: 5-fold over models, history only)
Methods, all given the same observed set S = greedyAcomp(FA) order unless stated:
  fa            : FA posterior (rank by held-out likelihood)             [reference]
  extratrees    : multi-output ExtraTrees from S to all benchmarks (completed history)
  kernelridge   : RBF kernel ridge from S, (gamma, alpha) chosen by inner CV on history
  mfa           : mixture of factor analysers (K in {1,2,3} by held-out history likelihood, hard-EM); posterior-weighted mean
Selection under the MFA: nonadaptive (component weights = prior, one order for all) vs adaptive (weights from the scores observed so far).
Records: model,k,selector,method,mse,rep,fold."""
import sys, os, argparse, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
import numpy as np, pandas as pd
from settings import mteb_setting, llm_setting
from infer import Ctx
import fa as FA, bselect as SEL
from scipy.special import logsumexp
from sklearn.ensemble import ExtraTreesRegressor
from sklearn.kernel_ridge import KernelRidge
from sklearn.cluster import KMeans

ap = argparse.ArgumentParser(); ap.add_argument('setting'); ap.add_argument('out'); ap.add_argument('--rep', type=int, default=0)
ap.add_argument('--ks', default='3,8,12'); ap.add_argument('--nfold', type=int, default=5); ap.add_argument('--n_random', type=int, default=0); ap.add_argument('--lean', action='store_true', help='FA/ExtraTrees/kernel ridge only (no mixture, no wrapper selection)'); a = ap.parse_args()
LLM = a.setting in ('OLMB40', 'HELMMMLU', 'HELMLITE', 'OLMB6', 'LIVEBENCH')
s = llm_setting(a.setting) if LLM else mteb_setting(a.setting)
X, obs = s['X'], s['obs']; M, N = X.shape; assert obs.all()
KS = [int(k) for k in a.ks.split(',')]
rng = np.random.default_rng([a.rep, 31, sum(map(ord, a.setting))])


def fit_mfa(Xs, K, r, seed):
    M_, N_ = Xs.shape; ones = np.ones_like(Xs, bool)
    lab = KMeans(K, n_init=5, random_state=seed).fit_predict(Xs) if K > 1 else np.zeros(M_, int)
    comps = None
    for it in range(8):
        comps = []
        for c in range(K):
            idx = np.where(lab == c)[0]
            if len(idx) < max(12, 2 * r + 4): return None
            p = FA.fit_fa(Xs[idx], ones[idx], r, iters=100, seed=seed); p['pi'] = len(idx) / M_; comps.append(p)
        ll = np.stack([FA.loglik_rows(Xs, ones, p['mu'], p['Lam'], p['psi']) + np.log(p['pi']) for p in comps], 1)
        new = ll.argmax(1)
        if (new == lab).all(): break
        lab = new
    return comps


def mix_ll(comps, Xs, cols=None):
    cols = np.arange(Xs.shape[1]) if cols is None else cols
    ones = np.ones((len(Xs), len(cols)), bool)
    return np.stack([FA.loglik_rows(Xs[:, cols] if Xs.shape[1] != len(cols) else Xs, ones, p['mu'][cols], p['Lam'][cols], p['psi'][cols]) + np.log(p['pi']) for p in comps], 1)


def mfa_predict(comps, S, xS, w=None):
    """posterior-weighted mean of component predictions. w: (n,K) weights; None -> responsibilities from xS."""
    S = np.asarray(S)
    if w is None:
        ll = np.stack([FA.loglik_rows(xS, np.ones_like(xS, bool), p['mu'][S], p['Lam'][S], p['psi'][S]) + np.log(p['pi']) for p in comps], 1)
        w = np.exp(ll - logsumexp(ll, 1, keepdims=True))
    preds = np.stack([FA.predict_fa(p, S, xS) for p in comps], 0)     # (K,n,N)
    return np.einsum('nk,knj->nj', w, preds)


def comp_cov(p):
    return p['Lam'] @ p['Lam'].T + np.diag(p['psi'])


def gain_vec(C, S, cand):
    """reduction of the total posterior variance of the other benchmarks from observing j (given S), for j in cand: sum_t Cov(t,j|S)^2 / Var(j|S)."""
    if len(S):
        CS = C[:, S]; K = np.linalg.solve(C[np.ix_(S, S)] + 1e-9 * np.eye(len(S)), CS.T)
        Cp = C - CS @ K
    else:
        Cp = C
    var = np.diag(Cp)[cand]
    sq = (Cp[:, cand] ** 2)
    tot = sq.sum(0) - np.diag(Cp)[cand] ** 2        # exclude t=j
    if len(S): tot = tot - sq[S].sum(0)             # exclude already observed t
    return tot / np.maximum(var, 1e-9)


def mix_order(comps, x_row, kmax, adaptive, first=None):
    Cs = [comp_cov(p) for p in comps]; S = []
    cand_all = np.arange(N)
    for t in range(kmax):
        cand = np.array([j for j in cand_all if j not in S])
        if adaptive and len(S):
            ll = np.array([FA.loglik_rows(x_row[None, S], np.ones((1, len(S)), bool), p['mu'][S], p['Lam'][S], p['psi'][S])[0] + np.log(p['pi']) for p in comps])
            w = np.exp(ll - logsumexp(ll))
        else:
            w = np.array([p['pi'] for p in comps])
        g = sum(wc * gain_vec(C, S, cand) for wc, C in zip(w, Cs))
        S.append(int(cand[np.argmax(g)]))
    return np.array(S)


perm = rng.permutation(M); folds = np.array_split(perm, a.nfold); recs = []
for fi, te in enumerate(folds):
    t0 = time.time(); tr = np.setdiff1d(np.arange(M), te)
    ctx = Ctx(X[tr], obs[tr], rank_nfold=3, seed=a.rep * 100 + fi, ranks=(0, 1, 2, 3, 4, 6, 8, 12))
    Xtr = ctx.Xs; Xte = (X[te] - ctx.m) / ctx.sd
    order = SEL.greedy_design(ctx.par, np.arange(N), max(KS), 'A_comp')
    # mixture of FA: pick K by held-out likelihood on an inner split
    h = rng.permutation(len(tr)); nv = max(len(tr) // 5, 8); va, pt = h[:nv], h[nv:]
    rr = max(1, min(ctx.r, 3)); best = (-np.inf, 1)
    for K in (() if a.lean else (1, 2, 3)):
        c = fit_mfa(Xtr[pt], K, rr, a.rep)
        if c is None: continue
        ll = logsumexp(mix_ll(c, Xtr[va]), 1).mean()
        if ll > best[0]: best = (ll, K)
    K = best[1]; comps = None if a.lean else (fit_mfa(Xtr, K, rr, a.rep) or fit_mfa(Xtr, 1, rr, a.rep))
    # kernel ridge hyper-parameters on inner split (completed history; S = order[:8])
    S8 = order[:8]; bestk = None
    for g in (0.01, 0.03, 0.1, 0.3):
        for al in (0.03, 0.1, 0.3, 1.0):
            kr = KernelRidge(alpha=al, kernel='rbf', gamma=g).fit(Xtr[pt][:, S8], Xtr[pt]); e = ((kr.predict(Xtr[va][:, S8]) - Xtr[va]) ** 2).mean()
            if bestk is None or e < bestk[0]: bestk = (e, g, al)
    _, kg, ka = bestk
    # wrapper greedy forward selection for the kernel ridge (error on the inner validation models over the unobserved benchmarks)
    wo = []
    for t in range(0 if a.lean else max(KS)):
        bj = None
        for j in range(N):
            if j in wo: continue
            Sj = wo + [j]; Tj = np.setdiff1d(np.arange(N), Sj)
            e = ((KernelRidge(alpha=ka, kernel='rbf', gamma=kg).fit(Xtr[pt][:, Sj], Xtr[pt][:, Tj]).predict(Xtr[va][:, Sj]) - Xtr[va][:, Tj]) ** 2).mean()
            if bj is None or e < bj[0]: bj = (e, j)
        wo.append(bj[1])
    wo = np.array(wo)
    ko = None if a.lean else mix_order(comps, np.zeros(N), max(KS), adaptive=False)                  # nonadaptive mixture order
    for k in KS:
        S = order[:k]; xS = Xte[:, S]; T = np.setdiff1d(np.arange(N), S)
        def rec(sel, me, Yh, T_=T, S_=S):
            for i in range(len(te)):
                recs.append(dict(model=int(te[i]), k=k, selector=sel, method=me, mse=float(((Yh[i, T_] - Xte[i, T_]) ** 2).mean()), rep=a.rep, fold=fi, K=K))
        rec('greedyAcomp', 'fa', FA.predict_fa(ctx.par, S, xS))
        et = ExtraTreesRegressor(100, min_samples_leaf=2, n_jobs=1, random_state=0, max_features=0.7).fit(Xtr[:, S], Xtr)
        rec('greedyAcomp', 'extratrees', et.predict(xS))
        rec('greedyAcomp', 'kernelridge', KernelRidge(alpha=ka, kernel='rbf', gamma=kg).fit(Xtr[:, S], Xtr).predict(xS))
        if not a.lean: rec('greedyAcomp', 'mfa', mfa_predict(comps, S, xS))
        if not a.lean:
            Sw = wo[:k]; Tw = np.setdiff1d(np.arange(N), Sw)
            Yw = KernelRidge(alpha=ka, kernel='rbf', gamma=kg).fit(Xtr[:, Sw], Xtr).predict(Xte[:, Sw])
            Yf = FA.predict_fa(ctx.par, Sw, Xte[:, Sw])
            for i in range(len(te)):
                recs.append(dict(model=int(te[i]), k=k, selector='wrapKRR', method='kernelridge', mse=float(((Yw[i, Tw] - Xte[i, Tw]) ** 2).mean()), rep=a.rep, fold=fi, K=K))
                recs.append(dict(model=int(te[i]), k=k, selector='wrapKRR', method='fa', mse=float(((Yf[i, Tw] - Xte[i, Tw]) ** 2).mean()), rep=a.rep, fold=fi, K=K))
        # random selection (n_random draws, mse averaged per model): does the selection gain survive nonlinear inference?
        if a.n_random:
            acc = {m_: np.zeros(len(te)) for m_ in ('fa', 'extratrees', 'kernelridge')}
            rrng = np.random.default_rng(10000 * a.rep + 100 * fi + k)
            for dr in range(a.n_random):
                Sr = rrng.choice(N, k, replace=False); Tr = np.setdiff1d(np.arange(N), Sr); xr = Xte[:, Sr]
                Ys = dict(fa=FA.predict_fa(ctx.par, Sr, xr),
                          extratrees=ExtraTreesRegressor(100, min_samples_leaf=2, n_jobs=1, random_state=0, max_features=0.7).fit(Xtr[:, Sr], Xtr).predict(xr),
                          kernelridge=KernelRidge(alpha=ka, kernel='rbf', gamma=kg).fit(Xtr[:, Sr], Xtr).predict(xr))
                for m_, Yh in Ys.items(): acc[m_] += ((Yh[:, Tr] - Xte[:, Tr]) ** 2).mean(1) / a.n_random
            for m_, v in acc.items():
                for i in range(len(te)): recs.append(dict(model=int(te[i]), k=k, selector='random', method=m_, mse=float(v[i]), rep=a.rep, fold=fi, K=K))
        if not a.lean:
            # selection under the mixture
            Sn = ko[:k]; Tn = np.setdiff1d(np.arange(N), Sn)
            Yn = mfa_predict(comps, Sn, Xte[:, Sn])
            for i in range(len(te)):
                recs.append(dict(model=int(te[i]), k=k, selector='mixNonadaptive', method='mfa', mse=float(((Yn[i, Tn] - Xte[i, Tn]) ** 2).mean()), rep=a.rep, fold=fi, K=K))
            for i in range(len(te)):
                Sa = mix_order(comps, Xte[i], k, adaptive=True) if K > 1 else Sn
                Ta = np.setdiff1d(np.arange(N), Sa)
                Ya = mfa_predict(comps, Sa, Xte[i, Sa][None, :])[0]
                recs.append(dict(model=int(te[i]), k=k, selector='mixAdaptive', method='mfa', mse=float(((Ya[Ta] - Xte[i, Ta]) ** 2).mean()), rep=a.rep, fold=fi, K=K))
    print(a.setting, a.rep, fi, 'K', K, 'r', ctx.r, 'secs', round(time.time() - t0), flush=True)
os.makedirs(a.out, exist_ok=True)
pd.DataFrame(recs).to_parquet(f"{a.out}/h3_rep{a.rep}.parquet")
