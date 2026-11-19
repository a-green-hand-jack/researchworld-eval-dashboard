"""LaTeX (booktabs) + CSV tables.

tab_methods        methods M1-M5 and the information each uses                      (T1)
tab_datasets       datasets, population moments and the predicted floor             (T2 context)
tab_real_cov       coverage at n = 100, 400 (N = 20n), Wilson CIs in the CSV         (T2)
tab_real_width     mean width of M3 and paired width ratios to M3 at n = 100, 400    (T2)
tab_regimes        where M4 is narrower / indistinguishable / wider than M3, and undercoverage counts (T3)
tab_native         intervals at native dataset sizes (one realisation, no coverage claim)
tab_synth_tail     heavy-tailed noise cells
tab_boot           bootstrap PPI++ ablation
tab_forest_wor     forest: draws with vs without replacement
Missing inputs are skipped with a message (so partial result directories still build).
"""
import os
import numpy as np
import pandas as pd
from common import *

M3 = "ppipp_pkg"
M5 = ["ppipp_jk", M4 + "_t"]
RATIO_M = ["classical", "ppi", M4] + M5


def write(df, name, column_format=None):
    df.to_csv(os.path.join(OUT_TAB, name + ".csv"), index=False)
    with open(os.path.join(OUT_TAB, name + ".tex"), "w") as f:
        f.write(df.to_latex(index=False, escape=False, column_format=column_format))


def g(v, d=4):
    """Number to d significant digits; large/small values as a x 10^k LaTeX string."""
    t = f"{v:.{d - 1}e}"
    m, e = t.split("e")
    e = int(e)
    if -3 <= e < 5:
        return f"{v:.{max(d - 1 - e, 0)}f}"
    return f"${float(m):.{d - 1}f}\\times10^{{{e}}}$"


def short(m):
    return {"classical": "M1", "ppi": "M2", M3: "M3", M4: "M4", "ppipp_jk": "M5 (M3)", M4 + "_t": "M5 (M4)"}.get(m, m)


def tab_methods():
    rows = [
        ("M1", "classical", "mean of $Y$ on the $n$ labeled", "labels only", "$z$"),
        ("M2", "PPI", "$\\bar f_{\\rm unl}+\\overline{(Y-f)}_{\\rm lab}$", "$(Y,f)$ labeled, $f$ unlabeled", "$z$"),
        ("M3", "PPI++ (\\texttt{ppi\\_py} 0.2.3, reference)", "power-tuned $\\hat\\lambda\\in[0,1]$", "same as M2", "$z$"),
        ("M4", f"{CAL_NAME[M4]}-calibrated PPI++",
         "PPI++ on a score $\\hat g(f)$ learned on the labels, 5-fold cross-fitted", "same as M2 (covariates not used)", "$z$"),
        ("M5", "small-$n$ corrections", "M3 with delete-one jackknife s.e.; M4 with $t_{n-1}$", "same as M2",
         "$t_{n-1}$"),
    ]
    write(pd.DataFrame(rows, columns=["", "Method", "Point estimate", "Information used", "Critical value"]), "tab_methods",
          column_format="llp{3.4cm}p{2.6cm}l")


def tab_datasets():
    th = load("theory_population.csv")
    pr = load("theory_predicted_ratios.csv")
    cal = M4.replace("cal_", "")
    rows = []
    for _, r in th.iterrows():
        d = r["dataset"]
        q = pr[(pr["dataset"] == d) & (pr["calibrator"] == cal) & (pr["N"] == 20 * pr["n"])]
        row = {"Dataset": DATASET_LABEL[d], "Pool size": f"{int(r['size']):,}".replace(",", "\\,"),
               "$\\mathrm{Var}(Y)$": g(r["sigma2"]), "$\\rho^2$": f"{r['rho2']:.3f}", "$R^2_{\\rm cal}$": f"{r['r2cal_' + cal]:.3f}"}
        for n in (100, 400):
            s = q[q["n"] == n]
            row[f"floor ratio, $n={n}$"] = f"{s['pred_ratio_M4_vs_M3'].iloc[0]:.3f}" if len(s) else "--"
        rows.append(row)
    write(pd.DataFrame(rows), "tab_datasets", column_format="lrrrrrr")


