"""LaTeX tables (booktabs tabular fragments, `\\input` them) from the aggregated results.
  tab1_grids.tex      experiment grids: what was varied, number of cells, worlds x assignments (read from netgate.experiments)
  tab2_estimators.tex estimator comparison, SBM, Bernoulli(0.5), gamma=2, linear and concave spillover (e2): bias (MC SE), SD, RMSE
  tab3_graphs.tex     OLS (z,f), correctly specified OLS and difference in means on every graph, concave spillover (e2)
  tab4_theory.tex     closed-form vs simulated noiseless bias summary per graph and shape (e9)
  tab5_scaling.tex    log-log fit of the SD of the estimate on n and d (e3, ER, Bernoulli(0.5))
Numbers in parentheses are Monte-Carlo standard errors (see common.py)."""
import glob
import importlib
import sys
import numpy as np
from common import *


def pm(v, se, nd=3):
    if pd.isna(v):
        return "--"
    return f"{v:.{nd}f}" + ("" if pd.isna(se) else f" ({se:.{nd}f})")


def write(name, tex):
    import re
    tex = re.sub(r"(?<![\d.])-(0\.0+)(?![\d])", r"\1", tex)  # no "-0.00"
    with open(os.path.join(OUT, name + ".tex"), "w") as f:
        f.write(tex)
    print("wrote", name)


def tab(header, rows, colspec, extra=""):
    out = [f"\\begin{{tabular}}{{{colspec}}}", "\\toprule", " & ".join(header) + " \\\\", "\\midrule"]
    for r in rows:
        out.append(r if r.startswith("\\") else r + " \\\\")
    out += ["\\bottomrule", "\\end{tabular}", ""]
    return "\n".join(out)


def tab1():
    for cand in [os.environ.get("NETGATE_SRC", ""), os.path.join(ROOT, "code", "src"), os.path.join(ROOT, "..", "experiment-repo", "src"),
                 "/hutian/experiment-repo/src"]:
        if cand and os.path.isdir(os.path.join(cand, "netgate")):
            sys.path.insert(0, cand); break
    from netgate.experiments import EXPERIMENTS
    rows = []
    desc = {"e1": "interference strength $\\gamma$", "e2": "spillover shape $\\times$ design", "e3": "$n$ $\\times$ mean degree",
            "e4": "$p$, cluster resolution/quality", "e5": "noise $\\sigma$, baseline smoothness", "e6": "variance estimators / coverage",
            "e7": "other interference mechanisms", "e8": "noiseless bias, shapes $\\times$ designs", "e9": "noiseless bias, curvature $\\times$ $p$",
            "e10": "bias vs $n$", "e11": "$\\gamma$ with non-linear truth$^\\dagger$", "e12": "Hájek baselines, low degree$^\\dagger$",
            "e13": "second seed of H2/H4/H5 cells$^\\dagger$",
            "e14": "degree distribution at matched mean degree$^\\dagger$", "e15": "interval type, GATE vs $E[\\hat\\tau]$ coverage$^\\dagger$",
            "e16": "estimator scope (ridge, lasso, GBM, $zf$)$^\\dagger$", "e17": "crossover: $n$ $\\times$ $d$ $\\times$ $\\sigma$ $\\times$ $\\gamma$$^\\dagger$",
            "e18": "20 worlds per cell$^\\dagger$", "e19": "cluster-design Hájek baselines$^\\dagger$", "e20": "factorial for variance decomposition$^\\dagger$",
            "e21": "components of the baseline variance$^\\dagger$"}
    for e, f in EXPERIMENTS.items():
        if not os.path.exists(os.path.join(RES, f"{e}.csv")):
            continue  # a grid is listed only once its summary exists
        cells = f()
        gr = sorted({c["graph"].split(":")[0] for c in cells})
        gr = ["stanford3" if g == "stanford3" else g for g in gr]
        des = sorted({c["design"].split(":")[0] for c in cells})
        w, r = cells[0]["worlds"], cells[0]["reps"]
        rows.append(" & ".join([e, desc[e], ", ".join(gr), ", ".join(des), str(len(cells)), f"{w}$\\times${r}"]))
    return tab(["exp.", "factor varied", "graphs", "designs", "cells", "worlds$\\times$assign."], rows, "llllrr")


