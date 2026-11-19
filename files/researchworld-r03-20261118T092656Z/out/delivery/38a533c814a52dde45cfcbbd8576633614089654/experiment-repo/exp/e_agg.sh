#!/bin/bash
# aggregation ablation: first-subset score instead of the mean over subsets; same blocks. usage: exp/e_agg.sh FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1 MTEB_SCORE_COL=main_score_first
for s in A2 A1; do for r in $(seq $1 $2); do
  [ -f results/${s}_first/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting $s --rep $r --out results/${s}_first --selectors greedyA,greedyAcomp,greedyGauss,pivqr --methods mean,fa,gcov,ridge --kgrid 1,2,3,5,8,12,20 --no_cluster --n_random_decision 5
done; done
echo "HUTIAN_WAKE: agg finished"
