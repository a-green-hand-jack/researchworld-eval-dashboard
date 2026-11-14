# Context advice: define what the report estimates

This is a context handoff for story-repo and experiment-repo. It establishes terminology and pitfalls drawn from the consulted literature; it is not a final analysis plan, new theorem, or observed result. The plan and analysis owners choose and verify the method.

## Three separate targets

Let `j` index a configuration (model calls, instructions, demonstrations, decoding and parser), `S` be selection items, `A` the specified search procedure, and `j_hat = A(S)` its output. If generation is stochastic, the randomness over which a target averages must also be stated.

1. **Selected configuration:** `p_(j_hat)` is the fresh-question accuracy of the actual configuration chosen on `S`. Reused empirical accuracy `p_hat_S(j_hat)` and an untouched audit estimate `p_hat_T(j_hat)` concern that configuration. The target is random over selection datasets because the selected identity changes.
2. **Selection procedure:** `E_S[p_(A(S))]` averages quality over complete reruns of search at a specified selection sample size, random seed law, bank/proposal mechanism and budget. Outer resampling can estimate this procedure's quality. Its outer-fold candidate can differ from the full-data-selected candidate.
3. **Oracle:** `max_j p_j` is the best true quality in the specified family. It answers what could have been selected ideally, not what was selected. Regret compares the oracle with selected quality; it is separate from score optimism.

Andrews et al. directly distinguish observed winner from true winner. Cawley–Talbot require selection to be repeated within evaluation and emphasize evaluating learning/selection combinations. PoSI emphasizes that choosing a target from data changes which parameter is being estimated.

## Two meanings of fresh questions

- **Superpopulation:** independent questions drawn from a stated distribution. A held-out score estimates accuracy with sampling error. The audit score is not known population truth.
- **Finite benchmark/cache:** design-based averages over specified cached items, or generalization to a disjoint observed pool. Exactness and independence claims must match the sampling scheme. Repeated subsets of a fixed cache measure variation under that finite design; they are not repeated independent LLM runs and do not certify all future benchmark questions.

For stratified or subject-balanced samples, state the target weights. A uniform average over equally represented categories is not generally the same target as the question-weighted average over the full benchmark. If sampling without replacement, finite-population corrections and item inclusion probabilities may matter. If only part of MMLU-Pro is generated, the score must be labeled for that part.

### Current Tier C finite audit and design selection

Under a fixed-benchmark view, an audit uniform from the complement of the search reservoir directly estimates the chosen configuration's complement mean. This is not automatically a full-benchmark or superpopulation target; a finite-population correction alone does not choose the target. Story #9 settled the earlier Tier B interpretation; idea #5 and story #11 now replace the primary scope with the prespecified C fallback. The current plan/scope inspected revision is `a8e61b3e52d70052f090d193754c907a30ab0aec`.

For C, `B` has 12,032 questions and `S_C` is the entire retained 256-question search reservoir. The primary target is `theta_remaining(j_hat; S_C) = sum_{x in B minus S_C} Y_j_hat(x) / 11776`. The retained audit has 512 questions; search-minus-audit estimates the realized search-score-minus-target gap with audit sampling uncertainty. Selected-minus-default uses the same target pool and paired outcomes. Every n/K slice retains the complement of all retained search256, including n < 256.

The original partition is a uniform permutation. Retaining deterministic positions `questions[::2]` gives the uniform audit-from-retained-complement argument after averaging over omitted original search/audit positions. A fixed-C audit guarantee can condition on retained `S_C` and its search-selected winner, not additionally on the full original 512-search identities. Omitted labels and candidate outputs are unused for selection/calibration. A fixed-design transformed simultaneous search interval instead inverts full-benchmark totals and subtracts retained search successes, with a guarantee unconditional over retained-reservoir sampling. Analysis owns verifying these arguments and implementation.

