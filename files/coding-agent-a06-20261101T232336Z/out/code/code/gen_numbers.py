"""Write paper/numbers.tex: every number quoted in the text/abstract that is computed from results files."""
import sys; sys.path.insert(0, "/work/code")
import numpy as np, pandas as pd, os
from summ import summarize
from fig_methods import prep
from realdata import load_Y
R = {}
NW = {50: "Fifty", 100: "Hund", 200: "TwoH", 400: "FourH", 800: "EightH"}
def put(k, v, fmt="{:.1f}"):
    for n, w in NW.items(): k = k.replace(f"N{n}", f"N{w}")
    R[k] = fmt.format(v)
Y = load_Y("/work/cache/q15"); N, K = Y.shape
p = Y.mean(0); Sig = np.cov(Y.T, ddof=1) / N; P = np.eye(K) - 1 / K
s2 = np.trace(P @ Sig @ P) / (K - 1); v = p.var(ddof=1)
put("RealN", N, "{:d}"); put("RealAcc", 100 * Y.mean()); put("RealMin", 100 * p.min()); put("RealMax", 100 * p.max()); put("RealSD", 100 * p.std(ddof=1))
put("RealTau", 100 * np.sqrt(max(v - s2, 0))); put("RealNoise", 100 * np.sqrt(s2)); put("RealCorr", np.corrcoef(Y.T)[np.triu_indices(K, 1)].mean(), "{:.2f}")
d = pd.read_parquet("/work/results/real_main.parquet"); m = prep(d[d.method_set == "main"])
s = summarize(m, ["alg", "n", "method"]).set_index(["alg", "n", "method"])
for a, tag in (("rs72", "RS"), ("rs8", "RSeight"), ("sh72", "SH"), ("ca", "CA"), ("mipro40", "MIPRO")):
    for n in (50, 100, 200, 400, 800):
        for meth, mt in (("naive", "Naive"), ("boot_opt", "Boot"), ("holdout", "Hold"), ("crossfit", "Cross")):
            r = s.loc[(a, n, meth)]
            put(f"{mt}{tag}N{n}", 100 * r.bias, "{:+.1f}"); put(f"Rmse{mt}{tag}N{n}", 100 * r.rmse); put(f"Cov{mt}{tag}N{n}", 100 * r.cover, "{:.0f}")
# gains
sw = pd.read_parquet("/work/results/real_sweep_naive.parquet")
x = sw[sw.method.isin(["naive", "mean_cfg"])].pivot_table(index=["n", "kw_B", "rep"], columns="method", values=["est", "truth"]).reset_index()
x.columns = ["_".join([c for c in col if c]) for col in x.columns]
x["rg"] = x.est_naive - x.est_mean_cfg; x["tg"] = x.truth_naive - x.truth_mean_cfg
for n in (50, 100, 200, 400, 800):
    h = x[(x.n == n) & (x.kw_B == 72)]; put(f"RepGainN{n}", 100 * h.rg.mean()); put(f"TrueGainN{n}", 100 * h.tg.mean())
    put(f"FracOptN{n}", 100 * (1 - h.tg.mean() / h.rg.mean()), "{:.0f}")
# conclusions (real)
c = pd.read_parquet("/work/results/conclusions_real.parquet"); c["claim"] = c.gap / c.se > 1.645; c["fc1"] = c.claim & (c.true_gap < 0.01)
c["B"] = c.algoB.fillna("None").replace("None", "default")
for B, tag in (("default", "Def"), ("rs", "Four")):
    for n in (100, 400):
        h = c[(c.algoA == "rs") & (c.B == B) & (c.n == n)]
        put(f"TrueGap{tag}N{n}", 100 * h[h.method == "naive"].true_gap.mean()); put(f"NaiveGap{tag}N{n}", 100 * h[h.method == "naive"].gap.mean())
        for meth, mt in (("naive", "Naive"), ("boot_opt", "Boot"), ("holdout", "Hold")):
            q = h[h.method == meth]; put(f"Claim{mt}{tag}N{n}", 100 * q.claim.mean(), "{:.0f}"); put(f"FalseClaim{mt}{tag}N{n}", 100 * q.fc1.mean(), "{:.0f}")

# ranges over real main cells
ss = s.reset_index()
def rng(meth, col, f=100):
    v = ss[ss.method == meth][col] * f; return v.min(), v.max()
for meth, mt in (("holdout", "Hold"), ("crossfit", "Cross"), ("boot_opt", "Boot"), ("naive", "Naive")):
    lo, hi = rng(meth, "cover"); put(f"{mt}CovMin", lo, "{:.0f}"); put(f"{mt}CovMax", hi, "{:.0f}")
    lo, hi = rng(meth, "bias"); put(f"{mt}BiasMin", lo, "{:+.1f}"); put(f"{mt}BiasMax", hi, "{:+.1f}")
