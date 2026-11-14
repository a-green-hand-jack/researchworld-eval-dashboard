#!/bin/bash
# usage: jobs/_run.sh LOGNAME OUTCSV -- run_core/run_robust args...   (HiGHS prints to stdout without newline; filtered into the log)
log=$1; shift; cd "$(dirname "$0")/.."; mkdir -p logs
python3 -u "$@" 2>&1 | grep --line-buffered -a -v Highs > logs/$log.log
