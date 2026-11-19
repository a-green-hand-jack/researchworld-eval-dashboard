# Self-Review

## Verdict

**Verdict: major-rework for a main-track submission; acceptance remains uncertain even after the concrete corrections.** The principal risk is limited contribution, not an invalid residual-audit theorem or fabricated headline results. The review found one reproducible evaluation defect: floating-point artifacts break theoretically exact prediction ties and change reported ranking metrics. The primary MAE results survive the arithmetic checks performed here.

**Reject-first simulation, recorded before the structured assessment:** This paper could be rejected because its estimator follows a standard finite-population identity, its learned pilot adds very little frontier MAE improvement over a fixed source-only difference estimator, and the study does not yet turn its careful implementation audit into a sufficiently distinctive main-track insight. Its own competitive Rasch and biased controls weaken a method-superiority argument. A ranking-metric inconsistency further needs correction before the evaluation can serve as the central contribution. These are reasons for skepticism, not evidence that the study is worthless or that its stated unbiasedness result is false.

**Severity-ordered findings:**

| ID | Severity | Finding | Action |
|---|---|---|---|
| F1 | High; confirmed scientific correction | Numerically broken ties change ranking metrics for a control that is exactly a common-offset transformation. | Repair ranking arithmetic/tie invariants and recompute metrics from saved predictions; no estimator reruns are needed. |
| F2 | High; venue-strength judgment | Remaining contribution may be insufficient for main track: frontier improvement over fixed stratified difference is only 0.0274 pp. | Make the incremental scientific question and evidence explicit; do not inflate algorithmic novelty or promise acceptance. |
| F3 | Medium; confirmed presentation problem | The no-audit caption can imply a cheaper-than-budget comparator, although the reported symmetrized estimator jointly uses all b labels. | State b-label total cost and b/2-label nuisance fits separately. |
| F4 | Medium; comparison gap | Related work calls nearest-source prediction an important control, but it is absent and its omission is not explained. | Explain the omission and its effect on scope; a future extension may add this source-only control, but this review ran nothing. |
| F5 | Low–medium; unsupported wording | Four decreasing budget points do not establish a frontier error floor. | Replace “error floor” with a finite-budget observation. |
| F6 | Low; reproducibility/disclosure | The promised numeric MIRT compute disclosure is missing from the manuscript, as are details of its target optimizer. | Insert the existing timing numbers and target-update settings. |
| F7 | Low; mechanical | Checklist references nonexistent Appendix I; reproduction/disclosure is Appendix H. Figure 1 lacks an explicit prose cross-reference. | Use label-based cross-references and cite Figure 1 in the results text. |

**Trust score: 8/10**, distinct from venue-strength scores: comparison fairness 1/2; reproducibility 2/2; honest limitations 2/2; failure transparency 2/2; statistical soundness 1/2. The statistical deduction reflects F1 and the limited inferential design, not an accusation of independent-bank significance claims. Those claims are explicitly disavowed.

**Scope and execution.** Draft reviewed: `/work/paper/main.tex`, with `/work/paper/appendix.tex`, `/work/paper/checklist_filled.tex`, `/work/paper/references.bib`, generated tables/figures, and `/work/paper.pdf`. Output: `/work/artifacts/paper_review.md`. Also inspected the frozen protocol, comparator amendment, relevant methods/runners/analysis/tests, and independent metric audit. Pass 1 preceded the skill checklist and script. No code interpreter was available: Pass 2 used the explicitly permitted sequential five-aspect fallback, not a claimed parallel subagent run. Pass 3 used actual read-only Python shell scans. No web access, prohibited-paper identification, manuscript edits, experiments, or experiment reruns occurred. Missing forthcoming README/final-report/archive deliverables are **not** counted as scientific deficiencies.

## Pass-1 Suspicions

These suspicions were recorded after the complete draft/PDF read and before opening the checklist. “Open” means not resolved in the unchanged draft, not that the suspicion is necessarily a demonstrated technical error.

