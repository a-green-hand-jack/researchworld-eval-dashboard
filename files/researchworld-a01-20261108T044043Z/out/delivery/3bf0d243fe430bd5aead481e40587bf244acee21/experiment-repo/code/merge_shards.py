"""Concatenate `run_core.py --shard k/m` outputs into one run file, rows ordered by (cap, rule, target_idx) as an unsharded run would
write them.   Usage: python3 code/merge_shards.py OUT.csv SHARD0.csv SHARD1.csv ..."""
import sys, pandas as pd
d = pd.concat([pd.read_csv(f) for f in sys.argv[2:]], ignore_index=True)
assert not d.duplicated(["cap", "rule", "target_idx"]).any(), "overlapping shards"
caps = list(dict.fromkeys(d.cap)); rules = list(dict.fromkeys(d.rule))   # first-seen order of the (identical) shard layouts
d = d.assign(_c=d.cap.map(caps.index), _r=d.rule.map(rules.index)).sort_values(["_c", "_r", "target_idx"], kind="stable").drop(columns=["_c", "_r"])
d.to_csv(sys.argv[1], index=False); print(len(d), "rows ->", sys.argv[1])
