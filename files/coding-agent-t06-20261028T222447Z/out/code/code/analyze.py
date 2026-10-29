"""Builds every table/figure/number in the paper from results/*.csv.  Writes results/summary.json,
results/tab_*.tex and figures/*.pdf."""
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import boards, bt, loaders as D

R = "/work/results"; F = "/work/figures"
rng = np.random.default_rng(7)
S = {}   # summary numbers

NAMES = {"arena55k": "Arena, crowd (64 models)", "arena140k": "Arena 140k, crowd (53 models)", "arena6": "Arena, crowd (6 models)",
         "arenaST_human": "Arena single-turn, crowd",
         "arenaST_Meta-Llama-3-70B-Instruct": "Arena single-turn, Llama-3-70B judge",
         "arenaST_Qwen2-72B-Instruct": "Arena single-turn, Qwen2-72B judge",
         "arenaST_Mistral-7B-Instruct-v0.2": "Arena single-turn, Mistral-7B judge",
         "mt_human": "MT-Bench, expert", "mt_gpt4": "MT-Bench, GPT-4 judge", "nba": "NBA seasons (69)"}
ORDER = list(NAMES)
COL = {"arena55k": "#0072B2", "arena140k": "#882255", "arena6": "#56B4E9", "arenaST_human": "#009E73",
       "arenaST_Meta-Llama-3-70B-Instruct": "#D55E00", "arenaST_Qwen2-72B-Instruct": "#E69F00",
       "arenaST_Mistral-7B-Instruct-v0.2": "#CC79A7", "mt_human": "#000000", "mt_gpt4": "#777777", "nba": "#B2182B"}
MK = {"arena55k": "o", "arena140k": "h", "arena6": "o", "arenaST_human": "s", "arenaST_Meta-Llama-3-70B-Instruct": "^",
      "arenaST_Qwen2-72B-Instruct": "v", "arenaST_Mistral-7B-Instruct-v0.2": "D", "mt_human": "P", "mt_gpt4": "X", "nba": "."}
SHORT = {"arena55k": "Arena-64", "arena140k": "Arena-140k", "arena6": "Arena-6", "arenaST_human": "ArenaST human", "arenaST_Meta-Llama-3-70B-Instruct": "ArenaST Llama-3-70B",
         "arenaST_Qwen2-72B-Instruct": "ArenaST Qwen2-72B", "arenaST_Mistral-7B-Instruct-v0.2": "ArenaST Mistral-7B",
         "mt_human": "MT-Bench human", "mt_gpt4": "MT-Bench GPT-4", "nba": "NBA seasons"}
plt.rcParams.update({"font.size": 8, "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 0.6,
                     "lines.linewidth": 1.2, "legend.frameon": False, "pdf.fonttype": 42})

A = pd.read_csv(f"{R}/attack_all.csv")
A["grp"] = np.where(A.board.str.startswith("nba"), "nba", A.board)
A["z"] = A.z_model
for op in ("drop", "relabel", "inject"):
    A["c_" + op] = A[op] / (A.z * np.sqrt(A.n_loc))
adj = A[A.kind == "adjacent"].copy()
st = pd.read_csv(f"{R}/dataset_stats.csv"); st["grp"] = np.where(st.board.str.startswith("nba"), "nba", st.board)

# ---------------------------------------------------------------- Table 1: datasets
def tab1():
    rows = []
    for g in ORDER:
        s = st[st.grp == g]
        rows.append((g, s.design.iloc[0], s.p.median(), s.N.median(), s.tie_rate.mean(), s.median_per_item.median(), s.pair_coverage.mean(), s.score_sd.mean()))
    t = pd.DataFrame(rows, columns=["grp", "design", "p", "N", "tie", "per_item", "coverage", "scsd"])
    with open(f"{R}/tab_datasets.tex", "w") as f:
        for _, r in t.iterrows():
            f.write(f"{NAMES[r.grp]} & {r.design} & {int(r.p)} & {int(r.N):,} & {100*r.tie:.0f}\\% & {int(r.per_item):,} & {r.coverage:.2f} & {r.scsd:.2f} \\\\\n".replace(",", "{,}"))
    S["table1"] = t.to_dict("records")
tab1()

