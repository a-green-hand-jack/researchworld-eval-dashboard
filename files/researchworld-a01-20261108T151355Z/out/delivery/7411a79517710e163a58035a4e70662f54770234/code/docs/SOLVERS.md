# Minimum-investment problems: exact statements and propositions (appendix-ready)

Notation. Score matrix $X\in[0,100]^{M\times n}$; target $i$ with scores $x=X_{i\cdot}$; rivals $X_{j\cdot}$ ($j\ne i$) are fixed.
The target chooses $y$ with $x_t\le y_t\le c_t$ (cap $c_t\ge x_t$; $c_t:=\max(c_t,x_t)$). Margin $\varepsilon=10^{-3}$ points (all runs).
Investment measures of $y$: $L_1=\sum_t(y_t-x_t)$, $K=\#\{t:y_t>x_t\}$, $L_\infty=\max_t(y_t-x_t)$.

## Problems (one per rule $f$; "first" = strictly above every rival)
* **Score rules** $f:\mathbb R^n\to\mathbb R$ (mean, geometric/harmonic = power means of $y+1$ with $p\to0$ / $p=-1$, median, min, $t$-trimmed mean):
  with $\tau=\max_{j\ne i}f(X_j)$ the target is first iff $f(y)\ge\tau+\varepsilon$.
  $L_1^*=\min\{\sum(y-x):f(y)\ge\tau+\varepsilon\}$, $K^*=\min\{|\{t:y_t>x_t\}|:\dots\}$ (separate optimisations: the $K$-optimal and $L_1$-optimal $y$ differ),
  $L_\infty^*=\min\{d: f(\min(x+d\mathbf 1,c))\ge\tau+\varepsilon\}$ (the uniform "general improvement" strategy; all these rules are monotone, so bisection is exact to 1e-7).
* **Borda / mean rank**: $B_j=\sum_t\big(\#\{k:X_{kt}<X_{jt}\}+\tfrac12\#\{k\ne j:X_{kt}=X_{jt}\}\big)$; first iff $B_i-B_j\ge\tfrac12$ for all $j$ (half-point granularity ⇒ strict).
* **Condorcet winner**: first iff for every rival $j$ the target wins strictly more than $n/2$ tasks (ties count $\tfrac12$ per task). Being Condorcet winner is *sufficient* for first
  under any Condorcet-consistent rule (Copeland, Schulze, Kemeny, …) and hence an *upper bound* of their minimum investment; it is not equivalent to them. `rank_rule` in the result files for this rule is the Copeland rank (pairwise task-majority wins, ties ½) — a ranking proxy, not the rule itself.
* **Plurality**: credit of model $j$ = $\sum_t \mathbf 1[X_{jt}=\max_k X_{kt}]/\#\text{ties}_t$ (first places, ties split); first iff credit$_i-$credit$_j\ge10^{-4}$ for all $j$.

Discretisation for rank rules: raising task $t$ to level $s$ changes the target's pairwise outcome only when $s$ crosses or ties a rival score, so only levels $\{s_{kt}\}$ (tie, half credit) and $\{s_{kt}+\varepsilon\}$ (strict pass) need be considered; the problem is then a 0/1 program with ≤1 level per task, solved exactly by MILP (HiGHS via `scipy.optimize.milp`) with lazily added rival constraints.

**Encodings in result files.** `inf` = proven infeasible (no $y\le c$ makes $i$ first); `NaN` = solver time limit / numerical failure ("censored", never counted as infeasible); `status ∈ {ok, infeasible, censored}`, `feasible` boolean. Rows with $K=0$ are targets that are already first under that rule.
Files written before these columns existed were completed by `src/finalize.py`; their infeasible rows are exact (closed-form or MILP infeasibility), but MILP time limits were not recorded by that code version (only trimmed-mean/ordinal MILPs have time limits; those were all re-run).

## Propositions (status: P = proved here, N = also checked numerically; code in `src/theory_checks.py`, `tests/`)
Let $b=\tau+\varepsilon$ and $H_t=c_t-x_t$ the headroom.

* **P1 (mean)** [P, N]. $L_1^*=\max(0,\,nb-\sum x)$ if $\sum_t H_t\ge nb-\sum x$, else infeasible. $K^*$ = smallest $k$ such that the $k$ largest headrooms sum to $\ge L_1^*$.
  If no cap binds, $L_\infty^*=b-\bar x$ and $L_1^*=n\,L_\infty^*$: under the mean, spreading the investment costs exactly as much total score as concentrating it; targeting buys breadth (small $K$), not points.
  *Proof.* The mean is linear: $\bar y\ge b\iff\sum(y-x)\ge nb-\sum x$; any $y$ with that total and $y\le c$ is feasible. $K$: fill the largest headrooms first. ∎ (checked: solver = formula, max abs deviation 0 on HELM, 79 targets, `results/theory_checks.csv`; the $L_\infty$ identity only where no cap binds, 4 of 79 HELM targets under `ceil`.)
* **P2 (min)** [P, N]. Feasible iff $c_t\ge b$ for all $t$; then $L_1^*=\sum_t(b-x_t)^+$, $K^*=\#\{t:x_t<b\}$, $L_\infty^*=\max_t(b-x_t)^+$. Hence $L_1^*\le nL_\infty^*$, with equality iff all tasks are equally short. ∎
* **P3 (median, $n$ odd)** [P, N]. With $m=(n+1)/2$: feasible iff at least $m$ tasks have $c_t\ge b$; $K^*=\max(0,m-\#\{t:x_t\ge b\})$ (so $K^*\le m$ whatever the field); $L_1^*$ = sum of the $m$ smallest $(b-x_t)^+$ restricted to tasks with $c_t\ge b$. *Proof.* median $\ge b$ iff at least $m$ coordinates $\ge b$; each task can be lifted to exactly $b$ at cost $(b-x_t)^+$. ∎ For even $n$ (OLLB, $n=6$) the median is the mean of the two middle scores; the solver enumerates the pair of threshold levels $(a,\bar a)$, $a+\bar a\ge2b$ (tested against LP grid search).
* **P4 (power means $p<1$, geometric, harmonic)** [P for the $L_1$/$K$ structure, N]. $f(y)\ge b\iff\frac1n\sum g(y_t)\ge g(b)$ with $g$ increasing and concave: $L_1^*$ is a water-filling problem (equalise $y_t+1$ at a level, clipped to $[x_t,c_t]$; bisection on the level), $K^*$ is additive in $g$ so greedy by $g(c_t)-g(x_t)$.
* **P5 (trimmed mean, $t$ per side)** [N only]. No closed form; exact MILP (`trimmed_milp`) verified against an independent $O(n^2)$-binary assignment formulation and against subset enumeration on random instances.
* **P6 (rank rules)** [N only]. Exact MILP verified against brute-force enumeration over all level combinations on small random instances (`tests/test_ordinal.py`).
* **Monotonicity** [P]. All rules above are monotone in the target's own scores, so the feasibility region in the cap box is an up-set; infeasibility under cap $c$ is equivalent to infeasibility at $y=c$ (used by every solver as an early exit, and a *proved* statement: "first is reachable iff the capped-out target is first").
