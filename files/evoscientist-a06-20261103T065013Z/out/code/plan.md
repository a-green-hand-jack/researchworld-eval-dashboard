# Precommitted plan: prompt-selection optimism and honest reporting

**Status:** design only; no implementation, endpoint calls, data download, outcome inspection, web search, or literature/paper identification. Prepared 2026-11-03. Freeze this document and a machine-readable manifest before collecting scored responses. Use the `paper-planning` rejection-first and ablation-first workflow. No prior relevant observation memory was found.

## 1. Assumptions, scope, and narrow contribution

**Question.** How optimistic is the score of the best of a small, fixed set of prompts when selection and reporting reuse the same finite evaluation sample? Which reporting procedures remain defensible, and at what precision cost?

**Smallest defensible contribution:** an estimand-explicit, paired evaluation of winner-score optimism and interval failure, with a finite-pool-valid audit reporting recipe and a characterization of when correlation-aware approximate intervals are useful or fail. This is a focused statistical case study, not a new general selective-inference theorem or a claim to have invented sample splitting, simultaneous inference, or the winner's curse.

- One endpoint model, eight frozen prompts, one pinned MMLU-Pro revision; 600 cached items by default. No model training, GPU, adaptive prompt search, search over models, or benchmark-wide prompt optimization claim.
- Provider strings such as `gpt-5.6-luna` are **unverified endpoint labels**, not authenticated model identities. Do not infer architecture, parameter count, training data, or capabilities. Use the endpoint's default documented reasoning setting, fixed for all prompts, if any; record it.
- Unit of observation is a question with its entire vector of prompt outcomes, not an individual prompt-answer pair. Prompt outcomes on the same item are dependent.
- Freeze a deterministic scoring/parser policy and cache one response per item-prompt pair. The empirical target is the resulting fixed response table. Even temperature zero does not establish deterministic generation. Generalization over fresh generations, unseen questions, providers, or training-contamination-free knowledge is out of scope.
- Replays of the same cache estimate a **conditional resampling distribution**, not 2,000 independent real benchmarks. Monte Carlo precision does not measure dataset-selection or provider uncertainty.
- No attempt will be made to find, reconstruct, or infer any forbidden existing paper. Novelty remains unverified; no novelty-by-absence claim.

### Rejection-first risks and planned responses

| Likely rejection | Design response / claim restriction |
|---|---|
| This is standard winner's curse, not a new method. | Claim a reproducible, finite-pool-aware measurement and reporting study; separate known guarantees from approximate engineering. A technical note is an acceptable outcome. |
| A held-out finite pool is not population truth. | Separate synthetic known probabilities, exact cached-cohort quantities, and sampled audit references. Never present audit-reference agreement as population coverage. |
| Wilson is invalid for stratified sampling or post-selection; bootstrap is not automatically honest. | Use unweighted uniform within-cohort replay sampling; label Wilson and multiplier intervals approximate. Include exact hypergeometric audits and simultaneous Hoeffding as guaranteed baselines under stated designs. |
| Prompt dependence, ties, and near-constant outcomes destroy the proposed benefit. | Predeclare correlation, exact-duplicate, small-n, high-accuracy, and tie stress tests. Publish degeneracy and undercoverage, not only narrower intervals. |
| Post-hoc benchmark/model/prompt choices produced the story. | Freeze item IDs, prompts, parsing, seeds, metrics, budgets, and all grids before correctness summaries. No replacements based on outcomes. Publish null findings. |
| Claimed gain is just a different estimand or test-set reuse. | Define fixed-configuration versus search-algorithm targets below; isolate a final one-shot audit and never use its outcomes to choose a reporting rule. |

### Target ledger: do not combine these estimands

Let Y_ij be the cached binary correctness of prompt j on cohort item i, N the cohort size, K=8, S a uniform selection subset of size n, and J the highest sample-accuracy prompt, with ties broken by lowest frozen prompt ID.

