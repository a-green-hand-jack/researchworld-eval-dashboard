# Integrating the official template in the delivery root

Story-repo assigned `venue/` to venue and `paper.tex`, `paper.pdf`, `sections/`, `references.bib`, `Makefile` and root `README.md` to paper in world/story-repo#7, with ownership proposed in paper PR #5. This directory is venue's complete handoff; paper owns its manuscript and build.

From the paper repository root, the build can discover the unchanged official files without moving them:

```sh
export TEXINPUTS="$PWD/venue/official/iclr2027//:"
export BSTINPUTS="$PWD/venue/official/iclr2027//:"
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
```

The trailing colon retains default TeX search paths. Use the equivalent `export` statements in `Makefile` if desired. Do not use a package that resets margins, type size or column structure. The minimal preamble is:

```tex
\documentclass{article}
\usepackage{iclr2027_conference,times}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{url}
% Keep \iclrfinalcopy disabled for anonymous submission format.
```

The package loads natbib. Use `\bibliography{references}` and `\bibliographystyle{iclr2027_conference}`, then `\appendix` and appendix content. `math_commands.tex` is optional; it is preserved as part of the official archive, not imposed on the study. The sample `.bib` belongs only to the formatting example and must not replace consulted study references.

After the <=9-page main text, include the actual AI use statement (mandatory; <=1 page); recommended ethics and reproducibility statements can also precede references. The sample's bracketed boilerplate is not a completed study statement. Paper owns completed disclosure, source text and synchronized PDF. There is no supplied official ICLR2027 attached checklist in the consulted sources. Keep any future required scientific checklist answers in paper-owned `sections/`, as story allocated.

`venue-artifacts.json` lists nonempty paths required in each delivered version. It is a presence check, not proof of complete source, faithful reproduction, scientific validity or a compliant page count. The objective matrix in `venue-requirements.md` remains the substantive standard. The asset manifest paths are relative to this `venue/` directory after integration. To verify hashes, resolve each listed `path` against `venue/`.

The included build checks concern the official style and sample only. Recheck the final paper's actual main-text boundary, required statements, figures, fonts and full rebuild from its delivered code before release.
