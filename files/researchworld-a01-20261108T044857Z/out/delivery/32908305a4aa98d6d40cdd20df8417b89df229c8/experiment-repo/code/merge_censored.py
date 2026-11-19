"""Replace censored (NaN L1 or K) rows of a run file by their reruns with a longer MILP time limit.
Usage: python3 code/merge_censored.py BASE.csv RERUN_GLOB OUT.csv   (rows matched on cap, rule, target_idx; a rerun row that is still censored keeps NaN)"""
import sys, glob, pandas as pd
base = pd.read_csv(sys.argv[1]); re = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(sys.argv[2]))])
key = ["cap", "rule", "target_idx"]
m = base.merge(re[key], on=key, how="left", indicator=True); assert (m._merge == "both").sum() == len(re)
out = pd.concat([base.merge(re[key], on=key, how="left", indicator=True).query("_merge=='left_only'").drop(columns="_merge"), re], ignore_index=True).sort_values("target_idx")
out.to_csv(sys.argv[3], index=False)
print(f"{len(re)} rows replaced; still censored: {int(out.L1.isna().sum())} (L1), {int(out.K.isna().sum())} (K) of {len(out)}")
