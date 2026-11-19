# Analysis protocol

The estimand is score-space investment needed for a fixed target to become the
unique winner, holding all other score vectors fixed. A separate optimization is
solved for each of K (number of coordinates raised), L1 (sum of score-point
increases) and Linf (largest coordinate increase). Their optimal interventions
need not coincide. No conversion to examples, compute, dollars, or training
success is identified by these public scores.

## Frames and rules

HELM MMLU v1.13.0 has 79 complete models × 57 subjects. OLLB contents at commit
9c09a7cae43334062a82cb164f2ef255013dafa2 has 4,576 rows; 79 repeated model names
are removed, keeping the largest reported Average, and one flagged model is
excluded: 4,496 models × 6 tasks. The top-500 frame is selected once by normalized
arithmetic mean and then fixed for all rules. The no-merge sensitivity has 3,789
models. These are censuses of selected public snapshots, not random model samples.

Arithmetic mean, median (average middle pair for even task counts), minimum,
shifted geometric mean and shifted harmonic mean are primary score rules.
The latter two aggregate score+1 and subtract 1 afterwards; the shift is a
modelling choice required for zeros, and arbitrary monotone transformations do
not preserve these rules. Borda is summed average task rank (equivalently,
pairwise wins plus half of ties). Plurality sums first-place shares, dividing a
tied task's unit credit equally. Condorcet is the requirement of beating each
rival in strict task-majority, counting task ties as half; it is not a complete
ranking and can have no unmodified winner. Achieving it is sufficient for first
under every Condorcet-consistent rule, so its minimum cost is an upper bound on
winning under any particular such rule; the reverse implication does not hold.

The supplementary six-task trimmed mean drops the lowest and highest task
score. Its L1 optimization uses continuous task scores with binary sorting
assignments, and Linf uses monotone uniform-lift bisection. It does not use the
ordinal finite levels; K is not supplied for this supplementary rule.

Primary targets are every model in the frame. When reporting non-leading
models, the *mean's* unique leader is excluded for all rules so comparisons are
paired. A target already uniquely first under another rule retains cost zero.
Additional rank-stratified summaries condition on the original mean rank.

## Feasibility and strictness

A target x can move only to x <= y <= c, where effective c=max(x,scenario cap).
Scenarios: ceil=100; front0/front2=best rival task score +0/+2, clipped at100;
gain5/10/20=x+5/10/20 clipped at100. Emp95/emp99 add per-task quantiles of 540
observed fine-tune-minus-listed-base score differences to x (clipping negative
quantiles to0). Those differences include selection, architecture, and training
confounding; these are illustrative heterogeneous gain scales, not estimated
causal feasible training gains. They apply only to the normalized OLLB frame.

For initially non-winning score targets, winning means f(y)>=max_rival f+0.001
score points. An initially unique winner has zero cost. Ordinal interventions
use a finite convention: each coordinate is unchanged, ties an existing rival
score at or above the original target coordinate, or reaches such a rival
score +0.001, within its effective cap. Rivals below the original target
coordinate are excluded from this candidate construction, even when adding
0.001 to one would yield an intervening real value. This handles the absence
of a minimum on an open strict-win constraint; all three ordinal objectives use
the same intervention set. Borda's winning margin is its half-point lattice;
plurality strictness is enforced on its exact rational-credit lattice. Linf
searches the same finite levels, not arbitrary infinitesimal crossings.

Infeasible optima are +infinity in CSV, never zero/missing. An optimality limit,
numerical failure or nonconvergence raises an error; it is not evidence of
infeasibility. MILPs request zero relative optimality gap. Solver results are
checked against independent exhaustive/LP oracles on small random instances.
No numerical method establishes bit-exact real arithmetic; epsilon and the
solver tolerances are separate modelling and numerical quantities.
Ordinal finite-set optima are upper bounds on the infimum over arbitrary real
strict crossings. Finite-set infeasibility is conditional on this convention;
changing epsilon can change the available levels near caps. Margin sensitivity
is supplied on fixed near-top panels.

## Uncertainty and controls

Across-model summaries describe the fixed frame. Target-bootstrap ranges
describe resampling of this frame and do not imply a representative population
of future models. Main comparisons retain infeasibility as infinity;
finite-only cost summaries and their denominators are explicitly labelled.

Descriptive quantiles use NumPy `method="inverted_cdf"`: for m sorted nonmissing
values z_(1),...,z_(m), including +infinity, Q(p)=z_(max(1,ceil(m*p))). The
median Q(0.5) is the lower middle observation for an even m, not the average of
the two middle observations. This applies to cost medians/quartiles, paired
finite-cost differences/ratios, task/noise and rival-frame percentile summaries,
and the R1000 paired-target bootstrap point estimates and percentile endpoints.
It keeps reported quantiles on observed values and avoids interpolation with
+infinity. Empty conditional panels have NaN summaries. The aggregation rule
called "median" is different: it averages the middle pair when the number of
*tasks* is even, as defined above. Derived presentation statistics must declare
any different convention (for example midpoint medians of random-order controls)
rather than relabel them as these analysis quantiles.

Task bootstrap: 100 shared draws resample n task columns with replacement;
fixed original-mean ranks2–11 are followed under every rule. Its 2.5–97.5%
percentiles are task-mixture sensitivity intervals; six OLLB tasks and correlated
MMLU subjects do not justify independent-task population inference.

Score noise: Gaussian score perturbations clipped to[0,100], using plug-in
binomial-style per-cell SEs. HELM counts are common across models per subject and
score×count/100 is integer to floating-point tolerance. OLLB counts/floors are
approximate effective scales (BBH/MUSR normalize subtasks; IFEval and other
metrics are not independent Bernoulli trials). Per-task shock correlations0 and
0.8 across models are tested. They are assumption-dependent sensitivity analyses,
not calibrated measurement-error confidence intervals; paired item responses
and model error covariances are unavailable in the score tables.

Task-count experiment: 100 subsets at n=3,6,12,24,48,57 HELM subjects, shared
across rules. Select sorted positions2 and5 separately within each resulting
rule/frame, record actual rank (ties may occur), and re-solve. This is task-count
sensitivity, not evidence that the two datasets differ causally because of n.

Controls on a fixed original-mean ranks2–21 panel: random task order raises
coordinates to their effective reachable caps until a unique win (200 random
orders), compared with optimal K; the uniform clipped improvement at optimal
Linf is compared in L1 with optimal L1. The former also spends score points
wastefully and is a support control, not an L1 optimum.

## Limits on interpretation

The optimizer has perfect score knowledge, independent coordinate control and
fixed rivals. Task overlap, tradeoffs, uncertain learning curves, score noise,
contamination detection and rival responses can all invalidate a literal training
interpretation. Rankings and caps depend on the competitor frame and scale.
Changing rules changes the original leader and gap; cross-rule cost differences
combine that with the rule's response to increases. A gap-matched theoretical
comparison and same-target empirical comparison answer different questions.
