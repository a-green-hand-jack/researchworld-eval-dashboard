"""Writes paper/quote_numbers.tex: every number quoted in the running text of the paper, computed from the committed files in results/.
Usage: python3 paper/quote_numbers.py [RESULTS_DIR] [OUT.tex]   (units: pp = percentage points; rates in percent)"""
import sys, os, numpy as np, pandas as pd
here = os.path.dirname(os.path.abspath(__file__))
R = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "results")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "quote_numbers.tex")
M = {}
def put(k, v, f="{:.1f}"): M[k] = f.format(v)
pp = lambda x: 100 * x

d = pd.read_csv(os.path.join(R, "synth_plan_summary.csv"))
th = pd.read_csv(os.path.join(R, "synth_theory_prediction.csv"))
cp = pd.read_csv(os.path.join(R, "synth_compare_summary.csv"))
ld = pd.read_csv(os.path.join(R, "synth_ladder_summary.csv"))

def cell(est="naive", **kw):
    q = d[(d.est_name == est) & (d.f_kind == "ofat")]
    for k, v in kw.items(): q = q[np.isclose(q[k], v) if isinstance(v, float) else (q[k] == v)]
    assert len(q) == 1, (est, kw, len(q)); return q.iloc[0]
REF = dict(f_n=200, f_K=16, f_tau=0.01, f_rho=0.5, f_m=0.3, f_proc="argmax", f_eps=0.0, f_leak=0, f_outlier=0.0)
def ref(est="naive", **over): return cell(est, **{**REF, **over})

# --- reference cell, all methods
for e in ["naive", "split", "crossfit", "boot_opt", "boot_oob", "boot_632", "simul", "cond"]:
    r = ref(e)
    put(f"ref_{e}_bias", pp(r.bias), "{:.2f}"); put(f"ref_{e}_biasse", pp(r.bias_se), "{:.2f}")
    put(f"ref_{e}_rmse", pp(r.rmse)); put(f"ref_{e}_cover", pp(r.cover), "{:.0f}"); put(f"ref_{e}_width", pp(r.width))
    put(f"ref_{e}_fp", pp(r.fp_rate), "{:.0f}")
put("ref_reps", ref().reps, "{:.0f}")
for e in ("naive", "split", "simul"): put(f"ref_{e}_claim", pp(ref(e).claim), "{:.0f}"); put(f"ref_{e}_ship2", pp(ref(e).ship_2pp), "{:.0f}"); put(f"ref_{e}_fship2", pp(ref(e).false_ship_2pp), "{:.0f}")
put("ref_nonpos", pp(ref().n_nonpos / ref().reps), "{:.0f}")
put("ref_mu_sel", pp(ref().mu_sel), "{:.1f}")
# --- margin-based claim rates (experiment-repo's synth_claim_margin_summary.csv / synth_compare_margin_summary.csv)
cm = pd.read_csv(os.path.join(R, "synth_claim_margin_summary.csv")); cc = pd.read_csv(os.path.join(R, "synth_compare_margin_summary.csv"))
rc = cm[(cm.f_kind == "ofat") & (cm.f_n == 200) & (cm.f_K == 16) & np.isclose(cm.f_tau, 0.01) & np.isclose(cm.f_rho, 0.5) & np.isclose(cm.f_m, 0.3) & (cm.f_proc == "argmax") & (cm.f_eps == 0) & (cm.f_leak == 0) & (cm.f_outlier == 0)].set_index("est_name")
for e in ("naive", "split", "simul"):
    put(f"mg_{e}_ws", pp(rc.loc[e, "wrong_sign_claim"]), "{:.1f}"); put(f"mg_{e}_le05", pp(rc.loc[e, "claim_given_le_0.5pp"]), "{:.0f}"); put(f"mg_{e}_le1", pp(rc.loc[e, "claim_given_le_1pp"]), "{:.0f}")
