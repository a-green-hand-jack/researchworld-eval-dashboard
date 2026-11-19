"""Analysis of synthetic + theory results -> tables (results/tables/*.csv, *.tex) and figures (figs/*.pdf).
Usage: python code/analyze_synth.py
"""
import numpy as np, pandas as pd, os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

os.makedirs("results/tables", exist_ok=True); os.makedirs("figs", exist_ok=True)
plt.rcParams.update({"font.size": 8, "axes.titlesize": 8, "figure.dpi": 150})
d = pd.read_csv("results/synth_raw.csv")
ALPHA = 0.1
LAB = {"l2": r"$\ell_2$", "l1": "TV", "linf": r"$\ell_\infty$", "hell": "Hellinger", "aitch": "Aitchison", "kl": "KL"}
SC = ["l2", "l1", "linf", "hell", "aitch", "kl"]
MET = ["plain", "norm", "mond"]
tex = lambda df, name, **kw: open(f"results/tables/{name}.tex", "w").write(df.to_latex(escape=False, **kw))


def agg(df, col, by):
    """mean over scenarios (equal weight) of per-scenario rep-means; SE from within-scenario rep variance."""
    g = df.groupby(["sid"] + by)[col].agg(["mean", "var", "count"]).reset_index()
    out = g.groupby(by).apply(lambda t: pd.Series({"mean": t["mean"].mean(),
                              "se": np.sqrt((t["var"] / t["count"]).sum()) / len(t), "nscen": len(t)}), include_groups=False)
    return out


def summ(df, col):
    """Grand mean over scenarios of rep-means, with SE clustered at (scenario, rep): scores sharing a draw are averaged first."""
    r = df.groupby(["sid", "rep"])[col].mean()          # average over scores/methods rows sharing the same data draw
    g = r.groupby("sid").agg(["mean", "var", "count"])
    return g["mean"].mean(), np.sqrt((g["var"] / g["count"]).sum()) / len(g)


# ---------- Table 1: theory vs Beta
t = pd.read_csv("results/theory.csv")
T1 = pd.DataFrame({"score": t.score.map(LAB), "n": t.n,
                   "mean": [f"{a:.4f} ({b:.4f})" for a, b in zip(t.emp_mean, t.emp_mean_se)], "Beta mean": t.beta_mean.round(4),
                   "SD": t.emp_sd.round(4), "Beta SD": t.beta_sd.round(4),
                   "P(C<.9)": t.p_below_90.round(3), "Beta": t.beta_p_below_90.round(3), "KS p": t.ks_p.round(2)})
T1.to_csv("results/tables/theory.csv", index=False); tex(T1, "theory", index=False)
print("KS p-values: min", t.ks_p.min(), " Holm-adj min", min(1, t.ks_p.min() * len(t)))

# ---------- Null for worst-slice coverage (perfect conditional validity, finite-sample noise only)
rng = np.random.default_rng(0)
def null_wsc(ncal_eff, nev=1000, nb=5, reps=20000):
    l = int(np.floor((ncal_eff + 1) * ALPHA))
    C = rng.beta(ncal_eff + 1 - l, l, (reps, nb)) if ncal_eff < 0 else None
    return None
