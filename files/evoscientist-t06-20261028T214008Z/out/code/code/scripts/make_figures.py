"""Generates every figure (paper/figures/*.pdf) and table (paper/tables/*.tex) from results/*.csv.

Run after e1..e7.  Also writes results/derived_*.csv with the numbers quoted in the text.
"""
from common import *  # noqa
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from lbrobust import data as D

TAB = os.path.join(ROOT, "paper", "tables")
os.makedirs(TAB, exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "pdf.fonttype": 42})
NAME2KEY = {"Arena-55k": "arena55k", "Arena-140k": "arena140k", "MT-Bench-Human": "mt_human",
            "MT-Bench-GPT4": "mt_gpt4"}
COL = {"Arena-55k": "C0", "Arena-140k": "C9", "MT-Bench-Human": "C3", "MT-Bench-GPT4": "C1", "NBA": "C2"}
_cache = {}


def player_counts(name):
    if name not in _cache:
        d = D.load(NAME2KEY.get(name, name.replace("NBA-", "nba")))
        _cache[name] = np.bincount(d.i, weights=d.n, minlength=d.K) + np.bincount(d.j, weights=d.n, minlength=d.K)
    return _cache[name]


def add_nmin(p):
    out = []
    for ds, g in p.groupby("dataset"):
        c = player_counts(ds)
        g = g.copy()
        g["nmin"] = np.minimum(c[g.hi.values], c[g.lo.values])
        out.append(g)
    q = pd.concat(out)
    q["grp"] = q.dataset.where(~q.dataset.str.startswith("NBA"), "NBA")
    return q


def fmt_int(x):
    return "--" if not np.isfinite(x) else f"{int(x)}"


def pct(x, nd=3):
    return "--" if not np.isfinite(x) else f"{100 * x:.{nd}f}"


def ci(v, lo=2.5, hi=97.5):
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return (np.percentile(v, lo), np.percentile(v, hi)) if len(v) else (np.nan, np.nan)


# =========================================================================================
def table_main():
    s = pd.read_csv(f"{RES}/e1_summary.csv")
    b = pd.read_csv(f"{RES}/e5_bootstrap.csv") if os.path.exists(f"{RES}/e5_bootstrap.csv") else None
    rows = []
    groups = [("Arena-55k", "crowd"), ("Arena-140k", "crowd"), ("MT-Bench-Human", "expert"),
              ("MT-Bench-GPT4", "LLM judge")]
    lines = []
    for ds, design in groups:
        r = s[s.dataset == ds].iloc[0]
        key = NAME2KEY[ds]
        bb = b[b.source == key] if b is not None else None

        def cell(col, frac=False):
            v = r[col]
            txt = pct(v, 3 if v < 0.01 else 2) if frac else fmt_int(v)
            if bb is not None and len(bb):
                lo, hi = ci(bb[col])
                txt += (f" {{\\tiny[{pct(lo, 3 if lo < 0.01 else 2)},{pct(hi, 3 if hi < 0.01 else 2)}]}}" if frac
                        else f" {{\\tiny[{fmt_int(lo)},{fmt_int(hi)}]}}")
            return txt
        lines.append(f"{ds} & {design} & {int(r.N):,} & {int(r.K)} & {r.z_top12:.2f} & "
                     f"{cell('top1_drop')} & {cell('top1_flip')} & {cell('top1_add')} & {cell('top1_drop_frac', True)} & "
                     f"{cell('sig_drop')} & {cell('sig_flip')} & {cell('sig_add')} & {cell('sig_drop_frac', True)} \\\\")
        rows.append(r)
    nba = s[s.dataset.str.startswith("NBA")]

    def med(col, frac=False):
        v = nba[col]
        q1, m, q3 = np.percentile(v, [25, 50, 75])
        if frac:
            return f"{pct(m, 2)} {{\\tiny[{pct(q1, 2)},{pct(q3, 2)}]}}"
        return f"{m:g} {{\\tiny[{q1:g},{q3:g}]}}"
    lines.append(f"NBA 1990--2015$^\\dagger$ & sports & {int(nba.N.median()):,} & {int(nba.K.median())} & "
                 f"{nba.z_top12.median():.2f} & {med('top1_drop')} & {med('top1_flip')} & {med('top1_add')} & "
                 f"{med('top1_drop_frac', True)} & {med('sig_drop')} & {med('sig_flip')} & {med('sig_add')} & "
                 f"{med('sig_drop_frac', True)} \\\\")
    tex = "\n".join(lines)
    open(f"{TAB}/main_rows.tex", "w").write(tex + "\n")
    return s