| ID | Initial suspicion and location | Confidence after review | Evidence that would settle it; disposition |
|---|---|---|---|
| S1 | Incremental estimator/application may not clear main-track contribution threshold. `main.tex:31,108,116,154`; Table 1. | High as a venue-risk judgment, not a priority finding. | Compare with the strongest simple honest control and articulate genuinely new empirical knowledge. Exact frontier gain over stratified difference is 0.0273845 pp. **Open: F2.** No literature priority inference was attempted. |
| S2 | No-audit caption may confuse per-fit pilot size with total labels used. `main.tex:128`; `appendix.tex:60`. | High. | Trace both imputation directions. `methods.py:130–134` averages predictions fitted on opposite halves, jointly consuming their union. **Open: F3.** |
| S3 | Stronger MIRT failure may reflect calibration/model restrictions, not merely optimization status. `main.tex:108`; `appendix.tex:63–71`. | Moderate initially; no demonstrated defect in the claimed result. | Check source-only inner fitting, saved statuses, and approximation labels. All 260 source/inner fits report success; all 2,080 saved error records recompute exactly; full Bayesian reproduction/global optimality are not claimed. **Resolved as an unsupported suspicion of invalid comparison.** Why another IRT pipeline would behave differently remains outside this experiment. |
| S4 | Budget-50 honesty/bias interpretation might import evidence from repeated masks at 10/100. `main.tex:132,141`; `appendix.tex:110–121`. | Low after checking qualifiers. | Identify an actual b=50 design-bias claim. The paper expressly denies one; Table 2 calls its statistic signed frontier error rather than design bias. **Resolved; do not demand a nonexistent missing experiment to support a claim not made.** |
| S5 | Theorem, sampler feasibility, and seed namespaces may not match. `main.tex:69–84`; `appendix.tex:2–35`. | High that conditions matter; no observed failure in this grid. | Inspect pilot-only fitting and saved masks; distinguish ideal randomization from a five-seed schedule. All actual budgets/folds passed checks; the finite-PRNG qualification is explicit. **Resolved for the stated ideal-design claim.** General sampler guards and conditional IID randomization are not thereby certified. |
| S6 | Fixed item offset should preserve ranks, yet tables report different correlations. `appendix.tex:48`; Tables 1, 5–6. | High; directly reproduced. | Compare paired saved predictions and exact ties. Offset variation is at floating-point precision; ties are nonetheless split by exact comparisons. **Open: F1.** |
| S7 | “Frontier error floor” overstates finite-budget evidence. `main.tex:113`. | High. | A limiting argument or broader asymptotic evidence would be needed; neither is supplied. Existing errors decrease from 11.57 to 5.99 pp. **Open: F5; simple wording repair suffices.** |
| S8 | MIRT cost promised but not numerically disclosed; checklist appendix references stale. `appendix.tex:144`; `checklist_filled.tex:53,118,220`. | High. | Search the complete manuscript and compare saved timings/section labels. The numbers exist in JSON but not in the manuscript; actual reproduction section is H. **Open: F6–F7.** |
| S9 | “All configurations” in Figure 1 caption may promise all-budget appendix tables. `main.tex:113`; `appendix.tex:78–88`. | Low after disambiguation. | All configurations are tabulated at b=50; the budget table contains six methods, with fuller machine-readable outputs. **Resolved under the narrower, natural reading.** “All configurations at b=50” would remove ambiguity; not a missing-grid finding. |
| S10 | Split description alone cannot establish absence of target leakage. `main.tex:86–100`; `appendix.tex:44,69`. | High as an audit requirement. | Trace every estimator call and inner-validation fit. Current code passes source responses and queried target slices; inner validation is excluded from MIRT item fitting/preprocessing. **Resolved by static inspection; historical absence of target-driven tuning is not independently certified.** |

Five suspicions remain open: S1, S2, S6, S7, S8.

## 5-Aspect Findings

### Contribution — 2/5

**F2: distinguish a sound study from a sufficiently strong main-track contribution.** Locations: `main.tex:31,41,108,116,132,149,154`; `tables/main.tex:8,13,16`; independent audit §6.

The proposition is a short conditioning argument for a standard identity, and the paper already says so. A capable specialist could derive the construction quickly. That is not an error or a novelty misrepresentation. It does mean that the contribution must rest on the information-boundary diagnosis and empirical insight, not on presenting the estimator itself as technical depth.

The strongest local comparison is not just SCFD versus uniform. At b=50, fixed stratified difference already gives 3.914657 pp IID and 3.830210 pp frontier, versus SCFD's 3.765808 and 3.802826. The learned-pilot increment is **0.148850 pp IID and 0.027384 pp frontier**. Rasch is better in both regimes (3.742502/3.757393); contaminated correction gives 3.57/3.71 in the displayed table. These are not hidden losses, but they make “why this additional estimator?” the hard question.

