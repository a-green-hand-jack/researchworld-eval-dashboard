# Methodological and theoretical notes: reporting after prompt selection

## Scope and overview

Selecting a prompt and estimating its accuracy are different statistical tasks. A score used to choose a configuration is a selection statistic; it is not automatically an unbiased estimate or a valid confidence statement for the selected configuration. We separate a fixed-family bound for reused winner scores from a conditional audit construction that permits arbitrary search before the audit. The latter requires an explicit sampling and access contract, and its finite-cohort target must not be confused with unseen-question population accuracy.

The intended contribution is an estimand-explicit reporting recipe that combines standard concentration, sample splitting, discrete confidence-set inversion, and Bonferroni allocation. We do not claim to introduce the winner's curse, exact binomial or hypergeometric inference, paired comparisons, or adaptive-data-analysis theory. The available literature is a restricted set of downloaded abstracts, not an exhaustive novelty review. No priority or novelty-by-absence claim follows from it. These notes contain methodological statements and proofs, not empirical findings.

## 1. Statistical units and distinct targets

### 1.1 Iid population accuracy

Let \(Y_i=(Y_{i1},\ldots,Y_{iK})\in[0,1]^K\) be independent, identically distributed item vectors for a family of \(K\) configurations fixed independently of these items. Define

\[
p_j=\mathbb E[Y_{ij}],\qquad
\widehat p_j=\frac1n\sum_{i=1}^nY_{ij},\qquad
J\in\operatorname*{arg\,max}_{1\le j\le K}\widehat p_j.
\]

The observation unit is an item with its entire outcome vector. Outcomes for different prompts on the same item may be arbitrarily dependent. The selected-configuration target is \(p_J\). Although \(p_J\) is random through \(J\), the family marginals \(p_1,\ldots,p_K\) are fixed. This distinction is central to the fixed-family proof.

### 1.2 Fixed finite-cohort accuracy and the changing remainder

For a fixed binary response table \(Y\in\{0,1\}^{N\times K}\), define the cohort accuracy \(\mu_j=N^{-1}\sum_{i=1}^NY_{ij}\). Let \(S\) be the set of accessed items, \(|S|=n<N\), and write \(R=S^c\), \(M=N-n\), and

\[
s_j=\frac1n\sum_{i\in S}Y_{ij},\qquad
\mu_{R,j}=\frac1M\sum_{i\in R}Y_{ij}.
\]

The selected-cohort target is \(\mu_J\), while a uniform audit drawn from \(R\) directly targets \(\mu_{R,J}\). The remainder target changes with \(S\), even when the response table and prompt family are fixed. Selection and audit disjointness does not make these draws independent samples from the original finite cohort.

The pointwise decomposition

\[
\mu_J=\frac nN s_J+\frac MN\mu_{R,J}
\tag{1}
\]

implies

\[
s_J-\mu_{R,J}=\frac NM(s_J-\mu_J).
\tag{2}
\]

Thus selection-minus-remainder optimism and selection-minus-cohort optimism are different quantities with a known conversion. Neither cohort accuracy nor remainder accuracy is, without further sampling assumptions, an unseen-question population parameter. If the cohort was assembled by stratified sampling, its uniform microaccuracy is still a cohort target; it is not automatically the full benchmark's microaccuracy or a category-macroaverage.

### 1.3 Search-algorithm performance

A search procedure \(\mathcal A\), including its training-sample size and internal randomness, induces an algorithm target such as

\[
\theta_{\mathcal A,n}=\mathbb E_{D,U}\bigl[p_{\mathcal A(D,U)}\bigr].
\]

This averages performance across repeated search datasets and random seeds. Its finite-cohort analogue averages \(\mu_{J(S,U)}\) over the specified selection design. An audit of the particular frozen winner targets that winner's accuracy, not automatically the algorithm expectation. Conversely, an outer resampling estimate of an algorithm's performance is not automatically a confidence interval for the particular final winner. Changing the training size can also change the algorithm target.

## 2. Fixed-family winner optimism

### Proposition 1: expected optimism for an iid fixed family

Under the assumptions of Section 1.1, for \(n\ge1\) and finite \(K\ge1\),

\[
0\le\mathbb E[\widehat p_J-p_J]
\le\sqrt{\frac{\log K}{2n}}.
\tag{3}
\]

