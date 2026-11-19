#!/bin/bash
# Reproduces every result of the paper (see README.md for data download steps, which must be done first).
# Usage: bash run_all.sh   (about 1.5 h on a shared 40-core CPU machine, plus NLI inference)
set -e
cd "$(dirname "$0")"
source venv/bin/activate        # python -m venv venv && pip install -r requirements.txt
export PYTHONPATH=$PWD/code
mkdir -p results paper/figs paper/tables
# --- predictors / logits
python code/real/extract_logits.py
python code/real/extract_nli_logits.py            # slow on CPU (roberta-large)
# --- synthetic experiments
python code/exp1_calibration.py
python code/exp1b_pool_check.py
python code/exp2_geometry.py
python code/exp2b_theory.py
python code/exp2c_dirmult.py
python code/exp2d_ellipsoid.py
python code/exp3_learned.py
python code/exp3b_misfit.py
python code/exp4_selection.py
python code/exp6_worst_slice.py
python code/check_mass_estimator.py
# --- real data
python code/exp5_real.py
python code/exp5_real.py --data chaosnli
python code/exp5_real.py --alpha 0.05
python code/exp5_real.py --alpha 0.2
python code/exp5b_shift.py
# --- tables and figures
for a in 0.05 0.1 0.2; do python analysis/alpha_table.py $a; done
python analysis/fig_ternary.py
python analysis/make_e2.py
python analysis/make_e2c.py
python analysis/make_e3b.py
python analysis/make_e2d.py
python analysis/make_rest.py e1 theory e3 e4 shift cifar cifar_other nli alpha
python analysis/make_rest.py merged roberta-large_T
cd paper && latexmk -pdf main.tex
