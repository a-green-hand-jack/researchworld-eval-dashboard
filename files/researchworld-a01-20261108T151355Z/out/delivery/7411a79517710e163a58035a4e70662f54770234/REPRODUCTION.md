# Reproduction notes

This file describes how to rebuild the paper and every number in it from the public data. Every claim in the paper is backed by a result file under `code/results/`; analyses that were not run are listed in Section 6 of the paper (Discussion and Limitations) and nowhere else.

## 1. Layout of this repository
- `paper/` LaTeX source (`main.tex`, `sections/`, `refs.bib`, NeurIPS 2026 style file, checklist); `paper.pdf` is the build of `paper/main.tex` (`cd paper && latexmk -pdf main.tex`, pdflatex, TeX Live in the sandbox).
- `code/` analysis code, tests, result files and data manifest (delivered by the analysis position).
- `figures/` figure/table scripts and outputs (delivered by the presentation position).
- `venue/` the venue's format rules, template provenance and the format checker (`venue/tools/check_venue.py paper.pdf paper/main.aux`; `paper/main.aux` is not shipped, it is written by the build `cd paper && latexmk -pdf main.tex`, which must be run first).
- `.forgejo/` holds the hosting platform's review configuration; it is not part of the paper or of the anonymous supplement.

## 2. Data (public, no account) — versions and checksums
| source | version used | checksum / size | licence status |
|---|---|---|---|
| HELM MMLU release summaries, `https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (per-subject tables `groups/json/mmlu_mmlu_subject:*.json`, metric `EM`) | release v1.13.0 (`summary.json` date 2025-01-10), 57 subjects x 79 models | manifest SHA-256 `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` (`code/data/processed/manifest.json`) | no data licence declared; code Apache-2.0 |
| Open LLM Leaderboard `contents`, `data/train-00000-of-00001.parquet` | dataset commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (last updated 2025-03-20); 4576 rows, 79 duplicate `fullname` rows dropped (best-scoring kept), 4497 models | file SHA-256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` (1,109,997 bytes) | no licence field on the card; per-model `Hub License` column |
| Open LLM Leaderboard `results`, per-model JSON | commit `aa81ecc38fdc5708254b833923368970efdf5ef5` (2025-03-15) | not used: the analysis does not use sub-task scores (listed because the task's starter material names it) | none declared |

**Licence judgement.** No licence is declared for the HELM score tables or the Open LLM Leaderboard tables (checked 2026-11-08: GitHub licence API reports Apache-2.0 for the HELM *code* only; the `contents` dataset card has no licence field; `results` has no card). We use them as public evaluation results under common research practice, record source, commit and checksum, redistribute only derived numbers and scripts (not the raw downloads or a mirror), and do not use model weights. The per-model `Hub License` column licenses the models, not the score rows. Anyone reusing the data should check the sources' current terms. This is our judgement, not legal advice. The optional `cais/mmlu` (MIT) is not used.

## 3. Environment
Python 3.11.2 on Linux (x86-64, glibc 2.36); numpy 2.4.6, scipy 1.17.1 (HiGHS MILP via `scipy.optimize.milp`), pandas 3.0.6, pyarrow 26.0.0, pytest 9.2.0: `code/environment.txt` (the pins of the analysis). Figures: matplotlib 3.11.2. Paper: TeX Live (pdfTeX, latexmk, BibTeX), `paper/neurips_2026.sty` unmodified. CPU only; no GPU, no training of any model, no paid API. Each analysis job is single-threaded.

## 4. Commands, seeds, measured run time
Setup and data (needs network, no account): `cd code && ./get_data.sh [RAWDIR]` downloads the three pinned raw sources (Open LLM Leaderboard `contents` parquet at commit `9c09a7ca…`, one pinned lm-eval results file for the item counts of the noise model, the 303 HELM MMLU v1.13.0 release files), checks each raw file against `code/data/raw_checksums.sha256`, rebuilds `code/data/processed` with `src/build_data.py` and `src/ollb_items.py`, and checks the rebuilt tables against `code/data/processed/CHECKSUMS.sha256` (they are byte-identical to the shipped ones). Tests: `cd code && python3 -m pytest tests` (needs `code/environment.txt`; `pytest` is pinned there). Result files: `cd code && ./run_all.sh JOB` for each job in `code/results/README.md` (file -> job table; see the comments at the top of `code/run_all.sh`). Summaries: `python3 code/src/analyze.py`; checksums and run times: `python3 code/src/provenance.py`. Figures and tables: `figures/make_all.sh code/results`. Numbers quoted in the paper text: `cd paper && python3 -I make_numbers.py` (writes `paper/gen/numbers.tex`, `paper/gen/tab_c4.tex`, `paper/gen/tab_slices.tex` from `code/results/summary/*.csv`). Paper: `cd paper && latexmk -pdf main.tex`.

Empirical-gain pairs: a pair is an Open LLM Leaderboard model whose user-entered `Base Model` field names another unflagged model of the leaderboard (540 pairs; `code/results/empirical_gains.csv`); the field was not audited (composition of the pairs, placeholder entries and the restricted subset of 239 pairs: `code/results/pairs_composition.csv`, `base_model_metadata.csv`, `emp_caps_restricted.csv`).

Seeds: every driver defaults to seed 0 and writes it to the `seed` column of its result file (rank-stratified target sample, bootstrap B = 1000 with seed 0, Monte-Carlo draws: 100 for noise and task bootstrap, 50 for task subsets, 200 for flip margins).

Measured run times: `code/results/summary/runtimes.csv` (per job: last wall-clock line of the job's log, and the scheduler's wall and CPU seconds) and `code/results/summary/cpu_total.csv` (scheduler-metered CPU seconds summed over the jobs finished at the time of its snapshot; the paper reports the rounded sum, about 24 CPU-hours). This is about five times the 4 CPU-hour estimate of the task description, which we therefore do not report as a measurement; the host was shared, so wall time exceeds CPU time. Peak resident memory of the ordinal-rule solves (the memory-critical jobs) is in `code/results/summary/peak_memory.csv` (maximum 669 MB, for Condorcet at mean target rank 1000). Each job is single-threaded.

## 5. Script -> table/figure map
| paper element | script | inputs (`code/results/`) | output |
|---|---|---|---|
| Figure 1 (cost vs rank) | `figures/scripts/fig_rank_rules.py` | `figures/provenance/fig_rank_rules.json` | `figures/fig_rank_rules.pdf` |
| Figure 2 (feasible share vs cap, $h^\ast$, empirical caps) | `figures/scripts/fig_cap_curve.py` | `figures/provenance/fig_cap_curve.json` | `figures/fig_cap_curve.pdf` |
| Table 1 (main) | `figures/scripts/tab_main.py` | `figures/provenance/tab_main.json` | `figures/tables/tab_main.tex` |
| Appendix: other caps | `figures/scripts/tab_main.py --caps front0,front2,gain5,gain20,emp99` | `figures/provenance/tab_caps_appendix.json` | `figures/tables/tab_caps_appendix.tex` |
| Appendix: $R^2$ rank vs gap (C4) | `figures/scripts/tab_c4.py` | `figures/provenance/tab_c4.json` | `figures/tables/tab_c4.tex` |
| Appendix: min vs mean by CV tercile (C2) | `figures/scripts/tab_c2.py` | `figures/provenance/tab_c2.json` | `figures/tables/tab_c2.tex` |
| Appendix: cap realism (C8) | `figures/scripts/tab_c8.py` | `figures/provenance/tab_c8.json` | `figures/tables/tab_c8.tex` |
| Appendix: slices (C7) | `figures/scripts/tab_slices.py` | `figures/provenance/tab_slices.json` | `figures/tables/tab_slices.tex` |
| Appendix: $h^\ast$ by rank, task-subset scaling (C3), noise and task-resampling runs (C7) | `figures/scripts/fig_hstar_bins.py`, `fig_tasksub.py`, `fig_robust.py` | `figures/provenance/fig_*.json` | `figures/fig_hstar_bins.pdf`, `fig_tasksub.pdf`, `fig_robust.pdf` |
| Table (theory checks) | `figures/scripts/tab_theory.py` | `theory_checks.csv` | `figures/tables/tab_theory.tex` |
| All rebuilt at once | `figures/make_all.sh code/results` | | |
| Every number in the text (macros) | `paper/make_numbers.py` | `summary/*.csv`, `theory_checks.csv` | `paper/gen/numbers.tex` |
| `summary/*.csv` | `code/src/analyze.py` | per-target result files | `code/results/summary/` |

Exact input checksums for each figure and table are in `figures/provenance/*.json`; for each result file in `code/results/MANIFEST.csv`. The paper was last built from the result files named by the commit that delivered it.

## 6. Forbidden-material log
The task forbids reading a certain published paper on this question and anything citing or discussing it. Contact log by position:
- report position: none known. Searches made: title lookups of the starter-literature items and of two works named in the context position's brief (bibliographic verification only).
- planning position: none known. It ran no literature or web searches and fetched no external pages (inputs: the frozen task files and the world's repositories); it asked the context and feasibility positions to state theirs. The context position's brief (§4) records that it did not seek the paper.
- venue position: none known. No literature search; pages read were the NeurIPS 2026, ICML 2026 and ICLR 2027 call-for-papers and author instructions and the NeurIPS 2026 template, none concerning the forbidden paper.
- analysis position: none known. No literature searches; external inputs were the two leaderboard data sources and package installs.
- presentation position: none known. No literature or web searches; it read only the frozen task material and the other positions' repositories.
- context position: it consulted the starter-list papers arXiv:2603.08371, 2107.07002 and 2312.03121, the abstract of arXiv:2405.01719 and the Crossref records of three bribery-in-elections papers, plus a handful of literature searches (queries logged by that position); it knowingly met nothing from the forbidden-material list. Stated limit: it did not read the full bibliographies of its sources, so it cannot exclude that one cites the forbidden paper; nothing it read pointed to it.
- feasibility position: it ran no literature or web searches and fetched no external pages; it worked from the frozen task files, the other positions' repositories and local timing runs on the committed score tables, and knowingly met none of the forbidden material.
- review position: it read no material about the forbidden paper.
- external-review position: it ran no literature or web searches and fetched no external pages; the only material it read was the frozen task files and the released versions of this delivery, so it knowingly met none of the forbidden material (its own statement).

## 7. Use of LLM agents
The study (planning, code, analysis, writing) was carried out by LLM-based agents. Every number in the paper is produced by the attached code from the pinned public data; the agents are not a component of the numerical method.