1. **Selected configuration, finite cohort:** mu_j = N^-1 sum_i Y_ij, with target mu_J after selection. The full cache makes this finite quantity available to the diagnostic evaluator, not to the selector. Primary finite-cohort optimism is O_pool = mean_S(Y_J) - mu_J.
2. **Selected configuration, unselected remainder:** mu_R,J = (N-n)^-1 sum_(i not in S) Y_iJ. Its target changes with S. Selection-versus-audit gap estimates O_rem = mean_S(Y_J) - mu_R,J, not O_pool. Exactly O_rem = N/(N-n) O_pool. Plot or report this conversion rather than silently changing targets.
3. **Selected configuration, synthetic population:** p_J, where p_j are known Bernoulli marginals. This supports actual repeated-sampling population-coverage measurements. Synthetic optimism is mean_S(Y_J)-p_J.
4. **Search-algorithm performance:** E_S[p_J(S)] or its finite-cohort analogue. This averages over training/selection datasets. Nested CV estimates a version of this different target; it is not a confidence interval for the particular final winner. Nested CV is not a primary method here. If ever added, report its training-size-dependent estimand separately and do not use it to claim coverage for mu_J.

The selected j is fixed when conditioning on selection history; it is random across replay repetitions. All interval coverage evaluations must name the target in the same row.

## 2. Frozen design and evaluation protocol

### Data and prompt population

- Dataset: real `TIGER-Lab/MMLU-Pro`, Hugging Face revision **b189ec765aa7ed75c8acfea42df31fdae71f97be**. Verify repository, available splits, schema, and revision resolution before use. Use the official test split only; no validation/test merging and no few-shot examples in the primary design.
- Draw N=600 items stratified approximately in proportion to test-category counts, with at least two per available category; use a frozen seed and deterministic largest-remainder allocation after minimum quotas. Freeze the eligible frame, counts, IDs, raw-record hashes, and allocation algorithm. This builds a broad cohort; **the primary target is uniform microaccuracy on that cohort**, not a weighted estimate of full MMLU-Pro accuracy or category macroaccuracy.
- If a verified worst-case price/throughput calculation makes N=600 infeasible, choose N=320 **before any scored response** and freeze the change. Do not reduce n or change prompts based on observed accuracy. If neither is affordable, stop at synthetic-only results and mark the empirical stage uncompleted.
- Eight zero-shot templates form a frozen 2x2x2 factorial: neutral versus subject-expert framing; direct instruction versus option-elimination instruction; final-answer-only versus short explanation followed by final answer. All end with an identical required final marker `ANSWER: <letter>`. The first prompt is neutral/direct/answer-only and is the immutable baseline. Fix complete strings and ID order in the manifest before generation. Do not pretend the wording factor measures hidden reasoning.
- Primary K=8. Assign IDs 1-8 in binary factorial order: neutral/expert is the fastest-changing factor, then direct/elimination, then answer-only/explanation. Freeze nested ablations as K=1: {1}, K=2: {1,8}, K=4: {1,4,5,8}, K=8: all. Smaller subsets balance factors where possible but still change composition: real-data K contrasts are case studies, not an isolated causal effect of K. Synthetic grids isolate K. K=16 is synthetic-only, not a trigger for more API spending.
- Same question/options, option ordering, model label, decoding settings, reasoning setting, and token ceiling across prompts; request temperature zero if supported, otherwise record the omitted/default setting. Retain all available answer choices, not a hard-coded four-choice assumption. Do not send gold labels, explanations, `cot_content`, or other solution fields to the endpoint.

### Freeze and audit access

Before scored cohort response collection, freeze hashes for this plan, dataset manifest, eight templates, scorer specification, model/decoding settings, seed namespaces, replay selections, simulation grid, final demonstration split, and cost ceilings. Use master seed 20261103 with separate deterministic namespaces: cohort=2201, simulation=1101, replay=3301, final audit=4401, multiplier=5501, and request order=6601; record the exact PRNG and seed-derivation convention. Any amendment gets a dated version and reason; outcome-aware amendments are exploratory.

Keep two empirical views:
- **Diagnostic view:** the completed cache is available to the evaluator to compute finite-cohort targets and 2,000 replays. Each replay's selector sees only its selection rows.
- **Final demonstration view:** separate precommitted seed; reveal only n=64 selection rows to the selection/reporting process, freeze its winner and reporting rule, then unseal m=128 audit rows sampled from the remainder. The evaluator may have the cache, but access separation must prevent leakage to the selector. If this cannot be enforced, call it a replay illustration, not a prospectively untouched audit. No second winner or final-report revision after audit.

### Splits and replay sampling

