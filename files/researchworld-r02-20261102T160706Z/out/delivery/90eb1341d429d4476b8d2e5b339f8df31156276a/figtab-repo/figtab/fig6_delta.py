"""Fig 6 (claim C6): delta-method prediction of pointwise conditional coverage vs simulation, Dirichlet noise, oracle mean predictor.
Input: results/theory/t4_points_<score>_phi<phi>.csv (phi, score, x_id, pred, emp, ...) and t4_cond_coverage.csv (rmse, corr).
Each point is one covariate value x; the dashed line is y=x; marginal coverage is 0.9 by construction.
"""
import glob
import matplotlib.pyplot as plt
from common import *

style()
fs = sorted(glob.glob(os.path.join(EXP, "results", "theory", "t4_points_*.csv")))
d = pd.concat([pd.read_csv(f) for f in fs], ignore_index=True)
s = pd.read_csv(os.path.join(EXP, "results", "theory", "t4_cond_coverage.csv"))
phis = sorted(d.phi.unique(), reverse=True)
scores = ["l2", "hell", "ait", "ait2"]
lo = np.floor(min(d.pred.min(), d.emp.min()) * 20) / 20
fig, ax = plt.subplots(len(phis), 4, figsize=(TEXT_W, 1.25 * len(phis)), sharex=True, sharey=True)
for i, p in enumerate(phis):
    for j, sc in enumerate(scores):
        a = ax[i, j]
        g = d[(d.phi == p) & (d.score == sc)]
        a.plot([lo, 1], [lo, 1], "--", color="0.5", lw=0.7)
        a.plot(g.pred, g.emp, ".", color=SCORE_COL[sc], ms=3, alpha=0.7, mew=0)
        r = s[(s.phi == p) & (s.score == sc)].iloc[0]
        a.text(0.96, 0.05, f"RMSE {r.rmse:.3f}\nmax|err| {r.max_abs:.3f}", transform=a.transAxes, va="bottom", ha="right", fontsize=5.5, bbox=dict(fc="white", ec="none", alpha=0.8, pad=1))
        if i == 0:
            a.set_title(SCORE_LAB[sc], fontsize=7)
        if j == 0:
            a.set_ylabel(rf"$\phi={p:g}$", fontsize=7)
        if i == len(phis) - 1:
            pass
        a.set_xticks([0, 0.5, 1]) if lo < 0.4 else None; a.set_xlim(lo, 1.01); a.set_ylim(lo, 1.01)
        a.grid(lw=0.3, color="0.88")
fig.supxlabel("delta-method predicted conditional coverage", fontsize=7.5)
fig.supylabel("simulated conditional coverage", fontsize=7.5)
save(fig, "fig6_delta_method.pdf")