# --------------------------------------------------------------- helper: c with CIs
B = pd.concat([pd.read_csv(f"{R}/scaling_all.csv"), pd.read_csv(f"{R}/scaling_140k.csv")], ignore_index=True); Bb = B[(B.exp == "boot") & (B.kind == "adjacent")].copy()
for op in ("drop", "relabel"):
    Bb["c_" + op] = Bb[op] / (Bb.z * np.sqrt(Bb.n_loc))
ZMIN = 1.0   # pairs with z >= ZMIN are used for c / regression (selection independent of k, avoids integer-floor bias)
def med_c(df, op):
    d = df[(df.z >= ZMIN) & df[op].notna()]
    return d["c_" + op].median() if len(d) else np.nan

def c_summary(g, op):
    """median c over pairs with k>=KMIN, with 95% CI: bootstrap datasets (non-NBA) / seasons (NBA)"""
    if g == "nba":
        per = adj[adj.grp == "nba"].groupby("board").apply(lambda d: med_c(d, op)).dropna().values
        bs = [np.median(rng.choice(per, len(per))) for _ in range(2000)]
        return np.median(per), np.percentile(bs, 2.5), np.percentile(bs, 97.5), "seasons"
    full = med_c(adj[adj.grp == g], op)
    b = Bb[Bb.board == g]
    if len(b):
        per = b.groupby("rep").apply(lambda d: med_c(d, op)).dropna().values
        return full, np.percentile(per, 2.5), np.percentile(per, 97.5), "bootstrap"
    return full, np.nan, np.nan, "none"

# --------------------------------------------------------------- Table 2: main results
def top1_budget(g, op):
    """minimum over challengers (ranks 2..5) of the budget to dethrone the top-1 item"""
    d = A[(A.grp == g) & (A["rank"] == 1) & (A.kind.isin(["adjacent", "top1"]))]
    out = d.groupby("board")[op].min()
    return out, d.groupby("board")["N"].first()

rows = []
for g in ORDER:
    a = adj[adj.grp == g]
    per_board_res = a.groupby("board").apply(lambda d: (d.z > 2).sum()).values
    npairs = a.groupby("board").size().values
    r = dict(grp=g, p=st[st.grp == g].p.median(),
             res_frac=float(np.mean(per_board_res / npairs)), res_n=float(np.mean(per_board_res)),
             z_med=float(a.z.median()))
    for op in ("drop", "relabel", "inject"):
        k, N = top1_budget(g, op)
        r[f"top1_{op}"] = float(k.median()); r[f"top1_{op}_frac"] = float((k / N).median())
        r[f"top1_{op}_q25"] = float((k / N).quantile(.25)); r[f"top1_{op}_q75"] = float((k / N).quantile(.75))
    # top-1 gap z against the closest challenger
    r["top1_z"] = float(A[(A.grp == g) & (A["rank"] == 1) & (A.kind == "adjacent")].z.median())
    for op in ("drop", "relabel"):
        m, lo, hi, how = c_summary(g, op)
        r[f"c_{op}"], r[f"c_{op}_lo"], r[f"c_{op}_hi"], r["c_how"] = m, lo, hi, how
    r["frac_adj_le_1pct"] = float(np.mean((a["drop"] / a.N) <= 0.01))
    r["frac_adj_le_01pct"] = float(np.mean((a["drop"] / a.N) <= 0.001))
    r["frac_adj_relabel_le_1pct"] = float(np.mean((a["relabel"] / a.N) <= 0.01))
    rows.append(r)
T2 = pd.DataFrame(rows); S["table2"] = T2.to_dict("records")
with open(f"{R}/tab_main.tex", "w") as f:
    for _, r in T2.iterrows():
        f.write(f"{NAMES[r.grp]} & {r.res_n:.1f}/{int(r.p)-1} & {r.z_med:.2f} & "
                f"{r.top1_drop:.0f} ({100*r.top1_drop_frac:.2g}\\%) & {r.top1_relabel:.0f} ({100*r.top1_relabel_frac:.2g}\\%) & "
                f"{r.c_drop:.2f} [{r.c_drop_lo:.2f}, {r.c_drop_hi:.2f}] & {r.c_relabel:.2f} [{r.c_relabel_lo:.2f}, {r.c_relabel_hi:.2f}] \\\\\n")

# --------------------------------------------------------------- scaling-law regression
def ols(df, op):
    d = df[(df.z >= ZMIN) & df[op].notna()]
    X = np.c_[np.ones(len(d)), np.log(d.z), np.log(d.n_loc)]; y = np.log(d[op].values)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return beta, len(d), np.std(y - X @ beta)
