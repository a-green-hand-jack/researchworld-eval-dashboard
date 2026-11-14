"""Core library: selection-then-report simulation on a (configs x questions) correctness matrix.

Y: float array (K, N) of 0/1 correctness for K configurations on a pool of N questions.
The pool is the *population*; a "benchmark" S is n questions drawn i.i.d. (with replacement) from the pool,
so the true accuracy of config k is mu_k = Y[k].mean() exactly (no finite-population artefacts).

An *optimizer* maps the sample matrix Ys (K x n) to the index of the selected config.
A *protocol* turns (Ys, optimizer) into a reported number and/or interval for the selected config.
"""
import math
import numpy as np

Z95 = 1.959963984540054
Z95_1 = 1.6448536269514722


# ----------------------------------------------------------------------------- optimizers
def opt_exh(Ys, rng):
    """Exhaustive best-of-K: evaluate every config on all n questions, take argmax (random tie-break)."""
    m = Ys.mean(1)
    K = len(m)
    return int(np.argmax(m + rng.random(K) * 1e-9))


def sh_cost(K, n):
    R = max(1, math.ceil(math.log2(K))) if K > 1 else 0
    alive, cost = K, 0
    for r in range(1, R + 1):
        nr = math.ceil(n / 2 ** (R - r))
        cost += alive * nr
        alive = math.ceil(alive / 2)
    return cost


def opt_sh(Ys, rng):
    """Successive halving on nested prefixes of the (randomly ordered) benchmark: round r scores the surviving
    configs on the first ceil(n/2^(R-r)) questions and keeps the best half; the last round uses all n questions."""
    K, n = Ys.shape
    if K == 1:
        return 0
    R = math.ceil(math.log2(K))
    alive = np.arange(K)
    for r in range(1, R + 1):
        nr = math.ceil(n / 2 ** (R - r))
        m = Ys[alive, :nr].mean(1) + rng.random(len(alive)) * 1e-9
        keep = max(1, math.ceil(len(alive) / 2))
        alive = alive[np.argsort(-m)[:keep]]
    return int(alive[0])


OPTS = {"exh": opt_exh, "sh": opt_sh}


# ----------------------------------------------------------------------------- helpers
def wilson(p, n, z=Z95):
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def boot_counts(rng, n, B):
    """Multinomial bootstrap weights, shape (n, B)."""
    idx = rng.integers(0, n, size=(B, n))
    W = np.zeros((n, B), dtype=np.float32)
    for b in range(B):
        W[:, b] = np.bincount(idx[b], minlength=n)
    return W


def eb_paired(Ys, k):
    """Paired empirical-Bayes shrinkage estimate for config k: shrink its deviation from the config-average accuracy."""
    K, n = Ys.shape
    if K < 3:
        return float(Ys[k].mean())
    mbar_q = Ys.mean(0)                       # per-question average over configs
    D = Ys - mbar_q[None, :]                  # centred per question
    d = D.mean(1)                             # = mu_hat_k - mean_j mu_hat_j
    s2 = D.var(1, ddof=1) / n                 # sampling variance of d_k
    tau2 = max(0.0, d.var(ddof=1) - s2.mean())
    Bk = tau2 / (tau2 + s2[k] + 1e-18)
    return float(Ys.mean() + Bk * d[k])


