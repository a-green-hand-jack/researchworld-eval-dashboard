# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: Budgeted repeat-run SHAP reliability study vs exact/high-budget reference, compared with background-resampling and retraining noise, plus within-run SE self-diagnostic. gate=kept; trigger=none; reason=no experimental evidence yet.
  - evidence: Cycle 1; no prior history; alternatives considered: pure seed-variance sweep, background-size study, estimator comparison.
- unknown_ts | step=unknown_step | scope=unknown_scope
  - summary: (missing summary)
  - evidence: (missing evidence)
- 2026-11-11T07:57:40.239972+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.9759702994791667, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.9759702994791667, "control_permuted_score": 0.9588846497395833, "correct": true, "mean_label_high_budget": 0.9580729166666667, "mean_label_low_budget": 0.8397395833333333, "skill_vs_always_reliable": 0.01142147135416666, "skill_vs_constant_half": 0.16032772135416667, "skill_vs_gap_heuristic": 0.0021711608071219683, "spearman_r_hat_vs_label": 0.5377285154757133}
- 2026-11-11T08:10:00+00:00 | step=idea | scope=idea
  - summary: Variance-reduced jackknife rerun simulator + offline calibration map from local replica simulator; ablations to isolate cycle-1 regression. gate=kept; trigger=none; reason=regression cause unknown.
  - evidence: cycle1 program_1 0.97597 < incumbent 0.98296
- unknown_ts | step=implement | scope=unknown_scope
  - summary: program_1 implemented: CRN 1000-draw antithetic jackknife sim (diag+full cov), hand-set _CALIB_COEF (not fitted; no code execution allowed), shrinkage 0.7, fallback 0.9. Files: program_1/src/program.py, NOTES.md.
  - evidence: (missing evidence)
- 2026-11-11T08:01:33.916788+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.983676205688752, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.983676205688752, "control_permuted_score": 0.9671057302616688, "correct": true, "mean_label_high_budget": 0.9580729166666667, "mean_label_low_budget": 0.8397395833333333, "skill_vs_always_reliable": 0.019127377563752074, "skill_vs_constant_half": 0.1680336275637521, "skill_vs_gap_heuristic": 0.009877067016707382, "spearman_r_hat_vs_label": 0.5429234168224505}
- unknown_ts | step=idea | scope=idea
  - summary: Budget-aware empirical-Bayes shrinkage + partition-ensembled jackknife + margin gate; gate=kept; trigger=none; reason=small cycle-2 gain, no new category confirmed
  - evidence: cycle2 score 0.98368 vs baseline ~0.9830; label means 0.84 low/0.96 high budget
- unknown_ts | step=implement | scope=unknown_scope
  - summary: 4-partition jackknife ensemble, budget-prior empirical-Bayes shrinkage (W_SIM=0.6), soft margin gate; files: program_1/src/program.py, NOTES.md; not executed
  - evidence: (missing evidence)
- 2026-11-11T08:04:41.261765+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.9854305898115931, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.9854305898115931, "control_permuted_score": 0.9752712898587708, "correct": true, "mean_label_high_budget": 0.9580729166666667, "mean_label_low_budget": 0.8397395833333333, "skill_vs_always_reliable": 0.020881761686593198, "skill_vs_constant_half": 0.16978801168659322, "skill_vs_gap_heuristic": 0.011631451139548504, "spearman_r_hat_vs_label": 0.5469261339936233}
