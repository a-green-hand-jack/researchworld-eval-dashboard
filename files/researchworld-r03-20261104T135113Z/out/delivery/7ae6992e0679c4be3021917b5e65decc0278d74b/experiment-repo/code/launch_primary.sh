#!/usr/bin/env bash
# Primary experiments, protocol B (25% of benchmarks held out as fixed targets, never selected; same targets for every k).
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
source "$HERE/_run.sh"
MET="mean avgreg fa ridge knn krr"
B="--target_frac 0.25 --methods $MET --K 10 --rank_metrics --rank_meth ridge krr --rank_k 2 4 8 16"
run B_mteb_dense56 --data mteb_dense56 --reps 3 $B
run B_mteb_dense --data mteb_dense --reps 2 $B
run B_mteb_mid --data mteb_mid --reps 2 $B
run B_mteb_sparse --data mteb_sparse --reps 2 $B
run B_helm_mmlu --data helm_mmlu --reps 5 $B
# protocol A (all benchmarks of a held-out model are targets; the revealed ones are removed from the score), earlier method list
A="--methods mean fa ridge avgreg pcals knn --K 10 --reps 3 --rank_metrics"
run A_mteb_dense56 --data mteb_dense56 $A
run A_helm_mmlu --data helm_mmlu --methods mean avgreg fa ridge knn krr --K 10 --reps 3 --ks 1 2 3 4 5 6 8 10 12 16 20 24 32 48
for d in helm livebench olb; do run A_$d --data $d $A --ks 1 2 3 4 5 6 8 --rank_k 1 2 4; done
run B_syn_base --data syn_base --reps 3 $B
# extended HELM-Lite matrix (91 models x 28 benchmarks; code/build_helm_ext.py) with floor
run B_helm_lite_ext --data helm_lite_ext --reps 5 $B
run F_helm_lite_ext --data helm_lite_ext --reps 5 --selectors random --n_rand 1 --methods $MET --K 10 --target_frac 0.25 --floor
