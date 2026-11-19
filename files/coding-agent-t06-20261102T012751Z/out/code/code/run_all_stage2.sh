export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /work/code
../venv/bin/python exp_judges.py > ../results/judges.log 2>&1
../venv/bin/python exp_control.py > ../results/control.log 2>&1
