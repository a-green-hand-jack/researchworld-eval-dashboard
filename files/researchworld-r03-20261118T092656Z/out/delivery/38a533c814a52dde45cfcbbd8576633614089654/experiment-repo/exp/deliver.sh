#!/bin/bash
# Assemble the delivered code tree: exp/deliver.sh DEST  ->  DEST/code/ (DEST = a checkout of paper-repo, branch dev).
# Ships: src/, exp/, tests/, figdata/, PRIMARY_COMPARISONS.md, the MTEB data tables (CC0), data/SOURCES.md, every small result table
# (csv/json), and the compact per-model tables (results/*/per_model.parquet). Not shipped: raw per-fold records (rec_*.parquet, ~380 MB),
# fitted-factor files (fit_*.npz), E8 sweep parquets, the LLM matrices data/*.parquet (licences unstated: rebuilt by src/build_*.py).
set -e
cd "$(dirname "$0")/.."
D=$1/code
rm -rf "$D"; mkdir -p "$D/data" "$D/results"
cp -r src exp tests figdata PRIMARY_COMPARISONS.md "$D"/
find "$D" -name __pycache__ -prune -exec rm -rf {} \;
cp data/SOURCES.md data/mteb_long.parquet data/mteb_models.parquet "$D/data/"
(git ls-files results | grep -v '\.parquet$'; ls results/*/per_model.parquet) | sort -u | while read f; do mkdir -p "$D/$(dirname $f)"; cp "$f" "$D/$f"; done
cp exp/code_readme_head.md "$D/README.md"; tail -n +2 REPRODUCE.md >> "$D/README.md"
pip freeze 2>/dev/null | grep -i -E "^(numpy|scipy|pandas|pyarrow|scikit-learn|matplotlib|torch)==" > "$D/requirements.txt" || true
du -sh "$D"
