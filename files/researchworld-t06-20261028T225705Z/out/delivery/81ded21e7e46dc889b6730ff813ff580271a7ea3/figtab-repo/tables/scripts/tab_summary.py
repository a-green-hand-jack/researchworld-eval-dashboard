"""Table 1 (C1): smallest verified attack, % of N, per dataset: top-1 changes (remove | flip | inject votes) and Kendall tau < 0.95 (remove | flip).
Original data; [2.5, 97.5] percentiles over bootstrap resamples of the comparisons when >= 20 resamples exist, else point value only; '>50' = none found within 50% of N.
Reads results/decisions_*.csv. Writes tables/tab_summary.tex (booktabs). Usage: tab_summary.py [RESULTS_DIR] [OUT_DIR]"""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "scripts")); import common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "tables"; os.makedirs(out, exist_ok=True)
dec = common.load(res, "decisions")
def f(x): return ">50" if np.isinf(x) else (f"{x*100:.3f}" if x < 0.001 else f"{x*100:.2f}" if x < 0.1 else f"{x*100:.1f}")
def cell(d, decision, method, pt):
    e, lo, hi, nb = common.attack_budget(d, decision, method, pt)
    return "--" if np.isnan(e) else (f"{f(e)} [{f(lo)}, {f(hi)}]" if nb >= 20 else f"{f(e)}")
def block(title, decision, method, types):
    r = [f"\\multicolumn{{6}}{{@{{}}l}}{{\\emph{{{title}}}}}\\\\"]
    for k, d in dec.items():
        r.append(" & ".join([common.SHORT[k], common.th(d.N.iloc[0]), str(int(d.p.iloc[0]))] + [cell(d, decision, method, t) if t else "--" for t in types]) + " \\\\")
    return r
rows = block("top-1 changes", "top1", "influence_exact", ("drop", "flip", "add_a_wins")) + ["\\midrule"] + block("Kendall $\\tau<0.95$", "tau0.95", "influence_exact_greedy", ("drop", "flip", None))
tex = common.wrap("\\begin{tabular}{@{}lrrccc@{}}\\toprule\nDataset & $N$ & $p$ & remove & flip & inject\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
open(f"{out}/tab_summary.tex", "w").write(tex); print(tex)
