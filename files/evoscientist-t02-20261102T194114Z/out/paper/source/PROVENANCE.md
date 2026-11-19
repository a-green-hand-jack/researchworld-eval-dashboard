# Official ICML 2026 LaTeX template provenance

## Selection and verification date

- Chosen conference/track: **ICML 2026, main research-paper track**.
- Verified online on **2026-11-02 UTC** (runtime date). Successful retrievals were at 19:52:53–19:52:58 UTC; exact timestamps and HTTP headers are in `SOURCE_METADATA.json`.
- This is the actual official archive currently linked from the official ICML 2026 Author Instructions, not a recreated template. All nine extracted files are byte-identical to their archive entries. No official source files were edited.
- **Latest verification:** verified the currently advertised ICML 2026 archive on the above date. A direct request to `https://icml.cc/Conferences/2027/AuthorInstructions` returned HTTP 404 at 2026-11-02T19:54:08 UTC (`LATEST_CHECK.json`). This does **not** prove that no newer ICML template exists elsewhere. No claim is made that this is chronologically newest across ICML, ICLR, and NeurIPS; those other conferences were not checked because ICML 2026 was the preferred choice. The version linked by the 2026 author page is verified; an absolute global “latest” claim cannot be verified from this restricted check.

## Official sources and exact version

[1] ICML 2026 Author Instructions:
https://icml.cc/Conferences/2026/AuthorInstructions

- HTTP 200; saved as `author-instructions.html`.
- The page links both [2] and [3]. No explicit page revision date or Last-Modified header was provided; the retrieval date is not a publication date.

[2] ICML 2026 official style archive:
https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip

- HTTP 200; saved unchanged as `icml2026.zip` (228,368 bytes).
- Exact style declaration: `\ProvidesPackage{icml2026}[2025/10/29 v2.0 ICML Conference Style File]`.
- Style header: `LaTeX style file for ICML-2026, version of 2025-10-29`.
- HTTP Last-Modified: **Thu, 13 Nov 2025 16:15:43 GMT**. This is server modification metadata, not an independently established release date.
- ZIP member timestamps: **2025-11-07 11:45:24**, with no timezone encoded. These are archive timestamps, not the style version date.
- SHA-256: `8b29290f5828e176debb57ea9cc00252502973d55ea561a2f18a7f0a326bfc6c`.

[3] ICML 2026 official formatting example PDF:
https://media.icml.cc/Conferences/ICML2026/Styles/example_paper.pdf

- HTTP 200; saved as `example_paper.official.pdf` (193,509 bytes).
- Byte-identical to the archive's `example_paper.pdf`.
- HTTP Last-Modified: **Wed, 12 Nov 2025 06:45:46 GMT**; not an independently established release date.
- SHA-256: `3e8fe0e952de8702ca4697dba09ca52e83bd649767b92a8340d34a591caa4d1b`.
- The example source is `example_paper.tex` inside [2]; its banner explicitly identifies ICML 2026. No separate example revision number is declared.

## Main-text limits and submission requirements

The current author instructions [1] govern where older example wording differs.

### Initial anonymous submission

- **At most 8 pages of main text.** An overlength main body is grounds for automatic rejection [1].
- References and appendices have unlimited pages and follow the main body in the **same PDF** [1].
- The required unnumbered **Impact Statement** belongs at the end of the paper, before References, and does not count toward the main-text page limit (`example_paper.tex`, Impact Statement section). It is mandatory for main-track papers [1, 2].
- **Maximum PDF size: 50 MB** [1].
- Double-blind: no identifying author details, acknowledgements, grant numbers, or non-anonymous repository links. Supplementary materials must also be anonymized [1].
- Use `\usepackage{icml2026}` for review. Preserve the official layout: US Letter, two columns, 10-point Times; do not shrink margins, fonts, or vertical spacing to evade the limit [1, 2].
- Abstract: one paragraph, ideally 4–6 sentences. Figure captions below figures; table captions above tables. Retain `\printAffiliationsAndNotice{}` even when its argument is empty [1, 2].

### Camera-ready version (different limit)

