# Self-Review

## Verdict

**READY for closure of the focused F1–F9 revision check. All nine findings are resolved; no remaining scientific blocker identified within this offline verification.** This is not an unrestricted novelty, rights, or venue-readiness certification.

- **Draft:** `/work/paper/main.tex`.
- **Prior findings:** `/work/artifacts/paper_review.md`.
- **Output:** `/work/artifacts/review_resolution.md`.
- **Date:** 2026-11-02.
- **Boundary:** strictly offline; no external sources, internet queries, prohibited-paper identification, simulation reruns, new empirical experiments, or regeneration of analysis/figures. Only this review artifact was written. Reporting unit fixtures and read-only calculations on archived records were used.
- **Inputs read:** all requested code/documentation files, analysis amendment and final verification JSON; supporting statistics, archived runs/configurations, feature/rank implementation, generated tables, figures and current PDF were cross-checked.
- **Workflow:** end-to-end draft reading and adversarial suspicion recording preceded the aspect assessment. No code-interpreter/sub-review dispatch tool was available; all five aspects were assessed sequentially. Mechanical scans and the protocol audit were performed separately using local Python. This is a focused resolution review, not a fresh unrestricted literature/theory audit.

**Reject-first simulation:** The strongest remaining rejection argument is that an elementary, narrowly controlled diagnostic study may not offer enough new knowledge, and fixed graphs with synthetic responses do not establish real-platform performance. Neither repairing Monte Carlo uncertainty nor polishing presentation answers novelty or rights questions. Those limitations remain explicit; the formerly stronger objection—misleading failure-conditioned pooled uncertainty—is now repaired rather than merely caveated.

## Pass-1 Suspicions

These suspicions were recorded after reading the current draft and before the structured assessment. Confidence concerns the suspicion at that stage; resolution is scoped to the evidence checked.

| ID | Suspicion and location | Confidence | Evidence that would settle it; verification | Status |
|---|---|---|---|---|
| S1 | Attempted-record and common-valid ratio SEs might be asserted in Appendix B without actually retaining failures in the variance calculation. | High-priority | Inspect influence calculation and recompute archived sparse and paired examples. Both source and independent calculations agree; F1/F5 below. | Resolved |
| S2 | Sparse flags could be mistaken for valid precision guarantees, particularly for zero-estimate HT cells; §4 metrics and rare-exposure paragraph. | Medium | Check flags, low-success MCSE behavior and explicit tail warnings. Flags and warnings are present; empirical zero SE is expressly not certified precision. | Resolved as a reporting issue; unseen tails remain a scope limitation |
| S3 | “Complete” validation might still check only totals/runtime markers; Appendix B/README. | High-priority | Inspect exact expected-key construction, truncation tests and all archived suites. Exact keys, record combinations and statuses are checked; all archives pass. | Resolved |
| S4 | Numerical rank acceptance might silently inherit exact-rank complement symmetry; Proposition 3/Appendix B. | Medium | Explicit qualification and acceptance counts settle the reported-evidence question. Draft distinguishes the cutoff from mathematical rank; Add has no rejected records in any reported suite. | Resolved for reported evidence; no general numerical-invariance claim |
| S5 | Heatmap subsets, support-table counts, log1p and plotted bias ordering might still differ from text/output; figures, Table 2, protocol. | High-priority | Compare source, CSVs, generated tables and rendered figures. Counts/annotations and transformations agree; F2/F7–F9. | Resolved |
| S6 | Repair closure might be misread as independent novelty or third-party-rights clearance; introduction, limitations, Appendix C. | Medium | Authorized human literature/rights assessment would settle these questions. Not undertaken under this task's restriction. Current disclosures remain explicit. | Open: external novelty/rights sign-off only |

**Open suspicions: 1**, encompassing external novelty/rights sign-off, not an unresolved detected scientific error. The prior review's actionable S1/S2/S7/S9/S10 are closed by the repairs below; its broader novelty concern remains open.

## 5-Aspect Findings

### Contribution — 3/5

The controlled synthesis, complement-symmetry caution and separation of endpoint bias, contrast variance and availability remain the defensible contribution. The elementary decomposition is not newly claimed as novel. No unrestricted novelty judgment follows from this restricted review; this unchanged concern is not repaired by better MCSEs.

### Clarity — 4/5

