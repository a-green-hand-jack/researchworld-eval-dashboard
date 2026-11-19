# Mathematical audit and plan update

**Scope:** reviewed only `/work/plan.md`, `/work/code/statistics.py`, and `/work/artifacts/tests.json`; no web, generated code, experiment execution, or other outcome inspection. Prior context: observation O-6ae7e06b810f3504. General claims below are checked analytically, not inferred from numerical tests.

**final-status: REFUTED** — the unrestricted adaptive fixed-K extension is false. The fixed-family optimism theorem and conditional exact-audit constructions are valid under the hypotheses stated below.

## Compact critique, ordered by importance

1. **Do not extend fixed-K selection guarantees to arbitrary prompt generation.** The plan correctly restricts its primary family to eight frozen prompts. M1 remains valid for arbitrary selection among a prespecified family, not for eight prompts generated using the same scored sample. Freezing a generated prompt afterward does not make its reused selection scores unbiased.
2. **Exact audits survive arbitrary pre-audit search, with an access/sampling contract.** Conditional on the entire pre-audit history, freeze the selected prompt, baseline, scoring rule, targets, sample size, and claims. Audit uniformly from the genuinely unaccessed remainder. No audit-dependent redesign, reranking, optional stopping, or claim selection is covered by this argument.
3. **Final joint-confidence allocation is not implemented by `evaluate` as written.** Its accuracy interval has alpha=.05 and its paired interval has total alpha=.05. These are correct separate 95% claims; the direct union-bound joint guarantee is only 90%. The plan's two-headline 95% guarantee requires alpha=.025 for each claim and alpha=.0125 for each discordance marginal. A separate final-report path could supply this, but it was not inspected; this function alone does not.
4. **The exact finite-pool target is the unselected remainder.** The affine full-cohort mapping is valid and preserves conditional coverage. It does not establish unseen-question population coverage. A sampling-dependent remainder mean cannot simply replace a fixed population probability in the iid optimism theorem.

## 1. Conditional hypergeometric inversion and affine mapping

Let H contain all pre-audit search information, including the accessed cohort set S, with |S|=n, and the frozen selected prompt J. Let M=N-n>0. Conditional on H, require a fixed binary outcome vector on the remaining M items and an audit A that is a uniform m-subset of them, with 1<=m<=M. Conditioning may also fix an independently generated response table; the audit must not reveal that table to the selector in advance.

If T is the number of selected-prompt successes in the remainder and X the audit successes, then

    X | H ~ Hypergeom(M,T,m).

For candidate t, retain it when both P_t(X>=x)>=alpha/2 and P_t(X<=x)>=alpha/2. Under the true T, each rejected-tail event has probability at most alpha/2: its tail probability is a discrete valid p-value. The union bound therefore gives coverage at least 1-alpha. The integer acceptance set's endpoint hull cannot reduce coverage.

`hg_table` uses `sf(x-1)` and `cdf(x)`, the correct inclusive tails. Its 1e-14 relaxation enlarges the acceptance set relative to exact arithmetic and so is conservative in principle, although SciPy floating-point evaluation is not a formal numerical certificate. Zero/all successes and a census audit m=M are covered by the argument. M=0 and invalid sample sizes need exclusion rather than division by zero.

Write s_J for the selected-prompt mean on S. The identity

    mu_J = (n/N)s_J + (M/N)(T/M)

holds pointwise. Given H, its first term is known and its slope is positive. Thus transforming remainder endpoints [L,U] by `(n/N)s_J + (M/N)[L,U]` preserves conditional coverage exactly. `evaluate` performs this mapping correctly; `remtruth` also uses the correct complement count. Similarly,

    s_J - mu_R,J = (N/M)(s_J - mu_J).

This is a conditional finite-response-table statement, not independence of selection and audit and not a population guarantee.

For genuinely adaptive search, S must include every cohort item whose information influenced search; excluding just a nominal final training subset is insufficient. The final selected prompt and baseline must have known scores on all S to compute the affine offset. Otherwise the remainder interval remains valid, but the claimed full-cohort transform is not available as written. Uniformity is required conditional on H, not merely marginally; audit randomness cannot already be revealed through search history.

## 2. Paired discordance and arbitrary pre-audit adaptivity

On each remainder item define D+=1{J correct, baseline wrong} and D-=1{J wrong, baseline correct}. Their remainder proportions q+ and q- obey Delta_R=q+-q-. Each audit count separately is hypergeometric; they are not independent, nor need they be.

Construct marginal intervals with failure probability alpha/2 each. With probability at least 1-alpha both hold, and then

    Delta_R in [L+ - U-, U+ - L-].

The identical reasoning uses Clopper-Pearson marginals for fresh iid audit items. `pairtab=...(.025)` correctly implements a total-alpha=.05 paired interval. The affine map using the known selection difference correctly targets the full cohort. A self-comparison is identically zero, so the [0,0] shortcut is valid. Declaring improvement only when the lower endpoint is positive gives false-promotion probability at most alpha for the specified target, including when its sign varies across histories.

Because coverage holds for every admissible H, averaging over H preserves it. There is no bound on the number or adaptivity of pre-audit candidate proposals. The final prompt and baseline may even be generated from selection outcomes. What cannot be arbitrary is reuse of audit feedback, outcome-dependent audit stopping, or the number of claims selected after audit inspection. Fresh independent audit data or an appropriately justified sequential/multiple-testing procedure would then be required.

## 3. Fixed-family expected winner optimism: proof

Assume n>=1 iid item vectors `(Y_i1,...,Y_iK)` in [0,1]^K, a finite family fixed independently of these vectors, fixed p_j=E[Y_ij], empirical means hat_p_j, and J in argmax_j hat_p_j. Within-item prompt correlations and true gaps are unrestricted; ties may be resolved arbitrarily among maximizers.

