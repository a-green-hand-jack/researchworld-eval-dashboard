# Experiment and release log

Date: **2026-11-04 UTC**. This is a retrospective, evidence-linked log, not an externally timestamped preregistration. Documentation work did **not** run experiments, change the paper/code, or regenerate measurements. Only `README.md`, `final_report.md`, `experiment_log.md`, and `ARTIFACT_MAP.md` are documentation deliverables.

## 1. Question and frozen design

Question: with a fitted tabular classifier, fixed input and finite empirical background, how often does **one** finite-budget paired permutation estimate recover the unordered top-three absolute Shapley players? Approximation fidelity is distinct from whether the model or explanation game supplies a valid real-world reason.

Frozen settings: Pima/OpenML37 v1, ACSIncome 2018 1-Year VT persons via Folktables0.0.12, UCI German dataset144 raw categorical file; LR/RF/MLP; seeds11/23/47; B8; R20; nested P1/4/16/64. Pima/ACS have exact finite-background targets; German has two independent 512-cycle reference pools. Equal-row-allowance one-way and constrained Kernel controls are implemented only for the exact datasets. Full acquisition URLs, preprocessing, model parameters, seed formulas and executable reproduction commands: `README.md` and the reproduction appendix in `paper.tex`.

Success signals were numerical correctness, completion/validation of all cells, paired budget/comparison evidence, and explicit failure boundaries—not automatic passage of the illustrative 0.95 criterion.

## 2. Chronology and decisions

| Stage | Recorded evidence | Outcome and interpretation |
|---|---|---|
| Restricted source reading and official template | `sources.md`, `access_log.jsonl`, `originals/`, `template/manifest.json` | Five allowed originals read to recorded scopes; official NeurIPS2026 selected. No literature topic search/citation-graph/repository discovery. |
| Acquisition and setup | `get_data.py`, `data/manifest.json`, `results/data_*.json`, `requirements.txt` | Identifiers fixed; train-only per-feature preprocessing; explicit splits and audit/background orders. Exact initial data-download transactions were not all logged. |
| Numerical/integration checks | `tests.py`, `results/tests.json` | Synthetic/factorial/exact-Kernel/efficiency and same-path averaging checks pass. SHAP-package checks are smoke tests, not categorical-game equivalence or speed results. |
| Original main campaign, n30 | `experiment_main.log` | Initial campaign interrupted by German pandas StringDtype loading error (see below); do not describe this run as uninterrupted success. |
| Loading/resume correction | `debug_log.md`, `experiment.patch`, `debug_regression.py` | Nonnumeric categorical detection and fail-closed resume checks; no unfavorable measurement removed. |
| Resume to completed original30 | `experiment_resume.log`, `results/*.npz` + JSON, `analysis/`, `analysis30/` | 27 main cells completed, including German. Original30 results were inspected and are exploratory. |
| B16 sensitivity | `experiment_sensitivity.log`, `results/*_b16.npz` + JSON | Six exact-dataset/seed11/first10 cells completed. Own-target comparisons retain both improvements and degradations. |
| Uniform precision expansion specification | `precision_expansion.md` | After inspecting n30, before expanded outcomes: expand **all** 27 main cells to120 without retuning or changing streams, thresholds, models, backgrounds or metrics. Sensitivity remains first10. |
| Expanded computation | `experiment_expansion.log`, `results120/` | 27 completed cells; log reaches120/120. Original30 prefix recomputation is real compute, included in costs. |
| Full120 and next90 analyses | `analysis120/summary.json`, `analysis90/summary.json` | Both `complete`, main27/27, B16 six/six, prefix audit27/27 exact equality. All120 inputs validated before slicing. |
| Independent analysis checks and manuscript self-review | `analysis120/analysis_tests.json`, `analysis90/analysis_tests.json`, `self_review.md`, `claim_audit.json` | Paired metrics/intervals and 63-contrast correction checked. Self-review found a fresh-run artifact-writing blocker, not a numerical headline error. Automated checks are not independent human review. |
| Bounded post-review repair | `postreview_checks.py`, `postreview_checks.json`, final `experiment.py` | Sensitivity manifests/model files now use `_b16` namespaces. Pima/ACS main30 manifests unchanged after sensitivity loading. Valid frozen results were not rerun or replaced. |
| Failure illustration and terminology clarification | `make_failure_example.py`, `paper_tables/failure_example.json/.tex`, final `paper.tex` | Existing-array near-tie example added; “any-material-game availability” distinguished from feature-level coverage. No new model evaluation/inference. |
| License audit and release assembly | `DATA_LICENSES.md`, `data_access_log.jsonl`, `official/data_licenses/` | German CC BY4.0 declaration verified; Pima and Census detailed terms unresolved. Release raw-data/model exclusion required; final build/checklist remains assembly gate. |

