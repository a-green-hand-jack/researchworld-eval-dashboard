# Artifact map and manuscript-to-result provenance

All paths below are **relative to the release root**, not a required `/work` installation. `paper.tex` is the manuscript source of record. Labels are authoritative if final float placement/page numbers change. Every scientific figure/table in that source is mapped below: **3 figures, 11 tables**. Results are measured, not schematic or placeholder data.

## 1. Dependency graph

```text
get_data.py --online--> data/ + manifest.json
  experiment.py --main30--> results/ main NPZ + JSON + data manifests
                --B16----> results/ *_b16 NPZ + JSON
                --n120---> results120/ NPZ + JSON + data manifests
  analyze.py --results results120 --sensitivity-results results
             |-- analysis120/ [0,120): main expanded analysis
             |-- analysis90/  [30,120): held-out next90 analysis
             |-- prefix audit against original30 results/
             |-- tables, bootstrap arrays, summaries, plots
  render_paper_tables.py <-- analysis120/ CSV --> paper_tables/{macro_metrics,cohorts}.tex
  make_failure_example.py <-- results120/pima_mlp_11.npz --> paper_tables/failure_example.{tex,json}
  paper.tex + references.bib + official template + analysis120/ imports
            + paper_tables/ imports + checklist_filled.tex
     -- sh build.sh --> paper.pdf
```

Raw data and fitted models are **not needed** below the analysis layer. `results/` original30 is required for expansion prefix validation even when only next90 is reported. Figures/tables do not use `model_*.joblib`.

## 2. Generator commands

From the extracted root, after installing `requirements.txt` in Python3.11 (see `README.md`):

```sh
ROOT="$(pwd)"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
# A120: canonical expanded analysis + tables + all three plots
python "$ROOT/analyze.py" --results "$ROOT/results120" \
  --out "$ROOT/analysis120" --expected-n 120 \
  --start-instance 0 --stop-instance 120 \
  --sensitivity-results "$ROOT/results"
# A90: same full source, held-out slice only; first10 B16 unchanged
python "$ROOT/analyze.py" --results "$ROOT/results120" \
  --out "$ROOT/analysis90" --expected-n 120 \
  --start-instance 30 --stop-instance 120 \
  --sensitivity-results "$ROOT/results"
# A30: original30 replay without overwriting the historical archives
python "$ROOT/analyze.py" --results "$ROOT/results" \
  --out "$ROOT/analysis30_replay" --expected-n 30 \
  --start-instance 0 --stop-instance 30 \
  --sensitivity-results "$ROOT/results"
# P: figures only, from existing measured CSVs/summary
python "$ROOT/analysis120/plot.py" --out "$ROOT/analysis120"
# T: manuscript-only macro/cohort table rendering; no new inference
python "$ROOT/render_paper_tables.py"
# F: deliberately selected existing-array example; no new prediction
python "$ROOT/make_failure_example.py"
# B: supplied by main-agent release assembly
sh "$ROOT/build.sh"
```

A120/A90 update canonical analysis outputs. For preservation-safe replay, replace their `--out` with `"$ROOT/replay/analysis120"` / `"$ROOT/replay/analysis90"` after `mkdir -p "$ROOT/replay"`. T/F have **no output-directory option** and still read canonical paths beside the scripts; P must point to the directory actually replayed. `analyze.py` has **no `--original-results` flag**; `--sensitivity-results` is the B16 location **and** original30 baseline. Always supply `--out`; do not overwrite the retained `analysis/`/`analysis30/`.

## 3. Every manuscript figure

| Figure / LaTeX label | Exact manuscript artifact | Measured table feeding figure | Script / replay |
|---|---|---|---|
| Fig.1, `fig:budget`: budget versus top3 recovery | `analysis120/budget_accuracy.pdf` (also `.png`) | `analysis120/cell_summary.csv` | A120 or P; master source `plot_precision.py`, saved `analysis120/plot.py`, per-figure `analysis120/budget_accuracy/plot.py` |
| Fig.2, `fig:gap`: oracle reference-gap strata | `analysis120/gap_budget.pdf` (also `.png`) | `analysis120/gap_summary.csv` | A120 or P; saved per-figure `analysis120/gap_budget/plot.py` |
| Fig.3, `fig:repeatability` (appendix): repeatability vs target match | `analysis120/repeatability_accuracy.pdf` (also `.png`) | `analysis120/cell_summary.csv` | A120 or P; saved per-figure `analysis120/repeatability_accuracy/plot.py` |

Each per-figure directory contains `inputs.csv`, `context.json`, `plot.py`, `plot.pdf`, `plot.png`, `figure-spec.md`, `audit.md`, `final-status.md`. To replay an individual plot from its exact saved inputs, run, for example:

```sh
python "$ROOT/analysis120/gap_budget/plot.py"
```

That individual command writes `plot.pdf/.png` **inside the figure directory**, not the top-level imported `gap_budget.pdf`; P refreshes top-level copies. Structural plot audits say `PASSED_WITH_WARNINGS`, not certified human visual validation. German panels are approximate-reference only; the gap figure excludes German. Kernel P64's full-enumeration branch is labeled; no figure is a package timing benchmark.

