"""Fig. 1: split-conformal prediction regions on the 3-part simplex for four scores (illustration, K=3).
Writes figs/fig_ternary.pdf and results/ternary_q.json"""
import json, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from cpcomp import *

rng = np.random.default_rng(3)
dgp = DGP("dir", het=True, K=3, d=3, phi=15.0, struct_seed=5)
sp = make_split(dgp, rng, n_cal=2000)
pred, H = fit_predictor(sp)
names = ["L2", "KL", "Aitchison", "L2/sqrtGini"]
scores = make_scores(names)
pts = np.array([[1 / 3, 1 / 3, 1 / 3], [0.6, 0.3, 0.1], [0.9, 0.07, 0.03]])
cols = ["tab:blue", "tab:orange", "tab:green"]

def xy(p):
    return np.stack([p[..., 1] + 0.5 * p[..., 2], np.sqrt(3) / 2 * p[..., 2]], -1)

# grid on simplex
n = 400
a, b = np.meshgrid(np.linspace(0, 1, n), np.linspace(0, 1, n))
c = 1 - a - b
m = c >= 0
P = np.stack([a[m], b[m], c[m]], -1)  # (a,b,c) -> comps
P = np.maximum(P, 1e-12); P = P / P.sum(1, keepdims=True)
Q = {}
fig, axs = plt.subplots(1, 4, figsize=(11.5, 3.3))
for ax, sc in zip(axs, scores):
    sc.fit(H["aux"], sp["aux"][1], zfeat(sp["aux"][0], H["aux"]))
    z = zfeat(sp["cal"][0], H["cal"])
    s = sc(H["cal"], sp["cal"][1], z)
    q = calibrate(sc, s, sc.group(H["cal"], z), 0.1)[0]
    Q[sc.name] = float(q)
    tri = np.array([[0, 0], [1, 0], [0.5, np.sqrt(3) / 2], [0, 0]])
    ax.plot(tri[:, 0], tri[:, 1], "k-", lw=0.8)
    for pt, col in zip(pts, cols):
        # the L2/sqrtGini score needs only h; pass dummy z
        sv = sc.raw(pt[None, :], P) / sc.scale(pt[None, :], None)[0] if isinstance(sc, L2Gini) else sc.raw(pt[None, :], P)
        inside = np.zeros((n, n)); inside[m] = (sv <= q)
        X = np.zeros((n, n)); Y = np.zeros((n, n))
        xs = xy(np.stack([a, b, c], -1).clip(0, 1))
        ax.contourf(xs[..., 0], xs[..., 1], np.where(m, inside, 0), levels=[0.5, 1.5], colors=[col], alpha=0.35)
        ax.contour(xs[..., 0], xs[..., 1], np.where(m, inside, 0), levels=[0.5], colors=[col], linewidths=1.2)
        ax.plot(*xy(pt), "o", color=col, ms=4, mec="k", mew=0.5)
    ax.set_title(sc.name, fontsize=10); ax.set_aspect("equal"); ax.axis("off")
plt.tight_layout()
plt.savefig("figs/fig_ternary.pdf", bbox_inches="tight")
json.dump(Q, open("results/ternary_q.json", "w"), indent=1)
print(Q)
