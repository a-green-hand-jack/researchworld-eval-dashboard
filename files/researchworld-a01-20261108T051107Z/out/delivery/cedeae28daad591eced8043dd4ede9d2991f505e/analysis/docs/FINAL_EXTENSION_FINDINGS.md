# Checked numerical handoff for the final-review additions

All five final-review addition groups below are complete, checked and cleanly
regenerated. The separate original16-file clean reproduction has also passed after the
preserved solver-timeout continuation; see REPRODUCTION.md and its full report. Definitions are in
`FINAL_EXTENSION_PROTOCOL.md`; paper and figure owners choose the final wording
and rendering.

## Marginal headline ranges and median conventions (request7)

`results/final_headline_intervals.csv` has84 rows: K/L1 for all21 frame/rule
combinations, at ceil/gain10. It supplies n, n_feasible, observed feasible fraction,
R1000/seed23 target-resampling endpoints, Wilson95% reference endpoints,
all-target and conditional feasible-panel medians with both inverse-CDF and
midpoint conventions, their separate resampling endpoints, and quartiles.
Whole-panel bootstrap draws are shared across rules within each frame/cap;
finite-only median ranges resample that rule's conditional feasible panel.
Infinity remains in whole-panel medians. Wilson bands are a binomial-model
reference, not uncertainty about the observed census. None is a population CI.

Examples (point [2.5%,97.5%] descriptive target-resampling range):

- Gain10 mean feasible fraction: HELM29/78=0.371795 [0.256410,0.487179];
  full OLLB113/4495=0.025139 [0.020467,0.030033]; matched top500113/499=0.226453
  [0.190381,0.264529]. Their Wilson endpoints are separate CSV columns.
- HELM ceil minimum K: inverse-CDF median11; conventional midpoint11.5;
  both ranges [9,15]. L1: inverse97.507205 versus midpoint98.114650; respective
  ranges [55.815515,145.118529] and [57.831029,149.436348]. Changing the display
  median changes no target's optimization problem or cost.
- `final_headline_shares.csv` has78 comparative share rows, with the direction
  explicitly **other comparator cheaper than mean**. At ceil, Borda L1 is
  cheaper for77/78 HELM targets=0.987179 [0.961538,1.0]; the joint share for which
  every comparator is cheaper is also77/78. Full OLLB's joint share is0.999333
  [0.998443,1.0], matched top500's0.993988 [0.985972,1.0]. “Comparators” includes
  the separately labelled Condorcet requirement where present, not a new ranking
  rule. The file also gives each complete rule's share separately.
- Paired minimum-minus-mean feasibility contrasts and their R1000/seed23 ranges
  already exist in `results/paired_target_bootstrap.csv` (K row, each frame/cap).
  These remain the canonical paired intervals; the new marginal endpoints must
  not be subtracted to manufacture a paired interval.

Validation: `final_census_validation.json` checks all canonical points and both
median conventions. `clean_final_census.json` independently regenerates all84
interval rows,78 share rows and60 existing-processing-summary rows from explicitly
named frozen main inputs, with zero numeric difference (byte-identical CSVs).
Fresh canonical runtime24.83wall/9.14CPU seconds; clean12.62wall/9.04CPU seconds.

## OLLB processing and rival-eligibility choices (request8)

`final_population.csv` has134,860 new target/cap/rule records under normalized
scores: lowest-Average deduplication; including the flagged row; and the full
main target set facing only nonmerged/unflagged rivals. `final_population_summary.csv`
and `final_population_orderings.csv` combine these with the existing full,
no-merge and raw-scale runs:120 rows each, reporting both all-target and
feasible-only medians and explicit feasibility denominators. Cost-rank ties
include infinity; finite-only ranks are conditional on different target sets.

At gain10, feasible counts ordered by rule are:

| frame/choice | mean | geometric | harmonic | median | minimum | denominator |
|---|---:|---:|---:|---:|---:|---:|
| normalized main |113|142|264|203|446|4495|
| raw task scores |296|382|459|21|224|4495|
| no merges (normalized) |81|106|196|150|389|3788|
| lowest-Average dedup (normalized) |111|142|259|201|444|4495|
| flagged row included (normalized) |113|142|264|203|446|4496|
| eligible rivals, full main targets (normalized) |113|142|264|203|520|4495|

