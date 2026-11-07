# Reproduction notes

All numbers in the paper come from the CSVs in `results/`, produced by the scripts below from the code in `src/cpc/`. Figures and tables are produced by `figtab-repo` generators from these CSVs (see Exhibit map).

## Environment
Python 3.11.2; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, torch 2.14.1 (CPU), pyarrow 26.0.0, Pillow 13.0.0, matplotlib (sandbox image). Everything runs on CPU: sandbox/jobs have 2 CPUs and 4 GB; the host was heavily shared, so wall-clock times below are those of an unloaded 2-CPU job (indicative, from pilot timings).
Install: the scientific stack is the sandbox's `research-packages` image; nothing else is needed (`pip` not required).

## Data
- **CIFAR-10** (Krizhevsky 2009, *Learning Multiple Layers of Features from Tiny Images*; no licence stated; cite the technical report). The official Toronto archive returned HTTP 404 through the world proxy, so the Hugging Face copy was used: `https://huggingface.co/datasets/uoft-cs/cifar10`, revision `0b2714987fa478483af9968de7c934580d0bb9a2` (card license field `unknown`), files `plain_text/train-00000-of-00001.parquet` (119 705 255 B) and `plain_text/test-00000-of-00001.parquet` (23 940 850 B). Download to `/hutian/data/cifar/`.
- **CIFAR-10H** (Peterson, Battleday, Griffiths, Russakovsky 2019, human label distributions for the CIFAR-10 test set): `https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-probs.npy` (10000x10, float64, 800 128 B) to `/hutian/data/c10h/c10h.npy`. No licence stated in the repository as retrieved. Row order verified against the CIFAR-10 test labels: argmax of CIFAR-10H agrees with the Hugging Face test labels for 99.21% of images.
- **Synthetic**: generated in `src/cpc/data.py` (fixed regression function per configuration, seed 0; fresh samples per replicate seed).

## Seeds
E1 / E4: replicate `r` uses `np.random.default_rng(seed0 + r)`, `seed0 = 0` (extension files: `seed0 = 100`); the regression function of a configuration is fixed (`World(..., seed=0)`). E2/E3: replicate `r` uses `default_rng(seed0 + r)`, `seed0 = 0`. CNN: `torch.manual_seed(0)`. Theory: `default_rng(2024)` (T1/T4), null simulation `default_rng(777)`.

## Commands (run from the repository root)
| Step | Command | Output | Expected time (2 CPUs, unloaded) |
|---|---|---|---|
| Download data | see Data (curl/HF resolve URLs above) | `/hutian/data/...` | 1-2 min |
| Train CNN | `python3 scripts/train_cnn.py` | `results/e23/cnn_logits_ep{2,12}.npy`, `cifar10_test_labels.npy` (final test acc. 0.8806 at epoch 12, 0.7403 at epoch 2) | ~25 min |
| E1 main grid | `bash scripts/e1_main.sh` (48 configs x 100 reps, 2 workers) | `results/e1/main_<family>_D<D>_h<h>_<pred>.csv` | ~1.5-3 h |
| E1 sensitivity | `bash scripts/e1_sens.sh` | `results/e1/sens_eps*`, `sens_ncal*` | ~1-2 h |
| E2/E3 | `bash scripts/e23_all.sh` | `results/e23/e2_*.csv`, `e2_*_ident.csv`, `e3_*.csv` | ~1 h |
| E4 shift | `bash scripts/e4_shift.sh` | `results/e4/shift_*.csv` | ~20 min |
| Theory | `python3 scripts/run_theory.py` | `results/theory/*` | ~10 min |
| Null simulation | `python3 scripts/run_null.py` | `results/null/null_binned.csv` | ~2 min |
| Summaries | `python3 scripts/aggregate.py` | `results/*_summary.csv`, `results/e2_ident_summary.csv` | <1 min |
Single replicate smoke test: `python3 scripts/run_e1.py --family dirichlet --D 5 --hetero 1 --pred linear --reps 1 --out /tmp/t.csv`.
Column definitions and the claim each file supports: `results/README.md`.

## Exhibit map
Generators are in `figtab-repo/figtab/` (run from a checkout of this repository placed at `../../experiment-repo` or with `CPC_RESULTS=<path>`; outputs are stamped with the experiment-repo commit). Seeds/runtime are those of the result file.

