"""Tables/figures for the synthetic experiments (main grid). Usage: python code/analyze_synth.py"""
import os, sys, json
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_common import *

os.makedirs("figures", exist_ok=True); os.makedirs("tables", exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8, "legend.fontsize": 7,
                     "xtick.labelsize": 7, "ytick.labelsize": 7, "figure.dpi": 150, "pdf.fonttype": 42})
df = pd.read_csv("results/synth_main.csv")
SUMMARY = {}

# ------------------------------------------------------------------ aggregate table
A = agg(df, ["dgp", "K", "n_cal", "method"], ["cov", "size_pool", "size_unif"])
gaps = []
for (dgp, K, n_cal, m), g in df.groupby(["dgp", "K", "n_cal", "method"]):
    e, lo, hi, cov = group_gap(g, "ent", 3)
    ea, loa, hia, cova = group_gap(g, "arg", K, min_n=1)
    z0 = g["g_zero0_c"].sum() / max(g["g_zero0_n"].sum(), 1)
    z1 = g["g_zero1_c"].sum() / g["g_zero1_n"].sum() if g["g_zero1_n"].sum() > 0 else np.nan
    gaps.append(dict(dgp=dgp, K=K, n_cal=n_cal, method=m, ent_gap=e, ent_lo=lo, ent_hi=hi, arg_gap=ea,
                     arg_lo=loa, arg_hi=hia, cov_zero0=z0, cov_zero1=z1, ent_min=cov.min(), ent_cov0=cov[0],
                     ent_cov2=cov[-1]))
G = pd.DataFrame(gaps)
A = A.merge(G, on=["dgp", "K", "n_cal", "method"])
A.to_csv("results/summary_synth_main.csv", index=False)


def fmt(m, hw, d=3):
    return f"{m:.{d}f}\\,$\\pm$\\,{hw:.{d}f}"


# ------------------------------------------------------------------ main table (n_cal=200, K=5)
sub = A[(A.n_cal == 200) & (A.K == 5)]
lines = [r"\begin{tabular}{l" + "rr" * 4 + "}", r"\toprule",
         " & " + " & ".join([r"\multicolumn{2}{c}{" + DGPN[d] + "}" for d in DGPN]) + r" \\",
         "Score & " + " & ".join(["size", "gap"] * 4) + r" \\", r"\midrule"]
best = {d: sub[sub.dgp == d].size_pool.min() for d in DGPN}
for m in ORDER:
    cells = []
    for d in DGPN:
        r = sub[(sub.dgp == d) & (sub.method == m)].iloc[0]
        s = f"{r.size_pool:.3f}"
        if r.size_pool <= best[d] * 1.0000001: s = r"\textbf{" + s + "}"
        cells += [s, f"{r.ent_gap:.3f}"]
    lines.append(NAMES[m] + " & " + " & ".join(cells) + r" \\")
lines += [r"\bottomrule", r"\end{tabular}"]
open("tables/tab_main.tex", "w").write("\n".join(lines))

# ------------------------------------------------------------------ coverage / validity table (appendix)
A["target"] = [np.ceil((n + 1) * (1 - ALPHA)) / (n + 1) for n in A.n_cal]
V = A[~A.method.str.contains("mond")].copy()
V["excess"] = V["cov"] - V["target"]
Vs = V.groupby("method").agg(cov_min=("cov", "min"), cov_max=("cov", "max"), exc_mean=("excess", "mean"),
                              exc_min=("excess", "min"), exc_max=("excess", "max"),
                              n_cells=("cov", "size"), hw_mean=("cov_hw", "mean")).reset_index()
V["z"] = V.excess / (V.cov_hw / 1.96)
Vs["max_abs_z"] = V.groupby("method").z.apply(lambda s: s.abs().max()).values
Vs["n_|z|>3"] = V.groupby("method").z.apply(lambda s: (s.abs() > 3).sum()).values
Vs.to_csv("results/summary_validity.csv", index=False)
lines = [r"\begin{tabular}{lrrrrr}", r"\toprule",
         r"Score & min cov. & max cov. & mean excess & max $|z|$ & cells $|z|>3$ \\", r"\midrule"]
