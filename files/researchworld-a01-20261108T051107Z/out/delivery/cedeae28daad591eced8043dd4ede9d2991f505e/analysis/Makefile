PYTHON ?= python3
RAW ?= data/raw
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

.PHONY: all quick data validate test main helm ollb robustness baselines review-checks core-tables tables
.NOTPARALLEL: all quick core-tables tables
all: validate test main robustness baselines review-checks tables final-additions

data:
	$(PYTHON) src/fetch_ollb.py $(RAW)/ollb.parquet
	$(PYTHON) src/fetch_helm.py $(RAW)/helm-v1.13.0
	$(PYTHON) src/build_data.py $(RAW)/ollb.parquet $(RAW)/helm-v1.13.0 data/processed
	$(PYTHON) src/build_final_variants.py $(RAW)/ollb.parquet
	$(PYTHON) src/audit_duplicate_selection.py $(RAW)/ollb.parquet
	$(PYTHON) src/ollb_items.py data/processed/ollb_noise.json
	$(PYTHON) src/audit_helm_aggregate.py $(RAW)/helm-v1.13.0

validate:
	$(PYTHON) src/record_environment.py
	$(PYTHON) src/validate_data.py

test:
	$(PYTHON) -m pytest tests -q

main: helm ollb
helm:
	$(PYTHON) src/run_suite.py helm
ollb:
	$(PYTHON) src/run_suite.py ollb

robustness:
	$(PYTHON) src/run_uncertainty_suite.py helm
	$(PYTHON) src/run_uncertainty_suite.py ollb_top500

baselines:
	$(PYTHON) src/run_baselines.py helm results/helm_baselines.csv --R 200

core-tables:
	$(PYTHON) src/check_results.py
	$(PYTHON) src/check_robustness.py
	$(PYTHON) src/analyze_results.py
	$(PYTHON) src/summarize_perturbations.py
	$(PYTHON) src/write_findings.py

tables: core-tables
	$(PYTHON) src/check_review_results.py

# Partial analysis for quick inspection: all HELM rules and full OLLB score rules.
quick: validate test helm
	$(PYTHON) src/run_core.py ollb ceil,front0,front2,gain5,gain10,gain20,emp95,emp99 mean,geomean,harmonic,median,min all results/ollb_scores.csv
	$(PYTHON) src/check_results.py --sources helm_main,ollb_scores,helm_sensitivity --out results/validation_quick.json
	$(PYTHON) src/analyze_results.py
	$(PYTHON) src/summarize_perturbations.py
	$(PYTHON) src/write_findings.py

# Additional checks requested by independent review; requires completed main runs.
review-checks:
	$(PYTHON) src/bootstrap_paired_targets.py results/paired_target_bootstrap.csv --R 1000
	$(PYTHON) src/run_frame_sensitivity.py results/frame_sensitivity.csv --R 10 --ntargets 10
	$(PYTHON) src/run_epsilon_sensitivity.py
	$(PYTHON) src/audit_ollb_borda.py
	$(PYTHON) src/summarize_review_checks.py
# Canonical paired summaries are generated and checked by the final tables stage.

# Final-review additions: all-target designs, not the sizing pilots.
.PHONY: final-additions final-frames final-controls final-population final-scales final-census final-summaries
.NOTPARALLEL: final-additions
final-additions: final-frames final-controls final-population final-scales final-census final-summaries
final-frames:
	$(PYTHON) src/run_measured.py results/final_frames_runtime.json -- $(PYTHON) src/run_final_frames.py results/final_frames.csv --R 100
final-controls:
	$(PYTHON) src/run_measured.py results/final_controls_runtime.json -- $(PYTHON) src/run_final_controls.py results/final_controls.csv
final-population:
	$(PYTHON) src/run_measured.py results/final_population_runtime.json -- $(PYTHON) src/run_final_population.py results/final_population.csv
final-scales:
	$(PYTHON) src/run_measured.py results/final_scales_runtime.json -- $(PYTHON) src/run_final_scales.py results/final_scales.csv
final-census:
	$(PYTHON) src/run_measured.py results/final_census_runtime.json -- $(PYTHON) src/summarize_final_census.py
final-summaries:
	$(PYTHON) src/summarize_full_frame_diagnostics.py
	$(PYTHON) src/check_full_frame_diagnostics.py
	$(PYTHON) src/check_final_results.py
	$(PYTHON) src/summarize_final_additions.py
	$(PYTHON) src/check_final_results.py --stage controls-summary
	$(PYTHON) src/check_final_results.py --stage frames-summary
	$(PYTHON) src/check_final_results.py --stage scales-summary
