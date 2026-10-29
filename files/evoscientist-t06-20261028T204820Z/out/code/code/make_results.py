"""Aggregate results/*.csv into the tables (paper/tables/*.tex) and figures (paper/figs/*.pdf) of the
paper plus results/summary.json.   Usage: python code/make_results.py"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import norm, kendalltau

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = os.path.join(ROOT, "results")
TAB = os.path.join(ROOT, "paper", "tables")
FIG = os.path.join(ROOT, "paper", "figs")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
rng = np.random.default_rng(0)
S = {}  # summary numbers

DES_ORDER = ["Arena crowd (64)", "Arena crowd, single-turn (64)", "LLM judges on Arena (64)", "MT-Bench expert (6)",
             "MT-Bench GPT-4 judge (6)", "NBA seasons (~30)", "NBA all-time (53)"]


def design(b):
    if b == "nba_alltime": return "NBA all-time (53)"
    if b.startswith("nba_"): return "NBA seasons (~30)"
    if b == "arena55k_human": return "Arena crowd (64)"
    if b == "mtbench_human": return "MT-Bench expert (6)"
    if b == "mtbench_gpt4": return "MT-Bench GPT-4 judge (6)"
    if b == "arenaST_human": return "Arena crowd, single-turn (64)"
    if b.startswith("arenaST_judge_"): return "LLM judges on Arena (64)"
    return b


def load_pairs():
    df = pd.concat([pd.read_csv(os.path.join(R, f"pairs_{g}.csv")) for g in ("core", "judges")], ignore_index=True)
    df["design"] = df.board.map(design)
    df["kappa"] = df.k_drop / df.N
    df["c"] = df.k_drop / (df.z * np.sqrt(df.n_inv))
    return df


def kpred(z, n):
    """Gaussian-influence heuristic: k = n * Q(t) with phi(t) = z / sqrt(n)."""
    z = np.asarray(z, float); n = np.asarray(n, float)
    eps = z / np.sqrt(n)
    out = np.full(eps.shape, np.nan)
    ok = (eps < 0.3989) & (eps > 0)
    t = np.sqrt(-2 * np.log(eps[ok] * np.sqrt(2 * np.pi)))
    out[ok] = n[ok] * norm.sf(t)
    return out


def q(x, p):
    return float(np.nanpercentile(x, p))


def boot_ci(x, f=np.median, B=2000, cluster=None):
    x = np.asarray(x, float)
    if cluster is None:
        idx = rng.integers(0, len(x), (B, len(x)))
        v = [f(x[i]) for i in idx]
    else:
        cl = np.asarray(cluster)
        u = np.unique(cl)
        groups = [x[cl == g] for g in u]
        v = []
        for _ in range(B):
            pick = rng.integers(0, len(u), len(u))
            v.append(f(np.concatenate([groups[k] for k in pick])))
    return float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))


def fmt(x, d=1):
    return f"{x:.{d}f}"


# ------------------------------------------------------------------------------------------
df = load_pairs()
df.to_csv(os.path.join(R, "pairs_all.csv"), index=False)
sig = df[(df.z > 2) & np.isfinite(df.k_drop) & (df.k_drop > 0)].copy()

# ---- Table 1: design-level summary on statistically significant pairs ------------------------
rows = []
for d in DES_ORDER:
    g = df[df.design == d]
    s = sig[sig.design == d]
    cl = s.board if d.startswith("LLM") or d.startswith("NBA seasons") else None
    clo, chi = boot_ci(s.c, cluster=cl)
    rows.append(dict(design=d, boards=g.board.nunique(), N=int(g.groupby("board").N.first().median()),
                     pairs=len(g), nsig=len(s), fsig=len(s) / len(g),
                     z_med=s.z.median(), k_med=s.k_drop.median(), k_q1=q(s.k_drop, 25), k_q3=q(s.k_drop, 75),
                     kappa_med=s.kappa.median(), c_med=s.c.median(), c_lo=clo, c_hi=chi,
                     kflip_ratio=(s.k_flip / s.k_drop).median(), kadd_ratio=(s.k_add / s.k_drop).median(),
                     klin_ratio=(s.klin_drop / s.k_drop).median()))
T1 = pd.DataFrame(rows)
T1.to_csv(os.path.join(R, "table_design_summary.csv"), index=False)
with open(os.path.join(TAB, "t_design.tex"), "w") as f:
    f.write("\\begin{tabular}{lrrrrrrr}\n\\toprule\n")
    f.write("Evaluation design & boards & $N$ & sig./all pairs & median $z$ & median $k^\\ast$ [IQR] & median $\\kappa^\\ast$ (\\%) & median $c$ [95\\% CI]\\\\\n\\midrule\n")
    for r in T1.itertuples():
        f.write(f"{r.design} & {r.boards} & {r.N:,} & {r.nsig}/{r.pairs} & {r.z_med:.1f} & {r.k_med:.0f} [{r.k_q1:.0f}--{r.k_q3:.0f}] & {100*r.kappa_med:.2f} & {r.c_med:.2f} [{r.c_lo:.2f}, {r.c_hi:.2f}]\\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")
S["design_summary"] = T1.round(4).to_dict("records")

# ---- Table 2: rank-1 questions ---------------------------------------------------------------
rows = []
for b in ["arena55k_human", "arenaST_human", "arenaST_judge_Athene-70B", "arenaST_judge_Meta-Llama-3-70B-Instruct",
          "arenaST_judge_Qwen2-72B-Instruct", "arenaST_judge_Mistral-7B-Instruct-v0.2", "arenaST_judge_dolphin-2.1-mistral-7b",
          "mtbench_human", "mtbench_gpt4", "nba_alltime"]:
    g = df[(df.board == b) & (df.rank_i == 0)]
    r = g[g.rank_j == 1].iloc[0]
    top = g.k_drop.min()
    rows.append(dict(board=b, N=int(r.N), top1_gap=r.gap, z=r.z, boot_flip=r.boot_flip, k_drop=r.k_drop, k_flip=r.k_flip, k_add=r.k_add,
                     top1_change_k=top, top1_change_frac=top / r.N, z_top1_vs_6=g[g.rank_j == 5].z.iloc[0] if (g.rank_j == 5).any() else np.nan,
                     k_top1_vs_6=g[g.rank_j == 5].k_drop.iloc[0] if (g.rank_j == 5).any() else np.nan))
T2 = pd.DataFrame(rows)
# NBA seasons: distribution over 36 seasons
ns = df[(df.design == "NBA seasons (~30)") & (df.rank_i == 0) & (df.rank_j == 1)]
nsm = df[(df.design == "NBA seasons (~30)") & (df.rank_i == 0)].groupby("board").k_drop.min()
S["nba_season_top1"] = dict(n=len(ns), N_med=float(ns.N.median()), k_drop_med=float(ns.k_drop.median()), k_drop_min=float(ns.k_drop.min()),
                            k_drop_max=float(ns.k_drop.max()), z_med=float(ns.z.median()), z_max=float(ns.z.max()),
                            frac_z_gt2=float((ns.z > 2).mean()), top1_change_k_med=float(nsm.median()), top1_change_k_max=float(nsm.max()),
                            boot_flip_med=float(ns.boot_flip.median()))
T2.to_csv(os.path.join(R, "table_top1.csv"), index=False)
S["top1"] = T2.round(4).to_dict("records")

# ---- Gaussian-influence heuristic vs measured ------------------------------------------------
m = sig.copy()
m["kp"] = kpred(m.z.values, m.n_inv.values)
m = m[np.isfinite(m.kp)]
m["lr"] = np.log(m.k_drop / m.kp)
gp = m.groupby("design").lr.agg(["mean", "std", "count"])
S["gauss_heuristic_logratio"] = gp.round(3).to_dict("index")
S["gauss_heuristic_overall"] = dict(mean=float(m.lr.mean()), std=float(m.lr.std()), abs_med=float(np.median(np.abs(m.lr))),
                                    corr_logk=float(np.corrcoef(np.log(m.k_drop), np.log(m.kp))[0, 1]))
# regression of log k on log(z sqrt(n_inv)), per design (pairs resampled)
reg = {}
for d in DES_ORDER:
    s = sig[sig.design == d]
    x = np.log(s.z * np.sqrt(s.n_inv)); y = np.log(s.k_drop)
    b1 = np.polyfit(x, y, 1)[0]
    bs = []
    for _ in range(1000):
        i = rng.integers(0, len(x), len(x))
        bs.append(np.polyfit(x.values[i], y.values[i], 1)[0])
    reg[d] = dict(slope=float(b1), lo=float(np.percentile(bs, 2.5)), hi=float(np.percentile(bs, 97.5)), n=len(s))
S["loglog_slope_k_vs_z_sqrt_n"] = reg
x = np.log(sig.z * np.sqrt(sig.n_inv)); y = np.log(sig.k_drop)
S["loglog_slope_pooled"] = float(np.polyfit(x, y, 1)[0])
S["corr_pooled_logk_logzsqrtn"] = float(np.corrcoef(x, y)[0, 1])

# ---- baselines table: drop vs flip vs add; random vs targeted-random ---------------------------
rr = df[df.rand_drop_flip.notna()].copy()
rrs = rr[(rr.k_drop >= 3) & (rr.z > 0)]
tab = []
for d in DES_ORDER:
    s = rrs[rrs.design == d]
    s2 = sig[sig.design == d]
    t = s[np.isfinite(s.k_targ_rand)]
    tab.append(dict(design=d, n_rand=len(s), rand_drop_flip=s.rand_drop_flip.mean(), rand_flip_flip=s.rand_flip_flip.mean(),
                    targ_ratio=(t.k_targ_rand / t.k_drop).median() if len(t) else np.nan,
                    targ_ratio_q1=q(t.k_targ_rand / t.k_drop, 25) if len(t) else np.nan,
                    targ_ratio_q3=q(t.k_targ_rand / t.k_drop, 75) if len(t) else np.nan,
                    flip_ratio=(s2.k_flip / s2.k_drop).median(), add_ratio=(s2.k_add / s2.k_drop).median(),
                    add_ratio_q1=q(s2.k_add / s2.k_drop, 25), add_ratio_q3=q(s2.k_add / s2.k_drop, 75),
                    klin_ratio=(s2.klin_drop / s2.k_drop).median(),
                    klin_q1=q(s2.klin_drop / s2.k_drop, 25), klin_q3=q(s2.klin_drop / s2.k_drop, 75)))
TB = pd.DataFrame(tab)
TB.to_csv(os.path.join(R, "table_baselines.csv"), index=False)
S["baselines"] = TB.round(4).to_dict("records")
with open(os.path.join(TAB, "t_base.tex"), "w") as f:
    f.write("\\begin{tabular}{lrrrrr}\n\\toprule\n")
    f.write("Design & rand.\\ drop & rand.\\ flip & targeted-rand./influence & flip/drop & add/drop\\\\\n\\midrule\n")
    for r in TB.itertuples():
        f.write(f"{r.design} & {r.rand_drop_flip:.3f} & {r.rand_flip_flip:.3f} & {r.targ_ratio:.1f} & {r.flip_ratio:.2f} & {r.add_ratio:.2f}\\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# bootstrap-significance vs adversarial robustness
bs = df[(df.boot_flip <= 0.0) & np.isfinite(df.k_drop)]
S["boot_never_flips"] = dict(n=len(bs), k_med=float(bs.k_drop.median()), k_min=float(bs.k_drop.min()), kappa_med=float(bs.kappa.median()),
                             frac_kappa_lt_1pct=float((bs.kappa < 0.01).mean()), frac_kappa_lt_0p5pct=float((bs.kappa < 0.005).mean()))
for d in DES_ORDER:
    s = df[(df.design == d) & (df.boot_flip <= 0.025) & np.isfinite(df.k_drop)]
    S.setdefault("boot_sig_by_design", {})[d] = dict(n=len(s), k_med=float(s.k_drop.median()) if len(s) else None,
                                                    kappa_med=float(s.kappa.median()) if len(s) else None,
                                                    k_min=float(s.k_drop.min()) if len(s) else None)

# ---- agreement of z measures
S["z_vs_boot"] = dict(corr_gap_over_bootsd_vs_z=float(np.corrcoef(df.gap / df.boot_sd, df.z)[0, 1]),
                      med_ratio_se_over_bootsd=float((df.se / df.boot_sd).median()))

# ---- sensitivity: ties dropped / no home advantage ---------------------------------------------
ex_path = os.path.join(R, "pairs_extras.csv")
if os.path.exists(ex_path):
    ex = pd.read_csv(ex_path)
    ex["c"] = ex.k_drop / (ex.z * np.sqrt(ex.n_inv)); ex["kappa"] = ex.k_drop / ex.N
    a1 = ex[(ex.board == "arena55k_noties") & (ex.z > 2) & (ex.k_drop > 0)]
    a0 = df[(df.board == "arena55k_human") & (df.z > 2) & (df.k_drop > 0)]
    n1 = ex[(ex.board != "arena55k_noties") & (ex.z > 2) & (ex.k_drop > 0)]
    n0 = df[(df.design == "NBA seasons (~30)") & (df.z > 2) & (df.k_drop > 0)]
    S["sensitivity"] = dict(
        arena_halfwin=dict(n=len(a0), z_med=float(a0.z.median()), k_med=float(a0.k_drop.median()), kappa_med=float(a0.kappa.median()), c_med=float(a0.c.median())),
        arena_noties=dict(n=len(a1), z_med=float(a1.z.median()), k_med=float(a1.k_drop.median()), kappa_med=float(a1.kappa.median()), c_med=float(a1.c.median()), N=int(a1.N.iloc[0])),
        nba_home=dict(n=len(n0), z_med=float(n0.z.median()), k_med=float(n0.k_drop.median()), kappa_med=float(n0.kappa.median()), c_med=float(n0.c.median())),
        nba_nohome=dict(n=len(n1), z_med=float(n1.z.median()), k_med=float(n1.k_drop.median()), kappa_med=float(n1.kappa.median()), c_med=float(n1.c.median())))
    # per-season top-1 comparison
    t1 = ex[(ex.board != "arena55k_noties") & (ex.rank_i == 0) & (ex.rank_j == 1)].copy()
    t1["season"] = t1.board.str.extract(r"nba_(\d+)_nohome").astype(int)
    t0 = df[(df.design == "NBA seasons (~30)") & (df.rank_i == 0) & (df.rank_j == 1)].copy()
    t0["season"] = t0.board.str.extract(r"nba_(\d+)").astype(int)
    mm = t0.merge(t1, on="season", suffixes=("_h", "_n"))
    S["sensitivity"]["nba_top1_same_leader_frac"] = float((mm.i_h == mm.i_n).mean())
    S["sensitivity"]["nba_top1_k_corr"] = float(np.corrcoef(mm.k_drop_h, mm.k_drop_n)[0, 1])

# ---- judge agreement ---------------------------------------------------------------------------
ja_path = os.path.join(R, "judge_agreement.csv")
if os.path.exists(ja_path):
    S["judge_agreement"] = pd.read_csv(ja_path).round(4).to_dict("records")
    jr = pd.read_csv(os.path.join(R, "judge_pair_reversal.csv"))
    jr["bin"] = pd.cut(jr.z, [-np.inf, 1, 2, 3, 5, np.inf], labels=["<1", "1-2", "2-3", "3-5", ">5"])
    S["judge_reversal_by_human_z"] = jr[~jr.judge.str.startswith("dolphin")].groupby("bin", observed=True).agg(
        frac_reversed=("reversed", "mean"), n=("reversed", "size"), k_med=("k_drop", "median")).round(4).to_dict("index")

# ---- scaling ------------------------------------------------------------------------------------
sc = pd.read_csv(os.path.join(R, "scaling_pairs.csv"))
sc["kappa"] = sc.k_drop / sc.N
sc["c"] = sc.k_drop / (sc.z * np.sqrt(sc.n_inv))
full = df[df.board == "arena55k_human"]
full = full[(full.rank_j == full.rank_i + 1)][["rank_i", "z", "k_drop", "N", "n_inv", "gap", "se"]].copy()
full["draw"] = 0
rows = []
for N_, g in sc.groupby("N"):
    s = g[(g.z > 2) & (g.k_drop > 0)]
    rows.append(dict(N=N_, n_sig=len(s), frac_sig=len(s) / len(g), z_med=s.z.median(), k_med=s.k_drop.median(), kappa_med=s.kappa.median(),
                     c_med=s.c.median(), gap_med_sig=s.gap.median()))
sf = full[(full.z > 2) & (full.k_drop > 0)]
rows.append(dict(N=57477, n_sig=len(sf), frac_sig=len(sf) / len(full), z_med=sf.z.median(), k_med=sf.k_drop.median(),
                 kappa_med=(sf.k_drop / sf.N).median(), c_med=(sf.k_drop / (sf.z * np.sqrt(sf.n_inv))).median(), gap_med_sig=sf.gap.median()))
SC = pd.DataFrame(rows)
SC.to_csv(os.path.join(R, "table_scaling.csv"), index=False)
S["scaling"] = SC.round(4).to_dict("records")
# same pairs across N: use pairs by name? ranks shift; use matched top-10 adjacent pairs ranks 0..9 with significance at N_full
with open(os.path.join(TAB, "t_scaling.tex"), "w") as f:
    f.write("\\begin{tabular}{rrrrrr}\n\\toprule\n$N$ & sig.\\ frac. & median $z$ & median $k^\\ast$ & median $\\kappa^\\ast$ (\\%) & median $c$\\\\\n\\midrule\n")
    for r in SC.itertuples():
        f.write(f"{r.N:,} & {r.frac_sig:.2f} & {r.z_med:.1f} & {r.k_med:.0f} & {100*r.kappa_med:.2f} & {r.c_med:.2f}\\\\\n")
    f.write("\\bottomrule\n\\end{tabular}\n")

# ================================ figures ========================================================
colors = {"Arena crowd (64)": "C0", "Arena crowd, single-turn (64)": "C9", "LLM judges on Arena (64)": "C2", "MT-Bench expert (6)": "C3",
          "MT-Bench GPT-4 judge (6)": "C1", "NBA seasons (~30)": "C4", "NBA all-time (53)": "C5"}
mk = {"Arena crowd (64)": "o", "Arena crowd, single-turn (64)": "o", "LLM judges on Arena (64)": "s", "MT-Bench expert (6)": "^",
      "MT-Bench GPT-4 judge (6)": "v", "NBA seasons (~30)": "x", "NBA all-time (53)": "D"}
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "legend.fontsize": 6.5})

# Fig 1: k vs z sqrt(n) ; kappa vs z
fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.7))
pos = df[(df.z > 0.05) & (df.k_drop > 0) & np.isfinite(df.k_drop)]
for d in DES_ORDER:
    s = pos[pos.design == d]
    ax[0].scatter(s.z * np.sqrt(s.n_inv), s.k_drop, s=4 if d != "NBA seasons (~30)" else 6, c=colors[d], marker=mk[d], alpha=0.35, linewidths=0.5, label=d)
xs = np.logspace(0, 3.2, 100)
ax[0].plot(xs, 0.4 * xs, "k--", lw=0.8, label="$k=0.4\\,z\\sqrt{n}$")
zz = xs / np.sqrt(1.0)
ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[0].set_xlabel("$z\\sqrt{n_{ij}}$  (z-score $\\times\\sqrt{\\#\\mathrm{votes\\ involving}\\ i\\ \\mathrm{or}\\ j}$)")
ax[0].set_ylabel("min. dropped votes $k^\\ast$")
ax[0].set_title("(a) budget to reverse a pair")
for d in DES_ORDER:
    s = pos[pos.design == d]
    ax[1].scatter(s.z, 100 * s.kappa, s=4 if d != "NBA seasons (~30)" else 6, c=colors[d], marker=mk[d], alpha=0.35, linewidths=0.5)
ax[1].set_xscale("log"); ax[1].set_yscale("log")
ax[1].axvline(2, color="gray", lw=0.6, ls=":")
ax[1].set_xlabel("z-score of the pair"); ax[1].set_ylabel("$\\kappa^\\ast=k^\\ast/N$ (%)")
ax[1].set_title("(b) fraction of all votes")
h, l = ax[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=4, frameon=False, markerscale=2.2, bbox_to_anchor=(0.5, -0.12))
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_k_vs_z.pdf"), bbox_inches="tight"); plt.close(fig)

# Fig 2: scaling
fig, ax = plt.subplots(1, 3, figsize=(6.8, 2.1))
Ns = SC.N.values
ax[0].plot(Ns, SC.z_med, "o-", ms=3); ax[0].plot(Ns, SC.z_med.iloc[0] * np.sqrt(Ns / Ns[0]), "k:", lw=0.8)
ax[0].set_title("(a) median $z$ of sig. pairs"); ax[0].set_xscale("log"); ax[0].set_yscale("log")
ax[1].plot(Ns, SC.k_med, "o-", ms=3, label="measured"); ax[1].set_title("(b) median $k^\\ast$"); ax[1].set_xscale("log"); ax[1].set_yscale("log")
ax[2].plot(Ns, 100 * SC.kappa_med, "o-", ms=3, label="median $\\kappa^\\ast$")
ax[2].set_title("(c) median $\\kappa^\\ast$ (%)"); ax[2].set_xscale("log")
ax[2].set_ylim(0, None)
for a in ax: a.set_xlabel("number of votes $N$")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_scaling.pdf"), bbox_inches="tight"); plt.close(fig)

# Fig 3: top-1 NBA seasons histogram + Arena judges
fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.2))
ax[0].hist(ns.k_drop, bins=np.arange(-0.5, ns.k_drop.max() + 1.5, 1), color="C4")
ax[0].set_xlabel("games to drop to change the #1 vs #2 order"); ax[0].set_ylabel("NBA seasons"); ax[0].set_title("(a) NBA seasons 1980--2015")
ax[1].scatter(ns.z, ns.boot_flip, s=8, c="C4")
ax[1].set_xlabel("z-score of #1 vs #2"); ax[1].set_ylabel("bootstrap P(order reversed)"); ax[1].set_title("(b) bootstrap flip probability")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_nba_top1.pdf"), bbox_inches="tight"); plt.close(fig)

# Fig 4: first-order accuracy
fig, ax = plt.subplots(1, 1, figsize=(3.3, 2.3))
for d in DES_ORDER:
    s = sig[sig.design == d]
    ax.scatter(s.klin_drop, s.k_drop, s=4, c=colors[d], marker=mk[d], alpha=0.4, linewidths=0.5)
xs = np.logspace(0, 3.3, 10); ax.plot(xs, xs, "k--", lw=0.7)
ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel("first-order estimate $k_{\\rm lin}$"); ax.set_ylabel("verified $k^\\ast$ (refit)")
fig.tight_layout(); fig.savefig(os.path.join(FIG, "fig_first_order.pdf"), bbox_inches="tight"); plt.close(fig)

with open(os.path.join(R, "summary.json"), "w") as f:
    json.dump(S, f, indent=1, default=float)
print(json.dumps(S, indent=1, default=float)[:12000])
