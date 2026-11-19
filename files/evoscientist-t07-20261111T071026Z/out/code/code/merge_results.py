"""Merge the partial result files of the (parallelised) main run into results/main.csv.

The main grid was executed as several invocations of run_experiments.py with disjoint seeds
(results are deterministic per seed, so this is equivalent to one `--seeds 30` run):
  a: seeds 0-11 (killed after seed 11 except 3 mmlu_pro tasks)  b: seeds 20-29  c: seeds 12-19
  d: seed 11, mmlu_pro (the 3 tasks missing from a)
"""
import os, sys
import pandas as pd
R = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ALL, OPENLLM

a = pd.read_csv(f"{R}/main_a_snapshot.csv"); a = a[a.seed < 12]
parts = [a] + [pd.read_csv(f"{R}/main_{x}.csv") for x in "bcd"]
df = pd.concat(parts, ignore_index=True)
df = df.drop_duplicates(subset=["dataset", "split", "seed", "n", "method"])
tasks = df[["dataset", "split", "seed"]].drop_duplicates()
exp = sum((3 if d in OPENLLM else 2) for d in ALL) * 30
print("tasks", len(tasks), "expected", exp, "rows", len(df))
assert len(tasks) == exp
df.to_csv(f"{R}/main.csv", index=False)