For each of 2,000 frozen random permutations of the N rows, use the first n rows for selection and the next m for audit. Evaluate n in {16,32,64,128}; primary audit size m=128. Reuse permutation seeds across n and methods for paired comparisons. Different n settings can overlap within a permutation; no claim of independent cells. Within a cell the audit and selection items are disjoint.

The audit is uniform without replacement from the remaining N-n items, **conditionally on S and the full selection history**. It is not an independent draw from the original finite cohort. This distinction drives the exact reporting construction below. Do not impose per-category replay quotas: they would change the variance and binomial/hypergeometric models. Small-n category imbalance is a real small-benchmark phenomenon and is reported descriptively.

### Primary metrics, fixed before outcomes

Primary empirical cell: N=600 (or frozen N=320 fallback), K=8, n=64, m=128. Primary synthetic cell: K=8, n=64, m=128, p0=0.70, zero true gaps, latent correlation rho=0.5. All grid cells are reported, not selected after inspection.

1. **Mean selection optimism**, in percentage points: mean over repetitions of O_pool in the cache and O_pop in simulations. Also report standard deviation and Monte Carlo SE. Selection-minus-audit gap and O_rem are separately labeled secondary quantities.
2. **95% accuracy-interval coverage (M0-M4)** of mu_J (finite cohort) or p_J (synthetic population), accompanied by interval width and Monte Carlo uncertainty. Audit-only remainder coverage appears in its own column. M5 coverage is assessed against the corresponding paired difference, never against accuracy, and is tabulated separately.
3. **Mean interval length**, plus median and 90th percentile; always read together with coverage. Do not rank methods solely by width or select a method after seeing empirical coverage.
4. **False promotion probability** for the honest paired audit decision: lower confidence bound for selected-minus-baseline accuracy >0 when the corresponding true difference <=0. Report unconditional false promotions and the frequency of truly nonpositive comparisons separately; the all-equal synthetic case is the primary type-I check. Self-selection of the baseline yields exactly zero difference and no promotion.

Secondary: selection frequency, tie rate, synthetic selection regret max_j p_j-p_J, paired error correlations, discordance counts, output/transport failure rates, cost/tokens/latency, and audit-based estimator RMSE. Do not reinterpret category-level summaries as powered confirmatory results.

Uncertainty convention: binomial Monte Carlo intervals for coverage rates; MCSE for replay means; paired MCSE for method differences. At R=2,000, coverage near 0.95 has MCSE about 0.49 percentage points (about +/-0.96 points for a 95% Monte Carlo interval). Reusing a cache permits these **conditional Monte Carlo** errors, not population confidence intervals. No minimum nonzero optimism is required for a successful study.

## 3. Reporting methods, guarantees, and checks

All intervals are two-sided 95%, clipped to their parameter support. Baseline comparisons use their own predeclared 95% paired interval; a collection of separately reported claims is not automatically jointly covered. For the final demonstration's two headline claims (accuracy and baseline difference), allocate alpha=0.025 to each, giving joint coverage at least 95% by a union bound. No such joint claim is attached to the exploratory plots of many n/K cells.

### M0: naive winner Wilson

Compute the usual Wilson interval from the winning selection column, ignoring selection. This is an intentional failure baseline. It has no finite-sample post-selection guarantee, and even K=1 Wilson is approximate. In the finite cohort, lack of finite-population adjustment is another separate effect. K=1 and equal/duplicate-prompt ablations isolate those effects.

### M1: simultaneous Hoeffding, selection only

For every j, use [mean_S(Y_j) +/- r], r=sqrt(log(2K/alpha)/(2n)); report the interval for J. A union bound gives simultaneous finite-sample coverage for independent bounded item vectors, regardless of dependence between prompts. The same bound is conservative-valid for uniform sampling without replacement from a fixed bounded finite cohort. Thus it covers mu_J in the real replay and p_J in the iid synthetic setting. No finite-population correction is silently applied to this bound. Record clipping and near-vacuous widths, especially at n=16.

### M2: correlation-aware multiplier, approximate

Resample one mean-zero unit-variance Gaussian multiplier per selection **row**, shared across all prompt columns. Center each column, form multiplier mean deviations, take max absolute deviation over the frozen K columns, and use its 95th percentile as a common simultaneous radius. Use B=999 multiplier draws per repetition and frozen seeds. For the finite-cohort version scale deviations by sqrt[n/(n-1) * (1-n/N)]; for iid simulations use sqrt[n/(n-1)]. This matches the usual sample-variance convention; it does not establish finite-sample validity.

