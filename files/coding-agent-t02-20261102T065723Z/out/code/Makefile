PYTHON ?= .venv/bin/python
.PHONY: experiments analyze audit paper reproduce package
experiments:
	$(PYTHON) src/batch.py configs/main.json --jobs 4
	$(PYTHON) src/batch.py configs/secondary.json --jobs 4
	$(PYTHON) src/batch.py configs/features.json --jobs 4
	$(PYTHON) src/batch.py configs/replication.json --jobs 4
analyze:
	$(PYTHON) src/construct_circuit.py
	$(PYTHON) src/analyze.py
	$(PYTHON) src/write_results.py
audit:
	$(PYTHON) src/audit.py
paper:
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper && bibtex main
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
reproduce:
	$(MAKE) experiments
	$(MAKE) analyze
	$(MAKE) audit
	$(MAKE) paper

package:
	$(PYTHON) src/package.py
