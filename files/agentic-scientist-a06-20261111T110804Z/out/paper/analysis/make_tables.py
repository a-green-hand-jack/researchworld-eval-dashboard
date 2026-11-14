"""Generate LaTeX table bodies from derived analysis JSON files (no numbers are typed by hand).
# @evidence[[analysis/final_per_case.json]]
# @evidence[[analysis/reconstructed_baselines.json]]
# @evidence[[analysis/search_variants.json]]
# @evidence[[analysis/kappa_values.json]]
"""
import json
F = json.load(open("analysis/final_per_case.json")); R = json.load(open("analysis/reconstructed_baselines.json"))
S = json.load(open("analysis/search_variants.json")); K = json.load(open("analysis/kappa_values.json"))
C = F["cases"]; RC = R["cases"]; A = F["aggregate_primary"]; RA = R["aggregate_primary"]
f = lambda x, n=3: f"{x:.{n}f}"
pm = lambda m, s, n=3: f"{m:.{n}f}".replace("-", "$-$") + f"$\\pm${s:.{n}f}"
hdr = "% @evidence[[analysis/final_per_case.json]]\n% @evidence[[analysis/reconstructed_baselines.json]]\n"

# Table 1: aggregate over primary cases P1-P6
rows = [
 ("Naive Wilson", pm(A["naive_IS"]["mean"], A["naive_IS"]["sd"], 4), pm(RA["naive_cov"]["mean"], RA["naive_cov"]["sd"]), f(RA["naive_width"]["mean"]), pm(A["naive_bias"]["mean"], A["naive_bias"]["sd"], 4)),
 ("Bonferroni-Wilson", pm(A["bonferroni_IS"]["mean"], A["bonferroni_IS"]["sd"], 4), pm(RA["bonf_cov"]["mean"], RA["bonf_cov"]["sd"]), f(RA["bonf_width"]["mean"]), pm(A["naive_bias"]["mean"], A["naive_bias"]["sd"], 4)),
 ("Resampling", pm(A["resample_IS"]["mean"], A["resample_IS"]["sd"], 4), pm(RA["resample_cov"]["mean"], RA["resample_cov"]["sd"]), f(RA["resample_width"]["mean"]), pm(RA["resample_bias"]["mean"], RA["resample_bias"]["sd"], 4)),
 ("EB-IRT (ours)", pm(A["proposed_IS"]["mean"], A["proposed_IS"]["sd"], 4), pm(A["coverage"]["mean"], A["coverage"]["sd"]), f(A["width"]["mean"]), pm(A["proposed_bias"]["mean"], A["proposed_bias"]["sd"], 4)),
]
t = hdr + "\\begin{tabular}{lcccc}\n\\toprule\nReporter & Interval score $\\downarrow$ & Coverage & Mean width & Signed bias \\\\\n\\midrule\n"
for i, r in enumerate(rows):
    name = r[0] if i < 3 else "\\textbf{" + r[0] + "}"
    t += name + " & " + " & ".join(r[1:]) + " \\\\\n"
t += "\\bottomrule\n\\end{tabular}\n"
open("tables/aggregate.tex", "w").write(t)

# Table 2: per-case interval score and coverage
meta = {"P1": ("synthetic", "exh.", 150, 32), "P2": ("synthetic", "halv.", 150, 32), "P3": ("real", "exh.", 200, 24), "P4": ("real", "halv.", 200, 24),
        "P5": ("real", "exh.", 60, 24), "P6": ("real", "exh.", 600, 24), "N1": ("synth.\\ null", "exh.", 150, 32), "N2": ("real null", "exh.", 200, 24), "Z1": ("all-zero", "exh.", 100, 8)}
t = hdr + "\\begin{tabular}{llrrcccccc}\n\\toprule\nCase & World, search & $N$ & $K$ & Naive & Bonf. & Resamp. & EB-IRT & Cov.\\ naive & Cov.\\ EB-IRT \\\\\n\\midrule\n"
for c in ["P1", "P2", "P3", "P4", "P5", "P6", "N1", "N2", "Z1"]:
    w, s, n, k = meta[c]
    best = min(C[c][x]["mean"] for x in ("naive_IS", "bonferroni_IS", "resample_IS", "proposed_IS"))
    cells = []
    for x in ("naive_IS", "bonferroni_IS", "resample_IS", "proposed_IS"):
        v = f(C[c][x]["mean"]); cells.append("\\textbf{" + v + "}" if abs(C[c][x]["mean"] - best) < 5e-4 else v)
    t += f"{c} & {w}, {s} & {n} & {k} & " + " & ".join(cells) + f" & {f(RC[c]['naive_cov']['mean'], 2)} & {f(C[c]['coverage']['mean'], 2)} \\\\\n"
    if c == "P6": t += "\\midrule\n"
