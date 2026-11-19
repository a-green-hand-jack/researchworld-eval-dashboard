# Exact score partition portfolio: implemented candidate, no empirical results

## Interface and target

`program.py:handle` retains the starter reset/input/infer protocol and exact
response keys. The supplied inputs are binary labeled outcomes, their frozen
scores, and unlabeled scores. The live infer target remains the documented
population mean `E[Y]`. There is no supplied pool-revelation design, full-pool
truth, case identifier, or additional sampling control.

Consequently this candidate does **not** claim to have implemented or run the
idea's fixed-pool repeated-mask study through the RPC. A fixed-pool-only interval
would be inappropriate for its target. Instead, the live method uses a protected
population envelope around the exact pooled-sample interval. This adaptation
requires iid pairs from a common population, with a frozen predictor independent
of those pairs; the RPC cannot verify that assumption. It is not valid for
convenience labels, distribution shift, clustered sampling, or predictor training
on the current labels without additional arguments. In particular its guarantee
is not conditional on an already observed labeled sample.

## Algorithm and finite-pool theorem

`program.py:exact_score_portfolio` accepts scores, revealed indices, and
revealed outcomes only. It never receives unrevealed labels. Pooled-score
quantiles define the requested 1, 2, 4, and 8 bin partitions; equal scores are
never split. Population-empty strata are removed and identical assignments are
deduplicated, without examining outcomes. The menu and error allocations are
fixed rules, not optimized using labels. Input order carries no predictive role.

For a stratum containing `M_k` items, `n_k` labels and `x_k` successes, feasible
positive totals range from `x_k` to `M_k-n_k+x_k`. Under uniform label revelation,
conditional on the stratum sample counts, the observed success count is
hypergeometric with those parameters and unknown total `T_k`. Retain integer
totals with both inclusive tail probabilities strictly greater than half the
stratum error budget. Monotone binary searches use the survival function for
the upper tail rather than subtracting the CDF from one. A sample-empty stratum
returns `[0,M_k]`; a fully labeled stratum returns `[x_k,x_k]`.

Discrete tail probabilities are superuniform under their true total. Thus either
tail excludes that total with probability at most its one-sided budget. Split
the portfolio error equally over distinct partitions and then over their
population-nonempty strata. Summing stratum endpoints protects the whole-pool
total for each partition. Two union bounds protect all partition intervals
simultaneously, so their intersection contains the true pool mean with probability
at least one minus the portfolio error. No independence across partitions or
strata is needed. Empty intersections return `[0,1]`, never zero width. The same
argument holds conditional on any fixed full population and scores under a
uniform without-replacement label sample. Floating-point SciPy tail evaluation
is used; this is not an arbitrary-precision or certified-rounding implementation.

## Protecting the documented population target

The live method reserves `alpha/10` for the population envelope and uses
`9*alpha/10` for the pooled-sample portfolio. This split is prespecified. With
`M=n+N`, iid sampling makes the unobserved full-pool success total `T` marginally
`Binomial(M,p)`, where `p=E[Y]`. Conditional on the unordered full pool of
score/outcome pairs, the labeled positions are a uniform subset. The fixed-pool
theorem therefore applies after integrating over iid pools, even though the
interface represents labeled positions first.

Let `[L,U]` be the integer-total interval from the portfolio. Consider the
equal-tailed Clopper-Pearson interval `C(T)` for the *unobserved* total, at error
`alpha/10`. Both CP endpoints are nondecreasing in the total. On the joint event
`L <= T <= U` and `p in C(T)`, `p` belongs to the interval from CP's lower endpoint
at `L` to its upper endpoint at `U`. A union bound gives total error at most
`9*alpha/10 + alpha/10`. The code computes only that envelope, not `T`. Rounded
products of pooled endpoints by `M` recover integer endpoints; RPC limits make
the integer representation and rounding unambiguous in binary64. An empty-pool
intersection or nonfinite envelope gives full support.

The reported point estimate is the labeled mean. It is unbiased under the iid
assumption and is not used for interval selection. No clipping, fitting, or
post-hoc event-count switch is used to choose between exact and asymptotic CIs.
No data or fitted results are retained across reset operations. The method is
deterministic; seeds are accepted by the unchanged protocol but not used.

All inference functions are in the entrypoint file. Loading the script by path
does not require an undocumented sibling-module import path.

## Gain regimes and limitations

For a fixed population and a partition with every `n_k>0`, let `w_k=M_k/M` and
`S_k^2` be the finite-population outcome variance using denominator `M_k-1`.
Conditional on all sample counts, the post-stratified mean has variance
`sum_k w_k^2 (1-n_k/M_k) S_k^2/n_k`. Stratum samples are conditionally independent.
For singleton census strata their variance contribution is zero. Separating
different outcome prevalences can lower this variance; nonmonotone score effects
can be represented by multiple bins without fitting a new predictor. This
variance explanation is not a width-dominance theorem for exact intervals.

Bonferroni allocation, discrete endpoints, sample-empty strata and the extra
population envelope can more than erase variance gains. The unstratified member
uses only its fraction of the portfolio budget and need not match a full-alpha
unstratified interval. Constant scores deduplicate to a single partition but
still pay the population-envelope cost in live inference. Sparse/rare outcomes,
weak scores and small label budgets are especially unfavorable. No universal
gain over PPI++, the incumbent, or classical exact methods is claimed. The method
uses existing scores as strata, not as a replacement trained predictor.

## Validation status and missing work

Only static source inspection was allowed in this editing stage. No Python,
candidate execution, tests, experiments, literature downloads, data downloads,
or evaluation was performed. There are no empirical numbers or claimed gains.
No research paper, conference-template compliance, bibliography review, or
completed repeated-sampling study is claimed. The permitted starter literature
was not fetched here, and no prohibited material was accessed.

Before scientific use, independently check the binary-search inversions against
exhaustive enumeration of feasible totals for small populations, including
zero-sample and census cases. Enumerate label subsets to check the coverage of
each partition and the protected intersection, tied/constant scores, sparse
strata, and the fallback. The population-envelope theorem needs separate iid
repeated-pool checks; fixed-pool masks alone cannot validate population coverage.

The proposed paired study (not performed or supplied as executed evidence) uses
identical uniform label masks on fixed binary pools for the exact portfolio,
standalone exact intervals and finite-target baselines. Prespecify monotone,
U-shaped, uninformative and rare-outcome pools and label budgets, save every
endpoint, and report exact binomial Monte Carlo coverage intervals plus paired
width-difference uncertainty, including widening and failures. Keep that study
separate from comparisons for the live iid population target. The RPC provides
no mechanism to generate those study masks or expose truths to inference; none
has been invented. The harness alone performs the official candidate evaluation.