def pick(df, n, N_mult=20):
    return df[(df["n"] == n) & (df["N"] == N_mult * n)]


def tab_real(ns=(100, 400)):
    df = summary("real_primary")
    rows_c, rows_w = [], []
    for ds in [d for d in PRIMARY if d in set(df["dataset"])]:
        for n in ns:
            d = pick(df[df["dataset"] == ds], n)
            if d.empty:
                continue
            rc = {"Dataset": DATASET_LABEL[ds], "$n$": n, "$R$": int(d["R"].iloc[0])}
            rw = {"Dataset": DATASET_LABEL[ds], "$n$": n}
            for m in [M3, "classical", "ppi", M4] + M5:
                s = d[d["method"] == m]
                if s.empty:
                    continue
                s = s.iloc[0]
                v = f"{s['coverage']:.3f}"
                rc[short(m)] = f"\\textbf{{{v}}}" if s["cov_hi"] < 0.95 else v       # bold: Wilson upper bound < 0.95
                if m == M3:
                    rw["M3 mean width"] = g(s["width_mean"], 3)
                else:
                    rw[short(m) + " / M3"] = f"{s['ratio_geo']:.3f} $\\pm$ {(s['ratio_hi'] - s['ratio_lo']) / 2:.3f}"
            rows_c.append(rc); rows_w.append(rw)
    if rows_c:
        write(pd.DataFrame(rows_c), "tab_real_cov", column_format="lrr" + "r" * 6)
        write(pd.DataFrame(rows_w), "tab_real_width", column_format="lrr" + "r" * 5)
        # full-precision CSV (coverage with Wilson bounds, ratios with bootstrap CI)
        full = df[(df["N"] == 20 * df["n"]) & df["n"].isin(ns)][["dataset", "n", "N", "R", "method", "coverage", "cov_lo", "cov_hi",
                 "width_mean", "ratio_geo", "ratio_lo", "ratio_hi", "frac_shorter_M3", "frac_degenerate"]]
        full.to_csv(os.path.join(OUT_TAB, "tab_real_full.csv"), index=False)


def tab_regimes():
    """Per group of cells (N = 20n): paired width ratio M4/M3 below 1 / CI containing 1 / above 1, and coverage Wilson upper
    bound < 0.95 for M3 and M4."""
    parts = []
    r = summary("real_primary", "real_appendix")
    r = r[r["N"] == 20 * r["n"]]
    for ds in [d for d in ORDER if d in set(r["dataset"])]:
        parts.append((DATASET_LABEL[ds], r[r["dataset"] == ds]))
    try:
        s = summary("synth")
        s[["_", "kind", "kappa", "snr", "tail"]] = s["dataset"].str.split(":", expand=True)
        s["kappa"] = s["kappa"].astype(float)
        s = s[(s["tag"].isin(["kappa", "n"])) & (s["tail"] == "0") & (s["snr"] == "1.0")]
        parts.append(("synthetic, $\\kappa=0$", s[(s["kappa"] == 0)]))
        parts.append(("synthetic, tanh/quad, $\\kappa>0$", s[(s["kappa"] > 0) & s["kind"].isin(["tanh", "quad"])]))
        parts.append(("synthetic, binary, $\\kappa>0$", s[(s["kappa"] > 0) & (s["kind"] == "bin")]))
    except FileNotFoundError:
        print("summary_final_synth.csv missing; regimes table without synthetic rows")
    rows = []
    for name, d in parts:
        a = d[d["method"] == M4]
        b = d[d["method"] == M3]
        if a.empty:
            continue
        rows.append({"Cells": name, "\\#": len(a), "M4 narrower": int((a["ratio_hi"] < 1).sum()),
                     "indistinguishable": int(((a["ratio_lo"] <= 1) & (a["ratio_hi"] >= 1)).sum()),
                     "M4 wider": int((a["ratio_lo"] > 1).sum()),
                     "smallest ratio": f"{a['ratio_geo'].min():.3f}", "largest ratio": f"{a['ratio_geo'].max():.3f}",
                     "M3 undercovers": int((b["cov_hi"] < 0.95).sum()), "M4 undercovers": int((a["cov_hi"] < 0.95).sum())})
    write(pd.DataFrame(rows), "tab_regimes", column_format="lrrrrrrrr")


