"""Table A1 (C5, appendix): modelling-choice variants (ties dropped, ridge, NBA home term). Reads results/sensitivity.csv; writes tables/tab_sensitivity.tex."""
import sys, os, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "figures", "scripts")); import common
res = sys.argv[1] if len(sys.argv) > 1 else "results"; out = sys.argv[2] if len(sys.argv) > 2 else "tables"; os.makedirs(out, exist_ok=True)
d = pd.read_csv(f"{res}/sensitivity.csv"); VN = {"primary": "primary", "ties_dropped": "ties dropped", "ridge_1e-1": "ridge $10^{-1}$", "ridge_1e-5": "ridge $10^{-5}$", "no_home_term": "no home term"}
prim = d[d.variant == 'primary'].set_index('dataset').top1; rows = []; last = None
for _, r in d.iterrows():
    ds = common.SHORT[r.dataset] if r.dataset != last else ""; last = r.dataset
    rows.append(f"{ds} & {VN.get(r.variant, r.variant)} & {int(r.N)} & {r.tau_vs_primary:.3f} & {'same' if r.top1 == prim[r.dataset] else 'changed'} & {r.z_top:.2f} & {int(r.top1_drop)} & {int(r.top1_flip)} \\\\")
tex = common.wrap(small="scriptsize", tabular="\\begin{tabular}{@{}llrrlrrr@{}}\\toprule\nDataset & variant & $N$ & $\\tau$ vs. primary & leader & $z_{\\rm top}$ & remove $k$ & flip $k$\\\\\\midrule\n" + "\n".join(rows) + "\n\\bottomrule\\end{tabular}\n")
open(f"{out}/tab_sensitivity.tex", "w").write(tex)
print(tex)
