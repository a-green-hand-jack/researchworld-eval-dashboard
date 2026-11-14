# Closed-form propositions (and what is *not* true), with the validation rows that check them

Setting (as in `src/mti/scorerules.py`): target model i has scores x ∈ [0,100]^n; it may raise task t to any y_t ∈ [x_t, c_t] (cap c_t; here
c_t = 100, the `ceil` cap), all rivals fixed. Let τ = best rival value under the rule, ε = 1e-3, **b = τ + ε**; the target is "first" iff f(y) ≥ b.
Measures: K = #tasks raised, L1 = Σ(y−x), Linf = max(y−x). Each is minimised **separately** (the minimiser of one is generally not the minimiser of another).
Everything below is checked per target in `results/theory_validation.csv` (script `src/theory_validate.py`, summary `results/theory_validation_summary.json`).

**M (mean, f = average).** Let R = n·b − Σx (deficit), h_t = c_t − x_t (headroom).
- M1. L1 = max(0, R) if Σh ≥ R, else infeasible. L1 does not depend on how the points are placed. (L1 = n·(gap+ε), gap = τ − f(x).)
- M2. K = least k such that the k largest headrooms sum to ≥ R. K depends on caps (not on rule gap alone): K = 1 iff max h ≥ R.
- M3. Linf = the water level d with Σ_t min(d, h_t) = R; equals R/n = gap+ε iff no task saturates at its cap.
- Consequence: at fixed per-task gap, L1 grows linearly in n; K and Linf do not.

**N (min, f = min_t x_t).**
- N1. K = #{t : x_t < b}; L1 = Σ_t (b − x_t)⁺; Linf = b − min_t x_t. Infeasible iff some x_t < b and c_t < b.
  *K = n only when every task is below the best rival's minimum; it is not n in general.*

**D (median).**
- D1 (ceil cap, any n). Raising the k lowest tasks to the ceiling is optimal; K = least k such that the median of
  z_k = (the n−k largest scores, plus k copies of 100) is ≥ b.
- D2 (n odd). With c = #{t : x_t ≥ b}, K = max(0, (n+1)/2 − c); L1 = Σ (b − x_t) over the K largest scores below b; Linf = b − (the K-th largest score below b).
  *The blanket statement "median needs ⌈n/2⌉+1 (resp. (n+1)/2) tasks" is false*: tasks already ≥ b count, so K can be anything in 0…(n+1)/2.
  In the data K equals ⌊n/2⌋+1 for only 17.9 % (HELM, n=57) and 0.9 % (OLLB, n=6) of targets.
  For n even (OLLB, n=6) only K (D1) is validated in closed form; L1/Linf for the median are the solver's (brute-force-tested in `tests/`).

**What is not covered by a closed form** (solver-only, validated against brute force on small random instances in `tests/`): geometric / power means with
caps (water-filling by bisection), trimmed means (MILP), Borda, Copeland/Condorcet-winner and plurality (MILP, `src/mti/ordinal.py`).

## Validation result (ceil cap, targets with rank_mean > 1; tolerance: L1 1e-6, K exact, Linf 2e-6 = solver bisection tolerance)
See `results/theory_validation_summary.json`: 0 mismatches in every (dataset, rule, measure) cell — HELM (78 targets, n=57) and OLLB (4495 targets, n=6),
mean/min/median. Rows with `capped_task_in_solution=True` mark mean-Linf targets where a task saturates at 100 (water-level case of M3, so Linf > gap+ε): 75 of 78 HELM targets (many MMLU subjects are near 100) and 149 of 4495 OLLB targets.
Validated only at the `ceil` cap; the closed forms with general caps follow by replacing 100 by c_t (not separately tested, the solver is).
