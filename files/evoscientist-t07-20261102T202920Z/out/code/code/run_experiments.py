"""Run one batch of benchmark-prediction experiments.

Usage: python run_experiments.py --out results/main --reps 20 --dim 3 [--benchmarks a,b] [--scen random,top]
                                  [--seed-offset 0] [--procs 36]
Each task = (benchmark, scenario, repetition) -> one npz file with raw predictions for every method/budget.
"""
import argparse, os, sys, time, itertools
import numpy as np
from bp import *

BUDGETS = [10, 25, 50, 100, 200]


def make_split(Y, scen, rng, frac_t=None):
    M = Y.shape[0]
    acc = Y.mean(1)
    if scen == "random":      # i.i.d. model split: 30% of models are targets
        perm = rng.permutation(M); nt = int(round(0.3 * M))
        tg, sr = perm[:nt], perm[nt:]
    elif scen == "top":       # extrapolation: the strongest 20% of models are targets
        nt = int(round(0.2 * M))
        order = np.argsort(-acc, kind="stable")
        tg, sr = order[:nt], order[nt:]
    elif scen == "bottom":    # extrapolation to the weakest 20% (supplementary)
        nt = int(round(0.2 * M))
        order = np.argsort(acc, kind="stable")
        tg, sr = order[:nt], order[nt:]
    else:
        raise ValueError(scen)
    return np.sort(tg), np.sort(sr)


def run_task(args):
    bench, scen, rep, dim, outdir, seed_offset, budgets, scale, dim_p, scale_p = args
    fn = os.path.join(outdir, f"{bench}__{scen}__{rep}.npz")
    if os.path.exists(fn):
        return fn, 0.0
    t0 = time.time()
    bi = BENCHMARKS.index(bench); si = ["random", "top", "bottom"].index(scen)
    seed = seed_offset + 100000 * bi + 1000 * si + rep
    rng = np.random.default_rng(seed)
    Y = load(bench); M, N = Y.shape
    tg, sr = make_split(Y, scen, rng)
    Ysrc, Ytg = Y[sr], Y[tg]
    truth = Ytg.mean(1)
    model, res = fit_latent(Ysrc, dim, seed=seed)
    if (dim_p, scale_p) == (dim, scale):
        model_p = model = model.with_prior_scale(scale)
    else:  # separately tuned configuration for the plug-in family
        model = model.with_prior_scale(scale)
        model_p = fit_latent(Ysrc, dim_p, seed=seed)[0].with_prior_scale(scale_p)
    diff = Ysrc.mean(0)
    P = model.prob_items(model.theta_src)  # in-sample source fit (used only for PPS item weights)
    rsd = np.sqrt(((Ysrc - P) ** 2).mean(0))
    budgets = [n for n in budgets if n <= N // 2]
    preds = {}

    def put(name, bi_, v):
        if name not in preds:
            preds[name] = np.full((len(budgets), len(tg)), np.nan)
        preds[name][bi_] = v

    info_order = info_select(model_p, max(budgets))
    for k, n in enumerate(budgets):
        S_info = np.sort(info_order[:n])
        put("info_plugin", k, est_plugin(model_p, S_info, Ytg[:, S_info]))
        put("info_ht", k, Ytg[:, S_info].mean(1))
        samplers = {
            "rand": sample_random(N, n, rng),
            "sort": sample_sorted(N, n, diff, rng),
            "pps": sample_pps(N, n, rsd, diff, rng),
        }
        for sname, (S, pi) in samplers.items():
            Yt_S = Ytg[:, S]
            put(f"{sname}_ht", k, est_ht_mean(Yt_S, pi[S], N))
            put(f"{sname}_plugin", k, est_plugin(model_p, S, Yt_S))
            d_, g_, beta, sed, seg = est_crossfit(model, S, pi[S], Yt_S, rng)
            put(f"{sname}_diff", k, d_)
            put(f"{sname}_greg", k, g_)
            put(f"{sname}_beta", k, beta)
            put(f"{sname}_se_ht", k, se_ht(Yt_S, pi[S], N))
            put(f"{sname}_se_diff", k, sed)
            put(f"{sname}_se_greg", k, seg)
        for sname in ["rand", "sort"]:
            S = samplers[sname][0]
            put(f"ridge_{sname}", k, est_ridge(Ysrc, S, Ytg[:, S]))
        # anchor points (Vivek et al.-style): correlation-distance k-means, medoids, cluster-size weights
        A, wA = anchor_select(Ysrc, n, seed + 7 * n)
        put("anchor_wmean", k, (Ytg[:, A] * wA).sum(1) / wA.sum())
        put("anchor_plugin", k, est_plugin(model_p, A, Ytg[:, A]))
        put("const_srcmean", k, np.full(len(tg), Ysrc.mean()))
    np.savez_compressed(fn, truth=truth, tg=tg, sr=sr, budgets=np.array(budgets), N=N,
                        src_mean_of_tg=Ysrc.mean(), fit_iters=res.nit, **preds)
    return fn, time.time() - t0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=20)
    ap.add_argument("--dim", type=int, default=3)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--dim-plug", type=int, default=None)
    ap.add_argument("--scale-plug", type=float, default=None)
    ap.add_argument("--benchmarks", default=",".join(BENCHMARKS))
    ap.add_argument("--scen", default="random,top")
    ap.add_argument("--seed-offset", type=int, default=0)
    ap.add_argument("--procs", type=int, default=36)
    ap.add_argument("--budgets", default=",".join(map(str, BUDGETS)))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    budgets = [int(x) for x in a.budgets.split(",")]
    # biggest benchmarks first for load balancing
    benches = sorted(a.benchmarks.split(","), key=lambda b: -os.path.getsize(os.path.join(DATA, b + ".jbl")))
    dp = a.dim_plug or a.dim; sp = a.scale_plug or a.scale
    tasks = [(b, s, r, a.dim, a.out, a.seed_offset, budgets, a.scale, dp, sp)
             for r in range(a.reps) for b in benches for s in a.scen.split(",")]
    tasks.sort(key=lambda t: -os.path.getsize(os.path.join(DATA, t[0] + ".jbl")))
    import multiprocessing as mp
    t0 = time.time()
    with mp.Pool(a.procs) as pool:
        for i, (fn, dt) in enumerate(pool.imap_unordered(run_task, tasks)):
            print(f"[{i+1}/{len(tasks)}] {os.path.basename(fn)} {dt:.0f}s (elapsed {time.time()-t0:.0f}s)", flush=True)
