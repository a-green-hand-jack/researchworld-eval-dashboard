"""H7: does a data-computable exposure-support statistic predict the extrapolation (approximation) error of OLS(z, f)?
Pre-specified: regress log|pop_bias| on log(ext), ext = max(1-f_mean, f_mean)/f_sd averaged over replicates (distance of the realised exposure
distribution from the nearer... farther of the two global-effect points, in SDs). Per mechanism; R^2 reported whichever way it goes.
Also reports secondary candidates. Output: results/h7.csv"""
import os, sys
import numpy as np, pandas as pd
R = os.path.join(os.path.dirname(__file__), "..", "..", "results")
dg = pd.read_csv(os.path.join(R, "diagnostics.csv"))
cfg = pd.read_json(os.path.join(R, "config.json"), typ="series")
rows = []
for e, specs in cfg.items():
    for s in specs:
        rows.append(dict(experiment=e, tag=s["tag"], kind=s["outcome"]["kind"], het=s["outcome"].get("het", 0), design=s["design"]["kind"],
                         p=s["design"]["p"], gerr=s.get("graph_err", 0)))
meta = pd.DataFrame(rows)
d = dg[dg.estimator == "ols_f"].merge(meta, on=["experiment", "tag"])
d = d[(d.gerr == 0) & (d.experiment != "MAIN_realdraws")]   # realdraws repeats the real-graph MAIN cells with other baseline draws
d["ext"] = np.maximum(1 - d.f_mean, d.f_mean) / d.f_sd
d["ext_far"] = (1 - d.f_mean) / d.f_sd + d.f_mean / d.f_sd
d["overlap"] = d.overlap_treated + d.overlap_control
d["abs_bias"] = d.pop_bias.abs()
d["mech"] = np.where(d.het > 0, "het", d.kind)
out = []
for name, g in list(d.groupby(["mech", "design"])) + [(("ALL_misspecified", "all"), d[(d.abs_bias > 1e-3)])]:
    g = g[g.abs_bias > 1e-3]
    if len(g) < 5:
        continue
    for stat in ("ext", "ext_far", "overlap", "mean_degree"):
        x = np.log(g[stat].clip(lower=1e-6)); y = np.log(g.abs_bias)
        if x.std() == 0:
            continue
        r = np.corrcoef(x, y)[0, 1]
        sl = np.polyfit(x, y, 1)[0]
        out.append(dict(mech=name[0], design=name[1], stat=stat, n_cells=len(g), r2=r**2, slope=sl, sign=np.sign(r)))
res = pd.DataFrame(out)
res.to_csv(os.path.join(R, "h7.csv"), index=False)
pd.set_option("display.width", 200)
print(res.round(3).to_string())
