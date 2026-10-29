"""Table A3 (appendix): smallest verified attack that changes the top-k SET (k=3,5,10), in comparisons (not %), original data; [2.5, 97.5] bootstrap percentiles
when >= 20 resamples exist. '--' = k >= number of participants (MT-Bench has 6). Reads results/decisions_*.csv. Writes tables/tab_topk.tex."""
import sys, os, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "scripts")); import common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "tables"; os.makedirs(out, exist_ok=True)
dec = common.load(res, "decisions")
def f(x): return ">50\\%" if np.isinf(x) else common.th(round(x))
def cell(d, decision, pt):
    e, lo, hi, nb = common.attack_budget(d, decision, "influence_exact", pt)
    if np.isnan(e): return "--"
    e, lo, hi = e * int(d.N.iloc[0]), lo * int(d.N.iloc[0]), hi * int(d.N.iloc[0])
    return f"{f(e)} [{f(lo)}, {f(hi)}]" if nb >= 20 else f(e)
rows = [" & ".join([common.SHORT[k], common.th(d.N.iloc[0])] + [cell(d, f"topk{t}", pt) for t in (3, 5, 10) for pt in ("drop", "flip")]) + " \\\\" for k, d in dec.items()]
tex = common.wrap(small="scriptsize", tabular="\\begin{tabular}{@{}lrcccccc@{}}\\toprule\n & & \\multicolumn{2}{c}{top-3 set} & \\multicolumn{2}{c}{top-5 set} & \\multicolumn{2}{c}{top-10 set}\\\\\n\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}\\cmidrule(l){7-8}\n"
       "Dataset & $N$ & remove & flip & remove & flip & remove & flip\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
open(f"{out}/tab_topk.tex", "w").write(tex); print(tex)