def tab2():
    d = load("e2"); d = d[(d.gname == "SBM") & (d.design == "bern:0.5")]
    EST = ["DM", "HajekKappa", "OLS_f", "OLS_cnt", "OLS_fd", "OLS_quad", "OLS_cubic", "OLS_big", "GBM", "ORACLE_D"]
    rows = []
    for e in EST:
        cells = [e.replace("_", "\\_") if False else ELAB[e].replace("$", "$")]
        for k in ["linear", "concave"]:
            s = d[(d.est_name == e) & (d.o_kind == k)]
            if s.empty or s.n_rep.iloc[0] < 5:
                cells += ["--"] * 3; continue
            s = s.iloc[0]
            cells += [pm(s.bias, s.bias_se), f"{s.sd:.3f}", f"{s.rmse:.3f}"]
        rows.append(" & ".join(cells))
    head = ("\\begin{tabular}{lrrrrrr}\n\\toprule\n & \\multicolumn{3}{c}{linear spillover} & \\multicolumn{3}{c}{concave spillover} \\\\\n"
            "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\n estimator & bias (MC SE) & SD & RMSE & bias (MC SE) & SD & RMSE \\\\\n\\midrule\n")
    return head + "\n".join(r + " \\\\" for r in rows) + "\n\\bottomrule\n\\end{tabular}\n"


def tab3():
    d = load("e2"); d = d[(d.design == "bern:0.5") & (d.o_kind == "concave")]
    rows = []
    for g in present(GORDER, d.gname):
        for e in ["DM", "OLS_f", "ORACLE_D"]:
            s = d[(d.gname == g) & (d.est_name == e)]
            if s.empty:
                continue
            s = s.iloc[0]
            rows.append(" & ".join([g if e == "DM" else "", ELAB[e], f"{s.n:.0f}", f"{s.mean_deg:.1f}", pm(s.bias, s.bias_se), f"{s.sd:.3f}", f"{s.rmse:.3f}"]))
        rows.append("\\addlinespace")
    rows = rows[:-1]
    return tab(["graph", "estimator", "$n$", "mean $d$", "bias (MC SE)", "SD", "RMSE"], rows, "llrrrrr")


def tab4():
    T = pd.read_csv(os.path.join(RES, "theory_vs_sim_e9.csv"))
    T["gname"] = T.graph.map(lambda s: GNAME.get(s, s))
    rows = []
    for (g, k), s in T.groupby(["gname", "o_kind"], sort=False):
        rows.append(" & ".join([g, k, str(len(s)), f"{s.bias.abs().max():.2f}", f"{np.corrcoef(s.bias, s.pred_exact)[0, 1]:.4f}",
                                f"{(s.bias - s.pred_exact).abs().mean():.4f}", f"{(s.bias - s.pred_exact).abs().max():.3f}",
                                f"{((s.bias - s.pred_exact).abs() <= 1.96 * s.bias_se).mean():.2f}"]))
    return tab(["graph", "shape", "cells", "max $|$bias$|$", "corr.", "mean $|$dev$|$", "max $|$dev$|$", "dev within 1.96 SE"], rows, "llrrrrrr")


def tab5():
    e3 = load("e3"); e3 = e3[e3.tag == "er"]
    rows = []
    for e in ["ORACLE", "OLS_f", "OLS_fd", "OLS_zf", "OLS_big"]:
        s = e3[e3.est_name == e]
        if len(s) < 6:
            continue
        X = np.column_stack([np.ones(len(s)), np.log(s.n_nom), np.log(s.d_nom)]); y = np.log(s.sd.values)
        b, res, *_ = np.linalg.lstsq(X, y, rcond=None)
        r = y - X @ b; s2 = r @ r / (len(y) - 3); cov = s2 * np.linalg.inv(X.T @ X); se = np.sqrt(np.diag(cov))
        rows.append(" & ".join([ELAB[e], str(len(s)), f"{b[1]:.3f} ({se[1]:.3f})", f"{b[2]:.3f} ({se[2]:.3f})", f"{np.sqrt(s2):.3f}"]))
    rows.append("reference $\\sqrt{d/n}$ & & $-0.500$ & $0.500$ & ")
    return tab(["estimator", "cells", "exponent of $n$ (SE)", "exponent of $d$ (SE)", "residual SD of $\\log$ SD"], rows, "lrrrr")


