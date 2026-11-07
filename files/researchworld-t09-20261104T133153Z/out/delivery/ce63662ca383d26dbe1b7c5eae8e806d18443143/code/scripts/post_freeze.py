#!/usr/bin/env python3
"""Analyses of the post-freeze grids (run after the first freeze; the decision rules below were written before any e11-e13 cell was read):
  H3g  (e11) bias of the misspecified regression is proportional to the interference strength gamma
  H6c/d/e (e12) exposure-mapping (Hajek) baselines: unbiased under a correct mapping, biased under a wrong one, RMSE vs regression
  H5s/H2s/H4s (e13) second seed of the H5 (Stanford3/ego-FB cluster designs), H2 (closed form) and H4 (ER exponents) cells
Writes results/tables/t14_gamma_dependence.csv, t15_hajek.csv, t16_second_seed.csv and the rows appended to results/hypotheses.csv by findings.py."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os, numpy as np, pandas as pd
from netgate import graphs
import theory_bias as TB

R = results_dir(); S = lambda e: pd.read_csv(os.path.join(R, "summary", f"{e}.csv"))
T = lambda n: os.path.join(R, "tables", n)
H = []  # hypothesis rows


def hyp(h, test, stat, rule, verdict, cells, note=""):
    H.append(dict(hypothesis=h, test=test, statistic=stat, decision_rule=rule, verdict=verdict, cells=cells, note=note))


# ---------------- H3g (e11)
e11 = S("e11"); rows = []
for (g, kind, des, est), d in e11.groupby(["graph", "o_kind", "design", "est_name"]):
    d = d.sort_values("o_gamma"); x, b, se = d.o_gamma.values, d.bias.values, d.bias_se.values
    A = np.column_stack([np.ones(len(x)), x]); w = 1 / np.maximum(se, 1e-6) ** 2
    cov = np.linalg.inv(A.T @ (A * w[:, None])); beta = cov @ (A.T @ (w * b))
    res = b - A @ beta; r2 = 1 - (res**2).sum() / ((b - b.mean()) ** 2).sum() if b.var() > 0 else np.nan
    rows.append(dict(graph=g, kind=kind, design=des, est_name=est, slope_per_gamma=beta[1], slope_se=np.sqrt(cov[1, 1]), intercept=beta[0],
                     intercept_se=np.sqrt(cov[0, 0]), r2=r2, bias_g05=b[0], bias_g4=b[-1], ratio_bias4_over_bias05=b[-1] / b[0] if b[0] else np.nan,
                     max_abs_bias_over_gamma_dev=np.max(np.abs(b / x - (b / x).mean()))))
G = pd.DataFrame(rows); G.to_csv(T("t14_gamma_dependence.csv"), index=False)
m = G[(G.est_name == "OLS_f") & (G.bias_g4.abs() > 0.2)]
ok = ((m.r2 >= 0.99) & (m.intercept.abs() <= 3 * m.intercept_se.clip(lower=0.02)))
hyp("H3g", "e11 OLS_f: bias vs gamma in {0.5,1,2,4}, per graph x shape x design (post-freeze)",
    f"{ok.sum()}/{len(m)} groups proportional; median slope_se {m.slope_se.median():.3f}",
    "per group weighted line bias = a + b*gamma; proportional if R2 >= 0.99 and |a| <= 3 max(SE_a, 0.02); supported if >= 75% of groups with |bias(4)|>0.2",
    "supported" if ok.mean() >= 0.75 else ("unclear" if ok.mean() >= 0.5 else "refuted"), len(m),
    "Prediction pre-stated in experiment-repo#7: OLS is linear in y and baseline/noise do not depend on gamma, so E[bias] is exactly proportional to gamma.")
print(G.round(3).to_string())

# ---------------- H6 (e12)
e12 = S("e12"); e12["mech"] = e12.o_mech + np.where(e12.o_mech == "step", "_k" + e12.o_kappa.astype(str), np.where(e12.o_mech == "shape", "_" + e12.o_kind.astype(str), ""))
keep = e12[e12.est_name.isin(["HajekFull", "HajekKappa", "DM", "OLS_f", "ORACLE", "ORACLE_D"])]
P = keep[["tag", "graph", "design", "mech", "est_name", "n_rep", "n_nan", "gate", "bias", "bias_se", "sd", "rmse"]]
P.to_csv(T("t15_hajek.csv"), index=False)
hf = e12[e12.est_name.isin(["HajekFull", "HajekKappa"])].copy()
hf["est_ok"] = hf.n_rep >= 200
frac = hf.groupby("est_name").est_ok.mean()
print("estimable (n_rep>=200) share:", frac.round(2).to_dict())
hf = hf[hf.est_ok]
small = lambda r: abs(r.bias) <= max(3 * r.bias_se, 0.1)
big = lambda r: abs(r.bias) > max(3 * r.bias_se, 0.2)
# correct mapping: HajekFull on step (kappa 1 and 0.75), HajekKappa on step kappa=.75; Bernoulli designs for Kappa, any design for Full
c1 = hf[(hf.o_mech == "step") & (hf.est_name == "HajekFull")]
c2 = hf[(hf.o_mech == "step") & (hf.o_kappa == 0.75) & (hf.est_name == "HajekKappa")]
cc = pd.concat([c1, c2]); okc = cc.apply(small, axis=1)
hyp("H6c", "e12 Hajek bias under a CORRECT exposure mapping (step mechanism)", f"{okc.sum()}/{len(cc)} estimable cells with |bias| <= max(3 SE, 0.1)",
    "supported (unbiased) if >= 75% of estimable (n_rep >= 200) cells", "supported" if okc.mean() >= 0.75 else ("unclear" if okc.mean() >= 0.5 else "refuted"), len(cc),
    f"estimable share of all e12 Hajek cells: HajekFull {frac.get('HajekFull', np.nan):.2f}, HajekKappa {frac.get('HajekKappa', np.nan):.2f}")
w1 = hf[(hf.est_name == "HajekFull") & hf.o_mech.isin(["twohop", "prop"])]
w2 = hf[(hf.est_name == "HajekKappa") & (hf.o_mech == "shape")]
w3 = hf[(hf.est_name == "HajekKappa") & (hf.o_mech == "step") & (hf.o_kappa == 1.0)]
ww = pd.concat([w1, w2, w3]); okw = ww.apply(big, axis=1)
hyp("H6d", "e12 Hajek bias under a WRONG exposure mapping (HajekFull on two-hop/propagation; HajekKappa(0.75) on linear/sigmoid shape and on step kappa=1)",
    f"{okw.sum()}/{len(ww)} estimable cells with |bias| > max(3 SE, 0.2)", "supported (biased) if >= 75% of estimable cells",
    "supported" if okw.mean() >= 0.75 else ("unclear" if okw.mean() >= 0.5 else "refuted"), len(ww),
    "HajekFull on 1-hop shape mechanisms is NOT wrong: its full-exposure contrast equals the GATE for any h (reported in t15_hajek.csv, not counted).")
def strat(df, flag):
    g = df.assign(dz=df.design.str.split(":").str[0] + np.where(df.design.str.startswith("bern"), df.design.str.split(":").str[1], ""), f=flag.values).groupby("dz").f.agg(["sum", "count"])
    return "; ".join(f"{k}: {int(r['sum'])}/{int(r['count'])}" for k, r in g.iterrows())
hyp("H6c-posthoc", "H6c stratified by design (post-hoc reading of the same cells; the verdict above is the pre-stated rule)", strat(cc, okc), "descriptive", "reported", len(cc),
    "Bernoulli(0.8): control-exposed units are rare (0.2^(d+1)), only ~330 of 400 replicates are estimable and the ratio estimator is biased upward (+0.5...+0.7)")
hyp("H6d-posthoc", "H6d stratified by design (post-hoc)", strat(ww, okw), "descriptive", "reported", len(ww), "HajekKappa on the sigmoid shape is not biased at Bernoulli(0.5): f >= 0.75 is already on the saturated part of the sigmoid")
cmp = []
for (t, g, des, mech), d in hf.groupby(["tag", "graph", "design", "mech"]):
    ols = e12[(e12.graph == g) & (e12.design == des) & (e12.mech == mech) & (e12.est_name == "OLS_f")]
    if len(ols) == 1:
        for _, r in d.iterrows():
            cmp.append(dict(est=r.est_name, hajek_rmse=r.rmse, ols_rmse=ols.rmse.iloc[0], better=r.rmse < ols.rmse.iloc[0]))
C = pd.DataFrame(cmp)
if len(C):
    sh = C.groupby("est").better.mean()
    hyp("H6e", "e12 RMSE of Hajek vs OLS_f over estimable cells", "; ".join(f"{k}: better in {v:.0%} of {int((C.est == k).sum())} cells" for k, v in sh.items()),
        "descriptive (no verdict threshold)", "reported", len(C), "median RMSE ratio Hajek/OLS_f: " + ", ".join(f"{k} {np.median(C[C.est == k].hajek_rmse / C[C.est == k].ols_rmse):.2f}" for k in sh.index))

# ---------------- e13: second seed
if not os.path.exists(os.path.join(R, "summary", "e13.csv")):
    pd.DataFrame(H).to_csv(os.path.join(R, "hypotheses_postfreeze.csv"), index=False); print(pd.DataFrame(H)[["hypothesis", "statistic", "verdict"]].to_string()); raise SystemExit
e13 = S("e13"); e13["tag"] = e13.tag.str.replace("seed2|", "", regex=False)
rows = []
# H5: Louvain vs random clusters, matched resolution, OLS_f RMSE
e4 = S("e4")
def h5(df):
    d = df[(df.est_name == "OLS_f") & df.design.str.match(r"^(louv|rand):") & df.graph.isin(["stanford3", "ego"])].copy()
    d["res"] = d.design.str.split(":").str[1].str.split(",").str[0]; d["kind"] = d.design.str.split(":").str[0]
    w = d.pivot_table(index=["graph", "o_kind", "res"], columns="kind", values="rmse")
    w["louv_worse"] = w.louv > w.rand
    return w
a, b = h5(e4), h5(e13)
for gname in ["stanford3", "ego"]:
    for nm, w in (("seed1", a), ("seed2", b)):
        x = w.xs(gname, level="graph")
        rows.append(dict(check="H5", graph=gname, seed=nm, matched_cells=len(x), louvain_rmse_greater_than_random=int(x.louv_worse.sum()),
                         mean_rmse_louvain=x.louv.mean(), mean_rmse_random=x.rand.mean()))
# H2 closed form on seed 2
e9 = e13[e13.graph.isin(["sbm:5000,50,20,0.8", "ba:5000,10", "stanford3"]) & (e13.o_mech == "shape") & e13.design.str.startswith("bern") & (e13.est_name == "OLS_f") & e13.o_curv.notna()]
cache = {}; dev = []
for _, r in e9.iterrows():
    cache.setdefault(r.graph, graphs.make(r.graph, seed=0))
    pe, _ = TB.predict(cache[r.graph], r.o_kind, r.o_curv, float(r.design.split(":")[1]))
    dev.append(dict(bias=r.bias, bias_se=r.bias_se, pred=pe))
D = pd.DataFrame(dev)
if len(D):
    rows.append(dict(check="H2", graph="sbm/ba/stanford3", seed="seed2", matched_cells=len(D), louvain_rmse_greater_than_random=np.nan,
                     mean_rmse_louvain=np.corrcoef(D.bias, D.pred)[0, 1], mean_rmse_random=(D.bias - D.pred).abs().max()))
    rows[-1]["note"] = "mean_rmse_louvain column = corr(sim, exact-binomial prediction); mean_rmse_random column = max |dev|; share within 3 SE: %.2f" % ((D.bias - D.pred).abs() <= 3 * D.bias_se.clip(lower=1e-3)).mean()
# H4 exponents on ER seed 2
er = e13[(e13.graph.str.startswith("er:")) & (e13.est_name == "OLS_f")].copy()
if len(er) >= 6:
    er["nn"] = er.graph.str.split(":").str[1].str.split(",").str[0].astype(float); er["dd"] = er.graph.str.split(",").str[1].astype(float)
    X = np.column_stack([np.ones(len(er)), np.log(er.nn), np.log(er.dd)]); y = np.log(er.sd)
    bb, *_ = np.linalg.lstsq(X, y, rcond=None); res = y - X @ bb; cov = np.linalg.inv(X.T @ X) * res.var(ddof=3)
    rows.append(dict(check="H4", graph="er", seed="seed2", matched_cells=len(er), mean_rmse_louvain=bb[1], mean_rmse_random=bb[2],
                     note="exp_n %.3f +- %.3f, exp_d %.3f +- %.3f (columns mean_rmse_* hold exp_n, exp_d)" % (bb[1], np.sqrt(cov[1, 1]), bb[2], np.sqrt(cov[2, 2]))))
pd.DataFrame(rows).to_csv(T("t16_second_seed.csv"), index=False)
print(pd.DataFrame(rows).round(3).to_string())
s2 = pd.DataFrame(rows)
if len(s2):
    r5 = s2[(s2.check == "H5") & (s2.graph == "stanford3")].set_index("seed")
    if {"seed1", "seed2"} <= set(r5.index):
        rep = r5.loc["seed2", "louvain_rmse_greater_than_random"] / r5.loc["seed2", "matched_cells"] >= 0.75
        hyp("H5s", "second seed of the Stanford3 cluster cells: Louvain RMSE > random RMSE", f"seed1 {int(r5.loc['seed1','louvain_rmse_greater_than_random'])}/{int(r5.loc['seed1','matched_cells'])}, seed2 {int(r5.loc['seed2','louvain_rmse_greater_than_random'])}/{int(r5.loc['seed2','matched_cells'])} matched cells",
            "reversal replicated if >= 75% of matched cells in seed 2", "replicated" if rep else "not replicated", int(r5.loc["seed2", "matched_cells"]), "post-freeze check")
pd.DataFrame(H).to_csv(os.path.join(R, "hypotheses_postfreeze.csv"), index=False)
print(pd.DataFrame(H)[["hypothesis", "statistic", "verdict"]].to_string())
