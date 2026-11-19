"""Per-cell x method reliability pass/fail (plan section 6), one-sided under/over-coverage counts, theory-vs-simulation disagreements and
margin-based false-claim rates. usage: make_cell_tables.py SYN3_DIR SYN_DIR RESULTS_DIR   (SYN3_DIR: per-cell parquets of run_synth3; SYN_DIR: synth2_compare.parquet)
Pass rule (plan section 6): |bias| <= max(2 * bias_se, 0.005)  AND  coverage inside the 95% Monte-Carlo band 0.95 +- 1.96 sqrt(.95*.05/reps).
under = coverage below the band, over = coverage above the band."""
import sys, glob, os, numpy as np, pandas as pd
from run_grid import derive
syn3, syn, R = sys.argv[1:4]
S = pd.read_csv(f"{R}/synth_plan_summary.csv"); cell = ["f_kind", "f_n", "f_K", "f_tau", "f_rho", "f_m", "f_proc", "f_eps", "f_leak", "f_outlier"]
S["bias_tol"] = np.maximum(2 * S.bias_se, 0.005); S["bias_pass"] = S.bias.abs() <= S.bias_tol
hw = 1.96 * np.sqrt(0.95 * 0.05 / S.reps); S["band_lo"] = 0.95 - hw; S["band_hi"] = 0.95 + hw
S["under_cover"] = S.cover < S.band_lo; S["over_cover"] = S.cover > S.band_hi; S["cover_pass"] = ~(S.under_cover | S.over_cover); S["pass"] = S.bias_pass & S.cover_pass
S["bias_dir"] = np.where(S.bias_pass, "", np.where(S.bias > 0, "over-report", "under-report"))
S[cell + ["is_reference", "est_name", "reps", "bias", "bias_se", "bias_tol", "bias_pass", "cover", "band_lo", "band_hi", "under_cover", "over_cover", "cover_pass", "pass", "bias_dir", "width"]]\
    .to_csv(f"{R}/synth_cell_pass_fail.csv", index=False)
rows = []
for sub, d in [("all", S)] + [(k, S[S.f_kind == k]) for k in ("ofat", "inter", "stress")]:
    g = d.groupby("est_name")
    t = g.agg(cells=("pass", "size"), pass_both=("pass", "sum"), bias_fail=("bias_pass", lambda x: (~x).sum()), bias_over_report=("bias_dir", lambda x: (x == "over-report").sum()),
              bias_under_report=("bias_dir", lambda x: (x == "under-report").sum()), cover_fail=("cover_pass", lambda x: (~x).sum()), under_cover=("under_cover", "sum"),
              over_cover=("over_cover", "sum"), median_cover=("cover", "median"), min_cover=("cover", "min"), median_width=("width", "median")).reset_index(); t.insert(0, "subset", sub); rows.append(t)
pd.concat(rows).to_csv(f"{R}/synth_pass_fail_by_method.csv", index=False)

# theory vs simulation disagreement (naive argmax gap), direction
T = pd.read_csv(f"{R}/synth_theory_prediction.csv").dropna(subset=["emp_gap"]); T["diff"] = T.pred_gap - T.emp_gap; T["se"] = np.hypot(T.pred_gap_mc_se, T.emp_gap_mc_se)
T["z"] = T["diff"] / T.se; T["differs_2se"] = T.z.abs() > 2; T["direction"] = np.where(T.z > 0, "theory above simulation", "theory below simulation")
T.to_csv(f"{R}/synth_theory_vs_sim.csv", index=False)

# margin-based claim rates (claim test: (est - base)/dse > 1.645; truth difference = mu_selected - mu_baseline(config 0))
rows = []
for f in sorted(glob.glob(f"{syn3}/*.parquet")):
    d = derive(pd.read_parquet(f)); d["claim"] = (d.est - d.base) / d.dse > d.z; d["td"] = d.mu - d.mu_base
    g = d.groupby("est_name")
    for en, x in g:
        r = {c: x[c].iloc[0] for c in ["f_kind", "f_n", "f_K", "f_tau", "f_rho", "f_m", "f_proc", "f_eps", "f_leak", "f_outlier"]}; r.update(est_name=en, reps=len(x), claim=x.claim.mean(), mean_true_diff=x.td.mean())
        for nm, mg in (("0", 0.0), ("0.5pp", .005), ("1pp", .01)):
            bad = x.td <= mg; r[f"false_claim_{nm}"] = (x.claim & bad).mean(); r[f"n_true_diff_le_{nm}"] = int(bad.sum()); r[f"claim_given_le_{nm}"] = x.claim[bad].mean() if bad.any() else np.nan
        r["wrong_sign_claim"] = (x.claim & (x.td < 0)).mean(); rows.append(r)
pd.DataFrame(rows).to_csv(f"{R}/synth_claim_margin_summary.csv", index=False)
# unequal-budget comparisons of two tuned systems (A better than B, one-sided z = 1.645 on the reported difference)
c = pd.read_parquet(f"{syn}/synth2_compare.parquet")
rows = []
for (tau, KA, KB, n, en), x in c.groupby(["tau", "KA", "KB", "n", "est_name"]):
    r = dict(tau=tau, KA=KA, KB=KB, n=n, est_name=en, reps=len(x), claim=x.claim.mean(), mean_true_diff=x.true_delta.mean())
    for nm, mg in (("0", 0.0), ("0.5pp", .005), ("1pp", .01)):
        bad = x.true_delta <= mg; r[f"false_claim_{nm}"] = (x.claim & bad).mean(); r[f"claim_given_le_{nm}"] = x.claim[bad].mean() if bad.any() else np.nan
    r["wrong_sign_claim"] = (x.claim & (x.true_delta < 0)).mean(); rows.append(r)
pd.DataFrame(rows).to_csv(f"{R}/synth_compare_margin_summary.csv", index=False)
print("ok")
