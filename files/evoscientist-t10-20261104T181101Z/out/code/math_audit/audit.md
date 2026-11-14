# Audit

## Clean Proof Checked
`/work/theory_audit.md`, §§2–10, read as a standalone argument without using exploratory candidate notes. One local adversarial verifier (this assistant); no claim of multiple independent reviewers, external formal verification, or experimental evidence.

## Findings

| Severity | Location | Issue |
|---|---|---|
| CRITICAL in original, resolved by explicit refutation | theory.md line 16 | Unrestricted K-monotonicity is false; exact K2/K3 example, error 0 versus 1/12. Restrict the positive theorem to refinement. |
| MAJOR original omission, repaired in report | theory.md line 19 | State n V_hat consistency and positive limiting variance for ordinary studentization. |
| MAJOR design qualification, repaired in report | todos.md line 25 | Wilson is approximate; exact Bonferroni MC statements require valid one-sided component bounds. |
| MINOR clean-draft clarification, repaired | report §7 | The deterministic-bin faster CLT transfers by high-probability equality to an unconditional pooled oracle mean, not by conditioning an iid CLT on occupancy. |
| MINOR clean-draft qualification, repaired | report §9 | Ordinary ratio-normal inference requires positive linearized variance; handle exact proportional widths and zero denominators separately. |
| MINOR provenance correction, repaired | report findings | Stage-4 inferential procedures occur on todos.md line 25, not the section heading on line 24. |

## Five local checks
1. **Model and conditioning:** multinomial factorization includes random counts and empty cells; exact-score conditioning is not used. Positive-size CP tail conventions and zero-size fallback are explicit. External randomness can be conditioned upon; learned evaluation boundaries cannot silently be treated as external.
2. **Finite-sample logic and constants:** 2K component budgets total alpha; adding M selection budgets gives alpha overall. K1 uses its per-partition budget directly. W is nonempty for every dataset; exchange moves preserve the simplex and bounds. Numeric certification requirements are outward, never merely approximate feasibility.
3. **Oracle algebra and scopes:** square-completion coefficients agree with r=n/N; variance headroom equals the projection residual divided by n(1+r). Affine equality includes zero/negative slopes. Binned and scalar classes need not be nested. No finite-sample or universal optimality conclusion is drawn.
4. **Asymptotics and boundaries:** fixed K and positive active masses imply finite-dimensional rates; dependent products are bounded in probability without independence. Both variance sample moments are centered and scaled correctly. The CLT treats rho=0 separately when necessary; constant Y has zero studentization denominator. No uniform-in-mass or growing-K assertion appears.
5. **Design and MC inference:** empirical-population iid resampling is distinguished from superpopulation inference; shift is outside assumptions. MC eta is distinct from data alpha, Bonferroni does not require independent methods, paired ratio estimands and p-value conditions are explicit, and failures cannot be silently dropped.

## Named-pattern screen
- P4: no reduction to an open problem.
- P5: CP uses fixed-bin binomial sampling; CLTs use fixed bounded variables and growing independent sample sizes; Slutsky's denominator condition is checked. The original zero-leading-variance omission is repaired rather than ignored.
- P6: no infinite-series manipulation; all cell/family sums are finite, and the only limits are justified by LLN/CLT and probability bounds.
- P18: inequalities establish new implications; confidence is not asserted by definition.
- P40: nontrivial conditioning, exchange, projection, fitted-error and variance-moment arguments are expanded in the report.
- P41: smallest/degenerate cases checked: n=1 adaptive-boundary contrast, n=N=2 learned bias, K1, empty and zero-mass cells, constant S/Y, and rho=0. Exact fractions in both counterexamples were independently recomputed by hand.

## Verdict
PASS for the clean repaired proof sketches and exact refutation in the report. The original unrestricted K-monotonicity claim is REFUTED; the original source as a whole is not endorsed unchanged. No unresolved proof gap was found in the restricted results. Arbitrary evaluation-learned boundaries, growing K, shrinking masses, covariate shift, universal optimality and source-example fidelity are outside scope, not silently proved.

## Validation
Mental phase-4 validation PASS: Clean Proof Checked is nonempty; Verdict contains PASS; findings, named-pattern screen, boundary tests, and the scope distinction are explicit. Script execution is unavailable through the virtual /skills mount and was not attempted or reimplemented. This is structural mental validation plus local mathematical review, not a machine proof.
