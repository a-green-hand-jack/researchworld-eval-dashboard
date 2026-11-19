# Predicting full-benchmark LLM scores from a few items: design vs. estimator

Paper: `paper/main.pdf` (LaTeX source `paper/main.tex`, ICLR 2027 official template, anonymous submission format).
Everything in the paper is produced by the scripts below from the public data; nothing is hand-entered.

## Layout
| path | content |
|---|---|
| `code/common.py` | data loading, the three model-split regimes (`interp`, `org`, `extrap`), metrics |
| `code/methods.py` | all methods: MIRT (own MAP IRT), designs (uniform / stratified / Neyman-PPS), estimators (Hajek, difference estimator, ridge / latent / kNN predictors, cross-fitting), anchors, pIRT |
| `code/run_experiments.py` | stage 1 grid (one task = dataset x regime x seed) -> `results/main*.csv` |
| `code/merge_results.py` | merges the partial stage-1 files (see "Run history") into `results/main.csv` |
| `code/run_stage2.py` | stage 2 (POST HOC) shrink-to-mean regression, guard, 1-D calibration -> `results/stage2.csv` |
| `code/analyze.py` | aggregation, bootstrap CIs, Wilcoxon + Holm, ablations, figures -> `results/tables/`, `figures/` |
| `code/extra_analysis.py` | dataset descriptors, item-equivalents, win rates -> `results/tables/` |
| `code/make_tex_tables.py` | CSV -> LaTeX tabulars in `paper/tables/` |
| `paper/` | `main.tex`, `sec_method_setup.tex`, `refs.bib`, ICLR 2027 style files, `build.sh` |
| `results/` | raw per-run results (`main.csv`: 132,000 rows; `stage2.csv`), logs, aggregated tables |
| `run_all.sh` | end-to-end script |

## Environment
Python 3.11.15, CPU only. `numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, joblib 1.6.0, matplotlib 3.11.2, kmedoids 0.5.5`
(`pip install -r requirements.txt`; PyMuPDF was used only to preview PDF pages). LaTeX: TeX Live 2025 (`pdflatex`, `bibtex`).
The reference repository's `torch`/`py_irt` dependencies are **not** needed: all methods are re-implemented in `code/methods.py`.

## Data (version used)
Public repository `https://github.com/socialfoundations/benchmark-prediction`, commit `55faff496947789f94e6b5908c77cbc3e84f81ad`
(MIT licence). Only `data/scores/{ifeval,openllm_math,mmlu_pro,arc_challenge,bbh,gpqa,musr,commonsense,gsm,legalbench,math,med_qa,mmlu}.jbl`
and the `*_models.jbl` name lists of the 7 Open LLM benchmarks are used (needed for the held-out-developer split).
`run_all.sh` clones and checks out that commit into `data/repo`. (This workspace keeps only those score files, ~85 MB; the
clone in `run_all.sh` is only needed if they are missing.) No account is required.

## Seeds, commands, runtime
* Stage 1: `python code/run_experiments.py --seeds 30 --procs 12 --out results/main.csv` (seeds 0-29). A seed fixes the model split (`interp`, `org`)
  and, via `numpy.random.default_rng([seed, n, crc32(design tag)])`, every coreset. MIRT is fitted with a seeded initialisation.
  k=1 and k=4 MIRT fits (ablation) are run only for seeds 0-9.
* Stage 2: `python code/run_stage2.py --seeds 30 --procs 12`  (~2 min). It regenerates the same uniform/stratified coresets (checked: random-sampling and RS-Learn errors are identical to stage 1, max abs. difference 0).
* Analysis: `python -W ignore code/analyze.py; python code/extra_analysis.py; python code/make_tex_tables.py`; paper: `bash paper/build.sh`.
* Runtime (shared, heavily oversubscribed 40-core machine; the effective speed was a few times slower than an idle machine): stage 1 about 3.5 h wall-clock with
  36 worker processes spread over three concurrent invocations (CPU-hours were not measured; MMLU-Pro `k`-medoids and MIRT fits dominate); stage 2 2 min; analysis ~10 min.

