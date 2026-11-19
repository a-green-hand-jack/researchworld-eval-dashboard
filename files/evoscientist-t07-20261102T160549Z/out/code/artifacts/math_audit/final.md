final-status: REFUTED

## Result

**The intended theorem is correct for deterministic finite predictions, bounded randomized predictions, or suitable integrable randomized predictions. The literal unrestricted “any pilot-randomized vector” wording needs a moment assumption; the counterexample below refutes that wording only.** If q is implicitly in [0,1]^N, this qualification is automatic.

**Implementation verdict:** `direction`'s honest output and `crossfit`'s first output implement the theorem under valid stratified uniform sampling, in exact arithmetic. No pilot/audit-membership preprocessing leak was found. This does not certify that the runner's coupled finite seed grid is itself the theorem's exact conditional randomization law.

## Proof / Report

### 1. Precise theorem and clean proof [L1–L4]

Fix the sources, all item covariates, a partition U=disjoint union of U_h, and labels y. Let N=sum_h N_h and mu=N^-1 sum_i y_i. Freeze any source-only allocation choices as well. Write P=union_h P_h, A=union_h A_h, M_h=N_h-p_h and R_h=U_h minus P_h.

Let W be exogenous learner randomness, independent of audit draws conditional on P, and let G_P contain P and W, with fixed quantities implicit. Conditional on G_P, the **entire** q^P vector must be fixed, not just its pilot entries. A_h is then an independent uniform a_h-subset of R_h. This follows directly by counting admissible disjoint pairs: for each fixed P_h, every a_h-subset of its complement has the same pair probability. Learner randomness cannot change this conditional law.

Set e_i=y_i-q_i^P and bar(e)_h=M_h^-1 sum_{i in R_h} e_i. Inclusion probability a_h/M_h gives

    E_A[ mean_{i in A_h} e_i | G_P ] = bar(e)_h.

Consequently, for the stated estimator,

    E_A[T(P→A) | G_P]
      = (sum_{i in P} y_i + sum_{i not in P} q_i^P
         + sum_h sum_{i in R_h}(y_i-q_i^P))/N
      = mu.

This is a finite-design averaging identity for every realized finite q^P. If E|T(P→A)|<infinity, the tower property gives E T(P→A)=mu. A convenient sufficient condition is E sum_i |q_i^P|<infinity; finite deterministic predictions automatically suffice because there are finitely many possible pilots. Do not invoke the tower property without first moments.

For M_h>1 define the residual finite-population variance

    S²_{e,h}(P,W) = sum_{i in R_h}(e_i-bar(e)_h)²/(M_h-1).

The directional conditional variance is exactly

    Var_A(T(P→A) | G_P)
      = (1/N²) sum_h [ M_h²/a_h · (1-a_h/M_h) · S²_{e,h}(P,W) ].       (1)

Indeed, for audit indicators I_i in a complement of size M and audit size a,

    Var(I_i)=a(M-a)/M²,
    Cov(I_i,I_j)=-a(M-a)/(M²(M-1)),  i≠j.

Expanding Var(a^-1 sum_i I_i e_i) gives (1-a/M)S²_e/a; conditional independence across strata then proves (1). If M_h=1, positivity forces a_h=1: define that summand as zero, without dividing by M_h-1. Any complement census a_h=M_h has zero variance and gives the exact stratum total.

If conditioning only on P, average the right side of (1) over learner randomness; its conditional mean is always mu, so there is no between-learner-mean term, provided the needed second moments exist. Under second moments the marginal directional variance is likewise the expectation of (1).

Fit q^A separately using only A,y_A and allowable fixed inputs. Repeat the proof after exchanging p_h and a_h. Hence, under first moments,

    E[(T(P→A)+T(A→P))/2] = mu.

**Fixed half averaging remains unbiased when sizes differ**, within or across strata. Neither equal sizes nor independence of the directions is needed. It need not reduce to the ordinary pooled sample mean when p_h≠a_h; that is not an unbiasedness requirement. The half-average is not asserted conditionally unbiased given either pilot, the realized union S=P∪A, or the observed labels.

### 2. Dependence and scope [L7]

The directions reuse the same queried items and labels in opposite roles; labels themselves are fixed in this design-based argument. They are generally dependent. For example, take one stratum, N=4,p=a=1,q=0,y=(1,0,0,0). Then

    T1=(y_P+3y_A)/4,    T2=(y_A+3y_P)/4,
    Var(T1)=Var(T2)=3/32,    Cov(T1,T2)=1/32.

Here E[y_P]=1/4, Var(y_P)=3/16 and Cov(y_P,y_A)=-1/16, which verify these values directly. Thus Var((T1+T2)/2)=1/16, not the independent-fold value 3/64. In general it equals (Var(T1)+Var(T2)+2Cov(T1,T2))/4, when defined. **No independent-fold standard error, calibrated confidence interval, MSE improvement, or broad novelty claim follows.**

### 3. Literal moment loophole and membership counterexample [L5,L8]

