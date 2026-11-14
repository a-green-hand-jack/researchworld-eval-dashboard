"""Generate LaTeX table fragments (paper/tables/*.tex) and a JSON of headline numbers from results/ CSVs."""
import os, json
import numpy as np, pandas as pd
from data import RESULTS

TAB = os.path.join(RESULTS, "tables")
OUT = os.path.abspath(os.path.join(RESULTS, "..", "paper", "tables"))
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(99)
NUM = {}
DSN = {"pima": "Pima", "gmsc": "GMSC", "acsincome": "ACSIncome", "german": "German"}


def w(name, s):
    open(os.path.join(OUT, name), "w").write(s)


def f2(x):
    return "--" if pd.isna(x) else f"{x:.2f}"


# ---------------- pooled pass rates
P = pd.read_csv(os.path.join(TAB, "tabI_pooled.csv"))
s = "\\begin{tabular}{r|cc|cc|cc}\n\\toprule\n& \\multicolumn{2}{c|}{top-1 pass rate} & \\multicolumn{2}{c|}{top-3 set pass rate} & \\multicolumn{2}{c}{median rel.\\ $\\ell_2$ diff.}\\\\\n$m/d$ & Kernel & Perm. & Kernel & Perm. & Kernel & Perm.\\\\\n\\midrule\n"
for mult in sorted(P.mult.unique()):
    k = P[(P.est == "kernel") & (P.mult == mult)].iloc[0]
    p = P[(P.est == "perm") & (P.mult == mult)].iloc[0]
    star = "$^\\dagger$" if k.n_exact > 0 else ""
    s += (f"{mult} & {k.pass1:.2f}{star} [{k.pass1_lo:.2f},{k.pass1_hi:.2f}] & {p.pass1:.2f} [{p.pass1_lo:.2f},{p.pass1_hi:.2f}] & "
          f"{k.pass3:.2f}{star} [{k.pass3_lo:.2f},{k.pass3_hi:.2f}] & {p.pass3:.2f} [{p.pass3_lo:.2f},{p.pass3_hi:.2f}] & {k.rel_l2:.3f} & {p.rel_l2:.3f}\\\\\n")
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_pooled.tex", s)
for _, r in P.iterrows():
    NUM[f"pooled_{r.est}_{int(r.mult)}"] = {c: round(float(r[c]), 3) for c in ("pass1", "pass1_lo", "pass1_hi", "pass3", "pass3_lo", "pass3_hi", "jac3", "rel_l2", "pass1_min", "pass1_max", "pass3_min", "pass3_max")}

# ---------------- deployed (pooled over models x instances; d<=10 vs d=20)
d = pd.read_csv(os.path.join(RESULTS, "deployed_metrics.csv"))
d["pass1"] = (d.top1 >= 0.9).astype(float)
d["pass3"] = (d.same3 >= 0.9).astype(float)
SMALL = "$d\\le 10$"
d["grp"] = np.where(d.d <= 10, SMALL, "$d=20$")


def bm(v, fn=np.mean):
    v = np.asarray(v, float)
    bs = fn(v[rng.integers(0, len(v), (2000, len(v)))], axis=1)
    return fn(v), np.percentile(bs, 2.5), np.percentile(bs, 97.5)


names = {"kernel_default": "KernelExplainer (nsamples=auto)", "perm_default": "PermutationExplainer (500 evals)",
         "tree_interventional": "TreeExplainer, interventional"}
s = "\\begin{tabular}{llcrrrr}\n\\toprule\nExplainer & background & $d$ & top-1 pass & top-3 pass & mean top-3 Jacc. & med.\\ rel.\\ $\\ell_2$\\\\\n\\midrule\n"
for ex in ["kernel_default", "perm_default", "tree_interventional"]:
    for bg in ["fixed", "resampled"]:
        for grp in [SMALL, "$d=20$"]:
            g = d[(d.explainer == ex) & (d.bg == bg) & (d.grp == grp)]
            if len(g) == 0:
                continue
            p1, p1l, p1h = bm(g.pass1); p3, p3l, p3h = bm(g.pass3); j, jl, jh = bm(g.jac3); l2, l2l, l2h = bm(g.rel_l2, np.median)
            small = grp == SMALL
            lab = names[ex] if (bg == "fixed" and small) else ""
            s += f"{lab} & {bg} & {grp} & {p1:.2f} & {p3:.2f} & {j:.2f} & {l2:.3f}\\\\\n"
            NUM[f"dep_{ex}_{bg}_{'small' if small else 'd20'}"] = dict(pass1=round(p1, 3), pass1_ci=[round(p1l, 3), round(p1h, 3)], pass3=round(p3, 3), pass3_ci=[round(p3l, 3), round(p3h, 3)], jac3=round(j, 3), rel_l2=round(l2, 3), n=len(g))
    s += "\\midrule\n" if ex != "tree_interventional" else ""
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_deployed.tex", s)

