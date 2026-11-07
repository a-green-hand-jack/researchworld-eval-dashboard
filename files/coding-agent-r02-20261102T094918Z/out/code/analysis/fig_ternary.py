import sys; sys.path.insert(0, "/work/code"); sys.path.insert(0, "/work/analysis")
import numpy as np
from style import *
from ccp.geometry import SCORES
from ccp.synth import SynthProblem

SQ3 = np.sqrt(3) / 2
to2d = lambda Y: np.stack([Y[:, 1] + Y[:, 2] / 2, Y[:, 2] * SQ3], 1)
g = np.linspace(0, 1, 301)
A, B = np.meshgrid(g, g)
m = A + B <= 1
grid = np.stack([1 - A[m] - B[m], A[m], B[m]], 1)
grid = np.clip(grid, 0, 1)
import matplotlib.tri as mtri
xy = to2d(grid)
tri = mtri.Triangulation(xy[:, 0], xy[:, 1])
# drop long triangles (none expected on a convex region)
use = ["euclid", "chi2", "aitchison"]
fig, axes = plt.subplots(1, 2, figsize=(6.4, 3.3))
mus = np.array([[1 / 3, 1 / 3, 1 / 3], [0.6, 0.3, 0.1], [0.08, 0.12, 0.80]])
for ax, fam, title in zip(axes, ["dirichlet", "logistic_normal"], ["Dirichlet noise", "Logistic-normal noise"]):
    pr = SynthProblem(D=3, family=fam, kappa=100, tau=1.5, seed=1)
    rng = np.random.default_rng(0)
    _, mu, y = pr.sample(200000, rng)
    q = {n: np.quantile(SCORES[n](y, mu), 0.9) for n in use}
    ax.plot(*np.array([[0, 0], [1, 0], [0.5, SQ3], [0, 0]]).T, color="#888", lw=0.8)
    for c in mus:
        ys = pr._draw(np.repeat(c[None], 150, 0), rng)
        ax.scatter(*to2d(ys).T, s=1.5, color="#bbbbbb", zorder=1)
        for n in use:
            z = SCORES[n](grid, c[None, :])
            ax.tricontour(tri, z, levels=[q[n]], colors=[COL[n]], linewidths=1.2, zorder=3)
        ax.plot(*to2d(c[None]).T, "k+", ms=5, zorder=4)
    ax.set_aspect("equal"); ax.axis("off"); ax.set_title(title)
    ax.grid(False)
from matplotlib.lines import Line2D
axes[1].legend(handles=[Line2D([], [], color=COL[n], lw=1.5, label=LAB[n]) for n in use], loc="upper right", frameon=False, bbox_to_anchor=(1.12, 1.0))
fig.savefig(FIG + "fig_ternary.pdf")
print("ok")
