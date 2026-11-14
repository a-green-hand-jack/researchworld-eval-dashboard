# Venue decision: NeurIPS 2026 main track

Verified 2026-11-02 against the official 2026 call, Main Track Handbook and formatting ZIP linked by the call. The official navigation identifies 2026 as its current edition. This satisfies the objective's choice among ICML/ICLR/NeurIPS using the latest published official edition available in these sources at retrieval. No external submission, author identity, acceptance or 2027 template is asserted.

## Binding format rules

| Item | Verified rule | Official source / locator |
| --- | --- | --- |
| Main text | At most **nine content pages**, including all figures and tables. | Handbook, Authors → Paper Formatting Instructions; official shell lines 129–131. |
| Exclusions | Acknowledgments, references, checklist and optional technical appendices are excluded. The nine-page cap applies to the complete substantive main paper. | Official shell lines 130–131; handbook formatting section. |
| Layout | Use unmodified `neurips_2026.sty`; 10-point type, 11-point leading, 5.5 × 9 inch text rectangle, Times preferred; preserve margins, numbering and heading sizes. | Official shell General formatting instructions / Final instructions. |
| Mode | Default or `[main]` produces anonymous main-track review format with line numbers. `[preprint]` is allowed for a non-anonymous public preprint; `[final]` is for accepted papers only. **Use default for this reviewed delivery**; no acceptance is established. | Official shell preamble and Style subsection; handbook Preprints. |
| PDF | A single PDF contains the paper, references, optional appendices, then completed checklist; maximum conference submission PDF size 50 MB. | Handbook Paper Formatting Instructions. |
| Appendix | No page cap; append to the same PDF. Critical evidence for main claims belongs in the main text, which must stand alone. | Official shell Technical appendices and supplementary material. |
| Checklist | Mandatory, excluded from page count, after references and optional appendix. Official 2026 checklist contains **16** questions. Retain questions, headings, answer fields and guideline blocks; remove only its introductory instruction block in the completed manuscript copy. | Official `checklist.tex`, introductory instructions. |
| Checklist answers | Use `\answerYes{}`, `\answerNo{}` or `\answerNA{}`; give a short 1–2 sentence justification for every answer and point to evidence for Yes answers. No/TODO/NA must not masquerade as compliance. | Official checklist introductory instructions. |
| Supplementary code | Conference format allows one anonymized ZIP up to 100 MB. The task additionally requires all code and reproduction instructions and forbids raw data in the repository/submission. Fetch public raw data during reproduction instead. | Handbook Code and Data Submission; frozen deliverable.md / data.md. |
| Citations | Consistent author-year or numeric citations; no requirement to invent a bibliography style. Cite only real consulted sources, per objective. | Official shell Citations; frozen deliverable.md. |
| Author/funding details | Default review format is anonymous; omit acknowledgments in submission mode. Do not invent author affiliations, funding, competing interests or approvals. | Handbook Double-blind Reviewing; official shell Acknowledgments. |
| LLM assistance | Venue requires description when agents/LLMs importantly enter the method; **the frozen objective requires disclosure if any LLM assistance is used**, including this organization. | Handbook Author Use of Agents and LLMs; frozen resources.md. |

The handbook allows an extra content page only after conference acceptance. That permission does not apply to this task: use the nine-page submission cap. The current call's deadlines and OpenReview administration are facts about an external submission process, not requirements to submit this study externally.

## Figures and tables

Official shell Figures/Tables: figures and tables must be clear and legible at rendered size, numbered consecutively and explained in captions including the takeaway. Put figure captions below and table titles/captions above. Tables should have no vertical rules (booktabs recommended). Color is permitted; preserve legibility in grayscale. Main-paper figures/tables count in the nine-page cap.

For uncertainty, the official checklist requires that variation sources, interval/error-bar meaning (SD, SE, CI), calculation, and assumptions be explained. Plot/table script mapping and actual-run provenance are additional objective requirements. These are evidence requirements, not permission to treat a perturbation-replicate range as sampling uncertainty.

## Build integration

The three files under `templates/neurips2026/` are unmodified files extracted from the official ZIP. The shell and checklist are reference templates, **not the study's completed paper or completed checklist**. Keep originals intact for provenance; copy the checklist into the report owner's source path, remove its introductory instruction block as instructed, and fill all 16 answers with evidence. The shell's demonstration figure, table, author names and bibliography must never be presented as study material.

In paper-repo, set `TEXINPUTS=venue/templates/neurips2026//:` in the build so `\usepackage{neurips_2026}` resolves to the official style without copying or modifying it. The trailing colon preserves default TeX search paths. Input the completed manuscript checklist, not the unfilled reference file. Build twice (or latexmk) so cross-references resolve. Check the **rendered** content/reference boundary to establish the nine-page cap; total PDF pages alone cannot do this.

## What remains to verify on the final paper

This rule record does not establish the final paper's page count, legibility, bibliography correctness, completed checklist truth, source build success or experimental reproducibility. Paper and independent review must inspect the built delivery. Require no remaining answer/justification TODOs in the actual manuscript checklist; the preserved official reference template intentionally contains them. Do not claim ethical approval, asset licenses, legal compliance, completed experiments or LLM-free work without evidence.

## Official evidence

URLs, retrieval times, content hashes and the unsuccessful guessed style-page URL are recorded in `sources/retrieval.json`. Successful official sources:

- https://neurips.cc/Conferences/2026/CallForPapers
- https://neurips.cc/Conferences/2026/MainTrackHandbook
- https://neurips.cc/public/guides/PaperChecklist
- https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip

`templates/neurips2026/SHA256SUMS` identifies the extracted files. No license for the study, its code, or its data is granted by this document. Official source files are preserved as supplied for the requested template use; other asset terms must be verified separately.
