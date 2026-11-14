"""Deterministic-equivalent (Marchenko-Pastur) prediction of the Bayes error of a *random* benchmark subset,
checked by simulation (synthetic data, matched Gaussian factor model with known loadings).

Model: y_j = v_j' u + e_j, v_j ~ N(0, I_r), u ~ N(0, I_r), e_j ~ N(0, s2); S = k random benchmarks.
Bayes (posterior-mean) error on a new benchmark:   s2 + E tr[(I + W/s2)^-1],  W = V_S' V_S ~ Wishart_r(k, I).
With c = r/k, lam = s2/k and m(z) the Stieltjes transform of the Marchenko-Pastur law with ratio c,
    E tr[(I + W/s2)^-1] ~= lam * r * m(-lam),   m(-lam) = [-(lam+1-c) + sqrt((lam+1-c)^2 + 4 c lam)] / (2 c lam)
Limits: k >> r: -> s2 r/k ;   k << r: -> r - k  (unresolved latent directions keep prior variance).
Usage: python code/theory_mp.py   -> results/theory_mp.csv
"""
import numpy as np, pandas as pd


def mp_excess(r, k, s2):
    c, lam = r / k, s2 / k
    b = lam + 1 - c
    m = (-b + np.sqrt(b * b + 4 * c * lam)) / (2 * c * lam)
    return lam * r * m


def sim_excess(r, k, s2, rng, trials=3000):
    out = []
    for _ in range(trials):
        VS = rng.standard_normal((k, r))
        P = np.eye(r) + VS.T @ VS / s2
        out.append(np.trace(np.linalg.inv(P)))
    return float(np.mean(out)), float(np.std(out) / np.sqrt(trials))


if __name__ == "__main__":
    rng = np.random.default_rng(0)
    rows = []
    for r in [5, 10, 20]:
        for s2 in [0.3, 1.0]:
            for k in [1, 2, 3, 5, 8, 12, 20, 40, 80, 160]:
                sim, se = sim_excess(r, k, s2, rng)
                rows.append(dict(r=r, s2=s2, k=k, sim=sim, se=se, mp=mp_excess(r, k, s2), naive=s2 * r / k,
                                 piecewise_naive=min(r - k, s2 * r / k) if k < r else s2 * r / k))
    d = pd.DataFrame(rows)
    d["relerr_mp"] = (d.mp - d.sim).abs() / d.sim
    d["relerr_naive"] = (d.naive - d.sim).abs() / d.sim
    d.to_csv("results/theory_mp.csv", index=False)
    print(d.round(3).to_string())
    print("median rel err  MP: %.3f   naive s2*r/k: %.3f" % (d.relerr_mp.median(), d.relerr_naive.median()))
    print("max rel err (k>=r)  MP: %.3f" % d[d.k >= d.r].relerr_mp.max())
