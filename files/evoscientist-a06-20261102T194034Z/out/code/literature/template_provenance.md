# Official NeurIPS 2026 template provenance

Verified 2026-11-02. Scope: main-track author submission/formatting instructions only. No accepted-paper list, proceedings, scientific program, scientific search or conference-paper content was visited. No ICML fallback was needed: the official NeurIPS 2026 sources and download were available.

## Exact official URLs and retrieval chain

1. Official 2026 call for papers, directly visited:
   https://neurips.cc/Conferences/2026/CallForPapers
   - HTTP 200, no redirect.
   - Its “Paper template” link points directly to the ZIP in item 3.
   - Its “MainTrackHandbook” link points to item 2.
   - Local snapshots: `/work/literature/neurips2026_call.html` and `neurips2026_call.txt`.
2. Official 2026 main-track handbook, author sections read:
   https://neurips.cc/Conferences/2026/MainTrackHandbook
   - HTTP 200, no redirect.
   - Sections actually used: Authors → Paper Formatting Instructions, Double-blind Reviewing: For Authors, Paper Submission, and Paper Checklist. The page also contains other policies; those were not used to inspect scientific content.
   - Local snapshots: `/work/literature/neurips2026_handbook.html` and `neurips2026_handbook.txt`.
3. Official downloadable template, followed from the official CFP:
   https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
   - HTTP 200, `application/zip`, 20,259 bytes, no redirect.
   - Local archive: `/work/paper/Formatting_Instructions_For_NeurIPS_2026.zip`.
   - Contains exactly `neurips_2026.tex`, `checklist.tex`, `neurips_2026.sty`.
   - All three files were extracted without modification to `/work/paper/`.
   - Style declaration: `\ProvidesPackage{neurips_2026}[2026-01-29 NeurIPS 2026 submission/camera-ready style file]`.

No guessed standalone `.sty` URL was used: the official ZIP is the verified source of the style, example and checklist files.

## Main-text limit and submission rules

**Main-track submission: nine content pages**, including all figures and tables.

Evidence: handbook Authors → Paper Formatting Instructions states “The main text of a submitted paper is limited to nine content pages, including all figures and tables.” The official example source, `/work/paper/neurips_2026.tex`, lines 130–131, independently states a nine-page limit including figures and excludes additional pages containing acknowledgments, references, checklist and optional technical appendices.

- References, optional technical appendices and mandatory checklist do **not** count toward the nine content pages.
- The handbook explicitly allows **one additional content page after acceptance** for camera-ready papers: distinguish the ten-page camera-ready allowance from the nine-page submission limit.
- Submit a **single PDF**, maximum **50 MB**. Suggested order in the handbook: main content → references → appendices → checklist.
- Use the **2026** LaTeX style. Do not shrink margins/fonts or tweak the style to evade the limit.
- The example's default package option is the anonymous main track. For submission omit `final` and `preprint`; these are for camera-ready/preprint use, respectively.
- The handbook forbids acknowledgments at anonymous submission time. The example's statement that acknowledgment pages are outside the content count is not permission to include identifying acknowledgments in a submission.

## Mandatory checklist requirements

Source: official ZIP member `/work/paper/checklist.tex`, instruction block at lines 1–28, and handbook Authors → Paper Checklist.

- **Include the checklist or risk desk rejection.** The checklist source says: “The papers not including the checklist will be desk rejected.”
- The checklist is part of the submitted single PDF, **after references and after any optional supplemental/appendix text**. It does not count against the content-page limit.
- Answer every question using the provided `\answerYes{}`, `\answerNo{}` or `\answerNA{}` macros, replacing placeholders. Provide a **1–2 sentence justification even for NA**. Yes answers should point to supporting sections.
- Delete the instruction block when preparing an actual manuscript, but retain the heading, question/subsection structure and guidelines. Do not modify the questions.
- No/NA answers with proper justification are generally not, by themselves, grounds for rejection; omitting the checklist is different.
- Checklist answers are visible to reviewers and chairs; include the revised checklist with the final paper, where it will be published.
- For this planned statistical study, especially relevant existing checklist questions concern theory assumptions/proofs, experimental reproducibility, data splits/hyperparameter choice and statistical significance. The statistical-significance guidelines ask authors to state sources of variability, interval/error-bar methods, assumptions and the meaning of bars (SD versus SE, etc.). These are checklist requirements, not an endorsement of any particular selection-adjustment method.

The original downloaded example/checklist files remain intact, including their instructions and TODOs; no manuscript has been drafted or checklist answers fabricated.

## SHA-256 provenance

| Local file under `/work/paper/` | SHA-256 |
|---|---|
| `Formatting_Instructions_For_NeurIPS_2026.zip` | `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9` |
| `neurips_2026.sty` | `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a` |
| `neurips_2026.tex` | `cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797` |
| `checklist.tex` | `780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6` |

The same hashes, sizes and PDF hashes are in `/work/literature/source_manifest.json`. Retrieval status for the ZIP is in `template_retrieval_log.json`. These record the files available at verification time; conference instructions can subsequently change.
