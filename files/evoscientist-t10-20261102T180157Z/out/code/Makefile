.PHONY: all data test experiments analysis paper validate

export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

all: data test experiments analysis paper validate

data:
	python download_data.py

test:
	python -m pytest tests -q

experiments:
	python run_experiments.py --reps 2000 --jobs 4
	python run_stratified.py --jobs 4

analysis:
	python analyze.py
	python plot.py

paper:
	latexmk -pdf -interaction=nonstopmode -halt-on-error paper.tex

validate:
	python validate.py
