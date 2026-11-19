#!/bin/bash
# Jobs for the follow-up analyses on cap composition, convex cost, margin robustness and cluster bootstrap. One JOB per call, single-threaded.
set -e; cd "$(dirname "$0")"; mkdir -p results logs
case "$1" in
  ollb_emp_restricted) python3 -u src/run_core.py ollb emp95,emp99,emp95r,emp99r mean,median,min top30 results/ollb_emp_restricted.csv ;;
  helm_emp_restricted) python3 -u src/run_core.py helm emp95,emp99,emp95r,emp99r mean,median,min top30 results/helm_emp_restricted.csv ;;
  helm_eps2)  python3 -u src/run_core.py helm ceil,gain10 mean,median,min all results/helm_eps2e0.csv --eps 2.0 ;;
  helm_eps8)  python3 -u src/run_core.py helm ceil,gain10 mean,median,min all results/helm_eps8e0.csv --eps 8.0 ;;
  ollb_eps2)  python3 -u src/run_core.py ollb ceil,gain10 mean,median,min top100 results/ollb_eps2e0.csv --eps 2.0 ;;
  ollb_eps8)  python3 -u src/run_core.py ollb ceil,gain10 mean,median,min top100 results/ollb_eps8e0.csv --eps 8.0 ;;
  cluster_bootstrap) python3 -u src/cluster_bootstrap.py ;;
  convex_cost) python3 -u src/convex_cost.py ;;
  *) echo "unknown job $1" >&2; exit 99 ;;
esac