Thus the normalized main feasibility ordering survives the lowest-Average and
no-merge choices, while **raw scale changes it**: harmonic is most reachable,
followed by geometric, mean, minimum and median. A +10 raw-score-point cap is a
different intervention scale from +10 normalized points; this is sensitivity
to the chosen score units, not a causal comparison of training gains. At ceil,
the L1 ordering stays minimum < median < harmonic < geometric < mean in these
six choices; all K/L1 ordering ranks and ties are supplied in the CSV.

The frozen parquet has one Flagged row, `newsbang/Homer-v0.5-Qwen2.5-7B`; the
main already excludes it. Adding it changes no common target's costs or
feasibility for these five rules/caps, but adds one denominator observation, so
marginal medians/fractions can shift. Restricting rivals to nonmerged/unflagged
rows keeps the full4495 mean-nonleading targets: 74 previously infeasible minimum
cases become feasible at gain10. Every restricted-rival score cost is <= its
full-rival cost, as checked. Metadata flags are taken as supplied, not independently
verified claims about a model's training history.

For each score rule, beating all eligible rivals is equivalent to beating its
best eligible rival's fixed aggregate (excluding the target itself). The eligible
leaders are Calme (`MaziyarPanahi/calme-3.2-instruct-78b`) for mean/geometric/harmonic,
`ehristoforu/qwen2.5-test-32b-it` for median, and
`OpenBuddy/openbuddy-llama3.3-70b-v24.1-131k` for minimum. These are per-rule
leaders, not a single rule-independent “best model”.

Validation: `final_population_validation.json` passes completeness, common-target
comparisons and rival monotonicity. `clean_final_population.json` re-executes all
134,860 costs and3 frame diagnostics with zero difference; canonical218.58wall/
137.30CPU seconds, clean217.39wall/137.92CPU seconds. The two compact120-row tables
were separately regenerated cleanly in4.82wall/4.47CPU seconds with zero difference
(`clean_final_population-summary.json`). The raw/no-merge rows remain the already
measured original-study results; this addition does not relabel their original
run as a new measurement.

## All-feasible-target score-policy controls (request5)

`final_controls.csv` contains110,876 policy records for all feasible
mean-nonleading targets, five score rules, ceil/gain10, HELM/full OLLB/top500.
Every target has lowest-score-first, largest-headroom-first, random-order
median (200 orders, seed7), and uniform-clipped policies; greedy L1 is also
reported after minimizing only its final task lift. Raw costs, separately
optimized K/L1, random-order percentiles and zero-cost cases are explicit.
`final_controls_summary.csv` has300 ratio rows: policy/optimum and its reverse,
median/quartiles, R1000/seed23 bootstrap endpoints, n_feasible, n_zero_opt,
n_positive_opt and the fraction exactly matching the optimum. Sorted target
draws are shared across all policies and metrics within each frame/cap/rule.
These are conditional feasible-census sensitivities, not population CIs.

A material negative finding: at ceil, lowest-score-first matches optimal K for
**every tested target, in all five score rules and all three frames** (15 panels,
78/4495/499 targets per rule). At both caps, lowest-score-first matches minimum's
optimal K and highest-headroom-first matches mean's optimal K. Thus superiority
over random orders does not demonstrate a K advantage over these simple greedy
policies. This is a statement about the evaluated frames/policies, not a claim
that every greedy policy solves every rule/box.

For HELM ceil, median random-order/optimal K ratios [target-resampling endpoints]
are mean1.764706 [1.666667,1.923077], median1.136364 [1.080000,1.210526], and
minimum4.230769 [3.437500,6.000000], each over all78 targets. All corresponding
lowest-score-first K ratios and endpoints are1.0. These census results have a
different target set from the old20-target near-top controls; a13--15x near-top
factor must not be promoted to an all-target or greedy-baseline claim.

L1 can still be spent wastefully by cap-prefix policies. On these78 HELM ceil
targets, lowest-score-first with only its final step refined has median L1/optimal
L1 ratio1.0 for mean,7.742053 [6.321592,9.526371] for median and4.785803
[4.138806,5.445024] for minimum. These describe the named policy: full lifts on
earlier tasks can overshoot their needed scores. They do not establish a
training-cost factor or an advantage over every possible threshold-aware greedy.

`final_controls_validation.json` passes all-target coverage, canonical optimal
cost references, objective bounds, the mean/headroom and minimum/low-score
identities, and independent scalar-prefix checks. `clean_final_controls.json`
freshly recomputes all110,876 records with zero difference.
`final_controls-summary_validation.json` independently checks all300 ratio
points, denominators, bounds and equality under the shared bootstrap draws.
`clean_final_controls-summary.json` separately regenerates all300 shared-draw
ratio/interval rows with zero difference. The earlier independent-policy-draw
bootstrap was superseded, preserving it under `checkpoint_archive/` with its
scope; no raw observations or point estimates changed.


