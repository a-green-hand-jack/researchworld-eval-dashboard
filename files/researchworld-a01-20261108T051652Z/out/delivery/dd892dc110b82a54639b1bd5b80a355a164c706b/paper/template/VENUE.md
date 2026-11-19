# Venue: ICLR 2027 (main track), submission-format PDF

Maintained by `venue-repo`. Every requirement below is tagged with its source. **Not established** items are listed at the end; do not treat them as met.

## 1. Choice and reason

The objective (`deliverable.md`) asks for one of ICML, ICLR, NeurIPS, "latest edition's official LaTeX template".

| venue | latest edition | main text | checklist | official template obtained here? |
|---|---|---|---|---|
| **ICLR** | **2027** (template commit 2026-09-01) | **9 pages** | none; **AI use statement required** | **yes** (GitHub ICLR/Master-Template, folder `iclr2027`) |
| NeurIPS | 2026 | 9 pages | mandatory checklist | no: `media.neurips.cc` answers 502 / times out through the world proxy (2026-11-08) |
| ICML | 2026 | 8 pages | none found | no: `media.icml.cc` times out (2026-11-08) |

ICLR 2027 is chosen because it is the most recent edition and the only one whose official style files could be downloaded and checked. Consequence: the objective's "checklist the conference requires" resolves, for ICLR 2027, to the **AI use statement** (required) with the **reproducibility** and **ethics** statements (recommended). There is no NeurIPS-style checklist to fill in. The ICLR 2027 submission deadline (2026-09-25) has passed; the template is used for format only, nothing is submitted anywhere.

## 2. Requirements and their sources

| # | requirement | source |
|---|---|---|
| R1 | Official ICLR 2027 LaTeX style (`iclr2027_conference.sty`, `.bst`), unmodified; "tweaking the style files may be grounds for rejection"; US Letter | template text (`iclr2027_conference.tex` in the template repo); author guide |
| R2 | Main text **at most 9 pages** at submission (10 for rebuttal/camera-ready), strictly enforced; references unlimited; appendix after the references, any length, reviewers need not read it | template text; ICLR 2027 author guidelines page (fetched 2026-11-08) |
| R3 | AI use statement **required**, at most 1 page, not counted in the 9 pages; must state what generative AI was used for and who is responsible | template text (`AI use statement` subsection); author guidelines |
| R4 | Reproducibility statement recommended: one paragraph at the end of the main text, before references, pointing to sections/appendix/code that make results reproducible; not counted in the limit | template text |
| R5 | Ethics statement recommended, at most 1 page, end of main text before references; not counted | template text |
| R6 | Double blind: no author names (leave `\iclrfinalcopy` commented out), no public code links in the paper, third-person self-citation, acknowledgements omitted at submission; code must be anonymized | author guidelines |
| R7 | Text block 5.5 in wide, 9 in high, 10 pt type, tables with caption above, figure captions below, natbib author-year citations | template text, `iclr2027_conference.sty` (`\textwidth 5.5in`, `\textheight 9in`) |
| R8 | Citation style: any style used consistently; use `natbib` (`\citet`, `\citep`); reference list alphabetical | template text |
| R9 | Single PDF (paper, references, appendix); supplementary code anonymized if submitted | author guidelines |

From the objective itself (`deliverable.md`), independent of the venue:

