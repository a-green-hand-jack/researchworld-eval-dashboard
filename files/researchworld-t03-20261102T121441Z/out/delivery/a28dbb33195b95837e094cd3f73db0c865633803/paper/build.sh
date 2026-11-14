#!/bin/sh
# Build the paper and copy the PDF to the delivery root.
set -e
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode main.tex
cp main.pdf ../paper.pdf
