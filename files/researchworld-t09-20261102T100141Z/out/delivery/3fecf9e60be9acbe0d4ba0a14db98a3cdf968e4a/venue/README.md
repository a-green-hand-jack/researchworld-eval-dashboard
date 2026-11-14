# venue/ — NeurIPS 2026 main track (owner: venue-repo)

Chosen venue: **NeurIPS 2026, main track** (reasons and unverifiable alternatives: `VENUE.md`). Template provenance: `SOURCE.md`.

| File | What |
|---|---|
| `neurips_2026.sty` | official style file, unmodified (sha256 of the zip in `SOURCE.md`) |
| `neurips_2026_example.tex` | official example/instructions paper (the zip's `neurips_2026.tex`), for reference only |
| `checklist.tex` | official **blank** paper checklist; do not edit questions/guidelines |
| `VENUE.md` | the verifiable format requirements V1–V9 and repro requirements D1–D5 |
| `check_format.py` | `python3 venue/check_format.py paper.pdf paper/main.tex` checks page limit, checklist, TODOs, style options |

## Rules in short
- `\usepackage{neurips_2026}` — no `final`, no `preprint` (anonymous, line numbers on). Do not change margins or fonts.
  Text width is 5.5in (single column, 10pt Times); figures should be sized to `\linewidth` or `0.48\linewidth`.
- Main text <= **9 pages** incl. figures and tables. References, acknowledgments (`ack` environment; hidden in anonymous mode),
  appendices and checklist do not count. No page limit on appendices.
- Order: main text, References, appendices, then `\input{checklist}` (the checklist must be last).
- The checklist: copy `venue/checklist.tex` to `paper/checklist.tex`, delete the `%%% BEGIN INSTRUCTIONS ... END INSTRUCTIONS %%%` block (keep the heading
  "NeurIPS Paper Checklist"), keep all questions and guideline lists, answer each with `\answerYes{}`/`\answerNo{}`/`\answerNA{}` and a 1–2 sentence
  justification that points to sections. No `\answerTODO`/`\justificationTODO` may remain.
- Anonymity: no names, no acknowledgments text, no public repo links; say the code is in the supplementary material.
- Required sections: abstract, introduction, related work, method, experiments, discussion and limitations, references.

## Build
`paper-repo` builds `paper/` with the style found in `venue/`:
```
cd paper && TEXINPUTS=../venue: BIBINPUTS=.: latexmk -pdf main.tex   # TeX Live (pdflatex + bibtex) is in the sandbox
cd .. && python3 venue/check_format.py paper.pdf paper/main.tex
```
(`neurips_2026.sty` loads natbib; use `\bibliographystyle{plainnat}` or similar.) `checklist.tex` is `\input` from `paper/` after it is copied there.
