#!/bin/bash
# Reproduction entrypoint: ./run_all.sh JOB   (each JOB is single-threaded; run independent JOBs in parallel)
# Setup (once): ./get_data.sh (downloads and checksums the raw data, builds data/processed, writes data/processed/ollb_noise.json); see README.md
# Jobs not listed here (ordinal ranks 2-100, h* grids, eps/robust-margin grids, 30-target noise/bootstrap, restricted pairs, cluster bootstrap, convex cost) are run by the companion scripts run_extra.sh, run_extra2.sh, run_robust30.sh, tried in that order.
# Unit tests: python3 -m pytest tests
set -e; cd "$(dirname "$0")"; mkdir -p results logs
SC=mean,geomean,harmonic,median,min; SL=mean,geomean,median,min; OR=borda,condorcet,plurality
ALLCAPS=ceil,front0,front2,gain5,gain10,gain20,emp95,emp99; C3=ceil,front0,gain10
case "$1" in
  helm_main)    python3 -u src/run_core.py helm ceil,front0,front2,gain5,gain10,gain20,emp95,emp99,emp95pool mean,geomean,harmonic,median,min,borda,condorcet,plurality all results/helm_main.csv ;;
  ollb_score)   python3 -u src/run_core.py ollb $ALLCAPS $SC all results/ollb_score.csv ;;
  ollb_ord_*)   cap=${1#ollb_ord_}; python3 -u src/run_core.py ollb $cap $OR sample results/ollb_ord_$cap.csv --nsample 100 ;;
  ollb_nomerge) python3 -u src/run_core.py ollb_nomerge $C3 $SL,$OR sample results/ollb_nomerge_sample.csv --nsample 100 ;;
  ollb_top500)  python3 -u src/run_core.py ollb_top500 $C3 $SL,$OR all results/ollb_top500.csv ;;
  ollb_raw)     python3 -u src/run_core.py ollb_raw $C3 $SL,$OR sample results/ollb_raw_sample.csv --nsample 100 ;;
  ollb_trim_*)  cap=${1#ollb_trim_}; python3 -u src/run_core.py ollb $cap trimmed1 all results/ollb_trim_$cap.csv ;;
  helm_trim)    python3 -u src/run_core.py helm ceil,front0,gain10,emp95 trimmed5 sample results/helm_trim_sample.csv --nsample 20 ;;
  helm_noise)   python3 -u src/run_robust.py noise helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_noise_gain10.csv --R 100 ;;
  ollb_noise)   python3 -u src/run_robust.py noise ollb mean,geomean,median,min gain10 results/ollb_noise_gain10.csv --R 100 ;;
  helm_taskboot) python3 -u src/run_robust.py taskboot helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_taskboot_gain10.csv --R 100 ;;
  helm_tasksub) python3 -u src/run_robust.py tasksub helm mean,median,min,borda,plurality gain10 results/helm_tasksub_gain10.csv --R 50 --sizes 5,9,13,17,21,25,29,33,37,41,45,49,53,57 ;;
  helm_flip)    python3 -u src/run_flip.py helm mean,geomean,median,min,borda ceil results/helm_flip_ceil.csv --R 200 ;;
  ollb_flip)    python3 -u src/run_flip.py ollb mean,geomean,median,min ceil results/ollb_flip_ceil.csv --R 200 ;;
  helm_spill)   python3 -u src/run_spillover.py helm ceil,gain10 results/helm_spillover.csv --nsample 40 ;;
  ollb_spill)   python3 -u src/run_spillover.py ollb ceil,gain10 results/ollb_spillover.csv --nsample 100 ;;
  helm_eps)     for e in 1e-6 1e-1; do python3 -u src/run_core.py helm ceil,gain10 mean,median,min,borda,condorcet,plurality all results/helm_eps$e.csv --eps $e; done ;;
  ollb_eps)     for e in 1e-6 1e-1; do python3 -u src/run_core.py ollb ceil,gain10 mean,median,min all results/ollb_eps$e.csv --eps $e; done ;;
  helm_hstar)   python3 -u src/run_hstar.py helm mean,geomean,harmonic,median,min,borda,condorcet,plurality all results/helm_hstar.csv ;;
  ollb_hstar)   python3 -u src/run_hstar.py ollb mean,geomean,harmonic,median,min all results/ollb_hstar.csv ;;
  ollb_hstar_ord) python3 -u src/run_hstar.py ollb borda,condorcet,plurality sample results/ollb_hstar_ord.csv --nsample 100 ;;
  *) for s in run_extra run_extra2 run_robust30; do rc=0; bash "./$s.sh" "$1" || rc=$?; [ "$rc" -ne 99 ] && exit "$rc"; done; echo "unknown job $1" >&2; exit 1 ;;
esac
