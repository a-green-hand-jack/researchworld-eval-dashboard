#!/bin/sh
# Download the two public graphs and verify checksums (see data.md of the task / README.md).
set -e
cd "$(dirname "$0")"
[ -f socfb-Stanford3.zip ] || curl -s -L -O https://nrvis.com/download/data/socfb/socfb-Stanford3.zip
[ -f facebook_combined.txt.gz ] || curl -s -L -O https://snap.stanford.edu/data/facebook_combined.txt.gz
echo "b1221e414dbaf3278468f60881bac932e935b8813020157bc6fb3823f5e8720d  socfb-Stanford3.zip" | sha256sum -c -
echo "125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7  facebook_combined.txt.gz" | sha256sum -c -
[ -f socfb-Stanford3.mtx ] || python3 -m zipfile -e socfb-Stanford3.zip .
