"""Summaries of the synthetic study into results/*.csv. usage: make_synth_results.py WORKDIR RESULTSDIR"""
import sys, glob, numpy as np, pandas as pd, warnings; warnings.filterwarnings("ignore")
from run_grid import summarize; from synth import make_pool; from theory import predict_gap
W, R = sys.argv[1], sys.argv[2]
F = ["f_kind", "f_n", "f_K", "f_tau", "f_rho", "f_m", "f_proc", "f_eps", "f_leak", "f_outlier"]
# (2) plan grid
fs = sorted(glob.glob(f"{W}/syn3/*.parquet")); df = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
df["f_cell"] = df.tag
s = summarize(df, groupcols=tuple(F + ["est_name"])).reset_index()
s["is_reference"] = (s.f_kind == "ofat") & (s.f_n == 200) & (s.f_K == 16) & (s.f_tau == 0.01) & (s.f_rho == 0.5) & (s.f_m == 0.3) & (s.f_proc == "argmax") & (s.f_eps == 0) & (s.f_leak == 0)
s.to_csv(f"{R}/synth_plan_summary.csv", index=False); print("plan cells", s.groupby(F).ngroups)
# (1) theory prediction on a grid
rows = []
for tau in (0.0, 0.005, 0.01, 0.03):
    for rho in (0.0, 0.3, 0.5, 0.6, 0.9):
        Y = make_pool(128, 20000, m=0.3, tau=tau, rho=rho, seed=7)
        for n in (50, 100, 200, 500, 1000, 2000):
            for K in (1, 2, 4, 8, 16, 32, 64, 128):
                g, se = predict_gap(Y, n, K, M=5000, seed=1)
                rows.append(dict(tau=tau, rho=rho, m=0.3, n=n, K=K, pred_gap=g, pred_gap_mc_se=se))
th = pd.DataFrame(rows)
emp = s[(s.est_name == "naive") & (s.f_proc == "argmax") & (s.f_eps == 0) & (s.f_leak == 0) & (s.f_outlier == 0) & (s.f_m == 0.3)][["f_tau", "f_rho", "f_n", "f_K", "bias", "bias_se", "reps"]]
emp.columns = ["tau", "rho", "n", "K", "emp_gap", "emp_gap_mc_se", "emp_reps"]
th.merge(emp, on=["tau", "rho", "n", "K"], how="left").to_csv(f"{R}/synth_theory_prediction.csv", index=False)
# (3) comparisons
c = pd.read_parquet(f"{W}/syn/synth2_compare.parquet")
c["err_diff"] = c.dhat - c.true_delta; c["fp"] = c.claim & (c.true_delta <= 0); c["wrong_sign"] = c.claim & (c.true_delta < 0)
cs = c.groupby(["tau", "KA", "KB", "n", "est_name"]).agg(claim=("claim", "mean"), false_claim=("fp", "mean"), wrong_sign=("wrong_sign", "mean"),
        mean_reported_diff=("dhat", "mean"), mean_true_diff=("true_delta", "mean"), bias_diff_se=("err_diff", "sem"), mean_reported_diff_se=("dhat", "sem"), reps=("claim", "size")).reset_index()
cs["bias_diff"] = cs.mean_reported_diff - cs.mean_true_diff
cs["claim_se"] = np.sqrt(cs.claim * (1 - cs.claim) / cs.reps); cs.to_csv(f"{R}/synth_compare_summary.csv", index=False)
# (4) ladder
try:
    l = pd.read_parquet(f"{W}/syn/ladder.parquet"); summarize(l, groupcols=("tau", "proc", "n", "K", "est_name")).reset_index().to_csv(f"{R}/synth_ladder_summary.csv", index=False)
except Exception as e: print("ladder", e)