**Proposed fix:** explicitly promote the near-equivalence to fixed stratified difference into the main results and organize the contribution around the controlled answer to “what does residual honesty buy, and what does it cost?” Use the already saved matched-fit diagnostics to distinguish a label-access guarantee from point-prediction utility. No amount of careful wording alone guarantees that this scope clears a main-track novelty/insight threshold. Restricted literature access also prevents an exhaustive priority judgment; this review neither searched nor inferred excluded work.

Promise–delivery check: the honest estimator is delivered in §3/Appendix A; the pinned-code distinction in §3.1 and equivalence tests; the controlled study in §5/Appendices E–G. The conclusion preserves the estimator-study message, though it does not specifically echo the pinned-implementation finding. No major promised contribution disappears.

### Clarity — 4/5

**F3: correct total-cost interpretation of the no-audit ablation.** `main.tex:128` says it “uses only each pilot for prediction, despite being shown beside a b-label system.” Per-direction pilot-only fitting is true; the implied aggregate cost comparison is misleading. `methods.py:130–134` returns `(i1+i2)/2`, and each half is the fitting set in one direction. The reported estimator therefore depends jointly on all b queried labels.

**Proposed replacement:** “All displayed SCFD variants use the same b-label union. In no-audit, each nuisance fit uses only its own half; their two population-imputation estimates are averaged without residual auditing.” This strengthens, rather than weakens, the matched-label comparison. It does not turn no-audit into an unbiased estimator.

**F5: remove the unsupported floor language.** `main.tex:113`, Figure 1 caption. Frontier score-ridge MAE is 11.57, 8.73, 7.51, 5.99 pp at 10/25/50/100 items (`tables/budgets.tex`). These observations show persistent error over studied budgets, not a limiting floor. Replace with “remains substantially less accurate on frontier targets over the studied budgets.” No new experiment is necessary.

**Reverse outline:** Introduction: evaluation cost → distinct prediction assumptions → honest finite-population construction → deliberately narrow contribution. Method: estimand → same-sample intercept degeneracy → pinned-code discrepancy → strata/folds → complement correction → guarantee and non-guarantees. Results: split dependence → selection contribution → failures/ranking → honesty ablations → repeated masks → sensitivities/compute. This is coherent. The method's modules are motivated, not just listed. Related-work and access-provenance qualifications are lengthy but understandable; shortening them is optional, not a scientific repair.

F7's stale references are detailed below. The main text is otherwise technically reconstructible from its equations and appendix.

### Results — 3/5

**F1: exact-comparison rank metrics are sensitive to numerical tie splitting.** Locations: `src/methods.py:82–89`, `src/run_experiments.py:17–26`; `appendix.tex:48,108`; `tables/main.tex:5,7`; `tables/all_frontier.tex:5,7`.

With shared uniform queries,

`item_difference(target) = uniform(target) + mean(d) - mean(d[queries])`.

The added quantity is identical for every target. Therefore all ordering metrics, including their predicted ties, should agree exactly. The paper states this invariance in Appendix C. The implementation instead averages itemwise floating-point residuals, introducing target-dependent roundoff. SciPy ranks and the pairwise `np.sign` computation then treat tiny nonzero differences as real orderings. The `1e-14` standard-deviation guard only detects nearly constant vectors; it does not protect ties inside nonconstant vectors.

**Direct saved-output evidence:** Across 130 primary b=50 cells, the maximum range of `(item_difference − uniform)` is only **6.66134e−16**, yet **111 cells** split at least one uniform tie, totaling **9,237 tied target pairs**. The maximum cell-level absolute changes are 0.01696 in Spearman, 0.03381 in Kendall, and 0.01186 in pair agreement. Example: `/work/artifacts/runs/arc_challenge__frontier__s0.npz`, group-representative target-array positions 4 and 22, has uniform predictions `(0.62, 0.62)` but difference predictions `(0.6209745164960183, 0.6209745164960182)`.

This explains the frontier macro discrepancy: uniform/item-difference Spearman **0.6638477/0.6628456**, Kendall **0.5184843/0.5140720**. It is a genuine evaluation inconsistency, not a contradiction in the offset identity. The earlier independent audit reproduced metrics but did not catch this semantic invariant failure.