For the unrestricted randomized wording, take N=3,p=a=1,y=0 and q_i^P=Z·1{i=3}, where Z is independent standard Cauchy randomness. This uses no audit membership. If P={1}, the two possible audits give T=Z/3 and T=-Z/3. Other pilots give another nonzero Cauchy multiple or zero. Since the event P={1} has positive probability, both positive and negative parts of T have infinite expectation. E T is undefined, although each fixed-Z audit average is zero. Using independent Cauchy seeds in the swapped fits also makes the half-average nonintegrable. The repair is the first-moment condition above, not a change to the estimator.

Independently, unlabeled union preprocessing is not generally safe: with the same N,p,a,y, let q_i^P=1{i in S}, S=P∪A. Then sum_{i not in P}q_i^P=1 and the correction is -2, so T=-1/3 on every draw instead of 0. This violates the stated membership restriction without using audit labels. Some membership-dependent transformations cancel algebraically, but require a separate proof; the general theorem does not cover them.

### 4. Static implementation audit [L6]

- **Strata:** `/work/src/methods.py:13–15` stable-sorts `source.mean(0)` and splits item indices. With source fixed, strata are fixed; ties and source-difficulty sorting are harmless. No target labels enter this construction.
- **Allocation/splitting:** `methods.py:18–34` chooses extra stratum allocations from the seed, then permutes each stratum and takes disjoint pilot/audit prefixes. Under ideal independent uniform permutations, conditioning on the source/seed-only extra allocation gives exactly the required design, including odd budgets. Random allocation sizes can be handled by conditioning first and averaging afterward. They need not be fixed unconditionally.
- **Fit isolation:** `ridge_fit`, `methods.py:37–50`, uses `source[:,pilot].T`, its **pilot-only** covariate mean, and pilot target-label means; alpha is fixed at 10. Neither A nor S=P∪A enters the coefficients or centering. Finite sources and positive ridge penalty give finite deterministic predictions for valid inputs.
- **Full-bank prediction is legal:** `sum_predictions`, `methods.py:57–59`, uses full-bank fixed source covariates. Equivalently, a fixed full-bank source-covariate mean may be used to aggregate predictions. This is not preprocessing fitted on the queried union. Evaluating the already-fixed prediction rule at audit indices is also legal. Replacing pilot source-centering with S-fitted preprocessing would fall outside this proof unless invariance were separately established.
- **Estimator:** `direction`, `methods.py:101–127`, forms `(sum_P y+qsum-sum_P q)/N` and adds `(N_h-|P_h|)/N` times audit residual means. These are the correct actual complement factors, not N_h-|P_h∪A_h|. Its honest output has no final clipping. The separately returned imputation and deliberately contaminated correction are **not** covered by the unbiasedness theorem.
- **Swapping:** `crossfit`, `methods.py:130–134`, refits in reverse and returns the fixed half-average first. Unequal fold sizes do not invalidate it.
- **Input contracts:** Public functions do not fully validate a disjoint covering partition, positive actual fold sizes, aligned labels, or allocation feasibility. `designs` can silently truncate a requested stratum prefix if `nh>N_h`; a positive audit-size assertion alone does not certify the requested budget. The theorem applies to valid **actual** sizes; truncation is a budget-contract problem and may also leave an empty fold. No blanket guarantee for arbitrary malformed calls.
- **Seed/split qualification:** `common.py:21–43` builds source/target groups; frontier/gap selection uses full response scores for evaluator-side stress construction, not source-only inference. `run_experiments.py:46–63,114–120` reuses the experiment seed for row splitting and item design, with five default seeds. For a fixed seed these outputs are deterministic. Offsetting seeds does not prove independent, uniform item draws conditional on a seed-selected source split. Freeze a source split and specify independent uniform item randomization to invoke the exact theorem; the current coupled seed grid alone is not an exact design-unbiasedness certificate. No bias from that grid was established here.
- **Tests:** Ran only the existing `/work/tests/test_methods.py`: **9 passed in 4.58 s**. Exhaustive checks include uniform unequal folds and a census, and a small equal-fold stratified case. The masking test checks audit-label fit isolation, not membership invariance or the variance formula. Tests support the inspected cases, not all designs or PRNG laws. No experiments or implementation edits were performed.

## Audit

- audits-run: One local adversarial audit of the clean report; exact boundary/counterexample checks; source-to-formula trace; nine existing regression tests. No web or code-agent delegation.
- critical-issues: Missing first-moment qualification in the literal unrestricted randomized claim; resolved by the explicit repaired theorem. Exact conditional sampling under the runner's coupled seed grid is not established.
- remaining-gaps: None in the repaired design theorem. No claim of literal finite-seed unbiasedness, general malformed-input safety, or confidence-interval validity.

## Proof Artifact

- positive lemmas: L1–L8 in `proof-artifact.md`; proof routes and revision counts in `candidates.md`.
- negative attempts: Unqualified tower property, independent swapped folds, and inferring exact conditional randomization from seed offsets.

## Reflection

- successful-pattern: Freeze the entire nuisance vector, then use finite-population inclusion probabilities; distinguish algebraic correctness from the actual randomization law.
- failed-pattern: Confusing pointwise conditional averaging with integrable marginal expectation, or treating shared-label folds as independent.
- memory-persisted: false; existing memory already covers the central pilot/audit principle.
- storage-location: /work/artifacts/math_audit/; parent /work/todos.md untouched.
- proposed-memory-updates: None required for this audit.
