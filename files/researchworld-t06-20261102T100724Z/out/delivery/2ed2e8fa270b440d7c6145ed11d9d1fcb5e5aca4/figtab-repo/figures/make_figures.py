"""Figures F1-F7 and tables T1-T3 from results/.   Run: python3 -I figures/make_figures.py [--results DIR --out DIR]  (defaults: ../results, figures/rendered)

Figure -> claim map (PLAN.md section 5):  F1 claim 1 (fragility, s1);  F2 claim 2 (worst case vs random vs bootstrap);
F3 claim 3 (the same k* on scales s1, s2, s3);  F4 claim 3 (s4, size control);  F5 claim 3 (matched MT-Bench contrast);
F6 claim 4 (what predicts k*);  F7 claim 4 (validity of the search);  T1 data;  T2 claims 1-3 numbers;  T3 claim 5 (E5).
Every number is read from results/; nothing is typed in.  Intervals are percentile ranges (2.5-97.5) over the replicate
units of ONE dataset (NBA: seasons; Arena: battle bootstrap; MT-Bench: question-cluster bootstrap), pooled over the claim
instances (adjacent pairs) of the claim, and are not design-level confidence intervals.
"""
import os, sys
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import style
from common import board_key, read, wilson, parser, provenance

CCOL = {"C1": "#CC79A7", "C2": "#000000", "C4": "#999999"}
PERTS = {"P1": "removal", "P2": "flips", "P3": "additions"}
CLAIMS = {"C1": "C1 top-1", "C2": "C2 adjacent\npair order", "C4": "C4 pair\nsignificant"}
KEYS = ["A", "M-h", "M-g", "N"]
UNIT_BOARDS = {"A": "arena55k", "M-h": "mtbench_human", "M-g": "mtbench_gpt4", "N": "nba_season"}
LAB = {"A": "Arena", "M-h": "MT-Bench human", "M-g": "MT-Bench GPT-4", "N": "NBA seasons"}


def units(results):
    u = read(results, "kstar_units")
    u = u[u.board.isin(UNIT_BOARDS.values())].copy()
    u["key"] = u.board.map(board_key)
    u["kN"] = u.k_star / u.N
    u["kNloc"] = u.k_star / u.N_local
    # censored searches enter at their cap, as in summary_claims.csv
    u.loc[~u.found, "k_star"] = u.k_max
    u["kN"] = u.k_star / u.N
    return u


def summ(x):
    return np.nanpercentile(x, [2.5, 50, 97.5])


def legend_designs(fig, extra=(), ncol=4, y=-0.02):
    h = [plt.Line2D([], [], ls="", ms=5, label=LAB[k], **style.marker_kw(k)) for k in KEYS] + list(extra)
    fig.legend(handles=h, loc="lower center", ncol=ncol, frameon=False, bbox_to_anchor=(0.5, y))


def rows_layout(claims, keys=KEYS, step=0.2):
    """y position of (claim, design)."""
    return {(c, k): ci + (ki - (len(keys) - 1) / 2) * step for ci, c in enumerate(claims) for ki, k in enumerate(keys)}


def dotplot(ax, u, col, pert, claims, pos, full=None, logx=True):
    for (c, k), y in pos.items():
        d = u[(u.claim == c) & (u.key == k) & (u.pert == pert)]
        if d.empty:
            continue
        lo, md, hi = summ(d[col])
        mk = style.marker_kw(k)
        ax.plot([lo, hi], [y, y], color=style.DESIGNS[k]["color"], lw=1.1, alpha=0.8, solid_capstyle="butt")
        ax.plot([md], [y], ls="", ms=4.5, **mk)
        if full is not None:
            f = full[(full.claim == c) & (full.key == k) & (full.pert == pert)]
            if len(f):
                ax.plot([f[col].median()], [y], ls="", marker="|", ms=7, color="k", mew=1.2)
    ax.set_yticks(range(len(claims)))
    ax.set_yticklabels([CLAIMS[c] for c in claims])
    ax.invert_yaxis()
    if logx:
        ax.set_xscale("log")


