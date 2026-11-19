"""Analysis of synthetic experiments -> figs/*.pdf, tables/*.tex, results/summary_synth.json
usage: python code/analyze_synth.py"""
import json, itertools
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats
from scipy.stats import beta as Beta, wilcoxon, binom
import os
os.makedirs("tables", exist_ok=True); os.makedirs("figs", exist_ok=True)

SUM = {}
plt.rcParams.update({"font.size": 8, "axes.titlesize": 9, "legend.fontsize": 6.5})
SC_ORDER = ["L2", "L1", "Linf", "Hellinger", "KL", "Aitchison", "Mahal-clr", "DirNLL",
            "L2/sqrtGini", "L2/learned-sigma", "L2-Mondrian(argmax)", "L2-Mondrian(gini)"]
SC_TEX = {s: s.replace("_", r"\_").replace("/", "/").replace("sqrtGini", r"$\sqrt{\mathrm{Gini}}$") for s in SC_ORDER}
DG_ORDER = ["dir_homo", "dir_het", "dir_sparse", "dir_nl", "lnorm_het", "mult50"]
DG_TEX = {d: d.replace("_", r"\_") for d in DG_ORDER}
ci = lambda x: 1.96 * np.std(x, ddof=1) / np.sqrt(len(x))

def expected_cov(n, a):  # E[coverage] of split conformal for continuous scores
    return np.ceil((n + 1) * (1 - a)) / (n + 1)

def beta_params(n, a):
    l = np.floor((n + 1) * a)
    return n + 1 - l, l

# --------------------------------------------------------------------------- coverage law
cl = pd.read_csv("results/covlaw.csv")
rows = []
for (dg, n, sc), g in cl.groupby(["dgp", "n_cal", "score"]):
    A, B = beta_params(n, 0.1)
    mean_th, var_th = A / (A + B), A * B / ((A + B) ** 2 * (A + B + 1))
    sd_th_with_test = np.sqrt(var_th + 0.9 * 0.1 / 20000)  # test-set noise in our estimate of coverage
    ks = stats.kstest(g["cov"].values, lambda x: Beta.cdf(x, A, B)).pvalue
    z = (g["cov"].mean() - mean_th) / (g["cov"].std(ddof=1) / np.sqrt(len(g)))
    rows.append(dict(dgp=dg, n_cal=n, score=sc, R=len(g), mean=g["cov"].mean(), sd=g["cov"].std(ddof=1),
                     mean_th=mean_th, sd_th=np.sqrt(var_th), sd_th_obs=sd_th_with_test, z_mean=z, ks_p=ks))
law = pd.DataFrame(rows); law.to_csv("results/coverage_law_summary.csv", index=False)
plain = law[~law.score.str.contains("Mondrian")]
SUM["law_plain_n"] = int(len(plain))
SUM["law_plain_ks_p_lt_0.05_frac"] = float((plain.ks_p < 0.05).mean())
SUM["law_plain_ks_p_lt_0.01_frac"] = float((plain.ks_p < 0.01).mean())
SUM["law_plain_abs_z_gt_3_frac"] = float((plain.z_mean.abs() > 3).mean())
SUM["law_plain_max_abs_meandev"] = float((plain["mean"] - plain.mean_th).abs().max())
SUM["law_plain_sd_ratio_range"] = [float((plain.sd / plain.sd_th_obs).min()), float((plain.sd / plain.sd_th_obs).max())]
mo = law[law.score.str.contains("Mondrian")]
SUM["law_mondrian_mean_minus_th"] = {f"{r.score}|{r.dgp}|{r.n_cal}": float(r["mean"] - r.mean_th) for _, r in mo.iterrows()}

