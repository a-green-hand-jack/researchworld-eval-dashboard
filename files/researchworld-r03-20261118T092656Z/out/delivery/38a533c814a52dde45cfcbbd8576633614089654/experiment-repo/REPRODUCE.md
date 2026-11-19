# Reproducing the analyses (experiment-repo)

Everything below runs from the repository root. All scripts use `python3 -I` (isolated), one BLAS thread per process
(`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`), and are resumable (a finished `rec_rep*.parquet` is skipped).

## Environment
- Host CPU: Intel Xeon Gold 6230 @ 2.10 GHz, 2 sockets × 20 cores (40 CPUs, shared with other jobs); host memory 256 GB.
  Each job here was limited to 2 CPUs (`local-compute`), 0.1–0.8 GB resident. No GPU.
- Python 3.11.2; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, pyarrow 26.0.0.
- Data: `data/*.parquet` built by `src/build_*.py`, `src/data_mteb.py`; provenance and licences in `data/SOURCES.md`
  (MTEB `embeddings-benchmark/results` at commit 6dabbcc: CC0-1.0, as verified by the task material; Open LLM Leaderboard v2 and LiveBench datasets: no licence on the dataset card;
  HELM Lite / HELM MMLU: no data licence stated, HELM code Apache-2.0; none of the non-MTEB data is redistributed here).

## Seeds
Repetition `r` seeds the fold split and every random draw with `r` (and `numpy.random.default_rng(r)` inside `e_opt.py`,
`e8_sweep.py`, `e_h3.py`). A1/A2: reps 0–9 (5 folds each). LLM matrices: family-grouped folds, reps 0–4. H3/H3k/H3r/H3c: reps 0–4.
Randomness within a run (random-k baselines) uses 100 draws (`--n_random 100`; OLMB40 30, H3 20).

## Commands (script → output)
| What | Command | Output |
|---|---|---|
| E1 synthetic, closed-form forecasts | `python3 -I exp/e1_synth.py REPS results/E1` ; `exp/analyze_e1.py` | `results/E1/*` |
| Main runs, dense A1/A2 (E3, E4, E5) | `exp/loop.sh A1 0 9 --kgrid …` / `exp/loop.sh A2 0 9` (defaults of `exp/run_cv.py`; grid up to N) | `results/{A1,A2}/rec_rep*.parquet`, `fit_rep*_fold*.npz` |
| Curves, primary comparisons (Holm) | `python3 -I exp/analyze_main.py A1` (and every matrix) | `results/<M>/{curves,primary,fa_rank}.csv` |
| E-floor (empirical precision floor) | `python3 -I exp/e_floor.py A1` | `results/<M>/floor.csv` |
| H1/H5 forecast vs measured | `python3 -I exp/analyze_h1.py A1` | `results/<M>/h1*.csv/json` |
| E0 leakage, E2 groups & cost | `exp/e2.sh 0 4` then `exp/e2b.sh 0 4`; `python3 -I exp/analyze_e2.py` | `results/E2/*.csv` |
| Aggregation ablation | `exp/e_agg.sh 0 4`; `python3 -I exp/analyze_agg.py` | `results/E2/agg_paired.csv` |
| E6 shift and stopping rules | `exp/e6.sh`; `python3 -I exp/analyze_e6.py` | `results/E6/*.csv` |
| E7 LLM matrices | `exp/e7.sh 0 4` | `results/{HELMMMLU,HELMLITE,LIVEBENCH,OLMB6,OLMB40}` |
| E8 history size / missingness | `exp/e8.sh`; `python3 -I exp/analyze_e8.py` | `results/E8/*` |
| Greedy vs optimum, restricted eigenvalue, stability | `python3 -I exp/e_opt.py A2 0` (and A1) | `results/<M>/{opt,stability}_rep0.csv` |
| H3, H3r, H3k, H3c nonlinear imputers | `exp/e_h3.sh 0 4`, `exp/e_h3r.sh 0 4`, `exp/e_h3k.sh 0 4`, `exp/e_h3c.sh A1 0 4` / `A2 0 4`; `python3 -I exp/analyze_h3.py` | `results/H3*/…` |
| Setting B (sparse MTEB) | `exp/loop.sh B R R --kgrid 1,2,3,5,8,12,20 --rank_nfold 2 --n_random 30 --n_random_decision 5 --no_cluster --selectors greedyA,greedyAcomp,greedyGauss,covered,central,pivqr,fwdreg` (R = repetition) | `results/B/` |
| Family-held-out folds (A1, A2, B) and k-medoids on B (wall-clock with 8 jobs sharing the host: A1fam, 5 reps ≈ 30 min; A2fam, 5 reps ≈ 12 min; Bfam ≈ 2 h per rep; Bcluster / Bfamcluster ≈ 2–3 min per rep) | `exp/e_fam.sh A1fam 0 4`, `exp/e_fam.sh A2fam 0 4`, `exp/e_fam.sh Bfam R R`, `exp/e_fam.sh Bcluster R R`, `exp/e_fam.sh Bfamcluster R R` (R = 0, 1, 2); then `python3 -I exp/analyze_fam.py A1 A2 B` and `python3 -I exp/fam_tables.py` | `results/{A1,A2,B}_fam`, `results/B_cluster`, `results/B_famcluster`, `results/FAM/{curves,paired}.csv`, `results/FAM/TABLES.md` |
| Compact per-model tables | `python3 -I exp/make_pm.py results/A1 results/A2 …` | `results/<M>/per_model.parquet` |
| Build this delivery | `exp/deliver.sh PAPER_REPO_CHECKOUT` | `code/` |
| Files for figures/tables | `python3 -I exp/export_figtab.py [--only NAME]` | `figdata/*.csv`, schema in `figdata/README.md` |
| Unit tests (closed forms) | `python3 -m pytest tests` | |

## Wall-clock (single job, 2 CPUs, shared host; per repetition = 5 folds; model fits only, from `info_rep*.json`)
| Run | per-rep fit time (median) | note |
|---|---|---|
| A2 main | median 3.5 min (max 5.3) | model fits only; the whole 10-rep run took ≈ 33 min of wall-clock (2 jobs in parallel) |
| A1 main | median 7.8 min (max 9.8) | whole 10-rep run ≈ 75 min wall-clock |
| A1 / A2 leakage; first-subset aggregation (5 reps) | A1 3.5 / 3.0 min, A2 0.7 / 1.2 min | fits only |
| HELMMMLU / HELMLITE / LIVEBENCH | 2.7 / 1.1 / 1.2 min | fits only (median per rep, 5 reps); the rest of the wall-clock is the 100-draw random baseline |
| OLMB6 / OLMB40 | 26.0 / 35.5 min | fits only (median per rep, 5 reps); the whole OLMB40 job (5 reps) took ≈ 3 h wall-clock on a loaded host |
| H3c (A1, FA/ET/KRR, 5 reps) | > 2 h on a loaded host | A2: ≈ 24 s per fold |
| E8 A2 sweep | ≈ 13 min | A1 sweep: > 1.5 h |
| Setting B | 26–35 min per fold (median 32), ≈ 2.5 h per rep | 3 reps (15 fits); reps 1 and 2 ran as two parallel jobs of ≈ 2.7 h wall-clock each on a loaded host |
Times are wall-clock on a loaded host and are upper bounds for the single-process cost.
