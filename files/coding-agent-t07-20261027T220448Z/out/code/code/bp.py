"""Coreset designs and estimators for benchmark prediction.

Notation: Y [models x N] binary; S source model indices, T target model indices; coreset C (|C|=n) selected using
Y[S] only; the target model's results on C are the only information about it. A design returns (C, W) where W[k] is
the population weight of coreset item k (sum ~ 1; for inclusion prob pi_i, W = 1/(N pi_i)). Estimators map target
coreset responses to a predicted full-benchmark accuracy.
"""
import numpy as np
from scipy.stats import spearmanr, kendalltau
from sklearn.linear_model import RidgeCV
from sklearn.cluster import KMeans
import irt as I

SHRINK_C0 = 0.5


# ----------------------------------------------------------------------------------------------- designs
def d_rand(N, n, rng, **kw):
    C = rng.choice(N, n, replace=False)
    return C, np.full(n, 1.0 / n)


def _systematic(order, pi, rng):
    """Fixed-size systematic sampling along `order` with inclusion probs pi (sum(pi)=n integer, pi<=1)."""
    cum = np.cumsum(pi[order])
    n = int(round(cum[-1]))
    pts = rng.random() + np.arange(n)
    pos = np.searchsorted(cum, pts, side="right")
    pos = np.minimum(pos, len(order) - 1)
    return order[pos]


def d_strat(N, n, rng, pS=None, **kw):
    """Difficulty-stratified: systematic sampling over items sorted by source accuracy (ties random)."""
    order = np.lexsort((rng.random(N), pS))
    C = _systematic(order, np.full(N, n / N), rng)
    return C, np.full(len(C), 1.0 / len(C))


def _capped_pi(q, n):
    """pi_i = min(1, c q_i) with sum n (water filling)."""
    pi = np.minimum(1.0, n * q / q.sum())
    for _ in range(100):
        free = pi < 1
        rest = n - (~free).sum()
        if free.sum() == 0 or rest <= 0:
            break
        pi_new = np.where(free, np.minimum(1.0, q * rest / q[free].sum()), 1.0)
        if np.allclose(pi_new, pi):
            break
        pi = pi_new
    return pi


def d_pps(N, n, rng, pS=None, vS=None, lam=0.5, **kw):
    """Neyman-style variance-aware design: pi_i ∝ (1-lam)/N + lam*sqrt(v_i)/sum sqrt(v); systematic PPS along difficulty."""
    s = np.sqrt(np.maximum(vS, 1e-4))
    q = (1 - lam) / N + lam * s / s.sum()
    pi = _capped_pi(q, n)
    order = np.lexsort((rng.random(N), pS))
    C = _systematic(order, pi, rng)
    return C, 1.0 / (N * pi[C])


def d_anchor(N, n, rng, YS=None, **kw):
    """Anchor points (Vivek et al.): k-means over item response vectors of source models; medoid per cluster,
    weight = cluster size / N."""
    X = YS.T.astype(np.float32)
    km = KMeans(n_clusters=n, n_init=1, max_iter=30, random_state=int(rng.integers(1 << 30))).fit(X)
    C, W = [], []
    for c in range(n):
        idx = np.where(km.labels_ == c)[0]
        if len(idx) == 0:
            continue
        dist = ((X[idx] - km.cluster_centers_[c]) ** 2).sum(1)
        C.append(idx[np.argmin(dist)])
        W.append(len(idx) / N)
    return np.array(C), np.array(W)


def d_dopt(N, n, rng, A=None, wI=None, **kw):
    """Greedy D-optimal (max log det Fisher information) item selection under the fitted IRT model."""
    d = A.shape[1]
    Minv = np.eye(d) * 1.0  # prior precision 1
    chosen = []
    avail = np.ones(N, bool)
    for _ in range(n):
        MA = A @ Minv
        gain = np.log1p(wI * np.einsum("nd,nd->n", MA, A))
        gain[~avail] = -np.inf
        i = int(np.argmax(gain))
        chosen.append(i)
        avail[i] = False
        a = A[i]
        Ma = Minv @ a
        Minv = Minv - np.outer(Ma, Ma) * wI[i] / (1 + wI[i] * a @ Ma)
    C = np.array(chosen)
    return C, np.full(n, 1.0 / n)


# --------------------------------------------------------------------------------------------- estimators
def e_mean(Yc, W):
    return (Yc * W[None]).sum(1) / W.sum()


