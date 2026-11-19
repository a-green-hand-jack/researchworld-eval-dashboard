#!/bin/bash
# A4: covariate shift (x_0 mean shift delta), unweighted vs weighted split conformal.
cd "$(dirname "$0")"
for k in dirichlet logisticnormal; do for d in 0.0 0.5 1.0 1.5; do
python3 -u -m cpsimplex.exp_a45 --exp a4 --config "{\"kind\":\"$k\",\"K\":3,\"hetero\":1.0,\"delta\":$d}" --reps 500 --seed0 7000 \
  --tag "A4_${k}_delta${d}" --out ../results/raw/A4_${k}_delta${d}.csv | tail -1
done; done
