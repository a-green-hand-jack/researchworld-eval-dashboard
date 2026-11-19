"""Prop. 2 check with equal cells: E[min_g chat_g] for G cells of m=n_te/G test points each with true coverage c.
exact = (1/m) sum_{j=1..m} prod_g P{Bin(m,c_g) >= j};  mc = Monte Carlo (2e5 draws); normal = c - sqrt(c(1-c)/m) * E[max of G N(0,1)].
Also a heterogeneous example (cells with c_g linearly spaced between c-0.1 and c+0.1, the realistic case).
Output results/tables/prop2_equal_cells.csv"""
import numpy as np, pandas as pd
from scipy.stats import binom, norm
from scipy.integrate import quad

rng = np.random.default_rng(3)


def emax(G):   # E[max of G iid N(0,1)] by quadrature
    return quad(lambda z: G * z * norm.pdf(z) * norm.cdf(z) ** (G - 1), -10, 10)[0]


rows = []
for case in ("equal", "spread"):
    for c0 in (0.9, 0.8):
        for G in (5, 10, 20):
            for nte in (500, 2000, 10000):
                m = nte // G
                c = np.full(G, c0) if case == "equal" else np.linspace(c0 - 0.1, c0 + 0.1, G) if c0 < 0.85 else np.linspace(c0 - 0.05, min(c0 + 0.05, 0.999), G)
                jj = np.arange(1, m + 1)
                ex = np.prod([binom.sf(jj - 1, m, cg) for cg in c], axis=0).sum() / m
                mc = (rng.binomial(m, c, size=(200000, G)) / m).min(1)
                cb = c.mean()
                rows.append(dict(cells=case, c_mean=cb, G=G, n_te=nte, m=m, exact=ex, mc=mc.mean(), mc_se=mc.std() / np.sqrt(len(mc)),
                                 normal=cb - np.sqrt(cb * (1 - cb) / m) * emax(G), true_min=c.min(),
                                 bias_exact=ex - c.min()))
T = pd.DataFrame(rows)
T.to_csv("results/tables/prop2_equal_cells.csv", index=False)
pd.set_option("display.width", 200)
print(T.round(4).to_string())