reg = {}
for op in ("drop", "relabel", "inject"):
    beta, n, sd = ols(adj, op)
    # cluster bootstrap over boards (NBA seasons are separate boards)
    boards_ = adj.board.unique(); byb = {b: adj[adj.board == b] for b in boards_}
    bs = []
    for _ in range(400):
        pick = rng.choice(boards_, len(boards_))
        try: bs.append(ols(pd.concat([byb[b] for b in pick]), op)[0])
        except Exception: pass
    bs = np.array(bs)
    reg[op] = dict(n=n, resid_sd=sd, b0=beta[0], bz=beta[1], bn=beta[2],
                   bz_ci=list(np.percentile(bs[:, 1], [2.5, 97.5])), bn_ci=list(np.percentile(bs[:, 2], [2.5, 97.5])))
    # per group
    reg[op]["by_group"] = {g: dict(zip(["b0", "bz", "bn"], ols(adj[adj.grp == g], op)[0])) | dict(n=ols(adj[adj.grp == g], op)[1])
                           for g in ORDER if ((adj[adj.grp == g].z >= ZMIN) & adj[adj.grp == g][op].notna()).sum() >= 8}
S["regression"] = reg

# --------------------------------------------------------------- Fig 1: collapse
fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.7), sharey=True)
for ax, op, ttl in zip(axs, ("drop", "relabel"), ("drop $k$ comparisons", "relabel $k$ comparisons")):
    for g in ORDER:
        d = adj[(adj.grp == g)]
        ax.scatter(d.z * np.sqrt(d.n_loc), d[op], s=6 if g == "nba" else 14, marker=MK[g] if g != "nba" else "o", c=COL[g],
                   alpha=0.25 if g == "nba" else 0.9, linewidths=0, label=SHORT[g], zorder=2 if g != "nba" else 1)
    x = np.logspace(-0.5, 3.2, 20)
    for c, ls in ((0.25, ":"), (0.5, "--"), (1.0, "-")):
        ax.plot(x, c * x if op == "drop" else 0.5 * c * x, c="#999999", lw=0.8, ls=ls)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_title(ttl, fontsize=8)
    ax.set_xlabel(r"$z\,\sqrt{n_{\mathrm{loc}}}$")
    ax.set_xlim(0.1, 2000); ax.set_ylim(0.8, 3000)
axs[0].set_ylabel(r"minimal flipping budget $k^\star$")
h, l = axs[1].get_legend_handles_labels()
fig.legend(h, l, fontsize=6, ncol=5, loc="upper center", handletextpad=0.1, columnspacing=0.8, bbox_to_anchor=(0.5, 1.02), markerscale=1.3)
axs[0].text(60, 120, r"$k^\star=z\sqrt{n}$", fontsize=6, rotation=33, color="#777777")
axs[0].text(110, 24, r"$0.25$", fontsize=6, rotation=33, color="#777777")
plt.tight_layout(rect=(0, 0, 1, 0.9)); plt.savefig(f"{F}/fig_collapse.pdf"); plt.savefig(f"/work/tmp/fig_collapse.png", dpi=110); plt.close()

# --------------------------------------------------------------- Fig 2: random vs adversarial
Nz = pd.concat([pd.read_csv(f"{R}/noise_all.csv"), pd.read_csv(f"{R}/noise_140k.csv")], ignore_index=True); Nz["grp"] = np.where(Nz.board.str.startswith("nba"), "nba", Nz.board)
show = ["arena55k", "mt_human", "arenaST_Meta-Llama-3-70B-Instruct", "nba"]
fig, axs = plt.subplots(1, 4, figsize=(6.9, 2.2), sharey=True)
for ax, g in zip(axs, show):
    n = Nz[(Nz.grp == g)]
    for mode, ls in (("drop", "-"), ("relabel", "--")):
        m = n[n["mode"] == mode].groupby("eps").adj_flip_mean.mean()
        ax.plot(m.index, m.values, ls=ls, c="#555555", marker="o", ms=2.5, label=f"random {mode}")
    a = adj[adj.grp == g]
    grid = np.logspace(-4.5, -0.3, 60)
    for op, ls in (("drop", "-"), ("relabel", "--")):
        f = [np.mean(a[op].fillna(np.inf) / a.N <= e) for e in grid]
        ax.plot(grid, f, c=COL[g] if g != "mt_human" else "#000000", ls=ls, lw=1.6, label=f"adversarial {op}")
    ax.set_xscale("log"); ax.set_title(SHORT[g], fontsize=7.5); ax.set_xlabel(r"budget $\epsilon=k/N$")
    ax.set_xlim(3e-5, 0.5)
