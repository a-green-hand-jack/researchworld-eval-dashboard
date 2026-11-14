# Artifact-to-claim map and delivery history

Current status: complete numerical delivery and integrated presentation
acceptance, as recorded in `figures/MAIN_HANDOFF.md` and
`figures/inspection.md`. The historical planning and preparation entries below
are retained to show how the evidence contract developed; their pending-input
statements do not describe current delivery status.

Initial status: layout and evidence contract, not an empirical result. Read against
objective #1, the idea Brief, story protocol at
`6e178e2afec2d3156922718fb27b6d9b30e24f01`, and venue requirements at
`6483302545cb5dc2426cddea871c89377ed4aeeb` on 2026-11-03.
Experiment's reply in experiment-repo#4 gives planned CSV names, not final
headers or measured results. Numeric generators will bind to the final schema;
no input fixture or illustrative result is distributed as evidence.

Owned delivery roots are `figures/` and `tables/`, including code, captions,
provenance and generation manifests (paper-repo CODEOWNERS, checked at
`3e8cc96d5dc700bd4b91b017f2f28fe6012dd541`). No `presentation/` root is needed.
Names below describe intended assets; final inventory depends on completed
results and the manuscript's nine-page main-text budget.

| Asset | Question it makes checkable | Encoding and placement | Numerical supply |
| --- | --- | --- | --- |
| `figures/one_run_budget.pdf` | Which dataset/model/estimator/budget cells meet the declared one-run tolerance scenario? | Main-body 2 by 3 small multiples (dataset rows, fitted model columns), common success-rate y scale [0,1], actual model rows on log x, two redundant method encodings and instance-cluster CIs; show reference ambiguity or refer to explicit assessability counts | Aggregate primary event estimates and intervals, actual budget coordinates, per-cell denominator and reference status |
| `figures/error_repeatability.pdf` | Does run agreement conceal reference error? | Main-body aligned condition panels; distinct series for reference error and independent-run error only when their normalization/scale is matched. Keep estimator color consistent; metric uses line/marker. If scale is not matched, use separate aligned rows rather than a misleading common axis | Analysis-defined per-instance repeatability and reference-error aggregates on the same instances, intervals and common normalization; pair counts are not n |
| `figures/conditions.pdf` | What changes near a ranking boundary or weak attribution signal? | Reference-defined gap/weak-signal strata, with uncertainty and n per stratum; preserve ambiguity counts. Main body if central to the supported claim, fuller strata appendix | Prespecified stratum labels/boundaries and aggregate results; reference norm/gap and assessability; no strata selected using observed low-budget success |
| `figures/budget_time.pdf` | Are reliable cells feasible in measured elapsed time? | Companion budget curves with measured seconds on x, same rate/condition encodings as primary figure. Do not add a secondary axis pretending model rows and time have one universal conversion | Time aggregate with defined scope/statistic, hardware, threads, overhead/caching policy; actual main-run measurements |
| `figures/metric_sensitivity.pdf` | Does the conclusion depend on magnitude floor or adequacy cutoffs? | Appendix aligned panels or heatmap with explicitly labeled thresholds; show magnitude and signed/unsigned selection components separately | Planned tolerance grid, normalization-floor sensitivity and component summaries with uncertainty |
| `figures/instance_distribution.pdf` | Does the panel-average rate hide individual failures? | Appendix ECDF of per-instance run success probabilities or numerical errors, identifying finite repetition count; no claim that finite zero failures certify an instance | Analysis-owned instance summaries and planned interval handling, source instance IDs and repetition denominators |
| `tables/study_coverage.tex` | What exactly ran and how well do the fitted models predict? | Main-body concise booktabs table, one row per dataset/fitted model; full version/split/feature/background/panel/repeat configuration in caption or companion appendix table to avoid unreadable width | Actual completed config/manifest, data version/row identity and model diagnostics including declared held-out quality metrics |
| `tables/cost_reference_status.tex` | How much did evaluation cost, and which references/runs were resolved? | Main-body compact summary where feasible; appendix detailed per-condition table with actual model rows/time, reference method/gate, assessable/ambiguous/failed counts. Give training/pilot/reference/main totals separately in the full accounting | Run/cost aggregates, reference diagnostics, failure records and denominator manifest |

