# What Survives Prompt Search?

Research package for the autonomous investigation of benchmark reporting after
automatic prompt selection. The final paper is `paper.pdf`; its LaTeX entry point
is `paper/main.tex`. The official, unmodified ICML 2026 style is included. The body
must be at most eight pages; references and appendices are additional.

`research_artifact.tar.gz` is the compact submission package: paper and LaTeX,
all original research code, data selection, raw real-model answers, statistical
results, and logs. It excludes model weights and the virtual environment; pinned
downloads and installation commands below recreate those. Extract it and work in
its `research_artifact/` directory (the commands show `/work` as the original
project root). `CHECKSUMS.sha256` and `ARTIFACT_MANIFEST.json` verify the contents.

## What was run

- Newly generated answers from **Qwen2.5-0.5B-Instruct, Q8_0**, not precomputed
  external benchmark predictions. CPU-only llama.cpp with a four-core quota.
- Pinned MMLU-Pro test revision; a uniform seeded sample split into development
  and independent locked audit questions. Exact selected questions and all prompt
  variants are in `data/questions.json` and `data/candidates.json`.
- A frozen exhaustive prompt search, not an execution of DSPy/MIPRO.
- Controlled Bernoulli simulations, empirical-population replay with known
  correctness means, and a separate primary locked evaluation on unused items.
- Exact binomial intervals, simultaneous Bonferroni intervals, exact paired
  superiority tests, independent audits, call- and question-budget ablations,
  and duplicate-program accounting.

The distinction between finite empirical-population coverage and generalization
to fresh natural-language questions is essential. Replay repetitions are not
independent replications of model training or benchmark collection. See the paper
and `PROTOCOL.md`, including `PROTOCOL_AMENDMENTS.md`.

The budget ablations replay the model calls each protocol would require from a
fully acquired response matrix. They do not claim that the research collection
itself used only winner-only auditing. Actual full-matrix inference cost,
including the descriptive nonwinning audit candidates, is reported separately.

## Environment

Tested with Python 3.11 on Linux x86_64. Exact installed packages are in
`requirements-lock.txt`; host and quota information are in `logs/environment.json`.
System tools: a C/C++ compiler, git, LaTeX (`pdflatex`, `bibtex`), Times and Computer
Modern Type 1 fonts, and the packages required by the official ICML style.
On a normal Debian machine these are available through build-essential,
texlive-latex-extra, texlive-fonts-recommended, and cm-super. No root privileges
are needed by the Python scripts once dependencies exist.

```bash
cd /work
python3 -m venv .venv
.venv/bin/pip install -r requirements-lock.txt
```

Matplotlib renders paper figures with LaTeX and embedded Type 1 fonts; PyMuPDF
creates PNG previews without requiring `dvipng` or `pdftotext`. No external LLM
API key is needed. GPU use is zero. The visible 40-core host has a **four-core
container CPU quota**; use the quota, not `nproc`, when selecting thread counts.

## Reproduce analysis and PDF from supplied responses

```bash
cd /work
bash src/reproduce.sh > logs/reproduce.log 2>&1
```

This regenerates every statistical result, all figures/tables/scalar macros, and
the PDF using the cached real answers. The core checks use exact enumeration,
not arbitrary snapshots of computed answers. Detailed per-stage measured timings
are in `logs/analysis_runs.jsonl` and `logs/render_run.json` after the final run.
Expected CPU analysis and rendering time is minutes on four cores; inference is
not repeated by this command.

Do not run the inference program concurrently against the same response file.
It appends in deterministic submission order and resumes completed responses.
The audit-choice integrity file is required for real analysis.

## Recreate data and model inference from scratch

1. Download pinned public files:

   ```bash
   .venv/bin/python src/download.py
   ```

   The MMLU-Pro dataset revision is
   `b189ec765aa7ed75c8acfea42df31fdae71f97be`, file
   `data/test-00000-of-00001.parquet`. Dataset metadata: 12,032 test questions,
   70 validation questions. The validation split is not used. The model revision
   is `9217f5db79a29953eb74d5343926648285ec7e67`, official file
   `qwen2.5-0.5b-instruct-q8_0.gguf`. Download URLs and SHA-256 hashes are in
   `logs/download_manifest.json`. No authentication is required.