axs[0].set_ylabel("fraction of adjacent pairs\nthat change order")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, fontsize=6, ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.02))
plt.tight_layout(rect=(0, 0.1, 1, 1)); plt.savefig(f"{F}/fig_random_vs_adv.pdf"); plt.savefig(f"/work/tmp/fig_random_vs_adv.png", dpi=110); plt.close()

# numbers for text: noise
def nz(g, mode, eps, col): return float(Nz[(Nz.grp == g) & (Nz["mode"] == mode) & (np.isclose(Nz.eps, eps))][col].mean())
S["noise"] = {g: dict(boot_tau=nz(g, "bootstrap", 1.0, "tau_mean"), boot_top1=nz(g, "bootstrap", 1.0, "top1_same"),
                      boot_adjflip=nz(g, "bootstrap", 1.0, "adj_flip_mean"), boot_ciw=nz(g, "bootstrap", 1.0, "rank_ci_width"),
                      drop5_tau=nz(g, "drop", .05, "tau_mean"), drop5_top1=nz(g, "drop", .05, "top1_same"),
                      drop5_adjflip=nz(g, "drop", .05, "adj_flip_mean"),
                      rel5_tau=nz(g, "relabel", .05, "tau_mean"), rel5_adjflip=nz(g, "relabel", .05, "adj_flip_mean"),
                      rel5_top1=nz(g, "relabel", .05, "top1_same"), drop1_adjflip=nz(g, "drop", .01, "adj_flip_mean"),
                      drop1_top1=nz(g, "drop", .01, "top1_same")) for g in ORDER}
with open(f"{R}/tab_noise.tex", "w") as f:
    for g in ORDER:
        s = S["noise"][g]
        f.write(f"{NAMES[g]} & {s['boot_tau']:.3f} & {s['boot_top1']:.2f} & {s['boot_adjflip']:.2f} & {s['drop5_tau']:.3f} & {s['drop5_adjflip']:.2f} & {s['rel5_tau']:.3f} & {s['rel5_adjflip']:.2f} \\\\\n")

# --------------------------------------------------------------- ablation table
def abl(g):
    a = adj[adj.grp == g]; d = a[(a.z >= ZMIN) & a["drop"].notna()]
    r = dict(grp=g)
    r["oneshot_eq"] = float(np.mean(a["drop"] == a.drop_oneshot))
    r["oneshot_ratio"] = float(np.nanmedian((d.drop_oneshot / d["drop"])))
    r["oneshot_worse"] = float(np.mean(a.drop_oneshot > a["drop"])); r["oneshot_better"] = float(np.mean(a.drop_oneshot < a["drop"]))
    r["direct_na"] = float(a.drop_direct.isna().mean()); r["direct_ratio"] = float(np.nanmedian(d.drop_direct / d["drop"]))
    r["relabel_over_drop"] = float(np.nanmedian(d.relabel / d["drop"])); r["inject_over_drop"] = float(np.nanmedian(d.inject / d["drop"]))
    r["rand_drop_flip"] = float(d.rand_drop_flip_at_k.mean()); r["rand_rel_flip"] = float(d.rand_relabel_flip_at_k.mean())
    r["rand_drop_flip_max"] = float(d.rand_drop_flip_at_k.max()); r["n_pairs_k5"] = int(len(d))
    r["pflip_boot_sep"] = float(a[a.z > 2].p_flip_boot.max()) if (a.z > 2).any() else np.nan
    return r
AB = pd.DataFrame([abl(g) for g in ORDER]); S["ablation"] = AB.to_dict("records")
with open(f"{R}/tab_ablation.tex", "w") as f:
    for _, r in AB.iterrows():
        f.write(f"{NAMES[r.grp]} & {r.n_pairs_k5} & {100*r.oneshot_eq:.0f}\\% & {r.oneshot_ratio:.2f} & {r.direct_ratio:.2f} ({100*r.direct_na:.0f}\\%) & "
                f"{r.relabel_over_drop:.2f} & {r.inject_over_drop:.2f} & {r.rand_drop_flip:.3f} \\\\\n")