| Exhibit | Generator (run in `figtab-repo/figtab/`) | Result files read | Claim | Seeds | Runtime |
|---|---|---|---|---|---|
| Fig 1 Beta law (`fig1_beta_law.pdf`) | `fig1_beta.py` | `theory/t1_beta_law.csv` | C1 | `default_rng(2024)` | generator 5 s; `run_theory.py` ~5 min |
| Fig 2 region size, `pool_frac` (`fig2_size.pdf`) | `fig2_size.py main_dirichlet_D3_h1_linear main_dirichlet_D5_h1_linear main_dirichlet_D10_h1_linear main_rounded_D10_h1_linear` | those four `e1/main_*.csv` of the final 48-config grid (`pool_frac`) | C2, C4 | reps 0-99 | generator ~7 s |
| Fig 2 appendix, Lebesgue volume (`fig2_size_volume.pdf`) | `SIZE_METRIC=vol_med python3 fig2_size.py main_dirichlet_D3_h1_linear main_dirichlet_D5_h1_linear main_lognormal_D5_h1_linear main_rounded_D5_h1_linear` | those four `e1/main_*.csv` (`vol_med`, D<=5 only) | C2 (robustness of the size metric) | reps 0-99 | ~7 s |
| Fig 3 conditional coverage (`fig3_conditional.pdf`) | `fig3_cond.py main_dirichlet_D5_h0_linear main_dirichlet_D5_h1_linear main_lognormal_D5_h1_linear main_multinomial_D5_h1_linear main_rounded_D5_h1_linear` | those five `e1/main_*.csv` (`or_*`, `ymax_*`, `wsc`), null band from `null/null_binned.csv` | C3, C5 | reps 0-99; null 777 | generator seconds |
| Fig 4 n_cal / schemes (`fig4_ncal.pdf`) | `fig4_ncal.py` | `e1/sens_ncal*_{dirichlet,lognormal}.csv`, `e1/main_{family}_D5_h1_linear.csv` | C4, C6 | reps 0-99 | seconds |
| Fig 5 null spread (`fig5_null_spread.pdf`) | `fig5_null.py` | `null/null_binned.csv` | C5 | 777 | generator seconds; `run_null.py` ~2 min |
| Fig 6 delta method (`fig6_delta_method.pdf`) | `fig6_delta.py` | `theory/t4_points_*.csv`, `theory/t4_cond_coverage.csv` | C6 | 2024 | `run_theory.py` ~5 min |
| Fig 7 covariate shift (`fig7_shift.pdf`) | `fig7_shift.py` | `e4_summary.csv` | C10 | reps 0-99 | E4 run |
| Fig 8 Aitchison eps sensitivity (`fig8_eps_sensitivity.pdf`) | `fig8_eps.py` | `e1/sens_eps*_{dirichlet,multinomial,rounded}.csv`, `e1/main_{family}_D5_h1_linear.csv` | C5 | reps 0-99 | generator ~7 s; `e1_sens.sh` for the data |
| Table 1 methods (`tab1_methods.tex`) | `tab1_methods.py` | none (static) | - | - | - |
| Table 2 headline (`tab2_e1_headline.tex`) | `tab2_e1_headline.py` (default: dirichlet and lognormal, D=5, heteroscedastic, linear) | `e1/main_*.csv` of those configs | C2, C3 | reps 0-99 | seconds |
| Tables A (appendix grid, `tabA_e1_grid_{dirichlet,lognormal,multinomial,rounded}.tex`) | `tab_a_grid.py` | all 48 `e1/main_*.csv` | C2, C3 (whole grid) | reps 0-99 | generator ~5 s |
| Table 3 CIFAR-10 sets (`tab3_e2_labelsets.tex`) | `tab3_e2.py` | `e2_summary.csv`, `e2_ident_summary.csv` | C7 | reps 0-199 | E2 run |
| Table 4 CIFAR-10H (`tab4_e3_cifar10h.tex`) | `tab4_e3.py` | `e3_summary.csv` | C8 | reps 0-99 | E3 run |

The E1 result files are those of `scripts/e1_main.sh` (48 configurations x 100 replicates, `results/e1/main_<family>_D<D>_h<hetero>_<predictor>.csv`; summaries with 95% t-intervals in `results/e1_main_summary.csv`). `figtab/fig_e1_config.py` is working material and not a delivered exhibit. Generator timings were measured on the final results in this repository (CPU, loaded host).

Other positions' exhibit rows may be added here by pull request.

## Accidental-encounter statement (forbidden material)
`experiment-repo` ran no literature or web searches and opened no paper pages; no forbidden material was encountered by this position. The log of `idea-repo` (wiki page `EncounterLog`, 2026-11-02) records no encounter either.

## Deviations and failed runs (as recorded)
- First `ait2` theory run failed (Cholesky error for a numerically singular covariance), fixed with an eigendecomposition and rerun.
- A first 100-rep E1 grid (without oracle pointwise coverage and `pool_frac`) and a 200-rep attempt stopped after one config were discarded; the final grid was regenerated with the final code.
- The first T1 Beta-law run drew calibration sets from a finite pool, which made KS p-values spuriously small at n=500; rerun with fresh calibration data and a 2e6-point test pool (the reported file).
- RAPS regularisation (lambda=0.01, k_reg=2) is not tuned.
