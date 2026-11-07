# Build the LaTeX source archive

Unzip `paper_source.zip`, enter its `paper/` directory, and run:

```bash
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

A standard TeX Live installation with the packages in `main.tex` is needed. The official `neurips_2026.sty` is bundled unchanged. The actual manuscript is **main.tex**, not the unchanged formatting-example `neurips_2026.tex`. Quantitative tables, numeric macros and figure inputs are included, so compiling this archive does not require Python or redownloading data.

For full numerical regeneration, use `code_and_results.zip` and its root README. Its tested builder is `python src/build_paper.py`; GNU make is not required. The supplied Makefile is optional.

The final manuscript has8content pages (official initial-submission limit9), one references page, technical appendices and the completed16-question checklist,25pages total. This is a research artifact, not a claim of acceptance or an open2026submission window. Official template provenance and byte hashes are documented in the main artifact's literature/template_rules.md.