put("mg_naive_fc05", pp(rc.loc["naive", "false_claim_0.5pp"]), "{:.0f}")
q = cc[np.isclose(cc.tau, 0.0) & (cc.KA == 64) & (cc.KB == 1) & (cc.n == 200) & (cc.est_name == "naive")].iloc[0]
put("cmp_00_6401_fc05", pp(q["false_claim_0.5pp"]), "{:.0f}"); put("cmp_00_6401_ws", pp(q.wrong_sign_claim), "{:.0f}")
# --- OFAT effects on the naive gap
for K in (2, 4, 8, 16, 32, 64, 128): put(f"gap_K{K}", pp(ref(f_K=K).bias))
for n in (50, 100, 200, 500, 1000, 2000): put(f"gap_n{n}", pp(ref(f_n=n).bias)); put(f"cov_n{n}", pp(ref(f_n=n).cover), "{:.0f}")
for K in (2, 4, 8, 16, 32, 64, 128): put(f"cov_K{K}", pp(ref(f_K=K).cover), "{:.0f}")
for t in (0.0, 0.005, 0.01, 0.03): put(f"gap_tau{str(t).replace('.','')}", pp(ref(f_tau=t).bias))
for r_ in (0.0, 0.3, 0.5, 0.6, 0.9): put(f"gap_rho{int(10*r_)}", pp(ref(f_rho=r_).bias))
for m in (0.1, 0.3, 0.5, 0.8): put(f"gap_m{int(10*m)}", pp(ref(f_m=m).bias))
for e in (0.1, 0.2): put(f"gap_eps{int(10*e)}", pp(ref(f_eps=e).bias))
for l in (3, 8): put(f"gap_leak{l}", pp(ref(f_leak=l).bias)); put(f"cov_leak{l}", pp(ref(f_leak=l).cover), "{:.0f}"); put(f"fp_leak{l}", pp(ref(f_leak=l).fp_rate), "{:.0f}")
for p in ("sh", "sr"): put(f"gap_{p}", pp(ref(f_proc=p).bias)); put(f"cov_{p}", pp(ref(f_proc=p).cover), "{:.0f}")
g = cell("naive", **{**REF, "f_K": 128, "f_proc": "greedy"}); put("gap_greedy", pp(g.bias)); put("cov_greedy", pp(g.cover), "{:.0f}")
put("gap_K128_argmax", pp(ref(f_K=128).bias)); put("fp_K128", pp(ref(f_K=128).fp_rate), "{:.0f}")
# --- stress cell: small n, K=128, chance-level accuracy
s = d[(d.f_kind == "stress") & (d.f_n == 50) & (d.f_K == 128) & (d.est_name == "naive")].iloc[0]
put("stress_gap", pp(s.bias)); put("stress_cover", pp(s.cover), "{:.0f}"); put("stress_fp", pp(s.fp_rate), "{:.0f}")
# --- theory vs. simulation
t = th.dropna(subset=["emp_gap"]).copy(); t["diff"] = t.emp_gap - t.pred_gap
t["z"] = t["diff"].abs() / np.sqrt(t.pred_gap_mc_se ** 2 + t.emp_gap_mc_se ** 2)
put("th_cells", len(t), "{:.0f}"); put("th_meanabs", pp(t["diff"].abs().mean()), "{:.2f}"); put("th_maxabs", pp(t["diff"].abs().max()), "{:.2f}")
put("th_dmin", pp(t["diff"].min()), "{:.2f}"); put("th_dmax", pp(t["diff"].max()), "{:.2f}"); put("th_above", int((t["diff"] > 0).sum()), "{:.0f}")
put("th_nz", int((t.z > 2).sum()), "{:.0f}"); put("th_over", int((t["diff"] < 0).sum()), "{:.0f}")
put("th_meandiff", pp(t["diff"].mean()), "{:.2f}")
put("th_nz_above", int(((t.z > 2) & (t["diff"] > 0)).sum()), "{:.0f}"); put("th_nz_below", int(((t.z > 2) & (t["diff"] < 0)).sum()), "{:.0f}")
from scipy.stats import binomtest
put("th_signp", binomtest(int((t["diff"] > 0).sum()), len(t)).pvalue * 1e4, "{:.1f}")   # two-sided sign-test p, in units of 1e-4
put("th_rho5_cells", int((np.isclose(t.rho, 0.5)).sum()), "{:.0f}"); put("th_Kmax", int(t.K.max()), "{:.0f}")
# --- reliability criterion of the plan (|bias| <= max(2 se, 0.5 pp) and coverage inside the 95% binomial MC band)
d["okb"] = d.bias.abs() <= np.maximum(2 * d.bias_se, 0.005)
d["okc"] = (d.cover - 0.95).abs() <= 1.96 * np.sqrt(0.95 * 0.05 / d.reps)
d["ok"] = d.okb & d.okc
rel = d.groupby("est_name").agg(cells=("ok", "size"), ok=("ok", "sum"), okb=("okb", "sum"), okc=("okc", "sum"))
for e, r in rel.iterrows():
    put(f"rel_{e}_cells", r.cells, "{:.0f}"); put(f"rel_{e}_ok", r.ok, "{:.0f}"); put(f"rel_{e}_okb", r.okb, "{:.0f}"); put(f"rel_{e}_okc", r.okc, "{:.0f}")