# ----------------------------------------------------------------------------- one replicate
def replicate(Y, K_idx, n, opt, rng, B=200, split_fracs=(0.5,), folds=5, protocols=("naive", "split", "boot", "cv", "eb", "maxt")):
    """Run one search + all reporting protocols. Returns dict of scalars (floats).
    Y: (Ktot, N); K_idx: indices of the configs the optimizer may search."""
    N = Y.shape[1]
    Ysub = Y[K_idx]
    mu = Ysub.mean(1)                          # true accuracies (population = pool)
    S = rng.integers(0, N, size=n)
    Ys = Ysub[:, S]
    out = {}
    k = opt(Ys, rng)
    out["truth"] = mu[k]; out["oracle"] = mu.max(); out["mean_cfg"] = mu.mean()
    # out-of-sample truth: accuracy of the selected config on pool questions NOT in the benchmark sample S
    # (removes the finite-pool overlap between 'truth' and S; noisy per replicate but unbiased on average)
    oos = np.ones(N, dtype=bool); oos[S] = False
    out["truth_oos"] = Ysub[k][oos].mean() if oos.any() else mu[k]
    naive = Ys[k].mean(); out["naive"] = naive
    lo, hi = wilson(naive, n); out["naive_lo"], out["naive_hi"] = lo, hi
    K = len(K_idx)
    muhat = Ys.mean(1)
    se = np.sqrt(np.maximum(muhat * (1 - muhat), 1.0 / n) / n)
    if "split" in protocols:
        for rho in split_fracs:
            n2 = int(round(rho * n)); n1 = n - n2
            Ys1, Ys2 = Ys[:, :n1], Ys[:, n1:]
            k1 = opt(Ys1, rng)
            p2 = Ys2[k1].mean()
            l2, h2 = wilson(p2, n2)
            tag = f"split{int(rho*100)}"
            out[tag] = p2; out[tag + "_lo"], out[tag + "_hi"] = l2, h2; out[tag + "_truth"] = mu[k1]
    if "boot" in protocols or "maxt" in protocols:
        W = boot_counts(rng, n, B)
        M = Ys @ W / n                         # (K, B) bootstrap means
    if "boot" in protocols:
        if opt is opt_exh:
            kb = np.argmax(M + rng.random(M.shape) * 1e-9, axis=0)
            app = M[kb, np.arange(B)]
            orig = muhat[kb]
            oobmask = (W == 0).astype(np.float32)
            noob = oobmask.sum(0)
            oob_sum = np.einsum("kn,nb->kb", Ys, oobmask)
            oob = oob_sum[kb, np.arange(B)] / np.maximum(noob, 1)
        else:
            app = np.zeros(B); orig = np.zeros(B); oob = np.zeros(B)
            for b in range(B):
                idx = np.repeat(np.arange(n), W[:, b].astype(int))
                Yb = Ys[:, idx]
                kb_ = opt(Yb, rng)
                app[b] = Yb[kb_].mean(); orig[b] = muhat[kb_]
                om = W[:, b] == 0
                oob[b] = Ys[kb_][om].mean() if om.any() else muhat[kb_]
        optimism = float(np.mean(app - orig))
        out["boot_opt"] = naive - optimism
        out["boot_632"] = 0.368 * naive + 0.632 * float(np.mean(oob))
        out["boot_optimism"] = optimism
        out["boot_opt_lo"], out["boot_opt_hi"] = (naive - optimism) - Z95 * math.sqrt(naive * (1 - naive) / n), (naive - optimism) + Z95 * math.sqrt(naive * (1 - naive) / n)
    if "cv" in protocols:
        perm = rng.permutation(n); fid = np.arange(n) % folds
        tot = 0.0
        for f in range(folds):
            te = perm[fid == f]; tr = perm[fid != f]
            kf = opt(Ys[:, tr], rng)
            tot += Ys[kf, te].sum()
        out["cv"] = tot / n
        out["cv_lo"], out["cv_hi"] = wilson(out["cv"], n)
    if "eb" in protocols:
        e = eb_paired(Ys, k); out["eb"] = e
        out["eb_lo"], out["eb_hi"] = e - Z95 * math.sqrt(naive * (1 - naive) / n), e + Z95 * math.sqrt(naive * (1 - naive) / n)
    if "maxt" in protocols:
        T = (M - muhat[:, None]) / se[:, None]
        c1 = float(np.quantile(T.max(0), 0.95))
        c2 = float(np.quantile(np.abs(T).max(0), 0.95))
        out["maxt_lower1"] = naive - c1 * se[k]
        out["maxt_lo"], out["maxt_hi"] = naive - c2 * se[k], naive + c2 * se[k]
        out["maxt_c1"], out["maxt_c2"] = c1, c2
        out["naive_lower1"] = naive - Z95_1 * se[k]
        # Bonferroni / Hoeffding union bound for the one-sided lower bound
        out["hoeff_lower1"] = naive - math.sqrt(math.log(K / 0.05) / (2 * n))
    out["k"] = k
    return out


