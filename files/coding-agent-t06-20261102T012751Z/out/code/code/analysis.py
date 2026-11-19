"""Turns results/*.csv into the paper's tables (paper/tables/*.tex), figures (paper/figs/*.pdf)
and auto-generated number macros (paper/numbers.tex).  Run after run_all.sh."""
import json, os, warnings
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm

import datasets as ds

R = "/work/results"; P = "/work/paper"
os.makedirs(f"{P}/tables", exist_ok=True); os.makedirs(f"{P}/figs", exist_ok=True)
warnings.filterwarnings("ignore")
rng = np.random.default_rng(2024)

plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150,
                     "axes.spines.top": False, "axes.spines.right": False})
# colour-blind-safe palette (Okabe-Ito subset)
COL = {"arena": "#0072B2", "mt_human": "#D55E00", "mt_gpt4": "#009E73", "nba": "#CC79A7",
       "st_human": "#0072B2", "st_athene70b": "#E69F00", "st_llama3_8b": "#56B4E9", "st_mistral7b": "#999999"}
NAME = {"arena": "Arena-55k (crowd)", "mt_human": "MT-Bench (experts)", "mt_gpt4": "MT-Bench (GPT-4 judge)",
        "nba": "NBA seasons (games)", "arena140k": "Arena-140k (crowd, 2025)",
        "st_human": "Arena single-turn, humans", "st_human_noties": "Arena single-turn, humans (no ties)",
        "st_athene70b": "Arena single-turn, Athene-70B", "st_llama3_8b": "Arena single-turn, Llama-3-8B-Inst.",
        "st_mistral7b": "Arena single-turn, Mistral-7B-Inst.", "mt_human_noties": "MT-Bench (experts, no ties)"}
KINDS = ["drop", "relabel", "insert"]
KNAME = {"drop": "delete", "relabel": "relabel", "insert": "insert"}
NUM = {}   # macro name -> string


def dsname(b):
    return "nba" if b.startswith("nba") else b


def load_pairs(fn):
    d = pd.read_csv(f"{R}/{fn}")
    d["ds"] = d.board.map(dsname)
    d["z"] = d.gap / d.se
    d["alpha"] = d.k / d.n
    d["phi"] = d.k / (d.z * np.sqrt(d.ntouch))
    d["kappa"] = d.k / (d.gap * d.ntouch)
    d["adj"] = d.rj == d.ri + 1
    return d


def fmt(x, p=2):
    return f"{x:.{p}f}"


def macro(name, val):
    NUM[name] = val


def pct(x, p=2):
    if 0 < x < 1e-4 and p == 2:
        p = 3
    return f"{100 * x:.{p}f}\\%"