bb = ss[ss.method == "holdout"].bias.abs().max() * 100; put("HoldBiasAbsMax", bb)
# extras on real (RS B=72)
e = pd.read_parquet("/work/results/real_extras.parquet"); se = summarize(e, ["kw_B", "n", "method"]).set_index(["kw_B", "n", "method"])
for meth, mt in (("eb", "EB"), ("worstcase", "Worst"), ("naive", "N"), ("cond", "Cond"), ("simult", "Simult"), ("ladder", "Ladder"), ("thresholdout_lo", "Tho")):
    r = se.loc[(72, 100, meth)]
    put(f"{mt}Bias", 100 * r.bias, "{:+.1f}"); put(f"{mt}Rmse", 100 * r.rmse); put(f"{mt}Cov", 100 * r.cover, "{:.0f}"); put(f"{mt}Width", 100 * r.width)
cw = se.loc[(72, 100, "cond")].width / se.loc[(72, 100, "naive")].width; put("CondWidthRatio", cw, "{:.1f}")
ew = se.loc[(72, 100, "eb")].width / se.loc[(72, 100, "naive")].width; put("EBWidthRatio", ew, "{:.2f}")
# robustness (synthetic)
rb = pd.read_parquet("/work/results/synth_robust.parquet"); rs_ = summarize(rb[(rb.w_K == 72) & (rb.w_tau == 0.05) & (rb.n == 100)], ["w_dist", "method"]).set_index(["w_dist", "method"])
for dist in ("normal", "sparse", "heavy", "bimodal"):
    for meth, mt in (("eb", "EB"), ("worstcase", "Worst"), ("boot_opt", "Boot"), ("holdout", "Hold"), ("naive", "Naive"), ("simult", "Simult"), ("cond", "Cond")):
        r = rs_.loc[(dist, meth)]; put(f"Rob{dist.capitalize()}{mt}Bias", 100 * r.bias, "{:+.1f}"); put(f"Rob{dist.capitalize()}{mt}Cov", 100 * r.cover, "{:.0f}")
# conclusions synthetic tau=0.1
cs = pd.read_parquet("/work/results/conclusions_synth.parquet"); cs["claim"] = cs.gap / cs.se > 1.645; cs["B"] = cs.algoB.fillna("None").replace("None", "default")
for tau, tg in ((0.0, "Z"), (0.1, "T")):
    h = cs[(cs.w_tau == tau) & (cs.algoA == "rs") & (cs.B == "default") & (cs.n == 100)]
    put(f"SynTrueGap{tg}", 100 * h[h.method == "naive"].true_gap.mean())
    for meth, mt in (("naive", "Naive"), ("boot_opt", "Boot"), ("holdout", "Hold")):
        q = h[h.method == meth]; put(f"SynClaim{tg}{mt}", 100 * q.claim.mean(), "{:.0f}")
# fraction of optimism removed by replay bootstrap (real)
nv = ss[ss.method == "naive"].set_index(["alg", "n"]).bias; bt = ss[ss.method == "boot_opt"].set_index(["alg", "n"]).bias
fr = (1 - bt / nv); put("BootRemovedMin", 100 * fr.min(), "{:.0f}"); put("BootRemovedMax", 100 * fr.max(), "{:.0f}"); put("BootRemovedMed", 100 * fr.median(), "{:.0f}")
# finite-pool (fresh items) variant
fr_ = pd.read_parquet("/work/results/real_main_fresh.parquet"); fr_ = prep(fr_[fr_.method.isin(["naive", "boot_opt", "holdout"])])
sf = summarize(fr_, ["alg", "n", "method"]).set_index(["alg", "n", "method"])
for n in (50, 100, 200):
    put(f"FreshNaiveRSN{n}", 100 * sf.loc[("rs72", n, "naive")].bias, "{:+.1f}"); put(f"FreshBootRSN{n}", 100 * sf.loc[("rs72", n, "boot_opt")].bias, "{:+.1f}")
    put(f"FreshHoldRSN{n}", 100 * sf.loc[("rs72", n, "holdout")].bias, "{:+.1f}"); put(f"PoolFactorN{n}", N / (N - n), "{:.2f}")
# matched simulation vs real
sm = pd.read_parquet("/work/results/synth_matched.parquet"); sm = prep(sm[sm.method_set == "main"])
a1 = summarize(sm[sm.method == "naive"], ["alg", "n"]).set_index(["alg", "n"]).bias; a2 = ss[ss.method == "naive"].set_index(["alg", "n"]).bias
put("MatchedR", np.corrcoef(a1.sort_index(), a2.sort_index())[0, 1], "{:.2f}"); put("MatchedMAE", 100 * np.abs(a1.sort_index() - a2.sort_index()).mean())
# hold-out frontier
fo = pd.read_parquet("/work/results/frontier.parquet"); fo["alg"] = fo.algo + fo.kw_B.fillna(0).astype(int).astype(str); fo["err"] = fo.est - fo.truth
for rh, tg in ((0.1, "Ten"), (0.3, "Thirty"), (0.5, "Fifty")):
    for n in (100, 400):
        h = fo[(fo.w_kind == "real") & (fo.alg == "rs72") & (fo.n == n) & (fo.rho_hold == rh)]
        hh = h[h.method == "holdout"]; nn = h[h.method == "naive"]
        put(f"FrRmse{tg}N{n}", 100 * np.sqrt((hh.err ** 2).mean())); put(f"FrLoss{tg}N{n}", 100 * (nn.truth.mean() - hh.truth.mean()), "{:.2f}")
