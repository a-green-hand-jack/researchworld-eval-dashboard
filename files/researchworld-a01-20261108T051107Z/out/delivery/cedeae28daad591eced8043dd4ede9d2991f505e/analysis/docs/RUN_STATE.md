# Analysis delivery state (2026-11-08)

All declared scientific analyses are complete and validated. The original
16-file independent clean recomputation has passed, including all457,772 rows.
The analysis commitment is complete; independent report/release review belongs
to its owner.

## Completed evidence

- Seven main/sensitivity files:283,772 rows, including HELM79 x57,
  full OLLB4496 x6 and the complete matched top500 ordinal frame16,000 rows.
  `results/validation.json` passes strict completeness and numerical invariants.
  The HELM release EM is the57-subject macro mean, verified for all79 models
  (`helm_aggregate_audit.json`); micro averaging remains a sensitivity.
- Both100-draw task/bootstrap/noise panels, correlated-noise panels, HELM
  task-count subsets and both200-order controls:174,000 rows, strict
  `robustness_validation.json`. Paired same-draw contrasts retain every
  feasibility class. Broad six-task mixture sensitivity qualifies rule ordering.
- Independent-review additions:24 actual-OLLB Borda full-constraint MILP checks,
  DP applicability audit (0 fallback-required out of4948 L1/K instances),
  400 epsilon rows,5040 rival-frame rows and306 R1000 paired census-target
  contrasts. `review_checks_validation.json` passes. Separate clean panel and
  bootstrap records have zero numerical differences.
- All final-review additions: all-feasible-target policies, headline ranges and
  both median conventions, OLLB processing choices,250848 matched-frame costs/
  201 diagnostics,234744 cost-unit/cap records, and their numerical summaries.
  Each has strict checks and zero-difference separate clean regeneration.
  `FINAL_EXTENSION_FINDINGS.md` maps files, findings, limitations and CPU/wall
  measurements. The independent reviewer reproduced selected new counts,
  fixed-top79 results, SD medians and all200 HELM6 draw-rule pairs
  (experiment-repo#3). These additions do not substitute for the original gate.
- All14 optimizer/oracle tests pass, including with the optional1200s MILP
  effort limit. The explicit-zero-gap trimmed-mean check reproduces the
  supplementary500-row panel byte for byte (`trimmed_zero_gap_validation.json`).

`FINDINGS.md`, `REVIEW_FINDINGS.md` and `FINAL_EXTENSION_FINDINGS.md` are numerical
handoffs. The report and figure owners integrate/render them in the delivery
root. No time-limit status is treated as proven infeasibility.

## Completed original clean gate

Tracked job-5668d00634 exited0. `results/clean_reproduction.json` records all16
files passing every key/label/numeric-column comparison, with matching infinity/
NaN statuses, at absolute1e-5 and relative0 tolerance. The maximum finite
absolute difference is5.8068962971447036e-9; all nine robustness/control files
(174000 rows) have zero difference. This is a tolerance pass, not a blanket
zero-difference claim. Seven main/sensitivity files contribute283772 rows.

The same initially empty export was resumed after the preserved120s Condorcet
proof timeout, retaining only its own fresh checkpoints and using1200s on
continuation. No canonical cost files were imported. The failed stage remains
part of the measured runtime history. `clean_reproduction_artifacts.json`
binds the report to both CSV/metadata hash sets and rechecks every comparison,
clean invariant-check completeness, pinned code and processed-input hashes.
`logs/clean_completed/` preserves successful stage and suite logs.

| completed or failed stage | wall seconds | child CPU seconds | return code |
|---|---:|---:|---:|
| validate and12 original solver tests |37.48|36.40|0|
| first main attempt,120s proof timeout |11442.95|9398.90|2|
| resumed main,1200s proof limit |1596.48|1460.48|0|
| robustness, controls and original tables |1681.49|1437.28|0|

These stage measurements include failed work and exclude idle gaps between
stages; their sums are in the artifact audit. Later14-test and explicit-zero-gap
checks, reviewer panels and final-review additions have their own completed
records. This original export is pinned to its recorded sources; it is not a
single uninterrupted rerun of every later extension. `REPRODUCTION.md` gives
commands for current code and explains those separate gates.

## Preserved failures and corrections

The first matched OLLB Borda run timed out; the certified integer-credit DP
with full-rival witness check and independent-MILP oracle repaired that route.
Some original checkpoint jobs were lost across world restoration; partial and
superseded results are explicitly archived. Restored wall-clock times include
suspension and must not be described as CPU times. Two early clean launches
failed before scientific computation because GNU make was missing. The first
package install hit a TLS trust-path error; GNU make4.4.1 was then installed
with verification using the image CA bundle. See setup/failure ledgers.

The final cost-scale rank-metadata reduction-roundoff defect was repaired in
canonical/clean raw files without changing any optimized cost or other non-rank
field text. Hashes, repair code, superseded tables and the earlier limited
checker record are retained. Current summaries use78/4495/499 nonleaders and
strictly check legacy denominators. Duplicate selection by highest Average is
not coordinatewise dominance:74/79 repeated names have a lower task coordinate
than their lowest-Average variant (`duplicate_selection_audit.json`). No general
monotone-cost claim follows from that processing convention.

The four-CPU-hour figure in resources.md was an unmeasured planning estimate.
Actual extension runtimes and the completed original clean-stage timings are
supplied. No pending requirement is represented by a pilot or a measured null.

Earlier selected-file audits explicitly remain partial historical records;
the completed16-file report above supersedes their pending-gate statements.
