# Venue: NeurIPS 2026 main track (double-blind)

Sources (fetched 2026-11-02): https://neurips.cc/Conferences/2026/CallForPapers,
https://neurips.cc/Conferences/2026/MainTrackHandbook, template package
https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
(sha256 `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`; files in `venue/template/`, hashes in `template/SHA256SUMS`).

## Why NeurIPS 2026
`deliverable.md` lets the study pick one of ICML / ICLR / NeurIPS, use the latest edition's official
template, and fill in the checklist the venue requires. NeurIPS 2026 has a published, dated template
(`neurips_2026.sty`, 2026-01-29) and a mandatory paper checklist, which is the checklist the objective
names as its example. ICML 2027 has no call yet (404). ICLR 2027 has a call (paper deadline 2026-09-25)
but its template was not located on the call page and ICLR has no mandatory checklist; so the choice is
NeurIPS 2026. This is a choice among options the objective permits, not a requirement of it.
Not established: whether an ICLR 2027 template exists elsewhere; not needed for this choice.

## Format requirements (verified in the 2026 handbook and template)
| Item | Requirement | Source |
|---|---|---|
| Template | `\usepackage{neurips_2026}` (default = Main track, anonymous). Do not alter margins, fonts or the style file ("tweaking ... grounds for desk rejection"). `preprint`/`final` options de-anonymise; the delivered version for review should stay in the default (anonymous) mode unless the objective's users need names (none are asked for). | handbook, `neurips_2026.tex` |
| Main text | at most **9 content pages**, figures and tables included. | handbook; `neurips_2026.tex` l.130 |
| Not counted | acknowledgments, references, technical appendices (no page limit), the paper checklist. | same |
| Order | main text, references, appendices, then checklist (`\input{checklist.tex}` at the end). | handbook; `neurips_2026.tex` l.492 |
| Checklist | mandatory, 16 questions; answer only with `\answerYes{}`, `\answerNo{}`, `\answerNA{}` plus a 1-2 sentence justification; delete the instruction block but keep the heading "NeurIPS Paper Checklist"; do not edit questions or guidelines. No `[TODO]` may remain. Papers without it are desk rejected. | `checklist.tex` |
| Appendix | optional reading; the paper must stand alone, critical experiments must be in the main text. | `neurips_2026.tex` l.486 |
| Anonymity | double-blind: no author names/affiliations, self-citation in third person, no identifying URLs; the `ack` environment hides the acknowledgments in anonymous mode. | handbook |
| Citation style | any consistent style; references may be set in `\small`. | `neurips_2026.tex` |
| Funding / competing interests | declared in the `ack` environment (hidden in anonymous mode). | `neurips_2026.tex` |
| LLM use | use of agents/LLMs must be described in the experimental setup if important, original or non-standard; routine editing/code help need not be, but authors answer for all content. The objective additionally requires disclosing LLM assistance (resources.md) and the checklist has a "Declaration of LLM usage" item (Q16). | handbook; `resources.md` |
| Code and data | supplementary code goes in a separate ZIP (<=100 MB), not in the PDF; here code is the repository itself. | handbook |
| Size | PDF <= 50 MB. | handbook |

## Requirements from the objective (what the delivery must contain)
Sources: `/initial-state/inputs/0/{TASK,deliverable,data,resources}.md`.

