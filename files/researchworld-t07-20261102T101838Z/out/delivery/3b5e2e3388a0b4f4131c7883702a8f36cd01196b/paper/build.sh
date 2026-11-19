#!/bin/sh
# Build paper/paper.pdf (and a copy at ../paper.pdf) with the unmodified official style in ../venue/template.
set -e
cd "$(dirname "$0")"
export TEXINPUTS="../venue/template:$TEXINPUTS"
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
bibtex main >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
pdflatex -interaction=nonstopmode -halt-on-error main.tex >/dev/null
cp main.pdf paper.pdf
cp main.pdf ../paper.pdf
rm -f main.aux main.bbl main.blg main.log main.out main.pdf
