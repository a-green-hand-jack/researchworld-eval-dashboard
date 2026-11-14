# Reproduction entry point. `make data` needs network; everything else is offline CPU work. Measured wall times per target: see REPRODUCE.md section 3.
PY=python3
DATA=data/raw
.PHONY: data test theory helm helm_extra ollb_score ollb_ordinal ollb_variants ollb_margin_c5 robust summary all
data:
	$(PY) src/fetch_ollb.py $(DATA)/ollb
	$(PY) src/fetch_helm.py $(DATA)/helm/v1.13.0
	$(PY) src/build_data.py $(DATA)/ollb/train-00000-of-00001.parquet $(DATA)/helm/v1.13.0 data/processed
	$(PY) src/ollb_items.py data/processed/ollb_noise.json
test:
	$(PY) -m pytest -q tests
theory:
	$(PY) src/theory_checks.py results/theory_checks.csv
helm:
	$(PY) src/run_core.py helm ceil,front0,front2,gain5,gain10,gain20 mean,geomean,harmonic,median,min,borda,condorcet,plurality all results/helm_main.csv
ollb_score:
	$(PY) src/run_core.py ollb ceil mean,geomean,harmonic,median,min all results/ollb_closed.csv
	$(PY) src/run_core.py ollb front0,front2,gain5,gain10,gain20 mean,geomean,harmonic,median,min,trimmed1 all results/ollb_score_caps.csv
	$(PY) src/run_core.py ollb emp95,emp99 mean,geomean,harmonic,median,min,trimmed1 all results/ollb_score_emp.csv
ollb_ordinal:
	for c in ceil front2 gain10 emp95; do $(PY) src/run_core.py ollb $$c borda,condorcet,plurality sample results/ollb_ordinal_$$c.csv --nsample 100; done
ollb_margin_c5:
	$(PY) src/run_core.py ollb ceil,front2,gain10 mean,geomean,harmonic,median,min all results/ollb_margin1_score.csv --eps 0.96
	$(PY) src/run_core.py ollb ceil,front2,gain10 mean,geomean,harmonic,median,min all results/ollb_margin_score.csv --eps 1.92
	$(PY) src/run_core.py ollb emp99 borda,condorcet,plurality top20 results/ollb_ordinal_emp99_top20.csv
helm_extra:    # item-count-weighted mean; statistical margins k*SE (k=1,2): score rules only, eps = k*0.6 pts (k=1,2; SE of a difference of two models' MEAN aggregate; for median/min it is only an approximate scale). Rank rules: eps there is a strict-pass granularity, not a statistical margin; their noise robustness is run_robust.py noise
	$(PY) src/run_core.py helm ceil,front2,gain10,gain20 wmean all results/helm_wmean.csv
	$(PY) src/run_core.py helm ceil,front2,gain20 mean,geomean,harmonic,median,min,wmean all results/helm_margin1_score.csv --eps 0.6
	$(PY) src/run_core.py helm ceil,front2,gain20 mean,geomean,harmonic,median,min,wmean all results/helm_margin_score.csv --eps 1.2
ollb_variants:  # raw (unnormalised) scores, non-merged slice, top-500 slice
	$(PY) src/run_core.py ollb_raw ceil,front2,gain10 mean,geomean,harmonic,median,min all results/ollb_raw_score.csv
	$(PY) src/run_core.py ollb_nomerge ceil,front2,gain10 mean,geomean,harmonic,median,min all results/ollb_nomerge_score.csv
	$(PY) src/run_core.py ollb_top500 ceil,front2,gain10 mean,geomean,harmonic,median,min,trimmed1,borda,condorcet,plurality sample results/ollb_top500.csv --nsample 100
robust:
	$(PY) src/run_robust.py noise helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_noise_gain10.csv --R 100
	$(PY) src/run_robust.py taskboot helm mean,median,min,borda,plurality gain10 results/helm_taskboot_gain10.csv --R 50
	for c in gain10 front2; do $(PY) src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality $$c results/helm_tasksub_$$c.csv --R 200; done
	for c in gain10 front2; do $(PY) src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality $$c results/helm_tasksubpaired_$$c.csv --R 200 --targets mean; done
summary:
	$(PY) src/raw_vs_norm_paired.py results/ollb_closed.csv results/ollb_raw_score.csv results/ollb_raw_vs_norm_paired_per_target.csv results/summary_ollb_raw_vs_norm_paired.csv
	$(PY) src/c5_table.py results/c5_top10_emp.csv results/ollb_score_emp.csv results/ollb_ordinal_emp95.csv results/ollb_ordinal_emp99_top20.csv
	$(PY) src/summarize_main.py results/summary_ollb_margin2se results/ollb_margin_score.csv
	$(PY) src/summarize_main.py results/summary_ollb_margin1se results/ollb_margin1_score.csv
	$(PY) src/condorcet_existence.py results/condorcet_existence.csv
	$(PY) src/summarize_main.py results/summary_helm_main results/helm_main.csv results/helm_wmean.csv
	$(PY) src/summarize_main.py results/summary_ollb results/ollb_closed.csv results/ollb_score_caps.csv results/ollb_score_emp.csv results/ollb_ordinal_ceil.csv results/ollb_ordinal_front2.csv results/ollb_ordinal_gain10.csv results/ollb_ordinal_emp95.csv
	$(PY) src/summarize_main.py results/summary_helm_margin2se results/helm_margin_score.csv
	$(PY) src/summarize_main.py results/summary_helm_margin1se results/helm_margin1_score.csv
	$(PY) src/summarize_main.py results/summary_ollb_raw results/ollb_raw_score.csv
	$(PY) src/summarize_main.py results/summary_ollb_nomerge results/ollb_nomerge_score.csv
	$(PY) src/summarize_main.py results/summary_ollb_top500 results/ollb_top500.csv
	for c in gain10 front2; do $(PY) src/summarize_robust.py tasksub results/helm_tasksub_$$c.csv results/summary_helm_tasksub_$$c; done
	for c in gain10 front2; do $(PY) src/summarize_robust.py tasksub results/helm_tasksubpaired_$$c.csv results/summary_helm_tasksubpaired_$$c; done
	$(PY) src/summarize_robust.py noise results/helm_noise_gain10.csv results/summary_helm_noise_gain10 results/helm_main.csv gain10
	$(PY) src/summarize_robust.py taskboot results/helm_taskboot_gain10.csv results/summary_helm_taskboot_gain10 results/helm_main.csv gain10
all: data test theory helm helm_extra ollb_score ollb_ordinal ollb_variants ollb_margin_c5 robust summary