For \(K=1\), the expectation is exactly zero. True performance gaps, dependence between columns, duplicate configurations, and any tie-breaking rule among empirical maximizers are allowed.

**Proof.** The lower bound follows from unbiasedness of each fixed column and the maximizing property:

\[
\mathbb E[\widehat p_J]
=\mathbb E\!\left[\max_j\widehat p_j\right]
\ge\max_j\mathbb E[\widehat p_j]
=\max_jp_j
\ge\mathbb E[p_J].
\]

For the upper bound, set \(Z_j=\widehat p_j-p_j\). A centered variable supported on an interval of length one has log moment-generating function at most \(t^2/8\). Indeed, its log moment-generating function has value and derivative zero at the origin, while its second derivative is a variance under exponential tilting, bounded by \(1/4\); integrating twice gives the claim. Independence across items consequently yields

\[
\mathbb E e^{\lambda Z_j}\le e^{\lambda^2/(8n)}
\qquad(\lambda>0).
\]

No independence between columns is needed. Since \(Z_J\le\max_jZ_j\), Jensen's inequality and \(e^{\lambda\max_j Z_j}\le\sum_j e^{\lambda Z_j}\) give

\[
\begin{aligned}
\mathbb E[Z_J]
&\le \mathbb E[\max_jZ_j]\\
&\le \frac1\lambda\log\mathbb E e^{\lambda\max_j Z_j}\\
&\le \frac{\log K}{\lambda}+\frac{\lambda}{8n}.
\end{aligned}
\]

For \(K>1\), choose \(\lambda=\sqrt{8n\log K}\). For \(K=1\), unbiasedness gives the result directly. \(\square\)

Equation (3) bounds expected winner optimism, not each realized error, and it is not a confidence interval. The nonnegative expectation relies on selecting an empirical maximizer. Arbitrary selection within the same fixed family retains the upper bound but need not retain the lower bound. The bound also need not be sharp when columns are highly dependent or performance gaps are large.

### Finite-cohort counterpart and simultaneous reporting

For a fixed family evaluated on a uniform size-\(n\) subset of a fixed cohort, the same bound holds with \(s_J-\mu_J\) in place of \(\widehat p_J-p_J\). To justify the exponential step without replacement, fix a column and put \(a_i=\exp\{\lambda(Y_{ij}-\mu_j)/n\}\). The exponential moment of its sampled mean error is the normalized degree-\(n\) elementary symmetric mean of \(a_1,\ldots,a_N\), which is at most \((N^{-1}\sum_i a_i)^n\). This inequality follows by pairwise averaging at fixed sum: averaging two entries preserves their sum and increases their product, so cannot decrease the elementary symmetric polynomial. Applying the bounded-variable exponential bound to a uniform single cohort item gives \(e^{\lambda^2/(8n)}\). Each sampled column mean is unbiased for \(\mu_j\); the rest of Proposition 1 is unchanged.

A separate two-sided argument gives a selection-only confidence interval. For either iid items or uniform sampling without replacement from a fixed bounded cohort, a union bound over the fixed family yields

\[
\Pr\!\left\{\exists j:\left|\widehat p_j-p_j\right|>r\right\}
\le2K e^{-2nr^2}.
\]

In the finite-cohort version replace \((\widehat p_j,p_j)\) with \((s_j,\mu_j)\). Taking

\[
r=\sqrt{\frac{\log(2K/\alpha)}{2n}}
\tag{4}
\]

therefore covers the selected column at least \(1-\alpha\), even when its selection rule is arbitrary within that fixed family. Endpoints may be intersected with \([0,1]\). The \(\log(2K)\) factor belongs to a two-sided simultaneous tail calculation; it should not be substituted into the one-sided expected-optimism statement. Neither guarantee uses a post-hoc count of generated prompts as a substitute for an independently fixed family.

## 3. Conditional exact audits after arbitrary pre-audit search

### 3.1 The access and sampling contract

Let \(H\) contain the complete pre-audit history: accessed items, search feedback, generated candidates, randomization already revealed, and the final reporting decisions. Before the audit is revealed, freeze the selected configuration \(J(H)\), baseline \(b(H)\), scoring rule, audit size, target definitions, claims, and confidence-budget allocation. The history may arise from arbitrary adaptive search; the proof below does not require a bound on the number of proposed candidates.

