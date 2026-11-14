"""Synthetic experiments with known truth.  Usage: python run_synth.py [reps]
Outputs: results/synth_summary.csv"""
import sys, os, time
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ.get('PYTHONPATH', '')
import pandas as pd
from joblib import Parallel, delayed
from synth_lib import make_scenarios, one_config

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    S = make_scenarios()
    cfgs = []
    for name, sc in S.items():
        for n in (50, 100, 200, 500, 1000):
            cfgs.append((name, n, 10000))
    for name in ("herm60", "lognorm1", "logistic3"):
        for N in (200, 1000, 100000):
            cfgs.append((name, 200, N))
    t0 = time.time()
    out = Parallel(n_jobs=36)(delayed(one_config)(i, nm, n, N, R) for i, (nm, n, N) in enumerate(cfgs))
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "synth_summary.csv"), index=False)
    print("done", len(df), "rows in %.0fs" % (time.time() - t0))
