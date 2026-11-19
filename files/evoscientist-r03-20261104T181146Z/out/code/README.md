# Few benchmarks, held-out scores: reproduction

This directory is the complete local research deliverable. `paper.pdf` is the final manuscript; `paper/main.tex` is its entry point. The official **NeurIPS 2026** style and completed mandatory checklist are included (9 content pages, 27 pages including references, appendices and checklist). This is a research artifact, not an accepted or currently submitted conference paper.

## Scientific scope and integrity

The source MTEB matrix is 279 embedding models ×62 English task names, not 279 generative LLMs. Original experiments use 8 candidate/4 fixed audit task panels. The registered-style, internally frozen **>=3 feasible organization split gate failed (1/5)**: all MTEB claims are descriptive. A broader incomplete-panel sensitivity and a metadata-alias-connected Open LLM sensitivity are explicitly post-audit exploratory experiments. Do not infer unseen-family guarantees, universal k, causal missingness correction, or actual benchmark-runtime savings.

Read `research_request.md`, `plan.md`, `success_criteria.md`, `protocol/sensitivity_plan.md`, `experiment_log.md`, `audit_protocol.md`, and `final_report.md`. Planned items not performed must not be described as completed. Source access was restricted to exact supplied papers, specified public data, and official conference pages; `literature/access_log.md` records what was actually inspected. No prohibited paper was identified or searched for.

## Environment

CPU only; Python 3.11.15. `requirements.txt` pins direct dependencies; `requirements.lock` records the full installed environment. `environment.json` records machine/platform. BLAS/OpenMP threads are restricted to one per process; no GPU or paid API.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 CUDA_VISIBLE_DEVICES=''
```

LaTeX needs `pdflatex`, `bibtex`, `latexmk`, the official style's standard packages, and Times-compatible fonts (a TeX Live base/recommended/fonts install is sufficient in the provided environment). Do not install a multi-GB TeX distribution into this workspace. Figures use Matplotlib; no foundation-model inference is needed.

## End-to-end commands, from this workspace root

```bash
python src/data.py                              # downloads/streams pinned MTEB + Open LLM
python src/cohorts.py                           # freezes metadata/mask-based original panels
python -m pytest -q                             # synthetic correctness contracts
python src/run.py                               # all 20 original train/validation/test pipelines
python src/run.py --stress                      # 18 training-label-deletion pipelines
python src/sensitivity.py                       # 10 post-audit exploratory pipelines
python src/theory_check.py                      # actual labelled synthetic check + real risk diagnostics
python src/diagnostics.py                       # metadata overlap, components, convergence, random MC
python src/mc_sensitivity.py                    # second 50-path bank, fixed estimators, no retuning
python src/reproduce_check.py                   # one exact end-to-end pipeline replay + CPU/RSS
python src/analyze.py                           # all summary tables/figures, 2000 cluster resamples
python src/manuscript_tables.py                 # link ALL empirical table rows to generated fragments
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
cp paper/main.pdf paper.pdf
python src/verify.py --before-package           # style, 9-page limit, checklist, figures/results
python src/package.py                           # excludes raw/row-level unresolved-license data
python src/verify.py                            # bundle hashes + current storage ceiling
```

**Fresh reproduction:** runners skip a pipeline when its `_done.json` exists. Before rerunning after changing source/data/configuration, use a new directory or move the previous `results/` aside; cached reports do NOT validate code identity. Do not combine old/new results without an explicit provenance decision. Manifests regenerated from the same pinned files and code are deterministic. Archive bytes can contain timestamp differences; compare table/array contents rather than compressed-file hashes.

## Versions, rows and canonicalization

- **MTEB**: `https://github.com/embeddings-benchmark/results`, commit `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`. Download codeload archive (no full Git history). One model revision per directory, chosen by unique task coverage, lexical tie break; no merging best per-task checkpoints. A fixed 62-English-task name list is in `src/data.py`. Take a single English **test** `main_score`, retain [-1,1] scores, and enforce modal dataset revision per task using metadata counts. Excludes multilingual ambiguous cases, MSMARCO dev and tasks not on the list. Trusts source main metric; evaluator/configuration versions are not fully harmonized. JSON is streamed, never expanded to multi-GB files. `data/processed/mteb_provenance.csv` maps every retained cell to its exact archive path and dataset revision. `mteb_eda.json` has SHA256/exclusions/counts.
- **Open LLM**: `https://huggingface.co/datasets/open-llm-leaderboard/contents`, commit `9c09a7cae43334062a82cb164f2ef255013dafa2`. Resolve its one parquet using the exact tree endpoint. Use six `* Raw` **proportions**, not normalized display scores or the aggregate. One row/fullname, bfloat16 then float16 then other precision, metadata/lexical ties. 4,497 retained complete rows from 4,576 evaluations. Original organization grouping allows revision aliases; sensitivity connects organization, nonempty model SHA and Base Model keys before splitting, with zero cross-partition nonempty key overlaps. This is not full ancestry recovery.