def table_overview():
    rows = []
    for key in ["arena55k", "arena140k", "mt_human", "mt_gpt4"]:
        d = D.load(key)
        c = np.bincount(d.i, weights=d.n, minlength=d.K) + np.bincount(d.j, weights=d.n, minlength=d.K)
        npairs_obs = len(set(zip(d.i[d.n > 0], d.j[d.n > 0])))
        rows.append(dict(dataset=d.meta["name"], design=d.meta["design"], N=int(d.N), K=d.K,
                         tie=float((d.n * (d.y == 0.5)).sum() / d.N), pairs_obs=npairs_obs,
                         pairs_all=d.K * (d.K - 1) // 2, nmin=int(c.min()), nmed=int(np.median(c)),
                         nmax=int(c.max())))
    for y in [1990, 2015]:
        d = D.load(f"nba{y}")
        c = np.bincount(d.i, weights=d.n, minlength=d.K) + np.bincount(d.j, weights=d.n, minlength=d.K)
        npairs_obs = len(set(zip(np.minimum(d.i, d.j)[d.n > 0], np.maximum(d.i, d.j)[d.n > 0])))
        rows.append(dict(dataset=d.meta["name"], design="sports", N=int(d.N), K=d.K, tie=0.0,
                         pairs_obs=npairs_obs, pairs_all=d.K * (d.K - 1) // 2, nmin=int(c.min()),
                         nmed=int(np.median(c)), nmax=int(c.max())))
    df = pd.DataFrame(rows)
    df.to_csv(f"{RES}/derived_overview.csv", index=False)
    lines = [f"{r.dataset} & {r.design} & {r.N:,} & {r.K} & {100 * r.tie:.1f} & {r.pairs_obs}/{r.pairs_all} & "
             f"{r.nmin:,} / {r.nmed:,} / {r.nmax:,} \\\\" for r in df.itertuples()]
    open(f"{TAB}/overview_rows.tex", "w").write("\n".join(lines) + "\n")


# =========================================================================================
def fig_rule(q):
    """Verified minimal deletions vs z*sqrt(n_min) (rule of thumb) and vs first-order estimate."""
    fig, axs = plt.subplots(1, 2, figsize=(6.6, 2.6))
    x = q[q.z > 0.5]
    for g in ["NBA", "Arena-55k", "Arena-140k", "MT-Bench-Human", "MT-Bench-GPT4"]:
        xx = x[x.grp == g]
        axs[0].scatter(xx.z * np.sqrt(xx.nmin), xx.drop_best, s=4 if g == "NBA" else 9, alpha=0.35 if g == "NBA" else 0.8,
                       c=COL[g], label=g, lw=0)
        axs[1].scatter(xx.klin_drop, xx.drop_best, s=4 if g == "NBA" else 9, alpha=0.35 if g == "NBA" else 0.8,
                       c=COL[g], lw=0)
    for ax in axs:
        ax.set_xscale("log"); ax.set_yscale("log")
        lim = [0.7, 2000]
        ax.plot(lim, lim, "k--", lw=0.7)
        ax.set_xlim(lim); ax.set_ylim(lim)
        ax.set_ylabel("verified min. deletions $k^*_{\\rm drop}$")
    axs[0].set_xlabel("$z_{ij}\\sqrt{n_{\\min}}$  (rule of thumb)")
    axs[1].set_xlabel("first-order estimate $\\Delta_{ij}/\\ell_{ij}=z_{ij}\\sqrt{n_{\\rm eff}}$")
    axs[0].legend(loc="upper left", markerscale=1.5, frameon=False)
    fig.tight_layout()
    fig.savefig(f"{FIG}/rule_of_thumb.pdf")
    plt.close(fig)
    # derived statistics
    out = []
    for g, xx in x.groupby("grp"):
        r = xx.drop_best / (xx.z * np.sqrt(xx.nmin))
        r2 = xx.drop_best / xx.klin_drop
        out.append(dict(grp=g, n_pairs=len(xx), ratio_rule_median=r.median(), ratio_rule_q10=r.quantile(.1),
                        ratio_rule_q90=r.quantile(.9), ratio_lin_median=r2.median(), ratio_lin_q10=r2.quantile(.1),
                        ratio_lin_q90=r2.quantile(.9),
                        flip_over_drop=(xx.flip_best / xx.drop_best).median(),
                        add_over_drop=(xx.add_best / xx.drop_best).median()))
    lx = np.log(x.z * np.sqrt(x.nmin)); ly = np.log(x.drop_best)
    slope, icpt = np.polyfit(lx, ly, 1)
    out.append(dict(grp="ALL", n_pairs=len(x), ratio_rule_median=(x.drop_best / (x.z * np.sqrt(x.nmin))).median(),
                    loglog_slope=slope, loglog_intercept=icpt, loglog_r=np.corrcoef(lx, ly)[0, 1],
                    loglog_r_lin=np.corrcoef(np.log(x.klin_drop), ly)[0, 1],
                    loglog_r_zonly=np.corrcoef(np.log(x.z), ly)[0, 1]))
    pd.DataFrame(out).to_csv(f"{RES}/derived_rule.csv", index=False)


