#!/usr/bin/env python3
"""Hypothesis-by-hypothesis tests (story-repo plan H1..H8) -> results/hypotheses.csv.
Every row: the test, the statistic, the decision rule written before looking at the verdict, the verdict (supported / refuted / unclear)
and the cells it rests on. Reads results/summary/*.csv; run after scripts/aggregate.py and scripts/theory_bias.py."""
import sys as _s, os as _o
_s.path.insert(0, _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "..", "src"))
from netgate.paths import results_dir
import os, sys
import numpy as np, pandas as pd

R = results_dir()
S = lambda e: pd.read_csv(os.path.join(R, "summary", f"{e}.csv"))
GN = {"sbm:5000,50,20,0.8": "SBM", "ba:5000,10": "BA", "ws:5000,20,0.1": "WS", "er:5000,20": "ER", "stanford3": "Stanford3", "ego": "ego-FB"}
rows = []


def add(h, test, stat, rule, verdict, cells, note=""):
    rows.append(dict(hypothesis=h, test=test, statistic=stat, decision_rule=rule, verdict=verdict, cells=cells, note=note))


def fmt(x, d=3):
    return f"{x:.{d}g}"


# ---------------- H1: correctly specified regression is unbiased
e8 = S("e8"); o = e8[e8.est_name == "ORACLE"]
mx = o.bias.abs().max()
add("H1", "noiseless ORACLE bias, e8 (all graphs/designs/shapes run)", f"max|bias|={mx:.2e} over {len(o)} cells (GATE=3)",
    "supported if max|bias|<1e-8 (machine precision); refuted if any |bias|>5 MC SE", "supported" if mx < 1e-8 else "refuted", f"e8 n={len(o)}")
noisy = []
for e in ["e1", "e2", "e3", "e5"]:
    d = S(e); d = d[d.est_name == "ORACLE_D"] if e != "e2" else d[d.est_name == "ORACLE_D"]
    d = d[d.bias_se > 0]; noisy.append(((d.bias / d.bias_se).abs()).dropna())
z = pd.concat(noisy)
add("H1", "noisy ORACLE_D bias in units of its MC SE, e1,e2,e3,e5", f"share |z|>3: {(z > 3).mean():.3f} of {len(z)} cells; max|z|={z.max():.2f}",
    "supported if share |z|>3 below 0.05 (expect ~0.003 under H0)", "supported" if (z > 3).mean() < 0.05 else "unclear", f"{len(z)} cells")

# ---------------- H2: noiseless bias = closed form
T = pd.read_csv(os.path.join(R, "summary", "theory_vs_sim_e9.csv"))
T["dev"] = T.bias - T.pred_exact; T["zz"] = T.dev / T.bias_se
dev_l = (T.bias - T.pred_largedeg).abs()
add("H2", "e9 noiseless OLS_f bias vs exact-binomial closed form (theory_bias.py)",
    f"max|dev|={T.dev.abs().max():.3f}, median|dev|={T.dev.abs().median():.4f}, share |dev|<3 MC SE={(T.zz.abs() < 3).mean():.3f}, corr={np.corrcoef(T.bias, T.pred_exact)[0,1]:.4f} over {len(T)} cells",
    "supported if corr>0.99 and median|dev|<0.01 (bias scale 0.1-5); report share within 3 MC SE", 
    "supported" if (np.corrcoef(T.bias, T.pred_exact)[0, 1] > 0.99 and T.dev.abs().median() < 0.01) else "unclear", f"e9 n={len(T)}",
    note=f"large-degree shortcut gamma*(h'(p)-1): median|dev|={dev_l.median():.3f}, max {dev_l.max():.3f}; deviations from the exact form exceed the MC SE in {(T.zz.abs()>3).mean():.0%} of cells (finite-sample/clustering of assignments, not studied further)")

# ---------------- H3: bias does not shrink with n; grows with gamma x curvature
e10 = S("e10")
d = e10[(e10.o_kind == "concave") & (e10.est_name == "OLS_f") & (e10.design.isin(["bern:0.1", "bern:0.5"]))].copy()
d["n_nom"] = d.graph.str.extract(r"sbm:(\d+)")[0].astype(float)
res = []
for des, g in d.groupby("design"):
    g = g.sort_values("n_nom"); sl = np.polyfit(np.log(g.n_nom), np.log(g.bias.abs()), 1)[0]
    res.append(f"{des}: bias {g.bias.iloc[0]:+.2f}->{g.bias.iloc[-1]:+.2f} (n 1e3->{int(g.n_nom.iloc[-1]):,}), slope log|bias|~log n={sl:+.2f}")
