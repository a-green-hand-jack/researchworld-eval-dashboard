"""F1 (plan A1): endpoints versus width at the primary setting. (a) t_gen over ALL runs (primary endpoint, censored at the ceiling),
(b) t_fit, (c) delay D = t_gen - t_fit for runs that fitted the training set. Per-seed points, KM median + bootstrap CI from analyze.py.
python fig_width_trends.py [sweep=main] -> figures/width_trends_<sweep>.{pdf,png}"""
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import common as C


def panel(ax, df, cells, col, ceiling, which, longdf=None):
    rng = np.random.default_rng(1)
    for w, g in df.groupby("width"):
        x = w * np.exp(rng.uniform(-0.07, 0.07, len(g)))
        if which == "tgen":
            y, cens = np.where(g.grokked, g.t_gen, g.steps_run).astype(float), ~g.grokked.values
        elif which == "tfit":
            y, cens = g.t_fit.values, np.zeros(len(g), bool)
        else:
            y, cens = g.delay_obs.values, ~g.grokked.values
        ok = ~np.isnan(y)
        ax.scatter(x[ok & ~cens], y[ok & ~cens], s=9, color=col[w], zorder=3, lw=0)
        ax.scatter(x[ok & cens], y[ok & cens], s=16, facecolor="none", edgecolor=col[w], marker="^", lw=0.8, zorder=3)
    c = cells.sort_values("width")
    m, lo, hi = dict(tgen=(c.tgen_km_median, c.tgen_lo, c.tgen_hi), tfit=(c.tfit_median, c.tfit_lo, c.tfit_hi),
                     delay=(c.delay_km_median, c.delay_lo, c.delay_hi))[which]
    fin = np.isfinite(m)
    ax.plot(c.width[fin], m[fin], color="k", lw=1.0, zorder=2)
    for w, mm, l, h in zip(c.width, m, lo, hi):
        if np.isfinite(mm):
            if np.isfinite(l):
                ax.plot([w, w], [l, h if np.isfinite(h) else ceiling * 1.5], color="k", lw=1.4, zorder=4)
        elif which != "tfit":  # KM median undefined (>half the runs censored): bounded below only
            g = df[df.width == w]
            lb = (np.where(g.grokked, g.t_gen, g.steps_run).max() if which == "tgen" else g.delay_obs.max())  # median exceeds every observed time
            if np.isfinite(lb):
                ax.annotate("", xy=(w, ceiling * 1.5), xytext=(w, lb), arrowprops=dict(arrowstyle="->", color="k", lw=1.0))
    if which == "tgen" and longdf is not None and len(longdf):
        lc = longdf.max_steps.iloc[0]
        for w, g in longdf.groupby("width"):
            y = np.where(g.grokked, g.t_gen, g.steps_run).astype(float)
            x = w * 1.2 * np.exp(np.linspace(-0.05, 0.05, len(g)))
            ax.scatter(x[g.grokked.values], y[g.grokked.values], s=14, marker="D", color="k", zorder=5, lw=0)
            ax.scatter(x[~g.grokked.values], y[~g.grokked.values], s=14, marker="D", facecolor="none", edgecolor="k", lw=0.8, zorder=5)
        ax.axhline(lc, color=C.OI["grey"], lw=0.6, ls="--")
    ax.set_xscale("log", base=2); ax.set_yscale("log")
    ws = sorted(df.width.unique()); ax.set_xticks(ws); ax.set_xticklabels([str(w) for w in ws])
    ax.xaxis.set_minor_locator(plt.NullLocator()); C.logfmt(ax); ax.set_xlabel("width (embedding dim.)"); ax.tick_params(axis="x", labelsize=6)
    if which != "tfit":
        ax.axhline(ceiling, color=C.OI["grey"], lw=0.6, ls=":"); ax.set_ylim(top=(longdf.max_steps.iloc[0] if which == "tgen" and longdf is not None and len(longdf) else ceiling) * 2)