## Caption and uncertainty contract

Every caption states the fixed empirical-background game, positive-class output
units as needed, grouped raw-feature units, estimator identity, what one point
averages, CI coverage/procedure/resampling unit, and the relevant n. Captions
can refer to the methods for full definitions but cannot omit the metric's
meaning or direction. All conditions use the same legend order and scales
where comparisons are intended. The operational primary event and its threshold
sensitivity follow the main-run freeze, not an unreviewed plotting default.

Near-zero signs and top-k ties have metric-specific status. Include definite
and possible success summaries only when the analysis supplies them. Keep
unresolved cases distinct from measured failures and list denominators in
both captions and machine-readable manifests. Label exact references as exact
only for the selected empirical game; label exhaustive estimator cells when
they cease to be stochastic.

No universal reliability claim is drawn from a point estimate or from an
average over unrelated cells. A declared panel-average target is drawn as a
reference line only with the protocol's justification; the interval lower bound
is what supports crossing it. Negative, flat and uncertain curves receive the
same rendering and visible costs as favorable ones.

## Venue implementation

NeurIPS 2026 uses a **single 5.5-inch column**, not two columns. Assets use
5.5-inch width unless the actual paper placement requests a smaller width.
Start with 9-point plot text, 8.5-point ticks and 10-point panel titles and check
at actual placed size; these are presentation choices, not official minima.
PDF/PNG are paired outputs; PDF fonts are embedded TrueType or Type 1, never
Type 3. Do not use tight-bbox export that silently changes the physical width.
Figure captions go below and table captions above; tables have no vertical
rules. Final assets are opened, inspected for clipping/legibility and grayscale
readability, and checked again in the integrated root PDF supplied by paper.

## Execution and handoff

1. Bind actual final analysis headers and definitions to figure/table generator
   code. Refuse missing required inputs rather than draw empty/synthetic panels.
2. Render from committed result paths, with analysis revision and hashes for
   each input plus panel/filter/column mapping in an artifact manifest.
3. Inspect each PDF/PNG and rendered table, verify fonts and physical size,
   and record the actual command, versions and inspection outcome.
4. Push our artifacts/code, submit an AGit PR to paper main under owned paths,
   and provide caption source and include commands. Keep integration requests
   figtab-repo#2 and #4 open until their numerical deliverables are complete.
5. Inspect the integrated root PDF for final size, legend/caption clarity,
   placement, page legibility and all factual values before final acceptance.


## First executed presentation assets (pilot validation only)

The initial pilot at analysis revision
`4f4cf9882bc2e8798ae3b68e8884091c6de5e818` supplies actual work and CPU-time
measurements. `figures/pilot_budget_accounting.pdf` shows nominal versus actual
prediction work, with exhaustive Kernel cells labeled; `tables/pilot_call_costs.tex`
preserves raw call times for the same pilot. They support budget accounting and
the rationale for dimension-specific later grids. They do not answer the main
single-run adequacy, repeatability, accuracy or failure-condition questions.
Those deliverables and integrated-placement checks remain open. All pilot
inputs, generators, captions, manifests and inspection records accompany them.


## Accepted full matrix and inference handoff

Read story main-design at `366e9927f4060d7c3ac2d9670de6b48c588fb13d` and
analysis result-schema/boundary-inference at
`de214716c29b7186c005e22f03da2ed4b92674e9`. Diabetes is retained: adapt main
panels to three dataset rows by three fixed-model columns, not a forced six
facets. All 540 references are planned as exact finite-game enumerations;
no main result is available yet. The 97,200 calls and 60-input/30-repeat/B32
matrix are accepted design counts, not executed evidence here.

For direct error/repeatability comparison, both L1 distances use the same
max(reference L1,.01) denominator; pairwise summaries have one independent unit
per input. The distinct average-run-normalized metric is not substituted.
Display `ci_low/high` and retain `interval`/`boundary_adjusted`: raw bootstrap
endpoints can degenerate at observed all-zero/all-one boundaries. Mark the
supplied positive-width two-sided Hoeffding boundary intervals and explain the
switch in captions. Only analysis's explicit `certifies_mean_ge_0p95` guard may
support that threshold claim; the current 60-input guard cannot certify it even
at zero observed failures. This is a precision limit, not measured unreliability.

