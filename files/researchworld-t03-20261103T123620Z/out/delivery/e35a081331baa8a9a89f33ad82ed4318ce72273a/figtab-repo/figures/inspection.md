# Executed-output inspection: initial pilot accounting

Inspected on 2026-11-03 against objective #1 and the commitment in figtab-repo#3.
This record covers the pilot assets only; it does not complete the required
main-study reliability delivery.

- Opened the generated figure PNG and independently rasterized its actual PDF
  with PyMuPDF. Opened a grayscale rasterization of that PDF. Checked the three
  dataset panels, requested/actual budget distinction, tick labels, method line
  and marker redundancy, hollow exhaustive-Kernel markers and absence of
  clipped labels. Condensed identical model-work facets into three dataset
  panels; all 72 measured call records remain represented and mapped in the
  manifest. No estimates, error bars or model contrasts are inferred from
  coincident traces.
- Opened the actual compiled table PDF through a rasterized preview, and the
  final PNG preview after retaining significant trailing zeros. Checked caption
  above the table, 18 raw-call rows, C1/C2 identity, CPU milliseconds, budget
  headers and alignment. The LaTeX build raised no overfull hbox/vbox. Preview
  geometry is a 5.5-inch text block; final official-template placement remains
  paper-owned.
- `pdffonts`: figure uses embedded CID TrueType STIXGeneral; table PDF uses
  embedded Type 1 Nimbus Roman. Neither has Type 3 or unembedded fonts.
- `pdfinfo`: figure is one page, 396 by 194.4 PDF points (5.5 by 2.7 inches).
  Table preview is one US Letter page. The table source, not the preview page,
  is the manuscript include.
- The input hash and complete 72-call pilot grid/configuration are checked by
  the generator. Every plotted coordinate and table cell maps to an original
  JSONL line; table values multiply measured CPU seconds by 1000 and round to
  three significant digits. No descriptive or inferential aggregate is added.
- Captions explicitly label pilot evidence, the B=32 empirical-background
  grouped-feature setting, raw calls, excluded setup/training/reference costs,
  exact Kernel controls and the absence of population uncertainty intervals.
  The old permutation `exhaustive` flag is ignored for exactness as required by
  the analysis owner's development log.

The manifests' generation-time pending-inspection note does not itself certify
visual review; this separate record documents the manual checks. The integrated
root manuscript PDF has not yet been delivered with these assets. That check,
plus the primary one-run accuracy/adequacy, repeatability, conditions, sensitivity
and final cost/reference tables, remains open. No claim of final reliability
coverage is made from these pilot artifacts.


## Integrated pilot placement accepted

Opened the actual root `main.pdf` at paper-repo revision
`77c9c7b0298b9b7fe0004d95e1715518f8fa1174` on 2026-11-03. Inspected rendered
pages 5 and 6 and extracted their text. Figure 1 is readable at the full
5.5-inch placement: labels/legend, separate dataset panels, hollow exact-Kernel
markers and the caption are intact. Table 1 preserves all 18 numerical rows,
caption, milliseconds and case/model groupings with no clipping. The appendix
correctly confines these assets to initial pilot accounting, and explicitly
notes that they precede the float64 prediction-adapter correction. They must
not be used for final-implementation latency or reliability claims.

Paper identified that the README's bare caption-input wrapper fails with its
hyperref setup. The corrected include example supplies an optional short
caption; the caption source and numerical assets remain unchanged. Integrated
pilot placement is accepted for this draft. Recheck after any later layout
change; acceptance of these pilot pages does not complete the main-results
presentation commitment.


## Reinspection after accepted-study pagination

Opened the delivered root `main.pdf` at paper-repo revision
`eadf0096245664b5d1f1b94fc79a801cb65d8c29` on 2026-11-03. The manuscript now
has eight pages; the initial-pilot figure and raw-call table occupy pages 7 and
8. Independently rasterized both actual PDF pages with PyMuPDF at 1.4x and
opened the rasters. The full figure legend, dataset/feature titles, hollow
exhaustive-Kernel markers, log ticks, axis units and caption remain legible and
unclipped. The table retains all 18 raw-call rows, C1/C2 labels, millisecond
headers, significant digits and caption with no clipping. The appendix still
explicitly limits these assets to the initial implementation pilot and records
the subsequent float64 correction; neither asset is presented as main-study
reliability or final-implementation latency evidence.

