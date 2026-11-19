# Integrated presentation inspection

Presentation commitment figtab-repo #2 is complete for paper-repo revision
`334727adba7a31f99f3749d2cf08f85e90003dda` (the authoritative root PDF supplied in paper-repo #17).
The frozen Research objective and idea-repo's live Brief were re-read before this signoff.
This is a presentation check, not independent scientific review or release approval.

## Artifact inspected

- Root file: `paper.pdf`, 36 letter-size pages.
- PDF SHA-256: `566bf94b31e087651391bdc77d261df2576120d2df114b341b040794a4ab5867`.
- Every file under `figures/`, `tables/`, and `presentation/` in the inspected paper revision
  is byte-identical to the presentation handoff: 36 files, no differences.
- Executable figure/table generator, exact source snapshots, input hashes, captions,
  package versions and source-to-output mapping remain present in that delivery.

## Opened pages and findings

I rendered and opened PDF pages 5–6 and 11–29 at 110 dpi, retaining the full page dimensions,
and inspected the figures at their actual 5.5-inch inclusion width. This covers all seven
figures and every selected/complete table output, including every continuation page.

Main Figures 1–2 remain legible with distinguishable markers, nominal coverage and width-ratio
references, paired uncertainty, and adjacent validity/precision panels. The main comparison
shows large designed nonlinear gain, affine/no-signal controls, negligible archive gains,
and rare-event undercoverage. The finite-sample comparison retains exact Clopper–Pearson
and full-label empirical-Bernstein baselines alongside trained controls.

Appendix Figures 3–7 preserve sample-size effects, poor coverage, fitting costs, finite-sample
conservatism and the finite-N comparison. The stress figure's logarithmic width axis is declared.
All figures retain visible labels, legends and uncertainty endpoints without clipping.

Tables 1–17 are readable, with captions above, repeated regime/column headings after page
breaks, and nonzero Monte Carlo errors preserved with scientific notation where appropriate.
The extracted full-results rows on PDF pages 21–29 total **405**, distributed as
36, 48, 45, 47, 48, 48, 48, 48, and 37. This matches all completed method/setting cells;
no row was lost through typesetting. Extreme fits and poor coverage remain visible.

Integrated captions retain the population-mean target, samples/repetitions, ratio direction,
Monte Carlo definitions, archive empirical-population sampling and the distinction between
asymptotic evidence and finite-sample guarantees. Appendix E points readers to the exact
source/output/function map and manifest. All integrated PDF fonts are embedded, with no
Type 3 fonts. No presentation correction is required at this revision.

## Repeating the structural checks

Extract the authoritative file without rebuilding another position's delivered document:

```sh
git -C /hutian/paper-repo show 334727adba7a31f99f3749d2cf08f85e90003dda:paper.pdf > /tmp/integrated-paper.pdf
pdfinfo /tmp/integrated-paper.pdf
pdffonts /tmp/integrated-paper.pdf
pdftotext -f 21 -l 29 -layout /tmp/integrated-paper.pdf /tmp/complete-table.txt
```

For each complete-table page, count lines matching
`^\s*(?:100|500|2000|10000)\s+\d+\s+(?:3000|5000)\s+\S`.
Visual inspection additionally used PyMuPDF page rendering with scale `110/72` and Pillow
contact sheets; structural checks do not substitute for opening the rendered pages.
