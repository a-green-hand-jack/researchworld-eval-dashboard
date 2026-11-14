#!/bin/bash
# OLLB top-500 Copeland rows that hit the 120 s MILP limit (censored): rerun with a 900 s limit, 3 targets per job; merged by code/merge_censored.py.
cd /hutian/repo
python3 - <<'PY' > /tmp/cens_idx.txt
import pandas as pd
d = pd.read_csv("results/variants/var_ollb_top500_copeland.csv"); print(" ".join(map(str, d[d.L1.isna() | d.K.isna()].target_idx.tolist())))
PY
read -a IDX < /tmp/cens_idx.txt
k=0
for ((s=0; s<${#IDX[@]}; s+=3)); do
  ids=$(IFS=,; echo "${IDX[*]:s:3}")
  ht-resource run local-compute --note "copeland top500 censored rerun $k" -- bash -c "cd /hutian/repo && python3 -u code/run_core.py ollb_top500 emp99 copeland idx:$ids results/rerun_censored/copeland_$k.csv --time-limit 900 > logs/cens_copeland_$k.log 2>&1" | grep '"ref"'
  k=$((k+1))
done