# figure: coverage histograms vs Beta
fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.1), sharey=False)
for ax, n in zip(axs, [50, 200, 1000]):
    g = cl[(cl.dgp == "dir_het") & (cl.n_cal == n) & (cl.score == "L2")]["cov"]
    A, B = beta_params(n, 0.1)
    ax.hist(g, bins=30, density=True, color="tab:blue", alpha=0.55, label="empirical (L2, dir_het)")
    xs = np.linspace(g.min() - .02, g.max() + .02, 400)
    ax.plot(xs, Beta.pdf(xs, A, B), "k-", lw=1.2, label=f"Beta({A:.0f},{B:.0f})")
    ax.axvline(0.9, color="r", ls=":", lw=1)
    ax.set_title(f"$n_{{cal}}={n}$"); ax.set_xlabel("realised test coverage")
    if n == 50: ax.legend()
plt.tight_layout(); plt.savefig("figs/fig_covlaw.pdf", bbox_inches="tight"); plt.close()

# ---- naive vs resampling-based evaluation protocol
rng = np.random.default_rng(0)
rows = []
for n in [50, 200, 1000]:
    for T in [500, 2000, 10000]:
        rej, rej_exp = [], []
        for (dg, sc), g in cl[(cl.n_cal == n) & (cl.score.isin(["L2", "KL", "Aitchison"]))].groupby(["dgp", "score"]):
            c = g["cov"].values
            k = rng.binomial(T, c)               # one test set of size T per calibration draw
            ph = k / T; se = np.sqrt(ph * (1 - ph) / T)
            lo, hi = ph - 1.96 * se, ph + 1.96 * se
            rej.append(np.mean((lo > 0.9) | (hi < 0.9)))                      # CI excludes nominal 0.9
            e = expected_cov(n, 0.1)
            rej_exp.append(np.mean((lo > e) | (hi < e)))                       # CI excludes exact expected coverage
        pred = 2 * (1 - stats.norm.cdf(1.96 / np.sqrt(1 + T / (n + 2))))   # Prop. 4 closed form
        rows.append(dict(n_cal=n, T=T, naive_excl_nominal=np.mean(rej), naive_excl_expected=np.mean(rej_exp), predicted=pred))
nv = pd.DataFrame(rows)
# resampling protocol: groups of Rg calibration draws, mean +- t-CI over draws
rows2 = []
for n in [50, 200, 1000]:
    for Rg in [10, 30]:
        rej = []
        for (dg, sc), g in cl[(cl.n_cal == n) & (cl.score.isin(["L2", "KL", "Aitchison"]))].groupby(["dgp", "score"]):
            c = g["cov"].values; m = len(c) // Rg
            for j in range(m):
                x = c[j * Rg:(j + 1) * Rg]
                h = stats.t.ppf(0.975, Rg - 1) * x.std(ddof=1) / np.sqrt(Rg)
                e = expected_cov(n, 0.1)
                rej.append((x.mean() - h > e) or (x.mean() + h < e))
        rows2.append(dict(n_cal=n, R=Rg, resample_excl_expected=np.mean(rej)))
rs = pd.DataFrame(rows2)
nv.to_csv("results/naive_protocol.csv", index=False); rs.to_csv("results/resample_protocol.csv", index=False)
SUM["naive"] = nv.round(3).to_dict("records"); SUM["resample"] = rs.round(3).to_dict("records")
fig, ax = plt.subplots(1, 1, figsize=(3.3, 2.2))
for T, ls in zip([500, 2000, 10000], ["-", "--", ":"]):
    s = nv[nv["T"] == T]
    ax.plot(s.n_cal, s.naive_excl_expected, "o" + ls, color="tab:red", label=f"single split, $T$={T}", ms=3)
for Rg, col in zip([10, 30], ["tab:green", "tab:olive"]):
    s = rs[rs.R == Rg]; ax.plot(s.n_cal, s.resample_excl_expected, "s-", color=col, ms=3, label=f"resampling, $R$={Rg}")
ax.axhline(0.05, color="k", lw=0.8, ls="-."); ax.set_xscale("log"); ax.set_xlabel("$n_{cal}$")
ax.set_ylabel("P(95% CI excludes\nthe exact expected coverage)"); ax.legend(); plt.tight_layout()
plt.savefig("figs/fig_protocol.pdf", bbox_inches="tight"); plt.close()