Use an unstudentized max statistic as the primary multiplier variant to avoid arbitrary variance floors. Report the fraction of columns with zero sample variance. **Raw multiplier is approximate**, especially at small n, near boundaries, or with singular correlation, and may return spuriously tiny radii. Predeclared guarded variant: use M1 whenever n<64 or any prompt has fewer than five correct or five incorrect selection answers; otherwise use M2. This guard is a diagnostic heuristic, not a new guaranteed procedure. Report raw and guarded outcomes, including fallback rate; do not market the guard as repairing coverage by theorem.

### M3: independent/held-out audit Wilson, approximate

Freeze J before viewing audit outcomes. In iid synthetic experiments, the audit Wilson interval targets p_J. In the finite-cohort replay it approximates mu_R,J and ignores the finite-population sampling fraction. Label both qualifications.

For a like-target finite-cohort comparison, map its endpoints [L_R,U_R] to

[n/N * mean_S(Y_J) + (N-n)/N * L_R,
 n/N * mean_S(Y_J) + (N-n)/N * U_R].

This uses the known contribution of selected items, so it targets mu_J rather than a different remainder mean. The transformation does not make Wilson exact. Report the raw remainder interval and transformed interval separately.

### M4: exact audit reference procedure, recommended default

For real finite-cohort replays, invert the hypergeometric distribution for the unknown number of correct responses among the M=N-n unselected items, based on a uniform audit of m of those items. Use conservative equal-tailed discrete inversion at alpha. This gives a conditional finite-sample interval for mu_R,J because J is already fixed given selection history. Apply the same affine transformation as M3 for an exact conditional interval for mu_J. This is a finite-cohort guarantee, **not an unseen-question population guarantee**.

For iid simulations, use the Clopper-Pearson audit interval for p_J as the finite-sample-guaranteed reference; also show Wilson's shorter approximate alternative. Known synthetic p_j, not an estimated audit score, determines population coverage.

A sampled audit point score is only a noisy reference. Full-cache mu_j is exact only for the cached finite response table. Neither is external population truth.

### M5: honest paired selected-versus-baseline decision interval

On the same untouched audit items, count D+=1{selected correct, baseline wrong} and D-=1{selected wrong, baseline correct}. Obtain separate two-sided 1-alpha/2 intervals for their proportions, using hypergeometric inversion for the finite remainder or Clopper-Pearson for iid simulations. By a union bound, [L+ - U-, U+ - L-], clipped to [-1,1], covers the paired accuracy difference at least 1-alpha. This accounts for pairing without incorrectly comparing two marginal Wilson intervals. For J equal to the baseline, return [0,0].

The audit-only target is Delta_R. To target the full cached cohort, transform endpoints by n/N * observed selection difference + (N-n)/N * endpoint. Report both only if clearly named. Declare improvement for the predeclared target only when its lower bound >0. Do not select a different baseline or rerank prompts after reading the audit. Optional secondary iid decision interval: paired score/Newcombe-style approximation, explicitly non-guaranteed; not needed for the main result.

**Recommended practical reporting:** identify the chosen prompt and complete search space, disclose reused winner score as a selection statistic, publish fresh audit score with its named target, an exact audit-based interval where applicable, and the honest paired comparison to the frozen baseline. If an audit is impossible, report M1 and its likely low precision; do not replace it with an unqualified narrow multiplier interval.

## 4. Numbered stages and gates

### Stage 0 — Preflight, invariants, and preregistration (half day)

**Goal:** establish feasible, auditable inputs and fix the statistical contract before responses.

**What to run, high level:** inspect environment and endpoint documentation; inspect pinned dataset schema; finalize templates and parser fixtures; optionally make up to 24 format/transport-only pilot requests on disjoint validation items, without inspecting correctness; then seal the manifests. Pilot edits may change format only and must precede the seal. Generate frozen seeds/split manifests without outcomes and calculate worst-case request/token/currency budgets before paid requests. No analysis implementation is prescribed here.

