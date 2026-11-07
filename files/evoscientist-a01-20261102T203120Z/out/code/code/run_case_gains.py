"""E6: case study (an extreme real-world 'benchmark-maxxed' submission on BBH-24) and E7: empirical per-task gains of
fine-tuned models relative to their declared base model (calibration of the gain bound g).
Outputs results/e6_case.csv, results/e6_case_ranks.csv, results/e7_gains.csv, results/e7_gain_quantiles.csv"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lb import agg, boards, runner

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
PARENT = "meta-llama/Llama-3.2-1B-Instruct"

# ---------------- E6
full = boards.load("bbh24"); nox = boards.load("bbh24x")
i_out = list(full.models).index(boards.OUTLIER)
d_real = full.S[i_out] - nox.S[list(nox.models).index(PARENT)]
rows = []
# rank of the outlier under each rule on the full board
for rule in agg.ALL_RULES:
    order, v = runner.rule_rank_order(rule, full.S)
    rows.append(dict(rule=rule, outlier_rank=int(np.where(order == i_out)[0][0]) + 1, value=float(v[i_out]),
                     best_value=float(v[order[0]]), best=full.models[order[0]]))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "e6_case_ranks.csv"), index=False)
# minimal investment for the *parent* to be first on the board without the outlier, per rule
tp = list(nox.models).index(PARENT)
S = nox.S
rows = []
for rule in agg.ALL_RULES:
    c = runner.one_cost(rule, S, tp, "ceil")
    rows.append(dict(rule=rule, min_l1=c["l1"], min_breadth=c["br"], realized_l1=float(d_real.sum()),
                     realized_breadth=int((d_real > 1.0).sum())))
pd.DataFrame(rows).to_csv(os.path.join(OUT, "e6_case.csv"), index=False)
print(pd.DataFrame(rows))

# ---------------- E7
out, qrows = [], []
for nm in ["oll6", "bbh24"]:
    b = boards.load(nm)
    meta = b.meta.reset_index(drop=True)
    idx = {m: i for i, m in enumerate(b.models)}
    for i, r in meta.iterrows():
        par = r["Base Model"]
        if isinstance(par, str) and par != r["fullname"] and par in idx and r["fullname"] != boards.OUTLIER:
            d = b.S[i] - b.S[idx[par]]
            out.append(dict(board=nm, child=r["fullname"], parent=par, type=r["Type"], l1=d.sum(), pos_l1=d[d > 0].sum(),
                            breadth_ge1=int((d >= 1.0).sum()), maxgain=d.max(), **{f"d_{t}": v for t, v in zip(b.tasks, d)}))
g = pd.DataFrame(out)
g.to_csv(os.path.join(OUT, "e7_gains.csv"), index=False)
for nm in ["oll6", "bbh24"]:
    sub = g[g.board == nm]
    tc = [c for c in sub.columns if c.startswith("d_")]
    vals = sub[tc].values
    pos = vals[vals > 0]
    qrows.append(dict(board=nm, n_pairs=len(sub), pooled_pos_gain_q50=np.quantile(pos, .5), q90=np.quantile(pos, .9),
                      q95=np.quantile(pos, .95), q99=np.quantile(pos, .99), max=float(np.nanmax(vals)),
                      maxgain_per_model_q50=sub.maxgain.median(), maxgain_per_model_q90=sub.maxgain.quantile(.9),
                      maxgain_per_model_q99=sub.maxgain.quantile(.99),
                      breadth_ge1_q50=sub.breadth_ge1.median(), breadth_ge1_q90=sub.breadth_ge1.quantile(.9)))
pd.DataFrame(qrows).to_csv(os.path.join(OUT, "e7_gain_quantiles.csv"), index=False)
print(pd.DataFrame(qrows).T)
