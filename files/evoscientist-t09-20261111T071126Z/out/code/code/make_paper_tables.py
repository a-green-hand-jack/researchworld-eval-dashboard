"""Build the LaTeX tables of the paper from tables/*.csv (all numbers come from the simulation outputs).
Writes paper/tab_*.tex."""
import numpy as np
import pandas as pd
import os
from analysis_lib import TAB, ROOT

OUT = os.path.join(ROOT, "paper")
f = lambda x, k=2: ("--" if not np.isfinite(x) else f"{x:.{k}f}")

# ---------------- Table 1: variance law ratio SD_emp / SD_pred ----------------
v = pd.read_csv(os.path.join(TAB, "E1_varlaw.csv"))
d7 = pd.read_csv(os.path.join(TAB, "E7_degdiag.csv"))


def rng(x):
    return f"{x.mean():.2f} [{x.min():.2f}, {x.max():.2f}] ({len(x)})"


rows = []
syn = v[v.gkind.isin(["er", "ba"]) & (v.tag != "real")]
rows.append(("ER/BA, iid baseline", rng(syn[syn.comm_sd == 0].ratio)))
rows.append(("ER/BA, community baseline", rng(syn[syn.comm_sd == 1].ratio)))
syn = v[v.gkind.isin(["ws", "sbm"]) & (v.tag != "real")]
rows.append(("WS/SBM, iid baseline", rng(syn[syn.comm_sd == 0].ratio)))
rows.append(("WS/SBM, community baseline", rng(syn[syn.comm_sd == 1].ratio)))
r0 = d7[d7.deg_coef == 0]
rows.append(("Real graphs, no degree loading", rng(r0[r0.graph.isin(["stanford3", "egofb"])].ratio_law)))
r1 = d7[(d7.deg_coef == 1)]
rows.append(("Real graphs, degree loading 1.0", rng(r1[r1.graph.isin(["stanford3", "egofb"])].ratio_law)))
rows.append(("ER/BA, degree loading 1.0", rng(r1[r1.graph.isin(["er", "ba"])].ratio_law)))
with open(os.path.join(OUT, "tab_varlaw.tex"), "w") as fh:
    fh.write("\\begin{tabular}{lc}\n\\toprule\nCondition & mean [min, max] (\\#configs) \\\\\n\\midrule\n")
    for a, b in rows:
        fh.write(f"{a} & {b} \\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")

# ---------------- Table 2: mismatch (E5) ----------------
c = pd.read_csv(os.path.join(TAB, "E5_count.csv"))
c = c[c.est == "lin_frac"]
th = pd.read_csv(os.path.join(TAB, "E5_twohop.csv"))
ed = pd.read_csv(os.path.join(TAB, "E5_edgedrop.csv"))
with open(os.path.join(OUT, "tab_mismatch.tex"), "w") as fh:
    fh.write("\\begin{tabular}{llrrr}\n\\toprule\nMismatch & Setting & Predicted bias & Observed bias [95\\% CI] & rRMSE \\\\\n\\midrule\n")
    for _, r in c.iterrows():
        nm = {"ba10": "BA d=10", "ba30": "BA d=30", "er10": "ER d=10", "er30": "ER d=30", "ws10": "WS d=10", "ws30": "WS d=30",
              "stanford30": "Stanford3", "egofb0": "ego-Facebook"}[r.graph]
        fh.write(f"Count channel & {nm} & {f(r.bias_pred)} & {f(r.bias)} [{f(r.bias_lo)}, {f(r.bias_hi)}] & {f(r.rel_rmse)} \\\\\n")
    fh.write("\\midrule\n")
    t = th[(th.est == "lin_frac") & (th.dkind == "bernoulli") & (th.gkind == "er")].sort_values("omega")
    for _, r in t.iterrows():
        fh.write(f"Two-hop (ER, Bern.) & $\\omega={r.omega:.2f}$ & {f(-r.omega)} & {f(r.bias)} [{f(r.bias_lo)}, {f(r.bias_hi)}] & {f(r.rel_rmse)} \\\\\n")
    t = th[(th.est == "lin_frac") & (th.dkind == "cluster") & (th.gkind == "sbm")].sort_values("omega")
    for _, r in t.iterrows():
        fh.write(f"Two-hop (SBM, cluster) & $\\omega={r.omega:.2f}$ & -- & {f(r.bias)} [{f(r.bias_lo)}, {f(r.bias_hi)}] & {f(r.rel_rmse)} \\\\\n")
    fh.write("\\midrule\n")
    t = ed[(ed.est == "lin_frac") & (ed.gkind == "er") & (ed.s == 0)].sort_values("edge_drop")
    for _, r in t.iterrows():
        fh.write(f"Missing edges (ER, $s{{=}}0$) & $q={r.edge_drop:.2f}$ & {f(-r.edge_drop)} & {f(r.bias)} [{f(r.bias_lo)}, {f(r.bias_hi)}] & {f(r.rel_rmse)} \\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")

# ---------------- Table 3: coverage (E6) ----------------
cv = pd.read_csv(os.path.join(TAB, "E6_coverage.csv"))
cv = cv[cv.est == "oracle_h"]
with open(os.path.join(OUT, "tab_coverage.tex"), "w") as fh:
    fh.write("\\begin{tabular}{llcccc}\n\\toprule\nGraph & Design & $s$ & HC1 & 2-hop HAC & SE-ratio \\\\\n\\midrule\n")
    for _, r in cv.sort_values(["graph", "dkind", "s"]).iterrows():
        nm = {"er": "ER", "sbm": "SBM", "egofb": "ego-FB"}[r.graph]
        dk = {"bernoulli": "Bern.", "cluster": "Cluster"}[r.dkind]
        fh.write(f"{nm} & {dk} & {int(r.s)} & {f(r.cov_hc)} & {f(r.cov_hac)} & {f(r.sd / r.se_hc)} \\\\\n")
    fh.write("\\bottomrule\n\\end{tabular}\n")
print("tables written")
