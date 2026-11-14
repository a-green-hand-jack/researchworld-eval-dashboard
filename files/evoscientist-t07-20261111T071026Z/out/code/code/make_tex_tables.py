"""Turn results/tables/*.csv|tex into complete LaTeX tabular environments used by the paper (paper/tables/*.tex).

(Whole tabulars are written because \\input of bare row fragments inside a tabular failed to compile.)"""
import os
import numpy as np, pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAB = os.path.join(ROOT, "results", "tables"); OUT = os.path.join(ROOT, "paper", "tables")
os.makedirs(OUT, exist_ok=True)
SPL = [("interp", "Random split"), ("org", "Held-out developers"), ("extrap", "Top-30\\% held out")]
NAME = {"uniform": "Uniform", "strat": "Stratified", "pps_resid": "Neyman-PPS"}


def tabular(colspec, header, body, path):
    txt = "\\begin{tabular}{" + colspec + "}\n\\toprule\n" + "\n".join(header) + "\n\\midrule\n" + "\n".join(body) + "\n\\bottomrule\n\\end{tabular}\n"
    open(path, "w").write(txt)


def rows_of(path):
    return [l.rstrip("\n") for l in open(path) if l.strip()]


# ---- Table 1 (several budgets) ---------------------------------------------------------------------------------------
for n in (10, 25, 50, 100):
    hdr = [r" & \multicolumn{2}{c}{Random model split} & \multicolumn{2}{c}{Held-out developers} & \multicolumn{2}{c}{Top-30\% models held out}\\",
           r"\cmidrule(lr){2-3}\cmidrule(lr){4-5}\cmidrule(lr){6-7}",
           r"Method & MAE ratio [95\% CI] & $\rho$ & MAE ratio [95\% CI] & $\rho$ & MAE ratio [95\% CI] & $\rho$ \\"]
    tabular("l cc cc cc", hdr, rows_of(os.path.join(TAB, f"table1_n{n}.tex")), os.path.join(OUT, f"table1_n{n}_tab.tex"))

# ---- Table 2: design x predictor x (in-sample | cross-fit), MAE ratio vs random, n=50 -------------------------
body = []
for s, lab in SPL:
    g = pd.read_csv(os.path.join(TAB, f"grid_{s}_n50.csv"), index_col=0)
    for d in ("uniform", "strat", "pps_resid"):
        cells = [f"{g.loc[f'{d}+{p}_{m}', 'mae']:.3f}" for p in ("ridge", "lat", "knn") for m in ("is", "cf")]
        body.append((f"\\multirow{{3}}{{*}}{{{lab}}}" if d == "uniform" else "") + f" & {NAME[d]} & " + " & ".join(cells) + r" \\")
    body.append(r"\midrule")
hdr = [r" & & \multicolumn{2}{c}{ridge predictor} & \multicolumn{2}{c}{latent (IRT) predictor} & \multicolumn{2}{c}{kNN predictor}\\",
       r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}", r"Regime & Design & is & cf & is & cf & is & cf\\"]
tabular("ll cc cc cc", hdr, body[:-1], os.path.join(OUT, "grid_tab.tex"))

# ---- ablation ------------------------------------------------------------------------------------------------
a = pd.read_csv(os.path.join(TAB, "ablation_seeds0-9_n50.csv"))
lab = {"random": "Random sampling", "uniform+lat_cf": "Uniform, $k{=}2$", "pps_resid+lat_cf": "Neyman-PPS $\\gamma{=}0.3$, $k{=}2$ (default)",
       "pps_resid_g0.0+lat_cf": "Neyman-PPS $\\gamma{=}0$", "pps_resid_g0.6+lat_cf": "Neyman-PPS $\\gamma{=}0.6$",
       "pps_resid_g1.0+lat_cf": "$\\gamma{=}1$ (uniform probabilities, systematic draw)",
       "uniform+lat_cf_k1": "Uniform, $k{=}1$", "pps_resid+lat_cf_k1": "Neyman-PPS, $k{=}1$",
       "uniform+lat_cf_k4": "Uniform, $k{=}4$", "pps_resid+lat_cf_k4": "Neyman-PPS, $k{=}4$",
       "uniform+lat_cf_k8": "Uniform, $k{=}8$", "pps_resid+lat_cf_k8": "Neyman-PPS, $k{=}8$"}
