"""Pick the strongest baseline per (benchmark, protocol) from the sources-only CV tables. usage: best_baseline.py results"""
import glob, sys
import pandas as pd
out = sys.argv[1]
g = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(f"{out}/source_cv/*.csv"))])
best = g.sort_values("rmse").groupby(["bench", "protocol"], as_index=False).first()[["bench", "protocol", "method", "rmse"]]
best.rename(columns={"rmse": "source_cv_rmse"}).to_csv(f"{out}/best_baseline.csv", index=False)
print(best.groupby(["protocol", "method"]).size())
