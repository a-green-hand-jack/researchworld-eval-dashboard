"""Numerical checks of the propositions in the paper.  usage: python code/theory_checks.py
Writes results/theory_*.csv / .json"""
import json, numpy as np, pandas as pd
from math import factorial, log, sqrt
from scipy.special import softmax
from cpcomp import gini, rdirichlet_rows, DGPS

rng = np.random.default_rng(7)
out = {}

# ---------------------------------------------------------------- Prop A: Jacobian of ilr -------
def ilr_basis(K):
    # orthonormal basis of the zero-sum subspace (Helmert)
    V = np.zeros((K - 1, K))
    for i in range(1, K):
        V[i - 1, :i] = 1.0 / i
        V[i - 1, i] = -1.0
        V[i - 1] *= sqrt(i / (i + 1))
    return V

def ilr_from_free(pfree, V):
    p = np.append(pfree, 1 - pfree.sum())
    return V @ np.log(p)

rows = []
for K in [2, 3, 4, 6]:
    V = ilr_basis(K)
    assert np.allclose(V @ V.T, np.eye(K - 1)) and np.allclose(V @ np.ones(K), 0)
    for _ in range(3):
        p = rng.dirichlet(np.ones(K) * 2)
        pf = p[:-1]
        J = np.zeros((K - 1, K - 1)); h = 1e-7
        for j in range(K - 1):
            e = np.zeros(K - 1); e[j] = h
            J[:, j] = (ilr_from_free(pf + e, V) - ilr_from_free(pf - e, V)) / (2 * h)
        rows.append(dict(K=K, det_numeric=abs(np.linalg.det(J)), det_formula=1 / (sqrt(K) * np.prod(p))))
jac = pd.DataFrame(rows); jac["rel_err"] = (jac.det_numeric / jac.det_formula - 1).abs()
jac.to_csv("results/theory_jacobian.csv", index=False)
out["jacobian_max_rel_err"] = float(jac.rel_err.max())

# ------------------------------------- Prop B: Aitchison volume of a Euclid ball diverges -------
# K=3, ball touching the face p1=0.  V_A(ball ∩ {min p >= eps}) grows like  c * log(1/eps).
K = 3
c = np.array([0.06, 0.44, 0.50]); r = 0.20
# predicted coefficient: (1/sqrt(K)) * int_{face section} dp2 / (p2 p3)
g = np.linspace(1e-6, 1 - 1e-6, 2_000_001)
inside = (c[0] ** 2 + (g - c[1]) ** 2 + (1 - g - c[2]) ** 2) <= r ** 2
lo, hi = g[inside].min(), g[inside].max()
gg = g[inside]
coef_pred = float(np.trapezoid(1 / (gg * (1 - gg)), gg) / sqrt(K))
# deterministic quadrature in the free coords (p1,p2), log-spaced in p1
def vol_A(eps, n1=4000, n2=4000):
    # integrate over p1 in [eps, 1] using log-spacing; inner over p2 on a fine grid
    u = np.linspace(np.log(eps), 0, n1)
    p1 = np.exp(u)
    tot = 0.0
    p2g = np.linspace(0, 1, n2)
    vals = []
    for a in p1:
        p2 = p2g * (1 - a)
        p3 = 1 - a - p2
        ok = (p2 > eps) & (p3 > eps) & ((a - c[0]) ** 2 + (p2 - c[1]) ** 2 + (p3 - c[2]) ** 2 <= r ** 2)
        f = np.where(ok, 1.0 / (sqrt(K) * a * np.maximum(p2, 1e-300) * np.maximum(p3, 1e-300)), 0.0)
        vals.append(np.trapezoid(f, p2) * a)  # d p1 = a du
    return float(np.trapezoid(vals, u))
rows = []
for e in [1e-1, 1e-2, 1e-3, 1e-4, 1e-5, 1e-6]:
    rows.append(dict(eps=e, volA=vol_A(e)))
va = pd.DataFrame(rows)
va["increment_per_decade"] = va.volA.diff()
va["predicted_per_decade"] = coef_pred * log(10)
va.to_csv("results/theory_aitchison_volume.csv", index=False)
out["aitchison_volume_coef_pred"] = coef_pred

# ----------- Prop C: E||y-mu||^2 = Gini(mu)/(phi+1) and Gaussian-approx conditional coverage ---------
K = 5
dgp = DGPS["dir_homo"]()
x = dgp.sample_x(rng, 4000)
MU = dgp.mean(x)
G = gini(MU)
edges = np.quantile(G, [0.2, 0.4, 0.6, 0.8]); b = np.searchsorted(edges, G)
rows = []; mom = []
for phi in [3, 10, 20, 100]:
    Y = rdirichlet_rows(rng, MU * phi)
    s2 = ((Y - MU) ** 2).sum(1)
    mom.append(dict(phi=phi, mean_s2_emp=s2.mean(), mean_s2_formula=(G / (phi + 1)).mean()))
    for name, scale in [("L2", np.ones(len(G))), ("L2/sqrtGini", np.sqrt(G))]:
        s = np.sqrt(s2) / scale
        q = np.quantile(s, 0.9)
        # Gaussian approximation: s^2 ~ sum_j lam_j Z_j^2/(phi+1), lam = eig(diag(mu)-mu mu')
        pred = np.zeros(len(G))
        Zs = rng.normal(size=(2000, K))
        for i in range(0, len(G)):
            if i % 4: pred[i] = np.nan; continue    # subsample every 4th point for speed
            S = np.diag(MU[i]) - np.outer(MU[i], MU[i])
            lam = np.clip(np.linalg.eigvalsh(S), 0, None) / (phi + 1)
            sq = (Zs ** 2 * lam).sum(1)
            pred[i] = (np.sqrt(sq) / scale[i] <= q).mean()
        for k in range(5):
            m = b == k
            rows.append(dict(phi=phi, score=name, bin=k, meanG=G[m].mean(),
                             cov_emp=(s[m] <= q).mean(), cov_gauss=np.nanmean(pred[m])))
pd.DataFrame(mom).to_csv("results/theory_gini_moment.csv", index=False)
pd.DataFrame(rows).to_csv("results/theory_gini_cond.csv", index=False)
json.dump(out, open("results/theory_summary.json", "w"), indent=1)
print(out); print(jac.groupby("K").rel_err.max()); print(va); print(pd.DataFrame(mom))
print(pd.DataFrame(rows).round(3).to_string())