No exact per-stage start/stop timestamps or elapsed makespan are invented here; source requests have UTC timestamps in the access logs, and cell timing sidecars provide the compute accounting below.

## 3. Failures, repairs and rejected substitutions

### F1. German loading failed under pandas3

`experiment_main.log:472–529` records `Cannot use median strategy with non-numeric data ... 'A14'`. Object-only detection missed pandas StringDtype, so a categorical credit field was sent to median imputation.

Correction: nonnumeric dtype detection preserves most-frequent categorical imputation/one-hot encoding and median/scaling for numeric fields. `debug_regression.py` covers inferred/object/string/category German loading, Pima/ACS loading, and 16 synthetic resume cases; training and SHAP construction are mocked as forbidden in this regression. `debug_log.md` records three tests passed and unchanged existing artifact bytes. Completed compatible cells were resumed; incompatible pilot/shape/repetition/budget/background/sidecar inputs fail without silent replacement. Pilot is isolated in `results/pilot/`.

### F2. Sensitivity overwrote main manifests in the pre-fix implementation

Historical `self_review.md` blocker B1: ten-instance B16 loading wrote main `data_pima.json`/`data_acs.json`, breaking a fresh original30 prefix audit. Existing valid analyses were not invalidated by that finding. The review's manifest-reconstruction workaround is **historical, not a required step with the final code**.

Final repair: sensitivity `data_{dataset}_b16.json` and `model_{dataset}_{model}_{seed}_b16.joblib` no longer overwrite main files. `postreview_checks.py` **was executed**; saved JSON reports for both Pima and ACS `main_n=30`, `sensitivity_n=10`, `main_manifest_unchanged=true`. The test also asserts identical backgrounds and first10 IDs in temporary loading outputs. This establishes bounded loading isolation, not a fresh full campaign rerun. The analyzer validates B16 instances/background against retained main manifests; old frozen results need not acquire new namespace files to remain usable.

### F3. Do not change the estimand to get an easier reference

Summing independent dummy-column TreeSHAP values is not an exact grouped raw-player reference. That shortcut was rejected. German remains an approximate two-pool-reference study; no exact German/RF result or formal reference-error bound is claimed. Equal-sized repeat-and-average over identical sampled paths is a longer run algebraically, not a new method.

## 4. Measured outcomes, including negatives

- Exact-game combined120 macro top3 recovery: P1 **0.7656 [0.7523,0.7790]**, P4 **0.8781 [0.8675,0.8882]**, P16 **0.9366 [0.9287,0.9440]**, P64 **0.9656 [0.9597,0.9709]**. Next90: P1 **0.7705**, P64 **0.9666**; original30: **0.7511/0.9628**. Cohort CIs and counts: `analysis120/expansion_cohort_headlines.csv`.
- P64−P1 macro gain **19.998 pp**, marginal interval[18.863,21.121]pp, joint63-contrast band[14.956,25.039]pp. P64 antithetic−one-way band[−1.400,8.683]pp spans zero. `analysis120/paired_comparisons.csv`.
- P64 exact Pima/MLP **0.9400** and ACS/MLP **0.9490** both below the user-defined0.95 point criterion, with intervals crossing it. Small-gap MLP strata remain **0.7647/0.7790**. No threshold certification follows from macro0.9656.
- Kernel P64 exactly enumerates both small cubes and achieves1.0000 at lower logical row cost; this is not a sampled-estimator or optimized-package superiority result.
- P1 material-sign agreement macro **0.9983** coexists with top3 recovery0.7656. Undefined material-sign games are excluded only from that metric; 2159/2160 exact games contain at least one material feature. Stability/repeatability are not correctness probabilities.
- German pool top3 agreement LR/RF/MLP **0.9917/0.9806/0.9778** leaves ambiguity; German/MLP P64 approximate-reference match **0.9493**. All pool disagreements retained.
- B8→B16 changes target top3 for Pima **5/5/4 of10** and ACS **9/5/7 of10** (LR/RF/MLP). MLP P64 own-target recovery changes Pima **1.000→0.985**, ACS **0.930→0.960**; no uniform improvement.
- Weak MLP fits retained: Pima seed23 AUC0.4826, German seed23 AUC0.5711. Approximation fidelity cannot make their predictions good.
- Worked failure: Pima/MLP seed11, zero-based audit position62/source row64, reference gap0.00026682, P64 recovery4/20. Post-hoc illustration, not representative sampling or extra validation.

Uncertainty is descriptive, conditional on fixed fits/backgrounds: 2,000 paired instance-cluster bootstrap replicates; joint max-centered-absolute-deviation correction for the63 reported contrasts. No pseudo-replication from seeds/repetition pairs, universal finite-sample guarantee, survey-population claim or calibrated reference-free selector. At n120 even perfect outcomes give a maximum illustrative24-cell Hoeffding lower bound0.8396 under its assumptions; ACS sampling assumptions are unverified.

