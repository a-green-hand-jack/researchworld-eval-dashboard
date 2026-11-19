# Statements supported by the solver model (proof notes for paper owner)

These are model propositions, not empirical generalizations. Formulas for
positive winning-margin costs apply to targets that are not already uniquely
first; an initially unique winner has cost0 by convention for every measure,
even when its lead is smaller than epsilon. All boxes use the effective
cap max(original score, scenario cap), so no scenario forces a score decrease.

1. **Mean total increase.** For n equally weighted tasks, target mean m and best
   rival mean tau, minimum L1 is max(0,n(tau+eps-m)), provided total available
   headroom is at least that amount. Otherwise the target is infeasible.
   Existing unique winners are assigned0 by convention. Proof: sum constraint is
   both necessary and sufficient in a box. Minimum K is the shortest descending
   headroom prefix whose sum reaches the required increase. It can be1 even for
   many tasks, but only if a task has enough headroom. Equal score gaps alone do
   not determine K.

2. **Weighted mean.** Required weighted increase is tau+eps-w·x. Minimum L1 fills
   available headroom in descending task weight, with at most one partial task
   (fractional knapsack). Minimum K uses descending weighted headroom. Minimum
   Linf is the smallest d with w·min(x+d,c)>=tau+eps.

3. **Minimum.** Let b=tau+eps under the minimum rule. Feasibility requires all
   task caps to reach b. If feasible, L1=sum(max(0,b-x_t)), K=#(x_t<b), and
   Linf=max(max(0,b-x_t)). It need not require touching every task; coordinates
   already above b cost nothing. Conversely, one unreachable coordinate blocks
   victory regardless of improvements elsewhere.

4. **Odd median.** With n=2h-1, at least h final coordinates must reach b.
   Minimum L1 is the sum of the h cheapest coordinate costs max(0,b-x_t), treating
   c_t<b as infinite. K is max(0,h-#(x_t>=b)) if that many lower coordinates can
   reach b. There is no universal positive lower bound h on *newly touched*
   tasks. For n=2h, the average-middle-pair convention permits tradeoffs between
   thresholds a>=b>=bb with a+bb=2b: h coordinates reach a and one additional
   coordinate reaches bb; breakpoints in x,c and their reflections enumerate
   the piecewise-linear optimum. K can instead enumerate threshold pairs from
   x and c, because selected coordinates can always be taken to their caps.

5. **Concave power means.** Aggregate score+1. For p<1 (including p0 as log), use
   the increasing concave transform g_p(z)=z^p/p, or log(z) for p0. The aggregate
   threshold is an additive g constraint. A minimum-L1 vector equalizes free
   coordinates at a common water level, subject to original scores and caps;
   K greedily selects the largest transformed capped gains. These conclusions
   rely on positive score+1, free coordinate increases and L1 weights all1.

6. **Ordinal optimization.** Increases between adjacent rival score levels do
   not change any task comparison. On the declared finite tie/pass intervention
   set, Borda/Condorcet constraints are linear in one-hot per-task level choices;
   Borda combines target gain and each rival's loss. Plurality needs only tie or
   pass the best rival per task; changes below that level have no effect. The
   least integer margin on the attainable rational-credit lattice enforces
   strict plurality victory. MILP optima on this finite set are exact up to
   numerical solver tolerance, not exact minima over arbitrary real strict
   crossings (which may fail to attain an infimum).

7. **No universal rule order.** Mean, median and minimum use different rivals'
   thresholds and different parts of x. Their optimal costs can reverse across
   score matrices, caps, investment metrics, and target models. Any claim that
   median or minimum is always more robust than mean requires additional
   conditions. The empirical comparison is conditional on the observed frames;
   it should not be promoted to an unconditional theorem.

Useful normalization: L1/n is mean score-point increase; K/n is task coverage.
Raw L1 and K at n6 vs n57 are not directly comparable. Linf has score-point units
under either dimension but remains scale- and cap-dependent.

`src/theory_examples.py` writes explicitly labelled constructed counterexamples
to `results/theory_examples.json`, separate from all public leaderboard results.
For example, five-task target(10,0,0,0,0) against rival(3,3,3,3,3), ceiling100:
mean K1, median K2, minimum K4. Against a concentrated rival(9,9,1,1,1), a zero
target under gain5 needs mean K5 but median K3, with median/minimum L1 below
mean L1. A target(4,4,4,4,0) against the same rival under gain1.1 needs minimum
K1 versus mean K5. These are mathematical counterexamples to unconditional
rule ordering, not empirical frequencies or demonstrations replacing the study.

8. **Uniform-gain feasibility threshold.** For any coordinate-monotone rule with
   the stated intervention convention, define d*=minimum Linf under ceiling100.
   A gain-h scenario is feasible iff d*<=h (up to numerical tolerance). Its box
   upper corner is min(x+h,100), which dominates every intervention with Linf<=h;
   conversely any feasible gain-h intervention has Linf<=h. The result holds
   irrespective of the number of tasks and explains why Linf is a useful
   feasibility diagnostic rather than a total training-cost estimate.

`src/check_results.py` checks this threshold equivalence against independently
run gain5/10/20 results, cap-monotonicity, agreement of feasibility across the
three separately solved objectives, K integrality and the mean-gap identity.

9. **Certified Borda dynamic-program relaxation.** Double all Borda credits to
   integers. Retain only the constraint against the rival with the highest
   original Borda total. A multiple-choice dynamic program over tasks finds
   minimum cost to reach the required integer improvement, choosing at most one
   finite score level per task. Saturating the reward state at the requirement
   preserves the optimum because rewards/costs are nonnegative. This is a lower
   bound on the multi-rival problem. Reconstruct a witness and check *all* rival
   constraints; if it satisfies them, the bound is attained and is the exact
   optimum. Infeasibility of the relaxation proves full infeasibility. Otherwise
   fall back to the independently tested multi-rival MILP. This avoids accepting
   a heuristic result and removes a measured timeout in the original OLLB run.

10. **Continuous trimmed-mean optimization.** For the small six-task supplement,
    L1 is minimized over continuous task scores in the box. Binary assignments
    associate each task with one sorted position; ordered auxiliary values are
    bounded above by their assigned task scores, and their middle sum must
    reach the required threshold. A feasible auxiliary vector implies that
    the sorted actual scores dominate it coordinatewise, so this one-sided
    assignment formulation is sufficient; conversely the sorted actual scores
    give feasible auxiliaries. Thus its projection is the desired continuous
    constraint. The solver requests zero relative MIP gap and is checked
    against exhaustive orderings with continuous LPs. Linf uses monotonicity
    and uniform-lift bisection; no trimmed K is supplied. The finite rival
    tie/pass levels belong only to ordinal rules.

## What the bounds do and do not imply

A score-rule optimum is a minimum in the declared fixed-rival box model. It
bounds from below the score-space cost of any particular intervention feasible
in that same box, for that same objective. Public scores do not identify a
training-cost conversion, training feasibility or future rival movement; no
unconditional lower bound on an actual training plan follows. Ordinal costs
are exact only on the finite declared candidate set and bound arbitrary-real
strict-win infima from above. The Condorcet requirement adds a different
sufficient-condition upper bound, relative to a particular Condorcet-consistent
rule with a compatible intervention convention. These are different bounds.

The constructed examples establish reversals for mean, median and minimum;
they refute universal orders among those rules and blanket half/all-task
statements. They do not prove pairwise reversals for every other studied rule,
nor a theorem that every member of any larger family fails to be cheapest.
