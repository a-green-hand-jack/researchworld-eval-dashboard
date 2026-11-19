"""Fig. 1 (claim C1): one real target on one real board, breadth-depth frontier per rule.

usage: make_fig1.py --results DIR --out DIR [--board helm_mmlu] [--target NAME] [--B 10]

Without --target the target is chosen by a stated rule: among targets with a finite
frontier for all drawn rules, the one whose range of minimum feasible breadth
across the drawn rules is the median over targets. The rule is repeated in the provenance note,
because the figure is an example, not an average (Fig. 2 is the average).
"""
import argparse

import matplotlib.pyplot as plt
import numpy as np

import common
import style

DRAWN = ["mean", "median", "min", "borda", "plurality"]


def pick_target(fr, rules):
    """The target whose range of minimum feasible breadth across the drawn rules is the median over targets
    (neither the most nor the least dramatic example)."""
    ranges = {}
    for t, g in fr.groupby("model"):
        ks = []
        for r in rules:
            f = g[(g.rule == r) & g.feasible.astype(bool)]
            ks.append(f.k.min() if len(f) else np.nan)
        if np.isnan(ks).any():
            continue
        ranges[t] = max(ks) - min(ks)
    order = sorted(ranges, key=lambda t: (ranges[t], t))
    return order[len(order) // 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--board", default="helm_mmlu"); ap.add_argument("--target")
    ap.add_argument("--B", type=float, default=10.0); ap.add_argument("--incumbent", default="own")
    a = ap.parse_args()
    style.apply()
    fr, p = common.load(a.results, "frontier")
    fr = fr[(fr.board == a.board) & (fr.incumbent == a.incumbent) & (np.isclose(fr.B, a.B))]
    rules = [r for r in DRAWN if r in set(fr.rule)]
    target = a.target or pick_target(fr, rules)
    g = fr[fr.model == target]
    m = int(g.k.max())
    fig, ax = plt.subplots(figsize=style.size("full", 0.45))
    for r in rules:
        d = g[(g.rule == r) & g.feasible.astype(bool) & (g.depth > 0)].sort_values("k")
        if d.empty:
            continue
        ax.plot(d.k, d.depth, label=style.RULE_LABEL[r], markevery=max(1, m // 12), **style.RULE_STYLE[r])
    ax.set_xlabel("tasks touched $k$ (breadth)")
    ax.set_ylabel("total boost (points)")
    ax.set_xlim(0, m)
    ax.set_yscale("log")
    ax.legend(ncol=5, loc="upper center", bbox_to_anchor=(0.5, -0.2), columnspacing=0.9, handlelength=1.8)
    ax.set_title(f"{target}, {style.BOARD_LABEL.get(a.board, a.board)}, cap $B={a.B:g}$ points per task", loc="left")
    common.save_fig(fig, a.out, "fig1_teaser", [p],
                    note=f"board={a.board} target={target} B={a.B} incumbent={a.incumbent}; "
                         "target auto-chosen as the median range of minimum feasible breadth across drawn rules, over targets"
                         if not a.target else f"target={target} given")


if __name__ == "__main__":
    main()
