# Isolated adversarial theory audit

## Findings, ordered by significance
1. **Median L1 boundary hole:** `h-q` can be negative for a baseline winner; the stated cheapest-crossing sum is then undefined. Use `r=max(0,h-q)`, an empty sum for `r=0`, and an explicit infeasibility branch. Strict median must recompute both the count and eligible candidates.
2. **Counterexample convention hole:** the supplied K values certify **shared first**, not both conventions. In particular, examples C and D below lose their advertised separations under unique first. There are six records but only four distinct matrices.
3. **Attainment sharpening:** for feasible mean or median strict-first magnitude optimization, if the baseline is not already strict, the infimum is **never** attained, not merely “generally” unattained. This statement must not be extended to discontinuous Borda.
4. **Support quantifiers:** endpoint reduction is exact for minimum support/at-most-k feasibility. Exact selected-support statements require positive headroom; it does not optimize L1.

| Assemble claim | Verdict |
|---|---|
| 1. Endpoint support reduction | HOLDS for mean, conventional odd/even median, and Borda, shared or unique first |
| 2. Mean support and magnitude | HOLDS; make feasibility and strict nonattainment explicit |
| 3. Odd-median plateau | HOLDS for fixed baseline and convention on the feasible rho domain |
| 3. Odd-median magnitude | HOLDS AFTER boundary/feasibility repairs below |
| 4. Borda covering and pruning | HOLDS, including updates to rivals; numerical solver certification is not established here |
| 5. No universal support ordering | HOLDS for shared first by exact certificates below; unique-first extension is not established |

## Plan Briefly
- Type: finite optimization, order statistics, and discontinuous rank aggregation.
- Goal: audit the Assemble claims, not implement or certify empirical computations.
- Strategy: derive exact feasibility/cost statements from monotonicity and counting, then certify the proposed rational counterexamples by explicit inequalities.
- Subgoals: endpoint/support quantifiers; mean including strict boundaries; odd-median feasibility and magnitude; Borda covering/pruning; exact support-order counterexamples and tie scope.

## Scope
Task sources used: the Assemble portion of `/work/theory.md`, `/work/artifacts/counterexamples.json`, and `/work/code/counterexamples.py` solely to resolve the examples' winner convention. No web, code execution, implementation edits, or empirical artifacts are used as proof. All task-file output is confined to this report. Proof-workflow checks are manual, without helper-script execution or extra task-file access. Scope disclosure: the source read window also exposed the short trailing Audit/Reflect paragraphs; they were excluded from the mathematical evidence.

## Try Candidates / Proof Artifact

| Candidate | Independent route | Internal rounds | Verdict |
|---|---|---:|---|
| C1 | Coordinatewise cardinal monotonicity; pairwise Borda margin monotonicity | 2 | sound, with actual-support quantifiers |
| C2 | Largest-capacity bound plus continuous filling for mean | 2 | sound; strict nonattainment is unconditional when baseline is not strict |
| C3 | Count threshold crossings for odd median; select cheapest eligible crossings | 3 | repair: nonnegative deficit, explicit feasibility, strict counts/candidates |
| C4 | Integer doubled-point covering and retention of an original maximum rival | 2 | sound for both winner conventions |
| C5 | Exact rational capacities and single-rival Borda lower bounds for all four distinct matrices | 3 | sound for shared first; unique-first scope must not be inferred |

Verified claims: endpoint reduction concerns minimum support, not magnitude; mean and odd-median strict magnitude infima are never attained unless the baseline is already strict; Borda rivals must be updated; the pruning bound is safe; the six records use four distinct shared-first examples. Exact Borda baseline score vectors are A=(10,21,5,24), B=(10,18,12,20), C=(9,13,22,16), D=(8,16,23,13). Against a selected leading rival, improvement-coefficient vectors are respectively (3,5,5,7,6), (4,0,8,7,8), (7,4,5,6,5), and (7,8,5,0,8). Their deficits are 14, 10, 13, and 15. These supply exact lower bounds, not empirical evidence.

Negative attempts excluded: freezing Borda opponents; extending endpoint reduction to L1; using shared threshold counts for strict median; reading shared-first counterexamples as unique-first certificates.

