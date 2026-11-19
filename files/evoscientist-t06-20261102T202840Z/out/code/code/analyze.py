"""Aggregate result CSVs into the tables/figures used in the paper.  Run: python code/analyze.py
Outputs: paper/tables/*.tex, paper/figures/*.pdf, results/summary.json"""
import os, json
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RES = os.path.join(ROOT, "results"); TAB = os.path.join(ROOT, "paper", "tables"); FIG = os.path.join(ROOT, "paper", "figures")
os.makedirs(TAB, exist_ok=True); os.makedirs(FIG, exist_ok=True)
rng = np.random.default_rng(2026)
_sf = plt.savefig
PREV = os.path.join(RES, "preview"); os.makedirs(PREV, exist_ok=True)
def _savefig(path, *a, **k):          # also keep a PNG preview of every figure
    _sf(path, *a, **k); _sf(os.path.join(PREV, os.path.basename(path).replace(".pdf", ".png")), dpi=110)
plt.savefig = _savefig
S = {}   # summary numbers quoted in the paper

DES = ["arena", "mt_human", "mt_gpt4", "nba"]
LAB = {"arena": "Arena (crowd votes)", "mt_human": "MT-Bench (human)", "mt_gpt4": "MT-Bench (GPT-4 judge)", "nba": "NBA (games)"}
COL = {"arena": "tab:blue", "mt_human": "tab:green", "mt_gpt4": "tab:red", "nba": "tab:orange"}
MRK = {"arena": "o", "mt_human": "s", "mt_gpt4": "^", "nba": "x"}

P = pd.read_csv(os.path.join(RES, "pairs.csv"))
P["design"] = P.kind
P["gap0"] = P.gap > 1e-9
BR = pd.read_csv(os.path.join(RES, "boot_rank.csv"))
for m in ("remove", "relabel", "insert"):
    P["f_" + m] = P["k_" + m] / P.n_local        # edits as a fraction of the votes involving the two contestants
P["c_relabel"] = P.k_relabel / (P.z * np.sqrt(P.n_local))
P["c_remove"] = P.k_remove / (P.z * np.sqrt(P.n_local))
P["c_insert"] = P.k_insert / (P.z * np.sqrt(P.n_local))


def boot_ci(df, fn, B=2000, cluster=None):
    """percentile bootstrap CI of fn(df); resample rows (or clusters if given)."""
    vals = []
    if cluster is None:
        idx = np.arange(len(df))
        for _ in range(B):
            vals.append(fn(df.iloc[rng.choice(idx, len(idx))]))
    else:
        groups = [g for _, g in df.groupby(cluster)]
        for _ in range(B):
            pick = rng.integers(0, len(groups), len(groups))
            vals.append(fn(pd.concat([groups[t] for t in pick])))
    return np.nanquantile(vals, [0.025, 0.975])


def cl(d):
    return "unit" if d == "nba" else None


def fmt_ci(x, lo, hi, p=2):
    return f"{x:.{p}f} [{lo:.{p}f}, {hi:.{p}f}]"


# ---------------------------------------------------------------- Table 1: overview
rows = []
for d in DES:
    sub = P[P.design == d]; br = BR[BR.kind == d]
    nu = len(br)
    tie = {"arena": 0.309, "mt_human": 0.2325, "mt_gpt4": 0.25, "nba": 0.0}[d]
    res = (sub.z >= 2).mean()
    lo, hi = boot_ci(sub, lambda s: (s.z >= 2).mean(), cluster=cl(d))
    def rng_str(c, p=2):
        v = br[c].values
        return f"{np.median(v):.{p}f}" if nu == 1 else f"{np.median(v):.{p}f} ({v.min():.{p}f}--{v.max():.{p}f})"
    rows.append(dict(design=LAB[d], units=nu, players=int(br.n.median()), N=int(br.N.median()),
                     tie=f"{100*tie:.0f}\\%", tau=rng_str("tau_boot_mean"), top1=rng_str("top1_retention"),
                     resolved=f"{100*res:.0f}\\% [{100*lo:.0f}, {100*hi:.0f}]", gap=f"{sub.gap.median():.3f}"))
    S[f"{d}_resolved"] = float(res)
