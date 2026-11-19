"""F4: scope panels. Delay vs width (KM median + bootstrap CI, per-seed points) for each secondary sweep, on a shared y-axis,
with the main sweep as grey reference. python fig_scope.py [sweep ...]  (default: frac wd mlp mul)"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
import common as C

LABEL = dict(frac="train fraction", wd="weight decay", mlp="MLP architecture", mul="multiplication", lrscale="lr ∝ 1/√width", splitfix="fixed split")


def conds(df, sweep):
    if sweep == "frac": return [(f"f = {f:g}", df[df.frac == f]) for f in sorted(df.frac.unique())]
    if sweep == "wd": return [(f"wd = {w:g}", df[df.wd == w]) for w in sorted(df.wd.unique())]
    return [(LABEL[sweep], df)]


def lr_panel(ax, ceiling):
    """t_gen per seed for lr ∝ 1/sqrt(width) (lrscale: w=32,128 seeds 0-4; lrscale2: w=16,64,256 seeds 0-2) against the fixed-lr main runs of the same seeds;
    KM medians (seeds 0-2, both arms) from sens_lrscale_grid.csv."""
    S = __import__("pandas").concat([C.load_runs("lrscale"), C.load_runs("lrscale2")])
    M = C.load_runs("main")
    keys = set(zip(S.width, S.seed))
    F = M[[k in keys for k in zip(M.width, M.seed)]]
    arms = [(F, C.OI["grey"], 1 / 1.1, "fixed lr (main)"), (S, C.OI["blue"], 1.1, "lr ∝ 1/√width")]
    for d, c, off, lab in arms:
        for k, (w, g) in enumerate(d.groupby("width")):
            y = np.where(g.grokked, g.t_gen, g.steps_run).astype(float)
            x = w * off * np.exp(np.linspace(-0.04, 0.04, len(g)))
            ax.scatter(x[g.grokked.values], y[g.grokked.values], s=9, color=c, lw=0, zorder=3, label=lab if k == 0 else None)
            ax.scatter(x[~g.grokked.values], y[~g.grokked.values], s=16, facecolor="none", edgecolor=c, marker="^", lw=0.8, zorder=3)
    gr = os.path.join(C.RESULTS, "sens_lrscale_grid.csv")
    if os.path.exists(gr):
        G = __import__("pandas").read_csv(gr)
        for (arm, d) in G.groupby("arm"):
            c, off = (C.OI["grey"], 1 / 1.1) if arm.startswith("fixed") else (C.OI["blue"], 1.1)
            d = d.sort_values("width"); fin = np.isfinite(d.tgen_km_median)
            ax.plot(d.width[fin] * off, d.tgen_km_median[fin], color=c, lw=1.0, zorder=2)
            for r in d.itertuples():
                if not np.isfinite(r.tgen_km_median):
                    ax.annotate("", xy=(r.width * off, ceiling * 1.5), xytext=(r.width * off, ceiling), arrowprops=dict(arrowstyle="->", color=c, lw=0.9))
                elif np.isfinite(r.tgen_lo):
                    ax.plot([r.width * off] * 2, [r.tgen_lo, r.tgen_hi if np.isfinite(r.tgen_hi) else ceiling * 1.5], color=c, lw=1.2, zorder=4)
    ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.xaxis.set_minor_locator(plt.NullLocator()); C.logfmt(ax)
    ws = sorted(S.width.unique()); ax.set_xticks(ws); ax.set_xticklabels(ws, fontsize=5, rotation=0)
    ax.axhline(ceiling, color=C.OI["grey"], lw=0.5, ls=":"); ax.set_ylim(1500, ceiling * 2)
    ax.set_xlabel("width"); ax.set_ylabel("t_gen (steps)")
    ax.set_title("lr ∝ 1/√width (n=5 at 32, 128)", loc="left", fontsize=7)
    ax.legend(fontsize=5.5, loc="lower left", frameon=False, borderaxespad=0.1)


def main(*sweeps):
    sweeps = sweeps or ("mlp", "mul", "splitfix")
    C.style()
    main_df, main_cells = C.load_runs("main"), C.load_cells("main")
    avail = [s for s in sweeps if not C.load_runs(s).empty]
    items = [(s, lab, d) for s in avail for lab, d in conds(C.load_runs(s), s)]
    if not items:
        print("no scope sweeps available"); return
    ceiling = main_df.max_steps.iloc[0]
    has_lr = not C.load_runs("lrscale").empty
    ncol = min(4, len(items) + has_lr); nrow = int(np.ceil((len(items) + has_lr) / ncol))
    fig, axs = plt.subplots(nrow, ncol, figsize=(C.TXT_W, 2.0 * nrow + 0.3), squeeze=False)
    for ax in axs.flat[1:len(items)]: ax.sharey(axs.flat[0])
    for ax in axs.flat[1:len(items)]: ax.tick_params(labelleft=False)
    mc = main_cells.sort_values("width")
    for ax in axs.flat[len(items) + has_lr:]: ax.axis("off")
    for ax, (s, lab, d) in zip(axs.flat, items):
        ax.plot(mc.width, mc.delay_km_median.replace(np.inf, np.nan), color=C.OI["grey"], lw=0.8, ls="--", label="main sweep")
        cells = C.load_cells(s)
        keys = [k for k in ("frac", "wd", "arch", "op") if k in d]
        for k in keys: cells = cells[cells[k].isin(d[k].unique())]
        cells = cells.sort_values("width")
        col = C.width_colors(d.width.unique())
        rng = np.random.default_rng(2)
        for w, g in d.groupby("width"):
            x = w * np.exp(rng.uniform(-0.06, 0.06, len(g)))
            ce = ~g.grokked.values
            ax.scatter(x[~ce], g.delay_obs.values[~ce], s=8, color=C.OI["blue"], lw=0, zorder=3)
            ax.scatter(x[ce], g.delay_obs.values[ce], s=14, facecolor="none", edgecolor=C.OI["blue"], marker="^", lw=0.8, zorder=3)
        for w, m, lo, hi in zip(cells.width, cells.delay_km_median, cells.delay_lo, cells.delay_hi):
            if np.isfinite(m): ax.plot([w, w], [lo, hi if np.isfinite(hi) else ceiling], color="k", lw=1.3, zorder=4)
        ax.plot(cells.width, cells.delay_km_median.replace(np.inf, np.nan), color="k", lw=1.0, zorder=2)
        ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.xaxis.set_minor_locator(plt.NullLocator()); C.logfmt(ax)
        ws = sorted(d.width.unique()); ax.set_xticks(ws); ax.set_xticklabels(ws, fontsize=5, rotation=0)
        ax.set_title(lab + f" (n={d.groupby('width').size().min()}/width)", loc="left", fontsize=7)
        ax.axhline(ceiling, color=C.OI["grey"], lw=0.5, ls=":")
        ax.set_xlabel("width")
    if has_lr: lr_panel(axs.flat[len(items)], ceiling)
    axs.flat[0].set_ylabel("delay (steps)")
    axs.flat[0].legend(fontsize=6, loc="best")
    C.caption("scope", "Secondary conditions. (a, b) Delay (t_gen − t_fit, steps) versus width, shared y-axis. Filled: grokked seed; open triangle: right-censored at the step ceiling (dotted). "
              "Black: Kaplan–Meier median with 95% bootstrap CI; dashed grey: main-sweep medians for reference. "
              "(c) Learning rate scaled as lr·sqrt(64/width) (blue) against the fixed-lr main-sweep runs of the same seeds (grey); y-axis is t_gen, not delay, because most scaled-lr runs do not generalise. "
              "Points: seeds 0–4 at widths 32 and 128, seeds 0–2 at widths 16, 64, 256. Lines: Kaplan–Meier median of t_gen over seeds 0–2 in both arms with 95% bootstrap CI (sens_lrscale_grid.csv); "
              "an arrow marks a median that is undefined (at least half the seeds censored at the ceiling). Settings not varied are as in the main sweep.")
    fig.tight_layout()
    C.save(fig, "scope")


if __name__ == "__main__":
    main(*sys.argv[1:])
