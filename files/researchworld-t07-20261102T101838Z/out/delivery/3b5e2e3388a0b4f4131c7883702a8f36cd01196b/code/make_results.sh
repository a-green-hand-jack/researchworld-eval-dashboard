#!/bin/bash
# Rebuild every derived table from the shard directories. usage: bash make_results.sh TIER SHARD_DIR RESULTS_DIR   (TIER = tier1 | tier2)
set -e
T=$1; D=$2; R=$3; mkdir -p $R/predictions $R/tables/$T
python3 -W ignore merge_predictions.py $D $R/predictions/$T.parquet $R/tables/$T/timing_by_shard.csv
python3 -W ignore aggregate.py $D $R/tables/$T --baseline random+mean
python3 -W ignore aggregate.py $D $R/tables/$T/vs_B2 --baseline strat+mean
python3 -W ignore analysis_extra.py $D $R/tables/$T
python3 -W ignore items_needed.py $R/tables/$T/summary.csv $R/tables/$T/items_needed.csv
