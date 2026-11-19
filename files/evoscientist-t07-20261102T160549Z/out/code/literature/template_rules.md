# Official template provenance and rules

Verified 2026-11-02 UTC. Selected venue: **NeurIPS 2026 Main Track**. This is the current-year archive linked by the official 2026 CFP, not a prior-year substitute. No claim is made that this is the newest template across every other allowed conference; ICLR 2027 and ICML 2026 were not checked. The NeurIPS 2026 submission deadline has already passed; using its style does not imply submissions remain open.

## Direct official provenance

1. CFP, HTTP 200: https://neurips.cc/Conferences/2026/CallForPapers
   - Its “Paper template” link points directly to the archive below.
2. Official archive, HTTP 200: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
3. Main Track Handbook, HTTP 200, displayed version V2026.3: https://neurips.cc/Conferences/2026/MainTrackHandbook
4. Failed initial known-pattern URL, HTTP 404: https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles
   - This failure was resolved using the official CFP's actual archive link; it is not the provenance of the downloaded style.

No search engine, account API, OpenReview submission page, blog, external bibliography link, or unrelated site was opened. All downloaded conference material came from neurips.cc or media.neurips.cc.

## Files downloaded unchanged

- `/work/paper/Formatting_Instructions_For_NeurIPS_2026.zip`
- `/work/paper/neurips_2026.sty`
- `/work/paper/neurips_2026.tex`
- `/work/paper/checklist.tex`

Archive SHA-256: `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`

Style SHA-256: `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a`

No manuscript was written and the template was not compiled. The archive contains the three files listed above, not a compiled formatting PDF. Archive/style hashes and file sizes are in `/work/literature/file_manifest.json`.

## Page limits and packaging

The handbook's “Paper Formatting Instructions” and archive's `neurips_2026.tex`, section 1.1, agree:

- Initial submission: **9 content pages**, including figures and tables.
- References, optional technical appendices, and mandatory checklist are outside the content-page limit. The template also excludes acknowledgments, but acknowledgments must be absent from anonymous submissions.
- Accepted camera-ready: **one additional content page**, hence **10**, according to the handbook. Do not confuse that with the template's initial 9-page instruction.
- Main content, references, appendices, and checklist belong in **one PDF**, suggested order exactly as listed. No separate appendix PDF; appendices have no page limit, but reviewers need not read them and main claims must stand alone.
- Main PDF maximum **50 MB**; supplementary code/data ZIP maximum **100 MB** (handbook).
- Use **US Letter**, not A4; preserve style-defined margins, font sizes and dimensions; use embedded supported fonts.
- Use the 2026 LaTeX style. Formatting modifications or page-limit violations risk desk rejection.
- `\usepackage{neurips_2026}` defaults to the anonymous Main Track. Do not use `final` or `preprint` for initial submission. `final` is for accepted papers; `preprint` for non-anonymous preprints. Other track switches in the archive do not establish those tracks' submission rules.

Short evidence spans (all <=80 characters):
- Handbook: “limited to nine content pages”
- Handbook: “allowed an additional content page”
- Handbook: “The maximum file size is 50MB.”
- Template: “There is no page limit for the technical appendices.”

## Mandatory checklist

Source: `checklist.tex` inside the official archive; handbook “Paper Checklist”.

- Must be included; the archive explicitly says missing checklists cause desk rejection.
- Place it **after references and optional supplemental appendices** in the single PDF; it does **not** count toward the content-page limit.
- Delete the instruction block, retain heading, subsection headings, questions, and guidelines.
- Use the provided `\answerYes{}`, `\answerNo{}`, or `\answerNA{}` macros and a **1–2 sentence justification for every answer**, including NA. Replace TODO placeholders.
- Yes justifications should identify supporting sections. A justified No/NA is generally acceptable; do not misrepresent unavailable evidence as Yes.
- Checklist answers are reviewed, revised for final publication, and published with accepted papers.
- The downloaded checklist contains **16 questions**: claims; limitations; theory assumptions/proofs; experimental reproducibility; open data/code; experimental settings; statistical significance; compute; ethics; broader impacts; safeguards; asset licenses; new assets; human subjects; IRB; declaration of methodologically important LLM use.
- Writing/editing/formatting-only LLM use does not require the methodological LLM declaration under this checklist. Authors remain responsible for all content and citations.

Short evidence spans:
- “The papers not including the checklist will be desk rejected.”
- “The checklist does NOT count towards the page” [continues on next line]
- “Please provide a short (1--2 sentence) justification”

## Anonymity and research reporting

Handbook: anonymize the paper, supplement and external artifacts; no acknowledgments at submission. Provide sufficient reproducibility information, report limitations and negative impacts honestly, and do not fabricate citations. Main-track rules here must not be transferred automatically to E&D or other tracks. CFP says tracks have distinct calls and may have distinct timelines.

## Access and incidental-exposure disclosure

The only conference access failure was the 404 above. Official template and rule access succeeded. While inspecting the allowed official `.tex` file, its **sample bibliography boilerplate was displayed incidentally**; while inspecting the allowed handbook, its **Further reading link labels were displayed incidentally**. No sample-cited or further-reading document/link was opened, traversed, or used as a research source. No attempt was made to identify the user's unidentified excluded paper. These incidental displays are reported rather than claiming that no unallowlisted work title could have appeared anywhere.