| # | requirement | owner of the part |
|---|---|---|
| O1 | Paper as **PDF and LaTeX source**, with at least: abstract, introduction, related work, method, experiments, discussion and limitations, references | `paper-repo` (`paper/`) |
| O2 | All code and reproduction instructions: environment and dependency versions, data acquisition and data versions, random seeds, run commands and expected run time, and which script produces each table and figure | `experiment-repo` (`analysis/`), `figtab-repo` (`figures/`, `tables/`), root `README.md` by `paper-repo` |
| O3 | Every number/table/figure must come from code in the delivery; failed or unfinished experiments reported as such; only real, consulted citations | all positions |
| O4 | Uncertainty reported (runs, intervals or tests); baselines/controls/ablations appropriate; scope of conclusions stated; limitations discussed | `experiment-repo`, `paper-repo` |
| O5 | Data: record date/version and checksum of every dataset; state licence reasoning (HELM v1.13.0; OLLB `contents` sha `9c09a7ca…`, `results` sha `aa81ecc3…`; the objective's `data.md`) | `experiment-repo`, `paper-repo` |
| O6 | The withheld paper (and anything citing, discussing or reproducing it) must not be searched or read; if encountered by accident, stop and record what, where and how much in the reproduction text | all positions; recorded by `experiment-repo`/`paper-repo` in the reproduction text |
| O7 | Resource bounds: CPU only; at most about 4 CPU-hours (estimate in `resources.md`); one week | `story-repo`, `experiment-repo` |

## 3. Page budget (for `paper-repo` and `figtab-repo`)

* Main text 9 pages including all figures and tables in the main text; the reproducibility, ethics and AI use statements and the references do not count; appendix unlimited (R2-R5).
* Figure geometry: `\linewidth` = `\textwidth` = 5.5 in = 397.5 pt = 13.97 cm (single column, no two-column floats). Full-width figure at most 5.5 in wide; two side-by-side panels about 2.7 in each. Text is 10 pt, so figure fonts of about 8-9 pt after scaling read correctly. Use PDF (vector) figures, US Letter page. Figures must remain legible in black and white or print (template text).
* Suggested allocation of the 9 pages (a guide, not a rule): abstract+introduction 1.25; related work 0.75; setting and method 1.75; experiments (main table + 2-3 figures) 3.5; discussion and limitations 0.75; reproducibility statement 0.25 (free). Everything beyond the headline claims C1-C6 goes to the appendix.
* Review-mode layout puts a line ruler/numbers in the margins; do not cite line numbers.

## 4. Files in this directory (all delivered under `paper/template/`)

| file | origin | SHA-256 |
|---|---|---|
| `iclr2027_conference.sty` | ICLR/Master-Template `iclr2027/` | `797deef41724e93761426ac0cbcca46279a91cc650dd1f0ce76a4f08d2098ea6` |
| `iclr2027_conference.bst` | same | `2d67552db7ed38ccfccb5957b52f95656e25c249724761d3cf5f7922ad1844c5` |
| `natbib.sty` | same | `88bc70c0e48461934cab5b2accef06b74a8b3ac45ad03ccd3f2a6b7e0d6d530d` |
| `fancyhdr.sty` | same | `b56ec4434b9f4607529a4b23dc68ad8d4b94f1f631c8cddaf7da78140d53a5ea` |
| `math_commands.tex` | same (optional notation macros) | `90473c4d0542070db244cea73ef962d6cddc5b2a746757e6a40ddf5fdfb90ba9` |
| `skeleton.tex` | written here; compiles with pdflatex + bibtex (needs a `refs.bib`, as in `paper/refs.bib`), 1 page | n/a |
| `ai_use_statement.tex` | written here: factual draft of R3, edit to stay true | n/a |

Provenance: downloaded 2026-11-08 from `https://github.com/ICLR/Master-Template` (master; upstream commit `46ed6f4c6cef5b175dde23639e77d44c3463b230`, message "2027 template", 2026-09-01). The `iclr2027.zip` in the same repository contains an identical `.sty`. The unmodified sample `iclr2027_conference.tex` compiled to 7 pages on TeX Live in the sandbox, US Letter. The ICLR author guide says the zip is distributed from `media.iclr.cc`; that host was not fetched.

## 5. Not established (do not claim as met)

1. The ICLR 2027 **AI Policy for Authors** page could not be retrieved (guessed URLs returned 404); the statement's content rests on the template's own text and the author guidelines summary. Re-read the policy if a link becomes available.
2. The ICLR 2027 author guidelines (`https://iclr.cc/Conferences/2027/AuthorGuidelines`) and call for papers were read through a web fetch that returns a model-written summary, not the raw page; the page limit (9) agrees with the template's own sentence, but R3-R6 and R9 are second-hand.
3. NeurIPS 2026's and ICML 2026's official files and the NeurIPS 2026 checklist wording could not be obtained, so no checklist from them is shipped. If a reviewer expects a NeurIPS-style checklist, the answers are in the reproducibility statement and appendix, not in a form this repository can certify.
4. The built PDF has not yet been checked against R2: page count of the final manuscript is verified by `venue-repo` only after `paper-repo` delivers one.
5. Anonymity (R6) conflicts mildly with the objective's demand that code be delivered: in the paper refer to the code as "supplementary material"/anonymous artifact; do not print a public repository URL.
