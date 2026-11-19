#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
