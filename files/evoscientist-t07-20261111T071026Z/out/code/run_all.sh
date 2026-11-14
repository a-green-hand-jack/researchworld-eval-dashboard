#!/usr/bin/env bash
# Reproduce everything (data -> results -> tables/figures -> paper PDF).
# Wall-clock on the shared 40-core CPU box used here (heavily oversubscribed; 12 worker processes):
#   stage 1 main grid ~3.5-5 h (990 tasks, dominated by MMLU-Pro), stage 2 ~2 min, analysis ~10 min, paper ~2 min.
# NOTE: in the original run, stage 1 was executed as 4 invocations with disjoint seeds (see README.md and
# code/merge_results.py); a single `--seeds 30` invocation is equivalent because every task is seeded
# deterministically.
set -euo pipefail
cd "$(dirname "$0")"

# 0. environment
pip install -r requirements.txt

# 1. data: fixed commit of the public benchmark-prediction repo (only data/scores/*.jbl is used)
mkdir -p data
if [ ! -d data/repo/.git ]; then
  rm -rf data/repo
  git clone https://github.com/socialfoundations/benchmark-prediction.git data/repo
fi
git -C data/repo checkout 55faff496947789f94e6b5908c77cbc3e84f81ad

# 2. stage 1: main grid (seeds 0..29; 3 regimes; budgets 10,25,50,100)
mkdir -p results
python code/run_experiments.py --seeds 30 --procs 12 --out results/main.csv > results/main.log 2>&1

# 3. stage 2 (post hoc estimators)
python code/run_stage2.py --seeds 30 --procs 12 --out results/stage2.csv

# 4. tables / figures / significance tests / extra statistics
python -W ignore code/analyze.py > results/analyze.log 2>&1
python code/extra_analysis.py > results/extra_analysis.log 2>&1
python code/make_tex_tables.py

# 5. paper (ICLR 2027 template)
bash paper/build.sh