def run_many(Y, K, n, optname, R, seed, B=200, pool_cfgs=None, **kw):
    """R replicates; each draws a random subset of K configs from pool_cfgs (default: all)."""
    rng = np.random.default_rng(seed)
    pool_cfgs = np.arange(Y.shape[0]) if pool_cfgs is None else np.asarray(pool_cfgs)
    rows = []
    for _ in range(R):
        K_idx = rng.choice(pool_cfgs, size=K, replace=False) if K < len(pool_cfgs) else pool_cfgs
        rows.append(replicate(Y, K_idx, n, OPTS[optname], rng, B=B, **kw))
    keys = rows[0].keys()
    return {k: np.array([r[k] for r in rows if k in r]) for k in keys}


def summarize(res):
    """Bias/RMSE/coverage table w.r.t. truth of the selected config."""
    t = res["truth"]
    R = len(t)
    d = {}
    def point(name, truth=None):
        tt = t if truth is None else truth
        e = res[name] - tt
        return dict(bias=float(e.mean()), bias_se=float(e.std(ddof=1) / math.sqrt(R)), rmse=float(math.sqrt((e ** 2).mean())))
    for name in ["naive", "boot_opt", "boot_632", "cv", "eb"]:
        if name in res:
            d[name] = point(name)
    for name in [k for k in res if k.startswith("split") and k.endswith(tuple("0123456789"))]:
        d[name] = point(name, res[name + "_truth"])
    def cover(name, truth=None):
        tt = t if truth is None else truth
        c = (res[name + "_lo"] <= tt) & (tt <= res[name + "_hi"])
        return float(c.mean()), float((res[name + "_hi"] - res[name + "_lo"]).mean())
    for name in ["naive", "boot_opt", "cv", "eb", "maxt"]:
        if name + "_lo" in res:
            d.setdefault(name, {})
            d[name]["cov"], d[name]["width"] = cover(name)
    for name in [k for k in res if k.startswith("split") and k.endswith("_lo")]:
        base = name[:-3]
        d.setdefault(base, {})
        d[base]["cov"], d[base]["width"] = cover(base, res[base + "_truth"])
    for name in ["maxt_lower1", "naive_lower1", "hoeff_lower1"]:
        if name in res:
            d[name] = dict(cov=float((res[name] <= t).mean()), margin=float((res["naive"] - res[name]).mean()))
    if "truth_oos" in res:   # robustness: same point-estimate biases against the out-of-sample truth
        d["oos"] = {}
        for name in ["naive", "boot_opt", "boot_632", "cv", "eb"]:
            if name in res:
                e = res[name] - res["truth_oos"]
                d["oos"][name] = dict(bias=float(e.mean()), bias_se=float(e.std(ddof=1) / math.sqrt(R)))
    d["truth_mean"] = float(t.mean()); d["oracle_mean"] = float(res["oracle"].mean()); d["mean_cfg"] = float(res["mean_cfg"].mean())
    for name in [k for k in res if k.startswith("split") and k.endswith("_truth")]:
        d[name] = float(res[name].mean())
    return d


# ----------------------------------------------------------------------------- synthetic generator
def synth_matrix(K, N, base=0.25, tau=0.01, rho_noise=0.5, seed=0, offsets=None):
    """Latent-variable correctness matrix with controlled spread of true accuracies and cross-config correlation.
    p_ki = sigmoid(logit(base) + a_i + b_k + g_ki), a_i~N(0,s_a^2) (shared question difficulty),
    b_k~N(0,tau_logit^2) config effects, g_ki~N(0,s_g^2) interaction.  rho_noise in [0,1] sets s_a^2/(s_a^2+s_g^2)
    with s_a^2+s_g^2 = 4 (large => strongly bimodal outcomes).  tau is the std (in accuracy units) of config effects."""
    rng = np.random.default_rng(seed)
    tot = 4.0
    sa, sg = math.sqrt(rho_noise * tot), math.sqrt((1 - rho_noise) * tot)
    a = rng.normal(0, sa, N); g = rng.normal(0, sg, (K, N))
    # config effects in logit units chosen so accuracy std ~ tau
    b = rng.normal(0, 1, K) * tau / (base * (1 - base))
    if offsets is not None:   # explicit config effects (approximately in accuracy units; realised spread is reported by callers)
        b = np.asarray(offsets, dtype=float) / (base * (1 - base))
    z = math.log(base / (1 - base)) + a[None, :] + b[:, None] + g
    p = 1 / (1 + np.exp(-z))
    Y = (rng.random((K, N)) < p).astype(np.float32)
    return Y
