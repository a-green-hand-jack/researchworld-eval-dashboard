"""T0-to-T1 fit check: gap of the real-LLM replay (T1) vs the synthetic world (T0) at the same (n, K), exhaustive search, base_acc 0.3, all T0 rho/tau
cells available (T0 rho 0.6 <-> binary item-correlation r ~0.39, rho 0.9 <-> r ~0.70; the matrix has r 0.57-0.68 and tau_prob_est 0.017-0.023,
tau 0.05/0.1 probit units <-> 0.017/0.035 on the probability scale). T0 columns are long format.
usage: t0_vs_t1.py -> results/t0_vs_t1_gap.csv"""
import pandas as pd
R = "/hutian/repo/results"
t0 = pd.read_csv(f"{R}/summary_gap_t0.csv"); t1 = pd.read_csv(f"{R}/summary_gap_t1.csv")
t0 = t0[(t0.procedure == "exhaustive") & (t0.base_acc == 0.3) & t0.tau.isin([0.05, 0.1]) & ~t0.cell_id.str.contains("leak=1|m3")]
t1 = t1[(t1.procedure == "exhaustive") & ~t1.cell_id.str.contains("m3")]
t1 = t1.set_index(["n", "K"])[["gap_mean", "gap_mcse", "gap_block_se", "gap_theory_from_matrix"]].add_prefix("t1_")
a = t0.set_index(["n", "K"])[["tau", "rho", "gap_mean", "gap_mcse"]].rename(columns={"gap_mean": "t0_gap_mean", "gap_mcse": "t0_gap_mcse", "tau": "t0_tau", "rho": "t0_rho"})
out = a.join(t1, how="inner").reset_index().sort_values(["t0_rho", "t0_tau", "n", "K"])
out["t0_over_t1"] = out.t0_gap_mean / out.t1_gap_mean
out.to_csv(f"{R}/t0_vs_t1_gap.csv", index=False); print(out.round(4).to_string())
