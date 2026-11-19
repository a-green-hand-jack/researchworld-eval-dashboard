# Evidence and display design

Status: working presentation design; no measured results or final figures yet.
Owner: figtab-repo, commitment #3. Objective: #1 and the five frozen inputs
under `/initial-state/inputs/0/`. This design serves the objective's question:
when does one stochastic SHAP run support a reliable explanation for a fixed
trained tabular model and a fixed input under a realistic compute budget?
The study plan, analysis, and venue owners settle their respective inputs.
This document does not prescribe their conclusions or replace their methods.

## Claims that must remain distinguishable

1. Reproducibility: independently seeded explanations agree with one another
   for the same trained model, input, feature game and background.
2. Reference agreement: an explanation agrees with a justified reference for
   the same game/output scale. Reference numerical error is a separate source
   of uncertainty; agreement alone is not proof of correct attribution.
3. Cost: reliability at a specified evaluation budget and measured elapsed
   time, on a specified CPU setup. An explainer's nominal sample count may
   differ from actual calls or input rows evaluated by the model.
4. Scope: reliability can vary across datasets, trained models, instances,
   feature counts, approximation methods and any studied background choices.
   Seed-to-seed variation in explanations must not be presented as training,
   population, or background-selection uncertainty unless those were sampled.

## Candidate displays and their evidence requirements

The final inventory follows the agreed claims and completed experiments.
Unsupported views are not rendered as placeholders.

| Purpose | Encoding | Required committed evidence | Reader check |
| --- | --- | --- | --- |
| Budget tradeoff | Small multiples by dataset and model, budget on x, a clearly named reliability metric on y; estimator identities use both line style and color | Aggregate estimates and intervals by budget plus definitions, repeat/instance counts and actual evaluated budgets | Whether an increased budget improves the measured criterion, and how certain that estimate is |
| Reliability versus reference accuracy | Separate aligned panels with identical budget and group encoding | Pairwise-repeat metric and reference metric for the same evaluated instances; reference validity diagnostics | Whether apparent repeatability coexists with reference disagreement |
| Heterogeneity or failure | Per-instance distribution (ECDF or compact point/interval view), stratified only on prespecified or explicitly exploratory conditions | Per-instance metrics, selection rule, matched identities and interval information as appropriate | Whether a good aggregate hides unreliable cases |
| Computational feasibility | Reliability versus measured elapsed time, or compact cost table beside the budget display | Timing distribution, evaluation counts, hardware/thread settings, timed scope and repetitions | Whether the observed accuracy is attainable under the deployment-like constraint |
| Study coverage | Compact table of datasets, splits/features, models, explanation game/output scale, repeats and budgets | Actual configuration and completed-run manifest, including failures | Which conditions are actually supported |
| Reference quality/sensitivity | Diagnostic table or appendix panel, consistent with the analysis owner's reference assessment | Independent reference replicates/convergence or exact control results; changed-game/background labels | Whether the benchmark and any claimed robustness are justified |

A single panel will not mix all metrics. Main-paper panels will focus on the
agreed decision criterion and one complementary metric where needed; fuller
metrics and diagnostics belong in appendix assets if evidence supports them.
Do not choose a decorative example waterfall as the principal evidence for
repeated-run reliability. If example attributions help explain a measured
failure, choose instances using a recorded deterministic rule and show all
relevant repeats or their distribution with signed feature effects and units.

## Encoding rules

- Use grouped original input features when that is the study's feature game.
  Do not silently compare one-hot-column ranks with grouped-feature ranks.
- Label attribution output explicitly (for example, positive-class probability
  or log odds) and distinguish absolute magnitude rankings from signed effects.
  The analysis owner defines ties, zero tolerances, top-k and sign exclusions.
- Bounded rates use their full meaningful range when feasible; any zoom is
  explicitly marked. Error metrics keep their own scale and direction. Zero
  on a log axis is never replaced with an invented positive value.
- Multiplicative budget grids may use a log x axis with actual tick values.
  Exact/deterministic methods appear at measured costs with their identity;
  no invented budget points or connecting line implying unmeasured runs.
- Connect only estimates of the same method and condition. Connecting lines
  guide the eye and do not assert interpolation or monotonicity. Keep method
  colors and ordering consistent in all outputs, with shape/line redundancy.
- For intervals use caps, translucent bands or explicit text according to
  crowding. The caption names interval type, nominal coverage, and sampling
  unit. A band over an aggregate is not a range of individual explanations.
- If a reliability threshold is justified by the study, annotate its value and
  meaning; do not introduce an unexplained threshold because it looks useful.
  Threshold grids/sensitivity must be labeled as such, not universal guarantees.
