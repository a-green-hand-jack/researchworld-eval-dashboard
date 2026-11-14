# Venue: NeurIPS 2026 main track (decided by venue-repo, 2026-11-04)

Objective (`deliverable.md`): pick one of ICML / ICLR / NeurIPS, use its **latest** official LaTeX template, keep to its main-text page limit, fill the venue's checklist. Status of each item: **[E]** established (read from the official page or template, source given), **[N]** not established.

## Choice and why
NeurIPS 2026, **Main Track, default (anonymous submission) mode**. Reasons: (1) its template and rules for the current year are published and downloadable (below), (2) the objective's own example is the NeurIPS paper checklist, which is part of the template, (3) the 2026 contribution types include *Negative Results*, matching the objective's "negative results are equally valuable", (4) the page rule (9 pages, references/appendix/checklist excluded) is the clearest to verify mechanically.
Alternatives checked 2026-11-04: ICML 2026 (author instructions found: 8 pages at submission / 9 camera-ready, `icml2026.zip`; the template itself was not downloaded by me) and ICLR 2027 (call for papers found; its AuthorGuidelines page returned HTTP 404, so its page limit and template could **not** be established) [N].

## Requirements [E]
| item | requirement | source |
|---|---|---|
| template | `neurips_2026.sty` (dated 2026-01-29), shell `neurips_2026.tex`, `checklist.tex`; the only accepted template; do not alter margins/fonts | `https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip` (sha256 of the zip `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`; file hashes in `template/SHA256SUMS`); linked from `https://neurips.cc/Conferences/2026/CallForPapers` |
| mode | `\usepackage{neurips_2026}` with **no** `final`/`preprint` option: anonymous, line numbers on. `final` is for accepted papers only | template text; Main Track Handbook |
| page limit | **9 content pages** including all figures and tables. Acknowledgments, references, technical appendices, checklist do not count (camera-ready would be 10) | `https://neurips.cc/Conferences/2026/MainTrackHandbook` (V2026.3); template §1.1 |
| page size / file | US letter, PDF ≤ 50 MB; one PDF in the order paper, references, appendices, checklist; code/data ZIP ≤ 100 MB separately | Handbook, template |
| checklist | the 17-item NeurIPS Paper Checklist (`template/checklist.tex`) is mandatory, part of the PDF, after references/appendix. Keep the heading "NeurIPS Paper Checklist", delete the instruction block, keep every question and guideline, answer only with `\answerYes{}/\answerNo{}/\answerNA{}` plus a 1–2 sentence `\justification`; "Yes" justifications must point to sections. Papers without the checklist are desk rejected | `checklist.tex` instructions |
| anonymity | no author names, no acknowledgments section (use the `ack` environment, which hides itself), third-person self-citation, anonymised links/code | Handbook |
| appendix | "optional reading"; main claims must stand alone in the 9 pages | template Appendix |
| LLM usage | declare LLM use only if it is an important, original or non-standard part of the core method (checklist item 17); hallucinated citations violate the Code of Conduct | Handbook, checklist |
| contribution type | chosen in the OpenReview form (General / Theory / Use-Inspired / Concept & Feasibility / Negative Results), not in the PDF; recommend decided by the story once the result is known | Handbook |
| required sections (objective) | abstract, introduction, related work, method, experiments, discussion & limitations, references | `deliverable.md` |

## Requirements of the objective beyond the venue [E, from `deliverable.md`]
Code and reproduction notes: environment/dependency versions, data acquisition and data version (commit `55faff49…`), random seeds, run commands and expected runtime, and **which script produces each table and figure**. Every number/figure reproducible from shipped code; failed/abandoned runs and unfinished experiments stated as such; only cited works actually read; a note in the reproduction notes if any forbidden-paper content is met by accident.

## Not established / not applicable [N]
- Submission to OpenReview, the funding/competing-interest statement and lay summary (camera-ready only) are outside the delivery; the delivered PDF is the **submission-format** paper. This is not a submission or acceptance.
- NeurIPS 2026 handbook links partly point to 2025 pages; where the 2026 template text and handbook agree (9 pages) I use them.
- "Latest edition" is read as the latest NeurIPS edition with a published template (2026); I did not establish whether a later-dated ICLR 2027 template would count as "more recent".

## Tooling
`tools/check_venue.py PAPER.pdf MAIN.tex` checks page size, the content-page limit (where the first References/Acknowledgments/Appendix/Checklist heading falls), checklist presence/order, leftover `answerTODO`/instruction block, the style option, and required headings. Verified: it flags the unmodified template exactly on the checklist leftovers. It cannot judge content; internal review should still read the PDF.

## Delivered layout (settled with story-repo, paper-repo PR #4/#5)
Venue-owned: `paper/neurips_2026.sty`, `paper/neurips_2026.tex`, `venue-artifacts.json`, `tools/`. Required nonempty in every version (`venue-artifacts.json`): `paper/main.tex`, `paper/main.pdf`, `paper/neurips_2026.sty`, `paper/checklist.tex`, `paper/refs.bib`, `paper/figures/`, `paper/tables/`, `code/`, `results/`, `README.md`. `paper/main.tex` must load `\usepackage{neurips_2026}` with no options and `\input{checklist}` after the references/appendix; run `python3 -I tools/check_venue.py paper/main.pdf paper/main.tex` before each version PR.
