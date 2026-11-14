#!/bin/sh
# Build paper/main.pdf (pdflatex + bibtex). Style files are in template/ (unmodified, owned by venue-repo).
set -e
cd "$(dirname "$0")"
export TEXINPUTS=./template//:./:
export BSTINPUTS=./template//:./:
pdflatex -interaction=nonstopmode main.tex >/dev/null
bibtex main >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdfinfo main.pdf | grep Pages
