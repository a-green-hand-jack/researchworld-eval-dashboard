#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export TEXINPUTS=".:./venue//:${TEXINPUTS:-}"
export BSTINPUTS=".:./venue//:${BSTINPUTS:-}"
latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
