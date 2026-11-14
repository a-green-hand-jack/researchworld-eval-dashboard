import sys
sys.path.insert(0, "code")
import run_synth as R, pandas as pd, numpy as np
print(pd.DataFrame([R.population_stats(s) for s in R.SCEN]).round(3).to_string())
rows = []
for sc in R.SCEN:
    for r in range(40):
        rows += R.one_rep(sc, 200, 10000, r, 0)
d = pd.DataFrame(rows); d["w"] = 3.92 * d.sd; d["cov"] = (abs(d.theta - d.truth) <= 1.96 * d.sd)
print(d.groupby(["scenario", "method"])["w"].mean().unstack("method").round(3).to_string())
print(d.groupby(["scenario", "method"])["cov"].mean().unstack("method").round(2).to_string())
