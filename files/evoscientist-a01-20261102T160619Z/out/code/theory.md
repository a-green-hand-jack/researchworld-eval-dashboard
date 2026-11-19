# Mathematical development and audit target

## Plan briefly
Type: finite optimization / order statistics. Goal: characterize minimum support and delimit magnitude claims. Strategy: prove monotonic endpoint reduction, derive rule-specific formulas, refute universal ordering with finite exact counterexamples. At most five subgoals: endpoint reduction; mean; odd median; Borda; non-dominance and magnitude boundaries.

## Try candidates
| Candidate | Idea | Internal rounds | Verdict | Issue or reason |
|---|---|---|---|---|
| C1 | Coordinate monotonicity and endpoint replacement | 2 | sound | Borda aggregate rivals change, but target-minus-rival margins are monotone |
| C2 | Mean: sort capacities | 1 | sound | Exact for support, not all rules |
| C3 | Odd median: count threshold crossings | 2 | sound | Requires explicit shared/strict convention; even median handled by exhaustive subsets |
| C4 | Borda fixed opponent aggregate threshold | 1 | fail | An edited target displaces rivals; must include rival loss |
| C5 | Borda integer margin-gain covering | 2 | sound | Include task-level half ties via doubled integer points |
| C6 | Endpoint magnitude equals minimum L1 | 1 | fail | Endpoint theorem only solves support; partial edits can cost much less |

## Assemble: definitions
Let S in [0,1]^(m x n), m>=2. Target i has x_j; bounded positive improvements x_j<=y_j<=c_j=x_j+rho(1-x_j), 0<rho<=1. Opponents' raw scores stay fixed. Investment K=||y-x||_0, not a resource-cost model. Shared first means aggregate at least all opponents; unique first uses >. Cardinal rules are mean and conventional sample median (average of middle two for even n). Borda uses b_ij=sum_(r!=i) ([s_ij>s_rj]+0.5[s_ij=s_rj]); total across tasks, normalization does not affect winner.

### Claim 1 (endpoint support reduction)
For mean and median, replacing a selected coordinate with a larger value cannot lower the target's aggregate; rival aggregates are constant. For Borda, raising the target weakly increases its pair points against every rival and weakly decreases that rival's pair points against the target, leaving all other rival-vs-rival comparisons fixed. Thus every target-minus-rival margin is nondecreasing. Given any winning edit vector with support A, set y_j=c_j for j in A and y_j=x_j otherwise. It still wins, with no more edits. Conversely an endpoint winning vector is admissible. The minimum support is therefore exactly the minimum cardinality feasible endpoint subset. This holds for shared and unique first, and certifies infeasibility by testing the full endpoint vector.

Boundary: x_j=c_j=1 cannot be an improved coordinate; an optimizer never needs such a zero-gain edit. Empirical witness validation checks this explicitly. The lemma does not claim anything about minimum sum of gains.

### Claim 2 (mean)
Let T=max_(r!=i) mean(S_r), d_j=c_j-x_j, and D=nT-sum_j x_j. For shared first, K=0 if D<=0; otherwise K=min{k: sum_(j=1)^k d_[j]>=D} with d sorted descending. If no such k, infeasible. Proof: any k coordinates have capacity at most the sum of the k largest capacities, and that capacity is attained by the corresponding endpoint edit. Strict first replaces >=D with >D, including K=0 if baseline strictly wins.

Minimum normalized L1 gain over all supports for shared first is max(0,T-mean(x)) when feasible: all aggregates require that gain, and it can be filled continuously inside admissible capacities. This is also achievable with a support-optimal set by filling the last used coordinate partially. For strict first when not already a strict winner, the same expression is an unattained infimum whenever unique victory is feasible, not an attained minimum.

