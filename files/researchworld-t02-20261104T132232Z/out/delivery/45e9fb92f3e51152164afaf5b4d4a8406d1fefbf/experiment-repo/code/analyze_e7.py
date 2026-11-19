"""E7 / P4(ii): width trend of t_gen when only the learning rate is tuned, at fixed weight decay.
python3 analyze_e7.py OUTDIR [MAX_LR]   (MAX_LR: only candidate lrs <= MAX_LR, e.g. 0.01 for the pre-planned E7 grid; default all, i.e. with the E7b grid up to 0.1; reads results/E7/mlp_e7_runs.csv, results/E7/mlp_hi_runs.csv if present, results/E3/e3_runs.csv, results/E3b/e3b_runs.csv)
For wd in {1, 2} (E7 and E7b grids) and wd = 3 (E3 + E3b): per width, the lr with the smallest median t_gen99 (sustained; censored runs enter at steps_run)
on the selection seeds 0-2 is selected (ties: smaller lr); the runs of the selected cell on seeds 0-2 ('selection') and on the fresh seeds 3-5 ('fresh')
are written to OUTDIR/sel_wd*.csv and fresh_wd*.csv, and OUTDIR/spec.json lists the width-slope settings for robust_slopes.py
(Tobit slope with run- and seed-level CIs at 0.99/0.95/0.50), each with all widths and without d=16.
wd = 3: d=16 never fits in E3 at any lr (censored at the cap in all 9 runs), so its 'selected' lr is that of d=32 and its rows are the E3 seeds 0-2 runs,
entered as censored; there are no fresh seeds at d=16 (E3b has none)."""
import json, os, sys
import numpy as np, pandas as pd

out = sys.argv[1]; os.makedirs(out, exist_ok=True)
e7 = [pd.read_csv("results/E7/mlp_e7_runs.csv")]
if os.path.exists("results/E7/mlp_hi_runs.csv"):
    e7.append(pd.read_csv("results/E7/mlp_hi_runs.csv"))
if os.path.exists("results/E7/mlp_wd3hi_runs.csv"):     # E7c: wd = 3 at lr 1e-2, 3e-2, 1e-1 (seeds 0-5)
    e7.append(pd.read_csv("results/E7/mlp_wd3hi_runs.csv"))
e7 = pd.concat(e7)
MAXLR = float(sys.argv[2]) if len(sys.argv) > 2 else 1e9
e7 = e7[e7.lr <= MAXLR]
e3 = pd.read_csv("results/E3/e3_runs.csv").query("model=='mlp'"); e3b = pd.read_csv("results/E3b/e3b_runs.csv").query("model=='mlp'")
e3_wd1 = e3[(e3.wd == 1.0) & (e3.lr == 0.0003)]            # slower than lr 1e-3 at every width (checked below); candidate for completeness
cand = {1.0: pd.concat([e7[e7.wd == 1.0], e3_wd1]), 2.0: e7[e7.wd == 2.0], 3.0: pd.concat([e3[e3.wd == 3.0], e7[e7.wd == 3.0]])}
fresh_src = {1.0: e7, 2.0: e7, 3.0: pd.concat([e3b, e7[e7.wd == 3.0]])}
tg = lambda d: d.t_gen99_s.fillna(d.steps_run)

sel_rows, spec = [], []
for wd, c in cand.items():
    s = c[c.seed <= 2].assign(tg=lambda d: tg(d))
    med = s.groupby(["width", "lr"]).tg.median().unstack("lr")
    ngen = s.groupby(["width", "lr"]).t_gen99_s.apply(lambda x: x.notna().sum()).unstack("lr")
    pick = {int(w): float(med.loc[w].idxmin()) for w in med.index}          # idxmin: first minimum in ascending-lr column order
    none = [w for w in med.index if ngen.loc[w].max() == 0]
    if none:
        ref = pd.Series([pick[w] for w in pick if w not in none]).mode()[0]
        for w in none:
            pick[int(w)] = float(ref)
    for w in med.index:
        sel_rows.append(dict(wd=wd, width=int(w), selected_lr=pick[int(w)], median_tgen_selected=float(med.loc[w, pick[int(w)]]), n_gen_selected=int(ngen.loc[w, pick[int(w)]]),
                             edge_of_grid=bool(pick[int(w)] == med.columns.max()), no_event_at_any_lr=int(w) in none,
                             **{f"med_lr{l:g}": float(med.loc[w, l]) for l in med.columns}))
    sel = pd.concat([c[(c.width == w) & (c.lr == pick[w]) & (c.seed <= 2)] for w in pick]); sel.to_csv(f"{out}/sel_wd{wd:g}.csv", index=False)
    fr = pd.concat([fresh_src[wd][(fresh_src[wd].width == w) & (fresh_src[wd].lr == pick[w]) & (fresh_src[wd].seed >= 3) & (fresh_src[wd].wd == wd)] for w in pick])
    censored16 = wd == 3.0 and not (fr.width == 16).any()
    if censored16:   # no fresh d=16 runs exist: the d=16 selection-seed runs (censored) stand in, flagged by the label
        fr16 = sel[sel.width == 16]
        fr_with16 = pd.concat([fr16, fr]); fr_with16.to_csv(f"{out}/fresh_wd{wd:g}_with16.csv", index=False)
    fr.to_csv(f"{out}/fresh_wd{wd:g}.csv", index=False)
    for nm, df, tag in [("selection seeds 0-2", sel, "sel"), ("fresh seeds 3-5", fr, "fresh")] + ([("fresh seeds 3-5 + d16 (seeds 0-2, censored)", fr_with16, "fresh_with16")] if censored16 else []):
        for lo, hi in [(16, 128), (32, 128)]:
            if lo == 16 and tag == "fresh" and censored16:
                continue
            csv = f"{out}/{'fresh' if tag.startswith('fresh') else 'sel'}_wd{wd:g}{'_with16' if tag == 'fresh_with16' else ''}.csv"
            if tag == "fresh_with16" and lo == 32:
                continue
            spec.append(dict(label=f"E7 MLP wd={wd:g}, lr tuned per width, {nm}, d{lo}-{hi}", csv=csv, query=f"width>={lo} and width<={hi}", group="E7"))
pd.DataFrame(sel_rows).to_csv(f"{out}/selection.csv", index=False)
json.dump(spec, open(f"{out}/spec.json", "w"), indent=1)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(pd.DataFrame(sel_rows).round(0).to_string(index=False))
