"""Cell-level summary of a raw grid: python scripts/summarize.py <grid>  -> results/summary/<grid>.csv
Columns per (cell, estimator): bias, sd, rmse (+CIs), predicted bias (exact projection), predicted iid sd
sqrt(sigma_tot^2 L / n), mean sandwich / iid standard errors, 95% coverage of the sandwich and iid intervals."""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from netgate.summ import cell_cols, est_stats, boot_ci  # noqa: E402


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan
    ph = k / n
    den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den
    h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return float(c - h), float(c + h)


def cover(d, name, lo, hi, tau):
    ok = ((tau >= lo) & (tau <= hi)).to_numpy()
    m = (~(lo.isna() | hi.isna())).to_numpy()
    k, n = int(ok[m].sum()), int(m.sum())
    l, u = wilson(k, n)
    return {f"cover_{name}": k / n if n else np.nan, f"cover_{name}_lo": l, f"cover_{name}_hi": u,
            f"width_{name}": float((hi - lo)[m].mean()) if n else np.nan}


g = sys.argv[1]
df = pd.read_parquet(f"results/raw/{g}.parquet")
by = cell_cols(df)
ests = [c for c in df.columns if c in ("DM", "HT", "HAJEK", "STAG-REG", "STAG-direct", "REPEAT-REG") or c.startswith("HAJEK-r") or c.startswith("REG-") and not any(c.endswith(s) for s in ("_se", "_se_iid", "_biaspred", "_L"))]
rows = []
for key, d in df.groupby(by, dropna=False):
    base = dict(zip(by, key))
    base.update(n_rep=len(d), n_eff=d.n_eff.mean(), d_mean=d.d_mean.mean(), d_hm=d.d_hm.mean(), d_cv=d.d_cv.mean(), rho=d.rho.mean(),
                d_eff=d.d_eff.mean())
    sig_tot = np.sqrt(base.get("out.sigma", 0) ** 2 + base.get("out.sigma_alpha", 0) ** 2)
    gcr = base.get("design.kind") == "gcr"
    p = base.get("design.p")
    scale = abs(base.get("out.beta", 1.0) if not pd.isna(base.get("out.beta", 1.0)) else 1.0) + abs(base.get("out.gamma", 1.0))
    base["scale"] = scale
    if p is not None and not pd.isna(p):
        for tag, dd in (("", base["d_eff"]), ("_hm", 1 / (base["rho"] + (1 - base["rho"]) / base["d_hm"]) if gcr else base["d_hm"])):
            s_g = np.sqrt(p * (1 - p) / dd)
            base[f"Z1{tag}"], base[f"Z0{tag}"] = (1 - p) / s_g, p / s_g
    if "ball2" in d:
        base["ball2"] = d.ball2.mean(); base["n_indep"] = float((d.n_eff / d.ball2).mean())
    for nm in ests:
        r = dict(base, est=nm, **est_stats(d[nm] - d["tau"]))
        r["rmse_norm"], r["rmse_norm_lo"], r["rmse_norm_hi"] = r["rmse"] / scale, r["rmse_lo"] / scale, r["rmse_hi"] / scale
        r["bias_norm"], r["bias_norm_se"] = r["bias"] / scale, r["bias_se"] / scale
        r["tau"] = float(d["tau"].mean())
        if nm + "_L" in d:
            r["L"] = d[nm + "_L"].mean()
            r["bias_pred"] = d[nm + "_biaspred"].mean()
            r["bias_pred_se"] = float(d[nm + "_biaspred"].std(ddof=1) / np.sqrt(len(d)))   # spread over replicate graphs; excludes design-MC noise (M draws)
            r["sd_iid_pred"] = float(np.sqrt(sig_tot ** 2 * np.mean(d[nm + "_L"] / d.n_eff)))
        if nm + "_se" in d and d[nm + "_se"].notna().any():
            err = (d[nm] - d["tau"]).abs()
            r["se_sandwich"] = float(np.sqrt((d[nm + "_se"] ** 2).mean()))
            r["se_iid"] = float(np.sqrt((d[nm + "_se_iid"] ** 2).mean()))
            r["cov_sandwich"] = float((err <= 1.96 * d[nm + "_se"]).mean())
            r["cov_iid"] = float((err <= 1.96 * d[nm + "_se_iid"]).mean())
            for tag, col in (("sandwich", nm + "_se"), ("iid", nm + "_se_iid")):
                r.update(cover(d, tag, d[nm] - 1.96 * d[col], d[nm] + 1.96 * d[col], d["tau"]))
        if nm == "REG-L":
            for c in [c for c in d.columns if c.startswith("se_")]:      # grids e9, e10: alternative standard errors
                r.update(cover(d, c[3:], d[nm] - 1.96 * d[c], d[nm] + 1.96 * d[c], d["tau"]))
                r["se_mean_" + c[3:]] = float(np.sqrt((d[c] ** 2).mean()))
            if "boot_lo" in d:                                           # grid e7: pre-registered intervals
                r.update(cover(d, "bootstrap", d.boot_lo, d.boot_hi, d["tau"]))
                r.update(cover(d, "blockboot", d.bboot_lo, d.bboot_hi, d["tau"]))
                hw = 1.96 * d["REG-L_se"] + d["d3_B"]
                r.update(cover(d, "biasaware", d[nm] - hw, d[nm] + hw, d["tau"]))
        rows.append(r)
    if "HT_var_exact" in d:
        v = d["HT_var_exact"].to_numpy()
        rows.append(dict(base, est="HT-exact", n=len(v), bias=0.0, sd=float(np.sqrt(v.mean())), rmse=float(np.sqrt(v.mean())),
                         rmse_lo=boot_ci(v, lambda x: np.sqrt(np.mean(x)), 200)[0], rmse_hi=boot_ci(v, lambda x: np.sqrt(np.mean(x)), 200)[1]))
os.makedirs("results/summary", exist_ok=True)
out = pd.DataFrame(rows)
out.to_csv(f"results/summary/{g}.csv", index=False)
print(out.shape)
