# Official NeurIPS 2026 template and main-track rules

Verified by direct official-source downloads on **2026-11-04 UTC**. This is the **2026** template, not a silently substituted 2025 template. The style declares `2026-01-29 NeurIPS 2026 submission/camera-ready style file`, the 40th conference and year 2026. These are formatting resources; availability does not mean the submission window is still open.

## Concrete paths

- **Template entry point:** `/work/paper/neurips2026/neurips_2026.tex`
- **Official style file:** `/work/paper/neurips2026/neurips_2026.sty`
- **Official checklist:** `/work/paper/neurips2026/checklist.tex`
- **Unmodified original ZIP:** `/work/paper/Formatting_Instructions_For_NeurIPS_2026.zip`
- Official CFP snapshot: `/work/paper/neurips2026_call_for_papers.html` (readable `.txt` alongside it).
- Official full handbook snapshot: `/work/paper/neurips2026_main_track_handbook.html` (readable `.txt` alongside it).
- Access status, source/archive hashes: `/work/literature/access_log.md`.

The archive contains exactly the three `.tex`/`.sty` files above; it does not contain a precompiled template PDF. Extraction was checked for workspace path traversal. All three extracted files are byte-for-byte copies of their archive members. No manuscript was drafted, checklist answers completed, experimental code implemented, or compilation attempted. The sample template still contains official example content/TODOs: it is a shell, not a submission-ready paper.

## Sources and provenance

1. **NeurIPS 2026 Call for Papers:** https://neurips.cc/Conferences/2026/CallForPapers
2. **NeurIPS 2026 Main Track Handbook:** https://neurips.cc/Conferences/2026/MainTrackHandbook
3. **Official formatting archive, directly linked by the CFP:** https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip

The initially attempted official `/Conferences/2026/PaperInformation/StyleFiles` endpoint returned HTTP 404. The CFP successfully supplied the current archive URL, downloaded with HTTP 200. No redirect was followed and no unofficial mirror used. See `sources.md` [6]–[8].

## Page limit and submission format — main track

The handbook's **Paper Formatting Instructions** state:

> “The main text of a submitted paper is limited to nine content pages, including all figures and tables.”

It then excludes additional pages containing references, optional technical appendices and the mandatory paper checklist, and allows an additional content page for accepted camera-ready papers. The template's Style subsection independently says **nine pages including figures**.

- **Initial submission: 9 content pages**, including figures and tables.
- **Accepted camera-ready: 10 content pages** (one extra).
- **Excluded from the content-page count:** references, optional technical appendices, mandatory checklist. The template also exempts acknowledgments, but the handbook explicitly prohibits acknowledgments **at anonymous submission time**; do not add them to an initial submission.
- Technical appendices have no page limit in the template, but are optional reviewer reading. Main claims must be supported by a self-contained main paper, not critical experiments hidden only in the appendix.
- Combine **main text, references, optional technical appendices, checklist** into **one PDF**. Do not submit a separate appendix PDF. The official template places the checklist last, after references and optional appendix.
- Main PDF maximum size: **50 MB**. Optional separate code/data supplementary material: one anonymized ZIP up to **100 MB** (handbook).
- Use this year's LaTeX style. Do not reduce margins, font sizes or otherwise tweak the style to squeeze pages. Word/RTF templates are not supported.
- Submission must be double-blind, including linked/supplementary material. Remove identifying acknowledgments and ensure anonymous external browsing.

These are **main-track** rules. The template supports several tracks, but the CFP warns that tracks have different calls, portals and possibly timelines; do not transfer these rules to another track without its official verification. The downloaded CFP lists the 2026 full-submission deadline as May 6, 2026 AoE; that is already past as of this acquisition date.

## Style options

- Anonymous main-track submission: `\usepackage{neurips_2026}` (official default), or explicitly `\usepackage[main]{neurips_2026}`.
- Do **not** use `final` or `preprint` options for an anonymous submission. The submission style adds line numbers; do not cite those line numbers in the manuscript.
- Accepted camera-ready main track: `\usepackage[main,final]{neurips_2026}`.
- Public non-anonymous preprint: `\usepackage[preprint]{neurips_2026}`. Do not present an unaccepted paper as a NeurIPS publication or identify it as under review there in the public version.

## Mandatory checklist and research reporting

The official `checklist.tex` is included by `\input{checklist.tex}` at the end of the template. It explicitly warns that **missing checklists cause desk rejection**. It is outside the page limit.

When preparing a real paper:

- Preserve the checklist heading, questions and guidelines. Delete its instructional block only as directed.
- Replace each TODO with `\answerYes{}`, `\answerNo{}` or `\answerNA{}` and a **1–2 sentence justification**, including a location of supporting evidence when applicable.
- Do not fabricate affirmative answers. A justified No/NA is generally acceptable; omitting the checklist is not.

The 2026 checklist has **16 topics**: claims; limitations; theory assumptions/proofs; reproducibility; open code/data; experimental settings; statistical significance; compute resources; ethics; broader impacts; safeguards; existing-asset licenses; new-asset documentation; human-subject methods/compensation; IRB/equivalent approvals; and **declaration of LLM usage**.

For planning these experiments, the directly relevant requirements are explicit train/validation/calibration/test separation; hyperparameter/selection details; correctly defined error bars; worker type, memory/time and total compute including unreported preliminary runs; versioned assets and licensing; and honest limitations. Code release is encouraged but the handbook/checklist recognize other reasonable reproduction avenues; do not claim every paper must release all code.

The handbook and checklist require disclosure when LLMs/agents are important, original or non-standard components of the **core methodology**. Ordinary writing/editing/formatting assistance alone does not require that declaration. Authors remain responsible for correctness, originality and verified citations; agents/LLMs cannot be authors.

## Verification limits

Official archive contents and the relevant handbook/template/checklist text were inspected; this was not a comprehensive legal/ethics audit of every linked policy. No external policy links or unofficial explainers were followed. The style/template have not been compiled or tested in a LaTeX environment, and checklist answers have intentionally been left untouched.
