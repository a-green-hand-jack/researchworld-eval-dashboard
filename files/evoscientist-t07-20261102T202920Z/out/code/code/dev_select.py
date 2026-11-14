"""Select (latent dim, prior scale) separately for the plug-in family and the model-assisted family on DEV benchmarks.
Score = geometric mean over (bench, scenario, budget) cells of mean-MAE(method) / mean-MAE(rand_ht)."""
import glob, os, re
import numpy as np, pandas as pd
from metrics import tidy

FAMILIES = {"plugin": ["rand_plugin", "sort_plugin", "pps_plugin"],
            "ma": ["rand_diff", "sort_diff", "pps_diff", "rand_greg", "sort_greg", "pps_greg"]}
rows = []
for d in sorted(glob.glob("results/dev/d*_s*")):
    dim, sc = map(int, re.match(r".*d(\d+)_s(\d+)", d).groups())
    df = tidy(d)
    df = df[~df.method.str.endswith("_beta")]
    cell = df.groupby(["bench", "scen", "n", "method"]).mae.mean().unstack("method")
    cell = cell[cell.index.get_level_values("n") >= 25]
    for fam, ms in FAMILIES.items():
        for scen in ["random", "top", "bottom", "all"]:
            c = cell if scen == "all" else cell[cell.index.get_level_values("scen") == scen]
            ratio = np.log(c[ms].values / c[["rand_ht"]].values)
            rows.append(dict(family=fam, dim=dim, scale=sc, scen=scen, score=float(np.exp(ratio.mean()))))
r = pd.DataFrame(rows)
pd.set_option("display.width", 200)
r.to_csv("results/dev_selection.csv", index=False)
for fam in FAMILIES:
    t = r[(r.family == fam)].pivot_table(index=["dim", "scale"], columns="scen", values="score")
    print(fam); print(t.round(3)); print("best (all):", t["all"].idxmin(), "best(random+top):", ((t["random"] + t["top"])).idxmin())
