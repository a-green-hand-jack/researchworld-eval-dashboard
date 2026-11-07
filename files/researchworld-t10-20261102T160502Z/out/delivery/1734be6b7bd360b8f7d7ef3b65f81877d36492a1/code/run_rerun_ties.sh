#!/bin/bash
# After fixing the binned calibrator for tied predictions (side="left"; src/estimators.py), the three datasets with
# tied/discrete predictor values are re-run with identical seeds; other datasets/methods are unchanged by the fix.
cd "$(dirname "$0")"
python3 -u src/sim.py --datasets forest ballots plankton --R 1000 --out results/sim_real_ties.csv --raw results/raw_real
python3 -u src/sim.py --datasets plankton --shift --R 1000 --out results/sim_plankton_shift.csv --raw results/raw_shift
