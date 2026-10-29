# Flip budgets of pairwise-comparison (Bradley–Terry) leaderboards — code & reproduction

Paper: `paper/main.tex` → `paper/main.pdf` (ICML 2026 template, anonymous-submission mode; style files copied from the official
`icml2026.zip`, https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip; NeurIPS 2026 template was not yet online; ICML 2026 is the latest edition available).
Main text ends on page 6 (limit 8); references, appendix (A–G) and the self-filled checklist follow.

## Layout
```
code/       all Python (see table below)         data/      raw data (NOT part of the code deliverable; created by the commands below)
results/    CSV/JSON outputs + generated LaTeX table bodies (tab_*.tex)      figures/   PDF figures used in the paper
paper/      LaTeX source, bib, style files        run_all.sh  end-to-end script      requirements.txt  pinned versions
```
Environment: Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.1.0, matplotlib 3.11.2, pyarrow 26.0.0 (`python3 -m venv venv && venv/bin/pip install -r requirements.txt`).
LaTeX: TeX Live pdflatex + latexmk (no other tools).

## Data (all under `data/`; versions are fixed commits)
| dir | source | version | check |
|---|---|---|---|
| `data/arena55k/train.csv` | HF `lmarena-ai/arena-human-preference-55k` | commit `18c298340948c0e7f7727399fd459cca6ce0ca6f` | sha256 `0692154a…5be2` (verified) |
| `data/arena140k/train-0000{0..6}-of-00007.parquet` + cache `data/arena140k_small.parquet` (3 columns, built by `loaders.arena140k`) | HF `lmarena-ai/arena-human-preference-140k` | commit `6322995ab34d7c2693e3f47dd13fa5caa0789a74` | file sizes match the HF listing (no whole-dataset checksum was given; per-file LFS oids match: 7b871a96…, 0cd29a6e…, c633264f…, 5bcf04c9…, 2c50b4b3…, de59f74d…, 1a32a1c6…) |
| `data/mtbench/{human,gpt4_pair}.parquet` | HF `lmsys/mt_bench_human_judgments` | commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25` | human sha256 `4877bc46…5769` (verified); gpt4_pair sha256 `57068327…0e71` (verified) |
| `data/judges/train.single-turn.json`, `Meta-Llama-3-70B-Instruct.jsonl`, `Qwen2-72B-Instruct.jsonl`, `Mistral-7B-Instruct-v0.2.jsonl` (from `llm-judges-prob-avg/`) | HF `potsawee/chatbot-arena-llm-judges` | commit `638a7e3be3078e55d2eb0b789d34749747822c49` | train.single-turn.json sha256 `6ed8793f…c8f3` (verified). No license on the page; derived from the Kaggle LMSYS competition data. |
| `data/nba/nbaallelo.csv` | github `fivethirtyeight/data`, `nba-elo/` | commit `4c1ff5e3aef1816ae04af63218015066e186c147` | sha256 `d46ed354…16bc` (verified) |

Download commands (what I ran; `R` = commit above):
```
curl -sL -o data/arena55k/train.csv https://huggingface.co/datasets/lmarena-ai/arena-human-preference-55k/resolve/$R/train.csv
curl -sL -o data/nba/nbaallelo.csv https://raw.githubusercontent.com/fivethirtyeight/data/4c1ff5e3aef1816ae04af63218015066e186c147/nba-elo/nbaallelo.csv
curl -sL -o data/mtbench/human.parquet      https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/$R/data/human-00000-of-00001-25f4910818759289.parquet
curl -sL -o data/mtbench/gpt4_pair.parquet  https://huggingface.co/datasets/lmsys/mt_bench_human_judgments/resolve/$R/data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet
curl -sL -o data/judges/train.single-turn.json https://huggingface.co/datasets/potsawee/chatbot-arena-llm-judges/resolve/$R/train.single-turn.json
curl -sL -o data/judges/<judge>.jsonl https://huggingface.co/datasets/potsawee/chatbot-arena-llm-judges/resolve/$R/llm-judges-prob-avg/<judge>.jsonl
curl -sL -o data/arena140k/train-0000i-of-00007.parquet https://huggingface.co/datasets/lmarena-ai/arena-human-preference-140k/resolve/$R/data/train-0000i-of-00007.parquet   # i = 0..6
```
Not used: WebDev Arena (license agreement required). Raw data are never copied into `code/`, `paper/` or `results/`.

## Run
`./run_all.sh` (≈40 min wall-clock with 12 worker processes on a 40-core machine, ≲ 4 CPU-hours; I did not time a 4-core run — expect roughly 3× longer wall-clock; `Pool(12)` is set in `run_attack.py`, `run_scaling.py`, `Pool(10)` in `run_noise.py`).
Seeds: every stochastic task uses `numpy.random.default_rng(20261028 + crc32(task name) % 100000)` (`run_attack.seed_for`); `analyze.py` uses seed 7 for its bootstraps; `run_cluster.py` uses 20261029; `tests.py` uses seed 0. All outputs are deterministic given the seeds.

## Which script produces what
| output in paper | script → file |
|---|---|
| Table 1 (datasets) | `dataset_stats.py` → `results/dataset_stats.csv`; `analyze.py` → `results/tab_datasets.tex` |
| Table 2 (flip budgets, c), Fig. 1 (collapse), regression & held-out test (Sec. 4.2), top-1/top-K, ablations, z-matched, c vs z-cutoff, slopes | `run_attack.py` → `results/attack_all.csv`; `run_scaling.py` (bootstrap datasets) → `results/scaling_all.csv`, `scaling_140k.csv`; `analyze.py` → `results/tab_main.tex`, `tab_topk.tex`, `tab_ablation.tex`, `tab_zmatched.tex`, `tab_slopes.tex`, `tab_czmin.tex`, `figures/fig_collapse.pdf`, `results/summary.json` |
| Table 3 (random noise), Fig. 2 (random vs adversarial) | `run_noise.py` → `results/noise_all.csv`, `noise_140k.csv`; `analyze.py` → `results/tab_noise.tex`, `figures/fig_random_vs_adv.pdf` |
| Fig. 3 (dependence on N), top-1 bootstrap intervals | `run_scaling.py` → `results/scaling_all.csv`; `analyze.py` → `figures/fig_scaling.pdf` |
| Tie-discarding table (App. D.6) | `run_attack.py … noties` → `results/attack_noties.csv`; `analyze.py` → `results/tab_noties.tex` |
| Cluster-bootstrap numbers (Sec. 4.5) | `run_cluster.py` → `results/cluster_check.csv`; `analyze.py` → `results/summary.json["cluster"]` |
| Appendix C validation (solver vs L-BFGS, brute force, first-order accuracy) | `tests.py` → `results/validation.json` |
| Search ablation numbers (α, one-shot, target-only injection) | columns of `attack_all.csv`; `analyze.py` → `summary.json["search_ablation"]` |
Library: `bt.py` (BT fit on aggregated cell counts, influence, greedy/one-shot/direct search, random perturbations), `loaders.py`, `boards.py` (leaderboard registry).
Numbers quoted in the paper text were copied by hand from `results/summary.json` and `results/tab_*.tex`; if you re-run, compare against those.

## Deviations, abandoned work, limitations (all also in the paper's Appendix F)
* First regression used a `k ≥ 5` selection (biased, truncation); replaced by selection on `z ≥ 1`. First draft of c used all pairs (integer-floor bias).
* Not done: WebDev Arena, Rao–Kupper/Davidson tie models, style control, lower bounds on the budgets, GPT-4 as judge on Arena battles, 4-core timing.
* `tests.py` brute force uses only 12 tiny synthetic instances.
* The Arena-140k data loader treats `both_bad` as a tie (my choice).
* Output of `analyze.py` is printed to `results/analyze.log`; PNG copies of the figures are written to `/work/tmp/` for visual checking only.

## Disclosures
* **LLM assistance:** the code, analysis and manuscript were produced by an LLM agent (Claude Sonnet 5.5 via Claude Code) working autonomously; no numbers were produced by the LLM itself — all come from the scripts above.
* **Restricted-content statement.** The task states that one published paper studies this research question and must not be searched for or read. I did not search for it or its title/authors/results. Item 8 of `starter_literature.md` ("Dropping Just a Handful of Preferences…", 2025) was **not opened, read or cited** (to stay on the safe side, since I could not tell whether it is the restricted paper). My literature searches (tool: scholarly search over titles/abstract snippets) were: "A Statistical Framework for Ranking LLM-Based Chatbots"; "adversarial attacks data poisoning ranking from pairwise comparisons Bradley-Terry" (result titles seen included RLHFPoison, Policy Teaching via Data Poisoning in Learning from Human Preferences, Modifying Bradley–Terry and other ranking models to allow ties, Improving Your Model Ranking on Chatbot Arena by Vote Rigging, Sequential Manipulation Against Rank Aggregation, plus unrelated items); "MM algorithms for generalized Bradley-Terry models"; "A Swiss Army Infinitesimal Jackknife"; and a second query for "Sequential Manipulation Against Rank Aggregation" (service error). None of the results looked like a paper on dropping/flipping few comparisons to change LLM leaderboard ranks; I read only titles and snippets, nothing else was encountered. Starter-list papers 2–7 were cited from my background knowledge and the abstracts shown by the search tool; I did not re-read them in full during this task (their descriptions in the paper are kept to what the starter-list summaries and abstracts say).
