"""Compare a re-run with the stored results: python3 check_subset.py RERUN_DIR STORED_RUNS_CSV [...]
Collects RERUN_DIR (tidy table), matches runs on run_id with the stored tables and prints the difference of the sustained
t_fit99 / t_gen99 (steps). Exit status 1 if any matched run differs by more than TOL steps (default 0: runs are deterministic on one machine)."""
import subprocess, sys, os
import pandas as pd
TOL = float(os.environ.get("TOL", 0))
here = os.path.dirname(os.path.abspath(__file__))
rerun = sys.argv[1]
subprocess.run([sys.executable, os.path.join(here, "collect.py"), rerun, rerun + "_collected"], check=True, stdout=subprocess.DEVNULL)
new = pd.read_csv(rerun + "_collected_runs.csv")
old = pd.concat([pd.read_csv(f) for f in sys.argv[2:]]).drop_duplicates("run_id")
m = new.merge(old, on="run_id", suffixes=("_new", "_old"))
bad = 0
for r in m.itertuples():
    df, dg = r.t_fit99_s_new - r.t_fit99_s_old, r.t_gen99_s_new - r.t_gen99_s_old
    fine = (abs(df) <= TOL or (pd.isna(df))) and (abs(dg) <= TOL or pd.isna(dg))
    same_na = pd.isna(r.t_gen99_s_new) == pd.isna(r.t_gen99_s_old)
    ok = fine and same_na
    bad += not ok
    print(f"{'OK ' if ok else 'DIFF'} {r.model_new} d={r.width_new} seed={r.seed_new}: t_fit99 {r.t_fit99_s_old} -> {r.t_fit99_s_new}, t_gen99 {r.t_gen99_s_old} -> {r.t_gen99_s_new}")
print(f"{len(m)} runs matched, {bad} differ (tolerance {TOL} steps)")
sys.exit(1 if bad else 0)
