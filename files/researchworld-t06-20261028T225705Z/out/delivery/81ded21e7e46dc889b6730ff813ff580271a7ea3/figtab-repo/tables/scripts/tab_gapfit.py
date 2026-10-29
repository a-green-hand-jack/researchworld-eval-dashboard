"""Table A4 (appendix): how the smallest adjacent-pair swap budget k tracks the pair gap z: n adjacent pairs, Spearman(k, z), log-log slope of k on z.
Reads results/summary_fragility_vs_gap.csv. Writes tables/tab_gapfit.tex. With n = 5 pairs (MT-Bench) the correlation is nearly uninformative."""
import sys, os, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "scripts")); import common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "tables"; os.makedirs(out, exist_ok=True)
d = pd.read_csv(f"{res}/summary_fragility_vs_gap.csv"); T = {"drop": "remove", "flip": "flip"}
rows = [f"{common.SHORT[r.dataset]} & {T[r.perturbation_type]} & {int(r.n_pairs)} & {r.spearman_k_z:.2f} & {r.loglog_slope:.2f} \\\\" for r in d.itertuples()]
tex = common.wrap(small="footnotesize", tabular="\\begin{tabular}{@{}llrrr@{}}\\toprule\nDataset & attack & $n$ pairs & Spearman$(k,z)$ & log-log slope\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
open(f"{out}/tab_gapfit.tex", "w").write(tex); print(tex)