def null_stats(n_cal_slice, nev=1000, nb=5, reps=20000, shared=True):
    l = int(np.floor((n_cal_slice + 1) * ALPHA))
    C = rng.beta(n_cal_slice + 1 - l, l, (reps, 1 if shared else nb))
    cov = rng.binomial(nev // nb, np.broadcast_to(C, (reps, nb))) / (nev // nb)
    return cov.min(1).mean(), np.abs(cov - 0.9).max(1).mean()
NULL = {"global (n=500)": null_stats(500), "Mondrian (n_g=100/bin)": null_stats(100, shared=False)}
print("NULL wsc/maxdev", NULL)

# ---------- Table 2: marginal coverage
rows = []
for m in MET:
    s_ = d[d.method == m]
    per = s_.groupby(["sid", "score"])["cov"].mean()
    mu, se = summ(s_, "cov")
    rows.append(dict(method=m, mean_cov=mu, se=se, min_scen=per.min(), max_scen=per.max(),
                     sd_across_reps=s_.groupby(["sid", "score"])["cov"].std().mean(), frac_scen_below_089=(per < 0.89).mean()))
T2 = pd.DataFrame(rows).round(4); T2.to_csv("results/tables/marginal_coverage.csv", index=False)
print(T2.to_string())
# expected SD across reps: Beta(n_cal) calibration noise + binomial eval noise
l = 50; nc = 500; ne = 1000
bsd2 = (nc + 1 - l) * l / ((nc + 1) ** 2 * (nc + 2)); print("theory SD of realised coverage:", np.sqrt(bsd2 + 0.9 * 0.1 / ne))

# ---------- Table 3: set size (mass) by score, by K x kappa0 (plain), relative to smallest
p = d[d.method == "plain"]
g = p.groupby(["K", "kappa0", "score"])["mass"].mean().unstack().loc[:, SC]
T3 = g.copy(); T3.columns = [LAB[c] for c in SC]
T3.round(3).to_csv("results/tables/mass_by_score.csv")
rank = g.rank(axis=1)
print(g.round(3)); print("mean rank by score:", rank.mean().round(2).to_dict())
# paired difference in mass vs. best fixed score (per K, kappa0) with SE over reps
pv = p.pivot_table(index=["sid", "K", "kappa0", "hetero", "misspec", "rep"], columns="score", values="mass")
for ref in ["kl", "hell"]:
    for sc in SC:
        if sc == ref: continue
        diff = (pv[sc] - pv[ref]).groupby(level=["K", "kappa0"]).agg(["mean", "sem"])
        if ref == "kl" and sc in ("l2", "linf"): print("diff mass", sc, "-", ref); print(diff.round(3))

# ---------- Table 4: conditional coverage vs. method
rows = []
for (h, ms), s in d.groupby(["hetero", "misspec"]):
    for m in MET:
        sm = s[s.method == m]
        r = dict(hetero=h, misspec=ms, method=m)
        for col in ["wsc_conf", "wsc_x1", "maxdev_conf", "maxdev_x1"]:
            mu, se = summ(sm, col)
            r[col] = f"{mu:.3f} ({se:.4f})"
        rows.append(r)
T4 = pd.DataFrame(rows); T4.to_csv("results/tables/conditional_coverage.csv", index=False); print(T4.to_string())

# paired tests: method vs plain on maxdev_x1 / wsc_x1, per (hetero, misspec); Holm over all comparisons
pairs = []
w = d.pivot_table(index=["sid", "K", "kappa0", "hetero", "misspec", "rep"], columns=["method"], values=["wsc_x1", "maxdev_x1", "wsc_conf"])
w = w.groupby(level=[0, 1, 2, 3, 4, 5]).mean()
for (h, ms), s in w.groupby(level=["hetero", "misspec"]):
    for col in ["maxdev_x1", "wsc_x1"]:
        for m in ["norm", "mond"]:
            diff = (s[(col, m)] - s[(col, "plain")])
            # cluster by scenario: mean of scenario-level mean differences, t-test over reps pooled (reps independent given scenario)
            g_ = diff.groupby(level="sid").agg(["mean", "var", "count"])
            md = g_["mean"].mean(); se_ = np.sqrt((g_["var"] / g_["count"]).sum()) / len(g_)
            tt = stats.ttest_1samp(g_["mean"], 0)   # scenario-level t-test (n_scenarios = 6 per cell): conservative, ignores rep noise
            pairs.append(dict(hetero=h, misspec=ms, metric=col, method=m, mean_diff=md, se_rep=se_, n_scen=len(g_),
                              n_scen_pos=int((g_["mean"] > 0).sum()), p_scen=tt.pvalue))
P = pd.DataFrame(pairs)
P['p'] = P.p_scen
order = P.p.sort_values().index; m_ = len(P)
holm = np.minimum(1, np.maximum.accumulate((m_ - np.arange(m_)) * P.p[order].values))
P.loc[order, "p_holm"] = holm
P.round(5).to_csv("results/tables/paired_tests_conditional.csv", index=False); print(P.round(4).to_string())

# ---------- Figures
# Fig: coverage per scenario (plain), by score
fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.4))
sc_cov = d[d.method == "plain"].groupby(["sid", "score"])["cov"].agg(["mean", "sem"]).reset_index()
for i, s_ in enumerate(SC):
    q = sc_cov[sc_cov.score == s_]
    ax[0].errorbar(q.sid + (i - 2.5) * 0.12, q["mean"], 1.96 * q["sem"], fmt=".", ms=3, lw=.6, label=LAB[s_])
ax[0].axhline(0.9, c="k", lw=.5); ax[0].set_xlabel("scenario id (24 scenarios)"); ax[0].set_ylabel("marginal coverage (100 reps, 95% CI)")
ax[0].legend(ncol=3, fontsize=5.5, loc="lower right"); ax[0].set_ylim(0.87, 0.93)
# empirical realised-coverage distribution vs Beta, theory
tt_ = pd.read_csv("results/theory.csv")
x_ = np.linspace(0, 1, 2)
ax[1].errorbar(tt_[tt_.score == "kl"].beta_sd, tt_[tt_.score == "kl"].emp_sd, fmt="o", ms=3, label="KL")
for s_, mk in [("l2", "s"), ("aitch", "^")]:
    q = tt_[tt_.score == s_]; ax[1].plot(q.beta_sd, q.emp_sd, mk, ms=3, label=LAB[s_])
ax[1].plot([0.005, 0.07], [0.005, 0.07], "k-", lw=.5); ax[1].set_xscale("log"); ax[1].set_yscale("log")
ax[1].set_xlabel("Beta-law SD of conditional coverage"); ax[1].set_ylabel("empirical SD (3000 cal. draws)"); ax[1].legend(fontsize=6)
plt.tight_layout(); plt.savefig("figs/synth_coverage_theory.pdf"); plt.savefig("scratch/synth_coverage_theory.png", dpi=110); plt.close()

