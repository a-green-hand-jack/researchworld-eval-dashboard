# Feasibility assessment: fixed-input mean confidence intervals

## Decision and scope

**Proceed with a bounded mean-inference study.** CPU cost is already demonstrated to be modest by the analysis owner's execution log. The feasible scientific conclusion is conditional: prespecified nonlinear transformations of a frozen score may reduce interval width relative to a specified scalar baseline, under stated sampling and validity assumptions. A claim of universally shortest valid intervals, novel optimal inference, or validity for every finite sample is not supported by this study design.

This is an independent feasibility judgement, not an analysis result or a final review. It covers the frozen Research objective and all six mapped input files. Settled against the subsequently published idea-repo Brief and story-repo operational plan: their fixed-input interpretation and bounded mean scope are consistent with the objective. Remaining comparison/reporting gates below do not prevent continuation of the existing grid; they limit claims until answered. No empirical effect size or coverage is asserted here.

## Inputs actually inspected

- `/initial-state/inputs/0/{TASK.md,TASK.en.md,data.md,deliverable.md,resources.md,starter_literature.md}`; task map in idea-review-repo#1.
- experiment-repo main `e489570fe452dcb8191cf768aa0c2be6202e2b36`: `analysis/methods.md`, `analysis/run_log.md`, `code/run_experiments.py`, `code/summarize.py`, `code/coverage_diagnostics.py`, `code/finalize_results.py`, `results/verification.json`, `provenance/manifest.json`.
- story-repo#2 and #4, experiment-repo#2; live local-compute status read during this turn. The latter contains measured job records, not independent timing experiments by this position.
- Initial context and plan requests: idea-repo#3 and story-repo#6. Settlement sources: idea-repo Brief wiki (read in full), idea-repo main `1d14e36a721ecc189de1c228bc852bce164e1d39`, and story-repo `0ab3706a1ad173fe2b62d317757844ea3b1110be`, `planning/study-plan.md`. The Brief references a Baseline-context page that was not yet available when inspected; no source claims from that unavailable page are treated as independently checked here.
- Follow-up analysis specification/log inspected at experiment-repo `ff9cd71b606721faeece061b71e2ce214ac6c3d7`; story-repo response to #6 confirms no delivered feasibility appendix is required. Current paper-repo CODEOWNERS respects that split.

No outside literature search was performed, and no restricted material was accessed or inferred.

## Risks and required bounds

| Risk | Consequence | Required bound or mitigation |
|---|---|---|
| Treating “fixed inputs” as conditioning on all observed values | Repeated-sampling coverage becomes undefined or answers a different question | Hold each labeled set, unlabeled set and predictor identical across methods within each replicate; explicitly state what is resampled across replicates. |
| Normal intervals treated as exact | Good Monte Carlo coverage cannot establish the required finite-sample guarantee | Distinguish fixed-dimension asymptotic Wald results from bounded-data empirical-Bernstein (EB) and exact binary label-only guarantees. Present failure regimes. |
| Coverage acceptance by a nonsignificant test | Low power can conceal undercoverage | Report point estimates and intervals; “compatible with 95%” is a diagnostic, never a proof of validity. Do not declare superiority because an invalid interval is narrow. |
| Free calibration labels or unfair unit-PPI split | Apparent gain comes from unequal resources or a weakened baseline | Count all nuisance-training labels in n; include full-label unit-PPI EB and all-label exact binary intervals, alongside the common-split comparators. |
| Baseline restriction mistaken for nonlinear benefit | Beating a coefficient clipped to [0,1] may reflect coefficient restrictions | Retain unrestricted scalar and cross-fitted linear diagnostics; distinguish representational gain from clipping and fitting costs. |
| Chosen basis/cells selected by final coverage or width | Selection can invalidate uncertainty or exaggerate gains | Keep cubic prespecified, degree 12 diagnostic, all declared regimes visible; record supplements and their timing. No post-selection validity claim. |
| Arbitrary transformations promised to beat all inference | The variance algebra optimizes only an estimator class | Bound theory to additive fixed-score control variates, with explicit regularity assumptions and finite-N cost. No universal optimality or novelty claim. |
| Archived-data resampling called scientific-population validation | With-replacement empirical-population truth does not establish generalization or representativeness | State empirical population, independent with-replacement draws, evaluator-only access to held-out Y, and no natural-population inference. Forest n=2000 exceeds its 1596 records; duplicates are part of this declared sampling design. |
| Unbounded/heavy-tail data assigned bounded guarantees | Range assumptions fail | Restrict EB claims to known Y and control ranges; report t3 cases only under their actual moment/asymptotic assumptions. |
| One sample ratio extrapolated to all resources | N=10n does not empirically characterize all N/n | Keep numerical claims at the studied ratios; any broader finite-N statement must be theoretical and explicitly scoped. |
| Overclaiming novelty in a restricted-literature task | A valid application may not clear a main-conference novelty bar | Describe the study as an independently evaluated control-variate route. Context owner positions only against permitted work; do not seek the withheld paper. Negative/conditional conclusions remain objective-compliant. |
| Missing final artifact despite completed computations | No reviewed release means no user delivery | Preserve time for the venue's current official template, PDF/source, reproducibility mapping, checklist if required, CODEOWNERS integration, and independent final review. These belong to their owners. |