# ---------------- certificate (z >= 1.96), averaged over datasets
F = pd.read_csv(os.path.join(TAB, "tabF_cert.csv"))
s = "\\begin{tabular}{r|ccc|ccc}\n\\toprule\n& \\multicolumn{3}{c|}{top-1 feature} & \\multicolumn{3}{c}{top-3 set}\\\\\n$m/d$ & acc.\\ (all) & coverage & acc.\\ (cert.) & acc.\\ (all) & coverage & acc.\\ (cert.)\\\\\n\\midrule\n"
for mult in (4, 8, 16, 32):
    row = f"{mult}"
    for tag in ("top1", "top3"):
        a = F[(F.mult == mult) & (F.target == tag) & (~np.isfinite(F.thr))]
        b = F[(F.mult == mult) & (F.target == tag) & (F.thr == 1.96)]
        row += f" & {a.precision.mean():.2f} & {b.coverage.mean():.2f} & {b.precision.mean():.2f} [{b.precision.min():.2f}]"
        NUM[f"cert_{tag}_{mult}"] = dict(acc_all=round(a.precision.mean(), 3), coverage=round(b.coverage.mean(), 3), acc_cert=round(b.precision.mean(), 3), acc_cert_min_over_datasets=round(b.precision.min(), 3), acc_all_min=round(a.precision.min(), 3))
    s += row + "\\\\\n"
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_cert.tex", s)

# ---------------- budget split
G = pd.read_csv(os.path.join(TAB, "tabG_split.csv"))
G = G[G.mult >= 4]
s = "\\begin{tabular}{llr|cc}\n\\toprule\nEstimator & split & $m/d$ (each) & err.\\ ratio (avg./single) & top-3 acc.\\ avg./single\\\\\n\\midrule\n"
for est in ("perm", "kernel"):
    for k in (2, 4):
        for mult in (4, 8, 16):
            g = G[(G.est == est) & (G.k == k) & (G.mult == mult)]
            if len(g) == 0:
                continue
            s += f"{'Perm.' if est == 'perm' else 'Kernel'} & {k}$\\times$ & {mult} & {g.ratio_median.median():.2f} & {g.acc3_avg.mean():.2f} / {g.acc3_single.mean():.2f}\\\\\n"
            NUM[f"split_{est}_{k}_{mult}"] = dict(ratio_median_of_cells=round(float(g.ratio_median.median()), 3), acc3_avg=round(float(g.acc3_avg.mean()), 3), acc3_single=round(float(g.acc3_single.mean()), 3))
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_split.tex", s)

# ---------------- validation
V = pd.read_csv(os.path.join(RESULTS, "validate_impl.csv"))
V2 = V[V.m >= 32]
g = V2.groupby("m")[["kernel_mine", "kernel_lib", "perm_mine", "perm_lib"]].median()
s = "\\begin{tabular}{r|cc|cc}\n\\toprule\n& \\multicolumn{2}{c|}{Kernel RMSE} & \\multicolumn{2}{c}{Permutation RMSE}\\\\\n$m$ & ours & \\texttt{shap} & ours & \\texttt{shap}\\\\\n\\midrule\n"
for m, r in g.iterrows():
    s += f"{m} & {r.kernel_mine:.4f} & {r.kernel_lib:.4f} & {r.perm_mine:.4f} & {r.perm_lib:.4f}\\\\\n"
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_validate.tex", s)
NUM["validate_ratio_kernel_median"] = float((V2.kernel_mine / V2.kernel_lib).median())
NUM["validate_ratio_perm_median"] = float((V2.perm_mine / V2.perm_lib).median())

# ---------------- kernel conditioning
K = pd.read_csv(os.path.join(RESULTS, "kernel_conditioning.csv"))
s = "\\begin{tabular}{rrrr}\n\\toprule\n$d$ & $m/d$ & $m$ & frac.\\ ill-conditioned\\\\\n\\midrule\n"
for _, r in K[K.mult.isin([2, 3, 4, 8])].iterrows():
    s += f"{int(r.d)} & {int(r.mult)} & {int(r.budget)} & {r.frac_cond_gt_1e8:.3f}\\\\\n"
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_cond.tex", s)

