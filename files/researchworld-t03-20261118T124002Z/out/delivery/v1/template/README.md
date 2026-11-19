ICML 2027 official style kit (from `ht-role venue icml --template`, kit updated 2026-11-10, retrieved 2026-11-14): `icml2027.sty`, `icml2027.bst`, `fancyhdr.sty`, `example_paper.tex/.bib/.pdf`, `icml_numpapers.pdf`. ICML has no paper-checklist file. Requirements: wiki page `Venue` of world/venue-repo and `venue.md` there.

Offline check (example_paper.tex compiles to 7 pages, US Letter, Type 1 fonts only):
`TEXINPUTS=../template//: BSTINPUTS=../template//: latexmk -pdf example_paper.tex`
(bibtex finds `icml2027.bst` through BSTINPUTS; `algorithm`/`algorithmic` are TeX Live's own packages, the kit's copies are unlicensed and not included.)
Do not edit these files. Submission mode = `\usepackage{icml2027}` with no `accepted` option.
