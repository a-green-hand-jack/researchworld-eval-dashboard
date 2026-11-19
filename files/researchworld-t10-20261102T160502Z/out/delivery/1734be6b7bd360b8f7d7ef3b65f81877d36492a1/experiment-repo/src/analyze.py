"""Summaries from raw per-replication interval endpoints.

Output columns (one row per cell x method):
 population, n, N, tag, space, R, method,
 coverage, cov_lo, cov_hi (Wilson 95% CI), mc_se (binomial MC s.e.), width_mean, width_median, frac_infinite,
 ratio_M3_geo / ratio_M3_lo / ratio_M3_hi : paired geometric-mean width ratio (method / M3 = ppipp_pkg) on the same
     draws, with percentile-bootstrap 95% CI over replicates (1000 resamples); ratio_nc_*: same vs unclipped PPI++ (ppipp_nc);
 frac_shorter_M3: fraction of replicates in which the method is narrower than M3;
 frac_degenerate: fraction of replicates with a zero-width interval for the method or the reference (excluded from ratios).
"""
import numpy as np, pandas as pd, glob, os, sys
from scipy.stats import norm

METHODS = ["classical", "classical_t", "ppi", "ppipp_pkg", "ppipp", "ppipp_t", "ppipp_jk", "ppipp_nc", "ppipp_nc_t",
           "cal_lin", "cal_iso", "cal_bin", "cal_spl", "cal_lin_t", "cal_iso_t", "cal_bin_t", "cal_spl_t"]
M3, NC = "ppipp_pkg", "ppipp_nc"


def wilson(k, n, a=0.05):
    z = norm.ppf(1 - a / 2); p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def paired(w, wr, rng, nboot=1000):
    ok = (wr > 0) & (w > 0) & np.isfinite(w) & np.isfinite(wr)
    if ok.sum() < 5:
        return np.nan, np.nan, np.nan, 1 - ok.mean()
    lr = np.log(w[ok] / wr[ok])
    bi = rng.integers(0, len(lr), (nboot, len(lr)))
    gb = np.exp(lr[bi].mean(1))
    return np.exp(lr.mean()), np.quantile(gb, .025), np.quantile(gb, .975), 1 - ok.mean()


def summarize(rawdir, space, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for fn in sorted(glob.glob(rawdir + "/*.npz")):
        z = np.load(fn)
        pop, n, N, tag = os.path.basename(fn)[:-4].split("__")
        th, R = float(z["theta"]), int(z["R"])
        w3 = z["hi_" + M3] - z["lo_" + M3]
        wn = z["hi_" + NC] - z["lo_" + NC]
        for me in METHODS:
            lo, hi = z["lo_" + me], z["hi_" + me]
            cov = (lo <= th) & (th <= hi)
            w = hi - lo
            k = int(cov.sum()); wl, wh = wilson(k, R)
            g3 = paired(w, w3, rng); gn = paired(w, wn, rng)
            rows.append(dict(population=pop.replace("_", ":") if pop.startswith("syn_") else pop, n=int(n), N=int(N), tag=tag,
                             space=space, R=R, method=me, coverage=k / R, cov_lo=wl, cov_hi=wh,
                             mc_se=np.sqrt(k / R * (1 - k / R) / R), width_mean=np.mean(w[np.isfinite(w)]),
                             width_median=np.median(w), frac_infinite=np.mean(~np.isfinite(w)),
                             ratio_M3_geo=g3[0], ratio_M3_lo=g3[1], ratio_M3_hi=g3[2], ratio_nc_geo=gn[0],
                             ratio_nc_lo=gn[1], ratio_nc_hi=gn[2], frac_shorter_M3=np.mean(w < w3),
                             frac_degenerate=g3[3], theta=th))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    space = sys.argv[1] if len(sys.argv) > 1 else "final"
    for d in sorted(glob.glob(f"results/raw_{space}_*")):
        grid = d.split(f"raw_{space}_")[1]
        df = summarize(d, space); out = f"results/summary_{space}_{grid}.csv"
        df.to_csv(out, index=False); print(out, len(df))