# ---------------- frontier (appendix)
B = pd.read_csv(os.path.join(TAB, "tabB_frontier.csv"))
s = "\\begin{tabular}{llcccc}\n\\toprule\n& & \\multicolumn{2}{c}{top-1: min.\\ $m/d$} & \\multicolumn{2}{c}{top-3 set: min.\\ $m/d$}\\\\\nDataset & model & Kernel & Perm. & Kernel & Perm.\\\\\n\\midrule\n"
for ds in ["pima", "gmsc", "acsincome", "german"]:
    for mo in ["lr", "xgb", "rf", "mlp"]:
        g = B[(B.dataset == ds) & (B.model == mo)]
        k = g[g.est == "kernel"].iloc[0]; p = g[g.est == "perm"].iloc[0]
        fmt = lambda x: "$>$64" if (pd.isna(x) and ds != "german") else ("$>$32" if pd.isna(x) else str(int(x)))
        s += f"{DSN[ds] if mo == 'lr' else ''} & {mo} & {fmt(k.pass1_min_mult_stable)} & {fmt(p.pass1_min_mult_stable)} & {fmt(k.pass3_min_mult_stable)} & {fmt(p.pass3_min_mult_stable)}\\\\\n"
    s += "\\midrule\n" if ds != "german" else ""
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_frontier.tex", s)

# ---------------- scale sensitivity (appendix)
S = pd.read_csv(os.path.join(TAB, "tabK_scale.csv"))
s = "\\begin{tabular}{llr|cc|cc}\n\\toprule\n& & & \\multicolumn{2}{c|}{top-1 pass} & \\multicolumn{2}{c}{top-3 pass}\\\\\nmodel & est. & $m/d$ & prob. & log-odds & prob. & log-odds\\\\\n\\midrule\n"
for mo in ["lr", "xgb", "rf", "mlp"]:
    for est in ["kernel", "perm"]:
        for mult in (4, 16):
            r = S[(S.model == mo) & (S.est == est) & (S.mult == mult)].iloc[0]
            s += f"{mo if (est == 'kernel' and mult == 4) else ''} & {est} & {mult} & {r.pass1_prob:.2f} & {r.pass1_logit:.2f} & {r.pass3_prob:.2f} & {r.pass3_logit:.2f}\\\\\n"
    s += "\\midrule\n" if mo != "mlp" else ""
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_scale.tex", s)

# ---------------- models
M = pd.read_csv(os.path.join(RESULTS, "core", "model_scores.csv"))
s = "\\begin{tabular}{lcccc}\n\\toprule\nDataset ($d$) & LR & XGB & RF & MLP\\\\\n\\midrule\n"
dd = {"pima": 8, "gmsc": 10, "acsincome": 10, "german": 20}
for ds in ["pima", "gmsc", "acsincome", "german"]:
    row = f"{DSN[ds]} ({dd[ds]})"
    for mo in ["lr", "xgb", "rf", "mlp"]:
        r = M[(M.dataset == ds) & (M.model == mo)].iloc[0]
        row += f" & {r.auc:.3f} / {r.acc:.3f}"
    s += row + "\\\\\n"
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_models.tex", s)

# ---------------- yardsticks (E2/E6)
H = pd.read_csv(os.path.join(TAB, "tabH_yard.csv"))
lab = {"kernel4d": "Kernel sampling, $m=4d$", "perm4d": "Permutation sampling, $m=4d$", "kernel16d": "Kernel sampling, $m=16d$",
       "perm16d": "Permutation sampling, $m=16d$", "bg10": "Background resampling, $B=10$", "bg50": "Background resampling, $B=50$",
       "bg100": "Background resampling, $B=100$", "bg200": "Background resampling, $B=200$", "retrain": "Model retraining (bootstrap)",
       "pathdep": "Path-dep.\\ vs.\\ interventional TreeSHAP", "between_instance": "Two different instances (chance level)"}
