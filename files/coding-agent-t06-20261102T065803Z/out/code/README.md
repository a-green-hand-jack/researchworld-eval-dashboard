# Pairwise leaderboard stability: research artifact

交付物：论文 PDF 为 [`paper/main.pdf`](paper/main.pdf)，LaTeX 源文件为 [`paper/main.tex`](paper/main.tex)。完整代码、结果、数据版本与复现命令均在本目录。原始数据单独保存在 `data/raw/`，不进入提交压缩包。

The paper **Exact and Bounded Stability Audits for Pairwise Leaderboards** uses the **official NeurIPS 2026 main-track template**. It includes the completed official 16-question checklist, full proofs, supplementary measurements, and a disclosure of LLM assistance. The main text is within the official nine-page limit; `results/pdf_check.json` records the actual compiled count. This is a research artifact, not a claim of conference acceptance or submission.

The study compares real crowdsourced Arena preferences, MT-Bench expert/author judgments, MT-Bench GPT-4 judgments, and NBA regular-season outcomes. It analyzes reversal of recorded decisive outcomes at a fixed schedule, retaining ties as half outcomes. A graph maximum-principle argument supplies a lower bound; actual edited-data refits supply upper bounds. Equality establishes an exact minimum. The all-rival audit distinguishes loss of the original winner from reversal of the original top pair.

## Quick reproduction

Requirements: Linux CPU, Python **3.11.2** (another compatible Python 3.11 may work but is untested), `make`, and a TeX Live installation with `pdflatex`, `bibtex`, `latexmk`, and standard packages including `natbib`, `amsmath`, `amsthm`, `booktabs`, `microtype`, and `hyperref`. The observed TeX version is in `logs/latex_version.txt`.

```bash
cd /work                      # or the directory containing this README
make reproduce
```

`make reproduce` creates `.venv`, installs exact pinned dependencies from `requirements.txt`, downloads or verifies the four frozen raw files, runs the checks and experiments, regenerates all displays and numeric macros, and compiles `paper/main.pdf`. It does not fetch literature or access any leaderboard service. Downloads require network access but no accounts or API keys. It runs sequentially, with one BLAS thread. No GPU or paid service is used.

With dependencies and raw data already present, allow approximately **2–4 minutes** on a CPU similar to the observed Xeon Gold 6230; the actual measured stage times are in `results/run.json` and `results/winner_run.json`. Network and installation time are additional and variable. Main-process peak memory was below 0.4 GiB in the measured runs; 8 GiB is ample. Raw downloads total approximately 195 MiB. All results use seed **20261102**, 500 original-data bootstrap replicates, 500 random-flip permutations, and 100 matched human selections. Bootstrap and random-flip streams are separated using `SeedSequence([seed,panel_index,stream])`; the panel order is fixed in `src/data.py`.

The individual commands, after environment setup, are:

```bash
make setup
.venv/bin/python src/download.py
.venv/bin/python src/verify.py
.venv/bin/python src/experiment.py --bootstrap 500 --random 500 --matched 100
.venv/bin/python src/winner.py
.venv/bin/python src/audit.py
.venv/bin/python src/report.py
make paper
make package
```

`make paper` recompiles from existing generated measurements without repeating experiments. `make package` creates `submission.zip`, including the PDF, all LaTeX inputs, code, result files, documentation, relevant logs, data metadata, and a file-checksum manifest. It **excludes raw data, the Python environment, downloaded literature, and LaTeX build intermediates**.

The paper's fixed numerical prose assumes the published full configuration. Short exploratory runs can use smaller `--bootstrap`, `--random`, and `--matched` values, but must **not** be substituted into the paper without reviewing its numerical text. The main values in tables and generated macros update automatically; descriptive sentences must also be checked after changing the protocol.

## Data sources, versions, and transformations

`src/download.py` contains exact snapshot URLs and verifies SHA-256 before permitting analysis. `data/manifest.json` also records file sizes, licenses, and URLs. Files are deliberately kept under `data/raw/` and excluded from source/submission archives. Dataset cards and the NBA license are retained under `data/`.