def main(sweep="main"):
    C.style()
    df, cells = C.load_runs(sweep), C.load_cells(sweep)
    longdf = C.load_runs("long") if sweep == "main" else None
    ceiling = df.max_steps.iloc[0]
    col = C.width_colors(df.width.unique())
    fig, axs = plt.subplots(1, 3, figsize=(C.TXT_W, 2.4))
    for ax, which, title, yl in zip(axs, ("tgen", "tfit", "delay"), ("(a) generalisation time t_gen", "(b) fitting time t_fit", "(c) delay D = t_gen − t_fit"),
                                    ("steps until val acc ≥ 0.99", "steps until train acc ≥ 0.99", "steps")):
        panel(ax, df, cells, col, ceiling, which, longdf); ax.set_title(title, loc="left", fontsize=7); ax.set_ylabel(yl)
    st = C.load_stats(sweep)
    aft = next((v for k, v in st.items() if k.endswith("A1_aft_slope")), None)
    if aft:
        axs[0].axvspan(min(df.width) / 1.2, aft["w_min"] / 1.2, color="#eeeeee", zorder=0, lw=0)
        aft_txt = (f"AFT slope of log t_gen on log2 width, w ≥ {aft['w_min']} (unshaded): {aft['slope_log_tgen_per_log2_width']:.2f} "
                   f"[{aft['ci95'][0]:.2f}, {aft['ci95'][1]:.2f}] per doubling")
    h = [Line2D([], [], marker="o", ls="", color="grey", ms=3, label="seed"),
         Line2D([], [], marker="^", ls="", mfc="none", mec="grey", ms=4, label="censored at ceiling (dotted)"),
         Line2D([], [], color="k", lw=1.4, label="KM median, 95% CI"),
         Line2D([], [], marker="$\u2191$", ls="", color="k", ms=5, label="median undefined (>½ censored)")]
    if longdf is not None and len(longdf):
        h += [Line2D([], [], marker="D", ls="", color="k", ms=3, label="seed re-run to 100k (dashed)"),
              Line2D([], [], marker="D", ls="", mfc="none", mec="k", ms=3, label="not generalised at 100k")]
    if aft:
        axs[0].text(0.03, 0.03, f"AFT slope, w ≥ {aft['w_min']}:\n{aft['slope_log_tgen_per_log2_width']:.2f} [{aft['ci95'][0]:.2f}, {aft['ci95'][1]:.2f}]\nper doubling",
                    transform=axs[0].transAxes, fontsize=5.5, va="bottom")
    fig.legend(handles=h, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=6)
    n = df.groupby("width").size(); nf = df[df.fit].groupby("width").size()
    C.caption(f"width_trends_{sweep}", f"Timing versus width ({C.main_setting(df)}; n = {C.nrange(n)} seeds per width). (a) t_gen over all runs; "
              "runs that had not generalised within the ceiling are right-censored (open triangles, plotted at the ceiling) and kept in the estimate. "
              f"(b) t_fit and (c) D = t_gen − t_fit exist only for runs that reach train acc ≥ 0.99 (n = {C.nrange(nf)} per width), so the panels may "
              "contain fewer seeds than (a); runs that never fit are shown in the regime figure. t = first logged step (interval 250) at accuracy ≥ 0.99. "
              "Black: Kaplan–Meier median over seeds with 95% percentile-bootstrap CI (analyze.py); a bar to the top of the panel means the upper limit is undefined, an arrow that the median itself is undefined (more than half the runs censored). "
              "Text in (a): censoring-aware lognormal AFT slope of log t_gen on log2 width over widths ≥ w_min (the smallest width at which ≥ 80% of seeds fit the training set); "
              "shaded: widths below w_min, excluded from the slope. "
              "Diamonds in (a): the same seeds 0–2 at widths 16 and 32 re-run to a 100,000-step ceiling (dashed); the 30,000-step ceiling there is a lower bound on t_gen, not evidence of non-generalisation.")
    fig.tight_layout()
    C.save(fig, f"width_trends_{sweep}")


if __name__ == "__main__":
    main(*sys.argv[1:])
