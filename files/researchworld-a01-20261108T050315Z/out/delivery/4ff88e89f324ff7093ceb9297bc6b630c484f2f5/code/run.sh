#!/usr/bin/env bash
# Reproduction entrypoint: ./run.sh <target> [<target> ...]   (targets: see the case list; 'all' runs everything sequentially)
# `data` needs network; every other target is offline and independent (can run in parallel as separate processes). Seeds: --seed 0 everywhere.
set -e; cd "$(dirname "$0")"
PY=python3; R=results
CLOSED=mean,geomean,harmonic,median,min,pow0.5,pow-0.5,pow-2,pow-5
ORD=borda,condorcet,plurality
CAPS=ceil,front0,front2,gain5,gain10,gain20

t_main_ollb_closed() {
  $PY src/run_core.py ollb $CAPS $CLOSED all $R/ollb_closed.csv
}
t_main_ollb_closed_emp() {
  $PY src/run_core.py ollb emp95,emp99 $CLOSED all $R/ollb_closed_emp.csv
}
t_main_ollb_ord_a() {
  $PY src/run_core.py ollb ceil,front0 $ORD,trimmed1 sample $R/ollb_ord_a.csv
}
# front2 (headline cap) was run as three parallel jobs after the sequential ord_a job was stopped at the end of front0; same sample, same eps
t_main_ollb_ord_front2() {
  $PY src/run_core.py ollb front2 borda sample $R/ollb_ord_front2_borda.csv
  $PY src/run_core.py ollb front2 condorcet sample $R/ollb_ord_front2_condorcet.csv
  $PY src/run_core.py ollb front2 plurality,trimmed1 sample $R/ollb_ord_front2_plurality_trimmed1.csv
}
# one front0 Borda L1 solve (target 3591) returned no incumbent in the old 120 s run; re-solved with the 600 s limit
t_main_ollb_ord_resolve() { $PY src/run_core.py ollb front0 borda idx3591 $R/ollb_ord_resolve_front0_borda.csv; }
t_main_ollb_ord_b() {
  $PY src/run_core.py ollb gain5,gain10,gain20 $ORD,trimmed1 sample $R/ollb_ord_b.csv
}
t_main_ollb_ord_c() {
  $PY src/run_core.py ollb emp95,emp99 $ORD,trimmed1 sample $R/ollb_ord_c.csv
}
t_main_helm_pow() {
  $PY src/run_core.py helm $CAPS pow0.5,pow-0.5,pow-2,pow-5 all $R/helm_pow.csv
}
t_main_helm() {
  $PY src/run_core.py helm $CAPS mean,geomean,harmonic,median,min,borda,condorcet,plurality all $R/helm_main.csv
}
t_rob_slices_a() {
  for d in ollb_nomerge ollb_top500; do
    $PY src/run_core.py $d ceil,front0,gain10 $CLOSED all $R/slice_${d}_closed.csv
    $PY src/run_core.py $d ceil,front0,gain10 $ORD sample $R/slice_${d}_ord.csv
  done
}
t_rob_slices_b() {
  $PY src/run_core.py ollb_raw ceil,front0,gain10 $CLOSED all $R/slice_ollb_raw_closed.csv
  $PY src/run_core.py ollb_raw ceil,gain10 borda,condorcet sample $R/slice_ollb_raw_ord.csv --nsample 60     # rank-invariant check, bounded compute
}
t_rob_noise_helm() {
  $PY src/run_robust.py noise helm mean,geomean,median,min,borda,condorcet,plurality gain10 $R/helm_noise_gain10.csv --R 100
}
t_rob_noise_ollb() {
  $PY src/run_robust.py noise ollb mean,geomean,median,min,borda,condorcet,plurality gain10 $R/ollb_noise_gain10.csv --R 100
}
t_rob_taskboot() {
  $PY src/run_robust.py taskboot ollb mean,geomean,median,min,borda,condorcet,plurality gain10 $R/ollb_taskboot_gain10.csv --R 200
  $PY src/run_robust.py taskboot helm mean,geomean,median,min,borda,condorcet,plurality gain10 $R/helm_taskboot_gain10.csv --R 100
}
t_rob_tasksub() {
  $PY src/run_robust.py tasksub helm mean,geomean,median,min,borda,condorcet,plurality gain10 $R/helm_tasksub_gain10.csv --R 100
  $PY src/run_robust.py tasksub helm mean,geomean,median,min,borda,condorcet,plurality ceil $R/helm_tasksub_ceil.csv --R 100
}
# standardised OLLB variants (scale-free; addresses unit dependence of min/median/means/pooled L1). z: per-task z-score, caps in SD units
# (gain10 = 10 raw points converted per task, sgain<h> = h SD for every task); pct: rank percentile (positive, so all score rules apply)
ZCAPS=ceil,front0,gain10,sgain0.5,sgain1
t_std_z_closed() {
  $PY src/run_core.py ollb_z $ZCAPS mean,median,min all $R/ollbz_closed.csv
}
t_std_z_ord() {
  $PY src/run_core.py ollb_z ceil,sgain1 borda,condorcet sample $R/ollbz_ord.csv --nsample 60     # rank-invariant check, bounded compute
}
t_std_pct_closed() {
  $PY src/run_core.py ollb_pct ceil,front0,sgain10,sgain25 $CLOSED all $R/ollbpct_closed.csv
}
t_time_milp() { $PY src/time_milp.py $R/time_milp_ollb.csv; }
t_summaries() {
  for f in ollb_closed ollb_ord_a ollb_ord_b ollb_ord_c helm_main helm_pow; do
    $PY src/summarize.py $R/$f.csv $R/summary_$f > /dev/null
  done
}
t_test() { $PY -m pytest -q tests; }
t_main() { t_main_ollb_closed; t_main_ollb_closed_emp; t_main_ollb_ord_a; t_main_ollb_ord_front2; t_main_ollb_ord_resolve; t_main_ollb_ord_b; t_main_ollb_ord_c; t_main_helm_pow; }
t_robust() { t_std_z_closed; t_std_z_ord; t_std_pct_closed; t_time_milp; t_rob_slices_a; t_rob_slices_b; t_rob_noise_helm; t_rob_noise_ollb; t_rob_taskboot; t_rob_tasksub; }
t_all() { t_main; t_robust; t_summaries; }
for t in "$@"; do "t_$t"; done
