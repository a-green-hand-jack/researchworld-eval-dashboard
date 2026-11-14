"""E7: degree-correlated baselines -> failure of the variance law; test a heteroskedastic-harmonic-degree refinement.

Refined plug-in (ignores cross-unit covariance of the exposure regressor):
  Var(tau_hat) ~ [ E r^2 + E[r^2/d] / (E[1/d])^2 ] / (n p (1-p))
where r_i is the residual of the population baseline after removing its mean (fixed finite population).
With homoscedastic r this reduces to sigma^2 (1 + d_H) / (n p (1-p)).
"""
import numpy as np
import pandas as pd
from analysis_lib import *
from gate.core import OutcomeSpec, Population
from gate.graphs import get_graph

reps, gr, cf = load("E7")
m = metrics(reps, cf, boot=False)
rows = []
for _, r in m[m.est == "lin_frac"].iterrows():
    sub = reps[(reps.cid == r.cid) & (reps.est == "lin_frac")]
    spec = OutcomeSpec(deg_coef=r.deg_coef, comm_sd=r.comm_sd)
    vl, vr, ve = [], [], []
    for pop in sorted(sub["pop"].unique()):
        if r.gkind in ("stanford3", "egofb"):
            A, lab = get_graph(r.gkind, K=100 if r.gkind == "stanford3" else 40)
        else:
            A, lab = get_graph(r.gkind, int(r.n_spec), int(r.d_spec), seed=int(r.seed) * 100 + int(pop), K=100, need_labels=True)
        P = Population(A, lab, spec, np.random.default_rng([int(r.seed), pop, 1]))
        d = P.deg
        res = P.base - P.base.mean()
        n = len(d)
        p = 0.5
        s2 = np.mean(res ** 2)
        law = (s2 * (1 + 1 / np.mean(1 / d))) / (n * p * (1 - p))
        refined = (np.mean(res ** 2) + np.mean(res ** 2 / d) / np.mean(1 / d) ** 2) / (n * p * (1 - p))
        vl.append(law); vr.append(refined); ve.append(sub[sub["pop"] == pop].hat.var())
    rows.append(dict(graph=r.gkind, deg_coef=r.deg_coef, sd_emp=np.sqrt(np.mean(ve)), sd_law=np.sqrt(np.mean(vl)), sd_refined=np.sqrt(np.mean(vr)),
                     ratio_law=np.sqrt(np.mean(ve) / np.mean(vl)), ratio_refined=np.sqrt(np.mean(ve) / np.mean(vr)),
                     se_hc=r.se_hc, sd_both=m[(m.cid == r.cid) & (m.est == "lin_both")].sd.iloc[0]))
t = pd.DataFrame(rows)
t.to_csv(os.path.join(TAB, "E7_degdiag.csv"), index=False)
print(t.round(3).to_string())