### Claim 3 (odd median: plateau)
Let n=2h-1 and T=max rival median. Let q=#{j:x_j>=T}, R={j:x_j<T<=c_j}. If q>=h then K=0. Otherwise K=h-q iff |R|>=h-q, and infeasible otherwise. Necessity: a median >=T requires >=h values >=T and each changed coordinate can increase that count by at most one. Sufficiency: upgrade h-q crossing coordinates. Hence once feasible, K is independent of rho: the baseline crossing deficit h-q is constant, even as admissible ceilings increase. Strict first replaces both >=T by >T, and uses x_j<=T<c_j for crossing candidates. The same plateau conclusion holds.

For shared first, put r=max(0,h-q). If infeasible, the magnitude optimum is +infinity. Otherwise minimum normalized L1 is the sum of the r cheapest T-x_j over j in R, divided by n, with an empty sum equal to zero for baseline winners. Those crossings attain the median threshold and every winning vector must pay at least those crossing deficits. For strict first recompute q=#{x_j>T}, R={x_j<=T<c_j}, and r=max(0,h-q). If infeasible, infimum is +infinity; if r=0, zero is attained at baseline; otherwise the sum of the r cheapest T-x_j over this strict R, divided by n, is an unattained infimum. Even-task median needs a coupled middle-pair condition and cannot use this crossing formula. Exhaustively evaluating all endpoint subsets is exact for six tasks, including median-convention sensitivities.

### Claim 4 (Borda binary covering)
Use doubled points q_ij=2b_ij, integer B_i=sum_j q_ij. Let g_j be target i's doubled-point gain on task j if x_j becomes c_j. For each rival r, let ell_rj>=0 be its doubled-point loss. All depend only on that task and endpoint. For subset indicator z, target score is B_i+sum g_j z_j and rival is B_r-sum ell_rj z_j. Thus the exact support problem is
min sum_j z_j subject to sum_j(g_j+ell_rj)z_j>=B_r-B_i+delta for all r!=i, z_j in{0,1}, with delta=0 shared or 1 unique. A rival loses at most 2 per task. If Bmax=max rival B_r, rivals with B_r<Bmax-2n cannot bind: the originally highest rival still has >=Bmax-2n points after any edits, whereas omitted rivals cannot increase. Keep all rivals at or above that bound. This is exact pruning, not a heuristic frozen-opponent approximation.

Solving the six-task covering by all 64 subsets is exact. HELM uses SciPy/HiGHS numerical MILP with zero reported relative gap, integral witnesses and agreeing numerical lower bounds; these are not formal rational-arithmetic certificates. Independent witnesses use full rivals, not only retained rows.

### Claim 5 (no universal support ordering)
`artifacts/counterexamples.json` contains six records covering four distinct dyadic-rational 4-model/5-task matrices with rho=1, shared first, and target row 0. For each ordered pair of mean, median and Borda, an example has strictly smaller K for the first rule, with every rule's target initially a nonwinner. `code/counterexamples.py` checks K by exact Fraction arithmetic, increasing support size and enumerating every subset at that size. These finite exact constructions refute universal pairwise support dominance under this intervention. They are synthetic mathematical examples, not empirical benchmark results. Search seed and examined cases are recorded only to reproduce the construction; no probabilistic theorem follows from random search.

## Audit
Requested isolated clean-claim review separately; verify endpoint monotonicity includes rivals, strict attainment issues, feasibility conditions, cardinal tolerance and finite exact counterexamples. Numerical empirical results use cardinal tolerance 1e-12 on aggregate scores and integer exact Borda points; separate sensitivity audit at zero and 1e-10. Theoretical statements above use real-number inequalities, not tolerance.

## Reflect
Successful pattern: establish support reduction before selecting algorithms; integer pair margins avoid Borda frozen-rival mistakes. Failed pattern: equating endpoints with magnitude optima. Memory not newly written: existing observation O-2441e24628cd134d already covers those lessons, but main memory preflight had no query hit; the planner independently recalled it. Formal proof status pending independent audit, not a claim of machine verification.