# ------------------------------------------------------------------ bootstrap helpers
def cluster_boot_median(df, col, cluster, B=2000):
    """Median of df[col] with a cluster bootstrap CI (clusters resampled with replacement)."""
    groups = [g[col].values for _, g in df.groupby(cluster)]
    med = float(np.median(df[col].values))
    bs = []
    for _ in range(B):
        idx = rng.integers(0, len(groups), len(groups))
        bs.append(np.median(np.concatenate([groups[i] for i in idx])))
    return med, float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    main_df = load_pairs("pairs.csv")
    jd = load_pairs("pairs_judges.csv")
    boot = load_pairs("boot.csv")
    ctl = load_pairs("control.csv")
    rnd = pd.read_csv(f"{R}/random.csv"); rnd["ds"] = rnd.board.map(dsname)
    a140 = load_pairs("pairs_arena140k.csv")
    allp = pd.concat([main_df, jd, a140], ignore_index=True)
    flip = allp[(allp["mode"] == "flip") & np.isfinite(allp.k)]
    sig = allp[(allp["mode"] == "sig") & np.isfinite(allp.k)]

    # ------------------------------------------------ Table 1: data summary
    boards = {"arena": ds.arena55k(), "mt_human": ds.mtbench_human(), "mt_gpt4": ds.mtbench_gpt4()}
    nba = ds.nba_seasons()
    rows = []
    for key, b in boards.items():
        pr = main_df[main_df.board == key]
        rows.append(dict(key=key, n=b.n, m=b.m, tie=b.N[:, 1].sum() / b.n, npairs=len(b.pairs),
                         zsig=(pr[pr["mode"] == "flip"].drop_duplicates(["i", "j"]).z > 1.96).mean(),
                         adj_sig=(pr[(pr["mode"] == "flip") & pr.adj].drop_duplicates(["i", "j"]).z > 1.96).mean()))
    ns = np.array([b.n for b in nba.values()]); ms = np.array([b.m for b in nba.values()])
    pr = main_df[main_df.ds == "nba"]
    pr0 = pr[(pr["mode"] == "flip") & (pr.kind == "drop")]
    rows.append(dict(key="nba", n=np.median(ns), m=np.median(ms), tie=0.0, npairs=np.nan,
                     zsig=(pr0.z > 1.96).mean(), adj_sig=(pr0[pr0.adj].z > 1.96).mean()))
    b140 = ds.arena140k(); pr = a140[(a140["mode"] == "flip") & (a140.kind == "drop")]
    rows.append(dict(key="arena140k", n=b140.n, m=b140.m, tie=b140.N[:, 1].sum() / b140.n, npairs=len(b140.pairs),
                     zsig=(pr.z > 1.96).mean(), adj_sig=(pr[pr.adj].z > 1.96).mean()))
    T1 = pd.DataFrame(rows)
    macro("nbaSeasons", str(len(nba))); macro("nbaNmin", str(int(ns.min()))); macro("nbaNmax", str(int(ns.max())))
    macro("nbaMmin", str(int(ms.min()))); macro("nbaMmax", str(int(ms.max())))
    with open(f"{P}/tables/data.tex", "w") as f:
        f.write("\\begin{tabular}{lrrrrrr}\\toprule\n")
        f.write("Leaderboard & votes $n$ & items $m$ & ties & pairs $z{>}1.96$ & adj. pairs $z{>}1.96$ \\\\\\midrule\n")
        for _, r in T1.iterrows():
            nn = f"{int(r.n):,}".replace(",", "{,}")
            if r.key == "nba":
                nn = f"{int(r.n):,}".replace(",", "{,}") + "$^\\dagger$"
                mm = f"{int(r.m)}$^\\dagger$"
            else:
                mm = f"{int(r.m)}"
            f.write(f"{NAME[r.key]} & {nn} & {mm} & {pct(r.tie, 0)} & {pct(r.zsig, 0)} & {pct(r.adj_sig, 0)} \\\\\n")
        f.write("\\bottomrule\\end{tabular}\n")
    for _, r in T1.iterrows():
        macro(f"zsig{r.key.replace('_', '')}", pct(r.zsig, 0)); macro(f"adjsig{r.key.replace('_', '')}", pct(r.adj_sig, 0))

    # ------------------------------------------------ Table 2: phi, kappa
    # z>2 flip pairs; CIs: season bootstrap (NBA), vote bootstrap replicates (others)
    g = flip[flip.z > 2]
    bg = boot[(boot["mode"] == "flip") & (boot.src == "rand") & np.isfinite(boot.k) & (boot.z > 2)]
    rows = []
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba", "arena140k"]:
        for kind in KINDS:
            x = g[(g.ds == d_) & (g.kind == kind)]
            if d_ == "arena140k":
                mphi = (x.phi.median(), np.nan, np.nan); mkap = (x.kappa.median(), np.nan, np.nan)
            elif d_ == "nba":
                x2 = x.assign(season=x.board)
                mphi = cluster_boot_median(x2, "phi", "season"); mkap = cluster_boot_median(x2, "kappa", "season")
            else:
                bb = bg[(bg.ds == d_) & (bg.kind == kind)]
                per = bb.groupby("rep").agg(phi=("phi", "median"), kappa=("kappa", "median"))
                mphi = (x.phi.median(), per.phi.quantile(.025), per.phi.quantile(.975))
                mkap = (x.kappa.median(), per.kappa.quantile(.025), per.kappa.quantile(.975))
            rows.append(dict(ds=d_, kind=kind, n=len(x), phi=mphi, kappa=mkap,
                             phi_q=(x.phi.quantile(.1), x.phi.quantile(.9))))
    T2 = pd.DataFrame(rows)
    with open(f"{P}/tables/phi.tex", "w") as f:
        f.write("\\begin{tabular}{llrccc}\\toprule\n")
        f.write("Leaderboard & edit & pairs & $\\hat\\varphi$ [95\\% CI] & pair spread (10--90\\%) & $\\hat\\kappa$ [95\\% CI] \\\\\\midrule\n")
        for d_ in ["arena", "mt_human", "mt_gpt4", "nba", "arena140k"]:
            for kind in KINDS:
                r = T2[(T2.ds == d_) & (T2.kind == kind)].iloc[0]
                ci = lambda t, p: (f"{t[0]:.{p}f} [{t[1]:.{p}f}, {t[2]:.{p}f}]" if np.isfinite(t[1]) else f"{t[0]:.{p}f} [n/a]")
                f.write(f"{NAME[d_] if kind == 'drop' else ''} & {KNAME[kind]} & {r.n} & "
                        f"{ci(r.phi, 2)} & {r.phi_q[0]:.2f}--{r.phi_q[1]:.2f} & {ci(r.kappa, 3)} \\\\\n")
            if d_ != "arena140k":
                f.write("\\addlinespace\n")
        f.write("\\bottomrule\\end{tabular}\n")
    for _, r in T2.iterrows():
        k = f"{r.ds.replace('_', '')}{r.kind}"
        macro(f"phi{k}", fmt(r.phi[0])); macro(f"kappa{k}", fmt(r.kappa[0], 3))
    # range of dataset medians across designs
    for kind in KINDS:
        v = T2[T2.kind == kind].phi.map(lambda t: t[0])
        macro(f"phimin{kind}", fmt(v.min())); macro(f"phimax{kind}", fmt(v.max()))
        v = T2[T2.kind == kind].kappa.map(lambda t: t[0])
        macro(f"kappamin{kind}", fmt(v.min(), 3)); macro(f"kappamax{kind}", fmt(v.max(), 3))

    # ------------------------------------------------ scaling regression  log k = a_d + b log z + c log ntouch
    rows = []
    for kind in KINDS:
        x = g[(g.kind == kind) & g.ds.isin(["arena", "mt_human", "mt_gpt4", "nba"])].copy()
        x["cl"] = np.where(x.ds == "nba", x.board, x.index.astype(str))
        def fit(xx):
            D = pd.get_dummies(xx.ds).astype(float).values
            A = np.column_stack([D, np.log(xx.z), np.log(xx.ntouch)])
            coef, *_ = np.linalg.lstsq(A, np.log(xx.k), rcond=None)
            res = np.log(xx.k) - A @ coef
            return coef[-2:], res.std()
        (b, c), sd = fit(x)
        # cluster bootstrap
        cl = x.cl.unique(); grp = {k: v for k, v in x.groupby("cl")}
        bs = []
        for _ in range(200):
            pick = rng.choice(len(cl), len(cl))
            xx = pd.concat([grp[cl[i]] for i in pick])
            bs.append(fit(xx)[0])
        bs = np.array(bs)
        rows.append(dict(kind=kind, b=b, c=c, b_ci=np.percentile(bs[:, 0], [2.5, 97.5]), c_ci=np.percentile(bs[:, 1], [2.5, 97.5]), sd=sd))
        macro(f"slopez{kind}", fmt(b)); macro(f"slopen{kind}", fmt(c)); macro(f"resid{kind}", fmt(sd))
        macro(f"slopezlo{kind}", fmt(np.percentile(bs[:, 0], 2.5))); macro(f"slopezhi{kind}", fmt(np.percentile(bs[:, 0], 97.5)))
        macro(f"slopenlo{kind}", fmt(np.percentile(bs[:, 1], 2.5))); macro(f"slopenhi{kind}", fmt(np.percentile(bs[:, 1], 97.5)))
    # ratio linearised/verified
    x = flip[(flip.z > 2) & np.isfinite(flip.k_lin) & flip.ds.isin(["arena", "mt_human", "mt_gpt4", "nba"])].copy()
    x["r"] = x.k_lin / x.k
    for kind in KINDS:
        v = x[x.kind == kind].r
        macro(f"linratio{kind}", fmt(v.median())); macro(f"linratiolo{kind}", fmt(v.quantile(.1))); macro(f"linratiohi{kind}", fmt(v.quantile(.9)))

    # ------------------------------------------------ Fig 1: collapse
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.4), sharex=True, sharey=True)
    for ax, kind in zip(axes, KINDS):
        for d_ in ["nba", "arena", "mt_human", "mt_gpt4"]:
            x = flip[(flip.ds == d_) & (flip.kind == kind) & (flip.z > 0.3)]
            if len(x) > 1500:
                x = x.sample(1500, random_state=1)
            ax.scatter(x.z, x.k / np.sqrt(x.ntouch), s=3 if d_ != "mt_human" and d_ != "mt_gpt4" else 14,
                       alpha=0.25 if d_ in ("nba", "arena") else 0.9, color=COL[d_], lw=0, label=NAME[d_],
                       marker="o" if d_ != "mt_gpt4" else "^")
        zz = np.array([0.3, 40])
        ph = T2[(T2.kind == kind)].phi.map(lambda t: t[0]).median()
        ax.plot(zz, ph * zz, "k--", lw=0.8, label=f"$k=\\varphi z\\sqrt{{n_{{ij}}}}$, $\\varphi$={ph:.2f}")
        ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(f"{KNAME[kind]} votes")
        ax.set_xlabel("$z=\\hat\\Delta_{ij}/\\mathrm{se}$")
    axes[0].set_ylabel("$k^*/\\sqrt{n_{ij}}$  (edits / $\\sqrt{\\text{votes on }i,j}$)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h[:4], l[:4], loc="lower center", ncol=4, frameon=False, markerscale=3, bbox_to_anchor=(0.5, -0.08))
    for ax in axes:
        ax.plot([], [])
    axes[0].legend(h[4:], l[4:], loc="upper left", frameon=False)
    for ax, kind in zip(axes[1:], KINDS[1:]):
        ph = T2[(T2.kind == kind)].phi.map(lambda t: t[0]).median()
        ax.legend([ax.lines[0]], [f"$\\varphi$={ph:.2f}"], loc="upper left", frameon=False)
    fig.tight_layout(); fig.savefig(f"{P}/figs/collapse.pdf", bbox_inches="tight"); plt.close(fig)

    # ------------------------------------------------ Table 3 + Fig 2: claims
    lead = []
    for key in ["arena", "mt_human", "mt_gpt4"] + sorted(b for b in main_df.board.unique() if b.startswith("nba")):
        for kind in KINDS:
            f_ = main_df[(main_df.board == key) & (main_df.kind == kind)]
            fl = f_[f_["mode"] == "flip"]; sg = f_[(f_["mode"] == "sig") & np.isfinite(f_.k)]
            top1 = fl[fl.ri == 0].k.min()
            adj = fl[fl.adj]
            lead.append(dict(board=key, ds=dsname(key), kind=kind, n=fl.n.iloc[0], top1=top1,
                             top1_frac=top1 / fl.n.iloc[0],
                             adj_sig_share=(adj.z > 1.96).mean(),
                             weakest=sg.k.min() if len(sg) else np.nan,
                             weakest_frac=(sg.k.min() / fl.n.iloc[0]) if len(sg) else np.nan,
                             nsig=len(sg),
                             med_sig_frac=(sg.k / sg.n).median() if len(sg) else np.nan,
                             med_sig_k=sg.k.median() if len(sg) else np.nan,
                             sig_le1=(sg.k / sg.n <= 0.01).mean() if len(sg) else np.nan,
                             sig_le_touch5=(sg.k / sg.ntouch <= 0.05).mean() if len(sg) else np.nan))
    L = pd.DataFrame(lead)
    L.to_csv(f"{R}/leaderboard_level.csv", index=False)
    with open(f"{P}/tables/leader.tex", "w") as f:
        f.write("\\begin{tabular}{llrrrr}\\toprule\n")
        f.write("Leaderboard & edit & top-1 reversal & median sig.\\ pair & sig.\\ pairs $\\le$1\\% of $n$ & sig.\\ pairs $\\le$5\\% of $n_{ij}$ \\\\\n")
        f.write(" & & votes (\\% of $n$) & votes (\\% of $n$) & share & share \\\\\\midrule\n")
        for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
            for kind in KINDS:
                x = L[(L.ds == d_) & (L.kind == kind)]
                tp = x.top1.median(); tf = x.top1_frac.median(); w = x.weakest.median(); wf = x.weakest_frac.median()
                ms_ = x.med_sig_frac.median(); mk = x.med_sig_k.median(); s1 = x.sig_le1.mean(); s5 = x.sig_le_touch5.mean()
                f.write(f"{NAME[d_] if kind == 'drop' else ''} & {KNAME[kind]} & {tp:.0f} ({pct(tf, 2)}) & {mk:.0f} ({pct(ms_, 2)}) & "
                        f"{pct(s1, 0)} & {pct(s5, 0)} \\\\\n")
                macro(f"top1{d_.replace('_', '')}{kind}", f"{tp:.0f}"); macro(f"weak{d_.replace('_', '')}{kind}", f"{w:.0f}")
                macro(f"top1frac{d_.replace('_', '')}{kind}", pct(tf, 2)); macro(f"weakfrac{d_.replace('_', '')}{kind}", pct(wf, 2))
                macro(f"medsig{d_.replace('_', '')}{kind}", pct(ms_, 2)); macro(f"sigle1{d_.replace('_', '')}{kind}", pct(s1, 0))
            if d_ != "nba":
                f.write("\\addlinespace\n")
        f.write("\\bottomrule\\end{tabular}\n")

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3))
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        # (a) adjacent pairs: alpha to reverse, relabel
        x = flip[(flip.ds == d_) & (flip.kind == "relabel") & flip.adj].alpha.sort_values().values
        axes[0].step(x, np.arange(1, len(x) + 1) / len(x), color=COL[d_], label=NAME[d_], where="post")
        # (b) significant pairs: alpha_sig
        x = sig[(sig.ds == d_) & (sig.kind == "relabel")].alpha.sort_values().values
        axes[1].step(x, np.arange(1, len(x) + 1) / len(x), color=COL[d_], where="post")
        # (c) same, per-touching vote
        x = (sig[(sig.ds == d_) & (sig.kind == "relabel")].k / sig[(sig.ds == d_) & (sig.kind == "relabel")].ntouch).sort_values().values
        axes[2].step(x, np.arange(1, len(x) + 1) / len(x), color=COL[d_], where="post")
    axes[0].set_title("(a) reverse adjacent pair"); axes[1].set_title("(b) erase significance (all sig. pairs)")
    axes[2].set_title("(c) as (b), per vote on the two items")
    axes[0].set_xlabel("relabelled votes / $n$"); axes[1].set_xlabel("relabelled votes / $n$")
    axes[2].set_xlabel("relabelled votes / $n_{ij}$")
    for ax in axes:
        ax.set_xscale("log"); ax.set_ylim(0, 1.02)
    axes[0].set_ylabel("cumulative share of pairs")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=4, frameon=False, bbox_to_anchor=(0.5, -0.1))
    fig.tight_layout(); fig.savefig(f"{P}/figs/claims.pdf", bbox_inches="tight"); plt.close(fig)

    # ------------------------------------------------ Fig 3: random vs adversarial
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.3))
    ax = axes[0]
    adjp = main_df[(main_df["mode"] == "flip") & main_df.adj & (main_df.kind == "drop")].drop_duplicates(["board", "i", "j"])
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        rr = rnd[(rnd.ds == d_) & (rnd["mode"] == "drop")]
        al = sorted(rr.alpha.unique())
        emp = [rr[rr.alpha == a].groupby("board").rev_frac.mean().mean() for a in al]
        zs = adjp[adjp.ds == d_]
        zs = zs.assign(zz=zs.z)
        pred = []
        for a in al:
            # board-level mean of Phi(-z sqrt((1-a)/a)); a = fraction removed
            pr_ = zs.groupby("board").zz.apply(lambda v: np.mean(norm.cdf(-v * np.sqrt((1 - a) / a))))
            pred.append(pr_.mean())
        ax.plot(al, emp, "o-", color=COL[d_], ms=3, label=NAME[d_])
        ax.plot(al, pred, "--", color=COL[d_], lw=0.9)
        macro(f"randval{d_.replace('_', '')}", fmt(np.mean(np.abs(np.array(emp) - np.array(pred))), 3))
    ax.set_xscale("log"); ax.set_xlabel("fraction of votes deleted at random"); ax.set_ylabel("share of adjacent pairs reversed")
    ax.set_title("(a) random deletion: simulation (solid)\nvs. $\\Phi(-z\\sqrt{(1-\\alpha)/\\alpha})$ (dashed)")
    ax = axes[1]
    zg = np.linspace(2, 30, 100)
    ax.plot(zg, zg ** 2 / (zg ** 2 + 1.645 ** 2), "k-", lw=1, label="random deletion (5% reversal prob.)")
    bins = np.array([2, 3, 4, 6, 9, 14, 25, 60])
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        x = flip[(flip.ds == d_) & (flip.kind == "relabel") & (flip.z > 2)]
        x = x.assign(b=pd.cut(x.z, bins), a_t=x.k / x.ntouch)
        gg = x.groupby("b", observed=True).agg(z=("z", "median"), a=("a_t", "median"), n=("z", "size"))
        gg = gg[gg.n >= 3]
        ax.plot(gg.z, gg.a, "o-", ms=3, color=COL[d_], label=f"{NAME[d_]}")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("$z$ of the pair"); ax.set_ylabel("edited fraction of the $n_{ij}$ votes")
    from matplotlib.ticker import FixedLocator, NullFormatter, FixedFormatter
    ax.xaxis.set_major_locator(FixedLocator([2, 5, 10, 20])); ax.xaxis.set_major_formatter(FixedFormatter(["2", "5", "10", "20"])); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_title("(b) edits needed to reverse a pair")
    ax.legend(frameon=False, fontsize=5.5, loc="upper left", bbox_to_anchor=(1.02, 1.0), title="adversarial relabelling\n(coloured), vs. random\ndeletion (black)", title_fontsize=5.5)
    fig.tight_layout(); fig.savefig(f"{P}/figs/random.pdf", bbox_inches="tight"); plt.close(fig)
    # key numbers for random baseline
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        for mode in ("drop", "relabel"):
            rr = rnd[(rnd.ds == d_) & (rnd["mode"] == mode) & (rnd.alpha == 0.05)]
            macro(f"tau5{d_.replace('_', '')}{mode}", fmt(rr.groupby("board").tau.mean().mean(), 3))
            rr = rnd[(rnd.ds == d_) & (rnd["mode"] == mode) & (rnd.alpha == 0.5)]
            macro(f"tau50{d_.replace('_', '')}{mode}", fmt(rr.groupby("board").tau.mean().mean(), 3))

    # ------------------------------------------------ Controls
    c = ctl[(ctl["mode"] == "flip") & np.isfinite(ctl.k)]
    # A: matched six
    A = c[c.part == "A"]
    A6 = A[A.label.isin(["arena6", "mt_human_n1367", "mt_gpt4_n1367"])]
    rows = []
    for lab in ["arena6", "mt_human_n1367", "mt_gpt4_n1367"]:
        for kind in KINDS:
            x = A6[(A6.label == lab) & (A6.kind == kind)]
            per = x.groupby("rep").agg(z=("z", "median"), alpha=("alpha", "median"), phi=("phi", lambda v: np.nan), kappa=("kappa", "median"))
            xz = x[x.z > 2]
            perphi = xz.groupby("rep").phi.median(); perkap = xz.groupby("rep").kappa.median()
            xa = ctl[(ctl.part == "A") & (ctl.label == lab) & (ctl.kind == kind) & (ctl["mode"] == "flip")]  # incl. censored
            peralpha = xa.groupby("rep").alpha.median(); perz = xa.groupby("rep").z.median()
            if lab == "arena6":   # point estimate on the real data; +- from vote bootstrap replicates
                xb = ctl[(ctl.label == "arena6_boot") & (ctl.kind == kind) & (ctl["mode"] == "flip")]
                xbz = xb[np.isfinite(xb.k) & (xb.z > 2)]
                perz = xb.groupby("rep").z.median(); peralpha = xb.groupby("rep").alpha.median()
                perphi = xbz.groupby("rep").phi.median(); perkap = xbz.groupby("rep").kappa.median()
                x0 = xa; x0z = x[x.z > 2]
                rows.append(dict(label=lab, kind=kind, n=int(x.n.iloc[0]),
                                 z=x0.z.median(), z_sd=perz.std(), alpha=x0.alpha.median(), alpha_sd=peralpha.std(),
                                 phi=x0z.phi.median(), phi_sd=perphi.std(), kappa=x0z.kappa.median(), kappa_sd=perkap.std(),
                                 nrep=xb.rep.nunique()))
                continue
            rows.append(dict(label=lab, kind=kind, n=int(x.n.iloc[0]),
                             z=perz.mean(), z_sd=perz.std(), alpha=peralpha.mean(), alpha_sd=peralpha.std(),
                             phi=perphi.mean(), phi_sd=perphi.std(), kappa=perkap.mean(), kappa_sd=perkap.std(),
                             nrep=x.rep.nunique()))
    TA = pd.DataFrame(rows); TA.to_csv(f"{R}/control_matched.csv", index=False)
    with open(f"{P}/tables/matched.tex", "w") as f:
        f.write("\\begin{tabular}{llrrrrr}\\toprule\n")
        f.write("Labels (same 6 models) & edit & $n$ & median $z$ & median $k^*/n$ & $\\hat\\varphi$ & $\\hat\\kappa$ \\\\\\midrule\n")
        nm = {"arena6": "Arena crowd (all available)", "mt_human_n1367": "MT-Bench experts (subsample)", "mt_gpt4_n1367": "MT-Bench GPT-4 (subsample)"}
        for lab in ["arena6", "mt_human_n1367", "mt_gpt4_n1367"]:
            for kind in KINDS:
                r = TA[(TA.label == lab) & (TA.kind == kind)].iloc[0]
                pm = "$\\pm$" if r.nrep > 1 else ""
                a_s = pct(r.alpha, 1) + (pm + pct(r.alpha_sd, 1) if r.nrep > 1 else "")
                z_s = f"{r.z:.2f}" + (pm + f"{r.z_sd:.2f}" if r.nrep > 1 else "")
                p_s = f"{r.phi:.2f}" + (pm + f"{r.phi_sd:.2f}" if r.nrep > 1 else "")
                k_s = f"{r.kappa:.3f}" + (pm + f"{r.kappa_sd:.3f}" if r.nrep > 1 else "")
                lab_s = nm[lab] if kind == "drop" else ""
                f.write(f"{lab_s} & {KNAME[kind]} & {r.n} & {z_s} & {a_s} & {p_s} & {k_s} \\\\\n")
            f.write("\\addlinespace\n")
        f.write("\\bottomrule\\end{tabular}\n")
    # B: scaling in n
    B_ = c[c.part == "B"]
    rows = []
    for lab, g_ in B_.groupby("label"):
        for kind in KINDS:
            x = g_[g_.kind == kind]; xz = x[x.z > 2]
            if len(xz) == 0:
                continue
            per = xz.groupby("rep").agg(phi=("phi", "median"), kappa=("kappa", "median"), alpha=("alpha", "median"), n=("n", "mean"))
            rows.append(dict(label=lab, kind=kind, n=per.n.mean(), phi=per.phi.mean(), phi_sd=per.phi.std(), kappa=per.kappa.mean(),
                             kappa_sd=per.kappa.std(), alpha=per.alpha.mean(), nrep=len(per),
                             z=xz.z.median()))
    TB = pd.DataFrame(rows); TB["ds"] = TB.label.map(lambda s: "arena" if s.startswith("arena") else ("mt_human" if s.startswith("mt_human") else ("mt_gpt4" if s.startswith("mt_gpt4") else "nba")))
    TB.to_csv(f"{R}/control_scaling.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.3))
    kinds_plot = {"relabel": "-", "drop": "--"}
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        for kind, ls in kinds_plot.items():
            x = TB[(TB.ds == d_) & (TB.kind == kind)].sort_values("n")
            if d_ == "nba":
                # pool over frac
                x = x.groupby("label").first().reset_index().sort_values("n")
            axes[0].errorbar(x.n, x.phi, yerr=x.phi_sd, color=COL[d_], ls=ls, marker="o", ms=3, lw=0.9, capsize=1.5,
                             label=NAME[d_] if kind == "relabel" else None)
            axes[1].plot(x.n, x.alpha, color=COL[d_], ls=ls, marker="o", ms=3, lw=0.9)
    # panel c: matched-six scatter of k/ntouch vs gap
    for lab, col, mk in [("arena6", COL["arena"], "o"), ("mt_human_n1367", COL["mt_human"], "s"), ("mt_gpt4_n1367", COL["mt_gpt4"], "^")]:
        x = A6[(A6.label == lab) & (A6.kind == "relabel")]
        x = x.groupby(["i", "j"]).agg(gap=("gap", "mean"), k=("k", "mean"), nt=("ntouch", "mean")).reset_index()
        axes[2].scatter(x.gap, x.k / x.nt, color=col, marker=mk, s=10, alpha=0.8, label={"arena6": "Arena crowd", "mt_human_n1367": "MT experts", "mt_gpt4_n1367": "MT GPT-4"}[lab])
    axes[0].set_xscale("log"); axes[1].set_xscale("log"); axes[1].set_yscale("log")
    axes[0].set_xlabel("votes $n$ (random subsample)"); axes[1].set_xlabel("votes $n$ (random subsample)")
    axes[0].set_ylabel("median $\\hat\\varphi$ ($z>2$)"); axes[1].set_ylabel("median $k^*/n$ ($z>2$)")
    axes[0].set_title("(a) $\\varphi$ vs. sample size\n(solid: relabel, dashed: delete)"); axes[1].set_title("(b) fraction of votes needed")
    axes[0].set_ylim(0, 0.9)
    axes[2].set_xlabel("BT gap $\\hat\\Delta_{ij}$ (log-odds)"); axes[2].set_ylabel("relabels $k^*/n_{ij}$")
    axes[2].set_title("(c) same six models, 15 pairs")
    axes[2].legend(frameon=False); axes[0].legend(frameon=False, fontsize=5.5, loc="lower right")
    fig.tight_layout(); fig.savefig(f"{P}/figs/control.pdf", bbox_inches="tight"); plt.close(fig)
    for lab in ["arena6", "mt_human_n1367", "mt_gpt4_n1367"]:
        for kind in KINDS:
            r = TA[(TA.label == lab) & (TA.kind == kind)].iloc[0]
            sl = {"arena6": "Arena", "mt_human_n1367": "MTH", "mt_gpt4_n1367": "MTG"}[lab]
            macro(f"A{sl}{kind}phi", fmt(r.phi)); macro(f"A{sl}{kind}kappa", fmt(r.kappa, 3))
            macro(f"A{sl}{kind}alpha", pct(r.alpha, 1)); macro(f"A{sl}{kind}z", fmt(r.z))
    macro("arenasixn", str(int(TA[TA.label == "arena6"].n.iloc[0])))

    # ------------------------------------------------ overtaking cost vs rank distance (insert / relabel)
    fig, axes = plt.subplots(1, 2, figsize=(5.2, 2.3))
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        for ax, kind in zip(axes, ["insert", "delete"]):
            kk = "insert" if kind == "insert" else "drop"
            x = flip[(flip.ds == d_) & (flip.kind == kk)].copy()
            x["r"] = x.rj - x.ri
            x = x[x.r <= 10]
            gg = x.groupby("r").alpha.agg(["median", lambda v: v.quantile(.25), lambda v: v.quantile(.75), "size"])
            gg.columns = ["med", "q1", "q3", "n"]
            ax.plot(gg.index, gg.med, "o-", ms=3, color=COL[d_], lw=1, label=NAME[d_])
            ax.fill_between(gg.index, gg.q1, gg.q3, color=COL[d_], alpha=0.12, lw=0)
            if kk == "insert":
                for r_ in (1, 5):
                    if r_ in gg.index:
                        macro(f"overtake{d_.replace('_', '')}r{r_}", pct(gg.loc[r_, "med"], 2))
                        macro(f"overtakek{d_.replace('_', '')}r{r_}", f"{(x[x.r == r_].k.median()):.0f}")
    for ax, t in zip(axes, ["(a) insert votes (rigging)", "(b) delete votes"]):
        ax.set_yscale("log"); ax.set_xlabel("rank positions overtaken"); ax.set_title(t)
    axes[0].set_ylabel("edits / $n$ (median, IQR)")
    h, l = axes[0].get_legend_handles_labels()
    fig.legend(h, l, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, -0.14))
    fig.tight_layout(); fig.savefig(f"{P}/figs/overtake.pdf", bbox_inches="tight"); plt.close(fig)

    # adjacent-pair medians
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        for kind in KINDS:
            x = flip[(flip.ds == d_) & (flip.kind == kind) & flip.adj]
            macro(f"adjk{d_.replace('_', '')}{kind}", f"{x.k.median():.0f}")
            macro(f"adjalpha{d_.replace('_', '')}{kind}", pct(x.alpha.median(), 3 if d_ == "arena" else 2))
            macro(f"adjz{d_.replace('_', '')}{kind}", fmt(x.z.median(), 2))
    ab = boards["arena"]; th_a = ab.fit(); o_a = np.argsort(-th_a[: ab.m])
    macro("arenatopa", ab.names[o_a[0]]); macro("arenatopb", ab.names[o_a[1]])
    macro("arenatopz", fmt((th_a[o_a[0]] - th_a[o_a[1]]) / ab.ij_se(th_a, o_a[0], o_a[1]), 2))
    macro("arenatopgap", fmt(173.7 * (th_a[o_a[0]] - th_a[o_a[1]]), 1))
    q = flip[(flip.ds != "nba") & (flip.kind == "relabel") & (flip.z > 2)]
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        x = flip[(flip.ds == d_) & (flip.kind == "relabel") & (flip.z > 2)]
        macro(f"sesqrtn{d_.replace('_', '')}", fmt((x.se * np.sqrt(x.ntouch)).median(), 1))
    for zv in (3, 5, 10):
        macro(f"randneed{zv}", pct(zv ** 2 / (zv ** 2 + 1.645 ** 2), 0))
    # NBA modern-era subset (>=1990) sensitivity of phi
    x = flip[(flip.ds == "nba") & (flip.z > 2)]
    x = x[x.board.str[3:].astype(int) >= 1990]
    for kind in KINDS:
        macro(f"phinbamodern{kind}", fmt(x[x.kind == kind].phi.median()))
    x = flip[(flip.ds == "nba") & (flip.z > 2)].assign(yr=lambda d: d.board.str[3:].astype(int))
    for kind in KINDS:
        q = x[x.kind == kind].groupby("board").phi.median()
        macro(f"phinbaseasonlo{kind}", fmt(q.quantile(.05))); macro(f"phinbaseasonhi{kind}", fmt(q.quantile(.95)))

    # ------------------------------------------------ Arena-140k replication
    for kind in KINDS:
        r = T2[(T2.ds == "arena140k") & (T2.kind == kind)].iloc[0]
        macro(f"phiarenaNew{kind}", fmt(r.phi[0])); macro(f"kappaarenaNew{kind}", fmt(r.kappa[0], 3))
        x = flip[(flip.ds == "arena140k") & (flip.kind == kind) & flip.adj]
        macro(f"adjkarenaNew{kind}", f"{x.k.median():.0f}")
    x = flip[(flip.ds == "arena140k") & (flip.kind == "drop")]
    macro("zsigarenaNew", pct((x.z > 1.96).mean(), 0)); macro("adjsigarenaNew", pct((x[x.adj].z > 1.96).mean(), 0))
    macro("arenaNewN", f"{int(x.n.iloc[0]):,}".replace(",", "{,}")); macro("arenaNewM", str(int(x.m.iloc[0])))
    dv = ds.arena140k_votes(); vc = dv.evaluation_session_id.value_counts()
    macro("arenaNewSessions", f"{len(vc):,}".replace(",", "{,}")); macro("arenaNewMulti", pct((vc[dv.evaluation_session_id.values].values > 1).mean(), 0))
    cd = pd.read_csv(f"{R}/cluster_arena140k.csv"); cd["r"] = cd.k_sessions / cd.k_votes
    macro("sessratio", fmt(cd.r.median(), 2)); macro("sessratiomin", fmt(cd.r.min(), 2)); macro("sessratiomax", fmt(cd.r.max(), 2)); macro("sesspairs", str(len(cd)))
    tp = pd.read_csv(f"{R}/temporal_arena140k.csv"); tt = tp[tp.kind == "temporal"].iloc[0]; tr = tp[tp.kind == "random"]
    macro("temptau", fmt(tt.tau, 3)); macro("randtau", fmt(tr.tau.mean(), 3)); macro("randtausd", fmt(tr.tau.std(), 3))
    macro("temprev", str(int(tt.rev))); macro("randrev", fmt(tr.rev.mean(), 1)); macro("randrevsd", fmt(tr.rev.std(), 1))
    macro("randrevmax", str(int(tr.rev.max()))); macro("tempp", fmt((tr.tau <= tt.tau).mean(), 2))
    macro("nsigtemp", str(int(tt.nsig))); macro("tempmodels", str(int(tt.nmodels))); macro("tempvotes", f"{int(tt.nvotes):,}".replace(",", "{,}"))

    # control-scaling macros
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        for kind in ("relabel", "drop"):
            x = TB[(TB.ds == d_) & (TB.kind == kind)]
            if d_ == "nba":
                x = x.groupby("label").first().reset_index()
            macro(f"scalephimin{d_.replace('_', '')}{kind}", fmt(x.phi.min())); macro(f"scalephimax{d_.replace('_', '')}{kind}", fmt(x.phi.max()))
    xa = TB[(TB.kind == "relabel") & (TB.label == "arena_n3000")].iloc[0]; xf = TB[(TB.kind == "relabel") & (TB.label == "arena_full")].iloc[0]
    macro("scalealphaarenasmall", pct(xa.alpha, 2)); macro("scalealphaarenafull", pct(xf.alpha, 2))
    xa = TB[(TB.kind == "drop") & (TB.label == "arena_n3000")].iloc[0]; xf = TB[(TB.kind == "drop") & (TB.label == "arena_full")].iloc[0]
    macro("scalealphadroparenasmall", pct(xa.alpha, 2)); macro("scalealphadroparenafull", pct(xf.alpha, 2))
    ab_ = pd.read_csv(f"{R}/ablate_ridge.csv"); ab_ = ab_[(ab_.gap / ab_.se > 2) & np.isfinite(ab_.k)]
    ab_["phi"] = ab_.k / ((ab_.gap / ab_.se) * np.sqrt(ab_.ntouch))
    pm = ab_.groupby(["board", "kind", "ridge"]).phi.median().unstack("ridge")
    macro("ridgemaxchg", pct(((pm[10.0] / pm[0.001]) - 1).abs().max(), 0))
    macro("ridgemaxchgsmall", pct(((pm[0.1] / pm[0.001]) - 1).abs().max(), 1))
    # ------------------------------------------------ search baselines
    bl = pd.read_csv(f"{R}/baselines.csv"); bl["ds"] = bl.board.map(dsname)
    w = bl.pivot_table(index=["board", "i", "j", "kind", "z"], columns="strategy", values="k").reset_index()
    w["ds"] = w.board.map(dsname)
    w = w[(w.z > 2) & np.isfinite(w.greedy)]
    rows = []
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        for kind in KINDS:
            x = w[(w.ds == d_) & (w.kind == kind)]
            rows.append(dict(ds=d_, kind=kind, n=len(x), touch_eq=(x.touch == x.greedy).mean(),
                             direct_inf=np.isinf(x.direct).mean(), random_ratio=np.median(x.random / x.greedy),
                             random_inf=np.isinf(x.random).mean(),
                             direct_ratio=np.median((x.direct / x.greedy)[np.isfinite(x.direct)]) if np.isfinite(x.direct).any() else np.nan))
    TBL = pd.DataFrame(rows)
    with open(f"{P}/tables/baselines.tex", "w") as f:
        f.write("\\begin{tabular}{llrrrrr}\\toprule\n")
        f.write("Leaderboard & edit & pairs & restrict to votes on $i,j$ = full search & only $i$--$j$ votes: infeasible & random helpful edits / ours (median) & random infeasible \\\\\\midrule\n")
        for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
            for kind in KINDS:
                r = TBL[(TBL.ds == d_) & (TBL.kind == kind)].iloc[0]
                f.write(f"{NAME[d_] if kind == 'drop' else ''} & {KNAME[kind]} & {r.n} & {pct(r.touch_eq, 0)} & {pct(r.direct_inf, 0)} & {r.random_ratio:.1f} & {pct(r.random_inf, 0)} \\\\\n")
            f.write("\\addlinespace\n")
        f.write("\\bottomrule\\end{tabular}\n")
    macro("basetoucheq", pct(TBL.touch_eq.min(), 0))
    macro("baserandmin", fmt(TBL.random_ratio.min(), 1)); macro("baserandmax", fmt(TBL.random_ratio.max(), 1))
    macro("basepairs", str(int(TBL.n.sum() / 3)))
    # ------------------------------------------------ cluster-level deletion (MT-Bench)
    cl = pd.read_csv(f"{R}/cluster.csv")
    cl["fq"] = cl.k_questions / cl.nq; cl["fv"] = cl.k_votes / cl.n
    cl["fqs"] = cl.k_questions_sig / cl.nq
    rows = []
    for b_ in ["mt_human", "mt_gpt4"]:
        x = cl[(cl.board == b_) & (cl.z > 2)]
        both = x[np.isfinite(x.k_votes) & np.isfinite(x.k_questions)]
        rows.append(dict(board=b_, npairs=len(x), fq=both.fq.median(), fv=both.fv.median(), ratio=(both.fq / both.fv).median(), rmin=(both.fq / both.fv).min(), rmax=(both.fq / both.fv).max(),
                         inf_q=np.isinf(x.k_questions).mean(), fqs=x.fqs.replace(np.inf, np.nan).median(),
                         nq=int(x.nq.iloc[0]), top1_q=cl[(cl.board == b_) & (cl.ri == 0)].k_questions.min()))
    TC = pd.DataFrame(rows); TC.to_csv(f"{R}/cluster_summary.csv", index=False)
    for _, r in TC.iterrows():
        sk = {"mt_human": "mth", "mt_gpt4": "mtg"}[r.board]
        macro(f"clq{sk}", pct(r.fq, 0)); macro(f"clv{sk}", pct(r.fv, 1)); macro(f"clratio{sk}", fmt(r.ratio, 1))
        macro(f"cltop{sk}", f"{r.top1_q:.0f}"); macro(f"clnq", str(r.nq)); macro(f"clpairs{sk}", str(int(r.npairs)))
    with open(f"{P}/tables/cluster.tex", "w") as f:
        f.write("\\begin{tabular}{lrrrrr}\\toprule\n")
        f.write("MT-Bench judgments & pairs ($z{>}2$) & questions removed (median share of 80) & votes deleted (median share) & ratio (range) & top-1 reversal (questions) \\\\\\midrule\n")
        for _, r in TC.iterrows():
            f.write(f"{NAME[r.board]} & {r.npairs} & {pct(r.fq, 0)} & {pct(r.fv, 1)} & {r.ratio:.1f} ({r.rmin:.1f}--{r.rmax:.1f}) & {r.top1_q:.0f} \\\\\n")
        f.write("\\bottomrule\\end{tabular}\n")
    # z in [4,6]
    for d_ in ["arena", "mt_human", "mt_gpt4", "nba"]:
        x = flip[(flip.ds == d_) & (flip.kind == "relabel") & (flip.z.between(4, 6))]
        macro(f"zfive{d_.replace('_', '')}", pct((x.k / x.ntouch).median(), 0) if len(x) else "n/a")
        macro(f"zfiven{d_.replace('_', '')}", str(len(x)))

    # ------------------------------------------------ Judges table
    rows = []
    for key in ["st_human", "st_human_noties", "st_athene70b", "st_llama3_8b", "st_mistral7b"]:
        b = jd[jd.board == key]
        fl = b[(b["mode"] == "flip")]
        board = {"st_human": None}
        for kind in ["relabel", "drop"]:
            x = fl[fl.kind == kind]
            xz = x[(x.z > 2) & np.isfinite(x.k)]
            adj = x[x.adj]
            rows.append(dict(key=key, kind=kind, n=int(x.n.iloc[0]), med_z=x.z.median(), adj_sig=(adj.z > 1.96).mean(),
                             sig_share=(x.z > 1.96).mean(), phi=xz.phi.median(), kappa=xz.kappa.median(),
                             med_gap=x.gap.median(), top1=x[x.ri == 0].k.min(),
                             alpha_sig=(sig[(sig.board == key) & (sig.kind == kind)].alpha.median())))
    TJ = pd.DataFrame(rows); TJ.to_csv(f"{R}/judges_table.csv", index=False)
    # score agreement
    st = {k: ds.arena_single_turn(j) for k, j in [("human", None), ("athene70b", "Athene-70B"), ("llama3_8b", "Meta-Llama-3-8B-Instruct"), ("mistral7b", "Mistral-7B-Instruct-v0.2")]}
    from scipy.stats import kendalltau
    th = {k: b.fit()[: b.m] for k, b in st.items()}
    tie = {k: b.N[:, 1].sum() / b.n for k, b in st.items()}
    nt = ds.arena_single_turn(None); N2 = nt.N.copy(); N2[:, 1] = 0; nt_b = nt.with_counts(N2); th["human_noties"] = nt_b.fit()[: nt.m]
    tie["human_noties"] = 0.0
    with open(f"{P}/tables/judges.tex", "w") as f:
        f.write("\\begin{tabular}{lrrrrrrr}\\toprule\n")
        f.write("Labels (same 49,938 battles) & ties & Kendall $\\tau$ vs.\\ humans & adj.\\ pairs $z{>}1.96$ & median $z$ & $\\hat\\varphi$ (relabel) & $\\hat\\kappa$ (relabel) & top-1 reversal (relabel) \\\\\\midrule\n")
        for key, th_k in [("st_human", "human"), ("st_human_noties", "human_noties"), ("st_athene70b", "athene70b"), ("st_llama3_8b", "llama3_8b"), ("st_mistral7b", "mistral7b")]:
            r = TJ[(TJ.key == key) & (TJ.kind == "relabel")].iloc[0]
            tau = kendalltau(th[th_k], th["human"])[0]
            f.write(f"{NAME[key].replace('Arena single-turn, ', '')} & {pct(tie[th_k], 0)} & {tau:.2f} & {pct(r.adj_sig, 0)} & {r.med_z:.1f} & {r.phi:.2f} & {r.kappa:.3f} & {r.top1:.0f} \\\\\n")
            sj = {"st_human": "human", "st_human_noties": "humannoties", "st_athene70b": "athene", "st_llama3_8b": "llama", "st_mistral7b": "mistral"}[key]
            macro(f"J{sj}tau", fmt(tau)); macro(f"J{sj}phi", fmt(r.phi)); macro(f"J{sj}z", fmt(r.med_z, 1))
            macro(f"J{sj}kappa", fmt(r.kappa, 3)); macro(f"J{sj}adjsig", pct(r.adj_sig, 0)); macro(f"J{sj}tie", pct(tie[th_k], 0))
        f.write("\\bottomrule\\end{tabular}\n")
    # MT-Bench no ties
    for key in ["mt_human", "mt_human_noties"]:
        x = flip[(flip.board == key) & (flip.kind == "relabel") & (flip.z > 2)]
        macro(f"mtties{key.replace('_', '')}phi", fmt(x.phi.median()))

    # ------------------------------------------------ validation numbers
    val = json.load(open(f"{R}/validate.json"))
    for kind in KINDS:
        v = val[kind]
        macro(f"valn{kind}", str(v["n"])); macro(f"valsub{kind}", str(v["greedy_suboptimal"]))
        macro(f"valk{kind}", fmt(v["mean_greedy"], 2))
    fs = np.array([s["ks"] for s in val["frac_sensitivity"]], float)
    ok = np.isfinite(fs).all(1); rel = fs[ok] / fs[ok][:, [0]]
    macro("fracmaxratio", fmt(rel.max(), 3)); macro("fracmeanratio", fmt(rel.mean(0)[-1], 3)); macro("fracn", str(int(ok.sum())))
    se = pd.DataFrame(val["se"]); r_ = se.ij / se.boot
    macro("seratiomed", fmt(r_.median(), 3)); macro("seratiomin", fmt(r_.min(), 2)); macro("seratiomax", fmt(r_.max(), 2))
    sc = pd.read_csv(f"{R}/sigcheck.csv")
    macro("sigcheckn", str(len(sc))); macro("sigcheckmax", fmt(sc.z_after.max(), 2))

    # misc counts
    macro("npairsmain", f"{len(main_df[(main_df['mode'] == 'flip') & (main_df.kind == 'drop')]):,}".replace(",", "{,}"))
    macro("nedits", f"{len(allp) + len(boot) + len(ctl):,}".replace(",", "{,}"))
    cens = allp[(allp["mode"] == "flip")]
    macro("censfrac", pct(np.isinf(cens.k).mean(), 3))

    with open(f"{P}/numbers.tex", "w") as f:
        for k, v in sorted(NUM.items()):
            kk = "".join(ch for ch in k if ch.isalnum())
            # macro names may not contain digits: map digits to letters
            for dg, w in zip("0123456789", ["Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine"]):
                kk = kk.replace(dg, w)
            f.write(f"\\newcommand{{\\N{kk}}}{{{v}}}\n")
    json.dump(NUM, open(f"{R}/numbers.json", "w"), indent=1)
    print("analysis done;", len(NUM), "numbers")


if __name__ == "__main__":
    main()
