PYTHON ?= .venv/bin/python
export OPENBLAS_NUM_THREADS = 1
export OMP_NUM_THREADS = 1

.PHONY: all data prepare experiments report test paper verify clean
all: data prepare experiments report test paper verify

data:
	$(PYTHON) -m src.fetch_data
prepare:
	$(PYTHON) -m src.prepare_data
experiments:
	$(PYTHON) -m src.run_experiments --task-bootstrap 300
report:
	$(PYTHON) -m src.report
test:
	$(PYTHON) -m pytest -q --junitxml=artifacts/tests.xml
paper:
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex
verify:
	$(PYTHON) -m src.verify_artifact
clean:
	cd paper && latexmk -c
