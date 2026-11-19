"""Evaluation protocol: hold out *models* (rows); the test model reveals only k chosen benchmarks; predict the rest.

For every held-out model i with observed benchmark set C_i (its non-missing cells), every selector chooses
S subset of C_i (using ONLY the training rows, via the fitted covariance), the predictor sees z_S, and the error is
measured on T = C_i \\ S (the model's other *actually observed* scores)."""
import numpy as np
from . import select as sel
from .fa import expected_mse
from . import predict as P

KS_DEFAULT = (1, 2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 24, 32, 40)


def rank_grid(N):
    rs = [r for r in (1, 2, 3, 4, 6, 8, 12) if (N - r) ** 2 > N + r and r < N]
    return rs or [1]


def standardize(Xtr):
    n = (~np.isnan(Xtr)).sum(0)
    with np.errstate(all='ignore'):
        mu = np.nanmean(Xtr, 0); sd = np.nanstd(Xtr, 0)
    mu = np.where(n > 0, mu, 0.0)
    sd = np.where((n >= 3) & (sd > 1e-9), sd, 1.0)
    return mu, sd


def make_orders(name, cov, par, cand, kmax, rng, popularity):
    """Return ordered list of positions (indices into cand)."""
    sub = cov[np.ix_(cand, cand)]
    if name == 'greedy_var': return sel.greedy_var(sub, kmax)
    if name == 'greedy_pivot': return sel.greedy_pivot(sub, kmax)
    if name == 'greedy_mi': return sel.greedy_mi(sub, kmax)
    if name == 'top_snr': return sel.top_snr(par['L'][cand], par['psi'][cand], kmax)
    if name == 'central': return sel.central(sub, kmax)
    if name == 'popular': return list(np.argsort(-popularity[cand], kind='stable')[:kmax])
    if name == 'random': return list(rng.permutation(len(cand))[:kmax])
    raise ValueError(name)