| Local raw file | Public dataset and snapshot | SHA-256 | License |
|---|---|---|---|
| `arena.csv` | `lmarena-ai/arena-human-preference-55k`, commit `18c298340948c0e7f7727399fd459cca6ce0ca6f`, `train.csv` | `0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2` | Apache-2.0 |
| `mt_human.parquet` | `lmsys/mt_bench_human_judgments`, commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25`, human split | `4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769` | CC-BY-4.0 |
| `mt_gpt4.parquet` | same MT-Bench commit, GPT-4 pair split | `57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71` | CC-BY-4.0 |
| `nba.csv` | `fivethirtyeight/data`, commit `4c1ff5e3aef1816ae04af63218015066e186c147`, `nba-elo/nbaallelo.csv` | `d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc` | CC-BY-4.0 |

- Arena: all 57,477 records and all 64 observed model IDs; winner columns map to 1, 0, or 0.5. Conversation text is not used.
- MT-Bench: all 3,355 human judgments and 2,400 GPT-4 pair judgments; both `tie` and `tie (inconsistent)` map to 0.5. The 80 questions are bootstrap clusters. Human includes expert and author IDs; it is not an independent expert-only subset.
- NBA: `_iscopy=0`, `lg_id=NBA`, `is_playoffs=0`, season-ending years 2010–2015, each fitted separately. Team identifiers are season-specific. Outcomes come from `game_result`; archived Elo scores are not used. One 2013 scheduled game is absent from the recorded completed season, so the panel has 1,229 games; it is not imputed. The 2012 panel has 990 games.
- All loaders canonicalize participant order and complement outcomes when swapping it. Self-comparisons are excluded by a common guard. No participant is filtered for poor ranking, low exposure, or inconvenient results.
- Matched MT-Bench: intersect canonical keys `(question_id,turn,model_a,model_b)`, choose one human record per key, retain the unique GPT-4 record. There are 1,814 shared keys; human annotator selection is repeated under 100 fixed seeds. This is a control using existing data, not a fifth independent evaluation population.

## Code and result map

| File | Purpose |
|---|---|
| `src/bt.py` | Aggregated damped-Newton BT fitting; static, adaptive, incident, and deletion constructions; direct-transfer and curvature bounds |
| `src/data.py` | Frozen-panel preprocessing and matched schedules |
| `src/download.py` | Fixed-URL acquisition, SHA-256 checks, manifest |
| `src/experiment.py` | Main/adjacent-pair experiments, bootstrap, random noise, model controls, matched-annotator selections |
| `src/winner.py` | All-rival lower/upper bounds for any loss of the original leader |
| `src/verify.py` | Five numerical and exhaustive synthetic checks; synthetic fixtures are never study evidence |
| `src/audit.py` | Reconstruct and refit all stored main/winner edit witnesses; verify bounds and endpoint invariants |
| `src/report.py` | Every paper figure/table and generated result macro |
| `src/fill_checklist.py` | Fill official checklist, preserving questions and guidelines |
| `src/check_pdf.py` | Check main-text page count, 16 checklist answers, unchanged style, and compilation warnings |
| `src/package.py` | Build the data-free submission archive and checksum manifest |

The main outputs are:

- `summary.csv`: panel sizes, gaps, bootstrap summaries, bounds, all main construction counts, support, and fit diagnostics.
- `random.csv`: every Monte Carlo replicate at every budget, with pair reversal, winner loss, and normalized Kendall discordance.
- `bootstrap.csv`: every resampled fixed-pair gap and winner identity.
- `adjacent.csv`: all 83 adjacent-pair queries, lower and upper counts, direct capacities, and influence predictions.
- `paths.json`: all main edited row indices, exact-refit gap traces, mathematical bounds, and original rankings/scores. Row indices refer to each deterministically preprocessed panel.
- `winner.csv`, `winner_rivals.csv`, `winner_paths.json`: any-winner-loss bounds, all rival lower bounds, feasible constructions, and actual witnesses. A missing rival upper bound means no better construction was needed/found under the current cap, not proof that reversal is impossible.
- `ablations.csv`: regularization, tie-policy, and NBA home-effect controls, holding the original queried pair fixed.
- `matched.csv`: all 100 human-choice controls and the unchanged matched GPT-4 panel.
- `run.json`, `winner_run.json`, `verification.json`, `audit.json`, `pdf_check.json`: runtime, environment, and check outcomes.
- `data_diagnostics.json`: comparison-graph connectivity, observed pair counts, and participant-support ranges, regenerated by `audit.py`.

All listed result files are under `results/`.

## Provenance of every paper display

Every display is emitted by `src/report.py`; none is hand-entered. Tables are rendered from `paper/tables/*.tex`, figures from `paper/figures/*.pdf`, and result macros from `paper/numbers.tex`.

| Display in manuscript | Generated asset | Measurement input | Experiment producer |
|---|---|---|---|
| Table 1, real-data panels | `tables/data.tex` | `summary.csv` | `experiment.py` |
| Table 2, certified thresholds | `tables/thresholds.tex` | `summary.csv`, `winner.csv` | `experiment.py`, `winner.py` |
| Table 3, matched schedules | `tables/matched.tex` | `summary.csv` | `experiment.py` |
| Figure 1, random noise | `figures/random.pdf` | `random.csv` | `experiment.py` |
| Figure 2, budget denominators | `figures/normalization.pdf` | `summary.csv` | `experiment.py` |
| Table 4, methods and capacities | `tables/methods.tex` | `summary.csv` | `experiment.py` |
| Table 5, random-noise detail | `tables/random.tex` | `random.csv` | `experiment.py` |
| Table 6, model controls | `tables/ablations.tex` | `ablations.csv` | `experiment.py` |
| Tables 7–17, all adjacent pairs | `tables/adjacent_*.tex` | `adjacent.csv` | `experiment.py` |
| Figure 3, influence/refit comparison | `figures/influence.pdf` | `adjacent.csv` | `experiment.py` |

Wilson intervals are conditional Monte Carlo intervals; bootstrap percentile intervals describe resampling of the original fixed pair, without selection adjustment. Construction counts are deterministic for the finite panel and have no artificial standard errors. The frozen two-bootstrap-SD reversal endpoint is **not** a post-edit confidence claim. Counts for deletion and tie dropping describe different operations/estimands. Read the paper's limitations before interpreting cross-design comparisons.

## Independent-research boundary and disclosure

No general web or scholarly search was used, and no attempt was made to identify the prohibited paper. Only five explicitly permitted starting papers were directly downloaded, along with named dataset documentation and official NeurIPS pages. No citation links were followed. No known prohibited material was encountered. See `logs/access_log.md` for exact sources/reading scope and `logs/research_log.md` for preliminary runs, access failures, modeling choices, and abandoned approaches.

An OpenAI Codex assistant developed the methods and code, performed the analysis, and drafted the paper. It did not generate or fabricate the experimental judgments. This artifact makes no claim of independent human authorship, peer review, or institution/IRB approval. No live system was modified and no messages were sent to participants. The literature PDFs remain outside the submission archive.

The official template comes from the 2026 call's linked [formatting ZIP](https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip). The original files are in `paper/vendor/`; `paper/neurips_2026.sty` is byte-identical to the vendor copy. The selected mode is anonymous main-track submission style; no claim of acceptance is implied. Code licensing and third-party attribution are in `LICENSE` and `THIRD_PARTY.md`.
