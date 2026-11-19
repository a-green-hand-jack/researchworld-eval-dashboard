"""E14 / P4(ii) at f = 0.4 and 0.3, not at the logging floor: width trend of t_gen when only the learning rate is tuned, with the lr grid extended above the optimum.
python3 analyze_e14.py OUTDIR [RUNS_CSV]   (default RUNS_CSV results/E14/mlp_e14_runs.csv, made by collect.py from results/E14/mlp)
For each f in {0.4, 0.3} and width: the lr with the smallest median t_gen99 (sustained; censored runs enter at steps_run) on the selection seeds 0-2 is selected
(ties: smaller lr); the selected cell on seeds 0-2 ('sel') and on the fresh seeds 3-5 ('fresh') are written to OUTDIR/{sel,fresh}_f*.csv.
selection.csv lists the selection medians for every lr, whether the optimum is interior (a higher lr is slower) and the number of events.
spec.json lists the slope settings for robust_slopes.py (Tobit slope, run- and seed-level bootstrap, 0.99/0.95/0.50): selected lr (fresh and selection seeds),
and every fixed lr on all six seeds (the selection-free view)."""
import json, os, sys
import numpy as np, pandas as pd

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
runs = pd.read_csv(sys.argv[2] if len(sys.argv) > 2 else "results/E14/mlp_e14_runs.csv")
tg = lambda d: d.t_gen99_s.fillna(d.steps_run)
sel_rows, spec = [], []
for f in sorted(runs.train_frac.unique(), reverse=True):
    r = runs[runs.train_frac == f]
    s = r[r.seed <= 2].assign(tg=lambda d: tg(d))
    med = s.groupby(["width", "lr"]).tg.median().unstack("lr")
    ngen = s.groupby(["width", "lr"]).t_gen99_s.apply(lambda x: x.notna().sum()).unstack("lr").fillna(0)
    nrun = s.groupby(["width", "lr"]).size().unstack("lr")
    pick = {}
    for w in med.index:
        m = med.loc[w]
        pick[int(w)] = float(m.idxmin()) if ngen.loc[w].max() > 0 else float("nan")
    for w in med.index:
        lrs = list(med.columns); p = pick[int(w)]
        if np.isnan(p):
            sel_rows.append(dict(f=f, width=int(w), selected_lr=p, no_event_at_any_lr=True)); continue
        i = lrs.index(p)
        sel_rows.append(dict(f=f, width=int(w), selected_lr=p, median_tgen_selected=float(med.loc[w, p]), n_gen_selected=int(ngen.loc[w, p]),
                             edge_of_grid=bool(i == len(lrs) - 1), interior=bool(0 < i < len(lrs) - 1),
                             slower_at_next_lr_up=bool(i < len(lrs) - 1 and med.loc[w, lrs[i + 1]] > med.loc[w, p]),
                             median_tgen_baseline_lr=float(med.loc[w, 0.001]), **{f"med_lr{l:g}": float(med.loc[w, l]) for l in lrs},
                             **{f"ngen_lr{l:g}": int(ngen.loc[w, l]) for l in lrs}))
    ok = [w for w in pick if not np.isnan(pick[w])]
    sel = pd.concat([r[(r.width == w) & (r.lr == pick[w]) & (r.seed <= 2)] for w in ok]); sel.to_csv(f"{out}/sel_f{f:g}.csv", index=False)
    fr = pd.concat([r[(r.width == w) & (r.lr == pick[w]) & (r.seed >= 3)] for w in ok]); fr.to_csv(f"{out}/fresh_f{f:g}.csv", index=False)
    for nm, tag in [("fresh seeds 3-5", "fresh"), ("selection seeds 0-2", "sel")]:
        for lo in (16, 32):
            if lo not in ok:
                continue
            spec.append(dict(label=f"E14 MLP f={f:g}, wd=1, lr tuned per width, {nm}, d{lo}-128", csv=f"{out}/{tag}_f{f:g}.csv", query=f"width>={lo}", group="E14"))
    for lr in sorted(r.lr.unique()):
        spec.append(dict(label=f"E14 MLP f={f:g}, wd=1, fixed lr={lr:g}, seeds 0-5, d16-128", csv=sys.argv[2] if len(sys.argv) > 2 else "results/E14/mlp_e14_runs.csv",
                         query=f"train_frac=={f} and lr=={lr}", group="E14"))
pd.DataFrame(sel_rows).to_csv(f"{out}/selection.csv", index=False)
json.dump(spec, open(f"{out}/spec.json", "w"), indent=1)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)
print(pd.DataFrame(sel_rows).round(0).to_string(index=False))
