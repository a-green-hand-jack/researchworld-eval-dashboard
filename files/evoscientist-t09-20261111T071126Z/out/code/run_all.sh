#!/bin/sh
# Reproduce every number, table and figure of the paper.
# Expected wall-clock on 40 shared CPU cores: ~3-4 h (simulation) + ~15 min (analysis); see README.md.
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
JOBS=${JOBS:-36}
sh data/get_data.sh
# --- simulations (each writes results/<EXP>_reps.csv.gz, _graphs.csv, _configs.csv)
python3 code/run_experiments.py E1 --jobs $JOBS      # variance law
python3 code/run_experiments.py E2 --jobs $JOBS --drop-last 1   # bias floor (the n=64000 point is not run, see README)
python3 code/run_experiments.py E3 --jobs $JOBS      # designs x estimators
python3 code/run_experiments.py E5 --jobs $JOBS      # mechanism mismatch
python3 code/run_experiments.py E6 --jobs $JOBS      # CI coverage
python3 code/run_experiments.py E7 --jobs $JOBS      # degree-correlated baselines
# --- analysis: tables/*.csv and figures/*.pdf; stdout is kept in results/*_analysis.log
for e in E1 E2 E3 E5 E6 E7; do python3 code/analyze_$e.py > results/${e}_analysis.log 2>&1; done
python3 code/make_paper_tables.py
