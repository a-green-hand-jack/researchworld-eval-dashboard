"""E9: t_fit at fine logging (every 5 steps) vs the E1 logging (every 50/100 steps).
python3 analyze_e9.py OUT_PREFIX E9_RUNDIR E1_RUNS_CSV:LABEL ...   (E1 csv: the label is 'mlp' or 'tfm')
Per run (E9, same seeds as E1): t_fit99 as (a) the sustained crossing (3 consecutive evals = 15 steps), (b) the first crossing, (c) the linear
interpolation of train accuracy between the two evaluations that bracket 0.99, (d) the sustained crossing of the E9 log thinned to the E1 eval spacing
(a check that fine logging reproduces E1), and the E1 value of the same run. Per (model, width): medians. Slopes of log10 t_fit on log10 d (OLS over runs,
CI by resampling seeds, i.e. whole width-profiles) for d=16-256, 16-64 and 64-256, for each of (a), (c), (d) and E1."""
import glob, json, os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collect import sustained

rng = np.random.RandomState(0)


def interp(steps, acc, thr=.99):
    acc = np.asarray(acc)
    for i in range(len(acc)):
        if acc[i] >= thr:
            return float(steps[i]) if i == 0 else steps[i - 1] + (thr - acc[i - 1]) / (acc[i] - acc[i - 1]) * (steps[i] - steps[i - 1])
    return np.nan


rows = []
for f in sorted(glob.glob(sys.argv[2] + "/*.json")):
    r = json.load(open(f)); c = r["config"]; l = r["log"]; st, tr = np.array(l["step"]), np.array(l["train_acc"])
    ee = 100 if c["model"] == "tfm" else 50
    thin = (st % ee == 0)
    rows.append({"model": c["model"], "width": c["width"], "seed": c["seed"], "fine_sustained": sustained(st, tr, .99), "fine_first": r["summary"]["t_fit99"],
                 "fine_interp": interp(st, tr), "thinned_sustained": sustained(st[thin], tr[thin], .99), "eval_every_E1": ee})
D = pd.DataFrame(rows)
E1 = pd.concat([pd.read_csv(s.split(":")[0]).assign(model=s.split(":")[1]) for s in sys.argv[3:]])
E1 = E1[(E1.train_frac == .5) & (E1.lr == .001) & (E1.wd == 1.0)][["model", "width", "seed", "t_fit99_s", "eval_every"]].rename(columns={"t_fit99_s": "E1_sustained", "eval_every": "E1_eval_every"})
D = D.merge(E1, on=["model", "width", "seed"], how="left").sort_values(["model", "width", "seed"])
D.to_csv(sys.argv[1] + "_runs.csv", index=False)
M = D.groupby(["model", "width"])[["fine_sustained", "fine_first", "fine_interp", "thinned_sustained", "E1_sustained"]].median(); M["n"] = D.groupby(["model", "width"]).size()
M.to_csv(sys.argv[1] + "_medians.csv"); print(M.round(1))
print("thinned vs E1 identical:", {m: int((g.thinned_sustained == g.E1_sustained).sum()) for m, g in D.groupby("model")}, "of", D.groupby("model").size().to_dict())


def slope(g, col, lo, hi):
    g = g[(g.width >= lo) & (g.width <= hi)].dropna(subset=[col])
    x, y = np.log10(g.width.values), np.log10(g[col].values)
    return np.polyfit(x, y, 1)[0] if len(set(x)) > 1 else np.nan, g


def boot(g, col, lo, hi, B=1000):
    g = g[(g.width >= lo) & (g.width <= hi)].dropna(subset=[col]); seeds = g.seed.unique()
    per = {k: (np.log10(h.width.values), np.log10(h[col].values)) for k, h in g.groupby("seed")}
    v = []
    for _ in range(B):
        s = rng.choice(seeds, len(seeds)); x = np.concatenate([per[k][0] for k in s]); y = np.concatenate([per[k][1] for k in s])
        xm, ym = x.mean(), y.mean(); v.append(((x - xm) * (y - ym)).sum() / ((x - xm) ** 2).sum() if x.std() > 0 else np.nan)
    return np.nanpercentile(v, [2.5, 97.5])


out = []
for m, g in D.groupby("model"):
    for col in ["fine_sustained", "fine_interp", "thinned_sustained", "E1_sustained"]:
        for lo, hi in [(16, 256), (16, 64), (64, 256)]:
            b, _ = slope(g, col, lo, hi); ci = boot(g, col, lo, hi)
            out.append({"model": m, "measure": col, "d_range": f"{lo}-{hi}", "slope": b, "lo": ci[0], "hi": ci[1]})
O = pd.DataFrame(out); O.to_csv(sys.argv[1] + "_slopes.csv", index=False); print(O.round(2).to_string())