T = pd.DataFrame(rows)
with open(os.path.join(TAB, "overview.tex"), "w") as f:
    f.write("\\begin{tabular}{lrrrrlll}\\toprule\n Design & \\#boards & players & votes $N$ & ties & bootstrap $\\tau$ & top-1 kept & adjacent pairs $z\\geq2$ \\\\\\midrule\n")
    for r in rows:
        f.write(f"{r['design']} & {r['units']} & {r['players']} & {r['N']} & {r['tie']} & {r['tau']} & {r['top1']} & {r['resolved']} \\\\\n")
    f.write("\\bottomrule\\end{tabular}\n")

# ---------------------------------------------------------------- Table 2: fragility
EPS = [0.005, 0.01, 0.02, 0.05]
def frag(sub, mode, eps):
    return float((sub["f_" + mode] <= eps).mean())

with open(os.path.join(TAB, "fragility.tex"), "w") as f:
    f.write("\\begin{tabular}{llcccc}\\toprule\n Design & pairs & " + " & ".join(f"$\\epsilon$={100*e:g}\\%" for e in EPS) + " \\\\\\midrule\n")
    for sel, nm in ((P.gap0, "all adjacent"), (P.gap0 & (P.z >= 2), "$z\\geq2$")):
        for d in DES:
            sub = P[sel & (P.design == d)]
            cells = []
            for e in EPS:
                x = frag(sub, "relabel", e)
                lo, hi = boot_ci(sub, lambda s: frag(s, "relabel", e), B=1000, cluster=cl(d))
                cells.append(f"{100*x:.0f} [{100*lo:.0f},{100*hi:.0f}]")
                S[f"frag_{d}_{'all' if nm[0]=='a' else 'z2'}_{e}"] = x
            f.write(f"{LAB[d]} & {nm} ($n$={len(sub)}) & " + " & ".join(cells) + " \\\\\n")
        if nm[0] == "a":
            f.write("\\midrule\n")
    f.write("\\bottomrule\\end{tabular}\n")

# fragility for removal-only adversary, text numbers
for d in DES:
    sub = P[P.gap0 & (P.design == d)]
    for e in EPS:
        S[f"fragrem_{d}_all_{e}"] = frag(sub, "remove", e)

# ---------------------------------------------------------------- leader table
with open(os.path.join(TAB, "leader.tex"), "w") as f:
    f.write("\\begin{tabular}{lrrrrrr}\\toprule\n Board & gap $\\hat\\theta_1-\\hat\\theta_2$ & $z$ & $n_{\\rm loc}$ & $k_{\\rm relabel}$ & $k_{\\rm remove}$ & $k_{\\rm relabel}/n_{\\rm loc}$ \\\\\\midrule\n")
    for d in DES:
        sub = P[(P.design == d) & (P["rank"] == 1)]
        def cell(c, p=2, pct=False):
            v = sub[c].values * (100 if pct else 1)
            if len(v) == 1:
                return f"{v[0]:.{p}f}"
            return f"{np.median(v):.{p}f} ({v.min():.{p}f}--{v.max():.{p}f})"
        f.write(f"{LAB[d]} & {cell('gap')} & {cell('z',1)} & {cell('n_local',0)} & {cell('k_relabel',0)} & {cell('k_remove',0)} & {cell('f_relabel',2,True)}\\% \\\\\n")
        S[f"leader_{d}_krelabel_med"] = float(sub.k_relabel.median())
        S[f"leader_{d}_z_med"] = float(sub.z.median())
    f.write("\\bottomrule\\end{tabular}\n")
nba1 = P[(P.design == "nba") & (P["rank"] == 1)]
S["nba_leader_frac_z_lt1"] = float((nba1.z < 1).mean()); S["nba_leader_frac_z_ge2"] = float((nba1.z >= 2).mean())
S["nba_leader_krelabel_range"] = [float(nba1.k_relabel.min()), float(nba1.k_relabel.max())]

# ---------------------------------------------------------------- scaling law c
lawrows = []
for thr in (1, 2):
    for d in DES:
        sub = P[(P.design == d) & (P.z >= thr) & P.gap0]
        if len(sub) < 3:
            lawrows.append((thr, d, len(sub), None)); continue
        out = {}
        for m in ("relabel", "remove", "insert"):
            x = sub["c_" + m].median()
            lo, hi = boot_ci(sub, lambda s: s["c_" + m].median(), B=1000, cluster=cl(d))
            out[m] = (x, lo, hi)
            S[f"c_{m}_{d}_z{thr}"] = float(x)
        lawrows.append((thr, d, len(sub), out))