# Fig: mass vs kappa0 for each score, K=3 / 10
fig, ax = plt.subplots(1, 2, figsize=(6.8, 2.4), sharey=False)
for j, K in enumerate([3, 10]):
    for s_ in SC:
        q = p[(p.K == K) & (p.score == s_)].groupby(["kappa0", "sid"])["mass"].mean().groupby("kappa0").mean()
        ax[j].plot(q.index, q.values, "o-", ms=3, label=LAB[s_])
    ax[j].set_xscale("log"); ax[j].set_title(f"K={K}"); ax[j].set_xlabel(r"concentration $\kappa_0$"); ax[j].set_ylabel("fraction of reference targets in set")
ax[0].legend(fontsize=6); plt.tight_layout(); plt.savefig("figs/synth_mass.pdf"); plt.savefig("scratch/synth_mass.png", dpi=110); plt.close()

# Fig: x1-slice conditional coverage by method in the 4 (hetero, misspec) cells
fig, ax = plt.subplots(1, 1, figsize=(3.4, 2.5))
cells = [(0, 0), (0, 1), (1, 0), (1, 1)]
for k, m in enumerate(MET):
    mus, ses = [], []
    for h, ms in cells:
        s = d[(d.method == m) & (d.hetero == h) & (d.misspec == ms)].groupby(["sid", "score"])["wsc_x1"]
        mus.append(s.mean().mean()); ses.append(np.sqrt((s.var() / s.count()).sum()) / len(s.mean()))
    ax.errorbar(np.arange(4) + (k - 1) * .15, mus, 1.96 * np.array(ses), fmt="o", ms=3, label=m, capsize=1.5)
ax.axhline(NULL["global (n=500)"][0], c="gray", ls="--", lw=.6); ax.text(3.3, NULL["global (n=500)"][0] + .004, "null", fontsize=6, ha="right")
ax.set_xticks(range(4)); ax.set_xticklabels(["homosk.\nwell-spec.", "homosk.\nmisspec.", "heterosk.\nwell-spec.", "heterosk.\nmisspec."], fontsize=6)
ax.set_ylabel("worst $x_1$-slice coverage"); ax.legend(fontsize=6); plt.tight_layout(); plt.savefig("figs/synth_conditional.pdf"); plt.savefig("scratch/synth_conditional.png", dpi=110); plt.close()
print("ok")

# ---------- Table 5: ranking of scores depends on the reference measure (K=3 only): data-law mass vs uniform-simplex volume
p3 = d[(d.method == "plain") & (d.K == 3)]
rows = []
for kap in [3, 30, 300]:
    for sc in SC:
        q = p3[(p3.kappa0 == kap) & (p3.score == sc)]
        rows.append(dict(kappa0=kap, score=sc, mass=q.groupby("sid")["mass"].mean().mean(), vol=q.groupby("sid")["vol"].mean().mean()))
T5 = pd.DataFrame(rows)
T5["rank_mass"] = T5.groupby("kappa0")["mass"].rank(); T5["rank_vol"] = T5.groupby("kappa0")["vol"].rank()
T5.round(3).to_csv("results/tables/mass_vs_volume_K3.csv", index=False); print(T5.round(3).to_string())
for kap in [3, 30, 300]:
    z = T5[T5.kappa0 == kap]; print("kappa0", kap, "Spearman(mass,vol)=", round(stats.spearmanr(z["mass"], z["vol"])[0], 2))
# pairwise (paired over data draws) test aitch vs kl in mass and vol, K=3
pv3 = p3.pivot_table(index=["sid", "rep"], columns="score", values=["mass", "vol"])
for met in ["mass", "vol"]:
    dd = pv3[(met, "aitch")] - pv3[(met, "kl")]; print(met, "aitch-kl K=3 mean diff", round(dd.mean(), 4), "SE", round(dd.sem(), 4))

# ---------- Extra paired contrasts of mass (plain method) for text: aitch-kl, hell-kl, l1-kl by (K, kappa0)
rows = []
for a_ in ["aitch", "hell", "l1", "l2", "linf"]:
    dd = (pv[a_] - pv["kl"]).groupby(level=["K", "kappa0"]).agg(["mean", "sem"])
    for (K_, k_), r_ in dd.iterrows():
        rows.append(dict(score=a_, vs="kl", K=K_, kappa0=k_, mean_diff=r_["mean"], sem=r_["sem"]))
pd.DataFrame(rows).round(4).to_csv("results/tables/mass_paired_vs_kl.csv", index=False)

pd.DataFrame([dict(setting=k, mean_worst_slice=v[0], mean_max_abs_dev=v[1]) for k, v in NULL.items()]).round(4).to_csv("results/tables/null_slice_reference.csv", index=False)