- **At most 9 pages of main text**, followed by acknowledgements, the main-track Impact Statement, references, and appendices [1]. This is not the initial-submission allowance.
- **Maximum PDF size: 20 MB** [1].
- Use `\usepackage[accepted]{icml2026}` and restore correct author/affiliation information [1].
- If applicable, disclose financial or other substantive conflicts in a paragraph titled **Conflict of Interest Disclosure**, as the last paragraph of the introduction. The current instructions say to omit it when there are no financial conflicts to disclose [1].
- Run the official camera-ready format checker at https://papercheck.icml.cc/papercheck.html and enter its successful five-letter code in the camera-ready form [1]. This URL is transcribed from [1]; it was not visited and no document was uploaded.
- Other author-page obligations include publishing/release forms, registration/presentation requirements, and a lay summary in the submission form. These are not additional LaTeX content sections [1].

### Checklist status and source discrepancies

- **No separate NeurIPS-style paper checklist is specified in the retrieved ICML 2026 author instructions or example source.** Neither contains a “checklist” instruction. This is scoped to the inspected sources, not a claim about every field in a logged-in submission form.
- The mandatory main-track Impact Statement and camera-ready formatting/COI checks above still apply.
- The example has older **10 MB** wording. The current author page explicitly specifies **50 MB submission / 20 MB camera-ready**; use those current limits.
- The example also contains older Type-1-only font language. The current author page explicitly says **there is no Type 3 font check this year** in its camera-ready guidance. Keep readable, properly embedded fonts; do not describe that obsolete example sentence as the current checker requirement.
- Official files are preserved verbatim despite these discrepancies.

## Local artifact inventory

All paths below are under `/work/template/`:

- `icml2026.zip`: unchanged official download.
- `icml2026.sty`, `icml2026.bst`: official LaTeX and BibTeX styles.
- `example_paper.tex`, `example_paper.bib`, `example_paper.pdf`: official example sources and PDF.
- `algorithm.sty`, `algorithmic.sty`, `fancyhdr.sty`, `icml_numpapers.pdf`: remaining official archive contents. Keep the supplied local `fancyhdr.sty` with the template.
- `example_paper.official.pdf`: separately downloaded official example, identical to the archived PDF.
- `author-instructions.html`, `SOURCE_METADATA.json`, `LATEST_CHECK.json`: source snapshot and retrieval evidence.
- `SHA256SUMS`: checksums for official downloaded/extracted files.
- `COMPILATION_CHECK.json`: tools, active direct package checks, and compilation result.
- `build/example_paper.pdf`: locally compiled example (distinct from the official supplied PDF).
- `build/compile-console.log`, `build/example_paper.log`: local build diagnostics.

## Brief local compilation verification

- **PASS**, 2026-11-02: unchanged official `example_paper.tex` compiled with `latexmk` + pdfLaTeX + BibTeX, exit code **0**. Output: **7 pages, 193,497 bytes**. The example's own length does not alter the 8-page submission allowance.
- Engine: `pdfTeX 3.141592653-2.6-1.40.26 (TeX Live 2025/dev/Debian)`.
- Bibliography processor: `BibTeX 0.99d (TeX Live 2025/dev/Debian)`.
- Available: `pdflatex`, `latexmk`, `bibtex`, `lualatex`, `kpsewhich`. All active direct packages checked are installed or bundled; successful compilation also exercises required transitive dependencies.
- Not available on PATH: `xelatex`, `tectonic`, `pdfinfo`, `pdffonts`. None is necessary for the tested pdfLaTeX build. No separate font-inspection test or official online format-checker certification was performed.

Rebuild the unchanged example:

```sh
cd /work/template
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error -outdir=build example_paper.tex
```

For later manuscript work, copy the official example source and retain its accompanying styles, bibliography style, and any referenced assets. Keep review mode for an anonymous submission; switch to `[accepted]` only for a camera-ready version. Do not count a successful build as proof of page-limit or anonymity compliance.

## Access boundary

Only official ICML author-instruction URLs and official formatting/style artifacts were fetched. No external links in the instructions were followed. No accepted-paper lists, proceedings, hidden manuscript, workspace literature, topic searches, or topic-discussion pages were accessed. The only document compiled was the unchanged official formatting example; no paper was drafted.
