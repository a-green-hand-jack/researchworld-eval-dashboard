# Protocol: reliability of regions for observed compositions

Status: version 1.5; the seven-method core design was frozen after a separate implementation/runtime pilot and before the core run. Later source-driven score additions are dated amendments, with their chronology below. This is a research plan, not a results report. Subsequent changes must name their reason and whether made before or after relevant results were inspected. The frozen Research objective (`story-repo#1`) and all five files under `/initial-state/inputs/0/` govern this plan.

## Objective, target and contribution

Evaluate simultaneous coverage and efficiency of conformal prediction regions for an observed response Y in the simplex, initially strictly positive, conditional on features X. The benchmark does not infer a latent true class-probability vector from a single class label, nor evaluate a set of labels. It studies split-conformal scores and calibration choices with a shared fitted predictor. It does not claim an exhaustive comparison of full conformal, jackknife+, classification methods, or all compositional distributions. Those distinctions and method-selection reasons belong in the reviewed related work.

Permitted close prior work already conformalizes simplex-valued distribution labels with multiple scores and evaluates coverage/simplex size (Javanmardi et al., as documented in idea-repo's Brief). Do not claim the first composition-region method, benchmark, or coverage/size evaluation. Its noisy-distribution versus latent-distribution distinction is directly relevant.

The intended contribution is an independently implemented, reproducible evaluation design and evidence about which diagnostics reveal failures and which choices help under specified conditions. No new conformal theorem or universal best method is presumed. Synthetic-only study is explicitly allowed by the objective. Realistic utility, unknown groups, arbitrary shift, and empirical applicability to a particular application remain outside its evidence.

## Research questions and hypotheses

1. **Joint versus coordinate reliability.** Do correctly ranked joint-score regions achieve the finite-sample marginal target under iid sampling across dimension and calibration size, while coordinatewise alpha calibration can miss the simultaneous target? Joint scores and Bonferroni have the standard rank/union-bound justification; naive coordinate intervals are a negative control, not a valid joint baseline. Report observed departures even if the anticipated contrast is weak.
2. **Marginal versus subgroup reliability.** How do heterogeneous noise, learned training-only scaling, and observed-group calibration affect group coverage and variation across calibrated datasets? Global marginal validity does not imply subgroup validity. Scaling may improve adaptation but has no general group guarantee; Mondrian has a guarantee only for predeclared exchangeable groups. Neither is assumed more efficient.
3. **Geometry and efficiency.** At matched nominal joint coverage, what changes when raw and log-ratio scores are calibrated? Use a common uniform-simplex area measure at K=3. Its ranking is a choice of reference measure, not a universal measure of utility. Do not compare raw and clr radii numerically as efficiency. Undercoverage is displayed alongside area and disqualifies an unqualified claim of improved efficiency at reliable coverage.
4. **Scope of robustness.** How do a controlled group-mixture shift, finite calibration ranks, and zero/replacement handling change the interpretation of reliability? Shift preserves within-group laws by construction, so it can test that mechanism but not arbitrary covariate shift. Positive replacement defines a transformed estimand. Its coverage does not automatically apply to direct original-response membership, but an explicitly defined inverse-image region has exactly the transformed membership event and hence inherits original-response coverage; it is a different region whose area requires separate evaluation.

Directional expectations above are theory-based checks, not findings. All planned method/cell results, including negative results, must remain available.

## Confirmatory matrix

| Element | Settled choice |
|---|---|
| Response generator | Logistic-normal regression, fixed coefficients per dimension, anisotropic noise; full executable generator and constants supplied by analysis |
| Features and predictor | 1000 independent training observations; ridge regression on clr responses; training-only fitted scale for adaptive method; calibration never fits or selects models/scales |
| Dimensions | K=3 and K=10 |
| Calibration size | 99 and 499 |
| Noise scenarios | Homogeneous and heterogeneous; observed high-noise group probability .2; experiment documents actual noise and feature laws |
| Test environments | iid, and group-mixture weight changed from .2 to .8 with within-group joint laws fixed |
| Nominal error | alpha=.1 |
| Replications | 100 fresh independent train/calibration/test datasets per dimension/calibration/scenario cell; separate from pilot seeds |
| Test observations | 5000 per environment per replication; these do not count as independent calibration replications |
| Pairing | Every method sees the same data and area candidates within replication; environments share trained/calibrated methods |
| Area | K=3 only, 32 independent X anchors and 8192 uniform-simplex candidates per anchor, as frozen by analysis before the main run; record MC precision and unresolved cells |

Seven core prespecified methods: raw L2 score; raw maximum absolute coordinate residual; Aitchison L2 (clr difference norm); training-only locally scaled Aitchison; observed-group/Mondrian Aitchison; naive coordinatewise absolute-residual calibration at alpha; and coordinatewise Bonferroni calibration at alpha/K. All raw regions are intersected with the simplex. Finite clr regions have the positive simplex as their domain; an infinite-threshold fallback is explicitly the whole closed simplex, consistent with the analysis convention. Orthonormal ilr and clr L2 are the same region and must not be counted as distinct methods.

An eighth, explicitly oracle shift baseline is approved from the analysis owner's pre-confirmatory proposal: weighted split-conformal Aitchison using the known group-mixture density ratio (4 for group 1, .25 for group 0 in the shifted environment, unit weights for iid). Its weighted quantile includes the test-point weight as a mass at infinity. It uses generator knowledge and is not a deployable estimated-ratio competitor. Verify finite-sample construction against the permitted primary shift source, unit-weight equivalence to ordinary split calibration, test-weight/infinite-threshold behavior, and simulated shifted coverage. Compare its shifted marginal/group coverage and K=3 area with global and Mondrian Aitchison; it has no automatic arbitrary-group conditional guarantee. If exact inference cannot be implemented/checked, keep the requirement open rather than reporting an ad hoc weighted percentile as conformal.

Two source-motivated score supplements are also required using the same fitted predictor and matched fresh-core seeds: total variation TV(y,p)=0.5*sum_j|y_j-p_j| and forward KL D(y||p)=sum_j y_j*log(y_j/p_j). The latter is an asymmetric score, not a metric; p is strictly positive and zero response terms use 0 log 0=0 if included in a boundary check. Compare their iid/shift simultaneous/group coverage and K=3 area with raw L2/max and clr L2 in the existing matrix; report all cells and paired contrasts. On the three-part simplex TV is algebraically identical to raw maximum absolute residual, so verify this and do not count the K=3 duplicate as independent evidence or a new geometry. It is distinct at K=10. These comparisons respond to close permitted prior work, not a test-outcome-driven search. The seven-method core run is retained unchanged; all added scores and the oracle can be separate matched-seed supplements with their own manifests and chronology.

The predictor is a fitted clr center, not necessarily E[Y|X]. The generator favors a simple log-ratio regression model; this is a limitation and an interpretation constraint, not evidence of superiority in arbitrary data. Do not tune methods on reported test data. Record all actual seeds, training choices and generator constants in the analysis manifest.

## Estimands and uncertainty

Primary reliability: probability the entire response vector lies in the region, averaging over new training/calibration/test samples in each cell. Report overall and both predeclared group coverages, group counts, and signed deviations from nominal. Separate marginal averaging from realized-calibration conditional performance.

Also retain replication-level distributions of test-estimated coverage and their lower-tail summaries (e.g. 10th percentile and fraction below .85 at nominal .90). These are descriptive finite-test diagnostics, not certified probabilities of population conditional coverage; include binomial uncertainty for estimated proportions, and note finite-test noise. Do not infer that every realized calibration dataset is reliable from a mean near .90.

Primary efficiency at K=3: expected fraction of Euclidean simplex area occupied by the region, averaged over independently sampled X anchors from the named environment and over replications. Share candidates across methods. Retain conditional candidate-MC SE separately from variation across X/calibration/training. Zero hit counts are unresolved small-area estimates, not proof of zero area. If an efficiency contrast is near MC resolution, analysis must increase candidates for a prespecified precision check or withhold its ranking; record the choice and cost. K=10 supports coverage and clearly labeled within-geometry diagnostics, not cross-geometry area rankings.

Use independent dataset replication as the inference unit: two-sided pointwise 95% t intervals for mean metrics and paired within-replication differences. The prespecified comparisons are naive versus Bonferroni joint coverage; scaled versus unscaled Aitchison group coverage/area; Mondrian versus unscaled Aitchison group coverage/area; oracle-weighted versus global and Mondrian Aitchison under the specified shift; TV and forward KL versus raw L2/max and Aitchison coverage/area; and raw L2/max versus Aitchison area with coverage shown. Add paired iid-to-shift changes for each method. Intervals are descriptive and not simultaneous; no familywise discovery or universal superiority claim follows from many pointwise intervals. Keep all cell summaries and paired draws. Report achieved precision rather than promising an arbitrary tolerance.

## Focused checks and sensitivity

Analysis owns exact implementations and numerical validity. Required checks: rank quantile k=ceil((n+1)(1-alpha)) with infinity for k>n, continuous-score expected coverage and beta calibration variability under iid scores; ties/conservative handling; Mondrian small/empty-group whole-simplex behavior; Bonferroni nesting; clr/orthonormal-ilr equivalence and perturbation invariance; and a known analytic K=3 area case. Derivations must state their assumptions and be checked by actual computation.

After the main run, a bounded focused sensitivity will cover calibration-rank discreteness (alpha and n including an infinite-threshold case) and boundary/replacement behavior. Before running it, analysis records exact cells/seeds and transformations in a separate plan: include exact zeros in the original response, raw-method original-target coverage, the frozen positive transform T_epsilon(y)_j=max(y_j,epsilon)/sum_l max(y_l,epsilon), applied consistently to train/calibration/test, and a small fixed epsilon grid (recommended 1e-8, 1e-4, 1e-2). Report transformed-response clr coverage as transformed coverage and any original-response check under a precisely defined membership rule. Literal zeros have no ordinary clr score; no automatic zero-safe claim is permitted for direct untransformed clr membership. The explicit pullback {y:T_epsilon(y) in C_epsilon(x)} gives exact original-response membership equivalence to transformed coverage; label any copied coverage/interval as this identity rather than a new simulation, and do not claim its original-simplex area was measured. Quantify replacement sensitivity rather than merely discussing it. These checks answer scope questions, not an unrestricted search for favorable settings.

## Work division and delivery interface

| Requirement | Functional owner and handoff |
|---|---|
| Objective Brief, reviewed related work and source provenance | idea-repo; supplies context to plan/report; no delivered-path ownership needed where it cannot read paper PRs |
| Independent feasibility and threats | idea-review-repo; judgement supplied through issues/release/wiki; not replaced by the plan |
| Questions, scope, protocol, assignment of requirements/paths | story-repo; `plan/` and `.forgejo/CODEOWNERS` |
| Generator, methods, all experiments, uncertainty, diagnostics, derivations/checks, environments, seeds and run instructions | experiment-repo; `analysis/`, `results/`, optional `data/`; all quantitative paper claims trace to these |
| All figures/tables, captions, visual checks, generators and provenance | figtab-repo; `figures/`, `tables/`, `presentation/` |
| Latest official chosen conference template/rules and mandatory-form requirements | venue-repo; `venue/`; declares exact required paper/source/reproduction paths |
| Complete paper, source, integrated citations, filled author checklist, build and root reproduction overview | paper-repo; `manuscript/`, `paper.pdf`, `README.md`; it integrates supplied context and evidence |
| Independent acceptance review and outside-reader critique | internal-review-repo and external-review-repo respectively; no plan-authored judgement or substitute review |

Proposed root entrypoints are `paper.pdf`, `manuscript/main.tex`, and `README.md`, with analysis reproduction at `analysis/README.md` and visual reproduction at `presentation/README.md`. Official style assets live in `venue/`; paper owns filled checklist answers under `manuscript/`. Venue verifies the actual latest official edition, page rules and required forms; the plan does not guess them. Paper maintains the built document at delivery root for others to inspect. Its build script belongs under `manuscript/` (for example `manuscript/build.sh`), using `manuscript/main.tex` as the source entrypoint.

Main display purposes: (1) joint coverage across method/dimension/calibration/noise cells; (2) subgroup coverage and controlled-shift change; (3) common K=3 area with paired contrasts and coverage; (4) compact full-cell numeric summary. An appendix display/table supports rank and zero/replacement sensitivity plus replication variability. Presentation decides rendering using field conventions and supplied intervals, without omitting unfavorable cells from the available tables.

## Completion and revision rules

A complete study needs reviewed context, executed main and sensitivity evidence with uncertainty, all code/environment/run and figure/table mappings, explicit boundaries of generalization, full official-template paper and required checklist, and independent review. A pilot or disclosed missing evaluation does not satisfy an executed-evidence requirement. Failures remain reported with a concrete next action while resources permit. Owners supply each missing part; the plan does not replace their work. Any new requirement or path is assigned by updating CODEOWNERS through PR before its delivery merges.

Review each claim against an input/result path, an estimand and its uncertainty. Inspect the built paper, not only component files, for claims that exceed the design. An inferential conclusion is conditional on actual results and reviewer judgement. No forbidden publication or derivatives may be searched, inferred, or used; accidental exposure is recorded by the responsible position for inclusion in reproduction notes.

## Revision record

Version 1.1 adds the analysis owner's pre-confirmatory known-ratio oracle weighting baseline after its follow-up proposal was read, and clarifies the paper build-script path. This expands the shift comparison without changing the seven core methods or target. No confirmatory result has been inspected by the plan owner. Source/feasibility review remains requested.

Version 1.2 aligns the protocol with the substantive Brief (idea-repo wiki revision `db2678892f7ab35631d8f3c172d4d4d3795eb740`) and the independent core-feasibility answer in idea-review-repo#3. It adds source-motivated TV and forward-KL matched-seed supplements after the seven-method core job started; the plan owner has not inspected confirmatory outcomes. The original core matrix is preserved. The feasibility endorsement concerns v1 core scope, not a sign-off on added results or final paper quality; see `plan/input_alignment.md`.

Version 1.3 records the analysis owner's pre-run freeze choices: 8192 candidates per anchor, clipping/reclosure (rather than the earlier merely recommended additive replacement), and whole-closed-simplex infinite-threshold fallback. These are implementation alignments, not outcome-selected changes. The independent feasibility owner also endorsed the resource feasibility of the oracle and TV/KL additions in story-repo#11; exact implementation checks/results remain with analysis.

Version 1.4 clarifies chronology from the analysis owner's `analysis/notes/prior_score_supplement_freeze.md` at `2aafd349f3ec979c72b9064f55e51000c1a6de15`: the plan owner requested TV/KL for prior-work relevance without inspecting core outcomes, but analysis had inspected core/oracle outcomes when implementing/freezing the supplement. No TV/KL supplement outcomes had then been inspected. These are matched-seed, source-driven additions, not members of the original core freeze; retain that label and every original core result. No method or sample-size change follows from this clarification.

Version 1.5 records the context-aligned inverse-image qualification supplied with the completed score evidence: a transformed region pulled back through the fixed replacement map can cover original boundary responses, by exact event equivalence. This is a region-definition clarification using existing measured memberships, not a new experiment or a changed main target; direct clr membership and pullback membership remain distinct. No pullback-area comparison is supported.