For finite-cohort inference, \(S\) must contain every cohort item whose information influenced search, not merely the rows later designated as a training subset. Conditional on \(H\), assume fixed binary outcome vectors for the frozen configurations on the genuinely unaccessed remainder \(R\), and draw the audit \(A\) uniformly among its size-\(m\) subsets, where \(1\le m\le M\). If a random response table is generated independently of audit sampling, the argument can instead condition on that table as well as \(H\), provided conditional uniformity still holds. Regeneration noise is not silently absorbed into a fixed-table guarantee.

Uniformity is conditional, not merely marginal. A seed or access path that lets search exploit future audit membership can violate the contract. Item disjointness alone is insufficient. Audit-dependent reranking, stopping, baseline changes, or selection of which claims to report are not covered by this fixed-audit argument.

### Proposition 2: exact finite-remainder coverage

Let \(T\) be the number of selected-configuration successes among the \(M\) remainder items, and let \(X\) be its number of successes in the audit. Under the contract,

\[
X\mid H\sim\operatorname{Hypergeom}(M,T,m).
\]

For an observed count \(x\), form the integer confidence set

\[
\mathcal C_\alpha(x)=\left\{t\in\{0,\ldots,M\}:\Pr_t(X\ge x)\ge\frac\alpha2,
\quad\Pr_t(X\le x)\ge\frac\alpha2\right\}.
\tag{5}
\]

Let \([L_R,U_R]\) be the endpoint hull of \(\mathcal C_\alpha(x)/M\). Then

\[
\Pr\{\mu_{R,J}\in[L_R,U_R]\mid H\}\ge1-\alpha.
\tag{6}
\]

**Proof.** Under the true count \(T\), each inclusive tail probability is a valid discrete p-value. For example, if \(k\) is the smallest count with \(\Pr_T(X\ge k)<u\), then the event \(\Pr_T(X\ge X)<u\) is contained in \(\{X\ge k\}\), whose probability is less than \(u\); the lower-tail argument is analogous. Consequently, either tail rejects the true \(T\) with probability at most \(\alpha/2\). The union bound gives \(\Pr\{T\notin\mathcal C_\alpha(X)\mid H\}\le\alpha\). Taking the endpoint hull and dividing by \(M\) cannot remove the true proportion when \(T\) is retained. \(\square\)

Here “exact” means finite-sample coverage at least the nominal level, not equality: discreteness can make the interval conservative. The inversion includes zero or all observed successes and a census audit \(m=M\). A remainder interval is undefined when \(M=0\); in that case the cohort is already fully observed if all final scores are known.

The implementation `hg_table` in `/work/code/statistics.py` uses `hypergeom.sf(x-1, M, T, m)` and `hypergeom.cdf(x, M, T, m)`, matching the inclusive tails in (5). Its small threshold relaxation enlarges the acceptance set relative to exact tail arithmetic. This is a conservative implementation intention, not a formal certificate of floating-point accuracy.

### Corollary: affine full-cohort coverage

If the final selected configuration has known scores on every item in \(S\), equation (1) transforms (6) into

\[
I_{\mathrm{cohort}}=
\left[\frac nN s_J+\frac MN L_R,
      \frac nN s_J+\frac MN U_R\right].
\tag{7}
\]

Conditional on \(H\), the offset is known and the slope is positive, so the coverage event is preserved exactly. This proves conditional coverage for \(\mu_J\), not merely for a remainder parameter. If adaptive search accessed additional items whose scores under the final configuration are unknown, a remainder interval can still be justified under the stated contract, but (7) cannot be evaluated using only a nominal training subset. Its offset requires all accessed-item contributions.

Because (6) and (7) hold for every admissible history, averaging over \(H\) preserves their coverage. Arbitrary pre-audit candidate generation is therefore compatible with exact audit inference. Conditioning does not, however, make already reused selection scores fresh or retroactively validate a fixed-family bound for generated candidates.

### 3.2 Fresh iid audits

For population inference, require genuinely fresh iid audit items independent of the search history. Conditional on \(H\), a frozen learned configuration has population success probability \(p(H)\), and its audit count is \(\operatorname{Binomial}(m,p(H))\). Inverting its two inclusive tails gives the Clopper–Pearson interval with conditional coverage at least \(1-\alpha\), by the same p-value and union-bound proof. Averaging over histories retains coverage for the random selected-configuration target \(p(H)\). It does not convert that target into \(\theta_{\mathcal A,n}\).

