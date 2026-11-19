#!/bin/bash
# P4 needs the cost-ignorant counterpart of the cost-aware A-criterion (greedyA, same criterion without the 1/cost): same folds/seeds as E2 cost runs.
# usage: exp/e2b.sh FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
F=$1; L=$2
run() { out=$1; shift; for r in $(seq $F $L); do [ -f results/$out/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --out results/$out --rep $r "$@"; done; }
run A1_costA --setting A1 --cost --selectors greedyA --methods mean,fa --kgrid 1,2,3,4,5,6,8,10,12,15,20,30,40,60,80 --no_cluster --n_random_decision 5
run A2_costA --setting A2 --cost --selectors greedyA --methods mean,fa --kgrid 1,2,3,4,5,6,8,10,12,15,20 --no_cluster --n_random_decision 5
echo "HUTIAN_WAKE: e2b $F-$L finished"
