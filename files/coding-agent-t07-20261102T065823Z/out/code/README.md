# Predicting full LLM benchmark scores from a small subset

This directory contains a complete research artifact: a NeurIPS 2026-format
paper, LaTeX source, CPU implementations, frozen data, actual prediction
outputs, uncertainty analyses, and the scripts that generate every paper
table and figure. The manuscript uses the official preprint option with an anonymous artifact byline; it has not
been submitted to or accepted by NeurIPS.

## Start here

- `paper.pdf`: compiled paper, including references, appendix and completed
  official NeurIPS 2026 checklist.
- `research_bundle.tar.gz`: portable paper/code/results/data package (without
  the virtual environment or unused upstream datasets); `PACKAGE_MANIFEST.json`
  records file hashes. Rebuild it with `src/package_artifact.py`.
- `paper/paper.tex`, `paper/references.bib`, `paper/checklist.tex`: LaTeX sources.
- `PROTOCOL.md`: local experimental plan and clearly marked amendments.
- `logs/RESEARCH_LOG.md`: consulted sources, implementation corrections,
  numerical checks, exploratory ablations, failures and recoveries.
- `results/metrics.csv`: every main method, budget, split and seed.
- `results/summary.csv`: macro results, 95% intervals and mean across-seed SD.
- `results/paired_contrasts.csv`: paired differences and dataset win counts.
- `results/main/*.npz`: actual predictions, truth, queried item indices,
  original source/target row indices and available variance estimates.
- `results/main/*.json`: individual metric rows and optimization/timing logs.
- `results/design*`, `results/source_size*`: the independent diagnostics.

The conclusion concerns empirical means of these frozen response matrices,
not unseen-question generalization, official task-weighted leaderboard scores,
fresh stochastic model evaluations, or actual measured inference savings.

## Environment

The executed environment uses Python 3.11.2 on Linux x86-64. Every installed
Python package version is pinned in `requirements.lock.txt`. Main numerical
versions are NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.6.1, pandas 2.2.3,
joblib 1.5.1, matplotlib 3.10.3 and kmedoids 0.5.3. PDF extraction/validation
uses pypdf 5.5.0 and PyMuPDF 1.25.5. No GPU, torch, model weights or evaluation
API is required.

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
```

For paper compilation, install a TeX Live environment with `pdflatex`, `bibtex`,
and the standard packages used in `paper/paper.tex` (e.g. texlive-latex-extra,
texlive-fonts-recommended and texlive-science on Debian). The official style
is supplied; no live conference-template download is needed to build.

The visible host exposes Intel Xeon Gold 6230 CPUs and much more RAM, but this
container has a **16 GiB memory limit and four CPU equivalents**. The recommended
main command therefore uses four processes, with one BLAS/OpenMP thread each.
Eight simultaneous MMLU-Pro correlation matrices caused an OOM in the initial
run; this failed invocation is preserved rather than hidden. A fresh run with
four processes and the in-place distance computation avoids that configuration.

## Data: fixed snapshot, no account

The only evaluation data are the thirteen matrices explicitly named in the task,
from `https://github.com/socialfoundations/benchmark-prediction`, commit
`55faff496947789f94e6b5908c77cbc3e84f81ad`. The workspace `upstream/` checkout is
detached at that commit; the portable bundle includes only the required files
and copyright notice. Its MIT notice is in `upstream/LICENSE.txt`; see also
`THIRD_PARTY_NOTICES.md`. The reproduction does not import the upstream package.

Download the same immutable files without cloning the repository:

```bash
.venv/bin/python src/download_data.py
.venv/bin/python src/common.py
```

`download_data.py` uses only raw GitHub URLs containing the full commit. File
hashes, exact URLs and sizes are in `data_manifest.json` and
`results/download_manifest.json`; the audit is `results/data_audit.csv`.
No Hugging Face login, gated details, or live leaderboard scraping is used.

`src/common.py` checks that entries are finite and binary, removes all-zero
rows as the upstream reader does, then keeps the first original row for every
exact full-response profile. All original item columns and weights remain.
Raw dimensions differ from model-list line counts; use the audited dimensions,
not the task's approximate counts. The all-zero exclusion is a cohort choice,
not proof that every such run was invalid. Deduplication defines a retrospective
population; it is not an operational test for an unseen target model.

## Reproduce the experiments

From a clean result directory, the following runs the entire artifact:

```bash
bash reproduce.sh
```

Or run stages independently:

```bash
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
.venv/bin/python src/test_design.py
.venv/bin/python src/run_experiments.py --jobs 4
.venv/bin/python src/augment_results.py --jobs 4
.venv/bin/python src/run_diagnostics.py --jobs 4
.venv/bin/python src/report.py
.venv/bin/python src/fill_checklist.py
bash build.sh
.venv/bin/python src/validate_outputs.py
```

The main runner skips any complete per-split JSON file. To **recompute** main
predictions without modifying the delivered results, choose a fresh output path:

```bash
.venv/bin/python src/run_experiments.py --jobs 4 --outdir results/fresh_main
```

The reporting/augmentation scripts intentionally read `results/main`; to use a
fresh run for the complete manuscript, move the delivered directory aside and
make the new directory `results/main` before those stages. Do not put different
protocols into one result directory. A completed JSON is written only after the
prediction archive succeeds. If interrupted before that, the incomplete task
is rerun. `run_summary.json` is a launch summary, not a prediction task.

