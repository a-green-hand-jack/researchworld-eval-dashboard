"""Table 2 (C2): smallest verified top-1 attack k (remove | flip) vs. P(top-1 changes) under random removal / flipping of m = k and m = 10k comparisons
(Wilson 95% interval over R draws). Reads results/decisions_*.csv (attack k) and results/benign_at_k_*.csv (random runs at equal size).
Datasets whose benign_at_k file is not yet there are listed with '--'. Writes tables/tab_adv_vs_benign.tex. Usage: tab_adv_vs_benign.py [RESULTS_DIR] [OUT_DIR]"""
import sys, os, numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "scripts")); import common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "tables"; os.makedirs(out, exist_ok=True)
dec = common.load(res, "decisions"); bk = common.load(res, "benign_at_k")
def cells(k, pt, bt):
    o = dec[k][(dec[k].replicate < 0) & (dec[k].decision == "top1") & (dec[k].method == "influence_exact") & (dec[k].perturbation_type == pt)]
    if o.empty or np.isnan(o.budget_k.iloc[0]): return ["--"] * 3
    kk = int(o.budget_k.iloc[0]); r = [common.th(kk)]
    for mult in (1, 10):
        g = bk[k][(bk[k].decision == "top1") & (bk[k].perturbation_type == bt) & (bk[k].multiple == mult)] if k in bk else []
        r.append("--" if len(g) == 0 else f"{g.p_change.iloc[0]:.2f} [{g.ci_lo.iloc[0]:.2f}, {g.ci_hi.iloc[0]:.2f}]")
    return r
rows = [" & ".join([common.SHORT[k]] + cells(k, "drop", "random_drop") + cells(k, "flip", "random_flip")) + " \\\\" for k in dec]
tex = common.wrap(small="scriptsize", tabular="\\begin{tabular}{@{}lrccrcc@{}}\\toprule\n & \\multicolumn{3}{c}{remove} & \\multicolumn{3}{c}{flip}\\\\\n\\cmidrule(lr){2-4}\\cmidrule(l){5-7}\n"
       "Dataset & attack $k$ & random, $m{=}k$ & random, $m{=}10k$ & attack $k$ & random, $m{=}k$ & random, $m{=}10k$\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
open(f"{out}/tab_adv_vs_benign.tex", "w").write(tex); print(tex)
