"""Uncertainty over target models, ablation table and extra metrics for the report (experiment-repo#6).
usage: python analysis_review.py PRED.parquet OUT_DIR [B]
(1) ablation_paired.csv: P3 ablations vs B1 (random+mean) and vs B2 (strat+mean), per benchmark and macro (13 benchmarks), all four metrics,
    CI = percentile bootstrap over repetitions (seeds), as in aggregate.py (targets fixed within a repetition).
(2) target_bootstrap_*.csv: two-level cluster bootstrap. Each replicate resamples repetitions (seeds) with replacement and, inside every
    resampled repetition, resamples that repetition's target models with replacement; the same indices are used for all methods, so
    paired differences stay paired. For `extrap` the target set is the same in every repetition, so this is a bootstrap over the strongest-25% models.
    Per benchmark the replicate is the mean over resampled repetitions of the metric (computed on the resampled targets); the macro replicate is the mean
    over the 13 benchmarks of independent per-benchmark replicates (benchmarks fixed). Kendall: the headline subset only (cost).
(3) macro_metrics.csv: macro MAE/RMSE/Spearman/Kendall for every method with seed-bootstrap CI, and differences to B1 and B2."""
import sys, os, numpy as np, pandas as pd
from scipy.stats import rankdata

pred, out = sys.argv[1], sys.argv[2]; B = int(sys.argv[3]) if len(sys.argv) > 3 else 1000
os.makedirs(out, exist_ok=True); rep = os.path.join(os.environ.get("REPS_DIR", "/tmp/reps")); os.makedirs(rep, exist_ok=True)
df = pd.read_parquet(pred, columns=["benchmark", "split_type", "n", "seed", "method", "target_model", "true", "pred"])
B1, B2 = "random+mean", "strat+mean"
NS = [10, 20, 50, 100]
rng = np.random.default_rng(0)
ABL = ["random+lowrank_dr", "strat+lowrank", "strat+lowrank_dr", "strat+lowrank_eb", "random+lowrank", "strat+mean", "random+mean"]
HEAD = ["random+mean", "strat+mean", "random+cal", "random+lowrank", "random+lowrank_dr", "strat+lowrank", "strat+lowrank_dr", "strat+lowrank_eb",
        "anchor+irt", "anchor+anchor", "random+irt", "omp+ridge", "const"]
KT = ["random+mean", "strat+mean", "random+lowrank_dr", "strat+lowrank_dr", "strat+lowrank_eb", "random+cal", "random+lowrank"]


def rank_corr(T, P):
    """Spearman along last axis for arrays (..., t); 0 when a side is constant."""
    rt, rp = rankdata(T, axis=-1), rankdata(P, axis=-1)
    rt = rt - rt.mean(-1, keepdims=True); rp = rp - rp.mean(-1, keepdims=True)
    den = np.sqrt((rt ** 2).sum(-1) * (rp ** 2).sum(-1))
    return np.where(den > 0, (rt * rp).sum(-1) / np.where(den > 0, den, 1), 0.0)


def kendall(T, P):
    sx = np.sign(T[..., :, None] - T[..., None, :]); sy = np.sign(P[..., :, None] - P[..., None, :])
    den = np.sqrt((sx ** 2).sum((-1, -2)) * (sy ** 2).sum((-1, -2)))
    return np.where(den > 0, (sx * sy).sum((-1, -2)) / np.where(den > 0, den, 1), 0.0)


def metric(name, T, P):
    e = P - T
    if name == "mae": return np.abs(e).mean(-1)
    if name == "rmse": return np.sqrt((e ** 2).mean(-1))
    if name == "spearman": return rank_corr(T, P)
    return kendall(T, P)


rows_t, rows_a, rows_m = [], [], []
for (b, sp), g in df.groupby(["benchmark", "split_type"], sort=True):
    for n in NS:
        gg = g[g.n == n]
        if gg.empty: continue
        # arrays (method -> (seed, target)); targets sorted by name within seed
        arr = {}
        for me, h in gg.groupby("method"):
            h = h.sort_values(["seed", "target_model"])
            S = h.seed.nunique(); T = len(h) // S
            arr[me] = (h["true"].values.reshape(S, T), h["pred"].values.reshape(S, T))
        S, T = arr[B1][0].shape
        # (a) seed-bootstrap metrics per seed (targets fixed)
        per = {me: {m: metric(m, *arr[me]) for m in ("mae", "rmse", "spearman", "kendall")} for me in arr}
        si = rng.integers(0, S, (B, S)); sb = {}
        for me in arr:
            for ref in (B1, B2):
                if me == ref: continue
                r = dict(benchmark=b, split_type=sp, n=n, method=me, baseline=ref, n_seeds=S, n_targets=T)
                for m in ("mae", "rmse", "spearman", "kendall"):
                    d = per[me][m] - per[ref][m]
                    bm = d[si].mean(1); sb[f"{me}|{ref}|{m}"] = bm
                    r[m + "_diff"] = d.mean(); r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(bm, [2.5, 97.5])
                rows_a.append(r)
            r = dict(benchmark=b, split_type=sp, n=n, method=me, n_seeds=S, n_targets=T)
            for m in ("mae", "rmse", "spearman", "kendall"): r[m] = per[me][m].mean()
            rows_m.append(r)
        np.savez_compressed(os.path.join(rep, f"seedboot_{b}_{sp}_{n}.npz"), **sb)
        # (b) two-level bootstrap over repetitions and target models; methods paired through shared indices
        if n == 10: continue
        meths = [m for m in HEAD if m in arr]
        reps = {me: {m: np.empty(B) for m in ("mae", "rmse", "spearman", "kendall")} for me in meths}
        for k in range(B):
            s = rng.integers(0, S, S); t = rng.integers(0, T, (S, T))
            for me in meths:
                Tt = np.take_along_axis(arr[me][0][s], t, 1); Pp = np.take_along_axis(arr[me][1][s], t, 1)
                reps[me]["mae"][k] = np.abs(Pp - Tt).mean(); reps[me]["rmse"][k] = np.sqrt(((Pp - Tt) ** 2).mean(1)).mean()
                reps[me]["spearman"][k] = rank_corr(Tt, Pp).mean()
                if me in KT: reps[me]["kendall"][k] = kendall(Tt, Pp).mean()
        for me in meths:
            for ref in (B1, B2):
                if me == ref: continue
                r = dict(benchmark=b, split_type=sp, n=n, method=me, baseline=ref, n_seeds=S, n_targets=T, B=B)
                for m in ("mae", "rmse", "spearman", "kendall"):
                    if m == "kendall" and not (me in KT and ref in KT): continue
                    d = reps[me][m] - reps[ref][m]
                    r[m + "_diff"] = np.mean([per[me][m].mean() - per[ref][m].mean()])
                    r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(d, [2.5, 97.5])
                rows_t.append(r)
        np.savez_compressed(os.path.join(rep, f"_reps_{b}_{sp}_{n}.npz"), **{f"{me}|{m}": reps[me][m] for me in meths for m in reps[me]})
    print(b, sp, flush=True)

