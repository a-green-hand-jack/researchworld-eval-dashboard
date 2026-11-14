"""Turn per-prediction parquet files into metric tables.
usage: python aggregate.py PRED_DIR OUT_DIR [--baseline random+mean]
Outputs (OUT_DIR): metrics_by_seed.csv (one row per benchmark, split_type, k, seed, method),
summary.csv (mean over seeds + percentile-bootstrap CI over seeds, B=1000),
paired_vs_baseline.csv (paired differences to the baseline method, same split/seed/k, CI by bootstrap over seeds),
rank_summary.csv (mean rank of MAE across benchmarks within split_type, k; descriptive only)."""
import sys, glob, os, argparse
import numpy as np, pandas as pd
from scipy.stats import rankdata

ap = argparse.ArgumentParser(); ap.add_argument("pred_dir"); ap.add_argument("out_dir"); ap.add_argument("--baseline", default="random+mean")
ap.add_argument("--B", type=int, default=1000)
a = ap.parse_args(); os.makedirs(a.out_dir, exist_ok=True)
df = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(os.path.join(a.pred_dir, "*.parquet")))], ignore_index=True)


def tau_b(x, y):
    sx = np.sign(x[:, None] - x[None, :]); sy = np.sign(y[:, None] - y[None, :])
    d = np.sqrt((sx ** 2).sum() * (sy ** 2).sum())
    return (sx * sy).sum() / d if d > 0 else 0.0


def met(g):
    t, p = g['true'].values, g['pred'].values
    e = p - t
    sp = np.corrcoef(rankdata(t), rankdata(p))[0, 1] if np.ptp(p) > 0 and np.ptp(t) > 0 else 0.0
    kt = tau_b(t, p) if np.ptp(p) > 0 else 0.0
    return pd.Series(dict(mae=np.abs(e).mean(), rmse=np.sqrt((e ** 2).mean()), bias=e.mean(), spearman=sp, kendall=kt,
                          n_targets=len(g), true_sd=t.std()))


keys = ["benchmark", "split_type", "s_frac", "n_source", "n", "seed", "method"]
ms = df.groupby(keys, sort=False).apply(met, include_groups=False).reset_index()
ms.to_csv(os.path.join(a.out_dir, "metrics_by_seed.csv"), index=False)

rng = np.random.default_rng(0)
cell = ["benchmark", "split_type", "n", "method"]
rows = []
for key, g in ms.groupby(cell, sort=False):
    v = g[["mae", "rmse", "bias", "spearman", "kendall"]].values
    bi = rng.integers(0, len(v), (a.B, len(v)))
    bm = v[bi].mean(1)
    r = dict(zip(cell, key)); r["n_seeds"] = len(v); r["n_targets_mean"] = g.n_targets.mean()
    for j, m in enumerate(["mae", "rmse", "bias", "spearman", "kendall"]):
        r[m] = v[:, j].mean(); r[m + "_lo"], r[m + "_hi"] = np.percentile(bm[:, j], [2.5, 97.5])
    rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(a.out_dir, "summary.csv"), index=False)

base = ms[ms.method == a.baseline].set_index(["benchmark", "split_type", "n", "seed"])
rows = []
for key, g in ms[ms.method != a.baseline].groupby(cell, sort=False):
    g = g.set_index(["benchmark", "split_type", "n", "seed"])
    b = base.reindex(g.index)
    r = dict(zip(cell, key)); r["baseline"] = a.baseline; r["n_seeds"] = len(g)
    bi = rng.integers(0, len(g), (a.B, len(g)))
    for m in ["mae", "rmse", "spearman", "kendall"]:
        d = (g[m] - b[m]).values
        bm = d[bi].mean(1)
        r[m + "_diff"] = d.mean(); r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(bm, [2.5, 97.5])
        r[m + "_win_rate"] = float((d < 0).mean() if m in ("mae", "rmse") else (d > 0).mean())
    rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(a.out_dir, "paired_vs_baseline.csv"), index=False)

s = pd.DataFrame(rows and pd.read_csv(os.path.join(a.out_dir, "summary.csv")))
s["rank_mae"] = s.groupby(["benchmark", "split_type", "n"]).mae.rank()
s["rank_spearman"] = s.groupby(["benchmark", "split_type", "n"]).spearman.rank(ascending=False)
s.groupby(["split_type", "n", "method"])[["rank_mae", "rank_spearman"]].mean().reset_index().to_csv(os.path.join(a.out_dir, "rank_summary.csv"), index=False)
print("done", len(ms), "metric rows")
