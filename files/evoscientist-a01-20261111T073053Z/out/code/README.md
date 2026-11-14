# Minimum targeted investment to top a multi-task leaderboard, by aggregation rule

Paper: `paper/main.pdf` (LaTeX: `paper/main.tex`, NeurIPS 2026 template `paper/neurips_2026.sty`, checklist in `paper/checklist_filled.tex`).
Everything in the paper is produced by the scripts below; `results/` holds the raw outputs (CSV).

## Environment
Python 3.11.15; numpy 2.4.6, scipy 1.17.1 (HiGHS MILP solver), pandas 3.0.6, matplotlib 3.11.2, pyarrow 26.0.1 (PyMuPDF only for previewing the PDF). LaTeX: pdflatex + bibtex (TeX Live 2025). CPU only. No GPU, no paid API.

## Data (public, no account) and versions
| Board | Source | Version |
|---|---|---|
| HELM-MMLU | `https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (303 files; `summary.json` date 2025-01-10) | v1.13.0 (the version prescribed in the brief) |
| OLLB-6 | `huggingface.co/datasets/open-llm-leaderboard/contents`, `data/train-00000-of-00001.parquet` | commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (2025-03-20) |
| OLLB-BBH24 | `huggingface.co/datasets/open-llm-leaderboard/results` (latest `results_*.json` of each model directory: 4,467 files downloaded) | commit `aa81ecc38fdc5708254b833923368970efdf5ef5` (2025-03-15) |

Checksums: `data/MANIFEST.json` (HELM + parquet, written by `00_download.py`) and `data/MANIFEST_full.json` (all 4,900 files incl. processed CSVs, written by `00c_manifest.py`).
Licences: HELM code is Apache-2.0; no licence statement found for the HELM score data, the OLLB `results` dataset (no card) or the `contents` card (no licence field; per-model `Hub License` column). Only aggregate scores are used; raw data are not redistributed (scripts download them; `data/` can be deleted and rebuilt).

## Reproduce (from the repository root)
```
pip install numpy scipy pandas matplotlib pyarrow
python code/00_download.py            # HELM release + OLLB parquet + checksums            (~1 min)
python code/00b_download_ollb_results.py   # OLLB results JSONs, rate-limited by the hub (HTTP 429 back-off) (~25 min)
python code/01_build_matrices.py      # HELM 79x57 matrix, OLLB-6 table                    (seconds)
python code/01b_build_bbh.py          # OLLB-BBH24 matrix (4,496 models with all 24 subtasks before de-dup)
python code/00c_manifest.py           # full checksum manifest
python code/test_lib.py               # exactness tests of all solvers vs brute force / SLSQP (~5 min), output: results/test_lib_output.txt
python code/02_main.py helm ollb6 bbh24    # main sweep: rank x rule x cap                 (~3 min, 20 processes)
python code/02b_common_targets.py     # paired design on common targets                    (~13 min, 20 processes)
python code/02c_paired_tests.py       # Wilcoxon + Holm + bootstrap on the paired design   (< 1 min)
python code/03_noise.py               # score-noise bootstrap on HELM, 100 draws           (~15 min, 20 processes)
python code/04_subsample.py           # task-subsampling on HELM, 4 sizes x 60 draws        (~15 min, 14 processes)
python code/05_synthetic.py           # synthetic latent-factor boards                      (~40 min, 14 processes)
python code/06_calibration.py         # gain caps from observed fine-tuning pairs + feasibility
python code/07_descriptives.py        # board descriptives, incumbents, Kendall tau
python code/09_case_study.py          # Benchmaxx case study
python code/08_figures.py && python code/10_tables.py    # figures (paper/figs) and LaTeX tables (paper/tables)
python paper/make_checklist.py
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
Run times are wall-clock on a shared 40-core machine (not measured as CPU time); the total is roughly 20 CPU-hours, higher than the 4 CPU-hour planning estimate in `resources.md` because of the Monte-Carlo repetitions. Memory < 16 GB, storage ~0.8 GB (mostly raw OLLB JSONs).