with open(os.path.join(TAB, "law.tex"), "w") as f:
    f.write("\\begin{tabular}{llrccc}\\toprule\n$z\\geq$ & Design & pairs & $c_{\\rm relabel}$ & $c_{\\rm remove}$ & $c_{\\rm insert}$ \\\\\\midrule\n")
    for thr, d, n, out in lawrows:
        if out is None:
            f.write(f"{thr} & {LAB[d]} & {n} & -- & -- & -- \\\\\n"); continue
        f.write(f"{thr} & {LAB[d]} & {n} & " + " & ".join(fmt_ci(*out[m]) for m in ("relabel", "remove", "insert")) + " \\\\\n")
        S[f"npairs_{d}_z{thr}"] = n
    f.write("\\bottomrule\\end{tabular}\n")
# pooled log-log regression
sub = P[(P.z >= 1) & P.gap0 & np.isfinite(P.k_relabel)]
X = np.c_[np.ones(len(sub)), np.log(sub.z), np.log(sub.n_local)]
for m in ("relabel", "remove"):
    y = np.log(sub["k_" + m].values)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    bs = []
    ids = np.arange(len(sub))
    # cluster by board
    boards = sub.unit.values; ub = np.unique(boards)
    for _ in range(1000):
        pick = rng.choice(ub, len(ub))
        ix = np.concatenate([np.where(boards == u)[0] for u in pick])
        bs.append(np.linalg.lstsq(X[ix], y[ix], rcond=None)[0])
    bs = np.array(bs)
    S[f"loglog_{m}"] = dict(beta=beta.tolist(), lo=np.quantile(bs, .025, axis=0).tolist(), hi=np.quantile(bs, .975, axis=0).tolist(),
                           resid_sd=float((y - X @ beta).std()), n=len(sub))

# ---------------------------------------------------------------- kappa: fraction of local votes per logit of gap
KMIN = 5   # exclude pairs whose greedy budget is < 5 edits (integer rounding dominates)
kap_rows = []
for d in DES:
    sub = P[(P.design == d) & (P.gap > 0.05) & (P.k_relabel >= KMIN)].copy()
    out = {}
    for m in ("relabel", "remove", "insert"):
        sub["kap_" + m] = sub["f_" + m].div(sub.gap)
        x = sub["kap_" + m].median()
        lo, hi = boot_ci(sub, lambda s_: s_["kap_" + m].median(), B=1000, cluster=cl(d))
        out[m] = (x, lo, hi); S[f"kappa_{m}_{d}"] = float(x)
    S[f"kappa_n_{d}"] = int(len(sub))
    kap_rows.append((d, len(sub), out))
with open(os.path.join(TAB, "kappa.tex"), "w") as f:
    f.write("\\begin{tabular}{lrccc}\\toprule\nDesign & pairs & $\\kappa_{\\rm relabel}$ & $\\kappa_{\\rm remove}$ & $\\kappa_{\\rm insert}$ \\\\\\midrule\n")
    for d, n, out in kap_rows:
        f.write(f"{LAB[d]} & {n} & " + " & ".join(fmt_ci(*out[m], p=3) for m in ("relabel", "remove", "insert")) + " \\\\\n")
    f.write("\\bottomrule\\end{tabular}\n")
sub = P[(P.gap > 0.05) & (P.k_relabel >= KMIN)]
for m in ("relabel", "remove", "insert"):
    X = np.c_[np.ones(len(sub)), np.log(sub.gap)]
    y = np.log(sub["f_" + m].values)
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    boards = sub.unit.values; ub = np.unique(boards); bs = []
    for _ in range(1000):
        pick = rng.choice(ub, len(ub))
        ix = np.concatenate([np.where(boards == u)[0] for u in pick])
        bs.append(np.linalg.lstsq(X[ix], y[ix], rcond=None)[0][1])
    S[f"logf_gap_{m}"] = dict(slope=float(beta[1]), lo=float(np.quantile(bs, .025)), hi=float(np.quantile(bs, .975)), resid_sd=float((y - X @ beta).std()), n=len(sub))