2. Build the exact inference backend and prepare the frozen grid:

   ```bash
   bash src/build_backend.sh
   .venv/bin/python src/infer.py --prepare-only
   ```

   Backend commit: `785322d17f2d51e5185cf996a1f4e46d87640841`.
   The native CPU build may use different instructions on another machine.

3. Start the server in one terminal:

   ```bash
   bash src/start_server.sh > logs/server.log 2>&1
   ```

   In another terminal, wait for local health to report `ok` and then run:

   ```bash
   curl --noproxy '*' http://127.0.0.1:8080/health
   .venv/bin/python src/infer.py > logs/inference.log 2>&1
   ```

   For an actual fresh rerun, first move the supplied `data/responses.jsonl` and
   `logs/locked_choice.json` to a separate backup location. Do not overwrite the
   supplied research evidence. With an existing response cache, inference simply
   resumes missing entries. Tiny numerical differences across hardware and
   batch schedules can change some greedy answers; statistical reproduction
   from the supplied cache is deterministic under the locked environment.

4. Run `bash src/reproduce.sh`.

`logs/inference_runs.jsonl` records completed run durations. `logs/compute.json`
records final measured wall span, retained prompt tokens, generated tokens,
process CPU usage, and peak resident memory. On this four-core quota, the pilot
achieved roughly 1.3 responses/second. The full retained inference spans **10.36
wall-clock hours**; the main server uses **36.34 CPU-hours** and peaks at **10.29
GiB resident memory**. Allow approximately **10--12 hours on comparable hardware**
for a complete inference rerun, plus dependency setup; runtime on other CPUs
will vary. The original task's GPU estimates do not apply to this CPU-only run.

## Seeds

| Purpose | Seed |
|---|---:|
| Uniform question permutation and greedy generation setting | 20261102 |
| Synthetic experiment | 77301 |
| Secondary heterogeneous-mean control | 77302 |
| Real replay, audits, and matched-budget experiments | 88302 |
| Budget-correct paired-superiority control | 88303 |
| Fixed nested candidate order | 5539 |
| Duplicate ablation resampled questions | 11003 |
| Duplicate ablation tie priorities | 22003 |

The real primary choice is smallest-ID on a tuning-score tie. Replays use
uniform tie breaking through independent continuous random priorities.
The definitive settings are executable in `src/analyze.py`.

## Every figure, table, and number

All paper outputs are rendered by **`src/render.py`**, which reads only generated
result files. It never manually inserts a result value. The LaTeX source inputs
generated scalar macros from `paper/generated/numbers.tex`.

| Paper artifact | Generated file | Statistical source/script |
|---|---|---|
| Synthetic search figure | `synthetic.pdf` | `results/synthetic.csv`, `analyze.py:synthetic` |
| Synthetic main table | `synthetic_table.tex` | Same |
| Real optimism/coverage figure | `real_replay.pdf` | `results/real_replay.csv`, `analyze.py:real` |
| Real main table | `real_table.tex` | Same |
| Gain and selected-quality figure | `gains_budget.pdf` | `real_replay.csv`, `call_budget.csv` |
| Matched-call budget table | `call_budget.tex` | `results/call_budget.csv`, `analyze.py:real` |
| Paired-superiority matched-budget appendix | `paired_call_budget.tex` | `results/paired_call_budget.csv`, `analyze.py:paired_call_budget` |
| All synthetic settings | `full_synthetic.tex` | `results/synthetic.csv` |
| Heterogeneous-mean secondary control | `heterogeneous.tex` | `results/heterogeneous.csv`, `analyze.py:heterogeneous` |
| All real replay settings | `full_real.tex` | `results/real_replay.csv` |
| Equal-question budget appendix | `question_budget.tex` | `results/budget.csv` |
| Duplicate-program appendix | `duplication.tex` | `results/duplication.csv` |
| Every real candidate | `candidates.tex` | `results/real_metadata.json` |
| Locked-audit and compute scalars | `numbers.tex`, `numbers.json` | `real_metadata.json`, `data/responses.jsonl` |

