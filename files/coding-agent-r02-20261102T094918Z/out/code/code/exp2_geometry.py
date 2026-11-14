"""E2: score geometry x noise family x dimension x concentration (oracle predictor yhat = mu(x)).
Writes results/e2_geometry.csv.  Usage: python exp2_geometry.py [--quick]"""
import sys, itertools, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from ccp.geometry import SCORES
from ccp.synth import SynthProblem
from ccp.conformal import conformal_quantile
from ccp.evalkit import SliceCoverage, MassLookup, quantile_bins

ALPHA, N_CAL, M_TEST, N_CENT, N_BINS = 0.1, 1000, 40000, 150, 10
QUICK = "--quick" in sys.argv
N_PROB, R = (2, 20) if QUICK else (5, 100)
if QUICK:
    M_TEST = 10000


def run_task(fam, D, kappa, prob_seed):
    pr = SynthProblem(D=D, family=fam, kappa=kappa, tau=1.5, seed=prob_seed,
                      mu_floor=0.3 if fam == "additive" else 0.0)
    pr.n_fallback = 0
    rng = np.random.default_rng(1000 * prob_seed + 7)
    _, mu_t, y_t = pr.sample(M_TEST, rng)
    names = list(SCORES)
    St = {n: SCORES[n](y_t, mu_t) for n in names}
    conf, lmin = mu_t.max(-1), np.log(mu_t.min(-1))
    b_conf, e_conf = quantile_bins(conf, N_BINS)
    b_min, _ = quantile_bins(lmin, N_BINS)
    cov_conf = {n: SliceCoverage(St[n], b_conf, N_BINS) for n in names}
    cov_min = {n: SliceCoverage(St[n], b_min, N_BINS) for n in names}
    # reference-mass lookup on a random subset of test centres (also needed for the Mondrian bin of each centre)
    cidx = rng.choice(M_TEST, N_CENT, replace=False)
    ml = {a: MassLookup(mu_t[cidx], SCORES, a=a, seed=prob_seed) for a in (1.0, 0.5)}
    cent_bin = b_conf[cidx]
    rows = []
    for r in range(R):
        rr = np.random.default_rng([prob_seed, r, 99])
        _, mu_c, y_c = pr.sample(N_CAL, rr)
        bc, _ = quantile_bins(mu_c.max(-1), N_BINS, edges=e_conf)
        for n in names:
            sc = SCORES[n](y_c, mu_c)
            q = conformal_quantile(sc, ALPHA)
            qm = np.array([conformal_quantile(sc[bc == b], ALPHA) for b in range(N_BINS)])
            for meth, qq, qcent in (("split", q, q), ("mondrian_conf", qm, qm[cent_bin])):
                if meth == "split":
                    cc, cm = cov_conf[n].per_slice(qq), cov_min[n].per_slice(qq)
                    marg = cov_conf[n].marginal(qq)
                else:
                    cc = cov_conf[n].per_slice(qq)
                    marg = (cc * cov_conf[n].sizes).sum() / M_TEST
                    # slices by min-component under Mondrian-by-conf thresholds: threshold of each test point's conf-bin
                    cm = np.array([np.mean(St[n][b_min == b] <= qq[b_conf[b_min == b]]) for b in range(N_BINS)])
                row = dict(family=fam, D=D, kappa=kappa, prob=prob_seed, rep=r, method=meth, score=n,
                           cov=marg,
                           worst_conf=np.abs(cc - (1 - ALPHA)).max(), mag_conf=np.abs(cc - (1 - ALPHA)).mean(),
                           min_conf=cc.min(),
                           worst_min=np.abs(cm - (1 - ALPHA)).max(), mag_min=np.abs(cm - (1 - ALPHA)).mean(),
                           min_min=cm.min())
                for a, key in ((1.0, "lm1"), (0.5, "lm05")):
                    row[key] = ml[a].mean_log_mass(n, qcent)[0]
                rows.append(row)
    assert pr.n_fallback / (M_TEST + R * N_CAL) < 1e-3, "additive sampler fallback too frequent"
    for row in rows:
        row["ess_min"] = min(ml[1.0].ess)
    return rows


if __name__ == "__main__":
    t0 = time.time()
    cells = [(f, D, k) for f in ("dirichlet", "logistic_normal", "additive") for D in (3, 5, 10) for k in (30, 100, 300, 1000)
             if not (f == "additive" and k == 30 and D == 10)]
    tasks = [(f, D, k, s) for (f, D, k) in cells for s in range(N_PROB)]
    out = Parallel(n_jobs=14, verbose=5)(delayed(run_task)(*t) for t in tasks)
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv("/work/results/e2_geometry%s.csv" % ("_quick" if QUICK else ""), index=False)
    print("done", len(df), time.time() - t0)
