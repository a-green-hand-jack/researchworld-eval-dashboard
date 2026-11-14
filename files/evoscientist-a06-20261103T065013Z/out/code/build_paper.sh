#!/usr/bin/env bash
set -euo pipefail
ROOT="$(dirname "$(realpath "$0")")"
export TEXINPUTS="$ROOT/:$ROOT/template//:${TEXINPUTS:-}"
export BIBINPUTS="$ROOT/:${BIBINPUTS:-}"
export BSTINPUTS="$ROOT/:$ROOT/template//:${BSTINPUTS:-}"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$ROOT" "$ROOT/paper.tex" > "$ROOT/artifacts/latex-pass1.log"
python -c 'import subprocess,sys; subprocess.run(["bibtex","paper"],cwd=sys.argv[1],check=True)' "$ROOT" > "$ROOT/artifacts/bibtex.log"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$ROOT" "$ROOT/paper.tex" > "$ROOT/artifacts/latex-pass2.log"
pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$ROOT" "$ROOT/paper.tex" > "$ROOT/artifacts/latex-pass3.log"
printf 'Built %s/paper.pdf\n' "$ROOT"