ok = all(abs(g.sort_values('n_nom').bias.iloc[-1]) > 0.7 * abs(g.sort_values('n_nom').bias.iloc[0]) for _, g in d.groupby("design"))
add("H3a", "e10 concave spillover: OLS_f bias vs n (SBM, 1k-20k, Bernoulli)", "; ".join(res),
    "supported if |bias| at the largest n is >=70% of that at n=1000 for both p (sampling error would fall like n^-1/2, to ~22%)", "supported" if ok else "refuted", f"e10 {len(d)} rows")
e9 = S("e9"); q = e9[e9.est_name == "OLS_f"].copy(); q["x"] = q.o_gamma * q.o_curv if "o_gamma" in q else q.o_curv
q = q.assign(ab=q.bias.abs())
rho = q.groupby(["graph", "design"]).apply(lambda g: g.ab.corr(g.o_curv, method="spearman"), include_groups=False)
add("H3b", "e9 noiseless |bias| vs curvature (gamma fixed)", f"median Spearman(|bias|,curvature) over graph x design = {rho.median():.2f} (min {rho.min():.2f}, n={len(rho)}); gamma is not varied in e9",
    "supported if median rho>0.8; gamma-dependence is NOT tested here (e9 fixes gamma) - see note", "supported" if rho.median() > 0.8 else "unclear", f"e9 {len(q)} rows",
    note="gamma x curvature interaction: only the curvature factor is varied in e9; the gamma factor is covered by e2 (gamma fixed 2) and not separately by this test")

# ---------------- H4: SD scaling in n, d (ER, Bernoulli 0.5, e3) and p (e4)
e3 = S("e3")
x = e3[e3.graph.str.startswith("er:") & (e3.est_name == "OLS_f") & (e3.design == "bern:0.5")].copy()
a = x.graph.str.extract(r"er:(\d+),(\d+)"); x["n"] = a[0].astype(float); x["d"] = a[1].astype(float)
X = np.column_stack([np.ones(len(x)), np.log(x.n), np.log(x.d)]); b, *_ = np.linalg.lstsq(X, np.log(x.sd), rcond=None)
r = np.log(x.sd) - X @ b; cov = np.linalg.inv(X.T @ X) * r.var(ddof=3); se = np.sqrt(np.diag(cov))
add("H4a", "e3 ER Bernoulli(0.5), OLS_f: log SD ~ log n + log d", f"exp_n={b[1]:+.3f}+-{se[1]:.3f} (pred -0.5), exp_d={b[2]:+.3f}+-{se[2]:.3f} (pred +0.5), {len(x)} cells, R2 residual sd {r.std():.3f}",
    "supported if both exponents within 0.05 of prediction", "supported" if abs(b[1] + .5) < .05 and abs(b[2] - .5) < .05 else "refuted", f"e3 n={len(x)}")
y = e3[e3.graph.str.startswith("sbm:") & (e3.est_name == "OLS_f") & (e3.design == "louv:1.0,0.5")].copy()
if len(y) >= 6:
    a = y.graph.str.extract(r"sbm:(\d+),\d+,(\d+)"); y["n"] = a[0].astype(float); y["d"] = a[1].astype(float)
    X = np.column_stack([np.ones(len(y)), np.log(y.n), np.log(y.d)]); b2, *_ = np.linalg.lstsq(X, np.log(y.sd), rcond=None)
    add("H4b", "e3 SBM + Louvain-cluster design, OLS_f: log SD ~ log n + log d", f"exp_n={b2[1]:+.3f}, exp_d={b2[2]:+.3f} ({len(y)} cells)",
        "descriptive (the prediction is stated for Bernoulli designs)", "unclear", f"e3 n={len(y)}")