def tab_native():
    df = load("full_data_intervals.csv")
    df["Method"] = df["method"].map(lambda m: METHODS[m][0] if m in METHODS else m)
    df["Interval"] = [f"[{g(lo)}, {g(hi)}]" for lo, hi in zip(df["lo"], df["hi"])]
    df["Width"] = df["width"].map(g)
    df["Dataset"] = df["dataset"].map(DATASET_LABEL)
    out = df[["Dataset", "n", "N", "Method", "Interval", "Width", "covers"]].rename(columns={"covers": "Covers $\\theta$"})
    write(out, "tab_native", column_format="lrrllrl")


def tab_synth_tail():
    s = summary("synth")
    s[["_", "kind", "kappa", "snr", "tail"]] = s["dataset"].str.split(":", expand=True)
    t = s[(s["tag"] == "tail")]
    rows = []
    for (kind, kappa, tail), d in t.groupby(["kind", "kappa", "tail"]):
        row = {"$h$": kind, "$\\kappa$": kappa, "tail": "Student-$t_3$" if tail == "1" else "Gaussian"}
        for m in (M3, M4, "ppipp_jk"):
            a = d[d["method"] == m].iloc[0]
            v = f"{a['coverage']:.3f}"
            row[short(m) + " cov."] = f"\\textbf{{{v}}}" if a["cov_hi"] < 0.95 else v
        a = d[d["method"] == M4].iloc[0]
        row["M4 / M3"] = f"{a['ratio_geo']:.3f} [{a['ratio_lo']:.3f}, {a['ratio_hi']:.3f}]"
        rows.append(row)
    write(pd.DataFrame(rows), "tab_synth_tail", column_format="lllrrrl")


def tab_boot():
    df = pd.read_csv(os.path.join(EXP_DIR, "results", "sim_boot.csv"))
    rows = []
    for (ds, n, N), d in df.groupby(["dataset", "n", "N"]):
        ref = d[d["method"] == "ppipp_nc"]["width"].iloc[0]
        row = {"Dataset": DATASET_LABEL[ds], "$n$": n, "$N$": N}
        for m, lab in (("ppipp_nc", "PPI++"), ("ppipp_boot_pct", "boot. pct"), ("ppipp_boot_t", "boot. $t$")):
            a = d[d["method"] == m].iloc[0]
            lo, hi = wilson(int(round(a["coverage"] * a["R"])), int(a["R"]))
            v = f"{a['coverage']:.3f}"
            row[lab + " cov."] = f"\\textbf{{{v}}}" if hi < 0.95 else v
            if m != "ppipp_nc":
                row[lab + " width / PPI++"] = f"{a['width'] / ref:.3f}"
        rows.append(row)
    write(pd.DataFrame(rows), "tab_boot", column_format="lrr" + "r" * 5)


def tab_forest_wor():
    a = summary("real_primary"); a = a[(a["dataset"] == "forest") & (a["N"] == 20 * a["n"])]
    b = summary("forest_wor")
    rows = []
    for n in sorted(set(a["n"]) & set(b["n"])):
        row = {"$n$": n}
        for lab, d in (("with repl.", a), ("without repl.", b)):
            d = d[d["n"] == n]
            for m in (M3, M4):
                s = d[d["method"] == m].iloc[0]
                v = f"{s['coverage']:.3f}"
                row[f"{short(m)} cov., {lab}"] = f"\\textbf{{{v}}}" if s["cov_hi"] < 0.95 else v
            s = d[d["method"] == M4].iloc[0]
            row[f"M4 / M3, {lab}"] = f"{s['ratio_geo']:.3f}"
        rows.append(row)
    write(pd.DataFrame(rows), "tab_forest_wor", column_format="r" * 7)


if __name__ == "__main__":
    for f in (tab_methods, tab_datasets, tab_real, tab_regimes, tab_native, tab_synth_tail, tab_boot, tab_forest_wor):
        try:
            f()
        except FileNotFoundError as e:
            print(f"{f.__name__}: skipped ({e})")
