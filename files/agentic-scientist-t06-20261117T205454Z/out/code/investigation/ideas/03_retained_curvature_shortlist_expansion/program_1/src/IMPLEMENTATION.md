# Retained-curvature shortlist expansion

## Supported mechanism

The RPC interface is unchanged. A centered Bradley--Terry fit uses the supplied
mean-loss ridge penalty, half-win ties, and all observed pairs. Repeated directed
pairs are compressed into sufficient statistics only during fitting; row keys
and individual outcomes remain intact for influence sorting and export. A
Newton fit with Cholesky solves and backtracking must satisfy a gradient
infinity-norm threshold of `1e-9` before its certificate is exported.

For every clean nonleader, the program solves the prescribed contrast against
the same clean Hessian, computes every row's deletion influence, and orders by
influence rounded to ten decimal places then by the stable row key. Budgets are
exactly the three required floored row counts. The chosen contender's deletion
sets are unmodified nested prefixes; there is no iterative order refinement.

The first-stage contender rule compares clean-Hessian predictions across those
three prefixes. For removed set S of size k from n rows, with row gradients g,
the predicted parameter displacement is

`H^{-1} (sum_{i in S} g_i + k * regularization * theta) / (n-k)`.

The penalty correction follows from retaining the contract's mean loss, not a
sum loss. All predictions use the original fit, original leader, and original
Hessian. They do not refit or retarget after deletions. The selection criterion,
in lexicographically descending order, is:

1. Sum of predicted original-leader rank drops over the three budgets.
2. Number of predicted leader-versus-that-contender gaps below `-1e-8`.
3. Sum of relative target-gap closure, individually clipped to `[0, 2]`, with
   denominator `max(original_gap, 1e-8)` to handle rounded ranking ties.
4. Earlier position in the deterministic original ranking.

## Bounded retained-data lookahead

Keep the original at-most-six distinct clean nonleaders: the screening winner first, the
clean runner-up second (unless already included), and the remaining candidates
in decreasing screening-score order. Clean certificates are reconstructed on
demand from the unchanged clean fit rather than stored for every contender.
Reconstruction always produces the same frozen order. No row swapping,
adaptive retargeting, or reordering is performed. If these six slots include
every nonleader, skip the proxy stage and use the original exact-refit path.

Otherwise seed a deterministic pool with the entire original shortlist, then
fill in decreasing original screening-score order, capped at 24 contenders.
For each pooled contender, incrementally subtract the sufficient statistics of
its three frozen deletion prefixes. At the original clean theta, calculate the
retained mean-loss gradient and retained Hessian using the supplied unchanged
ridge. The proxy is one Newton step, `theta - H_retained^{-1} g_retained`,
centered to zero mean. It is not a converged fit and has no convergence claim.
Zero budgets reuse clean theta; duplicate budgets reuse the same local proxy.

Rank only complete, finite proxy candidates by the same rank-drop, reversal,
gap-closure, and clean-rank tuple described below. Add at most six outsiders to
the original shortlist. Every original finalist remains eligible regardless
of its proxy quality. Numerical proxy failures exclude that nomination;
unexpected optional-expansion exceptions restore the original shortlist.
Neither proxies nor refits ever alter the clean influence ordering.

Directed pair counts and fractional wins are aggregated once and shared by the
clean fit and all lookahead fits. For each candidate, incrementally subtract
its frozen prefix's sufficient statistics at the three required budgets. Refit
the identical ridge objective, dividing the data loss by the retained row count,
not the original count. The supplied ridge coefficient never changes. Scores
are centered, Newton directions use Cholesky solves, and backtracking accepts
sufficient objective descent or a roundoff-sized objective change with improved
gradient residual. Each fit has at most 100 Newton iterations, matching the
only accepted `max_iterations` request value. A fit is usable only with finite
scores and gradient and gradient infinity norm at most `1e-9`.

Warm-start the first positive budget from clean scores and later budgets from
the preceding successful refit. Cache scores by the canonical set of removed
row positions, including the empty prefix, so identical prefixes reuse their
fit across candidates and budgets. Duplicate budgets still contribute once
per requested fraction to the objective. Failures are cached as failures and
never interpreted as exact scores. These positions identify supplied rows only;
they do not infer design, question, or judge labels.

For candidates with successful fits at every requested budget, maximize:

1. Sum of original-leader rank drops using refitted scores rounded to eight
   decimals and participant-ID tie breaking.
2. Number of refitted target gaps below `-1e-8`.
3. Sum of target-gap closure fractions clipped to `[0, 2]`, with denominator
   `max(original_gap, 1e-8)`.
4. Earlier clean rank.

If no candidate has complete converged lookahead, return the original screening
winner. Otherwise exclude incomplete candidates and choose the lexicographic
maximum. Inclusion of the incumbent only implies a nonworse local primary
lookahead objective when its refits succeed; it does not guarantee improvement
in any external score. This is a bounded search, not a global optimum or an
uncertainty estimate. All lookahead scores, failures, and cache contents remain
local to the solve call. Only the selected contender's original clean scores,
Hessian direction, influences, and unmodified exact prefixes are exported.
All output keys, shapes, chunking, reset, release, and token semantics are
inherited from the starter. No diagnostics enter RPC responses.

The implementation performs at most 72 one-step proxy solves and 36
positive-prefix exact refits per solve before cache savings, in addition to its
clean fit. The original finalists are evaluated first, sharing the unchanged
exact-fit cache with additional finalists. Proxy quantities and all lookahead
diagnostics remain internal; only the winning clean certificate is reconstructed
for export. The internal exact objective is nondecreasing relative to the
original shortlist when the same baseline fits succeed, but external scores
and runtime need not improve. CPU cost and selection
quality have not been measured: this stage prohibits code execution, tests,
numerical probes, benchmarks, and evaluation. Validation here is source-only;
the harness will perform the official evaluation after submission.

## Unsupported parts of the research idea

Inputs contain only participant IDs, outcomes, and unique row keys. A row key
is never treated as a question, judge, or session identity. There is no support
for identifying Arena versus MT-Bench, matching questions or turns, clustered
deletion, clustered bootstrap, or reporting confidence intervals. The required
mean-loss objective is not silently replaced by the proposed fixed sum-loss
ridge objective. The allowed budgets are not extended to a research grid.

No data were downloaded, scientific experiments run, literature retrieved,
paper generated, or empirical improvement claimed. The stage forbids project
execution and provides no artifact channel for a paper. Retained-data refitting
is implemented as internal lookahead but has not been run in this stage;
its implementation is not empirical evidence. The original scientific study,
multi-design comparisons, dependence estimates, confidence intervals, paper,
and reproducibility artifacts remain outstanding. No evaluation was launched
and no test, benchmark, or project module was executed during implementation.
