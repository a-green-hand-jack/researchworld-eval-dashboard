# Reproduction guide

Everything in `experiment/` is run from the directory `experiment/` (all paths below are relative to it).
Numbers marked **[measured]** come from logs of the runs in this study; nothing here is an estimate unless it says so.

## 1. Environment
- Machine: container sandboxes of a shared host (jobs: single thread each, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`;
  the host was shared and oversubscribed, so wall-clock exceeds metered CPU time; see §4 for both).  CPU only, no GPU.
- Python 3.11.2; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, **shap 0.51.0**, pyarrow 26.0.0,
  folktables 0.0.12, openml 0.15.1, liac-arff 2.5.0, requests 2.34.2, matplotlib (figures, see `figures/README.md`).
  Full pinned list: `experiment/requirements.txt` (output of `pip freeze` in the run environment).
- Build: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`.
- shap behaviours that the design relies on (verified in 0.51.0, see `code/explain.py`): `KernelExplainer` ignores `seed=`
  (we call `np.random.seed(s)` before every `shap_values`); with `nsamples >= 2^d - 2` it enumerates (the default `2d+2048`
  is exact for d <= 11: 2*11+2048 = 2070 >= 2^11-2); the default `l1_reg="num_features(10)"` pre-selects features (LARS), so the main grid uses
  `l1_reg=False` and the default is a separate stage (`kernell1`, run on the German cells and ACS-Employment lr); the permutation explainer needs
  `max_evals >= 2d+1` and honours `seed=`.

## 2. Data
Raw files are downloaded once (needs network) into `$SHAP_DATA` (default `/hutian/data/raw`) by `code/data.py`; jobs then read the cache.

| dataset | source | retrieved | licence | rows x cols raw -> used | sha256 of the file used | loader |
|---|---|---|---|---|---|---|
| German Credit (d=20) | UCI, `statlog+german+credit+data` (`german.zip`) | 2026-11 | as stated on the UCI page (CC BY 4.0; not re-verified by this position) | 1000 x 20 -> 1000 x 20 | `e12d9d5def6845c0622634a1cd2ab87fa470668c4298f1ec52a4e403376a435b` (all files incl. OpenML metadata: `results/data_checksums.txt`) | `load_german` |
| Pima diabetes (d=8) | OpenML id 37 (`diabetes` v1, uploaded 2014-04-06) | 2026-11 | Public | 768 x 8 -> 768 x 8 | `fb636382eebd32e0bdff703297be03328a3bd59c4e032b93dd8bfc5a0c92961b` | `load_pima` |
| Give Me Some Credit (d=10) | OpenML 46929 (v1, uploaded 2025-04-30) | 2026-11 | Public | 150000 x 10 -> 20000 x 10 (random subsample, median imputation) | `1de1300406fb2f8ca789f2a8ee38c60d4e699002c8eaa257b87a4ca7d8a64e75` | `load_gmsc` |
| ACS Income (d=10) | folktables ACSIncome, California, 2018, 1-Year, person | 2026-11 | US Census public use (folktables MIT) | -> 30000 x 10 (random subsample) | `dc2187fc90df2c5f6b546ee89a2b41c9a97379c9e7136461b6a6c8de871b43e0` (`psam_p06.csv`) | `load_acs` |
| ACS Employment (d=16) | folktables ACSEmployment, California, 2018, 1-Year, person | 2026-11 | same | -> 30000 x 16 (random subsample) | same file | `load_acs_emp` |

Split: 70/30 stratified train/test (`random_state=seed`, seed 0); background = 50 training rows; the explained instances are 50
random test rows. Categorical attributes are one-hot encoded inside the model wrapper and masked as one attribute.

## 3. Seeds
- Data split, main-model training, background and instance selection: seed 0 (`RandomState(1000)` for background/instances).
- Explainer runs (kernel, kernel with default l1, permutation): run r at budget index b of instance i uses seed `10000*(i+1) + 100*b + r`
  (Kernel via `np.random.seed(seed)` before each call, Permutation via `seed=`). Reference runs: `7000000 + 100*i + r` (German, Kernel at 20000 coalitions);
  retrain-standard Kernel runs (German): `8000000 + 100*k + i`. Seeds are the same function of (i,b,r) in every cell, so cells are not independent in their random-number streams.
  **[measured]** Consequence: for the same dataset (same 50 instances; equal d gives the same coalitions and permutation orders) the run noise of two models is correlated;
  Spearman correlation of the noise between two models of one dataset at one budget, median over model pairs and budgets (`results/tables/seed_correlation.csv`; the null with the run index permuted is 0 within ±0.07):
  Kernel ACS-Income 0.59, ACS-Employment 0.28, Pima 0.17, GMSC 0.11, German 0.05; Permutation 0.33, 0.07, 0.06, 0.03, 0.01.  Cells of one dataset are therefore not independent replicates;
  intervals that pool cells (`c5_hier.csv`) carry a second interval that resamples datasets first.  Between datasets (different instances, different d) no noise is shared.
- Retrain standard: 5 retrains on random 80% subsamples of the training set, seeds 100-104. Background standard: redraws of 50 / 200 rows.
- Bootstrap (analysis): instance-cluster bootstrap, 1000 resamples, seed 12345 (`analysis/`); figures use their own seed, see `figures/README.md`.

## 4. Commands and run time
Two kinds of numbers, kept apart. **Wall-clock** per stage and cell is measured from the cell logs (`results/tables/runtime_cells.csv`, made by `analysis/runtime_from_logs.py` from `results/logs/`);
the host was oversubscribed (load far above its CPU count; our jobs got 0.3-1 core each), so wall-clock overstates compute and is only indicative. **CPU-h** is the world's meter
(`ht-resource status local-compute`, `used.spend`, CPU-seconds of all jobs of this position) **[measured]**; where a line is a difference of meter readings it says so **[estimate]**.
Single calls: `results/tables/timing.csv` (one thread, shared host).

| step | command | wall-clock (sum over cells, from logs) | CPU-h | output |
|---|---|---|---|---|
| timing of single calls | `python3 code/timing.py` | not logged | not metered separately | `results/tables/timing.csv` |
| core grid, all 20 cells (`ref`, `kernel`, `perm`, `retrain`, `bg`) | `bash code/queue.sh "german rf" "german gbm" ...` | 45.2 h (pima 0.7, gmsc 1.8, acs 4.9, german 17.5, acs_emp 20.3; of which `ref` 8.6, `kernel` 17.6, `perm` 9.1, `retrain` 8.5, `bg` 1.3) | about 33-35 [estimate: meter before the extras 56.5 h minus the measured log-odds and German default-l1/enumeration lines below] | `results/raw/<ds>__<model>__{ref,kernel,perm,retrain,bg}.npz` |
| log-odds sensitivity (German lr/gbm, ACS-Employment gbm, Pima gbm; German mlp is counted with the extras) | `bash code/queue_logit.sh "german lr" ...` | 4 cells: 22.2 h (23.6 h with the German mlp cell) | 18.7 [measured, the 4 cells run before the extras] | `results/raw/<ds>_logit__*.npz` |
| German default-`l1_reg` stage and enumeration check (first 3 instances) | `bash code/queue_stages.sh kernell1,refcheck "german lr" "german gbm"` | see `runtime_cells.csv` (`german__{lr,gbm}__extra`) | 4.7 [measured] | `...__kernell1.npz`, `...__refcheck.npz` |
| **extras, not part of the core plan** (see below) | `python3 code/run_cell.py <ds> <model> --stages retrain_f50,retrain_f95,retrain_rep,bgd,refcheck_more,kernell1` | see `runtime_cells.csv` (`*__extra`, `*__rcmore*`) | see the total below | `...__{retrain_f50,retrain_f95,retrain_rep,bgd,refcheckmore_*}.npz` |
| tables | `bash analysis/run_all.sh results/raw results/tables` | about 15 min on 1 core | < 0.5 [measured, 0.13 CPU-h per run] | `results/tables/*.csv` |
| long format | `python3 analysis/export_long.py results/raw results/long` (inside `run_all.sh`) | seconds | negligible | `results/long/*.parquet` |

**Total at the end of the study: 72.5 CPU-h on the meter [measured]** (`used.spend` = 260 845 s when the last extras job ended; plus about 0.15 CPU-h for the final table build), against the 24 CPU-h of the plan.
Split: core grid (20 cells) about 33-35 CPU-h [estimate: the meter before the extras, 56.5 h, minus the measured 18.7 (log-odds) and 4.7 (German default-l1 and enumeration of 3 instances) = 33.1, plus
the part of ACS-Employment mlp that ran after that reading (at most 1.5 h, its logged wall-clock)]; everything else, about 38-39 CPU-h, is extras: log-odds cells 20.1 (measured: 18.7 + German mlp 1.4), default-l1 and the first enumeration check 4.7 (measured),
enumeration of instances 3-13 of German lr/gbm 3.1 (measured), retrain sensitivity for ACS-Employment mlp 1.75 (measured), and the rest of the extras (retrain 50/95 % and second-seed retrains, background redraws, default-l1 for German mlp / ACS-Employment lr) about 9-10 [estimate, by difference].
The excess over the plan is the Kernel/Permutation grids on d >= 16 cells (German and ACS-Employment, up to 12 CPU-h for one cell) and the sensitivity work that the reviews asked for.

**Extras (requested by the reviews, not part of the core plan; the headline claims C1-C5 do not depend on them):** log-odds sensitivity cells, default-`l1_reg` stages, enumeration check,
retrain-standard sensitivity (50 % / 95 % subsamples, second Kernel seed for the d = 20 retrain explanations), reduced background-redraw standard for d > 12 (`bgd`: 3 redraws,
30 instances). All extras that were started finished and are in this delivery (section 6).

### Smoke test (about 15 s)
A small re-run of one cell reproduces the delivered raw results exactly on the shared instances and runs:
```
python3 code/run_cell.py pima lr --n_inst 5 --R 5 --K_retrain 2 --K_ref 2 --m_ref 2000 --out /tmp/smoke
python3 code/smoke_check.py /tmp/smoke pima lr
```
Expected: the first line printed by `run_cell.py` is `pima__lr 0.871440329218107 0.7748917748917749` (test AUC and accuracy of the main model), the last is `done pima__lr <seconds>`, and
`smoke_check.py` prints `kernel max |difference| on (5, 5, 5) = 0.0` and `perm max |difference| on (5, 5, 5) = 0.0` **[measured]**.  A different value means a different shap/numpy/scikit-learn version or data file.

## 5. Table / figure -> script map
Figures and tables of the paper are made by `figures/*.py` from `results/raw` (see `figures/README.md` for the full table);
the numbers cited in the text that are not in a figure come from `results/tables/*.csv` made by `analysis/`:

| item | script | input |
|---|---|---|
| error vs budget, slopes (C1) | `figures/fig_c1.py` | raw `ref`, `kernel`, `perm` |
| top-k match tables (C2) | `figures/tab_c2.py` | same |
| flip vs margin (C2) | `figures/fig_c2_margin.py` | same |
| run-to-run vs retrain/background/null (C3) | `figures/fig_c3.py` | + `retrain`, `bg` |
| repeat vs enlarge (C5) | `figures/tab_c5.py`, `analysis/compute_matched.py` | kernel/perm |
| adequacy fractions with Wilson CI, per-instance diagnostic (C4), SNR bins, timing | `analysis/summarize.py`, `analysis/diagnostic.py`, `code/timing.py` | `results/tables/` |

## 6. Unfinished or failed runs
Final state of the study. **Core grid: complete, 20 of 20 cells** {Give Me Some Credit, ACS-Income, Pima, German Credit, ACS-Employment} x {lr, rf, gbm, mlp}, all analysed (`results/tables/cells.csv`). No core run failed.
**Extras (not part of the core plan): every extra that was started finished and is in the tables**:
- log-odds cells: German lr/gbm/mlp, ACS-Employment gbm, Pima gbm (5 cells, each with Kernel, Permutation and retrain);
- default-`l1_reg` stage (`kernell1`): German lr/gbm/mlp and ACS-Employment lr; enumeration check of the German reference: lr and gbm on 13 instances each;
- 50 % / 95 % retrain subsamples: ACS-Income (4 models), German (4 models), ACS-Employment lr/rf/mlp; second-seed retrain explanations (`retrain_rep`) for the four German cells; 80 % retrains only for GMSC, Pima and ACS-Employment gbm;
- reduced background redraws (`bgd`, d > 12): German x4, ACS-Employment lr/rf.
**Not run (decided for cost, no job exists):** `l1_reg`/log-odds checks on the d > 10 cells other than the ones above, ACS-Employment gbm retrain sensitivity and background redraws, a bootstrap-retrain variant, 50 %/95 % retrains for GMSC and Pima.
Not done (optional in the plan): TreeSHAP / tree-explainer comparison, Covert-Lee covariance diagnostic comparison, Arrhythmia stress test, German budgets beyond 5000.
Known numerical failures: Kernel SHAP at the smallest budgets occasionally returns a numerically singular solution (relative error >10); the share is stored as
`blowup_frac` in `budget_curve.csv`, and the error summaries therefore also report the median (`relerr_med`).
**Raw directory**: `results/raw` is about 67 MB (npz, compressed); I recommend delivering it (it is the input of every table and of the long format and is small next to the data it replaces); `results/long/*.parquet` can be regenerated from it by `analysis/export_long.py`.

## 7. Forbidden-material log
None encountered so far. Sources consulted for the experiments: shap documentation/source code (installed package), UCI/OpenML/folktables
dataset pages and the Census file. No search about the withheld question was run by this position.

## 8. AI-use disclosure
See the AI-use statement section of the paper (`paper/sections/ai_use.tex`).
