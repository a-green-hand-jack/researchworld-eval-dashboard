"""Evaluation protocol: leakage-safe cross-fitting over held-out models, selectors x inference x k.

Unit of replication = held-out model. Everything fitted (standardisation, FA, rank, hyperparameters,
selection orders, conformal calibration) uses history rows only. Candidate benchmarks for a test model =
the benchmarks it has a score for (availability constraint); targets = its other observed benchmarks."""
import numpy as np
from scipy.stats import norm, rankdata
import fa as FA
import bselect as SEL
import infer as INF

Z90 = norm.ppf(0.95)
KGRID = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 40, 60]


# ---------------------------------------------------------------- hyper-parameter tuning (history only)
def tune(ctx, make, grid, rng, ks=(3, 8, 15), nfold=5, max_rows=60):
    """pick grid value minimising inner-CV error on history models with random observed sets. The
    method is rebuilt on an inner-train Ctx-like view (only Xc/Xs/obs/par used from history rows)."""
    M = ctx.M
    perm = rng.permutation(M)[:max_rows] if M > max_rows else rng.permutation(M)
    folds = np.array_split(perm, nfold)
    err = np.zeros(len(grid))
    for f in folds:
        tr = np.setdiff1d(np.arange(M), f)
        sub = _SubCtx(ctx, tr)
        for gi, g in enumerate(grid):
            p = make(sub, g)
            for i in f:
                O = np.where(ctx.obs[i])[0]
                for k in ks:
                    if len(O) < k + 3:
                        continue
                    S = rng.choice(O, k, replace=False)
                    T = np.setdiff1d(O, S)
                    yh = p.predict(S, ctx.Xs[i, S])
                    err[gi] += ((yh[T] - ctx.Xs[i, T]) ** 2).mean()
    return grid[int(np.argmin(err))]


class _SubCtx:
    def __init__(self, ctx, rows):
        self.obs = ctx.obs[rows]; self.Xs = ctx.Xs[rows]; self.Xc = ctx.Xc[rows]
        self.par = ctx.par; self.M = len(rows); self.N = ctx.N; self.coverage = self.obs.mean(0)


def tune_fa_rank(ctx, ranks, rng, ks=(3, 8, 15), nfold=5, max_rows=80):
    """rank chosen by held-out *prediction* error (inner CV over history models, refit per fold)."""
    M = ctx.M
    perm = rng.permutation(M)[:max_rows] if M > max_rows else rng.permutation(M)
    folds = np.array_split(perm, nfold)
    err = {r: 0.0 for r in ranks}
    for f in folds:
        tr = np.setdiff1d(np.arange(M), f)
        draws = []
        for i in f:
            O = np.where(ctx.obs[i])[0]
            for k in ks:
                if len(O) >= k + 3:
                    S = rng.choice(O, k, replace=False)
                    draws.append((i, S, np.setdiff1d(O, S)))
        init = None
        for r in ranks:
            p = FA.fit_fa(ctx.Xs[tr], ctx.obs[tr], r, iters=150, init=init)
            init = p if r > 0 else None
            for i, S, T in draws:
                yh = FA.predict_fa(p, S, ctx.Xs[i, S][None, :])[0]
                err[r] += ((yh[T] - ctx.Xs[i, T]) ** 2).mean()
    return min(err, key=err.get), err


