# Reproduction notes (experiment-repo)

Everything below regenerates every number in `results/`. Figures/tables of the paper are produced by the scripts of
`figtab-repo` from `results/tables/*.csv` (they are not generated here).

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1 (not used by the experiments), torch 2.14.1+cpu
(used only for Dirichlet-regression MLE and the CIFAR CNN), Pillow, pyarrow. CPU only; 2 CPUs per job; no GPU.
No package beyond the preinstalled research stack was needed (no `torchvision`: CIFAR images are decoded with Pillow).

## Data and licences
* **Synthetic data**: generated in `code/cpsimplex/dgp.py` (fixed population coefficients, `coef_seed=12345`); no external data.
* **CIFAR-10** (Krizhevsky 2009, *Learning Multiple Layers of Features from Tiny Images*; the page states no licence, asks for
  citation of the technical report; no account). Obtained as the parquet copy of the Hugging Face dataset `uoft-cs/cifar10`
  (`plain_text/train/0.parquet`, `plain_text/test/0.parquet` via `https://huggingface.co/api/datasets/uoft-cs/cifar10/parquet/plain_text/{train,test}/0.parquet`);
  the official toronto.edu archive (`cifar-10-python.tar.gz`, md5 `c58f30108f718f92721af3b95e74349a`) answered HTTP 200 but the download stalled, so it was
  not used. md5 of the parquet files used: train `7170dcdaf6355deedaa01d9915ae0d31`, test `a52165db3ae649545cf55cf1791cd12d`
  (50000 + 10000 images, 10 classes). The parquet copy and the official archive are the same 60000 images; we did not verify
  this by checksum of the pixel content.
  Place the files at `/hutian/data/cifar/{train,test}.parquet`.

## Seeds
Replication `i` of an experiment uses RNG seed `seed0 + i` (`seed0` given in each launcher: A1 1000, A2 50000, A4 7000, A5 9000,
B 0; the B-synth pool for replication `i` is generated with seed `10000 + i`). The DGP coefficients and the ground-truth grid
(seed 777) are fixed within a configuration. The CNN uses seed 0 (`torch.manual_seed`, numpy `default_rng(0)`; multi-threaded
CPU kernels are not bit-reproducible, so retrained logits may differ slightly; the logits used are committed as
`results/cifar_logits.npz`, 1 MB).

## Commands (all from the repository root; every raw CSV records `git_rev`, config and seeds)
Raw CSVs are stored gzip-compressed (`results/raw/*.csv.gz`); the analysis scripts read `.csv` and `.csv.gz` alike.
| step | command | output | wall time* |
|---|---|---|---|
| A2 coverage law | `bash code/run_a2.sh {dirichlet,logisticnormal} {20,50,100,200,500,2000} 2000` | `results/raw/A2_*` | 15-40 min per file |
| A2 extensions (alpha, K, rounding) | `bash code/run_manifest.sh code/manifest_a2.txt P 4` (P=0..3) | `results/raw/A2x_*` | ~1.5 h per part |
| A2 tie case | `bash code/run_a2tie.sh {olsmean,constmean}` | `results/raw/A2tie_*` | ~40 min each |
| A1 grid (20 configs) | one line of `code/manifest_chunk_0*.txt` per run: `bash code/run_a1.sh TAG REPS CONFIG` | `results/raw/A1_*` | 0.5-6 h per config (volume computation dominates; K=10 slowest) |
| A1 Mahalanobis add-on | `bash code/run_a1m.sh P` (P=0..3) | `results/raw/A1m_*` | ~1 h per part |
| A1 delta sensitivity | `bash code/run_a1d.sh` | `results/raw/A1d_*` | ~30 min |
| A3 half-split | `bash code/run_a3hs.sh I` (I=0..7) | `results/raw/A3hs_*` | 0.5-2 h each |
| A3 plug-in Prop. 2 | `bash code/run_a3pi.sh I` (I=0..7) | `results/raw/A3pi_*` | ~10 min each |
| A6 mean misspecification | `bash code/run_a6.sh I` (I=0..3) | `results/raw/A6_*` | ~5-15 min each |
| A4 covariate shift | `bash code/run_a4.sh` | `results/raw/A4_*` | ~1 h |
| A5 split vs CV+/jackknife+ | `bash code/run_a5.sh {dirichlet,logisticnormal}` | `results/raw/A5_*` | n = 30, 50, 100, 200 (jackknife+ not at 200), 100 reps |
| B-synth | `bash code/run_b_synth.sh` | `results/raw/B_synth_*` | ~1 h |
| CIFAR CNN | `python3 code/train_cifar.py 15 0` | `results/cifar_logits.npz` | ~4 h (CPU, loaded host) |
| B-cifar | `bash code/run_b_cifar.sh` | `results/raw/B_cifar_*` | ~5 min per config |
| tables | `python3 code/analyze_a2.py; analyze_a1.py; analyze_a1.py A1m; analyze_a1.py A1d; resolve_a1.py; analyze_a3.py; analyze_a3_biasrank.py; analyze_a3hs.py; analyze_a3_flip.py; analyze_a3pi.py; analyze_a1.py A6; analyze_a6.py; analyze_a45.py; analyze_b.py; certify_n.py; prop2_table.py` | `results/tables/*` | minutes (analyze_a3.py ~10 min) |
\*host was heavily loaded; idle-host times are several times shorter. Launch the long steps as background jobs (`ht-resource run`).

