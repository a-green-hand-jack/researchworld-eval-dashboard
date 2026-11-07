# Post-review resolution and release verification

The original `self_review.md` is preserved unchanged. It was a review of the earlier draft/delivery state, not a claim to have audited files that did not yet exist.

## B1 / P3: reproduction and compute deliverables — RESOLVED
- Added root README, exact requirements, reproduction driver, code license, artifact map, final report and experiment/failure log.
- Timed full in-place replay completed successfully in98.0s (94.7s before compilation); peak cumulative childRSS349.1MiB. All16 scientificCSV SHA256s matched prior outputs exactly.
- Created an independent extracted code directory and a fresh isolated Python virtual environment, installed pinned requirements, verified cached raw data checksums, and reran the entire analysis/PDF pipeline. It completed in87.9s, again with16/16 scientificCSVs exactly identical,11 tests passed,338 cold witness replays passed,8 content pages and no Type3 fonts. Cached source data were symlinked, not distributed; the system TeX installation was shared, not a new OSimage.
- `clean_reproduction_report.json` verifies every tested final Python source/test/requirements entry against the extracted code by SHA256. Later additions are release documentation only.
- `paper/resources.tex` now contains measured resources, and the final compiled PDF no longer contains its provisional fallback text. Source-derived tables/macros regenerate; no placeholder results remain.
- Final archives include code, source, derived measurements and witnesses, but exclude raw data, conversations, third-party research PDFs, dependency-recovery binaries and virtual environments. Final sizes/hashes and exclusion checks are in root release_manifest.json.

## B2 / P1: Type3 bitmap fonts — RESOLVED
- Added vector Courier monospace via standard psnfss; no margins, base font size, official style or official checklist questions were altered.
- Recompiled and inspected every page's font resources including embedded figures:0 Type3 resources; all font occurrences embedded.
- `pdf_audit.json` records the complete inventory and finalPDF hash. The isolated replay independently passed the same check.

## B3 / P2: table caption placement — RESOLVED
- All13 captions/labels now precede their table contents, preserving figure captions below figures.
- Mechanical audit verifies13/13, no overfull boxes or unresolved references, officialstyle/checklist original bytes unchanged,8 content pages within9-page limit,16 complete checklist answers/questions.

## P4: missing direct exhibit references — RESOLVED
Added explicit references to the random-control and cap-feasibility tables, approximation figure and grid-witness table. Generated figures/tables remain unchanged numerically.

## P5 and novelty judgment — RETAINED LIMITATIONS
The internally recorded pre-outcome plan is not externally preregistered or independently timestamp-authenticated. The post-outcome bootstrap is explicitly exploratory. No causal/evaluator-accuracy claim, globally optimal attack, nonlinear certificate, independently validated novelty clearance, institutional approval, or acceptance prediction was added. Novelty remains that of an empirical denominator-and-constraint audit, not a new generic influence method.

## Evidence closure
Current validation reconciles18,293 fit records with finite gradients below1.00e-8;338 deterministic witnesses cold-replay within7.32e-9. The review found no demonstrated scientific/numerical defect and subsequent changes did not modify scientific estimands or measured outputs. This is an artifact-completeness and mechanical-compliance closure, not a new peer-review acceptance verdict or a substitute for human scholarly/legal judgment.
