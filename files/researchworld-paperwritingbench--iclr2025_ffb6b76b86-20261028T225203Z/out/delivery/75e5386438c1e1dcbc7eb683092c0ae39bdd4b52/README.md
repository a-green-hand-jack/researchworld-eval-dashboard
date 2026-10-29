# paper-repo

ResearchWorld role: paper-repo (venue + report). The repository root is the delivered tree (caller workspace `/work`).

- `template.tex` — the paper (ICLR 2025 template, filled in); `references.bib` — its bibliography; `template.pdf` — the compiled paper.
- `iclr2025_conference.sty/.bst`, `math_commands.tex`, `fancyhdr.sty`, `natbib.sty`, `figures/figure_{1..6}.png` — byte-identical copies of the frozen inputs (`/initial-state/inputs/{1,2,4,5,6,7}`), present only so the tree compiles.

Build: `latexmk -pdf template.tex` (pdflatex + bibtex). Sources: every number in the paper comes from the experimental log in the `Research objective` issue (#1); every bibliography entry was checked against arXiv / Crossref / OpenAlex metadata.