def fig_random_vs_adv():
    r = pd.read_csv(f"{RES}/e2_random.csv")
    s = pd.read_csv(f"{RES}/e1_summary.csv")
    r["grp"] = r.dataset.where(~r.dataset.str.startswith("NBA"), "NBA")
    s["grp"] = s.dataset.where(~s.dataset.str.startswith("NBA"), "NBA")
    fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.3), sharey=True)
    for ax, kind in zip(axs, ["drop", "flip", "add"]):
        for g in ["Arena-55k", "Arena-140k", "MT-Bench-Human", "MT-Bench-GPT4", "NBA"]:
            rr = r[(r.grp == g) & (r.kind == kind)].groupby("rate").any_sig_reversed.mean()
            ax.plot(rr.index, rr.values, "o-", c=COL[g], ms=3, lw=1, label=g)
            adv = s[s.grp == g][f"sig_{kind}_frac"].median()
            ax.axvline(adv, c=COL[g], ls=":", lw=1)
        ax.set_xscale("log")
        ax.set_xlim(1e-4, 0.2)
        ax.set_title(f"{kind}: random (lines) vs adversarial (dotted)")
        ax.set_xlabel("fraction of comparisons perturbed")
    axs[0].set_ylabel("P(some significant pair reversed)")
    axs[0].legend(frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(f"{FIG}/random_vs_adv.pdf")
    plt.close(fig)
    g = r.groupby(["grp", "kind", "rate"])[["top1_changed", "any_sig_reversed", "frac_sig_reversed",
                                              "kendall_tau"]].mean().reset_index()
    g.to_csv(f"{RES}/derived_random.csv", index=False)


def fig_scaling():
    if not os.path.exists(f"{RES}/e4_scaling.csv"):
        return
    s = pd.read_csv(f"{RES}/e4_scaling.csv")
    p = pd.read_csv(f"{RES}/e4_pairs.csv")
    fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.2))
    lab = {"arena55k": "Arena-55k", "arena140k": "Arena-140k", "mt_human": "MT-Bench-Human"}
    rows = []
    for src in ["arena55k", "arena140k", "mt_human"]:
        pp = p[(p.source == src) & (p.z > 0.5)].copy()
        pp["k_over_z"] = pp.drop_best / pp.z
        agg = pp.groupby(["frac", "seed"]).agg(N=("N", "first"), koz=("k_over_z", "median"),
                                               z=("z", "median"), kd=("drop_best", "median")).reset_index()
        agg["alpha"] = agg.kd / agg.N
        m = agg.groupby("frac").agg(N=("N", "mean"), koz=("koz", "median"), koz_lo=("koz", lambda v: np.percentile(v, 10)),
                                    koz_hi=("koz", lambda v: np.percentile(v, 90)), z=("z", "median"),
                                    alpha=("alpha", "median"))
        ss = s[s.source == src].groupby("frac").agg(sig=("sig_drop_frac", "median"), N=("N", "mean"))
        c = COL[lab[src]]
        axs[0].errorbar(m.N, m.koz, yerr=[m.koz - m.koz_lo, m.koz_hi - m.koz], c=c, marker="o", ms=3, lw=1,
                        capsize=2, label=lab[src])
        axs[1].plot(m.N, m.z, "o-", c=c, ms=3, lw=1)
        axs[2].plot(ss.N, ss.sig, "o-", c=c, ms=3, lw=1)
        for fr, rr in m.iterrows():
            rows.append(dict(source=src, frac=fr, N=rr.N, median_k_over_z=rr.koz, median_adj_z=rr.z,
                             median_adj_alpha=rr.alpha, sig_drop_frac=ss.loc[fr, "sig"]))
    Ns = np.logspace(2, 5.3, 10)
    axs[0].plot(Ns, 0.8 * np.sqrt(Ns / 20), "k:", lw=0.8, label="$\\propto\\sqrt{N}$")
    for ax in axs:
        ax.set_xscale("log")
        ax.set_xlabel("number of comparisons $N$ (subsample)")
    axs[0].set_yscale("log"); axs[2].set_yscale("log")
    axs[0].set_ylabel("median $k^*_{\\rm drop}/z$ (adjacent pairs)")
    axs[1].set_ylabel("median $z$ (adjacent pairs)")
    axs[2].set_ylabel("$k^*_{\\rm drop}/N$, least robust sig. pair")
    axs[0].legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{FIG}/scaling.pdf")
    plt.close(fig)
    pd.DataFrame(rows).to_csv(f"{RES}/derived_scaling.csv", index=False)


