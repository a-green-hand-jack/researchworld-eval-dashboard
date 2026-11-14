# Final-review additions (implementation and running gates)

These additions answer experiment-repo#3--8 and extend the analysis commitment;
all delivered paths remain under analysis/. No new result is declared by this
protocol. Original full-study clean reproduction is an independent gate, now passed
with its own16-file report (see REPRODUCTION.md).

- Matched frames: 100 OLLB random79-model censuses and fixed top79; 100 HELM
  six-subject subsets, all79 models retained. All eight primary rules/requirements,
  ceil and gain10; all targets except a unique mean leader in each draw. A tied
  mean lead excludes nobody. Seed31. Record per-draw median K/L1, feasibility,
  min-minus-mean feasibility difference, average rival-min-minus-rival-mean
  threshold difference, task correlations and selected names/tasks/matrix hashes.
  Matching one dimension at a time does not identify a causal effect of the
  remaining differences; distributions are finite-frame sensitivities.
- Policy controls: five score rules, all feasible mean-nonleading targets on
  HELM, full OLLB and top500, ceil/gain10. Raise to caps in lowest-original-score
  or largest-headroom order; also show L1 after refining the final greedy step
  by bisection. This avoids attributing full-step waste to targeting skill.
  Compare200 random orders (seed7) and clipped uniform lift at optimal Linf.
  Bootstrap per-target ratios in both directions, R1000/seed23; 0/0=1 with
  zero-cost counts explicit. Random-policy target values are medians over its
  200 orders, then targets are resampled, a conditional descriptive procedure.
- Units and caps: K/n and L1/n are exact scalar normalizations of existing optima.
  SD uses across-all-model task population SD (ddof0) within each fixed frame.
  Separately optimize sum(delta_t/SD_t) and max(delta_t/SD_t), keeping the
  original ranking rule and score margin. Do not divide an old scalar optimum
  by an average SD: heterogeneous task costs can change its minimizer.
  These units remain frame-specific, not frame-free or training-cost estimates.
  New descriptive gain caps add each task's across-model IQR (linear Q.75-Q.25)
  to each target coordinate and clip100, in both benchmarks. They estimate no
  achievable training gain. All existing primary caps are retained; matched
  top500 gain5/gain20 are additionally solved, giving side-by-side reachability.
- Headline ranges: R1000/seed23 paired draws within each frame/cap for marginal
  all-target medians and feasible fractions, plus separate feasible-panel draws
  for conditional medians; both inverse-CDF and conventional midpoint medians.
  Wilson95% bands are binomial reference bands, not uncertainty of an observed
  census. Report all comparative L1 shares with the direction explicit (other
  rule cheaper than mean), including the joint all-comparator share.
- Data choices: frozen parquet checksum verified before making lowest-Average
  deduplicated rows. Main already excludes every flagged model; compare adding
  the single flagged row, lowest-Average deduplication, and full main targets
  facing only nonmerged/unflagged rivals. Retain existing no-merge/raw-scale
  results and compare rule orderings using denominators and both all-target and
  feasible-only cost medians. The restricted-rival comparison is a sufficient
  requirement to beat all eligible rivals, not an exact election against a
  single externally identified “best” model under every rule.

Existing12 solver tests plus new independent weighted LP/convex/exhaustive
oracles passed14 tests. Pilots: matched3744 rows125.85wall sec; policies252rows
2.50sec; population600rows2.12sec; SD/cap three-target pilot58.86wall/28.45CPU
sec; R20 marginal-bootstrap pilot10.60wall/5.13CPU sec. These size full runs;
extrapolations are planning estimates, not measured full runtime. Full runs are
tracked resource jobs with per-command CPU/wall records and progress checkpoints.

`clean_final_reproduce.py CANONICAL CLEAN_EXPORT STAGE` recomputes each addition
from an isolated code/data export with empty derived outputs, copies only named
frozen main tables where they are inputs, measures CPU/wall time, and compares
keyed output/diagnostic rows with atol1e-5/rtol0 preserving infinity/NaN. A clean
run overtaking its canonical run leaves comparison pending; --compare-only later
uses the already-computed records. No failed or pending check is a passed gate.

The final-frame checker independently reconstructs seed31 selections, matrices,
unique-mean-leader exclusions, task correlations and rival-theory diagnostics;
the final-scale checker reconstructs task SD/IQR and checks gain5/10/20 cost
monotonicity. Summary checkers independently recalculate each group's points,
quantiles and denominators. These are validity checks in addition to isolated
clean replication of the same numerical implementation.

Expanded max-SD checks also passed all14 tests in35.13 test seconds
(36.65 elapsed/35.47 child CPU seconds measured by run_measured.py).
They exhaustively compare ordinal weighted Linf with all small finite-domain
interventions and check score-rule Linf feasibility and its left boundary.
See results/final_sd_expanded_tests_runtime.json and its log.

The existing `results/summary/main_descriptive.csv` column `normalized_median`
is `median/n_tasks` for K and L1 (n_tasks=57 on HELM,6 on OLLB), and the unchanged
score-point median for Linf. It retains all nonmissing target costs including
infinity when its group is `all_nonleader`; it is neither a finite-only median
nor an SD transformation. On a fixed frame, median(K/n)=median(K)/n and likewise
for L1, under either declared median convention. New explicit `K_fraction` and
`L1_per_task` columns remove that overloaded name. SD objectives instead weight
each task before optimization and need not share an original raw-cost optimizer.
