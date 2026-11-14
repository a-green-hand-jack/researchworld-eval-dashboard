"""Turn raw prediction npz files into a tidy metrics table (one row per bench/scenario/rep/budget/method)."""
import glob, os, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr, kendalltau

METHODS_SKIP = ("_beta",)


def rank_corr(p, t):
    if np.ptp(p) < 1e-12 or np.ptp(t) < 1e-12:
        return np.nan, np.nan
    return spearmanr(p, t)[0], kendalltau(p, t)[0]


def tidy(resdir):
    rows = []
    for fn in sorted(glob.glob(os.path.join(resdir, "*.npz"))):
        b, s, r = os.path.basename(fn)[:-4].split("__")
        z = np.load(fn)
        truth = z["truth"]; budgets = z["budgets"]
        for m in z.files:
            if m in ("truth", "tg", "sr", "budgets", "N", "src_mean_of_tg", "fit_iters"):
                continue
            P = z[m]
            for k, n in enumerate(budgets):
                p = P[k]
                if "_se_" in m:
                    continue
                if m.endswith("_beta"):
                    rows.append(dict(bench=b, scen=s, rep=int(r), n=int(n), method=m, beta=float(np.mean(p))))
                    continue
                e = p - truth
                sp, kt = rank_corr(p, truth)
                rows.append(dict(bench=b, scen=s, rep=int(r), n=int(n), method=m,
                                 mae=np.abs(e).mean(), rmse=np.sqrt((e ** 2).mean()), bias=e.mean(),
                                 spearman=sp, kendall=kt, ntg=len(truth)))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = tidy(sys.argv[1])
    df.to_csv(sys.argv[2], index=False)
    print(df.shape)


def coverage(resdir, z_crit=1.96):
    """Empirical coverage . width of pred +- z*SE intervals for the design-based estimators."""
    rows = []
    for fn in sorted(glob.glob(os.path.join(resdir, "*.npz"))):
        b, s, r = os.path.basename(fn)[:-4].split("__")
        z = np.load(fn); truth = z["truth"]; budgets = z["budgets"]
        for samp in ("rand", "sort", "pps"):
            for est in ("ht", "diff", "greg"):
                P = z[f"{samp}_{est}"]; SE = z[f"{samp}_se_{est}"]
                for k, n in enumerate(budgets):
                    rows.append(dict(bench=b, scen=s, rep=int(r), n=int(n), method=f"{samp}_{est}",
                                     cover=float((np.abs(P[k] - truth) <= z_crit * SE[k]).mean()),
                                     width=float(2 * z_crit * SE[k].mean())))
    return pd.DataFrame(rows)