def fig_judges():
    if not os.path.exists(f"{RES}/e3_summary.csv"):
        return
    s = pd.read_csv(f"{RES}/e3_summary.csv")
    p = pd.read_csv(f"{RES}/e3_pairs.csv")
    # per judge: human vs judge metrics
    h = s[s.label_source == "human"].set_index("judge")
    j = s[s.label_source == "judge"].set_index("judge")
    cmp = pd.DataFrame({"agree": h.label_agreement, "N": h.N, "K": h.K,
                        "h_sig": h.sig_drop, "j_sig": j.sig_drop, "h_adj": h.adj_drop_median, "j_adj": j.adj_drop_median,
                        "h_top1": h.top1_drop, "j_top1": j.top1_drop, "h_nsig": h.n_sig_pairs, "j_nsig": j.n_sig_pairs,
                        "h_tie": h.tie_rate, "j_tie": j.tie_rate, "h_z12": h.z_top12, "j_z12": j.z_top12,
                        "h_top1name": h.top1, "j_top1name": j.top1})
    # rule-of-thumb ratio per label source (pairs with z > 0.5)
    rr = []
    for (judge, src), g in p.groupby(["judge", "label_source"]):
        g = g[g.z > 0.5]
        if judge == "gpt4":
            dh, _ = D.mtbench_matched()
        else:
            dh, _ = D.llmjudge_pair(judge)
        c = np.bincount(dh.i, weights=dh.n, minlength=dh.K) + np.bincount(dh.j, weights=dh.n, minlength=dh.K)
        nmin = np.minimum(c[g.hi.values], c[g.lo.values])
        adj = g[g.roles.str.contains("adjacent")]
        rr.append(dict(judge=judge, label_source=src, rule_ratio=float(np.median(g.drop_best / (g.z * np.sqrt(nmin)))),
                       adj_z_median=float(adj.z.median()) if len(adj) else np.nan,
                       adj_neff_over_nmin=float(np.median(g.neff_drop / nmin))))
    rr = pd.DataFrame(rr)
    cmp = cmp.join(rr[rr.label_source == "human"].set_index("judge")[["rule_ratio", "adj_z_median"]].add_prefix("h_"))
    cmp = cmp.join(rr[rr.label_source == "judge"].set_index("judge")[["rule_ratio", "adj_z_median"]].add_prefix("j_"))
    cmp.to_csv(f"{RES}/derived_judges.csv")
    a = cmp.drop(index="gpt4", errors="ignore")
    fig, axs = plt.subplots(1, 3, figsize=(6.8, 2.3))
    axs[0].scatter(a.agree, a.j_adj_z_median / a.h_adj_z_median, c="C4", s=12)
    axs[0].axhline(1, c="k", lw=0.6, ls="--")
    axs[0].set_xlabel("label agreement with crowd")
    axs[0].set_ylabel("median adjacent $z$: judge / crowd")
    axs[1].scatter(a.h_adj, a.j_adj, c="C4", s=12)
    m = max(a.h_adj.max(), a.j_adj.max()) * 1.2
    axs[1].plot([0.8, m], [0.8, m], "k--", lw=0.6)
    axs[1].set_xscale("log"); axs[1].set_yscale("log")
    axs[1].set_xlabel("crowd labels: median adj. $k^*_{\\rm drop}$")
    axs[1].set_ylabel("LLM-judge labels: median adj. $k^*_{\\rm drop}$")
    axs[2].scatter(a.h_rule_ratio, a.j_rule_ratio, c="C4", s=12)
    axs[2].plot([0.5, 1.3], [0.5, 1.3], "k--", lw=0.6)
    axs[2].set_xlabel("crowd: median $k^*/(z\\sqrt{n_{\\min}})$")
    axs[2].set_ylabel("judge: median $k^*/(z\\sqrt{n_{\\min}})$")
    fig.tight_layout()
    fig.savefig(f"{FIG}/judges.pdf")
    plt.close(fig)
    return cmp


