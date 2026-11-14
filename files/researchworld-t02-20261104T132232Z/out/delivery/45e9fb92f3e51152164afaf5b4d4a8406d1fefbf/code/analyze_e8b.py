"""Cap-matched long-cap grid (E8 + E8b): cell fractions that generalise with Wilson 95% CIs, f_gen(width) and a merged run table.

python3 analyze_e8b.py OUTDIR [E8_RUNS_MLP E8B_RUNS_MLP E8_RUNS_TFM E8B_RUNS_TFM]

Merging rule: runs are keyed by (model, width, train_frac, seed); training is deterministic given the config and the stop rule ends a run
~500 steps after val acc >= 0.99, so a run is the same under any cap above its stopping step. Where E8 and E8b both contain a key (d = 256,
f = 0.3, seeds 0-2: 60k cap in E8, 100k in E8b) the E8b (100k) run is used and the two are compared (they must agree).
Counts use the sustained (3-evaluation) crossing t_gen99_s / t_gen95_s; a seed 'generalises' if the crossing happened within the run.
"""
import sys, os, json
import numpy as np, pandas as pd

def wilson(k, n, z=1.959964):
    if n == 0: return (np.nan, np.nan)
    ph = k / n; den = 1 + z * z / n
    c = (ph + z * z / (2 * n)) / den; h = z * np.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - h), min(1.0, c + h))

def merge(a, b):
    k = ["model", "width", "train_frac", "seed"]
    a = a.copy(); b = b.copy(); a["src"] = "E8"; b["src"] = "E8b"
    both = a.merge(b, on=k, suffixes=("_a", "_b"))
    cmp = both[k + ["max_steps_a", "max_steps_b", "t_gen99_s_a", "t_gen99_s_b", "t_gen95_s_a", "t_gen95_s_b", "steps_run_a", "steps_run_b"]]
    keep = a.merge(b[k], on=k, how="left", indicator=True); keep = keep[keep._merge == "left_only"].drop(columns="_merge")
    return pd.concat([keep, b], ignore_index=True), cmp

def cells(d):
    rows = []
    for (m, f, w), g in d.groupby(["model", "train_frac", "width"]):
        n = len(g); r = dict(model=m, train_frac=f, width=w, n_seeds=n, cap=int(g.max_steps.max()), caps_in_cell=",".join(map(str, sorted(g.max_steps.unique()))))
        for thr, col in (("99", "t_gen99_s"), ("95", "t_gen95_s")):
            k = int(g[col].notna().sum()); lo, hi = wilson(k, n)
            r.update({f"n_gen{thr}": k, f"frac_gen{thr}": k / n, f"wilson_lo{thr}": lo, f"wilson_hi{thr}": hi})
        ev = g.t_gen99_s.dropna()
        r["median_tgen99_events"] = float(ev.median()) if len(ev) else np.nan
        r["n_events_for_median"] = len(ev)
        rows.append(r)
    return pd.DataFrame(rows).sort_values(["model", "train_frac", "width"])

def fgen(c, level=0.5):
    """Per width: the smallest f in the grid at which at least `level` of the seeds generalise (0.99, sustained); NaN if none."""
    rows = []
    for (m, w), g in c.groupby(["model", "width"]):
        g = g.sort_values("train_frac"); ok = g[g.frac_gen99 >= level]
        rows.append(dict(model=m, width=w, level=level, f_gen=float(ok.train_frac.min()) if len(ok) else np.nan,
                         f_grid_tested=",".join(f"{x:g}" for x in g.train_frac), cap_at_f_gen=int(ok.sort_values('train_frac').cap.iloc[0]) if len(ok) else -1))
    return pd.DataFrame(rows)

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    p = sys.argv[2:] or ["results/E8/mlp_e8_runs.csv", "results/E8b/mlp_e8b_runs.csv", "results/E8/tfm_e8_runs.csv", "results/E8b/tfm_e8b_runs.csv"]
    allr, allc = [], []
    for old, new in ((p[0], p[1]), (p[2], p[3])):
        a = pd.read_csv(old); b = pd.read_csv(new) if os.path.exists(new) else a.iloc[:0]
        d, cmp = merge(a, b); allr.append(d); allc.append(cmp)
    mlp, tfm = allr; mlp.to_csv(f"{out}/mlp_merged_runs.csv", index=False); tfm.to_csv(f"{out}/tfm_merged_runs.csv", index=False)
    pd.concat(allc).to_csv(f"{out}/overlap_check.csv", index=False)
    c = pd.concat([cells(mlp), cells(tfm)]); c.to_csv(f"{out}/cell_fractions.csv", index=False)
    pd.concat([fgen(c, 0.5), fgen(c, 1.0 / 3)]).to_csv(f"{out}/f_gen_by_width.csv", index=False)
    print(c.to_string(index=False)); print(pd.read_csv(f"{out}/overlap_check.csv").to_string(index=False))