t += "\\bottomrule\n\\end{tabular}\n"
open("tables/per_case.tex", "w").write(t)

# Supplement per-case detail (mean over 8 seeds with sd)
t = hdr + "\\begin{tabular}{lcccccc}\n\\toprule\nCase & IS EB-IRT & IS naive & Width EB-IRT & Width naive & Bias EB-IRT & Bias naive \\\\\n\\midrule\n"
for c in ["P1", "P2", "P3", "P4", "P5", "P6", "N1", "N2", "Z1"]:
    t += f"{c} & {pm(C[c]['proposed_IS']['mean'], C[c]['proposed_IS']['sd'])} & {pm(C[c]['naive_IS']['mean'], C[c]['naive_IS']['sd'])} & {f(C[c]['width']['mean'])} & {f(RC[c]['naive_width']['mean'])} & {pm(C[c]['proposed_bias']['mean'], C[c]['proposed_bias']['sd'])} & {pm(C[c]['naive_bias']['mean'], C[c]['naive_bias']['sd'])} \\\\\n"
t += "\\bottomrule\n\\end{tabular}\n"
open("tables/supp_per_case.tex", "w").write(t)

# Supplement: Bonferroni and resampling detail
t = hdr + "\\begin{tabular}{lcccccc}\n\\toprule\nCase & IS Bonf. & IS Resamp. & Cov.\\ Bonf. & Cov.\\ Resamp. & Width Bonf. & Width Resamp. \\\\\n\\midrule\n"
for c in ["P1", "P2", "P3", "P4", "P5", "P6", "N1", "N2", "Z1"]:
    t += f"{c} & {pm(C[c]['bonferroni_IS']['mean'], C[c]['bonferroni_IS']['sd'])} & {pm(C[c]['resample_IS']['mean'], C[c]['resample_IS']['sd'])} & {f(RC[c]['bonf_cov']['mean'], 2)} & {f(RC[c]['resample_cov']['mean'], 2)} & {f(RC[c]['bonf_width']['mean'])} & {f(RC[c]['resample_width']['mean'])} \\\\\n"
t += "\\bottomrule\n\\end{tabular}\n"
open("tables/supp_baselines.tex", "w").write(t)

# Search-plane variants
names = [("eb_irt", "EB-IRT (frozen selection)"), ("config_subject_interaction", "+ config$\\times$subject effects"), ("param_bootstrap_pivot", "Bootstrap pivot calibration")]
t = "% @evidence[[analysis/search_variants.json]]\n\\begin{tabular}{lccccc}\n\\toprule\nVariant & Interval score & Coverage & Width & Bias & Null-control cov. \\\\\n\\midrule\n"
for k, lab in names:
    r = S[k]
    t += f"{lab} & {f(r['interval_score'], 4)} & {f(r['coverage'])} & {f(r['width'])} & {f(r['signed_bias'], 4)} & {f(r['null_control_coverage'])} \\\\\n"
r = S["eb_irt"]
t += "\\midrule\n" + f"Naive Wilson & {f(r['naive_IS'], 4)} & -- & -- & {f(r['naive_bias'], 4)} & -- \\\\\n"
t += f"Bonferroni-Wilson & {f(r['bonferroni_IS'], 4)} & -- & -- & -- & -- \\\\\n" + f"Resampling & {f(r['resample_IS'], 4)} & -- & -- & -- & -- \\\\\n"
t += "\\bottomrule\n\\end{tabular}\n"
open("tables/search_variants.tex", "w").write(t)

# kappa table
t = "% @evidence[[analysis/kappa_values.json]]\n\\begin{tabular}{lcccc}\n\\toprule\nCase & $N$ & $K$ & Searcher & $\\kappa$ \\\\\n\\midrule\n"
for c in ["P1", "P2", "P3", "P4", "P5", "P6", "N1", "N2"]:
    v = K[c]; t += f"{c} & {v['N']} & {v['K']} & {v['searcher']} & {v['kappa']:.3f} \\\\\n"
t += "\\bottomrule\n\\end{tabular}\n"
open("tables/kappa.tex", "w").write(t)
