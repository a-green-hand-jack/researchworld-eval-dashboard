# Few-response LLM benchmark prediction — reproducible research artifact

## Deliverables

- **`paper.pdf`** — complete English research paper, official **NeurIPS 2026** anonymous main-track style. **8 content pages**, within the 9-page limit; references, technical appendices and the fully answered 16-question official checklist follow (25 pages total).
- **`paper/`** and **`paper_source.zip`** — complete LaTeX source, unchanged official style, bibliography, generated tables and vector/PNG figures.
- **`src/`, `tests/`, `requirements.txt`** — all implementation and reproducibility code.
- **`code_and_results.zip`** — portable code, results, logs and documentation; raw data are obtained by the pinned download script rather than duplicated in this archive.
- **`final_report.md`** — Chinese experiment report. `artifacts/analysis/` contains machine-readable results; `artifacts/final_verification.json` records final numerical/build/archive checks.

### Bottom line

At 50 queried items, macro MAE in percentage points (group-weighted within each bank, 13 banks, five seeds):

| Method | Random-group holdout | Capability frontier |
|---|---:|---:|
| Uniform | 4.48 | 4.40 |
| Stratified mean | 3.98 | 3.93 |
| Fixed stratified difference | 3.91 | 3.83 |
| Score ridge | 3.09 | 7.51 |
| Population-corrected AIPW | 3.60 | 3.82 |
| Rasch 1PL | 3.74 | 3.76 |
| SCFD (studied proposal) | 3.77 | 3.80 |
| Source-calibrated MIRT mixture (added) | 3.27 | 6.93 |
| Nearest source (added) | 4.16 | 9.26 |

SCFD applies an honest finite-population residual audit; it is **not a newly invented survey-sampling principle or an overall winner**. Its frontier improvement over fixed stratified difference is only **0.0274 pp**. Simple controls deserve priority in practical comparisons. Lower MAE does not imply better rankings. Benchmark-resampling intervals are **descriptive** because model pools/tasks overlap; no population-valid independent-benchmark or per-model score confidence claim is made. The main-track novelty/insight threshold remains an explicit self-review risk; a compiled conference-format paper is not a claim of acceptance readiness.

## 1. Environment

- Actual Python: **3.11.15**, x86-64 Linux.
- Actual host: **40 Intel Xeon Gold 6230 CPU cores at 2.10 GHz**, about **251 GiB RAM exposed**. Runs used **8 CPU workers**, one BLAS/OMP/MKL thread per worker, **no GPU**. Peak process RSS was not measured.
- Exact numerical-package versions are pinned in `requirements.txt`; platform/BLAS information is in `artifacts/environment.json`, `artifacts/resources.json`, `logs/lscpu.txt`, and `logs/memory.txt`.
- Building the paper requires `pdflatex` and `bibtex` with ordinary TeX Live packages (`natbib`, `geometry`, `lineno`, `booktabs`, `amsmath`, `amsthm`, `graphicx`, `xcolor`, `microtype`, etc.). The actual build used pdfTeX/TeX Live 2025-dev. GNU Make is **not required**; the Python builder is the tested route. A Makefile is supplied as an optional convenience on systems with make.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

No API key, account, paid service, model inference, external embeddings, or gated dataset is needed. A 16-core/32GB machine should be sufficient for this implementation; benchmark a large cell before projecting its timings. Do not regard the host's large RAM as measured peak consumption.

## 2. Fixed data and provenance

Only the thirteen specified LLM binary matrices are used, at:

- Repository: https://github.com/socialfoundations/benchmark-prediction
- **Commit: `55faff496947789f94e6b5908c77cbc3e84f81ad`** (not a branch).
- OpenLLM banks: `arc_challenge`, `bbh`, `gpqa`, `ifeval`, `mmlu_pro`, `musr`, `openllm_math`.
- HELM-derived banks: `commonsense`, `gsm`, `legalbench`, `math`, `med_qa`, `mmlu`.

