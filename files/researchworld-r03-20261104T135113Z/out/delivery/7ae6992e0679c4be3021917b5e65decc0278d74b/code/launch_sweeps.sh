#!/usr/bin/env bash
# Launch the sweep / robustness experiments as ht-resource jobs (each writes results/raw/<name>.parquet).
# usage: bash code/launch_sweeps.sh [group]   groups: dense56 olb syn
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE/.."
SEL="random gv_fa gv_emp kcenter popular dopt"
MET="mean fa ridge knn krr"
source "$HERE/_run.sh"
case ${1:-all} in
dense56|all)
  D="--data mteb_dense56 --selectors $SEL --methods $MET --reps 3 --K 10 --target_frac 0.25"
  for m in 15 30 60; do run d56_mtrain$m $D --m_train $m; done
  for p in 0.3 0.6 0.8; do run d56_miss$p $D --extra_missing $p; done
  run d56_group $D --split group --group_col org
  run d56_temporal $D --split temporal --K 5 --reps 1
  run d56_leak $D --leak
  for r in 2 4 8; do run d56_rank$r $D --rank $r; done
  run d56_lomo --data mteb_dense56 --selectors random gv_fa --methods fa ridge --split lomo --reps 1 --target_frac 0.25
  run d56_logit $D --transform logit
  ;;&
olb|all)
  O="--data olb --selectors random gv_fa exh popular rawvar --methods mean fa ridge knn krr --ks 1 2 3 4 --reps 3 --K 10 --n_rand 5"
  run olb_group $O --split group --group_col "Base Model" --reps 2
  run olb_temporal $O --split temporal --K 5 --reps 1
  for m in 100 500 2000; do run olb_mtrain$m $O --m_train $m; done
  ;;&
dense|all)
  D="--data mteb_dense --selectors random gv_fa gv_emp kcenter popular --methods mean fa ridge knn krr --reps 1 --K 10 --target_frac 0.25"
  run d275_group $D --split group --group_col org
  run d275_temporal $D --split temporal --K 5
  ;;&
esac
# cost-aware budgets (per-mille of the total evaluation time of the candidate benchmarks)
case ${1:-all} in
cost|all)
  BUD="5 10 20 40 80 160 320 640"
  run C_d56 --data mteb_dense56 --selectors random gv_fa gvc_fa cheap --methods mean ridge krr --reps 3 --K 10 --target_frac 0.25 --budgets $BUD
  run C_d275 --data mteb_dense --selectors random gv_fa gvc_fa cheap --methods mean ridge krr --reps 1 --K 10 --target_frac 0.25 --budgets $BUD
  ;;
esac
# full-information floors (every observed non-target benchmark revealed; k label 999); same seeds/folds/targets as the B_* runs
case ${1:-all} in
floor|all)
  F="--selectors random --n_rand 1 --methods mean avgreg fa ridge knn krr --K 10 --target_frac 0.25 --floor"
  run F_mteb_dense56 --data mteb_dense56 --reps 3 $F
  run F_mteb_dense --data mteb_dense --reps 2 $F
  run F_mteb_mid --data mteb_mid --reps 2 $F
  run F_mteb_sparse --data mteb_sparse --reps 2 $F
  run F_helm_mmlu --data helm_mmlu --reps 5 $F
  for s in base r8 noisy hetero clust M30 miss50; do run F_syn_$s --data syn_$s --reps 3 $F; done
  ;;
esac
# small-N leaderboards under protocol B (2 fixed held-out targets, random draw per rep) with floor
case ${1:-all} in
smallN|all)
  S="--selectors random popular gv_fa dopt kcenter --methods mean avgreg fa ridge knn krr --K 10 --n_rand 10"
  run B_olb --data olb --ks 1 2 3 --target_frac 0.34 --reps 8 $S
  run F_olb --data olb --target_frac 0.34 --reps 8 --selectors random --n_rand 1 --methods mean avgreg fa ridge knn krr --K 10 --floor
  run B_helm --data helm --ks 1 2 3 4 5 6 --target_frac 0.25 --reps 8 $S
  run F_helm --data helm --target_frac 0.25 --reps 8 --selectors random --n_rand 1 --methods mean avgreg fa ridge knn krr --K 10 --floor
  run B_livebench --data livebench --ks 1 2 3 4 --target_frac 0.34 --reps 8 $S
  run F_livebench --data livebench --target_frac 0.34 --reps 8 --selectors random --n_rand 1 --methods mean avgreg fa ridge knn krr --K 10 --floor
  ;;
