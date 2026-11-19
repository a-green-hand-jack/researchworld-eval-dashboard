"""E7 transformer part (cheap version of the P4(ii) clean test): wd = 1, d = 16, 32, 64. python3 analyze_e7_tfm.py OUTDIR
lr per width selected on seeds 0-2 of E3 (candidates 3e-4, 1e-3, 3e-3; smallest median censored t_gen99), fresh seeds 3-5 from E7 (tfm) and E3b.
Writes OUTDIR/fresh_tuned.csv, OUTDIR/fresh_lr1e-3.csv and spec.json for robust_slopes.py. Three widths and three seeds: expected 'not informative'."""
import json, os, sys
import pandas as pd
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
e3 = pd.read_csv("results/E3/e3_runs.csv").query("model=='tfm' and wd==1.0")
fresh = pd.concat([pd.read_csv("results/E7/tfm_e7_runs.csv"), pd.read_csv("results/E3b/e3b_runs.csv").query("model=='tfm'")]).query("wd==1.0 and seed>=3")
e3["tg"] = e3.t_gen99_s.fillna(e3.steps_run)
pick = e3.groupby(["width", "lr"]).tg.median().unstack().idxmin(axis=1).to_dict()
print("selected lr per width:", pick)
tuned = pd.concat([fresh[(fresh.width == w) & (fresh.lr == l)] for w, l in pick.items()]); tuned.to_csv(f"{out}/fresh_tuned.csv", index=False)
fixed = fresh[fresh.lr == 1e-3]; fixed.to_csv(f"{out}/fresh_lr1e-3.csv", index=False)
json.dump([dict(label="E7 tfm wd=1, lr tuned per width (E3 seeds 0-2), fresh seeds 3-5, d16-64", csv=f"{out}/fresh_tuned.csv", group="E7"),
           dict(label="E7 tfm wd=1, lr=1e-3, fresh seeds 3-5, d16-64", csv=f"{out}/fresh_lr1e-3.csv", group="E7")], open(f"{out}/spec.json", "w"), indent=1)
print(tuned.groupby("width").agg(n=("seed", "size"), lr=("lr", "first"), ngen=("t_gen99_s", lambda x: x.notna().sum())))
