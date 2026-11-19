"""Nominal-95% interval coverage of the subset-mean (analytic finite-population SE) and of the model-assisted estimators
(Hajek residual SE with finite-population correction; stratified designs use the conservative with-replacement formula).
usage: python coverage.py OUT.csv [reps]"""
import sys, hashlib, numpy as np, pandas as pd
from bpx import data, splits, methods
from run_experiment import seed_of

out = sys.argv[1]; reps = int(sys.argv[2]) if len(sys.argv) > 2 else 20
rows = []
for b in data.BENCHMARKS:
    S, names, _ = data.load(b); N = S.shape[1]
    for kind in ("random", "extrap"):
        for rep in range(reps):
            rng = np.random.default_rng(seed_of(b, kind, rep, "cov"))
            si, ti = splits.make_split(kind, S, names, rng)
            if kind == "extrap":
                si = np.sort(rng.choice(si, int(0.8 * len(si)), replace=False))
            src = methods.Source(S[si], fit_irt=False)
            T = S[ti].astype(np.float32); true = T.mean(1)
            for n in (20, 50, 100):
                if n > N // 4: continue
                for sname in ("random", "strat"):
                    r = np.random.default_rng(seed_of(b, kind, rep, n, sname, "cov"))
                    idx, pi = methods.SELECTORS[sname](src, n, r)
                    Y = T[:, idx]
                    fpc = np.sqrt(1 - n / N)
                    def add(method, est, se):
                        for i in range(len(true)):
                            rows.append(dict(benchmark=b, split=kind, rep=rep, n=n, method=method,
                                             cover=float(abs(est[i] - true[i]) <= 1.96 * se[i]), halfwidth=float(1.96 * se[i])))
                    if sname == "random":
                        p = Y.mean(1)
                        add("random+mean", p, np.sqrt(p * (1 - p) / (n - 1)) * fpc)
                    P = methods._lowrank_prob(src, idx, Y)
                    est = methods._dr(P, idx, pi, Y)
                    e = Y - P[:, idx]; w = 1 / pi; rbar = (e * w).sum(1) / w.sum()
                    se = np.sqrt(((w ** 2) * (e - rbar[:, None]) ** 2).sum(1)) / w.sum() * np.sqrt(n / (n - 1)) * fpc
                    add(f"{sname}+lowrank_dr", est, se)
    print(b, flush=True)
df = pd.DataFrame(rows)
df.groupby(["benchmark", "split", "n", "method"]).agg(coverage=("cover", "mean"), halfwidth=("halfwidth", "mean"), count=("cover", "size")).reset_index().to_csv(out, index=False)
