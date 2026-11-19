# Final review resolution

The initial self-review (`paper/self_review.md`) concerns the pre-revision 8-content-page/26-total-page PDF. Its scientific limitations remain in force; it is not overwritten as a favorable review.

## Resolved presentation blocker B1

- `src/analyze.py::plots` now produces the main figures at their final **5.5-inch** manuscript width, rather than shrinking 12/10.5-inch canvases. Axis/title text is 8pt, ticks/legends 7.5pt at final size. Marker/dash patterns redundantly distinguish all policies; no color-only distinction is required.
- Re-rendered from unchanged `artifacts/summary.csv` only; no experiment, fitted method, loss, confidence interval, or cohort was changed. Inspected rendered PNGs for clipping and legend readability.
- Target-support appendix figure also uses final-size typography and marker redundancy.

## Other fixes

- Compressed archive units corrected to **377 MiB (396 decimal MB)**.
- Correlation-coverage formula now explicitly uses the fitted PSD-repaired/shrunk unit-diagonal matrix, matching code.
- Added connected-component concentration: 2,890 rows, 64.3% of source and91.4% of seed71 test rows, with an explicit warning that conditional percentiles do not demonstrate population coverage. Values are reproducible with `src/diagnostics.py` → `artifacts/connected_components.json`.
- Added exact appendix table references; full-CI table cells are left-aligned, avoiding stretched justification.
- Sharpened practical takeaway without adding novelty/superiority claims.

## Final mechanical verification

Final `latexmk` build succeeds. `maintextend` in `paper/main.aux` is on page9, references begin on page10; final PDF has27 pages including appendices and the16-topic official checklist. This meets the9-content-page NeurIPS2026 submission limit; no style/margin changes. No overfull boxes or undefined citations/references in the final log. The final PDF replaces root `paper.pdf` and `paper/main.pdf` identically. The initial review's8/26 pagination is superseded, not silently rewritten.

The released source ZIP was additionally extracted to a temporary clean subdirectory and its manuscript compiled successfully to27 pages using only bundled source/style/table/figure files. The temporary copy was removed; `package_smoke_build.log` preserves the successful build. This checks manuscript packaging, not a second end-to-end data/experiment reproduction.

## Scientific issues deliberately NOT claimed resolved

Failed original MTEB >=3-split gate; reused-data status; imperfect organization/component ancestry; original alias overlaps; full-panel native-objective mismatch; conditional-only uncertainty including giant component; bounded/nonconverged low-rank fits; omitted planned ablations; unknown OpenLLM source redistribution license; incomplete project-wide resource accounting. All remain explicitly discussed. No claim of NeurIPS acceptance or guaranteed publication.