for rh, tg in ((0.1, "Ten"), (0.3, "Thirty"), (0.5, "Fifty")):
    h = fo[(fo.w_kind == "synth") & (fo.alg == "rs72") & (fo.n == 100) & (fo.rho_hold == rh)]
    put(f"FrSynLoss{tg}NHund", 100 * (h[h.method == "naive"].truth.mean() - h[h.method == "holdout"].truth.mean()), "{:.2f}")
h = fo[(fo.w_kind == "real") & (fo.alg == "rs72") & (fo.n == 100)]; put("FrRmseNaiveNHund", 100 * np.sqrt((h[h.method == "naive"].err ** 2).mean()))
# real-pool check of eq. (1): optimism / E[Z_(B)] is constant in B and equals sigma^2/sqrt(tau^2+sigma^2)
rg = np.random.default_rng(5); EZ = {B: rg.standard_normal((200000, B)).max(1).mean() for B in (2, 4, 8, 16, 32, 72)}
swn = sw[sw.method == "naive"].copy(); swn["opt"] = swn.est - swn.truth
res = Y.astype(float) - Y.mean(1, keepdims=True); vspec = float(res.var(0).mean()) * K / (K - 1)
tau2 = max(v - s2, 0.0)
for n in (50, 100, 200, 400, 800):
    g = swn[swn.n == n].groupby("kw_B").opt.mean()
    cs_ = [g[B] / EZ[B] for B in EZ]; put(f"CObsN{n}", 100 * np.mean(cs_)); put(f"CObsSdN{n}", 100 * np.std(cs_), "{:.2f}")
    sig2 = vspec / n; put(f"CPredN{n}", 100 * sig2 / np.sqrt(tau2 + sig2))
# Real-II (model x prompt pool)
from realdata import load_pool2
Y2 = load_pool2(); N2, K2 = Y2.shape; p2 = Y2.mean(0)
put("RTwoN", N2, "{:d}"); put("RTwoK", K2, "{:d}"); put("RTwoMin", 100 * p2.min()); put("RTwoMax", 100 * p2.max()); put("RTwoSD", 100 * p2.std())
r2 = pd.read_parquet("/work/results/real2_main.parquet"); r2["alg"] = r2.algo + r2.kw_B.astype(str); r2 = r2[r2.method_set == "main"]
s2_ = summarize(r2[r2.method.isin(["naive", "boot_opt", "holdout", "crossfit"])], ["alg", "n", "method"]).set_index(["alg", "n", "method"])
for n in (50, 100, 200):
    for meth, mt in (("naive", "Naive"), ("boot_opt", "Boot"), ("holdout", "Hold"), ("crossfit", "Cross")):
        r = s2_.loc[("rs32", n, meth)]; put(f"RTwo{mt}N{n}", 100 * r.bias, "{:+.1f}"); put(f"RTwoCov{mt}N{n}", 100 * r.cover, "{:.0f}"); put(f"RTwoRmse{mt}N{n}", 100 * r.rmse)
# theory
t = pd.read_csv("/work/results/theory.csv"); put("TheoryR", np.corrcoef(t.opt, t.pred)[0, 1], "{:.4f}"); put("TheoryCells", len(t), "{:d}")
put("TheoryMAE", 100 * np.abs(t.opt - t.pred).mean(), "{:.2f}")
# leak
z = np.load("/work/results/leak.npz"); put("LeakIn", 100 * z["a_in"].mean(), "{:.0f}"); put("LeakOut", 100 * z["a_out"].mean(), "{:.0f}")
put("LeakSets", len(z["a_in"]), "{:d}")
# permnull
pn = pd.read_parquet("/work/results/permnull.parquet"); pn["opt"] = pn.report - pn.truth; pn["alg"] = pn.algo + pn.B.astype(str)
g = pn.groupby(["alg", "n", "kind"]).opt.mean().unstack("kind"); rr = (g.perm / g.real)
put("PermRatioMin", rr.min(), "{:.2f}"); put("PermRatioMed", rr.median(), "{:.2f}"); put("PermRatioMax", rr.max(), "{:.2f}")
put("PermAcc", 100 * pn[pn.kind == "perm"].truth.mean(), "{:.0f}")
os.makedirs("/work/paper", exist_ok=True)
with open("/work/paper/numbers.tex", "w") as f:
    for k, v in R.items(): f.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(len(R), "macros")