def full_table(results):
    f = read(results, "kstar_full")
    f = f[f.board.isin(["arena55k", "mtbench_human", "mtbench_gpt4"])].copy()
    f["key"] = f.board.map(board_key)
    f["kN"] = f.k_star / f.N
    f["kNloc"] = f.k_star / f.N_local
    return f


def f1(u, full, out):
    """F1: k*/N per claim, design and perturbation family."""
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXT_WIDTH_IN, 2.5), sharex=True, sharey=True)
    claims = list(CLAIMS)
    pos = rows_layout(claims)
    for ax, (p, t) in zip(axes, PERTS.items()):
        dotplot(ax, u, "kN", p, claims, pos, full)
        ax.set_title(f"P{p[1]}: worst-case {t}")
        ax.set_xlabel("$k^*/N$ (log)")
    legend_designs(fig, [plt.Line2D([], [], ls="", marker="|", ms=7, color="k", mew=1.2, label="full-data fit")], ncol=5, y=-0.07)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f1_fragility.pdf"))
    plt.close(fig)


def f2(rc, bf, kf, out):
    """F2: random edits vs the worst case vs resampling, for C1 and the top adjacent pair."""
    boards = ["arena55k", "mtbench_human", "mtbench_gpt4", "nba_2015"]
    rows = [("C1", 0, "C1 top-1"), ("C2", 1, "C2 rank-1/2 pair"), ("C2", 2, "C2 rank-2/3 pair")]
    fig, axes = plt.subplots(len(rows), len(boards), figsize=(style.TEXT_WIDTH_IN, 4.4), sharey=True, squeeze=False)
    for ci, (c, cid, ct) in enumerate(rows):
        for bi, b in enumerate(boards):
            ax = axes[ci, bi]
            key = board_key(b)
            col = style.DESIGNS[key]["color"]
            for kind, ls, pert in (("remove", "-", "P1"), ("flip", "--", "P2")):
                d = rc[(rc.board == b) & (rc.claim == c) & (rc.claim_id == cid) & (rc.kind == kind)].sort_values("k")
                x = d.k / d.N
                lo, hi = wilson(d.n_changed, d.n_rep)
                ax.fill_between(x, lo, hi, color=col, alpha=0.15, lw=0)
                ax.plot(x, d.n_changed / d.n_rep, ls=ls, color=col, lw=1.2)
                if d.n_changed.iloc[-1] == 0:  # no flip up to the largest random size: ratios to k* are lower bounds
                    ax.plot([x.iloc[-1]], [0.0 if kind == "remove" else 0.05], ls="", marker=">", ms=4, color=col, clip_on=False)
                ks = kf[(kf.board == b) & (kf.claim == c) & (kf.claim_id == cid) & (kf.pert == pert)]
                ax.axvline(ks.k_star.iloc[0] / ks.N.iloc[0], color="k", ls=ls, lw=0.9)
            e = bf[(bf.board == b) & (bf.claim == c) & (bf.claim_id == cid) & (bf.frac == 1.0)]
            ax.axhline(e.n_changed.iloc[0] / e.n_rep.iloc[0], color="grey", ls=":", lw=1.0)
            ax.set_xscale("log")
            ax.set_ylim(-0.03, 1.03)
            if ci == 0:
                ax.set_title(LAB[key] if key != "N" else "NBA 2015", fontsize=7.5)
            if bi == 0:
                ax.set_ylabel(f"{ct}\nP(claim changes)")
            if ci == len(rows) - 1:
                ax.set_xlabel("size $k/N$ (log)")
    h = [plt.Line2D([], [], color="0.4", ls="-", label="random removals"), plt.Line2D([], [], color="0.4", ls="--", label="random flips"),
         plt.Line2D([], [], color="k", ls="-", label="worst case $k^*$, removal"), plt.Line2D([], [], color="k", ls="--", label="worst case $k^*$, flips"),
         plt.Line2D([], [], color="grey", ls=":", label="bootstrap resampling flip rate"),
         plt.Line2D([], [], ls="", marker=">", ms=4, color="0.4", label="no random flip up to here (lower bound)")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.13))
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f2_worst_vs_random.pdf"))
    plt.close(fig)


