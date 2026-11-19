"""Synthetic mean-CI experiments with known truth.

usage: run_synth.py SCENARIO N_LAB RHO REPS SEED OUT.csv [NPROC]
  RHO = n / N  (labeled-to-unlabeled ratio), N = round(n / RHO).
X ~ N(0, I_5); mu(X) = X1 + 0.5 X2.  Each scenario defines (Y, f) with E[Y] = 0 unless noted.
`oracle` = control variate with the TRUE E[Y | f, X] (not available in practice; the efficiency bound
for control variates built from (f, X)).
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import sys, time, numpy as np, pandas as pd
from multiprocessing import Pool
from scipy.stats import norm
from civ import all_intervals, Z

D = 5
rt3 = lambda rng, n: rng.standard_t(3, n) / np.sqrt(3)  # unit variance


def mu(X): return X[:, 0] + 0.5 * X[:, 1]


# scenario -> (sampler(rng, n) -> (Y, f, X), oracle m(f, X), true mean)
def make(sc):
    def base(rng, n, eps=None):
        X = rng.standard_normal((n, D))
        e = rng.standard_normal(n) if eps is None else eps(rng, n)
        return X, e
    if sc == "calibrated":
        def s(rng, n):
            X, e = base(rng, n); m = mu(X); return m + e, m, X
        return s, lambda f, X: f, 0.0
    if sc == "monotone_miscal":      # E[Y|f] = logit(f): nonlinear but monotone
        def s(rng, n):
            X, e = base(rng, n); m = mu(X); return m + e, 1 / (1 + np.exp(-2 * m)), X
        return s, lambda f, X: 0.5 * np.log(f / (1 - f)), 0.0
    if sc == "nonmonotone":         # E[Y|f] = f^2 - Var(mu)
        def s(rng, n):
            X, e = base(rng, n); m = mu(X); return m**2 - 1.25 + e, m, X
        return s, lambda f, X: f**2 - 1.25, 0.0
    if sc == "X_informative":       # predictor misses an X-signal
        def s(rng, n):
            X, e = base(rng, n); m = mu(X); return m + 0.8 * X[:, 2] + e, m, X
        return s, lambda f, X: f + 0.8 * X[:, 2], 0.0
    if sc == "subgroup_bias":       # predictor biased in a subgroup
        def s(rng, n):
            X, e = base(rng, n); m = mu(X); return m + e, m + 1.5 * (X[:, 2] > 0), X
        return s, lambda f, X: f - 1.5 * (X[:, 2] > 0), 0.0
    if sc == "heavy_tail":          # calibrated predictor, t3 noise
        def s(rng, n):
            X, e = base(rng, n, rt3); m = mu(X); return m + 2 * e, m, X
        return s, lambda f, X: f, 0.0
    if sc == "f_noise_X_informative":   # predictor is noise, but the features X carry signal
        def s(rng, n):
            X, e = base(rng, n); return mu(X) + e, rng.standard_normal(n), X
        return s, lambda f, X: mu(X), 0.0
    if sc == "pure_noise":                    # neither f nor X carry signal
        def s(rng, n):
            X, e = base(rng, n); return 1.5 * e, rng.standard_normal(n), X
        return s, lambda f, X: 0 * f, 0.0
    if sc.startswith("knob"):       # headroom knob: E[Y|f] = cos(phi) z + sin(phi) (z^2-1)/sqrt2, z = f standardised
        phi = np.deg2rad(float(sc[4:]))
        sd = np.sqrt(1.25)
        mk = lambda f: np.cos(phi) * (f / sd) + np.sin(phi) * ((f / sd) ** 2 - 1) / np.sqrt(2)
        def s(rng, n):
            X, e = base(rng, n); f = mu(X); return mk(f) + e, f, X
        return s, lambda f, X: mk(f), 0.0
    raise ValueError(sc)


def oracle_ci(y_l, m_l, m_u):
    n, N = len(y_l), len(m_u)
    v = np.concatenate([m_l, m_u]).var()
    lam = 0.0 if v == 0 else np.cov(y_l, m_l, ddof=0)[0, 1] / ((1 + n / N) * v)
    th = y_l.mean() + lam * (m_u.mean() - m_l.mean())
    se = np.sqrt((y_l - lam * m_l).var(ddof=1) / n + lam**2 * m_u.var(ddof=1) / N)
    return th, Z * se


def one(a):
    sc, n, N, seed, learners = a
    samp, orc, truth = make(sc)
    rng = np.random.default_rng(seed)
    Yl, fl, Xl = samp(rng, n)
    _, fu, Xu = samp(rng, N)
    res = all_intervals(Yl, fl, Xl, fu, Xu, learners, rng=rng, boot=True)
    res["oracle"] = oracle_ci(Yl, orc(fl, Xl), orc(fu, Xu))
    row = {"seed": seed}
    for k, (th, hw) in res.items():
        if k.startswith("_"): row[k] = th
        else:
            row[k + "_cov"] = float(abs(th - truth) <= hw); row[k + "_w"] = 2 * hw; row[k + "_est"] = th
    return row


if __name__ == "__main__":
    sc, n, rho, reps, seed, out = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]), sys.argv[6]
    nproc = int(sys.argv[7]) if len(sys.argv) > 7 else 2
    N = int(round(n / rho))
    learners = ["lin_f", "iso_f", "poly_f", "gbm_f"] if sc.startswith("knob") else ["lin_f", "iso_f", "poly_f", "gbm_f", "lin_fX", "gbm_fX"]
    t0 = time.time()
    jobs = [(sc, n, N, seed * 1_000_003 + r, learners) for r in range(reps)]
    with Pool(nproc) as p: rows = p.map(one, jobs, chunksize=max(1, reps // 40))
    df = pd.DataFrame(rows); df.insert(0, "rho", rho); df.insert(0, "n", n); df.insert(0, "scenario", sc); df["N"] = N
    df.to_csv(out, index=False); print(sc, n, N, "reps", reps, "%.1fs" % (time.time() - t0), flush=True)