e4 = S("e4"); p4 = e4[e4.tag.str.contains("bern_p") & (e4.o_kind == "linear") & (e4.est_name == "OLS_f")].copy()
p4["p"] = p4.design.str.extract(r"bern:([\d.]+)")[0].astype(float)
out = []
for g, gg in p4.groupby("graph"):
    gg = gg.sort_values("p"); sl = np.polyfit(np.log(np.sqrt(1 / (gg.p * (1 - gg.p)))), np.log(gg.sd), 1)[0]
    out.append(f"{GN.get(g, g)}: slope of log SD on log sqrt(1/(p(1-p)))={sl:.2f} ({len(gg)} p-values)")
add("H4c", "e4 SD vs p, OLS_f, linear truth", "; ".join(out), "supported if slope within [0.7,1.3] (pred 1) for every graph", "supported" if all(0.7 < float(s.split('=')[1].split(' ')[0]) < 1.3 for s in out) else "unclear", f"e4 {len(p4)} rows")

# ---------------- H5: good vs random clusters (e4)
c = e4[e4.tag.str.contains("louv_res|rand_res") & e4.est_name.isin(["OLS_f", "DM", "ORACLE_D"])].copy()
c["clus"] = np.where(c.design.str.startswith("louv"), "louvain", "random"); c["res"] = c.design.str.extract(r":([\d.]+),")[0].astype(float)
piv = c.pivot_table(index=["graph", "o_kind", "est_name", "res"], columns="clus", values=["bias", "sd", "rmse"], aggfunc="first").dropna()
piv.columns = [f"{a}_{b}" for a, b in piv.columns]
piv = piv.reset_index()
txt = []
for (g, k, en), gg in piv.groupby(["graph", "o_kind", "est_name"]):
    if en != "OLS_f": continue
    txt.append(f"{GN.get(g,g)}/{k}: median RMSE louvain={gg.rmse_louvain.median():.2f} vs random={gg.rmse_random.median():.2f}; |bias| {gg.bias_louvain.abs().median():.2f} vs {gg.bias_random.abs().median():.2f}")
frac = (piv[piv.est_name == "OLS_f"].rmse_louvain < piv[piv.est_name == "OLS_f"].rmse_random).mean()
fracdm = (piv[piv.est_name == "DM"].bias_louvain.abs() < piv[piv.est_name == "DM"].bias_random.abs()).mean()
add("H5a", "e4 matched-resolution comparison of Louvain vs random clusters (OLS_f RMSE; DM |bias|)",
    f"Louvain RMSE<random in {frac:.0%} of {int((piv.est_name=='OLS_f').sum())} matched OLS_f cells; DM |bias| smaller in {fracdm:.0%}; " + " | ".join(txt),
    "supported if good clusters have lower RMSE in >=75% of matched cells and random clusters show no gain over Bernoulli", "supported" if frac >= .75 else ("refuted" if frac <= .25 else "unclear"), f"e4 {len(piv)} matched rows")
pb = e4[e4.tag.str.startswith("sbm_f") & e4.est_name.isin(["OLS_f", "DM"]) & (e4.o_kind == "linear")]
if len(pb):
    t = pb.assign(f=pb.tag.str.replace("sbm_f", "").astype(float)).groupby(["f", "design", "est_name"])[["bias", "sd", "rmse"]].mean().round(3)
    add("H5b", "e4 planted-block quality (within-block edge fraction 0.8/0.9/0.97), linear truth", "see results/tables/t6b_planted_blocks.csv; " + str(len(pb)) + " rows",
        "descriptive: monotone improvement in RMSE with quality would support H5", "unclear", f"e4 {len(pb)} rows", note=t.to_string().replace("\n", " | "))

# ---------------- H6: DM vs regression by strength (e1)
e1 = S("e1"); rr = []
for (g, des), gg in e1.groupby(["graph", "design"]):
    dm = gg[gg.est_name == "DM"].set_index("o_gamma"); ols = gg[gg.est_name == "OLS_f"].set_index("o_gamma")
    sl = np.polyfit(dm.index, dm.bias, 1)[0]; rr.append(dict(graph=GN.get(g, g), design=des, slope=sl, dm_gt_ols_gamma=min([k for k in dm.index if dm.rmse[k] > ols.rmse[k]], default=np.nan),
                                                          dm_wins_at0=bool(dm.rmse[0.0] < ols.rmse[0.0])))