Provenance note: `git_rev` in a raw CSV is the HEAD commit when the run started; for the A2 rerun, A1m, A1d, A2tie and A3hs runs the working tree
also held uncommitted edits that were committed afterwards unchanged (adding the `maha` score, `halfsplit` and `const_mean` options and the n_te/alpha arguments of `run_a2.sh`); none changes the
code path of earlier runs (checked: the euc, aitch and dirnll columns of `A1m_*` equal those of `A1_*` to the last digit).

## Incidents and discarded runs
* A first A1 grid used 30 evaluation x-points per slab; the ground-truth conditional coverage was too noisy, so it was discarded and the grid rebuilt with 300 x-points x 30 y-draws (Grid defaults). No number from it is used.
* A first B-synth run estimated size-stratified coverage without a minimum cell count (error 0.1-0.2 from tiny cells); discarded; the rerun applies the minimum-30-cell rule (`ssc30_*` columns).
* The first A2 raw files (older harness: no `alpha`/`n_te`/`git_rev` columns; n_te=2000, alpha=0.1 were the defaults) were replaced by a rerun with explicit `n_te=2000`, `alpha=0.1`, `n_tr=500` (`run_a2.sh`); the rerun draws differ (different harness), the conclusions do not.
* The first DGP had extreme means (coefficient scale 0.8, oracle HPD volume zero in the Monte-Carlo sample); coefficient scale was set to 0.4 and only x-points with oracle fraction >= 20/M enter volume ratios.
* A3hs jobs 0-5 and 7 were reported as failed by the scheduler: `run_a3hs.sh` was edited (new cases appended) while they were running, which made the shell stop after the Python process had written its complete CSV; all 8 CSVs have 1000 replications.

* `A3_rank_blocks.csv` was first computed with disjoint blocks of size R up to nrep/2; for R = nrep/2 the two blocks partition the pool and are anticorrelated by construction (tau of the marginal-coverage gap -0.11 at R=100). `analyze_a3.py` now uses R <= nrep/4 (R=50 for the 200-replication configs only), draws block pairs from their own random stream and records `nrep`; the other A3 tables are unchanged except for Monte-Carlo noise (< 0.002) in `pred_mc`. The 1000-replication pools of A3hs give `A3hs_rank_blocks.csv` for R up to 100.
* The first version of `analyze_a3pi.py` defined the oracle bias as formula minus the observed estimate instead of formula minus the true minimum; found before any number was used, fixed, and the table regenerated.
* A3pi reruns the A3hs configurations with the same seeds and `cells=True`; all compared columns (q, true and estimated worst cells, half-split, marginal coverage) are identical to A3hs (max abs difference 0.0).

## Script -> result map
* Prop. 1/C1,C2: `analyze_a2.py` -> `A2_beta_law.csv`; `certify_n.py` -> `certify_n.csv` (C1(c) certification).
* C3-C5: `analyze_a1.py` -> `A1_summary.csv`, `A1_paired_vs_euc.csv` (+ `A1m_*` Mahalanobis add-on, `A1d_*` delta sensitivity); `resolve_a1.py` -> `A1_resolved.csv`.
* C6-C8: `analyze_a3.py` -> `A3_bias.csv` (estimated minus true worst-cell coverage), `A3_pred_bias.csv` (exact/MC/normal prediction, Prop. 2),
  `A3_rank_blocks.csv`, `A3_rank_single.csv` (ranking stability), `A3_paired_unpaired.csv`; `analyze_a3_biasrank.py` -> `A3_bias_rank.csv`; `analyze_a3hs.py` -> `A3hs_bias.csv`, `A3hs_rank.csv`; `prop2_table.py` -> `prop2_equal_cells.csv`.
* C7 additions: `analyze_a3_flip.py` -> `A3_flip_pairs.csv`, `A3_flip_bins.csv`, `A3_flip_threshold.csv` (pairwise mis-ranking by true gap); `analyze_a3hs.py` -> `A3hs_rank_blocks.csv`.
* C13: `analyze_a3pi.py` -> `A3pi_pred_bias.csv`, `A3pi_summary.csv`, `A3pi_rank.csv`. C14: `analyze_a1.py A6` -> `A6_summary.csv`, `A6_paired_vs_euc.csv`; `analyze_a6.py` -> `A6_vs_A1.csv`, `A6_rank_agreement.csv`.
* C9, C10: `analyze_b.py` -> `B_summary.csv`, `B_paired_vs_lac.csv`, `B_ssc_bias.csv`.
* C11, C12: `analyze_a45.py` -> `A4_summary.csv`, `A5_summary.csv`, `A5_paired_vs_split.csv`.
* `results/CLAIMS_MAP.md`: claim -> file -> number -> uncertainty.
`results/STATUS.md` states which experiments are finished.

## Forbidden-material record (deliverable.md)
* experiment-repo ran **no literature searches** (only the starter list and the plan/brief of other positions were used).
* idea-repo (Brief §4, incident log): while running a broad OpenAlex search for conformal/multivariate/Dirichlet topics on 2026-11-04 a listing surfaced
  whose title is a conformal-prediction paper on compositional data with Dirichlet regression (query: "Conformal prediction regions for multivariate response
  Mahalanobis split conformal"); only the title and about 600 characters of the abstract snippet were seen; the page was not opened and nothing from it
  was used; it is treated as possibly the forbidden paper and excluded.
* paper-repo (issue #4 of this repository): on 2026-11-04 searches on APS/LAC, conditional-coverage limits, multivariate-response conformal; nothing about
  compositional/Dirichlet conformal surfaced in those listings.
