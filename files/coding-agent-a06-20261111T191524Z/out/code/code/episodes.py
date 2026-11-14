"""One search episode -> reported numbers under every reporting protocol (all paired on the same labelled set)."""
import numpy as np
from sim_lib import *

def episode(Y, theta, n, opt, space, rng, opt_kw=None, split_f=(0.5,), cv_folds=5, nboot=100,
            do_boot=True, do_cv=True, do_maxt=True, do_cond=True, do_ladder=True, replace=True):
    opt_kw = opt_kw or {}; N = Y.shape[1]
    D = rng.integers(N, size=n) if replace else rng.choice(N, n, replace=False)
    Yd = Y[:, D]; r = {}
    o = OPTS[opt](Yd, space, rng, **opt_kw); k = int(o['k'])
    r.update(k=k, theta=theta[k], theta_star=theta[space].max(), theta_space_mean=theta[space].mean(), naive=Yd[k].mean())
    lo, hi = wilson(Yd[k].sum(), n); r.update(naive_lo=lo, naive_hi=hi)
    if not replace:   # truth on genuinely fresh questions = pool minus the dev questions
        comp = np.ones(N, bool); comp[D] = False; r.update(theta_fresh=Y[k, comp].mean())
    # --- sample splitting: select on the first f*n labelled questions, report on the remaining ones (fresh for k)
    for f in split_f:
        ns = int(round(f * n)); nr = n - ns
        o2 = OPTS[opt](Yd[:, :ns], space, rng, **opt_kw); k2 = int(o2['k'])
        x = Yd[k2, ns:].sum(); lo, hi = wilson(x, nr)
        r.update({f'split{f}_k_theta': theta[k2], f'split{f}_est': x / nr, f'split{f}_lo': lo, f'split{f}_hi': hi})
    # --- K-fold cross-fitting of the whole procedure (estimates the procedure's expected true accuracy at n(1-1/K))
    if do_cv:
        folds = np.array_split(rng.permutation(n), cv_folds); est = []; thk = []
        for fo in folds:
            tr = np.setdiff1d(np.arange(n), fo); k3 = int(OPTS[opt](Yd[:, tr], space, rng, **opt_kw)['k'])
            est.append(Yd[k3, fo].mean()); thk.append(theta[k3])
        r.update(cv_est=np.mean(est), cv_target=np.mean(thk))
    # --- search-replay bootstrap optimism correction
    if do_boot:
        app, orig, oobacc = boot_optimism(Yd, space, rng, opt, nb=nboot, oob=True, **opt_kw)
        r.update(boot_opt=r['naive'] - np.mean(app - orig))
        oobm = np.nanmean(oobacc)
        r.update(boot632=0.368 * r['naive'] + 0.632 * oobm, boot_oob=oobm)
    # --- simultaneous (max-t) interval over fully-evaluated configs; valid for any selection among them
    vis = np.asarray(o['vis']); r.update(nvis=len(vis))
    if do_maxt and len(vis) >= 3:   # valid for grid/random; heuristic for adaptive optimizers (greedy/minibatch) applied to their fully-evaluated set
        kpos = int(np.flatnonzero(vis == k)[0])
        est, (lo, hi), lb, c2 = maxt_bounds(Yd[vis], kpos, rng)
        r.update(maxt_lo=lo, maxt_hi=hi, maxt_lb=lb, maxt_c=c2)
        eb, (elo, ehi), (wlo, whi) = eb_winner(Yd[vis], kpos); r.update(eb_est=eb, eb_lo=elo, eb_hi=ehi, ebw_lo=wlo, ebw_hi=whi)
        if do_cond and opt == 'grid':
            med, (clo, chi), (vlo, vhi) = cond_winner(Yd[vis], kpos, rng=rng)
            r.update(cond_med=float(np.clip(med, 0, 1)), cond_lo=float(np.clip(clo, 0, 1)), cond_hi=float(np.clip(chi, 0, 1)))
    if do_ladder:
        for nm, eta in (('ladder_n13', n ** (-1 / 3)), ('ladder_n12', n ** (-1 / 2))):
            kb, s = ladder(Yd, space, rng, eta)
            r.update({f'{nm}_k_theta': theta[kb], f'{nm}_est': s})
    return r