def f3(u, full, out):
    """F3: the same P1 result on scales k*, s1 = k*/N, s2 = k*/N_local, and the claim's z."""
    fig, axes = plt.subplots(1, 4, figsize=(style.TEXT_WIDTH_IN, 2.5), sharey=True)
    claims = list(CLAIMS)
    pos = rows_layout(claims)
    for ax, (col, xl) in zip(axes, (("k_star", "$k^*$ (votes)"), ("kN", "s1: $k^*/N$"), ("kNloc", "s2: $k^*/N_{local}$"), ("z", "s3: gap in s.e., $z$"))):
        uu = u[u.z > 0] if col == "z" else u
        dotplot(ax, uu, col, "P1", claims, pos, full if col != "z" else None)
        ax.set_xlabel(xl)
        if col == "z":
            ax.axvline(1.96, color="grey", ls=":", lw=0.8)
    legend_designs(fig, ncol=4, y=-0.06)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f3_scales.pdf"))
    plt.close(fig)


def f4(u, m, out):
    """F4: size control (s4). k*/N against the number of comparisons N: Arena size curve and matched subsets vs the real datasets."""
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXT_WIDTH_IN, 2.5), sharey=True, sharex=True)
    for ax, c in zip(axes, CLAIMS):
        sc = m[(m.claim == c) & (m.pert == "P1") & (m.unit_type == "sizecurve")].copy()
        sc["kN"] = sc.k_star / sc.N
        g = sc.groupby("N").kN.apply(lambda x: pd.Series(summ(x), index=["lo", "md", "hi"])).unstack()
        ax.fill_between(g.index, g.lo, g.hi, color=style.DESIGNS["A"]["color"], alpha=0.18, lw=0)
        ax.plot(g.index, g.md, color=style.DESIGNS["A"]["color"], lw=1.2)
        for ut, mk in (("mt_dense", "s"), ("mt_random6", "x"), ("nba_like", "D")):
            d = m[(m.claim == c) & (m.pert == "P1") & (m.unit_type == ut)]
            if d.empty:
                continue
            lo, md, hi = summ(d.k_star / d.N)
            x = d.N.median()
            ax.plot([x, x], [lo, hi], color=style.DESIGNS["A"]["color"], lw=1)
            ax.plot([x], [md], ls="", marker=mk, ms=5, mfc="white", mec=style.DESIGNS["A"]["color"], mew=1)
        for k in ("M-h", "M-g"):
            d = u[(u.board == UNIT_BOARDS[k]) & (u.claim == c) & (u.pert == "P1")]
            if len(d):
                lo, md, hi = summ(d.kN)
                x = d.N.median()
                ax.plot([x, x], [lo, hi], color=style.DESIGNS[k]["color"], lw=1)
                ax.plot([x], [md], ls="", ms=5, **style.marker_kw(k))
        d = u[(u.board == "nba_season") & (u.claim == c) & (u.pert == "P1")]
        if len(d):
            s = d.groupby("unit_id").agg(N=("N", "first"), kN=("kN", "median"))
            ax.plot(s.N, s.kN, ls="", ms=2.5, alpha=0.5, **style.marker_kw("N"))
        d = u[(u.board == "arena55k") & (u.claim == c) & (u.pert == "P1")]
        if len(d):
            lo, md, hi = summ(d.kN)
            ax.plot([d.N.median()] * 2, [lo, hi], color=style.DESIGNS["A"]["color"], lw=1)
            ax.plot([d.N.median()], [md], ls="", ms=5, **style.marker_kw("A"))
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_title(CLAIMS[c].replace("\n", " "))
        ax.set_xlabel("comparisons $N$ (log)")
    axes[0].set_ylabel("P1: $k^*/N$ (log)")
    h = [plt.Line2D([], [], color=style.DESIGNS["A"]["color"], label="Arena subsample size curve"),
         plt.Line2D([], [], ls="", marker="s", mfc="white", mec=style.DESIGNS["A"]["color"], label="Arena, 6 dense models, MT-Bench size"),
         plt.Line2D([], [], ls="", marker="x", mec=style.DESIGNS["A"]["color"], label="Arena, 6 random models, MT-Bench-like"),
         plt.Line2D([], [], ls="", marker="D", mfc="white", mec=style.DESIGNS["A"]["color"], label="Arena, 30 models, NBA-like"),
         plt.Line2D([], [], ls="", ms=5, label="MT-Bench human", **style.marker_kw("M-h")),
         plt.Line2D([], [], ls="", ms=5, label="MT-Bench GPT-4", **style.marker_kw("M-g")),
         plt.Line2D([], [], ls="", ms=3, label="NBA seasons (one dot per season)", **style.marker_kw("N")),
         plt.Line2D([], [], ls="", ms=5, label="Arena full data", **style.marker_kw("A"))]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.2))
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f4_size_control.pdf"))
    plt.close(fig)


