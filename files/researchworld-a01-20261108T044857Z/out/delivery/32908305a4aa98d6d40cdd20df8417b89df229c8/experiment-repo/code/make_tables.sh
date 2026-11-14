#!/bin/bash
# Tidy core tables, summaries, feasibility frontier and paired comparisons. Run from the repository root after the runs.
set -euo pipefail
R=results; mkdir -p $R/summary
python3 code/assemble_core.py $R/runs $R
for f in $R/robust/rob_*.csv; do python3 code/summarize_robust.py $f $R/summary/summary_$(basename $f); done
python3 code/summarize.py $R/core_ollb.csv $R/summary/summary_ollb
python3 code/summarize.py $R/core_helm.csv $R/summary/summary_helm
python3 code/summarize.py $R/core_ollb.csv $R/summary/summary_ollb rank_rule
python3 code/summarize.py $R/core_helm.csv $R/summary/summary_helm rank_rule
python3 code/frontier.py $R/core_ollb.csv $R/summary/frontier_ollb.csv
python3 code/frontier.py $R/core_helm.csv $R/summary/frontier_helm.csv
python3 code/paired.py $R/core_ollb.csv $R/summary/paired_ollb.csv
python3 code/paired.py $R/core_helm.csv $R/summary/paired_helm.csv
python3 code/summarize_variants.py $R $R/summary/summary_variants.csv
python3 code/uniform_baseline.py $R/core_ollb.csv ollb $R/uniform_baseline_ollb.csv $R/summary/summary_uniform_baseline_ollb.csv
python3 code/uniform_baseline.py $R/core_helm.csv helm $R/uniform_baseline_helm.csv $R/summary/summary_uniform_baseline_helm.csv
python3 code/feasible_counts.py $R/robust/rob_helm_tasksub_emp99T.csv $R/summary/summary_rob_helm_tasksub_feasible_counts.csv
python3 code/feasible_counts.py $R/robust/rob_helm_tasksubcommon_emp99T.csv $R/summary/summary_rob_helm_tasksubcommon_feasible_counts.csv