TAB = os.path.join(RES, "..", "tables")


def rd(name):
    return pd.read_csv(os.path.join(TAB, name + ".csv"))


def tabx(header, rows, colspec):
    """Like tab() with a ready-made header block (lines ending in \\\\ or \\cmidrule)."""
    return "\n".join([f"\\begin{{tabular}}{{{colspec}}}", "\\toprule"] + header + ["\\midrule"] + [r if r.startswith("\\") else r + " \\\\" for r in rows]
                     + ["\\bottomrule", "\\end{tabular}", ""])


def tab6():
    """Coverage of the GATE and of E[tau-hat] by interval type (t19b, grid e15), Bernoulli(0.5) and Louvain-cluster designs."""
    d = rd("t19b_coverage_by_se_type"); d = d[d.exp == "e15"]
    assert (d.n_cells == 12).all() and (d.graphs == 6).all()
    names = [("HC0", "HC0"), ("cluster", "cluster-robust"), ("HAC1", "HAC-1"), ("HAC2", "HAC-2"), ("boot_sd", "block bootstrap, SD"), ("boot_pct", "block bootstrap, percentile")]
    ds = ["Bernoulli(0.5)", "Louvain clusters"]
    hdr = ["interval & covers & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{b}}}" for b in ds) + " \\\\", "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}",
           " & & mean [95\\% CI over cells] & min--max & mean [95\\% CI over cells] & min--max \\\\"]
    rows = []
    for k, lab in names:
        for q, ql in [("cov_gate", "GATE"), ("cov_exp", "$E[\\hat\\tau]$")]:
            cells = []
            for dk in ds:
                r = d[(d.interval == k) & (d.design == dk) & (d.quantity == q)].iloc[0]
                cells += [f"{r.mean_coverage:.2f} [{r.boot_lo:.2f}, {r.boot_hi:.2f}]", f"{r['min']:.2f}--{r['max']:.2f}"]
            rows.append(" & ".join([lab if q == "cov_gate" else "", ql] + cells))
        rows.append("\\addlinespace")
    return tabx(hdr, rows[:-1], "llcccc")


def tab7():
    """Variance law with the harmonic-mean degree: default outcome (t17) and noise-only outcome (t17c, e21, gamma = 0)."""
    a = rd("t17_variance_law").set_index("graph"); b = rd("t17c_variance_law_components"); b = b[b.variant == "noise_only"].set_index("graph")
    hdr = [" & & & \\multicolumn{5}{c}{(i) default outcome (e1, pooled $\\gamma$)} & \\multicolumn{5}{c}{(ii) independent errors only (e21)} \\\\",
           "\\cmidrule(lr){4-8}\\cmidrule(lr){9-13}",
           "graph & $d$ & $d_h$ & obs. & $\\hat s_{d_h}$ & $\\hat s_{d}$ & $r_{d_h}$ & $r_{d}$ & obs. & $\\hat s_{d_h}$ & $\\hat s_{d}$ & $r_{d_h}$ & $r_{d}$ \\\\"]
    rows = []
    for g in ["sbm:5000,50,20,0.8", "er:5000,20", "ws:5000,20,0.1", "ba:5000,10", "stanford3", "ego"]:
        x, y = a.loc[g], b.loc[g]
        rows.append(" & ".join([GNAME[g], f"{x.mean_deg:.1f}", f"{x.d_harm:.1f}",
                                f"{x.sd_obs_pooled_gammas:.3f}", f"{x.sd_pred_dh:.3f}", f"{x.sd_pred_d:.3f}", f"{x.ratio_obs_over_pred_dh:.2f}", f"{x.ratio_obs_over_pred_d:.2f}",
                                f"{y.sd_obs:.3f}", f"{y.sd_pred_dh:.3f}", f"{y.sd_pred_d:.3f}", f"{y.ratio_dh:.2f}", f"{y.ratio_d:.2f}"]))
    e3 = rd("t17b_variance_law_e3")
    rows.append("\\addlinespace")
    m = lambda c: f"{e3[c].median():.2f}"; r_ = lambda c: f"{e3[c].min():.2f}--{e3[c].max():.2f}"
    rows.append(f"\\multicolumn{{3}}{{l}}{{e3 sweeps ({len(e3)}): median}} & & & & {m('ratio_dh')} & {m('ratio_d')} & & & & \\\\")
    rows.append(f"\\multicolumn{{3}}{{l}}{{\\hspace{{2.2em}}min--max}} & & & & {r_('ratio_dh')} & {r_('ratio_d')} & & & & \\\\")
    return tabx(hdr, rows, "lrr" + "rrrrr" * 2)


