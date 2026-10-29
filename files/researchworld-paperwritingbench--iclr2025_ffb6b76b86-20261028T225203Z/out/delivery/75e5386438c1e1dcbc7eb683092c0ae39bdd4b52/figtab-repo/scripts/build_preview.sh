#!/bin/sh
# Compile the exhibits in the ICLR 2025 style to preview/preview.pdf for visual inspection.
# Uses the task's frozen style files and figures from /initial-state (read-only).
set -e
ROOT=$(cd "$(dirname "$0")/.." && pwd)
B=$ROOT/preview/build
rm -rf "$B"; mkdir -p "$B"
I=/initial-state/inputs
cp $I/1/fancyhdr.sty $I/4/iclr2025_conference.bst $I/5/iclr2025_conference.sty \
   $I/6/math_commands.tex $I/7/natbib.sty "$B"/
ln -s $I/2 "$B/figures"
cp "$ROOT/exhibits/figures.tex" "$ROOT/exhibits/tables.tex" "$ROOT/exhibits/table_fim_fallback.tex" "$ROOT/preview/preview.tex" \
   "$ROOT/preview/preview.bib" "$B"/
cd "$B"
pdflatex -interaction=nonstopmode preview.tex >/dev/null
bibtex preview >/dev/null
pdflatex -interaction=nonstopmode preview.tex >/dev/null
pdflatex -interaction=nonstopmode preview.tex > pdflatex.log
grep -E "Warning|Error|Overfull|Underfull" preview.log | grep -v "Font shape" || true
cp preview.pdf "$ROOT/preview/preview.pdf"
