#!/bin/bash
# E2 (CIFAR-10 hard labels) and E3 (CIFAR-10H soft labels) grids on the small-CNN logits.
cd "$(dirname "$0")/.."
L12=results/e23/cnn_logits_ep12.npy; L2=results/e23/cnn_logits_ep2.npy
{
echo "python3 -u scripts/run_e23.py --e 2 --logits $L12 --T 1 --n_cal 1000 --reps 200 --out results/e23/e2_ep12_T1_n1000.csv"
echo "python3 -u scripts/run_e23.py --e 2 --logits $L2 --T 1 --n_cal 1000 --reps 200 --out results/e23/e2_ep2_T1_n1000.csv"
for T in 0.5 2.0; do echo "python3 -u scripts/run_e23.py --e 2 --logits $L12 --T $T --n_cal 1000 --reps 200 --out results/e23/e2_ep12_T${T}_n1000.csv"; done
for n in 100 500 5000; do echo "python3 -u scripts/run_e23.py --e 2 --logits $L12 --T 1 --n_cal $n --reps 200 --out results/e23/e2_ep12_T1_n${n}.csv"; done
echo "python3 -u scripts/run_e23.py --e 3 --logits $L12 --T 1 --n_cal 1000 --reps 100 --out results/e23/e3_ep12_T1_n1000.csv"
echo "python3 -u scripts/run_e23.py --e 3 --logits $L2 --T 1 --n_cal 1000 --reps 100 --out results/e23/e3_ep2_T1_n1000.csv"
echo "python3 -u scripts/run_e23.py --e 3 --logits $L12 --T 1 --n_cal 300 --reps 100 --out results/e23/e3_ep12_T1_n300.csv"
} | xargs -P 2 -I{} bash -c "{} > /dev/null 2>&1"
echo "HUTIAN_WAKE: E2/E3 grid finished"