def f5(pm, out):
    """F5: matched MT-Bench contrast: log ratio of k* (GPT-4 board / human board) over the same resampled questions."""
    fig, axes = plt.subplots(1, 2, figsize=(style.TEXT_WIDTH_IN, 3.3), sharey=True)
    panels = (("mtmatched_h1", "human, one judgment per key\n(equal $N$)"), ("mtmatched_h", "human, all judgments\n(human $N$ larger)"))
    d0 = pm[(pm.pert == "P1") & pm.claim.isin(["C1", "C2", "C4"])].copy()
    d0["lab"] = d0.claim + np.where(d0.claim == "C1", "", " r=" + d0.claim_id.astype(str))
    labs = list(d0[d0.a == "mtmatched_h1"].sort_values(["claim", "claim_id"]).lab)
    for ax, (a, t) in zip(axes, panels):
        d = d0[d0.a == a].set_index("lab").reindex(labs)
        y = np.arange(len(labs))
        sig = (d.logratio_k_q025 > 0) | (d.logratio_k_q975 < 0)
        for yi, (lab, r) in zip(y, d.iterrows()):
            ax.plot([r.logratio_k_q025, r.logratio_k_q975], [yi, yi], color=style.DESIGNS["M-g"]["color"], lw=1.2)
            ax.plot([r.logratio_k_median], [yi], ls="", ms=4.5, mfc=style.DESIGNS["M-g"]["color"] if sig[lab] else "white", **{k: v for k, v in style.marker_kw("M-g").items() if k != "markerfacecolor"})
        ax.axvline(0, color="k", lw=0.8)
        ax.set_title(t, fontsize=7.5)
        ax.set_xlabel("$\\log(k^*_{GPT\\text{-}4}/k^*_{human})$")
    axes[0].set_yticks(range(len(labs))); axes[0].set_yticklabels(labs); axes[0].invert_yaxis()
    fig.text(0.5, -0.03, "right of 0: GPT-4 board needs more edits. Filled: 95% range excludes 0. n = 200 question-cluster bootstrap replicates; P1.", ha="center", fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f5_matched_mtbench.pdf"))
    plt.close(fig)


def f6(u, sf, out):
    """F6: what predicts k*: scatter k* vs z and the log-log regression coefficients."""
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXT_WIDTH_IN, 2.6), gridspec_kw=dict(width_ratios=[1.3, 1, 1]))
    ax = axes[0]
    d = u[(u.pert == "P1") & (u.claim == "C2") & (u.z > 0.02)]
    rng = np.random.default_rng(0)
    for k in KEYS:
        dd = d[d.key == k]
        dd = dd.iloc[rng.permutation(len(dd))[:800]]
        ax.plot(dd.z, dd.k_star, ls="", ms=2.2, alpha=0.35, **style.marker_kw(k))
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("gap in s.e., $z$ (log)"); ax.set_ylabel("$k^*$, C2 P1 (log)")
    ax.set_title("C2 pair instances (subsample)")
    cl = ["C1", "C2", "C4"]
    for ax, terms, ttl in ((axes[1], ["log_z", "log_Nlocal"], "elasticities (M0)"),
                           (axes[2], ["design_expert", "design_model-judge", "design_sports"], "design shift vs crowd (M1)")):
        for ti, t in enumerate(terms):
            for ci, c in enumerate(cl):
                y = ti + (ci - 1) * 0.22
                if t.startswith("log"):
                    for scheme, lw, a in (("dataset", 2.2, 0.35), ("unit", 1.0, 1.0)):
                        r = sf[(sf.claim == c) & (sf.pert == "P1") & (sf.model == "M0") & (sf.term == t) & (sf.scheme == scheme)]
                        ax.plot([r.ci_lo.iloc[0], r.ci_hi.iloc[0]], [y, y], color=CCOL[c], lw=lw, alpha=a, solid_capstyle="butt")
                    ax.plot([r.coef.iloc[0]], [y], ls="", marker="o", ms=3.5, color=CCOL[c], label=c if ti == 0 else None)
                else:
                    r = sf[(sf.claim == c) & (sf.pert == "P1") & (sf.model == "M1") & (sf.term == t) & (sf.scheme == "unit")]
                    ax.plot([r.ci_lo.iloc[0], r.ci_hi.iloc[0]], [y, y], color=CCOL[c], lw=1.0)
                    ax.plot([r.coef.iloc[0]], [y], ls="", marker="o", ms=3.5, color=CCOL[c], label=c if ti == 0 else None)
        ax.set_yticks(range(len(terms)))
        ax.set_yticklabels([t.replace("design_", "").replace("log_Nlocal", "log $N_{local}$").replace("log_z", "log $z$") for t in terms])
        ax.invert_yaxis(); ax.axvline(0, color="k", lw=0.6)
        ax.set_title(ttl, fontsize=7.5)
    axes[1].set_xlabel("coefficient")
    axes[2].set_xlabel("shift in log $k^*$")
    h = [plt.Line2D([], [], ls="", marker="o", ms=3.5, color=CCOL[c], label=c) for c in cl]
    h += [plt.Line2D([], [], color="0.5", lw=1.0, label="95% CI, replicate units"), plt.Line2D([], [], color="0.5", lw=2.2, alpha=0.35, label="95% CI, datasets as clusters")]
    fig.legend(handles=h, loc="lower center", ncol=5, frameon=False, bbox_to_anchor=(0.5, -0.07))
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f6_predictors.pdf"))
    plt.close(fig)