**Success signals:** exact dataset commit resolvable; one fixed model label accessible; price or enforceable credit cap known; prompts/targets/methods and primary metrics frozen; selection/audit access policy documented; expected cost fits limits. Metadata-only model listing or synthetic format checks are allowed, not benchmark-based model comparisons.

**Expected artifacts:** versioned preregistration, dataset manifest, template manifest, endpoint/decoding metadata, budget sheet, parser examples, access-control note, environment inventory.

**Gate:** if commit cannot be resolved, audit separation cannot be described honestly, or spend cannot be bounded, do not proceed as if the real-data design were unchanged. A synthetic-only report is allowed.

### Stage 1 — Analytic and synthetic sanity checks (half to one day)

**Goal:** verify target mappings and failure cases before paying for a full cache.

**What to run:** small deterministic tables with known finite-cohort means; hand-check hypergeometric endpoint containment including zero/all successes; one-prompt and perfectly duplicate-prompt simulations; exact two-prompt tie examples; paired D+=D-=0; compare iid versus finite-pool target calculations. Use tiny enumerated populations for complete selection/audit enumeration and coverage checking.

**Success signals:** the identity O_rem=N/(N-n) O_pool holds to numerical precision; paired self-comparison is exactly zero; M1 and exact audits have at least nominal coverage under full enumeration, up to numerical tolerance 1e-10; duplicate prompts do not produce additional winners or extra raw multiplier multiplicity; no method silently swaps targets. Conservativeness is not a failed gate.

**Expected artifacts:** invariant checklist, enumeration tables, failure-case examples, method-assumption ledger.

**Gate:** any guaranteed interval fails its enumerated guarantee: stop and diagnose sampling/inversion/indexing before further experiments. Do not solve this by dropping a case or merely increasing repetitions.

### Stage 2 — Main known-truth simulations (one day)

**Goal:** measure optimism, true coverage, and width under controlled prompt dependence and gaps.

**Generator:** for each iid item, sample common and prompt-specific standard normals, form Z_j=sqrt(rho)Z_common+sqrt(1-rho)epsilon_j, and set Y_j=1{Z_j <= Phi^-1(p_j)}. This gives exact Bernoulli marginals p_j. Rho is **latent Gaussian dependence**, not observed binary correlation; report observed binary correlations too. Generate selection and audit item vectors independently. Baseline j=1 has p0; j=K alone has p0+delta when delta>0, all others have p0.

**Core grid:** K=8, p0=0.70, n={16,32,64,128}, m=128, rho={0,0.5,0.9}, delta={0,0.01,0.05}: 36 cells, R=2,000 each. Evaluate all M0-M5, with interval comparisons sharing the same draws. Draw fresh items in every replication; do not treat a finite synthetic pool mean as the known p_j.

**Predeclared stresses:** at n=64 and delta=0 vary K={1,2,4,16} and rho={0,0.9} (8 cells); at K=8,n=16,delta=0 vary p0={0.30,0.95},rho={0,0.9} (4 cells); exact duplicate prompts at K=8,p0=0.70,n={16,64},rho=1 (2 cells). K=1 has no distinguished best-prompt gap. R=2,000 each. Add the finite-cohort sampling stress in Stage 4, not an unbounded grid expansion.

**Success signals:** all 50 cells and all methods reported, including null/undercoverage/vacuous-interval cases; Monte Carlo precision reported; high-dependence/equal-prompt limits behave sensibly. Guaranteed methods should not show statistically credible undercoverage: use one-sided exact binomial lower-tail checks with Holm correction across guaranteed-method core cells at family alpha=0.05. Any rejection triggers a correctness review. Approximate-method undercoverage is a result, not a reason to tune the scenario away. Coverage below 0.93 is separately flagged as practically severe, without defining 0.94 as a new nominal guarantee.

**Expected artifacts:** tidy per-repetition metrics, 50-cell summary table, coverage-width and optimism plots, degeneration/fallback counts, generator verification report.

### Stage 3 — One fixed real response cache (one to two days)

**Goal:** collect paired response vectors once without model/prompt selection or audit feedback.

**What to run:** precommitted zero-shot evaluation against the one endpoint label, randomized/interleaved item-prompt request order to reduce temporal confounding; incremental immutable response caching; blind scoring after prompt and parser freeze; scoring and data-quality audit before statistical replay.

