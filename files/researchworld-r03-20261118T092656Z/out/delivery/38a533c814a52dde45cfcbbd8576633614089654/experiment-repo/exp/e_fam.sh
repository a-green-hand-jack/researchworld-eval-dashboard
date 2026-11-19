#!/bin/bash
# Family-held-out folds on the MTEB matrices (review finding: siblings of a test model must not be in the history) and
# k-medoids on setting B. Usage: exp/e_fam.sh SETTING_TAG FIRST LAST
#   A1fam / A2fam : same run as the main one with --group_kfold (folds = groups of organisations; history excludes every test family)
#   Bfam          : setting B (no cluster selector), group folds       -> results/B_fam
#   Bfamcluster   : setting B, k-medoids selector only, group folds    -> results/B_famcluster (same folds as results/B_fam)
#   Bcluster      : setting B, k-medoids selector only, random folds    -> results/B_cluster (same folds as results/B)
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONUNBUFFERED=1
t=$1; a=$2; b=$3
KB=1,2,3,5,8,12,20
for r in $(seq $a $b); do
  case $t in
    A1fam) o=results/A1_fam; [ -f $o/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting A1 --rep $r --out $o --group_kfold --kgrid 1,2,3,4,5,6,8,10,12,15,20,30,40,60 ;;
    A2fam) o=results/A2_fam; [ -f $o/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting A2 --rep $r --out $o --group_kfold --kgrid 1,2,3,4,5,6,8,10,12,15,20 ;;
    Bfam) o=results/B_fam; [ -f $o/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting B --rep $r --out $o --group_kfold --kgrid $KB --rank_nfold 2 --n_random 30 --n_random_decision 5 --no_cluster --selectors greedyA,greedyAcomp,greedyGauss,covered,central,pivqr,fwdreg ;;
    Bfamcluster) o=results/B_famcluster; [ -f $o/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting B --rep $r --out $o --group_kfold --kgrid $KB --rank_nfold 2 --n_random 0 --n_random_decision 0 --selectors '' --methods fa ;;
    Bcluster) o=results/B_cluster; [ -f $o/rec_rep$r.parquet ] || python3 -I exp/run_cv.py --setting B --rep $r --out $o --kgrid $KB --rank_nfold 2 --n_random 0 --n_random_decision 0 --selectors '' --methods fa ;;
  esac
done
echo "HUTIAN_WAKE: e_fam $t $a-$b finished"
