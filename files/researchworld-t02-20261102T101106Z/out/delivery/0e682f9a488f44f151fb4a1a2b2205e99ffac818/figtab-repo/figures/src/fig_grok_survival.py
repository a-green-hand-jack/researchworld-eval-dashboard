"""F3: (a) fraction of seeds reaching val acc>=0.99 with Wilson CI vs width (from cells CSV);
(b) Kaplan-Meier curves of t_gen by width (computed here from the runs CSV; unfit runs count as censored at steps_run).
python fig_grok_survival.py [sweep=main]"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import common as C


def main(sweep="main"):
    C.style()
    df, cells = C.load_runs(sweep), C.load_cells(sweep).sort_values("width")
    col = C.width_colors(df.width.unique())
    ceiling = df.max_steps.iloc[0]
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 2.4))
    ax = axs[0]
    fr = cells.n_grok / cells.n
    ax.errorbar(cells.width, fr, yerr=[fr - cells.grok_lo.clip(lower=0), cells.grok_hi.clip(upper=1) - fr], fmt="o-", color="k", ms=3, capsize=2, lw=0.8)
    for w, k, n in zip(cells.width, cells.n_grok, cells.n):
        ax.annotate(f"{k}/{n}", (w, 1.04), ha="center", fontsize=6, annotation_clip=False)
    ax.set_xscale("log", base=2); ax.set_xticks(cells.width); ax.set_xticklabels(cells.width.astype(int)); ax.minorticks_off()
    ax.set_ylim(-0.03, 1.03); ax.set_xlabel("width (embedding dim.)"); ax.set_ylabel(f"fraction grokked by step {int(ceiling)}")
    ax.set_title("(a) fraction generalised (95% Wilson CI)", loc="left", pad=12)
    ax = axs[1]
    for w, g in df.groupby("width"):
        t = np.where(g.grokked, g.t_gen, g.steps_run)
        x, y = C.km_curve(t, g.grokked.values)
        x = np.append(x, ceiling); y = np.append(y, y[-1])
        ax.step(x, y, where="post", color=col[w], label=str(w), lw=1.3)
    ax.set_xlabel("optimiser step"); ax.set_ylabel("P(not yet generalised)"); ax.set_ylim(-0.02, 1.02); ax.set_xlim(0, ceiling)
    ax.set_title("(b) KM survival of t_gen", loc="left", pad=12)
    ax.legend(title="width", ncol=2, fontsize=6, title_fontsize=6, loc="lower left")
    C.caption(f"grok_survival_{sweep}", f"(a) Fraction of seeds whose validation accuracy reached 0.99 within {int(ceiling)} steps, with 95% Wilson intervals (k/n above each point). "
              f"(b) Kaplan–Meier estimate of the probability that a run has not yet generalised, by width ({C.main_setting(df)}); runs that never did are censored at the ceiling, "
              "so curves that end above 0 indicate undetermined t_gen. Widths with no generalising run lie on 1.0 and overlap.")
    fig.tight_layout()
    C.save(fig, f"grok_survival_{sweep}")


if __name__ == "__main__":
    main(*sys.argv[1:])
