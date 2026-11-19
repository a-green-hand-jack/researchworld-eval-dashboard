"""Dataset descriptors, equivalent-sample-size table and win rates (all from data + results/main.csv)."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

TAB = os.path.join(ROOT, "results", "tables"); os.makedirs(TAB, exist_ok=True)

# ---------------- dataset descriptors ----------------------------------------------------
rows = []
for name in ALL:
    S = load_scores(name); acc = S.mean(1)
    rows.append(dict(dataset=name, family="OpenLLM" if name in OPENLLM else "HELM", models=S.shape[0], items=S.shape[1],
                     mean_acc=S.mean(), sd_model_acc=acc.std(), min_acc=acc.min(), max_acc=acc.max(),
                     frac_items_constant=float((S.std(0) == 0).mean()),
                     frac_dup_model_rows=1 - len(np.unique(S, axis=0)) / S.shape[0]))
pd.DataFrame(rows).round(3).to_csv(os.path.join(TAB, "dataset_stats.csv"), index=False)

# ---------------- win rate and item-equivalents ------------------------------------------------
df = pd.read_csv(os.path.join(ROOT, "results", "main.csv"))
out = []
for (split, n), g in df.groupby(["split", "n"]):
    piv = g.pivot_table(index=["dataset", "seed"], columns="method", values="mae")
    for m in piv.columns:
        if m == "random": continue
        ok = piv[[m, "random"]].dropna()
        win = (ok[m] < ok["random"]).mean()
        ds_mean = ok.groupby("dataset").mean()
        ratio = np.exp(np.log(ds_mean[m] / ds_mean["random"]).mean())
        # random sampling MAE scales ~ n^-1/2 => items of random sampling matching this MAE
        out.append(dict(split=split, n=n, method=m, geo_mae_ratio=ratio, equiv_random_items=n / ratio ** 2, seed_win_rate=win))
pd.DataFrame(out).to_csv(os.path.join(TAB, "equiv_items_winrate.csv"), index=False)
print("extra analysis done")
