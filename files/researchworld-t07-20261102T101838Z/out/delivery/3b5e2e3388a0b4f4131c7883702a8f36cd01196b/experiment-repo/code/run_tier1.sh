#!/bin/bash
# Tier-1 final run for one benchmark: both splits, 30 seeds. Resumable (skips finished outputs).
# usage: bash run_tier1.sh BENCH OUTDIR
set -e
B=$1; OUT=$2; mkdir -p $OUT
P=const,random+mean,strat+mean,random+cal,anchor+anchor,anchor+irt,random+irt,random+lowrank,strat+lowrank,random+lowrank_dr,omp+ridge,strat+lowrank_dr,strat+lowrank_eb
for K in random extrap; do
  F=$OUT/${B}_${K}.parquet
  [ -f $F ] || python3 -W ignore run_experiment.py $B $K 30 $F --pipelines $P
done
echo "HUTIAN_WAKE: tier1 done $B"