S["kappa_pooled_range_relabel"] = [float(sub.f_relabel.div(sub.gap).min()), float(sub.f_relabel.div(sub.gap).max())]

# Figure 1: (a) fraction of local votes vs gap, (b) k vs z sqrt(n_loc)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1))
for d in DES:
    s_ = P[(P.design == d) & P.gap0]
    axs[0].scatter(s_.gap, s_.f_relabel, s=13, marker=MRK[d], c=COL[d], alpha=.7, label=LAB[d], linewidths=1 if d == "nba" else 0.3)
    s_ = P[(P.design == d) & (P.z >= 0.5) & P.gap0]
    axs[1].scatter(s_.z * np.sqrt(s_.n_local), s_.k_relabel, s=13, marker=MRK[d], c=COL[d], alpha=.7, linewidths=1 if d == "nba" else 0.3)
xs = np.logspace(-3, 0.3, 10)
axs[0].plot(xs, 0.06 * xs, "k--", lw=.8, label=r"$f=0.06\,\Delta\theta$")
axs[0].plot(xs, 0.12 * xs, "k:", lw=.8, label=r"$f=0.12\,\Delta\theta$")
axs[0].set_xscale("log"); axs[0].set_yscale("log"); axs[0].set_xlabel(r"BT gap $\hat\theta_i-\hat\theta_j$ (logits)"); axs[0].set_ylabel(r"relabelled votes / $n_{\rm loc}$")
axs[0].legend(fontsize=6, frameon=False, loc="upper left")
xs = np.logspace(0.3, 3.2, 10)
axs[1].plot(xs, 0.2 * xs, "k--", lw=.8, label=r"$k=0.2\,z\sqrt{n_{\rm loc}}$"); axs[1].plot(xs, 0.4 * xs, "k:", lw=.8, label=r"$k=0.4\,z\sqrt{n_{\rm loc}}$")
axs[1].set_xscale("log"); axs[1].set_yscale("log"); axs[1].set_xlabel(r"$z\sqrt{n_{\rm loc}}$"); axs[1].set_ylabel("relabels $k$ needed to flip the pair")
axs[1].legend(fontsize=6, frameon=False, loc="upper left")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_law.pdf")); plt.close()

# ---------------------------------------------------------------- Figure 2: fragility curves
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=True)
eg = np.logspace(-3.3, -0.7, 60)
for ax, sel, ttl in ((axs[0], P.gap0, "all adjacent pairs"), (axs[1], P.gap0 & (P.z >= 2), r"resolved pairs ($z\geq2$)")):
    for d in DES:
        s = P[sel & (P.design == d)]
        ax.plot(eg, [(s.f_relabel <= e).mean() for e in eg], c=COL[d], label=LAB[d] + f" (n={len(s)})")
    ax.set_xscale("log"); ax.set_xlabel(r"fraction $\epsilon$ of the contestants' votes relabelled"); ax.set_title(ttl, fontsize=9)
axs[0].set_ylabel("fraction of adjacent pairs flipped")
axs[0].legend(fontsize=6, frameon=False, loc="upper left")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_fragility.pdf")); plt.close()

# ---------------------------------------------------------------- Rank shift
R = pd.read_csv(os.path.join(RES, "rankshift.csv"))
R["design"] = np.where(R.unit.str.startswith("nba"), "nba", R.unit)
R["f_relabel"] = R.k_relabel / R.n_local; R["gap0"] = R.gap > 1e-9
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
for d in DES:
    s = R[R.design == d]
    g = s.groupby("d")
    axs[0].errorbar(g.f_relabel.median().index + (0.06 * DES.index(d) - .09), 100 * g.f_relabel.median(),
                    yerr=[100 * (g.f_relabel.median() - g.f_relabel.quantile(.25)), 100 * (g.f_relabel.quantile(.75) - g.f_relabel.median())],
                    c=COL[d], marker=MRK[d], ms=4, lw=1, capsize=2, label=LAB[d])
    s2 = s[s.d == 1]
    S[f"rankshift_{d}_d1_med"] = float(s2.f_relabel.median()); S[f"rankshift_{d}_d5_med"] = float(s[s.d == 5].f_relabel.median())
    axs[1].plot(range(1, 6), [(s[s.d == dd].f_relabel <= 0.01).mean() for dd in range(1, 6)], c=COL[d], marker=MRK[d], ms=4, lw=1)
