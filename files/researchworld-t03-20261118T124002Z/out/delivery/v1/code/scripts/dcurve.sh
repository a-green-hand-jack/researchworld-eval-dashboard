#!/bin/bash
# usage: dcurve.sh DATASET DSUB OUTPUT MODEL... : build tables (seed 0 only for arrhythmia, 0-2 otherwise) and run the R=20 grid for each cell of the d-curve
cd "$(dirname "$0")/.."
export PYTHONPATH=.
DS=$1; DSUB=$2; OUT=$3; shift 3
SEEDS="0 1 2"; [ "$DS" = arrhythmia ] && SEEDS="0"
for MD in "$@"; do for s in $SEEDS; do
  python3 -u scripts/build_cell.py --dataset $DS --model $MD --seed $s --d_sub $DSUB --output $OUT > /dev/null || continue
  C=$(python3 -c "from shapaudit import cells; print(cells.cell_id('$DS', $DSUB, '$MD', $s, '$OUT'))")
  python3 -u scripts/run_estimators.py --cell $C --R 20 --tag R20 && python3 scripts/summarize_cell.py --cell $C --tag R20 | tail -1
done; done
