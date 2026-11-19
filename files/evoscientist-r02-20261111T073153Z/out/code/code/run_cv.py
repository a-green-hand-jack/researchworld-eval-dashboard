"""Calibration-scheme comparison at equal labelled budget N: split conformal (N/2 fit + N/2 calibrate)
vs. 5-fold cross-conformal (CV+-style, multivariate scores). Usage: python code/run_cv.py [R] [nproc]
Writes results/synth_cv.csv"""
import os, sys, time, itertools
import numpy as np, pandas as pd
from multiprocessing import Pool
from compconf import *

ALPHA, KF, K = 0.1, 5, 5


def run_one(args):
    dgp, N, rep, idx = args
    rng = np.random.default_rng(np.random.SeedSequence([20261113, idx, rep]))
    W = make_world(rng, K)
    n_test, n_pool = 500, 1000
    X, Y, _ = gen_data(rng, W, N + n_test + n_pool, dgp, K)
    Xl, Yl, Xt, Yt, pool = X[:N], Y[:N], X[N:N + n_test], Y[N:N + n_test], Y[N + n_test:]
    unif = rng.dirichlet(np.ones(K), size=2000)
    rows = []
    # ---- split
    h = N // 2
    f = fit_softmax_reg(Xl[:h], Yl[:h])
    Fc, Ft = f(Xl[h:]), f(Xt)
    for s in ["l2", "hell", "ait"]:
        sc = Score(s, K, eps=1e-3)
        q = conf_quantile(sc.paired(Yl[h:], Fc), ALPHA)
        cov, sp, su = evaluate(sc, Ft, Yt, np.full(n_test, q), pool, unif)
        rows.append(dict(dgp=dgp, N=N, rep=rep, scheme="split", method=s, cov=cov.mean(), size_pool=sp.mean(),
                         size_unif=su.mean()))
    # ---- cross-conformal
    fold = rng.permutation(N) % KF
    Fk_t, Rk, ids = [], {s: [] for s in ["l2", "hell", "ait"]}, []
    scs = {s: Score(s, K, eps=1e-3) for s in Rk}
    for k in range(KF):
        tr, ho = fold != k, fold == k
        fk = fit_softmax_reg(Xl[tr], Yl[tr])
        Fk_t.append(fk(Xt))
        Fho = fk(Xl[ho])
        for s, sc in scs.items():
            Rk[s].append(np.sort(sc.paired(Yl[ho], Fho)))
    thr = (1 - ALPHA) * (N + 1)
    for s, sc in scs.items():
        cnt_cov = np.zeros(n_test); cnt_pool = np.zeros((n_test, n_pool)); cnt_unif = np.zeros((n_test, len(unif)))
        for k in range(KF):
            cnt_cov += np.searchsorted(Rk[s][k], sc.paired(Yt, Fk_t[k]), side="left")
            cnt_pool += np.searchsorted(Rk[s][k], sc.pair(Fk_t[k], pool).ravel(), side="left").reshape(n_test, n_pool)
            cnt_unif += np.searchsorted(Rk[s][k], sc.pair(Fk_t[k], unif).ravel(), side="left").reshape(n_test, len(unif))
        rows.append(dict(dgp=dgp, N=N, rep=rep, scheme="cross", method=s, cov=(cnt_cov < thr).mean(),
                         size_pool=(cnt_pool < thr).mean(), size_unif=(cnt_unif < thr).mean()))
    return rows


if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    jobs = [(d, N, r, i) for i, (d, N) in enumerate(itertools.product(["ln", "ln_het", "dir", "mult"], [60, 150, 400]))
            for r in range(R)]
    t = time.time()
    with Pool(nproc) as p:
        res = p.map(run_one, jobs, chunksize=2)
    df = pd.DataFrame([r for rr in res for r in rr])
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "synth_cv.csv"), index=False)
    print(df.shape, f"{time.time() - t:.0f}s")
