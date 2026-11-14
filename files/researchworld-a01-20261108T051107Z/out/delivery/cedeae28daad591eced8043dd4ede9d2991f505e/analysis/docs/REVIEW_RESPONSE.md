# Analysis response to the independent audit

The review owner reported independent checks in internal-review-repo issue3,
against experiment-repo7e2995b: 1,185 HELM score-rule cases, all79 plurality targets
at two caps, independent full-constraint Borda/Condorcet MILPs on six random
cases per rule/cap, and ordinal Linf checks. It reported zero mismatches and no
code/theory defect. These are the reviewer's reported measurements, not new
runs by this position; they are not release approval.

1. **Condorcet interpretation.** Keep the sufficient requirement separate from
   complete ranking rules. Its cost bounds from above the cost of making a
   target first under a particular Condorcet-consistent rule; it is not that
   rule's exact cost. Protocol and figure/report handoffs explicitly require
   this label. No claim of a cheaper complete rule is drawn from comparing its
   K29 to Borda's K46 on HELM.
2. **Paired frame-level ranges.** `src/bootstrap_paired_targets.py` resamples
   paired targets together for feasible-fraction and lower-cost fractions, and
   resamples the conditional finite paired panel for the median difference.
   R1000, seed23. These are descriptive resampling ranges of selected, often
   related model censuses, not calibrated iid-model population CIs. Existing
   `paired_vs_mean.csv` already gives both/only-one-feasible counts.
3. **Competitor frames.** `src/run_frame_sensitivity.py` keeps original-mean
   positions2–11 fixed, includes the original frame, removes the original mean
   leader for every rule, or retains a common random half of the original
   models and forcibly includes the target. Ten half-frames, seed11, ceil and
   gain10, all primary rules in their declared frames. Per-target rival counts
   and frame hashes are recorded. A measured 378-row pilot took4.49seconds;
   the full design has5,040 rows (an initial job note's4,620 omitted the original
   frame; that was a sizing estimate, not a result). Costs for score rules
   cannot rise on removal of rivals at these fixed caps; this is checked.
4. **Caps and conditional costs.** Capped feasible fractions are primary.
   Finite-only costs condition on rule-specific sets and do not demonstrate
   unconditional superiority. Ceiling100 is an idealized score-space scenario,
   not evidence of realistic achievable training gains.
5. **Epsilon and infima.** `src/run_epsilon_sensitivity.py` runs0.001 and0.1
   on the same original-mean positions2–21 for mean and Borda, at ceil/gain10
   in HELM and matched top500; full OLLB mean is also included. The finite
   ordinal convention yields an upper bound on the arbitrary-real strict-win
   infimum and can omit real interventions near caps. Score-rule optima are
   exact for their declared closed margin constraint. The epsilon experiment
   does not establish independence of that convention.
6. **Actual OLLB DP validation.** `src/audit_ollb_borda.py` re-executes the
   deterministic single-rival DP/full-witness check for every declared main
   Borda target/cap/objective. It records accepted, proved-infeasible,
   fallback-required and initial-winner counts, explicitly as an audit rather
   than retroactive original-run telemetry. It separately constructs full
   rival-constraint MILPs (no DP or lazy constraints) at OLLB original-mean
   ranks2,5,10,20,50,100, two caps, two objectives. Non-optimal solver statuses
   are not accepted as agreement or infeasibility.
7. **Reproduction and runtime.** The full declared primary/sensitivity/control
   study was recomputed from an isolated export initially without derived outputs;
   exact commands, measured child CPU/wall time, numeric agreement and failed
   setup attempts are recorded separately. Restored clocks are not CPU-time
   measurements. Additional review checks have reproduction commands and
   their own passing validation/clean records.