bd = 1.96 * np.sqrt(0.95 * 0.05 / d.reps); d["under"] = d.cover < 0.95 - bd; d["over"] = d.cover > 0.95 + bd   # which side of the band
for e, r in d.groupby("est_name").agg(under=("under", "sum"), over=("over", "sum")).iterrows():
    put(f"rel_{e}_under", r.under, "{:.0f}"); put(f"rel_{e}_over", r.over, "{:.0f}")
sp = d[(d.est_name == "split") & ~d.ok]
put("split_fail_bias", int((~sp.okb).sum()), "{:.0f}"); put("split_fail_cov", int((~sp.okc).sum()), "{:.0f}")
sb = d[d.est_name == "split"]; put("split_maxabsbias", pp(sb.bias.abs().max()), "{:.2f}")
# --- two-system comparison (naive)
def cmpv(tau, KA, KB, n, col, est="naive"):
    q = cp[(np.isclose(cp.tau, tau)) & (cp.KA == KA) & (cp.KB == KB) & (cp.n == n) & (cp.est_name == est)]; assert len(q) == 1; return q.iloc[0][col]
for tau in (0.0, 0.01):
    k = str(tau).replace(".", "")
    put(f"cmp_{k}_6401_claim", pp(cmpv(tau, 64, 1, 200, "claim")), "{:.0f}")
    put(f"cmp_{k}_6401_false", pp(cmpv(tau, 64, 1, 200, "false_claim")), "{:.0f}")
    put(f"cmp_{k}_6401_diff", pp(cmpv(tau, 64, 1, 200, "mean_reported_diff")), "{:.1f}")
    put(f"cmp_{k}_1616_false", pp(cmpv(tau, 16, 16, 200, "false_claim")), "{:.1f}")
put("cmp_reps", cmpv(0.0, 64, 1, 200, "reps"), "{:.0f}")
sp_ = cmpv(0.0, 64, 1, 200, "claim", "split"); put("cmp_0_6401_claim_split", pp(sp_), "{:.0f}")
# --- Ladder-type report vs naive (tau=0, argmax, n=200, K=16 and K=128)
for K in (16, 128):
    for e in ("naive", "ladder"):
        q = ld[(ld.est_name == e) & np.isclose(ld.tau, 0.0) & (ld.proc == "argmax") & (ld.n == 200) & (ld.K == K)]
        if len(q) == 1: put(f"lad_{e}_K{K}_bias", pp(q.iloc[0].bias)); put(f"lad_{e}_K{K}_cover", pp(q.iloc[0].cover), "{:.0f}")

# --- hybrid (winner-aware) interval and ranking study
hy = pd.read_csv(os.path.join(R, "synth_hybrid_summary.csv")); rk = pd.read_csv(os.path.join(R, "synth_ranking_summary.csv"))
for e in ("hybrid", "cond", "simul", "naive"):
    q = hy[hy.est_name == e]
    put(f"hy_{e}_covmin", pp(q.cover.min()), "{:.1f}"); put(f"hy_{e}_covmax", pp(q.cover.max()), "{:.1f}"); put(f"hy_{e}_covmean", pp(q.cover.mean()), "{:.1f}")
    put(f"hy_{e}_width", pp(q.width.mean()), "{:.1f}")
    r0 = q[(q.n == 200) & (q.K == 16) & np.isclose(q.tau, 0.01)]; assert len(r0) == 1
    put(f"hy_{e}_refcover", pp(r0.iloc[0].cover), "{:.0f}"); put(f"hy_{e}_refwidth", pp(r0.iloc[0].width), "{:.1f}")
