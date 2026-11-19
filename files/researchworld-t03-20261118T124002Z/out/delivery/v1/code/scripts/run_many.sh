#!/bin/bash
# usage: run_many.sh STAGE CELL... ; STAGE = est (R=20 grid) | certs
cd "$(dirname "$0")/.."
ST=$1; shift
for c in "$@"; do
  if [ "$ST" = est ]; then python3 -u scripts/run_estimators.py --cell $c --R 20 --tag R20;
  elif [ "$ST" = certs ]; then python3 -u scripts/run_certs.py --cell $c --R 20 --tag certs; fi
done
