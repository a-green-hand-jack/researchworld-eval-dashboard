# Venue: NeurIPS 2026 main track

Verified 2026-11-04 from the official pages (fetched in this turn); anything not
stated there is listed under "Cannot be established".

## Choice
`deliverable.md` lets the study pick one of ICML, ICLR, NeurIPS, the latest edition, with
that venue's official template, page cap and checklist. We use **NeurIPS 2026, Main Track**:
the task names its paper checklist, the official template (with `checklist.tex`) was
obtained and compiles in the sandbox, and its rules are published. ICML 2026 (8 pages,
no checklist but an impact statement and, for camera-ready, a lay summary) was read as
the alternative; an ICLR 2027 author guide could not be found at the URL tried
(`iclr.cc/Conferences/2027/AuthorGuide` returned 404), so ICLR was not evaluated.

## Sources
- Call for papers: https://neurips.cc/Conferences/2026/CallForPapers
- Main Track Handbook: https://neurips.cc/Conferences/2026/MainTrackHandbook
- Template: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
  (contains only `neurips_2026.tex`, `checklist.tex`, `neurips_2026.sty`, dated 2026-06-23;
  style file header `[2026-01-29 NeurIPS 2026 ...]`).
  SHA-256 of the copies in `venue/`: `neurips_2026.sty` c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a,
  `checklist.tex` 780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6.

## Requirements (quoted or paraphrased from the sources)
| # | Requirement | Source | Checked by |
|---|---|---|---|
| V1 | Main text at most **nine content pages** including figures and tables; over the limit is not reviewed. References, acknowledgments, checklist and technical appendices do not count. (Camera-ready: one extra page; not applicable to this delivery.) | Handbook; template §1.1 | `check_venue.py` |
| V2 | Single PDF ordered: paper, references, appendices, checklist; at most 50 MB | Handbook | `check_venue.py` (order), size by `ls` |
| V3 | Use `neurips_2026.sty` unmodified ("tweaking the style files may be grounds for desk rejection"); US letter, 5.5 x 9 in text block, 10 pt Times | template | hash in `check_venue.py` |
| V4 | Anonymous submission mode: no `final`/`preprint` option, no acknowledgments/funding text (use the `ack` environment), no author names, no public code links in paper or supplement; refer to own work in third person | Handbook; template | `check_venue.py` (heuristic, WARN) |
| V5 | Complete the 16-question NeurIPS paper checklist from `checklist.tex`: answer only with `\answerYes/\answerNo/\answerNA`, a 1-2 sentence justification each (pointing to sections for Yes), keep questions and guidelines, delete the instruction block, keep heading "NeurIPS Paper Checklist". A paper without it is desk-rejected. | checklist.tex | `check_venue.py` |
| V6 | Citations: natbib is loaded; any consistent style. Authors answer for every reference (no hallucinated citations) | template; Handbook | `check_venue.py` (undefined cites); existence of each reference is for `paper-repo`/`internal-review-repo` |
| V7 | Figures: caption below, tables: title above, legible in black/white as well as colour; table titles/captions lower case except first word | template §4 | reviewers/`figtab-repo` |
| V8 | Code supplement (separate ZIP <= 100 MB in the real system): anonymized, self-contained and executable if possible, with dependency specification; non-executable parts explained | Handbook | repro doc, see requirements.md |
| V9 | LLM policy: LLMs are not authors; authors answer for all text, figures and references; LLM use needs describing only if it is an important/original/non-standard part of the method | Handbook | n/a (no such method planned) |

## Objective's own requirements added by venue (from `deliverable.md`)
Paper sections at least: abstract, introduction, related work, method, experiments,
discussion and limitations, references. PDF and LaTeX source. Code and reproduction notes:
environment and dependency versions, data acquisition steps and data version, random seeds,
run commands and expected runtime, a map from each table and figure to the script that makes
it. Every number must come from code that reruns; no invented citations; the
forbidden-content rule (the published paper on this problem is off limits) with a record of
any accidental encounter in the reproduction notes. See `requirements.md`.

## Cannot be established
- The official **checklist guidelines page** was not fetched separately; the question
  texts are those in `checklist.tex`, which we treat as authoritative.
- This delivery is **not a submission**: no OpenReview, no deadline (the 2026 deadlines,
  abstract 2026-05-04 and paper 2026-05-06, have passed), no review. "NeurIPS 2026 format"
  means only the template, page cap and checklist. The paper must not claim acceptance or
  submission.
- The page count the real submission system would compute can differ slightly from
  `check_venue.py` (it reads the PDF text, not the system's own check).
- Whether the title block needs the "Anonymous Author(s)" line is a style choice: the
  template's default mode anonymizes it automatically.
- The supplementary ZIP (100 MB) does not exist as such here: the code lives in the delivery
  tree; its size is below 100 MB if the data (about 48 MB total for ppi-python, downloaded
  at run time, not stored) is not committed.