# --------------------------------------------------------------- scaling in N (Fig 3)
sub = B[B.exp == "sub"]; sa = sub[sub.kind == "adjacent"].copy()
sa["c"] = sa["drop"] / (sa.z * np.sqrt(sa.n_loc))
sizes = sorted(sa["size"].unique())
res = []
for s_ in sizes:
    d = sa[sa["size"] == s_]
    resolv = d.groupby("rep").apply(lambda x: (x.z > 2).sum())
    top1 = sub[(sub["size"] == s_) & (sub.kind.isin(["top1", "adjacent"])) & (sub["rank"] == 1)].groupby("rep")["drop"].min()
    top1z = sub[(sub["size"] == s_) & (sub.kind == "adjacent") & (sub["rank"] == 1)].groupby("rep").z.first()
    dd = d[(d.z >= ZMIN) & d["drop"].notna()]
    pr = dd.groupby("rep").apply(lambda x: x.c.median()).dropna()
    n_rep_c = int(len(pr))
    res.append(dict(size=int(s_), resolvable=float(resolv.mean()), resolvable_sd=float(resolv.std()), top1_k=float(top1.median()),
                    top1_k_q=[float(top1.quantile(.25)), float(top1.quantile(.75))], top1_z=float(top1z.median()),
                    n_rep_c=n_rep_c, c_med=float(pr.median()), c_lo=float(pr.quantile(.025)), c_hi=float(pr.quantile(.975)),
                    eps_z24=float((dd[(dd.z > 2) & (dd.z < 4)]["drop"] / dd[(dd.z > 2) & (dd.z < 4)].N).median()) if ((dd.z > 2) & (dd.z < 4)).any() else np.nan,
                    n_pairs_z24=int(((dd.z > 2) & (dd.z < 4)).sum())))
S["scaling_sub"] = res
# add full data
fd = adj[adj.grp == "arena55k"]
S["scaling_full"] = dict(resolvable=float((fd.z > 2).sum()), top1_k=float(top1_budget("arena55k", "drop")[0].iloc[0]))
fig, axs = plt.subplots(1, 3, figsize=(6.9, 2.1))
sz = np.array([r["size"] for r in res])
axs[0].errorbar(sz, [r["resolvable"] for r in res], yerr=[r["resolvable_sd"] for r in res], c="#0072B2", marker="o", ms=3, capsize=2)
axs[0].plot([57477], [S["scaling_full"]["resolvable"]], marker="o", ms=3, c="#0072B2", mfc="white")
axs[0].set_ylabel("# adjacent pairs with $z>2$")
ek = [(np.array(r["top1_k_q"])) for r in res]
axs[1].plot(sz, [r["top1_k"] for r in res], c="#D55E00", marker="o", ms=3)
axs[1].fill_between(sz, [e[0] for e in ek], [e[1] for e in ek], color="#D55E00", alpha=0.2, lw=0)
axs[1].plot([57477], [S["scaling_full"]["top1_k"]], marker="o", ms=3, c="#D55E00", mfc="white")
axs[1].set_ylabel("$k^\\star$ to dethrone top-1 (drop)"); axs[1].set_yscale("log")
okc = np.array([r["n_rep_c"] >= 10 for r in res])
axs[2].plot(sz[okc], np.array([r["c_med"] for r in res])[okc], c="#009E73", marker="o", ms=3)
axs[2].fill_between(sz[okc], np.array([r["c_lo"] for r in res])[okc], np.array([r["c_hi"] for r in res])[okc], color="#009E73", alpha=0.2, lw=0)
axs[2].set_ylabel(r"$c=k^\star/(z\sqrt{n_{\rm loc}})$ (median)"); axs[2].set_ylim(0, 1)
from matplotlib.ticker import NullFormatter
for ax in axs:
    ax.set_xscale("log"); ax.set_xlabel("# comparisons $N$ (Arena-64 subsample)"); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([1000, 10000, 57477]); ax.set_xticklabels(["1k", "10k", "57k"])
plt.tight_layout(); plt.savefig(f"{F}/fig_scaling.pdf"); plt.savefig(f"/work/tmp/fig_scaling.png", dpi=110); plt.close()

