#!/bin/sh
# copy code and results into a checkout of paper-repo (dev): code/ and results/ (tables) + results/raw/ (raw run files)
set -e
D=${1:?usage: sync_delivery.sh PAPER_REPO_CHECKOUT}
mkdir -p $D/code $D/results/raw
cp -r lbprice scripts tests analysis data_proc data_meta $D/code/
find $D/code -name __pycache__ -prune -exec rm -rf {} +
cp code_docs/*.md $D/code/
for f in ${RAWFILES:-results/*.csv}; do cp $f $D/results/raw/; done
cp results_tables/* $D/results/ 2>/dev/null || true