## Assemble: clean proofs and exact repairs

### 0. Common hypotheses and estimands

Take integers `m>=2`, `n>=1`, scores `S in [0,1]^(m x n)`, fixed rival raw scores, fixed target baseline `x`, and `x_j<=y_j<=c_j=x_j+rho(1-x_j)`, `0<rho<=1`. Let

- `J={j:c_j>x_j}` be the positive-headroom coordinates;
- `K_* = min{ |supp(y-x)| : y wins }`, with `K_*=+infinity` if no winning vector exists;
- `M(y)=(1/n) sum_j(y_j-x_j)` be the normalized L1 gain.

A magnitude infimum over an empty feasible set is `+infinity`, not the displayed finite threshold cost. State whether first place is shared (`>=`) or unique (`>`). Define normalization by `n` explicitly. All comparisons below are exact real/integer comparisons, without tolerances.

### 1. Endpoint support reduction — HOLDS

For any actual support `A=supp(y-x)`, define `e(A)_j=c_j` on `A` and `x_j` elsewhere. Necessarily `A subset J`, and `e(A)>=y` coordinatewise with exactly the same actual support.

The mean is coordinatewise nondecreasing. Every order statistic is also coordinatewise nondecreasing: increasing coordinates cannot reduce the number above any fixed threshold, and thus cannot reduce any ordered coordinate. This proves monotonicity of both odd medians and the average of the two middle coordinates for even n. Rival cardinal aggregates stay fixed.

For Borda, write the doubled pair contribution as

`p(t,a)=2*1[t>a]+1[t=a]`.

It is nondecreasing in t, and `p(t,a)+p(a,t)=2`. Raising the target therefore increases each of its pair contributions and decreases the corresponding rival contribution by the same amount. All rival-vs-rival terms are fixed. For every rival r, the target-minus-rival aggregate margin is nondecreasing. This proof covers exact ties and both winner conventions.

Consequently, every winning vector with support A has a winning endpoint vector on A; conversely every endpoint vector is admissible. Equivalently,

`K_* = min{ |A| : A subset J and e(A) wins }`.

For each k, a winner using at most k edits exists iff a winning endpoint subset of cardinality at most k exists. The full endpoint vector wins iff any admissible vector wins. If subsets outside J are allowed as binary bookkeeping, their endpoint support is `A intersect J`; zero-headroom coordinates can be deleted without changing the vector or winner, so the minimum remains unchanged.

**Exact repair:** explicitly quantify subsets over J, or explicitly state that their cardinality is bookkeeping and minimizers omit zero-headroom coordinates. Do not infer that endpoints minimize magnitude, or that padding a subset with frozen coordinates realizes that exact actual support.

### 2. Mean — HOLDS, with a sharper strict statement

Let `T=max_{r!=i} mean(S_r)`, `D=n*T-sum_j x_j`, and let `d_[1]>=...>=d_[|J|]>0` be the capacities. Write `C_0=0`, `C_k=sum_{a=1}^k d_[a]`.

The fully quantified formulas are

- shared first: `K_*=min{0<=k<=|J|: C_k>=D}`;
- unique first: `K_*=min{0<=k<=|J|: C_k>D}`.

An empty minimum means infeasible. In particular, shared `K_*=0` iff `D<=0`, and unique `K_*=0` iff `D<0`; a tied baseline (`D=0`) is not already a unique winner. Any k-coordinate intervention gains at most C_k, and the top-k endpoint intervention gains exactly C_k. This proves both directions, including infeasibility.

For shared first, if feasible,

`min M = max(0,D)/n = max(0,T-mean(x))`.

The mean inequality supplies the lower bound. For `D>0`, take the smallest k with `C_k>=D`, fill the first k-1 capacities, and put `D-C_{k-1}` into the kth coordinate. This final amount lies in `(0,d_[k]]`, so the vector has exactly support-optimal cardinality k. For `D<=0`, use the unedited vector.

For unique first:

