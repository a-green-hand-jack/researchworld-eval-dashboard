"""E1: synthetic compositional regression.  One replicate = fresh data draw, fit, calibrate, evaluate."""
import numpy as np
from .simplex import (BASE_SCORES, make_score_nll, fit_dirichlet_precision, uniform_simplex, score_l2)
from .conformal import conf_quantile, SigmaModel
from .metrics import binned_gap, wsc
from .predictors import make_predictor, SoftmaxLinear

ALPHAS = (0.05, 0.1, 0.2)
SCORE_NAMES = ["l2", "l1", "hell", "kl", "ait", "linf", "nll"]
SIG_NAMES = ["l2", "l1", "hell", "kl", "ait", "linf"]
NORMALISED = ["l2", "hell", "ait", "kl", "linf"]  # nll can be negative: no multiplicative scale
MONDRIAN = ["l2", "hell", "ait"]


def method_list(pred):
    m = [(s, "plain") for s in SCORE_NAMES] + [(s, "norm") for s in NORMALISED] + [(s, "mond") for s in MONDRIAN]
    if pred == "linear":
        m += [("l2", "cvplus")]
    return m


def mname(s, k):
    return {"plain": s, "norm": s + "_n", "mond": s + "_m", "cvplus": "cvp_" + s}[k]


def entropy(P):
    return -(P * np.log(P + 1e-12)).sum(1)


def run_rep(world, pred, seed, n_fit=1000, n_sig=500, n_cal=500, n_test=2000, eps=1e-3, n_vol=60, m_vol=4000, n_oracle=60, m_oracle=400, n_pool=300,
            alphas=ALPHAS, cvplus_K=10):
    rng = np.random.default_rng(seed)
    D = world.D
    Xf, Yf = world.sample(n_fit, rng)
    Xs, Ys = world.sample(n_sig, rng)
    Xc, Yc = world.sample(n_cal, rng)
    Xt, Yt = world.sample(n_test, rng)
    mdl = make_predictor(pred, seed).fit(Xf, Yf)
    Ps, Pc, Pt = (mdl.predict(X) for X in (Xs, Xc, Xt))
    phi = fit_dirichlet_precision(Ys, Ps, eps)
    fn = dict(BASE_SCORES, nll=make_score_nll(phi))
    S = {k: [f(Y, P, eps=eps) for Y, P in ((Ys, Ps), (Yc, Pc), (Yt, Pt))] for k, f in fn.items()}
    sig = SigmaModel(seed).fit(np.c_[Xs, Ps], np.stack([S[k][0] for k in SIG_NAMES], 1))
    sc_c, sc_t = sig.predict(np.c_[Xc, Pc]), sig.predict(np.c_[Xt, Pt])
    sigc = {k: sc_c[:, i] for i, k in enumerate(SIG_NAMES)}
    sigt = {k: sc_t[:, i] for i, k in enumerate(SIG_NAMES)}
    gc, gt = Pc.argmax(1), Pt.argmax(1)
    U = uniform_simplex(m_vol, D, rng) if D <= 5 else None
    vol_idx = rng.choice(n_test, n_vol, replace=False)
    ymax, ent = Pt.max(1), entropy(Pt)
    hs = world.scale(Xt)
    bnd = Yt.min(1) < 0.01
    Xpool, Ypool = world.sample(n_pool, rng)  # marginal-law pool: informativeness measure valid for any D
    or_idx = rng.choice(n_test, n_oracle, replace=False)  # points for oracle pointwise coverage (fresh draws of y | x)
    Yor = world.sample_y(np.repeat(Xt[or_idx], m_oracle, 0), rng).reshape(n_oracle, m_oracle, D)
    rows = []
    for s, kind in method_list(pred):
        if kind == "cvplus":
            cover, volfn = cvplus(Xf, Yf, Xc, Yc, Xt, Yt, vol_idx, alphas, cvplus_K, seed)
            thr = None
        else:
            sc, st = S[s][1], S[s][2]
            if kind == "norm":
                sc, st = sc / sigc[s], st / sigt[s]
            cover = {}
            if kind == "mond":
                qs = {a: np.array([conf_quantile(sc[gc == g], a) for g in range(D)]) for a in alphas}
                cover = {a: st <= qs[a][gt] for a in alphas}
                thr = qs[0.1][gt]
            else:
                qs = {a: conf_quantile(sc, a) for a in alphas}
                cover = {a: st <= qs[a] for a in alphas}
                thr = np.full(n_test, qs[0.1])
            if kind == "norm":
                thr = thr * sigt[s]
        c = cover[0.1]
        row = dict(method=mname(s, kind), **{f"cov{int(round(a*100)):02d}": cover[a].mean() for a in alphas})
        row["ymax_min"], row["ymax_max"] = binned_gap(c, ymax)
        row["ent_min"], row["ent_max"] = binned_gap(c, ent)
        if world.hetero:
            row["scale_min"], row["scale_max"] = binned_gap(c, hs, 3)
        row["bnd_frac"] = bnd.mean()
        row["bnd_cov"] = c[bnd].mean() if bnd.sum() >= 20 else np.nan
        row["int_cov"] = c[~bnd].mean() if (~bnd).sum() >= 20 else np.nan
        row["wsc"] = wsc(c, Xt, rng=np.random.default_rng(seed + 1))
        if U is not None:
            if kind == "cvplus":
                v = volfn(U)
            else:
                v = np.array([(fn[s](U, Pt[i], eps=eps) <= thr[i]).mean() if np.isfinite(thr[i]) else 1.0 for i in vol_idx])
            row["vol_med"], row["vol_mean"] = np.median(v), v.mean()
        if thr is not None:  # oracle pointwise coverage P(y in C(x_i) | x_i, cal) from fresh draws of y | x_i
            ci = np.array([(fn[s](Yor[j], Pt[i], eps=eps) <= thr[i]).mean() if np.isfinite(thr[i]) else 1.0
                           for j, i in enumerate(or_idx)])
            row["or_gap"], row["or_rmse"] = np.abs(ci - 0.9).mean(), np.sqrt(((ci - 0.9) ** 2).mean())
            row["or_q05"], row["or_q95"] = np.quantile(ci, 0.05), np.quantile(ci, 0.95)
        if kind == "cvplus":
            row["pool_frac"] = float(volfn(Ypool).mean())
        else:
            row["pool_frac"] = float(np.mean([(fn[s](Ypool, Pt[i], eps=eps) <= thr[i]).mean() if np.isfinite(thr[i]) else 1.0
                                              for i in vol_idx]))
        row["inf_frac"] = 0.0 if thr is None else float(np.mean(~np.isfinite(thr)))
        rows.append(row)
    return rows, dict(phi_hat=phi)