# --------------------------------------------------------------- bootstrap-of-datasets CIs for top-1 budget
bt1 = B[(B.exp == "boot") & (B.kind.isin(["adjacent", "top1"])) & (B["rank"] == 1)]
S["boot_top1"] = {}
for g in B[B.exp == "boot"].board.unique():
    x = bt1[bt1.board == g].groupby("rep").agg(k=("drop", "min"), kr=("relabel", "min"), N=("N", "first"))
    S["boot_top1"][g] = dict(drop_med=float(x.k.median()), drop_ci=[float(x.k.quantile(.025)), float(x.k.quantile(.975))],
                            relabel_med=float(x.kr.median()), relabel_ci=[float(x.kr.quantile(.025)), float(x.kr.quantile(.975))],
                            frac_ci=[float((x.k / x.N).quantile(.025)), float((x.k / x.N).quantile(.975))], N=float(x.N.iloc[0]))
    # share of resamples with an identical top-1 item pair? (rank-1 item identity not stored) -> skip

# --------------------------------------------------------------- z-matched cross-design comparison
zb = [(1, 2), (2, 4), (4, 8), (8, 100)]
tab = []
for g in ORDER:
    a = adj[adj.grp == g]; r = dict(grp=g)
    for lo, hi in zb:
        d = a[(a.z >= lo) & (a.z < hi) & (a["drop"] >= 1)]
        r[f"n_{lo}"] = int(len(d)); r[f"eps_{lo}"] = float((d["drop"] / d.N).median()) if len(d) else np.nan
        r[f"c_{lo}"] = float(d.c_drop.median()) if len(d) else np.nan
    tab.append(r)
S["zmatched"] = tab
with open(f"{R}/tab_zmatched.tex", "w") as f:
    for r in tab:
        cells = []
        for lo, hi in zb:
            cells.append("--" if r[f"n_{lo}"] == 0 else f"{100*r[f'eps_{lo}']:.2f}\\% ({r[f'n_{lo}']})")
        f.write(f"{NAMES[r['grp']]} & " + " & ".join(cells) + " \\\\\n")

# --------------------------------------------------------------- agreement between designs
def fit_scores(d):
    P = bt.Problem(d); return P.items, P.fit()[:P.p]
ag = {}
ma, mb, yh, yj = D.arena_judge("Meta-Llama-3-70B-Instruct")
items_h, th_h = fit_scores(boards.get_all(False)["arenaST_human"]["load"]())
for j in boards.JUDGES:
    items_j, th_j = fit_scores(boards.get_all(False)[f"arenaST_{j}"]["load"]())
    assert items_j == items_h
    ag[j] = dict(tau=bt.kendall(th_h, th_j), top1_same=bool(np.argmax(th_h) == np.argmax(th_j)),
                 label_agree=float(np.mean(((yj if j == boards.JUDGES[0] else D.arena_judge(j)[3]) == yh))))
i_h, t_mh = fit_scores(D.mtbench("human")); i_g, t_mg = fit_scores(D.mtbench("gpt4"))
ag["mt_human_vs_gpt4"] = dict(tau=bt.kendall(t_mh, t_mg), items=i_h, human=list(map(float, t_mh)), gpt4=list(map(float, t_mg)))
i6, t6 = fit_scores(boards.arena_matched6())
ag["arena6"] = dict(items=i6, scores=list(map(float, t6)))
S["agreement"] = ag

# --------------------------------------------------------------- out-of-sample check of the law on Arena-140k
tr = adj[(adj.board != "arena140k") & (adj.z >= ZMIN) & adj["drop"].notna()]
te = adj[(adj.board == "arena140k") & (adj.z >= ZMIN) & adj["drop"].notna()]
Xtr = np.c_[np.ones(len(tr)), np.log(tr.z), np.log(tr.n_loc)]; btr, *_ = np.linalg.lstsq(Xtr, np.log(tr["drop"].values), rcond=None)
pred_fit = np.exp(np.c_[np.ones(len(te)), np.log(te.z), np.log(te.n_loc)] @ btr)
c0 = float(np.median(tr["drop"] / (tr.z * np.sqrt(tr.n_loc))))
pred_c0 = c0 * te.z * np.sqrt(te.n_loc)
err = lambda p_: np.log(p_ / te["drop"].values)
S["oos_140k"] = dict(n_test=int(len(te)), n_train=int(len(tr)), beta=list(map(float, btr)), c0=c0,
                     fit_median_abs_logerr=float(np.median(np.abs(err(pred_fit)))), fit_within25=float(np.mean(np.abs(err(pred_fit)) < np.log(1.25))),
                     fit_within50=float(np.mean(np.abs(err(pred_fit)) < np.log(1.5))),
                     c0_median_abs_logerr=float(np.median(np.abs(err(pred_c0)))), c0_within25=float(np.mean(np.abs(err(pred_c0)) < np.log(1.25))),
                     c0_within50=float(np.mean(np.abs(err(pred_c0)) < np.log(1.5))),
                     test_c_median=float(te.c_drop.median()), test_c_min=float(te.c_drop.min()), test_c_max=float(te.c_drop.max()),
                     test_nloc_max=float(te.n_loc.max()))
