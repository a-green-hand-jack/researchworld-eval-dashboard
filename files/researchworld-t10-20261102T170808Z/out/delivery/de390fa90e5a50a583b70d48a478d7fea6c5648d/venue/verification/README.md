# Reproduce the format probes

From the venue repository root (requires pdflatex and Poppler):

```sh
mkdir -p verification/build
TEXINPUTS="$PWD/official:" pdflatex -interaction=nonstopmode -halt-on-error -output-directory=verification/build verification/geometry.tex
TEXINPUTS="$PWD/official:" pdflatex -interaction=nonstopmode -halt-on-error -output-directory=verification/build official/neurips_2026.tex
pdfinfo verification/build/neurips_2026.pdf
pdffonts verification/build/neurips_2026.pdf
```

For the compatibility check copy the official example to the build directory, add `\renewcommand{\ttdefault}{pcr}` to that copy's preamble, compile it with the same TEXINPUTS, and inspect pdffonts. The official source remains unmodified. This is a format-only check, not a study result.
