#!/bin/sh
# runs all stages sequentially, retrying a stage (resumable) up to 3 times
for s in E1 E4 E3 E2 E5; do
  for t in 1 2 3; do
    python3 src/run_main.py $s ${NJOBS:-28} && break
  done
done
echo ALLDONE
