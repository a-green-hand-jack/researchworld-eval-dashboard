"""Build committed tidy result tables from raw per-target predictions.

usage: make_tables.py OUTDIR RAWDIR [RAWDIR ...]   (per-benchmark CSVs go to OUTDIR/cells, merged by merge_tables.py)

Bootstrap: B=200 percentile intervals (95%). Resampling unit:
  * protocols with a fixed target set (extrap*): the target models; each resample's metric is averaged over the
    item-selection seeds (reps);
  * protocols with a new target set per rep (random, family, *_s*): the reps (= independent model splits + item seeds).
Both methods in a paired difference use identical resamples.
"""
import os, sys
import numpy as np, pandas as pd
from scipy.stats import rankdata
sys.path.insert(0, os.path.dirname(__file__))
import analysis as A

B = 200  # bootstrap resamples
METRICS = ["mae", "rmse", "spearman", "kendall", "bias", "rmse_over_sd"]


def metrics_arr(a, t):
    """a: (R, T) predictions, t: (T,) truth -> (R, 6) MAE, RMSE, Spearman, Kendall(tau-b), bias (pred-true), RMSE/SD(true)."""
    e = a - t
    mae, rmse = np.abs(e).mean(1), np.sqrt((e ** 2).mean(1))
    ra, rt = rankdata(a, axis=1), rankdata(t)
    ra = ra - ra.mean(1, keepdims=True)
    rt = rt - rt.mean()
    den = np.sqrt((ra ** 2).sum(1) * (rt ** 2).sum())
    sp = np.where(den > 0, (ra * rt).sum(1) / np.where(den > 0, den, 1), 0.0)
    sa = np.sign(a[:, :, None] - a[:, None, :])
    st = np.sign(t[:, None] - t[None, :])
    num = (sa * st).sum((1, 2))
    d = np.sqrt((np.abs(sa).sum((1, 2))) * np.abs(st).sum())
    ke = np.where(d > 0, num / np.where(d > 0, d, 1), 0.0)
    return np.stack([mae, rmse, sp, ke, e.mean(1), rmse / max(t.std(), 1e-12)], 1)


def cell(g, methods, rng):
    """g: rows of one (bench, protocol, n) for all methods. Returns point (M,4), boot (M,B,4), n_models, n_reps."""
    fixed = g.protocol.iloc[0].startswith("extrap")
    reps = np.sort(g.rep.unique())
    pt, bt = {}, {}
    if fixed:
        models = np.sort(g.model.unique())
        tr = g.drop_duplicates("model").set_index("model").loc[models, "true"].values
        arr = {m: g[g.method == m].pivot(index="rep", columns="model", values="pred").loc[reps, models].values for m in methods}
        ixs = rng.integers(0, len(models), (B, len(models)))
        for m in methods:
            pt[m] = metrics_arr(arr[m], tr).mean(0)
            bt[m] = np.stack([metrics_arr(arr[m][:, ix], tr[ix]).mean(0) for ix in ixs])
        nm = len(models)
    else:
        pr = {}
        for m in methods:
            gm = g[g.method == m]
            rows = [metrics_arr(x.pred.values[None], x.true.values)[0] for _, x in gm.groupby("rep")]
            pr[m] = np.array(rows)
        ixs = rng.integers(0, len(reps), (B, len(reps)))
        for m in methods:
            pt[m] = pr[m].mean(0)
            bt[m] = np.stack([pr[m][ix].mean(0) for ix in ixs])
        nm = int(g.groupby("rep").model.nunique().mean())
    return pt, bt, nm, len(reps)


REFS = ["random", "ridge", "aipw_rand", "anchor_irt", "null"]
PROPOSED = "mass_ens"


def run_bench(bench, dirs, outdir, best=None):
    df = A.load(dirs)
    df = df[df.bench == bench]
    cells, paired = [], []
    for (proto, n), g in df.groupby(["protocol", "n"]):
        methods = sorted(g.method.unique())
        rng = np.random.default_rng(abs(hash((bench, proto, int(n)))) % 2 ** 32 if False else (sum(map(ord, bench + proto)) * 1000 + int(n)))
        pt, bt, nm, nr = cell(g, methods, rng)
        nsrc = int(g.n_src.iloc[0])
        for m in methods:
            for j, met in enumerate(METRICS):
                lo, hi = np.percentile(bt[m][:, j], [2.5, 97.5])
                cells.append(dict(bench=bench, protocol=proto, method=m, n=n, metric=met, mean=pt[m][j], ci_lo=lo, ci_hi=hi,
                                  n_models=nm, n_reps=nr, n_src=nsrc))
        refs = list(REFS)
        if best is not None:
            b = best.get((bench, "extrap" if proto.startswith("extrap") else "random"))
            if b and b not in refs:
                refs.append(b)
        pairs = [(m, r) for r in refs for m in methods if m != r] + [(PROPOSED, r) for r in methods if r not in REFS and r != PROPOSED]
        for m, r in pairs:
            if m not in pt or r not in pt:
                continue
            for j, met in enumerate(METRICS):
                d = bt[m][:, j] - bt[r][:, j]
                lo, hi = np.percentile(d, [2.5, 97.5])
                paired.append(dict(bench=bench, protocol=proto, n=n, metric=met, method=m, ref=r,
                                   delta_mean=pt[m][j] - pt[r][j], ci_lo=lo, ci_hi=hi))
    os.makedirs(f"{outdir}/cells", exist_ok=True)
    pd.DataFrame(cells).to_csv(f"{outdir}/cells/{bench}.csv", index=False)
    pd.DataFrame(paired).to_csv(f"{outdir}/cells/{bench}__paired.csv", index=False)


if __name__ == "__main__":
    out, dirs = sys.argv[1], sys.argv[2:]
    best = None
    if os.path.exists(f"{out}/best_baseline.csv"):
        bb = pd.read_csv(f"{out}/best_baseline.csv")
        best = {(r.bench, r.protocol): r.method for r in bb.itertuples()}
    benches = sorted(A.load(dirs).bench.unique()) if not os.environ.get("BENCH") else os.environ["BENCH"].split(",")
    for b in benches:
        run_bench(b, dirs, out, best)
        print("done", b, flush=True)