A = pd.DataFrame(rows_a); A.to_csv(os.path.join(out, "ablation_by_benchmark.csv"), index=False)
Tb = pd.DataFrame(rows_t); Tb.to_csv(os.path.join(out, "target_bootstrap_by_benchmark.csv"), index=False)
M = pd.DataFrame(rows_m); M.to_csv(os.path.join(out, "metrics_by_benchmark.csv"), index=False)

# macro: combine per-benchmark replicates (independent across benchmarks) -------------------------------------
import glob
macro_t = []
benchs = sorted(df.benchmark.unique())
for sp in ("random", "extrap"):
    for n in (20, 50, 100):
        R = {b: np.load(os.path.join(rep, f"_reps_{b}_{sp}_{n}.npz")) for b in benchs if os.path.exists(os.path.join(rep, f"_reps_{b}_{sp}_{n}.npz"))}
        if len(R) < len(benchs): print("macro: missing benchmarks", sp, n, set(benchs) - set(R)); continue
        base = M[(M.split_type == sp) & (M.n == n)]
        for me in HEAD:
            for ref in (B1, B2):
                if me == ref: continue
                r = dict(split_type=sp, n=n, method=me, baseline=ref, n_benchmarks=len(R), B=B)
                for m in ("mae", "rmse", "spearman", "kendall"):
                    if m == "kendall" and not (me in KT and ref in KT): continue
                    reps = np.mean([R[b][f"{me}|{m}"] - R[b][f"{ref}|{m}"] for b in benchs], 0)
                    pt = np.mean([base[(base.benchmark == b) & (base.method == me)][m].iloc[0] - base[(base.benchmark == b) & (base.method == ref)][m].iloc[0] for b in benchs])
                    r[m + "_diff"] = pt; r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(reps, [2.5, 97.5])
                # number of benchmarks whose own target-bootstrap CI excludes 0 in favour of / against the method (MAE)
                sub = Tb[(Tb.split_type == sp) & (Tb.n == n) & (Tb.method == me) & (Tb.baseline == ref)]
                r["n_bench_mae_ci_below0"] = int((sub.mae_diff_hi < 0).sum()); r["n_bench_mae_ci_above0"] = int((sub.mae_diff_lo > 0).sum())
                macro_t.append(r)
pd.DataFrame(macro_t).to_csv(os.path.join(out, "target_bootstrap_macro.csv"), index=False)
# macro ablation: per-benchmark seed-bootstrap replicates (independent resamples per benchmark) averaged over benchmarks
rows = []
for sp in ("random", "extrap"):
    for n in NS:
        a = A[(A.split_type == sp) & (A.n == n)]
        R = {b: np.load(os.path.join(rep, f"seedboot_{b}_{sp}_{n}.npz")) for b in benchs}
        for (me, ref), h in a.groupby(["method", "baseline"]):
            r = dict(split_type=sp, n=n, method=me, baseline=ref, n_benchmarks=len(h))
            for m in ("mae", "rmse", "spearman", "kendall"):
                reps = np.mean([R[b][f"{me}|{ref}|{m}"] for b in benchs], 0)
                r[m + "_diff"] = h[m + "_diff"].mean(); r[m + "_diff_lo"], r[m + "_diff_hi"] = np.percentile(reps, [2.5, 97.5])
            r["n_bench_mae_ci_below0"] = int((h.mae_diff_hi < 0).sum()); r["n_bench_mae_ci_above0"] = int((h.mae_diff_lo > 0).sum())
            rows.append(r)
pd.DataFrame(rows).to_csv(os.path.join(out, "ablation_macro.csv"), index=False)
mm = M.groupby(["split_type", "n", "method"])[["mae", "rmse", "spearman", "kendall"]].mean().reset_index()
mm.to_csv(os.path.join(out, "macro_metrics.csv"), index=False)
print("done")
