"""R4 on HELM subsets: ratio (order-statistic/majority-type breadth fraction) / (mean-type) against m; cluster bootstrap over subset draws.
usage: r4_helm.py results/e2_helm_s*.csv"""
import sys, glob, numpy as np, pandas as pd
df = pd.concat([pd.read_csv(f) for f in sys.argv[1:]]); rng = np.random.default_rng(7)
MEAN = ["mean", "zmean"]; MED = ["median", "plurality", "copeland"]
def prep(b, col):
    d = df[df.b == b].copy(); d["kf"] = d[col] / d.m
    # keep (draw,target) where nobody is already first, so ratios are about a real price
    g = d.groupby(["m_sub", "draw", "target"]).gap0.apply(lambda x: (x > 0).all()); keep = g[g].index
    d = d.set_index(["m_sub", "draw", "target"]).loc[keep].reset_index()
    return d
def ratio_by_draw(d, num, den):
    p = d.pivot_table(index=["m_sub", "draw"], columns="rule", values="kf", aggfunc="mean")
    return (p[num].mean(1) / p[den].mean(1)).rename("ratio"), p
for b in (1.0, 2.0, 4.0):
    for col in ("k_breadth",):
        d = prep(b, col)
        d = d[d.feas_breadth]  # feasible at this per-task budget
        r, p = ratio_by_draw(d, MED, MEAN)
        r = r.replace([np.inf, -np.inf], np.nan).dropna().reset_index()
        r["lm"] = np.log(r.m_sub)
        def slope(x): return np.polyfit(x.lm, x.ratio, 1)[0]
        s0 = slope(r); bs = []
        keys = r.groupby("m_sub").indices
        for _ in range(500):
            idx = np.concatenate([rng.choice(ix, len(ix)) for ix in keys.values()])
            bs.append(slope(r.iloc[idx]))
        print(f"b={b}sigma  slope of ratio vs ln m = {s0:.3f}  CI [{np.percentile(bs, 2.5):.3f}, {np.percentile(bs, 97.5):.3f}]  n_draws={len(r)}")
        print(r.groupby("m_sub").ratio.agg(["mean", "median", "count"]).round(3).T)