## Matched rival counts and task counts (request4)

`final_frames.csv` contains250,848 costs for201 frames:100 random79-model OLLB
subsets, fixed mean-top79 OLLB, and100 six-subject HELM subsets retaining all79
models (seed31). Every draw has78 targets after excluding its unique mean leader,
eight rules/requirements, ceil/gain10 and independently optimized K/L1.
`final_frames_diagnostics.csv` records selected names/tasks, matrix hashes,
task correlations and mean best-rival-minimum minus best-rival-mean threshold.
`final_frame_draws.csv` gives6,432 rule/cap/metric group rows with feasibility,
all-target and conditional finite medians/quartiles, under both median conventions.
`final_frame_contrasts.csv` has402 paired min-minus-mean feasibility contrasts;
`final_frame_intervals.csv` and `final_frame_contrast_intervals.csv` give96 and6
across-draw summaries. These are selected-frame sensitivity ranges, not CIs.

At gain10 (median paired feasibility difference [2.5%,97.5%] across draws):

- Random OLLB79: +0.076923 [-0.051282,+0.307692]. Minimum is more reachable than
  mean in84 draws, less in12, equal in4; their marginal median reachability is
  0.205128 versus0.128205. Matching the number of rivals therefore preserves
  the original sign in most draws, not uniformly.
- Random HELM6: -0.179487 [-0.371795,+0.230769]. Minimum is less reachable in89
  draws, more in9, equal in2; marginal median reachability0.128205 versus0.346154.
  Matching task count alone likewise preserves the original sign in most draws,
  with substantial exceptions.
- Fixed mean-top79 OLLB: minimum59/78=0.756410 versus mean78/78=1.0; paired
  difference -0.243590. The sign reverses relative to full OLLB and most random79
  draws despite having the same number of models/tasks. Mean-based population
  selection matters; the fixed frame supplies one observation, not100 replicates.

At ceil, every target in these panels is feasible, so the feasibility contrast
is0 and the K/L1 distributions, rather than reachability, distinguish rules.
The theory diagnostics are descriptive: mean pairwise task correlation has
median0.666492 [0.579582,0.744896] in random OLLB79 and0.798605
[0.659912,0.882286] in HELM6; top79 has0.015920. Mean rival-threshold gaps are
respectively -25.884157 [-31.208952,-20.830249], -8.416410
[-26.661365,-3.048762] and -28.946318 score points. Their differing score units
and jointly changing populations prevent an identified causal explanation by
correlation or threshold gap alone. Matching one dimension does not identify
all remaining differences.

Validation: `final_frames_validation.json` independently reconstructs seed31
selections, all201 matrices/hashes, target sets, correlations/theory quantities
and cap monotonicity. `final_frames-summary_validation.json` checks all group
points and paired/cross-draw ranges. `clean_final_frames.json` recomputes every
cost/diagnostic with zero difference, byte-identical CSVs: canonical5335.46wall/
3232.31CPU seconds, clean5066.35wall/3184.97CPU seconds. The four summary CSVs
also regenerate cleanly with zero difference (`clean_final_frames-summary.json`).

## Cost units and data-derived caps (request6)

`final_scales.csv` contains234,744 target/cap/rule records for HELM, full OLLB
and top500: existing raw optima, K/n and L1/n, separately optimized sum(delta/SD)
and max(delta/SD), all primary caps plus gain_iqr, and missing top500 gain5/20.
SD is across all models of that frame, ddof0. `final_scales_task_scales.csv` gives
all69 task SDs/IQRs. The1099 rows of `final_costscale_summary.csv` retain infinity,
conditional feasible-panel denominators, both median conventions and quartiles.
`final_caps_feasibility.csv` gives84 gain5/10/20/IQR rule/frame rows. The full
OLLB frame has the five score rules; its ordinal comparisons remain explicitly
the top500 frame. Condorcet is a sufficient requirement, separately labelled.

Raw score points and SD units support different comparisons. At ceil, median
L1_sd for mean/geometric/harmonic/median/minimum is:

| frame | mean | geometric | harmonic | median | minimum |
|---|---:|---:|---:|---:|---:|
| HELM (78 targets) |49.635875|50.518605|50.396255|9.887937|8.229266|
| full OLLB (4495 targets) |11.125774|15.399040|14.408455|7.233986|6.406905|
| top500 (499 targets) |7.332226|9.945774|7.307283|4.568627|2.931271|

