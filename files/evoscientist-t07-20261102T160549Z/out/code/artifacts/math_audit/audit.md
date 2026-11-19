# Audit

## Clean Proof Checked

Reviewed only the assembled `final.md` as the mathematical object, then compared implementation references to the source files. One careful local audit; no delegated or purported independent reviewers. Existing tests: 9 passed. Numerical regression checks are not used as general proof steps.

## Findings

| Severity | Location | Issue |
|---|---|---|
| FATAL for literal original wording; repaired explicitly | Unrestricted pilot-randomized vector | First moments are missing. Exact Cauchy example has undefined marginal expectation. Final status refers to this literal overbreadth, not the corrected theorem. |
| MAJOR limitation of an implementation-wide overclaim | Seed-selected source split and finite coupled seed grid | Conditional uniform item sampling is not established by seed offsets; report states ideal-design scope and does not allege measured bias. |
| MAJOR input-contract limitation | designs and public direction arguments | No complete feasibility/partition/alignment validation; prefix truncation can change actual budgets. The theorem uses valid actual counts. |
| No defect | Corrected theorem, formula (1), fixed half-average | Conditional finite-population identities, moment-qualified tower property, and reverse sampling law justify every conclusion. |
| No defect | Fit preprocessing and full-bank aggregation | Pilot-only fitting/centering; full fixed-bank covariates legal; union membership not used to fit q. |

### Counterexample-first and boundary checks

- N=2,p=a=1: both directional estimators equal the exact total/N for every finite q; M=1 variance term zero.
- General complement census a_h=M_h: q cancels against all complement residuals, regardless of pilot fraction.
- N=5,p=1,a=2: reverse sizes differ but both conditional residual sums remain unbiased; no equal-size assumption enters.
- Constant y and/or zero residuals: expectation remains mu; zero complement residual variance gives zero directional variance.
- N=4,p=a=1,q=0,y=(1,0,0,0): exact dependent-fold example gives covariance 1/32 and half-average variance 1/16.
- N=3,p=a=1,y=0: Cauchy nuisance refutes unqualified moments; union-membership nuisance gives deterministic bias -1/3 when the membership restriction is dropped.

### Named-pattern screen

P4: no open-problem reduction. P5: sampling hypotheses and first/second moments are reverified; original moment omission explicitly flagged. P6: no unlicensed infinite expectation interchange in the repaired proof. P18: expectation cancellation adds an actual inclusion-probability argument. P40: sample-variance claim expanded using indicator covariance. P41: smallest admissible population and census/unequal boundaries checked. Restatement drift: all marginal claims carry first-moment qualifications; implementation verdict retains valid-input, ideal-design and exact-arithmetic scope.

## Verdict

PASS for the repaired theorem and the clean report. Literal original unrestricted randomized claim is refuted by the exact moment counterexample; no unresolved gap in the repaired proof. WARN for any attempt to promote the current coupled seed grid or malformed calls to an unconditional implementation-wide exact guarantee. No independence, confidence-interval, improved-MSE, or broad novelty claim is made.