def tab8():
    """Matched heavy-tail test (t23, grid e14): OLS_f only, n = 5000, mean degree ~ 20; linear and concave truth."""
    d = rd("t23_heavy_tail"); d = d[d.est_name == "OLS_f"]
    L = {"reg": "20-regular", "er": "ER", "pl3.0": "power law 3.0", "pl2.5": "power law 2.5", "pl2.2": "power law 2.2", "cmba": "BA config. model", "ba": "BA(10)"}
    hdr = [" & & & \\multicolumn{2}{c}{$\\gamma=0$} & \\multicolumn{3}{c}{$\\gamma=2$} \\\\", "\\cmidrule(lr){4-5}\\cmidrule(lr){6-8}",
           "graph & truth & $d_h$ & SD & SD/pred. & bias (MC SE) & SD & RMSE \\\\"]
    rows = []
    for g in L:
        for k in ["linear", "concave"]:
            a = d[(d.graph == g) & (d.kind == k) & (d.gamma == 0)].iloc[0]; b = d[(d.graph == g) & (d.kind == k) & (d.gamma == 2)].iloc[0]
            rows.append(" & ".join([L[g] if k == "linear" else "", k, f"{(a.d_harm + b.d_harm) / 2:.1f}", f"{a.sd:.3f}", f"{a.sd_obs_over_pred_dh:.2f}", pm(b.bias, b.bias_se), f"{b.sd:.3f}", f"{b.rmse:.3f}"]))
        rows.append("\\addlinespace")
    return tabx(hdr, rows[:-1], "llrrrrrr")


def rt(x, sh):
    """Median RMSE ratio (two decimals below 10, one above) and the share of cells better than OLS_f without leading zero."""
    return (f"{x:.2f}" if x < 10 else f"{x:.1f}") + f"/{sh:.2f}".replace("/0.", "/.").replace("/1.00", "/1")


def tab9():
    """Estimator scope (t25, grid e16): median RMSE ratio to OLS_f (share of cells better than OLS_f), per truth and p."""
    d = rd("t25_estimator_scope")
    ests = [("OLS_zf", "OLS $z,f,zf$"), ("OLS_big", "OLS big (11)"), ("RIDGE_big", "ridge (11)"), ("LASSO_big", "lasso (11)"), ("GBM", "GBM, untuned"), ("GBM_tuned", "GBM, tuned")]
    truths = ["linear", "concave", "convex", "sigmoid"]
    hdr = ["estimator & " + " & ".join(f"\\multicolumn{{2}}{{c}}{{{t}}}" for t in truths) + " & all cells \\\\",
           "\\cmidrule(lr){2-3}\\cmidrule(lr){4-5}\\cmidrule(lr){6-7}\\cmidrule(lr){8-9}",
           " & " + " & ".join(["$p$=0.1 & $p$=0.5"] * 4) + " & \\\\"]
    rows = []
    for k, lab in ests:
        cells = []
        for t in truths:
            for p in ["0.1", "0.5"]:
                r = d[(d.est_name == k) & (d.truth == t) & (d.p.astype(str) == p)]
                cells.append("--" if r.empty else rt(r.median_rmse_ratio.iloc[0], r.share_better_than_OLS_f.iloc[0]))
        r = d[(d.est_name == k) & (d.truth == "all")].iloc[0]
        rows.append(" & ".join([lab] + cells + [rt(r.median_rmse_ratio, r.share_better_than_OLS_f) + f", {r.n_cells:.0f}"]))
    return tabx(hdr, rows, "lrrrrrrrrr")


