#!/bin/bash
# Tier-2 runs for one benchmark (resumable). usage: bash run_tier2.sh BENCH OUTDIR [openllm|helm]
set -e
B=$1; OUT=$2; FAM=$3; mkdir -p $OUT
T1=const,random+mean,strat+mean,random+cal,anchor+anchor,anchor+irt,random+irt,random+lowrank,strat+lowrank,random+lowrank_dr,omp+ridge,strat+lowrank_dr,strat+lowrank_eb
run() { F=$OUT/$1.parquet; shift; [ -f $F ] || python3 -W ignore run_experiment.py "$@" $F; }
# selector x estimator factorial (Q7), both splits
for K in random extrap; do
  F=$OUT/${B}_fact_${K}.parquet
  [ -f $F ] || python3 -W ignore run_experiment.py $B $K 20 $F --factorial --tag _fact
done
# family hold-out (open-LLM benchmarks only: model-name prefixes verified there)
if [ "$FAM" = openllm ]; then
  F=$OUT/${B}_family.parquet; [ -f $F ] || python3 -W ignore run_experiment.py $B family 20 $F --pipelines $T1
fi
# size of S (Q5)
for SS in 10 20 40; do for K in random extrap; do
  F=$OUT/${B}_${K}_S${SS}.parquet
  [ -f $F ] || python3 -W ignore run_experiment.py $B $K 20 $F --pipelines $T1 --s_size $SS --tag _S$SS
done; done
# 50% sources
F=$OUT/${B}_random_tfrac50.parquet; [ -f $F ] || python3 -W ignore run_experiment.py $B random 20 $F --pipelines $T1 --tfrac 0.5 --tag _T50
# duplicates kept
F=$OUT/${B}_random_nodedup.parquet; [ -f $F ] || python3 -W ignore run_experiment.py $B random 20 $F --pipelines $T1 --no_dedup --tag _nodedup
echo "HUTIAN_WAKE: tier2 done $B"
