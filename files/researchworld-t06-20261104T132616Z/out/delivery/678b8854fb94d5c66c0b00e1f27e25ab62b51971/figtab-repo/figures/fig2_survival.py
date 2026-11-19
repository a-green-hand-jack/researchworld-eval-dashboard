"""F2 (claim E2): survival of ranking claims under random perturbation, with the verified adversarial budgets on the same axis.

Reads random_survival.csv and adv_budgets.csv. `--layout row|grid` (default row: one compact row of four panels; grid: 2x2 with a bootstrap panel, for the appendix), `--perturbation remove|flip` (default remove) selects random removal of a
fraction f of the comparisons or random label flips of a fraction f. Writes fig2_survival_<perturbation>.pdf (row) or fig2b_survival_<perturbation>_grid.pdf (grid).
"""
import os
import sys

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import common as C

if "--perturbation" in sys.argv:
    i = sys.argv.index("--perturbation"); PERT = sys.argv[i + 1]; del sys.argv[i:i + 2]
else:
    PERT = "remove"
if "--layout" in sys.argv:
    i = sys.argv.index("--layout"); LAYOUT = sys.argv[i + 1]; del sys.argv[i:i + 2]
else:
    LAYOUT = "row"
A = C.args(__doc__)
C.set_style()
r = C.read(A.results, "random_survival.csv")
adv = C.read(A.results, "adv_budgets.csv")
if PERT == "remove":
    adv = adv[adv.dataset.isin(C.BASE_UNITS) & adv.verified & ~adv.exact_tie]
else:  # adversarial relabelling budgets (additions.csv): the adversary counterpart of random label flips
    adv = C.read(A.results, "additions.csv")
    adv = adv[adv.dataset.isin(C.BASE_UNITS) & adv.flipped_relabel & ~adv.exact_tie].rename(
        columns={"frac_N_relabel": "budget_frac_N", "claim": "claim_id"})

if LAYOUT == "row":
    fig = plt.figure(figsize=(C.TEXTWIDTH, 2.3))
    gs = GridSpec(2, 4, figure=fig, height_ratios=[2.6, 1.0], hspace=0.12, wspace=0.12, left=0.1, right=0.995, top=0.91, bottom=0.27)
    XL = (1.5e-5, 0.8)
    for k, unit in enumerate(C.BASE_UNITS):
        des = C.design_of(unit); col_d = C.DESIGN_COLOR[des]
        ax = fig.add_subplot(gs[0, k], sharey=None if k == 0 else fig.axes[0]); strip = fig.add_subplot(gs[1, k], sharex=ax)
        d = r[(r.dataset == unit) & (r.perturbation == PERT)]
        c1 = d[d.claim_type == "C1"].sort_values("f")
        c2 = d[d.claim_type == "C2"].groupby("f").p_survive.agg(["mean", "min", "max"]).reset_index()
        c3 = d[d.claim_type == "C3"].groupby("f").p_survive.mean().reset_index()
        ax.fill_between(c2.f, c2["min"], c2["max"], color=col_d, alpha=0.15, lw=0)
        ax.plot(c2.f, c2["mean"], "-", color=col_d, lw=1.3, label="C2 adjacent pair: mean (band: min–max over pairs)")
        ax.plot(c3.f, c3.p_survive, "--", color=col_d, lw=1.0, label="C3 top-$k$ set: mean over $k\\in\\{3,5,10\\}$")
        ax.plot(c1.f, c1.p_survive, ":", color=C.INK, lw=1.2, label="C1 top-1")
        ax.set_xscale("log"); ax.set_xlim(*XL); ax.set_ylim(0.1 if PERT == "remove" else 0.0, 1.02)
        ax.tick_params(labelbottom=False)
        ax.set_title(C.SHORT_LABEL[unit], loc="left", color=C.INK, fontsize=7, pad=2)
        if k == 0:
            ax.set_ylabel("P(claim unchanged)", fontsize=7)
        else:
            ax.tick_params(labelleft=False)
        s2 = adv[(adv.dataset == unit) & (adv.claim_type == "C2")]
        strip.plot(s2.budget_frac_N, 1 - (s2["rank"] - 0.5) / s2["rank"].max() * 0.9 - 0.05, C.DESIGN_MARKER[des], color=col_d, ms=2.6, mec="white", mew=0.3, alpha=0.9)
        s1 = adv[(adv.dataset == unit) & (adv.claim_type == "C1")]
        strip.plot(s1.budget_frac_N, [0.5] * len(s1), "*", color=C.INK, ms=5, mec="white", mew=0.3)
        strip.set_ylim(0, 1); strip.set_yticks([]); strip.grid(axis="y", visible=False)
        strip.set_xscale("log"); strip.set_xlim(*XL); strip.set_xticks([1e-4, 1e-3, 1e-2, 1e-1])
        strip.tick_params(labelsize=6)
        if k == 0:
            strip.set_ylabel("adversary", fontsize=6, color=C.MUTED)
        if k == 0:
            h, l = ax.get_legend_handles_labels()
    fig.text(0.54, 0.1, "fraction of comparisons removed" if PERT == "remove" else "fraction of labels flipped", ha="center", fontsize=7)
    fig.legend(h, l, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.01), fontsize=6, columnspacing=1.0, handlelength=1.8)