for m in [x for x in ORDER if "mond" not in x]:
    r = Vs[Vs.method == m].iloc[0]
    lines.append(f"{NAMES[m]} & {r.cov_min:.3f} & {r.cov_max:.3f} & {r.exc_mean:+.4f} & {r.max_abs_z:.1f} & {int(r['n_|z|>3'])}/36 \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open("tables/tab_validity.tex", "w").write("\n".join(lines))
M = A[A.method.str.contains("mond")].copy()
M["target_note"] = M["cov"]
SUMMARY["mond_cov_range"] = [float(M["cov"].min()), float(M["cov"].max())]

# ------------------------------------------------------------------ full grid table (appendix): size_pool
lines = [r"\begin{tabular}{llr" + "r" * 10 + "}", r"\toprule",
         r"DGP & $K$ & $n_{cal}$ & " + " & ".join(NAMES[m] for m in ORDER) + r" \\", r"\midrule"]
for d in DGPN:
    for K in [3, 5, 10]:
        for n in [50, 200, 1000]:
            s = A[(A.dgp == d) & (A.K == K) & (A.n_cal == n)].set_index("method")
            b = s.loc[ORDER].size_pool.min()
            cells = [(r"\textbf{" + f"{s.loc[m].size_pool:.3f}" + "}") if s.loc[m].size_pool <= b * 1.0000001 else f"{s.loc[m].size_pool:.3f}" for m in ORDER]
            lines.append(f"{DGPN[d]} & {K} & {n} & " + " & ".join(cells) + r" \\")
    lines.append(r"\midrule")
lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
open("tables/tab_grid_size.tex", "w").write("\n".join(lines))
# full grid table: worst entropy-group gap
lines = [r"\begin{tabular}{llr" + "r" * 10 + "}", r"\toprule",
         r"DGP & $K$ & $n_{cal}$ & " + " & ".join(NAMES[m] for m in ORDER) + r" \\", r"\midrule"]
for d in DGPN:
    for K in [3, 5, 10]:
        for n in [50, 200, 1000]:
            s = A[(A.dgp == d) & (A.K == K) & (A.n_cal == n)].set_index("method")
            lines.append(f"{DGPN[d]} & {K} & {n} & " + " & ".join(f"{s.loc[m].ent_gap:.3f}" for m in ORDER) + r" \\")
    lines.append(r"\midrule")
lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
open("tables/tab_grid_gap.tex", "w").write("\n".join(lines))

# ------------------------------------------------------------------ heatmap of relative size
cols = [(d, K) for d in DGPN for K in [3, 5, 10]]
Hm = np.zeros((len(ORDER), len(cols)))
for j, (d, K) in enumerate(cols):
    s = A[(A.dgp == d) & (A.K == K) & (A.n_cal == 200)].set_index("method")
    for i, m in enumerate(ORDER):
        Hm[i, j] = np.log2(s.loc[m].size_pool / s.loc["l2"].size_pool)
fig, ax = plt.subplots(figsize=(6.8, 2.6))
im = ax.imshow(Hm, cmap="RdBu_r", vmin=-2.5, vmax=2.5, aspect="auto")
for i in range(Hm.shape[0]):
    for j in range(Hm.shape[1]):
        ax.text(j, i, f"{2 ** Hm[i, j]:.2f}", ha="center", va="center", fontsize=6)
ax.set_xticks(range(len(cols))); ax.set_xticklabels([f"{DGPN[d]}\nK={K}" for d, K in cols], fontsize=5.5)
ax.set_yticks(range(len(ORDER))); ax.set_yticklabels([PLAIN[m] for m in ORDER])
plt.colorbar(im, ax=ax, label=r"$\log_2$(size / size of $\ell_2$)", pad=0.01)
plt.tight_layout(); plt.savefig("figures/fig_relsize.pdf"); plt.close()

# ------------------------------------------------------------------ measure agreement
rows = []
for d in DGPN:
    for K in [3, 5]:
        for n in [50, 200, 1000]:
            s = A[(A.dgp == d) & (A.K == K) & (A.n_cal == n)].set_index("method").loc[ORDER]
            tau = stats.kendalltau(s.size_pool, s.size_unif)[0]
            rows.append(dict(dgp=d, K=K, n_cal=n, tau=tau, best_pool=s.size_pool.idxmin(), best_unif=s.size_unif.idxmin(),
                             rank_pool_l2=int(s.size_pool.rank()["l2"]), rank_unif_l2=int(s.size_unif.rank()["l2"]),
                             rank_pool_hell=int(s.size_pool.rank()["hell"]), rank_unif_hell=int(s.size_unif.rank()["hell"])))
T = pd.DataFrame(rows); T.to_csv("results/summary_measure_agreement.csv", index=False)
SUMMARY["kendall_min"] = float(T.tau.min()); SUMMARY["kendall_median"] = float(T.tau.median())
SUMMARY["best_differs_frac"] = float((T.best_pool != T.best_unif).mean())
lines = [r"\begin{tabular}{llrrll}", r"\toprule", r"DGP & $K$ & $n_{cal}$ & Kendall $\tau$ & best (pool) & best (uniform) \\", r"\midrule"]
for _, r in T.iterrows():
    lines.append(f"{DGPN[r.dgp]} & {r.K} & {r.n_cal} & {r.tau:.2f} & {NAMES[r.best_pool]} & {NAMES[r.best_unif]} \\\\")
lines += [r"\bottomrule", r"\end{tabular}"]
open("tables/tab_measure.tex", "w").write("\n".join(lines))

# ------------------------------------------------------------------ paired differences (Holm)
comps = [("ait", "l2"), ("hell", "l2"), ("ait", "hell"), ("kl", "hell"), ("l2n", "l2"), ("l2_mond", "l2"), ("ait_mond", "ait")]
P = pd.concat([paired_diff(df, a, b, "size_pool", ["dgp", "K", "n_cal"]) for a, b in comps])
P["p_holm"] = holm(P.p.to_numpy())
P.to_csv("results/summary_paired_size.csv", index=False)
cnt = P.assign(sig=P.p_holm < 0.05, neg=P["diff"] < 0).groupby(["a", "b"]).apply(
    lambda g: pd.Series(dict(n=len(g), a_smaller=int((g.sig & g.neg).sum()), a_larger=int((g.sig & ~g.neg).sum()),
                             ns=int((~g.sig).sum()))), include_groups=False).reset_index()
cnt.to_csv("results/summary_paired_counts.csv", index=False)
print(cnt.to_string())
# appendix table: paired relative differences at n_cal=200
lines = [r"\begin{tabular}{llrrrr}", r"\toprule", r"Comparison & $K$ & " + " & ".join(DGPN[d] for d in DGPN) + r" \\", r"\midrule"]
for a, b in comps:
    for K in [3, 5, 10]:
        cells = []
        for d in DGPN:
            r = P[(P.a == a) & (P.b == b) & (P.dgp == d) & (P.K == K) & (P.n_cal == 200)].iloc[0]
            star = "*" if r.p_holm < 0.05 else ""
            cells.append(f"{100 * r.rel:+.0f}\\%{star}")
        lines.append((f"{NAMES[a]} vs {NAMES[b]}" if K == 3 else "") + f" & {K} & " + " & ".join(cells) + r" \\")
    lines.append(r"\midrule")
lines[-1] = r"\bottomrule"; lines.append(r"\end{tabular}")
open("tables/tab_paired.tex", "w").write("\n".join(lines))

# ------------------------------------------------------------------ conditional coverage figure (entropy terciles)
fig, axs = plt.subplots(1, 4, figsize=(6.8, 1.9), sharey=True)
meths = ["l2", "hell", "ait", "l2n", "l2_mond", "ait_mond"]
for ax, d in zip(axs, DGPN):
    for m in meths:
        s = A[(A.dgp == d) & (A.K == 5) & (A.n_cal == 200) & (A.method == m)].iloc[0]
        g = df[(df.dgp == d) & (df.K == 5) & (df.n_cal == 200) & (df.method == m)]
        cov = [g[f"g_ent{j}_c"].sum() / g[f"g_ent{j}_n"].sum() for j in range(3)]
        ax.plot([0, 1, 2], cov, marker="o", ms=3, lw=0.9, label=PLAIN[m])
    ax.axhline(0.9, color="k", ls=":", lw=0.6); ax.set_title(DGPN[d])
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["low", "mid", "high"]); ax.set_xlabel("entropy of $f(x)$")
axs[0].set_ylabel("coverage")
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=6, frameon=False)
plt.tight_layout(rect=[0, 0.1, 1, 1]); plt.savefig("figures/fig_cond_entropy.pdf"); plt.close()

