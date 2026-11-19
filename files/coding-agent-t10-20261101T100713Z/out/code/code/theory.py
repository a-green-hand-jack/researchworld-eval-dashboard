"""Population-level headroom quantities (oracle variances) for every real / synthetic population.

For a population P of (Y, F, X) we compute (with 5-fold cross-validated learners on up to 200k points)
  mse_c = E (Y - g_c(Z))^2 for learners c in {lin, iso, linX, gbm};  mu-hat variance = Var(Y) - min_c mse_c
and, for every (n, N), the asymptotic variances
  V_class  = Var(Y)/n
  V_ppi    = Var(Y - F)/n + Var(F)/N                           (lambda = 1)
  V_ppipp  = Var(Y - l F)/n + l^2 Var(F)/N,  l = clip(Cov/(Var(F)(1+n/N)), 0, 1)
  V_lin    = Var(mu)/(n+N) + Var(m_lin) N/(n (n+N)) + E e^2/n   (cross-fitted AIPW, g = best linear in F)
  V_opt    = Var(mu)/(n+N) + E e^2/n                            (AIPW with g = E[Y|Z], efficiency bound)
Output: ../results/theory_pop.csv (population constants).  Variances are then combined in analysis.py.
"""
import os
os.environ.setdefault("OMP_NUM_THREADS", "4")
import numpy as np, pandas as pd, sys
from sklearn.model_selection import KFold
from datasets import REAL, SYNTH, get_pop, learners_for
from methods import make_learner

rng = np.random.default_rng(1)
rows = []
for name in REAL + list(SYNTH):
    pop = get_pop(name)
    if name in SYNTH:
        Y, F, X = pop.draw(rng, 200000)
    else:
        Y, F, X = pop.Y, pop.F, pop.X
        if len(Y) > 200000:
            i = rng.choice(len(Y), 200000, replace=False); Y, F, X = Y[i], F[i], X[i]
    Z = np.c_[F, X] if X.shape[1] else F[:, None]
    r = dict(dataset=name, M=len(Y), varY=Y.var(), varF=F.var(), cov=np.cov(Y, F)[0, 1], meanY=Y.mean(),
             meanF=F.mean(), corr=np.corrcoef(Y, F)[0, 1])
    for l in ["lin", "iso", "linX", "gbm"]:
        if l not in learners_for(pop) and not (l == "gbm"):
            continue
        if l == "gbm" and X.shape[1] == 0:
            continue
        p = np.empty(len(Y))
        for tr, te in KFold(5, shuffle=True, random_state=0).split(Z):
            p[te] = make_learner(l).fit(Z[tr], Y[tr]).predict(Z[te])
        r["mse_" + l] = np.mean((Y - p) ** 2)
    rows.append(r); print(name, {k: round(v, 5) for k, v in r.items() if k != "dataset"}, flush=True)
pd.DataFrame(rows).to_csv("../results/theory_pop.csv", index=False)
