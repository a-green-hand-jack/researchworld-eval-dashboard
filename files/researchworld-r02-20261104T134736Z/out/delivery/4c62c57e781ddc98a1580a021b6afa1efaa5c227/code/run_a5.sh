#!/bin/bash
# A5: split vs CV+ (5-fold) vs jackknife+ (n<=100) at small total sample size n. Usage: run_a5.sh KIND
K=$1
cd "$(dirname "$0")"
for n in 30 50 100 200; do for mode in split cv+ jackknife+; do
  if [ "$mode" = "jackknife+" ] && [ $n -gt 100 ]; then continue; fi
python3 -u -m cpsimplex.exp_a45 --exp a5 --config "{\"kind\":\"$K\",\"K\":3,\"hetero\":0.5,\"n\":$n,\"mode\":\"$mode\"}" --reps 100 --seed0 9000 \
  --tag "A5_${K}_n${n}_${mode}" --out ../results/raw/A5_${K}_n${n}_${mode}.csv | tail -1
done; done
