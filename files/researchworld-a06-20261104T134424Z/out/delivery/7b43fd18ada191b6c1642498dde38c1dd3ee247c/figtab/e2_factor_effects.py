"""E2: one-factor-at-a-time effects on the optimism gap (naive report - true score of the selected config), synthetic plan grid.
Input: results/synth_plan_summary.csv, rows f_kind == 'ofat', est_name == 'naive'. Each panel varies one factor, all others at the
reference cell (n=200, K=16, tau=.01, rho=.5, mean acc .3, best-of-K, eps=0, leak=0, no outlier). Bars: 1.96 * MC s.e.; dotted line: reference cell."""
from style import *

REF = dict(f_n=200, f_K=16, f_tau=0.01, f_rho=0.5, f_m=0.3, f_proc="argmax", f_eps=0.0, f_leak=0, f_outlier=0.0)
PANELS = [("f_n", "tuning questions, n", True), ("f_K", "candidates searched, K", True), ("f_tau", r"true spread $\tau$", False),
          ("f_rho", r"config correlation $\rho$", False), ("f_m", "mean accuracy", False),
          ("f_proc", "search procedure", False), ("f_eps", r"generation noise $\epsilon$", False),
          ("f_leak", "demo questions leaked into tuning set", False), ("f_outlier", "outlier-config fraction", False)]
PROC = {"argmax": "best-of-K", "sh": "succ. halving", "sr": "succ. rejects", "greedy": "greedy"}

def main():
    setup(); d = load_plan(); d = d[(d.f_kind == "ofat") & (d.est_name == "naive")]
    ref = d[(d[list(REF)] == pd.Series(REF)).all(axis=1)]
    assert len(ref) == 1, "reference cell missing"
    ref = ref.iloc[0]
    panels = []
    for col, lab, log in PANELS:
        others = [c for c in REF if c != col]
        g = d[(d[others] == pd.Series({c: REF[c] for c in others})).all(axis=1)].sort_values(col)
        if g[col].nunique() >= 2: panels.append((col, lab, log, g))
    nc = 3; nr = -(-len(panels) // nc)
    fig, axs = plt.subplots(nr, nc, figsize=(W, 1.55 * nr), sharey=True, squeeze=False)
    for ax, (col, lab, log, g) in zip(axs.flat, panels):
        x = np.arange(len(g)) if col == "f_proc" else g[col].values
        ax.errorbar(x, 100 * g.bias, yerr=100 * 1.96 * g.bias_se, color=OI[0], marker="o", ls="-" if col != "f_proc" else "none", capsize=1.5, elinewidth=0.7)
        ax.axhline(100 * ref.bias, color="0.4", lw=0.6, ls=":")
        ax.plot([REF[col] if col != "f_proc" else list(g[col]).index("argmax")], [100 * ref.bias], marker="o", mfc="white", mec=OI[1], ms=6, ls="none", zorder=0)
        if col == "f_proc": ax.set_xticks(x); ax.set_xticklabels([PROC[p] for p in g[col]], rotation=30, ha="right")
        elif log: ax.set_xscale("log"); ax.set_xticks(list(g[col])); ax.set_xticklabels([str(int(v)) for v in g[col]], rotation=45)
        else: ax.set_xticks(list(g[col])); ax.set_xticklabels([f"{v:g}" for v in g[col]], rotation=45)
        ax.set_xlabel(lab); ax.set_ylim(bottom=0)
    for ax in axs.flat[len(panels):]: ax.axis("off")
    for r in range(nr): axs[r, 0].set_ylabel("optimism gap (pp)")
    fig.tight_layout()
    save(fig, "e2_factor_effects.pdf")

if __name__ == "__main__":
    main()
