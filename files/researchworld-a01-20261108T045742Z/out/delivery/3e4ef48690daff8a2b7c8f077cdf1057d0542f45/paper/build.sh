#!/bin/sh
# Build paper/main.pdf with the unmodified ICLR 2027 style files from ../venue/iclr2027 (no `make` needed).
cd "$(dirname "$0")" || exit 1
export TEXINPUTS=../venue/iclr2027: BSTINPUTS=../venue/iclr2027:
latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex && cp main.pdf ../paper.pdf