## Precision and compute feasibility

Planning calculation, **not a measured coverage result**: at true coverage p=.95, the Monte Carlo standard deviation of an R-replicate proportion is sqrt(.95*.05/R). For R=5000 it is about .00308 (0.31 percentage points), with a rough two-sided 95% half-width of .00604 (0.60 points). For R=3000 these are .00398 and .00780. Wilson intervals in the implementation are appropriate to report. These repetitions can expose percent-scale failure and sizable width changes; they cannot certify exact .95 coverage or resolve arbitrarily small departures. A fresh independent test set is not a substitute for a theorem either. Multiplicity adjustments are needed for joint rejection claims; per-method Holm diagnostics in the inspected code have that limited family scope.

Width uncertainty must use paired draws. The implemented ratio of mean widths and paired delta-method SE answer the objective better than mean per-replicate ratios, which can misbehave with zero-width Wald intervals. Direct comparisons to the strongest finite-sample baselines must remain available. Coverage and width are different outcomes; absence of a detected coverage deficit does not turn an asymptotic method into a finite-sample method.

Measured costs reported by the analysis owner/resource record:

| Work | Source | Measured elapsed time |
|---|---|---:|
| Main real empirical-population grid, 45,000 draws | `analysis/run_log.md`, completed resource record | 223.495 seconds |
| Main synthetic grid, 105,000 draws | completed resource output, last cell | 474.88 seconds |
| Bounded high-signal supplement, 6,000 draws | `analysis/run_log.md` | 68.332 seconds |

These elapsed times are not additive CPU accounting: jobs can overlap and the resource records separately measure spend. They establish practical feasibility of this bounded grid well within the supplied one-week/<8-CPU-hour planning envelope, not a promise about arbitrary extensions. Exact-baseline additions and deterministic summary replay are short jobs already implemented. Three downloaded data files total less than 1 MB by the manifest; scalar arrays and fixed low-dimensional least squares fit the actual 2-CPU/4-GB sandbox. The input resources.md recommendation of >=4 CPUs/16 GB is not a demonstrated requirement for this implementation. No GPU, model retraining, paid API, or additional labels are necessary.

Remaining costs are mainly context checking, artifact integration, figure/report construction, and review. Do not expand to training new models, quantiles/regression targets, all nine datasets, broad model searches, adaptive labeling, or exhaustive ratios before these required artifacts are secured. Those are not needed to answer the chosen mean question.

## Gates before claims and release

1. Context/plan owners settle the meaning of inference-only calibration, indispensable baselines, scope and ownership against the Brief and frozen objective.
2. Analysis supplies complete measured outputs, seeds, metadata, data hashes, dependency versions and reproducible commands. Reference matching is useful implementation evidence, not coverage evidence.
3. Evidence includes nonlinear gain, linear/no-signal limits, rare-event/heavy-tail/small-n failures, same-input paired uncertainty, and separately identified theorem-backed comparisons. A measured no-gain result passes the objective; an unrun item does not.
4. The report states which conclusions are asymptotic, finite-sample guaranteed, or empirical diagnostics. It must not silently choose methods/scenarios because their measured coverage is favorable.
5. Code/PDF/source/figure-table provenance and venue obligations are delivered and independently reviewed by their owners. This memo is advisory and supplies no approval for release.

If nonlinear fitting is unstable or does not improve width, revise the conclusion rather than add labels or alter the predictor. If EB gains occur only in the designed high-signal large-n case, report that boundary and its conservative costs. If normal intervals under-cover, retain the failure evidence and limit the validity claim. There is no feasibility reason to promise a positive result.


## Settled independent judgement supplied to planning