The supplied workspace retains the permitted full vendor checkout. A fresh code-archive extraction needs only:

```bash
python src/download_data.py
python src/download_data.py --verify-only
python src/audit.py
```

The script uses fixed-commit raw URLs, downloads only the 13 matrices and baseline-verification files, and checks the matrix SHA-256 hashes against `artifacts/data_audit.csv`. `artifacts/download_manifest.json` records paths, URLs, sizes and hashes. Never load untrusted joblib/pickle files: loading can execute code. This task explicitly permits the pinned artifacts.

The packaged repository is MIT-licensed; preserve `vendor/benchmark-prediction/LICENSE.txt`. Upstream benchmark/text/evaluation assets may have different terms; their full upstream licenses were not independently revalidated, no fresh task text was scraped, and no blanket new license is asserted over them. New code has the separate `LICENSE` below.

The estimand is the **flat binary matrix mean**, not necessarily the official benchmark's subject/scenario-weighted leaderboard score. Every file is checked finite/binary. All-zero rows, constant items, duplicate columns, and original item multiplicities are retained. In particular all 53 all-zero OpenLLM-MATH rows remain. Exact-response model rows are grouped across source/target splits; this prevents direct response-copy leakage, **not family/ancestry dependence**. Source training retains original row multiplicities; primary metrics weight each target duplicate group once. Original-row weighting is a sensitivity.

## 3. Reproduce experiments

