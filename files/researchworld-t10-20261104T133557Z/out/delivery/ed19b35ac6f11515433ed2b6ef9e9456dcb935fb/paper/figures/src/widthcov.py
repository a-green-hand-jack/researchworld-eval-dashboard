"""Shared drawing routine: paired width ratio (top) and coverage with Wilson 95% intervals (bottom) vs labeled size n,
one column per dataset/scenario.  Input: experiment-repo summary CSVs (columns dataset|scenario, n, method, reps, coverage,
cov_lo, cov_hi, ratio, ratio_lo, ratio_hi, ratio_lfl, ratio_lfl_lo, ratio_lfl_hi).  Ratio bands: 95% CI of the paired
geometric-mean width ratio over replicates (delta method) -- Monte-Carlo uncertainty only."""
import numpy as np, pandas as pd, matplotlib.pyplot as plt
import style; style.setup()
import matplotlib as mpl

def read(path):
    return pd.read_csv(path, keep_default_na=False, na_values=[""])   # scenario 'null' must not become NaN

def draw(df, out, key, groups, ratio_methods, cov_only=(), ratio_col="ratio_lfl", ylabel="", theory=None, rho=None,
         titles=None, width=1.25, height=3.7, ratio_ticks=None, cov_ylim=(0.80, 1.0), ncol_leg=3, fs=None, ms=3.5):
    ncol = len(groups)
    if fs: mpl.rcParams.update({'font.size': fs, 'axes.titlesize': fs, 'axes.labelsize': fs, 'legend.fontsize': fs - 0.5, 'xtick.labelsize': fs - 1, 'ytick.labelsize': fs - 1})
    fig, axs = plt.subplots(2, ncol, figsize=(style.TEXT_W * width, height), sharey="row", squeeze=False,
                            gridspec_kw={"height_ratios": [1.3, 1]})
    for j, g in enumerate(groups):
        a_w, a_c = axs[0, j], axs[1, j]
        d = df[df[key] == g]
        a_w.axhline(1, color="k", lw=0.8); a_c.axhline(0.95, color="k", lw=0.8)
        for k, m in enumerate(list(ratio_methods) + list(cov_only)):
            lab, colr, mk = style.style_of(m)
            s = d[d.method == m].sort_values("n")
            if s.empty: continue
            ls = "-" if m in ratio_methods else (0, (3, 1.5))
            if m in ratio_methods:
                a_w.plot(s.n, s[ratio_col], marker=mk, color=colr, ms=ms, lw=1, label=lab)
                a_w.fill_between(s.n, s[ratio_col + "_lo"], s[ratio_col + "_hi"], color=colr, alpha=0.2, lw=0)
                if theory is not None:
                    t = theory[(theory.scenario == g) & (theory.method == m) & np.isclose(theory.rho, rho)]
                    if len(t): a_w.axhline(t.iloc[0]["asym_width_ratio_vs_ppi++"], color=colr, ls=(0, (3, 2)), lw=0.7)
            x = s.n * (1 + 0.025 * (k - len(ratio_methods) / 2))
            a_c.errorbar(x, s.coverage, yerr=[s.coverage - s.cov_lo, s.cov_hi - s.coverage], marker=mk, color=colr, ms=ms - 0.3, lw=0.9,
                         ls=ls, elinewidth=0.6, capsize=0, label=lab if m in cov_only else None)
        a_w.set_xscale("log"); a_c.set_xscale("log"); a_w.minorticks_off(); a_c.minorticks_off()
        a_w.set_title(titles(g) if titles else g)
        ns = sorted(d.n.unique())
        a_c.set_xticks(ns); a_c.set_xticklabels([str(int(v)) for v in ns], rotation=0, fontsize=(fs - 1) if fs else 6)
        a_w.set_xticks(ns); a_w.set_xticklabels([])
        a_c.set_xlabel("labeled size $n$")
    lo, hi = axs[0, 0].get_ylim()
    cand = (0.5, 0.6, 0.7, 0.8, 0.9, 1, 1.25, 1.5, 2, 3) if hi > 1.4 else (0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1, 1.05, 1.1, 1.2, 1.3)
    ticks = ratio_ticks or [t for t in cand if lo * 0.99 <= t <= hi * 1.01]
    if not ratio_ticks:  # thin crowded labels: walk outward from 1, keep a tick only if >= 11% of the log axis from the last kept
        span = np.log(hi / lo); keep = [1.0]
        for side in (sorted([t for t in ticks if t > 1]), sorted([t for t in ticks if t < 1], reverse=True)):
            last = 1.0
            for t in side:
                if abs(np.log(t / last)) >= 0.11 * span: keep.append(t); last = t
        ticks = sorted(keep)
    axs[0, 0].set_yticks(ticks); axs[0, 0].set_yticklabels([f"{t:g}" for t in ticks])
    axs[1, 0].set_ylim(*cov_ylim)
    axs[0, 0].set_ylabel(ylabel); axs[1, 0].set_ylabel("coverage")
    handles, labels = {}, []
    for a in axs.flat:
        for h, l in zip(*a.get_legend_handles_labels()): handles.setdefault(l, h)
    if theory is not None:
        from matplotlib.lines import Line2D
        handles["asymptotic prediction"] = Line2D([], [], color="#555555", ls=(0, (3, 2)), lw=0.8)
    fig.legend(list(handles.values()), list(handles), loc="lower center", ncol=ncol_leg, frameon=False, bbox_to_anchor=(0.5, -0.09 if not fs else -0.15), columnspacing=1.0, handlelength=1.6)
    fig.tight_layout()
    fig.savefig(out + ".pdf"); fig.savefig(out + ".png", dpi=200); plt.close(fig)
