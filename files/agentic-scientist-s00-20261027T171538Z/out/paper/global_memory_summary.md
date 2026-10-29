# Global Memory Summary

Use as qualitative context only; do not use as quantitative grounding source.

## Recent Entries

- 2026-10-27T00:00:00Z | step=idea | scope=idea
  - summary: Positive mixture of physics scaling terms (n*H_n, m*diam/min_deg, m*diam/mean_deg, n^2, m*diam) fit with pseudo-Huber log loss plus CV log-linear residual; K-fold CV selects vs baseline ridge. gate=kept; trigger=none; reason=no execution evidence yet this cycle.
  - evidence: Incumbent ridge_log_linear_v0 combined_score=-0.1929 correct=true; single power law cannot represent regime switches between n log n, n^2, n^3 cover times.
- 2026-10-27T18:30:00Z | step=implement | scope=attempt
  - summary: program_1 ready: physmix_cv_v1 = positive mixture of 7 physics scaling terms (n*H_n, m*diam/min_deg, m*diam/mean_deg, n^2, m*diam, n*H_n*diam, m*H_n/min_deg) fit via Adam on pseudo-Huber ln-residual, plus IRLS ridge log residual (lam grid 0.3-30), 5-fold seeded order-invariant CV selecting among baseline ridge/mix/mix+res (top-2 log-average allowed), baseline fallback on any failure.
  - evidence: Not executed in this stage (no Python allowed); rubric source patterns verified by grep.
