# Code: scoring a real LLM on MMLU-Pro, and replaying tuning searches

Everything the paper reports is produced by scripts in `code/` (scoring) and `analysis/` (search replay, reporting methods, synthetic study, summaries). Results are in `results/` (`results/README.md` lists, for every file, the script that produces it).

## Environment (as run)
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, pyarrow 26.0.0, torch 2.14.1+cpu, transformers 5.22.1. CPU only (2 CPUs / 4 GB per job, shared host).
- Model: `Qwen/Qwen2.5-0.5B-Instruct` (fp32; bf16 on CPU was too slow, the 1.5B model does not fit in 4 GB in fp32).
- Data: MMLU-Pro (`TIGER-Lab/MMLU-Pro`) at revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`, test split; 3-shot demonstrations come from its validation split.

## Scoring (`code/`)
- `configs.py`: the configuration space. 6 instruction wordings x demonstration set (none, or one of 4 random 3-shot sets, seed 12345) x option layout (plain / reversed) = 60 configurations; `config_pool.json` is the frozen list (index = 10*instr + 2*demo_id + layout).
- `qidx_pool.npy`: the 2000 test questions (seed 2024, drawn from items of at most 300 tokens; `test_token_len.npy`).
- `score.py`: for each configuration builds the shared prompt prefix, caches its key/value states, and for each question reads the log-probabilities of the option letters (A..J, original option indices, absent options -inf) at the answer position. No sampling: scoring is deterministic, so the correctness matrix is a fixed 0/1 array (configs x questions) and any search procedure can be replayed on it.
  `python3 code/score.py --model MODEL_DIR --data TEST.parquet --qidx code/qidx_pool.npy --configs code/config_pool.json --cfg_range 0:6 --out OUTDIR/pool_0-6.npy --threads 2`
- `analysis/assemble.py OUTDIR TEST.parquet code/qidx_pool.npy results/matrix.npz`: merges per-job files, keeping only configurations complete on all questions (freeze rule: K is reported as the actual number of complete configurations).

## Analysis (`analysis/`)
- `lib.py`: search procedures (exhaustive argmax, successive halving, successive rejects, greedy coordinate ascent) and reporting methods (naive, split, 5-fold cross-fit, Harrell bootstrap optimism, bootstrap out-of-bag and .632 (derived in `run_grid.derive`), simultaneous Gaussian-max interval, conditional-on-selection median-unbiased estimate/CI, Ladder-type thresholded report).
- `run_grid.py`: replication engine (`run`, `run_compare`), `summarize` (bias, RMSE, coverage with MC s.e., width, regret, claim / false-claim rates, false-ship rates).
- `synth.py`, `theory.py`: Gaussian-copula item pool and the Gaussian-max prediction of the gap.
- `run_synth*.py`, `make_synth_results.py`: synthetic study and its result files.
- `run_real.py`: replay on the cached real matrix, with `disjoint` arm (T drawn without replacement, truth on the remaining pool items) and the iid arm (truth = exact pool mean).

## Measured compute
Reported in `results/compute_log.json` when the study ends (CPU-hours, forward passes, wall-clock per job, seeds).

## Regenerating `results/` (ordered commands, seeds, measured runtimes)
All paths below are relative to the repository root; `W` is any scratch directory (`mkdir -p $W/syn $W/syn3 $W/out $W/real`). Every job ran in a container with 2 CPUs (4 GB) on a shared host; "ran" is the running time the resource measured (world running time; does not include time the world was frozen between turns), not an exclusive-CPU time. Where the table says "not recorded" the resource list no longer held the job.

| # | Step | Command | Measured |
|---|------|---------|----------|
| 1 | Score the response matrix (10 parallel jobs, 6 configs each; resumable) | `cd $W && for lo in 0 6 12 18 24 30 36 42 48 54; do python3 <repo>/code/score.py --model models/Qwen2.5-0.5B-Instruct --data data/mmlupro --qidx <repo>/code/qidx_pool.npy --configs <repo>/code/config_pool.json --cfg_range $lo:$((lo+6)) --maxtok 400 --out out/pool_$lo-$((lo+6)).npy > out/pool_$lo-$((lo+6)).log 2>&1 & done` (`data/mmlupro` = a local copy of the pinned dataset; `models/...` = a local copy of the model) | ≈0.19 questions/s per job; ≈3 h of running time per configuration (≈17 h expected per job of 6) at 2 CPUs under contention (`results/compute_log.json`: wall-clock per chunk 21–35 h, including time the containers were frozen; chunks 24:30, 36:42, 42:48, 48:54 finished after 21 h or less) |
| 2 | Assemble the matrix (complete configurations only) | `python3 analysis/assemble.py $W/out $W/data/mmlupro/data/test-00000-of-00001.parquet code/qidx_pool.npy results/matrix.npz` | seconds |
| 3 | Plan grid (6 shards in parallel) | `for sh in 0 1 2 3 4 5; do (cd analysis && python3 run_synth3.py $sh 6 $W/syn3 > $W/syn3_$sh.log 2>&1) & done` | shards 2–5: 493, 535, 520, 587 s; shards 0 and 1 re-run in a fresh container: ≈ 710 s each (read off the resource: 474 and 451 s at a point 4–5 min before the end; last output file 12 min after the first), (cells identical to the original run), so all six shards take 8–12 min each in parallel |
| 4 | Part 2: conditional intervals and two-system comparison | `cd analysis && python3 run_synth2.py $W/syn/synth2 500` (writes `synth2_cond.parquet`, `synth2_compare.parquet`) | re-run at the same size (M=500): ≈ 1050 s (first output 08:24, last 08:41 on the same clock; the original log's 50 689 s elapsed is inflated by freezes); outputs identical to the original run |
| 5 | Ladder | `cd analysis && python3 run_synth_ladder.py $W/syn/ladder.parquet` | re-run: 33 s (outputs identical to the original run) |
| 6 | Synthetic summaries (plan grid, theory table, compare, Ladder) | `cd analysis && python3 make_synth_results.py $W ../results` | 87–366 s (theory table M=5000 dominates) |
| 7 | Hybrid vs conditional intervals | `cd analysis && python3 run_hybrid.py ../results/synth_hybrid_summary.csv` | 1325 s (re-run with the hybrid median-unbiased point estimate; 880 s for the earlier version) |
| 8 | Ranking flips among tuned systems | `cd analysis && python3 run_rank_synth.py ../results/synth_ranking_summary.csv` | 382 s |
| 9 | Real replay, disjoint-truth arm (per pool, M=1000) | `cd analysis && MATRIX=$W/matrix.npz python3 run_real.py full60 $W/real/full60_disjoint.parquet 1000 disjoint` (`MATRIX` defaults to `results/matrix.npz`) | 1454 s at K=5; 3734 s at K=21; 5116 s at K=60 (with greedy) |
| 10 | Real replay, iid arm | `cd analysis && MATRIX=$W/matrix.npz python3 run_real.py full60 $W/real/full60_iid.parquet 1000` | 4608 s at K=21; 6529 s at K=60 (with greedy) |
| 11 | Real summaries and composition | `cd analysis && python3 make_real_results.py $W/real ../results` | seconds |
| 12 | Compute log | `ht-resource status local-compute \| python3 analysis/compute_log.py results/matrix.npz results/compute_log.json $W/out` | seconds |
| 13 | Fresh-evaluation-set study, synthetic (6 shards, 18 cells) | `for sh in 0 1 2 3 4 5; do (cd analysis && python3 run_fresh.py cells $sh 6 $W/fresh) & done` | 1018–1387 s for shards 0, 1, 3, 4, 5; shard 2 (cells K=64 at tau .01 and .03 with rho .5, and tau 0 with rho .9) 3263 s |
| 14 | Equal-budget ranking study, synthetic | `cd analysis && python3 run_fresh.py rank $W/fresh/rank_eq.csv` | 623 s |
| 15 | Fresh-evaluation-set study, real matrix | `cd analysis && python3 run_fresh.py real $W/matrix.npz $W/fresh/real_k60.parquet 500` | 751 s at K=10; 943 s at K=21; 857 s at K=60 |
| 16 | Fresh-set summaries | `cd analysis && python3 make_fresh_results.py $W ../results` (uses the `real_k*.parquet` with most configurations) | seconds |
| 17 | Validation of conditional / hybrid inference | `cd analysis && python3 validate_cond.py $W/val` ; `python3 validate_cond_lead.py $W/val/validation_lead.csv` | 2214 s ; 614 s (777 s for the earlier version with the outlier dropped) |
| 18 | Real-matrix Gaussian-max check | `cd analysis && python3 real_theory.py ../results/matrix.npz ../results/real_summary.csv ../results/real_gaussian_max_check.csv` | 45 s at K=60 (job, M=5000 draws per cell; output identical on re-run) |
| 19 | Calibrated generator vs real gap | `cd analysis && python3 calibrated_generator.py ../results/matrix.npz ../results/real_summary.csv ../results 10 300` | 113 s at K=60 (job; output identical on re-run) |

`analysis/run_synth.py` (first-stage study, tau in {0, .01, .03}, M=500) is superseded by step 3 and feeds no file in `results/`. Steps 3–8 need no GPU and no data files; step 1 needs the pinned MMLU-Pro snapshot and the Qwen2.5-0.5B-Instruct weights.

### Seeds
| Script | Pool / data seed | Replication seed |
|---|---|---|
| `configs.py` (demo sets) | 12345 | – |
| question subset (`qidx_pool.npy`) | 2024 | – |
| `run_synth3.py` (plan grid) | pool seed 7 (128 configs, N=20000) | 100 + cell index (order of the `add(...)` calls) |
| `run_synth2.py` | pool seed 7 (64 configs) | 21 |
| `run_synth_ladder.py` | pool seed 7 | 77 |
| `run_hybrid.py` | 300 + 1000·tau | 11 |
| `run_rank_synth.py` | 400 + 1000·tau | 21 |
| `make_synth_results.py` theory table | pool seed 7 | 1 |
| `run_real.py` | – (real matrix) | 5 |
Replication seeds are combined with n and a hash of the cell tag (`zlib.crc32`), so cells are independent and any cell can be re-run alone.
