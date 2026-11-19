"""Synthetic benchmark driver.  usage: python run_bench.py EXP [--R R] [--jobs J]
Experiments: main, ncal, covlaw, shift, mult_N, quick
Writes results/<EXP>.csv (one row per replicate x config x score)."""
import sys, argparse, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from cpcomp import *

SEED0 = 20261102


def get_dgp(name):
    if name.startswith("multN"):
        N = int(name[5:])
        return DGP("mult", N=N, name=name)
    return DGPS[name]()


def one_rep(exp, dgp_name, rep, n_cals, alphas, score_names, full, n_te, shift=0.0, weighted=False,
            extra_scores=(), delta=1e-3):
    rng = np.random.default_rng([SEED0, abs(hash_str(exp + dgp_name)) % 10**6, rep])
    dgp = get_dgp(dgp_name)
    sp = make_split(dgp, rng, n_cal=max(n_cals), n_te=n_te, shift_te=shift)
    pred, H = fit_predictor(sp)
    Z = {k: zfeat(sp[k][0], H[k]) for k in sp}
    scores = make_scores(score_names, delta) + [Aitchison(d) for d in extra_scores]
    rows = []
    for sc in scores:
        sc.fit(H["aux"], sp["aux"][1], Z["aux"])
        s_all = sc(H["cal"], sp["cal"][1], Z["cal"])
        g_all = sc.group(H["cal"], Z["cal"])
        if shift != 0.0:
            s_te = sc(H["te"], sp["te"][1], Z["te"]); g_te = sc.group(H["te"], Z["te"])
        for n in n_cals:
            for ia, alpha in enumerate(alphas):
                if shift == 0.0:
                    q = calibrate(sc, s_all[:n], g_all[:n], alpha)
                    m = evaluate(sc, q, H["te"], sp["te"][1], Z["te"], rng, alpha,
                                 full=(full and ia == 0))
                else:
                    cov_u = s_te <= get_q(calibrate(sc, s_all[:n], g_all[:n], alpha), g_te)
                    w_cal = np.exp(shift * sp["cal"][0][:n, 0] - shift ** 2 / 2)
                    w_te = np.exp(shift * sp["te"][0][:, 0] - shift ** 2 / 2)
                    qw = weighted_thresholds(s_all[:n], w_cal, w_te, alpha)  # (Mondrian not supported)
                    cov_w = s_te <= qw
                    m = dict(cov=cov_u.mean(), cov_w=cov_w.mean())
                    # coverage restricted to the high-noise region x0<-1
                    hi = sp["te"][0][:, 0] < -1.0   # high-noise region (noise precision phi ~ exp(1.2 x0))
                    m.update(cov_hi=cov_u[hi].mean(), cov_w_hi=cov_w[hi].mean())
                m.update(exp=exp, dgp=dgp_name, n_cal=n, alpha=alpha, rep=rep, score=sc.name, shift=shift)
                rows.append(m)
    return rows


def hash_str(s):
    h = 0
    for c in s:
        h = (h * 131 + ord(c)) % 1000003
    return h


def run(jobs_list, jobs):
    res = Parallel(n_jobs=jobs, verbose=0)(delayed(one_rep)(**j) for j in jobs_list)
    return pd.DataFrame([r for rr in res for r in rr])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("exp"); ap.add_argument("--R", type=int, default=300); ap.add_argument("--jobs", type=int, default=36)
    a = ap.parse_args()
    t0 = time.time()
    J = []
    if a.exp == "quick":
        for r in range(a.R):
            J.append(dict(exp="quick", dgp_name="dir_het", rep=r, n_cals=[200], alphas=[0.1], score_names=ALL_SCORES, full=True, n_te=2000))
    if a.exp == "main":   # main benchmark, all DGPs, n_cal in {100,500}, alpha in {.1,.05,.2}
        for d in DGPS:
            for r in range(a.R):
                J.append(dict(exp="main", dgp_name=d, rep=r, n_cals=[100, 500], alphas=[0.1, 0.05, 0.2],
                              score_names=ALL_SCORES, full=True, n_te=4000))
    if a.exp == "ncal":
        for d in ["dir_het", "mult50"]:
            for r in range(a.R):
                J.append(dict(exp="ncal", dgp_name=d, rep=r, n_cals=[30, 50, 100, 200, 500, 1000, 2000], alphas=[0.1],
                              score_names=["L2", "Aitchison", "KL", "L2/sqrtGini", "L2-Mondrian(gini)"], full=False, n_te=4000))
    if a.exp == "covlaw":
        for d in ["dir_het", "mult50"]:
            for r in range(a.R):
                J.append(dict(exp="covlaw", dgp_name=d, rep=r, n_cals=[50, 200, 1000], alphas=[0.1],
                              score_names=ALL_SCORES, full=False, n_te=20000))
    if a.exp == "shift":
        for sh in [0.0, 1.0, -0.5, -1.0, -1.5]:
            for r in range(a.R):
                J.append(dict(exp="shift", dgp_name="dir_het", rep=r, n_cals=[1000], alphas=[0.1], shift=sh,
                              score_names=["L2", "L2/sqrtGini", "L2/learned-sigma", "Aitchison", "KL"], full=False, n_te=4000))
    if a.exp == "mult_N":
        for N in [5, 10, 20, 50, 200, 1000]:
            for r in range(a.R):
                J.append(dict(exp="mult_N", dgp_name=f"multN{N}", rep=r, n_cals=[500], alphas=[0.1],
                              score_names=["L2", "L1", "Hellinger", "KL", "Aitchison", "L2/sqrtGini"], full=True, n_te=4000,
                              extra_scores=(1e-4, 1e-2, 1e-1)))
    df = run(J, a.jobs)
    df.to_csv(f"results/{a.exp}.csv", index=False)
    print(a.exp, df.shape, f"{time.time()-t0:.0f}s")