The binomial and finite-cohort constructions are alternatives under different sampling designs. An audit drawn from the complement of a fixed cohort is hypergeometric, not a fresh iid population sample. Likewise, an affine transformation of a remainder interval cannot manufacture population validity from finite-table validity.

## 4. Paired improvement and joint confidence allocation

### Proposition 3: a paired Bonferroni interval

For the frozen selected configuration \(J\) and baseline \(b\), define on each audit-eligible item

\[
D_i^+=\mathbf1\{Y_{iJ}=1,Y_{ib}=0\},\qquad
D_i^-=\mathbf1\{Y_{iJ}=0,Y_{ib}=1\}.
\]

Write \(q^+\) and \(q^-\) for their remainder proportions, or their population probabilities in the iid setting. The corresponding paired accuracy difference is \(\Delta=q^+-q^-\). For a paired-claim failure budget \(\beta\), construct separate two-sided intervals \([L_+,U_+]\) and \([L_-,U_-]\), each with failure probability at most \(\beta/2\). Use hypergeometric inversion for the finite remainder or binomial inversion for fresh iid items. Then

\[
I_\Delta=[L_+-U_-,\ U_+-L_-]\cap[-1,1]
\tag{8}
\]

has conditional coverage at least \(1-\beta\).

**Proof.** Each discordance count has the stated marginal sampling law. The two counts are dependent because the discordance categories are mutually exclusive, but independence is unnecessary: the probability that either marginal interval fails is at most \(\beta/2+\beta/2=\beta\). On the event that both cover,

\[
L_+-U_-\le q^+-q^-\le U_+-L_-.
\]

Intersecting with the known parameter support preserves coverage. \(\square\)

For a finite cohort, let \(d_S=n^{-1}\sum_{i\in S}(Y_{iJ}-Y_{ib})\). The identity

\[
\Delta_{\mathrm{cohort}}=\frac nN d_S+\frac MN\Delta_R
\tag{9}
\]

maps both endpoints of (8) to the full-cohort difference, preserving conditional coverage exactly. When \(J=b\), the difference is identically zero on every item, so the interval \([0,0]\) is valid without estimating discordances.

A predeclared promotion rule accepts improvement only if the lower endpoint for the named target is positive. For each history with \(\Delta(H)\le0\), promotion implies noncoverage, so its conditional probability is at most \(\beta\). Averaging gives \(\Pr\{\text{promote},\Delta(H)\le0\}\le\beta\Pr\{\Delta(H)\le0\}\le\beta\). This controls false promotion for the specified target; a positive remainder effect and a positive full-cohort effect are not interchangeable decisions.

### Joint accuracy-and-improvement reporting

Two separately valid confidence intervals are not automatically jointly valid at the same nominal level. If the headline accuracy interval receives failure budget \(\alpha_a\) and the paired-difference interval receives \(\alpha_\Delta\), then

\[
\Pr\{\text{both headline intervals cover}\mid H\}
\ge1-\alpha_a-\alpha_\Delta.
\tag{10}
\]

For a total failure budget of \(0.05\), equal allocation gives \(\alpha_a=\alpha_\Delta=0.025\). Each discordance interval must then use failure budget \(\alpha_\Delta/2=0.0125\). Thus the two headline intervals are individually at least 97.5% covered, the discordance marginals are individually at least 98.75% covered, and the two headlines are jointly at least 95% covered under the audit contract. This allocation does not give simultaneous coverage over an unspecified collection of other targets or claims.

The final allocation is implemented in the separate report-card block of `real()` in `/work/code/run_experiments.py`, not in `evaluate()`. That block calls `hg_table(N-n, m, .025)` for selected-configuration accuracy and `hg_table(N-n, m, .0125)` for each discordance proportion, then applies (7) and (9). By contrast, `evaluate()` in `/work/code/statistics.py` uses an accuracy failure budget of `.05` and discordance failure budgets of `.025`, producing a paired failure budget of `.05`. Those are separate marginal 95% claims; their direct joint union-bound guarantee is only 90%. The distinction concerns call paths and confidence budgets, not evidence from numerical coverage outcomes.

## 5. Why arbitrary candidate generation changes the theorem

### An adaptive counterexample with one generated candidate

Let inputs be iid uniform on \([0,1]\), with true label always one. After seeing the selection inputs \(X_1,\ldots,X_n\), generate the classifier