Interval types, valid/attempted denominators, exact log1p construction and exact-versus-numerical rank are now explicit. The reverse outline remains coherent: endpoint problem → bounded contributions → error accounting/support/symmetry → controlled protocol → degree, support, allocation, features, clustering and covariance → limitations. Direct references to the heatmap and graph-statistics table are present. No manuscript editing was performed.

### Results — 4/5

The prior statistical reporting blocker is removed. Independently reproduced sparse and common-valid paired uncertainty agrees with current released CSVs. The heatmap now makes its selected subset visible, and no true-risk ranking is inferred from sparse HT behavior. Verification is strongest for the named repaired cells and full-record completeness; this review did not independently regenerate every aggregate metric.

### Testing — 4/5

All seven current reporting tests passed in this verification. Tests cover all-valid reduction, random accepted-count effects, singleton-success uncertainty and completeness rejection. All three archived suites pass the strengthened validator. The saved final verification reports 15 total tests and five deterministic replays; those eight other tests/replays were not rerun here, and no new simulation assignments were generated.

### Method — 4/5

The corrected ratio influence variance is appropriate as the stated local fixed-stratum delta approximation, including random accepted-count variation. Joint-valid comparisons use the same treatment. Interval and numerical-rank qualifications align with their mathematical scope. No remaining technical blocker was identified; finite-sample rare-tail reliability and deployment-valid covariance inference are not established.

## Protocol Audit & Mechanical Scans

### F1 — RESOLVED: failure-conditioned pooled MCSE; prior blocker B1 closed

**Evidence:** `audit_stats.py:4–15`, `analyze.py` summary calculation, Appendix B, and `analysis_amendment.md`.

The implementation constructs an attempted-length zero vector, assigns `H - mean(H)` only to valid positions, sums `R_j * sample_var(U_j)` within fixed graph strata, and divides its square root by total valid count. Thus failures contribute zero influence observations, not zero losses, and accepted-count randomness is retained. Fewer than two total successes returns NaN. MSE uses squared errors; RMSE applies the stated delta transform.

Independent reconstruction from archived **main / WS32 / Bernoulli / Hajek80 / correlated**, without calling the implementation under review for the reference calculation:

| Quantity | Recomputed | Released output |
|---|---:|---:|
| Attempts | 900 | 900 |
| Valid | 11: seed counts 5/3/3 | 11 |
| Bias MCSE | 0.4624155845169193 | agrees to floating-point precision |
| MSE MCSE | 0.8265078430248894 | agrees to floating-point precision |
| RMSE MCSE | 0.25334075494187086 | follows the stated delta transform |
| Precision warning | `sparse_valid_local_delta_only` | present |

These reproduce the requested rounded values **.462416 / .826508 / Nvalid 11**. The earlier .319320/.453964 uncertainty is no longer the current reporting contract. Eleven successes still cannot certify asymptotic precision or unseen tails.

**Sparse-tail checks:** current aggregate CSV has 2,325 ordinary-local-delta, 36 sparse-valid, 77 all-zero-tail-warning and 82 no-valid cells. Every cell with fewer than two successes has unavailable bias/MSE/RMSE MCSE; every nonempty cell below 30 successes carries a sparse or all-zero-tail warning. The regular32/Bernoulli/linear HTfull example retains 900 valid zeros, empirical bias −2 and bias MCSE 0, explicitly flagged `all_zero_estimates_unseen_tails_not_certified`. This is correctly not presented as proof against exact unbiasedness or as reliable precision.

### F2 — RESOLVED: heatmap availability

`plot_results.py::heatmap`, the actual PNG and underlying heatmap CSV agree. Of the 96 displayed cells, exactly one has incomplete availability: **WS / threshold / Oracle, 181/900**, RMSE **.8507374489**. It visibly reads `0.85*` with `181/900`. The caption supplies ordinary denominators and explicitly states that these method-conditional risks are not common-subset comparisons. No failed loss is imputed as zero.

### F3 — RESOLVED: analysis chronology and estimand

The frozen `analysis_protocol.md` is retained and now has an explicit superseding amendment notice. The dated `analysis_amendment.md` identifies the original formula, corrected success-conditioned fixed-graph estimand, success-probability reweighting, strata, ratio variance, paired/decomposition applications and affected reporting outputs. It identifies `results_audit.md` as historical first-analysis documentation, not final uncertainty authority. The draft and README disclose the post-review correction; prespecification is not represented as an unchanged final uncertainty formula. This verification does not independently prove historical chronology or raw-file immutability from an earlier snapshot.

