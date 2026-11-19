"""R1 at the pre-registered budget: breadth of each rule at b = c * (median over targets of B* of the mean family), c in (1, 1.5, 2), in sigma units of the board's own granularity.
usage: [CGRID=1,1.5,2] run_r1.py BOARD(helm|m6raw|m39) OUT.csv [shard n_shards] [ntargets=30: targets with official rank <= ntargets, also for the median B*]   needs results/e2_full_helm.csv (helm) or results/e2_ollb_s*.csv (m6raw, m39) for B*."""
import sys, os, glob, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import numpy as np, pandas as pd
from lbprice import solvers as SV
from lbprice.e2 import RULES2
from lbprice.boards import load_helm, load_ollb
name, out = sys.argv[1], sys.argv[2]
shard, ns = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (0, 1)
raw = pd.read_csv("results/e2_full_helm.csv") if name == "helm" else pd.concat([pd.read_csv(f) for f in sorted(glob.glob("results/e2_ollb_s*.csv"))])
NT = int(sys.argv[5]) if len(sys.argv) > 5 else 30
CG = tuple(float(x) for x in os.environ.get("CGRID", "1,1.5,2").split(","))   # budget multiples c; CGRID=... gives the crossing-budget grid (files r1x_*.csv)
raw = raw[raw.board == name]
if "rank_official" in raw: raw = raw[raw.rank_official <= NT]   # the OLLB E2 files hold exactly the top-30 targets
raw = raw.drop_duplicates(["target", "rule"])
b = load_helm() if name == "helm" else load_ollb(name)
S = b["S"]; sig = S.std(axis=0); m = S.shape[1]; wh = b.get("w_h")
meanfam = ["mean", "zmean"] if name != "m39" else ["meanh", "zmean"]
medB = float(raw[raw.rule.isin(meanfam)].groupby("target").Bstar.median().replace(np.inf, np.nan).median())
rules = RULES2 + (["meanh"] if wh is not None else [])
targets = sorted(raw.target.unique()); rows = []; t0 = time.time()
for i, t in enumerate(targets):
    if i % ns != shard: continue
    for c in CG:
        for rule in rules:
            rr, w = ("mean", wh) if rule == "meanh" else (rule, None)
            kw = dict(ceil=100.0, kappa=1.0 / sig, gamma=1, sigma=sig, w=w, time_limit=30.0)
            gap0 = float(raw[(raw.target == t) & (raw.rule == rule)].gap0.iloc[0]) if ((raw.target == t) & (raw.rule == rule)).any() else np.nan
            for obj in ("breadth", "depth"):
                p = SV.price(rr, S, t, c * medB * sig, objective=obj, **kw)
                rows.append(dict(board=name, target=int(t), model=b["names"][t], rank_official=int(raw[raw.target == t].rank_official.iloc[0]) if "rank_official" in raw else np.nan, rule=rule, c=c, b_sigma=c * medB,
                                 med_Bstar_meanfam=medB, objective=obj, feasible=p["feasible"], k=p["breadth"] if p["feasible"] else np.nan, m=m, cost=p["cost"] if p["feasible"] else np.nan,
                                 gap0=gap0, mip_gap=p["mip_gap"], verified=p["verified"]))
    print(name, t, len(rows), round(time.time() - t0), flush=True)
    pd.DataFrame(rows).to_csv(out, index=False)
print("done", len(rows), "medB*", medB)