Placement is accepted for this revision. This check does not certify the main
results, which remain unavailable; prepared renderer code is not a rendered
numerical delivery. Recheck after future layout changes. Full-page pixel
identity with the earlier six-page revision is not asserted: pagination and
line numbers have changed.


## Executed main evidence inspection, 2026-11-05

Source is analysis revision `c291b715fcfed90d5b5905e2d7a8e1f721937616`, complete
97,200-call/540-reference/9-model handoff. The objective and commitment were
reread before delivery. No pilot record enters any main display.

Opened independently rasterized actual PDFs for all 16 main figures: primary
adequacy/work, CPU, interrupted-wall records and reference-error/repeatability;
three datasets each for conditions, metric sensitivity, accuracy components
and observed-input distributions. Opened color and grayscale views. Fixed
legend/xlabel collisions and title spacing found during inspection, made log
cost ticks readable within the evaluated range, and put boundary plus markers
above the method markers. Final text-bounds checks pass. All PDFs are one page
and exactly 396 PDF points (5.5 inches) wide, with embedded CID TrueType STIX
and no Type 3 fonts. Common bounded-rate axes, shared error scales, method
markers, scenario line styles, stratum n and unavailable low-signal estimates
remain visible. No curve interpolates an empty stratum. ECDF endpoint masses
and the 0-to-1 domain are retained; observed fractions are not latent rates.

Opened all four actual compiled table sources as PDF previews, with enlarged
rasters of their captions and every numerical row. Checked 9 coverage rows,
18 lowest-budget condition rows, 9 reference-assessability rows and 9 compute
rows. Captions are above tables, rules are horizontal and no overfull box is
reported. The preview uses the venue's 5.5-inch text width. Preserved nonzero
small reference costs by printing reference CPU minutes to three decimals.
All table numerical cells map to actual analysis CSV lines. Preview generators
and their source/output hashes are included; the .tex is the manuscript input.

`audit_artifacts.py` verifies all 21 main manifests' source/output hashes,
embedded fonts, physical width and PDF text bounds. Analysis claim-ledger input
hashes were independently matched; all primary/comparison plotted CSV-line
keys and metrics were checked against their source rows. Complete-grid and
metric denominator checks passed in both renderers. The primary .20/.01/signed
two-of-three event, supplied boundary-adjusted intervals, 60-instance/30-repeat
units and absence of >=.95 certification are retained. Actual-work/time means
are not quantiles, and nominal budgets do not imply equal work. Wall timing
caveats, no observed low signal and inactive floor sensitivities remain explicit.

Executed versions: Python 3.11.2, Matplotlib 3.11.2, pandas 3.0.6, NumPy 2.4.6,
PyArrow 26.0.0, PyMuPDF 1.28.2; pdfTeX/TeX Live and poppler as in the pilot
record. Main rendering plus four preview compilations takes about one minute
on this sandbox (reproduction guidance, not an estimator benchmark).

This is acceptance of standalone main artifacts. Final placement/captions in
paper's root PDF remain to be inspected after integration. The separate
changed-background sensitivity arm remains pending analysis supply. Neither
request #2/#4 nor commitment #3 is closed by this standalone main delivery.


## Completed changed-background and compact-contrast inspection

Opened both actual `background_sensitivity_{acs,diabetes}.pdf` outputs as
independently rasterized color and grayscale images. Source is analysis
`5d8d8e37ed7868e8d088315688c0843678abee55`; its complete manifest has 144 exact
changed targets and 5,760 calls. Checked categorical B8/B128 coordinates,
12-input/20-repeat denominators, model columns, all supplied intervals,
boundary plus marks, and distinct target-shift/top1-target-match versus
changed-game estimator-accuracy rows. The common target-shift range includes
all error bars without clipping. No line implies a smooth size effect from
one draw per size. Captions keep B32 as a comparator and size/row changes
confounded. Captured compatibility warnings are preserved in the cost caption.

Compiled and opened `background_compute.preview.pdf` and its actual rendered
PNG; all six phase-timer rows and caption are readable, with no overfull box.
Its phase CPU/wall excludes import/data/bundle setup and is not mislabeled as
an all-inclusive or directly comparable main-process total. Source row IDs,
unit conversion and all input/output hashes are included. The four earlier
preview PDFs were refreshed with the same unchanged table sources; their
numerical content is unchanged.

