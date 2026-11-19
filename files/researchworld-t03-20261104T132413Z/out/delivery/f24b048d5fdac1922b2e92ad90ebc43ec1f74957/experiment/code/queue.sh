#!/bin/bash
# usage: queue.sh "dataset model" ...   (runs the cells sequentially, one process, single thread)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$(dirname "$0")/.."
mkdir -p logs
ALL="$*"
for c in "$@"; do
  set -- $c
  python3 -u code/run_cell.py $1 $2 2>&1 | grep -v -i warn >> logs/$1__$2.log
done
echo "HUTIAN_WAKE: queue finished: $ALL"
