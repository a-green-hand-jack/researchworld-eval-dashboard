# Selecting whole benchmarks to predict unmeasured scores

Read [the paper](report.pdf). It is a public research report in the unchanged official ICML 2026 preprint format, with an eight-page main-text limit, references, Impact Statement and appendices in one PDF. It is not a conference acceptance or submission.

The study selects whole benchmark columns from incomplete historical score matrices and predicts held-out models' remaining scores. Primary evidence concerns English-labelled/involving embedding tasks in MTEB; Open LLM Leaderboard is a separate six-benchmark generative-model supplement. All results are exploratory and conditional on availability-selected cohorts. Bootstrap intervals are descriptive model-resampling intervals, not population or per-prediction guarantees. Negative controls and superseded runs are retained.

## Build the paper

Use GNU Make 4.4.1 and TeX Live with `latexmk`, `pdflatex`, BibTeX, the usual LaTeX packages and Times fonts. The official style and bibliography files are included under `venue/templates/`. From this delivery root:

```sh
make paper
make check
```

For `make check`, install `pymupdf==1.28.2` (also included in the presentation requirements). This builds `paper/main.tex` and copies `paper/main.pdf` to `report.pdf`. Sources are `paper/body.tex` and `paper/appendix.tex`; checked citations are supplied under `context/`. `make check` uses PyMuPDF to check source references, internal PDF links and the eight-page main-text boundary; it does not refit models or replace scientific review. Venue provenance and requirements are in [venue/REQUIREMENTS.md](venue/REQUIREMENTS.md).

## Reproduce numerical results

The tested minimal analysis dependencies are in `analysis/requirements.txt`; `analysis/requirements.lock` archives the full original environment, including unused packages, and is not the installation target. The run environment used Python 3.11, CPU only, one BLAS/OMP thread. Use an isolated Python environment. No GPU, paid API or model execution is needed. From the delivery root:

```sh
python3 -m pip install -r analysis/requirements.txt
cd analysis
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/reproduce.py
```

This acquires only the task-supplied pinned MTEB GitHub and Open LLM Hugging Face snapshots, prepares cohorts and regenerates the full numerical evidence. Exact source URLs, commit identifiers, byte counts, SHA-256 hashes and measurement paths are in `analysis/data/`; cohort rules, train/validation/test names, query orders and per-model losses are in `analysis/results/`. See [analysis/README.md](analysis/README.md) and [analysis/notes/PROTOCOL.md](analysis/notes/PROTOCOL.md).

To use the committed processed score matrices without downloading sources, run from `analysis/`:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python3 scripts/reproduce.py --prepared
```

`make analysis` runs this prepared-data command. The corrected full experiment loop measured 168.067 wall seconds, excluding download, 72.83-second MTEB parsing, fixed-target diagnostics and aggregation. Download time varies; the original pinned archive download was about 82 seconds. These are measured component timings, not an end-to-end promise. The parser streams the source archive rather than extracting it. Full experiment and correction logs are in `analysis/notes/RUN_LOG.md`; original/source data and intermediates were reported below 0.5 GB by the analysis owner. Keep the task's total storage limit of 5 GB when retaining downloads and reruns.

Seeds: random model partitions 0–9; eight random query orders per partition with seed `100*s + draw`; additional masks `200+s`; fixed targets `500+s`; 4,000 unique-model bootstrap resamples with seed 20261102; Gaussian identity check seed 913. Provider splits record deterministic retry seeds. Submission chronology is a single partition.

## Regenerate every figure and table

From the delivery root:

```sh
python3 -m pip install -r presentation/requirements.txt
python3 presentation/generate.py
make paper
```

The default presentation generator verifies and uses the included hashed snapshots of corrected analysis summaries. After a new analysis run, explicitly regenerate from its results:

```sh
python3 presentation/generate.py --results analysis/results
make paper
```

Verify that the intended analysis revision/inputs match before comparing an altered run. All three plot PDFs and nine numerical table fragments come from `presentation/generate.py`; [presentation/README.md](presentation/README.md) maps every asset to its numerical source, and `presentation/source_manifest.json` and `presentation/diagnostic_source_manifest.json` record provenance. The manuscript's artifact-map table is typeset directly from `paper/appendix.tex`. Preview generation takes about ten seconds according to the presentation owner's measured run; no external artwork is used.

## Evidence and access boundary

The main data snapshots are MTEB `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383` and Open LLM `9c09a7cae43334062a82cb164f2ef255013dafa2`. Model licenses do not establish a dataset license: the supplied Open LLM dataset license is undeclared. No new license is asserted for that source.

The research objective explicitly excludes an existing related study and pages discussing it. Contributing owners used only permitted starter literature, task-listed data and official venue instructions, without attempting to identify the excluded work. No prohibited encounter was identified. Checked paper versions, consulted locations, hashes and access records accompany `context/`; venue-source checks accompany `venue/`. The permitted-source review supports bounded positioning, not an exhaustive novelty claim.

The division of responsibilities is in `plan/STUDY_PLAN.md` and `.forgejo/CODEOWNERS`. A research version is published only after independent review of its exact proposed revision.