def e_lin(Yc, W, YS_C, accS):
    x = (YS_C * W[None]).sum(1) / W.sum()
    if np.ptp(x) < 1e-9:
        return np.full(len(Yc), accS.mean())
    b, a = np.polyfit(x, accS, 1)
    return a + b * e_mean(Yc, W)


def e_ridge(Yc, YS_C, accS):
    m = RidgeCV(alphas=np.logspace(-2, 3, 12)).fit(YS_C, accS)
    return m.predict(Yc)


def e_irt_family(Yc, W, C, fit, N, prior_var=4.0, K=5, rng=None, cf=False):
    """Estimates from one IRT fit: irt (pure MAP-ability prediction), plug (imputation), greg (model-assisted:
    prediction + weighted residual correction), cal (pure prediction after per-target Platt recalibration of the logit,
    s*z+c fitted on the coreset), calgreg (recalibrated + residual correction); optionally gregcf (cross-fitted)."""
    A, b = fit["A"], fit["b"]
    th = I.infer_theta(A[C], b[C], Yc, prior_var)
    Z = th @ A.T + b[None]
    P = I._sig(Z)  # [T x N]
    pure = P.mean(1)
    mask = np.ones(N, bool)
    mask[C] = False
    plug = (Yc.sum(1) + P[:, mask].sum(1)) / N
    greg = pure + ((Yc - P[:, C]) * W[None]).sum(1)
    s, c = I.platt(Z[:, C], Yc)
    Pc = I._sig(s[:, None] * Z + c[:, None])
    cal = Pc.mean(1)
    calgreg = cal + ((Yc - Pc[:, C]) * W[None]).sum(1)
    # pretest / positive-part shrinkage of the recalibration shift: kappa=max(0,1-c0*Var(rbar)/rbar^2)
    res = Yc - P[:, C]
    rbar = (res * W[None]).sum(1)
    n_ = len(C)
    vr = res.var(1, ddof=1) / n_ * max(1 - n_ / N, 1e-3)
    kap = np.maximum(0.0, 1.0 - SHRINK_C0 * vr / np.maximum(rbar ** 2, 1e-12))
    shrcal = pure + kap * (cal - pure)
    out = dict(irt=pure, plug=plug, greg=greg, cal=cal, calgreg=calgreg, shrcal=shrcal)
    if cf:
        n = len(C)
        folds = np.arange(n) % K
        rng.shuffle(folds)
        resid_cf = np.zeros_like(Yc)
        for k in range(K):
            tr, te = folds != k, folds == k
            thk = I.infer_theta(A[C[tr]], b[C[tr]], Yc[:, tr], prior_var)
            resid_cf[:, te] = Yc[:, te] - I.predict_probs(thk, A[C[te]], b[C[te]])
        out["gregcf"] = pure + (resid_cf * W[None]).sum(1)
    return out


def metrics(est, tru):
    err = est - tru
    out = dict(rmse=float(np.sqrt(np.mean(err ** 2))), mae=float(np.mean(np.abs(err))), bias=float(np.mean(err)))
    if np.ptp(est) < 1e-12:
        out["spearman"] = 0.0; out["kendall"] = 0.0
    else:
        out["spearman"] = float(spearmanr(est, tru)[0]); out["kendall"] = float(kendalltau(est, tru)[0])
    return out


# ------------------------------------------------------------------------------------------------ driver
def fit_source(YS, ds, seed):
    pS = YS.mean(0)
    fits = {d: I.fit_irt(YS, d, seed=seed) for d in ds}
    for d, f in fits.items():
        P = I.predict_probs(f["theta"], f["A"], f["b"])
        f["v"] = ((YS - P) ** 2).mean(0)
        f["wI"] = (P * (1 - P)).mean(0)
    return pS, fits


DESIGNS = ("rand", "strat", "pps0.5", "pps1.0", "anchor", "dopt")
AUTO_DESIGNS = ("strat", "pps0.5", "pps1.0")


