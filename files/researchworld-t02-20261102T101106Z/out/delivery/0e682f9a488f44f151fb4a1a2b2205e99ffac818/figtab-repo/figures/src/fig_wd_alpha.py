"""F4 (plan A2): (a) delay D versus weight decay per width (log-log) with the A2 slope -1 as a reference line (a prediction, not a fit);
(b) t_gen versus initialisation scale per width. Cells' medians/CIs come from analyze.py. python fig_wd_alpha.py"""
import numpy as np
import matplotlib.pyplot as plt
import common as C


def cell_plot(ax, runs, cells, xcol, ycol_runs, med, lo, hi, col, xs_label=None, dx=0.05):
    rng = np.random.default_rng(4)
    for w in sorted(cells.width.unique()):
        c = cells[cells.width == w].sort_values(xcol)
        r = runs[runs.width == w]
        for xv, g in r.groupby(xcol):
            y = ycol_runs(g); cens = ~g.grokked.values
            x = xv * np.exp(rng.uniform(-dx, dx, len(g)))
            ax.scatter(x[~cens], y[~cens], s=8, color=col[w], lw=0, zorder=3)
            ax.scatter(x[cens], y[cens], s=14, marker="^", facecolor="none", edgecolor=col[w], lw=0.8, zorder=3)
        fin = np.isfinite(c[med])
        ax.plot(c[xcol][fin], c[med][fin], color=col[w], lw=1.2, marker="_", ms=6, zorder=4, label=f"w={w}")
        for xv, l, h, m in zip(c[xcol], c[lo], c[hi], c[med]):
            if np.isfinite(m) and np.isfinite(l) and np.isfinite(h):
                ax.plot([xv, xv], [l, h], color=col[w], lw=1.2, zorder=4)


def main():
    C.style()
    cells, runs = C.all_cells(("main", "wd", "alpha", "wd0")), C.all_runs(("main", "wd", "alpha", "wd0"))
    if runs.empty or not {"wd", "alpha"} <= set(runs.sweep): print("wd_alpha: wd and alpha sweeps not available yet"); return
    base = dict(arch="tf", op="add", frac=0.4, lr_ref=0, split_seed=-1)
    sel = lambda d: d[np.logical_and.reduce([d[k] == v for k, v in base.items()])]
    cells, runs = sel(cells), sel(runs)
    col = C.width_colors(C.load_runs("main").width.unique())
    ceiling = runs.max_steps.iloc[0]
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 2.5))
    # (a) wd sweep: widths present in the wd sweep, init x1
    wdw = set(runs[runs.sweep == "wd"].width)
    a_cells = cells[(cells.init_mult == 1.0) & (cells.wd > 0) & cells.width.isin(wdw)]
    a_runs = runs[(runs.init_mult == 1.0) & (runs.wd > 0) & runs.fit & runs.width.isin(wdw)]
    ax = axs[0]
    cell_plot(ax, a_runs, a_cells, "wd", lambda g: g.delay_obs.values, "delay_km_median", "delay_lo", "delay_hi", col)
    for w in sorted(wdw):  # A2 prediction D ~ 1/wd, anchored at the wd=1 median of each width
        m = a_cells[(a_cells.width == w) & (a_cells.wd == 1.0)].delay_km_median
        if len(m) and np.isfinite(m.iloc[0]):
            xs = np.array([min(a_runs.wd), max(a_runs.wd)]); ax.plot(xs, m.iloc[0] / xs, color=col[w], lw=0.7, ls="--", zorder=1)
    z = runs[(runs.wd == 0) & (runs.sweep == "wd0")]
    if len(z):
        zc = C.load_cells("wd0").iloc[0]
        ax.text(0.02, 0.03, f"wd = 0 control (width {int(z.width.iloc[0])}): {int(z.grokked.sum())}/{len(z)} \ngeneralised by step {int(z.max_steps.iloc[0])}"
                f"\n(Wilson 95% CI [{max(zc.grok_lo, 0):.2f}, {zc.grok_hi:.2f}])",
                transform=ax.transAxes, fontsize=6, color=C.OI["grey"])
    ax.set_xscale("log"); ax.set_yscale("log"); tk = sorted(a_runs.wd.unique()); ax.set_xticks(tk); ax.set_xticklabels([f"{t:g}" for t in tk]); ax.xaxis.set_minor_locator(plt.NullLocator())
    C.logfmt(ax); ax.set_xlabel("weight decay"); ax.set_ylabel("delay D (steps)"); ax.set_title("(a) delay vs weight decay", loc="left", fontsize=7)
    ax.legend(fontsize=6, loc="upper right")
    # (b) init scale: t_gen over all runs
    aw = set(runs[runs.sweep == "alpha"].width)
    b_cells = cells[(cells.wd == 1.0) & cells.width.isin(aw)]; b_runs = runs[(runs.wd == 1.0) & runs.width.isin(aw)]
    ax = axs[1]
    cell_plot(ax, b_runs, b_cells, "init_mult", lambda g: np.where(g.grokked, g.t_gen, g.steps_run).astype(float), "tgen_km_median", "tgen_lo", "tgen_hi", col, dx=0.04)
    ax.axhline(ceiling, color=C.OI["grey"], lw=0.5, ls=":")
    ax.set_xscale("log", base=2); ax.set_yscale("log"); tk = sorted(b_runs.init_mult.unique()); ax.set_xticks(tk); ax.set_xticklabels([f"{t:g}" for t in tk]); ax.xaxis.set_minor_locator(plt.NullLocator())
    C.logfmt(ax); ax.set_xlabel("initialisation scale multiplier"); ax.set_ylabel("t_gen (steps)"); ax.set_title("(b) t_gen vs initialisation scale", loc="left", fontsize=7)
    ax.legend(fontsize=6, loc="lower right")
    C.caption("wd_alpha", "Mechanism interventions (tf, add mod 53, train fraction 0.4, lr 1e-3). (a) Delay D = t_gen − t_fit versus weight decay at three widths; points: seeds "
              "(open triangles: censored at the ceiling), lines with bars: Kaplan–Meier median with 95% bootstrap CI; dashed: the A2 prediction D ∝ 1/wd anchored at the wd = 1 median "
              "(a reference, not a fit); the wd = 0.5 runs have a 60,000-step ceiling, the others 30,000. Text: the wd = 0 control (grok fraction). (b) t_gen over all runs versus the factor by which all parameters are scaled at initialisation (dotted: step ceiling).")
    fig.tight_layout()
    C.save(fig, "wd_alpha")


if __name__ == "__main__":
    main()
