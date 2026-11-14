# Predicting a new model's scores on the remaining benchmarks from k benchmarks

Paper: `paper/main.pdf` (LaTeX: `paper/main.tex`, NeurIPS 2026 template `paper/neurips_2026.sty`, checklist `paper/checklist_filled.tex`).
Main text is 8 pages (limit 9); references, proofs, extra results and the checklist follow.

## Environment
Python 3.11; numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, scikit-learn 1.9.1, pyarrow 26.0.0, joblib 1.6.0, matplotlib 3.11.2
(`pip install numpy scipy pandas scikit-learn pyarrow joblib matplotlib`; `pymupdf` only used to look at figures). CPU only; a TeX Live with `pdflatex`/`bibtex`.
All scripts are run from the repository root. Random seeds: fold/split seed `--seed` (default 0; seeds 1,2 for the stability check), bootstrap seed 123 (`analysis.py`), synthetic scripts seeds 0/1/2 fixed in the files.

## Data (pinned versions from `data.md`)
1. MTEB results (CC0-1.0):
   `git init data/results && cd data/results && git remote add origin https://github.com/embeddings-benchmark/results && git fetch --depth 1 origin 6dabbcc68c28ea5f180ce7df79347b3ca9cc6383 && git checkout FETCH_HEAD` (about 3.2 GB; the checkout was deleted after extraction to keep the repository small, the extracted table `data/mteb_long.csv.gz` is kept).
2. Open LLM Leaderboard (dataset commit 9c09a7ca...), HELM Lite v1.13.0, LiveBench judgments (dataset commit 9704e5da...) -> `data/extra/`:
   ```
   curl -L -o data/extra/olb.parquet  https://huggingface.co/datasets/open-llm-leaderboard/contents/resolve/9c09a7cae43334062a82cb164f2ef255013dafa2/data/train-00000-of-00001.parquet
   curl -L -o data/extra/helm_core.json https://storage.googleapis.com/crfm-helm-public/lite/benchmark_output/releases/v1.13.0/groups/core_scenarios.json
   curl -L -o data/extra/lb.parquet   https://huggingface.co/datasets/livebench/model_judgment/resolve/9704e5da7bfbefe75ac1482a13de827127295993/data/leaderboard-00000-of-00001.parquet
   ```
3. `python code/extract_mteb.py` (about 1 min) -> `data/mteb_long.csv.gz`; `python code/data_prep.py` (seconds) -> `data/processed/*.csv`.
Licences: MTEB CC0-1.0; OLB and LiveBench dataset cards declare none; HELM scenario data licences not verified item by item.

## Reproducing results (about 40 min wall-clock on 40 cores, about 4 CPU-hours)
```
sh run_all.sh                                   # 20 protocol runs -> results/raw/*.csv.gz (+ *_fits.json)
python code/theory_synth.py                     # synthetic checks (~4 min)   -> results/theory_t1t2.csv, theory_t3.csv, theory_t4.csv
python code/theory_mp.py                        # Marchenko-Pastur check (~1 min) -> results/theory_mp.csv
PYTHONPATH=code python code/analysis.py         # bootstrap summaries + figures (~10 min) -> results/summary_*.csv, paper/figs/*.pdf
PYTHONPATH=code python code/make_tables.py      # paper/tables/*.tex
PYTHONPATH=code python code/select_demo.py      # results/summary_selected.json
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
(`run_all.sh` job list = `logs/jobs.txt`; individual runs: `python code/run_protocol.py --data mteb_mid --split family --kmax 24`.)

## Code map
| file | role |
| --- | --- |
| `code/extract_mteb.py`, `code/data_prep.py` | MTEB json -> long table -> matrices (wide / dense / mid), other leaderboards |
| `code/bsp.py` | factor-analysis EM with missing data, Gauss-cov, kNN predictors, selection rules, model-implied errors |
| `code/run_protocol.py` | held-out-model/family protocol, hyper-parameter tuning, all (selection x predictor x k) evaluations |
| `code/theory_synth.py`, `code/theory_mp.py` | synthetic verification of Propositions 1-2, design value, cost of estimating loadings |
| `code/analysis.py`, `code/make_tables.py`, `code/select_demo.py` | summaries, bootstrap CIs, tests, figures, tables |

## Which script makes which table / figure of the paper
| item | produced by |
| --- | --- |
| Fig. 1 `fig_main_curves`, Fig. 2 `fig_selection_gain` | `analysis.py` (`fig_main`, `fig_selection_gain`) from `results/raw/{data}_family` |
| Table 1 (matrices), 2 (MTEB main), 3 (selection gain), 4 (theory vs measured), 5 (k needed), appendix tables (LLM boards, raw units, seeds, conditions) | `make_tables.py` from `results/summary_*.csv` and raw results |
| Fig. synthetic (appendix) | `analysis.py` (`fig_synth`) from `results/theory_*.csv` |
| Fig. theory vs real, predictors, spectrum, conditions (appendix) | `analysis.py` |
| Selected benchmarks (appendix C) | `select_demo.py` |
| Paired tests (appendix D) | `analysis.py` (`paired_tests`) -> `results/summary_paired_tests.csv` |

## Honest notes
* Metric: per-held-out-model RMSE in training-z units; headline = median over models (the mean is dominated by a few new-family models with extreme scores; both are stored in `results/summary_curves.csv`). The choice of the median as headline was made after seeing that outlier families (e.g. `codefuse-ai__F2LLM-v2-*` on MTEB-mid, which scores up to 39 training SDs above others on one task) dominate the mean; it is not a pre-registered choice.
* An early exploratory run on MTEB-mid (10 folds, 5 random draws) was used to debug the pipeline, to notice the outlier problem and to add the Gauss-cov predictor/greedy-cov rule; those test files were deleted and all reported numbers come from the final `run_all.sh`. Hyper-parameter grids were not re-tuned on test results afterwards, but design choices (including adding Gauss-cov and greedy-cov) were made after seeing exploratory test-fold output, so the comparison between rules is not strictly confirmatory.
* The selection rules choose among benchmarks that the held-out model actually has in the data (availability pattern is used, scores are not).
* Not done: nuclear-norm matrix completion and boosted predictors as baselines; item-level (within-benchmark) subsampling; temporal splits (the MTEB json files carry no reliable date); other leaderboards (BigCodeBench, AlpacaEval) were not used. No comparison to published methods for this exact task.
* The LLM leaderboards have only 6-10 benchmarks, so k <= 6 there; the three MTEB matrices are nested views of one data source.
* Restricted content: no page about the forbidden paper was searched for, opened or read. The only web access was to the pinned data sources, the NeurIPS 2026 call for papers / template, and Crossref title lookups for classical references (Tipping-Bishop, Rubin-Thayer, Chaloner-Verdinelli, Marchenko-Pastur, Guestrin et al., Candes-Recht, Vivek et al.). Starter-literature items are cited on the basis of their entries in `starter_literature.md` (descriptions), not full reading.
* Wall-clock times quoted are those observed on the 40-core machine used here.
