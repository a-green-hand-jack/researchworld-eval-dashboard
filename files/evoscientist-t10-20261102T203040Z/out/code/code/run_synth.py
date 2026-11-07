"""Experiment B: synthetic data with known E[Y|f] (mis)calibration regimes.
Usage: python code/run_synth.py <reps>
Outputs: results/synth.csv.gz (grid over scenario x n at N=10000) and results/synth_N.csv.gz (grid over N at n=200).
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "1"); os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
sys.path.insert(0, "code")
from ppi_lib import run_all, SUPER, control_variate_mean

SEED = 7771
sig = lambda x: 1 / (1 + np.exp(-x))


# each scenario: sampler(rng, size) -> (f, y); m(f) = E[Y|f]; truth = E[Y]
def mk(name):
    if name == "S0_calibrated":      # E[Y|f] = f
        m = lambda f: f
        def samp(rng, k):
            f = rng.normal(size=k); return f, f + rng.normal(size=k)
        return samp, m, 0.0
    if name == "S1_convex":          # monotone but nonlinear-ish
        m = lambda f: f + 0.8 * (f ** 2 - 1)
        def samp(rng, k):
            f = rng.normal(size=k); return f, m(f) + rng.normal(size=k)
        return samp, m, 0.0
    if name == "S2_symmetric":       # affine-uninformative, calibrated-informative
        m = lambda f: f ** 2 - 1
        def samp(rng, k):
            f = rng.normal(size=k); return f, m(f) + rng.normal(size=k)
        return samp, m, 0.0
    if name == "S3_overconfident":   # binary Y, f = sigmoid(3 z) while P(Y=1|z)=sigmoid(z)
        m = lambda f: sig(np.log(np.clip(f, 1e-12, 1 - 1e-12) / np.clip(1 - f, 1e-12, 1)) / 3)
        def samp(rng, k):
            z = rng.normal(scale=1.5, size=k); return sig(3 * z), (rng.uniform(size=k) < sig(z)).astype(float)
        return samp, m, 0.5
    if name == "S4_saturating":      # step-like
        m = lambda f: np.tanh(3 * f)
        def samp(rng, k):
            f = rng.normal(size=k); return f, m(f) + 0.5 * rng.normal(size=k)
        return samp, m, 0.0
    if name == "S5_uninformative":   # f independent of Y
        m = lambda f: 0 * f
        def samp(rng, k):
            return rng.normal(size=k), rng.normal(size=k)
        return samp, m, 0.0
    raise ValueError(name)


SCEN = ["S0_calibrated", "S1_convex", "S2_symmetric", "S3_overconfident", "S4_saturating", "S5_uninformative"]


GROUPS = {"cheap": ["classical", "ppi", "ppi++", "poly2", "poly3", "strat5", "strat10", "spline", "iso_cf"],
          "exp": ["ppi++py", "hgb_cf"]}


def one_rep(sc, n, N, rep, tag, group):
    rng = np.random.default_rng(np.random.SeedSequence([SEED, SCEN.index(sc), n, N, rep, tag]))
    samp, m, truth = mk(sc)
    fL, yL = samp(rng, n); fU, _ = samp(rng, N)
    res = run_all(yL, fL[:, None], fU[:, None], rng, methods=GROUPS[group])
    if group == "cheap":
        t, s, b = control_variate_mean(yL, m(fL)[:, None], m(fU)[:, None]); res["oracle_m"] = (t, s, 1)
    return [dict(scenario=sc, n=n, N=N, rep=rep, method=k, theta=t, sd=s, p=p, truth=truth) for k, (t, s, p) in res.items()]


def population_stats(sc, K=2_000_000):
    rng = np.random.default_rng(1)
    samp, m, truth = mk(sc); f, y = samp(rng, K)
    A = np.column_stack([np.ones(K), f]); b = np.linalg.lstsq(A, y, rcond=None)[0]
    vy = y.var()
    return dict(scenario=sc, var_y=vy, R2_affine=1 - np.mean((y - A @ b) ** 2) / vy, R2_cal=m(f).var() / vy,
                mean_y=y.mean(), truth=truth)


if __name__ == "__main__":
    group, reps = sys.argv[1], int(sys.argv[2]); os.makedirs("results", exist_ok=True); t0 = time.time()
    pd.DataFrame([population_stats(s) for s in SCEN]).to_csv("results/synth_population.csv", index=False)
    with Parallel(n_jobs=8, batch_size=4) as par:
        rows = []
        for sc in SCEN:
            for n in (30, 60, 100, 200, 500, 1000, 3000):
                out = par(delayed(one_rep)(sc, n, 10000, r, 0, group) for r in range(reps))
                rows += [x for o in out for x in o]
            print(sc, "grid-n done", time.time() - t0, flush=True)
        pd.DataFrame(rows).to_csv(f"results/synth_{group}.csv.gz", index=False)
        rows = []
        for sc in SCEN:
            for N in (200, 1000, 10000, 100000):
                out = par(delayed(one_rep)(sc, 200, N, r, 1, group) for r in range(reps))
                rows += [x for o in out for x in o]
            print(sc, "grid-N done", time.time() - t0, flush=True)
        pd.DataFrame(rows).to_csv(f"results/synth_N_{group}.csv.gz", index=False)
