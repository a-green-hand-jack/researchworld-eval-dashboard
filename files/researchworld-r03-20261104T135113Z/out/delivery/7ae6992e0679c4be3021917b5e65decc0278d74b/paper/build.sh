#!/bin/bash
# build paper.pdf from paper/ with the unmodified official ICLR 2027 files in ../venue/template
cd "$(dirname "$0")"
export TEXINPUTS=../venue/template//:$TEXINPUTS
export BSTINPUTS=../venue/template//:$BSTINPUTS
latexmk -pdf -interaction=nonstopmode -jobname=paper main.tex