**Quality rules:** resolve schema and answer indices; validate category totals and option lengths; retain variable-choice counts; exact/normalized-text duplicate detection, including cross-split contamination where available. Remove exact duplicate questions and conflicting-label duplicates from the eligible frame using a frozen, outcome-blind rule before sampling. Record exclusions. Near-duplicates are flagged, not selectively removed after scores. Official labels are used without outcome-based relabeling. Prompt-contamination from model pretraining cannot be ruled out.

Parse only the anchored final `ANSWER: <valid letter>` marker. Missing, multiple conflicting final markers, or out-of-range letters count incorrect. Do not silently use a semantic judge or regenerate to fix an answer. Retry only transport failures, respecting idempotent cache keys; do not retry refusals or malformed content. Record requested/returned model ID, timestamps, finish reason, usage fields, request hashes, response hashes, decoding settings, and price source. Never store API secrets in artifacts.

**Success signals:** complete N x 8 response table; no duplicate cache keys, gold-label leakage, or missing scored cells; every content failure retained and flagged; endpoint identity and request settings documented. Any format-only pilot was completed in Stage 0, before the manifest seal. No template, parser, or decoding edits during this acquisition stage.

**Expected artifacts:** raw request/response cache, binary outcome table, parser audit table, row-level provenance, category/choice-count summary, token/cost/latency report.

**Gate:** >5% formatting/refusal failures, >2% unresolved transport failures, unexplained model-ID change, or detectable run-setting drift: pause acquisition and report a protocol failure. Repair only through a documented pre-outcome restart or stop; no dropping inconvenient prompt columns. If an unavoidable transport cell remains missing at the hard cap, the primary complete-cache analysis is incomplete, not imputed as benchmark error.

### Stage 4 — Frozen empirical replay, ablations, and final audit (one day)

**Goal:** quantify finite-cohort optimism and characterize reporting trade-offs without an external-population claim.

**What to run:** 2,000 fixed permutation replays at all four n; all reporting methods; predeclared ablations below; final access-separated audit demonstration. Compute finite-cohort mu_j from the full cache for diagnostics only. Produce cohort-conditional coverage against mu_J and separate remainder-target results. Simulate a complementary finite pool drawn once from the primary Bernoulli generator, then replay without replacement, to expose finite-population versus iid differences.

**Success signals:** primary cell and every planned ablation reported; no reference-target substitution; audit score discrepancies interpreted with sampling uncertainty; interval labels include exact/approximate and target; final winner and reporting procedure frozen before audit reveal. No requirement that real optimism be positive, multiplier be narrower, or a winner beat the baseline.

**Expected artifacts:** paired replay table, final audit report card, finite-pool reference table, ablation table, access log, four final figures.

### Stage 5 — Claim audit and compact report (half day)

**Goal:** deliver a defensible statistical note and reporting checklist, including useful failures.

**What to run:** reconcile numbers across tables/figures; verify every guarantee against assumptions and every claimed performance gain against coverage; repeat the mock rejection audit; enumerate all deviations.

**Success signals:** no synthetic probability, cached-cohort quantity, audit estimate, or search-algorithm target mislabeled; all null and negative results retained; no attribution to an authenticated model identity; no unearned population/novelty claim.

**Expected artifacts:** short methods/results report, complete tables, figure captions, deviations ledger, reporting checklist, reproducibility manifest.

## 5. Ablations designed before outcomes

| Ablation | Fixed comparison | Failure or mechanism isolated |
|---|---|---|
| No search / fewer prompts | Frozen K=1,2,4,8 real subsets; K=16 synthetic | Multiplicity versus baseline interval approximation; no post-hoc best subset. |
| Prompt dependence | Latent rho=0,0.5,0.9; exact duplicates | Dependence reduces effective search, but small-n correlation estimates may fail. Do not claim binary rho equals latent rho. |
| True gaps | delta=0,0.01,0.05 synthetic | Pure winner's curse versus actual prompt-quality separation and selection regret. |
| Small n / boundary accuracy | n=16..128; p0=0.30,0.95 stresses | Wilson discreteness, multiplier degeneracy, and Hoeffding vacuity. |
| Audit size | m=32,64,128 at n=64,K=8, using prefixes of same audit permutation | Precision cost of honest reporting; same target, not a new dataset. Run synthetic primary cell and real cohort only, R=2,000. |
| Correlation-blind versus aware | Paired row multiplier versus independently shuffled multipliers per column, n=64,K=8, primary synthetic and real cells | Effect of ignoring cross-prompt dependence; column-independent version is a deliberately misspecified dependence comparator, not a trusted method. |
| Raw versus guarded multiplier | Fixed guard rule above | Useful failure: apparent efficiency disappears after a safety fallback; no guarantee assigned to either. |
| iid versus finite sampling | Primary synthetic iid cell versus one frozen N=600 finite pool and its SRS replays; real finite-cohort calculations | Sampling fraction, audit-target transformation, and FPC effects; also show multiplier without FPC as a labeled sensitivity. |
| Bootstrap Monte Carlo budget | B=999 versus B=3,999 on first 200 frozen repetitions of two predeclared cells: n=16 and n=64, p0=.70,rho=.5,delta=0 | Numerical quantile noise versus statistical method failure. Do not retune B using best coverage. |

