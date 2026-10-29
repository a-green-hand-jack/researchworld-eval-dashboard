#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
mkdir -p data/raw data/processed results figures logs paper/generated
if [[ ! -x .venv/bin/python ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements-lock.txt
fi
.venv/bin/python src/download.py | tee logs/download.log
.venv/bin/python src/prepare.py | tee logs/prepare.log
.venv/bin/python src/test_methods.py | tee logs/tests.log
.venv/bin/python src/experiment.py --reps 500 --boot 1000 | tee logs/experiment.log
.venv/bin/python src/matched.py | tee logs/matched.log
.venv/bin/python src/supplement.py | tee logs/supplement.log
.venv/bin/python src/verify_results.py | tee logs/verification.log
.venv/bin/python src/report.py > logs/report.log 2>&1
cp data/manifest.json DATA_MANIFEST.json
(
  cd paper
  pdflatex -interaction=nonstopmode -halt-on-error paper.tex > ../logs/latex-pass1.log
  bibtex paper > ../logs/bibtex.log
  pdflatex -interaction=nonstopmode -halt-on-error paper.tex > ../logs/latex-pass2.log
  pdflatex -interaction=nonstopmode -halt-on-error paper.tex > ../logs/latex-pass3.log
)
.venv/bin/python src/audit_pdf.py | tee logs/pdf-audit.log
printf '\nCompleted: paper/paper.pdf\n'
