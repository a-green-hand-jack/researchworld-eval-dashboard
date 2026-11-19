#!/bin/bash
# Minimal reproduction path: from the processed score matrices (data/processed, shipped) to the primary-cap grid, the feasibility
# frontier, the paired rule comparisons and the rank-stratum summaries (F1-F3, T2, T3, T4), without the robustness and variant runs.
# Writes only under $OUT (default results_min/); `python3 code/check_minimal.py $OUT` compares it with the shipped results/.
# Wall-clock and CPU seconds per step are appended to $OUT/times.csv.
set -euo pipefail
OUT=${OUT:-results_min}; mkdir -p $OUT/runs $OUT/summary
T="python3 code/timed.py"; TC=$OUT/times.csv
$T tests $TC -- python3 -m pytest -q code/tests
$T theory_check $TC -- python3 code/theory_check.py $OUT/theory_check.csv
$T ollb_primary_closed $TC -- python3 code/run_core.py ollb emp99 mean,median,min,geomean,harmonic,pow-2 all $OUT/runs/ollb_primary_closed.csv
$T ollb_ordinal_top50 $TC -- python3 code/run_core.py ollb emp99 borda,condorcet,plurality top50 $OUT/runs/ollb_primary_ordinal_top50.csv
$T helm_primary $TC -- python3 code/run_core.py helm emp99T mean,median,min,geomean,harmonic,borda,condorcet,plurality all $OUT/runs/helm_primary.csv
$T assemble $TC -- python3 code/assemble_core.py $OUT/runs $OUT --partial
$T summaries $TC -- bash -c "python3 code/summarize.py $OUT/core_ollb.csv $OUT/summary/summary_ollb && python3 code/summarize.py $OUT/core_helm.csv $OUT/summary/summary_helm \
  && python3 code/frontier.py $OUT/core_ollb.csv $OUT/summary/frontier_ollb.csv && python3 code/frontier.py $OUT/core_helm.csv $OUT/summary/frontier_helm.csv \
  && python3 code/paired.py $OUT/core_ollb.csv $OUT/summary/paired_ollb.csv && python3 code/paired.py $OUT/core_helm.csv $OUT/summary/paired_helm.csv"
python3 code/check_minimal.py $OUT
