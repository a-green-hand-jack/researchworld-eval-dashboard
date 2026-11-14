# sourced by the launch_*.sh scripts.  run <name> <run_cv.py options>   writes results/raw/<name>.parquet (+ .json with the exact arguments)
# default: one ht-resource job per run; with LOCAL=1 plain python in the foreground (sequential; no ht-resource needed):  LOCAL=1 bash code/launch_primary.sh
run() {
  name=$1; shift
  if [ -n "$LOCAL" ]; then
    python3 -u code/run_cv.py --out results/raw/$name.parquet "$@"
  else
    ht-resource run local-compute --note "$name" -- python3 -u code/run_cv.py --out results/raw/$name.parquet "$@" | grep '"ref"'
  fi
}
