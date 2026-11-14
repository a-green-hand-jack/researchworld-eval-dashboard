#!/bin/sh
# Build the anonymous NeurIPS 2026 submission PDF to ../paper.pdf
set -e
cd "$(dirname "$0")"
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex >/dev/null
cp main.pdf ../paper.pdf