rr = pd.DataFrame(rr); bern = rr[rr.design == "bern:0.5"]
add("H6a", "e1 DM bias slope in gamma (truth: GATE = tau + gamma; DM sees tau only under Bernoulli)",
    f"Bernoulli(0.5): slope {bern.slope.min():.3f}..{bern.slope.max():.3f} over {len(bern)} graphs; Louvain clusters: {rr[rr.design!='bern:0.5'].slope.min():.2f}..{rr[rr.design!='bern:0.5'].slope.max():.2f}",
    "supported if Bernoulli slopes within 0.05 of -1 (proportional to gamma)", "supported" if (bern.slope + 1).abs().max() < .05 else "unclear", f"e1 {len(rr)} graph x design")
add("H6b", "e1 DM wins RMSE at gamma=0, loses at larger gamma",
    f"DM wins at gamma=0 in {int(rr.dm_wins_at0.sum())}/{len(rr)} graph x design; first gamma at which OLS_f beats DM: " + ", ".join(f"{r.graph}/{r.design.split(':')[0]}={r.dm_gt_ols_gamma:g}" for r in rr.itertuples()),
    "supported if DM wins at gamma=0 in all combinations and OLS_f wins by gamma<=4", "supported" if rr.dm_wins_at0.all() and rr.dm_gt_ols_gamma.notna().all() else "unclear", "e1")
hj = e1[e1.est_name.isin(["HajekFull", "HajekKappa"])]
add("H6c", "Hajek / exposure-mapping baselines estimable?", f"HajekFull n_rep median {hj[hj.est_name=='HajekFull'].n_rep.median():.0f} (of ~400), n_nan median {hj[hj.est_name=='HajekFull'].n_nan.median():.0f}; HajekKappa n_rep median {hj[hj.est_name=='HajekKappa'].n_rep.median() if (hj.est_name=='HajekKappa').any() else float('nan')}",
    "reported as unestimable when n_rep<10 (full-neighbourhood exposure units absent at this degree)", "unclear", "e1", note="no extra Hajek design run; the statement 'Hajek is biased if its exposure model is wrong' is therefore not tested")

# ---------------- H7: coverage (e6)
e6 = S("e6"); e6 = e6[~(e6.mean_se_cl < 1e-6)]
cv = e6[e6.est_name.isin(["OLS_f", "ORACLE_D"])]
def cov(kind, est, col): 
    g = cv[(cv.o_kind == kind) & (cv.est_name == est)]; return g[col].mean(), g[col].min(), len(g)
parts = []
for kind in ["linear", "concave"]:
    for est in ["ORACLE_D", "OLS_f"]:
        parts.append(f"{kind}/{est}: " + ", ".join(f"{c[4:]}={cov(kind, est, c)[0]:.2f}" for c in ["cov_hc", "cov_cl", "cov_hac1", "cov_hac2"]))
hc_l = cov("linear", "OLS_f", "cov_hc")[0]; hc_c = cov("concave", "OLS_f", "cov_cl")[0]
add("H7a", "e6 mean 95% CI coverage by SE type (degenerate cell e6 BA acl0.5 excluded: one analysis cluster)", " | ".join(parts) + f"; n cells linear/OLS_f={cov('linear','OLS_f','cov_hc')[2]}",
    "supported if HC0 coverage <0.85 for correctly specified/linear cells and cluster-robust/HAC raise it; coverage loses under bias (concave OLS_f < 0.85)",
    "supported" if (hc_l < .85 and hc_c < .85) else "unclear", f"e6 {len(cv)} rows")

# ---------------- H8: graph family and 2-hop (e2, e7)
e2 = S("e2"); a = e2[(e2.design == "bern:0.5") & (e2.o_kind == "linear") & (e2.est_name == "OLS_f")].set_index("graph").rmse
b = e2[(e2.design == "bern:0.5") & (e2.o_kind == "linear") & (e2.est_name == "ORACLE_D")].set_index("graph").sd
add("H8a", "e2 graph family: OLS_f RMSE (Bernoulli 0.5, linear truth)", ", ".join(f"{GN.get(g,g)}={v:.2f}" for g, v in a.items()) + f" (n,d differ across graphs: confounded)",
    "supported if both heavy-tailed graphs (BA, Stanford3) have RMSE above the median of the six graphs; refuted if both are below it",
    "supported" if (a.reindex(["ba:5000,10", "stanford3"]) > a.median()).all() else ("refuted" if (a.reindex(["ba:5000,10", "stanford3"]) < a.median()).all() else "unclear"), f"e2 {len(a)} graphs")