**Proposed fix:** compute known common-offset controls in an invariant-preserving form, add a rank-equivalence assertion for these controls, and use a documented roundoff-aware tie policy where numerical solvers or summations can perturb mathematical ties. Avoid arbitrary jitter or an outcome-selected tie threshold. Audit the same issue for stratified offsets and other algebraic equivalences. Recompute ranking summaries from existing saved predictions under the documented policy; this is postprocessing, not experiment rerunning. State whether any substantive ranking conclusions change. **Do not discard the MAE findings or assert that SCFD's ranking conclusion reverses: this review did not establish either.**

The error claims are otherwise well supported. Absolute 3.8 pp MAE is not sufficient evidence for resolving small leaderboard differences, and the paper appropriately makes no such deployment claim. Figures show real effects but also close competing curves; suppressing that overlap would be worse presentation.

**Figure/table checks:** inspected rendered PDF figures, not just LaTeX declarations. Plots are legible vector graphics with clear units; Figure 2 has a meaningful zero reference; Figure 3 correctly distinguishes 2-MCSE bars from population intervals. The palette does not depend on a red-versus-green contrast. Tables use booktabs, no vertical rules, captions above, and defined units/directions in the main caption. No best values are bolded, so there is no incorrect bold-best claim; restrained highlighting would help navigation but is optional. No pipeline/teaser figure is required to validate this simple estimator. F7 covers cross-reference omissions.

### Testing — 4/5

The actual evidence is substantial for this narrow setting: 130 primary cells × 17 original configurations × four budgets; 65 gap cells; 130 additional MIRT cells with two estimates per budget; matched fit/design ablations; 200-mask panels; group/row sensitivity; score and rank metrics; and visible failures. Neither the gap nor MIRT grid is unfinished. Full Bayesian/learned-acquisition pipelines are explicitly excluded and adaptations are clearly labeled. It would be unfair to report “missing SOTA reproduction” as an undisclosed fatal flaw.

**F4: the nearest-source control has a more specific omission problem.** `main.tex:35` itself calls nearest-source prediction an “important control,” but no such row appears in `tables/main.tex` or `tables/all_iid.tex`/`all_frontier.tex`, and `run_experiments.py:64–89` does not implement it. Unlike confidence features or adaptive RL, a simple queried-signature nearest-source control can use information available in this matrix-only setting.

**Proposed fix:** explicitly explain its omission and acknowledge that the comparison does not exhaust even simple source-trained decoders. If extending the study later, specify the queried-distance and tie rule without target-error tuning, and preserve the frozen primary endpoint. This is a completeness weakness, not grounds to say the existing comparisons are fake or the point estimates are wrong. No new run was performed or required by this review.

Existing tests cover sklearn/pinned class equivalence, residual identity, tiny-population enumeration, duplicate split separation, hidden-label invariance, and endpoint Rasch behavior. They do not cover the F1 metric invariant or the full general sampler input contract. The manuscript reports the initial nine passed tests; I inspected them but did not rerun them. At b=25, equal half-averaging of unequal folds is a valid prespecified choice, not a missing ablation or a theorem counterexample.

### Method — 4/5

The ideal-design argument is sound under the stated assumptions. For fixed pilot and learner randomness, the audit's inclusion probability is `a_h/(N_h−p_h)`. Consequently its mean residual is unbiased for the **pilot complement**, and multiplying by `N_h−p_h` cancels that complement's predicted total. This proves the directional conditional expectation is the fixed population mean. The swapped direction has the same marginal expectation; their fixed half-average is unbiased even with unequal folds. No independence between directions is needed for that expectation.

`appendix.tex:2–33` handles integrability for randomized learners, audit-membership isolation, conditional stratum variance, the census/singleton-complement boundary, and the covariance between directions. The variance uses complement residual variance and the appropriate finite-population correction. A finite deterministic ridge fit on this finite sampling space satisfies the moment requirement. The intercept normal equation makes total in-fit residual zero, so §3.1's algebra/interpretation is correct. Absence of unbiasedness guarantees for same-sample fitting is not itself proof of bias in every population; the draft does not need that stronger claim.

`methods.py:101–134` matches the honest equation: pilot-only centering/fitting; fixed source covariate totals; stratum pilot-complement weights; swapped refitting; fixed averaging; no clipping. The contaminated and imputation returns are correctly outside the theorem.

