#!/bin/sh
# Full reproduction (run from /work; 4 CPU cores were available -> ~3 h in total). Seeds: base seed 20261102 (see run_*.py).
set -e
PY="./venv/bin/python -I"
sh code/download_data.sh /work/data_raw
$PY code/prep_data.py data_raw data                      # .jbl -> .npz (restricted unpickler)
$PY code/run_main.py --reps 30 --tag main2 --workers 4   # main factorial experiment      (~80 min)
$PY code/run_main.py --reps 30 --tag main2 --workers 4 --regimes fam --benches arc_challenge,bbh,gpqa,ifeval,mmlu_pro,musr,openllm_math   # family hold-out (~38 min)
$PY code/run_cover.py --workers 3 --reps 5               # unbiasedness / coverage check  (~20 min)
$PY code/run_ablate.py --workers 3 --reps 10             # ablations                      (~60 min)
$PY code/data_summary.py                                 # results/tables/datasets.tex
$PY code/analyze_main.py                                 # main tables/figures, significance.csv, summary_main.pkl
$PY code/analyze_extra.py                                # cover.tex, ablation csv files
$PY code/make_ablation_tables.py                         # ablation tables for the appendix
$PY code/analyze_diag.py                                 # fig_pirt_bias_mechanism.pdf, diag.csv
$PY code/make_paper_tables.py                            # tables included by the paper
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
