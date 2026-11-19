"""Fig 4 (claims C1, C2; hypothesis H4): standard deviation of the regression GATE estimate vs n, mean degree d and treatment
probability p, against the reference sqrt(d / (n p (1-p))). (a,b) ER graph, Bernoulli(0.5), linear spillover gamma=1 (e3).
(c) SD relative to p=0.5 vs p (e4, gamma=2, linear). Reference constant C in (a) is fitted once on the OLS_f points (log-LS)."""
import numpy as np
import matplotlib.pyplot as plt
from common import *

DCOL = plt.cm.Blues(np.linspace(0.35, 0.95, 5))


def main():
    style()
    e3 = load("e3"); e3 = e3[(e3.tag == "er") & (e3.est_name == "OLS_f")]
    fig, axs = plt.subplots(1, 3, figsize=(TEXTW, 2.2), gridspec_kw={"width_ratios": [1.15, 1, 1]})
    ax = axs[0]
    ref = np.sqrt(e3.d_nom / e3.n_nom)
    C = float(np.exp(np.mean(np.log(e3.sd / ref))))
    ds = sorted(e3.d_nom.unique())
    for i, dd in enumerate(ds):
        s = e3[e3.d_nom == dd].sort_values("n_nom")
        ax.errorbar(s.n_nom, s.sd, yerr=1.96 * sd_se(s), color=DCOL[i], marker="o", ms=3, elinewidth=0.5, capsize=1, label=f"$d$={dd:g}")
        n = np.array([s.n_nom.min(), s.n_nom.max()])
        ax.plot(n, C * np.sqrt(dd / n), color=DCOL[i], ls=":", lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("number of units $n$"); ax.set_ylabel("SD of estimate")
    ax.set_title(f"dotted: $C\\sqrt{{d/n}}$, $C$={C:.2f}", fontsize=7); ax.legend(fontsize=6, ncol=2, loc="lower left"); panel_label(ax, "(a)")
    ax = axs[1]
    for est, mk in [("OLS_f", "o"), ("OLS_big", "s")]:
        t = load("e3"); t = t[(t.tag == "er") & (t.est_name == est)]
        for i, nn in enumerate(sorted(t.n_nom.unique())):
            s = t[t.n_nom == nn].sort_values("d_nom")
            ax.plot(s.d_nom, s.sd / np.sqrt(s.d_nom / s.n_nom), marker=mk, ms=3, color=plt.cm.Blues(0.35 + 0.15 * i) if est == "OLS_f" else plt.cm.Oranges(0.35 + 0.15 * i),
                    lw=0.8, label=ELAB[est] if i == 0 else None)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("mean degree $d$"); ax.set_ylabel("SD$\\,/\\sqrt{d/n}$")
    ax.set_xticks([5, 10, 20, 40, 80]); ax.get_xaxis().set_major_formatter(plt.ScalarFormatter()); ax.minorticks_off()
    ax.legend(fontsize=6.5); ax.set_title("one line per $n$", fontsize=7); panel_label(ax, "(b)")
    ax = axs[2]
    e4 = load("e4"); e4 = e4[(e4.tag.str.endswith("bern_p")) & (e4.o_kind == "linear") & (e4.est_name == "OLS_f")]
    pp = np.linspace(0.04, 0.55, 100)
    ax.plot(pp, np.sqrt(0.25 / (pp * (1 - pp))), color="k", lw=0.8, ls=":", label="$\\sqrt{0.25/(p(1-p))}$")
    for g in present(GORDER, e4.gname):
        s = e4[e4.gname == g].sort_values("p"); base = s[s.p == 0.5]
        if base.empty:
            continue
        ax.errorbar(s.p, s.sd / base.sd.iloc[0], yerr=1.96 * sd_se(s) / base.sd.iloc[0], color=GCOL[g], marker=GMARK[g], ms=3, elinewidth=0.5, lw=0.9, label=g)
    ax.set_yscale("log"); ax.set_yticks([1, 1.5, 2, 3]); ax.get_yaxis().set_major_formatter(plt.ScalarFormatter()); ax.minorticks_off()
    ax.set_xlabel("treatment probability $p$"); ax.set_ylabel("SD / SD at $p$=0.5"); ax.legend(fontsize=6); panel_label(ax, "(c)")
    fig.tight_layout(w_pad=0.6)
    save(fig, "fig4_variance_scaling")


if __name__ == "__main__":
    main()