## 4. Every manuscript table

| Table / LaTeX label | Imported TeX or inline source | Numerical source / full-precision companion | Generator |
|---|---|---|---|
| Table1 `tab:nine`: all nine antithetic cells | `analysis120/paper_antithetic_9cells.tex` | Matching `.csv`; expanded `cell_summary.csv`, `per_seed.csv` | A120 (`analyze.py`, compact precision tables) |
| Table2 `tab:controls`: exact-game macro controls | `analysis120/paper_exact_macro_controls.tex` | Matching `.csv`; `analysis120/exact_macro.csv` | A120 |
| Table3 `tab:data`: actual splits/dimensions | `analysis120/paper_data_splits.tex` | Matching `.csv`; `analysis120/data_splits.csv`; `results120/data_*.json` | A120 |
| Table4 `tab:performance`: all seed fits, full test metrics | `analysis120/paper_model_performance.tex` | Matching `.csv`; `analysis120/model_performance.csv`; result JSON `metrics` and `warnings` | A120; no new fitting during analysis |
| Table5 `tab:metrics`: macro secondary metrics | **`paper_tables/macro_metrics.tex`** | **`analysis120/exact_macro.csv`**, antithetic rows, means + interval endpoints | **T (`render_paper_tables.py`)**, after A120 |
| Table6 `tab:cohorts`: first30 / next90 / combined120 | **`paper_tables/cohorts.tex`** | **`analysis120/expansion_cohort_headlines.csv`**, `dataset=exact_macro` | **T**, after A120; A90 separately verifies held-out analysis |
| Table7 `tab:gaps`: every oracle gap bin/budget with game/cluster counts | `analysis120/paper_gaps_per_budget.tex` | Matching `.csv`; `analysis120/gap_summary.csv` | A120 |
| Table8 `tab:failure`: worked near-tie failure | **`paper_tables/failure_example.tex`** | **`paper_tables/failure_example.json`**, from `results120/pima_mlp_11.npz`, position62, P64, first repetition | **F (`make_failure_example.py`)**, no new model calls |
| Table9 `tab:german`: independent reference pools | `analysis120/paper_german_reference_pools.tex` | Matching `.csv`; `analysis120/reference_pool_summary.csv` | A120 |
| Table10 `tab:sensitivity`: first10/seed11 B8 versus B16 | `analysis120/paper_sensitivity_first10.tex` | Matching `.csv`; `analysis120/background_sensitivity.csv`; `results/*_11_b16.*` plus main first10 arrays | A120; same first10 sensitivity in A90, not next90 sensitivity |
| Table11 `tab:costs`: logical row allowances | **Inline `tabular` in `paper.tex`**, not an imported TeX table | `analysis120/logical_costs.csv` (also generated `.tex`); formula B[2+2P(d−1)], exact cube B·2^d | **A120** computes audit table; **B** renders manuscript's inline table. No separate cost-table renderer exists. |

The failure case is deliberately selected post hoc, not representative: Pima/MLP seed11/source row64, reference gap0.00026682, recovery4/20 atP64. Its script outputs attribution vectors and feature names, not raw patient attributes. Table5 material-sign coverage excludes undefined games and is not a feature-coverage claim. Table11's German exact cube is `---` because it was not run, not a missing measured result to fill.

## 5. Numerical claims outside the figures/tables

| Claim/provenance family | Canonical artifacts |
|---|---|
| Main/held-out completion, headline means/CIs and scope | `analysis120/summary.json`, `analysis90/summary.json` |
| Original exploratory analysis and preserved archive | `analysis/`, `analysis30/`, `precision_expansion.md`; A30 writes elsewhere |
| Every method/cell/budget and valid counts | `analysis120/cell_summary.csv`, `per_seed.csv`, `instance_clusters.csv` |
| Macro secondary metrics and sign availability | `analysis120/exact_macro.csv`; `cell_summary.csv` legacy `material_feature_coverage` = fraction of games with **any** material feature, not fraction of features |
| Paired gains and all63 corrected contrasts | `analysis120/paired_comparisons.csv`, `contrast_bootstrap.npz` |
| Bootstrap input arrays and exact resampling indices | `analysis120/analysis_inputs.npz`, `input_metadata.json`, `versions.json`; analogous `analysis90/` outputs |
| Original30 exact prefix and frozen metadata equality | `analysis120/original_prefix_audit.json`, `original_prefix_npz_audit.csv`; analogous `analysis90/` outputs |
| Input dimension/finiteness, instance/background/split checks | `analysis120/validation.json`, `analysis_tests.json`, `analysis90/analysis_tests.json` |
| Predicted performance and small-model failures | `analysis120/model_performance.csv`, result JSON sidecars; no prediction-level uncertainty fabricated from aggregate metrics |
| Logical vs shared actual compute | `analysis120/logical_costs.csv`, `resources.csv`; `summary.json` → `campaign_resources`; source per-cell JSON counters/timers |
| Synthetic/exact/package-smoke numerical errors | `results/tests.json`, generator `tests.py` (requires local data, fits a model) |
| Loading/resume failure and fix | `experiment_main.log`, `debug_log.md`, `experiment.patch`, `debug_regression.py` |
| Subsequent campaign progress | `experiment_resume.log`, `experiment_sensitivity.log`, `experiment_expansion.log` |
| Self-review judgments and independent numerical replay | `self_review.md`, `claim_audit.json` (historical line numbers/findings, not all current blockers) |
| Post-review manifest fix validation | `postreview_checks.py`, `postreview_checks.json`: both Pima/ACS main manifests unchanged |
| Environment provenance | `requirements.txt`, `environment.json`, `paper_environment.json`; assembly/post-hoc inventories, not historical allocation/peak RAM |