| # | Requirement | Verifiable by | Owner (by function; paths pending) |
|---|---|---|---|
| R1 | Complete paper as **PDF and LaTeX source**, NeurIPS 2026 template, <=9 content pages | `venue/tools/check_pdf.py`; LaTeX tree builds | paper-repo |
| R2 | Sections: abstract, introduction, related work, method, experiments, discussion & limitations, references | `pdftotext` heading scan | paper-repo |
| R3 | Completed NeurIPS checklist inside the PDF, answers consistent with the repo (compute, seeds, licences, LLM use) | checklist has no `[TODO]`; each Yes points to a section | paper-repo, with venue input below |
| R4 | Study based on real data from >=2 distinct evaluation designs (crowd votes, expert labels, LLM judge, sports); the scale of perturbation and the cross-dataset comparison are defined and justified in the paper | experiments section | story-repo / experiment-repo / paper-repo |
| R5 | Conclusions state conditions and limits, not one number; negative / "depends" results acceptable; uncertainty reported (repeats, CIs or tests) | results + discussion | experiment-repo / paper-repo |
| R6 | Every number, table and figure in the paper comes from code actually run and re-runnable; no placeholder or synthetic numbers (synthetic data allowed only if declared as synthetic); failed or unfinished runs reported as such | provenance table (R8), spot re-run | experiment-repo, figtab-repo |
| R7 | Code and **reproduction instructions**: environment and dependency versions, data acquisition steps and data versions (HF/GitHub commits and sha256 from `data.md`), random seeds, run commands, expected run time | `REPRODUCE.md`-style document in the code tree | experiment-repo (code), paper-repo (document, as divided by story-repo) |
| R8 | A map stating which script generates each table and figure of the paper | table in the reproduction doc | figtab-repo + experiment-repo |
| R9 | Raw data kept in a `data/` working directory, **not** committed to the repository or submitted with the paper; sources, versions and checksums recorded | `.gitignore`; checksum list | experiment-repo |
| R10 | Cite only literature actually consulted; no invented references | bib entries traceable to a fetched source | idea-repo / paper-repo |
| R11 | Disclose LLM assistance (reading, code generation) in the paper | paper section + checklist Q16 | paper-repo |
| R12 | **Forbidden-source rule**: the published paper that studied this exact question (and every mirror, preprint, abstract page, review page, slides, poster, video, blog, code repository, and any page citing/discussing/reproducing it) must not be searched, accessed, read or used; its title/authors/results must not be guessed or searched. `starter_literature.md` items and unrelated literature are allowed. If such content is met by accident: stop reading and record in the reproduction notes what, where, and how much was read. | the reproduction notes carry a section "Forbidden-source encounters" (even if "none") | every position that searches; recorded by paper-repo |
| R13 | Licence caveats: `potsawee/chatbot-arena-llm-judges` has no declared licence; `webdev-arena-preference-10k` carries a licence agreement; NBA data CC-BY-4.0, Arena 55k Apache-2.0, 140k CC-BY-4.0, MT-Bench CC-BY-4.0. Checklist Q12 must reflect what was actually used. I declare no licence for the delivery. | checklist Q12/Q13 | paper-repo |
| R14 | Compute: CPU only, about one week, no paid API, data <= 3 GB, memory 8 GB | checklist Q8 | experiment-repo, paper-repo |

Not established / cannot be verified by the venue position: whether the hidden "published paper" is
among the starter literature (`starter_literature.md` is declared safe to use); the real-world acceptance
of the paper by NeurIPS (outside this world); the exact count of content pages before a build exists.

## Layout facts for figure sizing
`neurips_2026.sty`: single column, text width 5.5 in, text height 9 in, 10 pt body (9 pt `\small`, used for references). Figures should be at most 5.5 in wide (`\linewidth`); sizes and fonts must not be altered to gain space.

## What NeurIPS 2026 reviewers look for
Reviewers score Quality, Clarity, Significance, Originality (each 1 poor ... 4 excellent) in the light of a *Contribution Type* the authors declare at submission (General, Theory, Use-Inspired, Concept & Feasibility, Negative Results); source: Main Track Handbook and https://neurips.cc/Conferences/2026/ReviewerGuidelines (fetched 2026-11-02; the overall-score scale is not on that page and is not established here).
- General: claims well supported by experiments, methods appropriate, work complete not in progress, candour about strengths and weaknesses (Quality); enough information for an expert to reproduce (Clarity); new insight/framing/metric, clear difference from prior work, evaluation of existing methods counts (Originality); unique conclusions about existing data count towards Significance.
- Negative Results: the finding must not be just "an experiment failed"; it needs deeper analysis (conjectures plus careful experiments, or proof), high bar for significance and for surprise relative to a commonly held view.
- This study should therefore be declared as General (a measured sensitivity study); a "small sensitivity" outcome should be argued from analysis, not only from an empirical null, if it is to be framed as Negative Results. This is guidance for `paper-repo`; the declaration itself is made at submission outside this world.
- The objective's own criteria (`deliverable.md`): novelty/positioning, rigour with uncertainty, evidence for every conclusion with stated scope, clarity/reproducibility, honest limitations.
- Reproducibility and LLM use: the checklist is visible to reviewers; "No" with a justification is not grounds for rejection, an unacknowledged limitation is.

## Supplied by this repository
- `venue/template/` : unmodified official NeurIPS 2026 `neurips_2026.sty`, `neurips_2026.tex`, `checklist.tex` (hashes in `SHA256SUMS`). `paper-repo` copies them into its tree unmodified; the `.tex` example is a skeleton to be replaced, the `.sty` and `checklist.tex` questions must stay as is.
- `venue/tools/check_pdf.py` : format check of a built PDF (page limit, order, checklist present with no TODO, anonymity).
- `venue/checklist-notes.md` : per-question guidance on what the facts of this study are likely to support, to be verified by `paper-repo` against the finished work (it is guidance, not answers).
- `venue-artifacts.json` : required delivered paths, declared once `story-repo` names them.

(This file is `VENUE.md` of `venue-repo`, delivered here under `venue/` per `.forgejo/CODEOWNERS`; the source of truth is `venue-repo`.)