def fig_schedule():
    if not os.path.exists(f"{RES}/e6_schedule.csv"):
        return
    s = pd.read_csv(f"{RES}/e6_schedule.csv")
    p = pd.read_csv(f"{RES}/e6_pairs.csv")
    p["rho"] = np.sqrt(p.neff_drop / p.N)
    agg = p.groupby(["source", "schedule", "seed"]).agg(rho=("rho", "median"), z=("z", "median"),
                                                         kd=("drop_best", "median")).reset_index()
    t = agg.groupby(["source", "schedule"]).agg(rho=("rho", "mean"), rho_sd=("rho", "std"), z=("z", "mean"),
                                                 kd=("kd", "mean"))
    ss = s.groupby(["source", "schedule"]).agg(sig_drop=("sig_drop", "median"), sig_lo=("sig_drop", lambda v: np.percentile(v, 10)),
                                               sig_hi=("sig_drop", lambda v: np.percentile(v, 90)),
                                               top1_drop=("top1_drop", "median"), nsig=("n_sig_pairs", "median"))
    t = t.join(ss)
    t.to_csv(f"{RES}/derived_schedule.csv")
    return t


def tables_ablation():
    out = {}
    for f in ["e7_ties", "e7_lambda", "e7_step", "e7_exact_k1"]:
        if os.path.exists(f"{RES}/{f}.csv"):
            out[f] = pd.read_csv(f"{RES}/{f}.csv")
    return out


def nba_fig():
    s = pd.read_csv(f"{RES}/e1_summary.csv")
    nba = s[s.dataset.str.startswith("NBA")].copy()
    nba["year"] = nba.dataset.str[4:].astype(int)
    fig, ax = plt.subplots(figsize=(3.3, 2.1))
    ax.plot(nba.year, nba.top1_drop, "o-", ms=3, lw=1, c="C2", label="top-1 change (drop)")
    ax.plot(nba.year, nba.sig_drop, "s-", ms=3, lw=1, c="C7", label="least robust sig. pair (drop)")
    ax2 = ax.twinx()
    ax2.plot(nba.year, nba.z_top12, "^:", ms=3, lw=0.8, c="C1")
    ax2.set_ylabel("$z$ of top-2 gap", color="C1")
    ax.set_xlabel("NBA season"); ax.set_ylabel("games to delete")
    ax.legend(frameon=False, fontsize=6, loc="upper left")
    fig.tight_layout()
    fig.savefig(f"{FIG}/nba_seasons.pdf")
    plt.close(fig)


if __name__ == "__main__":
    table_overview()
    table_main()
    p = add_nmin(pd.read_csv(f"{RES}/e1_pairs.csv"))
    p.to_csv(f"{RES}/derived_e1_pairs_nmin.csv", index=False)
    fig_rule(p)
    fig_random_vs_adv()
    fig_scaling()
    fig_judges()
    fig_schedule()
    nba_fig()
    print("done")
