# How Many Votes Move a Leaderboard? — code and reproduction

Paper: `paper/main.pdf` (LaTeX source `paper/main.tex`, NeurIPS 2026 template, checklist in
`paper/checklist_filled.tex`). This README covers the environment, data provenance, the commands
that rebuild every number, table and figure, and the expected run times.

## Environment
* CPU only. Developed on Linux with a 4-core CPU quota and Python 3.11.2.
* `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt`
  (numpy 2.4.6, scipy 1.17.1, pandas 3.1.0, pyarrow 26.0.0, matplotlib 3.11.2; pymupdf/pypdf are
  used only to inspect the PDF).
* LaTeX: `pdflatex` + `latexmk` (TeX Live), `natbib`/`plainnat`.

## Data (public, fixed snapshots; not included in this repository)
`./get_data.sh` downloads everything into `data/` (about 2 GB) and checks the files against `SHA256SUMS`.

| Data | Source | Version | License |
|---|---|---|---|
| Chatbot Arena 55k | HF `lmarena-ai/arena-human-preference-55k` `train.csv` | commit 18c298340948c0e7f7727399fd459cca6ce0ca6f | Apache-2.0 |
| Chatbot Arena 140k | HF `lmarena-ai/arena-human-preference-140k` (7 parquet files; only `model_a`, `model_b`, `winner` are read) | commit 6322995ab34d7c2693e3f47dd13fa5caa0789a74 | CC-BY-4.0 |
| WebDev Arena 10k | HF `lmarena-ai/webdev-arena-preference-10k` | commit 7c397e652ffb8c2384e6d71d21d8388c19365fdc | dataset license (see HF page) |
| MT-Bench human & GPT-4 pair judgments | HF `lmsys/mt_bench_human_judgments` | commit f7d2896d2cc5d80f8b55c2bbc722613555233c25 | CC-BY-4.0 |
| LLM judges on Arena battles | HF `potsawee/chatbot-arena-llm-judges` (`train.single-turn.json`, 5 judges × {original, reversed}) | commit 638a7e3be3078e55d2eb0b789d34749747822c49 | **no license stated** (derived from the Kaggle LMSYS Arena data; flagged in the paper) |
| NBA game results | FiveThirtyEight `nba-elo/nbaallelo.csv` | commit 4c1ff5e3aef1816ae04af63218015066e186c147 | CC-BY-4.0 |

The checksums of the given files match the values in the task's `data.md` (55k `train.csv`, MT-Bench
human parquet, NBA csv). Preprocessing is in `code/data_prep.py`. Competitors with fewer than 50
comparisons are removed iteratively. Ties, and "both bad" in the 140k data, count as half-wins.
LLM-judge verdicts are the argmax of the judge's outcome probabilities averaged over both presentation
orders. NBA uses regular-season NBA games only, with one row per game (`_iscopy==0`), and drops
seasons with more than 20% neutral-site games.

## Running
```
./get_data.sh        # once
./run_all.sh         # ~30 min on 4 cores; NPROC=<k> sets worker processes (default 4)
```
Measured wall-clock times on 4 cores: run_pairs about 4 min, bootstrap_k about 16 min, everything else
1–2 min each.

## Which script produces what
| Paper item | Script → output |
|---|---|
| Table 1 (datasets) | `analysis_tables.py` → `paper/tables/datasets.tex` (from `derived/meta.json`) |
| Table 2 (top-1 fragility, bootstrap CI) | `run_pairs.py`, `pair_influence.py`, `bootstrap_k.py` → `analysis_tables.py` → `tables/main.tex` |
| Fig. 1, Table 3 (law) | `run_pairs.py`, `pair_influence.py` → `analysis_law.py` → `figs/fig_law.pdf`, `tables/law.tex`, `results/law_summary.json` |
| Table 4 top (same battles, judges) | `run_pairs.py` → `analysis_tables.py` → `tables/judges.tex` |
| Table 4 bottom (same 6 models, equal N) | `matched_mt6.py`, `bootstrap_k.py` → `tables/mt6.tex` |
| Fig. 2 (random vs worst case) | `random_noise.py` → `figs/fig_random.pdf` |
| Table 5 (constrained attackers) | `realistic_attack.py` → `tables/attack.tex` |
| Table 6 (relaxation check, App. B) | `relaxation_check.py` → `tables/relax.tex` |
| Table 7 (ties, App. C) | `run_pairs.py` (tie-removed variants `*__noties`) → `tables/ties.tex` |
| Fig. 3 (subsampling, App. D) | `subsample.py` → `figs/fig_subsample.pdf` |
| In-text numbers | `results/numbers.json`, `results/law_summary.json`, `results/composition.json` |

Core library: `code/bt.py` provides the BT fit on aggregated cells, influence quantities, the
iterated-greedy drop/flip/inject search with exact refit verification, and the one-shot AMIP ordering.
`code/common.py` holds shared helpers.

## Randomness
All randomness uses `numpy.random.default_rng` with seeds derived deterministically from the dataset
name and the replicate index (`zlib.crc32(name)` plus the replicate). The worst-case searches themselves
are deterministic. Replicates: 100 bootstrap resamples, 200 random-noise replicates per rate, 20 attack
sequences, 10 subsamples per size, 100 equal-N subsamples, and 500 board-cluster bootstrap resamples
for the law CIs. The full pipeline was re-run end-to-end from scratch (`results/logs/run_all.log`). All tables
were reproduced except two small differences caused by row-order-dependent tie-breaking in the analysis:
the NBA median z in Table 2 (0.66 → 0.64) and some cluster-bootstrap CI endpoints in Table 3 (by at
most 0.01). The analysis now sorts rows deterministically, and the paper reports the post-fix values.

## Notes on honesty / scope
* Every reported k* is a refit-verified upper bound. All 12,456 searches were verified.
* The relaxation check (App. B) shows that the greedy search can overestimate k* by up to 23% for
  well-separated pairs. This is reported in the paper.
* Not done: Elo (online) ratings, style-controlled BT, and platform defences. These are listed as
  limitations.
* LLM use: this whole project (design, code, runs, writing) was carried out autonomously by an AI
  agent based on a Claude model. This is disclosed in the paper (App. A and checklist).

## Restricted-content statement
The task forbade accessing one specific published paper on this research question, and any page that
cites or discusses it. I did not search for it, and I did not knowingly encounter it or any page that
discusses it. The only literature pages opened were the arXiv abstract pages of starter-literature items
(Huang et al. 2025 v1, Broderick et al. 2020, Min et al. 2025, Singh et al. 2025, Chiang et al. 2024,
Zheng et al. 2023), the NeurIPS 2026 call for papers and style files, and Crossref/Project Euclid metadata
for Hunter (2004), Efron (1979) and Bradley & Terry (1952). No general literature search was performed.
