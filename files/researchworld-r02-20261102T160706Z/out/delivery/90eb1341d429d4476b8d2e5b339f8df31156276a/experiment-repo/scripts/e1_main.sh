#!/bin/bash
# Main E1 grid: 4 families x 2 heteroscedasticity x 3 dims x 2 predictors, 100 replicates each; 2 parallel workers.
cd "$(dirname "$0")/.."
for fam in dirichlet lognormal multinomial rounded; do for D in 3 5 10; do for het in 0 1; do for pred in linear rf; do
  f=results/e1/main_${fam}_D${D}_h${het}_${pred}.csv
  [ -f $f ] || echo "python3 -u scripts/run_e1.py --family $fam --D $D --hetero $het --pred $pred --reps 100 --out $f > results/e1/log_${fam}_D${D}_h${het}_${pred}.txt 2>&1"
done; done; done; done | xargs -P 2 -I{} bash -c "{}"
echo "HUTIAN_WAKE: E1 main finished"
