# Compact clean-proof audit worklog

## Plan / Problem Type
Probability, finite-dimensional regression, concentration inequalities.

## Goal
Audit /work/theory.md only; seek exact counterexamples before repairing statements. No papers, web, experiment code, or other research-task files.

## Strategy
Separate algebraic identities from asymptotic steps and from concentration premises; check dependence, degeneracies, and quantifiers.

## Subgoals
- [x] g1: Oracle identity, projection equality, and no-gain cases.
- [x] g2: Crossfit remainder, balanced weights, ridge rate, reused unlabeled sample, studentization.
- [x] g3: Finite dictionary concentration premise, ranges, simultaneous selection, and edge cases.
- [x] g4: Synthetic moments and required outcome law.
- [x] g5: Severity-ordered report with safe theorem wording.

## Intake / assumptions not silently added
The finite-sample oracle claims use deterministic g and independent iid labeled/unlabeled samples. For a random independently frozen predictor, proofs will be conditional on its realized value. Crossfit folds must be specified independently of observations. Binary synthetic outcomes are not stated and will be tested as an absent hypothesis, rather than assumed. The cited empirical-Bernstein theorem will not be accessed; its mathematical premise must be proved here or explicitly marked conditional. Natural logarithms; confidence levels in (0,1).

## Candidates

| Subgoal | Candidate | Idea | Verdict | Issue Or Reason | Internal rounds |
|---|---|---|---|---|---|
| g1 | A1 | Centered Hilbert-space square, then scalar projection | sound | Identity, equality, and no-gain cases proved; scalar score must have finite second moment | 2 |
| g2 | B1 | Sort uniform scores into exactly balanced folds, Y=S squared | sound | Exact limiting bias 1/[8(1+r)]; balance does not imply independent folds | 2 |
| g2 | B2 | Noiseless Y=S, covariance ridge epsilon=n^(-1/4) | sound | b=1/(1+epsilon); root-n error and O_p(n^(-1)) product rate fail | 2 |
| g2 | B3 | Exact weighted remainder with convergent finite-dimensional coefficients | sound | Consistency alone suffices for first-order equivalence; reused U handled as one average control | 3 |
| g3 | C1 | Pairing-MGF concentration for unbiased sample variance plus Bernstein MGF for mean | sound | Derives 7/3 radius self-contained; K union bound and ranges correct | 3 |
| g4 | M1 | Set Y=m(S), then alternatively Bernoulli conditional on S | sound | Refutes claimed VarY without binary law; all other displayed moments correct | 2 |

## Negative Attempts
Trying to invalidate the nonzero residual range or dictionary union bound failed: controls all lie in [0,a], residuals in [-a,1], and the total error budget is exactly alpha. Independence across dictionary entries and between fold-specific reused U means is not required by the respective proofs. No numerical checks are used as proof.

## Validation
Phase 1: PASS by manual application of the skill validator's required fields (Problem Type, Goal, Strategy, filled subgoals). Skill scripts live on a virtual mount without shell mapping; no experiment code or validator copies created.
Phase 2: PASS by manual application of its candidate-table checks (nonempty ideas and sound/repair/fail verdicts). The clean report contains the verified proofs, not exploration traces.
Phase 3: PASS by manual application of its assembly checks: the report has a nonempty Proof / Report section and substantive theorem proofs, with no shielding phrases. Aggregate status is REFUTED because the original bundle has exact counterexamples; the repaired statements carry separate labels.
Phase 4: PASS for the repaired clean report by manual application of audit checks. The original bundle fails as specified in the findings. Boundary and named-pattern screens are recorded below.
Phase 5: PASS by manual application of reflection checks: memory-persisted, storage-location, and proposed-memory-updates all have nonempty values in the report. Safe theorem wording was reread after tightening its outcome-moment, score-law, normalization, and zero-control conditions. No persistent-memory or profile update was warranted.

## Clean Proof Checked
The saved report only: A's centered square and scalar projection; B's explicit assumptions, coefficient rate, weighted remainder, CLT, and variance consistency; C's self-contained Bernstein and pairing-MGF proof, ranges, and union budget; analytic synthetic moments. No exploration chain or external source supplied a proof premise.

## Findings
| Severity | Location | Issue |
|---|---|---|
| High | Original B | Balanced score-sorted folds yield a nonvanishing bias; independent fold assignment is needed. |
| Medium | Original B | Vanishing ridge does not by itself give root-n coefficients; consistency still gives first-order equivalence. |
| Medium | Synthetic variances | A Bernoulli law is absent; conditional means alone do not determine outcome variance. |
| Low | Theorem domains | Specify finite positive score variance, K>=2, regression fallback, alpha in (0,1), and n,N>=2. |

## Verdict
PASS: the repaired proofs and exact counterexamples are sound under their stated domains. Original-bundle verdict is REFUTED, not an aggregate PROVED award. A single careful local clean-proof audit was used; no independent reviewer agents were available or claimed.

Named-pattern screen: P4 absent (no open-problem reduction); P5 resolved by explicit CLT/LLN hypotheses and internal concentration proof; P6 resolved by bounded-variable exponential-series convergence and fixed finite-dimensional sums; P18/P40 resolved by expanded algebra and remainder identities; P41 checked via k=2/odd pairing, zero variance/range, constant score, and finite K. Uniformity was not inferred from pointwise limits, nor actual variance convergence from convergence in distribution.