# ---------------------------------------------------------------------------- main benchmark
M = pd.read_csv("results/main.csv")
M10 = M[(M.alpha == 0.1) & (M.n_cal == 500)]
MET = ["cov", "xc", "vf0.1", "vf0.3", "vf1", "vf3", "gapG_max", "gapG_mean", "minG", "gapC_max", "minC"]
tab = {}
for m in MET:
    mu = M10.groupby(["dgp", "score"])[m].mean().unstack(0)
    c = M10.groupby(["dgp", "score"])[m].apply(ci).unstack(0)
    tab[m] = (mu.loc[SC_ORDER, DG_ORDER], c.loc[SC_ORDER, DG_ORDER])
pd.concat({m: tab[m][0] for m in MET}).to_csv("results/main_means.csv")
pd.concat({m: tab[m][1] for m in MET}).to_csv("results/main_ci.csv")

def latex_table(m, fname, fmt="{:.3f}", lower_better=True, caption_cols=DG_ORDER, ci_digits=3, bold=True, show_ci=True):
    mu, c = tab[m]
    lines = [r"\begin{tabular}{l" + "r" * len(caption_cols) + "}", r"\toprule",
             "score & " + " & ".join(DG_TEX[d] for d in caption_cols) + r" \\", r"\midrule"]
    best = mu.idxmin() if lower_better else mu.idxmax()
    for s in SC_ORDER:
        cells = []
        for d in caption_cols:
            t = f"{mu.loc[s, d]:.{ci_digits}f}"
            if bold and best[d] == s: t = r"\mathbf{" + t + "}"
            if show_ci:
                cells.append("$" + t + r"{\scriptstyle\pm" + f"{c.loc[s, d]:.{ci_digits}f}" + "}$")
            else:
                cells.append("$" + t + "$")
        lines.append(SC_TEX[s] + " & " + " & ".join(cells) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}"]
    open(f"tables/{fname}.tex", "w").write("\n".join(lines))

for m, lb in [("xc", True), ("vf0.1", True), ("vf0.3", True), ("vf1", True), ("vf3", True),
              ("gapG_max", True), ("minG", False), ("gapC_max", True), ("cov", False)]:
    latex_table(m, f"main_{m.replace('.', '')}", lower_better=lb, bold=(m != "cov"))
    latex_table(m, f"main_{m.replace('.', '')}_nc", lower_better=lb, bold=(m != "cov"), show_ci=False)
SUM["max_ci"] = {m: float(tab[m][1].values.max()) for m in MET}

# paired comparisons: best vs others (Wilcoxon, Holm) for xc, vf, gap
def paired_best(m, lower=True):
    out = {}
    for d in DG_ORDER:
        P = M10[M10.dgp == d].pivot(index="rep", columns="score", values=m)[SC_ORDER]
        best = P.mean().idxmin() if lower else P.mean().idxmax()
        ps = {}
        for s in SC_ORDER:
            if s != best:
                ps[s] = wilcoxon(P[best], P[s]).pvalue
        # Holm
        items = sorted(ps.items(), key=lambda kv: kv[1]); mm = len(items)
        holm = {}; run = 0
        for i, (s, p) in enumerate(items):
            run = max(run, min(1, p * (mm - i))); holm[s] = run
        out[d] = dict(best=best, indistinguishable=[s for s, p in holm.items() if p >= 0.05])
    return out
SUM["best_xc"] = paired_best("xc"); SUM["best_vf0.1"] = paired_best("vf0.1"); SUM["best_vf3"] = paired_best("vf3")
SUM["best_vf1"] = paired_best("vf1"); SUM["best_gapG"] = paired_best("gapG_max"); SUM["best_gapG_mean"] = paired_best("gapG_mean")