def cvplus(Xf, Yf, Xc, Yc, Xt, Yt, vol_idx, alphas, K, seed):
    """CV+ with the L2 score pooled over fit+cal data (softmax-linear predictor). Returns coverage dict and a volume fn."""
    X, Y = np.r_[Xf, Xc], np.r_[Yf, Yc]
    n = len(X)
    fold = np.random.default_rng(seed + 7).permutation(n) % K
    ms = [SoftmaxLinear().fit(X[fold != k], Y[fold != k]) for k in range(K)]
    Poo = np.zeros_like(Y)
    for k in range(K):
        Poo[fold == k] = ms[k].predict(X[fold == k])
    s = score_l2(Y, Poo)
    Pk_t = np.stack([m.predict(Xt) for m in ms])  # (K, nt, D)
    d = np.stack([score_l2(Yt, Pk_t[k]) for k in range(K)])  # (K, nt)
    cover = {a: (s[None, :] < d[fold, :].T).sum(1) < (1 - a) * (n + 1) for a in alphas}

    def volfn(Uu, a=0.1):
        lim = (1 - a) * (n + 1)
        out = []
        for i in vol_idx:
            dk = np.stack([score_l2(Uu, Pk_t[k, i]) for k in range(K)])
            out.append(((s[:, None] < dk[fold, :]).sum(0) < lim).mean())
        return np.array(out)
    return cover, volfn
