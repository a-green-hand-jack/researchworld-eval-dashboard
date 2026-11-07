"""T5 (claim E8): adversarial addition and relabelling budgets relative to removal, adjacent-pair claims.

Reads additions.csv (budget_remove / budget_add / budget_relabel: smallest verified number of comparisons removed, added, or
relabelled that reverses the claim; exact ties excluded; rows with synthetic=True would be excluded too).
The last two columns are the constrained adversary of s5_constrained.csv (all added or relabelled comparisons involve the
target participant, whose opponents follow its observed pair frequencies; best of pushing it down / its rival up): median over the same
claims. Noise-equivalent budget (s5_noise.csv): k_noise_05 = smallest number of uniformly random removals that flips the claim in >= 5% of 200
draws; NaN = never within 98% of N, treated as infinite for the medians; "never" = share of claims with NaN. Writes table5_additions.tex.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "figures"))
import common as C

A = C.args(__doc__)
a = C.read(A.results, "additions.csv")
a = a[(a.claim_type == "C2") & ~a.exact_tie & ~a.synthetic & (a.budget_remove > 0)].copy()
a["group"] = a.dataset.where(a.dataset.isin(C.BASE_UNITS), "nba_seasons")
con = C.read(A.results, "s5_constrained.csv").rename(columns={"unit": "dataset"})
a = a.merge(con[["dataset", "claim", "budget_con_add", "budget_con_relabel"]], on=["dataset", "claim"], how="left")
nz = C.read(A.results, "s5_noise.csv").rename(columns={"unit": "dataset"})
a = a.merge(nz[["dataset", "claim", "k_noise_05"]], on=["dataset", "claim"], how="left")
assert a.k_noise_05.notna().sum() > 0
a["k_noise_inf"] = a.k_noise_05.fillna(float("inf"))
a["noise_ratio"] = a.k_noise_inf / a.budget_remove
def inf(x, fmt):
    return r"$>\!98\%\,N$" if x == float("inf") else fmt.format(x)


rows = []
for g in ["arena55k", "mt_human", "mt_gpt4", "nba_all", "nba_seasons"]:
    d = a[a.group == g]
    q = lambda s: f"{s.median():.2f} [{s.quantile(.25):.2f}, {s.quantile(.75):.2f}]"
    rows.append(" & ".join([C.SHORT_LABEL[g], str(len(d)), f"{d.budget_remove.median():g}", f"{d.budget_add.median():g}", f"{d.budget_relabel.median():g}",
                            q(d.ratio_add_over_remove), q(d.ratio_relabel_over_remove),
                            f"{d.budget_con_add.median():g}", f"{d.budget_con_relabel.median():g}",
                            inf(d.k_noise_inf.median(), "{:.0f}"), f"{100 * d.k_noise_05.isna().mean():.0f}\\%", inf(d.noise_ratio.median(), "{:.0f}")]) + r" \\")
tex = "\n".join([r"\begin{tabular}{lrrrrccrrrrr}", r"\toprule",
                 r"Data & Claims & \multicolumn{3}{c}{Median budget (comparisons)} & \multicolumn{2}{c}{Ratio to removal: median [IQR]} & \multicolumn{2}{c}{Constrained (median)} & \multicolumn{3}{c}{Random removals to flip (5\%)} \\",
                 r"\cmidrule(lr){3-5}\cmidrule(lr){6-7}\cmidrule(lr){8-9}\cmidrule(lr){10-12}",
                 r" & & remove & add & relabel & add & relabel & add & relabel & median $k$ & never & $\div$ adversary \\", r"\midrule", *rows, r"\bottomrule", r"\end{tabular}", ""])
open(os.path.join(A.out, "table5_additions.tex"), "w").write(tex)
C.record_inputs(A.out, "table5_additions.tex", [os.path.join(A.results, f) for f in ["additions.csv", "s5_constrained.csv", "s5_noise.csv"]])