# rank-reversals across reference measures (paired Wilcoxon, Holm over all pairs within DGP/measure)
MEAS = ["xc", "vf0.1", "vf0.3", "vf1", "vf3"]
def sig_dir(d, m):
    P = M10[M10.dgp == d].pivot(index="rep", columns="score", values=m)[SC_ORDER]
    res = {}
    pairs = list(itertools.combinations(SC_ORDER, 2))
    ps = []
    for a, b in pairs:
        diff = P[a] - P[b]
        p = wilcoxon(P[a], P[b]).pvalue if (diff != 0).any() else 1.0
        ps.append(p)
    ps = np.array(ps); o = np.argsort(ps); holm = np.empty(len(ps)); run = 0
    for i, j in enumerate(o):
        run = max(run, min(1, ps[j] * (len(ps) - i))); holm[j] = run
    for (a, b), p in zip(pairs, holm):
        res[(a, b)] = 0 if p >= 0.05 else (1 if P[a].mean() < P[b].mean() else -1)
    return res
rev = {}
tot = 0; nrev = 0; rev_by_dgp = {}
for d in DG_ORDER:
    sd = {m: sig_dir(d, m) for m in MEAS}
    cnt = 0; both = 0
    for pair in sd["xc"]:
        for m1, m2 in itertools.combinations(MEAS, 2):
            a, b = sd[m1][pair], sd[m2][pair]
            if a != 0 and b != 0:
                both += 1
                if a != b: cnt += 1
    # pairs with an outright reversal between any two measures
    anyrev = sum(1 for pair in sd["xc"] if {sd[m][pair] for m in MEAS} >= {1, -1})
    rev_by_dgp[d] = dict(pairs=len(sd["xc"]), pairs_with_reversal_any_measures=int(anyrev))
SUM["rank_reversals"] = rev_by_dgp
# mean ranks heatmaps
fig, axs = plt.subplots(2, 3, figsize=(7.4, 5.0))
for ax, d in zip(axs.ravel(), DG_ORDER):
    R = np.array([[tab[m][0].loc[s, d] for m in MEAS] for s in SC_ORDER])
    rk = stats.rankdata(R, axis=0)
    ax.imshow(rk, cmap="viridis_r", aspect="auto", vmin=1, vmax=12)
    for i in range(len(SC_ORDER)):
        for j in range(len(MEAS)):
            ax.text(j, i, f"{int(rk[i, j])}", ha="center", va="center", color="w" if rk[i, j] < 7 else "k", fontsize=6.5)
    ax.set_xticks(range(len(MEAS))); ax.set_xticklabels(["XC", "V.1", "V.3", "V1", "V3"], fontsize=6.5)
    ax.set_yticks(range(len(SC_ORDER))); ax.set_yticklabels(SC_ORDER if d in ("dir_homo", "dir_nl") else [], fontsize=6.5)
    ax.set_title(d, fontsize=8)
plt.tight_layout(); plt.savefig("figs/fig_ranks.pdf", bbox_inches="tight"); plt.close()
SUM["rank_table"] = {d: {s: [int(x) for x in stats.rankdata(np.array([[tab[m][0].loc[s2, d] for m in MEAS] for s2 in SC_ORDER]), axis=0)[i]]
                          for i, s in enumerate(SC_ORDER)} for d in DG_ORDER}

# conditional coverage curves
fig, axs = plt.subplots(1, 4, figsize=(7.4, 2.1), sharey=True)
show = ["L2", "KL", "Aitchison", "L2/sqrtGini", "L2/learned-sigma", "L2-Mondrian(gini)"]
cols = dict(zip(show, ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]))
for ax, d in zip(axs, ["dir_homo", "dir_het", "lnorm_het", "mult50"]):
    g = M10[M10.dgp == d]
    for s in show:
        gg = g[g.score == s]
        mu = [gg[f"covG{i}"].mean() for i in range(5)]
        e = [ci(gg[f"covG{i}"]) for i in range(5)]
        ax.errorbar(np.arange(5), mu, yerr=e, marker="o", ms=2.5, lw=1, color=cols[s], label=s, capsize=1.5)
    ax.axhline(0.9, color="k", ls=":", lw=0.8); ax.set_title(d); ax.set_xlabel("Gini($\\hat h$) quintile")
