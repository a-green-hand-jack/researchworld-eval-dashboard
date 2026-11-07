#!/usr/bin/env bash
# Reproduce every result file. Order: A and B (parallel); `collect0` (budgets_remove.csv, random_all.csv, influence); then C, D, E, F, G, H
# (independent, distinct outputs, parallel, 2 CPUs each; F-H read budgets_remove.csv); finally `collect` (regressions, tidy tables, merges).
# Usage: bash code/run_all.sh A|B|collect0|C|D|E|F|G|H|collect|all
# Each step appends "<group>,<script + args>,<wall seconds>" to results/runtimes.csv.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONHASHSEED=0
step() {  # step GROUP script args...
  local g=$1; shift
  local t0=$(date +%s)
  python3 -u "$@"
  echo "$g,$*,$(( $(date +%s) - t0 ))" >> results/runtimes.csv
}
case "${1:-all}" in
  A) step A code/s0_base.py
     step A code/s1_run.py --what random --units arena55k,mt_human,mt_gpt4,nba_all,arena55k_top20count,nba_all_top20count
     step A code/s1_run.py --what adv --units arena55k,mt_human,mt_gpt4,nba_all,arena55k_top20count,nba_all_top20count ;;
  B) step B code/s1_run.py --what adv --units nba_seasons ;;
  C) step C code/s2_controls.py --tasks syn,sub,arena6 ;;
  D) step D code/s2_matched.py --human-draws 20 --B 1000
     step D code/s1_exhaustive.py --instances 60 --m 60,80,100 --kmax 5 ;;
  E) step E code/s3_extra.py --what rigging
     step E code/s3_extra.py --what ablation
     step E code/s3_extra.py --what uncert ;;
  E1) step E code/s3_extra.py --what rigging ;;
  E2) step E code/s3_extra.py --what ablation ;;
  E3) step E code/s3_extra.py --what uncert ;;
  F) step F code/s5_cluster.py
     step F code/s5_constrained.py
     step F code/s5_noise.py ;;
  G) step G code/s5_estimator.py
     step G code/s5_published.py
     step G code/s5_restarts.py ;;
  H) step H code/s5_control.py --D 40
     step H code/s5_window.py --part score
     step H code/s5_window.py --part count ;;
  collect0) step collect0 code/s2_collect.py
     step collect0 code/s3_influence.py ;;
  collect) step collect code/s3_models.py --B 2000
     step collect code/s4_export.py
     step collect code/s5_window.py --part merge
     step collect code/s5_window.py --part support
     step collect code/s5_merge.py
     step collect code/s5_zshares.py
     step collect code/s5_oos.py --B 2000 ;;
  all) for g in A B collect0 C D E F G H collect; do bash "$0" $g; done ;;
esac
