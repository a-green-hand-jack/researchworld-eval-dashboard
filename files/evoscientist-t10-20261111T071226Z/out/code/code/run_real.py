"""Resampling experiments on real datasets.  Usage: python run_real.py [reps]
Outputs results/real_summary.csv"""
import sys, os, time
os.environ['PYTHONPATH'] = os.path.dirname(os.path.abspath(__file__)) + os.pathsep + os.environ.get('PYTHONPATH', '')
import pandas as pd
from joblib import Parallel, delayed
from real_lib import DATASETS, SMALL, one_config, cached_oracle

if __name__ == "__main__":
    R = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    cfgs = []
    for ds in DATASETS:
        for n in ((50, 100, 200, 500) if ds in SMALL else (50, 100, 200, 500, 1000, 2000)):
            cfgs.append((ds, n, 10000))
    t0 = time.time()
    Parallel(n_jobs=9)(delayed(cached_oracle)(ds) for ds in DATASETS)  # theory inputs, cached
    print('oracle done %.0fs' % (time.time() - t0), flush=True)
    out = Parallel(n_jobs=36)(delayed(one_config)(i, ds, n, N, R) for i, (ds, n, N) in enumerate(cfgs))
    df = pd.DataFrame([r for rows in out for r in rows])
    df.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "real_summary.csv"), index=False)
    print("done", len(df), "rows in %.0fs" % (time.time() - t0))