axs[0].set_yscale("log"); axs[0].set_xlabel("rank distance $d$ (pair $r$ vs $r{+}d$)"); axs[0].set_ylabel(r"relabelled, % of $n_{\rm loc}$ (median, IQR)", fontsize=8)
axs[1].set_xlabel("rank distance $d$"); axs[1].set_ylabel(r"fraction flippable with $\leq1\%$ of $n_{\rm loc}$")
axs[0].legend(fontsize=6, frameon=False)
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_rankshift.pdf")); plt.close()
# leader dethroning cost vs d in text
for d in DES:
    s = R[(R.design == d) & (R["rank"] == 1)]
    S[f"leader_shift_{d}"] = {int(dd): float(s[s.d == dd].k_relabel.median()) for dd in range(1, 6)}

# ---------------------------------------------------------------- Noise vs adversary
Nz = pd.read_csv(os.path.join(RES, "noise.csv"))
Nz["design"] = np.where(Nz.unit.str.startswith("nba"), "nba", Nz.unit)
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.9))
for d in DES:
    s = Nz[(Nz.design == d) & (Nz.kind == "relabel")]
    g = s.groupby("f")
    axs[0].errorbar(g.tau.mean().index, g.tau.mean(), yerr=1.96 * g.tau.std() / np.sqrt(g.tau.count()), c=COL[d], marker=MRK[d], ms=3, lw=1, capsize=2, label=LAB[d])
    b = BR[BR.kind == d]
    axs[0].axhline(b.tau_boot_mean.mean(), c=COL[d], ls=":", lw=.8)
    ga = s.groupby("f").adj_flip.mean()
    axs[1].plot(ga.index, ga.values, c=COL[d], marker=MRK[d], ms=3, lw=1, label=LAB[d] + " (random)")
    sa = P[P.gap0 & (P.design == d)]
    axs[1].plot(eg, [(sa.f_relabel <= e).mean() for e in eg], c=COL[d], ls="--", lw=1)
    S[f"noise_tau_{d}"] = {str(k): float(v) for k, v in g.tau.mean().items()}
    S[f"noise_adjflip_{d}"] = {str(k): float(v) for k, v in ga.items()}
    S[f"boot_tau_{d}"] = float(b.tau_boot_mean.mean())
axs[0].set_xscale("log"); axs[0].set_xlabel("fraction $f$ of votes randomly relabelled"); axs[0].set_ylabel("Kendall $\\tau$ to original ranking")
axs[1].set_xscale("log"); axs[1].set_xlabel("fraction of votes edited"); axs[1].set_ylabel("fraction of adjacent pairs flipped")
axs[1].set_xlim(1.5e-3, 0.5)
axs[0].legend(fontsize=6, frameon=False, loc="lower left")
axs[1].text(0.03, 0.9, "solid: random relabel of $f N$ votes\ndashed: targeted relabel of $\\epsilon n_{\\rm loc}$ votes", transform=axs[1].transAxes, fontsize=6, va="top")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_noise.pdf")); plt.close()

# ---------------------------------------------------------------- Subsampling (Arena)
Sb = pd.read_csv(os.path.join(RES, "subsample.csv"))
Sb["c"] = Sb.k_relabel / (Sb.z * np.sqrt(Sb.n_local)); Sb["f_rel"] = Sb.k_relabel / Sb.n_local
full = P[P.design == "arena"].copy(); full["frac"] = 1.0; full["rep"] = 0; full["c"] = full.c_relabel; full["f_rel"] = full.f_relabel
Sb2 = pd.concat([Sb, full[Sb.columns.intersection(full.columns)]])
srow = []
for fr, g in Sb2.groupby("frac"):
    gg = g[(g.z >= 1) & (g.gap > 1e-9)]
    g2 = g[(g.z >= 2) & (g.gap > 1e-9)]
    srow.append(dict(frac=fr, N=int(g.N.median()), n_loc=g.n_local.median(), resolved=float((g.z >= 2).mean()), c_med=float(gg.c.median()),
                     f_resolved_med=float(g2.f_rel.median()) if len(g2) else np.nan, med_gap=float(g.gap.median()), k_med_resolved=float(g2.k_relabel.median()) if len(g2) else np.nan))
