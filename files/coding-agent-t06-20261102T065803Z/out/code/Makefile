SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
PY := .venv/bin/python

.PHONY: setup download verify experiments winner audit report paper reproduce package

setup: .venv/.ready

.venv/.ready: requirements.txt
	python3 -m venv .venv
	.venv/bin/pip install -r requirements.txt
	touch $@

download: setup
	$(PY) src/download.py | tee logs/download.log

verify: setup
	$(PY) src/verify.py 2>&1 | tee logs/verification.log

experiments: setup
	$(PY) src/experiment.py --bootstrap 500 --random 500 --matched 100 | tee logs/experiment.log

winner: setup
	$(PY) src/winner.py | tee logs/winner.log

audit: setup
	$(PY) src/audit.py | tee logs/audit.log

report: setup
	$(PY) src/report.py | tee logs/report.log

paper: setup
	$(PY) src/fill_checklist.py
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex > ../logs/latex.log 2>&1
	$(PY) src/check_pdf.py | tee logs/pdf_check.log

reproduce: setup
	$(MAKE) download
	$(MAKE) verify
	$(MAKE) experiments
	$(MAKE) winner
	$(MAKE) audit
	$(MAKE) report
	$(MAKE) paper

package:
	python3 src/package.py
