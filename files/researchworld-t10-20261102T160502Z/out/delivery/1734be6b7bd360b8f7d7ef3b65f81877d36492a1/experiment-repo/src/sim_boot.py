"""Finite-sample route: does a bootstrap (percentile / studentized) PPI++ interval repair small-n undercoverage,
and what does it cost in width?  Vectorised bootstrap of (labeled, unlabeled) with lambda re-estimated in every
resample.  Small n, N = 4n and 16n only (cost).
"""
import numpy as np, pandas as pd, sys, os, time
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(__file__))
import data as D, estimators as E
from sim import seed_for

B = 500


def boot_ppi(Y, f, fu, rng, alpha=0.05):
    n, N = len(Y), len(fu)
    il = rng.integers(0, n, (B, n)); iu = rng.integers(0, N, (B, N))
    Yb, fb, fub = Y[il], f[il], fu[iu]
    # lambda per resample (unclipped power tuning)
    allf = np.concatenate([fb, fub], 1)
    v = allf.var(1)
    c = ((Yb - Yb.mean(1, keepdims=True)) * (fb - fb.mean(1, keepdims=True))).mean(1)
    lam = np.where(v > 0, c / ((1 + n / N) * np.where(v > 0, v, 1)), 0.0)
    est_b = (Yb - lam[:, None] * fb).mean(1) + lam * fub.mean(1)
    se_b = np.sqrt((Yb - lam[:, None] * fb).var(1, ddof=1) / n + lam ** 2 * fub.var(1, ddof=1) / N)
    z, t = E.ppi_scores(Y, f, fu, both=True)
    est = 0.5 * (z[0] + z[1]); se = (z[1] - z[0]) / (2 * 1.959963984540054)
    pct = (np.quantile(est_b, alpha / 2), np.quantile(est_b, 1 - alpha / 2))
    tt = (est_b - est) / np.where(se_b > 0, se_b, np.nan)
    qlo, qhi = np.nanquantile(tt, 1 - alpha / 2), np.nanquantile(tt, alpha / 2)
    bt = (est - qlo * se, est - qhi * se)
    return {"ppipp_nc": z, "ppipp_boot_pct": pct, "ppipp_boot_t": bt}


def cell(args):
    name, n, N, R = args
    pop = D.population(name); th = pop["theta"]
    rng = np.random.default_rng(seed_for("final", "boot", name, n, N))
    cov = {}; wid = {}
    for k in range(R):
        i = rng.integers(0, len(pop["Y"]), n); Y, f = pop["Y"][i], pop["f"][i]
        fu = pop["f"][rng.integers(0, len(pop["Y"]), N)]
        cl = E.classical(Y)
        res = boot_ppi(Y, f, fu, rng); res["classical"] = cl
        for m, (lo, hi) in res.items():
            cov.setdefault(m, []).append(lo <= th <= hi); wid.setdefault(m, []).append(hi - lo)
    print("HUTIAN_PROGRESS boot", name, n, N, flush=True)
    return [dict(dataset=name, n=n, N=N, R=R, method=m, coverage=np.mean(cov[m]), width=np.mean(wid[m])) for m in cov]


if __name__ == "__main__":
    R = 1000
    cells = [(d, n, m * n, R) for d in ["ballots", "forest", "alphafold", "galaxies", "census_income", "gene_expression"]
             for n in [50, 100, 200] for m in [5, 20]]
    with Pool(2) as p:
        out = p.map(cell, cells, chunksize=1)
    pd.DataFrame([r for o in out for r in o]).to_csv("results/sim_boot.csv", index=False)