SB = pd.DataFrame(srow); S["subsample"] = SB.to_dict("records")
# a fixed pair across subsample sizes
fixed = ("gpt-4-0314", "gpt-4-0613")
fr_rows = []
for fr, g in Sb2.groupby("frac"):
    h = g[(g.a == fixed[0]) & (g.b == fixed[1])]
    if len(h):
        fr_rows.append(dict(frac=fr, reps=len(h), gap=h.gap.mean(), z=h.z.mean(), n_loc=h.n_local.mean(), k=h.k_relabel.mean(), f=100 * h.f_rel.mean(), f_sd=100 * h.f_rel.std(ddof=1) if len(h) > 1 else np.nan))
FX = pd.DataFrame(fr_rows); S["fixed_pair"] = FX.to_dict("records")
Sb["kap"] = Sb.f_rel.div(Sb.gap)
ks = Sb[(Sb.gap > 0.05) & (Sb.k_relabel >= KMIN)].groupby("frac").kap.agg(["median", "count"])
S["subsample_kappa"] = {str(k): [float(v["median"]), int(v["count"])] for k, v in ks.iterrows()}
kfull = float(P[(P.design == "arena") & (P.gap > 0.05) & (P.k_relabel >= KMIN)].f_relabel.div(P.gap).median())
fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.7))
axs[0].plot(list(ks.index) + [1.0], list(ks["median"]) + [kfull], "o-", c="tab:blue", label=r"$\kappa_{\rm relabel}$ (median)")
axs[0].plot(SB.frac, SB.c_med, "s--", c="tab:gray", label=r"$c_{\rm relabel}$ (median)")
axs[0].set_xscale("log"); axs[0].set_ylim(0, 0.3); axs[0].set_xlabel("fraction of Arena votes kept"); axs[0].legend(fontsize=6, frameon=False)
axs[1].plot(SB.frac, 100 * SB.resolved, "o-", c="tab:red"); axs[1].set_xscale("log")
axs[1].set_xlabel("fraction of Arena votes kept"); axs[1].set_ylabel(r"adjacent pairs with $z\geq2$ (%)")
plt.tight_layout(); plt.savefig(os.path.join(FIG, "fig_subsample.pdf")); plt.close()

# ---------------------------------------------------------------- Matched control
M = pd.read_csv(os.path.join(RES, "matched.csv")); MS = pd.read_csv(os.path.join(RES, "matched_sub.csv"))
MH = P[P.unit == "mt_human"]
MS["f"] = MS.k_relabel / MS.n_local; MS["c"] = MS.k_relabel / (MS.z * np.sqrt(MS.n_local))
M["f"] = M.k_relabel / M.n_local; M["c"] = M.k_relabel / (M.z * np.sqrt(M.n_local))
with open(os.path.join(TAB, "matched.tex"), "w") as f:
    f.write("\\begin{tabular}{llrrrrr}\\toprule\n Board & adjacent pair & gap & $z$ & $n_{\\rm loc}$ & $k_{\\rm relabel}$ & $k/n_{\\rm loc}$ (\\%) \\\\\\midrule\n")
    for r in range(1, 6):
        a = M[M["rank"] == r].iloc[0]
        f.write(f"Arena-6 (crowd, $N$=1367) & {a.a} / {a.b} & {a.gap:.2f} & {a.z:.1f} & {a.n_local:.0f} & {a.k_relabel:.0f} & {100*a.f:.1f} \\\\\n")
    f.write("\\midrule\n")
    for u, nm in (("mt_human", "MT-Bench human, subsampled to 1367"), ("mt_gpt4", "MT-Bench GPT-4, subsampled to 1367")):
        for r in range(1, 6):
            g = MS[(MS.unit == u) & (MS["rank"] == r)]
            f.write(f"{nm} & rank {r}--{r+1} & {g.gap.mean():.2f} & {g.z.mean():.1f} & {g.n_local.mean():.0f} & {g.k_relabel.mean():.0f} & {100*g.f.mean():.1f} \\\\\n")
        f.write("\\midrule\n" if u == "mt_human" else "")
    f.write("\\bottomrule\\end{tabular}\n")
