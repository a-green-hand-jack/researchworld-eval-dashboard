# Experiment and development log

Date: 2026-11-02 UTC. No model training, GPU, paid API, or private data.

## Intake / source boundary
- Blank workspace; root `/work`. Original task summarized in `research_request.md`; frozen local analysis plan in `todos.md` before score analysis. This is a local timestamped plan, not an independent preregistration.
- Autonomous implementation by main agent; planner, restricted-source researcher, mathematical auditor, appendix writer and paper reviewer delegated. No code-agent mode preference was presumed.
- Research agent used only exact user-permitted original source URLs. Scope and accidental preview disclosures in `sources/access_log.md`; no thematic search or forbidden-work identification attempted.

## Attempts, failures and corrections
1. File-list tool batching initially failed because wrapper calls lost required path arguments. Switched to direct calls; no research result affected.
2. Exact URL guesses for ICLR 2026 template files returned HTTP 404. Chose ICML 2026 instead, retrieved official style ZIP and AuthorInstructions; no modified margins/fonts/page layout. Official author page says 8 main pages, references/appendix separate and Impact Statement mandatory.
3. Initial HELM listing filter selected 114 subject-containing files, two parallel exported table sets, and failed expected-count assertion before downloading scores. Narrowed to `mmlu_mmlu_subject:` prefix, exactly 57. Corrected download successful. No duplicate task coordinates entered analysis.
4. Frozen plan mistakenly described Open Raw as percent. Schema/first-row audit established Raw is already a fraction; corrected implementation before analysis. Normalized percentages alone divided by 100. All 4,576 rows valid; official normalized-average reconstruction max error 1.6653345369377348e-16.
5. Pilot: 12 HELM targets across Borda ranks, complete competitor roster, rho=.5, Borda solver about .06 s total. Infeasible cases explicitly returned; finite cases numerical gap zero. Full-cohort execution justified rather than replacing with sample.
6. Full primary/sensitivity run: see `artifacts/timing_all.json`: 104.56 s wall, 104.45 s process CPU. Six result CSVs, 128,915 cases. Zero unresolved/timeout statuses. These timings exclude installation, source reading, tests, independent validation, plotting, writing and later clean reproduction.
7. Initial five support-oriented test groups passed. Mathematical audit found wording/quantifier defects: nonnegative median crossing deficit, strict cardinal nonattainment, shared-first scope of nonordering, four distinct matrices rather than six. Proof text repaired; no empirical K values changed.
8. Independent full saved-witness/infeasibility audit: 147.95 s; all 128,915 cases passed. All 238 positive HELM Borda optima have zero numerical gap and matching bound, not formal certificates. Tolerance reruns at 0 and 1e-10 changed no primary K/feasibility.
9. Fixed-cohort analysis: triple-rule half-cap feasible nonwinners N=31/1839. Same IDs reused at full cap. Pair-only cohorts N=37/2926 check that Borda selection is not necessary for the reversal. Target resampling is descriptive, not a population uncertainty estimate. Seeds 17/29/43, 2000 draws each. Individual target signs, not only averages, saved.
10. Optional HELM leave-one-task-out not run because n=56 conventional median lacks a large-panel analytic implementation. Explicit bounded substitute drops two preselected subjects, keeping n=55 odd. Open all six leave-one-out panels run, changing n=6 to5; parity/confounding and empty/single-target conditional cohorts disclosed. No task-population robustness claim.
11. Publication PDFs initially used TrueType fonts. Attempted Matplotlib usetex; initial defaults failed because cm-super/type1ec was absent. A direct CTAN type1ec fetch did not solve a relative TEXMF lookup in temporary LaTeX directories. `sudo` was disallowed and no elevation occurred. Final solution uses existing Times/Helvetica/Courier LaTeX Type-1 families, not Computer Modern default family checks; PNGs use DejaVu Serif without dvipng. No required font or package download remains in the code path. Final recursive PDF font audit passes.
12. Initial compiled anonymous paper had literal AUTHORERR from missing corresponding-author declaration. Self-review caught it; an anonymous reserved `.invalid` contact declaration satisfies the template (identity suppressed in anonymous mode), and build script now rejects AUTHORERR. Long snapshot hash fixed with an explicit safe line break; no overfull boxes remain.
13. Paper self-review verified all headline quantities but required “on average/shared first,” removal of unsupported generic tractability wording, cleaner resampling language, and reproduction documentation. Repaired those and figure legend placement. Added two dedicated magnitude test groups, including baseline/infeasible/strict-zero-deficit/cap-equality cases and independent formula checks plus 77/64 saved-data regression. Final tests: 7 passed, original environment 27.26 s.
14. Fresh isolated Python virtualenv (without system site packages) installed all exact requirements successfully; full reanalysis in fresh filesystem and numerical comparison is recorded in `artifacts/reproduction_check.json`. It is an offline computation using copied raw files, separate from online data retrieval. Final proof table generation and PDF audit also run explicitly. Details in README; installation and reproduction logs retained.

15. Extracted preliminary `submission.zip` to a new directory with no raw/processed inputs and ran the single public entry point in the fresh venv. Preflight found and repaired a directory-creation assumption in `prepare.py` before the run (it now creates data/processed and artifacts itself). Then public downloads, frozen hash verification, all numerical stages, seven tests, exact proof tables, figures, and PDF audit completed: 307.08 s wall / 292.27 CPU seconds, max child RSS 317,328 KiB. All core CSV and summary comparisons match. Final edits after extraction add only the continuous-score lattice caveat and delivery documentation; source algorithms/results remain as tested.

## Unrun / not claimed
- No real training, score-to-resource calibration, contamination attribution, future-model prediction, item-level confidence intervals, measurement-noise or score-rounding perturbation study.
- No general polynomial-time complexity claim for Borda covering.
- No optimized continuous Borda/even-median magnitude, no unique-first universal nonordering theorem.
- No complete novelty assessment under forbidden-source restriction; no claim of conference acceptance.
- No independent license grant inferred for source scores or cached papers.

## Remaining interpretation risks
Simple theoretical tools and counterfactual assumptions may limit selective-venue contribution strength. Fixed public cohorts contain correlated submissions. Bootstrap intervals have no population-coverage claim. Those are retained as scientific boundaries, not erased by successful reproduction.
