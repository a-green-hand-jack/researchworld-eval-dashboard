SHELL := /bin/bash
export TEXINPUTS := $(CURDIR)/venue/official/iclr2027//:
export BSTINPUTS := $(CURDIR)/venue/official/iclr2027//:

.PHONY: all paper check clean
all: paper
paper:
	latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex
check: paper
	python3 docs/check_integrated_sources.py
	python3 docs/check_document.py
clean:
	latexmk -c paper.tex
