#!/usr/bin/env bash
# Reproduction entry points (run from anywhere; paths are relative to the repository root).
#   code/reproduce.sh quick            re-run 10 runs of E1 (MLP d=16/32/64, tfm d=16/32, seeds 0-1) and compare with the stored results
#                                      (expected last line: "10 runs matched, 0 differ"; measured 10 min on 2 contended cores)
#   code/reproduce.sh tables [PAPER]   rebuild the tidy tables and summaries from the per-run JSON in results/ (a few hours: the bootstrap
#                                      summaries dominate), and, if PAPER is the paper-repo root, the figures and tables via figtab's generators
#   code/reproduce.sh figures PAPER    only the figures and LaTeX tables (minutes), from the stored results/ tables
set -euo pipefail
cd "$(dirname "$0")/.."
export EXPERIMENT_CODE="$PWD/code"
case "${1:-}" in
  quick)
    python3 code/sweep.py code/grids/QUICK_subset.json results/quick_check --workers 2
    python3 code/check_subset.py results/quick_check results/E1/mlp_runs.csv results/E1/tfm_runs.csv ;;
  tables)
    for d in E1/mlp E1/tfm E1/small E2/mlp E2/tfm E4/mlp E4/tfm_p97; do python3 code/collect.py results/$d results/$d; done
    for d in E0b E2b E3 E3b E6 E9 E10 E11 E13; do
      [ -d results/$d/runs ] && python3 code/collect.py results/$d/runs results/$d/$(echo $d | tr A-Z a-z)
    done
    python3 -W ignore code/analysis.py e1 results/E1/mlp_runs.csv results/E1/summary_mlp.json --label "E1 mlp"
    python3 -W ignore code/analysis.py e1 results/E1/tfm_runs.csv results/E1/summary_tfm_all.json --label "E1 tfm all"
    python3 -W ignore code/analysis.py e1 results/E1/tfm_runs.csv results/E1/summary_tfm_seeds0-7.json --max-seed 7 --label "E1 tfm seeds 0-7"
    python3 -W ignore code/analyze_e2.py results/E2/mlp_cells.csv results/E2/mlp_runs.csv results/E1/mlp_runs.csv
    python3 -W ignore code/analyze_e2.py results/E2/tfm_cells.csv results/E2/tfm_runs.csv results/E1/tfm_runs.csv
    python3 -W ignore code/e2_slopes.py results/E2/slopes_by_f.json results/E2/mlp_runs.csv:mlp results/E2/tfm_runs.csv:tfm
    python3 -W ignore code/analyze_e3.py results/E3/e3_runs.csv results/E3/summary_e3.json --fresh results/E3b/e3b_runs.csv
    python3 -W ignore code/analyze_e3.py results/E3/e3_runs.csv results/E3/summary_e3.json --fresh results/E3b/e3b_runs.csv --wd3-only
    python3 -W ignore code/capacity_ratio.py results/capacity_ratio results/E1/mlp_runs.csv results/E1/tfm_runs.csv results/E2/mlp_runs.csv results/E2/tfm_runs.csv
    python3 -W ignore code/robust_slopes.py code/specs/robust_main.json results/robust/main --B 1000
    for d in mlp:mlp_e7 mlp_hi:mlp_hi mlp_wd3hi:mlp_wd3hi tfm:tfm_e7; do python3 code/collect.py results/E7/${d%%:*} results/E7/${d##*:}; done
    for d in mlp tfm; do python3 code/collect.py results/E8/$d results/E8/${d}_e8; done
    python3 -W ignore code/analyze_e7.py results/E7/analysis_final
    python3 -W ignore code/robust_slopes.py results/E7/analysis_final/spec.json results/E7/robust_final --B 1000
    python3 -W ignore code/robust_slopes.py code/specs/robust_e8.json results/E8/robust --B 1000
    python3 -W ignore code/robust_slopes.py code/specs/robust_e10.json results/robust/e10 --B 1000
    for d in mlp tfm; do python3 code/collect.py results/E8b/$d results/E8b/${d}_e8b; done
    python3 -W ignore code/analyze_e8b.py results/E8b/analysis results/E8/mlp_e8_runs.csv results/E8b/mlp_e8b_runs.csv results/E8/tfm_e8_runs.csv results/E8b/tfm_e8b_runs.csv
    for k in 0 1 2; do python3 -W ignore code/robust_slopes.py results/E8b/analysis/spec_$k.json results/E8b/robust_$k --B 1000; done   # split of code/specs/robust_e8b.json
    python3 -c "import pandas as pd; pd.concat([pd.read_csv(f'results/E8b/robust_{k}_table.csv') for k in range(3)]).to_csv('results/E8b/robust_table.csv',index=False)"
    python3 code/collect.py results/E14/mlp results/E14/mlp_e14
    python3 -W ignore code/analyze_e14.py results/E14/analysis results/E14/mlp_e14_runs.csv
    # one spec per block (the full spec.json takes over an hour on one core); concatenated into results/E14/robust_table.csv
    for k in sel sel32 fx04 fx03; do python3 -W ignore code/robust_slopes.py results/E14/analysis/spec_$k.json results/E14/robust_$k --B 1000; done
    python3 -c "import pandas as pd; pd.concat([pd.read_csv(f'results/E14/robust_{k}_table.csv') for k in ['sel','sel32','fx04','fx03']]).to_csv('results/E14/robust_table.csv',index=False)"
    python3 -W ignore code/analyze_e9.py results/E9/fine results/E9/runs results/E1/mlp_runs.csv:mlp results/E1/tfm_runs.csv:tfm
    [ -n "${2:-}" ] && "$0" figures "$2" || true ;;
  figures)
    P="${2:?path to the paper-repo checkout}"
    python3 "$P/figures/make_figures.py" --results "$PWD/results" --out "$P/figures/"
    python3 "$P/tables/make_tables.py" --results "$PWD/results" --out "$P/tables/" ;;
  *) sed -n '2,9p' "$0"; exit 2 ;;
esac
