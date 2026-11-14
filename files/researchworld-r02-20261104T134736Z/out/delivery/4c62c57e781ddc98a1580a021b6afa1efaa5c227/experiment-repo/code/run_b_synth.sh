#!/bin/bash
# B-synth: probability-vector classifiers with known true label law; grid over Dirichlet concentration (task hardness),
# classifier sharpness tau (tau<1 under-, >1 over-confident) and logit noise.
cd "$(dirname "$0")"
for beta in 0.1 0.3 1.0; do for tau in 0.5 1.0 2.0; do for noise in 0.0 1.0; do for nc in 100 1000; do
python3 -u -m cpsimplex.exp_b --config "{\"source\":\"synth\",\"K\":10,\"beta\":$beta,\"tau\":$tau,\"noise\":$noise,\"n_cal\":$nc,\"N\":20000}" \
  --reps 500 --seed0 0 --tag "B_synth_b${beta}_t${tau}_s${noise}_n${nc}" --out ../results/raw/B_synth_b${beta}_t${tau}_s${noise}_n${nc}.csv | tail -1
done; done; done; done
