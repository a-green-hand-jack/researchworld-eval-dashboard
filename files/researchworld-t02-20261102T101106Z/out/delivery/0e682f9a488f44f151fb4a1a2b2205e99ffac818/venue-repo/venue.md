# Venue: NeurIPS 2026 main track (40th NeurIPS, Sydney)

Objective (`deliverable.md`): pick one of ICML/ICLR/NeurIPS, use the latest edition's official LaTeX template,
obey its main-text page limit, fill in the checklist the venue requires.

## Choice and why
- **NeurIPS 2026, Main Track.** Reasons, all checked on 2026-11-02:
  - Its official template is published and downloadable (`template/`, provenance in `template/SOURCE.md`)
    and its handbook gives a complete, unambiguous rule set (https://neurips.cc/Conferences/2026/MainTrackHandbook,
    https://neurips.cc/Conferences/2026/CallForPapers).
  - It has the mandatory paper checklist the objective names as the example (`template/checklist.tex`, 16 questions).
  - A small, CPU-only, empirical study of a training phenomenon fits "Generalization", "Deep learning" and
    "in-depth analysis of existing methods ... beyond the scope of the original work" in its call.
- Not chosen: ICML 2026 (author instructions read: main body up to 8 pages, references/appendix extra, code encouraged; I did not
  find a mandatory checklist there, while the objective expects one). ICLR 2027 (call read: deadline 25 Sep 2026) is the newer cycle,
  but a scan of its Call for Papers and Author Guide pages showed no template link (and I did not read the rules in full), so a "latest
  official template" for it is unverified. If a position cannot use NeurIPS 2026, ask here before switching.

## Hard format rules (NeurIPS 2026 Main Track)
| Item | Requirement | Source |
|---|---|---|
| Template | `\usepackage{neurips_2026}` (default = `main`, anonymous submission). Do not use `final`/`preprint`/`nonanonymous` unless the world decides to simulate camera-ready; do not touch margins, fonts, spacing | template header, handbook |
| Main text | at most **9 content pages**, figures and tables included | handbook "Formatting" |
| Not counted | references, optional technical appendices, the paper checklist | handbook |
| Order | main text -> references -> (appendix) -> checklist (`\input{checklist.tex}` after `\newpage`, as in the example) | template; a wrong order is a minor violation per the FAQ |
| Appendix | unlimited, but "optional reading": evidence the claims depend on must be in the 9 pages | template appendix note |
| Checklist | mandatory; missing -> desk rejection. Keep headings, questions, guidelines unchanged; delete the instruction block (between `%%% BEGIN/END INSTRUCTIONS %%%`) but keep the heading "NeurIPS Paper Checklist"; answer only with `\answerYes{}`, `\answerNo{}`, `\answerNA{}` each followed by a 1-2 sentence justification (for Yes: point to sections). No `\answerTODO{}` / `\justificationTODO{}` may remain | `checklist.tex` |
| Anonymity | double blind: no author names/affiliations (template prints "Anonymous Author(s)"), no acknowledgments/funding section in the anonymized version (use the `ack` environment, which hides itself), no links to identifying repos; self-citations in third person; code links must be anonymous | handbook |
| Citations | natbib is loaded by the style; any consistent style; references may be `\small` | template |
| Figures/tables | `booktabs` is loaded; text in figures should stay legible at print size (not a stated rule; reviewer expectation) | template |
| LLM/agent use | must be described in the setup section only if an important, original or non-standard part of the method; authors are responsible for all content, no hallucinated plots or citations. Checklist item 16 answers this | handbook "Author Use of Agents and LLMs" |
| Supplementary code | NeurIPS takes code as a separate anonymized ZIP (<=100 MB) with training/evaluation code, dependency spec, and run instructions (https://github.com/paperswithcode/releasing-research-code is the cited guide). Here the code lives in the delivery repository (see below) | handbook |

## What the objective adds on top of the venue (also required, from `deliverable.md`)
1. Paper in PDF **and** LaTeX source, containing at least: abstract, introduction, related work, method, experiments,
   discussion & limitations, references. (NeurIPS does not itself require a "Limitations" section; the checklist asks about it.)
2. All code plus a reproduction document that states: environment and dependency versions; how data are obtained and
   which version (data are synthetic, generated in memory: state the generator, `p`, the operation, the split rule, no download/license);
   random seeds; run commands and estimated run time; **which script produces each table and each figure**.
3. Honest reporting: every number/table/figure produced by actual runs reproducible by the shipped code; failed, negative and
   unfinished runs reported as such; only real, consulted references.
4. Statistical uncertainty for every conclusion (multi-seed, CIs or tests). (Objective, `TASK.md`.)
5. The **forbidden-content rule**: the published paper that already studied this question, and any page citing, discussing or
   reproducing it, must not be searched, opened or used. If one is met by accident, stop reading and record in the reproduction
   document what, where, and how much was read. Every position that searches literature is bound by this; the reproduction document needs a
   section "Withheld-paper exposure" that says "none encountered" or gives the record.
6. The scope statement: conclusions must state where they apply and where they fail.

## What cannot be established
- Nothing can be verified about acceptance, the real submission portal, or OpenReview formatting checks; "meets venue" here means: template
  unmodified, builds, <= 9 content pages, checklist complete, anonymized.
- ICLR 2027 / ICML 2026 template availability was not exhaustively checked (see above).
- The page count must be checked on the built PDF by whoever builds it (`pdfinfo`, and visually where "References" starts); the
  9-page rule counts up to the end of the Discussion/Conclusion, before references.

## Supplied files
- `template/` unmodified official files and provenance.
- `checklist-guide.md` per-question map of what the study can honestly answer and which evidence/paths each answer needs
  (suggestions; the answers themselves belong to `paper-repo`).
- `repro-doc-requirements.md` skeleton the reproduction document must fill (the owner of the document is `paper-repo`).
- `venue-artifacts.json` (in `venue-repo`) declares the required delivered paths: paper/main.tex, paper/main.pdf, paper/checklist.tex, paper/neurips_2026.sty, paper/REPRODUCE.md, experiments/, results/, figures/.

## Layout for the build (agreed paths from story-repo's work division)
`paper/main.tex` starts from `venue/template/neurips_2026.tex` (keep `\usepackage{neurips_2026}`), `paper/neurips_2026.sty` is a byte-identical copy of
`venue/template/neurips_2026.sty`, `paper/checklist.tex` starts from `venue/template/checklist.tex` (answers filled per `venue/checklist-guide.md`),
`paper/REPRODUCE.md` follows `venue/repro-doc-requirements.md`. Code in `experiments/`, outputs in `results/`, figures and table files in `figures/`.
