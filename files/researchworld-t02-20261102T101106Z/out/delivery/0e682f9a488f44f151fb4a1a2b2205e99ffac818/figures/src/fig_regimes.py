"""F3b: outcome regime per width: counts of seeds by regime (grok = fit then generalise; direct = generalise without a separate fit phase;
memorise-only = fit train but val < 0.99 at ceiling; neither), and final validation accuracy per seed.
Regime labels are experiment-repo's `regime` column. python fig_regimes.py [sweep=main]"""
import sys
import numpy as np
import matplotlib.pyplot as plt
import common as C

ORDER = ["grok", "direct", "memorise-only", "neither"]
COLORS = dict(zip(ORDER, [C.OI["blue"], C.OI["green"], C.OI["orange"], C.OI["verm"]]))


def main(sweep="main"):
    C.style()
    df = C.load_runs(sweep)
    ws = sorted(df.width.unique())
    fig, axs = plt.subplots(1, 2, figsize=(C.TXT_W, 2.4))
    ax = axs[0]
    bottom = np.zeros(len(ws))
    for r in ORDER:
        n = np.array([((df.width == w) & (df.regime == r)).sum() for w in ws])
        if n.sum():
            ax.bar(range(len(ws)), n, bottom=bottom, color=COLORS[r], label=r, width=0.7)
        bottom += n
    ax.set_xticks(range(len(ws))); ax.set_xticklabels(ws); ax.set_xlabel("width (embedding dim.)"); ax.set_ylabel("number of seeds")
    ax.set_title("(a) outcome regime", loc="left"); ax.legend(fontsize=6, loc="upper center", bbox_to_anchor=(0.5, -0.28), ncol=2)
    ax = axs[1]
    rng = np.random.default_rng(3)
    for r in ORDER:
        g = df[df.regime == r]
        idx = [ws.index(w) for w in g.width]
        ax.scatter(np.array(idx) + rng.uniform(-0.18, 0.18, len(g)), g.final_val, s=10, color=COLORS[r], lw=0, zorder=3)
    ax.axhline(0.99, color=C.OI["grey"], lw=0.5, ls=":")
    ax.set_xticks(range(len(ws))); ax.set_xticklabels(ws); ax.set_xlabel("width (embedding dim.)"); ax.set_ylabel("val. accuracy at end of run")
    ax.set_title("(b) final validation accuracy", loc="left"); ax.set_ylim(0, 1.03)
    C.caption(f"regimes_{sweep}", f"Outcome of each run by width ({C.main_setting(df)}). (a) Number of seeds per regime: grok = train acc ≥ 0.99 reached, then val acc ≥ 0.99 later; "
              "direct = val acc ≥ 0.99 without a separate fitting phase; memorise-only = train acc ≥ 0.99 but val acc < 0.99 at the ceiling; neither = train acc < 0.99 at the ceiling "
              "(labels from the analysis position's runs CSV). (b) Validation accuracy at the end of each run (dotted: 0.99); runs that generalise stop 500 steps after t_gen.")
    fig.tight_layout()
    C.save(fig, f"regimes_{sweep}")


if __name__ == "__main__":
    main(*sys.argv[1:])