# ------------------------------------------------------------------ n_cal dependence of size & sd of coverage
fig, axs = plt.subplots(1, 2, figsize=(3.3, 1.9))
for m in ["l2", "hell", "ait"]:
    for d, ls in [("ln", "-"), ("dir", "--")]:
        s = A[(A.dgp == d) & (A.K == 5) & (A.method == m)].sort_values("n_cal")
        axs[0].plot(s.n_cal, s.size_pool, ls, marker="o", ms=2, label=f"{PLAIN[m]}/{d}")
axs[0].set_xscale("log"); axs[0].set_xlabel("$n_{cal}$"); axs[0].set_ylabel("pool size ($K$=5)")
sd = df[(df.method == "l2") & (df.K == 5)].groupby(["dgp", "n_cal"])["cov"].std().reset_index()
for d in DGPN:
    s = sd[sd.dgp == d]; axs[1].plot(s.n_cal, s["cov"], marker="o", ms=2, label=DGPN[d])
nn = np.array([50, 200, 1000]); axs[1].plot(nn, np.sqrt(0.09 / (nn + 2) + 0.09 / 1000), "k:", label="theory")
axs[1].set_xscale("log"); axs[1].set_xlabel("$n_{cal}$"); axs[1].set_ylabel("sd of test coverage")
axs[1].legend(frameon=False, fontsize=5)
plt.tight_layout(); plt.savefig("figures/fig_ncal.pdf"); plt.close()

json.dump(SUMMARY, open("results/summary_synth_misc.json", "w"), indent=1)
print(json.dumps(SUMMARY, indent=1))