# --------------------------------------------------------------- extra search ablations (alpha, target-only injection)
s_ = adj[(adj.z >= ZMIN) & adj["drop"].notna()]
S["search_ablation"] = dict(
    alpha02_equal=float(np.mean(adj.drop_a02 == adj["drop"])), alpha02_smaller=float(np.mean(adj.drop_a02 < adj["drop"])), alpha02_larger=float(np.mean(adj.drop_a02 > adj["drop"])),
    alpha005_equal=float(np.mean(adj.drop_a005 == adj["drop"])), alpha005_smaller=float(np.mean(adj.drop_a005 < adj["drop"])), alpha005_larger=float(np.mean(adj.drop_a005 > adj["drop"])),
    oneshot_equal=float(np.mean(adj.drop_oneshot == adj["drop"])), oneshot_smaller=float(np.mean(adj.drop_oneshot < adj["drop"])), oneshot_larger=float(np.mean(adj.drop_oneshot > adj["drop"])),
    n_adj=int(len(adj)),
    inj_target_over_inject_median=float(np.nanmedian(s_.inject_target / s_.inject)), inj_target_equal=float(np.mean(adj.inject_target == adj.inject)),
    inj_target_over_inject_max=float(np.nanmax(s_.inject_target / s_.inject)), inj_target_over_drop_median=float(np.nanmedian(s_.inject_target / s_["drop"])),
    inj_target_na=float(adj.inject_target.isna().mean()))
# --------------------------------------------------------------- cluster-robustness of z
CC = pd.read_csv(f"{R}/cluster_check.csv"); CC["r_cl_iid"] = CC.sd_cluster / CC.sd_iid; CC["r_iid_model"] = CC.sd_iid / CC.se_model; CC["r_cl_model"] = CC.sd_cluster / CC.se_model
S["cluster"] = {b: dict(cl_over_iid=float(g.r_cl_iid.median()), cl_over_iid_range=[float(g.r_cl_iid.min()), float(g.r_cl_iid.max())],
                        iid_over_model=float(g.r_iid_model.median()), cl_over_model=float(g.r_cl_model.median()),
                        resolved_model=int((g.gap / g.se_model > 2).sum()), resolved_cluster=int((g.gap / g.sd_cluster > 2).sum()), n_clusters=int(g.n_clusters.iloc[0]))
                for b, g in CC.groupby("board")}

# --------------------------------------------------------------- tie-handling ablation (ties discarded)
NT = pd.read_csv(f"{R}/attack_noties.csv"); NT["z"] = NT.z_model
for op in ("drop", "relabel"): NT["c_" + op] = NT[op] / (NT.z * np.sqrt(NT.n_loc))
S["noties"] = {}
for b in ("arena55k", "mt_human", "mt_gpt4"):
    x = NT[(NT.board == b + "_noties") & (NT.kind == "adjacent")]; y0 = adj[adj.board == b]
    t1 = lambda df, op: float(df[(df["rank"] == 1)][op].min())
    S["noties"][b] = dict(N=float(x.N.iloc[0]), res_pairs=int((x.z > 2).sum()), res_pairs_with_ties=int((y0.z > 2).sum()),
                          c_drop=float(x[(x.z >= ZMIN) & x["drop"].notna()].c_drop.median()), c_drop_with_ties=float(y0[(y0.z >= ZMIN)].c_drop.median()),
                          c_relabel=float(x[(x.z >= ZMIN) & x["relabel"].notna()].c_relabel.median()), c_relabel_with_ties=float(y0[(y0.z >= ZMIN)].c_relabel.median()),
                          top1_drop=t1(NT[(NT.board == b + "_noties") & NT.kind.isin(["adjacent", "top1"])], "drop"),
                          top1_drop_with_ties=t1(A[(A.board == b) & A.kind.isin(["adjacent", "top1"])], "drop"),
                          z_med=float(x.z.median()), z_med_with_ties=float(y0.z.median()))
