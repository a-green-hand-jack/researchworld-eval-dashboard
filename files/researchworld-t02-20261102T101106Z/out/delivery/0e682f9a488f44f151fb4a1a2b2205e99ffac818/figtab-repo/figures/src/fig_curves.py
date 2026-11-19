"""F1: train/val accuracy vs step per width (all seeds thin, seed-median bold). python fig_curves.py [sweep=main]"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import common as C


def main(sweep="main", widths=None):
    C.style()
    df = C.load_runs(sweep)
    ws = sorted(df.width.unique())
    if widths:
        ws = [w for w in ws if w in set(map(int, widths))]
    col = C.width_colors(df.width.unique())
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 2.4), sharey=True)
    for ax, key, title in zip(axs, ["train_acc", "val_acc"], ["(a) training accuracy", "(b) validation accuracy"]):
        for w in ws:
            g = df[df.width == w]
            L = [C.load_log(sweep, f) for f in g.file]
            for log in L:
                ax.plot([r["step"] for r in log], [r[key] for r in log], color=col[w], lw=0.4, alpha=0.35)
            # median over seeds on the common step grid (runs stop at t_gen+extra; held at last value afterwards)
            steps = sorted({r["step"] for log in L for r in log})
            M = np.array([np.interp(steps, [r["step"] for r in log], [r[key] for r in log]) for log in L])
            ax.plot(steps, np.median(M, 0), color=col[w], lw=1.6, label=f"{w}")
        ax.set_xscale("symlog", linthresh=250); ax.set_xlabel("optimiser step"); ax.set_title(title, loc="left")
        ax.set_ylim(-0.02, 1.02)
    axs[0].set_ylabel("accuracy"); axs[1].axhline(0.99, color=C.OI["grey"], lw=0.5, ls=":")
    fig.legend(*axs[1].get_legend_handles_labels(), title="width", ncol=len(ws), loc="upper center", bbox_to_anchor=(0.5, 0.0), fontsize=6, title_fontsize=6)
    C.caption(f"curves_{sweep}", f"Training (a) and validation (b) accuracy versus optimiser step ({C.main_setting(df)}). Thin lines: individual seeds; "
              "bold: median over seeds, colour = width. Runs stop 500 steps after validation accuracy first reaches 0.99; their curves are held at the last logged value. "
              "Dotted line: the 0.99 threshold defining t_gen.")
    fig.tight_layout()
    C.save(fig, f"curves_{sweep}")


if __name__ == "__main__":
    main(*sys.argv[1:2], widths=sys.argv[2:] or None)
