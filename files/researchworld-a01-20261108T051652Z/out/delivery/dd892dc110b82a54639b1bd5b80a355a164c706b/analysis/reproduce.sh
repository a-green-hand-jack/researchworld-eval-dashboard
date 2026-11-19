#!/usr/bin/env bash
# Reproduction entrypoint: ./reproduce.sh TARGET   (seeds fixed, default 0). `data` needs network; everything else is offline.
# Targets are independent (run in parallel). Wall-clock estimates are for one 2-CPU container on a loaded shared host.
set -euo pipefail
main() {
cd "$(dirname "$0")"
PY="python3 -u"
CLOSED=mean,geomean,harmonic,median,min       # exact + fast: every model is a target
TRIM=trimmed1                                  # MILP, ~1 s per target: rank-stratified sample of targets
ORD=borda,condorcet,plurality
CAPS_ALL=ceil,front0,front2,gain5,gain10,gain20
mkdir -p results logs
case "${1:-help}" in
  data)  # network; rebuilds data/processed byte-identically (checked against data/processed/manifest.json) except ollb_noise.json, rewritten in place
    $PY src/fetch_helm.py data/raw/helm && $PY src/fetch_ollb.py data/raw/ollb &&
    $PY src/build_data.py data/raw/ollb/train-00000-of-00001.parquet data/raw/helm data/processed && $PY src/ollb_items.py data/processed/ollb_noise.json ;;
  test)  python3 -m pytest tests -q ;;                                                                 # ~30 s
  core_helm)         $PY src/run_core.py helm $CAPS_ALL mean,geomean,harmonic,median,min,borda,condorcet,plurality all results/helm_main.csv ;;   # ~15 min
  core_ollb_closed)  $PY src/run_core.py ollb $CAPS_ALL,emp95,emp99 $CLOSED all results/ollb_closed.csv ;;
  core_ollb_trim)    $PY src/run_core.py ollb $CAPS_ALL,emp95,emp99 $TRIM sample results/ollb_trim.csv --nsample 40 ;;
  core_ollb_ord_a)   $PY src/run_core.py ollb ceil,front0,front2 $ORD sample results/ollb_ord_a.csv --nsample 40 ;;
  core_ollb_ord_b)   $PY src/run_core.py ollb gain5,gain10,gain20 $ORD sample results/ollb_ord_b.csv --nsample 40 ;;
  core_ollb_ord_c)   $PY src/run_core.py ollb emp95,emp99 $ORD sample results/ollb_ord_c.csv --nsample 40 ;;
  variants)          # score-normalisation (raw) and leaderboard-slice (no merged models / top-500) variants of OLLB
    for d in ollb_raw ollb_nomerge ollb_top500; do
      $PY src/run_core.py $d ceil,front0,gain10 $CLOSED all results/var_${d}_closed.csv
      $PY src/run_core.py $d ceil,front0,gain10 $ORD sample results/var_${d}_ord.csv --nsample 40
    done ;;
  robust_helm_noise)   $PY src/run_robust.py noise helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_noise_gain10.csv --R 100 ;;
  robust_ollb_noise)   $PY src/run_robust.py noise ollb mean,geomean,median,min,borda,plurality gain10 results/ollb_noise_gain10.csv --R 100 ;;
  robust_helm_taskboot) $PY src/run_robust.py taskboot helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_taskboot_gain10.csv --R 100 ;;
  robust_helm_tasksub) $PY src/run_robust.py tasksub helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_tasksub_gain10.csv --R 50 ;;
  core_helm_emp)     # HELM has no base/fine-tune pairs: caps transferred from the OLLB MMLU-PRO gain quantiles (see src/mti/data.py, hemp<q>)
    $PY src/run_core.py helm hemp95,hemp99 mean,geomean,harmonic,median,min,borda,condorcet,plurality all results/helm_emp.csv ;;
  eps01)             # tie-margin check (plan D5): eps = 0.1 instead of 1e-3
    $PY src/run_core.py helm ceil,gain10 mean,geomean,harmonic,median,min,borda,condorcet,plurality all results/eps01_helm.csv --eps 0.1
    $PY src/run_core.py ollb ceil,gain10,emp95 $CLOSED all results/eps01_ollb_closed.csv --eps 0.1
    $PY src/run_core.py ollb ceil,gain10,emp95 $ORD sample results/eps01_ollb_ord.csv --nsample 40 --eps 0.1 ;;
  loto_*)            $PY src/run_loto.py ${1#loto_} results/loto_${1#loto_}.csv ;;   # leave-one-task-out on OLLB, e.g. loto_0 ... loto_5 (independent)
  uniform_helm)      $PY src/run_uniform.py results/ustar_helm.csv results/helm_main.csv results/helm_emp.csv ;;
  uniform_ollb_closed) $PY src/run_uniform.py results/ustar_ollb_closed.csv results/ollb_closed.csv ;;
  uniform_ollb_ord)  $PY src/run_uniform.py results/ustar_ollb_ord.csv results/ollb_ord_a.csv results/ollb_ord_b.csv results/ollb_ord_c.csv results/ollb_trim.csv ;;
  uniform_var)       $PY src/run_uniform.py results/ustar_var.csv results/var_ollb_*_closed.csv results/var_ollb_*_ord.csv ;;
  l2)                $PY src/run_l2.py results/l2_cost.csv results/helm_main.csv results/ollb_closed.csv results/var_ollb_*_closed.csv ;;
  weighted)          $PY src/run_weighted.py helm ceil,front0,gain10,hemp95 results/weighted_helm.csv --draws 200
                     $PY src/run_weighted.py ollb ceil,front0,gain10,emp95 results/weighted_ollb.csv --draws 200 ;;
  copeland_helm)     $PY src/run_copeland.py helm ceil,front0,front2,gain5,gain10,gain20,hemp95 results/copeland_helm.csv --time-limit 300 ;;
  theory)            $PY src/theory_checks.py results/theory_checks.csv && $PY src/theory_table.py results/theory_pred.csv ;;
  summaries)         bash src/summaries.sh ;;
  *) echo "targets: data test theory core_helm core_helm_emp core_ollb_closed core_ollb_trim core_ollb_ord_{a,b,c} variants eps01 robust_{helm_noise,ollb_noise,helm_taskboot,helm_tasksub} loto_{0..5} uniform_{helm,ollb_closed,ollb_ord,var} l2 weighted copeland_helm summaries"; exit 1 ;;
esac
}
main "$@"
exit $?