def tab10():
    """Exposure variation by design (t18; SD of OLS_f from e4): Louvain, size-matched random clusters and Bernoulli(0.5)."""
    d = rd("t18_exposure_variation")
    hdr = [" & & & \\multicolumn{4}{c}{Louvain clusters} & \\multicolumn{3}{c}{random clusters} \\\\", "\\cmidrule(lr){4-7}\\cmidrule(lr){8-10}",
           "graph & res. & clusters & Var($f$) & Var($f\\mid z$) & corr($z,f$) & SD OLS$_f$ & Var($f$) & corr($z,f$) & SD OLS$_f$ \\\\"]
    rows = []
    for g in ["sbm:5000,50,20,0.8", "stanford3", "ego"]:
        b = d[(d.graph == g) & (d.design == "bern")].iloc[0]
        rows.append(" & ".join([GNAME[g], "Bern.", f"{b.n_clusters:.0f}"] + ["--"] * 4 + [f"{b.var_f:.3f}", f"{b.corr_z_f:.2f}", f"{b.ols_f_sd_e4:.2f}"]))
        for res in sorted(d[(d.graph == g) & (d.design == "louv")].resolution):
            l = d[(d.graph == g) & (d.design == "louv") & (d.resolution == res)].iloc[0]; r = d[(d.graph == g) & (d.design == "rand") & (d.resolution == res)].iloc[0]
            rows.append(" & ".join(["", f"{res:g}", f"{l.n_clusters:.0f}", f"{l.var_f:.3f}", f"{l.var_f_within_arm:.3f}", f"{l.corr_z_f:.2f}", f"{l.ols_f_sd_e4:.2f}",
                                    f"{r.var_f:.3f}", f"{r.corr_z_f:.2f}", f"{r.ols_f_sd_e4:.2f}"]))
        rows.append("\\addlinespace")
    return tabx(hdr, rows[:-1], "llrrrrrrrr")


def tab11():
    """Few worlds (t20b, from the 20 worlds of e18) and variance components (t20, e2 with 4 worlds, e18 with 20)."""
    b = rd("t20b_worlds_needed"); v = rd("t20_variance_components")
    hdr = ["\\multicolumn{10}{l}{(a) subsets of $W$ of the 20 worlds of e18 (12 cells): median SE of the bias and coverage of the 20-world mean} \\\\",
           "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}",
           " & \\multicolumn{3}{c}{median SE} & \\multicolumn{3}{c}{coverage, $\\pm1.96$ SE} & \\multicolumn{3}{c}{coverage, $\\pm t$ SE} \\\\",
           "$W$ & rule & world & repl. & rule & world & repl. & rule & world & repl. \\\\"]
    rows = [" & ".join([f"{r.W:.0f}", f"{r.median_se_rule:.3f}", f"{r.median_se_world:.3f}", f"{r.median_se_rep:.3f}",
                        f"{r['cover_1.96_rule']:.2f}", f"{r['cover_1.96_world']:.2f}", f"{r['cover_1.96_rep']:.2f}",
                        f"{r.cover_t_rule:.2f}", f"{r.cover_t_world:.2f}", f"{r.cover_t_rep:.2f}"]) for _, r in b.iterrows()]
    rows += ["\\midrule", "\\multicolumn{10}{l}{(b) intraclass correlation of the error (between-world share of its variance), 12 cells per row} \\\\",
             "estimator & worlds & cells & med. ICC & max ICC & med. DE & & & &"]
    for e in ["DM", "OLS_f", "OLS_zf", "ORACLE_D"]:
        for w in [4, 20]:
            s = v[(v.est_name == e) & (v.n_worlds == w)]
            rows.append(" & ".join([ELAB[e] if w == 4 else "", f"{w}", f"{len(s)}", f"{s.icc.median():.3f}", f"{s.icc.max():.3f}", f"{s.design_effect.median():.2f}", "", "", "", ""]))
    return tabx(hdr, rows, "l" + "r" * 9)


if __name__ == "__main__":
    style()
    for n, f in [("tab1_grids", tab1), ("tab2_estimators", tab2), ("tab3_graphs", tab3), ("tab4_theory", tab4), ("tab5_scaling", tab5),
                 ("tab6_coverage_se_types", tab6), ("tab7_variance_law", tab7), ("tab8_heavy_tail", tab8), ("tab9_estimator_scope", tab9),
                 ("tab10_exposure_variation", tab10), ("tab11_worlds_icc", tab11)]:
        write(n, f())
