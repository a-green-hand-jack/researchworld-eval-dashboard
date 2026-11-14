#!/bin/bash
# usage: queue_stages.sh STAGES "dataset model" ...   (extra stages, one process, single thread)
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd "$(dirname "$0")/.."
mkdir -p logs
ST=$1; shift
ALL="$*"
for c in "$@"; do
  set -- $c
  python3 -u code/run_cell.py $1 $2 --stages $ST 2>&1 | grep --line-buffered -v -i warn >> logs/$1__$2__extra.log
done
echo "HUTIAN_WAKE: extra stages $ST finished: $ALL"