axs[0].set_ylabel("coverage"); axs[0].legend(loc="lower left")
plt.tight_layout(); plt.savefig("figs/fig_cond.pdf", bbox_inches="tight"); plt.close()

# noise floor of gapG_max: simulate perfect-conditional-coverage protocol (n_cal=500, bins of 800)
rng = np.random.default_rng(1); A, B = beta_params(500, 0.1)
fl = []
for _ in range(4000):
    c = rng.beta(A, B); k = rng.binomial(800, c, 5) / 800
    fl.append(np.abs(k - 0.9).max())
SUM["gapG_noise_floor"] = float(np.mean(fl))
# alpha sensitivity
for a in [0.05, 0.2]:
    s = M[(M.alpha == a) & (M.n_cal == 500)]
    SUM[f"cov_alpha{a}_mean_by_score_minmax"] = [float(s.groupby("score")["cov"].mean().min()), float(s.groupby("score")["cov"].mean().max())]
s = M[(M.alpha == 0.1) & (M.n_cal == 100)]
SUM["n100_xc_mean"] = s.groupby(["dgp", "score"])["xc"].mean().unstack(0).round(3).to_dict()

# ------------------------------------------------------------------- n_cal sweep
N = pd.read_csv("results/ncal.csv")
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.1))
ns = sorted(N.n_cal.unique())
for sc, col in zip(["L2", "KL", "Aitchison", "L2/sqrtGini"], ["tab:blue", "tab:orange", "tab:green", "tab:red"]):
    s = N[(N.dgp == "dir_het") & (N.score == sc)]
    axs[0].plot(ns, [s[s.n_cal == n]["cov"].std() for n in ns], "o-", ms=3, color=col, label=sc)
