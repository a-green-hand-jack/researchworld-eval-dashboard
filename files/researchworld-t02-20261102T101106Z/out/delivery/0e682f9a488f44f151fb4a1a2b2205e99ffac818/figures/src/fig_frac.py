"""F5 (plan A3): fraction of seeds that generalise within the ceiling (Wilson 95% CI) and t_gen KM median versus training fraction, per width.
python fig_frac.py"""
import numpy as np
import matplotlib.pyplot as plt
import common as C


def main():
    C.style()
    cells = C.all_cells(("main", "frac"))
    if cells.empty: print("no runs"); return
    cells = cells[(cells.arch == "tf") & (cells.op == "add") & (cells.wd == 1.0) & (cells.init_mult == 1.0) & (cells.lr_ref == 0) & (cells.split_seed == -1)]
    fw = set(cells[cells.sweep == "frac"].width)
    cells = cells[cells.width.isin(fw)]
    col = C.width_colors(C.load_runs("main").width.unique())
    ceiling = C.load_runs("main").max_steps.iloc[0]
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 2.4))
    for k, w in enumerate(sorted(fw)):
        c = cells[cells.width == w].sort_values("frac"); off = 1 + 0.012 * (k - 1)
        fr = c.n_grok / c.n
        axs[0].errorbar(c.frac * off, fr, yerr=[fr - c.grok_lo.clip(lower=0), c.grok_hi.clip(upper=1) - fr], fmt="o-", ms=3, lw=0.9, capsize=2, color=col[w], label=f"w={w}")
        fin = np.isfinite(c.tgen_km_median)
        axs[1].plot(c.frac[fin], c.tgen_km_median[fin], "o-", ms=3, lw=0.9, color=col[w], label=f"w={w}")
        for f_, l, h, m in zip(c.frac, c.tgen_lo, c.tgen_hi, c.tgen_km_median):
            if np.isfinite(m) and np.isfinite(l) and np.isfinite(h): axs[1].plot([f_ * off] * 2, [l, h], color=col[w], lw=1.2)
        for f_, m in zip(c.frac, c.tgen_km_median):
            if not np.isfinite(m): axs[1].annotate("", xy=(f_, ceiling * 1.5), xytext=(f_, ceiling), arrowprops=dict(arrowstyle="->", color=col[w], lw=1.0))
    axs[0].set_ylabel(f"fraction grokked by step {int(ceiling)}"); axs[0].set_ylim(-0.03, 1.03); axs[0].set_title("(a) probability of generalising", loc="left", fontsize=7)
    axs[1].set_yscale("log"); C.logfmt(axs[1]); axs[1].set_ylabel("t_gen KM median (steps)"); axs[1].set_title("(b) generalisation time", loc="left", fontsize=7)
    axs[1].axhline(ceiling, color=C.OI["grey"], lw=0.5, ls=":"); axs[1].set_ylim(top=ceiling * 2)
    for ax in axs:
        ax.set_xlabel("training fraction"); tk = sorted(cells.frac.unique()); ax.set_xticks(tk); ax.set_xlim(tk[0] - 0.02, tk[-1] + 0.02)
    axs[0].legend(fontsize=6, loc="upper left")
    grid = "; ".join(f"w={w}: f = " + ", ".join(f"{f:g} (n={int(n)})" for f, n in zip(c.frac, c.n)) for w, c in ((w, cells[cells.width == w].sort_values("frac")) for w in sorted(fw)))
    C.caption("frac", f"Training-set size and width (tf, add mod 53, wd 1, lr 1e-3). Cells run: {grid}; combinations not listed were not run (budget) and are absent, not zero. (a) Fraction of seeds with val acc ≥ 0.99 within the step ceiling, 95% Wilson intervals "
              "(slight horizontal offset between widths). (b) Kaplan–Meier median t_gen with 95% bootstrap CI over all runs; an arrow marks cells in which more than half "
              "of the runs were censored, so the median is only bounded below by the ceiling (dotted).")
    fig.tight_layout()
    C.save(fig, "frac")


if __name__ == "__main__":
    main()