## Run history (for exact reproduction of `results/main.csv`)
Stage 1 was run as several invocations with disjoint seeds, purely for speed: `a` = seeds 0-11 (`--seeds 30 --procs 12`, stopped after
seed 11 was nearly complete, snapshot `results/main_a_snapshot.csv`), `c` = seeds 12-19, `b` = seeds 20-29, `d` = seed 11 of MMLU-Pro (three tasks missing from `a`).
`code/merge_results.py` merges them (asserting all 990 tasks are present). Because each task is deterministic given its seed, one `--seeds 30` run gives the same numbers
(up to floating-point nondeterminism of multi-threaded BLAS; we pinned `OMP_NUM_THREADS=1`). An earlier launch with 36 processes and `--seeds 50` was
aborted after ~20 minutes (no results used); two earlier 2-3 seed pilots on GSM/IFEval/MuSR only checked that the code runs.

## Which script produces which table / figure of the paper
| paper item | produced by |
|---|---|
| Table 1 (main comparison, n=50) | `analyze.py` -> `results/tables/table1_n50.tex` / `key_*_n50.csv`; `make_tex_tables.py` -> `paper/tables/table1_n50_tab.tex` |
| Fig. 1 (budget curves) | `analyze.py` -> `figures/fig_budget_curves.pdf` (from `results/tables/key_*_n*.csv`) |
| Fig. 2 (signed error) | `analyze.py` -> `figures/fig_bias.pdf` |
| Table 2 (design x predictor grid) | `analyze.py` (`grid_*_n50.csv`) -> `make_tex_tables.py` -> `paper/tables/grid_tab.tex` |
| Table 3 (ablations gamma, k; seeds 0-9) | `analyze.py` -> `results/tables/ablation_seeds0-9_n50.csv` -> `paper/tables/ablation_tab.tex` |
| Equivalent random items, win rates (Sec. 5.1) | `extra_analysis.py` -> `results/tables/equiv_items_winrate.csv` |
| Paired tests (Sec. 5.2/5.3, Table 6) | `analyze.py` -> `results/tables/significance.csv` |
| Appendix Table 4 (data), 5 (per benchmark), figure heatmap | `extra_analysis.py` (`dataset_stats.csv`), `analyze.py` (`perdataset_*`, `fig_heatmap.pdf`) |
| Appendix full-budget tables | `analyze.py` (`key_*_n{10,25,50,100}.csv`) -> `make_tex_tables.py` |
| Absolute MAE of random sampling (Fig. 1 caption, Sec. 5.1) | computed from `results/main.csv` (method `random`, geometric mean over benchmarks of seed-mean MAE) |

## Method names in the CSV files
`random`, `strat_mean`, `pps_resid_mean`, `rs_learn`, `aipw_ref`, `anchor_w`, `pirt_k2`, `pirt_k8`, `irt_plugin`;
`{uniform|strat|pps_resid}+{ridge|lat|knn}_{is|cf}` (design + predictor + in-sample/cross-fitted difference estimator; **Neyman-DR = `pps_resid+lat_cf`**);
ablations `pps_resid_g{0.0,0.6,1.0}+lat_cf`, `{uniform|pps_resid}+lat_cf_k{1,4,8}`; stage 2 (post hoc): `rsres_{uniform,strat}`, `rslearn_strat`, `cal1d_*`, `guard_*`.

## Honest notes
* Stage 2 estimators and the "guard" were designed after seeing stage-1 results (documented in the paper, Sec. 5.3, and in `run_stage2.py`).
* Known implementation caveat: `Runner.anchors_irt` (pIRT) does not merge duplicate anchor items (an attempted patch was not applied before the main run); effect expected to be negligible but not quantified.
* Results of the held-out-developer regime use only the 7 Open LLM benchmarks (model names are not available for the HELM matrices).

## Access / contamination disclosure
Resources accessed: the data repository above (README and source were read; only score files used as data), the arXiv API (titles/dates/authors of cited arXiv IDs),
GitHub/NeurIPS URLs to obtain LaTeX templates (the ICLR 2027 template was used; a NeurIPS 2025 style archive was downloaded but not used). No literature searches were performed and no
page identified as the withheld prior publication, or discussing it, was knowingly encountered. The README of the data repository contains a high-level statement of the findings of its
accompanying paper (starter reference no. 6, which is on the permitted list); it was read before the experiments.