Opened `criterion_instance_contrast.pdf` and a grayscale rasterization. The
left panel preserves all 18 highest-budget strict-event estimates/intervals;
black plus marks retain the boundary switch and the caption identifies broad
primary observed success separately. The right ACS RF lowest-budget ECDF
retains its endpoint masses and accurately highlights the saved 0/30 Kernel
input (original row 296124), with its supplied Wilson interval stated in the
caption. It makes no known-latent-probability or individual-certification claim.
Method colors/shapes survive grayscale; labels, titles and arrow do not clip.

The artifact audit now passes 25 manifests and all 19 vector figure PDFs:
source/output hashes match, widths are 5.5 inches, fonts are embedded without
Type3, and PDF text bounds are inside the page. Root-PDF placement/caption
acceptance remains required after paper integrates these assets. The
standalone numerical presentation is complete; no analysis supplement is
still awaited under experiment-repo#4.


## Complete integrated placement accepted, 2026-11-05

Re-read Research objective #1, the idea Brief and commitment #3, then inspected
paper-repo's actual root `main.pdf` at
`8aa79e935dae75d9fdcc3be7b9f290d9c16692a1` (48 pages, SHA-256
`3f4b1999412683e325d108f9b2ab0347ad53f95dfb938c5354f5504f322a4239`).
This is the integrated delivery, not a local rebuild. Independently rasterized
and opened every page containing our assets at 1.5x PDF resolution: 6, 7, 11,
12 and 20–41. All 19 numerical figures, five numerical tables and the archived
pilot figure/table were inspected with their actual captions and surrounding
text. There are no requested presentation corrections for this revision.

- Main figures 1/2 on pages 6/7 preserve the nine fitted-model conditions,
  actual prediction-row coordinates, method encodings, supplied boundary plus
  markers and intervals, all 18 strict-recovery conditions and the highlighted
  0/30 input. The ECDF's masses at zero and one remain visible. Their captions
  distinguish observed primary success, strict recovery, finite input fractions
  and population/individual certification, with 60-input/30-run denominators.
- Archived pilot figure/table on 11/12 retain all labels and 18 table rows.
  Their initial-implementation/float64-history scope is explicit; they are not
  presented as main reliability or corrected-implementation latency results.
- Background phase costs on 20 retain six rows, CPU/wall/memory units, excluded
  setup scope, overlapping timers and all 18 import notices. Figures on 21/22
  clearly separate exact-target shift/top1 match from changed-game estimation
  accuracy, with categorical B8/B128 coordinates, 12-input/20-run denominators,
  conditional intervals and the one-draw/size confounding limitation. B32
  remains a comparison target rather than population truth.
- Tables on 23–26 preserve all 9 coverage, 18 lowest-budget rate, 9 reference
  caution and 9 compute rows. Captions are above the tables; numeric columns,
  rate intervals/marks, actual-work/CPU units and small reference costs remain
  legible. The main compute table retains resumed-process and interrupted-wall
  scope caveats. No row or caption is clipped.
- Matched-scale reference-error/two-run-disagreement figure on 27 retains its
  shared normalization and distinct line styles. The caption states that
  pairwise disagreement is not single-run accuracy. CPU and interrupted-wall
  figures on 28/29 retain their different timing interpretations; the wall
  plot is not offered as a deployment-latency or equal-cost comparison.
- Conditions on 30–32 retain sparse stratum n and absent low-signal strata;
  no empty stratum is rendered as zero success. Scenario/component displays
  on 33–38 retain cutoff/selection/floor legends, supplied interval switches,
  distinct mean-overlap versus pass-rate axes and probability-unit absolute
  errors. The floor curves coincide for the stated reason, not an omission.
  Input distributions on 39–41 retain full [0,1] axes, endpoint masses, method
  and budget encodings, and finite-30-run/no-individual-certificate caveats.

The independent artifact audit in the actual delivery layout passes all 25
main/background manifests and all 19 numerical PDFs: input/output hashes,
5.5-inch physical widths, embedded fonts without Type3 and text bounds. All
20 placed figure Form XObject widths, including the pilot, are 396 PDF points;
manual inspection confirms full-column placement. All 19 numerical caption
wrappers exactly match their supplied plain-text sources after reversing TeX
escaping and the equivalent leq/geq math-symbol substitutions. No numerical
asset, statistic, denominator or inference was changed for this acceptance.

The presentation commitment and requests figtab-repo#2/#4 are fulfilled for
this inspected revision. This is presentation-owner acceptance, not independent
scientific review, venue approval or authorization of a final release. Any
later change affecting assets, captions or placement needs a targeted recheck.
