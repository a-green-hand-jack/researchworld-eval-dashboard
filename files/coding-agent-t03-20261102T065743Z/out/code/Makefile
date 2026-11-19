PYTHON ?= .venv/bin/python
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
WORKERS ?= 4
.PHONY: data train games explain background validate timing solver analyze paper reproduce

data:
	$(PYTHON) code/download.py
train:
	$(PYTHON) code/prepare.py
games:
	$(PYTHON) code/games.py --workers $(WORKERS)
	$(PYTHON) code/reference_summary.py
explain:
	$(PYTHON) code/explain.py --workers $(WORKERS)
	$(PYTHON) code/explain.py --datasets german --default --workers $(WORKERS)
background:
	$(PYTHON) code/background.py
validate:
	$(PYTHON) code/validate.py
timing:
	$(PYTHON) code/timing.py
solver:
	$(PYTHON) code/solver_audit.py
analyze:
	$(PYTHON) code/analyze.py
	$(PYTHON) code/write_numbers.py
paper:
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper && bibtex main
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
	cd paper && pdflatex -interaction=nonstopmode -halt-on-error main.tex
reproduce: data train games explain background validate timing solver analyze paper
