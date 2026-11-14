# Building and checking the manuscript

Run from the delivery root with Python 3, TeX Live, latexmk, BibTeX, and the official venue assets installed:

```sh
python3 manuscript/build.py
```

The build uses `manuscript/main.tex`, the authored section/bibliography/checklist inputs it includes, and the official `venue/neurips2026/neurips_2026.sty`. It runs latexmk from the delivery root, retains diagnostics in `manuscript/.build/`, rejects unresolved references/citations, and copies the successful output to root `paper.pdf`. Missing source or template inputs are errors. The build does not generate or substitute empirical results. Rebuild after integrating any source, evidence, figure/table, or venue change.

```sh
python3 manuscript/build.py --clean
```

This removes only generated files in `manuscript/.build/`; the root PDF remains the last delivered build until replaced by a successful rebuild.

Before delivery, inspect every PDF page, all figures and tables at included size, citation and hyperlink destinations, and the text extracted by `pdftotext -layout paper.pdf`. Check unresolved and overfull-box warnings in the log. Confirm that main content fits nine pages under the official NeurIPS 2026 review style and that references, technical appendices, and the completed checklist follow in that order. Venue policy/provenance is supplied in `venue/`; analysis and presentation owners supply the experiment and artifact-generation commands. A successful TeX build alone does not establish scientific or format completeness.
