"""Aggregate results/deployed_metrics.csv -> results/tables/tabL_deployed.csv (cluster bootstrap over model x instance)"""
import os
import numpy as np, pandas as pd
from data import RESULTS

rng = np.random.default_rng(31)
d = pd.read_csv(os.path.join(RESULTS, "deployed_metrics.csv"))
d["pass1"] = (d.top1 >= 0.9).astype(float)
d["pass3"] = (d.same3 >= 0.9).astype(float)
rows = []
for (ds, ex, bg), g in d.groupby(["dataset", "explainer", "bg"]):
    r = dict(dataset=ds, explainer=ex, bg=bg, n=len(g), d=int(g.d.iloc[0]))
    for c, fn in (("top1", np.mean), ("jac3", np.mean), ("pass1", np.mean), ("pass3", np.mean), ("rel_l2", np.median)):
        v = g[c].values
        bs = fn(v[rng.integers(0, len(v), (2000, len(v)))], axis=1)
        r[c], r[c + "_lo"], r[c + "_hi"] = fn(v), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
    r["frac_exactly_reproducible"] = float((g.rel_l2 < 1e-9).mean())
    rows.append(r)
T = pd.DataFrame(rows)
T.to_csv(os.path.join(RESULTS, "tables", "tabL_deployed.csv"), index=False)
pd.set_option("display.width", 250)
print(T.round(3).to_string())
