"""LaTeX tables for the paper (written to /work/paper/tables).

Numbers are read from the results written by run_real.py / run_synth.py / theory_pool.py /
theory_check.py; nothing is typed in by hand.  Booktabs style.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import pandas as pd

from summarize import summarize

OUT = "/work/paper/tables"
os.makedirs(OUT, exist_ok=True)

CONFIGS = [("galaxies", "f"), ("forest", "f"), ("gene_expression", "f"), ("alphafold", "f"),
           ("alphafold", "fX"), ("census_income", "f"), ("census_income", "fX"),
           ("census_healthcare", "f"), ("census_healthcare", "fX"),
           ("census_education", "f"), ("census_education", "fX")]
NICE = {"galaxies": "galaxies", "forest": "forest", "gene_expression": "gene expr.",
        "alphafold": "alphafold", "census_income": "census income",
        "census_healthcare": "census health", "census_education": "census educ."}


def bound_ratio(t):
    """Efficient-bound width ratio vs PPI++: sqrt(1 - (1-a) Delta / (E(Y-L)^2 + a Var(L)))."""
    a = t["a"]
    return np.sqrt(1 - (1 - a) * t["Delta"] / (t["E_res_L"] + a * t["Var_L"]))


def fmt(x, d=3):
    return "--" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:.{d}f}"


def tabular(header, rows, colfmt):
    lines = [f"\\begin{{tabular}}{{{colfmt}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    for r in rows:
        lines.append(" & ".join(r) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    return "\n".join(lines) + "\n"


def real_tables():
    raw = pd.read_csv("/work/results/real_main.csv")
    th = pd.read_csv("/work/results/theory_pool.csv")
    # per-config summary over all (n, N/n) cells
    keys = ["dataset", "regime", "n", "ratio"]
    s = summarize(raw, keys)
    rows_main, rows_sens = [], []
    for ds, rg in CONFIGS:
        sub = s[(s.dataset == ds) & (s.regime == rg)]
        base_m = "ppi_linear_X" if rg == "fX" else "ppi_pp"
        cf = "cf_spline_X" if rg == "fX" else "cf_spline"
        cells = sub[sub.method == cf]
        base_cells = sub[sub.method == base_m]
        t = th[(th.dataset == ds) & (th.regime == rg) & (th.ratio == 4)].iloc[0]
        wr = {}
        for n in [50, 200, 1000]:
            r = sub[(sub.method == cf) & (sub.n == n) & (sub.ratio == 4)]
            wr[n] = r.width_ratio_vs_ppi_pp.values[0]
        bound = bound_ratio(t)
        cov_cf = cells.coverage
        cov_base = base_cells.coverage
        rows_main.append([NICE[ds], rg if rg == "f" else "f+X",
                          fmt(bound),
                          fmt(wr[50]), fmt(wr[200]), fmt(wr[1000]),
                          f"{cov_cf.min():.3f}--{cov_cf.max():.3f}",
                          f"{cov_base.min():.3f}--{cov_base.max():.3f}"])
        # sensitivity at n=200, N/n=4
        r = sub[(sub.n == 200) & (sub.ratio == 4)]
        row = [NICE[ds], rg if rg == "f" else "f+X"]
        for m in (["cf_spline", "cf_hgb", "cf_linear", "sppi", "ppi", "classical"] if rg == "f" else
                  ["cf_spline_X", "cf_hgb_X", "cf_linear_X", "sppi", "ppi", "classical"]):
            v = r[r.method == m].width_ratio_vs_ppi_pp
            row.append(fmt(v.values[0]) if len(v) else "--")
        rows_sens.append(row)
    hdr = ["Pool", "Info", "Bound", "$n{=}50$", "$n{=}200$", "$n{=}1000$",
           "CF cov.\\ range", "Baseline cov.\\ range"]
    tab1 = tabular(hdr, rows_main, "llcccccc")
    open(f"{OUT}/tab_real_main.tex", "w").write(tab1)
    hdr2 = ["Pool", "Info", "CF spline", "CF boosting", "CF linear", "Strat. PPI", "PPI", "Classical"]
    tab2 = tabular(hdr2, rows_sens, "llcccccc")
    open(f"{OUT}/tab_real_sensitivity.tex", "w").write(tab2)

    # pool constants
    rows = []
    for ds, rg in CONFIGS:
        t = th[(th.dataset == ds) & (th.regime == rg)]
        t4 = t[t.ratio == 4].iloc[0]
        kappa = t4.Delta / t4.E_res_L
        rows.append([NICE[ds], rg if rg == "f" else "f+X", f"{int(t4.M)}",
                     fmt(t4.R2_linear), fmt(t4.R2_nonlinear), fmt(kappa, 3),
                     fmt(bound_ratio(t[t.ratio == 1].iloc[0])),
                     fmt(bound_ratio(t[t.ratio == 4].iloc[0])),
                     fmt(bound_ratio(t[t.ratio == 16].iloc[0]))])
    hdr3 = ["Pool", "Info", "$M$", "$R^2_{\\rm lin}$", "$R^2_{\\rm nl}$", "$\\kappa$",
            "$a{=}\\tfrac12$", "$a{=}\\tfrac15$", "$a{=}\\tfrac1{17}$"]
    tab3 = tabular(hdr3, rows, "llrrrrrrr")
    open(f"{OUT}/tab_pool_constants.tex", "w").write(tab3)
    print("real tables written")


def synth_tables():
    s = pd.read_csv("/work/results/synth_main_summary.csv")
    th = pd.read_csv("/work/results/theory_check.csv")
    scen = [("lin", "linear calibrator"), ("nl", "nonlinear calibration"), ("bin", "binary outcome"),
            ("xonly", "covariate beyond $f$"), ("heavy", "heavy-tailed noise")]
    rows = []
    for sc, lab in scen:
        for n in [50, 200, 1000]:
            r = s[(s.scenario == sc) & (s.n == n) & (s.ratio == 4)]
            g = lambda m: r[r.method == m]
            cf = g("cf_spline_X") if sc == "xonly" else g("cf_spline")
            info = "X" if sc == "xonly" else "f"
            b = th[(th.scenario == sc) & (th["info"] == info) & (th.method == "oracle_s0.0") & (th.n == n) & (th.ratio == 4)]
            rows.append([lab if n == 50 else "", f"{n}",
                         fmt(cf.width_ratio_vs_ppi_pp.values[0]),
                         f"{cf.coverage.values[0]:.3f}",
                         fmt(g("cf_hgb").width_ratio_vs_ppi_pp.values[0] if sc != "xonly" else
                             g("cf_hgb_X").width_ratio_vs_ppi_pp.values[0]),
                         fmt(g("sppi").width_ratio_vs_ppi_pp.values[0]),
                         fmt(g("ppi").width_ratio_vs_ppi_pp.values[0]),
                         fmt(b.width_ratio_pred.values[0]) if len(b) else "--",
                         f"{g('ppi_pp').coverage.values[0]:.3f}"])
    hdr = ["Scenario", "$n$", "CF spline", "CF cov.", "CF boosting", "Strat. PPI", "PPI",
           "Bound", "PPI++ cov."]
    open(f"{OUT}/tab_synth_main.tex", "w").write(tabular(hdr, rows, "llccccccc"))

    rows = []
    for sc, lab in scen:
        for info in (["f", "X"] if sc == "xonly" else ["f"]):
            t = th[(th.scenario == sc) & (th["info"] == info)]
            if len(t) == 0:
                continue
            r = t.iloc[0]
            for s_val in ["oracle_s0.0", "oracle_s0.2"]:
                tt = t[(t.method == s_val) & (t.n == 200) & (t.ratio == 4)]
                var_d = float(s_val.replace("oracle_s", "")) ** 2
                rows.append([lab if info == "f" else "", info, f"$\\mathrm{{Var}}(\\delta){{=}}{var_d:.2f}$",
                             fmt(r.Delta_f, 3) if info == "f" else "--",
                             fmt(tt.emp_sd.values[0], 4), fmt(tt.pred_sd.values[0], 4),
                             fmt(tt.width_ratio_emp.values[0]), fmt(tt.width_ratio_pred.values[0]),
                             f"{tt.emp_cov.values[0]:.3f}"])
    hdr = ["Scenario", "Info", "Calibrator error", "$\\Delta_L$", "MC sd", "Pred.\\ sd", "MC ratio",
           "Pred.\\ ratio", "Coverage"]
    open(f"{OUT}/tab_theory_check.tex", "w").write(tabular(hdr, rows, "lllrrrrrr"))
    print("synthetic tables written")


if __name__ == "__main__":
    which = sys.argv[1:] or ["real", "synth"]
    if "real" in which: real_tables()
    if "synth" in which: synth_tables()
