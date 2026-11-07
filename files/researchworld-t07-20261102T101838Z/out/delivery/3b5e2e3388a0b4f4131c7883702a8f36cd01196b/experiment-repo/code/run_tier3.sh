#!/bin/bash
# Rank / regularisation ablation of the proposed estimator on the core benchmarks. usage: bash run_tier3.sh BENCH OUTDIR
set -e
B=$1; OUT=$2; mkdir -p $OUT
P=random+mean,strat+lowrank_k2,strat+lowrank_k4,strat+lowrank,strat+lowrank_k16,strat+lowrank_k32,strat+lowrank_dr_k2,strat+lowrank_dr_k4,strat+lowrank_dr,strat+lowrank_dr_k16,strat+lowrank_dr_k32,strat+lowrank_eb_k2,strat+lowrank_eb_k4,strat+lowrank_eb,strat+lowrank_eb_k16,strat+lowrank_eb_k32
for K in random extrap; do
  F=$OUT/${B}_rank_${K}.parquet
  [ -f $F ] || python3 -W ignore run_experiment.py $B $K 20 $F --pipelines $P --tag _rank
done
echo "HUTIAN_WAKE: tier3 done $B"