The matched top500 main is complete and the seven-file full main checker
passes283,772 rows. R1000 paired-target ranges are complete,306 contrasts;
`review_checks_validation.json` passes every required canonical/paired check.
`REVIEW_FINDINGS.md` gives the measured paired feasibility reversals.
Clean review frame/epsilon/audit reproduction passed5,464 rows with zero numeric
difference and identical DP counts, with per-command CPU and elapsed times.
The clean target-bootstrap comparison passed all306 contrasts with zero
differences. The separate original16-file clean reproduction subsequently passed all457772
rows; see clean_reproduction.json and REPRODUCTION.md.

## Focused independent re-check and quantile convention

The reviewer reports a focused re-check on paper-repo main4f06127 in
internal-review-repo issue3 (recorded in its main4b98117): its own top500 plurality
implementation and sampled full-constraint Borda MILPs found zero mismatches;
its own R2000 target bootstrap agreed with selected paired feasibility ranges
and finite-pair medians to sampling noise. It accepted the resampling
interpretation and the finite-convention upper-bound qualification. It did not
rerun the epsilon/frame panels, DP applicability counts or clean full study.
These are reviewer-reported checks with that scope, not release approval.

Its remaining convention objection is resolved by retaining, and explicitly
documenting in `PROTOCOL.md`, the existing inverse empirical-CDF quantiles
(`method="inverted_cdf"`). For even target counts the reported median is the
lower middle observation, distinct from midpoint medians and from the median
*aggregation rule* over tasks. `FINDINGS.md` already stated this convention;
the protocol now states the exact order-statistic definition and its scope.
No solver, raw result, summary value or bootstrap draw has changed. The paper
and figure/table owners are asked to make the convention visible alongside the
relevant statistics and label any different presentation-statistic convention.

## Final methods-domain check

Paper request28 is resolved at checked paper main5eb9eb5: the manuscript now
states the effective max cap and exact ordinal candidate domain, and limits
the rival-sensitivity comparison to Borda K on the HELM near-top panel. Its
Section5 and main-table caption also state the descriptive quantile convention.

A separate check found that the methods sentence incorrectly grouped continuous
trimmed means with finite ordinal optimization; paper request33 asks its owner
to separate them. `PROTOCOL.md` and `THEORY.md` now spell out the continuous
trimmed L1 sorting-assignment MILP, continuous Linf bisection and absent K.
The supplementary MILP also lacked an explicit zero requested relative gap.
That option is now0.0; fresh validation passed8 existing score-rule/oracle tests
and regenerated all500 supplementary rows (100 trimmed) byte-identically to the
canonical CSV, in18.93wall/18.05CPU seconds. See
`results/trimmed_zero_gap_validation.json` and `results/solver_checks/`.
This correction has measured equivalence; the separate original clean export
subsequently passed, with its own pinned source and recorded comparison.

## Final-review extensions

All five requested addition groups are accepted; definitions and estimands are
in FINAL_EXTENSION_PROTOCOL.md. Headline ranges/both median conventions, OLLB
processing/rival variants, and all-target greedy/random/uniform controls are
now validated and cleanly regenerated; FINAL_EXTENSION_FINDINGS.md records the
negative greedy-K result and the raw-scale ordering reversal. Matched-frame
and standardized-objective/IQR-cap runs and clean replicas have also passed.
The separate original16-file clean reproduction requirement is now passed.

The independent reviewer spot-checked the first three final-extension groups
against main4dc485c (reported in experiment-repo issue3): its own HELM ceiling
low-score greedy K,504 headline-point checks and restricted-rival gain10 counts
agree; its R300 bootstrap endpoints are within0.026. Those are the reviewer's
reported checks, not a check of the subsequently delivered matched-frame/SD
results or a release approval.

The reviewer subsequently checked the matched-frame and SD/IQR batch at main
fd2b6ff (experiment-repo issue3): its own cap counts, fixed-top79 counts, selected
SD medians and all200 HELM6 draw-rule pairs reproduced exactly. These are the
reviewer's reported checks, not release approval. All analysis commitment gates
are now supplied; the report owner integrates this completed original clean
record before independent final-version review.
