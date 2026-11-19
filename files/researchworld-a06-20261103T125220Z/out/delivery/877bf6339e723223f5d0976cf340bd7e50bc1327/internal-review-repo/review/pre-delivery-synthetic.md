# Pre-delivery synthetic evidence review — 2026-11-03

This is an early independent check, not an approval of a paper version. No pull request into paper-repo release/final or world/result release exists at this reading. The governing objective and all five frozen files were read, then TASK.md was reread before recording this delivery. Review standard and ongoing commitment: internal-review-repo #2 and `review/standard.md`.

## Exact inspected revisions and material

- experiment-repo `e7879db19aeadc2b9e12f3f6786b50880cb0f43e`: README; design/specification, statistical guarantees, results handoff and run log; simulation, exact-null reference, summary and validation code/results; real partition/prompt/generation/pilot preparation; acquisition and failure provenance. The real preparation is implementation, not evidence that the real experiment has run.
- figtab-repo `e73407f581145229e7ad1b30df1345077a18f854`: plotting generator, numerical inputs and provenance, all captions, ten-row full-precision table and its LaTeX. I rendered and opened EVERY PDF figure: synthetic-selection, synthetic-budgets, synthetic-decisions, synthetic-optimism-grid, synthetic-coverage-grid and synthetic-mse. I also rendered/opened synthetic-methods-preview.pdf. Renderings were made directly from PDFs with PyMuPDF at 108 dpi, rather than trusting existing PNG previews. All had nonempty content, readable labels/units, distinguishable methods and no blank/placeholder panels. Publication sizing remains subject to venue and final integration checks.
- idea-repo context at `64c0666b9c9c4a2cf1122b840332aad9bb1aaf53`, including Brief, Primary Sources, Estimands and Evaluation, source summaries and actual-consulted-version bibliography. The core phenomenon, holdout and simultaneous protection are classical antecedents; no novelty claim is established by this check. I did not seek the withheld paper or related prohibited material.
- paper-repo `5788153d06e3b4d64f98f4a4831650357e1cd9e3`, story-repo `b1dde3f3009fed58f20a7c47b5447526e7e4339c`, venue-repo `0310ac33c5a356a7ef59d23e7104e54a57d8a5c7`: initial repositories do not yet supply a manuscript, settled plan/CODEOWNERS or venue assets. Their live issues contain requests for those inputs and paper's manuscript commitment.
- external-review-repo #2 is an external-review commitment, not a substantive finding about a version. Its role and standard are consistent with this review; there is no published version for it to assess yet.

## Independent numerical and mathematical checks

`review/check_synthetic.py` writes `review/synthetic-check.json`. Run command is in its docstring. It does not run or modify study outputs and imports none of the study's CP/selection functions.

1. All 7,200 rows form the expected 288 cells × 25 metrics, with 20,000 repetitions, finite values, no duplicate metric keys, and nonnegative MCSEs. Presentation inputs are byte-for-byte equal to upstream experiment inputs.
2. For all 48 independent equal-quality cells, I computed the exact maximum-count distribution as differences of Binomial-CDF powers. CP coverage was computed independently using binomial-tail acceptance conditions, without the study's beta-quantile interval code. All 144 comparisons of optimism/naive coverage/simultaneous coverage agree with Monte Carlo results within 5 reported MCSEs; the maximum discrepancy is 3.651 MCSEs. This is a validation diagnostic across many comparisons, not a substantive significance claim.
3. Interval nesting, selected-quality-plus-regret identity, and corrected-decision monotonicity hold across the full grid. Every derived table mean and call cost matches its declared upstream metric and protocol.
4. Code inspection supports the specified joint-count sampler: conditional shared-question counts are multinomial over sorted Bernoulli thresholds and independent-question counts are conditionally independent binomials. This yields the claimed marginal means and covariance. Selection includes independent uniform tie breaking.
5. The expected-optimism bound follows from convexity and a bounded-variable MGF maximum bound. The simultaneous CP statement follows by union bound and permits dependence between candidates. Independent-audit conditional unbiasedness/coverage requires fresh iid questions after freezing the selected system. The text states those conditions and distinguishes them from finite-pool experiments and label-adaptive candidate generation.

The principal showcased equal-quality result (n=64,K=16,rho=.5) is consistent with the supplied summaries: 7.71 pp optimism and 82.30% naive coverage, with conservative simultaneous coverage. The 9.89% false-superiority figure is specifically the unconditional interval-nonoverlap decision at n=512,K=128,rho=0, not FDR or a general paired-test failure rate. Captions retain these restrictions. Split methods target their own potentially different selected candidates and their costs are labeled; simultaneous intervals retain point-score bias.

## Disposition and remaining review inputs

No actionable defect was found in this scoped synthetic package. This does not establish main-conference merit, completeness, real-model validity or final rendering quality; those need the integrated report and remaining empirical evidence.

Before a complete version can be approved, the required actual generated-response LLM × pinned MMLU-Pro experiment must be supplied and judged, including real gap/decision/reporting comparisons and appropriate uncertainty. The audit target is estimated, not known population truth; conditional response-matrix repetitions are not independent LLM experiments. Experiment owns these pending inputs, already requested in experiment-repo #3 (figtab) and #4 (paper), so no duplicate request was opened. Paper owns the complete manuscript/PDF/reproduction integration, venue its official current template/rules, and story the settled plan and CODEOWNERS, under the open requests in their repositories.

A proposed version still requires full objective rereading, exact-head report/code/figure/table/link checks and a formal Forgejo review. No release/final approval was given in this turn.