S["matched_arena6_c_relabel_med"] = float(M.c.median()); S["matched_arena6_f"] = M.f.tolist(); S["matched_arena6_z"] = M.z.tolist()
S["matched_mthuman_sub_c_med"] = float(MS[(MS.unit == "mt_human") & (MS.z >= 1)].c.median())
S["matched_mtgpt4_sub_c_med"] = float(MS[(MS.unit == "mt_gpt4") & (MS.z >= 1)].c.median())
S["matched_mthuman_sub_f"] = {int(r): float(MS[(MS.unit == "mt_human") & (MS["rank"] == r)].f.mean()) for r in range(1, 6)}
S["matched_mthuman_sub_z"] = {int(r): float(MS[(MS.unit == "mt_human") & (MS["rank"] == r)].z.mean()) for r in range(1, 6)}
S["matched_arena6_kappa"] = (M.f / M.gap).tolist(); S["matched_arena6_kappa_med"] = float((M.f / M.gap).median())
MSg = MS[(MS.gap > 0.05) & (MS.k_relabel >= 5)]
S["matched_mthuman_sub_kappa_med"] = float((MSg[MSg.unit == "mt_human"].f / MSg[MSg.unit == "mt_human"].gap).median())
S["matched_mtgpt4_sub_kappa_med"] = float((MSg[MSg.unit == "mt_gpt4"].f / MSg[MSg.unit == "mt_gpt4"].gap).median())
# standardise: relabel fraction vs gap
S["matched_arena6_gap"] = M.gap.tolist()
S["mthuman_full_f"] = MH.f_relabel.tolist(); S["mthuman_full_z"] = MH.z.tolist()

# ---------------------------------------------------------------- Greedy quality / first-order
G = pd.read_csv(os.path.join(RES, "robust_greedy_exact.csv"))
S["greedy_exact"] = {m: dict(n=int(len(g)), optimal=float((g.greedy == g.exact).mean()), max_ratio=float((g.greedy / g.exact).max()), mean_ratio=float((g.greedy / g.exact).mean())) for m, g in G.groupby("mode")}
fin = P[(P.k_remove >= 5) & np.isfinite(P.k_remove)]
S["oneshot_ratio"] = {m: dict(median=float((fin["oneshot_" + m] / fin["k_" + m]).median()), q10=float((fin["oneshot_" + m] / fin["k_" + m]).quantile(.1)), q90=float((fin["oneshot_" + m] / fin["k_" + m]).quantile(.9)), n=int(len(fin)))
                      for m in ("remove", "relabel", "insert")}
S["relabel_over_remove_med"] = float((P.k_relabel / P.k_remove)[P.k_remove >= 5].median())
S["insert_over_remove_med"] = float((P.k_insert / P.k_remove)[P.k_remove >= 5].median())
S["relabel_over_remove_q"] = [float(x) for x in (P.k_relabel / P.k_remove)[P.k_remove >= 5].quantile([.1, .9])]
S["rand_flip_rate_max"] = float(P.rand_remove_flip_rate.max()); S["rand_flip_rate_mean"] = float(P.rand_remove_flip_rate.mean())
S["rand_flip_rate_mean_k_ge5"] = float(P[P.k_remove >= 5].rand_remove_flip_rate.mean())
S["pflip_vs_z"] = dict(z_lt1=float(P[P.z < 1].p_flip_boot.mean()), z_1_2=float(P[(P.z >= 1) & (P.z < 2)].p_flip_boot.mean()), z_ge2=float(P[P.z >= 2].p_flip_boot.mean()))
# edits needed vs "statistical" budget : pairs not distinguished by sampling noise
S["frac_pairs_z_lt2"] = {d: float((P[P.design == d].z < 2).mean()) for d in DES}
S["k_le_5_frac"] = {d: float((P[(P.design == d)].k_relabel <= 5).mean()) for d in DES}
S["n_pairs"] = {d: int((P.design == d).sum()) for d in DES}

