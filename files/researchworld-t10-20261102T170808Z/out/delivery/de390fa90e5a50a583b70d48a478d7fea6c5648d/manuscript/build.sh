#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p manuscript/build
python3 manuscript/import_numbers.py
TEXINPUTS="$PWD/venue/official:$PWD/manuscript:" latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=manuscript/build manuscript/main.tex
cp manuscript/build/main.pdf paper.pdf
