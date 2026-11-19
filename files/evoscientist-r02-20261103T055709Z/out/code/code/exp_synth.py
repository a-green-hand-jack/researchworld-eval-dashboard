"""Main synthetic experiment. Usage: python code/exp_synth.py [REPS] [NPROC]
Writes results/synth_raw.csv  (one row per scenario x rep x method x score).
Design: x~N(0,I_5); y|x ~ Dirichlet(kappa(x) m(x)); predictor = soft-label multinomial regression (linear logits).
Scenario grid: K in {3,10}, kappa0 in {3,30,300}, hetero in {0,1} (kappa = kappa0*exp(hetero*x1)), misspec in {0,1}.
Split: n_train=1000 (mean model + sigma-hat), n_cal=500, n_test=1500 (first 500 = reference pool for 'mass' metric, last 1000 evaluated).
"""
import sys, itertools, time
import numpy as np, pandas as pd
from multiprocessing import Pool
sys.path.insert(0, __file__.rsplit("/", 1)[0])
import cp

ALPHA = 0.1
NTR, NCAL, NREF, NEV = 1000, 500, 500, 1000
SCORES = ["l2", "l1", "linf", "hell", "aitch", "kl"]
NB = 5


def pair_scores(f, P, Y, chunk=100):
    out = np.empty((len(P), len(Y)))
    for a in range(0, len(P), chunk):
        out[a:a + chunk] = f(Y[None, :, :], P[a:a + chunk, None, :])
    return out


def one_rep(args):
    sid, K, kappa0, hetero, misspec, rep = args
    rng = np.random.default_rng([sid, rep])
    B, C = cp.scenario_params(K)
    n = NTR + NCAL + NREF + NEV
    x, y, kap = cp.gen_data(rng, n, K, kappa0, hetero, misspec, B=B, C=C)
    tr, cal, ref, ev = np.split(np.arange(n), np.cumsum([NTR, NCAL, NREF]))
    pred = cp.fit_softmax_reg(x[tr], y[tr])
    P = pred(x)
    conf = P.max(1)
    edges = np.quantile(conf[tr], np.linspace(0, 1, NB + 1)[1:-1])
    grp = np.searchsorted(edges, conf, side="right")           # Mondrian groups: predicted-confidence bin
    conf_bins = cp.quantile_bins(conf[ev], NB)                  # evaluation slices (observable)
    x1_bins = cp.quantile_bins(x[ev, 0], NB)                    # evaluation slices (drives kappa)
    rows = []
    base = dict(sid=sid, K=K, kappa0=kappa0, hetero=hetero, misspec=misspec, rep=rep)
    for sc in SCORES:
        f = cp.make_score(sc)
        s_tr = f(y[tr], P[tr]); s_cal = f(y[cal], P[cal]); s_ev = f(y[ev], P[ev])
        sig = cp.fit_logscale(x[tr], s_tr)
        sg_cal, sg_ev = sig(x[cal]), sig(x[ev])
        M = pair_scores(f, P[ev], y[ref])                       # (n_ev, n_ref) scores of reference targets vs each eval prediction
        if K == 3:
            U = rng.dirichlet(np.ones(K), 4000)
            Mu = pair_scores(f, P[ev][:200], U)
        for meth in ["plain", "norm", "mond"]:
            if meth == "plain":
                q = np.full(NEV, cp.conf_quantile(s_cal, ALPHA)); den = np.ones(NEV)
            elif meth == "norm":
                q = np.full(NEV, cp.conf_quantile(s_cal / sg_cal, ALPHA)); den = sg_ev
            else:
                q = cp.mondrian_quantiles(s_cal, grp[cal], grp[ev], ALPHA); den = np.ones(NEV)
            covd = s_ev / den <= q
            inside = M / den[:, None] <= q[:, None]
            r = dict(base, method=meth, score=sc, cov=covd.mean(), mass=inside.mean(),
                     radius=np.median(q), wsc_conf=cp.slice_cov(covd, conf_bins, NB).min(),
                     wsc_x1=cp.slice_cov(covd, x1_bins, NB).min(),
                     maxdev_conf=np.abs(cp.slice_cov(covd, conf_bins, NB) - (1 - ALPHA)).max(),
                     maxdev_x1=np.abs(cp.slice_cov(covd, x1_bins, NB) - (1 - ALPHA)).max())
            r["vol"] = (Mu / den[:200, None] <= q[:200, None]).mean() if K == 3 else np.nan
            rows.append(r)
    return rows


if __name__ == "__main__":
    reps = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    nproc = int(sys.argv[2]) if len(sys.argv) > 2 else 12
    grid = list(itertools.product([3, 10], [3, 30, 300], [0, 1], [0, 1]))
    jobs = [(sid, *g, r) for sid, g in enumerate(grid) for r in range(reps)]
    t0 = time.time()
    with Pool(nproc) as p:
        res = []
        for i, rr in enumerate(p.imap_unordered(one_rep, jobs, chunksize=2)):
            res += rr
            if i % 100 == 0: print(i, len(jobs), f"{time.time()-t0:.0f}s", flush=True)
    pd.DataFrame(res).to_csv("results/synth_raw.csv", index=False)
    print("done", time.time() - t0)