body = []
for m in lab:
    cells = []
    for s, _ in SPL:
        r = a[(a.split == s) & (a.method == m)]
        if len(r) == 0: cells.append("--"); continue
        r = r.iloc[0]; cells.append(f"{r.mae_ratio:.2f} {{\\scriptsize[{r.lo:.2f},{r.hi:.2f}]}}")
    body.append(lab[m] + " & " + " & ".join(cells) + r" \\")
tabular("l ccc", [r"Variant & Random split & Held-out developers & Top-30\% held out\\"], body, os.path.join(OUT, "ablation_tab.tex"))

# ---- significance --------------------------------------------------------------------------------------------
sg = pd.read_csv(os.path.join(TAB, "significance.csv"))
def esc(x): return x.replace("_", r"\_")
body = []
for s, lab_ in SPL:
    for _, r in sg[(sg.split == s) & (sg.n == 50)].iterrows():
        body.append(f"{s} & \\texttt{{{esc(r.a)}}} vs \\texttt{{{esc(r.b)}}} & {r.geo_ratio:.3f} & {r.wins}/{r.n_ds} & {r.p:.4f} & {r.p_holm:.4f} \\\\")
    body.append(r"\midrule")
tabular("llcccc", [r"Regime & Pair & ratio & wins & $p$ & Holm $p$\\"], body[:-1], os.path.join(OUT, "signif_tab.tex"))

# ---- dataset stats ---------------------------------------------------------------------------------------------
d = pd.read_csv(os.path.join(TAB, "dataset_stats.csv"))
body = []
for _, r in d.iterrows():
    body.append(f"{r.dataset.replace('_', chr(92) + '_')} & {r.family} & {r.models} & {r['items']} & {r.mean_acc:.3f} & {r.sd_model_acc:.3f} & "
                f"{r.min_acc:.2f}--{r.max_acc:.2f} & {r.frac_items_constant:.3f} & {r.frac_dup_model_rows:.3f} \\\\")
tabular("llrrrrrrr", ["Dataset & Family & Models & Items & Mean acc. & sd & Range & const. & dup.\\\\"], body, os.path.join(OUT, "data_tab.tex"))

# ---- per-dataset MAE ratio (n=50) ------------------------------------------------------------------------------
cols = ["strat_mean", "rs_learn", "aipw_ref", "anchor_w", "pirt_k2", "strat+ridge_cf", "pps_resid+lat_cf", "guard_strat"]
body = []
for s, lab_ in SPL:
    p = pd.read_csv(os.path.join(TAB, f"perdataset_ratio_{s}_n50.csv"), index_col=0)
    body.append(f"\\multicolumn{{9}}{{l}}{{\\emph{{{lab_}}}}}\\\\")
    for ds, r in p.iterrows():
        body.append(ds.replace("_", r"\_") + " & " + " & ".join(f"{r[c]:.2f}" for c in cols) + r" \\")
    body.append(r"\midrule")
tabular("l cccccccc", ["Benchmark & Strat & RS-L & AIPW & Anch & pIRT & S+rDR & N-DR & Guard\\\\"], body[:-1], os.path.join(OUT, "perdataset_tab.tex"))

# ---- appendix: all budgets per regime ---------------------------------------------------------------------------
for s, _ in SPL:
    body = []
    for n in (10, 25, 50, 100):
        body.append(f"\\multicolumn{{5}}{{l}}{{\\emph{{$n={n}$}}}}\\\\")
        body += rows_of(os.path.join(TAB, f"key_{s}_n{n}.tex"))
        body.append(r"\midrule")
    tabular("l cccc", [r"Method & MAE ratio & RMSE ratio & Spearman & Kendall\\"], body[:-1], os.path.join(OUT, f"key_{s}_tab.tex"))
print("tex tables written")
