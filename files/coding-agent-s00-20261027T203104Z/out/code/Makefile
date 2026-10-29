PYTHON ?= .venv/bin/python

.PHONY: reproduce experiment paper
reproduce: experiment paper

experiment:
	$(PYTHON) experiment.py > experiment.log
	$(PYTHON) report.py

paper:
	pdflatex -interaction=nonstopmode -halt-on-error paper.tex > latex-build.log
	bibtex paper >> latex-build.log
	pdflatex -interaction=nonstopmode -halt-on-error paper.tex >> latex-build.log
	pdflatex -interaction=nonstopmode -halt-on-error paper.tex >> latex-build.log

