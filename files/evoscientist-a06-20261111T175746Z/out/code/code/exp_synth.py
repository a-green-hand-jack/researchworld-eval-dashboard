"""E6: synthetic validation of the theory and of the reporting protocols (CPU only).

python code/exp_synth.py --out results/synth.json
"""
import argparse, json, math, sys, time
import numpy as np
from scipy import stats
sys.path.insert(0, "code")
import sel
from common import pmap, to_py

ap = argparse.ArgumentParser()
ap.add_argument("--out", required=True); ap.add_argument("--R", type=int, default=600)
ap.add_argument("--nproc", type=int, default=3); ap.add_argument("--N", type=int, default=40000)
ap.add_argument("--only", default="")
a = ap.parse_args()
NPOP = a.N


def emax_norm(K):
    x = np.linspace(-9, 9, 40001)
    return float(np.trapezoid(x * K * stats.norm.cdf(x) ** (K - 1) * stats.norm.pdf(x), x)) if K > 1 else 0.0


def regime_matrix(name, K, seed=0, base=0.25, rho=0.3):
    if name.startswith("tau"):
        return sel.synth_matrix(K, NPOP, base, float(name[3:]), rho, seed)
    if name == "null":
        return sel.synth_matrix(K, NPOP, base, 0.0, rho, seed)
    if name == "spread1":    # config effects ~ N(0, 1pt^2)
        return sel.synth_matrix(K, NPOP, base, 0.01, rho, seed)
    if name == "spread3":    # N(0, 3pt^2)
        return sel.synth_matrix(K, NPOP, base, 0.03, rho, seed)
    if name.startswith("needle") and name != "needle":   # needle<delta>: one config +delta (accuracy units), rest equal
        off = np.zeros(K); off[0] = float(name[6:])
        return sel.synth_matrix(K, NPOP, base, 0.0, rho, seed, offsets=off)
    if name == "needle":     # one config +5pt, rest equal
        off = np.zeros(K); off[0] = 0.05
        return sel.synth_matrix(K, NPOP, base, 0.0, rho, seed, offsets=off)
    if name == "heavy":      # Laplace-like heavy-tailed config effects, scale 1pt
        rng = np.random.default_rng(seed + 99)
        off = rng.laplace(0, 0.01, K)
        return sel.synth_matrix(K, NPOP, base, 0.0, rho, seed, offsets=off)
    raise ValueError(name)


def job(args):
    kind, regime, K, n, rho, R, seed, optname = args
    Y = regime_matrix(regime, K, seed=seed, rho=rho)
    res = sel.run_many(Y, K, n, optname, R, seed + 1, B=200, split_fracs=(0.2, 0.5))
    s = sel.summarize(res)
    mu = Y.mean(1)
    cov = np.cov(Y[:min(K, 64)]); var = Y.var(1).mean()
    rho_hat = float((cov.sum() - np.trace(cov)) / (cov.shape[0] * (cov.shape[0] - 1)) / var)
    s.update(kind=kind, regime=regime, K=K, n=n, rho_target=rho, rho_hat=rho_hat, sigma=math.sqrt(var), opt=optname, R=R,
             mu_sd=float(mu.std()), mu_range=float(mu.max() - mu.min()), mu_top_gap=float(np.sort(mu)[-1] - np.sort(mu)[-2]),
             mu_top_minus_median=float(mu.max() - np.median(mu)),
             pred_null=math.sqrt(var) * math.sqrt(max(0, 1 - rho_hat) / n) * emax_norm(K),
             pred_hoeffding=math.sqrt(math.log(K) / (2 * n)) if K > 1 else 0.0,
             pred_subgauss=math.sqrt(var) * math.sqrt(2 * math.log(K) / n) if K > 1 else 0.0)
    return s


if __name__ == "__main__":
    jobs = []
    R = a.R
    R_small = max(100, int(R * 0.3))   # fewer replicates for the expensive K>=256 / successive-halving settings
    # (A) bias vs K and n under the null, two correlation levels
    for rho in (0.0, 0.3, 0.7):
        for K in (2, 4, 8, 16, 32, 64, 128, 256, 1000):
            for n in (100, 400, 1600):
                jobs.append(("scaleK", "null", K, n, rho, R if K <= 256 else R_small, 1000 + K, "exh"))
    # (B) gap sweep: K=32 configs with N(0,tau^2) effects, n=400
    for tau in (0.0, 0.0025, 0.005, 0.01, 0.02, 0.04):
        jobs.append(("gap", f"tau{tau}", 32, 400, 0.3, R, 2000 + int(tau * 1e4), "exh"))
    # (C) protocol comparison across regimes
    for regime in ("null", "spread1", "spread3", "needle", "heavy"):
        for (K, n) in ((8, 200), (32, 200), (32, 800), (256, 400)):
            jobs.append(("regimes", regime, K, n, 0.3, R if K <= 32 else R_small, 3000 + K + n, "exh"))
    for regime in ("null", "spread1"):
        for (K, n) in ((32, 200), (32, 800)):
            jobs.append(("regimes", regime, K, n, 0.3, R_small, 4000 + K + n, "sh"))
    if a.only == "needle_sweep":   # (D) bias vs needle size: K=32, n=400  (run separately: --only needle_sweep)
        jobs = [("needle_sweep", f"needle{d}", 32, 400, 0.3, R, 5000 + int(d * 1000), "exh")
                for d in (0.0, 0.01, 0.02, 0.03, 0.04, 0.06, 0.08, 0.12, 0.2)]
    t0 = time.time()
    out = pmap(job, jobs, a.nproc)
    print("done", len(jobs), "jobs in", time.time() - t0, flush=True)
    json.dump(to_py(dict(rows=out, N=NPOP)), open(a.out, "w"))
