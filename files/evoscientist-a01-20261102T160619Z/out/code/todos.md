# Frozen analysis plan (before score analysis)

> Historical plan retained for transparency, not independent preregistration. **Correction before analysis:** Open Raw scores are already fractions and must NOT be divided by 100. The original Data paragraph below has stale units; `code/prepare.py`, README, and the appendix contain the verified convention. Only normalized percentages are divided by 100.

## Scope and primary estimand
Fixed public score matrix, one target modified, competitors frozen except rank scores recomputed. Scores in [0,1]. Ceiling c=x+rho(1-x), rho=0.25,0.5,1; primary rho=0.5. Investment K = minimum number of improved task coordinates to achieve shared first. K/n primary; unique-first secondary, explicitly separate from ties. No claim that ceilings are attainable via training or that K measures dollars/tokens. Main rules: arithmetic mean, conventional median (average middle pair for even n), and per-task midrank Borda. Equal task weights, higher is better. No universal robustness ordering assumed.

Secondary: minimum normalized L1 gain for mean and odd-task median only (separate estimand, not automatically support-optimal). For all rules record endpoint witness magnitude but label it as witness cost, not minimum. Abstain from general continuous Borda L1 optimization because strict threshold crossings can have unattained infima. No training tuning applies; rho is a sensitivity parameter, not fitted.

## Data
HELM MMLU v1.13.0: exact-match 57-subject complete-case matrix, each row a displayed model configuration; inspect metadata and missingness. Open LLM contents pinned 9c09a7cae43334062a82cb164f2ef255013dafa2: six Raw task scores divided by 100; alternate official normalized task scores as a scale sensitivity. Preserve all complete valid rows; duplicate-score rows sensitivity. Reject out-of-range rather than clipping. Record masks, checksums and downloads. Equal subject macro mean is our constructed ranking, not a claim to reproduce official HELM aggregate.

## Algorithms and gates
1. Baseline: no-edit ranks and all-ceilings attainability. Independently reproduce own mean/midrank formulas. Validate manifest and exclusions.
2. Support theorem: for coordinate-monotone cardinal aggregators or Borda target-vs-rival margins, any winning support also wins at its endpoint. Mean solved by descending headroom. Odd median solved by threshold-crossing count. Six-task rules solved exhaustively over all 64 subsets. Borda 57-task support via binary MILP with all changing rival contributions. MILP bounds, objective integrality, primal witnesses checked; not describe floating point solvers as formal certificates. Exhaustive small cases cross-check.
3. Empirical cohort: all complete-case targets; report infeasible separately, paired within common nonwinner cohort and baseline rank strata. Current shared winners have K=0. No arbitrary infeasible finite penalty in main summaries. Rho monotonicity must hold.
4. Sensitivity: shared vs unique first; rho; Raw vs official scale (six tasks); model-score deduplication; alternative median convention (six tasks); leave-one-task-out for HELM on fixed preselected targets if budget allows. Uniform random coordinate ordering, headroom heuristic against exact Borda; saved seeds 17,29,43. Compare to attainable oracle rather than a learned method.

## Uncertainty
Data are fixed snapshots, not iid samples of future models. Report population summaries without pretending training variance. Three-seed target bootstrap, conditional on fixed competitor matrix, for paired differences in normalized support, with 2000 resamples per seed, 95% intervals, descriptive only; do not rebuild Borda competitors. No significance claims and no uncorrected multiple hypothesis tests. Stratify at initial own-rule rank, also provide common target cohorts to separate ranking effects.

## Evidence and fallback
Every number/plot generated from saved artifacts. If ordering changes across datasets, ceilings, metrics or rank strata, the main conclusion is conditionality. If Borda MILP is too expensive, report bounds and unresolved cases or narrow predeclared rank-stratified cohort, never fabricate optima. Bound heavy work to <=4 CPU hours; pilot first, limit workers/BLAS threads.

## Rejection risks / defenses
- Not real training: explicitly a structural counterfactual, no causal extrapolation.
- Novelty unknowable under restriction: claim a self-contained measurement and exact characterization, not first-of-kind.
- Ties/scaling: report conventions and sensitivity, use raw precision.
- Model selection/missingness: publish exclusions and compare common targets.
- Weak exactness: exhaustive oracle tests plus solver certificates and independent witnesses.

## Outputs
`code/` download, analysis, plotting and validation scripts; `data/` sources and matrices; `artifacts/` target results, summaries, tests, plots and logs; `paper/` official ICML 2026 template (latest available official ICML styles retrieved), complete paper <=8 main-text pages plus references/appendix and impact statement; root PDF/LaTeX access, README, requirements, source manifest, execution log and final report.

## Final stage updates
- [x] Source-restricted literature grounding, official ICML template and pinned data manifests.
- [x] Validated baseline, all-target support computation, magnitude formulas and exact synthetic nonordering examples.
- [x] Paired feasible-cohort controls, descriptive resampling, rank strata, tie/scale/roster/even-median sensitivities.
- [x] Bounded task diagnostic; explicit deviation: HELM deletes pairs to preserve odd parity, not the unimplemented 56-task median.
- [x] Full witness/infeasibility and numerical bound audit, tolerance sensitivity, seven support/magnitude test groups.
- [x] Full paper, proofs, generated figures/tables, impact statement, voluntary checklist, PDF/page/font audit.
- [x] Adversarial self-review and documented repairs; no claim that venue novelty or acceptance is established.
- [x] Fresh virtualenv installation, isolated offline recomputation, extracted-bundle public download and one-command reproduction, result comparison, and final code/documentation packaging (see `reproduction_check.json`, `archive_reproduction_check.json`, and `review_resolution.md`).

No training tuning applies. No score-rounding/measurement-noise experiment or real resource-cost calibration is claimed. Full task-delete generality and formal rational MILP certification remain outside scope.

