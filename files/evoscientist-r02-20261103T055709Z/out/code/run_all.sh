#!/bin/bash
# Full reproduction pipeline (from the repository root). Wall-clock estimates are for a shared 40-core CPU box (load avg ~100-200);
# on an idle machine everything is several times faster.
set -e
pip install numpy==2.4.6 scipy==1.17.1 pandas==3.0.6 matplotlib==3.11.2 scikit-learn==1.9.1 pyarrow pillow
pip install torch==2.15.0 torchvision==0.29.2 --index-url https://download.pytorch.org/whl/cpu
mkdir -p data results results/tables figs paper/tables

# --- data (see README.md): CIFAR-10 parquet mirror (HF uoft-cs/cifar10) and CIFAR-10H soft labels
cd data
curl -L -o cifar10_train.parquet https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/train-00000-of-00001.parquet
curl -L -o cifar10_test.parquet  https://huggingface.co/datasets/uoft-cs/cifar10/resolve/main/plain_text/test-00000-of-00001.parquet
curl -L -o cifar10h-probs.npy  https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-probs.npy
curl -L -o cifar10h-counts.npy https://raw.githubusercontent.com/jcpeterson/cifar-10h/master/data/cifar10h-counts.npy
cd ..

# --- synthetic experiments (~6 min with 16 processes; 2400 jobs x 18 conformal variants)
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python code/exp_synth.py 100 16 > results/synth.log      # -> results/synth_raw.csv
OMP_NUM_THREADS=1 python code/exp_theory.py > results/theory.log                                    # -> results/theory.csv (~10 min)
OMP_NUM_THREADS=1 python code/diag_mondrian.py                                                       # -> results/diag_mondrian.csv
OMP_NUM_THREADS=2 python code/exp_scale.py                                                           # -> results/scale_law.csv
python code/analyze_synth.py > results/analyze_synth.log                                             # tables + figs/synth_*.pdf

# --- CIFAR-10 predictor: two seeds, 10 epochs each (~2 h each on the shared CPU; run both in parallel)
OMP_NUM_THREADS=6 python code/cifar_train.py 0 10 6 > results/cifar_train_seed0.log &
OMP_NUM_THREADS=6 python code/cifar_train.py 1 10 6 > results/cifar_train_seed1.log &
wait
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python code/exp_cifar.py 30 16 > results/cifar.log          # -> results/cifar_raw.csv
python code/analyze_cifar.py > results/analyze_cifar.log                                             # tables + figs/cifar_main.pdf
python code/make_tex_tables.py                                                                        # paper/tables/*.tex
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