A finite seed list is not the ideal sampling distribution. Split seed `1000+seed`, query seeds `20000+seed`/`30000+seed`, and calibration seed `6021+seed` are distinct namespaces but not a proof of independent randomization conditional on an IID split. The manuscript explicitly limits its guarantee rather than hiding this issue. Saved budget compliance is not a universal feasibility contract for future sampler inputs. These are real boundaries, but **not newly discovered invalidity of the stated proposition or observed grid**.

## Protocol Audit & Mechanical Scans

### Protocol reconstruction and leakage audit

| Stage | Information used and fitted objects | Verification and interpretation |
|---|---|---|
| Data/split | All binary rows for response-equivalence groups; full group scores for frontier/gap split only. IID sources are 70% of groups; frontier uses complete score-tie boundaries; gap reduces sources to approximately bottom 50%, retaining the approximately top-30% targets. | `common.py:21–43`; `main.tex:86–90`. Oracle score use is disclosed retrospective split construction, not an inference-time feature. Exact groups do not establish family independence. |
| Source features/acquisition | Original source-row multiplicities; item difficulty, five strata, source correctness covariates; source-only anchors and Rasch/MIRT parameters. | `methods.py:13–34,137–190`; `run_experiments.py:46–61,81–85`. Full-bank **source** covariates are legitimate transductive information. Repeated columns/constants are retained, not secretly filtered. |
| Score decoder | Source model rows as observations, queried responses as features, source full means as labels; RidgeCV penalties 0.1/1/10. | `methods.py:62–66`. No outer-target score enters fitting or penalty selection. Distinct from item-regression orientation. |
| Target-item predictor | Observations are queried items; predictors are source responses; labels are only queried target values; penalty 10. SCFD uses each pilot alone and audits the disjoint complement sample. | `methods.py:37–59,69–79,101–134`; runner slices at lines 61–79. Audit membership is used for evaluating residuals, not for fitting the directional nuisance. |
| Additional MIRT calibration | Inner source-group 80/20 split; only inner training rows determine spectral preprocessing/item fit. Validation full scores determine a source-only mixture weight; final item parameters refit on all outer sources. | `irt_comparator.py:60–83`. The reused query context is uniform/source-independent. No outer target enters calibration. The mixture formula uses squared validation MAE as a heuristic, not a claimed optimal MSE blend. |
| Evaluation | Evaluator retains full target means, group representatives, and row sensitivity. Metrics aggregate within bank, then equally across banks/seeds. | `run_experiments.py:46–53,90–99`; `analyze.py:61–77`. Full labels are owned by the evaluator, not passed to predictor functions. |
| Uncertainty/diagnostics | Seeds averaged within bank before bank bootstrap/sign flip; Holm across four contrasts. Fixed-source diagnostics share each new mask across six targets and methods. | `analyze.py:94–110`; `diagnostics.py:16–49`. Mask-level MCSE retains shared-target covariance; descriptive bank dependence is explicitly acknowledged. |

**Comparison fairness:** same matrices/splits, explicit uniform/stratified/anchor acquisition tracks, matched label counts except the labeled 2b reference. Baseline numbers are newly generated under this setup, not copied from incompatible published experiments. Source-only RidgeCV versus fixed target-ridge penalty is disclosed, as are the changed effective regularization with smaller pilots and post-primary MIRT amendment. This is not evidence of equal global tuning optimality, nor does the paper claim it.

**Assumption inventory:** full historical source responses; fixed finite-bank estimand; source-defined strata; feasible positive pilot/audit quotas; uniform complement auditing; pilot-information measurability; learner moment conditions; unbounded/unclipped final scores; retrospective score-defined stress; non-independent banks/model pools. Each is stated and revisited. The theorem needs neither item-label independence nor source/target exchangeability. No unexplained inference-time oracle signal or hidden-label leakage was found in the current code. Current files/logs cannot prove historical absence of outcome-driven decisions; the amendment and frozen protocol provide disclosed provenance rather than an independently timestamped preregistration certificate.

### Executed numeric checks

All computations below read saved outputs; none fit estimators or generate query experiments.

