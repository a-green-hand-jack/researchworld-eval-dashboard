#!/usr/bin/env bash
# Second-round analyses (cluster bootstrap, selector/rule contrasts, extra baselines, detector, diagnostics).
# Each command is one ht-resource job in the original run; LOCAL=1 runs them sequentially in plain python (see _run.sh).
# usage: bash code/launch_review.sh [group]    groups: xrun xtable cluster extra ood diag
# Requires the primary runs (launch_primary.sh) and sweeps (launch_sweeps.sh) to have produced results/raw/*.parquet.
HERE="$(cd "$(dirname "$0")" && pwd)"; cd "$HERE"
J() { # J <note> <command...>: job on the compute resource, or in-place when LOCAL=1
  note=$1; shift
  if [ "${LOCAL:-0}" = 1 ]; then echo "== $note"; "$@"; else ht-resource run local-compute --note "$note" -- bash -c "cd $HERE && $*" | grep '"ref"'; fi
}
# leakage-free rank sweep for the leverage / pivoted-QR selectors (rank 3 and 12 instead of CV rank)
case ${1:-all} in
diag|all)
  J d56_selrank2 python3 -u run_cv.py --out ../results/raw/d56_selrank2.parquet --data mteb_dense56 --selectors lev_r3 lev_r12 qr_r3 qr_r12 --methods mean fa krr --reps 3 --K 10 --target_frac 0.25 --ks 1 2 3 4 6 8 12 16 24
  J analyze_selrank2 python3 analyze.py d56_selrank2
  J lev_diag python3 lev_diag.py
  J describe_sparse python3 describe_sparse.py
  J target_draws python3 target_draws.py
  ;;&
# extra selectors (forward ridge, multi-task lasso, adaptive local-Gaussian) and rules (OLS, rank-r FA, soft-impute, trend)
xrun|all)
  S1="--sel random gv_fa fwd_ridge mtl adapt_loc --meth fa krr ridge ols softimpute fa_r1 fa_r2 --ks 1 2 4 8 16"
  S2="--sel random gv_fa --meth fa krr ols avgreg trend_fa trend_ols softimpute --ks 2 4 8 16"
  for r in B_mteb_dense56 B_helm_mmlu B_mteb_dense; do J X_$r python3 -u xrun.py $r sel_$r $S1; done
  for r in d56_temporal d275_temporal d56_group d56_famgroup; do J X_$r python3 -u xrun.py $r rules_$r $S2; done
  ;;&
xtable|all)   # needs the xrun outputs
  J xtab python3 -u x_table.py sel_B_mteb_dense56 sel_B_mteb_dense sel_B_helm_mmlu rules_d56_temporal rules_d275_temporal rules_d56_group rules_d56_famgroup
  J xkstar python3 x_kstar.py
  ;;&
cluster|all)
  for d in mteb_dense56 mteb_dense mteb_mid helm_mmlu mteb_sparse; do J cluster_$d python3 cluster_analysis.py $d; done
  J group_counts python3 cluster_analysis.py --groups
  for d in mteb_dense56 mteb_dense mteb_mid helm_mmlu mteb_sparse; do J theory_train_$d python3 theory_train_only.py $d; done
  ;;&
extra|all)    # rolling-origin temporal, soft-impute / trend baselines, per-target forward selection, Mahalanobis scores
  for n in mteb_dense56 mteb_dense mteb_mid; do J extra_$n env REPS=4 python3 -u extra_baselines.py $n; done
  J extra_summary python3 extra_summary.py
  ;;&
ood|all)
  J ood python3 ood_detector.py B_mteb_dense56 d56_group d56_famgroup d56_temporal B_mteb_dense d275_group d275_temporal
  ;;
esac