**Lower bound.** Since hat_p_J=max_j hat_p_j,

    E[hat_p_J] = E[max_j hat_p_j] >= max_j p_j >= E[p_J].

Thus E[hat_p_J-p_J]>=0. Merely saying the maximum centered error is nonnegative in expectation would not prove this lower bound for the selected error; the displayed argument does.

**Upper bound.** Set Z_j=hat_p_j-p_j. Hoeffding's lemma and independence across items imply, for every lambda>0,

    E exp(lambda Z_j) <= exp(lambda^2/(8n)).

For completeness, a centered [0,1] variable has log-MGF g with g(0)=g'(0)=0 and g'' equal to a tilted variance, at most 1/4; integrating twice gives g(t)<=t^2/8. Apply this to each Y_ij at t=lambda/n and multiply over independent rows.

No independence across prompts is used. Jensen and exp(max)<=sum exp give

    E[Z_J] <= E[max_j Z_j]
             <= log(E exp(lambda max_j Z_j))/lambda
             <= log(K)/lambda + lambda/(8n).

For K>1 choose lambda=sqrt(8n log K). Consequently

    0 <= E[hat_p_J-p_J] <= sqrt(log(K)/(2n)).

For K=1, J is fixed and E[hat_p_1-p_1]=0 directly (equivalently take lambda down to zero). There is no log(2K) here: this is a one-sided expected maximum, not a simultaneous two-sided confidence interval. Large gaps, unequal means, perfectly correlated columns, and duplicates do not invalidate the proof; the bound need not be sharp. Non-winner selection retains the upper bound for a fixed family but need not retain the lower bound.

The supplied files contain no explicit derivation of this theorem; the argument above supplies it rather than certifying an unseen proof.

## 4. Why generated prompts and sampling-dependent targets matter

**Adaptive-generation counterexample, already at K=1.** Let iid inputs be uniform on [0,1] with true label always 1. After observing S, generate the classifier that outputs 1 exactly on the observed inputs and 0 elsewhere. Then hat_p=1 and its actual population accuracy p(S)=0 almost surely. Expected optimism is 1, contradicting the asserted K=1 upper bound zero. Reversing the predictions gives hat_p=0 and p(S)=1 almost surely, contradicting the lower bound. These examples establish that neither side survives arbitrary data-dependent prompt/function generation without restrictions on the available function class. They are not claims about the expressivity of any particular frozen prompt family.

The same memorizer on a finite pool has selection mean 1, remainder mean 0, and cohort mean n/N. Applying fixed-K Hoeffding to the single generated candidate is invalid: a post-hoc count of evaluated/generated candidates does not control the underlying data-dependent class. A prespecified encompassing finite family, an independent family-construction sample, or another justified complexity/adaptivity bound is needed.

**Sampling-dependent p alone is not the diagnosis.** In the proved theorem p_J is random because J is random, and that is harmless: all p_j are fixed and each Z_j has the stated MGF. Fresh iid audits also permit a random learned prompt with population accuracy p(H), because that accuracy is fixed conditional on H and fresh audit scores have conditional mean p(H).

But replacing p_j by mu_R,j(S) in the fixed-family proof fails. Exact example: N=2, n=1, K=2, fixed outcome rows (1,0) and (0,1). The empirical winner always scores 1; its remainder accuracy is always 0. Expected remainder optimism is 1, exceeding sqrt(log(2)/2). The full-cohort optimism is only 1/2 and does not violate the fixed-cohort analogue. For a fixed family, without-replacement concentration gives the same full-cohort upper bound; the remainder upper bound inherited through the identity is multiplied by N/(N-n). Thus changing the target changes the theorem even without adaptive prompt generation.

## 5. Evidence limits and minimal plan updates

`tests.json` reports minimum exhaustive hypergeometric coverage 0.9502262443438912, CP grid coverage 0.9507460924917581, 560 enumerated selection/audit cases, and full/paired pipeline coverage 1.0. These support the intended constructions for the tested cases. They do not prove all parameter values, arbitrary adaptive histories, correct audit access control, or the final joint-confidence allocation. CP grid checks are not exhaustive over a continuum of probabilities. The reported multiplier quantile difference is compatible with finite Monte Carlo error; multiplier methods remain approximate as the plan already states.

**Stage 1 additions:** place the proof and both adaptive counterexamples in the assumption ledger; add the two-row remainder-target example; explicitly distinguish fixed family, arbitrary selection within it, generated candidates, and fresh conditional audits. Add boundary/design checks for m=M, M>0, audit leakage, and the final confidence-allocation hierarchy. These are analytical/test recommendations, not code changes performed here.

**Stage 4 clarification:** before final audit reveal, document H, the genuinely unaccessed sampling frame, frozen final prompt/baseline and scores on S, audit size, targets, and allocated alpha. Use 97.5% intervals for each of the two final headline claims and 98.75% intervals for each discordance marginal. Keep ordinary simulation claims at their planned separate 95% levels.

**Stage 5 clarification:** report fixed-family optimism separately from any adaptive-search extension. Audit conditional guarantees do not imply that the fixed-K selection-only interval or expected-optimism bound applies to generated prompts. No dataset/model change or additional paid collection is warranted by this audit.

**Audit checks:** verified inclusive tails, affine offsets, paired Bonferroni levels, K=1, arbitrary fixed-column dependence, ties, self-comparison, and exact counterexamples. Remaining implementation scope: no orchestration/access-control or separate final-report path was inspected. Successful pattern: condition on search history for genuinely fresh audits. Failure pattern: conditioning cannot retroactively make reused training data fresh.
