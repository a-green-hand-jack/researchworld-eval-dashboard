"""Grid of select-then-report simulations -> aggregated per-cell metrics CSV.

python run_grid.py real <api|local> <model> OUT.csv R
python run_grid.py synth OUT.csv R
"""
import sys, os, time, numpy as np, pandas as pd
from multiprocessing import Pool
import sel_lib as sl
import data_mats as dm
from synth import SynthModel

EST = ["naive", "hold", "cv", "boot", "b632", "eb"]
CI = {"naive": ("naive_lo", "naive_hi"), "hold": ("hold_lo", "hold_hi"), "cv": ("cv_lo", "cv_hi"),
      "boot": ("boot_lo", "boot_hi"), "eb": ("eb_lo", "eb_hi"), "sim": ("sim_lo", "sim_hi")}
G = {}


def init(mode, payload):
    G["mode"] = mode; G["p"] = payload


def cell(args):
    n, Kc, seed, R, extra = args
    rng = np.random.default_rng(seed)
    rows = []
    for r in range(R):
        if G["mode"] == "real":
            rows.append(sl.one_replicate(G["p"], n, Kc, rng))
        else:
            m = G["p"][extra]  # SynthModel
            rows.append(m.replicate(n, Kc, rng))
    df = pd.DataFrame(rows)
    res = dict(n=n, K=Kc, R=R, tag=extra)
    tv = df["truth_var"].values
    res["truth_mean"] = df["truth"].mean(); res["best_truth"] = df["best_truth"].mean(); res["mean_cfg_truth"] = df["mean_truth"].mean()
    for e in EST:
        tr = df["hold_truth"] if e == "hold" else df["truth"]
        tvv = df["hold_truth_var"].values if e == "hold" else tv
        d = df[e] - tr
        res[f"{e}_bias"] = d.mean(); res[f"{e}_bias_se"] = d.std() / np.sqrt(len(d))
        mse = (d ** 2).mean()
        res[f"{e}_rmse"] = np.sqrt(mse); res[f"{e}_rmse_adj"] = np.sqrt(max(0.0, mse - tvv.mean()))
        if e == "cv":
            d2 = df["cv"] - df["cv_proc_truth"]
            res["cv_proc_bias"] = d2.mean()
    for e, (lo, hi) in CI.items():
        if lo not in df: continue
        tr = df["hold_truth"] if e == "hold" else df["truth"]
        tvv = df["hold_truth_var"].values if e == "hold" else tv
        cov = sl.cover(df[lo].values, df[hi].values, tr.values, tvv)
        res[f"{e}_cov"] = cov.mean(); res[f"{e}_width"] = (df[hi] - df[lo]).mean()
    res["sel_gain_over_mean"] = (df["truth"] - df["mean_truth"]).mean()
    res["optimism"] = (df["naive"] - df["truth"]).mean()
    return res


if __name__ == "__main__":
    mode = sys.argv[1]
    nproc = int(os.environ.get("NPROC", 6))
    if mode == "real":
        kind, model, out, R = sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5])
        S, cfgs, _ = dm.api_matrix(model) if kind == "api" else dm.local_matrix(model)
        S = S[:, ~np.isnan(S).any(0)]
        if os.environ.get("TOP"):  # post-hoc 'fine-search' sub-pool: top-T configs by full-pool accuracy
            S = S[np.argsort(-S.mean(1))[: int(os.environ["TOP"])]]
        K, N = S.shape
        print("matrix", S.shape, "mean acc", S.mean(), flush=True)
        ns = [n for n in [25, 50, 100, 200, 400, 800] if n <= N // 2]
        Ks = sorted(set(k for k in [1, 2, 3, 5, 10, 20, K] if k <= K))
        payload = S; extra = model; init("real", payload)
    else:
        out, R = sys.argv[2], int(sys.argv[3])
        from synth import PRESETS
        init("synth", PRESETS)
        ns = [25, 50, 100, 200, 400, 800, 1600]; Ks = [1, 2, 5, 10, 20, 40, 100]
        extra = None
    jobs = []
    seed = 12345
    tags = [extra] if mode == "real" else list(PRESETS.keys())
    for tg in tags:
        for n in ns:
            for Kc in Ks:
                seed += 1; jobs.append((n, Kc, seed, R, tg))
    t0 = time.time()
    with Pool(nproc, initializer=init, initargs=(("real", payload) if mode == "real" else ("synth", PRESETS))) as p:
        res = p.map(cell, jobs, chunksize=1)
    pd.DataFrame(res).to_csv(out, index=False)
    print("done", len(res), "cells", time.time() - t0, "s", flush=True)
