#!/bin/bash
# Rebuilds every figure (figures/*.pdf, *.png) and table (figures/tables/*.tex, *.csv) from experiment-repo's results.
# Env: EXP_DIR  checkout of experiment-repo (default: ../code next to figures/ in paper-repo, else ../../experiment-repo)
#      FIG_DIR / TAB_DIR  output directories (default: this directory / its tables/)
#      PPI_DATA_DIR  ppi-python 0.2.3 data (only fig_calibration.py; downloaded by experiment-repo's src/data.py)
# Needs python3 with numpy, pandas, scipy, matplotlib. Runtime: about 1 minute.
set -e
cd "$(dirname "$0")/src"
python3 fig_real.py                  # real_main, real_correction, real_appendix, real_nsweep   (C1, C3)
python3 fig_theory_vs_measured.py    # plugin_cost                                               (C1)
python3 fig_calibration.py           # calibration_curves, calibration_gap                       (C1, C2)
python3 fig_synthetic.py             # synthetic_kappa, synthetic_factors                        (C2)
python3 fig_shift.py                 # plankton_shift                                            (C4)
python3 tables.py                    # tables/*.tex, *.csv
