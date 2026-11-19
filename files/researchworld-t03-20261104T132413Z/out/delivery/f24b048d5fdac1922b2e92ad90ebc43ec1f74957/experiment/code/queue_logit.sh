#!/bin/bash
# log-odds sensitivity cells: queue_logit.sh "dataset model" ...
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$(dirname "$0")/.."
mkdir -p logs
ALL="$*"
for c in "$@"; do
  set -- $c
  python3 -u code/run_cell.py $1 $2 --output logit --stages ref,kernel,perm,retrain 2>&1 | grep --line-buffered -v -i warn >> logs/$1_logit__$2.log
done
echo "HUTIAN_WAKE: logit queue finished: $ALL"
