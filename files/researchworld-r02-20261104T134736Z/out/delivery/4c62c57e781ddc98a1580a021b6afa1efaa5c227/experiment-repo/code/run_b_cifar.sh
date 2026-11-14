#!/bin/bash
# B-cifar: split-conformal sets on CIFAR-10 CNN softmax (holdout 10k + test 10k pooled, random cal/test splits).
cd "$(dirname "$0")"
for T in 0.5 1.0 2.0; do for nc in 100 1000; do
python3 -u -m cpsimplex.exp_b --config "{\"source\":\"cifar\",\"T\":$T,\"n_cal\":$nc}" --reps 1000 --seed0 0 \
  --tag "B_cifar_T${T}_n${nc}" --out ../results/raw/B_cifar_T${T}_n${nc}.csv | tail -1
done; done