No post-hoc prompt replacement, model swap, more benchmark subjects, new tuning objective, or adaptive best-method selector is permitted in confirmatory analysis. Category summaries and unexpected mechanisms can motivate a separately preregistered follow-up.

## 6. Figures and tables fixed in advance

1. **Figure 1: estimands and access diagram.** Fixed prompt family -> selection S -> frozen J -> untouched conditional audit A; separate boxes for finite-cohort mu_J, remainder mu_R,J, and synthetic p_J. Annotate the affine mapping and contrast search-algorithm expectation.
2. **Figure 2: optimism curves.** n on x-axis, mean optimism in percentage points on y-axis; synthetic dependence/gap panels and real-cache O_pool panel. Show MC uncertainty explicitly as conditional; show audit-gap conversion separately, not as a second truth curve.
3. **Figure 3: coverage versus width.** Nominal 95% reference; methods faceted by true target and small-n/boundary stress. Exact/conservative and approximate methods use different markings. Never merge population and finite-pool coverage in one unlabeled average.
4. **Figure 4: honest reporting cost/failure map.** Audit size versus exact interval length and false promotion; side panel for multiplier undercoverage/fallback rate by n and dependence. Include low-power or vacuous intervals rather than cropping them away.

Tables: (T1) target/assumption/guarantee ledger; (T2) fixed primary-cell results; (T3) complete simulation grid plus stresses; (T4) real prompt/pairing/parser/cost summary; (T5) ablations and deviations; (T6) final single-winner audit report card. Preserve source data for each plot; do not produce figures during this planning task.

## 7. Environment preflight, dependencies, and resource budget

**Available, user-reported:** empty `/work`, CPU 40 cores, no GPU, OpenAI-compatible endpoint; hardware and network have not been independently tested in this planning task. Plan uses no local LLM and no CUDA dependencies. If a local fallback were later proposed, it must be a separate CPU-feasible plan, not an unplanned 7B inference workload.

**Before execution, inspect at a high level:** Python version and virtual environment; CPU/RAM limits and BLAS thread settings; free disk/inodes; outbound HTTPS access to HF and endpoint; TLS/certificates; endpoint auth, rate limits, model labels, pricing, usage accounting, and reasoning-token behavior. Confirm no GPU with system inventory; CUDA/VRAM checks are recorded as not applicable, not installation tasks. Dataset downloads pinned to the stated revision. Do not require endpoint token probabilities.

**Required pip packages:** `numpy`, `scipy`, `pandas`, `pyarrow`, `datasets`, `huggingface_hub`, `openai`, `httpx`, `matplotlib`, `seaborn`, `PyYAML`, `tqdm`, `threadpoolctl`, `pytest`. Record resolved versions in a lockfile. A tiny analytic normal-CDF/hypergeometric calculation uses SciPy; avoid heavy training frameworks. No `torch`, GPU stack, semantic answer judge, or web-search dependency is required.

