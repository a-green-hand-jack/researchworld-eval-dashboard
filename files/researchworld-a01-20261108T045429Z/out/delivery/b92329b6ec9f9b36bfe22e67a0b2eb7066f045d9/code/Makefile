# Reproduction entrypoint.  `make data` needs network; everything else is offline.  Wall-clock figures are from a 2-CPU container.
PY ?= python3
RAW ?= /tmp/mti_raw
LEAFRAW ?= raw_leaf   # ~1.2 GB of compact JSONL; keep outside git
R = mean,geomean,harmonic,median,min
ALL = $(R),borda,condorcet,plurality
.PHONY: all data data-leaf test core robust copeland control leaf analyze checks final
all: test core robust copeland control leaf analyze checks final

data:      # ~1 min; rewrites data/processed/{ollb6,helm_mmlu*}.csv and manifest.json (hashes must match the committed manifest)
	$(PY) src/fetch_ollb.py $(RAW)/ollb && $(PY) src/fetch_helm.py $(RAW)/helm
	$(PY) src/build_data.py $(RAW)/ollb/ollb_contents.parquet $(RAW)/helm data/processed
	$(PY) src/ollb_items.py data/processed/ollb_noise.json

test:      # ~40 s idle host (194 s when the host was loaded): solvers vs brute force
	$(PY) -m pytest tests -q

core:      # HELM: ~15 min; OLLB score rules: ~15 min; OLLB ordinal rules (sampled targets): ~1.5 h
	$(PY) src/run_core.py helm ceil,front0,front2,gain5,gain10,gain20 $(ALL) all results/helm_main.csv
	$(PY) src/run_core.py ollb ceil $(R) all results/ollb_closed.csv
	$(PY) src/run_core.py ollb front0,front2,gain5,gain10,gain20 $(R) all results/ollb_score_caps.csv
	$(PY) src/run_core.py ollb emp95,emp99 $(R) all results/ollb_score_emp.csv
	$(PY) src/run_core.py ollb gain5,gain10,gain20 plurality,borda,condorcet sample results/ollb_ordinal_gain.csv
	$(PY) src/run_core.py ollb_top500 ceil,front0,gain5,gain10,gain20 $(ALL) sample results/ollb_top500.csv
	$(PY) src/run_core.py ollb ceil,gain10 trimmed1 sample results/ollb_trimmed.csv
	$(PY) src/run_core.py ollb_nomerge ceil,gain10 $(R) all results/ollb_nomerge_score.csv
	$(PY) src/run_core.py ollb_raw ceil,gain10 $(R) all results/ollb_raw_score.csv

robust:    # noise ~20 min, task bootstrap ~7 min, task subsets ~4 min each cap
	$(PY) src/run_robust.py noise helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_noise_gain10.csv --R 100 --ntargets 10
	$(PY) src/run_robust.py taskboot helm mean,geomean,median,min,borda,condorcet,plurality gain10 results/helm_taskboot_gain10.csv --R 100 --ntargets 10
	$(PY) src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality ceil results/helm_tasksub_ceil.csv --R 200 --sizes 3,6,12,24,48
	$(PY) src/run_robust.py tasksub helm mean,geomean,median,min,borda,plurality gain10 results/helm_tasksub_gain10.csv --R 200 --sizes 3,6,12,24,48
	$(PY) src/run_robust.py noise ollb mean,geomean,harmonic,median,min ceil results/ollb_noise_ceil.csv --R 100 --ntargets 10
	$(PY) src/run_robust.py noise ollb mean,geomean,harmonic,median,min gain10 results/ollb_noise_gain10.csv --R 100 --ntargets 10

copeland:  # exact Copeland MILP on HELM ranks 2..70 and OLLB top-500 ranks 2..11 (ceil, gain10; L1) + comparison with the Condorcet-winner requirement
	$(PY) src/run_copeland.py results/copeland_check.csv
	$(PY) src/copeland_table.py

control:   # random-allocation control (spread / ktasks schemes), HELM ranks <= 30
	$(PY) src/run_random_control.py results/random_control_ceil.csv --caps ceil --draws 100
	$(PY) src/run_random_control.py results/random_control_gain10.csv --caps gain10 --draws 100

data-leaf: # NETWORK, ~1.2 GB, ~40 min with 32 threads (resumable): 10 509 result JSONs of open-llm-leaderboard/results -> compact JSONL -> data/processed/ollb_leaf.csv
	$(PY) src/fetch_ollb_results.py $(LEAFRAW)
	$(PY) src/build_leaf.py $(LEAFRAW)/ollb_results_leaf.jsonl data/processed

leaf:      # leaf-task OLLB board (39 tasks, same models): score rules on all targets, same models aggregated to 6 benchmarks, top-500 slice with all rules, task-subset scaling
	$(PY) src/run_core.py ollb_leaf ceil $(R) all results/leaf_closed.csv
	$(PY) src/run_core.py ollb_leaf front0,front2,gain5,gain10,gain20 $(R) all results/leaf_score_caps.csv
	$(PY) src/run_core.py ollb_leaf6 ceil,gain10 $(R) all results/leaf6_score.csv
	$(PY) src/run_core.py ollb_leaf_top500 ceil,gain10 $(ALL) sample results/leaf_top500.csv
	$(PY) src/run_robust.py tasksub ollb_leaf mean,geomean,median,min ceil results/leaf_tasksub_ceil.csv --R 100 --sizes 3,6,12,24,39
	$(PY) src/run_robust.py tasksub ollb_leaf mean,geomean,median,min gain10 results/leaf_tasksub_gain10.csv --R 100 --sizes 3,6,12,24,39
	$(PY) src/run_robust.py tasksub ollb_leaf_top500 mean,geomean,median,min,borda,plurality ceil results/leaf_top500_tasksub_ceil.csv --R 60 --sizes 3,6,12,24,39

analyze:   # seconds
	$(PY) src/analyze.py
	for f in helm_main ollb_closed ollb_score_caps ollb_score_emp ollb_top500 ollb_trimmed ollb_nomerge_score ollb_raw_score; do $(PY) src/summarize.py results/$$f.csv results/tables/summary_$$f > /dev/null; done

final:     # ~3 min (finalize 150 s, extras ~1 min): figure-ready files results/final/ (status encoding, per-task units, theory per target, robustness summaries) and results/manifest.csv
	$(PY) src/finalize.py
	$(PY) src/summarize_extras.py
	$(PY) src/helm_neartie.py
	$(PY) src/manifest.py

checks:
	$(PY) src/theory_checks.py > results/theory_checks.txt; ! grep -q FAIL results/theory_checks.txt