### F4 — RESOLVED: exact completeness validation

`validate_results.validate_frame` reconstructs expected assignment keys from the suite schedule `configurations(suite)` plus saved repetition/design configuration. It compares exact observed/expected keys, checks unique full keys, global allowed method/mechanism sets and all 70 unique combinations per assignment, allowed statuses, finite successful values, nonnegative variance, error identity and missing failed estimates. Because allowed sets plus uniqueness and the full product count hold within every assignment, missing method/mechanism combinations cannot hide behind a correct total. Hard-coded public sizes and the versioned suite schedule are part of this contract; generic pilot seed metadata is not treated as realized coverage.

Current archived validation, actually executed:

| Suite | Assignments | Method–mechanism rows |
|---|---:|---:|
| main | 12,000 | 840,000 |
| size | 7,200 | 504,000 |
| allocation | 4,800 | 336,000 |
| Total | **24,000** | **1,680,000** |

Seven reporting tests passed (`python -B -m pytest -q -p no:cacheprovider /work/test_reporting.py`, bytecode writing disabled). Rejection fixtures cover a missing row, a missing whole assignment and an unknown status. Summary/per-seed/paired outputs contain **2,520 / 7,000 / 64** rows. Counts are no longer justified solely by a runtime marker or integer division.

### F5 — RESOLVED: paired fixed-stratum, joint-valid ratio SE

`analyze.py` now takes all attempted assignment keys for method A, marks the A/B validity intersection, aligns loss differences to that attempted ordering and applies the ratio variance by graph seed. Complete method coverage ensures both methods have the same attempted key universe. Pairing remains within design only.

Independent archived calculations agree with `paired.csv`:

| Bernoulli comparison | Common / attempted | Mean squared-loss difference | MCSE |
|---|---:|---:|---:|
| regular32/linear, Quad − Add | 900/900 | 2.138551081207277 | .10236977016685014 |
| WS/threshold, Oracle − Add | 181/900 | −.33330371086520755 | .09444375596079241 |

The sparse comparison is risk conditional on **joint validity**, not unconditional reliability or each method's separate-valid-subset contrast.

### F6 — RESOLVED: interval wording

§4 now says **residual-variance** intervals are not implemented for DIM/exposure estimators, then describes the generic known-noise diagnostic that is still emitted. It explicitly excludes randomization variability and automatic valid GATE inference, and distinguishes zero-weight HT degeneracy. Appendix A states Gaussianity, zero conditional contrast bias and positive variance for the exact conditional coverage claim. Ridge intervals remain diagnostic. The correction is present in the current PDF as well as TeX.

### F7 — RESOLVED: table denominators and Hájek notation

Generated `support_table.tex` shows integer valid/attempted counts. All **20** Oracle/H80 count entries were checked against current summary CSVs and match, including 210/900, 51/900 and 181/900. The caption defines H80 as H\'ajek80 using a proper LaTeX accent, avoiding the former literal apostrophe. Empirical Add error bias and noise-integrated conditional bias remain correctly distinguished.

### F8 — RESOLVED: references, design label and plotting ambiguity

Direct `fig:heatmap` and `tab:graphs` references exist. Figure 1 states Bernoulli(.5); its moved legend no longer obscures the middle TwoHop point in the inspected PNG. Figure 2's actual axis is `|E[b(Z)]| (Monte Carlo mean)`, matching `abs(mean(b))`, not `mean(abs(b))`. The caption likewise says absolute mean conditional bias.

### F9 — RESOLVED: exact covariate construction

§4 and Appendix B specify centered **log(1+d)**, standardization when nonconstant, the constant-degree branch, addition of **.5 independent Gaussian variation**, and final standardization. This matches `gate.py::prepare_graph`, rather than implying log(d).

### Numerical-rank qualification — addressed, not a newly proved invariance

Appendix B explicitly states that the raw-coordinate Gram cutoff need not be complement invariant and that Proposition 3 concerns mathematical rank. All Add records are successful in main, size and allocation archives, so there is no observed accepted-pair filtering issue in the reported Add cancellation evidence. No general numerical-invariance theorem is inferred.

