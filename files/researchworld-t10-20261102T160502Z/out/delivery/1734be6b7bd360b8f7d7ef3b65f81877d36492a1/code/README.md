# Code, results and reproduction notes — fixed-input CI width (prediction-powered inference)

Question: with labeled set, unlabeled set and predictor all fixed, can a valid 95% interval for a population mean be
shorter than PPI++ (`ppi-python` 0.2.3), by how much, and when?  Estimand: E[Y]. Information used by every method:
labeled (Y, f) and unlabeled f only (covariates X of census sets are *not* used).

## Layout
| path | content |
|---|---|
| `src/estimators.py` | classical, PPI, PPI++ (own implementation, checked against `ppi_py`), cross-fitted calibrated-score PPI++ (`cal_ppi`; `lin/iso/bin/spl` maps), delete-one jackknife PPI++ (`ppi_jackknife`), conformal wrapper |
| `src/data.py` | dataset access (`ppi_py.datasets`), synthetic populations with known truth |
| `src/grids.py` | the cell lists (population, n, N, R) of every study |
| `src/sim.py` | Monte-Carlo driver (one cell = population × n × N × R replicates; all methods share the same draws) |
| `src/analyze.py` | raw endpoints → summary CSVs (columns below) |
| `src/theory.py`, `src/theory_check.py` | Q1 population floors / predicted ratios; predicted vs observed on the synthetic grid |
| `src/sim_boot.py` | bootstrap (percentile, studentized) PPI++ ablation |
| `src/full_data.py` | one realisation at native dataset sizes (no coverage claim) |
| `theory.md` | derivation of the efficiency floor, assumptions and scope |
| `tests/` | `check_vs_ppi_py.py` (own PPI/PPI++ vs package), `test_jackknife.py` |
| `results/` | all CSVs used in the paper; `frozen_choices.json` records the pre-final choice of M4/M5 |
| `run_all.sh` | final-space reproduction of everything |

## Environment
Python 3.11.2; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, statsmodels 0.15.0, ppi-python 0.2.3, gdown 6.5.1 (`requirements.txt`). CPU only, 2 cores.

## Data (versions)
`pip install ppi-python==0.2.3` (tag v0.2.3, commit 6b8475b). Files are fetched by the package from Google Drive into `./data/<name>.npz`:
`python -c "from ppi_py.datasets import load_dataset as L; [L('./data/', n) for n in ['galaxies','forest','alphafold','gene_expression','census_income','census_healthcare','census_education','plankton','ballots']]"`
(46 MB; no account). `data/` is git-ignored. No other data used. The `.npz` files carry no separate licence statement (original sources: `ppi_py` example notebooks).

## Sampling model
Pool of each dataset = population, truth = pool mean of Y. Labeled and unlabeled records are iid draws *with replacement* from the pool (independently), so
n/pool does not enter; n ≤ pool/5 (forest ≤ 200, ballots ≤ 200 here). ballots: pool = its 1027 labeled records (the real 78 150 unlabeled predictions have no labels, so no truth).
plankton shift: labeled drawn from 2013 labeled pool, unlabeled from the 2014 predictions, truth = mean of 2014 labels; control = both from 2013. Synthetic: `src/data.py::synth_sampler`.
Forest ablation `forest_wor`: labeled draws without replacement.

## Methods (names in the CSV `method` column)
M1 `classical` (z), M2 `ppi` (λ=1), **M3 `ppipp_pkg`** = `ppi_py.ppi_mean_ci` default (λ̂ clipped to [0,1], ddof=0, z; the reference),
M4 `cal_iso` = PPI++ on out-of-fold isotonic scores g(f) (5-fold cross-fitting; labeled use out-of-fold g, unlabeled fold-averaged g; λ̂ power-tuned) — chosen on dev synthetic runs (`results/frozen_choices.json`),
M5 `ppipp_jk` = M3-type estimator with delete-one jackknife SE and t(n−1); M5 on M4 = `cal_iso_t`.
Ablations/controls: `classical_t`, `ppipp` (own M3, ddof=1, clipped), `ppipp_t`, `ppipp_nc` / `ppipp_nc_t` (unclipped λ̂), `cal_lin` (cross-fit with an affine map: isolates the pure cost of cross-fitting), `cal_spl`, `cal_bin`, `*_t` (t critical value), bootstrap (`sim_boot.py`).
Conformal (`ppi_py.baselines.conformal_mean_ci`, Bonferroni): returns (−∞, ∞) whenever (1−α/N)(1+1/n) > 1, i.e. unless n ≥ N/α − 1 — never for N=20n (needs n ≥ 20N); not simulated.

## Seeds
`SeedSequence([space, sha256(population|n|N|shift|wor)[:8]])`, `space` 0 = dev, 1 = final (disjoint); all methods use the same draws within a cell. Dev runs: pilot (`--grid pilot --space dev`, R=2000) and `--grid synth --space dev --R 500`.

## Commands
```
bash run_all.sh      # final: theory, grids real_primary shift forest_wor real_nsweep real_appendix synth, bootstrap, analyze, theory_check, full_data
python tests/check_vs_ppi_py.py ; python tests/test_jackknife.py
```
Runtime: see section "Measured runtimes" at the end (filled from the logged final run).

## Summary CSV columns (`results/summary_final_<grid>.csv`)
`population` (dataset name or `syn:<kind>:<kappa>:<snr>:<tail>`), `n`, `N`, `tag`, `space`, `R`, `method`,
`coverage` (+ `cov_lo`, `cov_hi` Wilson 95%, `mc_se` binomial), `width_mean`, `width_median`, `frac_infinite`,
`ratio_M3_geo/lo/hi` (paired geometric-mean width ratio vs M3 on the same draws, bootstrap 95% CI over replicates), `ratio_nc_*` (vs unclipped PPI++),
`frac_shorter_M3`, `frac_degenerate` (zero-width draws excluded from ratios), `theta` (truth).
Grids → files: `real_primary`, `real_appendix`, `real_nsweep`, `shift` (tags `shift` and `control`), `forest_wor`, `synth` (tags kappa, n, Nratio, snr, tail, bin_n).
Other CSVs: `theory_population.csv`, `theory_predicted_ratios.csv`, `theory_check_synth_final.csv`, `sim_boot.csv`, `full_data_intervals.csv`, dev: `summary_dev_*.csv`.

## Forbidden-content log
No page of the withheld paper or any page citing/discussing it was searched, opened or read by experiment-repo. Literature consulted: starter list items (Brief from idea-repo) and the ppi-python 0.2.3 source. (idea-repo logged one generic search returning titles/snippets; not opened here.)

## Measured runtimes
Final run (R=2000, all grids, `local-compute` jobs with 2 CPUs each, grids in parallel): simulation wall-clock ≈ 2 h (first to last raw file 22:37–00:30), analysis + bootstrap ablation a few minutes. Dev synthetic run (R=500, 45 cells) and the dev pilot were run before the final runs. Raw per-replicate `.npz` (≈60 MB, `results/raw_final_*`) are git-ignored and regenerated by `run_all.sh`.

## Note on `full_data_intervals.csv`
Regenerated with the final code (the `cal_bin` rows changed in the 3rd–4th decimal relative to the earlier commit because the binned calibrator was made tie-safe afterwards); rerunning `src/full_data.py` reproduces the committed file. It is descriptive only (one random 10%/90% split, seed 0).