\[
f_S(x)=\mathbf1\{x\in\{X_1,\ldots,X_n\}\}.
\]

Its reused selection accuracy is one, while its fresh population accuracy is zero: a finite set has probability zero under the continuous input distribution. The expected optimism is therefore one even though only one final candidate is counted. This contradicts an unrestricted adaptive extension of the \(K=1\) zero-optimism bound. Reversing the predictions gives selection accuracy zero and population accuracy one, so even the nonnegative lower bound fails for arbitrary generated candidates.

These constructions concern unrestricted data-dependent prediction functions, not the established expressivity of any particular prompt family or language model. They show why counting only evaluated or retained candidates does not control the complexity of the functions generated from the sample. Freezing the memorizer after seeing its training data does not repair inference based on those same data. A prespecified encompassing family, an independent family-construction sample, or another justified adaptivity bound would be needed for selection-only inference. Fresh conditional auditing remains available under Section 3.

### A changing-target counterexample without generated candidates

Even a fixed family does not justify replacing a fixed cohort target with a sampling-dependent remainder target in (3). Consider a fixed two-item, two-configuration response table with rows \((1,0)\) and \((0,1)\). Select on one uniformly sampled item. The empirical winner always has selection accuracy one and remainder accuracy zero, so its remainder optimism is one. This exceeds \(\sqrt{\log(2)/2}\), the unscaled fixed-family expression for this selection size. Its full-cohort optimism is only one half, consistent with the cohort bound.

The failure here is target substitution, not adaptive prompt generation. Equation (2) supplies the correct scaling: the fixed-cohort upper bound implies a remainder-optimism upper bound multiplied by \(N/(N-n)\). The fact that \(p_J\) is random in Proposition 1 is not itself a defect; the defect is replacing fixed column means by complement means that depend on the sampled set without redoing the argument.

## 6. Approximate alternatives and the boundary of the guarantee

A Wilson interval computed from reused winner scores ignores selection and has no post-selection finite-sample guarantee. Wilson inference remains approximate even for a single fixed configuration. Freezing a winner before an audit removes the selection dependence under the audit contract, but does not make the Wilson approximation exact. Mapping a finite-remainder Wilson interval through (7) changes its target, not its approximation status.

The correlation-aware multiplier construction, defined for \(n\ge2\), uses one Gaussian multiplier per selection row, shared across all columns, so that it retains empirical cross-prompt dependence. With centered row vectors \(Y_i-\bar Y\), the iid multiplier vector can be written as

\[
G=\frac{1}{\sqrt{n(n-1)}}\sum_{i=1}^n\xi_i(Y_i-\bar Y),
\qquad \xi_i\stackrel{\mathrm{iid}}\sim N(0,1).
\]

Its conditional covariance is \(\sum_i(Y_i-\bar Y)(Y_i-\bar Y)^\top/[n(n-1)]\); the finite-cohort version multiplies this by \(1-n/N\). The function `multiplier_radius` simulates this Gaussian distribution through a covariance eigendecomposition and takes a quantile of the maximum absolute coordinate. This simulation equivalence is exact for the specified conditional Gaussian distribution; it does not establish that this distribution exactly calibrates sampling errors.

Both raw multiplier intervals and the prespecified guarded variant remain approximate. Estimated covariance, singular or constant columns, boundary probabilities, small samples, and simulated quantile error can matter. Under the fixed-family design, any noncoverage on the fallback branch is contained in the simultaneous band's failure event; this does not give coverage conditional on the data-dependent fallback event. The hybrid can additionally fail on the multiplier branch, so it does not acquire a finite-sample guarantee merely because it sometimes falls back. No unproved claim of narrower valid intervals or coverage repair is made here.

## 7. Access status and methodological limitations

The final illustration is a precommitted replay, not a prospectively blinded audit. `/work/deviations.md` records that response acquisition caches the entire table before analysis and that the investigator can access it. The selector's restriction to selection rows is a computational separation; it is not evidence of investigator blinding. The report-card code explicitly labels its output accordingly. Conditional random-split validity describes the mathematical replay mechanism on a fixed table under a frozen rule, whereas prospective audit integrity requires an actual access contract. The former must not be described as demonstrated enforcement of the latter.

