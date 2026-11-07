#!/bin/bash
# delta sensitivity (zero-replacement constant) on the rounded Dirichlet and logistic-normal configs; same seeds as A1.
cd "$(dirname "$0")"
M='"methods":["euc","l1","hell","aitch","kl_fwd","kl_rev","aitch/n","dirnll"]'
for d in 0.01 0.000001; do
python3 -u -m cpsimplex.exp_a --config "{\"kind\":\"dirichlet\",\"K\":3,\"hetero\":0.5,\"a\":1.6094379,\"digits\":2,\"delta\":$d,$M}" --reps 100 --seed0 1000 --tag A1d_dirichlet_delta$d --out ../results/raw/A1d_dirichlet_delta$d.csv | tail -1
python3 -u -m cpsimplex.exp_a --config "{\"kind\":\"logisticnormal\",\"K\":3,\"hetero\":0.5,\"s\":0.0,\"digits\":2,\"delta\":$d,$M}" --reps 100 --seed0 1000 --tag A1d_logisticnormal_delta$d --out ../results/raw/A1d_logisticnormal_delta$d.csv | tail -1
done