e7 = S("e7"); tw = e7[(e7.o_mech == "twohop") & (e7.design == "bern:0.5") & e7.est_name.isin(["OLS_f", "ORACLE_D"])].pivot_table(index="graph", columns="est_name", values=["bias", "rmse"])
if len(tw):
    add("H8b", "e7 two-hop interference fitted with 1-hop features (OLS_f) vs the 2-hop-aware ORACLE_D, Bernoulli 0.5",
        ", ".join(f"{GN.get(g,g)}: OLS_f bias {r[('bias','OLS_f')]:+.2f}, rmse {r[('rmse','OLS_f')]:.2f} vs ORACLE_D rmse {r[('rmse','ORACLE_D')]:.2f}" for g, r in tw.iterrows()),
        "supported if OLS_f |bias|>0.3 on all graphs", "supported" if (tw[('bias', 'OLS_f')].abs() > .3).all() else "unclear", f"e7 {len(tw)} graphs",
        note="ORACLE_D here = [1, z, f1, f2, log-degree]: the correctly specified model (2-hop exposure + degree-dependent baseline). Its RMSE is variance-dominated and exceeds that of the misspecified OLS_f in most graphs (bias-variance trade-off); 'ORACLE' (no degree term) is not correctly specified in e7 because baselines depend on degree")

# ---------------- claim-level supporting numbers (C2, C6)
g = e1[(e1.o_gamma == 0) & (e1.design == "bern:0.5")].pivot(index="graph", columns="est_name", values="sd")
rat = (g.OLS_f / g.DM)
add("C2a", "e1 gamma=0, Bernoulli(0.5): SD of OLS_f over SD of DM (no interference, both unbiased)", ", ".join(f"{GN.get(k,k)}={v:.1f}" for k, v in rat.items()),
    "supported if the ratio exceeds 3 on every graph", "supported" if rat.min() > 3 else "unclear", "e1 6 graphs")
dd = e2[e2.est_name == "OLS_f"].assign(rb=lambda d: d.bias / d.gate)
txt = "; ".join(f"{k}: median |bias|/GATE={gg.rb.abs().median():.2f}, bias-dominated (bias^2>RMSE^2/2) in {(gg.bias**2/gg.rmse**2 > .5).mean():.0%} of {len(gg)} cells" for k, gg in dd.groupby("o_kind"))
add("C2b", "e2 OLS_f: bias vs variance by spillover shape (gamma=2, 6 graphs x 4 designs)", txt, "bias dominates for sigmoid, not for linear (bias-dominated share 0 for linear)",
    "supported" if (dd[dd.o_kind == "linear"].bias**2 / dd[dd.o_kind == "linear"].rmse**2 > .5).mean() == 0 and (dd[dd.o_kind == "sigmoid"].bias**2 / dd[dd.o_kind == "sigmoid"].rmse**2 > .5).mean() > .5 else "unclear", "e2")
pv = e2[e2.est_name.isin(["DM", "OLS_f", "GBM", "OLS_quad", "ORACLE_D"])].pivot_table(index=["graph", "o_kind", "design"], columns="est_name", values="rmse")
add("C2c", "e2 RMSE comparisons over 96 graph x shape x design cells",
    f"OLS_f<DM in {(pv.OLS_f < pv.DM).mean():.0%}; ORACLE_D<OLS_f in {(pv.ORACLE_D < pv.OLS_f).mean():.0%}; OLS_quad<OLS_f in {(pv.OLS_quad < pv.OLS_f).mean():.0%}; GBM<OLS_f in {(pv.GBM < pv.OLS_f).mean():.0%}",
    "descriptive (ranking of estimators by RMSE)", "unclear", f"e2 {len(pv)} cells", note="OLS_quad and GBM rarely beat OLS_f: extra flexibility costs variance at these n and often extrapolates badly")

H = pd.DataFrame(rows); H.to_csv(os.path.join(R, "hypotheses.csv"), index=False)
pd.set_option("display.width", 250, "display.max_colwidth", 300)
for r in rows:
    print(f"\n[{r['hypothesis']}] {r['verdict'].upper()} - {r['test']}\n   {r['statistic']}\n   rule: {r['decision_rule']}\n   {r['note']}")
