#!/usr/bin/env bash
set -eu
# Run from the delivered paper root after analysis-owned results are present.
analysis_revision=c291b715fcfed90d5b5905e2d7a8e1f721937616
python3 figures/generate_main.py --results results --config analysis/configs/main.json --analysis-revision "$analysis_revision"
python3 figures/generate_diagnostics.py --results results --config analysis/configs/main.json --analysis-revision "$analysis_revision"
python3 tables/generate_main_tables.py --results results --config analysis/configs/main.json --analysis-revision "$analysis_revision"
python3 tables/generate_primary_rates.py --results results --config analysis/configs/main.json --analysis-revision "$analysis_revision"
python3 figures/generate_claim_contrast.py --results results --config analysis/configs/main.json --analysis-revision "$analysis_revision"
python3 figures/generate_background.py --results results/background_sensitivity --analysis-revision 5d8d8e37ed7868e8d088315688c0843678abee55
python3 tables/render_previews.py
python3 figures/audit_artifacts.py