**Seeds.** Noise bootstrap: `default_rng(1000+draw)`; subsampling: `default_rng(5000+100*m+draw)`; synthetic: `default_rng(777+1000*n+10*sigma+rep*7919 % 100003)`; paired-test bootstrap: `default_rng(0)`. The main sweep, the common-target design, the descriptives, the calibration and the case study are deterministic. MILP solutions are optimal, so objective values do not depend on solver tie-breaking.

## Which script produces what
| Paper item | Script(s) | Output |
|---|---|---|
| Table 1 (boards) | `07_descriptives.py`, `10_tables.py` | `results/descriptives.csv`, `paper/tables/descriptives.tex` |
| Table 2 (paired ratios), Tables 6-8 (full paired) | `02b_common_targets.py`, `02c_paired_tests.py`, `10_tables.py` | `results/common_*.csv`, `results/common_tests.csv` |
| Fig. 1 (rank sweep), Table 5 (medians/IQR), Fig. 4 (cap sweep) | `02_main.py`, `08_figures.py` | `results/main_*.csv` |
| Fig. 2 (task subsampling) | `04_subsample.py`, `08_figures.py` | `results/subsample_helm.csv` |
| Fig. 3 (synthetic) | `05_synthetic.py`, `08_figures.py` | `results/synthetic.csv` |
| Table 9 (noise), Fig. 5 left | `03_noise.py`, `08_figures.py`, `10_tables.py` | `results/noise_helm_*.csv` |
| Tables 3 and 10, Fig. 5 right (calibrated caps) | `06_calibration.py`, `08_figures.py`, `10_tables.py` | `results/finetune_gain*.csv`, `results/calibrated_feasibility_ollb6.csv` |
| Table 4 (case study) | `09_case_study.py`, `10_tables.py` | `results/case_study_*.csv` |
| Table 11 (incumbents), Kendall tau in text | `07_descriptives.py`, `10_tables.py` | `results/winners.csv`, `results/kendall_*.csv` |
| Solver verification | `test_lib.py` | `results/test_lib_output.txt` |

Library: `code/lib.py` (rules, closed-form and MILP solvers), `code/exp_utils.py`, `code/data_utils.py`.

## Method summary
Investment = non-negative gain vector delta on the target's task scores, per-task cap g, ceiling 100. Costs: breadth (#tasks with delta>0), magnitude (sum of delta), depth (smallest uniform cap g* for which any plan wins). The target must be strictly first with rivals fixed. Rules: arithmetic/geometric/harmonic mean, minimum, median (closed forms / water-filling / breakpoint search), Borda, Copeland, plurality (exact MILPs). Assumptions and limits are in the paper (Sec. 3 and 6).

## Deviations, failures and honest notes
* Ordinal rules on the two OLLB boards use the top-100 models by arithmetic mean as the model pool (solver size); cardinal rules use the full board.
* Study design was settled after exploratory pilot runs on HELM-MMLU; there is no confirmatory hold-out board.
* First OLLB download attempts hit HTTP 429; the script now backs off. The first median solver failed `test_lib.py` and was replaced before any reported result; no reported experiment was dropped.
* MILP optimality flags were recorded only in `02_main.py` (none hit the 60 s limit). The Monte-Carlo scripts use 20-30 s limits and do not record them.
* Compute exceeded the planning estimate (above).
* Content-access statement: no page of the withheld published paper, or any page citing/discussing it, was searched for or read. Web access was limited to: the data sources above, the NeurIPS 2026 formatting zip, the arXiv API (by ID, title only) and Crossref lookups to verify that the cited references exist. `starter_literature.md` item 9 was verified to exist by its title only and was not read.
* Authorship: study design, code and manuscript were produced by an autonomous LLM-based agent.
