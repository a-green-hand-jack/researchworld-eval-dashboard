#!/bin/sh
# Reproduces every number, table and figure of the paper. Run from /work (or set BT_DATA).
# Wall-clock about 40 min with 12 worker processes (Pool(12)); reduce the Pool size in run_*.py for fewer cores.
set -e
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
PY=${PY:-python3}
cd code
$PY dataset_stats.py                                  # results/dataset_stats.csv           (Table 1)
$PY tests.py                                          # results/validation.json             (Appendix C; ~2.5 min)
$PY run_attack.py ../results/attack_all.csv           # flip budgets, all adjacent/top-k pairs (Tables 2, A*; Fig 1, 2)
$PY run_attack.py ../results/attack_noties.csv noties # tie-discarding variant              (Appendix D.6)
$PY run_noise.py  ../results/noise_all.csv            # random perturbations                (Table 3, Fig 2)
$PY run_noise.py  ../results/noise_140k.csv arena140k
$PY run_scaling.py ../results/scaling_all.csv         # N-scaling + bootstrap datasets      (Fig 3, CIs of Table 2)
$PY run_scaling.py ../results/scaling_140k.csv arena140k
$PY run_cluster.py                                    # cluster-bootstrap check             (Section 4.5)
$PY analyze.py                                        # all tables (results/tab_*.tex), figures/*.pdf, results/summary.json
cd ../paper && latexmk -pdf main.tex
