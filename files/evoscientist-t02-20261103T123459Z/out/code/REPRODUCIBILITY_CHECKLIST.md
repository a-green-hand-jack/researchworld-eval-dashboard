# Completed reproducibility and integrity checklist

This is an **artifact-specific** checklist, not a mandatory ICLR form. The official ICLR2027 guidelines/template inspected specify an AI-use statement but no separate mandatory checklist. See `template/PROVENANCE.md`.

## Claims and scope
- [x] W and C are stated as author-formulated, falsifiable operational hypotheses, not theories attributed to cited papers.
- [x] Prior model-wise grokking is acknowledged; no first-discovery or unrestricted novelty claim.
- [x] Width effects, endpoint censoring, threshold sensitivity and late regression are reported together.
- [x] Exact width-8 construction is distinguished from learned generalization and optimizer accessibility.
- [x] No Transformer, large-language-model, real-data or universal width-law claim.
- [x] Main-track novelty/readiness remains explicitly unestablished; independent self-review and response are included.

## Data and access
- [x] Exhaustive synthetic data, exact integer labels, generator source, seed offsets, sizes and split hashes supplied.
- [x] Two-way split, independent pilot seeds and repeated held-out logging disclosed; no untouched third-test claim.
- [x] Data/operand/class audit completed for all32 planned split combinations.
- [x] No external dataset/account/license/snapshot required.
- [x] Only seven supplied original papers read directly; no topical/citation/repository expansion or excluded-work identity search.
- [x] Reading pages, versions, hashes and access incidents recorded. No known forbidden exposure; identity-based certainty is not claimed.

## Experiments and statistics
- [x] Complete240-job frozen manifest supplied; every job completed with return code0.
- [x] All240 configurations, summaries,401-point trajectories and final checkpoints supplied.
- [x] All13 independent pilots, unsuccessful settings and one separate technical duplicate retained; only240 enter the frozen study.
- [x] Hyperparameters, masks, normalization conventions, source/initial/split hashes and dependency versions supplied.
- [x] No seed filtering, best-checkpoint primary result, slow-arm horizon extension or post-outcome experimental change.
- [x] Administrative non-events and numerical failures are distinct; censored values are never described as true times.
- [x] Three paired primary tests and Holm correction; paired-seed bootstrap intervals with resampling count/seed and inferential assumptions specified.
- [x] Wilson incidence uncertainty and90/95% threshold sensitivities provided; intervals identified as unadjusted where appropriate.
- [x] Common-clock/native-event counts, horizons and persistence are distinguished; C32 non-rejection is not equivalence.
- [x] Post-hoc stability audit labeled descriptive and kept separate from the frozen primary event.
- [x] Projection is oracle-assisted and diagnostic-only; absolute energies and bias component logged.
- [x] Fixed-update comparisons are not called compute-matched efficiency comparisons.

## Code and verification
- [x] Full current trainer and exact hash-matching first-pilot source supplied.
- [x] Eighteen unit tests pass, including finite-difference gradient, projection, actual AdamW shrinkage and statistical plumbing checks.
- [x] Every saved event recomputed from CSVs at all three thresholds.
- [x] All240 final checkpoints re-evaluated; recorded final accuracy agrees.
- [x] All96,240 confirmation rows finite; exact evaluation schedule and orthogonal-energy identity checked.
- [x] One20000-update technical repeat exactly reproduces all401 numerical non-timing rows.
- [x] All figures/tables/macros generated from actual saved records; producer mapping in README.
- [x] Full and analysis-only reproduction entrypoints provided; data require no downloads.
- [x] Runtime and package/hardware records included, with contention/startup caveats.

## Paper and final handoff
- [x] Complete abstract, introduction, related work, methods, experiments, discussion/limitations and real references.
- [x] Latest released official ICLR2027 style and bibliography files preserved byte-for-byte.
- [x] Anonymous formatting, mandatory truthful AI-use statement, ethics and reproducibility statements included.
- [x] Main-text limit is9 pages; actual final page count, Letter sizing and disclosure boundary are checked in `verification_report.json`.
- [x] No missing bibliography keys, unresolved references, numerical placeholders or overfull boxes in final build.
- [x] Final build-input digests match current source/figures/tables; audit records source/PDF SHA-256 values.
- [x] No claim of actual submission, acceptance, human scientific verification or submission eligibility.

**Authoritative machine checks:** `verification_report.json`, `test_results.txt`, `analysis/determinism_audit.json`, `confirm_jobs.json.execution.json`. This checklist documents the release checks; it is not a certificate of scientific novelty or correctness beyond those checks.