## 5. Cost ledger

Source: `analysis120/summary.json` → `campaign_resources`, plus `analysis120/resources.csv`.

| Successful campaign scope | Completed cells | Process CPU seconds | Sum of cell wall seconds | Shared cached model rows |
|---|---:|---:|---:|---:|
| Original30 main + B16 once | 33 | 260.540218 | 539.120842 | 126,314,640 |
| Expanded120 including first30 replay once | 27 | 934.138349 | 1,615.335063 | 502,776,528 |
| Total counted success | 60 | **1,194.678566** | **2,154.455905** | **629,091,168** |

Total **0.3319 CPUh**, not24h. B16's component is15.243676 CPU seconds/42.442605 summed wall seconds/614,400 rows; do not add it again. Next90 analysis reuses expanded120 and adds no experiment campaign. Failed/incomplete attempts and orchestration overhead were not recoverably measured; package/data acquisition, analysis/plotting, documentation and TeX cost are outside this ledger. Cell wall sums are not elapsed parallel makespan; shared reference/control caches prevent per-estimator or deployment-latency attribution.

Environment inventory is assembly-time Python3.11.15 and pinned `requirements.txt`, not a historical lockfile. Historical hardware allocation and peak RSS were not logged. `environment.json` is post-hoc host inspection only.

**Reproduction estimate, not a measurement:** compatible multi-core CPU with dependencies/data ready: replay about1–5min; full small-model workflow/checks/build about5–30min, machine-dependent and potentially longer on constrained hosts. Estimates are based on ~20 CPU-minutes and ~36 summed cell-wall minutes, not measured end-to-end makespan. Online installs/downloads add network-dependent time. Current release recipe uses main8 workers, sensitivity4, numerical threads1 each.

## 6. Executable recovery and release gates

Run from release root, set `ROOT="$(pwd)"`, activate the Python3.11 environment and set the four thread variables as in `README.md`.

- Raw-data-free replay uses `analyze.py` on saved NPZ/JSON. Both `--out` and the expanded `--sensitivity-results` baseline must be explicit. **No `--original-results` flag exists**. Full commands, including all slice flags, are in `README.md`.
- Fresh experiment sequence: original30 → B16 → expanded120 → analyses. B16 no longer requires manifest restoration. `tests.py` does model fitting and writes a main Pima manifest, so it precedes campaigns and is not part of raw-free replay.
- `render_paper_tables.py` generates macro/cohort appendix tables from canonical `analysis120/`; `make_failure_example.py` generates the illustration from canonical `results120/`. No Jinja2 needed. Neither automatically follows optional `replay/` paths.
- **Final PDF gate passed:** `sh "$ROOT/build.sh"` generated `paper.pdf`; `build_validation.json` confirms 8 main pages≤9, 26 total, references at page9, completed 16-item checklist at page20, official style unchanged, no undefined citations/references or overfull boxes. A build-only missing-xcolor error was fixed by explicitly loading xcolor; the page locator was adjusted for official review line numbers. Neither change affects measurements.
- Exclude raw files, pickles, row-level source subsets and fitted joblib models from the release archive even if present locally. Downloader/provenance/derived audit outputs remain. Data license uncertainty is not repaired by a checksum.

## 7. Unfinished scope and independence

Not executed: tolerance-aware top-k sensitivity beyond the reported exact tie-breaking and gap strata; optional Give Me Some Credit/Arrhythmia or other additional datasets; optimized SHAP/Leverage implementation comparisons; exact German truth/grouped-game RF audit; tuning, calibration, causal/subgroup fairness/human-use studies; prespecified design-weighted ACS resampling; deployment budget selector. These are scope boundaries, not fabricated completed experiments.

Only five original works were read/cited, to exact scopes in `sources.md`: arXiv1705.07874v2, 2006.16234v1, 2410.01917v3 (2026-10-08), JMLR18(174)2018, 2108.04884v3. Official NeurIPS2026 CFP/handbook/template and ethics material are separate; data/license audit endpoints and failed Census policy attempts are documented in `DATA_LICENSES.md` and `data_access_log.jsonl`. Do not follow literature links in those materials or infer the prohibited work's identity. Recorded displayed readings recognized no prohibited material; raw fetched PDFs retain unread bibliographies. This is a bounded access/exposure account, not exhaustive screening. Documentation phase made no new external requests.

The study was LLM-mediated without human validation. Limited novelty and main-conference acceptance risk remain despite strong artifact auditing. The result is not a claim of peer-reviewed publication or clinical/credit suitability. **Final known self-review blocker: manifest namespaces fixed; `postreview_checks.py` executed and passed the saved bounded regression.**