# sensitivity of c to the z cutoff
S["c_vs_zmin"] = {}
for g in ORDER:
    a = adj[adj.grp == g]
    S["c_vs_zmin"][g] = {str(zm): dict(n=int(((a.z >= zm) & a["drop"].notna()).sum()),
                                       c_drop=float(a[(a.z >= zm)].c_drop.median()) if (a.z >= zm).any() else None,
                                       c_relabel=float(a[(a.z >= zm)].c_relabel.median()) if (a.z >= zm).any() else None) for zm in (0.5, 1.0, 2.0)}

# --------------------------------------------------------------- top-k boundary budgets
S["topk"] = {}
for g in ORDER:
    S["topk"][g] = {}
    for k in ("top1", "top3", "top5", "top10"):
        d = A[(A.grp == g) & ((A.kind == k) | ((k == "top1") & (A.kind == "adjacent") & (A["rank"] == 1)))]
        if d.empty: continue
        per = d.groupby("board").agg(drop=("drop", "min"), relabel=("relabel", "min"), N=("N", "first"), z=("z", "min"))
        S["topk"][g][k] = dict(n_boards=int(len(per)), drop=float(per["drop"].median()), relabel=float(per["relabel"].median()),
                               drop_frac=float((per["drop"] / per.N).median()), z_min=float(per.z.median()))
with open(f"{R}/tab_topk.tex", "w") as f:
    for g in ORDER:
        cells = []
        for k in ("top1", "top3", "top5", "top10"):
            v = S["topk"][g].get(k)
            cells.append("--" if v is None else f"{v['drop']:.0f} ({100*v['drop_frac']:.2g}\\%)")
        f.write(f"{NAMES[g]} & " + " & ".join(cells) + " \\\\\n")

# --------------------------------------------------------------- appendix tables
with open(f"{R}/tab_slopes.tex", "w") as f:
    for op in ("drop", "relabel", "inject"):
        v = S["regression"][op]
        f.write(f"{op} (pooled) & {v['n']} & {v['bz']:.2f} [{v['bz_ci'][0]:.2f}, {v['bz_ci'][1]:.2f}] & {v['bn']:.2f} [{v['bn_ci'][0]:.2f}, {v['bn_ci'][1]:.2f}] & {v['resid_sd']:.2f} \\\\\n")
    for op in ("drop",):
        for g, b in S["regression"][op]["by_group"].items():
            f.write(f"\\quad {op}, {NAMES[g]} & {b['n']} & {b['bz']:.2f} & {b['bn']:.2f} & \\\\\n")
with open(f"{R}/tab_czmin.tex", "w") as f:
    for g in ORDER:
        v = S["c_vs_zmin"][g]
        f.write(f"{NAMES[g]} & " + " & ".join(f"{v[z]['c_drop']:.2f} / {v[z]['c_relabel']:.2f} ({v[z]['n']})" if v[z]["c_drop"] is not None else "--" for z in ("0.5", "1.0", "2.0")) + " \\\\\n")
with open(f"{R}/tab_noties.tex", "w") as f:
    for b, v in S["noties"].items():
        f.write(f"{NAMES[b]} & {v['N']:.0f} & {v['res_pairs_with_ties']} / {v['res_pairs']} & {v['c_drop_with_ties']:.2f} / {v['c_drop']:.2f} & {v['c_relabel_with_ties']:.2f} / {v['c_relabel']:.2f} & {v['top1_drop_with_ties']:.0f} / {v['top1_drop']:.0f} \\\\\n")

json.dump(S, open(f"{R}/summary.json", "w"), indent=1, default=float)
print(T2.round(3).to_string())
print(json.dumps(S["regression"], indent=1, default=float)[:3000])

# LaTeX: the last row must not end with \\ inside an \input'd file (main.tex adds it)
import glob, re
for fn in glob.glob(f"{R}/tab_*.tex"):
    t = open(fn).read().rstrip()
    t = re.sub(r"\s*\\\\\s*$", "", t)
    open(fn, "w").write(t + "\n")
