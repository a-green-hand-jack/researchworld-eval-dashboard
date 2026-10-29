"""Table A2 (appendix): what the cheapest verified top-1 attack does to the *published-style* rank (Arena convention: 1 + #models whose Wald 95% CI lower
bound exceeds this model's upper bound). Reads results/pubrank_summary.csv. Writes tables/tab_pubrank.tex."""
import sys, os, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "scripts")); import common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "tables"; os.makedirs(out, exist_ok=True)
d = pd.read_csv(f"{res}/pubrank_summary.csv"); rows = []
for _, r in d.iterrows():
    esc = lambda x: str(x).replace("_", "\\_")
    rows.append(f"{common.SHORT[r.dataset]} & {r.attack.replace('top1_', '')} & {common.th(r.k)} & {esc(r.new_top1)} & {int(r.n_top1_pubrank)} $\\to$ {int(r.n_top1_pubrank_after)} & {int(r.n_models_pointrank_changed)} & {int(r.n_models_pubrank_changed)} \\\\")
tex = common.wrap(small="scriptsize", tabular="\\begin{tabular}{@{}llrlccc@{}}\\toprule\nDataset & attack & $k$ & new leader & \\# at pub.\\ rank 1 & $\\Delta$ point ranks & $\\Delta$ pub.\\ ranks\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
open(f"{out}/tab_pubrank.tex", "w").write(tex); print(tex)