- if `D<0`, minimum zero is attained at the baseline;
- if `D>=0` and `C_|J|>D`, the infimum is `D/n` and is **not attained**;
- if `C_|J|<=D`, the problem is infeasible.

For the middle case, choose total gain `D+epsilon` within the available capacities and let epsilon decrease to zero. Every strict winner must have total gain strictly greater than D, proving nonattainment. The same infimum can be approached within a support-optimal top-capacity set, since its capacity strictly exceeds D.

**Exact repair:** replace “generally only an infimum” by “an unattained infimum whenever the baseline is not already a unique winner and unique victory is feasible.” Keep feasibility separate; do not report a finite magnitude for an infeasible strict problem.

**Independent continuity check (also covers even median):** let f be the target mean or conventional median, and suppose f(x)<=T but f(y)>T. The function `t -> f(x+t*(y-x))` is continuous. Thus some t<1 sufficiently close to 1 still gives strict victory, stays inside the admissible box, and has strictly smaller M because M(y)>0. Hence no strict magnitude minimizer exists, even conditional on any fixed nonempty actual support: positive t preserves that support. This proves the nonattainment assertion without relying on the special formulas; it does not supply an even-median cost formula.

### 3. Odd median — plateau HOLDS; L1 needs explicit edge cases

Let `n=2h-1`, and `T=max_{r!=i} median(S_r)`.

#### Shared first

Define

`q_ge=#{j:x_j>=T}`,

`R_ge={j:x_j<T and c_j>=T}`,

`r_ge=max(0,h-q_ge)`.

Then `K_*=r_ge` if `|R_ge|>=r_ge`, and `K_*=+infinity` otherwise. For `r_ge=0`, the first branch always applies and the baseline wins.

A median is at least T iff at least h entries are at least T. Existing qualifying entries cannot be lost by upward edits; each newly qualifying coordinate must come from R_ge. Hence at least r_ge coordinates must cross, and raising any r_ge eligible coordinates to T suffices.

If feasible, let `a_[1]<=...<=a_[|R_ge|]` be the costs `T-x_j` for j in R_ge. The exact magnitude formula is

`min M=(1/n) sum_{a=1}^{r_ge} a_[a]`,

with the empty sum defined as zero. Every winner must newly qualify at least r_ge coordinates and pay their threshold deficits; raising the r_ge cheapest eligible coordinates exactly to T attains the bound. This magnitude optimum also has support-optimal cardinality.

#### Unique first

Recompute, rather than reuse the shared count:

`q_gt=#{j:x_j>T}`,

`R_gt={j:x_j<=T and c_j>T}`,

`r_gt=max(0,h-q_gt)`.

Then `K_*=r_gt` iff `|R_gt|>=r_gt`; otherwise unique victory is infeasible. These are genuinely different candidate/count conditions: coordinates at x_j=T do not already qualify, and ceilings at c_j=T cannot cross strictly.

If feasible, sort the boundary costs `b_j=T-x_j>=0` over **R_gt only**. If `r_gt=0`, minimum zero is attained at the baseline. If `r_gt>0`,

`inf M=(1/n) sum_{a=1}^{r_gt} b_[a]`,

and it is **never attained**. A strict winner needs at least r_gt new entries strictly above T, so its total gain strictly exceeds the sum of the r_gt cheapest boundary costs. Conversely, for the cheapest r_gt candidates take `y_j=T+epsilon_j` with `0<epsilon_j<c_j-T` and let all epsilon_j tend to zero. This approaches the bound using support-optimal cardinality. In particular an infimum of zero need not mean zero edits or an attained optimum.

#### Plateau quantifier and boundary repairs

Hold S, x, the target, T, and the winner convention fixed while varying rho. Then q and r do not depend on rho. Eligibility can change with rho, so feasibility can change; **on the feasible rho domain** the minimum support remains the same r. This is the precise plateau statement, not a claim of unconditional feasibility or independence under changes to the task/model cohort or median convention.

For a shared crossing with `x_j<T`, eligibility is

`rho >= (T-x_j)/(1-x_j)`.

For a strict crossing with `x_j<=T<1`, eligibility is the strict inequality with the same right side. Equality at the admissible ceiling is therefore allowed for shared first but not unique first. If `T=1`, unique median victory is impossible under these bounds.