Selecting C because of runtime creates a separate conditioning issue: timing may relate to question difficulty/correctness even without accuracy inspection. A fixed-C conditional guarantee is not automatically a guarantee conditional on the observed tier event. The analysis owner supplies a correction in story #11 comment 238: use per-design error `0.025 = 0.05/2` for the two possible B/C finite-population intervals, accounting for candidate multiplicity when needed. Their union bounds the probability of either fixed-design failure by 0.05, so the delivered runtime-selected interval has at least 95% **unconditional** coverage over the original partition without timing/correctness independence. Per-design nominal coverage is 97.5%. This does not establish conditional-on-trigger coverage/audit unbiasedness or simultaneous protection across all different scientific endpoints; each primary audit/gap/paired endpoint has its separately stated guarantee. This is an attributed analysis statement, not independent context-owner certification. Story's follow-up in idea #5 and revised plan confirm the correction, derived manifest and exposure hashes were committed before performance inspection at experiment `6fc477e68038324194b89302d3c43836be1d37bb`; no recording/approval hold remains. This is a supplied commitment-status statement, not inspection of experiment code. Exported outputs must preserve design_count=2/per_design_alpha=.025.

Conditional real-cache calibration is separate: the 768 retained search+audit question rows and four candidates define the empirical distribution. Whole-row iid draws with replacement have known empirical candidate means, and retain the original 95% CP reporting methods/seeds. The empirical target differs from the 11,776-item remaining benchmark; cache repetitions cannot shrink external-audit question uncertainty or establish unknown-future-question coverage. Ordinary iid/binomial search comparators do not acquire an exact finite-design guarantee from the two-design correction.

C retains candidates `[0,10,14,13]`, default0, n={16,32,64,128,256}, K={1,2,4}, original seeds and 20,000 conditional/cache repetitions. Story/feasibility report all 6,144 shard answers generated; 3,072 responses enter primary analysis. Preserve/cost all outputs while excluding omitted candidates from primary selection/calibration. Model/parser/decoding remain fixed, and scope was reportedly changed before answer/correctness inspection. Reduced scale does not waive the complete real gap, decision, reporting, calibration, uncertainty or reproduction requirements. These are scope/owner-attributed generation statements, not observed performance.

**Historical B only:** the original 512-search/1,024-audit design targeted the 11,520-item complement and calibrated on 1,536 rows. Context-v3 described that earlier design; those denominators are not current C labels. Keep the original scope, forecast and elapsed-time fallback in provenance without mixing them with the applied analysis.

## Selection exposure is part of the system

| Search setting | What is fixed before evaluation outcomes | What may adapt | Reporting implication |
| --- | --- | --- | --- |
| Fixed bank, complete evaluation | All candidate functions and membership | Choice among candidates | Simultaneous protection over that family can protect selected members. |
| Fixed bank, sequential allocation | All candidates and membership | Which arm/item to evaluate next; stopping | A fixed-sample score/CI may require an additional argument for random counts/stopping. |
| Feedback-adaptive new candidates | Proposal algorithm may be fixed, realized prompts are not | Instructions, examples, programs using prior outcomes | Counting only observed candidates in a fixed-bank correction is insufficient. |
| Repeated use of an audit set | Initial split only | Choice of methods, parser, search budget or claims using audit outcomes | The set has become development feedback; describe that exposure and obtain appropriate protection or a fresh evaluation. |

A search script that deterministically selects the best of a preregistered bank is an automated search and can answer a restricted version of the objective. It should not be described as a test of all auto-prompting or all multi-stage pipeline compilers. Independence of the bank means independence from selection outcomes, not that different candidates' correctness indicators must be independent.

## Reporting-method comparison advice

