# Certified cap-response allocation through the supplied RPC interface

## Scope and assumptions

This candidate accepts only the starter's documented `handle(request)` protocol.
It preserves reset/upload/commit/solve/release, chunk hashing and score validation,
target-major/rule-major/cap-major ordering, the three requested rules, two supplied
fractions, and the exact response schema. Diagnostics and certificates are not
added to responses. There are no downloads, filenames supplied by the caller,
external services, or additional dependencies beyond the starter's NumPy.

Scores are rounded to ten decimal places on commit. Selecting task `j` changes
only the target's score to `round(x_j + fraction * (1 - x_j), 10)`. Investment is
the number of selected tasks; the caller may normalize it by the task count.
Rivals' task scores stay fixed. For mean and ordinary median, their aggregate
scores therefore also stay fixed. Borda ranks are different: improvements to the
target reduce its opponents' pairwise credits, which this implementation includes.
The only winning criterion is the supplied co-first tolerance, not an invented
strict margin. Saturating a selected coordinate cannot hurt any of these rules:
mean and median are coordinatewise monotone, and every target/opponent Borda gap
is nondecreasing. Thus endpoint subsets suffice for minimum support.

The caps are hypothetical score-space responses, not a prediction about training
examples, compute, or causal contamination effects. No transfer, forgetting,
uncertain response, or reacting rivals are modeled. Under a genuine upper-response
envelope, an exact support minimum would lower-bound the number of affected tasks
for a successful real intervention, not its training cost.

## Exact mean certificate

For a budget `k`, sort achievable gains `caps - original` in descending order.
The top `k` gains maximize the attainable sum over all subsets of that size.
`_mean_budget` returns the first winning sorted prefix. Each smaller prefix fails,
certifying that no smaller subset can succeed in the mathematical score-space
model. The final mean is evaluated directly on the attacked vector rather than
relying on a separately rounded cumulative-sum comparison.

## Exact odd ordinary median certificate

For `T = 2h + 1`, success requires at least `h + 1` coordinates whose values pass
the same score-minus-rival tolerance comparison used by the final witness check.
Count those already passing, then promote exactly the deficit from coordinates
whose caps pass. Fewer changes leave too few passing coordinates. If there are
not enough promotable coordinates, success is impossible.

## Exact even ordinary median certificate

For `T = 2h`, ordinary median is the average of order statistics `h` and `h + 1`
(one-based), not either middle statistic alone. `_even_median_budget` enumerates
each possible lower middle endpoint `a` from original scores and caps. For this
`a`, it finds the least endpoint `b >= a` for which `(a + b) / 2` wins. Using
endpoint comparisons directly also avoids cancellation in a derived `2r - a`
threshold near a tolerance boundary.

It is sufficient to have at least `h + 1` scores at least `a`, and at least `h`
scores at least `b`. Promotions are partitioned into shared (meet both deficits),
low-only, and high-only categories. If the deficits are `L, H` and `S` shared
promotions exist, use `s = min(S, max(L, H))` shared promotions, then
`max(0, L-s)` low-only and `max(0, H-s)` high-only promotions. Check that each
category has sufficient supply. The size is minimal: any solution needs at least
`max(L, H)` changes and at least `L + H - S` changes, and this construction attains
the larger bound whenever feasible.

Every feasible endpoint subset has an actual lower middle endpoint in this
enumeration. Its upper middle endpoint is at least the enumerated admissible `b`.
Consequently the best constructed solution is a global support minimum. Work is
polynomial in the task count, including all even task counts through 100.

On supplied matrices with at most six tasks, all three scalar cases are additionally
cross-checked against independent cardinality-ordered exhaustive subset search
(at most 64 endpoint subsets). These checks run inside future RPC solves; no
fixtures, tests, or candidate code were executed during preparation of this patch.
If a discrepancy occurs, the exhaustive witness is used. Every scalar witness
is checked again with the actual aggregate and tolerance before returning it.

## Borda compatibility and bounded search

Task credits are represented in integer half-win units. For a column with a tied
group of size `c` and `l` strictly lower models, twice the credit is `2l + c - 1`.
Totals share denominator `2 * (models - 1) * tasks`. This avoids accumulating
floating tie errors. The tolerance is converted to an integer deficit by ceiling.

Let `delta_ij` be the increase in the target's twice-credit against opponent `i`
on task `j`, and let `g_j = sum_i delta_ij`. After selecting a set, the pairwise
aggregate gap against rival `i` improves by `sum_j (g_j + delta_ij)` in these units.
Each local delta is between zero and two. All infeasibility declarations are
therefore certified by failure even when every task is selected.

A descending-`g_j` prefix and deletion pass give a feasible incumbent. For bounded
improvement search, rivals with deficit at most `D - 2U` can be omitted, where `D`
is the largest deficit and `U` the incumbent size: satisfying the largest deficit
with at most `U` tasks implies the common gain is at least `D - 2U`, so omitted
rivals are automatically satisfied. Zero-gain tasks cannot change any rank gap.
Individual-rival sorted-coefficient bounds give a cardinality lower bound.
Branch-and-bound then tries budgets from that bound upwards, pruning when a
rival's best available contributions cannot fill its remaining deficit. It is
bounded by the supplied deadline and an internal node limit. The current feasible
incumbent is returned if search is interrupted; Borda optimality is not claimed
in that case. Final witnesses are validated against all initially winning rivals,
not just the search screening set. Initially nonwinning rivals cannot become
threatening because every gap is monotone.

Aggregate caches are local to a solve call, and equal fractions reuse decisions.
The shared remaining work budget is divided among remaining Borda decisions.
Mean/median computations are bounded polynomial operations and do not need an
exponential-search timeout. Reset and release retain the starter's clearing
behavior, with no persistent cross-episode data.

## What this stage does not establish

This interface provides anonymous score arrays and task IDs, not public-source
URLs, model names, source versions, source bytes, or data-license metadata. Its
SHA-256 transfer check verifies received bytes; it is not public-data provenance.
Only perfect-headroom fractions and co-first tolerance are available, not
observed-cohort ceilings, strict-margin sensitivity, or resampling controls.
The proposed public-snapshot study, composition intervals, figures, paper, and
conference template cannot be honestly implemented as RPC outputs. None are
claimed here, and no research results or score improvements have been fabricated.
These are limitations of this candidate interface, not completed experiments.

Validation for this preparation stage is source inspection only. The stage
prohibits candidate execution, tests, package installation, network access, and
evaluation. The harness owns any subsequent execution. No prohibited literature
was searched for or accessed.