## Seeds and supports

- Outer split seeds: 11,23,37,53,71. Repeated grouped holdouts, NOT five disjoint folds. Approximate 60/20/20 row proportions, allocating shuffled whole groups by relative deficit. Original row-split regime is secondary.
- Permanent MTEB audit role: SHA256 integer of `audit-role:101:<task>` modulo3=0; other tasks candidates. Original training coverage >=60%, >=40 cells; frozen panel ladder 16/8→10/6→8/4; masks, not test values, select feasibility. Original complete panels end up 8/4. Wide sensitivity drops coverage/cap but keeps >=40 train observations and uses all eligible tasks.
- Random: 50 nested permutations, RNG seed outer+811; average **losses**, never loss of averaged anchor predictions. Low-rank starts:101,202,303, maximum200 iterations, tolerance1e-5; convergence flags retained. Gaussian lambda grid0,.1,.3,.6,.9,1; low-rank rank1,2,4,8 (capped by task count), ridge .01,.1,1. Validation average k=1,2,4 (Open LLM1,2); shared Gaussian lambda for all policies. Means/scales from observed training scores only; tiny numerical ridge1e-6; pairwise overlap minimum20 then PSD projection.
- Training deletion seed outer+941, rates20%/50%, MCAR/task-propensity/synthetic high-score MNAR, organization seeds11,37,71 only. Training preprocessing/refitting/retuning repeated; validation/test labels unchanged.
- Global budget heuristic: minimum k within one organization-bootstrap SE of validation minimum, including0;500 conditional resamples seed outer+411. Evaluate selected k only on **dense** test supports; native curves do not contain every selected k.
- Final intervals:2,000 paired cluster bootstrap draws; organization IDs (metadata-connected components for corrected transfer) are resampled once jointly across all repeated split appearances. Equal split means. Conditional descriptive intervals, not family-independent or post-selection guarantees. Tasks, random anchor paths and split appearances are NOT independent samples. Secondary comparisons are descriptive; no multiple uncorrected significance declarations.

## Table / figure provenance

- Every empirical manuscript table has generated row fragments: `src/manuscript_tables.py` uses the authoritative CSVs for Tables1/2/3/6/7/8; Tables4/5 use `src/analyze.py` → `main_table.tex`/`contrast_table.tex`. The evidence-map Table9 is static documentation in `paper/main.tex` (rendered by LaTeX), not an experimental result.
- Full method confidence-interval table: `artifacts/main_table.tex` ← `src/analyze.py`, reading actual stored loss CSVs.
- Contrasts/raw errors: `artifacts/contrast_table.tex`, `summary.csv`; same script. Raw RMSE is sqrt(equal-split mean per-row canonical raw MSE), not mean of per-model RMSE.
- Main budget figure: `artifacts/budget_curves.pdf` (+PNG) ← `src/analyze.py`.
- Training missingness figure: `artifacts/missingness.pdf` (+PNG) ← `src/analyze.py`.
- Target-support diagnostic: `artifacts/target_support.pdf` (+PNG) ← `src/analyze.py`; changing-target deployment error is not a paired-target superiority test.
- Cohort table: `artifacts/cohort_counts.csv` ← same analysis from frozen manifests.
- All split results: `artifacts/split_results.csv`; selected-budget table: `validation_budgets.csv`; resource table: `run_resources.csv`; lambdas: `hyperparameters.csv`.
- Gaussian Monte Carlo identity table: `artifacts/synthetic_identity.csv`, `synthetic_metadata.json` ← `src/theory_check.py`. Synthetic, clearly separate from leaderboards. Risk-calibration diagnostics: `risk_calibration.csv` ← same script.
- Every base/sensitivity pipeline stores per-model paired losses and NPZ prediction arrays with truth, training means/SD, acquired indices and row IDs. Stress saves per-model loss and validation reports (no prediction arrays). `audit_protocol.md` independently reconstructed original base losses from float32 prediction arrays.

## Runtime and storage

Measured pipeline timings are in `artifacts/run_resources.csv`; acquisition and process logs are retained. The original20 fits/evaluations completed in about4.5 wall minutes with one BLAS thread; stress in seconds; expanded sensitivities and bootstrap analysis take additional minutes. Download377MiB depends on network. These times exclude running actual benchmarks: the study reuses existing scores. Full reconstruction is expected to finish within about30 minutes on a comparable machine after dependencies, conservatively under one CPU-hour; consult actual timings rather than treating this estimate as a result.

Keep one377MiB compressed MTEB snapshot plus compact CSV/NPZ artifacts; no repository history or raw dataset inputs are needed. `storage_report.json` records measured local bytes. Total must remain<5GB. Public distribution licenses differ; see `DATA_LICENSES.md`. `submission_code.zip` is a lightweight code/manuscript/results-summary bundle, not a redistribution of unlicensed Open LLM raw scores.