put("hy_cells", len(hy[hy.est_name == "hybrid"]), "{:.0f}"); put("hy_reps", hy.reps.max(), "{:.0f}")
def rkv(design, est, col, tau=0.0, n=200):
    q = rk[(rk.design == design) & (rk.est_name == est) & np.isclose(rk.tau_gen, tau) & (rk.n == n)]; assert len(q) == 1; return q.iloc[0][col]
for e in ("naive", "split"):
    put(f"rk_{e}_big_rep", pp(rkv("unequal_K4_64", e, "big_reported_best")), "{:.0f}")
    put(f"rk_{e}_big_true", pp(rkv("unequal_K4_64", e, "big_truly_best")), "{:.0f}")
put("rk_naive_eq_big_rep", pp(rkv("equal_K16", "naive", "big_reported_best")), "{:.0f}")
put("rk_naive_kt_uneq", rkv("unequal_K4_64", "naive", "tau_mean", 0.03), "{:.2f}"); put("rk_split_kt_uneq", rkv("unequal_K4_64", "split", "tau_mean", 0.03), "{:.2f}")
put("rk_reps", rk.reps.max(), "{:.0f}")

# --- real LLM x MMLU-Pro (interim scale: whatever configurations are complete; K and items are read from the files)
import json
rl = pd.read_csv(os.path.join(R, "real_summary.csv")); rsp = pd.read_csv(os.path.join(R, "matrix_spread.csv")).iloc[0]
cl = json.load(open(os.path.join(R, "compute_log.json")))
rl = rl[rl.truth_arm == "disjoint"]; KR = int(rl.K.max())
put("real_K", KR, "{:.0f}"); put("real_items", cl["matrix"]["items"], "{:.0f}"); put("real_planned", 60, "{:.0f}")
put("real_accmin", pp(cl["matrix"]["acc_min"]), "{:.1f}"); put("real_accmax", pp(cl["matrix"]["acc_max"]), "{:.1f}")
put("real_accmean", pp(rsp.acc_mean), "{:.1f}"); put("real_sd", pp(rsp.sd_acc_across_configs), "{:.1f}"); put("real_corr", rsp.mean_pairwise_item_corr, "{:.2f}")
put("real_reps", rl.reps.max(), "{:.0f}"); put("real_passes", cl["matrix"]["forward_passes_scored"], "{:,.0f}"); put("real_cells", cl["matrix"]["cells_planned"], "{:,.0f}")
def rr(proc, n, K, est, col):
    q = rl[(rl.proc == proc) & (rl.n == n) & (rl.K == K) & (rl.est_name == est)]; assert len(q) == 1, (proc, n, K, est); return q.iloc[0][col]
for n in (50, 100, 200, 400):
    put(f"real_gap_n{n}", pp(rr("argmax", n, KR, "naive", "bias"))); put(f"real_gapse_n{n}", pp(rr("argmax", n, KR, "naive", "bias_se")))
    put(f"real_cover_n{n}", pp(rr("argmax", n, KR, "naive", "cover")), "{:.0f}"); put(f"real_fp_n{n}", pp(rr("argmax", n, KR, "naive", "fp_rate")), "{:.0f}")
put("real_gap_K1_n200", pp(rr("argmax", 200, 1, "naive", "bias"))); put("real_gapse_K1_n200", pp(rr("argmax", 200, 1, "naive", "bias_se")))
put("real_gap_K2_n200", pp(rr("argmax", 200, 2, "naive", "bias"))); put("real_gap_K4_n200", pp(rr("argmax", 200, 4, "naive", "bias")))
for pr in ("sh", "sr", "greedy"):
    put(f"real_gap_{pr}", pp(rr(pr, 200, KR, "naive", "bias"))); put(f"real_cover_{pr}", pp(rr(pr, 200, KR, "naive", "cover")), "{:.0f}"); put(f"real_fp_{pr}", pp(rr(pr, 200, KR, "naive", "fp_rate")), "{:.0f}")
