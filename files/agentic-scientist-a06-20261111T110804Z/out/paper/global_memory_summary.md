# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: EB hierarchical logistic IRT posterior-quantile interval, searcher-agnostic; gate=kept; trigger=none; reason=first cycle
  - evidence: baseline interface docstring; incumbent -0.232 naive Wilson
- unknown_ts | step=implement | scope=unknown_scope
  - summary: (missing summary)
  - evidence: (missing evidence)
- 2026-11-11T14:18:48.100735+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=-0.1479678140153992, correct=True; scientific acceptance passed; search metrics (data): {"bonferroni_baseline_score": -0.19613290095582664, "combined_score": -0.1479678140153992, "completed_replication_fraction": 1.0, "constant_control_error": 0.0, "correct": true, "coverage": 0.915, "mean_interval_score": 0.1479678140153992, "mean_width": 0.12388584277274953, "naive_baseline_score": -0.2320671337621134, "naive_signed_bias": 0.03663575640937149, "null_control_abs_bias": 0.0158004367862136, "null_control_coverage": 0.9333333333333333, "resample_baseline_score": -0.27324378381976666, "rmse": 0.034627720109070406, "signed_bias": 0.014323250435029461}
- 2026-11-11T14:19:41.868591+00:00 | step=idea | scope=idea
  - summary: Parametric-bootstrap pivot calibration of EB-IRT interval; gate=kept; trigger=none; reason=no contradiction/new category yet
  - evidence: idea_bundle.json + target_rubrics.json
- unknown_ts | step=implement | scope=unknown_scope
  - summary: parametric-bootstrap pivot calibration with width floor, clipped bias shift, mild real-data inflation, kappa fallback; not executed locally
  - evidence: (missing evidence)
- 2026-11-11T14:22:37.952214+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=-0.15618012526390268, correct=True; scientific acceptance passed; search metrics (data): {"bonferroni_baseline_score": -0.19613290095582664, "combined_score": -0.15618012526390268, "completed_replication_fraction": 1.0, "constant_control_error": 0.0, "correct": true, "coverage": 0.77, "mean_interval_score": 0.15618012526390268, "mean_width": 0.08498630334101204, "naive_baseline_score": -0.2320671337621134, "naive_signed_bias": 0.03663575640937149, "null_control_abs_bias": 0.014874381815085994, "null_control_coverage": 0.7375, "resample_baseline_score": -0.27324378381976666, "rmse": 0.03330424395337889, "signed_bias": 0.00916662063782031}
- 2026-11-11T14:30:00+00:00 | step=idea | scope=idea
  - summary: EB-IRT with config-by-subject interaction random effects; gate=kept; trigger=none; reason=same calibration category as prior cycles
  - evidence: idea_bundle.json + target_rubrics.json
- 2026-11-11T14:45:00+00:00 | step=implement | scope=attempt
  - summary: implemented config-by-subject interaction EB fit with eta2, conditional u_d draws, _KAPPA_REAL=1.10, c01 fallback; files: program_1/src/program.py
  - evidence: (missing evidence)
- 2026-11-11T14:25:32.120913+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=-0.15187690797023273, correct=True; scientific acceptance passed; search metrics (data): {"bonferroni_baseline_score": -0.19613290095582664, "combined_score": -0.15187690797023273, "completed_replication_fraction": 1.0, "constant_control_error": 0.0, "correct": true, "coverage": 0.8925000000000001, "mean_interval_score": 0.15187690797023273, "mean_width": 0.11951537963709527, "naive_baseline_score": -0.2320671337621134, "naive_signed_bias": 0.03663575640937149, "null_control_abs_bias": 0.016713899438435622, "null_control_coverage": 0.9083333333333333, "resample_baseline_score": -0.27324378381976666, "rmse": 0.03510043946075491, "signed_bias": 0.015155074141144285}
