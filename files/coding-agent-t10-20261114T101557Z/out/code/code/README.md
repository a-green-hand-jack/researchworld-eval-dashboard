# Reproduction notes

Code for the paper on shortening prediction-powered confidence intervals with a fixed labeled set,
unlabeled set and predictor. Everything in the paper is produced by `run_main.sh` followed by
`make_tables.py` and `make_figures.py`.

## Environment

- Hardware used: 40 visible cores, but a **cgroup quota of 4 CPUs** (`/sys/fs/cgroup/cpu.max` = 400000/100000).
  All timings below are for a 4-CPU quota.
- Python 3.11.2, packages pinned in `requirements.txt` (numpy 2.4.6, scipy 1.17.1, pandas 3.1.1,
  scikit-learn 1.9.1, ppi-python 0.2.3, gdown 6.5.1, matplotlib 3.11.2, statsmodels 0.15.0).
- Create the environment with:
  `python3 -m venv /work/venv && /work/venv/bin/pip install -r requirements.txt`
- `gdown` must be on `PATH` when the first dataset is downloaded (the `ppi_py` loader shells out to it):
  `export PATH=/work/venv/bin:$PATH`.

## Data

- Real data: the example pools shipped with `ppi-python==0.2.3` (GitHub tag `v0.2.3`). They are downloaded
  automatically by `ppi_py.datasets.load_dataset('/work/data/', name)` from Google Drive, one file each, into
  `/work/data/*.npz` (nine files, about 48 MB in total). Files used: `galaxies`, `forest`, `gene_expression`,
  `alphafold`, `census_income`, `census_healthcare`, `census_education`. `plankton` and `ballots` are not
  used for coverage (see paper, Section 4).
- Synthetic data: generated in `synth.py` (synthetic truth is computed by Monte Carlo with a fixed seed).
- No paid APIs, no accounts. The folktables/ACS data was not used.

## Scripts

| Script | What it does | Output |
| --- | --- | --- |
| `ppi_flex.py` | Estimators (classical, PPI, PPI++, stratified PPI, cross-fitted calibration) and real-data loader | — |
| `synth.py` | Synthetic DGPs and Monte Carlo truth | — |
| `tests/test_identities.py` | Sanity checks (PPI++ identity, oracle efficiency, cross-fit unbiasedness) | stdout |
| `run_synth.py --stage dev` | Development grid (seed offset 10^6), used only to choose the primary learner | `results/synth_dev.csv` |
| `run_synth.py --stage main` | Main synthetic grid (500 reps per cell) | `results/synth_main.csv` |
| `run_real.py --stage main` | Main real-data grid (300 reps per cell) | `results/real_main.csv` |
| `theory_pool.py` | Pool-level efficient-bound quantities for each real pool | `results/theory_pool.csv` |
| `theory_check.py` | Oracle / perturbed-calibrator Monte Carlo against the variance formulas (3000 reps) | `results/theory_check.csv` |
| `summarize.py` | Coverage, widths, width ratios | `results/*_summary.csv` |
| `make_figures.py` | Figures | `paper/figures/*.pdf` |
| `make_tables.py` | LaTeX tables | `paper/tables/*.tex` |
| `run_main.sh` | Full pipeline in order | logs in `results/run_main.log` |

Development notes (kept for transparency): `results/synth_dev.csv` was produced with 100 reps per cell
and the **naive** stratified-PPI variance (strata weights treated as known). That variant undercovers, so it
was replaced; the dev rows for `sppi` are therefore not used anywhere in the paper.

## Seeds

- Synthetic main: `np.random.default_rng(seed)` with `seed = 0 + 7919*rep + 104729*n + 13*ratio + scenario_index*1000003`
  (mod 2^32). Dev uses the same formula with offset 10^6.
- Real main: `np.random.default_rng([0, config_index, n, ratio, rep])` (dev uses offset 10^6 in the first entry).
- Cross-fitting folds: `np.random.default_rng(seed).permutation`, with `seed = rep` for synthetic and real data.
- Theory check: `np.random.default_rng([20260301, scenario_index, n, ratio, info_index])`; population constants use seed 11.

## Runtime (4-CPU quota)

- `tests/test_identities.py`: about 10 s.
- `run_synth.py --stage dev --reps 100`: about 29 min.
- `run_synth.py --stage main --reps 500`: about 100 min (37,500 cells).
- `run_real.py --stage main --reps 300`: see `results/run_main.log` for the actual time (about 49,500 cells).
- `theory_pool.py`: a few minutes (cross-fitted gradient boosting on each full pool).
- `theory_check.py`: a few minutes.

## Which script produces which paper element

| Paper element | Produced by | Inputs |
| --- | --- | --- |
| Figure 1 (`fig_synth.pdf`) | `make_figures.py synth` | `results/synth_main_summary.csv`, `results/theory_check.csv` |
| Figure 2 (`fig_real.pdf`) | `make_figures.py real` | `results/real_main.csv`, `results/theory_pool.csv` |
| Appendix figure (`fig_theory.pdf`) | `make_figures.py theory` | `results/theory_check.csv` |
| Table 1 (real pools, main) | `make_tables.py real` (`tab_real_main.tex`) | `results/real_main.csv`, `results/theory_pool.csv` |
| Table 3 (calibrator sensitivity, real) | `make_tables.py real` (`tab_real_sensitivity.tex`) | `results/real_main.csv` |
| Pool constants (kappa, bounds) | `make_tables.py real` (`tab_pool_constants.tex`) | `results/theory_pool.csv` |
| Table 2 (synthetic, main) | `make_tables.py synth` (`tab_synth_main.tex`) | `results/synth_main_summary.csv`, `results/theory_check.csv` |
| Theory-check table | `make_tables.py synth` (`tab_theory_check.tex`) | `results/theory_check.csv` |
| Large-n paragraph | `run_real.py --ns 5000 20000 --ratios 4 ...` | `results/real_largen.csv` (summarize by `summarize.py`) |
| Learner choice numbers (appendix) | `run_synth.py --stage dev` | `results/synth_dev.csv` (100 reps; the naive stratified rows are superseded) |

Note: the large-n numbers quoted in the text were read from `results/real_largen.csv` with `summarize.summarize`
and the bound formula in `make_tables.bound_ratio`; they are not written to a table file.