put("real_regret_n200", pp(rr("argmax", 200, KR, "naive", "regret")))
for e in ("naive", "split", "crossfit", "boot_opt", "boot_oob", "boot_632", "simul", "cond", "hybrid"):
    for n in (50, 200):
        put(f"real_{e}_n{n}_bias", pp(rr("argmax", n, KR, e, "bias"))); put(f"real_{e}_n{n}_biasse", pp(rr("argmax", n, KR, e, "bias_se")))
        put(f"real_{e}_n{n}_rmse", pp(rr("argmax", n, KR, e, "rmse"))); put(f"real_{e}_n{n}_cover", pp(rr("argmax", n, KR, e, "cover")), "{:.0f}")
        put(f"real_{e}_n{n}_width", pp(rr("argmax", n, KR, e, "width")), "{:.1f}"); put(f"real_{e}_n{n}_fp", pp(rr("argmax", n, KR, e, "fp_rate")), "{:.0f}")
# --- equal-total-item-budget comparison of reporting protocols (fresh_protocol_summary.csv; each row scored against its own mu_ship)
fp = pd.read_csv(os.path.join(R, "fresh_protocol_summary.csv"))
def fpr(est, items, nt=None, **over):
    k = dict(tau=0.01, K=16, rho=0.5, m=0.3); k.update(over)
    q = fp[(fp.est_name == est) & (fp["items"] == items)]
    for a, b in k.items(): q = q[np.isclose(q[a], b)]
    if nt is not None: q = q[q.n_tune == nt]
    assert len(q) == 1, (est, items, nt, over, len(q)); return q.iloc[0]
for N in (200, 400):
    for e in ("naive", "boot_oob", "boot_opt", "boot_632", "crossfit", "hybrid", "split", "simul"):
        r = fpr(e, N)
        put(f"fr_{e}_{N}_bias", pp(r.bias), "{:.1f}"); put(f"fr_{e}_{N}_rmse", pp(r.rmse)); put(f"fr_{e}_{N}_cover", pp(r.cover), "{:.0f}"); put(f"fr_{e}_{N}_width", pp(r.width), "{:.1f}")
        put(f"fr_{e}_{N}_mu", pp(r.mu_ship), "{:.1f}")
for N, nts in ((200, (50, 100)), (400, (100, 200))):
    for nt in nts:
        r = fpr("fresh", N, nt)
        put(f"fr_fresh{nt}_{N}_bias", pp(r.bias), "{:.1f}"); put(f"fr_fresh{nt}_{N}_rmse", pp(r.rmse)); put(f"fr_fresh{nt}_{N}_cover", pp(r.cover), "{:.0f}"); put(f"fr_fresh{nt}_{N}_width", pp(r.width), "{:.1f}")
        put(f"fr_fresh{nt}_{N}_mu", pp(r.mu_ship), "{:.1f}")
