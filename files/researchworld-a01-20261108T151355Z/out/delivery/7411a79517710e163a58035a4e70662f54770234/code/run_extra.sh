#!/bin/bash
# Extra jobs after the first delivery (follow-up analyses); to be merged into run_all.sh. One JOB per call, single-threaded.
set -e; cd "$(dirname "$0")"; mkdir -p results logs
OR=borda,condorcet,plurality
case "$1" in
  ollb_ord100_*)  r=${1#ollb_ord100_}; python3 -u src/run_core.py ollb ceil,gain10 $r top100 results/ollb_ord100_$r.csv ;;
  ollb_hstar100_*) r=${1#ollb_hstar100_}; python3 -u src/run_hstar.py ollb $r top100 results/ollb_hstar_ord100_$r.csv ;;
  helm_eps1)      python3 -u src/run_core.py helm ceil,gain10 mean,geomean,median,min,borda,condorcet,plurality all results/helm_eps1e0.csv --eps 1.0 ;;
  ollb_eps1)      python3 -u src/run_core.py ollb ceil,gain10 mean,median,min all results/ollb_eps1e0.csv --eps 1.0 ;;
  helm_tasksub_eps1) python3 -u src/run_robust.py tasksub helm mean,median,min,borda,plurality gain10 results/helm_tasksub_gain10_eps1e0.csv --R 50 --sizes 5,9,17,33,57 --eps 1.0 ;;
  helm_tasksub_eps1e-1) python3 -u src/run_robust.py tasksub helm mean,median,min,borda,plurality gain10 results/helm_tasksub_gain10_eps1e-1.csv --R 50 --sizes 5,9,17,33,57 --eps 0.1 ;;
  *) echo "unknown job $1" >&2; exit 99 ;;
esac
