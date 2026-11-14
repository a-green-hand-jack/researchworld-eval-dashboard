# Review findings: resolution and remaining risks

This closes the local self-review in `paper_review.md`; it is not an external peer-review endorsement or a claim of likely acceptance. Original review retained unchanged as a historical artifact.

| Finding | Resolution | Verification |
|---|---|---|
| F1 / B1: visible AUTHORERR | Added anonymous corresponding-author declaration using a reserved `.invalid` address; anonymous style suppresses identifying/contact information. Build now fails on AUTHORERR. | `pdf_audit.json`: false; actual compiled PDF re-extracted. |
| F2 / B2: unqualified reversal | Abstract now explicitly says **shared first**, **on average**, and fixed jointly feasible nonwinner cohorts. Body retains individual reversal counts separately. | Main source and fixed-cohort CSV. |
| F3 / B3: generic tractability overclaim | Replaced with finite subset selection and separate magnitude optimization; no polynomial-time Borda claim. | Conclusion and method match. |
| F4 / B4: incomplete reproduction setup | Added README, exact requirements, portable run_all/reproduce/build entry points, author-code license with third-party exclusions, script-to-table/figure map and precise TeX prerequisites. | Fresh venv install succeeds; full isolated recomputation succeeds; submission bundle supplies local reviewer access. No public persistent archive is claimed. |
| F5: magnitude regression coverage | Added two tests for magnitude/attainment boundaries and independent saved-data cardinal formulas, including 77/64 headline regression. | Seven test groups pass in both original and clean environment; no endpoint witness used as an optimal magnitude proxy. |
| F6: bootstrap coverage ambiguity | Added explicit empirical target-resampling / no population-coverage language; finite-population quantities and exact sign counts retained. | Statistical method and README. Intervals remain descriptive, not simultaneous confidence guarantees. |
| F7: rounding/task coverage | Explicitly states **no score-rounding perturbation or measurement-noise study was performed**; all limited-task/parity/empty-cohort caveats retained. | Main limitations and appendix. This is a scope boundary, not a repaired measurement-uncertainty experiment. |
| F8: hash overflow | Explicit safe line break in snapshot SHA; final build asserts no overfull boxes. | `pdf_audit.json` empty overflow list. |
| F9: figure legend/table navigation | Legend moved to free area of HELM panel; sensitivity table now has its own label and direct appendix reference. | Updated PNG inspected; final references resolve. |
| F10: selective-venue significance | Narrow conditional contribution retained. No priority, training-efficacy, resource-conversion, or acceptance claim added. | **Residual scholarly judgment remains**, not fixable by tests alone. |

## Mathematical-audit closeout
- Mean/median baseline and infeasible branches explicit; odd median uses nonnegative crossing deficit.
- Feasible strict cardinal magnitude is never attained unless baseline already strictly wins; discontinuous Borda exceptions stated.
- Exact nonordering proof is **shared-first only**; six ordered-pair records use **four distinct** matrices.
- Borda constraints update rivals and exact pruning proof retains the original leader's lower bound.
- Appendix proof tables now actually regenerate through `counterexamples.py` + `paper_assets.py` with Fraction arithmetic, not just hand-copied values.
- Proof audit had no remaining mathematical hole after these repairs; empirical MILP optima remain numerical, not formally machine-certified.

## Fresh reproduction evidence
- New isolated Python virtualenv, exact pinned packages, no system-site-packages; successful installation log retained.
- Full new-directory analysis: **294.20 s wall, 287.88 CPU seconds**, max child RSS **313,352 KiB** (Linux units), numerical CSV and summary comparisons all pass.
- Every fresh endpoint witness or full-ceiling infeasibility is independently checked; all six result files cover **128,915 rows**. Numerical-equivalence comparison excludes nonunique optimal masks/witness costs and solver bookkeeping, but the fresh witnesses are validated.
- Seven tests pass again. Raw data are copied locally for this isolated offline test; online downloads and pinned checksums were verified separately. Do not call it a new network download or cross-platform reproduction.
- Exact appendix table regeneration and final PDF build were separately executed with the fresh interpreter. Final PDF: **15 pages, 7 main pages**, impact/references begin page 8; all fonts embedded Type-1, no unresolved references/citations, no AUTHORERR, no overfull boxes.

- Extracted-bundle online check also passes: public score downloads/verification through final PDF and all numeric comparisons, **307.08 s wall / 292.27 CPU seconds**, max child RSS 317,328 KiB. See `archive_reproduction_check.json`. This second check begins without raw/processed input matrices; final post-extraction changes only add the continuous-score-lattice caveat and delivery documentation.

## Remaining boundaries
No independent evaluation of novelty beyond allowed sources; no excluded-paper identification; no external acceptance assurance. No actual training or causal resource experiment, no family-independent or task-population inference, no unknown-score measurement uncertainty. Roster and normalization sensitivities change the estimand. Public score licensing is still undeclared. These limitations are visible in the paper and README rather than silently treated as completed experiments.
