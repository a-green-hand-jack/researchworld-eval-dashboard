"""Why do unclipped / calibrated PPI++ lose coverage under the plankton 2013->2014 shift?
Estimates, over R=300 draws per (n, N=20n), the PPI++ power-tuning weight lambda-hat (unclipped, ddof=0, pooled
variance of f over labeled+unlabeled as in ppi_py) when the unlabeled predictions come from 2014 (shift) or 2013 (control).
lambda>1 puts weight (1-lambda)<0 on the labeled-vs-unlabeled contrast, which is only valid if labeled and unlabeled have
the same distribution; lambda=1 (M2, or M3 after clipping) is valid whenever E[Y-f] is stable. Writes results/shift_lambda_check.csv."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd, data as D
p = D.population("plankton"); Y, f, fs = p["Y"], p["f"], p["f_shift"]
rng = np.random.default_rng(12345)
rows = []
for n in [50, 100, 200, 400, 1000]:
    N = 20 * n
    for tag, pool in (("shift", fs), ("control", f)):
        lam = []
        for _ in range(300):
            i = rng.integers(len(Y), size=n); j = rng.integers(len(pool), size=N)
            fl, yl, fu = f[i], Y[i], pool[j]
            c = np.cov(yl, fl, ddof=0)[0, 1]
            lam.append(c / ((1 + n / N) * np.concatenate([fl, fu]).var()))
        lam = np.array(lam)
        rows.append(dict(n=n, N=N, tag=tag, R=300, lam_mean=lam.mean(), lam_sd=lam.std(), frac_gt1=(lam > 1).mean()))
pd.DataFrame(rows).to_csv(os.path.join(os.path.dirname(__file__), "..", "results", "shift_lambda_check.csv"), index=False)
print("mean E[Y-f] 2013 %.4f, 2014 %.4f; var f 2013 %.4f, 2014 %.4f" % ((Y - f).mean(), (p["Y_shift"] - fs).mean(), f.var(), fs.var()))
