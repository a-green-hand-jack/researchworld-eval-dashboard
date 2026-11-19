#!/bin/bash
# Full reproduction, from the downloads to every result table. Run from the repository root.
# Each block is independent after block 1; approximate wall-clock on a shared 2-CPU container is given per block.
# Raw outputs go to results/runs, results/robust, results/variants; summaries to results/summary; tidy tables to results/.
set -euo pipefail
DATA=${DATA:-data/raw}                      # raw downloads (not redistributed)
R=results; mkdir -p $R/runs $R/robust $R/variants $R/summary $R/logs
S3="2,3,5,10,20,50,100"; SH="2,3,5,10,20,40"

# 1. data (minutes): pinned downloads, checksums, model x task matrices
python3 code/fetch_ollb.py $DATA/ollb
python3 code/fetch_helm.py $DATA/helm/v1.13.0
python3 code/build_data.py $DATA/ollb/train-00000-of-00001.parquet $DATA/helm/v1.13.0 data/processed
python3 code/ollb_items.py data/processed/ollb_noise.json          # item counts and normalisation floors (one pinned results JSON)
python3 code/official_rules_check.py $DATA/helm/v1.13.0 $R/official_rules_check.csv

# 2. solver tests and theory check (about 5 min)
python3 -m pytest -q code/tests
python3 code/theory_check.py $R/theory_check.csv

# 3. core grid (OLLB closed forms ~15 min; HELM all rules incl. Copeland ~1.5 h; OLLB ordinal top-50 ~25 min)
python3 code/run_core.py ollb emp99,emp95 mean,median,min,geomean,harmonic,pow-2 all $R/runs/ollb_primary_closed.csv
python3 code/run_core.py ollb ceil,front0,gain5,gain10,gain20 mean,median,min,geomean,harmonic,pow-2 all $R/runs/ollb_capsweep_closed.csv
python3 code/run_core.py ollb emp99,ceil borda,condorcet,plurality top50 $R/runs/ollb_primary_ordinal_top50.csv
python3 code/run_core.py helm emp99T,emp99P,emp95T mean,median,min,geomean,harmonic,borda,condorcet,plurality all $R/runs/helm_primary.csv
python3 code/run_core.py helm ceil,front0,gain5,gain10,gain20 mean,median,min,borda,condorcet,plurality,copeland,geomean,harmonic all $R/runs/helm_capsweep.csv
python3 code/run_core.py helm emp99T,ceil copeland all $R/runs/copeland_helm.csv

# 4. uncertainty (evaluation noise, task bootstrap, task-subset scaling) at the primary caps
python3 code/run_robust.py noise ollb mean,median,min,pow-2 emp99 $R/robust/rob_ollb_noise_closed_emp99.csv --R 300 --strata $S3
python3 code/run_robust.py taskboot ollb mean,median,min,pow-2 emp99 $R/robust/rob_ollb_taskboot_closed_emp99.csv --R 300 --strata $S3
python3 code/run_robust.py noise ollb borda,condorcet,plurality emp99 $R/robust/rob_ollb_noise_ord_emp99.csv --R 60 --strata $S3
python3 code/run_robust.py taskboot ollb borda,condorcet,plurality emp99 $R/robust/rob_ollb_taskboot_ord_emp99.csv --R 60 --strata $S3
python3 code/run_robust.py noise helm mean,median,min,borda,condorcet,plurality emp99T $R/robust/rob_helm_noise_emp99T.csv --R 200 --strata $SH
python3 code/run_robust.py taskboot helm mean,median,min,borda,condorcet,plurality emp99T $R/robust/rob_helm_taskboot_emp99T.csv --R 200 --strata $SH
python3 code/run_robust.py tasksub helm mean,median,min,borda,plurality emp99T $R/robust/rob_helm_tasksub_emp99T.csv --R 60

