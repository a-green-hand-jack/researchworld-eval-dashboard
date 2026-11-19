# Stability of Bradley-Terry leaderboards under edits to the comparison data

Code, results and paper (NeurIPS 2026 template) for *How Many Comparisons Does It Take to Flip a Leaderboard?*

## Layout
- `code/` analysis code (`bt.py` BT fit + greedy adversary, `data.py` loaders, `common.py`, `run_*.py` experiments, `analyze.py` tables/figures, `make_checklist.py`)
- `data/` raw data (NOT part of the release; created by `code/download_data.sh`)
- `results/` CSV outputs of the experiments, `summary.json` (all numbers quoted in the paper), `preview/` PNG copies of the figures
- `paper/` `main.tex` (+ `references.bib`, `neurips_2026.sty`, generated `tables/`, `figures/`, `checklist.tex`), `main.pdf`

## Environment
Python 3.11.15, numpy 2.4.6, pandas 3.0.6, matplotlib 3.11.2, pyarrow 26.0.0 (`pip install -r code/requirements.txt`);
TeX Live `pdflatex`/`bibtex` for the paper. CPU only; 8 GB RAM is enough. Style file: official `neurips_2026.sty`
(downloaded from the NeurIPS 2026 call-for-papers page, `Formatting_Instructions_For_NeurIPS_2026.zip`).

## Data (all public; versions fixed)
| key | source | version | license | sha256 (verified) |
|---|---|---|---|---|
| Arena 55k | HF `lmarena-ai/arena-human-preference-55k` `train.csv` | commit `18c298340948c0e7f7727399fd459cca6ce0ca6f` | apache-2.0 | `0692154a...5be2` |
| MT-Bench human | HF `lmsys/mt_bench_human_judgments` `human-*.parquet` | commit `f7d2896d2cc5d80f8b55c2bbc722613555233c25` | cc-by-4.0 | `4877bc46...5769` |
| MT-Bench GPT-4 judge | same repo, `gpt4_pair-*.parquet` | same commit | cc-by-4.0 | `57068327...0e71` |
| NBA Elo | github `fivethirtyeight/data` `nba-elo/nbaallelo.csv` | commit `4c1ff5e3aef1816ae04af63218015066e186c147` | CC-BY-4.0 | `d46ed354...16bc` |

Not used: Arena 140k, the LLM-judge Arena set, WebDev Arena. No account was needed.
`bash code/download_data.sh` downloads and verifies the checksums.

## Reproduce everything
```
pip install -r code/requirements.txt
bash code/download_data.sh
bash code/run_all.sh            # ~4.5 min wall-clock on a 40-core machine using 20 workers (measured)
```
All randomness is seeded inside the scripts (seeds: `run_pairs.py` 20261102, `run_rankshift_scaling.py` 7, `run_noise.py` 11,
`run_robust.py` 5, `run_matched_sub.py` 99, `analyze.py` 2026); results were re-generated bit-identically in a second
full run (see "Verification" below). Multiprocessing pools use up to 20 workers; set `OMP_NUM_THREADS=1`.

## Which script produces what
| paper item | script | output |
|---|---|---|
| Table 1 (boards) | `run_pairs.py` -> `analyze.py` | `paper/tables/overview.tex` |
| Table 2 (fragility), Table 3 (leader) | `run_pairs.py` -> `analyze.py` | `tables/fragility.tex`, `tables/leader.tex` |
| Fig. 1, Table 4 ($\kappa$), appendix table ($c$) | `run_pairs.py` -> `analyze.py` | `figures/fig_law.pdf`, `tables/kappa.tex`, `tables/law.tex` |
| Fig. 3 left (rank displacement) | `run_rankshift_scaling.py` -> `analyze.py` | `figures/fig_rankshift.pdf` |
| Fig. 3 right (random vs targeted) | `run_noise.py` (+ `run_pairs.py`) -> `analyze.py` | `figures/fig_noise.pdf` |
| Fig. 4 (Arena subsampling) | `run_rankshift_scaling.py` -> `analyze.py` | `figures/fig_subsample.pdf` |
| Table 5 (matched control) | `run_rankshift_scaling.py`, `run_matched_sub.py` -> `analyze.py` | `tables/matched.tex` |
| Validity checks, appendix B | `run_robust.py` -> `analyze.py` | `results/robust_*.csv`, `summary.json` |
| NeurIPS checklist | `make_checklist.py` | `paper/checklist.tex` |

Every number in the text of `paper/main.tex` is taken from `results/summary.json` or the generated tables; where the text
quotes a number that is not in a generated table it comes from `summary.json` (keys named after the quantity).

## Method in one paragraph
BT with ties as half-wins (ridge 1e-3, Newton on pair-aggregated counts). For an adjacent pair (i, j) a chunked greedy
adversary ranks (pair, outcome) cells by the first-order change of theta_i - theta_j (`v = H^-1 (e_i - e_j)`), applies a chunk
of edits (remove / relabel / insert), refits exactly, and stops when the order flips; chunk size shrinks to 1 near the flip.
Budgets are upper bounds on the true minimum (checked against exhaustive search on tiny instances, `run_robust.py`).

## Honest notes / deviations
- Starter-list item 8 (a paper on dropping preferences from LLM leaderboard data) was **not retrieved, opened or read**, to keep
  the study independent of previously published work on this question; nothing from the restricted categories was encountered
  during the work. Because it was not read, it is not cited and no priority claim relative to it is made.
- Literature actually consulted: arXiv API abstracts of 2403.04132, 2306.05685, 1703.04730, 2011.14999, 2501.17858, 2504.20879
  (saved in `data/lit/`). Bradley & Terry (1952) is cited from the task's reading list without being re-read.
- The proportionality `f ~ kappa * gap` was found post hoc on the main pair table (see paper Sec. 4); it is a descriptive
  regularity, not a pre-registered hypothesis. The Arena subsample series reuses the same votes.
- The adversary is heuristic (greedy); numbers are upper bounds. Exhaustive validation covers only 3-contestant toy instances.
- An AI assistant (Claude) planned the study, wrote code and drafted the text, as disclosed in the paper.
- `paper/main.tex` uses the NeurIPS 2026 default (anonymous) mode; main text is 7 pages (limit 9) plus references,
  appendix and the filled checklist.