def f7(ac, ec, kf, out):
    """F7: validity of the search: linearisation error, greedy vs exhaustive, one-shot prediction vs verified k*."""
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXT_WIDTH_IN, 2.3))
    ax = axes[0]
    d = ac[(ac.pert == "P1") & (ac.actual_change != 0)].copy()
    d["rel"] = d.pred_change / d.actual_change
    for f, mk in ((0.1, "o"), (0.25, "s"), (0.5, "^"), (1.0, "D")):
        e = d[np.isclose(d.frac_of_kstar_P1, f)]
        ax.plot(e.frac_of_kstar_P1 * (1 + 0.03 * np.random.default_rng(0).standard_normal(len(e))), e.rel, ls="", marker=mk, ms=3, mfc="none", color="0.3")
    ax.axhline(1, color="k", lw=0.8); ax.set_xscale("log")
    ax.set_xlabel("edit budget / $k^*$ (log)"); ax.set_ylabel("predicted / refit change"); ax.set_title("influence prediction", fontsize=7.5)
    ax = axes[1]
    e = ec[~ec.exact_capped]
    jit = np.random.default_rng(1).uniform(-0.15, 0.15, (len(e), 2))
    ax.plot(e.k_exact + jit[:, 0], e.k_greedy + jit[:, 1], ls="", marker="o", ms=2.5, alpha=0.5, color="0.3")
    lim = [0, max(e.k_exact.max(), e.k_greedy.max()) + 1]
    ax.plot(lim, lim, color="k", lw=0.8)
    ax.set_xlabel("exhaustive $k^*$"); ax.set_ylabel("greedy $k^*$")
    ax.set_title(f"agree in {int((e.k_exact == e.k_greedy).sum())}/{len(e)} instances", fontsize=7.5)
    ax = axes[2]
    kf2 = kf[kf.found & (kf.pert == "P1") & (kf.k_star > 0)]
    for k in KEYS:
        dd = kf2[kf2.key == k]
        ax.plot(dd.k_lin.clip(lower=0.3), dd.k_star, ls="", ms=3, alpha=0.6, **style.marker_kw(k))
    lim = [0.25, kf2.k_star.max() * 1.5]
    ax.plot(lim, lim, color="k", lw=0.8)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("one-shot $k_{lin}$ (log)"); ax.set_ylabel("verified $k^*$ (log)"); ax.set_title("full-data fits, P1", fontsize=7.5)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f7_search_validity.pdf"))
    plt.close(fig)


