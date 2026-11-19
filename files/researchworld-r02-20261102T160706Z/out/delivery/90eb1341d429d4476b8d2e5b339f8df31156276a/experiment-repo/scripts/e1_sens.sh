#!/bin/bash
# E1 sensitivity: zero-replacement eps for the Aitchison-type scores, and calibration-set size.
cd "$(dirname "$0")/.."
{
for fam in multinomial rounded dirichlet; do for eps in 0.0001 0.01 0.1; do
  echo "python3 -u scripts/run_e1.py --family $fam --D 5 --hetero 1 --pred linear --reps 100 --eps $eps --out results/e1/sens_eps${eps}_${fam}.csv"
done; done
for fam in dirichlet lognormal; do for n in 30 100 250 2000; do
  echo "python3 -u scripts/run_e1.py --family $fam --D 5 --hetero 1 --pred linear --reps 100 --n_cal $n --out results/e1/sens_ncal${n}_${fam}.csv"
done; done
} | xargs -P 2 -I{} bash -c "{} > /dev/null 2>&1"
echo "HUTIAN_WAKE: sensitivity grid finished"