From the workspace root:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest tests -q
python src/audit.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run_experiments.py --jobs 8
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/diagnostics.py --jobs 8 --reps 200
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/run_experiments.py --regimes gap --budgets 50 --jobs 8
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/irt_comparator.py --jobs 8
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/nearest_source.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python src/analyze.py
python src/fill_checklist.py
python src/build_paper.py
python src/verify_artifacts.py
```

Main and IRT runners cache completed cell JSON/NPZ files. To actually regenerate supplied existing predictions, add **`--force`** to `run_experiments.py` and `irt_comparator.py`, or run from a clean result directory. Diagnostics and nearest-source scripts recompute their panels. Do not combine results made under different code/configurations without explicit invalidation. `--names gsm --seeds 0 --jobs 1` is a fast main/IRT smoke run; `--names mmlu_pro --seeds 0 --jobs 1` tests the large-bank resource cost. Main smoke has both regimes by default. Keep all four budgets when generating final tables.

**Seeds and settings:** outer seeds 0–4, split namespace 1000+seed, uniform-query 20000+seed, stratified-query 30000+seed; source inner MIRT calibration 6021+seed; fixed-target selection 910; diagnostic masks 500000+r for r=0..199; bootstrap 701. These are reproducibility streams, not a proof that a finite seed schedule is an ideal conditional sampling distribution. Main budgets 10/25/50/100; primary endpoint b=50. Source split ~70% exact-response groups; tie-block frontier boundaries keep equal scores together; optional gap uses ~bottom50/top30. Full target outcomes enter only retrospective split construction and evaluation. The theorem concerns ideal randomized item selection with pilot/audit independence, not zero empirical bias over five seeds.

**Hypers:** five source-difficulty strata, target-item summed-loss ridge penalty10 and unpenalized intercept; source-score RidgeCV penalties0.1/1/10. Rasch and rank-5 MIRT priors, fitting/init/tolerances, binary-anchor approximation, inner validation and mixture formula are fully stated in paper Appendices C–D and code. MIRT is a point-estimate/source-calibrated adaptation, **not an exact hierarchical Bayesian tinyBenchmarks/gpIRT reproduction**. Nearest-source Hamming ties average all tied source rows and retain actual queried outcomes. No target-driven method tuning was performed. Full Bayesian GPIRT, metabench, learned RL acquisition, temporal/family-held-out deployment, new-item generalization and score-CI coverage were **not completed or claimed**.

## 4. Observed runtime and grids

These are script-measured wall times on the actual host, not guarantees on another machine:

| Stage | Completed grid | Measured wall time |
|---|---|---:|
| Original main | 13 banks × 2 regimes × 5 seeds × 4 budgets × 17 configurations = **8,840** group-metric outputs | **80.3 s** |
| Repeated masks | largest/median bank × 2 regimes × 2 budgets × 200 masks × 6 fixed target groups | **78.8 s** |
| Stronger gap | 13 × 5 seeds × b50, 17 configurations | **20.0 s** |
| Added MIRT controls | 130 cells, 260 source/inner fits, 2 estimators × 4 budgets | **569.5 s** |
| Added nearest source | 130 cells × 4 budgets | **4.95 s** |

The original 17 configurations include ablations and a labeled **2b extra-label-cost** reference; they are not seventeen independent published algorithms. Added controls bring main outputs to 20 configurations. Group and original-row metrics are both saved. Main worker-cell wall times sum to **544.4 s =9.1 cell-minutes**; MIRT sums to **3,840.6 s =64.0 cell-minutes**, including calibration and scoring. These are not hardware-counter CPU times. Some stages overlapped and had contention. Per-cell times and optimizer statuses live in run JSONs; stage summaries are `artifacts/*summary*.json`. Initial invalidated attempts and preparation costs are separate.

Fresh runs should be on the order of minutes to tens of minutes on a comparable multicore CPU, plus downloading/installing/building; this is a projection from measured stages, not a promised runtime. Eight large-bank MIRT fits can be the dominant stage. Reduce `--jobs` if memory/CPU is constrained; never silently reduce data/seed counts and call it the complete experiment.

## 5. Exactly how each paper table/figure is made

All quantitative paper tables, macros and data figures are produced by **`python src/analyze.py`**, reading saved numerical outputs only; nothing is copied from published result tables. There are no illustrative/synthetic benchmark outcomes in the paper. Tiny synthetic enumeration tests check code algebra and are explicitly distinct from empirical results.

| Paper artifact | Generated file | Underlying run source |
|---|---|---|
| Table1, comparison | `paper/tables/main.tex` | main + added MIRT/nearest results, b50 |
| Table2, ablation | `paper/tables/ablation.tex` | main matched configurations, b50 |
| Table3, data | `paper/tables/data.tex` | `artifacts/data_audit.csv`, seed0 split JSONs |
| Table4, per-bank frontier | `paper/tables/per_benchmark_frontier.tex` | main b50 five-seed bank means |
| Tables5–6, all metrics | `paper/tables/all_iid.tex`, `all_frontier.tex` | main and added control outputs |
| Table7, budgets | `paper/tables/budgets.tex` | original selected methods, all budgets |
| Table8, row sensitivity | `paper/tables/row_weighted.tex` | identical fits, original-row metrics |
| Table9, gap stress | `paper/tables/gap.tex` | gap b50 outputs |
| Table10, contrasts | `paper/tables/effects.tex` | four frozen b50 paired contrasts |
| Table11, masks | `paper/tables/diagnostics.tex` | actual 200-mask fixed-row panels |
| Figure1, budget curves | `paper/figures/budget_curves.{pdf,png}` | macro MAE and descriptive bank intervals |
| Figure2, bank effects | `paper/figures/paired_effects.{pdf,png}` | original frontier b50 effects |
| Figure3, bias diagnostics | `paper/figures/bias_diagnostics.{pdf,png}` | shared-mask means ±2 MCSE |
| Prose numeric macros | `paper/tables/numbers.tex` | same CSV/JSON results |

Final PDF numbering above is checked after build. `artifacts/analysis/all_metrics.csv` is long-form (bank, regime, seed, budget, method, weighting, metrics); `macro_summary.csv`, `per_benchmark.csv`, `primary_effects.json`, and `repeated_mask_summary.csv` expose the aggregation. NPZ keys `method__b50`, `u_50`, `s_50`, `sp_50`, `sa_50`, `anchors_50`, source/target rows, truths and group representatives make masks and scores auditable. Per-method nuisance full-bank predictions are not all stored because they can be recomputed and are unnecessary for score-metric checks. Diagnostic NPZs retain targetwise repeated predictions.

**Uncertainty:** MAE/CI units are percentage points in the paper but fractions in data CSVs. Macro RMSE = sqrt(mean bank/seed/group MSE), not mean per-bank RMSE. Bootstrap resamples13 seed-averaged bank means, 10,000 draws, paired by bank; correlation/dependence makes intervals descriptive. Four planned sign-flip summaries receive Holm adjustment, without a claim that Holm fixes bank dependence. MCSE uses replicate-level target-mean errors under each shared mask; squared empirical bias includes finite-mask noise. Correlations are within-bank; never concatenate unrelated banks into one leaderboard.

## 6. Audit fixes, negatives and provenance

- The fixed public AIPW implementation and paper-level population correction differ; both are retained and numerically tested against the original classes. An intercept makes training residual means zero. Their MAEs are similar here, so the code discrepancy is not inflated into the main empirical gain.
- An initial main run stopped after42 completed cells because the **source-only** Rasch convergence monitor hit its cap. Exact common-shift prior minimization repaired this; all main cells were rerun. `logs/optimizer_repair.json` and the preliminary log preserve the failed attempt.
- Added multidimensional IRT was declared after primary analysis (`logs/irt_comparator_amendment.md`). Four cap250 smoke cells were superseded by the full cap1000 run; all260 final source/inner fits report numerical success, maximum474 iterations. This is not a global optimum or a saved target-optimizer certificate.
- Self-review found machine roundoff splitting mathematically identical prediction ties. **Fixed:** ordering metrics alone round truth/predictions to10 decimals; raw MAE/RMSE/bias/predictions are unchanged. `src/recompute_metrics.py` performs legacy saved-result postprocessing, `logs/rank_correction_ledger.csv` preserves before/after fields, and **1,170** uniform/stratified common-offset rank checks pass. New runs calculate the corrected metrics directly; do not overwrite the historical correction ledger just to rerun a no-op.
- A nearest-source control was added after review without tuning, and the no-audit caption now correctly distinguishes each half-fit from total b-label use. The unsupported “error floor” phrase was removed; only finite-budget observations are claimed.
- The final suite has **12 passing tests**. `artifacts/paper_review.md` and `artifacts/analysis/independent_audit.md` are retained **historical** reviews; see `logs/review_resolutions.md` and final verification for repaired findings. Incremental contribution/main-track risk remains, rather than being falsely marked solved.
- A pandas name collision and missing LaTeX command/package were repaired during analysis/build; these did not change experimental outcomes. GNU make was unavailable, so the tested builder uses Python subprocesses. No failed benchmark was silently removed.

## 7. Restricted reading / incidental access disclosure

No open-ended literature search, citation traversal, citing-paper page, or attempt to infer the prohibited paper's identity was used. Only seven user-allowlisted starter papers were read through their primary arXiv URLs; the allowed fixed repository and official conference template/rules were inspected. Actual versions read include later revisions, explicitly recorded in `literature/reading_notes.md` and BibTeX. Their reference lists were withheld from reading. Ordinary main-text citations were encountered. Official template sample bibliography boilerplate and handbook further-reading labels were incidentally displayed; none of those links was followed. Since the excluded work was unspecified and identity inference was forbidden, complete absence of an incidental mention cannot be certified. Exact URLs, reading depth, extraction safeguards, failures, hashes and exposure extent are disclosed, not guessed.

Official template provenance: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip ; rules: https://neurips.cc/Conferences/2026/MainTrackHandbook . Style SHA256 is verified unchanged. Using the2026 style does not imply its closed submission deadline remains open.

Autonomous LLM agents assisted design, implementation, literature reading, checking and writing. All scores and plotted quantities come from actual numerical execution on the allowed fixed matrices. The checklist explicitly discloses methodological LLM use, absence of independent human ethics certification, and the residual upstream-license verification limitation.