def tex_escape(s):
    return str(s).replace("_", "\\_")


PRE = "{\\footnotesize\\setlength{\\tabcolsep}{3pt}\n"


def write_tab(path, lines):
    open(path, "w").write(PRE + "\n".join(lines) + "\n}\n")


def t1(ds, out):
    ds = ds[ds.board.isin(["arena55k", "mtbench_human", "mtbench_gpt4", "nba_1950", "nba_1970", "nba_1990", "nba_2005", "nba_2010", "nba_2015"])]
    L = [r"\begin{tabular}{llrrrrr}", r"\toprule",
         r"Board & Design & $N$ & Participants & Cmp./participant & Tie rate & Score s.d. \\", r"\midrule"]
    for _, r in ds.iterrows():
        L.append(f"{tex_escape(r.board)} & {r.design} & {int(r.N)} & {int(r.n_participants)} & {r.cmp_per_participant:.0f} & {r.tie_rate:.2f} & {r.score_sd:.2f} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    write_tab(os.path.join(out, "t1_data_summary.tex"), L)


def t2(u, full, out):
    """T2: k* [2.5, 97.5 pct over replicate units] and k*/N by dataset, claim, family; with the full-data fit."""
    L = [r"\begin{tabular}{llllll}", r"\toprule", r"Dataset & Claim & Family & Full fit $k^*$ & Median $k^*$ [2.5, 97.5 pct] & Median $k^*/N$ \\", r"\midrule"]
    for k in KEYS:
        for c in CLAIMS:
            for p in PERTS:
                d = u[(u.key == k) & (u.claim == c) & (u.pert == p)]
                if d.empty:
                    continue
                lo, md, hi = summ(d.k_star)
                f = full[(full.key == k) & (full.claim == c) & (full.pert == p)] if k != "N" else full.iloc[0:0]
                fs = f"{int(f.k_star.median())}" if len(f) else "--"
                if len(f) > 1:
                    fs += f" ({int(f.k_star.min())}--{int(f.k_star.max())})"
                L.append(f"{LAB[k]} & {c} & {p} & {fs} & {md:.0f} [{lo:.0f}, {hi:.0f}] & {np.median(d.k_star / d.N):.2g} \\\\")
        L.append(r"\midrule")
    L[-1] = r"\bottomrule"
    L.append(r"\end{tabular}")
    write_tab(os.path.join(out, "t2_headline.tex"), L)


def t3(sens, u, out):
    """T3: sensitivity of k* (P1) to modelling choices, as the median ratio to the reference variant on the same claim instances."""
    s = sens[sens.pert == "P1"].copy()
    # unit_id of the NBA variants is the job index of code/run_sens.py (6 Arena/MT jobs, then no_home, with_playoffs per
    # season 1947..2015); decode it to the season so the rows pair with kstar_units
    nb = s.board == "nba_season"
    assert ((s[nb].unit_id - 6) % 2 == (s[nb].variant == "with_playoffs")).all()
    s.loc[nb, "unit_id"] = 1947 + (s[nb].unit_id - 6) // 2
    keycols = ["board", "claim", "claim_id", "unit_id"]
    L = [r"\begin{tabular}{llllr}", r"\toprule", r"Board & Variant & Claim & Median ratio $k^*_{var}/k^*_{ref}$ [IQR] & $n$ \\", r"\midrule"]
    for board, variants, ref in (("arena55k", ["tie_dropped"], "tie_half"), ("mtbench_human", ["tie_dropped"], "tie_half"), ("mtbench_gpt4", ["tie_dropped"], "tie_half"),
                                 ("nba_season", ["no_home", "with_playoffs"], None)):
        for v in variants:
            for c in ("C1", "C2", "C4"):
                a = s[(s.board == board) & (s.variant == v) & (s.claim == c)]
                if ref:
                    b = s[(s.board == board) & (s.variant == ref) & (s.claim == c)]
                else:
                    b = u[(u.board == "nba_season") & (u.pert == "P1") & (u.claim == c)]
                kc = keycols if board == "nba_season" else keycols[:-1]  # one fit per variant elsewhere
                m = a.merge(b[kc + ["k_star"]], on=kc, suffixes=("", "_ref"))
                m = m[(m.k_star_ref > 0) & (m.k_star > 0)]
                if m.empty:
                    continue
                r = m.k_star / m.k_star_ref
                q = np.percentile(r, [25, 50, 75])
                L.append(f"{tex_escape(board)} & {tex_escape(v)} & {c} & {q[1]:.2f} [{q[0]:.2f}, {q[2]:.2f}] & {len(m)} \\\\")
    pooled = sens[(sens.board == "nba_pooled") & (sens.pert == "P1")]
    for v in sorted(pooled.variant.unique()):
        for c in ("C1", "C2"):
            d = pooled[(pooled.variant == v) & (pooled.claim == c)]
            if len(d):
                L.append(f"nba\\_pooled & {tex_escape(v)} & {c} & median $k^*/N$ = {np.median(d.k_star / d.N):.2g} & {len(d)} \\\\")
    L += [r"\bottomrule", r"\end{tabular}"]
    write_tab(os.path.join(out, "t3_sensitivity.tex"), L)


def f8(kj, pm, out):
    """F8: crowd vs model judges on the SAME 49,938 Arena battles: k*, paired log ratio of k* (judge/human, over 40 shared battle bootstraps) and the unperturbed z."""
    JUDGES = [("Meta-Llama-3-70B-Instruct", "Llama-3-70B"), ("Athene-70B", "Athene-70B"), ("Qwen2-72B-Instruct", "Qwen2-72B")]
    CL = [("C1", 0, "C1 top-1"), ("C2", 2, "C2 pair 2/3"), ("C2", 3, "C2 pair 3/4"), ("C4", 2, "C4 pair 2/3")]
    fu = kj[(kj.unit_type == "full") & (kj.pert == "P1")]
    tie = fu.groupby("board").tie_rate.first()
    G = style.DESIGNS["M-g"]
    kw0 = {k: v for k, v in style.marker_kw("M-g").items() if k != "markerfacecolor"}
    fig, axes = plt.subplots(1, 3, figsize=(style.TEXT_WIDTH_IN, 3.6), sharey=True, gridspec_kw=dict(width_ratios=[1, 1.15, 1]))
    ycoord, ylab = [], []
    y = 0.0
    for gi, (c, r, lab) in enumerate(CL):
        for j, jl in JUDGES:
            ycoord.append(y)
            ylab.append("%s (ties %.0f%%)" % (jl, 100 * tie["arena49k_" + j]))
            sel = lambda b: fu[(fu.board == b) & (fu.claim == c) & (fu.claim_id == r)].iloc[0]
            hq, jq = sel("arena49k_h"), sel("arena49k_" + j)
            for ax, col in ((axes[0], "k_star"), (axes[2], "z")):
                ax.plot([hq[col], jq[col]], [y, y], color="0.7", lw=0.6, zorder=0)
                ax.plot([hq[col]], [y], ls="", ms=4.5, **style.marker_kw("A"))
                ax.plot([jq[col]], [y], ls="", ms=4.5, **style.marker_kw("M-g"))
            for pert, dy in (("P1", -0.14), ("P2", 0.14)):
                q = pm[(pm.a == "arena49k_h") & (pm.b == "arena49k_" + j) & (pm.claim == c) & (pm.claim_id == r) & (pm.pert == pert)].iloc[0]
                sig = (q.logratio_k_q025 > 0) or (q.logratio_k_q975 < 0)
                axes[1].plot([q.logratio_k_q025, q.logratio_k_q975], [y + dy] * 2, color=G["color"], lw=1.0)
                axes[1].plot([q.logratio_k_median], [y + dy], ls="", ms=3.8, mfc=G["color"] if sig else "white", **kw0)
            y += 1
        y += 1.0
        if gi < len(CL) - 1:
            for ax in axes:
                ax.axhline(y - 0.5, color="0.7", lw=0.5)
    axes[0].set_yticks(ycoord); axes[0].set_yticklabels(ylab, fontsize=6)
    axes[0].invert_yaxis()
    for i, (c, r, lab) in enumerate(CL):
        axes[0].text(0.0, ycoord[3 * i] - 0.55, lab, transform=axes[0].get_yaxis_transform(), ha="left", va="center", fontsize=6.5, fontweight="bold")
    axes[0].set_xscale("log"); axes[0].set_xlabel("$k^*$ (removals, P1)")
    axes[1].axvline(0, color="k", lw=0.8)
    axes[1].set_xlabel("$\\log(k^*_{judge}/k^*_{human})$")
    axes[2].axvline(1.96, color="k", lw=0.6, ls=":"); axes[2].set_xlim(-0.2, 5.6)
    axes[0].set_xlim(4, 300); axes[0].set_ylim(y - 0.4, -0.9)
    for ax in axes:
        ax.grid(False)
    axes[2].set_xlabel("unperturbed $z$ = gap / s.e.")
    for ax, t in zip(axes, ("(a) edits to overturn", "(b) paired log ratio", "(c) the data's own margin")):
        ax.set_title(t, fontsize=7.5)
    h = [plt.Line2D([], [], ls="", **style.marker_kw("A"), label="human votes"), plt.Line2D([], [], ls="", **style.marker_kw("M-g"), label="LLM judge"),
         plt.Line2D([], [], color=G["color"], lw=1.0, marker="^", mfc=G["color"], mec=G["color"], ms=3.8, label="(b) upper P1 removal, lower P2 flips; filled: 95% range excludes 0")]
    fig.legend(handles=h, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.07), fontsize=6.5)
    fig.tight_layout()
    fig.savefig(os.path.join(out, "f8_crowd_vs_judges.pdf"))
    plt.close(fig)


