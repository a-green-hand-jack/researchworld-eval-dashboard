"""Generate all figures (paper/figs/*.pdf) and LaTeX tables (paper/tabs/*.tex) from results/*.
Usage: python code/make_figures.py [fig names ...]   (default: all)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from analysis_lib import *

plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 6.5,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150, "axes.grid": True,
                     "grid.alpha": 0.25, "lines.linewidth": 1.3, "lines.markersize": 3.5})
COL = {"DM": "#7f7f7f", "OLS-f": "#1f77b4", "OLS-s": "#17becf", "OLS-sx": "#9467bd", "OLS-fx": "#2ca02c",
       "OLS-fs": "#bcbd22", "OLS-quad": "#ff7f0e", "OLS-2hop": "#8c564b", "OLS-full": "#e377c2",
       "Oracle": "#d62728", "GBM": "#000000", "Hajek-full": "#aec7e8", "Hajek-eps": "#ffbb78"}
MK = {"DM": "s", "OLS-f": "o", "OLS-fx": "^", "OLS-quad": "v", "Oracle": "D", "GBM": "x", "OLS-fs": "P",
      "OLS-2hop": "<", "OLS-full": ">", "OLS-s": "*", "OLS-sx": "h"}
GATE = 2.0


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def band(ax, x, S, est, key="rmse", **kw):
    g = S[S.est == est].sort_values(x)
    ax.plot(g[x], g[key], color=COL[est], marker=MK.get(est, "o"), label=est, **kw)
    return g


# ------------------------------------------------------------------ Fig: theory vs simulation
def fig_theory():
    T = pd.read_csv(os.path.join(RES, "theory_check.csv"))
    T = T[T.est != "OLS-s"]
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.3))
    cls = {"OLS-f": "OLS-f", "OLS-fx": "OLS-fx", "OLS-quad": "OLS-quad", "Oracle": "Oracle", "OLS-2hop": "OLS-2hop",
           "OLS-full": "OLS-full", "OLS-fs": "OLS-fs", "OLS-sx": "OLS-sx"}
    for est, g in T.groupby("est"):
        ax[0].errorbar(g.bias_pred, g.bias_obs, yerr=1.96 * g.bias_obs_se, fmt=MK.get(est, "o"), color=COL[est],
                       ms=2.2, elinewidth=0.4, alpha=0.6, label=est)
    lim = [-3.2, 3.2]
    ax[0].plot(lim, lim, "k--", lw=0.8)
    ax[0].set_xlim(lim); ax[0].set_ylim(lim)
    ax[0].set_xlabel("predicted bias $\\delta^\\top\\beta^\\star-\\tau$"); ax[0].set_ylabel("simulated bias")
    ax[0].set_title("(a) extrapolation bias"); ax[0].legend(ncol=2, loc="upper left", handlelength=1, columnspacing=0.6)
    # sd: noise-only vs noise+design
    sub = T[T.sd_obs.between(0.0, 6)]
    for est, g in sub.groupby("est"):
        ax[1].plot(g.sd_pred_noise, g.sd_obs, MK.get(est, "o"), color=COL[est], ms=2.2, alpha=0.6)
        ax[2].plot(g.sd_pred_total, g.sd_obs, MK.get(est, "o"), color=COL[est], ms=2.2, alpha=0.6)
    for a, t in zip(ax[1:], ["(b) noise-only $\\sigma^2 D^2/n$", "(c) noise + design variance"]):
        a.plot([0.02, 8], [0.02, 8], "k--", lw=0.8)
        a.set_xscale("log"); a.set_yscale("log"); a.set_xlim(0.02, 8); a.set_ylim(0.02, 8)
        a.set_xlabel("predicted sd"); a.set_ylabel("simulated sd"); a.set_title(t)
    fig.tight_layout()
    save(fig, "fig_theory")


# ------------------------------------------------------------------ Fig: kappa x p
def fig_grid():
    scen, df, pred = load("E2grid")
    S = summarize(df, ["o_kappa", "p", "est"], ci=False)
    T = pd.read_csv(os.path.join(RES, "theory_check.csv"))
    T = T[T.exp == "E2grid"]
    fig, ax = plt.subplots(1, 3, figsize=(7.0, 2.3), gridspec_kw=dict(width_ratios=[1.15, 1, 1]))
    g = S[S.est == "OLS-f"].pivot(index="o_kappa", columns="p", values="bias")
    im = ax[0].imshow(g.values, origin="lower", aspect="auto", cmap="RdBu_r", vmin=-1.5, vmax=1.5)
    ax[0].set_xticks(range(len(g.columns))); ax[0].set_xticklabels(g.columns)
    ax[0].set_yticks(range(len(g.index))); ax[0].set_yticklabels(g.index)
    for i in range(g.shape[0]):
        for j in range(g.shape[1]):
            ax[0].text(j, i, f"{g.values[i, j]:.2f}", ha="center", va="center", fontsize=5.5)
    ax[0].set_xlabel("treatment probability $p$"); ax[0].set_ylabel("exposure curvature $\\kappa$ ($h=f^\\kappa$)")
    ax[0].set_title("(a) bias of OLS-$f$ (GATE=2)"); ax[0].grid(False)
    fig.colorbar(im, ax=ax[0], fraction=0.046, pad=0.02)
    for est in ["OLS-f", "Oracle", "GBM", "OLS-quad"]:
        g = S[(S.est == est) & (S.o_kappa == 4.0)].sort_values("p")
        ax[1].plot(g.p, g.sd, color=COL[est], marker=MK[est], label=est)
        g = S[(S.est == est) & (S.o_kappa == 4.0)].sort_values("p")
        ax[2].plot(g.p, g.rmse, color=COL[est], marker=MK[est], label=est)
    g = S[(S.est == "DM") & (S.o_kappa == 4.0)].sort_values("p")
    ax[2].plot(g.p, g.rmse, color=COL["DM"], marker="s", label="DM")
    ax[1].set_yscale("log"); ax[2].set_yscale("log")
    ax[1].set_title("(b) sd, $\\kappa=4$"); ax[2].set_title("(c) RMSE, $\\kappa=4$")
    for a in ax[1:]:
        a.set_xlabel("treatment probability $p$")
    ax[1].set_ylabel("sd"); ax[2].set_ylabel("RMSE"); ax[2].legend(ncol=2, handlelength=1, columnspacing=0.6)
    fig.tight_layout()
    save(fig, "fig_grid")


# ------------------------------------------------------------------ Fig: degree and sample size
def fig_deg_n():
    scen, df, pred = load("E2deg")
    df["gk"] = df["g_kind"]
    S = summarize(df, ["gk", "o_kappa", "p", "g_d", "est"], ci=False)
    T = pd.read_csv(os.path.join(RES, "theory_check.csv"))
    Td = T[(T.exp == "E2deg") & (T.est == "OLS-f")]
    fig, ax = plt.subplots(1, 4, figsize=(7.2, 2.2))
    # (a) sd vs d, kappa=1, p=.5 (correct specification for OLS-f): prediction sqrt(sigma^2 (1+dH)/(n p (1-p)))
    for gk, ls in [("er", "-"), ("ws", "--")]:
        g = S[(S.gk == gk) & (S.o_kappa == 1) & (S.p == 0.5) & (S.est == "OLS-f")].sort_values("g_d")
        ax[0].plot(g.g_d, g.sd, color=COL["OLS-f"], marker="o", ls=ls, label=f"OLS-f ({gk})")
        t = Td[(Td.g_kind == gk) & (Td.o_kappa == 1) & (Td.p == 0.5)].sort_values("g_d")
        ax[0].plot(t.g_d, t.sd_pred_noise, color="k", ls=":" if gk == "er" else "-.", lw=0.9, label=f"$\\sigma D/\\sqrt{{n}}$ ({gk})")
        g = S[(S.gk == gk) & (S.o_kappa == 1) & (S.p == 0.5) & (S.est == "DM")].sort_values("g_d")
        ax[0].plot(g.g_d, g.sd, color=COL["DM"], marker="s", ls=ls, label=f"DM ({gk})")
    ax[0].set_xscale("log"); ax[0].set_yscale("log"); ax[0].set_xlabel("mean degree $d$"); ax[0].set_ylabel("sd")
    ax[0].set_title("(a) sd vs degree ($\\kappa{=}1$, $p{=}.5$)"); ax[0].legend(handlelength=1.2, ncol=1)
    # (b) bias vs d for kappa=4 and kappa=2,p=.8
    for (kap, p), ls in [((4.0, 0.5), "-"), ((2.0, 0.8), "--")]:
        for est in ["OLS-f", "OLS-quad", "GBM"]:
            g = S[(S.gk == "er") & (S.o_kappa == kap) & (S.p == p) & (S.est == est)].sort_values("g_d")
            ax[1].plot(g.g_d, g.bias, color=COL[est], marker=MK[est], ls=ls, label=f"{est} ($\\kappa{{=}}{kap:g},p{{=}}{p}$)")
    ax[1].axhline(0, color="k", lw=0.6)
    ax[1].set_xscale("log"); ax[1].set_xlabel("mean degree $d$"); ax[1].set_ylabel("bias")
    ax[1].set_title("(b) bias vs degree (ER)"); ax[1].legend(handlelength=1.2, fontsize=5.5)
    # (c) RMSE vs d kappa=4
    for est in ["DM", "OLS-f", "OLS-quad", "Oracle", "GBM"]:
        g = S[(S.gk == "er") & (S.o_kappa == 4.0) & (S.p == 0.5) & (S.est == est)].sort_values("g_d")
        ax[2].plot(g.g_d, g.rmse, color=COL[est], marker=MK[est], label=est)
    ax[2].set_xscale("log"); ax[2].set_yscale("log"); ax[2].set_xlabel("mean degree $d$"); ax[2].set_ylabel("RMSE")
    ax[2].set_title("(c) RMSE vs degree ($\\kappa{=}4$)"); ax[2].legend(handlelength=1.2, ncol=2)
    # (d) n scaling
    scen2, df2, _ = load("E2n")
    S2 = summarize(df2, ["o_kappa", "g_n", "est"], ci=False)
    for kap, ls in [(1.0, "--"), (4.0, "-")]:
        for est in ["OLS-f", "Oracle", "GBM", "DM"]:
            g = S2[(S2.o_kappa == kap) & (S2.est == est)].sort_values("g_n")
            ax[3].plot(g.g_n, g.rmse, color=COL[est], marker=MK[est], ls=ls, label=f"{est}, $\\kappa{{=}}{kap:g}$" if est in ("OLS-f",) else None)
    x = np.array([500, 16000.0])
    ax[3].plot(x, 0.2 * np.sqrt(4000 / x) * 1.0, "k:", lw=0.8, label="$n^{-1/2}$")
    ax[3].set_xscale("log"); ax[3].set_yscale("log"); ax[3].set_xlabel("number of units $n$"); ax[3].set_ylabel("RMSE")
    ax[3].set_title("(d) RMSE vs $n$ (ER, $d{=}20$)"); ax[3].legend(handlelength=1.2)
    fig.tight_layout()
    save(fig, "fig_deg_n")


if __name__ == "__main__":
    names = sys.argv[1:] or [k[4:] for k in list(globals()) if k.startswith("fig_")]
    for n in names:
        globals()["fig_" + n]()
