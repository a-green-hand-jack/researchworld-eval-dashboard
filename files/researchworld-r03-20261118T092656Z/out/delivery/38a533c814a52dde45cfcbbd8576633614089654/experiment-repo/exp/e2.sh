#!/bin/bash
# E2 (group transfer, cost-aware budgets) and E0 (leakage ablation). usage: exp/e2.sh FIRST LAST
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
F=$1; L=$2
run() { out=$1; shift; for r in $(seq $F $L); do [ -f results/$out/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --out results/$out --rep $r "$@"; done; }
G=greedyAT,greedyAcomp,greedyGauss,central,pivqr,leverage,fwdreg
for t in Retrieval Clustering Classification; do
  run A1_tgt$t --setting A1 --target_group $t --selectors $G --methods mean,fa,gcov,ridge --kgrid 1,2,3,5,8,12,20,30 --no_cluster --n_random_decision 5
done
for t in Classification Clustering; do
  run A2_tgt$t --setting A2 --target_group $t --selectors $G --methods mean,fa,gcov,ridge --kgrid 1,2,3,5,8,12 --no_cluster --n_random_decision 5
done
run A1_cost --setting A1 --cost --selectors greedyAcost,greedyGaussCost,greedyAcomp,greedyGauss,central,pivqr --methods mean,fa,gcov --kgrid 1,2,3,4,5,6,8,10,12,15,20,30,40,60,80 --no_cluster --n_random_decision 5
run A2_cost --setting A2 --cost --selectors greedyAcost,greedyGaussCost,greedyAcomp,greedyGauss,central,pivqr --methods mean,fa,gcov --kgrid 1,2,3,4,5,6,8,10,12,15,20 --no_cluster --n_random_decision 5
for s in A1 A2; do
  run ${s}_leak --setting $s --leak --selectors greedyA,greedyAcomp,greedyGauss,pivqr --methods mean,fa,gcov,ridge --kgrid 1,2,3,5,8,12,20 --no_cluster --n_random_decision 5
done
echo "HUTIAN_WAKE: e2 $F-$L finished"