# ---------------------------------------------------------------- Robustness
RL = pd.read_csv(os.path.join(RES, "robust_lambda.csv"))
rl = []
base = RL[RL.lam == 1e-3].set_index(["unit", "rank"])
for lam, g in RL.groupby("lam"):
    g = g.set_index(["unit", "rank"]).join(base[["k_relabel", "k_remove", "z"]], rsuffix="_base")
    ok = g.k_relabel_base >= 5
    ratio = (g.k_relabel / g.k_relabel_base)[ok]
    gz = g[(g.z >= 1) & (g.gap > 1e-9)]
    c = (gz.k_relabel / (gz.z * np.sqrt(gz.n_local))).median()
    gk = g[(g.gap > 0.05) & (g.k_relabel >= KMIN)]
    kap = (gk.k_relabel.div(gk.n_local).div(gk.gap)).median()
    rl.append(dict(kappa=float(kap), lam=lam, ratio_med=float(ratio.median()), ratio_q=[float(x) for x in ratio.quantile([.05, .95])], c_med=float(c), n=int(ok.sum())))
S["robust_lambda"] = rl
RN = pd.read_csv(os.path.join(RES, "robust_noties.csv"))
RN["c"] = RN.k_relabel / (RN.z * np.sqrt(RN.n_local))
S["robust_noties_c"] = {u: float(g[(g.z >= 1) & (g.gap > 1e-9)].c.median()) for u, g in RN.groupby("unit")}
RN["kap"] = RN.k_relabel.div(RN.n_local).div(RN.gap)
S["robust_noties_kappa"] = {u: float(g[(g.gap > 0.05) & (g.k_relabel >= KMIN)].kap.median()) for u, g in RN.groupby("unit")}
S["robust_noties_n"] = {u: int(((g.z >= 1) & (g.gap > 1e-9)).sum()) for u, g in RN.groupby("unit")}
RC = pd.read_csv(os.path.join(RES, "robust_cluster.csv"))
base_mt = P[P.unit.isin(["mt_human", "mt_gpt4"])].set_index(["unit", "rank"])
RC = RC.set_index(["unit", "rank"])
RC["z_vote"] = base_mt.z
RC["c_cluster"] = RC.k_relabel / (RC.z * np.sqrt(RC.n_local)); RC["c_vote"] = RC.k_relabel / (RC.z_vote * np.sqrt(RC.n_local))
S["robust_cluster"] = {u: dict(z_ratio_med=float((g.z / g.z_vote).median()), c_cluster_med=float(g[g.z >= 1].c_cluster.median()), c_vote_med=float(g[g.z_vote >= 1].c_vote.median()),
                               z_cluster=g.z.tolist(), z_vote=g.z_vote.tolist()) for u, g in RC.reset_index().set_index("unit").groupby(level=0)} if False else \
    {u: dict(z_ratio_med=float((RC.loc[u].z / RC.loc[u].z_vote).median()), c_cluster_med=float(RC.loc[u][RC.loc[u].z >= 1].c_cluster.median()),
             c_vote_med=float(RC.loc[u][RC.loc[u].z_vote >= 1].c_vote.median()), z_cluster=RC.loc[u].z.round(2).tolist(), z_vote=RC.loc[u].z_vote.round(2).tolist()) for u in ("mt_human", "mt_gpt4")}

P["s_inv"] = P.boot_sd * np.sqrt(P.n_local)
S["sd_sqrt_nloc"] = {d: [float(P[P.design == d].s_inv.median()), float(P[P.design == d].s_inv.quantile(.1)), float(P[P.design == d].s_inv.quantile(.9))] for d in DES}
# overview numbers
S["boards"] = {d: dict(N=int(BR[BR.kind == d].N.median()), tau=float(BR[BR.kind == d].tau_boot_mean.mean()), top1=float(BR[BR.kind == d].top1_retention.median())) for d in DES}
S["nba_top1_retention"] = BR[BR.kind == "nba"].top1_retention.tolist()
S["arena_gaps_top"] = P[(P.design == "arena") & (P["rank"] <= 6)][["a", "b", "gap", "z", "k_relabel", "k_remove", "n_local"]].to_dict("records")
json.dump(S, open(os.path.join(RES, "summary.json"), "w"), indent=1, default=float)
print("ok")
