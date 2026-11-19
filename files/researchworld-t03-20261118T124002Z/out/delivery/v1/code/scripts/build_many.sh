#!/bin/bash
# usage: build_many.sh DATASET MODEL [D_SUB|full] [OUTPUT] : builds seeds 0,1,2
cd "$(dirname "$0")/.."
DS=$1; MD=$2; DSUB=${3:-full}; OUT=${4:-prob}
for s in 0 1 2; do
  if [ "$DSUB" = "full" ]; then python3 -u scripts/build_cell.py --dataset $DS --model $MD --seed $s --output $OUT > /dev/null;
  else python3 -u scripts/build_cell.py --dataset $DS --model $MD --seed $s --d_sub $DSUB --output $OUT > /dev/null; fi
done