**Concrete baseline hole:** for three tasks, target `(1,1,1)` and rival `(0,0,0)`, h=2 and q_ge=3. The original phrase “the h-q cheapest” requests minus one costs, although the correct magnitude is zero. The nonnegative r and empty-sum convention repair this.

**Concrete tie-count warning:** for target `(1/2,1/2,0)` and rival `(1/2,1/2,1/2)`, rho=1, shared first has K=0. Unique first has q_gt=0 and K=2, with unattained magnitude infimum zero. Keeping the shared count would incorrectly identify a baseline strict winner.

**Exact repair:** replace the L1 paragraph with the two feasible formulas and their baseline/infeasible branches above. The odd-median formula must not be applied to even n. Endpoint subset enumeration remains exact for even n because Claim 1 still applies, but a count of crossings at T does not characterize an even median.

### 4. Borda binary covering and pruning — HOLDS

Let `B_i` and `B_r` denote baseline totals in doubled points. For each task j, let `ell_rj` be the decrease in rival r's doubled pair contribution against the target at the endpoint. Then

`ell_rj in {0,1,2}`, `g_j=sum_{r!=i} ell_rj`.

The latter identity follows from pairwise complementarity and is a useful independent check; these quantities do not depend on what other tasks are selected. Rival-vs-rival comparisons do not change. Thus for endpoint choices z,

`B_i(z)=B_i+sum_j g_j*z_j`,

`B_r(z)=B_r-sum_j ell_rj*z_j`.

The exact support covering is therefore

`min sum_j z_j`

subject to, for all r != i,

`sum_j (g_j+ell_rj)*z_j >= B_r-B_i+delta`,

where `z_j in {0,1}`, and `delta=0` for shared first or `delta=1` for unique first. The unique-first increment is exactly one **doubled** point because every total and margin is integral. Use J only, or note that zero-effect choices are discarded by minimization. Claim 1 turns this endpoint program into the original continuous minimum-support problem.

For pruning, fix an original maximum rival r_star with baseline total Bmax. It remains in the retained set, and under every admissible edit,

`B_r_star(y) >= Bmax-2n`.

An omitted rival satisfies

`B_r(y) <= B_r < Bmax-2n <= B_r_star(y)`.

Thus a target that weakly or strictly beats all retained rivals necessarily beats every omitted rival. The reverse direction is automatic because retained constraints are a subset. This proves exactness for both winner conventions and all ties. The originally leading rival need not remain the leading rival; the proof requires only its lower bound and retention. Rows at equality are retained by the proposed rule, so there is no boundary omission.

**Exact repair:** no change to the mathematical covering or pruning is needed. Keep the “fixed rival raw scores, not fixed rival Borda totals” distinction explicit. Exhausting all 64 subsets for six tasks is mathematically exact only when the comparisons are exact; the existence of such an algorithm does not certify a particular numerical run. The HiGHS/gap/witness narrative is not a formal proof of optimum and is neither verified nor used here.

#### Attainment is rule-specific

The continuous-cardinal strict nonattainment result must not be applied to Borda. For example, with two tasks, rho=1, target `(0,1)` and sole rival `(1/2,0)`, unique Borda victory first occurs at target `(1/2,1)`. The normalized magnitude minimum `1/4` is attained, although the baseline is only tied. Conversely, for target `(0,0)` and rival `(1/2,1)`, shared Borda victory is achieved by `(1/2+epsilon,0)`. Its magnitude infimum is `1/4`, but no vector with that magnitude wins. These examples show why neither strictness alone nor a shared weak inequality resolves Borda attainment.

### 5. No universal support ordering — exact shared-first certificates

The checker `exact_K` tests `v[0]>=max(v[1:])`, so its convention is shared first. Its exact median is the middle order statistic, valid for these odd five-task matrices only. I did not run it, import its dependencies, or assume its asserted values are proofs. The following exact inequalities independently certify the values in the JSON.