esac
# oracle selection (uses the held-out model's own target scores; upper bound on what selection can achieve, NOT a method)
case ${1:-all} in
oracle|all)
  O="--selectors oracle --methods mean fa ridge krr --K 10 --target_frac 0.25 --ks 1 2 3 4 5 6 8 10 12 16"
  run O_mteb_dense56 --data mteb_dense56 --reps 3 $O
  run O_helm_mmlu --data helm_mmlu --reps 5 $O
  run O_helm --data helm --reps 8 $O
  run O_olb --data olb --reps 3 --selectors oracle --methods mean fa ridge krr --K 10 --target_frac 0.34 --ks 1 2 3
  run O_livebench --data livebench --reps 8 --selectors oracle --methods mean fa ridge krr --K 10 --target_frac 0.34 --ks 1 2 3 4
  ;;
esac
# (re-launch after fixing the 'Removed' family and the OLB date column)
case ${1:-all} in
olbfix)
  O="--data olb --selectors random gv_fa popular rawvar --methods mean fa ridge knn krr --ks 1 2 3 4 --reps 3 --K 10 --n_rand 5"
  run olb_group $O --split group --group_col "Base Model" --reps 2
  run olb_temporal $O --split temporal --K 5 --reps 1
  ;;
esac
# leakage check redone with the selection model (factor fit, covariance) also fitted on the held-out rows
case ${1:-all} in
leakfix)
  D="--data mteb_dense56 --selectors $SEL --methods $MET --reps 3 --K 10 --target_frac 0.25"
  run d56_leak $D --leak
  run hm_leak --data helm_mmlu --selectors $SEL --methods $MET --reps 5 --K 10 --target_frac 0.25 --leak
  ;;
esac
# floors for the shift splits (same folds/targets as d56_group, d56_temporal, d275_group, d275_temporal)
case ${1:-all} in
floorshift)
  F="--selectors random --n_rand 1 --methods mean avgreg fa ridge knn krr --target_frac 0.25 --floor"
  run F_d56_group --data mteb_dense56 --split group --group_col org --K 10 --reps 3 $F
  run F_d56_temporal --data mteb_dense56 --split temporal --K 5 --reps 1 $F
  run F_d275_group --data mteb_dense --split group --group_col org --K 10 --reps 1 $F
  run F_d275_temporal --data mteb_dense --split temporal --K 5 --reps 1 $F
  run F_olb_group --data olb --split group --group_col "Base Model" --K 10 --reps 2 --selectors random --n_rand 1 --methods mean fa ridge knn krr --floor --target_frac 0.34
  ;;
esac
# ---- additions after review (issue experiment-repo#6): strict-family leave-out, leverage / QR rank diagnostic
case ${1:-all} in
extra|all)
  SELX="random gv_fa dopt central kcenter popular"
  D="--data mteb_dense56 --selectors $SELX --methods $MET --reps 3 --K 10 --target_frac 0.25"
  run d56_famgroup $D --split group --group_col family
  run d275_famgroup --data mteb_dense --selectors $SELX --methods $MET --reps 1 --K 10 --target_frac 0.25 --split group --group_col family
  F="--selectors random --n_rand 1 --methods mean avgreg fa ridge knn krr --target_frac 0.25 --floor"
  run F_d56_famgroup --data mteb_dense56 --split group --group_col family --K 10 --reps 3 $F
  run F_d275_famgroup --data mteb_dense --split group --group_col family --K 10 --reps 1 $F
  run d56_selrank --data mteb_dense56 --selectors random lev_r1 lev_r2 lev_r4 lev_r8 lev_r16 qr_r1 qr_r2 qr_r4 qr_r8 qr_r16 --methods mean fa krr --reps 3 --K 10 --target_frac 0.25 --ks 1 2 3 4 6 8 12 16 24
  ;;
esac
