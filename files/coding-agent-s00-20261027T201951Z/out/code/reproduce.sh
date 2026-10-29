#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
.venv/bin/python experiment.py
.venv/bin/python write_tables.py
TEXINPUTS="$PWD/vendor:" pdflatex -interaction=nonstopmode -halt-on-error paper.tex > results/latex.log
TEXINPUTS="$PWD/vendor:" pdflatex -interaction=nonstopmode -halt-on-error paper.tex >> results/latex.log