def main():
    a = parser().parse_args()
    os.makedirs(a.out, exist_ok=True)
    style.apply()
    R = lambda n: read(a.results, n)
    u, full = units(a.results), full_table(a.results)
    kf_all = read(a.results, "kstar_full")
    jobs = [("F1", lambda: f1(u, full, a.out)), ("F2", lambda: f2(R("random_curve"), R("boot_flip"), kf_all, a.out)),
            ("F3", lambda: f3(u, full, a.out)), ("F4", lambda: f4(u, R("matched_arena"), a.out)),
            ("F5", lambda: f5(R("paired_mt"), a.out)), ("F6", lambda: f6(u, R("scaling_fit"), a.out)),
            ("F7", lambda: f7(R("approx_check"), R("exact_check"), full, a.out)), ("F8", lambda: f8(R("kstar_judges"), R("paired_mt"), a.out)),
            ("T1", lambda: t1(R("data_summary"), a.out)), ("T2", lambda: t2(u, full, a.out)), ("T3", lambda: t3(R("sensitivity"), u, a.out))]
    for n, fn in jobs:
        fn()
        print("wrote", n)
    import hashlib, json
    names = {"F1": ["kstar_units", "kstar_full"], "F2": ["random_curve", "boot_flip", "kstar_full"], "F3": ["kstar_units", "kstar_full"],
             "F4": ["matched_arena", "kstar_units"], "F5": ["paired_mt"], "F6": ["kstar_units", "scaling_fit"],
             "F7": ["approx_check", "exact_check", "kstar_full"], "F8": ["kstar_judges", "paired_mt"], "T1": ["data_summary"], "T2": ["kstar_units", "kstar_full"],
             "T3": ["sensitivity", "kstar_units"]}
    sha = lambda n: hashlib.sha256(open(os.path.join(a.results, n + ".csv"), "rb").read()).hexdigest()
    prov = {k: {n + ".csv": sha(n) for n in v} for k, v in names.items()}
    json.dump(dict(script="figures/make_figures.py", inputs_sha256=prov, results_manifest=provenance(a.results, sorted({n for v in names.values() for n in v}))),
              open(os.path.join(a.out, "PROVENANCE.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
