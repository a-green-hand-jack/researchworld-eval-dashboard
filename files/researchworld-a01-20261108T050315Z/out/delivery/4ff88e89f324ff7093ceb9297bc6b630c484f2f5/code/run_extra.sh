#!/usr/bin/env bash
# Second half of the reproduction entrypoint: feasibility/baseline quantities, eps sensitivity, HELM empirical-gain caps, theory checks,
# consolidation into results/tidy and results/tables.   Usage: ./run_extra.sh <target> [<target> ...]   (run.sh holds the main experiments)
# Targets are independent and offline (except none), each a separate process; `consolidate` must run last.
set -e; cd "$(dirname "$0")"
PY=python3; R=results
CAPS=ceil,front0,front2,gain5,gain10,gain20,emp95,emp99
SCORE=mean,geomean,harmonic,median,min,pow0.5,pow-0.5,pow-2,pow-5,trimmed1
ORD=borda,condorcet,plurality
HEAD=mean,geomean,median,min,borda,condorcet
t_helm_empm() { $PY src/run_core.py helm empm95,empm99 mean,geomean,harmonic,median,min,borda,condorcet,plurality all $R/helm_empm.csv; }
t_x_helm() { $PY src/run_extra.py helm ceil,front0,front2,gain5,gain10,gain20,empm95,empm99 $SCORE,$ORD all $R/extra_helm.csv; }
t_x_ollb_score() { $PY src/run_extra.py ollb $CAPS $SCORE all $R/extra_ollb_score.csv; }
t_x_ollb_ord() { $PY src/run_extra.py ollb $CAPS $ORD sample $R/extra_ollb_ord.csv; }
t_x_ollbz() {
  $PY src/run_extra.py ollb_z ceil,front0,gain10,sgain0.5,sgain1 mean,median,min,trimmed1 all $R/extra_ollbz_score.csv
  $PY src/run_extra.py ollb_z ceil,front0,gain10,sgain0.5,sgain1 $ORD sample $R/extra_ollbz_ord.csv
}
t_x_ollbpct() {
  $PY src/run_extra.py ollb_pct ceil,front0,sgain10,sgain25 $SCORE all $R/extra_ollbpct_score.csv
  $PY src/run_extra.py ollb_pct ceil,front0,sgain10,sgain25 $ORD sample $R/extra_ollbpct_ord.csv
}
t_eps_helm() { for e in 0 0.01 0.1; do $PY src/run_core.py helm ceil,front2,empm95 $HEAD all $R/eps_helm_$e.csv --eps $e; done; }
t_eps_ollb_score() { for e in 0 0.01 0.1; do $PY src/run_core.py ollb ceil,front2,emp95 mean,geomean,median,min all $R/eps_ollb_score_$e.csv --eps $e; done; }
t_eps_ollb_ord() { for e in 0.01 0.1; do $PY src/run_core.py ollb ceil,front2,emp95 borda,condorcet sample $R/eps_ollb_ord_$e.csv --eps $e --nsample 40; done; }
t_theory() { $PY src/theory_checks.py $R/theory_checks.csv; }
t_consolidate() { $PY src/consolidate.py; }
for t in "$@"; do "t_$t"; done
