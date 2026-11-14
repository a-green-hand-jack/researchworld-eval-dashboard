#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 manuscript/extract_claims.py
export TEXINPUTS="$PWD/venue/official/neurips2026//:${TEXINPUTS:-}"
latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=manuscript/build manuscript/main.tex
cp manuscript/build/main.pdf paper.pdf
pdftotext -layout paper.pdf manuscript/rendered-text.txt