put("fr_reps", fp.reps.max(), "{:.0f}")
# in how many of the 18 cells x 2 budgets the out-of-bag bootstrap has the smaller rmse than the 50/50 split and than the half/half fresh protocol
nb = ns = nf = nh = ntot = 0; covlo = 1.0; covhi = 0.0
for (tau, K, rho), g in fp.groupby(["tau", "K", "rho"]):
    for N in (200, 400):
        gg = g[g["items"] == N]; ob = gg[gg.est_name == "boot_oob"].iloc[0]; sp = gg[gg.est_name == "split"].iloc[0]
        fr = gg[(gg.est_name == "fresh") & (gg.n_tune == N // 2)].iloc[0]; na = gg[gg.est_name == "naive"].iloc[0]; hy_ = gg[gg.est_name == "hybrid"].iloc[0]
        ntot += 1; ns += ob.rmse < sp.rmse; nf += ob.rmse < fr.rmse; nh += hy_.rmse > na.rmse
        covlo = min(covlo, ob.cover); covhi = max(covhi, ob.cover)
put("fr_ncells", ntot, "{:.0f}"); put("fr_oob_lt_split", ns, "{:.0f}"); put("fr_oob_lt_fresh", nf, "{:.0f}"); put("fr_hyb_gt_naive", nh, "{:.0f}")
put("fr_oob_covmin", pp(covlo), "{:.0f}"); put("fr_oob_covmax", pp(covhi), "{:.0f}")
vc = pd.read_csv(os.path.join(R, "validation_cond_hybrid.csv")); vl = pd.read_csv(os.path.join(R, "validation_lead.csv"))
vc["num"] = pd.to_numeric(vc.value, errors="coerce")
def vv(chk, stat):
    q = vc[vc.check.str.contains(chk, regex=False) & (vc.stat == stat)]; assert len(q) == 1, (chk, stat, len(q)); return float(q.iloc[0].num)
cv = vc[vc.check.str.startswith("PIT/coverage")]
cvals = cv[cv.stat.isin(["cond coverage", "hybrid coverage"])].num
put("val_cov_min", pp(cvals.min()), "{:.1f}"); put("val_cov_max", pp(cvals.max()), "{:.1f}")
put("val_ks_min", cv[cv.stat.str.startswith("KS")].num.min(), "{:.2f}"); put("val_ks_max", cv[cv.stat.str.startswith("KS")].num.max(), "{:.2f}")
put("val_ncases", len(cv[cv.stat.str.startswith("KS")]), "{:.0f}")
put("val_k2_cdf", vv("closed form", "max |cdf diff| over 2000 draws"), "{:.0e}")
ak = vc[vc.check.str.startswith("AKM")]
put("val_akm_n", int(ak[ak.stat.str.startswith("instances")].iloc[0].value.split("/")[0]), "{:.0f}")
put("val_akm_skip", int(ak[ak.stat.str.startswith("instances")].iloc[0].value.split("/")[1]), "{:.0f}")
put("val_ref_cond_cov_known", pp(vv("reference cell K=16 n=200 tau=.01 rho=.5 (gauss_known_Sigma)", "coverage")), "{:.0f}")
put("val_ref_cond_cov_est", pp(vv("reference cell K=16 n=200 tau=.01 rho=.5 (bernoulli_est_Sigma)", "coverage")), "{:.0f}")
put("val_ref_cond_width_mean", pp(vv("reference cell K=16 n=200 tau=.01 rho=.5 (gauss_known_Sigma)", "mean width")), "{:.0f}")
put("val_ref_cond_width_med", pp(vv("reference cell K=16 n=200 tau=.01 rho=.5 (gauss_known_Sigma)", "median width")), "{:.0f}")
put("val_ref_hyb_rmse", pp(vv("point estimates minus true score", "hybrid median: rmse")), "{:.1f}")
put("val_ref_cond_rmse", pp(vv("point estimates minus true score", "conditional median: rmse")), "{:.0f}")
put("val_ref_cond_medae", pp(vv("point estimates minus true score", "conditional median: median abs err")), "{:.1f}")
put("val_ref_hyb_medae", pp(vv("point estimates minus true score", "hybrid median: median abs err")), "{:.1f}")
put("val_ref_lead_med", vv("K=16 tau=0.01 rho=0.5 n=200", "median standardised lead (x_k - V-)/se_k"), "{:.2f}")
put("val_ref_lead_lt05", pp(vv("K=16 tau=0.01 rho=0.5 n=200", "share lead < 0.5")), "{:.0f}")
lr = vl[vl.case.str.startswith("reference")]; lb = lr[lr.bin == "[0.0, 0.25)"].iloc[0]
put("lead_ref_share_small", pp(lb.share), "{:.0f}"); put("lead_ref_condmed_err", pp(lb.cond_err_median), "{:.0f}"); put("lead_ref_condmean_err", pp(lb.cond_err_mean), "{:.0f}")
put("lead_ref_condwidth_med", pp(lb.cond_width_median), "{:.0f}"); put("lead_ref_hybwidth", pp(lb.hyb_width_mean), "{:.0f}"); put("lead_ref_hyberr", pp(lb.hyb_err_mean), "{:.0f}")
put("lead_ref_nall_cov", pp(lr[lr.bin == "all"].iloc[0].cond_cov), "{:.0f}")
l5 = vl[vl.case.str.contains("n=1000") & (vl.bin == "all")].iloc[0]; put("lead_clear_n1000_width", pp(l5.cond_width_mean), "{:.0f}")
put("lead_clear_n1000_best", pp(l5.winner_is_truly_best), "{:.0f}")
l5b = vl[vl.case.str.contains("n=500") & (vl.bin == "all")].iloc[0]; put("lead_clear_n500_best", pp(l5b.winner_is_truly_best), "{:.0f}")
rb = pd.read_csv(os.path.join(R, "ranking_equal_budget_summary.csv"))
def rbv(kind, label, tau, col, design="unequal_K4_64", items=400):
    q = rb[(rb.design == design) & (rb.kind == kind) & (rb.label == label) & np.isclose(rb.tau_gen, tau) & (rb["items"] == items)]; assert len(q) == 1, (kind, label, tau); return q.iloc[0][col]
for nm, kind, lab in (("naive", "naive", "insample_400"), ("split", "split", "insample_400"), ("oob", "boot_oob", "insample_400"), ("fresh", "fresh", "fresh_half_400")):
    put(f"rkb_{nm}_big_rep", pp(rbv(kind, lab, 0.0, "big_reported_best")), "{:.0f}"); put(f"rkb_{nm}_kt", rbv(kind, lab, 0.03, "tau_b_mean"), "{:.2f}")
put("rkb_big_true", pp(rbv("naive", "insample_400", 0.0, "big_truly_best")), "{:.0f}"); put("rkb_reps", rb.reps.max(), "{:.0f}")
frl = pd.read_csv(os.path.join(R, "fresh_protocol_real.csv")); KF = int(frl.K.max()); put("fr_real_K", KF, "{:.0f}")
frk = frl[frl.K == KF]
def frr(est, tot, col, nt=None):
    q = frk[(frk.est_name == est) & (frk["items"] == tot)]
    if nt is not None: q = q[q.n_tune == nt]
    assert len(q) == 1, (est, tot, nt); return q.iloc[0][col]
for e in ("naive", "boot_oob", "split", "hybrid"):
    put(f"frr_{e}_200_rmse", pp(frr(e, 200, "rmse"))); put(f"frr_{e}_200_bias", pp(frr(e, 200, "bias")))
put("frr_boot_oob_200_cover", pp(frr("boot_oob", 200, "cover")), "{:.0f}")
put("frr_fresh100_200_rmse", pp(frr("fresh", 200, "rmse", 100))); put("frr_fresh50_200_rmse", pp(frr("fresh", 200, "rmse", 50)))
put("frr_fresh100_200_cover", pp(frr("fresh", 200, "cover", 100)), "{:.0f}"); put("frr_reps", frk.reps.max(), "{:.0f}")
put("frr_boot_oob_400_rmse", pp(frr("boot_oob", 400, "rmse"))); put("frr_fresh200_400_rmse", pp(frr("fresh", 400, "rmse", 200)))

# --- real matrix: Gaussian-max check, iid arm, calibrated generator
gm = pd.read_csv(os.path.join(R, "real_gaussian_max_check.csv"))
put("gm_cells", len(gm), "{:.0f}"); put("gm_maxdiff", pp(gm["diff"].abs().max()), "{:.2f}"); put("gm_z2", (gm.z.abs() > 2).sum(), "{:.0f}")
put("gm_nK", gm.K.nunique(), "{:.0f}"); put("gm_nmax", gm.n.max(), "{:.0f}")
gd = gm[(gm.truth_arm == "disjoint") & (gm.K == KR)].set_index("n")
for n in (50, 100, 200, 400): put(f"gm_pred_n{n}", pp(gd.loc[n, "pred_gap"])); put(f"gm_rep_n{n}", pp(gd.loc[n, "replay_gap"]))
put("gm_relmax", 100 * ((gd.pred_gap - gd.replay_gap) / gd.replay_gap).abs().max(), "{:.0f}")
ri = pd.read_csv(os.path.join(R, "real_summary.csv")); ri = ri[ri.truth_arm == "iid"]
def ri1(n, K, est, col):
    q = ri[(ri.proc == "argmax") & (ri.n == n) & (ri.K == K) & (ri.est_name == est)]; assert len(q) == 1; return q.iloc[0][col]
for n in (50, 200, 400): put(f"real_iid_gap_n{n}", pp(ri1(n, KR, "naive", "bias")))
put("real_iid_cover_n200", pp(ri1(200, KR, "naive", "cover")), "{:.0f}"); put("real_iid_nmax", ri.n.max(), "{:.0f}"); put("real_iid_reps", ri.reps.max(), "{:.0f}")
gc = pd.read_csv(os.path.join(R, "generator_calibration.csv")).set_index("item")
put("gen_rho", gc.loc["latent rho matched to the real phi", "generator"], "{:.2f}")
put("gen_phi_real", gc.loc["mean pairwise phi", "real"], "{:.2f}"); put("gen_phi_min", gc.loc["min pairwise phi", "real"], "{:.2f}"); put("gen_phi_max", gc.loc["max pairwise phi", "real"], "{:.2f}")
put("gen_sditem_real", gc.loc["sd of item-mean accuracy across items", "real"], "{:.3f}"); put("gen_sditem_gen", gc.loc["sd of item-mean accuracy across items", "generator"], "{:.3f}")
put("gen_acc_real", pp(gc.loc["accuracy mean", "real"])); put("gen_zero_real", pp(float(gc.loc["share of items solved by exactly 0 of 60 configs", "real"])), "{:.0f}")
gpf = pd.read_csv(os.path.join(R, "generator_pairwise_fit.csv")).set_index("item")
put("gen_clip", int(float(gpf.loc["tetrachoric R: eigenvalues clipped (count)", "tetrachoric"])), "{:.0f}")
put("gen_pw_err_uni", float(gpf.loc["pairwise phi: max |generator - real| over pairs", "uniform_rho"]), "{:.2f}"); put("gen_pw_err_tet", float(gpf.loc["pairwise phi: max |generator - real| over pairs", "tetrachoric"]), "{:.3f}")
gv = pd.read_csv(os.path.join(R, "generator_vs_real_gap.csv")); gv["rel"] = (gv.gen_gap - gv.real_gap) / gv.real_gap
for g, nm in (("uniform_rho", "uni"), ("tetrachoric", "tet")):
    q = gv[(gv.generator == g) & (gv.K >= 4)]; a = gv[gv.generator == g]
    put(f"gen_{nm}_rel", 100 * q.rel.mean(), "{:+.0f}"); put(f"gen_{nm}_relmin", 100 * q.rel.min(), "{:+.0f}"); put(f"gen_{nm}_relmax", 100 * q.rel.max(), "{:+.0f}")
    put(f"gen_{nm}_z2", (a.z.abs() > 2).sum(), "{:.0f}"); put(f"gen_{nm}_cells", len(a), "{:.0f}")
    q2 = a[(a.n == 200) & (a.K == KR) & (a.truth_arm == "disjoint")]; put(f"gen_{nm}_gap_n200", pp(q2.gen_gap.iloc[0])); put(f"gen_{nm}_real_n200", pp(q2.real_gap.iloc[0]))
pm = pd.read_csv(os.path.join(R, "synthetic_phi_map.csv"))
for r_ in (0.3, 0.5, 0.7, 0.9): put(f"phimap_{int(r_*10)}", pm[np.isclose(pm.m, 0.195) & np.isclose(pm.rho, r_)].phi.iloc[0], "{:.2f}")
put("phimap_m3_r5", pm[np.isclose(pm.m, 0.3) & np.isclose(pm.rho, 0.5)].phi.iloc[0], "{:.2f}")

with open(OUT, "w") as f:
    f.write("% generated by paper/quote_numbers.py from results/*.csv; do not edit. Use as \\N{key}.\n")
    f.write("\\newcommand{\\N}[1]{\\csname num@#1\\endcsname}\n")
    for k, v in sorted(M.items()): f.write("\\expandafter\\gdef\\csname num@%s\\endcsname{%s}\n" % (k, v))
print(len(M), "numbers ->", OUT)