### Separate mechanical/protocol checks

- **Promise–delivery / reverse outline:** decomposition, support obstruction, symmetry and controlled failure comparisons remain delivered; no new universally superior estimator, graph-population rate or real-platform effect is claimed.
- **Dataflow / information:** revisions are reporting-only; fixed features and partitions remain outcome-independent, Oracle quantities are simulation diagnostics rather than tuning information, and no endpoint truth is promoted as observable real-data information. Designs remain unpaired across their distinct RNG streams.
- **Markers / references:** scans over main/checklist/generated TeX find no TODO/FIXME/TBD markers, duplicate labels, unresolved reference targets or unresolved citation keys. This checks internal citation integrity, not external bibliographic or novelty completeness.
- **Figures/tables:** current heatmap, degree and failure PNGs were inspected; count cells and table/caption definitions agree. These intentionally non-ranking comparisons do not need a fabricated globally “best” bold entry.
- **Current PDF:** 20 pages; its SHA-256 matches `final_verification.json` and the root `paper.pdf`: `76e52ff7710a2bd4eac2244f89439720e9a9304cc196309bb7c8814c4819827c`. Extracted page 12 includes the attempted-record formula and sparse warning; page 4 has the revised interval wording. A literal math-token search initially missed the formula because PDF extraction separates subscripts/superscripts; direct contextual inspection cleared that false alarm. Saved verification reports eight main-text pages and references starting on page 9; no new layout build was run.
- **Reproducibility safety:** no analyzer, plotting, fetching, experiment runner, or artifact-writing verifier was executed in this review. Reporting tests used no cache provider and disabled bytecode generation.

**F1–F9 status tally: 9 resolved, 0 unresolved.** Protocol/mechanical repair items reverified: 9; newly identified unresolved scientific defects: 0.

## Blocking Issues

**Scientific blocking count: 0 within this focused verification.** Prior B1 is closed by the implemented ratio correction, matching released sparse outputs, tests and documented amendment. No new experiments are required to close F1–F9.

Remaining boundaries are real and must not be recast as solved:

1. **Rare tails and sparse validity:** local delta MCSEs, including the corrected ones, cannot certify unobserved compensating tails or reliable tiny-sample approximation. Availability and warnings must accompany conditional risks.
2. **Scientific scope:** fixed known static undirected graphs, controlled synthetic outcomes, three graph seeds and two public topologies; no graph-population inference, real behavioral effects, general interference identification, practical covariance estimator, learned-feature/bootstrap superiority, or optimized-design claim.
3. **Novelty:** elementary algebra and familiar support/variance concerns do not independently establish sufficient publication novelty. The integrated controlled audit is the bounded contribution. No unrestricted search or prohibited-source identification was attempted.
4. **Rights and accountability:** SNAP licensing, full third-party attribution/right clearance and Stanford ShareAlike obligations are not certified by this review. Omitting public graphs from a portable archive reduces redistribution exposure but does not itself clear all rights. Qualified human author review, venue suitability and accountability remain external pre-submission gates.

## Prebuttal Notes

- **“Failure-conditioned error bars are wrong.”** Show the attempted-record influence formula and independently reproduced .462416/.826508 example; do not defend the original fixed-accepted-count formula. Retain the 11-success warning.
- **“The heatmap makes Oracle look unfairly reliable.”** Point to the visible 181/900 annotation and conditional-risk caption; show the separate 181-common-valid paired comparison if relevant. Neither gives unconditional risk for a method that declines to estimate.
- **“HT zero MCSE proves precision/bias.”** It proves neither; the all-zero-tail flag and exact-target qualification are indispensable.
- **“Symmetry guarantees the implementation under every cutoff.”** No: the theorem is exact-rank; numerical noninvariance is disclosed and reported Add cells have no rejection.
- **“Repair closure certifies novelty or legal clearance.”** No: those require authorized human sign-off and remain expressly unresolved outside this scientific repair check.

**Counterintuitive protocol, verification-only:** unsupported generic uncertainty guarantees were replaced by a qualified corrected calculation; subset availability is promoted onto the figure; novelty is kept narrow rather than defended by an unauthorized search. No paper edits were made. Trust improves through correctness and transparency, not a new performance claim.
