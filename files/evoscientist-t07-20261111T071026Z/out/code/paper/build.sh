#!/usr/bin/env bash
# Build paper/main.pdf (ICLR 2027 template). Run from anywhere.
cd "$(dirname "$0")"
rm -f main.aux main.out main.bbl main.blg
pdflatex -interaction=batchmode main.tex > build.log 2>&1
bibtex main >> build.log 2>&1
pdflatex -interaction=batchmode main.tex >> build.log 2>&1
pdflatex -interaction=batchmode main.tex >> build.log 2>&1
grep -E "^! |Output written" main.log
