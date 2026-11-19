# Venue source record

Retrieved 2026-11-03 UTC directly from official NeurIPS pages, without paper/topic searches. Raw page snapshots, extracted text and HTTP retrieval records are retained in venue-repo `sources/venue/`; this handoff contains the official original assets and enough provenance to check their origin. These are policy/template sources, not scientific evidence.

| ID | Official source | What was established |
| --- | --- | --- |
| S1 | https://neurips.cc/Conferences/2026/CallForPapers | Current 2026 main-track call, direct link to S3; main track is distinct from Evaluations & Datasets/Position tracks; analytical insights into existing methods are in scope. |
| S2 | https://neurips.cc/Conferences/2026/MainTrackHandbook | Paper Formatting Instructions: 9 content pages including figures/tables; references, appendices, mandatory checklist excluded; one PDF in main/references/appendices/checklist order; 50 MB; +1 content page only after acceptance. Code and Data Submission: optional separate ZIP ≤100 MB. Checklist/author-LLM/anonymity policies. |
| S3 | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | Official archive linked by S1. Three original files supplied under `neurips2026/`; style edition and detailed typography, figure/table, PDF/font rules, complete 16-item checklist. |
| S4 | https://neurips.cc/Conferences/FutureMeetings | 2026 Sydney; 2027 Europe and 2028 Western United States listed as future meetings. No later style package was supplied by this page. This supports a dated selection, not an exhaustive proof about all future URLs. |

Exact source excerpts:

- S2: “The main text of a submitted paper is limited to nine content pages, including all figures and tables. Additional pages containing references, optional technical appendices and mandatory paper checklist do not count as content pages.”
- S2: “If your submission is accepted, you will be allowed an additional content page for the camera-ready version. The maximum file size is 50MB.”
- S3 `neurips_2026.tex`: “Do not change any aspects of the formatting parameters in the style files.” “Please prepare submission files with paper size ‘US Letter’”. “The paper must be able to stand alone without the appendix”.
- S3 `checklist.tex`: “The checklist should follow the references and follow the (optional) supplemental material.” “Keep the checklist subsection headings, questions/answers and guidelines below.” “Do not modify the questions and only use the provided macros for your answers”.

## Integrity

| File/source | SHA-256 |
| --- | --- |
| S1 HTML | f71f07bd2555393fbee78b8e4f891872ccd572ac4946a91ffa0712d8fb3af41f |
| S2 HTML | 0d13b32386e23d7072c56e603bd6c19c5d913edeca7f0c5d2f5492dc88adfea1 |
| S3 ZIP, 20,259 bytes | 82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9 |
| S4 HTML | 23dc66458f01bdf79397907a0db9df6a4295c0e7e6bdb5e0e38a57ee280a376b |
| `neurips2026/neurips_2026.sty` | c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a |
| `neurips2026/neurips_2026.tex` | cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797 |
| `neurips2026/checklist.tex` | 780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6 |

Style identifies itself as `2026-01-29 NeurIPS 2026 submission/camera-ready style file` and says last revision January 2026. No style changes were made. The archive does not contain a separate license file or explicit license grant in these three files; we preserve source attribution and do not label them with an invented license. Distribution as the task's template support is not a declaration of ownership or publication acceptance.

Two guessed generic policy URLs returned HTTP 404 before the correct sources were followed from S1: `/Conferences/2026/PaperInformation/StyleFiles` and `/Conferences/2026/PaperInformation/PaperChecklist`. Their nonexistence is recorded in retrieval.json; no rule is inferred from them. Latest-edition evidence is the official current-year 2026 call and its linked archive, retrieved on the stated date, not the failed guesses.

## Frozen objective provenance

The objective is venue-repo #1. All five source files were read in full, verified against its frozen SHA-256 map, and requirements were reconciled with idea-repo wiki Brief revision `f0821bd899a9812e9bc047b850717807fe3b53d7`.

| `/initial-state/` path | SHA-256 |
| --- | --- |
| `inputs/0/TASK.md` | b0b006c8a36fa433a3892417fb274e0455e8658f2dc2a95310fc866e2cfc57de |
| `inputs/0/deliverable.md` | 834149d69338b8157120ef2c0c5287d1563f62996568d3b04e18a22a6b8a84c8 |
| `inputs/0/data.md` | b85e1505a8cf09c97b22a5381d25b5a125416ffdeddc12b3d91855e4cbdea1df |
| `inputs/0/resources.md` | 0372860f8a581344930e3396ada275adf19b858705b0ba4cb4d39e2905a793e2 |
| `inputs/0/starter_literature.md` | 9bc4464c972a35f9a8deffb1017162163d56ef58a1ec6f008fe78cf43a424c52 |

These files establish requirements and permitted starter literature, not that every listed article has been read by venue. Scientific citation validation belongs to the context owner and report integration. No independent claim of organization-wide restricted-source compliance can be made from this venue-only access record.
