# Venue and format requirements

Sources: the objective (`deliverable.md`, `TASK.md`, `data.md`, `resources.md`) first; the venue's rules second.

## Venue choice
NeurIPS 2026 Main Track (the objective lets us pick one of ICML/ICLR/NeurIPS and use that venue's latest
official template). Reasons: NeurIPS 2026 is the current-year edition whose template and handbook are public
(ICLR 2027's submission deadline has passed; ICML 2026's rules are 8 pages with no in-PDF checklist),
and its mandatory paper checklist maps well to the objective's "honest reporting / reproducibility" criteria.
The study is an analysis of existing methods/data, which the NeurIPS call explicitly welcomes
("in-depth analysis of existing methods ... limitations or behavior"). Negative or "depends on conditions"
results are acceptable under the objective.

## Verifiable requirements
Objective-derived (these come first):
1. Paper as PDF **and** LaTeX source; official latest-edition template (`template/`, unmodified).
2. Sections at least: abstract, introduction, related work, method, experiments, discussion & limitations, references.
3. Main text within the venue limit; the conference's checklist filled in.
4. Code + reproduction notes: environment and dependency versions, data acquisition steps and exact data versions
   (commit + sha256 from `data.md`), random seeds, run commands, expected runtimes, and a map
   "every table / figure -> generating script".
5. Evidence: >= 2 different evaluation designs of real data (e.g. crowd votes: Arena 55k/140k; expert/human+GPT-4
   judgments: MT-Bench; LLM judges: potsawee; sports: NBA Elo); define the perturbation scale and the cross-dataset
   comparison, with reasons; uncertainty reported (repeats / CIs / tests); conclusions with scope and limits.
6. Honest reporting: every number/table/figure is produced by shipped code; failed or unfinished runs are
   stated as such; only real, actually-consulted citations; synthetic data must be labelled synthetic.
7. Raw data lives in `data/`, not in the code repo or submission; record source, version, checksum.
8. Forbidden-material rule: do not search for, access, read or use the one published paper on this question, nor
   anything that cites, discusses or reproduces it (see `deliverable.md`, "不得访问的内容"). Caution (a judgement call,
   consistent with story-repo's PLAN.md and idea-repo's Brief): starter_literature item 8 (Huang et al. 2025,
   "Dropping Just a Handful of Preferences ...") is described as a paper on exactly this topic and may be the barred
   paper. Although the objective lists the starter file as usable, nobody should read, cite or search for it; items 1-7
   are fine. If anything forbidden is encountered, stop reading and record what, where and how much was read in
   `REPRODUCE.md` (required section, even if the entry is "nothing encountered").
9. Data terms: potsawee data has no stated license (check upstream terms before use); WebDev Arena requires
   its dataset agreement; Arena-55k is apache-2.0, 140k cc-by-4.0, MT-Bench cc-by-4.0, NBA CC-BY-4.0.
10. LLM-assistance disclosure: the objective requires disclosing it in the paper.

NeurIPS 2026 rules (Main Track Handbook, https://neurips.cc/Conferences/2026/MainTrackHandbook, read 2026-10-28):
- <= **9 content pages** including all figures and tables; references, appendices and the checklist do not count;
  the camera-ready gets a 10th page. Single PDF: content, references, appendices, then the checklist.
- Double-blind: anonymous authors (the `neurips_2026` default option), no acknowledgments, anonymous links
  (also in code / supplement). The `final`/`preprint` options are not used for the review PDF.
- Mandatory **NeurIPS Paper Checklist** (16 items; Yes/No/NA with 1-2 sentence justification, pointing to sections);
  papers without it are desk-rejected; keep headings/questions unmodified.
- Do not alter margins/fonts; max PDF 50 MB; separate code ZIP <= 100 MB (data excluded).
- LLM use: describe in the experimental setup if important/original; also disclose per the objective.
  Authors are responsible for all figures (no hallucinated plots).
- Appendix is "optional reading": the paper must stand alone; main claims cannot rest on appendix-only evidence.

## Template geometry (measured by compiling `template/neurips_2026.sty`, default option)
Single column. Text width 397.5 pt = 5.50 in; text height 650.4 pt = 9.0 in. Body font Times (`ptm`) 10 pt / 10.95 pt
leading; `\small` 9/10 pt, `\footnotesize` 9/10 pt per the .sty, `\scriptsize` 7/8 pt. Figures should be made at
5.5 in width (or 2.7 in for side-by-side pairs) with text >= 7 pt at final size; tables in `\small` or `\footnotesize`.
Citations: natbib loaded by default; author-year or numeric both allowed, any reference style if consistent
(suggest `\bibliographystyle{plainnat}` + BibTeX). Appendix after references via `\appendix`; checklist via
`\input{checklist.tex}` last. Colour is allowed; use colour-blind-safe palettes and distinguish series also by
marker/linestyle (reviewers may print).

## Layout (paper-repo CODEOWNERS, story-repo PR #3)
`venue/` is mine: `venue/VENUE.md` (this file), `venue/template/` (the unmodified template files). `paper/` is
paper-repo's: it copies the template files from `venue/template/` into `paper/` and keeps `checklist.tex` inside
`paper/`. `REPRODUCE.md` (repo root) is experiment-repo's and must hold the reproduction items of requirement 4 and 8.

## Not established
- Whether the 9-page limit is met can only be checked on the compiled paper (content pages = everything before the
  references); I check it against the PDF of each version.
- File names of the paper PDF/source: asked of paper-repo (venue-repo#3 reply); `venue-artifacts.json` lists
  only names fixed by CODEOWNERS until then.
