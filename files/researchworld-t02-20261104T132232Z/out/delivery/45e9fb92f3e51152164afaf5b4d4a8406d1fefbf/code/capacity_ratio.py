"""Capacity-ratio table and collapse test (PLAN P3): python3 capacity_ratio.py OUT_PREFIX RUNS_CSV [...]
Cell = (model, width, f) at task add, p = 59, lr 1e-3, wd 1 (E1 + E2 runs). ratio = n_params / (f p^2) (parameters per training example).
Table: fraction generalising (sustained 0.99 and 0.95), KM-median t_gen, median t_fit per cell.
Collapse check: spread of the fraction generalising among cells in the same factor-2 bin of ratio, and rank correlations of frac_gen with ratio
overall, within one width (varying f) and within one f (varying width) -- the last two have opposite signs if ratio mixes two roles."""
import sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import stats as S

d = pd.concat([pd.read_csv(f) for f in sys.argv[2:]], ignore_index=True)
d = d[(d.task == "add") & (d.p == 59) & np.isclose(d.lr, 1e-3) & np.isclose(d.wd, 1.0) & (d.init_scale == 1.0)]
d = d.drop_duplicates("run_id")
d["ntr"] = (d.train_frac * d.p ** 2).round().astype(int)
d["ratio"] = d.n_params / (d.train_frac * d.p ** 2)
rows = []
for (m, w, f), g in d.groupby(["model", "width", "train_frac"]):
    r = dict(model=m, width=w, f=f, n=len(g), n_params=int(g.n_params.iloc[0]), n_train=int(g.ntr.iloc[0]), ratio=g.ratio.iloc[0])
    for thr in ("99", "95"):
        tg = g[f"t_gen{thr}_s"]; ev = tg.notna()
        r[f"frac_gen{thr}"] = ev.mean()
        r[f"t_gen{thr}_km"] = S.km_median(tg.fillna(g.steps_run).values, ev.values)
    r["t_fit_median"] = g.t_fit99_s.median(); rows.append(r)
T = pd.DataFrame(rows).sort_values(["model", "ratio"]); T.to_csv(sys.argv[1] + "_table.csv", index=False)


# Collapse check: if ratio were the controlling variable, cells with a similar ratio would have a similar outcome whatever (family, width, f).
# Cells are grouped in factor-2 bins of ratio; the spread of frac_gen within a bin (and the rank correlation of frac_gen with ratio, per family) is reported.
T["bin"] = np.floor(np.log2(T.ratio)).astype(int)
B = T.groupby("bin").agg(ratio_lo=("ratio", "min"), ratio_hi=("ratio", "max"), n_cells=("f", "size"),
                          frac_gen99_min=("frac_gen99", "min"), frac_gen99_max=("frac_gen99", "max"),
                          frac_gen95_min=("frac_gen95", "min"), frac_gen95_max=("frac_gen95", "max")).reset_index()
B.to_csv(sys.argv[1] + "_bins.csv", index=False)
print(T.round(3).to_string()); print(B.round(2).to_string())
for m, g in T.groupby("model"):
    print(m, "Spearman(ratio, frac_gen95) over cells:", np.round(spearmanr(g.ratio, g.frac_gen95)[0], 2),
          "| within one width, over f:", {int(w): np.round(spearmanr(h.ratio, h.frac_gen95)[0], 2) for w, h in g.groupby("width") if h.f.nunique() > 3},
          "| within one f, over width:", {float(f): np.round(spearmanr(h.ratio, h.frac_gen95)[0], 2) for f, h in g.groupby("f") if h.width.nunique() > 3})
