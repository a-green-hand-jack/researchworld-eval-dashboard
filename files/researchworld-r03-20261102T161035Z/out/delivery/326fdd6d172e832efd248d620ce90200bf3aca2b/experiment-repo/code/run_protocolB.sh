#!/bin/sh
# Protocol-B raw runs and aggregation, as used for results/ct_*.csv, rank_corr.csv, lowsd_check.csv.  Run from the repository root.
# Wall times in comments: measured on the 2-CPU job container while 5-12 such jobs shared the host (alone ~2-4x faster); rep = one repeat.
# Shards (REP0) are independent: start them as parallel jobs.   Seeds depend on REP0+rep only, so sharded and unsharded runs are identical.
set -e; mkdir -p results/raw; R=results/raw; P="python3 -u code/run_exp2.py"
EXTRA=random,random_pm,greedy_ridge,backelim,full
# --- main common-target runs (selectors random, coverage, variance, corr_mean, qr, farthest, greedy_ridge, greedy_bayes, full) ---
REP0=0 $P mteb random 6 $R/ct_mteb_random_a.csv        # ~80-100 s/rep alone-ish, 3-6 min/rep with 12 jobs sharing
REP0=6 $P mteb random 6 $R/ct_mteb_random_b.csv
REP0=0 $P mteb group 6 $R/ct_mteb_group_a.csv
REP0=6 $P mteb group 6 $R/ct_mteb_group_b.csv
$P mtebsparse random 8 $R/ct_mtebsparse_random.csv     # ~80 s/rep
$P olb random 5 $R/ct_olb_random.csv ; $P olb group 5 $R/ct_olb_group.csv ; $P olb time 3 $R/ct_olb_time.csv   # ~35-45 s/rep (leave-one-benchmark-out over 6 benchmarks, 150 test models)
$P helm random 20 $R/ct_helm_random.csv ; $P helm group 10 $R/ct_helm_group.csv        # ~15 s/rep
# --- conditions: controlled missingness, selection penalty, train size, duplicates, family / time shift ---
for p in 0.1 0.3 0.5; do DENS=0.98 MASK=$p $P mteb random 4 $R/ct_mteb_mask$p.csv; done   # 3-20 min/rep depending on load (heavier FA fits with missing cells)
PEN=1 REP0=20 $P mteb random 4 $R/ct_mteb_pen.csv      # only 2 repeats finished; stopped
for n in 30 60; do NTRAIN=$n $P mteb random 4 $R/ct_mteb_ntrain$n.csv; done
DEDUP=1 $P mteb random 5 $R/ct_mteb_dedup.csv
PRED=1 $P mteb family 5 $R/ct_mteb_family.csv           # ~1-5 min/rep
PRED=1 $P mteb time 4 $R/ct_mteb_time.csv               # ~1.5 min/rep (36 test models)
# --- extra selectors (random_pm, backelim) on the same splits (same seeds as the runs above), with true/predicted z-scores for rank_corr.csv ---
PRED=1 ONLY=$EXTRA REP0=0 $P mteb random 3 $R/ex_mteb_random_a.csv      # 6 of the 12 repeats: reps 0-5
PRED=1 ONLY=$EXTRA REP0=3 $P mteb random 3 $R/ex_mteb_random_b.csv
ONLY=random_pm,backelim $P mteb group 4 $R/ex_mteb_group.csv             # reps 0-3, no PRED
ONLY=$EXTRA $P mtebsparse random 4 $R/ex_mtebsparse_random.csv           # reps 0-3
PRED=1 ONLY=$EXTRA $P olb random 5 $R/ex_olb_random.csv
PRED=1 ONLY=$EXTRA $P helm random 20 $R/ex_helm_random.csv
# --- aggregation (each < 2 min) ---
python3 code/theory_real.py results                    # spectrum.csv, theory_real_*.csv
python3 code/analyze2.py results/raw results           # ct_curves, ct_paired, ct_reference, ct_k_needed (merges _a/_b shards and ex_* files; '<data>|sub' views)
python3 code/analyze3.py results/raw results           # rank_corr.csv, lowsd_check.csv (from *.pred.csv.gz)
python3 code/theory_fit.py results                     # theory_fit.csv