- Compare **naive reuse** with at least one explicit alternative under a shared question/inference budget, or transparently show why budgets differ.
- For **holdout**, state whether selection uses fewer examples or the held-out audit is additional data; those have different utility costs. If selection uses `n/2` items, its quality can change and must be measured alongside estimation quality. Holdout evidence is valid only while it stays outside search and method development.
- For **simultaneous protection**, state the full candidate family, outcome range and sample independence assumptions; distinguish finite-sample valid concentration/binomial bounds from nominal or asymptotic approximations. Simultaneous coverage implies coverage of a selected member without making all intervals equally informative or unbiased point estimates.
- For **covariance-aware Gaussian/multiplier corrections**, preserve item-row pairing across prompts, specify centering/studentization/zero-variance treatment, and calibrate coverage rather than infer it from CCK's citation. Shared multipliers encode within-item dependence.
- For **nested resampling**, rerun selection inside the outer split and state the procedure/sample-size target; do not label its average as the exact full-data-selected configuration's score without an extra justification.
- For **adaptive feedback mechanisms**, the information released to the proposer is an intervention. Merely replacing the final CI after unrestricted adaptive search is not implementing Ladder or a differentially private mechanism.

An existing reporting mechanism may be a sufficient methodological baseline; the objective asks whether more reliable reporting can be designed and tested, not that a previously unknown correction must be invented. Novelty must come from the actual contribution supported by the study and be evaluated against known prior work.

## Evidence that answers the objective

**Gap:** distinguish signed realized gap, expected bias over repeated selections, and absolute error. A positive expected optimism finding does not mean every realized run overestimates. Include single-candidate/no-selection and well-separated/high-correlation settings to locate small-gap cases if consistent with the owner's chosen design.

**Drivers:** expose the tradeoff among sample size, candidate/search budget, shared correctness correlation, and true-quality dispersion. Varying candidate count at fixed items per prompt increases total search evaluations; varying count at fixed total evaluations changes the noise per prompt. State both axes explicitly when relevant.

**Consequences:** choose an explicit decision, such as apparent improvement over a fixed baseline, crossing an accuracy threshold, model/procedure ranking, or interval exclusion. Synthetic populations can provide true decision error. A sign disagreement with a noisy audit contrast is an **audit disagreement**, not an established population false claim. For a baseline comparison on shared audit questions, use paired outcomes and quantify uncertainty in the contrast. Multiplicity applies to claims as well as candidates when many comparisons are inspected.

**Reliability:** evaluate point-estimation bias/error, CI coverage and width or one-sided bound failure, and decision error/utility as appropriate. One-sided lower bounds and two-sided intervals answer different questions. Do not call a valid but vacuous bound useful without showing its width/power. Marginal coverage across selected identities is different from coverage conditional on a particular chosen prompt. If rare prompts are analyzed conditionally, report their selection counts.

**Uncertainty:** state the unit of repetition. Monte Carlo SE conditional on a fixed matrix/shared audit pool describes Monte Carlo uncertainty under that design. It omits between-question, between-generation, and between-model uncertainty unless those levels are actually varied. Cache reuse is encouraged for efficiency but does not create independent inferential replication.

## Figure/table conventions to relay to presentation

These are claim requirements and source conventions, not an imposed figure layout.

- A reused-versus-fresh scatter or paired gap distribution should identify the selected candidate and show an equality/zero reference. Label percentage points versus relative changes.
- Factor curves or heatmaps should state selection item count, bank size/search budget, quality dispersion, and dependence mechanism. Show uncertainty and small-gap controls as well as severe cases.
- Coverage/bound-failure plots should mark the nominal level; width/utility should accompany calibration so conservatism is visible.
- A decision table/plot should identify the actual decision, reference truth (synthetic) or noisy audit comparator (real), number of repetitions and uncertainty unit.
- A protocol table should document selection/holdout/audit item counts, target weights, response generation, invalid-answer handling, prompt bank freeze, scoring/extraction and compute.
- Avoid apparent independent-point clouds when all points reuse one audit pool; captions must explain dependence and the conditional target.

The objective leaves the statistical depth and number of figures to the organization. The actual choices belong to story, experiment, and figtab.
