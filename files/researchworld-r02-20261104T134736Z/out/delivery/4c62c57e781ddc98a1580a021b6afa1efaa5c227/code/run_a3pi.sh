#!/bin/bash
# A3 plug-in Prop. 2: re-run of the A3hs configurations (same seeds) additionally saving per-cell estimated coverage and cell sizes.
cd "$(dirname "$0")"
run() { python3 -u -m cpsimplex.exp_a --config "$2" --reps 1000 --seed0 1000 --tag "$1" --out ../results/raw/$1.csv | tail -1; }
case $1 in
0) run A3pi_dirichlet_K3_h1.0_linear '{"kind":"dirichlet","K":3,"hetero":1.0,"form":"linear","volume":false,"halfsplit":true,"cells":true}';;
1) run A3pi_dirichlet_K5_h0.5_linear '{"kind":"dirichlet","K":5,"hetero":0.5,"volume":false,"halfsplit":true,"cells":true}';;
2) run A3pi_dirichlet_K10_h0.5_linear '{"kind":"dirichlet","K":10,"hetero":0.5,"volume":false,"halfsplit":true,"cells":true}';;
3) run A3pi_logisticnormal_K3_h1.0_linear '{"kind":"logisticnormal","K":3,"hetero":1.0,"form":"linear","volume":false,"halfsplit":true,"cells":true}';;
4) run A3pi_logisticnormal_K5_h0.5_linear '{"kind":"logisticnormal","K":5,"hetero":0.5,"volume":false,"halfsplit":true,"cells":true}';;
5) run A3pi_logisticnormal_K10_h0.5_linear '{"kind":"logisticnormal","K":10,"hetero":0.5,"volume":false,"halfsplit":true,"cells":true}';;
6) run A3pi_dirichlet_K3_h0.5_linear '{"kind":"dirichlet","K":3,"hetero":0.5,"form":"linear","volume":false,"halfsplit":true,"cells":true}';;
7) run A3pi_logisticnormal_K3_h0.5_linear '{"kind":"logisticnormal","K":3,"hetero":0.5,"form":"linear","volume":false,"halfsplit":true,"cells":true}';;
esac
