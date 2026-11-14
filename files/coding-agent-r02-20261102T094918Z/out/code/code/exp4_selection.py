"""E4: choosing the score geometry from data.  Candidates: Box-Cox/power family + chi2/KL/TV/Aitchison.
Compares (A) naive: select and calibrate on the same data, (B) honest: select on one half, calibrate on the other,
(C) fixed defaults, (O) oracle (population-best).  Writes results/e4_selection.csv"""
import sys, time
import numpy as np, pandas as pd
from joblib import Parallel, delayed
from ccp.geometry import SCORES, make_boxcox
from ccp.synth import SynthProblem
from ccp.conformal import conformal_quantile
from ccp.evalkit import SliceCoverage, MassLookup

ALPHA, N_TOT, M_TEST, N_CENT = 0.1, 1000, 400000, 150
CAND = {"euclid": SCORES["euclid"], "bc0.75": make_boxcox(0.75), "hellinger": SCORES["hellinger"],
        "bc0.25": make_boxcox(0.25), "aitchison": SCORES["aitchison"], "chi2": SCORES["chi2"],
        "kl": SCORES["kl"], "tv": SCORES["tv"]}
NAMES = list(CAND)
R = 30 if "--quick" in sys.argv else 300


def run(fam, D, kappa, ps):
    pr = SynthProblem(D=D, family=fam, kappa=kappa, tau=1.5, seed=ps, mu_floor=0.3 if fam == "additive" else 0.0)
    rng = np.random.default_rng(777 + ps)
    _, mu_t, y_t = pr.sample(M_TEST, rng)
    cov = {n: SliceCoverage(CAND[n](y_t, mu_t), np.zeros(M_TEST, int), 1) for n in NAMES}
    cidx = rng.choice(M_TEST, N_CENT, replace=False)
    ml = MassLookup(mu_t[cidx], CAND, a=1.0, seed=ps)
    # population-oracle: best candidate at its exact population quantile
    pop_q = {n: np.quantile(CAND[n](y_t, mu_t), 1 - ALPHA) for n in NAMES}
    pop_lm = {n: ml.mean_log_mass(n, pop_q[n])[0] for n in NAMES}
    best = min(pop_lm, key=pop_lm.get)
    rows = []
    for r in range(R):
        rr = np.random.default_rng([ps, r, 4])
        _, mu_c, y_c = pr.sample(N_TOT, rr)
        S = {n: CAND[n](y_c, mu_c) for n in NAMES}
        # A: naive
        qA = {n: conformal_quantile(S[n], ALPHA) for n in NAMES}
        lmA = {n: ml.mean_log_mass(n, qA[n])[0] for n in NAMES}
        pickA = min(lmA, key=lmA.get)
        # B: honest split
        h = N_TOT // 2
        qS = {n: conformal_quantile(S[n][:h], ALPHA) for n in NAMES}
        lmS = {n: ml.mean_log_mass(n, qS[n])[0] for n in NAMES}
        pickB = min(lmS, key=lmS.get)
        qB = conformal_quantile(S[pickB][h:], ALPHA)
        res = {"naive": (pickA, qA[pickA]), "honest": (pickB, qB), "oracle": (best, conformal_quantile(S[best], ALPHA))}
        for n in ("euclid", "aitchison", "chi2"):
            res["fixed_" + n] = (n, qA[n])
        for scheme, (pick, q) in res.items():
            rows.append(dict(family=fam, D=D, kappa=kappa, prob=ps, rep=r, scheme=scheme, pick=pick, cov=cov[pick].marginal(q),
                             lm=ml.mean_log_mass(pick, q)[0], pop_best=best, lm_pop_best=pop_lm[best]))
    return rows


if __name__ == "__main__":
    t0 = time.time()
    tasks = [(f, 5, 100, s) for f in ("dirichlet", "logistic_normal", "additive") for s in range(5)]
    tasks += [(f, 10, 300, s) for f in ("dirichlet", "logistic_normal", "additive") for s in range(5)]
    out = Parallel(n_jobs=10)(delayed(run)(*t) for t in tasks)
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv("/work/results/e4_selection%s.csv" % ("_quick" if "--quick" in sys.argv else ""), index=False)
    print("done", time.time() - t0)
