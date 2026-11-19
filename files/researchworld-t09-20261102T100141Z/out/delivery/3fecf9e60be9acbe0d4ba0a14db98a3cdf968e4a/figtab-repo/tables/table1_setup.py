"""Table 1: setup of the main grid (graphs, mechanisms, designs, estimators, metrics, replicates).
Graph sizes, mean degrees and replicate counts are read from results/replicates.parquet and
results/config.json; the mechanism/estimator descriptions restate results/SCHEMA.md and code/docs/THEORY.md.
Output: tables/table1_setup.tex (tabular fragment)."""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "figures"))
import pandas as pd
import common as C

cfg = json.load(open(os.path.join(C.RESULTS, "config.json")))["MAIN"]
d = pd.read_parquet(os.path.join(C.RESULTS, "replicates.parquet"),
                    columns=["experiment", "graph", "graph_id", "rep", "n", "mean_degree", "estimator", "fit_data", "tag"])
d = d[(d.experiment == "MAIN") & (d.estimator == "dm") & (d.fit_data == "observed")]
gl = []
for g in ["er", "sbm", "ba", "ws", "fb_ego", "fb_stanford"]:
    x = d[d.graph == g]
    G = x.groupby("tag").graph_id.nunique().iloc[0]
    reps = x.groupby("tag").size().iloc[0]
    gl.append("\\hspace{1em}%s & $n=%s$, $\\bar d=%.1f$, %d graph draw(s) $\\times$ %d assignments \\\\"
              % (C.GRAPH_LABEL[g], f"{int(x.n.iloc[0]):,}".replace(",", "{,}"), x.mean_degree.mean(), G, reps // G))
tex = r"""\begin{tabular}{@{}lp{9.2cm}@{}}
\toprule
\multicolumn{2}{@{}l}{\textbf{Graphs} (size $n$, mean degree $\bar d$, replicates per cell)} \\
""" + "\n".join(gl) + r"""
\midrule
\textbf{Mechanisms} & M1 linear in neighbour fraction $f_i$; M3 saturating $g(f_i)$; M4 = M1 + 2-hop term; M5 = M1 with degree-dependent spill-over. The GATE $\tau$ is computed exactly from $m(\mathbf 1)-m(\mathbf 0)$ (no rescaling); it equals $2$ in all four mechanisms (direct effect $1$, total spill-over $1$). \\
\textbf{Designs} & Bernoulli($0.5$), Bernoulli($0.1$), graph-cluster randomisation (Louvain, $p=0.5$). \\
\textbf{Estimators} & difference-in-means; Hajek exposure (strict and $q{=}0.75$); OLS on $(z,f)$, $(z,f,\text{degree int.})$, $(z,f,\text{2-hop})$, $(z,f,f^2,zf)$, $(z,f)$ + covariates. \\
\textbf{Metrics} & bias, SD, RMSE, RMSE$/|\tau|$ with bootstrap CIs over replicates; coverage of a cluster-robust 95\% interval. \\
\bottomrule
\end{tabular}
"""
os.makedirs(C.TABOUT, exist_ok=True)
open(os.path.join(C.TABOUT, "table1_setup.tex"), "w").write(tex)
print(tex)