def build_methods(ctx, rng, which=('mean', 'fa', 'meanz', 'ridge', 'knn', 'softimpute'), tune_rows=60):
    out = {}
    for w in which:
        if w == 'mean': out[w] = INF.MeanPred(ctx)
        elif w == 'fa': out[w] = INF.FAPred(ctx)
        elif w == 'fa_pcv':
            r, _ = tune_fa_rank(ctx, [r_ for r_ in (1, 2, 3, 4, 6, 8, 12, 16) if r_ <= max(1, ctx.N // 2)], rng)
            out[w] = INF.FAPred(ctx, par=FA.fit_fa(ctx.Xs, ctx.obs, r)); out[w].name = 'fa_pcv'; out[w].r = r
        elif w == 'gcov':
            al = tune(ctx, lambda c, g: INF.GaussPred(c, g), [0.05, 0.1, 0.2, 0.4, 0.7], rng, max_rows=tune_rows)
            out[w] = INF.GaussPred(ctx, al)
        elif w == 'meanz': out[w] = INF.MeanZPred(ctx)
        elif w == 'ridge':
            lam = tune(ctx, lambda c, g: INF.RidgePred(c, g), [0.1, 1.0, 10.0], rng, max_rows=tune_rows)
            out[w] = INF.RidgePred(ctx, lam)
        elif w == 'knn':
            K = tune(ctx, lambda c, g: INF.KnnPred(c, g), [3, 5, 10, 20], rng, max_rows=tune_rows)
            out[w] = INF.KnnPred(ctx, K)
        elif w == 'softimpute':
            lam = tune(ctx, lambda c, g: INF.SoftImpute(c, g), [0.3, 1.0, 3.0, 10.0], rng, max_rows=tune_rows)
            out[w] = INF.SoftImpute(ctx, lam)
        elif w == 'extratrees':
            out[w] = INF.TreePred(ctx)
    return out


def _spear(a, b):
    ra, rb = rankdata(a), rankdata(b)
    ra -= ra.mean(); rb -= rb.mean()
    den = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / den) if den > 0 else 0.0


# ---------------------------------------------------------------- metrics for one (model, S, prediction)
def model_metrics(ctx, y, yhat, S, obs_row, var=None, decision=True, rawsd=None):
    """y: standardised truth (N,), yhat: prediction (N,), S: observed set. targets = obs_row minus S."""
    T = np.setdiff1d(np.where(obs_row)[0], S)
    e = yhat[T] - y[T]
    out = dict(nT=len(T), mse=float((e ** 2).mean()))
    if rawsd is not None:
        out['mae_raw'] = float(np.abs(e * rawsd[T]).mean())
    if var is not None:
        sdv = np.sqrt(var[T])
        out['cov90'] = float((np.abs(e) <= Z90 * sdv).mean())
        out['zsq'] = float((e ** 2 / var[T]).mean())
    if decision and len(T) >= 3:
        out['spear'] = _spear(yhat[T], y[T])
        H = ctx.Xs[:, T]; Ho = ctx.obs[:, T]            # history values on targets (M,nT)
        st = np.sign(y[T][None, :] - H) ; sp = np.sign(yhat[T][None, :] - H)
        m = Ho & (st != 0)
        out['pw_acc'] = float(((st == sp) & m).sum() / max(m.sum(), 1))
        # top-10 inclusion among history models (+ the model)
        n_better_t = ((H > y[T][None, :]) & Ho).sum(0); n_better_p = ((H > yhat[T][None, :]) & Ho).sum(0)
        tt = n_better_t < 10; tp_ = n_better_p < 10
        out['t10_tp'] = int((tt & tp_).sum()); out['t10_fp'] = int((~tt & tp_).sum()); out['t10_fn'] = int((tt & ~tp_).sum())
    return out


# ---------------------------------------------------------------- selector orders
def selector_orders(ctx, cand, kmax, names, rng, C=None, cost=None, target=None, sigma=None):
    """dict name -> ordered array (nested prefixes) for non-random selectors."""
    cand = np.array(cand)
    out = {}
    for nme in names:
        if nme == 'greedyA':
            out[nme] = SEL.greedy_design(ctx.par, cand, kmax, 'A_all')
        elif nme == 'greedyD':
            out[nme] = SEL.greedy_design(ctx.par, cand, kmax, 'D')
        elif nme == 'greedyAcomp':
            out[nme] = SEL.greedy_design(ctx.par, cand, kmax, 'A_comp')
        elif nme == 'greedyAT':
            out[nme] = SEL.greedy_design(ctx.par, cand, kmax, 'A_T', target=target)
        elif nme == 'greedyAcost':
            out[nme] = SEL.greedy_design(ctx.par, cand, kmax, 'A_all', cost=cost)
        elif nme == 'greedyGauss':
            out[nme] = SEL.greedy_gauss(sigma, cand, kmax, target=target)
        elif nme == 'greedyGaussCost':
            out[nme] = SEL.greedy_gauss(sigma, cand, kmax, target=target, cost=cost)
        elif nme == 'covered':
            out[nme] = SEL.most_covered_order(cand, ctx.coverage, rng)
        elif nme == 'central':
            out[nme] = SEL.centrality_order(cand, C)
        elif nme == 'pivqr':
            out[nme] = SEL.pivoted_qr_order(cand, ctx.Xc)
        elif nme == 'leverage':
            out[nme] = SEL.leverage_order(cand, ctx.Xc, max(ctx.r, 1))
        elif nme == 'fwdreg':
            out[nme] = SEL.greedy_forward_regression(cand, ctx.Xc, kmax)
    return out


def eval_fold(ctx, Xte_s, obs_te, selectors, methods, kgrid, rng, n_random=100, n_random_decision=10,
              rand_methods=('fa',), cluster=True, sel_cost=None, decision=True, rawsd=None, target=None):
    """Evaluate every test model. Returns list of record dicts (one per model x k x selector x method).
    Test models with identical candidate sets (always, in a dense block) share selections and batched
    predictions. Random: metrics averaged over n_random draws; decision metrics from the first
    n_random_decision draws. Coverage/zsq only for FA-type models with a predictive variance."""
    recs = []
    sigma = methods['gcov'].Sigma if 'gcov' in methods else None
    need_C = cluster or 'central' in selectors
    Cmat = SEL.abs_corr(ctx.Xs, ctx.obs) if need_C else None
    n_te = Xte_s.shape[0]
    groups = {}
    tmask = np.zeros(ctx.N, bool)
    if target is not None:
        tmask[list(target)] = True
    for i in range(n_te):
        cand = np.where(obs_te[i] & (~tmask if target is not None else True))[0]
        groups.setdefault(cand.tobytes(), (cand, []))[1].append(i)

    def varfun(mname, S):
        if mname == 'fa' or mname == 'fa_pcv':
            return FA.predicted_mse(methods[mname].par, S, np.arange(ctx.N))
        if mname == 'gcov':
            return methods['gcov'].cond_var(S)
        return None

    def run(models, cand, selname, S, k, dec, tag=None):
        XS = Xte_s[np.ix_(models, S)]
        out = []
        for mname, meth in methods.items():
            if tag is not None and mname not in tag:
                continue
            YH = INF.predict_many(meth, S, XS)
            var = varfun(mname, S)
            for a, i in enumerate(models):
                r = model_metrics(ctx, Xte_s[i], YH[a], S, obs_te[i] & (tmask if target is not None else True), var=var, decision=dec, rawsd=rawsd)
                if sel_cost is not None:
                    r['cost_S'] = float(sel_cost[S].sum())
                r.update(model=i, k=k, selector=selname, method=mname)
                out.append(r)
        return out

    for key, (cand, models) in groups.items():
        kg = [k for k in kgrid if k <= len(cand) - 3]
        if not kg:
            continue
        kmax = max(kg)
        orders = selector_orders(ctx, cand, kmax, selectors, rng, C=Cmat, cost=sel_cost, sigma=sigma, target=target)
        for selname, order in orders.items():
            for k in kg:
                recs.extend(run(models, cand, selname, order[:k], k, decision))
        if cluster:
            for k in kg:
                S = SEL.kmedoids(cand, Cmat, k, rng, n_init=3)
                recs.extend(run(models, cand, 'cluster', S, k, decision))
        acc = {}
        for d in range(n_random):
            perm = rng.permutation(cand)
            for k in kg:
                tag = None if d < n_random_decision else rand_methods
                for r in run(models, cand, 'random', perm[:k], k, decision and d < n_random_decision, tag=tag):
                    acc.setdefault((r['model'], k, r['method']), []).append(r)
        for (i, k, mname), lst in acc.items():
            keys = set().union(*[r.keys() for r in lst]) - {'model', 'k', 'selector', 'method'}
            r = {kk: float(np.mean([x[kk] for x in lst if kk in x])) for kk in keys}
            r['mse_sd_draws'] = float(np.std([x['mse'] for x in lst]))
            r.update(model=i, k=k, selector='random', method=mname)
            recs.append(r)
    return recs
