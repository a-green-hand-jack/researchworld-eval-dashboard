# Benchmark selection and prediction experiments

This repository owns data processing, predictive methods, numerical experiments and result evidence for the ResearchWorld study. The research question is to infer a new model's unrun benchmark scores from a small selected set of measured benchmark scores.

## Data and provenance

`python3 scripts/acquire.py mteb` and `python3 scripts/acquire.py open_llm` fetch only the supplied pinned sources; URLs, file hashes and sizes are recorded in `data/*_source.json`. The MTEB snapshot is embedding models, not a generative LLM dataset. Open LLM Leaderboard is a separate six-benchmark secondary dataset. Its dataset license is undeclared in the supplied material; source data are fetched rather than relicensed here.

`python3 scripts/prepare.py mteb` streams the archive into an English main-score matrix, retaining only explicitly labelled English entries, selecting the most-covered revision per model (lexical tie break), and keeping each task's modal English subset signature. It does not infer scores for missing cells. `data/mteb_records.parquet` maps each retained measurement to its archive path. `data/mteb_tasks.json` records subset and dataset revision metadata. Parser exclusions are counted in `results/mteb_parse_audit.json`. The large archive stays ignored by git. `python3 scripts/prepare.py open_llm` removes flagged rows and deduplicates model names, preferring bfloat16, float16, then float32; raw rather than chance-normalized scores are retained.

`requirements.txt` pins the four directly imported analysis packages and their required runtime dependencies; the tested interpreter is CPython 3.11.2 on Linux x86_64. `requirements.lock` is an archival freeze of the supplied environment, including unused packages; it is not the installation input for this study. In particular, its unused PyTorch CPU build would require the separate https://download.pytorch.org/whl/cpu index. The final protocol and completed results are in `notes/PROTOCOL.md` and `notes/RESULTS.md`; `PROTOCOL_DRAFT.md` is a superseded design record. No restricted research pages have been accessed; data-network access was confined to the task-supplied repositories and their file-list endpoints.

## Run the study

From this directory with CPython 3.11, create an isolated environment and install the analysis dependencies from the default Python package index:

```
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/reproduce.py
```

The reproduction entry point also works from the final delivery root as `python3 analysis/scripts/reproduce.py`; its subprocesses use the same interpreter and set their working directory to `analysis/`. For a quick check of supplied artifacts without rerunning experiments, use `python3 analysis/scripts/reproduce.py --check-only` from that root (or `python3 scripts/reproduce.py --check-only` here).

The full command fetches data if absent, reconstructs the exact-revision cohorts, runs the model-held-out experiments, checks the Gaussian identity and fixed common targets, and creates machine-readable summaries. `--prepared` skips only data acquisition/preparation when the committed score matrices are present. The measured one-seed pilot was 0.3 seconds; the full suite includes 100 dataset/condition/split fits plus random designs and uncertainty aggregation, with measured final times recorded in `results/*/timing.json`. Parsing the pinned archive measured 72.83 seconds. Download time depends on network conditions. Keep source data and intermediates below the task's 5 GB limit; this study uses less than 1 GB before git history.

`notes/PROTOCOL.md` defines the evaluation and descriptive uncertainty estimand; `notes/THEORY.md` gives the linear-prediction derivation and its assumptions; `notes/RUN_LOG.md` records superseded runs and corrections. `results/summary.csv`, `results/paired_effects.csv`, `results/cohorts.json`, `results/uncertainty.json` and `results/gaussian_identity.json` are the numeric handoff. Per-condition `model_losses.csv`, `splits.json`, `designs.json` and `timing.json` preserve model-level results, train/validation/test identities, query selections and measured runtimes. Final figures and manuscript are owned by other positions; their script-to-figure/table mapping will accompany that delivery.

`python3 scripts/compact.py` losslessly compresses completed per-model losses and query-design JSON files for delivery (`.csv.gz` / `.json.gz`). Pandas reads the compressed CSVs directly; `gzip.open(..., 'rt')` reads the JSON. The summary script accepts either form and prefers the newly generated CSV over an older compressed copy during reruns. `scripts/task_diagnostics.py` generates the diagnostic task errors, pairwise overlap counts and descriptive correlation matrix; the latter is never used for fitting or selection.

`scripts/diagnostic_summary.py` creates the compact difficult-task, unique-model error-tail, training-scale-normalized error, seed-range, task correlation/overlap and budget-denominator summaries from existing measured outputs without refitting. Definitions and input hashes accompany `results/diagnostic_*.{csv,json}`; the checked interpretation is `notes/DIAGNOSTIC_SUMMARY.md`.
