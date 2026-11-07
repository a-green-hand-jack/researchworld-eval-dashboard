#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/paper"
pdflatex -interaction=nonstopmode -halt-on-error paper.tex > ../logs/latex_first.log
bibtex paper > ../logs/bibtex.log
pdflatex -interaction=nonstopmode -halt-on-error paper.tex > ../logs/latex_second.log
pdflatex -interaction=nonstopmode -halt-on-error paper.tex > ../logs/latex_final.log
cp paper.pdf ../paper.pdf