axs[0].plot(ns, [np.sqrt(0.09 / (n + 2) + 0.09 / 4000) for n in ns], "k--", label=r"$\sqrt{\alpha(1-\alpha)/(n+2)}$+test")
axs[0].set_xscale("log"); axs[0].set_yscale("log"); axs[0].set_xlabel("$n_{cal}$"); axs[0].set_ylabel("SD of realised coverage"); axs[0].legend(fontsize=5.5)
for sc, col in zip(["L2", "KL", "Aitchison", "L2/sqrtGini", "L2-Mondrian(gini)"], ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:brown"]):
    s = N[(N.dgp == "dir_het") & (N.score == sc)]
    axs[1].plot(ns, [s[s.n_cal == n]["gapG_max"].mean() for n in ns], "o-", ms=3, color=col, label=sc)
    axs[2].plot(ns, [s[s.n_cal == n]["cov"].mean() for n in ns], "o-", ms=3, color=col, label=sc)
axs[1].legend(); axs[1].set_xscale("log"); axs[1].set_xlabel("$n_{cal}$"); axs[1].set_ylabel("worst Gini-bin gap"); axs[2].set_xscale("log")
axs[2].set_xlabel("$n_{cal}$"); axs[2].set_ylabel("mean coverage"); axs[2].axhline(0.9, color="k", ls=":")
plt.tight_layout(); plt.savefig("figs/fig_ncal.pdf", bbox_inches="tight"); plt.close()
SUM["ncal_mondrian_gini_cov"] = {int(n): float(N[(N.dgp == "dir_het") & (N.score == "L2-Mondrian(gini)") & (N.n_cal == n)]["cov"].mean()) for n in ns}
SUM["ncal_L2_cov_sd"] = {int(n): float(N[(N.dgp == "dir_het") & (N.score == "L2") & (N.n_cal == n)]["cov"].std()) for n in ns}
SUM["ncal_gapG"] = {sc: {int(n): float(N[(N.dgp == "dir_het") & (N.score == sc) & (N.n_cal == n)]["gapG_max"].mean()) for n in ns}
                    for sc in ["L2", "L2/sqrtGini", "L2-Mondrian(gini)"]}

# ------------------------------------------------------------------- covariate shift
S = pd.read_csv("results/shift.csv")
rows = []
for (sh, sc), g in S.groupby(["shift", "score"]):
    rows.append(dict(shift=sh, score=sc, cov=g["cov"].mean(), cov_ci=ci(g["cov"]), cov_w=g["cov_w"].mean() if g["cov_w"].notna().any() else np.nan,
                     cov_w_ci=ci(g["cov_w"].dropna()) if g["cov_w"].notna().sum() > 1 else np.nan,
                     cov_tail=g["cov_hi"].mean(), cov_w_tail=g["cov_w_hi"].mean()))
sh = pd.DataFrame(rows); sh.to_csv("results/shift_summary.csv", index=False)
fig, axs = plt.subplots(1, 2, figsize=(5.4, 2.1), sharey=True)
shs = sorted(S["shift"].unique())
for sc, col in zip(["L2", "KL", "Aitchison", "L2/sqrtGini", "L2/learned-sigma"], ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple"]):
    s = sh[sh.score == sc].set_index("shift").loc[shs]
    axs[0].plot(shs, s["cov"], "o-", ms=3, color=col, label=sc)
    axs[1].plot(shs, s["cov_w"].where(s.index != 0, s["cov"]), "o-", ms=3, color=col)
for ax, t in zip(axs, ["unweighted split conformal", "weighted (exact density ratio)"]):
    ax.axhline(0.9, color="k", ls=":"); ax.set_xlabel("shift of $x_0$ at test time"); ax.set_title(t)
axs[0].set_ylabel("test coverage"); axs[0].legend()
plt.tight_layout(); plt.savefig("figs/fig_shift.pdf", bbox_inches="tight"); plt.close()

# ------------------------------------------------------------------- multinomial N / delta
MN = pd.read_csv("results/mult_N.csv")
MN["N"] = MN.dgp.str.replace("multN", "").astype(int)
fig, axs = plt.subplots(1, 3, figsize=(7.4, 2.1))
for sc, col in zip(["L2", "L1", "Hellinger", "KL", "Aitchison", "L2/sqrtGini"], ["tab:blue", "tab:cyan", "tab:pink", "tab:orange", "tab:green", "tab:red"]):
    s = MN[MN.score == sc].groupby("N")
    axs[0].errorbar(s.size().index, s["xc"].mean(), yerr=s["xc"].apply(ci), marker="o", ms=3, color=col, label=sc, capsize=1.5)
    axs[1].errorbar(s.size().index, s["vf1"].mean(), yerr=s["vf1"].apply(ci), marker="o", ms=3, color=col, capsize=1.5)
for d, col in zip([1e-4, 1e-3, 1e-2, 1e-1], ["tab:gray", "tab:green", "tab:olive", "tab:brown"]):
    nm = "Aitchison" if d == 1e-3 else f"Aitchison(d={d:g})"
    s = MN[MN.score == nm].groupby("N")
    axs[2].errorbar(s.size().index, s["xc"].mean(), yerr=s["xc"].apply(ci), marker="o", ms=3, color=col, label=f"$\\delta$={d:g}", capsize=1.5)
for ax in axs: ax.set_xscale("log"); ax.set_xlabel("counts per composition $N$")
axs[0].set_yscale("log"); axs[1].set_yscale("log"); axs[2].set_yscale("log")
axs[0].set_ylabel("cross-coverage (XC)"); axs[1].set_ylabel("volume fraction, uniform ref."); axs[2].set_ylabel("XC, Aitchison")
axs[0].legend(); axs[2].legend()
plt.tight_layout(); plt.savefig("figs/fig_multN.pdf", bbox_inches="tight"); plt.close()
SUM["multN_xc"] = MN.groupby(["score", "N"])["xc"].mean().unstack().round(4).to_dict()
SUM["multN_cov"] = MN.groupby(["score", "N"])["cov"].mean().unstack().round(4).to_dict()
SUM["multN_gapG"] = MN.groupby(["score", "N"])["gapG_max"].mean().unstack().round(4).to_dict()
json.dump(SUM, open("results/summary_synth.json", "w"), indent=1, default=str)
print("ok")