# 5. variants: dataset slices, scoring scale, margin, weights, cost scale
python3 code/run_core.py ollb_nomerge emp99,ceil mean,median,min all $R/variants/var_ollb_nomerge.csv
mkdir -p $R/variants/shards
for k in 0 1; do python3 code/run_core.py ollb_top500 emp99,ceil mean,median,min,borda,condorcet,plurality all $R/variants/shards/var_ollb_top500_$k.csv --shard $k/2 & done; wait
# Copeland on the top-500 slice: one MILP per target with 499 rivals (up to the 120 s limit, hits are censored); same shards, merged into the same file
for k in 0 1 2 3 4 5; do python3 code/run_core.py ollb_top500 emp99 copeland all $R/variants/shards/var_ollb_top500_copeland_$k.csv --shard $k/6 & done; wait
python3 code/merge_shards.py $R/variants/var_ollb_top500.csv $R/variants/shards/var_ollb_top500_0.csv $R/variants/shards/var_ollb_top500_1.csv \
  $R/variants/shards/var_ollb_top500_copeland_{0,1,2,3,4,5}.csv
python3 code/run_core.py ollb_raw ceil,gain10 mean,median,min all $R/variants/var_ollb_raw.csv
for e in 1 2; do
  python3 code/run_core.py helm emp99T mean,median,min,borda,condorcet,plurality all $R/variants/margin${e}_helm.csv --eps $e
  python3 code/run_core.py ollb emp99 mean,median,min all $R/variants/margin${e}_ollb.csv --eps $e
done
python3 code/run_weights.py ollb emp99 $R/variants/weights_ollb_emp99.csv
python3 code/run_weights.py helm emp99T $R/variants/weights_helm_emp99T.csv --strata $SH
for c in emp99 ceil; do python3 code/run_zcost.py ollb $c $R/variants/zcost_ollb_$c.csv; done
for c in emp99T ceil; do python3 code/run_zcost.py helm $c $R/variants/zcost_helm_$c.csv; done

# margin grid check (strict-win margin 1e-5 instead of 1e-3, ordinal rules): HELM all targets, OLLB 50 best targets
python3 code/run_core.py helm emp99T borda,condorcet,plurality,copeland all $R/variants/eps1e5_helm.csv --eps 1e-5
python3 code/run_core.py ollb emp99 borda,condorcet,plurality top50 $R/variants/eps1e5_ollb.csv --eps 1e-5

# 6. tables (about 15 min)
bash code/make_tables.sh
python3 code/uniform_lift.py $R                                   # Linf read as a cap-saturated uniform lift: its L1 / K against the optimum
python3 code/eps_check.py $R $R/eps_grid_check.csv                # finite-margin check of the ordinal grid
# Minimal path (data/processed to the primary-cap tables, ~17 min wall, ~10 CPU-min): OUT=results_min bash code/run_minimal.sh

# optional: OLLB leaf-task run (request #8); needs data/processed/ollb_leaves.csv (shipped; rebuilt by fetch_ollb_leaves.py + build_ollb_leaves.py)
for s in closed_leaf closed_six ord_leaf ord_six; do bash code/run_leaf.sh $s > results/logs/leaf_$s.log 2>&1 & done; wait
python3 code/assemble_leaf.py

# cap evidence (request #10; 18 s) and the full-board ordinal sample (request #11; 4 shards, ~5-7 min each)
python3 code/cap_evidence.py results/cap_evidence
mkdir -p results/ordinal_sample/shards
for k in 0 1 2 3; do python3 -u code/ordinal_sample.py results/ordinal_sample/shards/sample_$k.csv --per-stratum 15 --seed 0 --shard $k/4 > results/logs/ordinal_sample_$k.log 2>&1 & done; wait
python3 code/summarize_ordinal_sample.py
# leaf source provenance (request #9); needs the retrieval directory written by code/fetch_ollb_leaves.py (network): python3 code/leaf_provenance.py RAW
python3 code/copeland_screen.py                                   # cap-saturated check of the top-500 Copeland statuses (about 30 min, single process)
