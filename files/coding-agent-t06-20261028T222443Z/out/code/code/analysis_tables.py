"""All tables (except the law table) and Figures 2-3 of the paper.

Usage: python code/analysis_tables.py
Reads results/*.parquet; writes paper/tables/*.tex, figs/*.pdf, results/numbers.json
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import kendalltau

from analysis_common import DESIGN_LABEL, FIG, RES, TAB, design, label, load_pairs, outcome_table

plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": "#52514e", "xtick.color": "#52514e", "ytick.color": "#52514e",
                     "legend.frameon": False})
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
NUM = {}


def fmt_k(k, N):
    if k is None or (isinstance(k, float) and np.isnan(k)):
        return "--"
    a = 100 * k / N
    s = f"{a:.3f}" if a < 0.01 else (f"{a:.2f}" if a < 1 else f"{a:.1f}")
    return f"{int(k)} ({s}\\%)"


def main_table(d):
    o = outcome_table(d[~d.noties])
    bs = pd.read_parquet(os.path.join(RES, "bootstrap_k.parquet"))
    rn = pd.read_parquet(os.path.join(RES, "random_noise.parquet"))
    boards = ["arena140k", "arena55k", "webdev", "arenaJ_crowd", "arenaJ_Meta-Llama-3-70B-Instruct",
              "arenaJ_Qwen2-72B-Instruct", "mtbench_human", "mtbench_gpt4", "arena55k_mt6"]
    lines = [r"\begin{tabular}{llrrrrrrcrr}", r"\toprule",
             r"& & & & \multicolumn{3}{c}{top-1 change: $k^\star$ (\% of $N$)} & boot.\ 90\% & $P_{\mathrm{boot}}$ & & \\",
             r"\cmidrule(lr){5-7}",
             r"Leaderboard & design & $N$ & $K$ & drop & flip & inject & CI (drop) & same \#1 & $z$ & $R$ \\",
             r"\midrule"]
    out = {}
    for b in boards:
        g = o[o.board == b].set_index("mode")
        bb = bs[bs.board == b]
        lo, hi = np.percentile(bb.k_drop.dropna(), [5, 95])
        dr = g.loc["drop"]
        lines.append(f"{label(b)} & {DESIGN_LABEL[design(b)]} & {int(dr.N):,} & {int(dr.K)} & "
                     f"{fmt_k(dr.k_top1, dr.N)} & {fmt_k(g.loc['flip'].k_top1, dr.N)} & {fmt_k(g.loc['add'].k_top1, dr.N)} & "
                     f"[{lo:.0f}, {hi:.0f}] & {bb.same_leader.mean():.2f} & {dr.z_top1:.2f} & {dr.R_top1:.1f} \\\\")
        out[b] = dict(N=int(dr.N), K=int(dr.K), k_drop=float(dr.k_top1), k_flip=float(g.loc["flip"].k_top1),
                      k_add=float(g.loc["add"].k_top1), boot_lo=float(lo), boot_hi=float(hi),
                      p_same=float(bb.same_leader.mean()), z=float(dr.z_top1), R=float(dr.R_top1),
                      k_top3_drop=float(dr.k_top3), k_any10_drop=float(dr.k_any10),
                      k_med_adj10_drop=float(dr.k_med_adj10))
    # NBA summary row (median over seasons 1947-2015 and over 2005-2015 for bootstrap)
    nb = o[o.board.str.startswith("nba")]
    lines.append(r"\midrule")
    q = {m: nb[nb["mode"] == m] for m in ["drop", "flip", "add"]}
    nbs = bs[bs.board.str.startswith("nba")]
    lines.append(r"NBA, median of 68 seasons & Sports & {:,.0f} & {:.0f} & {:.0f} ({:.1f}\%) & {:.0f} & {:.0f} & [{:.0f}, {:.0f}]$^\dagger$ & {:.2f}$^\dagger$ & {:.2f} & {:.1f} \\".format(
        q["drop"].N.median(), q["drop"].K.median(), q["drop"].k_top1.median(),
        100 * (q["drop"].k_top1 / q["drop"].N).median(), q["flip"].k_top1.median(), q["add"].k_top1.median(),
        *np.percentile(nbs.k_drop.dropna(), [5, 95]), nbs.same_leader.mean(), q["drop"].z_top1.median(),
        q["drop"].R_top1.median()))
    out["nba"] = dict(k_drop_med=float(q["drop"].k_top1.median()), alpha_med=float((q["drop"].k_top1 / q["drop"].N).median()),
                      k_drop_iqr=[float(q["drop"].k_top1.quantile(.25)), float(q["drop"].k_top1.quantile(.75))],
                      frac_k_le_5=float((q["drop"].k_top1 <= 5).mean()), p_same=float(nbs.same_leader.mean()),
                      z_med=float(q["drop"].z_top1.median()), k_any10_med=float(q["drop"].k_any10.median()))
    for b in ["nba_2015"]:
        g = o[o.board == b].set_index("mode")
        out[b] = dict(k_drop=float(g.loc["drop"].k_top1), k_flip=float(g.loc["flip"].k_top1), N=int(g.loc["drop"].N))
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "main.tex"), "w").write("\n".join(lines) + "\n")
    NUM["main"] = out

    # random-noise: smallest rate with P(top-1 change) >= 0.5 (or none up to 30%)
    rr = rn.groupby(["board", "kind", "rate"]).top1.mean().reset_index()
    NUM["random"] = {f"{b}|{k}": {str(x): float(p) for x, p in zip(g.rate, g.top1)} for (b, k), g in rr.groupby(["board", "kind"])}


def ties_table(d):
    o = outcome_table(d[~d.board.str.startswith("nba")])
    boards = ["arena140k", "arena55k", "webdev", "arenaJ_crowd", "arenaJ_Athene-70B", "arenaJ_Meta-Llama-3-70B-Instruct",
              "arenaJ_Meta-Llama-3-8B-Instruct", "arenaJ_Mistral-7B-Instruct-v0.1", "arenaJ_Qwen2-72B-Instruct",
              "mtbench_human", "mtbench_gpt4", "arena55k_mt6"]
    lines = [r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r"& \multicolumn{3}{c}{ties as half-wins (main)} & \multicolumn{3}{c}{ties removed} \\",
             r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}",
             r"Leaderboard & $N$ & top-1 & top-3 set & $N$ & top-1 & top-3 set \\", r"\midrule"]
    for b in boards:
        a = o[(o.board == b) & (o["mode"] == "drop")].iloc[0]
        c = o[(o.board == b + "__noties") & (o["mode"] == "drop")].iloc[0]
        lines.append(f"{label(b)} & {int(a.N):,} & {int(a.k_top1)} & {int(a.k_top3)} & {int(c.N):,} & {int(c.k_top1)} & {int(c.k_top3)} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "ties.tex"), "w").write("\n".join(lines) + "\n")


def judges_table(d):
    """Same 49,938 battles labelled by the crowd and by five LLM judges."""
    boards = ["arenaJ_crowd", "arenaJ_Athene-70B", "arenaJ_Meta-Llama-3-70B-Instruct", "arenaJ_Qwen2-72B-Instruct",
              "arenaJ_Meta-Llama-3-8B-Instruct", "arenaJ_Mistral-7B-Instruct-v0.1"]
    meta = json.load(open(os.path.join(os.path.dirname(RES), "derived", "meta.json")))
    o = outcome_table(d[~d.noties])
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from common import load_board
    Bc = load_board("arenaJ_crowd")
    thc = Bc.fit()[0][: Bc.K]
    lines = [r"\begin{tabular}{lrrrrrrr}", r"\toprule",
             r"Labeler & tie rate & $\tau$ vs.\ crowd & top-1 $k^\star$ & top-3 $k^\star$ & med.\ adj.\ $k^\star$ & med.\ adj.\ $z$ & med.\ $k^\star/(zR)$ \\",
             r"\midrule"]
    out = {}
    for b in boards:
        B = load_board(b)
        th = B.fit()[0][: B.K]
        assert list(B.names) == list(Bc.names)
        tau = kendalltau(th, thc)[0]
        a = o[(o.board == b) & (o["mode"] == "drop")].iloc[0]
        adj = d[(d.board == b) & (d["mode"] == "drop") & (d.rj == d.ri + 1) & (d.ri < 10)]
        ratio = d[(d.board == b) & (d["mode"] == "drop") & (d.kb >= 3)].ratio.median()
        lines.append(f"{label(b).replace('Arena-50k: ', '').replace('Arena-50k single-turn (crowd)', 'Crowd (original votes)')} & "
                     f"{meta[b]['tie_rate']:.2f} & {tau:.2f} & {int(a.k_top1)} & {int(a.k_top3)} & {adj.kb.median():.0f} & {adj.z_ij.median():.2f} & {ratio:.2f} \\\\")
        out[b] = dict(tau=float(tau), k_top1=float(a.k_top1), k_top3=float(a.k_top3), med_adj_k=float(adj.kb.median()),
                      med_adj_z=float(adj.z_ij.median()), ratio=float(ratio), tie=meta[b]["tie_rate"])
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "judges.tex"), "w").write("\n".join(lines) + "\n")
    NUM["judges"] = out


def mt6_table():
    m = pd.read_parquet(os.path.join(RES, "matched_mt6.parquet"))
    bs = pd.read_parquet(os.path.join(RES, "bootstrap_k.parquet"))
    lines = [r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Labeler (same 6 models) & $N$ (full) & top-1 $k^\star$, full & top-1 $k^\star$ at $N{=}1{,}367$ [90\% int.] & $\sum$ adj.\ $k^\star$ at $N{=}1{,}367$ & full $z_{12}$ \\",
             r"\midrule"]
    out = {}
    names = {"arena55k_mt6": "Arena crowd votes", "mtbench_human": "MT-Bench experts", "mtbench_gpt4": "MT-Bench GPT-4 judge"}
    for b in ["arena55k_mt6", "mtbench_human", "mtbench_gpt4"]:
        full = m[(m.board == b) & (m.rep == -1)]
        sub = m[(m.board == b) & (m.rep >= 0)]
        t1 = sub[sub.r == 0].k_drop
        if b == "arena55k_mt6":  # board already has N=1367: use bootstrap resamples for an interval
            t1 = bs[bs.board == b].k_drop
        sums = sub[sub.r > 0].groupby("rep").k_drop.sum()
        if b == "arena55k_mt6":
            sums_txt = f"{sums.iloc[0]:.0f}"
        else:
            sums_txt = f"{sums.median():.0f} [{sums.quantile(.05):.0f}, {sums.quantile(.95):.0f}]"
        lo, hi = t1.quantile(.05), t1.quantile(.95)
        k_full = full[full.r == 0].k_drop.iloc[0]
        lines.append(f"{names[b]} & {int(full.n.iloc[0]):,} & {k_full:.0f} & {t1.median():.0f} [{lo:.0f}, {hi:.0f}] & {sums_txt} & {full[full.r == 1].z.iloc[0]:.2f} \\\\")
        out[b] = dict(N=int(full.n.iloc[0]), k_full=float(k_full), k_eq=float(t1.median()), lo=float(lo), hi=float(hi),
                      sum_adj=float(sums.median()), z12=float(full[full.r == 1].z.iloc[0]))
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "mt6.tex"), "w").write("\n".join(lines) + "\n")
    NUM["mt6"] = out


def attack_table():
    a = pd.read_parquet(os.path.join(RES, "realistic_attack.parquet"))
    a["battles"] = np.where(a.kind == "target", a.votes * a.N / a.n_t, a.votes)
    boards = ["arena140k", "arena55k", "webdev", "mtbench_human", "mtbench_gpt4"]
    lines = [r"\begin{tabular}{llrrrr}", r"\toprule",
             r"Leaderboard & start rank & free (optimal) & target-only: votes & target-only: battles seen & omnipresent: votes \\",
             r"\midrule"]
    out = {}
    for b in boards:
        for rk in [2, 3, 5, 10]:
            g = a[(a.board == b) & (a["rank"] == rk)]
            if len(g) == 0:
                continue
            f = g[g.kind == "free"].votes.iloc[0]
            t = g[g.kind == "target"]; om = g[g.kind == "omni"]
            def mq(x):
                return f"{x.median():,.0f} [{x.quantile(.05):,.0f}, {x.quantile(.95):,.0f}]"
            lines.append(f"{label(b) if rk == 2 else ''} & {rk} & {f:,.0f} & {mq(t.votes)} & {t.battles.median():,.0f} & {mq(om.votes)} \\\\")
            out[f"{b}|{rk}"] = dict(free=float(f), target=float(t.votes.median()), target_battles=float(t.battles.median()),
                                    omni=float(om.votes.median()))
        lines.append(r"\addlinespace")
    lines = lines[:-1] + [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "attack.tex"), "w").write("\n".join(lines) + "\n")
    NUM["attack"] = out


def relax_table():
    r = pd.read_parquet(os.path.join(RES, "relaxation_check.parquet"))
    r["lb"] = np.ceil(r.relax - 1e-6)
    r["close"] = (r.rj == r.ri + 1) | ((r.ri == 1) & (r.rj == 2))
    out = {}
    for c, g in r.groupby("close"):
        ex = (g.k_best - g.lb) / g.k_best
        out["adjacent" if c else "far"] = dict(n=int(len(g)), within1=float(((g.k_best - g.lb) <= 1).mean()),
                                               med_excess=float(ex.median()), max_excess=float(ex.max()),
                                               round_eq_lb=float((g.k_round == g.lb).mean()))
    NUM["relax"] = out
    lines = [r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"pairs & \# & greedy $\le \lceil\text{relax}\rceil{+}1$ & median excess & max excess & rounded relax.\ $=\lceil\text{relax}\rceil$ \\",
             r"\midrule"]
    for key, nm in [("adjacent", "adjacent and 1-vs-2"), ("far", "1-vs-$j$, $j\\ge3$")]:
        v = out[key]
        lines.append(f"{nm} & {v['n']} & {100 * v['within1']:.0f}\\% & {100 * v['med_excess']:.1f}\\% & {100 * v['max_excess']:.1f}\\% & {100 * v['round_eq_lb']:.0f}\\% \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "relax.tex"), "w").write("\n".join(lines) + "\n")


def fig_random(d):
    rn = pd.read_parquet(os.path.join(RES, "random_noise.parquet"))
    o = outcome_table(d[~d.noties])
    boards = ["arena140k", "arena55k", "webdev", "mtbench_human", "nba_2015"]
    fig, ax = plt.subplots(1, len(boards), figsize=(6.75, 1.95), sharey=True)
    for a, b in zip(ax, boards):
        g = rn[rn.board == b].groupby(["kind", "rate"]).top1.agg(["mean", "count"]).reset_index()
        for kind, col, mk in [("drop", C1, "o"), ("flip", C2, "s")]:
            h = g[g.kind == kind]
            se = np.sqrt(h["mean"] * (1 - h["mean"]) / h["count"])
            a.errorbar(100 * h.rate, h["mean"], yerr=1.96 * se, color=col, marker=mk, ms=3, lw=1.2, capsize=0,
                       label=f"random {kind}")
            kk = o[(o.board == b) & (o["mode"] == kind)].iloc[0]
            a.axvline(100 * kk.k_top1 / kk.N, color=col, ls=":", lw=1.2)
        a.set_xscale("log")
        a.set_xlim(5e-4, 40)
        a.set_title(label(b), fontsize=7.5)
        a.grid(True, color="#e6e5e0", lw=0.5); a.set_axisbelow(True)
    ax[0].set_ylabel("P(top-1 changes)")
    ax[0].legend(fontsize=6.5, loc="upper left", handlelength=1.2)
    ax[-1].text(0.0012, 0.55, "dotted:\nworst case", fontsize=6.5, color="#52514e")
    fig.supxlabel("% of comparisons perturbed (log scale)", fontsize=8, y=0.02)
    fig.tight_layout(w_pad=0.6)
    fig.savefig(os.path.join(FIG, "fig_random.pdf")); fig.savefig(os.path.join(FIG, "fig_random.png"), dpi=150)


def fig_subsample():
    s = pd.read_parquet(os.path.join(RES, "subsample.parquet"))
    fig, ax = plt.subplots(1, 2, figsize=(6.75, 2.3))
    cols = {"arena140k": C1, "arena55k": "#6250d6", "webdev": C3, "mtbench_human": C2, "mtbench_gpt4": "#e34948"}
    out = {}
    for b, g in s.groupby("board"):
        h = g.groupby("n").agg(k=("k_13", "median"), z=("z_13", "median"), k1=("k_top1", "median")).reset_index()
        ax[0].plot(h.n, h.k, marker="o", ms=3, color=cols[b], lw=1.2, label=label(b))
        ax[1].plot(h.n, 100 * h.k / h.n, marker="o", ms=3, color=cols[b], lw=1.2)
        sl = np.polyfit(np.log(h.n[h.k > 0]), np.log(h.k[h.k > 0]), 1)[0]
        out[b] = float(sl)
    for a in ax:
        a.set_xscale("log"); a.grid(True, color="#e6e5e0", lw=0.5); a.set_axisbelow(True)
        a.set_xlabel("number of comparisons $N$ (random subsample)")
    ax[0].set_yscale("log")
    ax[0].set_ylabel("worst-case drops, rank 1 vs 3")
    ax[1].set_ylabel("as % of $N$")
    ax[1].set_yscale("log")
    h, l = ax[0].get_legend_handles_labels()
    ax[1].legend(h, l, fontsize=6.5, loc="lower left")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, "fig_subsample.pdf")); fig.savefig(os.path.join(FIG, "fig_subsample.png"), dpi=150)
    NUM["subsample_slope_k13"] = out


def misc_numbers(d):
    base = d[~d.noties & (d["mode"] == "drop")]
    llm = base[~base.board.str.startswith("nba")]
    sig = llm[(llm.rj == llm.ri + 1) & (llm.z_ij > 1.96)]
    NUM["sig_adjacent_llm"] = dict(n=int(len(sig)), k_med=float(sig.kb.median()), k_min=float(sig.kb.min()),
                                   alpha_med=float(sig.alpha.median()), alpha_max=float(sig.alpha.max()),
                                   frac_alpha_lt_0p1=float((sig.alpha < 0.001).mean()),
                                   frac_alpha_lt_1=float((sig.alpha < 0.01).mean()))
    a140 = base[(base.board == "arena140k") & (base.rj == base.ri + 1)]
    NUM["arena140k_adj"] = dict(n=int(len(a140)), sig=int((a140.z_ij > 1.96).sum()),
                                k_le_10=int((a140.kb <= 10).sum()), k_le_100=int((a140.kb <= 100).sum()),
                                sig_k_max=float(a140[a140.z_ij > 1.96].kb.max()), sig_k_med=float(a140[a140.z_ij > 1.96].kb.median()))
    # flip/drop and add/drop ratios
    p = d[~d.noties].pivot_table(index=["board", "ri", "rj"], columns="mode", values="kb")
    p = p[(p["drop"] >= 5)]
    NUM["mode_ratios"] = dict(flip_over_drop=float((p["flip"] / p["drop"]).median()), add_over_drop=float((p["add"] / p["drop"]).median()))
    # model SE vs IJ SE
    NUM["se_ratio"] = float((base.se_ij / base.se_model).median())
    # one-shot vs iterative
    dd = d[~d.noties & d.k.notna() & d.k_os.notna()]
    NUM["iter_vs_oneshot"] = dict(iter_better=float((dd.k < dd.k_os).mean()), os_better=float((dd.k > dd.k_os).mean()),
                                  fo_under=float((dd.k_fo > dd.kb).mean()), fo_over=float((dd.k_fo < dd.kb).mean()),
                                  fo_rel_err_med=float((abs(dd.k_fo - dd.kb) / dd.kb.clip(lower=1)).median()))
    # decomposition of rho = k*/(zR) into capacity (k_lin/zR) and nonlinearity (k*/k_lin), drop, k*>=3
    x = base[(base.kb >= 3) & (base.z_ij > 0)]
    NUM["rho_parts"] = dict(klin_over_zR=float((x.k_fo / x.pred).median()), k_over_klin=float((x.kb / x.k_fo).median()),
                            by_design={g: [float((h.k_fo / h.pred).median()), float((h.kb / h.k_fo).median())]
                                       for g, h in x.groupby("design")})
    X = np.c_[np.ones(len(x)), np.log(x.z_ij)]
    yy = np.log(x.kb)
    res = yy - X @ np.linalg.lstsq(X, yy, rcond=None)[0]
    NUM["R2_z_only"] = float(1 - res.var() / yy.var())
    for nm, g in [("llm", x[x.design != "sports"]), ("nba", x[x.design == "sports"])]:
        yy, pp = np.log(g.kb), np.log(g.pred)
        NUM["R2_identity_" + nm] = float(1 - ((yy - pp) ** 2).sum() / ((yy - yy.mean()) ** 2).sum())
    NUM["n_pairs_total"] = int(d[~d.noties].groupby(["board", "ri", "rj"]).ngroups)
    NUM["n_boards"] = int(d[~d.noties].board.nunique())
    NUM["secs_med"] = float(d.secs.median()); NUM["secs_max"] = float(d.secs.max())


def dataset_table():
    meta = json.load(open(os.path.join(os.path.dirname(RES), "derived", "meta.json")))
    rows = [("arena55k", "Chatbot Arena 55k (2023--24)", "crowd votes, user prompts"),
            ("arena140k", "Chatbot Arena 140k (2025)", "crowd votes, user prompts"),
            ("webdev", "WebDev Arena 10k (2025)", "crowd votes, web-dev tasks"),
            ("arenaJ_crowd", "Arena single-turn 50k", "crowd votes (subset of 55k)"),
            ("arenaJ_Qwen2-72B-Instruct", "\\quad + 5 LLM judges", "judge verdicts on same battles"),
            ("mtbench_human", "MT-Bench human", "expert votes, 80 fixed questions"),
            ("mtbench_gpt4", "MT-Bench GPT-4", "GPT-4 pairwise judge"),
            ("arena55k_mt6", "Arena-55k, 6 MT-Bench models", "crowd votes (subset)"),
            ("nba_2015", "NBA regular seasons 1947--2015", "game results (68 seasons)")]
    lines = [r"\begin{tabular}{lllrrr}", r"\toprule", r"Leaderboard & design & labels & $N$ & $K$ & ties \\", r"\midrule"]
    nba = [v for k, v in meta.items() if k.startswith("nba_") and v["N"] > 0]
    for k, nm, lab in rows:
        if k == "nba_2015":
            lines.append(f"{nm} & Sports & {lab} & {min(v['N'] for v in nba)}--{max(v['N'] for v in nba):,} & {min(v['K'] for v in nba)}--{max(v['K'] for v in nba)} & 0 \\\\")
            continue
        v = meta[k]
        tie = f"{v['tie_rate']:.2f}"
        if k.startswith("arenaJ_Q"):
            tie = "0.00--0.26"
        lines.append(f"{nm} & {DESIGN_LABEL[design(k)]} & {lab} & {v['N']:,} & {v['K']} & {tie} \\\\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(os.path.join(TAB, "datasets.tex"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
    d = load_pairs()
    dataset_table()
    main_table(d)
    ties_table(d)
    judges_table(d)
    mt6_table()
    attack_table()
    relax_table()
    fig_random(d)
    fig_subsample()
    misc_numbers(d)
    json.dump(NUM, open(os.path.join(RES, "numbers.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in NUM.items() if k != "random"}, indent=1))
