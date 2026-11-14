# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-11-11T00:00:00Z | step=idea | scope=idea
  - summary: Selected model-assisted difference estimator with D-optimal latent item selection and source-only shrinkage blend; gate=kept; trigger=none; reason=no experimental evidence yet.
  - evidence: No prior attempts; alternatives (anchors+IRT, adaptive selection) judged lower novelty or unsupported by interface.
- unknown_ts | step=unknown_step | scope=unknown_scope
  - summary: (missing summary)
  - evidence: (missing evidence)
- 2026-11-11T09:49:41.166976+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.9380925613781035, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.9380925613781035, "control_constant_mae_delta": 0.07726097736208108, "control_permuted_mae_increase": 0.10870841506379365, "control_permuted_spearman_drop": 1.0211921141944755, "correct": true, "delta_mae_vs_anchor_points": 0.0096319520996609, "delta_mae_vs_irt_style": 0.04049827197149433, "delta_mae_vs_random_mean": 0.007293950664303436, "delta_score_vs_best_baseline": 0.00839987275490861, "kendall": 0.7302692602388781, "mae": 0.02846351072129862, "mae_random_targets": 0.018045177171652875, "mae_strong_targets": 0.03888184427094436, "n_candidate_rpc_calls_observed": 88.0, "n_completed_episodes": 22.0, "n_failed_episodes": 0.0, "rmse": 0.03467138259534235, "spearman": 0.8662242883976079, "spearman_random_targets": 0.9615014631482122, "spearman_strong_targets": 0.7709471136470037}
- unknown_ts | step=idea | scope=idea
  - summary: Logistic latent model + upper-tail Fisher D-opt + NNLS stacking targeting strong_targets extrapolation; gate=kept; trigger=none; reason=no new experimental evidence this step.
  - evidence: c01 strong_targets MAE 0.0389 Spearman 0.771 vs random_targets MAE 0.0180 Spearman 0.962
- unknown_ts | step=implement | scope=unknown_scope
  - summary: program_1 = program_0 + logistic latent model, Fisher D-opt designs, NNLS stacking over source pseudo-target folds with incumbent fallback; edited program_1/src/program.py only; not executed/tested.
  - evidence: (missing evidence)
- 2026-11-11T09:56:45.297046+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.9451570370449338, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.9451570370449338, "control_constant_mae_delta": 0.07665360954547458, "control_permuted_mae_increase": 0.11042130792928442, "control_permuted_spearman_drop": 1.033348198404393, "correct": true, "delta_mae_vs_anchor_points": 0.010889158694541295, "delta_mae_vs_irt_style": 0.041755478566374724, "delta_mae_vs_random_mean": 0.00855115725918383, "delta_score_vs_best_baseline": 0.015464348421738938, "kendall": 0.7555694417372909, "mae": 0.027206304126418224, "mae_random_targets": 0.01851911680243392, "mae_strong_targets": 0.03589349145040253, "n_candidate_rpc_calls_observed": 88.0, "n_completed_episodes": 22.0, "n_failed_episodes": 0.0, "rmse": 0.03356816169564755, "spearman": 0.8894533646854086, "spearman_random_targets": 0.96292000907211, "spearman_strong_targets": 0.8159867202987072}
- 2026-11-11T10:00:00+00:00 | step=idea | scope=idea
  - summary: Posterior-mean + bagged-rank logistic ability estimator with strong-holdout tail correction in NNLS stack; gate=kept; trigger=none; reason=no new experimental evidence this step.
  - evidence: incumbent strong_targets MAE ~2x random_targets MAE
- unknown_ts | step=implement | scope=unknown_scope
  - summary: bagged logistic fits + Laplace posterior-mean + ridge-to-identity tail correction as 4th NNLS stack candidate with incumbent fallback; untested
  - evidence: (missing evidence)
- 2026-11-11T10:04:29.207983+00:00 | step=evaluate | scope=attempt
  - summary: harness evaluated program_1 exactly once
  - evidence: combined_score=0.9445415952067878, correct=True; scientific acceptance passed; search metrics (data): {"combined_score": 0.9445415952067878, "control_constant_mae_delta": 0.07665360954547458, "control_permuted_mae_increase": 0.11042130792928442, "control_permuted_spearman_drop": 1.033348198404393, "correct": true, "delta_mae_vs_anchor_points": 0.010731825297838692, "delta_mae_vs_irt_style": 0.041611419008976976, "delta_mae_vs_random_mean": 0.008407097701786083, "delta_score_vs_best_baseline": 0.014848906583592947, "kendall": 0.7521315158702038, "mae": 0.02735036368381597, "mae_random_targets": 0.018501606726149544, "mae_strong_targets": 0.036199120641482396, "n_candidate_rpc_calls_observed": 88.0, "n_completed_episodes": 22.0, "n_failed_episodes": 0.0, "rmse": 0.03394347425132193, "spearman": 0.887567835562415, "spearman_random_targets": 0.9629503004063457, "spearman_strong_targets": 0.8121853707184844}
