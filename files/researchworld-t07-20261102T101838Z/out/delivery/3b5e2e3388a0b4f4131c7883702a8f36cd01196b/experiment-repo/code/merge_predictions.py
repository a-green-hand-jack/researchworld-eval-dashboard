"""Concatenate the shard files of a run directory into one parquet table and collect per-shard timings.
usage: python merge_predictions.py SHARD_DIR OUT.parquet OUT_timing.csv"""
import sys, glob, json, os
import pandas as pd
d, out, tout = sys.argv[1:4]
fs = sorted(glob.glob(os.path.join(d, "*.parquet")))
pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True).to_parquet(out, compression="zstd")
rows = []
for f in fs:
    j = json.load(open(f + ".json"))
    for k, v in j["timing"].items():
        rows.append(dict(shard=os.path.basename(f), step=k, seconds=v, models_raw=j["info"]["M_raw"], items=j["info"]["N"], reps=j["args"]["reps"]))
pd.DataFrame(rows).to_csv(tout, index=False)
