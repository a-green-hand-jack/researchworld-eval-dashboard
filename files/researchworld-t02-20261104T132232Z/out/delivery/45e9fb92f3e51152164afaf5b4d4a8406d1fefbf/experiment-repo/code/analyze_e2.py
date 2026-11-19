"""E2: outcome classes and generalisation fraction per (model, width, f). python3 analyze_e2.py OUT.csv RUNS.csv [RUNS.csv ...]
Classes (SPEC): no_fit | memorise_only (fit, no 0.99 sustained gen in budget) | grok (delay > 5*eval_every) | direct.
f_gen(w): smallest f at which >= 2/3 of the seeds generalise (sustained 0.95 / 0.99) within budget.
Pass the E1 runs (f = 0.5) together with the E2 runs so that f = 0.5 is a tested f; widths tested at fewer than 3 values of f
(E1-only widths, e.g. d = 256 for tfm, d = 4, 8) are dropped from the table because f_gen is not defined there."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from analysis import wilson

out = sys.argv[1]
d = pd.concat([pd.read_csv(f) for f in sys.argv[2:]]).query("task=='add' and lr==0.001 and wd==1.0 and p==59")
d = d.drop_duplicates("run_id")
d = d[d.groupby(["model", "width"]).train_frac.transform("nunique") >= 3]
def cls(r):
    if pd.isna(r.t_fit99_s): return "no_fit"
    if pd.isna(r.t_gen99_s): return "memorise_only"
    return "grok" if r.t_gen99_s - r.t_fit99_s > 5 * r.eval_every else "direct"
d["outcome"] = d.apply(cls, axis=1)
rows = []
for (m, f, w), g in d.groupby(["model", "train_frac", "width"]):
    n = len(g); r = dict(model=m, train_frac=f, width=w, n=n, n_params=g.n_params.iloc[0])
    for c in ("no_fit", "memorise_only", "grok", "direct"):
        r["n_" + c] = int((g.outcome == c).sum())
    for thr in ("99", "95"):
        k = int(g[f"t_gen{thr}_s"].notna().sum()); lo, hi = wilson(k, n)
        r[f"frac_gen{thr}"] = k / n; r[f"frac_gen{thr}_lo"] = lo; r[f"frac_gen{thr}_hi"] = hi
        r[f"t_gen{thr}_median_events"] = g[f"t_gen{thr}_s"].median()
    r["t_fit_median"] = g.t_fit99_s.median()
    r["final_val_median"] = g.final_val_acc.median()
    rows.append(r)
t = pd.DataFrame(rows); t.to_csv(out, index=False)
pd.set_option("display.width", 250)
print(t[["model", "train_frac", "width", "n", "n_no_fit", "n_memorise_only", "n_grok", "n_direct", "frac_gen95", "frac_gen99", "t_gen95_median_events", "t_fit_median"]].to_string())
for (m, thr), g in [((m, t_), t[t.model == m]) for m in t.model.unique() for t_ in ("99", "95")]:
    fg = {}
    for w, gg in g.groupby("width"):
        ok = gg[gg[f"frac_gen{thr}"] >= 2 / 3].train_frac
        fg[int(w)] = float(ok.min()) if len(ok) else None
    print(m, "thr", thr, "f_gen(w) (smallest f with >=2/3 seeds generalising, among tested f):", fg)
