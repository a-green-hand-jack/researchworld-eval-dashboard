#!/bin/sh
# Reproduction entrypoint: `sh run.sh data` (network), `sh run.sh <target>` for one experiment, `sh run.sh all` for everything sequentially.
# Targets are independent and can be run as parallel jobs. Raw downloads go to $RAW (outside the repo); processed matrices to data/processed (committed).
cd "$(dirname "$0")"
RAW=${RAW:-/hutian/data}; PY=${PY:-python3}
SC=mean,geomean,harmonic,median,min,pow0.5,pow-0.5,pow-2,pow-5   # trimmed1 (MILP, ~0.7 s per target) only on sampled targets
ORD=borda,condorcet,plurality
WM=wmean0,wmean1,wmean2,wmean3,wmean4
ALLCAPS=ceil,front0,front2,gain5,gain10,gain20,emp95,emp99
mkdir -p logs results

run() { echo "+ $*"; "$@"; }
t=$1
case "$t" in
data)
  $PY src/fetch_ollb.py $RAW/ollb
  $PY src/fetch_helm.py $RAW/helm/v1.13.0
  $PY src/build_data.py $RAW/ollb/train-00000-of-00001.parquet $RAW/helm/v1.13.0 data/processed
  $PY src/ollb_items.py data/processed/ollb_noise.json
  ;;
tests)
  $PY -m pytest -q tests
  ;;
ollb_score)
  $PY src/run_core.py ollb $ALLCAPS $SC all results/ollb_score.csv > logs/ollb_score.log 2>&1
  ;;
ollb_ord_ceil|ollb_ord_front0|ollb_ord_gain10|ollb_ord_emp95)
  cap=${t#ollb_ord_}
  # rank rules on the full leaderboard: head-20 + 40 rank-stratified targets (MILP cost grows with the number of models above the target);
  # Copeland needs M x M pairwise tensors and is run on the top-500 slice only
  $PY src/run_core.py ollb $cap $ORD sample results/ollb_ord_$cap.csv --nsample 40 > logs/ollb_ord_$cap.log 2>&1
  ;;
ollb_wmean)
  $PY src/run_core.py ollb $ALLCAPS $WM all results/ollb_wmean.csv > logs/ollb_wmean.log 2>&1
  ;;
ollb_top500_a)   # score rules and non-Copeland rank rules on the top-500 slice (116 sampled targets); Copeland MILP is ~1 h per cap here, so it runs on gain10 (b) and a 30-target subset at ceil
  $PY src/run_core.py ollb_top500 ceil $SC,$WM,trimmed1,$ORD sample results/ollb_top500_a.csv > logs/ollb_top500_a.log 2>&1
  ;;
ollb_top500_b)
  $PY src/run_core.py ollb_top500 gain10 $SC,$WM,trimmed1,$ORD,copeland sample results/ollb_top500_b.csv > logs/ollb_top500_b.log 2>&1
  $PY src/run_core.py ollb_top500 gain20 $SC,$WM,trimmed1,$ORD sample results/ollb_top500_b2.csv > logs/ollb_top500_b2.log 2>&1   # same rows as the gain20 part of ollb_top500_b.csv
  ;;
ollb_top500_c)
  $PY src/run_core.py ollb_top500 front0,front2,gain5,emp95,emp99 $SC,$WM,trimmed1,$ORD sample results/ollb_top500_c.csv > logs/ollb_top500_c.log 2>&1
  ;;
ollb_top500_cope_ceil)
  $PY src/run_core.py ollb_top500 ceil copeland sample results/ollb_top500_cope_ceil.csv --nsample 10 > logs/ollb_top500_cope_ceil.log 2>&1
  ;;
ollb_variants_score)
  $PY src/run_core.py ollb_nomerge ceil,front0,front2,gain5,gain10,gain20,emp95,emp99 $SC all results/ollb_nomerge_score.csv > logs/ollb_nomerge_score.log 2>&1
  $PY src/run_core.py ollb_raw ceil $SC all results/ollb_raw_score.csv > logs/ollb_raw_score.log 2>&1
  for c in front0 gain10 gain20; do $PY src/run_core.py ollb_raw $c $SC all results/ollb_raw_score_$c.csv > logs/ollb_raw_score_$c.log 2>&1; done
  ;;
ollb_variants_ord)
  $PY src/run_core.py ollb_nomerge ceil,front0,gain10 $ORD sample results/ollb_nomerge_ord.csv --nsample 40 > logs/ollb_nomerge_ord.log 2>&1
  $PY src/run_core.py ollb_raw ceil,front0,gain10 $ORD sample results/ollb_raw_ord.csv --nsample 40 > logs/ollb_raw_ord.log 2>&1
  ;;
helm_main)
  $PY src/run_core.py helm ceil,front0,front2,gain5,gain10,gain20 mean,geomean,harmonic,median,min,$WM,$ORD,copeland all results/helm_main.csv > logs/helm_main.log 2>&1
  ;;
helm_pow)
  $PY src/run_core.py helm ceil,front0,gain10 pow0.5,pow-0.5,pow-2,pow-5 all results/helm_pow.csv > logs/helm_pow.log 2>&1
  ;;
noise_helm)
  $PY src/run_robust.py noise helm mean,geomean,median,min,$ORD gain10 results/helm_noise_gain10.csv --R 100 --ntargets 10 > logs/helm_noise.log 2>&1
  ;;
noise_ollb)
  $PY src/run_robust.py noise ollb_top500 mean,geomean,median,min,$ORD gain10 results/ollb_noise_gain10.csv --R 50 --ntargets 10 > logs/ollb_noise.log 2>&1
  ;;
taskboot)
  $PY src/run_robust.py taskboot helm mean,geomean,median,min,$ORD gain10 results/helm_taskboot_gain10.csv --R 100 --ntargets 10 > logs/helm_taskboot.log 2>&1
  ;;
tasksub)
  $PY src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality gain10 results/helm_tasksub_gain10.csv --R 60 > logs/helm_tasksub.log 2>&1
  $PY src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality ceil results/helm_tasksub_ceil.csv --R 60 > logs/helm_tasksub_ceil.log 2>&1
  ;;
theory)
  $PY src/theory_checks.py > logs/theory_checks.log 2>&1
  ;;
example_plan)
  $PY src/example_plan.py helm 5 gain10 mean,median,plurality,borda,condorcet results/example_plan.csv
  ;;
all)
  for x in tests ollb_score ollb_ord_ceil ollb_ord_front0 ollb_ord_gain10 ollb_ord_emp95 ollb_wmean ollb_top500_a ollb_top500_b ollb_top500_c ollb_top500_cope_ceil ollb_variants_score ollb_variants_ord helm_main helm_pow noise_helm noise_ollb taskboot tasksub theory example_plan; do sh "$0" $x; done ;;
*) echo "unknown target $t"; exit 1 ;;
esac