def evaluate_split(Y, S, T, budgets, seed, ds=(2, 4, 8), designs=DESIGNS, pre=None, auto=False, auto_reps=2, cf=True):
    """All designs x estimators for one source/target split. Returns list of row dicts. If auto, additionally
    evaluates the pseudo-shift-tuned selector AUTO (see `auto_select`)."""
    rng = np.random.default_rng(seed)
    YS, YT = Y[S], Y[T]
    N = Y.shape[1]
    accS, accT = YS.mean(1), YT.mean(1)
    pS, fits = pre if pre is not None else fit_source(YS, ds, seed)
    rows = []
    byname = {}

    def add(n, design, est_name, est):
        r = dict(n=n, design=design, est=est_name)
        r.update(metrics(est, accT))
        rows.append(r)

    rows.append(dict(n=0, design="none", est="src_mean", **metrics(np.full(len(T), accS.mean()), accT)))
    chosen = {}
    if auto:
        chosen = auto_select(YS, budgets, seed, ds, auto_reps)
    for n in budgets:
        if n >= N:
            continue
        dsg = {}
        if "rand" in designs: dsg["rand"] = d_rand(N, n, rng)
        if "strat" in designs: dsg["strat"] = d_strat(N, n, rng, pS=pS)
        for lam in (0.5, 1.0):
            if f"pps{lam}" in designs:
                dsg[f"pps{lam}"] = d_pps(N, n, rng, pS=pS, vS=fits[ds[1]]["v"], lam=lam)
        if "anchor" in designs: dsg["anchor"] = d_anchor(N, n, rng, YS=YS)
        if "dopt" in designs:
            for d in ds:
                dsg[f"dopt{d}"] = d_dopt(N, n, rng, A=fits[d]["A"], wI=fits[d]["wI"])
        for name, (C, W) in dsg.items():
            Yc = YT[:, C]
            if name.startswith("dopt"):
                dd = int(name[4:])
                for k, v in e_irt_family(Yc, W, C, fits[dd], N, rng=rng).items():
                    if k in ("irt", "plug", "greg", "cal", "shrcal"):
                        add(n, name, k, v)
                add(n, name, "mean", e_mean(Yc, W))
                continue
            add(n, name, "mean", e_mean(Yc, W)); byname[(n, name, "mean")] = rows[-1]
            add(n, name, "lin", e_lin(Yc, W, YS[:, C], accS))
            if name in ("rand", "strat", "anchor") or name in AUTO_DESIGNS:
                add(n, name, "ridge", e_ridge(Yc, YS[:, C], accS))
            for d in ds:
                cf_ = cf and (d == ds[1]) and name in ("rand", "strat", "pps0.5")
                for k, v in e_irt_family(Yc, W, C, fits[d], N, rng=rng, cf=cf_).items():
                    add(n, name, f"{k}{d}", v)
        if auto:
            for crit, ch in chosen[n].items():
                src = [r for r in rows if r["n"] == n and r["design"] + "/" + r["est"] == ch][0]
                r = dict(src)
                r.update(design="AUTO", est=crit, chosen=ch)
                rows.append(r)
    return rows


def _method_table(rows):
    """mean rmse per (n, method) over a list of rows."""
    acc = {}
    for r in rows:
        if r["n"] == 0:
            continue
        acc.setdefault((r["n"], r["design"] + "/" + r["est"]), []).append(r["rmse"])
    return {k: float(np.mean(v)) for k, v in acc.items()}


def auto_select(YS, budgets, seed, ds, reps):
    """Pseudo-shift tuning using only source models: two inner splits of the source set (random 30% held out, and
    strongest 25% held out). For each candidate (design, estimator) and budget, score = RMSE relative to random sampling
    on the inner targets. 'minimax' picks argmin of the worst score over the two inner splits, 'mean' the average."""
    m = len(YS)
    accS = YS.mean(1)
    rng = np.random.default_rng(777_000 + seed)
    perm = rng.permutation(m)
    nt = int(round(0.3 * m))
    inner = {"random": (np.sort(perm[nt:]), np.sort(perm[:nt]))}
    order = np.argsort(accS, kind="stable")
    nt2 = int(round(0.25 * m))
    inner["top"] = (np.sort(order[:-nt2]), np.sort(order[-nt2:]))
    tabs = {}
    for kind, (Si, Ti) in inner.items():
        pre = fit_source(YS[Si], ds, seed + 1)
        rows = []
        for rep in range(reps):
            rows += evaluate_split(YS, Si, Ti, budgets, seed * 100 + rep, ds=ds, designs=AUTO_DESIGNS, pre=pre, cf=False)
        tabs[kind] = _method_table(rows)
    chosen = {}
    for n in {k[0] for k in tabs["random"]}:
        cands = [k[1] for k in tabs["random"] if k[0] == n and (n, k[1]) in tabs["top"]]
        score = {c: [tabs[kind][(n, c)] / tabs[kind][(n, "strat/mean")] for kind in tabs] for c in cands}
        chosen[n] = {"minimax": min(cands, key=lambda c: max(score[c])), "mean": min(cands, key=lambda c: np.mean(score[c]))}
    return chosen
