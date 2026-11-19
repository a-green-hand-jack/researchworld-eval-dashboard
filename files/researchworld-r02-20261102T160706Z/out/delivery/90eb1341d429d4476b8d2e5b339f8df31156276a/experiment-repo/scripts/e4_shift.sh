#!/bin/bash
cd "$(dirname "$0")/.."
mkdir -p results/e4
for fam in dirichlet lognormal multinomial; do echo "python3 -u scripts/run_shift.py --family $fam --reps 100 --out results/e4/shift_${fam}.csv"; done | xargs -P 2 -I{} bash -c "{} >/dev/null 2>&1"
echo "HUTIAN_WAKE: E4 shift finished"