The table-to-script correspondence remains valid regardless of final LaTeX
float numbering. Raw synthetic per-repetition optimism is retained in
`results/synthetic_repetitions.json`; real replay identities and optimism in
`results/real_repetitions.npz`. Aggregate CSVs include MCSEs for every mean and
frequency, including metrics not placed in the paper. `data/correctness.npz`
is derived from responses, rather than an external prediction dataset.

## Failures, deviations, and uncompleted work

- `python` was not installed as a command; the environment uses `python3`.
- The first cmake configuration failed because the virtual environment's Ninja
  binary was not on PATH; adding `.venv/bin` resolved it.
- Local HTTP requests initially followed the global network proxy and were
  rejected (`blocked by time shielding`). This concerned requests to our own
  localhost inference server, not attempts to access prohibited literature.
  Local sessions now disable proxy inheritance. Errors are retained in
  `logs/inference_errors.jsonl`.
- Initial inference oversubscribed the four-core quota with 20 threads. The
  interrupted pilot retained valid completed outputs; the server was restarted
  with four threads. Restart attempts while the old server still held the port
  failed and were retried after termination. No result-based setting change was
  made. Retained responses include the completed pilot answers.
- `pdftotext` and `dvipng` are unavailable. Permitted PDFs were read with PyPDF;
  previews are generated with PyMuPDF.
- The first full LaTeX compilation failed because percent signs in a generated
  table header were not escaped. The rendering script now escapes them; the
  failure log is retained in `logs/finalize.log`. A later formatting check also
  caught the official style's missing-corresponding-author warning, which was
  corrected using its anonymous-author command. No experimental output changed.
- After results completed, paired Monte Carlo errors were added for the quality
  difference in the budget tables. This reports uncertainty for the same fixed
  experiments and does not change their random draws or existing metrics.
- Final validation caught that the winner-only budget supports accuracy but
  paired superiority additionally requires baseline audit answers. The original
  accuracy experiment and its table remain unchanged. Unbudgeted paired-test
  diagnostic columns were removed from that CSV. A separate, transparently
  labeled final-validation control uses K*t+2h=K*n and seed 88303 to budget both
  streams; its full settings are in amendment 5. No additional LLM inference
  was needed, and the original experiment's random draws did not change.
- Prospective budget terminology and the actual per-item option count are
  clarified in `PROTOCOL_AMENDMENTS.md` before locked-audit generation.
- Larger models, stochastic decoding replication, adaptive prompt generators,
  multistage optimizers, and distribution-shift evaluations were not run and
  are not presented as completed experiments.

## Source access and independence restriction

No scholarly or general web search was performed. We accessed only the supplied
starter references by their explicit arXiv IDs, the official ICML 2026 template
and author/call instructions, and official dataset/model/software sources.
`refs/SOURCE_ACCESS.md` records the consulted material. We did not attempt to
identify the excluded paper, its authors, or results. No accidental encounter
with known prohibited material occurred. The local-proxy startup rejection
described above was unrelated to literature access.

## Licenses and attribution

- MMLU-Pro: dataset card marks MIT; retained card in `refs/dataset_card.md`.
- Qwen2.5-0.5B-Instruct official weights/card: Apache-2.0; official repository
  license and downloaded model card are included in `refs/`.
- llama.cpp: MIT; backend source includes its license.
- ICML 2026 style files: official style distribution, included unmodified with
  its original notices. Template example prose is not used as research content.
- Original research scripts: MIT, see `LICENSE`.

This is an AI-agent-produced research artifact, not an actual submitted or
accepted conference paper. All empirical numbers come from executed programs.
