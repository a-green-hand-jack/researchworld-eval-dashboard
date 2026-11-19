# Status of the analysis (updated each delivery)

Last update: 2026-11-18 (second delivery of the day: d-curve on the probability scale complete for 3 models x 3 seeds, GBDT margin-scale single-seed control, Leverage SHAP T2 partial). **Tier 1 (E1–E3, E5) is complete for the 18 main cells** (German d=20 and ACS-Employment d=16 × LR/MLP/GBDT × 3 seeds, n=100 instances, R=20). Tier 2, the d-curve and the yardstick for some cells are still running; their files are marked preliminary below and nothing in them is final. Files named `pilot_*` (analysis repo only) are layout tests and must not be reported.

| stage | what | state |
|---|---|---|
| tables | exact value tables, 18 main cells; d-curve subsets d=8,12 (German, ACS) | done (main), done (d=8,12 tables) |
| E0 | re-implemented estimators vs live shap 0.51.0 | passed on German MLP d=20, German LR M=10, ACS MLP/GBDT d=16 (6 inst, R=100); also on the live Arrhythmia d=100 cell (`e0_fidelity_*.json`) |
| E1/E2/E3 | R=20 grid, all arms × 6 budgets + perm500 | **final for the 18 main cells**: `tidy_*_R20.csv`, `plugz_*_R20.npz`, `verdicts_R20.csv`, `instances_R20.csv`, `bias_variance_R20.csv` (groups also include d-curve subsets; see below) |
| E5 | certificate audit, 5 rules × 4 δ × 3 k | **final for the 18 main cells**: `certificates_<cell>.csv`, `certificate_coverage.csv`, `fixed_budget_*.csv`, `cost_at_equal_reliability.csv` (columns `comparison` = same_estimator / across_estimators; same-estimator rows first) |
| oracle tightness | certified share vs oracle 'certify iff r_k(x;B) ≥ 1−δ', R=200 subset (30 stratified instances, ×¼/×1/×4), s0 of each main cell | `oracle_tightness.csv`, `r200_subset.csv`, `r200_agreement.csv` for the 6 s0 cells; the subset is stratified by r, so shares are not population shares |
| E4 yardstick | retrain/background variants, 30 instances, s0 | ACS LR/MLP/GBDT and German LR summarised (`yardstick_summary.csv`); German MLP and GBDT running |
| d-curve | German and ACS d=8,12 (3 seeds), **complete**; GBDT margin-scale control s0 (German/ACS d=8,12; d=20/16 running); Arrhythmia d=12,16 (s0) | R=20 tidy files delivered; German d=12 MLP/GBDT s0 and logit-scale GBDT cells and Arrhythmia d=40,100,279 (live, 20 instances) running; **preliminary** |
| Tier 2 | Leverage SHAP arm (Algorithm 1 as printed), SHAP@k-style stopping inside E5 (`shapk` rule) | `shapk` final with E5; Leverage T2 running on the Tier-1 cells (not delivered yet) |
| E7 | chance baseline and global-importance control from the R=20 grids | `e7_controls.csv` (final for the 18 main cells) |

Not run: see `cells_not_run.csv`. Nothing has been cut from the agreed grid so far.