**Budget, hard ceilings fixed before outcomes:**
- Empirical primary: 600 x 8 = **4,800 successful benchmark responses**; fallback 320 x 8 = 2,560. At most 24 disjoint format-pilot requests. At most **5,100 total paid request attempts**, counting retries and pilots; transport retries capped at two per failed request and still subject to the global cap.
- Default response ceiling **256 billed output tokens including reasoning if the endpoint supports such a combined ceiling**; otherwise require a documented conservative bound on all billed reasoning/output tokens before launch. Short-explanation templates must fit the same ceiling. If this is unsupported or preflight shows persistent truncation in format-only checks, amend and reprice before outcomes; no outcome-driven token increases.
- **US$250 total endpoint-spend ceiling**, **8 million total billed-token ceiling**, and **12 hours acquisition wall time**, whichever binds first. Worst-case forecast uses actual serialized prompt token estimates plus the documented output/reasoning ceiling and verified pricing; average pilot usage alone is not a safe upper bound. An endpoint without known prices requires an independently enforceable credit cap, otherwise no paid launch. Currency and token limits include pilots and retries.
- Endpoint concurrency: start at 4, maximum 8 within documented limits; backoff on rate limits. Reserve the documented worst-case cost and billed tokens for every in-flight request before launching it; do not rely on a delayed spend counter to enforce caps. No response-based prompt scheduling. Cache before retrying ambiguous transport failures and include any potentially billed duplicate in spend accounting.
- Local simulation/replay: 2,000 reps per declared cell; B=999 for multiplier calculations. Core plus stresses: 100,000 simulation repetitions, plus small declared ablations and real replays. Expect roughly tens of billions of primitive multiplier arithmetic operations rather than LLM training; benchmark a fixed 100-repetition chunk before scheduling the full run.
- Reserve **8 GB RAM**, **10 GB free disk**, and at most **6 hours local compute wall time / 240 core-hours** for the main analysis. Chunk simulations; save sufficient per-repetition summaries, not every multiplier matrix. Prevent BLAS oversubscription: use small worker batches with one BLAS thread each, leaving capacity for the endpoint client. If RAM/disk forecasts exceed these limits, reduce concurrency/chunk sizes, not the data after viewing results.
- Estimate a total **4-6 working days** including review, not six uninterrupted days of compute. All future shell jobs longer than 300 seconds must be backgrounded with logs/checkpoints and polled; keep individual inspection output small.

## 8. Stop signals, iteration rules, and useful negative outcomes

1. **Do not launch** a paid stage without revision verification, frozen manifests, endpoint settings, and enforceable cost bounds.
2. **Stop analysis for correctness** if finite-population identities, enumeration, conditional audit uniformity/access separation, or exact-interval coverage checks fail. Diagnose implementation/design before additional compute; never tune confidence levels to make results pass.
3. **Stop acquisition** at the first cost/token/time/request cap or material endpoint/format drift. Report completeness; no selectively retained best-performing prompts or substitution of an easier dataset/model.
4. If the fixed 100-repetition timing projection exceeds six hours, reduce parallel overhead/chunk memory first. If still infeasible, preserve R=2,000 and all analytic/exact baselines, and run the multiplier only in the frozen primary cells plus n=16 stress and high-dependence n=64 stress. Record this resource-only scope reduction before inspecting coverage; do not quietly use fewer reps or adaptive stopping for nice results.
5. **No observed optimism** or no winner improvement is useful: publish the upper precision limits and explain whether high correlation, true gaps, or near-identical predictions account for it. Do not enlarge K or swap the model to force a positive story.
6. **Hoeffding too wide / exact audits low power** is useful: quantify the precision price of finite-sample validity. Do not rebrand a narrow undercovered multiplier interval as valid reporting.
7. **Multiplier fails** at n=16, boundaries, or high dependence: report the failure region and use exact audit or M1 for recommendations. A follow-up modification requires a new protocol and new evaluation grid, not the same outcomes as a tuning set.
8. **Near-ceiling endpoint accuracy** remains in the primary report; use the predeclared boundary simulations rather than replacing the real task after observing scores.
9. Any change of dataset, model, prompt family, scoring objective, audit target, or final decision threshold after outcomes creates a separately labeled exploratory/new study. Never use the final audit to select another configuration or choose which claims to publish.

### Final report card template (not a fabricated result)

Endpoint label and identity caveat; dataset revision/cohort definition; complete K and search policy; selected frozen prompt ID; selection n and reused winner score labeled selection-only; audit m and audit score with remainder target; exact audit interval; affine-mapped finite-cohort estimate/interval if relevant; paired baseline difference interval and predeclared decision; failures/token spend; and an explicit statement that cached-cohort validity is not population-truth validation.