else:
    fig = plt.figure(figsize=(C.TEXTWIDTH, 5.0))
    gs = GridSpec(5, 5, figure=fig, height_ratios=[3.0, 1.1, 0.35, 3.0, 1.1], width_ratios=[10, 1, 0.35, 10, 1],
                  hspace=0.25, wspace=0.08, left=0.09, right=0.985, top=0.95, bottom=0.2)
    XL = (1.5e-5, 0.8)
    for k, unit in enumerate(C.BASE_UNITS):
        row, col = 3 * (k // 2), 3 * (k % 2)
        des = C.design_of(unit); col_d = C.DESIGN_COLOR[des]
        ax = fig.add_subplot(gs[row, col]); strip = fig.add_subplot(gs[row + 1, col], sharex=ax)
        axb = fig.add_subplot(gs[row, col + 1], sharey=ax)
        d = r[(r.dataset == unit) & (r.perturbation == PERT)]
        c1 = d[d.claim_type == "C1"].sort_values("f")
        c2 = d[d.claim_type == "C2"].groupby("f").p_survive.agg(["mean", "min", "max"]).reset_index()
        c3 = d[d.claim_type == "C3"].groupby("f").p_survive.mean().reset_index()
        ax.fill_between(c2.f, c2["min"], c2["max"], color=col_d, alpha=0.15, lw=0)
        ax.plot(c2.f, c2["mean"], "-", color=col_d, lw=1.4, label="C2 adjacent pair: mean (band: min–max over pairs)")
        ax.plot(c3.f, c3.p_survive, "--", color=col_d, lw=1.1, label="C3 top-$k$ set: mean over $k\\in\\{3,5,10\\}$")
        ax.plot(c1.f, c1.p_survive, ":", color=C.INK, lw=1.3, label="C1 top-1")
        ax.set_xscale("log"); ax.set_xlim(*XL); ax.set_ylim(0.1 if PERT == "remove" else 0.0, 1.02)
        ax.tick_params(labelbottom=False)
        ax.set_title(C.SHORT_LABEL[unit], loc="left", color=C.INK, fontsize=8)
        if col == 0:
            ax.set_ylabel("P(claim unchanged)")
        else:
            ax.tick_params(labelleft=False)
        # bootstrap of the whole data set: separate narrow panel (a resample of all N, not a removal fraction)
        b = r[(r.dataset == unit) & (r.perturbation == "bootstrap")].set_index("claim_type")
        bs = {"C1": b.loc["C1"].p_survive, "C2": b[b.index == "C2"].p_survive.mean(), "C3": b[b.index == "C3"].p_survive.mean()}
        axb.plot([0, 1, 2], [bs["C1"], bs["C2"], bs["C3"]], "o", color=col_d, ms=3)
        axb.set_xticks([0, 1, 2]); axb.set_xticklabels(["C1", "C2", "C3"], fontsize=5.5, rotation=90)
        axb.set_xlim(-0.8, 2.8); axb.tick_params(labelleft=False, labelbottom=False, length=0); axb.grid(False)
        axb.spines["left"].set_visible(False)
        axb.set_title("boot-\nstrap", fontsize=5.5, color=C.MUTED, pad=1.5)
        # adversarial budgets as fractions of N, one dot per claim (C2 pairs; C1 as a diamond)
        s2 = adv[(adv.dataset == unit) & (adv.claim_type == "C2")]
        strip.plot(s2.budget_frac_N, 1 - (s2["rank"] - 0.5) / s2["rank"].max() * 0.9 - 0.05, C.DESIGN_MARKER[des], color=col_d, ms=3, mec="white", mew=0.3, alpha=0.9)
        s1 = adv[(adv.dataset == unit) & (adv.claim_type == "C1")]
        strip.plot(s1.budget_frac_N, [0.5] * len(s1), "*", color=C.INK, ms=6, mec="white", mew=0.3)
        strip.set_ylim(0, 1); strip.set_yticks([]); strip.grid(axis="y", visible=False)
        strip.set_xscale("log"); strip.set_xlim(*XL)
        strip.set_ylabel("adversary\n(rank 1 at top)", fontsize=5.5, color=C.MUTED) if col == 0 else None
        if row == 3:
            strip.set_xlabel("fraction of comparisons removed" if PERT == "remove" else "fraction of labels flipped", fontsize=7)
        if k == 0:
            h, l = ax.get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=1, frameon=False, bbox_to_anchor=(0.5, 0.0), fontsize=6.5)

out = os.path.join(A.out, f"fig2_survival_{PERT}.pdf" if LAYOUT == "row" else f"fig2b_survival_{PERT}_grid.pdf")
fig.savefig(out)
C.record_inputs(A.out, os.path.basename(out), [os.path.join(A.results, "random_survival.csv"), os.path.join(A.results, "adv_budgets.csv" if PERT == "remove" else "additions.csv")])