A fixed response table also conditions away fresh-generation variability. A deterministic parser and one cached response per item–configuration pair define the measured outcomes; they do not establish deterministic model generation. Endpoint labels do not authenticate model architecture, training data, or absence of benchmark contamination. These theoretical statements do not remove uncertainty about how the cohort, endpoint, or response table was obtained.

The data contract requires stable row identities, valid labels and option ranges, a frozen parser, complete item–configuration cells, and a documented outcome-blind duplicate policy. Transport failures must be distinguished from malformed model outputs rather than selectively repaired according to correctness. Source-level assertions in `real()` check response-count completeness, duplicate cell indices, nonmissing outcome cells, and parser-score reconstruction. Those checks are narrower than a comprehensive leakage audit: for example, searching a request for a particular field name is not proof that no solution information was sent. These notes make no claim that any quality check passed or that access separation was enforced.

## 8. Related work

### Prompt sensitivity and benchmark construction

Prompt variation is already a documented evaluation concern. Sclar et al., *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design or: How I learned to start worrying about prompt formatting* [@arxiv:2310.11324], study meaning-preserving formatting choices in few-shot prompting and introduce FormatSpread to assess plausible prompt formats without model-weight access. Wang et al., *MMLU-Pro: A More Robust and Challenging Multi-Task Language Understanding Benchmark* [@arxiv:2406.01574], describe a benchmark with more reasoning-focused questions, an expanded answer-choice set, and removal of trivial or noisy questions; their abstract also discusses stability across prompts. These abstracts motivate treating the prompt specification as part of evaluation. They do not establish the magnitude of winner optimism for a different endpoint or cohort. The present methodological focus is the distinction between selecting with a score and using it for inference, rather than a claim that prompt sensitivity or benchmark refinement is new.

### Multi-prompt estimation and budgeted selection

Performance across prompts and performance of a selected prompt are related but distinct targets. Polo et al., *Efficient multi-prompt evaluation of LLMs* [@arxiv:2405.17202], introduce PromptEval to estimate a performance distribution across prompt variants by borrowing information across prompts and examples; the abstract discusses quantile-based summaries, consistency, and best-prompt-identification applications. Shi et al., *Efficient Prompt Optimization Through the Lens of Best Arm Identification* [@arxiv:2402.09723], introduce TRIPLE for prompt selection under an explicit budget using a connection to fixed-budget best-arm identification. Our exposition concerns how to name and cover the accuracy or paired improvement of a frozen selected configuration. This is a difference in emphasis, not evidence that those works omit post-selection issues or that the present recipe improves their selection efficiency.

### Adaptive analysis and reused holdouts

Adaptive-data-analysis work explains why candidate counting alone is not a general protection against data reuse. Dwork et al., *Preserving Statistical Validity in Adaptive Data Analysis* [@arxiv:1411.2664], study estimation of expectations of adaptively chosen functions and describe perturbation and coordination techniques drawing on privacy preservation. Blum and Hardt, *The Ladder: A Reliable Leaderboard for Machine Learning Competitions* [@arxiv:1502.04585], address sequential, adaptive leaderboard estimation and introduce a leaderboard-accuracy notion and the Ladder algorithm. The conditional audit argument here imposes a simpler boundary: arbitrary search may occur before one frozen audit, but the audit is not reused for further adaptation. It is not a reusable-holdout mechanism or a new general solution to adaptive querying.

### Gaussian multiplier approximations

Correlation-aware approximation for maxima has an established theoretical literature. Chernozhukov, Chetverikov, and Kato, *Gaussian approximations and multiplier bootstrap for maxima of sums of high-dimensional random vectors* [@arxiv:1212.6906], describe conditions for Gaussian approximation and conditional Gaussian multiplier estimation of maxima, with nonasymptotic bounds on approximation errors. This motivates preserving item-level covariance in the multiplier construction. The abstract does not verify those conditions or an error bound for the particular binary, finite-cohort implementation here. The multiplier method therefore remains an approximate comparator, not an interval with the exact conditional guarantee established for discrete audit inversion.

All literature statements above are restricted to abstracts actually read in `/work/retrieval.json`. No linked references were followed and no web search was performed for these notes. The stored Project Euclid response for DOI `10.1214/12-AOS1077` contains no usable abstract in that manifest and is not cited as substantive evidence. This restricted reading supports contextual positioning only, not a comprehensive related-work or novelty claim.

## 9. Claim-to-evidence ledger for later paper writing