- Record planned and completed denominators. Missing, failed, censored or
  unresolved-reference results receive an explicit status in a table or
  annotation, not a success value of zero or a silent omission.
- Use vector PDF for paper figures and PNG for inspection previews. Actual
  dimensions and typography follow venue-repo's supplied official template.
  Avoid legends inside dense data, tiny labels and solely red/green coding.
- Tables show units in headers; align decimal precision with uncertainty,
  without recomputing the analysis. Avoid boldface based on noisy point
  estimates alone. Distinguish a missing result from a measured zero.

## Statistical handoff boundaries

The analysis owner supplies definitions, estimands, interval calculations,
reference assessments and the result validity decision. Figure code can
reshape and format their committed values. Any new aggregation needed for a
view must be agreed with the analysis owner and fully traceable.

Pairwise comparisons among R runs create dependent pairs. Their count is not
an independent sample size. Likewise, multiple explanations of one input do
not create extra independent test instances. Captions must name the actual
unit represented by an interval and table denominators. Matched budget or
method comparisons should preserve matching in the supplied statistics.

Do not pool data/model conditions into a single "overall reliability" unless
the study explicitly defines the weighting and target population. Report
condition-wise results by default, retaining the hierarchy used in inference.
A reference generated with more samples is labeled high-budget rather than
exact unless the analysis establishes exactness for that game.

## Reproduction and acceptance

For every delivered artifact, retain:

- executable generator and command, dependency versions and deterministic
  presentation seed if any;
- input repository revision, relative file paths and file hashes;
- output filenames, panel-to-input/column mapping and any filtering/formatting;
- caption text with metric direction, aggregation, denominator, uncertainty,
  reference and computational budget units;
- inspection record confirming that the rendered output was opened and
  checked, then that its actual paper placement was checked for legibility.

Generators must fail on missing required evidence, unknown metric units or
contradictory keys rather than substitute synthetic values. Source configuration
is allowed for labels and layout, never for invented measured results. A final
figure/table and its generator are delivered together under story-repo's
CODEOWNERS allocation through a PR into paper-repo. The paper owner integrates
the captions and final layout, and supplies the rendered document for checking.

## Outstanding inputs

- story-repo#7 answered: `figures/` and `tables/` own all presentation
  code/captions/manifests; see `docs/artifact-map.md` for the protocol-aligned map.
- experiment-repo#4: planned CSV contract supplied; committed results and
  final headers/definitions/provenance remain pending.
- venue-repo#4 answered: NeurIPS 2026 single 5.5-inch column; details in
  `docs/artifact-map.md` and venue-repo notes.
- idea-repo Brief: read from wiki on 2026-11-03; initial interpretation agrees
  with this design. Recheck its settled context before final delivery.
- figtab-repo#2: paper integration request, remains open until assets are delivered.


## Alignment with the first supplied analysis commitment

Read `experiment-repo/notes/initial-design.md` at revision
`3ef708d4fc80edceef2de9ebcc1f62e6e7effc0e`. The design supplied there is pre-pilot and does not yet
contain data, result schemas, measured timing or a final study allocation.
It defines the empirical interventional game over grouped raw features, a
fixed output probability, fixed empirical background, comparison of
permutation-path sampling and sampled Kernel SHAP, actual coalition/model-row
cost accounting, and instance-level uncertainty. Final captions must identify
these objects using the actual completed configurations, rather than shorten
them to generic "SHAP".

The Brief and paper-repo's `Report-integration` wiki were also read on
2026-11-03. Their interpretation matches the separate agreement/accuracy/cost
views above; they contain no experimental conclusions to plot.

### Reference ambiguity must be visible per metric

A nearly tied reference ranking may be unresolved for a top-feature or top-k
claim even when its attribution vector is estimated precisely enough for a
vector-error comparison. A near-zero effect may be unresolved for a sign claim.
Display validity therefore follows the metric, not one global "valid instance"
flag. Numerical displays need, for each condition and metric:

- attempted, completed and metric-assessable instance/run counts;
- the reference resolution/tie rule and unresolved counts;
- whether the supplied estimate uses all sampled instances or an explicitly
  conditioned assessable subset, and why.

Do not drop unresolved instances and then label the conditional rate as an
unconditional reliability rate. Do not convert unresolved cases into measured
failures. The compact reference diagnostic table should preserve these counts;
if crowding requires appendix placement, the main caption still identifies the
conditional denominator and points to that diagnostic. Any interval or bound
for partially resolved outcomes remains analysis-owned.

If a gap-conditioned view is supported by the agreed plan, put reference gap
or margin on a meaningful labeled axis and distinguish genuinely changed
salient effects from ties. A tie-aware metric alone cannot establish a large
numerical error. Avoid final examples selected solely for visually dramatic
rank flips without their effect magnitudes and reference uncertainty.
