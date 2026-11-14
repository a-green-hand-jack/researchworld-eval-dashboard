# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: Selected cross-fitted recalibrated PPI mean intervals (isotonic/binned g(Yhat), shrinkage, efficiency-bound theory) vs classical/PPI/PPI++/stratified PPI. gate=kept; trigger=none; reason=first cycle with no executed evidence.
  - evidence: Alternatives considered: active allocation (violates fixed labels), DML with X (changes information set), bootstrap-only small-n fixes (modest gain).
- unknown_ts | step=implement | scope=unknown_scope
  - summary: program_1 cloned from program_0; src/program.py adds cross-fitted isotonic/binned recalibrated PPI mean CI with PPI++ fallback selection (1% margin), baselines, and src/harness.py with wilson/bootstrap/synthetic harness; untested
  - evidence: (missing evidence)
- 2026-11-11T10:41:08.974705+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.027080121099549548, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.027080121099549548, "controls_passed": 1.0, "correct": true, "coverage_min_family": 0.9333333333333333, "coverage_pooled": 0.9433333333333334, "log_ratio_vs_classical_mean": 0.49413320035056846, "log_ratio_vs_ppi_family_alphafold": 0.010428103934328083, "log_ratio_vs_ppi_family_forest": 0.016791531451063855, "log_ratio_vs_ppi_family_galaxies": 0.0035018565908873267, "log_ratio_vs_ppi_family_gene_expression": 0.028990259989334164, "log_ratio_vs_ppi_family_synthetic": 0.07568885353213431, "log_ratio_vs_ppi_lambda1_mean": 0.05393618082192103, "n_failed_episodes": 0}
- 2026-11-11T10:42:25Z | step=idea | scope=idea
  - summary: Selected label-free spline-basis control-variate PPI with PRESS selection and LOO-residual SE. gate=updated; trigger=b; reason=new category after cycle1 evaluation.
  - evidence: idea_bundle.json + target_rubrics.json; cycle1 metrics score 0.027, coverage pooled 0.943
- unknown_ts | step=implement | scope=unknown_scope
  - summary: program_1 implemented: label-free hinge basis + vector-lambda PPI + PRESS selection + LOO-residual SE with t(n-1-p); PPI++ fallback; harness with ablations. Files: src/program.py, src/harness.py. Untested.
  - evidence: (missing evidence)
- 2026-11-11T10:57:48.846372+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.004641570343273279, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.004641570343273279, "controls_passed": 1.0, "correct": true, "coverage_min_family": 0.9333333333333333, "coverage_pooled": 0.95, "log_ratio_vs_classical_mean": 0.47169464959429214, "log_ratio_vs_ppi_family_alphafold": 0.004872193619134172, "log_ratio_vs_ppi_family_forest": 0.0024126203314315487, "log_ratio_vs_ppi_family_galaxies": 0.0014330156547436338, "log_ratio_vs_ppi_family_gene_expression": 0.011109273479074356, "log_ratio_vs_ppi_family_synthetic": 0.0033807486319826856, "log_ratio_vs_ppi_lambda1_mean": 0.031497630065644766, "n_failed_episodes": 0}
- 2026-11-11T11:10:00Z | step=idea | scope=idea
  - summary: Selected repeated cross-fitted NNLS-stacked calibration PPI with split-dispersion variance and PPI++ fallback. gate=updated; trigger=a; reason=cycle2 evaluation contradicts the label-free-basis lead.
  - evidence: idea_bundle.json + target_rubrics.json; cycle2 score 0.0046 < incumbent 0.0271; synthetic gain 0.003 (basis) vs 0.076 (isotonic)
- 2026-11-11T11:30:00Z | step=implement | scope=attempt
  - summary: program_1 implemented from incumbent: NNLS-stacked calibrator library (isotonic, bins 3/5/8, local-linear kernels, linear), repeated cross-fit R=5 with [Yhat,g] control variates, averaged-residual variance + split dispersion, t df n-3, PPI++ 1% fallback; harness run_ablation added. Files: src/program.py, src/harness.py. Untested.
  - evidence: (missing evidence)
- 2026-11-11T11:16:41.889562+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.022255735814912924, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.022255735814912924, "controls_passed": 1.0, "correct": true, "coverage_min_family": 0.9166666666666666, "coverage_pooled": 0.9433333333333334, "log_ratio_vs_classical_mean": 0.4893088150659318, "log_ratio_vs_ppi_family_alphafold": 0.0037823141071903696, "log_ratio_vs_ppi_family_forest": 0.005425940895992022, "log_ratio_vs_ppi_family_galaxies": 0.0035630075950539167, "log_ratio_vs_ppi_family_gene_expression": 0.02776956644462489, "log_ratio_vs_ppi_family_synthetic": 0.07073785003170342, "log_ratio_vs_ppi_lambda1_mean": 0.049111795537284446, "n_failed_episodes": 0}
