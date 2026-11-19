#!/usr/bin/env bash
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
source "$HERE/_run.sh"
for v in syn_r8 syn_noisy syn_hetero syn_clust syn_miss50 syn_M30; do
  run B_$v --data $v --reps 3 --K 10 --target_frac 0.25 --methods mean avgreg fa ridge knn krr
done
