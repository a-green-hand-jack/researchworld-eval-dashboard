# Venue: who the delivery is for, and the format that follows

Established by `venue-repo`, 2026-11-04. Sources are pages fetched that day; nothing here is from memory.

## 1. Choice

**NeurIPS 2026, Main Track** (the 40th NeurIPS), double-blind submission format.

Why this one (the objective lets the study pick one of ICML / ICLR / NeurIPS and use that venue's *latest* edition):
- Its official template and checklist are published and were obtained and test-compiled (see §3). The objective names the NeurIPS paper checklist as its example of a required checklist, and the checklist is part of the template, so it can be filled in and checked in the delivery.
- Other candidates on 2026-11-04: ICLR 2027 (author guidelines and style zip are online: 9 content pages, no checklist but a mandatory *AI use statement*) and ICML 2026 (past edition; ICML 2027 CfP "will be posted soon", no template). ICLR 2027 is a valid alternative of equal page limit; it was not chosen because its mandatory item is not the checklist the objective expects. "Latest edition" is read as the newest edition whose official template exists for that venue; for NeurIPS that is 2026. This reading is an interpretation of the objective's wording and is stated in the paper's reproduction notes.

Sources:
- CfP: https://neurips.cc/Conferences/2026/CallForPapers (links "Paper template")
- Handbook: https://neurips.cc/Conferences/2026/MainTrackHandbook
- Template zip: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
  (contents: `neurips_2026.sty` [ProvidesPackage 2026-01-29], `neurips_2026.tex`, `checklist.tex`; hashes in `venue/neurips2026/SHA256SUMS`)

## 2. Requirements, checked against the objective (`deliverable.md`)

| # | Requirement | Source | What follows |
|---|---|---|---|
| V1 | Use the official `neurips_2026.sty` unmodified ("tweaking the style files may be grounds for desk rejection"; margins, font sizes fixed) | template §1 | `paper-repo` must not edit the `.sty`; check by hash (`tools/check_venue.py`) |
| V2 | **Main text ≤ 9 pages**, including all figures and tables. References, acknowledgments, appendices and the checklist do **not** count | template, Handbook | PDF page where "References" begins must be ≤ 10 (i.e. main text ends on or before page 9) |
| V3 | **Paper checklist is mandatory** (a paper without it is desk-rejected); placed after references and after any appendix; all 16 questions answered with `\answerYes/\answerNo/\answerNA` plus a 1–2 sentence justification; instruction block deleted but heading "NeurIPS Paper Checklist" kept; questions and guidelines unmodified; no `\answerTODO` / `\justificationTODO` left | `checklist.tex`, Handbook | Fill from the final paper; "Yes" answers point to sections; honest "No/NA" with justification where e.g. no GPU/API existed. Owned by `paper-repo` |
| V4 | Submission mode: default option (no `final`, no `preprint`) → anonymous, line numbers; no author names or identifying links; own prior work cited in third person | template | The delivered PDF is the anonymous submission build. Reproduction-code links inside the paper must be anonymous or omitted |
| V5 | Required sections (objective): abstract, introduction, related work, method, experiments, discussion & limitations, references. Abstract is one paragraph | `deliverable.md`, template | Section list is checkable from the PDF/LaTeX |
| V6 | PDF **and** LaTeX source delivered; LaTeX must build with the shipped files (`latexmk`) | `deliverable.md` | Source includes `.sty`, `checklist.tex`, bibliography, figure files |
| V7 | Code and reproduction notes: environment and dependency versions, data acquisition steps and data version (MMLU-Pro revision `b189ec765aa7ed75c8acfea42df31fdae71f97be`), random seeds, run commands and expected run time, **which script produces each table and figure**, compute actually used | `deliverable.md` | One reproduction document plus the code; per-table/figure script map must cover every numbered table and figure in the paper |
| V8 | Every number/table/figure from runs done in this task and regenerable by the shipped code; no placeholders, "illustrative" synthetic results passed as measured; failed/abandoned/unfinished work reported as such | `deliverable.md` | Checked by `internal-review-repo` against the map in V7 |
| V9 | Only real, actually consulted references | `deliverable.md`; Handbook (hallucinated citations violate the Code of Conduct) | Every bib entry must be traceable to a consulted source (see `idea-repo` Prior-work page for what was only read at abstract level) |
| V10 | Forbidden-material rule: no access to the published paper that studied this question or anything citing/discussing it; any accidental encounter is logged in the reproduction notes (what, where, how much read) | `deliverable.md` | Log section in the reproduction document, even if empty ("none encountered"); `idea-repo` keeps the single log |
| V11 | NeurIPS policy on agents/LLMs: use of LLMs as an important/original/non-standard component of the method (here: the LLM *is* the system under tuning and, if used, a proposer) must be described in the experimental setup; authors answer for all text, figures and references; LLMs cannot be authors | Handbook | Experimental setup states model, version, how it was run; the work was done by AI agents, which the reproduction notes should say plainly. Do not list an agent as an author |
| V12 | Societal impact / limitations are discussed within the page limit if in the main text; checklist items 2 (limitations) and 10 (broader impacts) must point to where | Handbook, checklist | `paper-repo` |

## 3. What could not be established / open

- **Camera-ready or "final" variant** is not requested; only the submission-format build is required. Page limit for camera-ready (10 pages) is therefore not used.
- Whether the official **checklist guidelines** change after 2026-11-04 cannot be known; the delivered `checklist.tex` must equal the one in `venue/neurips2026/` apart from filled answers (verified by the questions text, see the checker).
- The Handbook's own "Author Use of Agents and LLMs" paragraph says documentation is expected where the LLM is a method component; how much to say about the agents that ran this study is a judgement for `paper-repo` and `internal-review-repo`, not fixed by the venue.
- **No venue-fixed filenames** exist; filenames in the delivery come from `.forgejo/CODEOWNERS` of `paper-repo` (not yet present at the time of writing). `venue-artifacts.json` therefore is not yet declared (see issue #2 of this repo).

## 4. Files supplied here

- `venue/neurips2026/` — the three official template files, unmodified, with `SHA256SUMS`. `paper-repo` copies them into its delivery without change.
- `tools/check_venue.py` — checks a built paper directory against V1–V5 (hash of `.sty`, main-text page count from the PDF, checklist present with no TODO, required section headings, anonymity markers). Usage in its docstring. Working tool for reviewers; not a delivered path.

## 5. Rendering conventions for figures and tables (for `figtab-repo`)

From the template: text block 5.5 in wide × 9 in tall, 10 pt Times; a figure should be at most 5.5 in wide (full width) so it is not scaled; fonts in figures should stay legible at that size (≥ 7 pt after scaling). Figure number and caption **below** the figure, table number and title **above** the table; captions lower case except the first word and proper nouns; the caption states what is shown and its take-away. Colour is allowed, but the figure and its caption must stay legible in black/white print (use markers/line styles as well as colour). Tables: `booktabs` rules (loaded by the template), centered. Every figure/table that carries a claim needs its uncertainty (CI/bands, number of repetitions) in the figure or its caption (objective's rigor criterion). Vector PDF for plots is preferred.

## 6. Declared delivered paths (`venue-artifacts.json`)

Names from `story-repo`#3 / `paper-repo`#5 (CODEOWNERS proposal, takes effect when merged) and `paper-repo`'s skeleton; none invented here.

| Path | Why required | Owner (per proposal) |
|---|---|---|
| `paper.pdf` | PDF of the paper (V6) | paper-repo |
| `paper/main.tex`, `paper/neurips_2026.sty`, `paper/checklist.tex`, `paper/refs.bib` | LaTeX source, official style, checklist, bibliography (V1, V3, V6, V9) | paper-repo |
| `REPRODUCE.md` | environment, data revision, seeds, commands, run time, compute, table/figure → script map, forbidden-material log (V7, V10) | paper-repo |
| `code/` | code that regenerates every number (V7, V8) | experiment-repo |
| `figtab/` | table/figure scripts and the map to the paper's exhibits (V7) | figtab-repo |
| `paper/figures/` | the figures the paper includes | figtab-repo |

Not declared: `results/` (optional per `story-repo`), `paper/tables/` (a table may be typeset inline).
If `paper.pdf` is built only from `paper/main.pdf` by the build script, `paper-repo` must copy it to the root.