`test_precision_analysis.py` is analysis-only: it checks saved canonical outputs, hash identity, cohort slices, paired metrics/intervals, corrected bands, source-run timing scope and retained archive equality. It writes verification JSON, not model predictions. `debug_regression.py` and `postreview_checks.py` require local raw inputs for loading but do not fit models. `tests.py` is **not** raw-free replay and should precede experiment campaigns.

The measured **0.3319 CPUh** total counts original30+B16 once and expanded120 including prefix replay once. Next90 timing columns retain full-source CPU/wall values, while row/prediction counters follow the slice; do not sum overlapping analysis reports or prorate full CPU to an estimator/cohort.

## 6. Sources, access constraints and release inventory

| Material | Location and boundary |
|---|---|
| Five actually read/cited originals | `sources.md`, `references.bib`, `originals/`: 1705.07874v2; 2006.16234v1; 2410.01917v3 (2026-10-08); JMLR18(174)2018; 2108.04884v3. Targeted reading, not exhaustive literature coverage. |
| Official venue/template | `official/neurips2026_cfp.html`, `official/neurips2026_handbook.html`, `template/Formatting_Instructions_For_NeurIPS_2026.zip`, unmodified `template/neurips_2026.sty`, `template/neurips_2026.tex`, `template/checklist.tex`, `template/manifest.json` |
| Official ethics material | `official/ethics.html`, `official/ethics.txt`; distinct from the five research works |
| Original-literature/venue acquisition log | `access_log.jsonl`; URLs, UTC, status, bytes, hashes; precise read scopes in `sources.md` |
| Data identity/license sources | `DATA_LICENSES.md`, `data_access_log.jsonl`, `official/data_licenses/`; failed/irrelevant Census policy attempts retained, not cited as permission |
| Local acquisition integrity | `data/manifest.json`, reference hashes in `DATA_LICENSES.md`, `official/data_licenses/local_validation.json`, `local_provenance.json`; hashes do not prove permission or a logged original transaction |
| Original task/protocol history | `research_request.md`, `precision_expansion.md`, `protocol_clarification.md`; not retroactive preregistration |

No prohibited prior work was identified/read in displayed scopes. Do not infer its identity or follow pages citing/discussing/reproducing it. No topic search, recommendation or citation-graph discovery is part of this provenance. Raw saved originals may retain unread bibliographies; presence on disk is not a reading claim. Documentation writing used local artifacts only.

**Archive inclusion boundary:** include code/downloader/requirements, documentation, manuscript/build assets, template with notices, and derived experiment/analysis outputs needed for replay. Do **not** bundle `data/` raw archives/ARFF/CSV/pickle, row-level source subsets or `results*/model_*.joblib`. Retain source identifiers/hash notices without treating them as clearance. Local raw/model files exist but are outside the intended release archive. German redistribution separately requires CC BY4.0 attribution; Pima/Census detailed reuse terms remain unresolved. Original research PDFs and other third-party source snapshots also have their own terms; reading provenance is not a blanket redistribution grant.

## 7. Manuscript assembly gate

`paper.tex` imports not just its main figures/tables but **appendix** `analysis120/*.tex` and all three `paper_tables/*.tex`. T and F are therefore mandatory before building if outputs were omitted. Plain LaTeX tables avoid pandas Styler/Jinja2; do not add Jinja2 to solve a nonexistent dependency.

Official NeurIPS2026 initial main limit is9 pages; checked preview main length is8. References, optional technical appendices and mandatory filled checklist are outside that count and must remain in **one final PDF, checklist last**. `paper_audit.json`/`self_review.md` concern a preview without the checklist, not final release verification.

**Final release assembly passed:** `build.sh`, `build_paper.py`, `prepare_checklist.py`, and `checklist_filled.tex` are supplied. `sh "$ROOT/build.sh"` built `paper.pdf`; `build_validation.json` verifies **8 main pages**, **26 total pages**, references at page 9 and the 16-answer checklist at page 20, unchanged official style, no undefined references and no overfull boxes. All appendix/T/F inputs are present; no extra Jinja2 is needed.

Final scientific/reproduction status: empirical claims remain bounded, novelty/acceptance unresolved, and this is not a claim of peer-reviewed publication. Historical self-review B1 is fixed via sensitivity namespaces; `postreview_checks.py` was executed and its saved checks pass for Pima/ACS. No broad experiment rerun was performed for that repair.