For a quick independent smoke test:

```bash
.venv/bin/python src/run_experiments.py --datasets commonsense \
  --protocols random --seeds 0 --jobs 1 --outdir results/smoke
```

The full main experiment comprises 390 model-cohort tasks (13 benchmarks ×
3 protocols × 10 seeds), each evaluating budgets 20, 50, 100, 200. Each task
fits its source models once and reuses them across budgets. The no-offset
augmentation adds an exploratory same-design control and consistently
recalculates rank ties from saved predictions; it does not refit comparators
or change MAE/RMSE/bias. The diagnostics perform 200 new item draws for each
fixed seed-zero split and source-count ablations on five seeds.

## Seeds and all method settings

- Main seeds: 0 through 9; diagnostic source-count seeds: 0 through 4.
- Source split: `default_rng(seed)` permutation, source count floor(0.7 M).
  Tail cohorts are sorted by full mean, with seed-permuted stable tie breaking.
- Uniform item stream: `default_rng(10000 + seed)` permutation.
- Stratified item stream: `default_rng(20000 + seed)`, independently permuting
  each stratum. KMeans has `random_state=seed`, 5 initializations, 100 iterations.
- Repeated design draws pass seeds 100000 through 100199 into these streams.
- Source-count subsampling: `default_rng(30000 + seed)` within eligible sources.
- Bootstrap: `default_rng(20261102)`, 10,000 benchmark-block resamples.
- All remaining penalties, initializations, minimum counts and allocation
  priorities are specified in `PROTOCOL.md`, `src/methods.py`, and the appendix.

All methods see the same source rows and are charged exactly the same number
of distinct target queries. Uniform-based estimators share the same item set.
There are no target-tuned hyperparameters. Model score-tail information is
used only for retrospective cohort construction, never in estimator fitting.
The AIPW paper and frozen-code formulas are evaluated separately, as explained
in the paper and research log. IRT rows are the documented logistic variants,
not mislabeled exact reproductions of tinyBenchmarks/IRT++.

## Tables, figures and numerical traceability

All manuscript numbers that describe our empirical results are generated by
`src/report.py`; `paper/generated/numbers.tex` supplies inline macros and
`results/paper_numbers.csv` lists their actual values. No placeholder results
or synthetic performance measurements are used. The tiny exact enumerations
are statistical implementation checks and are not presented as benchmark data.

| Paper object | Generated file | Source results / producer |
|---|---|---|
| Main score-error table | `paper/generated/main_mae.tex` | `results/main/*`, `src/report.py` |
| Main Kendall ranking table | `paper/generated/main_rank.tex` | same |
| Main ablation table | `paper/generated/ablations.tex` | main + `src/augment_results.py`, report |
| Budget curves | `figures/budget_curves.pdf` | main, report |
| Data audit table | `paper/generated/data.tex` | `src/common.py`, report |
| Per-benchmark mean/SD table | `paper/generated/per_benchmark.tex` | main, report |
| Design-variance ratios | `figures/variance_ratios.pdf` | `src/run_diagnostics.py`, report |
| Source-count curves | `figures/source_count.pdf` | same |
| Coverage and width tables | `paper/generated/coverage.tex`, `width.tex` | repeated-design outputs, report |
| RMSE, Spearman, bias, pair error | `paper/generated/all_*.tex` | main, report |
| Larger-benchmark MAE sensitivity | `paper/generated/long_mae.tex` | main filtered by audited item count, report |

The complete all-budget results, suite-specific means, source-optimization
convergence and paired error differences are also provided as CSV. CI brackets
are pointwise 95% percentile intervals over benchmark blocks after averaging
seeds. Benchmarks share models and related tasks; these are collection-level
heterogeneity summaries, not a guarantee of independence or future performance.
Per-benchmark SDs describe seed variability. Design-draw coverage is an empirical
diagnostic and must be read alongside interval width.

## Integrity and independent-research restrictions

Only direct PDFs from the explicitly permitted starter list were consulted;
no broad literature search or citation traversal was used to identify the
unspecified prohibited paper. No prohibited content was knowingly encountered.
`logs/RESEARCH_LOG.md` records the directly accessed papers, initial newer
versions delivered by arXiv, the later v1 equation check, official template,
failed runs and implementation corrections. The AI research agent's role is
declared in the paper and checklist. Results have not been independently
verified by a human researcher.

The official 2026 template permits nine main-text pages, excluding references,
appendix and checklist. `src/validate_outputs.py` checks the actual compiled
pagination, numerical files, result completeness and selected metric identities.
The original official questions and guidelines are preserved in the checklist;
all sixteen answers have justifications.

## Observed runtime and resource record

The final measured timings and completion checks are in `results/validation.json`,
`results/main/run_summary.json`, and `logs/main_initial_oom_summary.json`.
`results/paper_numbers.csv` records the manuscript's timing values. The expected
cost on a similar four-core CPU allocation is the order of the measured main
runtime; the longest tasks are MMLU-Pro correlation medoids. Diagnostics and
rendering are much smaller. A fresh environment install additionally requires
downloading the dependency wheels. The shipped virtual environment, references,
data and results fit within the stated approximate storage budget at completion;
the exact final disk usage is logged. The failed initial run and smoke tests
are additional research compute, not included silently in successful-worker
timings.
