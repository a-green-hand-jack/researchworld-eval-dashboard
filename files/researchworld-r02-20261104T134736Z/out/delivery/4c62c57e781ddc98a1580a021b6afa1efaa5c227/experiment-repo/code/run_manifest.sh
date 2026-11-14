#!/bin/bash
# Usage: run_manifest.sh MANIFEST PART NPARTS -- runs every NPARTS-th line (offset PART), skipping outputs that exist.
M=$1; P=$2; N=$3; i=0
while read tag reps cfg; do
  if [ $((i % N)) -eq $P ] && [ ! -f results/raw/${tag}.csv ]; then bash code/run_a1.sh "$tag" "$reps" "$cfg"; fi
  i=$((i+1))
done < $M
