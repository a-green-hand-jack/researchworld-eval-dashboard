# usage: jobs/ollb_ordinal.sh RULE CAP   -- stratified (rank-log-uniform) sample: ranks 2..21 + 150 log-uniform, seed 0
cd "$(dirname "$0")/.."
jobs/_run.sh ollb_ordinal_$1_$2 src/run_core.py ollb $2 $1 sample results/ollb_ordinal_$1_$2.csv --nsample 150
