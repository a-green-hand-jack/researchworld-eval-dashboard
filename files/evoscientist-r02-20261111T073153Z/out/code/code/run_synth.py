"""Synthetic experiments. Usage: python run_synth.py {main|predq|eps} [R] [nproc]
Writes results/synth_<exp>.csv (one row per replicate x method)."""
import sys, itertools, time
import numpy as np, pandas as pd
from multiprocessing import Pool
from compconf import *

ALPHA = 0.1
EPS_DEFAULT = 1e-3
BASE_SCORES = ["l2", "l1", "linf", "hell", "kl", "ait", "mah", "l2n"]


def run_one(args):
    exp, cfg, rep = args
    dgp, K, n_cal, n_train = cfg["dgp"], cfg["K"], cfg["n_cal"], cfg["n_train"]
    rng = np.random.default_rng(np.random.SeedSequence([20261111, cfg["id"], rep]))
    W = make_world(rng, K)
    n_aux, n_test, n_pool = 500, 1000, 1000
    n = n_train + n_aux + n_cal + n_test + n_pool
    X, Y, _ = gen_data(rng, W, n, dgp, K)
    i0, i1, i2, i3 = n_train, n_train + n_aux, n_train + n_aux + n_cal, n_train + n_aux + n_cal + n_test
    f = fit_softmax_reg(X[:i0], Y[:i0])
    F = f(X)
    Fa, Ya = F[i0:i1], Y[i0:i1]
    Fc, Yc = F[i1:i2], Y[i1:i2]
    Ft, Yt = F[i2:i3], Y[i2:i3]
    pool = Y[i3:]
    unif = rng.dirichlet(np.ones(K), size=4000) if K <= 5 else None
    edges = ent_edges(Fa)
    gc, gt = group_of(Fc, edges), group_of(Ft, edges)

    specs = []  # (method name, score name, eps, mondrian)
    if exp in ("main", "predq"):
        for s in BASE_SCORES:
            specs.append((s, s, EPS_DEFAULT, False))
        specs += [("l2_mond", "l2", EPS_DEFAULT, True), ("ait_mond", "ait", EPS_DEFAULT, True)]
    elif exp == "eps":
        for e in cfg["eps_list"]:
            specs.append((f"ait_eps{e:g}", "ait", e, False))
            specs.append((f"mah_eps{e:g}", "mah", e, False))
        specs += [("l2", "l2", EPS_DEFAULT, False), ("hell", "hell", EPS_DEFAULT, False)]
    rows = []
    for name, sname, eps, mond in specs:
        aux = fit_aux(Ya, Fa, eps)
        sc = Score(sname, K, eps, aux)
        scal = sc.paired(Yc, Fc)
        if mond:
            qt = mondrian_thresholds(scal, gc, gt, ALPHA)
        else:
            qt = np.full(len(Ft), conf_quantile(scal, ALPHA))
        cov, sp, su = evaluate(sc, Ft, Yt, qt, pool, unif)
        row = dict(exp=exp, dgp=dgp, K=K, n_cal=n_cal, n_train=n_train, rep=rep, method=name,
                   cov=cov.mean(), size_pool=sp.mean(), size_unif=np.nan if su is None else su.mean(),
                   q=np.nanmean(np.where(np.isfinite(qt), qt, np.nan)) if np.isfinite(qt).any() else np.inf,
                   q_inf=float(np.mean(~np.isfinite(qt))))
        # size restricted to finite thresholds is handled by size==1 for inf thresholds (whole simplex)
        for k, (c, m) in group_summary(cov, Ft, Yt, edges, K).items():
            row[f"g_{k}_c"], row[f"g_{k}_n"] = c, m
        rows.append(row)
    return rows


def make_jobs(exp, R):
    cfgs = []
    if exp == "main":
        for dgp, K, n_cal in itertools.product(["ln", "ln_het", "dir", "mult"], [3, 5, 10], [50, 200, 1000]):
            cfgs.append(dict(dgp=dgp, K=K, n_cal=n_cal, n_train=1000))
    elif exp == "predq":
        for dgp, n_train in itertools.product(["ln", "ln_het", "dir", "mult"], [30, 100, 300, 3000]):
            cfgs.append(dict(dgp=dgp, K=5, n_cal=200, n_train=n_train))
    elif exp == "eps":
        for dgp in ["ln", "dir", "mult"]:
            cfgs.append(dict(dgp=dgp, K=5, n_cal=200, n_train=1000,
                             eps_list=[1e-8, 1e-6, 1e-4, 1e-3, 1e-2, 5e-2]))
    off = {"main": 0, "predq": 1000, "eps": 2000}[exp]
    for i, c in enumerate(cfgs):
        c["id"] = off + i
    return [(exp, c, r) for c in cfgs for r in range(R)]


if __name__ == "__main__":
    exp = sys.argv[1]
    R = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    nproc = int(sys.argv[3]) if len(sys.argv) > 3 else 32
    jobs = make_jobs(exp, R)
    t = time.time()
    with Pool(nproc) as p:
        res = p.map(run_one, jobs, chunksize=4)
    df = pd.DataFrame([r for rr in res for r in rr])
    import os; df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", f"synth_{exp}.csv"), index=False)
    print(exp, len(jobs), "jobs", df.shape, f"{time.time() - t:.0f}s")