The plan's Q1–Q4 can answer the frozen objective as a conditional investigation of score-only mean inference. I agree that estimating prespecified score controls from existing labels is admissible inference under the frozen predictor constraint: it leaves the original predictor and its outputs unchanged, acquires no extra observations, and charges all calibration labels to n. The report must describe this interpretation rather than imply an unconditional permission to retrain a predictor.

The proposed same-input pairing, all-label and split-aware baselines, empirical-population sampling, asymptotic/finite-sample separation, and class-restricted theory address the main feasibility risks. The extra finite-sample construction is valuable because it prevents a normal-approximation success from being the only answer to the nominal-validity requirement. No result is promised: no gain and detected undercoverage are legitimate conclusions.

Two concrete claim gates were identified at this settlement; both have since been answered as recorded below. First, experiment-repo#5 requests direct paired rows against full-label unit-PPI EB and exact binary label-only; this is inexpensive postprocessing, and it holds claims of shortening relative to those baselines, not the experiment grid. Second, story-repo/idea-repo must settle the permitted stratified-PPI comparison or give an explicit scope-based exclusion. Until then, name the implemented baselines and avoid a statement that nonlinear controls improve on existing valid methods generally. Neither issue justifies accessing the withheld literature.

A new practical risk appears in the analysis owner's updated run log: rare very large cubic widths at small n in forest/alphafold. This is an analysis-owned observation, not my independently generated result. It makes fitting-cost/no-gain reporting essential: retain every draw, preserve mean width as the objective's metric, report tails and uncertainty, and do not substitute a median or delete unstable cases to claim improvement. Fixed p and cross-fitting alone do not ensure useful finite-sample behavior. If uncertainty of a claimed gain is dominated by a few draws, narrow the claim or have analysis assess that uncertainty before release; the feasible fallback is an honest unstable/no-gain conclusion, not tuning away the evidence.

No new estimand, predictor training, extra datasets, adaptive labels or exhaustive N/n grid is required for feasibility. The remaining required effort is direct baseline summaries, checked contextual positioning, honest analysis/figure/report integration, and independent review. Planning owns the final comparator decision, analysis the statistical results, and report/presentation/venue/review their respective deliveries. This judgement does not approve a research result or release.


## Follow-up: supplied answers checked and claim gates resolved

I checked story-repo#6's scope decision and the revised plan at `59d9e5388aeb2ff10ff9b9ede8e08bb75f442242`. No feasibility appendix is required; the assessment is advisory input to planning. The revised plan preserves the validity, fixed-input, label-accounting and empirical-population boundaries. It also documents the subsequent n=N=2000, three-scenario finite-N follow-up as a follow-up rather than a preregistration. Accordingly, the numerical scope is now the original N=10n grid plus those explicitly identified N=n cells, not arbitrary ratios.

The previously missing context was supplied in idea-repo main `9441ead4475ba2b8002d81aab8fca88fafab3f8b` and wiki `c0b8b2570288bde407dc8eb6a971ccd58062db07`. I read Baseline-context in full. It supports a reasoned exclusion of the published fixed-stratum-allocation StratPPI design from a strict already-realized-iid-input comparison: known masses and controlled stratum counts differ from the present random counts/estimated masses. A suitable retrospective bin-indicator control remains possible. Therefore no further stratified experiment is essential to the narrow cubic-versus-affine study, provided the relationship and design mismatch are discussed and broad superiority claims are excluded. This does not imply all stratification is inadmissible. The supplied context separately confirms unrestricted scalar tuning and matched linear controls are essential and already included.

I checked experiment-repo#5's delivered answer against main `1bca487b5f3d3a16fdf6e6293a44267df46bd277`. The actual `results/paired.csv` contains explicit full-label unit-PPI EB and Clopper–Pearson baseline rows, including paired ratio/difference uncertainty and eb_cubic comparisons wherever applicable. `analysis/findings.md` separates the bounded nonbinary high-signal EB result from negative binary/real-data comparisons, preserves small-label failures and tail instability, and limits normal-coverage language to empirical compatibility. This closes the requested baseline-summary gap; it is a check of supplied comparison material, not an independent reanalysis or theorem verification.

**Current feasibility conclusion:** both earlier comparator gates are answered. Continue to complete and review the integrated paper/code; no additional experiment is required by this feasibility assessment. All validity, estimator-class, empirical-population, uncertainty and novelty limits remain. Independent analysis/review owners must still check the statistical proof and actual final claims; resolved feasibility does not approve release.
