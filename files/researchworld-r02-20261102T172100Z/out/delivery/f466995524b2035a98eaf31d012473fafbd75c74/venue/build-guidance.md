# Building and checking the paper

The paper owner controls `manuscript/` and the root `paper.pdf`. Use the unmodified style at `venue/official/neurips2026/neurips_2026.sty`; expose that directory through TeX's search path and load it by its official basename:

```latex
\documentclass{article}
\usepackage[main]{neurips_2026}
```

For example, from the delivery repository root (adjust build output handling in the paper-owned build instructions):

```bash
TEXINPUTS="$PWD/venue/official/neurips2026//:" latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=manuscript manuscript/main.tex
cp manuscript/main.pdf paper.pdf
```

The trailing colon preserves TeX's standard search paths. Paper-repo must test its actual bibliography, paths and package choices in the final build; this is an integration example, not a claim that an unwritten paper compiles. If using `latexmk -cd`, adapt all relative figure, bibliography and input paths consistently.

**Do not accidentally input the blank upstream checklist.** Create the final filled copy in `manuscript/` and input it explicitly (e.g. `\input{manuscript/checklist.tex}` when compiling from the repository root), after references and optional appendix. An unqualified `\input{checklist.tex}` can resolve to the blank official form through TEXINPUTS. The final copy must keep the original 16 questions and guidelines, delete the initial instruction block, and replace all answer/justification TODOs. The original in `venue/official/` remains byte-for-byte upstream for provenance.

Use the main submission format and 9-page content limit. Neither `final` nor invented acceptance/funding/affiliation information is appropriate. All reference/appendix/checklist pages are in the same PDF; local recommendation is a fresh page before references so the main-content page count is unmistakable. Extra appendices must not substitute for main-text evidence.

Checks against the actual built delivery:

```bash
pdfinfo paper.pdf
pdffonts paper.pdf
pdftotext -layout paper.pdf manuscript/rendered-text.txt
python3 venue/scripts/verify_sources.py
```

Inspect PDF metadata for US Letter (612 × 792 PDF points) and size ≤50 MB; inspect fonts for Type 1 or embedded TrueType and absence of Type 3/nonembedded TrueType. Check main-text end page manually, since total PDF pages legitimately exceed nine. Inspect visual layout, figure/table text and captions, overflow, bibliography and all 16 completed checklist answers; do not rely only on a TODO grep because the archived official form intentionally contains TODOs. Compare the loaded style's SHA-256 against the source manifest. Confirm all scientific numbers/figures/tables trace to actual runs and every reproduction/provenance requirement in requirements.md is covered.

A small geometry probe was compiled independently of the research manuscript; see `validation/template-probe.txt`. This checks the selected style's loadability and dimensions, not the future paper's scientific or layout compliance.
