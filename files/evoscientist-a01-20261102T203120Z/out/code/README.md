# Targeted investment and aggregation rules on public multi-task leaderboards

Code, derived data and paper source for *"How Much Does It Cost to Top a Multi-Task Leaderboard? Aggregation Rules and
Targeted Investment"* (NeurIPS 2025 template; the NeurIPS 2026 style file was not available at
`media.neurips.cc/Conferences/NeurIPS2026/Styles.zip` (HTTP 404) when this was written).

## Layout
```
code/lb/agg.py            minimum-investment solvers for 10 aggregation rules (closed forms, LP, MILP, DP)
code/lb/boards.py         loaders for the 4 board variants (HELM-MMLU, BBH-24, BBH-24 without outlier, OLL-6)
code/lb/runner.py         shared helpers (caps, rankings, contender costs)
code/test_solvers.py      brute-force validation of all solvers (must print TOTAL MISMATCHES 0)
code/fetch_helm.py        download HELM-MMLU v1.13.0 summaries (+ sha256 list)
code/fetch_oll.sh         download Open LLM Leaderboard `contents` parquet and `results` repo at pinned commits
code/build_data.py        raw -> data/processed/*.csv (+ SHA256SUMS)
code/run_main.py          E0 (winners, Kendall), E1 (contenders x rules x caps), E2 (rank sweep)
code/run_scaling_uncert.py E4 (number of tasks), E5 (task / noise bootstrap)
code/run_case_gains.py    E6 (case study), E7 (child-parent gain calibration)
code/analyze.py           all tables (paper/tables) and figures (paper/figs) from results/*.csv
results/                  all raw result CSVs and logs
paper/                    main.tex, refs.bib, checklist (make_checklist.py), tables/, figs/, main.pdf
data/processed/           derived score matrices (small); raw downloads are not redistributed
```

## Environment
Python 3.11.15; numpy 2.4.6, scipy 1.17.1 (HiGHS via `scipy.optimize.milp/linprog`), pandas 3.0.6, matplotlib 3.11.2,
pyarrow 26.0.0 (`pip install -r requirements.txt`). CPU only. LaTeX: `pdflatex` + `bibtex`/`latexmk` (TeX Live).

## Data (versions, checksums, licenses)
* HELM-MMLU: `https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (latest of 14
  releases; `summary.json` date 2025-01-10). `python code/fetch_helm.py` downloads all 303 summary files (about 240 MB
  because `runs.json` is 165 MB; only `groups/json/mmlu_*_subject:*.json` are used) and writes `data/helm_v1.13.0.sha256`.
* Open LLM Leaderboard `contents` commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (2025-03-20), parquet SHA-256
  `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5`; `results` commit
  `aa81ecc38fdc5708254b833923368970efdf5ef5` (2025-03-15; the git checkout HEAD matched it; 10,509 JSON files). `sh code/fetch_oll.sh`.
* None of the sources declares a license for the score tables (the HELM code is Apache-2.0; the `contents` card has no
  license field, but has a per-model "Hub License" column which we do not use). We use the scores for research only and
  release only derived score matrices (`data/processed`, checksums in `data/processed/SHA256SUMS`).
* Choice of HELM v1.13.0 follows the task brief; no other release was used.
* Processing choices: OLL `contents` deduplicated by `fullname` (latest submission, 4,497 models; 1 flagged model dropped
  -> 4,496); BBH-24 from the latest run per model in `results` having all 24 `leaderboard_bbh_*` sub-tasks with standard
  errors (4,507 models; 4,496 after the merge with `contents`; flagged dropped -> 4,495); HELM: 79 models having all 57
  subjects (no missing cells). "BBH-24 (no outlier)" drops `qingy2024/Benchmaxx-Llama-3.2-1B-Instruct` (4,494 models).

## Reproduce (all seeds fixed: 20261102 for bootstraps / task subsets)
```
pip install -r requirements.txt
python code/fetch_helm.py          # ~1 min, ~240 MB
sh code/fetch_oll.sh               # ~2-5 min, ~1.3 GB (git clone of the results repo)
python code/build_data.py          # ~1 min
python code/test_solvers.py        # ~4 min; prints TOTAL MISMATCHES 0
python code/run_main.py            # ~1 min on 32 processes
python code/run_scaling_uncert.py  # E4 ~1.5 min, E5 ~15 min on 36 processes
python code/run_case_gains.py      # seconds
python code/analyze.py             # seconds; writes paper/tables/*.tex and paper/figs/*.pdf
cd paper && python make_checklist.py && latexmk -pdf main.tex
```
Total wall-clock of the full pipeline: about 25 minutes on a 40-core CPU machine, < 16 GB RAM, no GPU.
(`run_main.py` and the scaling/bootstrap script use multiprocessing with 32-36 workers; reduce `Pool(...)` for fewer cores,
the results do not depend on it.)

## Which script produces which table / figure
| Paper item | Source script | Result file |
|---|---|---|
| Table 1 (winners) | analyze.py <- run_main.py E0 | results/e0_winners.csv |
| Table 2 (main depth/breadth) | analyze.py <- run_main.py E1 | results/e1_contenders.csv, table_main.csv |
| Fig. 1 (depth by rule, CIs) | analyze.py <- E1 + E5 | results/e5_uncertainty.csv |
| Fig. 2 / Table 5 (gain bounds) | analyze.py <- E1 | results/e1_contenders.csv |
| Fig. 3 (scaling in m) | analyze.py <- run_scaling_uncert.py E4 | results/e4_scaling.csv |
| Table 3 (case study) | analyze.py <- run_case_gains.py E6 | results/e6_case*.csv |
| Sec. 5.5 gain calibration | run_case_gains.py E7 | results/e7_gains.csv, e7_gain_quantiles.csv |
| Table 6 (stability vs mean) | analyze.py <- E5 | results/table_vs_mean_stability.csv |
| Table 7 (CIs) | analyze.py <- E1 + E5 | results/table_main.csv |
| Fig. 4 (rank sweep) | analyze.py <- run_main.py E2 | results/e2_rank_sweep.csv |
| Solver validation | code/test_solvers.py | results/logs/test_solvers.log |

## Notes / known deviations
* All costs use "ties favour the target" (infimum cost); see the paper (A5).
* Borda for boards with n > 120 models (BBH-24, OLL-6) is bracketed by a DP; the paper reports the upper bound
  (relative gap to the lower bound <= 8.1%, `results/borda_gap.csv`). HELM (n=79) uses an exact MILP.
* The trimmed-mean/median(even m) minimum *breadth* is a window-search upper bound (validated against the exact MILP on 84
  random instances), minimum *depth* is an exact LP (caps must be nondecreasing in x, true for `ceil` and `x+g`).
* In OLL-6, noise standard deviations use an affine rescaling from raw to normalised scores which is approximate for BBH and MuSR.
* Preliminary exploratory runs (speed tests, an earlier version of the pipeline without the "BBH-24 (no outlier)" board
  and with a DP-only Borda on HELM) were superseded by the final runs; all reported numbers come from the final run of the
  scripts above. A first run of E5 used a wrong noise scale for OLL-6 (slope in raw units) and was re-run after the fix.
* Encounter with restricted material: none. No search for, or access to, the paper the task brief excludes was made. One starter reference
  (arXiv:2603.08371, listed in `starter_literature.md`) was opened only to read its title, authors and the first ~900
  characters of its abstract for citation; nothing else of it was read.
