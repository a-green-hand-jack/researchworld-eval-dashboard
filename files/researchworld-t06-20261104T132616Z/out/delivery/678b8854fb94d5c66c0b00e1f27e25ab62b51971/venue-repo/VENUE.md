# Venue: NeurIPS 2026, Main Track (double-blind submission format)

Requirements of the objective (`deliverable.md`) come first; the venue details below only serve them.

## Choice of venue
`deliverable.md` asks for one of ICML / ICLR / NeurIPS, the **latest edition's** official LaTeX template,
its page limit, and its checklist. Chosen: **NeurIPS 2026 main track**, because (checked 2026-11-04)
- its official template is published (`templates/neurips2026/`) and it ships the mandatory paper checklist
  that the objective names as its example;
- ICML 2026 (template exists, 8 pages, no checklist in its instructions) is an earlier edition of the same
  year's cycle; the ICML 2027 author-instruction page exists but says "will be published with the Call for
  Papers"; the ICLR 2027 author-guide URL I tried returned 404. So no newer template than NeurIPS 2026 could
  be established for ICML/ICLR. (Not established: whether an ICLR 2027 template exists under another URL.)
- Sources: https://neurips.cc/Conferences/2026/CallForPapers, https://neurips.cc/Conferences/2026/MainTrackHandbook,
  https://icml.cc/Conferences/2026/AuthorInstructions (read 2026-11-04).

## Format rules (verifiable)
| Item | Requirement | Check |
|---|---|---|
| Template | `\usepackage{neurips_2026}` (default = `main`, anonymous, line numbers). Do not use `final` (accepted papers only) and do not edit margins/fonts/`.sty`. | `tools/check_paper.py` compares `.sty` hash |
| Main text | **at most 9 pages including figures and tables**. Acknowledgments, references, checklist and appendices do not count. Over-limit = not reviewed. | page of "References" heading; `check_paper.py` |
| Order | main text, references, (appendix), checklist (checklist follows references/appendix) | `check_paper.py` |
| Required sections (objective) | abstract, introduction, related work, method, experiments, discussion & limitations, references | read by reviewers |
| Checklist | `checklist.tex` included, all 16 `\answerTODO{}` replaced by Yes/No/NA with 1-2 sentence justification; Yes points to sections. Missing checklist = desk rejection. Guide: `checklist_guide.md` | `check_paper.py` |
| Anonymity | no author names/affiliations, no acknowledgments, self-citations in third person, no identifying URLs in paper, code or supplement. Repo URLs must be anonymized or omitted in the PDF. | grep |
| Size | PDF <= 50 MB; supplementary ZIP <= 100 MB (code, no raw data) | `ls -l` |
| LLM use | LLM/agent use that is "important, original or non-standard" part of the method must be described; the objective additionally requires disclosing any LLM assistance (literature reading, code generation) in the paper. Authors are responsible for every citation. | Disclosure paragraph in paper |
| Bibliography | natbib is loaded by the style; only references actually consulted and verifiable | spot check |

NeurIPS says nothing the style file enforces about the page count; `latexmk` will not warn. The check is manual/scripted.

## Deliverables required by the objective (and owner proposals)
1. Paper: **PDF + LaTeX source** (builds from source with `latexmk -pdf`, bib included, template files included).
2. **Code and reproduction instructions**: environment and dependency versions, data acquisition steps and
   dataset versions (commits and sha256 in `data.md`), random seeds, run commands, expected run time, and a
   **table mapping every paper figure/table to the script that produces it** (`templates/REPRODUCE_template.md`).
3. Raw data stays in `data/` outside the repo / submission (objective). Record source, version, checksum only.
4. Honest reporting: every number/figure/table comes from code that is shipped; failed/unfinished runs reported as such;
   only real, consulted references.
5. Restricted-content rule: record in the reproduction notes anything met that belongs to the excluded paper
   (what, where, how much was read) — section "Excluded-content disclosure" in the template, even if "none".
6. Third-party data licenses to state in the paper/checklist: Arena-55k apache-2.0, Arena-140k cc-by-4.0, MT-Bench cc-by-4.0,
   FiveThirtyEight NBA CC-BY-4.0, LLM-judge set (potsawee) license undeclared (Kaggle origin), WebDev Arena has a click-through
   data license. Only datasets actually used need citing.

## Open point on the restricted-paper rule (needs attention from idea-repo / story-repo)
`starter_literature.md` item 8 (arXiv 2508.11847, "Dropping Just a Handful of Preferences Can Change Top LLM Rankings")
matches the description of the paper the objective says must not be retrieved (a published paper on exactly this question),
yet the same objective says starter-literature items may be used normally. I have **not** opened it. The conservative
reading is: do not read item 8 or anything citing/discussing it; if someone does, disclose it in the reproduction notes.
Items 4, 5 (influence/robustness metrics) are generic background; items 6 and 7 are listed as usable. That decision belongs to
`story-repo`; I only record it here.

## Not established / limits
- Exact NeurIPS 2026 submission-time page rule for "the checklist plus appendices" is as stated by the Handbook (not counted);
  the Handbook was read via a summarizing fetch, so quote the Handbook, not this file, if it matters.
- Whether the PDF will be judged by a format checker: NeurIPS has none described; no checker exists here.
- Nothing here is a submission to NeurIPS; the release is a reviewed research delivery.
