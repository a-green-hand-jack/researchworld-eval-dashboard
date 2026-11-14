"""C5 table: for each rule and each ex-ante top-10 challenger (initial mean rank 2-11) on OLLB, does the minimum investment fit inside the
empirical fine-tune-gain envelope (emp95 / emp99)? One row per (cap, rule, target): feasible flag, K, L1, Linf (inf = infeasible).
Usage: python3 src/c5_table.py OUT IN1.csv [IN2.csv ...]"""
import sys, numpy as np, pandas as pd
out, ins = sys.argv[1], sys.argv[2:]
d = pd.concat([pd.read_csv(f) for f in ins], ignore_index=True)
d = d[d.cap.isin(["emp95", "emp99"]) & d.rank_mean.between(2, 11)].copy()
d["feasible"] = np.isfinite(d.L1)
d = d[["cap", "rule", "target", "rank_mean", "feasible", "K", "L1", "Linf"]].sort_values(["cap", "rule", "rank_mean"])
d.to_csv(out, index=False)
s = d.groupby(["cap", "rule"]).agg(n_targets=("target", "nunique"), feasible_share=("feasible", "mean"),
                                    K_median=("K", lambda x: np.median(x[np.isfinite(x)]) if np.isfinite(x).any() else np.nan),
                                    L1_median=("L1", lambda x: np.median(x[np.isfinite(x)]) if np.isfinite(x).any() else np.nan)).reset_index()
s.to_csv(out.replace(".csv", "_summary.csv"), index=False); print(s.round(2).to_string())