`figures/generate_main.py` is prepared against this schema, with no generated
numerical outputs yet. It stops for missing/partial evidence or an exhaustive
primary cell that needs explicit annotations. Component/condition/sensitivity
views and final tables still require the main handoff. Pilot placement was
accepted at paper revision `77c9c7b0298b9b7fe0004d95e1715518f8fa1174`;
see `figures/inspection.md`.


## Expanded postprocessing handoff

Analysis `8e2ef11a761c6051c2eaef5ca28941ee1ccfc343` supplies final schemas for
`assessability_counts.csv` and `floor_sensitivity.csv`; these remain future main
outputs. Reference-defined numerical top1/top3-boundary ties, selected nearzero
signs, weak signals and active-sign defined counts stay separate from the
all-instance exact-reference primary denominator. Counts repeated across
method/budget cells must not be summed into an inflated sample size.

The prepared `tables/generate_main_tables.py` binds actual predictive coverage,
reference caution counts and completion-process/saved-reference cost records,
with full-grid/source/count checks and per-row provenance. There are no new
numerical tables yet. Floor sensitivity uses the supplied .001/.01/.05 rows for
both normalized L1 error and the unchanged signed-top3 success event. The
sensitivity display will keep the selected floor as an explicit axis/legend,
with the .01 primary scenario identified and absolute error/weak-signal counts
nearby; no post-hoc floor is selected for better apparent reliability.

For near-tie and weak-signal condition plots, missing intervals at n<2 must
remain visibly unavailable. An empty stratum is not a zero-success stratum;
a one-input stratum can show its observed estimate with no population interval.
All stratum n, fixed references and exploratory/descriptive scope remain visible.
The execution GO in story main now authorizes the accepted full matrix; it does
not supply achieved reliability evidence or alter these presentation rules.


## Condition, scenario and heterogeneity implementation

At accepted execution freeze signature
`8369b51bd944ea510afbc5a372f17d1c7f28f15a6a08d9c242bf6b3effaaef26`,
analysis reports tracked jobs but no completed main panel. Preparation now
includes `figures/generate_diagnostics.py`, without numerical artifacts. It
binds per-dataset gap/weak-signal curves with n and absent/singleton handling;
cutoff, selection and floor scenarios; magnitude/selection/absolute-error
components; and ECDFs of observed successes/30. All scenario intervals come
from analysis; no new inference is done by presentation. `figures/README.md`
lists candidate assets, semantics, dependencies and execution limitations.

These code paths cover the outstanding display types in the accepted artifact
allocation, but do not complete #2/#4 or numerical-output inspection. Full
results, interval/source/denominator validation, actual rendering, final density
and font checks, numerical verification and root-PDF acceptance remain open.
Post-main background checks, if executed, require separate displays of
changed-game estimation error and reference-target shifts; do not pool those
with the fixed-B32 main experiment or label target shifts as estimator error.

## Executed complete-main handoff (2026-11-05)

All required fixed-background display types have now been rendered from
experiment `c291b715fcfed90d5b5905e2d7a8e1f721937616`. The actual inventory and
recommendations are `figures/MAIN_HANDOFF.md`: 16 figure PDFs and 4 numerical
tables, each with code, source mappings and preview/inspection support. Main
cost views use measured process CPU and actual rows; contaminated wall times
are archived with explicit limits. Near-tie conditions retain sparse n;
weak-signal strata have no inputs, and floors never activate. Those unsupported
conditions remain visible limitations. No fitted inference was reimplemented.
Main numerical handoff does not finish the separate changed-background arm or
root-PDF placement inspection; requests #2/#4 remain open for those items.

The completed supplement at analysis
`5d8d8e37ed7868e8d088315688c0843678abee55` is now rendered separately as two
changed-background figure PDFs and a phase-cost table. A compact
`criterion_instance_contrast.pdf` joins strict high-budget recovery with the
observed ACS RF 0/30 input contrast for main-text use. Total standalone
inventory is 19 figure PDFs and five numerical tables. All are opened and
checked; integrated root-PDF placement remains the open item in #2/#4.
