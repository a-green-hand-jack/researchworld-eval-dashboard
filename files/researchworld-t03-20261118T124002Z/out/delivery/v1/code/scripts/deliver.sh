#!/bin/bash
# Sync code/ and results/ into the delivery (paper-repo `dev`). usage: scripts/deliver.sh "commit message"
set -e
R="$(cd "$(dirname "$0")/.." && pwd)"; P=/hutian/paper
cd $P && git pull -q --rebase origin dev
rm -rf $P/code && mkdir -p $P/code $P/results
cp -r $R/shapaudit $R/scripts $R/docs $R/requirements.txt $P/code/ && cp $R/README.md $P/code/README.md
find $P/code -name __pycache__ -prune -exec rm -rf {} \;
rsync -a --delete --exclude='pilot_*' $R/results/ $P/results/ 2>/dev/null || cp -r $R/results/. $P/results/
cd $P && git add code results && git commit -qm "$1

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>" && git push -q origin HEAD:dev && git log --oneline | head -1
