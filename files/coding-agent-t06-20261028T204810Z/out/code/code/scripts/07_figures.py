"""All paper figures (paper/figs/*.pdf) from results/*."""
import json, os, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from lbstab import data as D

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
RES = os.path.join(ROOT, "results")
FIG = os.path.join(ROOT, "paper", "figs")
os.makedirs(FIG, exist_ok=True)

# validated categorical slots (dataviz reference palette; first three pass all-pairs
# CVD checks); sports folds to neutral ink with a distinct marker
COL = {"crowd": "#2a78d6", "expert": "#eb6834", "llm-judge": "#1baf7a", "sports": "#52514e"}
MRK = {"crowd": "o", "expert": "s", "llm-judge": "^", "sports": "x"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 8, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.5, "legend.frameon": False,
                     "pdf.fonttype": 42, "lines.linewidth": 1.5})

R = pd.read_parquet(os.path.join(RES, "all_pairs.parquet"))
P = R[(R.z > 0.25) & np.isfinite(R.k_drop) & (R.k_drop >= 1)].copy()


def fig_collapse():
    fig, axes = plt.subplots(1, 3, figsize=(7.0, 2.4))
    order = ["sports", "crowd", "llm-judge", "expert"]
    ax = axes[0]
    for d in order:
        q = P[P.design == d]
        ax.scatter(q.z, 100 * q.k_drop / q.N, s=3 if d != "expert" else 10, c=COL[d], marker=MRK[d],
                   alpha=0.35 if d in ("crowd", "sports") else 0.8, lw=0.6 if d == "sports" else 0,
                   label=d, rasterized=True)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("standardised gap $z$ (sandwich SE)")
    ax.set_ylabel("deletions needed (% of data)")
    ax.set_title("(a) fraction of data vs. $z$", fontsize=8, loc="left")
    for kk, (ax, kind, lab) in enumerate([(axes[1], "drop", "deletions"), (axes[2], "inject", "injections")]):
        for d in order:
            q = P[(P.design == d) & np.isfinite(P[f"k_{kind}"])]
            ax.scatter(q.z * np.sqrt(q.nh), q[f"k_{kind}"], s=3 if d != "expert" else 10, c=COL[d], marker=MRK[d],
                       alpha=0.35 if d in ("crowd", "sports") else 0.8, lw=0.6 if d == "sports" else 0,
                       rasterized=True)
        xx = np.logspace(-0.5, 4.2, 10)
        ax.plot(xx, xx, color=INK, lw=1, ls="--")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel(r"$z\sqrt{n_h}$")
        ax.set_ylabel(f"{lab} needed (count)")
        ax.set_title(f"({'bc'[kk]}) {lab} vs. $z\\sqrt{{n_h}}$", fontsize=8, loc="left")
        ax.text(0.04, 0.93, "dashed: $k=z\\sqrt{n_h}$", transform=ax.transAxes, fontsize=7, color=INK2)
    h = [plt.Line2D([], [], ls="", marker=MRK[d], color=COL[d], markersize=5, mew=1) for d in order]
    fig.legend(h, order, loc="upper center", ncol=4, bbox_to_anchor=(0.5, 1.04), fontsize=7.5)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(os.path.join(FIG, "collapse.pdf"), dpi=300)
    plt.close(fig)


def fig_random():
    sets = [("arena140k", "Arena-140k"), ("webdev10k", "WebDev-10k"), ("mtbench_human", "MT-Bench (experts)"), ("nba2015", "NBA 2014-15")]
    sets = [s for s in sets if os.path.exists(os.path.join(RES, "random", s[0] + ".parquet"))]
    if not sets:
        return
    fig, axes = plt.subplots(1, len(sets), figsize=(7.0, 2.1), sharey=True)
    for ax, (nm, lab) in zip(np.atleast_1d(axes), sets):
        rr = pd.read_parquet(os.path.join(RES, "random", nm + ".parquet"))
        meta = json.load(open(os.path.join(RES, "budgets", nm + ".meta.json")))
        r = R[R.ds == nm]
        # metric: share of adjacent pairs whose order is reversed
        for kind, col, ls in [("drop", COL["crowd"], "-"), ("flip", COL["expert"], "-")]:
            g = rr[rr.kind == kind].groupby("frac").adj_reversed.agg(["mean", "std", "count"])
            se = g["std"] / np.sqrt(g["count"])
            ax.plot(100 * g.index, g["mean"], color=col, ls=ls, marker="o", markersize=3, label=f"random {kind}")
            ax.fill_between(100 * g.index, g["mean"] - 1.96 * se, g["mean"] + 1.96 * se, color=col, alpha=0.2, lw=0)
        b = rr[rr.kind == "bootstrap"].adj_reversed.mean()
        ax.axhline(b, color=INK2, ls=":", lw=1, label="bootstrap")
        # adversarial: share of adjacent pairs reversible with budget <= x% (each pair separately)
        adj = r[r.rank_j == r.rank_i + 1]
        xs = np.logspace(-3, np.log10(30), 60)
        for kind, col in [("drop", COL["crowd"]), ("flip", COL["expert"])]:
            frac = [(adj[f"k_{kind}"] <= x / 100 * meta["n"]).mean() for x in xs]
            ax.plot(xs, frac, color=col, ls="--", lw=1.2, label=f"targeted {kind} (per pair)")
        ax.set_xscale("log")
        ax.set_title(lab, fontsize=8, loc="left")
        ax.set_xlabel("perturbed share of data (%)")
    np.atleast_1d(axes)[0].set_ylabel("adjacent pairs reversed")
    h, l = np.atleast_1d(axes)[0].get_legend_handles_labels()
    fig.legend(h, l, loc="upper center", ncol=5, bbox_to_anchor=(0.5, 1.06), fontsize=7)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(os.path.join(FIG, "random_vs_adv.pdf"))
    plt.close(fig)