The ledger separates analytical arguments, source-code behavior, and protocol disclosures. It records no empirical outcomes. A source-code reference establishes what a call path computes, not that its assumptions were satisfied in a real acquisition.

| Claim suitable for the paper | Direct evidence | Scope restriction |
|---|---|---|
| Expected empirical-winner optimism is nonnegative and bounded by \(\sqrt{\log K/(2n)}\). | Proposition 1 above; `/work/theory_audit.md`, §3. | Independently fixed finite family; iid bounded item vectors. Column independence is unnecessary. |
| The same expression bounds selection-minus-cohort optimism under uniform sampling without replacement. | Symmetric-mean exponential argument in §2; `/work/theory_audit.md`, §4. | Fixed cohort and family; not an unscaled remainder bound. |
| A simultaneous Hoeffding radius covers any selection within the fixed family. | Equation (4); `/work/plan.md`, M1; `/work/code/statistics.py::evaluate`. | Prespecified family and stated sampling design; no post-hoc generated-candidate count. |
| Exact finite-remainder intervals permit arbitrary pre-audit search. | Proposition 2; `/work/theory_audit.md`, §§1–2; `/work/code/statistics.py::hg_table`. | Conditional uniformity, frozen claims and scoring, fixed eligible outcomes; no audit feedback. |
| The affine map preserves coverage for the selected full-cohort accuracy. | Equations (1), (7); `/work/code/statistics.py::evaluate`; `/work/code/run_experiments.py::real`. | Scores of the final configuration must be known on every accessed item. No unseen-population guarantee. |
| Fresh iid audits give exact conditional population intervals after search. | §3.2; `/work/code/statistics.py::cp_table`; `/work/theory_audit.md`, §2. | Genuinely fresh iid observations; selected-configuration rather than algorithm-expectation target. |
| Discordance intervals give a paired difference interval without assuming count independence. | Proposition 3 and equation (9); `/work/code/statistics.py::evaluate`. | Two marginal failure budgets sum to the paired budget; target must be named. |
| The final two-headline report uses nested Bonferroni allocation. | Equation (10); direct `.025` and `.0125` calls in `/work/code/run_experiments.py::real`. | Final report-card path only; `evaluate()` does not supply this joint allocation. |
| Arbitrary generated candidates invalidate the fixed-family extension. | Exact memorization and reverse-memorization constructions in §5; `/work/theory_audit.md`, §4. | Unrestricted-function counterexamples, not an expressivity result for the frozen prompts. |
| Remainder optimism is a different estimand and can exceed the unscaled cohort bound. | Equation (2) and the two-row counterexample in §5. | A changing remainder cannot replace fixed column means in the same proof. |
| Covariance simulation implements the specified Gaussian multiplier law, not an exact sampling law. | Covariance identity in §6; `/work/code/statistics.py::multiplier_radius`. | Raw and guarded intervals are approximate; no asserted coverage or efficiency outcome. |
| The final demonstration is replay rather than prospective blinding. | `/work/deviations.md`; explicit replay label in `/work/code/run_experiments.py::real`. | Computational row separation does not demonstrate investigator access separation. |
| Implemented structural QC is narrower than full leakage verification. | Assertions and parser reconstruction in `/work/code/run_experiments.py::real`; quality rules in `/work/plan.md`. | Source inspection only; no claim of checks passing. |
| Related-work descriptions are abstract-supported and novelty is unverified. | Read abstract entries in `/work/retrieval.json`; related-work paragraphs above. | No full-text theorem attribution, exhaustive survey, superiority claim, or novelty-by-absence claim. |

### Citation-key and local-source register

The following are the only paper citation keys used above. Each corresponds to a successful downloaded abstract entry in `/work/retrieval.json`; the associated local abstract-page paths are retained for provenance, not represented as full-text reading.

| Citation key | Local downloaded abstract page |
|---|---|
| `arxiv:2310.11324` | `/work/sources/2310.11324.html` |
| `arxiv:2406.01574` | `/work/sources/2406.01574.html` |
| `arxiv:2405.17202` | `/work/sources/2405.17202.html` |
| `arxiv:2402.09723` | `/work/sources/2402.09723.html` |
| `arxiv:1411.2664` | `/work/sources/1411.2664.html` |
| `arxiv:1502.04585` | `/work/sources/1502.04585.html` |
| `arxiv:1212.6906` | `/work/sources/1212.6906.html` |