- Enumerated **195 original run JSONs**: 130 primary + 65 gap; **19,890** records including group/row weighting. Primary group records are exactly **8,840 = 13 × 2 × 5 × 4 × 17**. No duplicate record keys.
- Checked saved unique query counts and pilot/audit disjoint union contracts for **520 primary and 65 gap budget cells**: no violations.
- Checked **611 rendered numerical fields** across main/ablation/all-results/budget/row/per-bank/gap tables and prose macros against current summaries: no mismatches. Checked 60 additional diagnostic/effect fields. One 0.01-pp CSV-rounding apparent discrepancy was resolved against original JSON: GSM b=100 uniform bias is 0.08500000000000227 pp, correctly rendered +0.09, not a manuscript error.
- Rebuilt all four primary effects from raw saved metrics, including 10,000-draw bank intervals, all 2^13 sign flips, and Holm adjustment: **maximum discrepancy 0.0** against `primary_effects.json`.
- Independently recomputed all **2,080 added-MIRT group/row error records** from saved predictions/truth: maximum MAE/MSE/RMSE/signed-error discrepancy **0.0**. Verified **130 cells, 260 source/inner fits, zero non-success statuses**, maximum 474 iterations. All statuses stop on relative objective reduction; the largest saved gradient infinity norm is about 1.985. This is consistent with the manuscript's numerical-status caveat, not proof of a global optimum or an undisclosed nonconvergence count.
- Recomputed all **88 repeated-mask records** from eight saved prediction panels: maximum checked metric discrepancy **2.78e−17**; maximum `MSE − within-target variance − targetwise empirical bias²` residual **2.75e−17**. Mask-level bias MCSE arithmetic agrees. No budget-50 repeated-mask bias experiment was inferred.
- Examined all 130 primary b=50 uniform/fixed-difference saved prediction pairs: F1 above. This is a semantic check beyond reproducing a summary column.
- Used the existing independent audit as corroboration for its broader summary/two-bank raw-truth checks; its older exclusion of then-unfinished IRT is **not** evidence that the now-complete comparator is missing.

Selected verified contrasts, percentage points:

| Quantity | IID | Frontier |
|---|---:|---:|
| SCFD MAE | 3.765808 | 3.802826 |
| Uniform MAE | 4.481279 | 4.401990 |
| SCFD − uniform | −0.715471 | −0.599164 |
| Relative MAE reduction versus uniform | 15.9658% | 13.6112% |
| SCFD − stratified mean | −0.217988 | −0.125194 |
| SCFD − fixed stratified difference | −0.148850 | −0.027384 |

Simple stratification accounts descriptively for about **69.5% IID / 79.1% frontier** of the SCFD-versus-uniform MAE reduction; this is an arithmetic decomposition, not a causal mediation estimate. Frontier SCFD beats uniform in 11/13 banks, losing BBH/GSM. The four adjusted sign-flip values reproduce as 0.0009766, 0.0021973, 0.0371094, 0.0515137. Their dependence qualifications are accurate. Bootstrap endpoints excluding zero and a sign-flip p above 0.05 are not contradictory constructions.

### Mechanical findings and passes

**F6 — comparator reproduction details and compute.** `appendix.tex:67–71,144` specifies source MIRT optimization well but omits the target Newton cap 60, step-norm limit 2, and stopping threshold 1e−7 (`irt_comparator.py:40–52`). Its target loop does not save a convergence status; the “260 fits” count correctly refers to source/inner fits only. Do not expand that count into a target-optimizer certificate. Add the target settings, and retain this distinction.

The phrase “The supplement reports the stronger multidimensional fitting time separately” (`appendix.tex:144`) has no corresponding numeric manuscript disclosure. Existing outputs provide **569.516 s stage wall time** (`artifacts/irt_summary.json`) and **3,840.551 summed worker-cell seconds = 64.009 cell-minutes** (`analysis/irt_integrity.json`), including calibration/scoring overhead. These are not pure optimizer-only seconds. Insert these measured values with the correct definition; do not present the original grid's 9.1 cell-minutes as total study compute. This is a manuscript disclosure repair, not criticism of a forthcoming README.

**F7 — navigation.** `checklist_filled.tex:53,118,220` says Appendix I, but the reproduction/LLM disclosure is Appendix H (PDF pp.16–17). Use `\ref{app:repro}` rather than hard-coded letters. A source search also finds no prose `\ref{fig:budgets}`; explicitly cite Figure 1 near its interpretation (`main.tex:108–116`). Several appendix tables are addressed through section references rather than individually; improving navigation is optional, not a missing-results accusation.