def fig_same_battles():
    f = os.path.join(RES, "all_pairs.parquet")
    st = ["arenaST_" + j for j in D.JUDGES]
    hum = R[R.ds == "arenaST_human"]
    mh = json.load(open(os.path.join(RES, "budgets", "arenaST_human.meta.json")))
    namesh = mh["names"]
    hk = {(namesh[i], namesh[j]): (z, k) for i, j, z, k in zip(hum.i, hum.j, hum.z, hum.k_drop)}
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.5))
    labs = []
    for t, s in enumerate(st):
        if not (R.ds == s).any():
            continue
        q = R[R.ds == s]
        mj = json.load(open(os.path.join(RES, "budgets", s + ".meta.json")))
        nj = mj["names"]
        zs_h, zs_j, ks_h, ks_j = [], [], [], []
        for i, j, z, k in zip(q.i, q.j, q.z, q.k_drop):
            key = (nj[i], nj[j])
            if key in hk:
                zh, kh = hk[key]
            elif key[::-1] in hk:
                zh, kh = -hk[key[::-1]][0], np.nan
            else:
                continue
            zs_h.append(abs(zh)); zs_j.append(z); ks_h.append(kh); ks_j.append(k)
        lab = s.replace("arenaST_", "").replace("-Instruct", "").replace("Meta-", "").replace("-v0.1", "")
        labs.append(lab)
        zs_j = np.array(zs_j); ks_j = np.array(ks_j)
        axes[0].boxplot([zs_j[(zs_j > 0)]], positions=[t], widths=0.6, showfliers=False,
                        medianprops=dict(color=COL["llm-judge"]))
        axes[1].boxplot([ks_j / mj["n"] * 100], positions=[t], widths=0.6, showfliers=False,
                        medianprops=dict(color=COL["llm-judge"]))
    zh_all = hum.z.values
    axes[0].boxplot([zh_all], positions=[-1.3], widths=0.6, showfliers=False, medianprops=dict(color=COL["crowd"]))
    axes[1].boxplot([hum.k_drop.values / mh["n"] * 100], positions=[-1.3], widths=0.6, showfliers=False,
                    medianprops=dict(color=COL["crowd"]))
    for ax, yl in zip(axes, ["pairwise $z$ (all ordered pairs)", "deletions to reverse (% of data)"]):
        ax.set_xticks([-1.3] + list(range(len(labs))))
        ax.set_xticklabels(["crowd\n(human)"] + labs, rotation=35, ha="right", fontsize=6.5)
        ax.set_ylabel(yl)
        ax.set_yscale("log")
    axes[0].set_title("(a) separation of the same 63 models", fontsize=8, loc="left")
    axes[1].set_title("(b) fragility of the same pairs", fontsize=8, loc="left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "same_battles.pdf"))
    plt.close(fig)


def fig_nba():
    T = pd.read_csv(os.path.join(RES, "table_nba_seasons.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.2))
    ax = axes[0]
    ax.scatter(T.top1_z, T.top1_drop, c=COL["sports"], marker="x", s=14, lw=0.8, label="deletions")
    ax.scatter(T.top1_z, T.top1_flip, c=COL["expert"], marker="o", s=10, lw=0, label="flips")
    ax.set_xlabel("$z$ of leader vs. runner-up"); ax.set_ylabel("games to change the leader")
    ax.set_title("(a) NBA seasons 1980-2015: top-1", fontsize=8, loc="left")
    ax.legend(fontsize=7)
    ax = axes[1]
    yrs = T.ds.str[3:].astype(int)
    ax.plot(yrs, T.top1_drop, color=COL["sports"], marker="x", markersize=4, lw=1, label="leader (deletions)")
    ax.plot(yrs, T.top5_drop, color=COL["crowd"], marker="o", markersize=3, lw=1, label="top-5 set (deletions)")
    ax.set_xlabel("season (ending year)"); ax.set_ylabel("games")
    ax.set_title("(b) budgets by season", fontsize=8, loc="left")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "nba.pdf"))
    plt.close(fig)


if __name__ == "__main__":
    fig_collapse()
    fig_random()
    fig_same_battles()
    if os.path.exists(os.path.join(RES, "table_nba_seasons.csv")) and len(pd.read_csv(os.path.join(RES, "table_nba_seasons.csv"))):
        fig_nba()