Thus mean no longer has the largest median L1 among score rules in SD units;
minimum and median remain cheaper at the median in these ceiling panels. These
are separate weighted optima with unchanged ranking rules/margins, not an old
L1 optimum divided by average SD. SD units remain population/frame dependent;
neither them nor per-task normalization identifies training costs or makes
all cross-benchmark comparisons commensurate. `normalized_median` in the old
main summary is median/n for K/L1, unchanged raw median for Linf; definitions
and infinity handling are explicit in FINAL_EXTENSION_PROTOCOL.md.

Reachable counts at gain5 / gain10 / gain20, with fixed mean-nonleader targets:

| frame (denominator) | mean | minimum | median | Borda | plurality |
|---|---|---|---|---|---|
| HELM (78) |11 /29 /56|7 /14 /34|16 /40 /66|11 /25 /49|29 /57 /74|
| full OLLB (4495) |13 /113 /830|105 /446 /2873|40 /203 /641|not evaluated|not evaluated|
| top500 (499) |13 /113 /499|95 /348 /496|40 /200 /480|53 /325 /495|8 /53 /476|

The cap `gain_iqr` raises each coordinate by its frame's task IQR (linear
Q.75-Q.25) and clips100, with effective cap at least the original target score.
It is a descriptive data-derived scale, not an achievable training gain. It
changes a central sign: on full OLLB, mean582/4495=0.129477 versus minimum
283/4495=0.062959, reversing the gain10 minimum advantage. On HELM, mean39/78=0.5
versus minimum20/78=0.256410; on top500, mean52/499=0.104208 versus minimum
129/499=0.258517. The ranking of reachability therefore depends on the cap as
well as the frame and rule; the gain10 reversal is not universal over caps.

Validation: `final_scales_validation.json` checks original costs, SD/IQRs,
normalized values, rank metadata, weighted objective bounds and gain-cap
monotonicity. `final_scales-summary_validation.json` checks every summary point
and legacy main-summary counts/medians. Independent raw and table regeneration
has zero difference (`clean_final_scales.json`, `clean_final_scales-summary.json`).
Canonical raw computation3967.06wall/3743.96CPU seconds; clean3849.86wall/
3673.73CPU seconds. The optional MILP effort limit does not change these results.

A caught metadata defect is preserved, not silently discarded: first-summary
HELM ranks compared a row-mean reduction with the matrix-mean reduction, so
roundoff included the mean leader among nonleaders. The runner now uses one
mean vector. `fix_final_scale_ranks.py` independently repaired1232 rank fields
(22 models across56 conditions) in both raw files, preserving every other CSV
field's text exactly, including every optimized cost. Repair hashes and the
unchanged-field hash are in `final_scales_rank_repair.json` and the raw metadata;
`clean_final_scales.json` records both postprocessing reports. Superseded tables
and the earlier limited checker record are explicitly archived under
`checkpoint_archive/final_scales_rank_metadata/`. Final summaries use corrected
78/4495/499 denominators and were regenerated from those corrected raw records.

## Full-frame diagnostic reference rows (figtab request9)

`full_frame_diagnostics.csv` supplies the same correlation and threshold-gap
quantities as the201 matched frames, with complete metadata and matrix hashes.
Pearson correlation averages all unordered task pairs across every model;
the gap averages max-rival-minimum minus max-rival-mean across fixed
mean-nonleaders, excluding each target from its rivals. No cap or epsilon enters.

| frame | models/tasks/targets | mean task correlation | mean rival-threshold gap (points) |
|---|---|---:|---:|
| HELM |79/57/78|0.7887879295|-27.6499327149|
| full OLLB |4496/6/4495|0.6723035414|-28.9352256895|
| top500 OLLB |500/6/499|0.0826548024|-28.9367942786|

These frame-dependent descriptive quantities identify no cause of the rule
reversal, and their gap score units differ across benchmarks. Generation:
`src/summarize_full_frame_diagnostics.py`; independent top-two leave-one-out
maxima and pandas-Pearson checker: `src/check_full_frame_diagnostics.py`.
Both are in `make final-summaries`/`make all`. A fresh code/processed-input export
(no copied results) regenerated a byte-identical CSV, zero difference:
`clean_full_frame_diagnostics.json`; measured canonical/clean runtime records
are supplied separately. This small diagnostic addition is separate from the
now-passed original16-file clean optimization gate.
