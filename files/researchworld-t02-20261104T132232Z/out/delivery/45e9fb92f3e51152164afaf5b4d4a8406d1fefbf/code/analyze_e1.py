"""E1: width sweep summary. python3 analyze_e1.py RUNS_CSV OUT_PREFIX"""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import stats as S

runs = pd.read_csv(sys.argv[1]); pre = sys.argv[2]
rows = []
for (model, f), d in runs.groupby(["model", "train_frac"]):
    cells = d.groupby("width").apply(S.cell_summary, include_groups=False).reset_index()
    cells.insert(0, "model", model); cells.insert(1, "train_frac", f)
    rows.append(cells)
    dd = S.add_censor_columns(d)
    for name, col in [("t_fit", "t_fit_c"), ("t_gen", "t_gen_c"), ("delay", "delay_c")]:
        r, p = S.perm_spearman(dd.width, dd[col])
        sl, ci = S.loglog_slope(dd.width.values, np.maximum(dd[col].values, 1))
        print(f"{model} f={f} {name}: spearman(width,.)={r:.2f} perm p={p:.4f}; loglog slope={sl:.2f} CI[{ci[0]:.2f},{ci[1]:.2f}] "
              f"(censored runs entered at the budget -> slopes for t_gen/delay are lower bounds in magnitude where censored)")
tab = pd.concat(rows); tab.to_csv(pre + "_cells.csv", index=False)
pd.set_option("display.width", 250); print(tab.to_string())
