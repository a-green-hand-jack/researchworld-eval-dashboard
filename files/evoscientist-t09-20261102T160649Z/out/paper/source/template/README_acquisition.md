# Official NeurIPS 2026 template acquisition

Acquisition date: 2026-11-02 UTC. This directory contains source/template acquisition only, not a paper draft.

## Original archive and provenance

- Exact original ZIP: `/work/paper/template/Formatting_Instructions_For_NeurIPS_2026.zip`
- URL: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip
- SHA-256: `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9`
- Direct link verified on the official 2026 Call for Papers: https://neurips.cc/Conferences/2026/CallForPapers
- Policy evidence: https://neurips.cc/Conferences/2026/MainTrackHandbook
- The requested `/Conferences/2026/PaperInformation/StyleFiles` route returned HTTP 404, as did `/Conferences/2026/PaperInformation` and the probed 2025 StyleFiles fallback. The 2026 archive itself was available via the CFP. Its link was **not** verified on the unavailable StyleFiles page. This distinction matters if the user's permitted link provenance is interpreted as StyleFiles-only.

Original successful HTML responses are preserved here. Derived `.txt` files are local extractions, not separate network sources. `/work/artifacts/access_log.md` records every request and hashes.

## Exact extracted files

`/work/paper/template/official_2026/` contains only:

| File | Bytes | SHA-256 |
|---|---:|---|
| `neurips_2026.tex` | 19,118 | `cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797` |
| `checklist.tex` | 26,167 | `780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6` |
| `neurips_2026.sty` | 13,704 | `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a` |

ZIP CRC validation passed. Each extracted file was byte-compared to its original archive member. The style header identifies `neurips_2026`, dated 2026-01-29. No member was edited. The archive does not include a precompiled PDF; none was generated here. `template_manifest.json` is locally generated integrity metadata, not an official conference file.

## Later use (instructions only; not executed)

1. Make a separate working copy of all three files, keeping these originals intact. Do not work directly in `official_2026/`.
2. For an anonymous main-track submission keep `\documentclass{article}` and default `\usepackage{neurips_2026}` or `[main]`. Do **not** set `final` or `preprint` for review; do not alter style files, margins, fonts, or spacing.
3. Replace placeholder paper content in that working copy. Keep `\input{checklist.tex}` after references and optional appendices. In the working checklist, remove the initial instruction block as instructed, but retain its heading, question/answer sections, and guidelines. Replace TODO macros using `\answerYes{}`, `\answerNo{}`, or `\answerNA{}` and give 1–2 sentence justifications; do not prefill unsupported answers.
4. From the working-copy directory, a conventional command is `pdflatex -interaction=nonstopmode -halt-on-error neurips_2026.tex` (repeat for references). Compilation and dependency sufficiency have **not** been tested here; do not treat this command as a verified build recipe.
5. Submission: maximum **nine content pages**, including figures/tables; references, technical appendices, and checklist are excluded. Use a single PDF containing content, references, optional appendices, and the mandatory checklist. The handbook permits one extra content page in an accepted camera-ready paper. It gives a 50 MB PDF limit.
6. The checklist is mandatory; its official instructions warn of desk rejection if omitted. It must also appear in the final paper. Do not include identifying acknowledgments in the anonymous submission. For accepted main-track papers the mode is `[main,final]`; `[preprint]` is a different, nonanonymous public-preprint mode.

No experiment code, manuscript draft, or official template member was modified, and no package registry or template mirror was accessed.
