# Dated analysis amendment — 2026-11-02 (after independent self-review)

## Reason and chronology
The network/design/mechanism/seed/repetition plan was fixed before main execution. The first analysis used within-valid-stratum variances and treated observed valid-count weights as fixed. Self-review F1 showed this understates repeat-Monte-Carlo uncertainty for the stated success-conditioned mixture when graph strata have different acceptance rates/means. This is an analysis correction, not a new experiment or outcome-dependent model selection. The pre-main protocol is preserved, with an explicit amendment pointer. Earlier results_audit.md documents the first analysis; final summary CSVs and this amendment are authoritative.

## Estimand and corrected formula
Graph seeds are fixed strata j with R_j attempted assignments, equal attempts for the three synthetic graphs. For metric H (error, squared error, conditional bias, accounting gap, or paired squared-error difference), V indicates a valid result (or joint validity for a pair). The pooled estimator is theta_hat=sum(V H)/sum(V), targeting the equal-attempt fixed-graph mixture conditional on validity. The graph mixture is therefore weighted by graph-specific success probabilities, not equal weights after failures.

Use U_jr=V_jr*(H_jr-theta_hat), zero for invalid attempts. The local delta/ratio variance estimator is

SE² = sum_j [R_j * sample_variance_r(U_jr)] / N_valid².

All attempted records enter, preserving random accepted counts. In all-valid cells this reduces to the ordinary fixed-stratum mean variance and leaves headline regression results unchanged to numerical precision. MSE uses H=error²; RMSE applies the delta transform SE_MSE/(2 RMSE). Paired loss comparisons use all attempted assignment keys and V=both methods valid. Decomposition uses H=error²-b²-v. Per-seed analysis is the one-stratum case. Fewer than two successes yields unavailable MCSE, never zero precision. Fewer than 30 successes is labeled `sparse_valid_local_delta_only`; all-zero estimates are labeled `all_zero_estimates_unseen_tails_not_certified`. These asymptotic diagnostics do not discover unobserved HT tails or justify precision from tiny accepted samples.

Wilson coverage/availability intervals are retained as declared approximations, with per-seed denominators available. No familywise significance or universal ranking claims follow.

## Implementation / regression tests
- `audit_stats.ratio_mcse` implements the attempted-record formula.
- `test_reporting.py` verifies the all-valid reduction, nonzero uncertainty from random success weights even with constant within-valid-stratum metrics, and unavailable precision with only one success.
- `validate_results.validate_frame` asserts exact config-derived assignment keys/replicates, complete 10×7 method/mechanism coverage, unique keys, allowed statuses, finite successes, nonnegative variance and missing failures. Unit fixtures test truncated row, missing assignment and unknown status rejection. Fixtures are unit tests, not empirical study outputs.
- `analyze.py` regenerates all summary tables/macros and paired comparisons from unchanged raw runs.
- Appendix heatmap marks incomplete cells with valid/attempted counts; risks are method-conditional, not common-subset comparisons.

## Remaining caveats
The correction addresses acceptance weighting, not rare-tail under-sampling, graph-population uncertainty, covariance estimation, unknown endpoint bias or rights clearance. No simulation rerun is required; all 24,000 archived assignments and all raw estimates remain unchanged.
