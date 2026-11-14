"""F3 (plan A2 mediation): t_fit and delay D against the weight norm at fit time ||theta_fit|| (value at the first logged step >= t_fit),
per seed, main sweep (circles) plus init-scale interventions (squares). python fig_mechanism.py"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import common as C


def main():
    C.style()
    df = C.all_runs(("main", "alpha"))
    df = df[df.fit & df.wnorm_fit.notna() & (df.arch == "tf") & (df.frac == 0.4) & (df.wd == 1.0) & (df.lr_ref == 0) & (df.split_seed == -1)]
    if df.empty:
        print("no fitted runs"); return
    col = C.width_colors(C.load_runs("main").width.unique())
    ceiling = df.max_steps.iloc[0]
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 2.5))
    for ax, y, title, yl in zip(axs, ("t_fit", "delay_obs"), ("(a) fitting time", "(b) delay D = t_gen − t_fit"), ("t_fit (steps)", "delay (steps)")):
        for (w, a), g in df.groupby(["width", "init_mult"]):
            cens = ~g.grokked.values if y == "delay_obs" else np.zeros(len(g), bool)
            mk = "o" if a == 1.0 else "s"
            ax.scatter(g.wnorm_fit[~cens], g[y][~cens], s=14, marker=mk, color=col[w], lw=0, zorder=3)
            ax.scatter(g.wnorm_fit[cens], g[y][cens], s=18, marker=mk, facecolor="none", edgecolor=col[w], lw=0.8, zorder=3)
        ax.set_xscale("log"); ax.set_yscale("log"); C.logfmt(ax); ax.set_xticks([20, 30, 40, 50]); ax.set_xticklabels(["20", "30", "40", "50"]); ax.xaxis.set_minor_locator(plt.NullLocator())
        ax.set_xlabel("‖θ‖ at t_fit (L2, all parameters)"); ax.set_ylabel(yl); ax.set_title(title, loc="left", fontsize=7)
    axs[1].axhline(ceiling, color=C.OI["grey"], lw=0.5, ls=":")
    hs = [Line2D([], [], marker="o", ls="", color=col[w], ms=3.5, label=f"w={w}") for w in sorted(col) if w in set(df.width)]
    hs += [Line2D([], [], marker="s", ls="", color="grey", ms=3.5, label="init ×0.5 / ×2"),
           Line2D([], [], marker="^", ls="", mfc="none", mec="grey", ms=4, label="delay censored at ceiling")]
    fig.legend(handles=hs, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=4, fontsize=6)
    C.caption("mechanism", "Weight norm at the time the training set is fitted versus (a) t_fit and (b) delay D, one point per run "
              "(tf, add mod 53, train fraction 0.4, wd 1, lr 1e-3; colour = width). Circles: default initialisation; squares: initialisation scaled by 0.5 or 2 "
              "(the interventional control of A2). Open markers in (b): runs not generalised within the ceiling (D right-censored). "
              "Only runs that fitted the training set appear. The regression that tests mediation is in Table 3.")
    fig.tight_layout()
    C.save(fig, "mechanism")


if __name__ == "__main__":
    main()
