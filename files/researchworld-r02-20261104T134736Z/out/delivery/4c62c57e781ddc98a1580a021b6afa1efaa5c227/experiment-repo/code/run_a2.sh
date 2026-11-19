#!/bin/bash
# A2: calibration-size sweep, no volume (coverage law / conditional coverage vs n_cal). Usage: run_a2.sh KIND NCAL REPS
KIND=$1; NC=$2; REPS=${3:-2000}
cd "$(dirname "$0")"
python3 -u -m cpsimplex.exp_a --config "{\"kind\":\"$KIND\",\"K\":3,\"hetero\":0.5,\"n_cal\":$NC,\"n_tr\":500,\"n_te\":2000,\"alpha\":0.1,\"volume\":false}" \
  --reps $REPS --seed0 50000 --tag "A2_${KIND}_n${NC}" --out ../results/raw/A2_${KIND}_n${NC}.csv
