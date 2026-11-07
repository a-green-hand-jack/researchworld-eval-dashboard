"""Asymptotic (n -> inf, fixed rho = n/N) width ratio vs PPI++ for each control-variate class and synthetic scenario.

n * Var_asym(m) = Var(Y) - Cov(Y, m)^2 / ((1 + rho) Var(m))   (lambda-tuned, m fixed);  ratio = sqrt(ratio of these).
m = L2 projection of Y on the class, fit on one half of a large population sample, evaluated on the other.
PPI (lambda = 1): Var(Y - f) + rho Var(f)  (in n units); classical: Var(Y).
"""
import os
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np, pandas as pd
from run_synth import make
from civ import LEARNERS, COLS

SC = ["knob0", "knob30", "knob60", "knob90", "calibrated", "monotone_miscal", "nonmonotone", "X_informative", "subgroup_bias", "heavy_tail", "f_noise_X_informative", "pure_noise"]
M = 400_000
rows = []
for sc in SC:
    samp, orc, _ = make(sc)
    rng = np.random.default_rng(0)
    Y, f, X = samp(rng, M)
    Zf = np.column_stack([f, X])
    h = M // 2
    ms = {"oracle": orc(f, X)}
    for L in ["lin_f", "iso_f", "poly_f", "gbm_f", "lin_fX", "gbm_fX"]:
        c = COLS[L]; Zc = Zf if c is None else Zf[:, c]
        m = np.empty(M)
        for a, b in [(slice(0, h), slice(h, M)), (slice(h, M), slice(0, h))]:
            mdl = LEARNERS[L](); mdl.fit(Zc[a], Y[a]); m[b] = mdl.predict(Zc[b])
        ms[L] = m
    def v(m, rho):
        return Y.var() - np.cov(Y, m)[0, 1] ** 2 / ((1 + rho) * m.var()) if m.var() > 0 else Y.var()
    for rho in [1, 0.1, 0.02]:
        base = v(ms["lin_f"], rho)
        r = {"classical": Y.var(), "ppi": (Y - f).var() + rho * f.var(), "ppi++": base, **{k: v(m, rho) for k, m in ms.items()}}
        for k, val in r.items():
            rows.append({"scenario": sc, "rho": rho, "method": {"lin_f": "cf_lin_f", "iso_f": "cf_iso_f", "poly_f": "cf_poly_f", "gbm_f": "cf_gbm_f", "lin_fX": "cf_lin_fX", "gbm_fX": "cf_gbm_fX"}.get(k, k),
                         "asym_width_ratio_vs_ppi++": np.sqrt(val / base)})
# closed form for the knob family: Var(Y) = 2, Var(m) = 1, PPI++ captures cos^2(phi) of Var(m)
for rho in [1, 0.1, 0.02]:
    for ph in [0, 30, 60, 90]:
        rows.append({"scenario": f"knob{ph}", "rho": rho, "method": "closed_form_best",
                     "asym_width_ratio_vs_ppi++": np.sqrt((2 - 1 / (1 + rho)) / (2 - np.cos(np.deg2rad(ph)) ** 2 / (1 + rho)))})
pd.DataFrame(rows).to_csv("../results/theory_synth.csv", index=False)
d = pd.DataFrame(rows).pivot_table(index=["scenario", "rho"], columns="method", values="asym_width_ratio_vs_ppi++")
pd.set_option("display.width", 250); print(d.round(3))
