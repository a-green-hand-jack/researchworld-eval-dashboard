#!/bin/sh
set -eu
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
bibtex paper
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex
