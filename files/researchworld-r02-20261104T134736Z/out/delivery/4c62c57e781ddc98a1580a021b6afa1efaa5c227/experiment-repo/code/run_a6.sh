#!/bin/bash
# A6 mean-model misspecification: true logit mean has a quadratic part (nl), the fitted mean model is linear in x. K=3, h=0.5, volume computed.
cd "$(dirname "$0")"
run() { python3 -u -m cpsimplex.exp_a --config "$2" --reps 200 --seed0 1000 --tag "$1" --out ../results/raw/$1.csv | tail -1; }
case $1 in
0) run A6_dirichlet_K3_h0.5_nl0.5 '{"kind":"dirichlet","K":3,"hetero":0.5,"nl":0.5}';;
1) run A6_dirichlet_K3_h0.5_nl1.0 '{"kind":"dirichlet","K":3,"hetero":0.5,"nl":1.0}';;
2) run A6_logisticnormal_K3_h0.5_nl0.5 '{"kind":"logisticnormal","K":3,"hetero":0.5,"nl":0.5}';;
3) run A6_logisticnormal_K3_h0.5_nl1.0 '{"kind":"logisticnormal","K":3,"hetero":0.5,"nl":1.0}';;
esac
