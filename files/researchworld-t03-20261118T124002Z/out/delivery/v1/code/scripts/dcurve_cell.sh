#!/bin/bash
# usage: dcurve_cell.sh DATASET DSUB|full OUTPUT MODEL SEED : (re)build one d-curve cell (cached tables are kept) and run its R=20 grid + summary
cd "$(dirname "$0")/.."
export PYTHONPATH=.
DS=$1; DSUB=$2; DARG="--d_sub $2"; [ "$2" = full ] && DARG=""; [ "$2" = full ] && DSUB=None; OUT=$3; MD=$4; s=$5
python3 -u scripts/build_cell.py --dataset $DS --model $MD --seed $s $DARG --output $OUT > /dev/null || exit 1
C=$(python3 -c "from shapaudit import cells; print(cells.cell_id('$DS', $DSUB, '$MD', $s, '$OUT'))")
python3 -u scripts/run_estimators.py --cell $C --R 20 --tag R20 && python3 scripts/summarize_cell.py --cell $C --tag R20 | tail -1