There are four distinct matrices, each displayed as integer numerators divided by 8. Target is row 0; rho=1, so every edited target coordinate becomes 8/8. Tasks in the certificates below are **1-based**; rival row labels remain 1,2,3.

```text
A (JSON records 1 and 2)
  [7,1,5,4,1]
  [7,0,8,7,8]
  [4,1,4,4,1]
  [8,6,6,5,5]

B (JSON records 3 and 4)
  [4,3,1,5,0]
  [3,1,3,8,5]
  [2,0,2,7,6]
  [7,0,5,6,6]

C (JSON record 5)
  [1,4,2,1,2]
  [6,1,8,8,1]
  [7,7,7,2,6]
  [8,3,1,8,2]

D (JSON record 6)
  [6,1,2,5,0]
  [7,2,8,2,1]
  [7,7,5,4,5]
  [8,2,0,0,2]
```

#### Mean certificates

Sums, deficits, and capacities in this table are integer eighth-units; dividing by the common task count is unnecessary for winner comparisons.

| Matrix | Target sum | Maximum rival sum | Deficit | Largest capacities descending | Exact K | Winning endpoint tasks |
|---|---:|---:|---:|---|---:|---|
| A | 18 | 30 | 12 | 7,7,4,3,1 | 2 | {2,5} |
| B | 13 | 24 | 11 | 8,7,5,4,3 | 2 | {3,5} |
| C | 10 | 29 | 19 | 7,7,6,6,4 | 3 | {1,3,4} |
| D | 14 | 28 | 14 | 8,7,6,3,2 | 2 | {2,5} |

The relevant maximal insufficient prefix sums are respectively 7<12, 8<11, 14<19, and 8<14; the next prefix sums are 14,15,20,15 and suffice. These are both exact lower bounds and feasible upper bounds by Claim 2.

#### Median certificates

Median entries and T in this table are also in eighth-units; h=3.

| Matrix | Baseline target median | T | q_ge | Exact K=3-q_ge | Winning endpoint tasks |
|---|---:|---:|---:|---:|---|
| A | 4 | 7 | 1 | 2 | {2,5} |
| B | 3 | 6 | 0 | 3 | {1,2,3} |
| C | 2 | 7 | 0 | 3 | {1,3,4} |
| D | 2 | 5 | 2 | 1 | {2} |

Every indicated candidate can reach 8; the crossing count gives necessity and sufficiency, not just an observed search result.

#### Borda certificates

All entries below are exact **doubled** Borda points. For a chosen baseline leading rival r_star, set `a_j=g_j+ell_r_star,j` and `d=B_r_star-B_0`.

| Matrix | Baseline (B0,B1,B2,B3) | r_star | (a1,a2,a3,a4,a5) | d | Insufficient-support lower bound |
|---|---|---:|---|---:|---|
| A | (10,21,5,24) | 3 | (3,5,5,7,6) | 14 | Any 2 edits gain at most 7+6=13<14 |
| B | (10,18,12,20) | 3 | (4,0,8,7,8) | 10 | Any 1 edit gains at most 8<10 |
| C | (9,13,22,16) | 2 | (7,4,5,6,5) | 13 | Any 1 edit gains at most 7<13 |
| D | (8,16,23,13) | 2 | (7,8,5,0,8) | 15 | Any 1 edit gains at most 8<15 |

These necessary single-rival inequalities lower-bound **all continuous interventions** by endpoint reduction. Here are upper-bound witnesses with all rival totals updated:

| Matrix | Endpoint tasks | Updated (B0,B1,B2,B3) | Exact Borda K |
|---|---|---|---:|
| A | {2,4,5} | (22,18,2,18) | 3 |
| B | {3,5} | (22,14,8,16) | 2 |
| C | {1,4} | (18,10,18,14) | 2 |
| D | {2,5} | (20,12,19,9) | 2 |

Thus the shared-first support triples `(mean,median,Borda)` are exactly

`A=(2,2,3), B=(2,3,2), C=(3,3,2), D=(2,1,2)`.

All baseline target sums, medians, and Borda totals are strictly below a rival maximum, as the tables show. The target is therefore initially a nonwinner under every rule. The six ordered inequalities are:

- A: mean < Borda and median < Borda;
- B: mean < median and Borda < median;
- C: Borda < mean;
- D: median < mean.

For every unordered pair of rules, examples exist in both directions. This exactly refutes either universal shared-first support dominance direction for that pair. One fixed admissible rho=1 already suffices to refute a statement universal over instances and rho. Precisely, the quantifier is “for each ordered pair, there exists an admissible instance with strict inequality,” not “one instance realizes all inequalities,” nor “for every fixed rho or every fixed dimension there are such examples.” No probabilistic or empirical assertion is involved.

#### Unique-first scope — a real limitation of these certificates

Under unique first the support triples for these same matrices instead are

`A=(2,3,3), B=(2,3,2), C=(3,3,3), D=(2,2,2)`.

For example C's largest two Borda coefficients sum to 13, but uniqueness needs 14 against row 2. Three tasks suffice (e.g. {1,2,4}), so its Borda support rises to 3. In D only one baseline entry is strictly above T=5/8, so unique median victory needs two crossings rather than one. In A no baseline entry is strictly above 7/8, so its unique median support is 3. The remaining values follow from the same strict mean prefixes, crossing counts, and displayed strict Borda witnesses.

Therefore the supplied examples do not establish a no-ordering theorem for unique first. This does not prove that a separate unique-first non-ordering theorem is false; it identifies the exact missing evidence/argument if that stronger theorem is intended.

**Exact repair:** state Claim 5 as: “For shared-first minimum support, the six ordered-pair records in the JSON, using four distinct dyadic-rational matrices, prove no universal pairwise support ordering. No unique-first extension is claimed here.”

## Audit

- **audits-run:** one isolated local clean-proof audit, with a second direct task-by-task recount of every displayed Borda witness. No independent reviewers or machine proof checker were used.
- **Checked boundaries:** n=1; zero-headroom coordinates; zero-edit winners; baseline ties; capacity exactly equal to the mean deficit; shared ceilings exactly T versus strict ceilings T; T=0 and T=1; infeasible candidate sets; zero strict infimum with positive support; odd/even median scope; equality at the pruning cutoff.
- **Checked quantifiers:** arbitrary continuous edit to endpoint support; at-most-k versus actual exact support; feasible-rho-only plateau; minimum versus infimum; one counterexample per ordered pair, with shared-first convention explicit.
- **Checked arithmetic:** all four integer-numerator matrices; capacity lower bounds; threshold counts; doubled Borda baseline totals, pair-gain coefficients, and full-rival witness totals. All certificates are symbolic counting/inequality arguments with exact rational data, not empirical outputs.
- **critical-issues:** median L1 needs the baseline/infeasibility branches; Claim 5 needs explicit shared-first scope and the four-distinct-matrix correction.
- **remaining-gaps:** none for the repaired shared-first statements or the stated mean/median strict formulas. A separate unique-first no-ordering theorem remains unproved if intended. Numerical solver optimality claims remain outside this mathematical audit.
- **Manual phase validation:** plan specifies type/goal/strategy/subgoals; candidate claims have independent arguments; the assembled proof includes every boundary branch; this audit checks the clean proof rather than search traces. Helper validators were not executed under the restricted reading/no-implementation scope.

The original source and implementation are unchanged. Return the listed mathematical wording repairs to the author; do not treat the entire original, convention-unqualified collection as certified without them.

## Reflect

- Successful pattern: prove margin monotonicity before endpoint enumeration, and give matching exact lower bounds and full-rival witnesses for every support value.
- Failed pattern to avoid: inferring attainment from a weak winner inequality, or transferring shared-first counts/counterexamples to unique first without recalculation.
- memory-persisted: false; no profile or observation memory was changed. The requested report is the sole task artifact.

## Final disposition

final-status: HANDED_OFF

The audit is complete. Claims 1, 2, and 4 hold with the stated boundary precision; Claim 3 holds after its explicit magnitude branches are repaired; Claim 5 is proved for shared first by exact certificates. The source wording repairs are handed back to the author, with no implementation changes. No proof of a separate unique-first no-ordering theorem or numerical solver optimality is claimed.