s = "\\begin{tabular}{lcccc}\n\\toprule\nSource of difference & cells & top-1 agree & top-3 Jaccard & rel.\\ $\\ell_2$\\\\\n\\midrule\n"
for src in ["kernel4d", "perm4d", "kernel16d", "perm16d", "bg10", "bg50", "bg100", "bg200", "retrain", "pathdep", "between_instance"]:
    g = H[H.source == src]
    if len(g) == 0:
        continue
    s += f"{lab[src]} & {len(g)} & {g.top1.median():.2f} [{g.top1.min():.2f},{g.top1.max():.2f}] & {g.jac3.median():.2f} [{g.jac3.min():.2f},{g.jac3.max():.2f}] & {g.rel_l2.median():.2f}\\\\\n"
    NUM[f"yard_{src}"] = dict(cells=len(g), top1_median=round(float(g.top1.median()), 3), jac3_median=round(float(g.jac3.median()), 3), jac3_min=round(float(g.jac3.min()), 3), jac3_max=round(float(g.jac3.max()), 3), rel_l2_median=round(float(g.rel_l2.median()), 3))
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_yard.tex", s)
T2 = pd.read_csv(os.path.join(TAB, "tabH2_yard_tests.csv"))
NUM["yard_tests"] = {f"{a}_vs_{b}": dict(n=int(len(g)), sampling_more_stable_sig=int(((g.p_holm < .05) & (g.mean_diff_jac3 > 0)).sum()), sampling_less_stable_sig=int(((g.p_holm < .05) & (g.mean_diff_jac3 < 0)).sum()))
                     for (a, b), g in T2.groupby(["sampling", "other"])}
Cc = pd.read_csv(os.path.join(TAB, "tabH3_yard_corr.csv"))
NUM["yard_corr"] = {f"{a}__{b}": dict(median=round(float(g.rho.median()), 2), min=round(float(g.rho.min()), 2), max=round(float(g.rho.max()), 2), n=int(len(g))) for (a, b), g in Cc.groupby(["a", "b"])}

# ---------------- threshold sensitivity
T_ = pd.read_csv(os.path.join(TAB, "tabM_threshold.csv"))
s = "\\begin{tabular}{lr|cccc|cccc}\n\\toprule\n& & \\multicolumn{4}{c|}{top-1 pass rate at threshold} & \\multicolumn{4}{c}{top-3 set pass rate at threshold}\\\\\nest. & $m/d$ & 0.80 & 0.90 & 0.95 & 0.99 & 0.80 & 0.90 & 0.95 & 0.99\\\\\n\\midrule\n"
for est in ("kernel", "perm"):
    for mult in (4, 8, 16, 32):
        row = f"{est} & {mult}"
        for c in ("pass1", "pass3"):
            for thr in (0.8, 0.9, 0.95, 0.99):
                row += f" & {T_[(T_.est == est) & (T_.mult == mult) & (np.isclose(T_.thr, thr))][c].iloc[0]:.2f}"
        s += row + "\\\\\n"
    s += "\\midrule\n" if est == "kernel" else ""
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_thr.tex", s)

# ---------------- mechanism AUC
J = pd.read_csv(os.path.join(TAB, "tabJ_auc.csv"))
for _, r in J.iterrows():
    NUM[f"auc_{r.est}_{r.target}"] = {c: round(float(r[c]), 3) for c in J.columns if c.startswith("auc") or c == "base_rate"}
s = "\\begin{tabular}{llccccc}\n\\toprule\nEst. & target & margin/noise & gap only & $-$non-add. & budget only & base rate\\\\\n\\midrule\n"
for _, r in J.iterrows():
    s += f"{r.est} & {r.target} & {r.auc_margin_over_noise:.2f} & {r.auc_gap_only:.2f} & {r.auc_neg_nonadd:.2f} & {r.auc_budget_only:.2f} & {r.base_rate:.2f}\\\\\n"
s += "\\bottomrule\n\\end{tabular}\n"
w("tab_auc.tex", s)

# ---------------- Spearman mechanism medians
C = pd.read_csv(os.path.join(TAB, "tabC_mechanism.csv"))
NUM["spearman_nonadd_noise_median"] = C.groupby("est")["rho_nonadd_noise"].median().round(3).to_dict()
NUM["spearman_gap3_jac3_median"] = C.groupby("est")["rho_gap3_jac3"].median().round(3).to_dict()
NUM["spearman_gap1_top1_median"] = C.groupby("est")["rho_gap1_top1"].median().round(3).to_dict()
NUM["frac_cells_sig_nonadd"] = float((C.p1 < 0.05).mean())
E = pd.read_csv(os.path.join(TAB, "tabE_kernel_vs_perm.csv"))
NUM["kernel_vs_perm"] = {int(m): dict(n=int(len(g)), kernel_sig_better=int(((g.p_holm < .05) & (g.kernel_minus_perm > 0)).sum()), perm_sig_better=int(((g.p_holm < .05) & (g.kernel_minus_perm < 0)).sum()), mean_diff_jac3=round(float(g.kernel_minus_perm.mean()), 3)) for m, g in E.groupby("mult")}
json.dump(NUM, open(os.path.join(RESULTS, "headline_numbers.json"), "w"), indent=1)
print("ok")
