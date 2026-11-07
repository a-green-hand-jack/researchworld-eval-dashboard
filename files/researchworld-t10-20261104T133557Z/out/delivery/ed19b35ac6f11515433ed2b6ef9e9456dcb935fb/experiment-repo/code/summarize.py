"""Aggregate raw per-replicate rows into per-cell summaries.

usage: [WIDTH_ONLY=1] summarize.py RAW_DIR OUT.csv [BASELINE]
For every method m (columns m_cov, m_w): coverage, its Monte-Carlo SE and 95% Wilson interval, mean width, and the paired
geometric-mean width ratio m / BASELINE (default ppi++, the Wald PPI++ interval) with a 95% CI (delta method over replicates).
`ratio_lfl` is the like-for-like ratio: m over PPI++ with the same calibration (Wald -> ppi++, `_t` -> ppi++_t, `_boot` -> ppi++_boot),
the comparison used for the headline (a wider-but-valid interval is compared with an equally calibrated baseline).
For OLS files (columns like m_c0_cov) the coordinate is part of the method name.
"""
import sys, glob, os, numpy as np, pandas as pd

raw, out = sys.argv[1], sys.argv[2]
base_default = sys.argv[3] if len(sys.argv) > 3 else "ppi++"
rows = []


def wilson(p, n, z=1.96):
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return c - h, c + h


def pratio(w, b):
    lr = np.log(w / b); se = lr.std(ddof=1) / np.sqrt(len(lr))
    return np.exp(lr.mean()), np.exp(lr.mean() - 1.96 * se), np.exp(lr.mean() + 1.96 * se)


for f in sorted(glob.glob(os.path.join(raw, "*.csv"))):
    if os.path.getsize(f) == 0: continue  # placeholder of a cell still running
    df = pd.read_csv(f)
    keys = {k: df[k].iloc[0] for k in ["dataset", "scenario", "n", "N", "rho"] if k in df}
    methods = sorted({c[:-4] for c in df if c.endswith("_cov")})
    # OLS: group per coordinate
    groups = {}
    for m in methods:
        if "_c" in m and m.rsplit("_c", 1)[1].isdigit():
            groups.setdefault(m.rsplit("_c", 1)[1], []).append(m)
        else:
            groups.setdefault("", []).append(m)
    for coord, ms in groups.items():
        base = (base_default + ("_lib" if coord else "") + (f"_c{coord}" if coord else ""))
        base = f"ppi++_lib_c{coord}" if coord else base_default
        for m in ms:
            cov = df[m + "_cov"]; w = df[m + "_w"]
            r = {**keys, "coord": coord, "method": m if not coord else m.rsplit("_c", 1)[0], "reps": len(df),
                 "coverage": cov.mean(), "cov_se": np.sqrt(cov.mean() * (1 - cov.mean()) / len(df)), "width": w.mean()}
            r["cov_lo"], r["cov_hi"] = wilson(cov.mean(), len(df))
            if base + "_w" in df:
                r["ratio"], r["ratio_lo"], r["ratio_hi"] = pratio(w, df[base + "_w"])
            if not coord:
                suf = "_t" if m.endswith("_t") else "_boot" if m.endswith("_boot") else ""
                lb = "ppi++" + suf
                if lb + "_w" in df:
                    r["baseline_lfl"] = lb
                    r["ratio_lfl"], r["ratio_lfl_lo"], r["ratio_lfl_hi"] = pratio(w, df[lb + "_w"])
            rows.append(r)
if not rows:
    print("no finished cells in", raw); sys.exit(0)
res = pd.DataFrame(rows)
if os.environ.get("WIDTH_ONLY"):  # truth not defined (e.g. ballots width-only protocol): coverage columns are not reported
    res[["coverage", "cov_se", "cov_lo", "cov_hi"]] = np.nan
res.to_csv(out, index=False)
print(len(rows), "rows ->", out)