**Passed mechanical scans:** all seven cited keys have matching entries; no unused bibliography entries, unresolved LaTeX references, duplicate labels, missing input/figure assets, or TODO/FIXME/TBD markers in the reviewed manuscript/bibliography sources. Local bibliography entries contain authors/title/year and venue or arXiv status; external metadata was not revalidated. No non-allowlisted citation was added or researched. Compile logs show only `h`→`ht` float-placement warnings among the scanned warning categories, not missing citations or overfull boxes. Root `/work/paper.pdf` and `/work/paper/main.pdf` are byte-identical. The PDF has 24 pages; references begin on page 9, hence eight content pages. Anonymous submission formatting is present. No obvious identity leak was found in the reviewed text, which is not a certification of all future release contents.

The **six distinct protocol/mechanical findings** are F1, F3, F4, F5, F6, F7. F2 is the separate contribution-strength judgment. Already disclosed independence, oracle-split, incomplete-pipeline, licensing-provenance, and calibration boundaries are not counted again as fabricated defects.

## Blocking Issues

1. **B1 — repair F1 before relying on the rank tables.** Exact-order metrics currently reward/penalize machine-precision perturbations of mathematical ties. Recompute from saved predictions using a documented invariant-preserving approach, add the common-offset rank check, and verify the ranking narrative afterward. The error/MAE evidence is not blocked by this issue.
2. **B2 — resolve the main-track case for F2.** The manuscript is honest about limited novelty, but honesty is not sufficient venue contribution. Make the fixed-control near-equivalence and actual incremental knowledge central, and obtain a substantive assessment of whether that study contribution is strong enough. This is a high-confidence acceptance risk, not a provable scientific falsity and not an instruction to invent gains or tune after outcomes. A narrower venue remains a reasonable outcome.

F3–F7 should also be corrected or explicitly scoped before submission, but do not independently require a new experiment. No claimed independent-bank significance, SOTA claim, missing-yet-finished MIRT run, or missing future handoff archive is used as a blocker. The score-based verdict is major-rework because contribution is 2/5, not because all experimental results are invalid.

## Prebuttal Notes

- **“This is standard survey estimation.”** Agree; the submission's defensible contribution is the target-label information boundary, pinned-code distinction, and controlled trade-off study. State the tiny frontier increment over fixed stratified difference. Do not suggest the standard theorem alone settles novelty.
- **“It barely improves, and biased controls win.”** Correct. IID score decoders, Rasch, and contaminated correction remain competitive or better. The guarantee is a design expectation, not lower finite-budget MAE or better ranking. Explain when that guarantee is useful without asserting unmeasured deployment utility.
- **“Ranking results are numerically inconsistent.”** The current draft does have F1. Fix it and disclose the postprocessing correction before making this response; a prebuttal cannot make an unfixed defect disappear.
- **“No-audit is not budget matched.”** The reported symmetrized no-audit output actually uses all b labels across its two fits. Correct the caption, explain per-fit versus total label use, and keep its lack of an honesty guarantee explicit.
- **“You leaked full target scores.”** Full responses define exact duplicate groups and retrospective frontier/gap splits, and are used by the evaluator. Current estimator call paths receive only queried target slices. This answers the direct label-access question, not ancestry leakage, temporal validity, or historical tuning provenance.
- **“Your uncertainty assumes independent banks.”** Numerical resampling/sign-flip summaries are reproduced but explicitly descriptive; shared model pools prevent confirmatory population interpretations. Do not defend Holm as a cure for dependence.
- **“The stronger IRT failed to converge / full published systems are missing.”** All 260 source/inner fits have numerical success statuses, with no global-optimum claim. The comparator is a point-estimate, source-calibrated adaptation; full Bayesian and learned-acquisition reproductions remain outside scope. Give its measured cost and target settings. Separately explain the nearest-source omission rather than bundling it with infeasible feature-based baselines.
- **“The repeated-mask plot proves zero bias.”** It does not. The theorem supplies ideal-design unbiasedness; the six-target 200-mask panels measure finite Monte Carlo behavior at 10/100 queries. Preserve targetwise squared-bias/noise and shared-mask qualifications.

**Counterintuitive actions recommended, not performed:** delete “error floor”; promote near-equivalence to fixed stratified difference; retain negative results and descriptive inference; fix the real rank defect rather than calling it a limitation. None of these requires identifying an excluded paper, editing outcomes, or conducting another experiment during this review.
