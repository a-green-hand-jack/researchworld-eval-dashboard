"""Summaries of the equal-budget protocol study. usage: make_fresh_results.py WORKDIR RESULTSDIR   (WORKDIR/fresh from run_fresh.py cells|rank|real)
 fresh_protocol_summary.csv   synthetic cells (tau x K x rho; m = .3): per protocol / est_name / n_tune / m_fresh / items: true accuracy of the shipped config (mu_ship), bias vs that row's own truth,
                              rmse, median abs error, coverage, width, regret, reps. protocol = insample (items = n_tune) or fresh (tune on n_tune, report on m_fresh new items; items = n_tune + m_fresh).
 fresh_protocol_real.csv      same on the real correctness matrix (disjoint arm; K = 1, 2, 4, all cached configs)
 ranking_equal_budget_summary.csv  ranking of tuned systems at equal item budgets (kind = naive/boot_oob/simul/split/fresh)."""
import sys, glob, pandas as pd
from run_fresh import summarize_fresh
W, R = sys.argv[1:3]
d = pd.concat([pd.read_parquet(f) for f in sorted(glob.glob(f"{W}/fresh/fresh_tau*.parquet"))], ignore_index=True)
s = summarize_fresh(d, extra=("tau", "rho", "m")); s.to_csv(f"{R}/fresh_protocol_summary.csv", index=False); print(len(s), "synthetic rows")
import os
real_files = sorted(glob.glob(f"{W}/fresh/real_k*.parquet"), key=lambda p: int(p.split("real_k")[1].split(".")[0]))   # the file with the most configurations
if real_files:
    r = pd.read_parquet(real_files[-1]); sr = summarize_fresh(r); sr.to_csv(f"{R}/fresh_protocol_real.csv", index=False); print(len(sr), "real rows")
if os.path.exists(f"{W}/fresh/rank_eq.csv"):
    q = pd.read_csv(f"{W}/fresh/rank_eq.csv"); q.to_csv(f"{R}/ranking_equal_budget_summary.csv", index=False)
