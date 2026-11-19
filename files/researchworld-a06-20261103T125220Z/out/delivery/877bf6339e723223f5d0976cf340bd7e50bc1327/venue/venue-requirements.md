# Venue and objective requirements

Status: venue rules verified 2026-11-03 UTC; scientific/artifact completion is not certified by this record.

## Selection and authority

Select **ICLR 2027 main conference, anonymous initial-submission format**, the latest ICLR submission template publicly linked by the official 2027 Author Guidelines when consulted. This is a formatting/evaluation choice under frozen `deliverable.md`; it is not an actual conference submission or a claim of acceptance. The study does not depend on obtaining a rebuttal or camera-ready page allowance.

Authority order: frozen objective and `deliverable.md` first; official ICLR 2027 Author Guidelines, AI Policy for Authors, and the unmodified linked template govern formatting. Where the guide's later FAQ says the submission limit is 10 pages, its explicit initial-submission rule and the official template both say 9; use **9**. The guide permits 10 for discussion/rebuttal and camera ready. This record does not use that allowance.

Consulted primary sources (full captured responses and SHA-256 inventory in `provenance/`):

- https://iclr.cc/Conferences/2027/CallForPapers — identifies the 15th ICLR and links the author guidelines; no paper/proceedings search performed.
- https://iclr.cc/Conferences/2027/AuthorGuidelines — sections Paper formatting, Supplementary Materials, Required: AI use statement, Recommended: Ethics statement, Recommended: Reproducibility statement.
- https://iclr.cc/Conferences/2027/AIPolicyForAuthors — mandatory disclosure scope and author responsibility.
- https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip — official assets, especially `iclr2027_conference.tex` and `.sty`.

The venue search also inspected official ICLR 2026 AuthorGuide, ICML 2026 AuthorInstructions and NeurIPS 2026 CallForPapers to select a venue; their rules are not applied. No topical literature or submission listings were searched. No prohibited-paper encounter was observed in this venue-source inspection; no exhaustive independent novelty search is claimed.

## Required paper setup and length

Use `\documentclass{article}`, `\usepackage{iclr2027_conference,times}` and the official `.bst` with natbib author-year citations. Keep `\iclrfinalcopy` disabled: it prints an acceptance/publication claim in the header. Official submission formatting includes anonymous author rendering, page numbers and review line numbers. Preserve the official style, margins, type size and spacing; do not patch them or shrink the paper to pass a limit. Include figures with `graphicx` and width relative to `\linewidth`.

The initial main text, including abstract, figures and tables, must fit in **9 pages**. Count through the discussion/limitations; a section heading alone does not exempt scientific results from the limit. References are unlimited and excluded. Appendices are unlimited and follow the bibliography; reviewers need not read them, so essential claims and evidence belong in the main text. Prefer one PDF containing main text, statements, bibliography and appendix, as the guide encourages. Use a page break after the main body and before the statements/reference region to make the 9-page boundary easy to verify; this is our audit recommendation rather than a venue requirement.

The objective requires abstract, introduction, related work, methods, experiments, discussion and limitations, and references. Section naming may vary while retaining all content. Supply both the compiled PDF and its complete LaTeX source/dependencies.

## Required accompanying material and statements

**AI use statement: required.** Put an unnumbered section after the main text and before references; the official sample says no more than 1 page and excludes it from the main limit. State the actual AI roles in this study, including AI-developed synthetic generators/methods, hypotheses, experiment design, code and interpretation where applicable. The official AI policy requires disclosure for synthetic-data generation, conceptual/theoretical development, mathematical claims/proof contributions, hypotheses, experiment methodology, method implementation, translation, data cleaning/reformatting, qualitative analysis and interpreting results. It recommends disclosure of writing, coding, figures, literature work and other assistance. Disclose the research-agent workflow truthfully. Do not copy the sample's claim of manual/two-author verification or human review unless that happened. State the checks that actually took place. Distinguish the LLM studied experimentally from AI used to conduct the research.

**Ethics statement: recommended**, excluded from the main limit, at most 1 page; address benchmark/model limitations, statistical misuse and research integrity as warranted, without inventing approvals. The guide requires conference participants to acknowledge its ethics code in the submission process; there is no actual conference submission here.

**Reproducibility statement: recommended**, a paragraph excluded from the main limit before references, pointing to actual methods, appendix and supplied code/instructions. It does not replace the objective's mandatory detailed reproduction documentation.

**Checklist:** no separately required attached paper checklist was found in the consulted official ICLR 2027 Author Guidelines, AI Policy or template; the template archive contains no checklist file. Therefore do not add a NeurIPS checklist or claim one is required. A live OpenReview submission form was not inspected: account, author, reviewing, ethics and AI form declarations are not established or completed here. If another official requirement appears, record and implement it; this scope statement does not waive the objective's requirement to include any checklist the chosen venue actually requires.

