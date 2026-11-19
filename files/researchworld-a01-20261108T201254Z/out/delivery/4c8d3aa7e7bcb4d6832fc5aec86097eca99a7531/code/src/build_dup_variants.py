"""Alternative duplicate-name rules for the OLLB matrix (external-review request #6.3a).
Usage: python3 src/build_dup_variants.py OLLB_PARQUET OUTDIR
The pinned `contents` table has 79 full names that occur twice (always as a float16 and a bfloat16 submission; 36 of the pairs share a
submission date). The delivered matrix keeps the best-scoring variant (src/build_data.py). Here the same table is reduced with
  first  : earliest `Submission Date`, ties broken by file order (first row)
  latest : latest `Submission Date`, ties broken by file order (last row)
  worst  : the lowest-scoring variant (the opposite bracket of 'best')
Each output has the columns of ollb6.csv, is written as OUTDIR/ollb6_dup_<rule>.csv.gz, and is used through MTI_OLLB_CSV (src/mti/data.py).
"""
import sys, pathlib, json
import pandas as pd, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
pq, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
TASKS = ["IFEval", "BBH", "MATH Lvl 5", "GPQA", "MUSR", "MMLU-PRO"]
meta = ["fullname", "Precision", "Type", "Architecture", "Hub License", "#Params (B)", "Flagged", "Merged", "MoE",
        "Official Providers", "Base Model", "Generation", "Submission Date", "Average ⬆️"]
d = pd.read_parquet(pq)[meta + TASKS + [t + " Raw" for t in TASKS]].copy()
d["_row"] = np.arange(len(d)); d["_date"] = pd.to_datetime(d["Submission Date"])
ref = pd.read_csv(pathlib.Path(__file__).resolve().parents[1] / "data" / "processed" / "ollb6.csv")
info = {}
for rule in ("first", "latest", "worst"):
    if rule == "first": s = d.sort_values(["_date", "_row"], ascending=[True, True], kind="stable")
    elif rule == "latest": s = d.sort_values(["_date", "_row"], ascending=[False, False], kind="stable")
    else: s = d.sort_values(["Average ⬆️", "_row"], ascending=[True, True], kind="stable")
    k = s.drop_duplicates("fullname", keep="first")
    k = k.sort_values("Average ⬆️", ascending=False, kind="stable").drop(columns=["_row", "_date"])   # same final order convention as build_data.py
    k.columns = [c.replace(" ⬆️", "") for c in k.columns]; k = k.reset_index(drop=True)
    k.to_csv(out / f"ollb6_dup_{rule}.csv.gz", index=False)
    info[rule] = dict(rows=len(k), rows_that_differ_from_best=int((k.set_index("fullname").loc[ref.fullname, "Precision"].values != ref.Precision.values).sum()))
    print(rule, info[rule])
json.dump(info, open(out / "dup_variants_manifest.json", "w"), indent=1)
