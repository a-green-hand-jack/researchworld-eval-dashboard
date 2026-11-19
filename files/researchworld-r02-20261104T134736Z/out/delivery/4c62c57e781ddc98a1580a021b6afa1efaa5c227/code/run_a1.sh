#!/bin/bash
# A1/A3 grid on simplex-valued targets. Usage: run_a1.sh TAG REPS 'JSON-config' (see launch_a1.sh for the list)
TAG=$1; REPS=$2; CFG=$3
cd "$(dirname "$0")"
python3 -u -m cpsimplex.exp_a --config "$CFG" --reps $REPS --seed0 1000 --tag "$TAG" --out ../results/raw/${TAG}.csv | tail -1
