"""E2 (hard labels = simplex vertices) and E3 (CIFAR-10H soft labels) from classifier softmax outputs."""
import numpy as np
from scipy.special import softmax
from .simplex import BASE_SCORES, score_ait, score_l2, replace_zeros, uniform_simplex
from .conformal import conf_quantile, SigmaModel
from .metrics import binned_gap, wsc

ALPHAS = (0.05, 0.1, 0.2)


# ---------- E2: label-set scores, S_all[i, k] = score of candidate label k ----------
def vertex_scores(P, name, eps=1e-3):
    K = P.shape[1]
    Eye = np.eye(K)[None, :, :]
    Pb = P[:, None, :]
    if name == "ait":
        return score_ait(np.broadcast_to(Eye, (len(P), K, K)), Pb, eps=eps)
    return BASE_SCORES[name](np.broadcast_to(Eye, (len(P), K, K)), Pb)


def aps_scores(P, U, lam=0.0, kreg=0):
    """Randomised APS (lam=0) / RAPS: score of candidate k = mass ranked strictly above k + U*p_k (+ penalty)."""
    order = np.argsort(-P, axis=1)
    Ps = np.take_along_axis(P, order, 1)
    cum = np.cumsum(Ps, 1) - Ps
    rank = np.arange(1, P.shape[1] + 1)[None, :]
    s_sorted = cum + U[:, None] * Ps + lam * np.maximum(rank - kreg, 0)
    S = np.empty_like(s_sorted)
    np.put_along_axis(S, order, s_sorted, 1)
    return S


E2_METHODS = ["lac", "aps", "raps", "l2", "l1", "hell", "kl", "ait3", "ait1", "lac_cc"]


def all_scores(P, U):
    return {"lac": 1 - P, "aps": aps_scores(P, U), "raps": aps_scores(P, U, 0.01, 2),
            "l2": vertex_scores(P, "l2"), "l1": vertex_scores(P, "l1"), "hell": vertex_scores(P, "hell"),
            "kl": vertex_scores(P, "kl"), "ait3": vertex_scores(P, "ait", 1e-3), "ait1": vertex_scores(P, "ait", 1e-1),
            "lac_cc": 1 - P}


def run_e2_rep(P, y, n_cal, rng, alphas=ALPHAS, extra_feat=None):
    n, K = P.shape
    perm = rng.permutation(n)
    ci, ti = perm[:n_cal], perm[n_cal:]
    U = rng.uniform(size=n)
    S = all_scores(P, U)
    rows, sets = [], {}
    pm, pt = P[ti], P[ti].max(1)
    for m in E2_METHODS:
        Sc = S[m][ci, y[ci]]
        St = S[m][ti]
        cov, size = {}, {}
        for a in alphas:
            if m == "lac_cc":
                q = np.array([conf_quantile(Sc[y[ci] == k], a) for k in range(K)])
                sets_a = St <= q[None, :]
            else:
                sets_a = St <= conf_quantile(Sc, a)
            cov[a] = sets_a[np.arange(len(ti)), y[ti]]
            size[a] = sets_a.sum(1)
            if a == 0.1:
                sets[m] = sets_a
        c, sz = cov[0.1], size[0.1]
        row = dict(method=m, **{f"cov{int(round(a*100)):02d}": cov[a].mean() for a in alphas},
                   **{f"size{int(round(a*100)):02d}": size[a].mean() for a in alphas})
        yt = y[ti]
        cc = np.array([c[yt == k].mean() for k in range(K)])
        row["classcov_min"], row["classcov_mean"] = cc.min(), cc.mean()
        bins = [(1, 1), (2, 3), (4, K)]
        sv = [c[(sz >= lo) & (sz <= hi)] for lo, hi in bins]
        sv = [v.mean() for v in sv if len(v) >= 30]
        row["sscv_min"] = min(sv) if sv else np.nan
        row["empty_frac"] = float((sz == 0).mean())
        row["conf_min"], row["conf_max"] = binned_gap(c, pt)
        row["wsc"] = wsc(c, np.log(P[ti] + 1e-6), rng=np.random.default_rng(rng.integers(1 << 30)))
        row["maxsize_frac_all"] = float((sz == K).mean())
        rows.append(row)
    ident = {f"same_as_lac_{m}": float((sets[m] == sets["lac"]).all(1).mean()) for m in ["l2", "l1", "hell", "kl", "ait3", "ait1", "aps", "raps"]}
    return rows, ident


# ---------- E3: soft labels ----------
E3_PLAIN = ["l2", "l1", "hell", "kl", "ait", "linf"]


def run_e3_rep(P, Y, n_sig, n_cal, rng, eps=1e-3, alphas=ALPHAS, n_pool=300):
    n, K = P.shape
    perm = rng.permutation(n)
    si, ci, ti = perm[:n_sig], perm[n_sig:n_sig + n_cal], perm[n_sig + n_cal:]
    S = {k: BASE_SCORES[k](Y, P, eps=eps) for k in E3_PLAIN}
    sig = SigmaModel(int(rng.integers(1 << 30))).fit(P[si], np.stack([S[k][si] for k in E3_PLAIN], 1))
    sg = sig.predict(P)
    sgd = {k: sg[:, i] for i, k in enumerate(E3_PLAIN)}
    gH = -(np.where(Y > 0, Y * np.log(np.where(Y > 0, Y, 1)), 0)).sum(1)  # entropy of human distribution
    pm = P.max(1)
    gm = P.argmax(1)
    pool = rng.choice(ti, n_pool, replace=False)
    rows = []
    for s in E3_PLAIN:
        for kind in ("plain", "norm", "mond"):
            if kind == "norm":
                sc, st = S[s][ci] / sgd[s][ci], S[s][ti] / sgd[s][ti]
            else:
                sc, st = S[s][ci], S[s][ti]
            if kind == "mond":
                qs = {a: np.array([conf_quantile(sc[gm[ci] == g], a) for g in range(K)]) for a in alphas}
                cov = {a: st <= qs[a][gm[ti]] for a in alphas}
                thr = qs[0.1][gm[ti]]
            else:
                qs = {a: conf_quantile(sc, a) for a in alphas}
                cov = {a: st <= qs[a] for a in alphas}
                thr = np.full(len(ti), qs[0.1])
            if kind == "norm":
                thr = thr * sgd[s][ti]
            c = cov[0.1]
            name = s + {"plain": "", "norm": "_n", "mond": "_m"}[kind]
            row = dict(method=name, **{f"cov{int(round(a*100)):02d}": cov[a].mean() for a in alphas})
            row["conf_min"], row["conf_max"] = binned_gap(c, pm[ti])
            hH = gH[ti]
            row["ambig_min"], row["ambig_max"] = binned_gap(c, hH)
            row["wsc"] = wsc(c, np.log(P[ti] + 1e-6), rng=np.random.default_rng(rng.integers(1 << 30)))
            # informativeness: fraction of *other* images' human distributions inside the region (lower = tighter)
            Ypool = Y[pool]
            pos = {j: i for i, j in enumerate(ti)}
            fr = []
            for j in pool[:100]:
                i = pos[j]
                if not np.isfinite(thr[i]):
                    fr.append(1.0); continue
                sj = BASE_SCORES[s](Ypool, P[j], eps=eps)
                fr.append((sj <= thr[i]).mean())
            row["pool_frac"] = float(np.mean(fr))
            row["inf_frac"] = float(np.mean(~np.isfinite(thr)))
            rows.append(row)
    return rows
