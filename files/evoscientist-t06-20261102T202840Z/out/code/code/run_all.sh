#!/bin/bash
# Reproduce all results. Run from the repository root:  bash code/run_all.sh
# Needs data/ (bash code/download_data.sh). Takes ~3-5 minutes on 20 CPU cores (pools use up to 20 workers).
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
python code/run_pairs.py                 # results/pairs.csv, boot_rank.csv            (Exp. 1)
python code/run_rankshift_scaling.py     # results/rankshift.csv, subsample.csv, matched.csv (Exp. 2-3)
python code/run_matched_sub.py           # results/matched_sub.csv
python code/run_noise.py                 # results/noise.csv                          (Exp. 4)
python code/run_robust.py                # results/robust_*.csv                       (Exp. 5)
python code/analyze.py                   # paper/tables/*.tex, paper/figures/*.pdf, results/summary.json
python code/make_checklist.py            # paper/checklist.tex
(cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex) > results/latex_build.log
