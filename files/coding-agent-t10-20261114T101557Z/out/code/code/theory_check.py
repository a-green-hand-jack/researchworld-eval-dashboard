"""Monte Carlo check of the variance formulas in the paper, with calibrators whose error is known.

Let m(Z) = E[Y|Z], sigma^2 = E[(Y - m)^2 | Z] (population residual term), a = n/(n+N), and let
delta be a centred function of Z with Var(delta) = s^2.  Proposition 2 of the paper says that for
the estimator with calibrator m_hat = m + delta,
    n * V = E[sigma^2] + a Var(m) + (1-a) Var(delta).
The oracle (s = 0) attains the efficient bound n V* = E[sigma^2] + a Var(m).
PPI++ (linear calibrator L of Y on f) has n V_PPI++ = E[sigma^2] + a Var(m) + (1-a) Delta,
with Delta = E(m - L)^2 (Theorem 3 of the paper; here with information Z = f).

Population constants come from one large Monte Carlo draw (fixed seed).
Output: /work/results/theory_check.csv
"""
import os
import sys
os.environ.setdefault("OMP_NUM_THREADS", "2")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd
from scipy.stats import norm

import ppi_flex as P

SCEN = ["lin", "nl", "bin", "xonly", "heavy"]
NS = [50, 200, 1000]
RATIOS = [1, 4, 16]
SVALS = [0.0, 0.1, 0.2, 0.4]
REPS = 3000
Z_CRIT = norm.ppf(0.975)


def sig(z):
    return 1 / (1 + np.exp(-z))


def draw(name, rng, size):
    """Return dict with f, Y, X (covariates or None), m_f = E[Y|f], m_X = E[Y|X]."""
    if name == "lin":
        X = rng.normal(size=size)
        f = 0.8 * X + 0.1
        m = 1 + 2 * X
        Y = m + np.sqrt(0.25 * (1 + 0.3 * X**2)) * rng.normal(size=size)
        return dict(f=f, Y=Y, X=None, m_f=m, m_X=m)
    if name in ("nl", "heavy"):
        X = rng.normal(size=size)
        m = np.sin(2 * X) + 0.5 * X
        noise = 0.5 * rng.normal(size=size) if name == "nl" else 0.5 * rng.standard_t(3, size=size)
        return dict(f=X, Y=m + noise, X=None, m_f=m, m_X=m)
    if name == "bin":
        X = rng.uniform(-2, 2, size=size)
        p = sig(3 * np.sin(X))
        Y = (rng.uniform(size=size) < p).astype(float)
        return dict(f=sig(X), Y=Y, X=None, m_f=p, m_X=p)
    if name == "xonly":
        X1 = rng.normal(size=size)
        X2 = rng.normal(size=size)
        mX = X1 + np.sin(2 * X2)
        Y = mX + 0.5 * rng.normal(size=size)
        return dict(f=X1, Y=Y, X=np.column_stack([X1, X2]), m_f=X1, m_X=mX)
    raise ValueError(name)


def h_of_f(f, center, scale):
    return (np.sin(3 * f) - center) / scale


def population_constants(name, size=4_000_000, seed=11):
    rng = np.random.default_rng(seed)
    d = draw(name, rng, size)
    f, Y = d["f"], d["Y"]
    hc = np.sin(3 * f).mean()
    hs = np.sin(3 * f).std()
    consts = {}
    Lf = np.polyval(np.polyfit(f, Y, 1), f)
    consts["f"] = dict(E_s2=np.mean((Y - d["m_f"]) ** 2), Var_m=d["m_f"].var(),
                       Delta=np.mean((d["m_f"] - Lf) ** 2), mu=Y.mean())
    if d["X"] is not None:
        consts["X"] = dict(E_s2=np.mean((Y - d["m_X"]) ** 2), Var_m=d["m_X"].var(),
                           Delta=np.nan, mu=Y.mean())
    consts["hc"], consts["hs"] = hc, hs
    return consts


def draw_sample(name, rng, n, N):
    dL = draw(name, rng, n)
    dU = draw(name, rng, N)
    return dL, dU


def main():
    rows = []
    for name in SCEN:
        C = population_constants(name)
        mu = C["f"]["mu"]
        infos = ["f"] + (["X"] if "X" in C else [])
        for info in infos:
            c = C[info]
            for n in NS:
                for ratio in RATIOS:
                    N = n * ratio
                    a = n / (n + N)
                    rng = np.random.default_rng([20260301, SCEN.index(name), n, ratio, infos.index(info)])
                    res = {}
                    for rep in range(REPS):
                        dL, dU = draw_sample(name, rng, n, N)
                        Y_L, f_L, f_U = dL["Y"], dL["f"], dU["f"]
                        e0, v0 = P.ppi_pp(Y_L, f_L, f_U)
                        res.setdefault("ppi_pp", []).append((e0, v0))
                        mL = dL["m_f"] if info == "f" else dL["m_X"]
                        mU = dU["m_f"] if info == "f" else dU["m_X"]
                        hL = h_of_f(f_L, C["hc"], C["hs"])
                        hU = h_of_f(f_U, C["hc"], C["hs"])
                        for s in SVALS:
                            mLh = mL + s * hL
                            mUh = mU + s * hU
                            e = Y_L.mean() + (1 - a) * (mUh.mean() - mLh.mean())
                            v = np.var(Y_L - (1 - a) * mLh, ddof=1) / n + (1 - a) ** 2 * np.var(mUh, ddof=1) / N
                            res.setdefault(f"oracle_s{s}", []).append((e, v))
                    # population n*V for PPI++ (f-only linear) -- its own calibrator error is Delta_f
                    nV_pp = C["f"]["E_s2"] + a * C["f"]["Var_m"] + (1 - a) * C["f"]["Delta"]
                    base_v = np.array([x[1] for x in res["ppi_pp"]])
                    base_w = 2 * Z_CRIT * np.sqrt(base_v).mean()
                    for k, vals in res.items():
                        e = np.array([x[0] for x in vals])
                        v = np.array([x[1] for x in vals])
                        if k == "ppi_pp":
                            s2 = np.nan
                            nV_pred = nV_pp
                        else:
                            s2 = float(k.replace("oracle_s", "")) ** 2
                            nV_pred = C[info]["E_s2"] + a * C[info]["Var_m"] + (1 - a) * s2
                            # hs-scaled h has variance 1 under the population law, so Var(delta) = s^2
                        width = 2 * Z_CRIT * np.sqrt(v).mean()
                        rows.append(dict(
                            scenario=name, info=info, n=n, N=N, ratio=ratio, a=a, method=k,
                            Var_delta=s2, Delta_f=C["f"]["Delta"], Var_m=C[info]["Var_m"],
                            E_s2=C[info]["E_s2"], mu=mu,
                            emp_sd=np.std(e, ddof=1), pred_sd=np.sqrt(nV_pred / n),
                            mean_est_sd=np.sqrt(np.mean(v)),
                            bias=np.mean(e) - mu, emp_cov=np.mean(np.abs(e - mu) <= Z_CRIT * np.sqrt(v)),
                            width_ratio_emp=width / base_w,
                            width_ratio_pred=np.sqrt(nV_pred / nV_pp),
                        ))
                    print(name, info, n, ratio, flush=True)
    df = pd.DataFrame(rows)
    out = "/work/results/theory_check.csv"
    df.to_csv(out, index=False)
    print("wrote", out, df.shape)


if __name__ == "__main__":
    main()
