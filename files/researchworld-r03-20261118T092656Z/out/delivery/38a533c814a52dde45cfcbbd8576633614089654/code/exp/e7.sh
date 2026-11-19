#!/bin/bash
# E7: second-kind matrices (generative-LLM leaderboards), family-grouped folds. Usage: exp/e7.sh FIRST LAST
cd "$(dirname "$0")/.."
F=$1; L=$2
for s in ${SETTINGS:-HELMMMLU HELMLITE LIVEBENCH OLMB6}; do
  K=1,2,3,4,5,6,8,12,20,30; [ $s = HELMLITE ] && K=1,2,3,4,5,6,8; [ $s = LIVEBENCH ] && K=1,2,3,4,5,6; [ $s = OLMB6 ] && K=1,2,3,4,5
  exp/loop.sh $s $F $L --group_kfold --nmin 3 --kgrid $K --n_random 100 --n_random_decision 10 --no_cluster
done
[ -z "$SETTINGS" ] && exp/loop.sh OLMB40 $F $L --group_kfold --nmin 3 --max_models 1200 --kgrid 1,2,3,4,5,6,8,12,20,30 --n_random 30 --n_random_decision 5 --no_cluster --methods mean,fa,gcov,ridge --rank_nfold 3
