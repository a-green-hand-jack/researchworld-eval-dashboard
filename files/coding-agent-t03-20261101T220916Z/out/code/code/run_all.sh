#!/bin/sh
# Reproduce every number, table and figure of the paper. Run from /work/code with the venv activated.
# Expected wall-clock on a 4-core quota (see README): data 1 min, main 75 min, bg 5 min, retrain 6 min,
# shaplib 10 min, highd 27 min, bgpair 8 min, replicate ~25 min, analysis 5 min.
set -e
python get_data.py /work/data/raw                  # raw data (UCI, OpenML, ACS PUMS CA 2018 via folktables)
python exp_main.py --ds pima,gmsc,acsincome,acsemployment,german --procs 4        # -> results/main
python exp_bg.py --procs 4                         # -> results/bg
python exp_bgpair.py --procs 4                     # -> results/bgpair
python exp_retrain.py --procs 4                    # -> results/retrain
python exp_shaplib.py --procs 4                    # -> results/shaplib
python exp_highd.py --procs 4                      # -> results/highd
SHAP_SPLIT=1 SHAP_OUT=/work/results/main_rep1 python exp_main.py --ds pima,gmsc,acsincome --procs 4   # replicate
python analyze_main.py 4                           # -> results/summary/*.parquet
python gen_setup.py                                # -> paper/gen/tab_setup.tex
python analyze_figs.py                             # -> paper/figs/*.pdf, paper/gen/*.tex, numbers.json
python analyze_rep.py                              # -> paper/gen/tab_rep.tex
python extra_stats.py                              # -> paper/gen/extra_stats.json (numbers quoted in prose)
cd ../paper && latexmk -pdf main.tex
