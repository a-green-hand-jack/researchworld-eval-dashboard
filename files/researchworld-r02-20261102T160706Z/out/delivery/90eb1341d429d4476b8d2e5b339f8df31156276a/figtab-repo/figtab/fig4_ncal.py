"""Fig 4 (claim C4/C6): effect of calibration size n_cal and calibration scheme, E1 (D=5, heteroscedastic, linear predictor, alpha=0.1).
(a) sd over replicates of the test-set coverage vs n_cal against the theory sqrt(Var Beta(k,n+1-k) + .09/n_test) (n_test=2000);
(b) mean region volume (fraction of simplex) vs n_cal for the plain L2 score and its Mondrian / normalised / CV+ variants; 95% CI over replicates.
Input: results/e1/sens_ncal<n>_<family>.csv (n in 30,100,250,2000) and results/e1/main*_<family>_D5_h1_linear.csv (n=500).
"""
import sys
import matplotlib.pyplot as plt
from scipy import stats
from common import *

style()
fams = ["dirichlet", "lognormal"]
ns = [30, 100, 250, 500, 2000]
fig, ax = plt.subplots(2, 2, figsize=(TEXT_W, 3.6), sharex=True)
th = np.array([np.sqrt(stats.beta(int(np.ceil((n + 1) * 0.9)), n + 1 - int(np.ceil((n + 1) * 0.9))).var() + 0.09 / 2000) for n in ns])
for j, fam in enumerate(fams):
    parts = []
    for n in ns:
        if n == 500:
            d = load_e1(f"main*_{fam}_D5_h1_linear.csv")
        else:
            p = os.path.join(EXP, "results", "e1", f"sens_ncal{n}_{fam}.csv")
            d = pd.read_csv(p)
            d["file"] = os.path.basename(p)
        d["n"] = n
        parts.append(d)
    d = pd.concat(parts)
    sd = d[d.method == "l2"].groupby("n").cov10.std().reindex(ns)
    axa = ax[0, j]
    axa.plot(ns, th, "-", color="0.4", lw=0.9, label="theory (Beta + test noise)")
    for m, mk, c in [("l2", "o", SCORE_COL["l2"]), ("hell", "s", SCORE_COL["hell"]), ("ait", "^", SCORE_COL["ait"])]:
        s = d[d.method == m].groupby("n").cov10.std().reindex(ns)
        axa.plot(ns, s, mk, color=c, ms=3.5, mfc="white", label=SCORE_LAB[m] + " (split)")
    axa.set_yscale("log"); axa.set_xscale("log")
    axa.set_title(f"({'ac'[j]}) {fam}", loc="left", fontsize=7.5)
    axa.grid(lw=0.3, color="0.88")
    axb = ax[1, j]
    for m, mk, ls, lab in [("l2", "o", "-", r"$L_2$ split"), ("l2_n", "s", "-", r"$L_2$ normalised"), ("l2_m", "^", "-", r"$L_2$ Mondrian"), ("cvp_l2", "D", "-", r"$L_2$ CV+")]:
        x = d[d.method == m]
        A = agg(x.assign(ncal=x.n), "vol_med", by=("ncal",)).set_index("ncal").sort_index()
        axb.errorbar(A.index, A["mean"], yerr=[A["mean"] - A.lo, A.hi - A["mean"]], fmt=mk + ls, color=SCORE_COL["l2"] if m == "l2" else None,
                     ms=3.5, lw=0.8, capsize=1.5, label=lab, mfc="white" if m == "l2" else None)
    axb.set_xscale("log")
    axb.set_xticks(ns); axb.set_xticklabels(ns); axb.minorticks_off()
    axb.set_xlabel("calibration size $n_{cal}$")
    axb.grid(lw=0.3, color="0.88")
    axb.set_title(f"({'bd'[j]}) {fam}", loc="left", fontsize=7.5)
ax[0, 0].set_ylabel("sd of coverage over reps")
ax[1, 0].set_ylabel("region volume (simplex frac.)")
ax[0, 0].legend(frameon=False, fontsize=6, loc="lower left")
ax[1, 0].legend(frameon=False, fontsize=6, loc="upper right")
fig.tight_layout()
save(fig, "fig4_ncal.pdf")