def run_split(X, tr, te, ks=KS_DEFAULT, selectors=('random', 'greedy_var', 'greedy_pivot', 'greedy_mi', 'top_snr', 'central', 'popular', 'kmedoids'),
              predictors=('gauss', 'fa', 'hybrid', 'avgshift', 'isvd', 'knn', 'mean'), full_preds=('gauss', 'fa'), grid_preds=('random', 'greedy_var'), main_cov='gauss',
              n_rand=10, seed=0, store_ks=(5, 10, 20), t0_frac=0.3, n_t0=2, t0_mode='frac', groups=None, fa_ranks=None, transform=None, inv_transform=None, tag=None):
    """X: (M,N) raw scores with NaN. tr/te: row index arrays. Returns (records, pooled, meta).
    For each test model: its observed set C is split into held-out targets T0 (30%, or one benchmark at a time when
    t0_mode='loo') and a pool C\\T0 from which a selector picks S (|S|=k); all selectors/predictors are scored on the same T0."""
    rng = np.random.default_rng(seed)
    Xraw_tr = X[tr]; Xtr = Xraw_tr
    if transform is not None: Xtr = transform(Xtr)
    mu, sd = standardize(Xtr)
    mu_raw, sd_raw = standardize(Xraw_tr)   # baseline predictor = training mean of the raw scores (same for every transform)
    Ztr = (Xtr - mu) / sd
    N = X.shape[1]
    pop = (~np.isnan(Ztr)).sum(0).astype(float)
    ok_col = pop >= 5
    # --- fit predictors (tuned on the training rows only)
    preds = {}; chosen = {}
    for name in predictors:
        if name == 'mean': preds[name] = P.MeanPred().fit(Ztr); continue
        if name == 'avgshift': preds[name] = P.AvgShift().fit(Ztr); continue
        grid = [dict(r=r) for r in (fa_ranks or rank_grid(N))] if name == 'fa' else P.GRIDS[name]
        kw, _ = P.tune(name, Ztr, grid, seed=seed)
        preds[name] = P.make(name, **kw).fit(Ztr); chosen[name] = kw
    fa = preds['fa']
    cov_fa = fa.cov(); par = fa.par
    cov_gauss = preds['gauss'].cov()
    cov_main, cov_alt, alt_name = (cov_gauss, cov_fa, 'fa') if main_cov == 'gauss' else (cov_fa, cov_gauss, 'gauss')
    # selection covariance estimated on ALL rows (incl. the test models): reference for the cost of estimating it from training rows only
    Xall = X if transform is None else transform(X)
    cov_orc = P.pairwise_corr((Xall - mu) / sd); cov_orc = 0.95 * cov_orc + 0.05 * np.eye(N)
    recs = []; pooled = []
    for i in te:
        zi = (X[i] if transform is None else transform(X[i][None])[0])
        xi_raw = X[i]
        zi = (zi - mu) / sd
        C = np.where(~np.isnan(zi) & ok_col)[0]
        if len(C) < (3 if t0_mode == 'loo' else 8): continue   # too few observed cells for a meaningful pool/target split
        # --- target draws: T0 = held-out targets (identical for every selector); pool = C \ T0 = what may be run
        if t0_mode == 'loo':
            draws = [np.array([j]) for j in C]
        elif groups is not None:   # family-disjoint targets: T0 = whole benchmark families, so no near-duplicate of a target is in the pool
            nt = max(2, int(round(t0_frac * len(C)))); g_ids = np.asarray(groups)[C]; ug = np.unique(g_ids); draws = []
            for _ in range(n_t0):
                T_ = []
                for g_ in rng.permutation(ug):
                    T_.extend(C[g_ids == g_])
                    if len(T_) >= nt: break
                draws.append(np.sort(np.array(T_)))
        else:
            nt = max(2, int(round(t0_frac * len(C))))
            draws = [np.sort(rng.choice(C, nt, replace=False)) for _ in range(n_t0)]
        for di, T in enumerate(draws):
            pool = np.setdiff1d(C, T)
            if len(pool) < 3: continue
            kk = [k for k in ks if len(pool) - k >= 1]
            if not kk: continue
            kmax = max(kk)
            sels = {}
            for s_ in selectors:
                if s_ == 'kmedoids': continue
                if s_ == 'random':
                    for d in range(n_rand): sels[f'random#{d}'] = pool[make_orders('random', cov_main, par, pool, kmax, rng, pop)]
                else:
                    sels[s_] = pool[make_orders(s_, cov_main, par, pool, kmax, rng, pop)]
            if 'greedy_var' in selectors:
                sels['greedy_var@oracle'] = pool[sel.greedy_var(cov_orc[np.ix_(pool, pool)], kmax)]
                sels[f'greedy_var@{alt_name}'] = pool[sel.greedy_var(cov_alt[np.ix_(pool, pool)], kmax)]
            for k in kk:
                sels_k = {'kmedoids': pool[sel.kmedoids(cov_main[np.ix_(pool, pool)], k, seed=seed)]} if 'kmedoids' in selectors else {}
                for sname, order in list(sels.items()) + list(sels_k.items()):
                    S = np.asarray(order[:k]) if sname != 'kmedoids' else np.asarray(order)
                    zS = zi[S]
                    base = sname.split('#')[0]
                    for pname, p in preds.items():
                        if pname not in full_preds and base not in grid_preds: continue
                        zh = p.predict(S, zS)
                        e = zh[T] - zi[T]
                        if transform is not None:   # always score errors in original units (points)
                            xh = inv_transform(zh[T] * sd[T] + mu[T]); er = xh - xi_raw[T]
                        else:
                            er = e * sd[T]
                        rec = dict(model=int(i), t0=di, selector=base, draw=sname, predictor=pname, k=k, nT=len(T),
                                   mse_z=float(np.mean((er / sd_raw[T]) ** 2)), mse_raw=float(np.mean(er ** 2)),
                                   mae_raw=float(np.mean(np.abs(er))), mse_z_model=float(np.mean(e ** 2)),
                                   agg_err=float(abs(np.mean(er))),
                                   mse0_z=float(np.mean(((mu_raw[T] - xi_raw[T]) / sd_raw[T]) ** 2)))
                        if pname == 'fa':
                            rec['exp_mse_z'] = expected_mse(par, S, np.concatenate([S, T]))
                        if pname == 'gauss':
                            Kss = cov_gauss[np.ix_(S, S)]; Kts = cov_gauss[np.ix_(T, S)]
                            rec['exp_mse_z'] = float(np.mean(np.diag(cov_gauss)[T] - np.einsum('ij,ji->i', Kts, np.linalg.solve(Kss + 1e-6 * np.eye(len(S)), Kts.T))))
                        recs.append(rec)
                        if pname == 'gauss' and base in ('random', 'greedy_var') and k in store_ks and sname in ('random#0', 'greedy_var') and di == 0:
                            for t in T: pooled.append((int(i), int(t), base, k, float(zh[t] * sd[t] + mu[t]), float(zi[t] * sd[t] + mu[t])))
    return recs, pooled, dict(chosen=chosen, spectrum=np.linalg.eigvalsh(cov_gauss)[::-1][:60].tolist(), fa_psi_mean=float(par['psi'].mean()), fa_r=int(par['L'].shape[1]), N=N)
