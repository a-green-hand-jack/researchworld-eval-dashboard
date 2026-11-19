#!/bin/bash
# A1 add-on: Mahalanobis (clr-residual) score vs euc/aitch/dirnll on every A1 config (same seeds as A1). Usage: run_a1m.sh PART(0..3)
cd "$(dirname "$0")"
cat manifest_chunk_0*.txt | awk -v p=$1 'NR%4==p' | while read TAG REPS CFG; do
  CFG2=$(python3 -c "import json,sys; c=json.loads(sys.argv[1]); c['methods']=['euc','aitch','dirnll','maha']; print(json.dumps(c))" "$CFG")
  T=${TAG/A1_/A1m_}
  [ -f ../results/raw/$T.csv ] || python3 -u -m cpsimplex.exp_a --config "$CFG2" --reps $REPS --seed0 1000 --tag "$T" --out ../results/raw/$T.csv | tail -1
done