Author contributions are optional. Acknowledgments use an unnumbered third-level heading and must not compromise submission anonymity. References should use actual consulted sources and consistent author-year style; the template's sample bibliography is demonstration material, not the study's literature evidence.

## Figure and table instructions

The unmodified style is **single column**: text/column/line width **5.5 in = 139.7 mm = 397.48499 TeX pt = 396 PDF points**; text height **9 in**; US Letter **8.5 × 11 in**. There is no two-column half-width convention. Native full-width figures should be 5.5 in wide; two panels can share this width with an appropriate gap. If a figure is inserted at 0.8 linewidth, design text for its final 4.4 in width.

Official requirements: neat, clean, legible artwork with sufficiently dark lines. Figure number/caption **below** the figure; table number/title **above** the table. Center tables. Consecutive numbering, sentence-case captions/titles (proper nouns retain capitals), captions kept with their artwork; one line space before figure caption and after figure, and around table title/table as illustrated by the template. Color is permitted; captions and text should make sense in black and white. Let the style provide caption spacing/fonts instead of overriding them.

Venue source specifies body **10 pt with 11 pt leading**, but supplies **no numerical minimum for plot labels**. Our presentation recommendation (not an official minimum): 9–10 pt labels at final size, no labels below 8 pt, distinguish methods with markers/dashes as well as color. Export vector PDF with embedded fonts and PNG previews; uncertainty definitions, repeated-run units, metric denominators and units should be explicit in captions. These last reporting recommendations serve the objective's rigor/reproducibility requirements; they are not invented venue rules.

## Objective compliance matrix

| Required content/artifact | Checkable acceptance evidence | Delivery owner/function |
| --- | --- | --- |
| Score gap, its drivers and effect on conclusions | Definitions of selected target/report, executed comparisons over drivers, explicit decision comparison and uncertainty | story settles; experiment results; figtab displays; paper explains |
| More reliable reporting and its validation | Concrete method/estimand, complete selection/evaluation experiment, error/calibration/utility evidence and limits | story/experiment; paper |
| Real LLM + real benchmark | Newly generated responses, model/version and prompts, pinned MMLU-Pro revision, item identifiers/scorer and actual runs; synthetic-only delivery fails | experiment |
| Full paper in latest official permitted venue template | PDF + complete LaTeX; ICLR2027 assets match manifest; <=9 main pages; required sections, AI statement and truthful claims | venue assets/rules; paper manuscript/build |
| Uncertainty and comparisons | Measured repeated-run uncertainty or valid intervals/tests, relevant controls/baselines and limitations | experiment; review judges |
| Every paper figure/table reproducible | Script-to-figure/table map plus machine-readable input/run provenance and reproducible rendering commands | experiment/figtab; paper integrates |
| All code and reproduction instructions | Exact environments/dependencies, dataset acquisition/version, seeds, commands, expected runtimes and actual compute | each code owner; paper integrates |
| Failure and scope disclosures | Failed/abandoned/incomplete runs recorded; no planned/estimated values reported as measurements; actual compute separate from supplied estimates | each owner; paper integrates |
| Citation/prohibited-material compliance | Only consulted real sources cited; no search/reading/use of the withheld work or discussions; any accidental encounter logged with scope | every position; context source record |
| Resource scope | One week, CPU emphasis, <=one 24GB GPU/equivalent API; actual environment and consumption recorded | experiment; feasibility/review |

The pinned dataset revision is `b189ec765aa7ed75c8acfea42df31fdae71f97be`; the supplied resource estimates are not measured allocations or study runtimes. A finite audit score is evidence about fresh-question performance, not known population truth. This matrix records obligations, not a conclusion that they have been met.

## Verification and integration limits

`verification/dimensions.tex` builds with the unmodified style; its measurement record includes tool version and exact dimensions. The official sample is also built as an asset-integrity check; no sample content is a scientific result. Assets are preserved byte for byte. The archive does not contain a top-level license; preserve notices and do not infer a license or publication rights. Official availability for conference formatting does not establish acceptance, external submission, or scientific compliance.

The final manuscript, reproduction code, completed statements, actual main-page boundary and figure legibility must be checked in paper-repo's built delivery. Those scientific/assembly checks belong to the respective owners and independent review. Exact delivered paths and the required-artifact declaration follow story-repo's CODEOWNERS allocation.

## Settled delivery paths

Story's answer in world/story-repo#7 (allocation source `study/CODEOWNERS.proposed`, paper PR #5) assigns all `venue/` paths to venue. Paper owns root `paper.tex`, synchronized `paper.pdf`, `references.bib`, `Makefile`, `README.md`, `sections/` and integration `docs/`; experiment owns `analysis/`; figtab owns `figures/`, `tables/`, `presentation/`. No standalone scientific checklist file is declared because none was established as required. The presence declaration `venue-artifacts.json` uses these assigned paths. It enforces nonempty artifacts only; the matrix above governs content and completeness. See `INTEGRATION.md` for build search paths.
