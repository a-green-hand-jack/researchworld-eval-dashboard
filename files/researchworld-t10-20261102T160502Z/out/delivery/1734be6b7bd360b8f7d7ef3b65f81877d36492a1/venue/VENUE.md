# Venue decision and format requirements

Established 2026-11-02 from the objective's `deliverable.md` and from the official NeurIPS 2026 pages
(fetched 2026-11-02): Call for Papers `https://neurips.cc/Conferences/2026/CallForPapers`, Main Track Handbook
`https://neurips.cc/Conferences/2026/MainTrackHandbook` (V2026.3), template
`https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip`
(zip sha256 `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`; contents in `template/`;
`neurips_2026.sty` is `\ProvidesPackage{neurips_2026}[2026-01-29 ...]`).

## Venue
**NeurIPS 2026 (40th), Main Track**, with the official `neurips_2026.sty` and its paper checklist.

Why NeurIPS and not ICML / ICLR (the objective allows one of the three): the objective asks that the
conference's own checklist be filled in "e.g. the NeurIPS paper checklist"; NeurIPS 2026 has a mandatory,
fixed-question checklist that makes the honesty/reproducibility requirements of `deliverable.md` checkable
item by item (error bars, compute, licences, code, LLM-use declaration). NeurIPS 2026 is the latest NeurIPS edition
whose template is published (the 2026 submission deadline, May 2026, has passed; this is a format-compliance
exercise, not a submission). Fact checked on the other two, for the record: ICML 2026 allows 8 main pages; an
ICLR 2027 template exists in `github.com/ICLR/Master-Template` (commit 2026-09-01) but its author guide page
was not reachable (HTTP 404), so its limits are **not established** here; neither was used.

## Requirements (R-numbers are cited by the checker `check_venue.py` and by reviewers)
| # | Requirement | Source | Owner | How verified |
|---|---|---|---|---|
| R1 | Use unmodified `neurips_2026.sty`, default (`main`, anonymous, double-blind) option; no `final`/`preprint` option in the delivered PDF; author block anonymous; no author/institution names, no non-anonymous links | Handbook; `.sty` | paper-repo | `check_venue.py` (sha256 of `.sty`, option grep, "Submitted to" footer in PDF) |
| R2 | Main text ≤ **9 content pages** including all figures and tables; references, appendices, the checklist and acknowledgements do not count | Handbook ("nine content pages") | paper-repo (figtab-repo sizes figures) | `check_venue.py`: page on which the `References` heading appears |
| R3 | Suggested order: content, references, appendices, **checklist last**; no more than 50 MB | Handbook | paper-repo | `check_venue.py` |
| R4 | The paper checklist (15 questions, fixed wording, macros `\answerYes/\answerNo/\answerNA`, 1–2 sentence justification each) is filled in, instruction block deleted, heading `NeurIPS Paper Checklist` kept, no `\answerTODO`/`\justificationTODO` left; a `Yes` points to a section | `template/checklist.tex` | paper-repo; evidence per item from the positions in `checklist_guide.md` | `check_venue.py` |
| R5 | Paper contains at least: abstract, introduction, related work, method, experiments, discussion and limitations, references (`deliverable.md`) | objective | paper-repo | `check_venue.py` section grep |
| R6 | PDF **and** LaTeX source delivered; the source builds with `latexmk -pdf` from the delivered files (the `.sty` included) | objective | paper-repo | build |
| R7 | Every number, table, figure comes from code that was run in this task and is in the delivery; each table/figure maps to its generating script; no placeholder or "illustrative" numbers | `deliverable.md` honest-reporting | experiment-repo (numbers), figtab-repo (figures/tables), paper-repo (text) | reviewers; map in README (R9) |
| R8 | Failed runs, discrepancies and abandoned approaches are reported; experiments not finished are stated as not finished | `deliverable.md` | all | reviewers |
| R9 | Reproduction notes: environment and dependency versions, data acquisition steps and data version (`ppi-python==0.2.3`, tag `v0.2.3`, commit `6b8475b`, any other data with version/date), random seeds, run commands, expected run times, and a table "paper table/figure → script" | `deliverable.md` item 2 | experiment-repo (content), paper-repo (README at root) | reviewers; `check_venue.py` greps the headings |
| R10 | Citations: only works actually consulted and real; `starter_literature.md` items usable | `deliverable.md` | idea-repo/paper-repo | reviewers |
| R11 | Forbidden-content log: the reproduction notes state whether the withheld published paper (or pages about it) was encountered; if yes: what, where, how much was read. If not, say so | `deliverable.md` | all positions; recorded in README | reviewers |
| R12 | Uncertainty reported for every comparative claim (repeats, CI/significance) | `deliverable.md`, objective | experiment-repo, figtab-repo | reviewers |
| R13 | Data licences: `ppi-python` data `.npz` carry **no stated licence** (code is MIT); say so in the paper/checklist, do not claim a licence. Wine/UCI = CC BY 4.0; census PUMS public | `data.md` | paper-repo | reviewer |

## Not established / limits
- The handbook's "Paper Checklist" guide (`neurips.cc/public/guides/PaperChecklist`) was not read in full; answers must
  follow the guideline text inside `template/checklist.tex`.
- Whether the camera-ready extra page applies is irrelevant: the delivery is the review-style (anonymous) version, 9 pages.
- No licence is declared for the delivery by this position.

## Layout numbers for figure/table sizing (from `neurips_2026.sty`)
Single column, letter paper; text width **5.5 in** (396 pt), text height **9 in**, top margin 1 in; body 10 pt Times
(leading 11 pt), captions/footnotes 9 pt/8 pt, `\scriptsize` 7 pt. Submission mode numbers the lines (`lineno`), so figures
must not rely on the margin. Figures should be exported at ≤ 5.5 in wide with ≥ 7 pt text at final size, vector (PDF).
