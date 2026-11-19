# Reproduction notes

This repository is the delivery root. The paper (`main.tex`, `sections/`, `refs.bib`, `checklist/`, built `paper.pdf`) is written by `paper-repo`; analysis code, data manifests and results are under `code/` (`experiment-repo`); figure/table generators and their outputs are under `figures/`, `tables/`, `scripts/` (`figtab-repo`); the unmodified NeurIPS 2026 template is under `template/` (`venue-repo`). Detailed commands, pinned environment and measured per-target run times for the analysis are in `code/README.md` (and the findings with their tables in `code/RESULTS.md`); the figure/table generators, their inputs' SHA-256 and the output-to-claim map are in `figures/README.md` (`figures/scripts/`, `figures/inputs.sha256`).

## 1. Build the paper
`pdflatex`/`bibtex` from TeX Live (sandbox: TeX Live with `latexmk`), from the repository root:
```
latexmk -pdf -jobname=paper main.tex      # writes paper.pdf; main.tex loads template/neurips_2026.sty by relative path
python3 check_venue.py paper.pdf          # venue-repo's format checker (tools/check_venue.py in venue-repo)
```
The style file is the unmodified `neurips_2026.sty` (hashes in `template/SOURCES.md`); the submission (anonymous) option is used.

## 2. Data (public; versions and checksums)
| Data | Version / commit | Checksum | Date |
|---|---|---|---|
| HELM MMLU benchmark output, release `v1.13.0` (`https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/`, summary date 2025-01-10; 303 objects, 11 384 206 bytes) | v1.13.0 (the version fixed by the task; no other version used) | manifest SHA-256 `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` (`code/data/processed/manifest.json`; per-file hashes next to the downloads written by `src/fetch_helm.py`) | fetched 2026-11 |
| Open LLM Leaderboard `contents` (`huggingface.co/datasets/open-llm-leaderboard/contents`) | commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (last update 2025-03-20) | `data/train-00000-of-00001.parquet` SHA-256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` | fetched 2026-11 |
| Open LLM Leaderboard `results` (`huggingface.co/datasets/open-llm-leaderboard/results`), **used** for the 39-leaf-task granularity board and item counts | commit `aa81ecc38fdc5708254b833923368970efdf5ef5`; 10 509 run files, about 1.2 GB download | digest of the sorted (path, file SHA-256) list `bcee5e13b1aa5eb6fbe1eaeb5775dcb532be23de22087f7160692d63940ae99f` (`code/data/processed/ollb_leaf_manifest.json`); not redistributed, only the derived matrix `ollb_leaf.csv` (4506 x 39) |
| `cais/mmlu` (MIT) | not used | | |

Derived matrices used by every result (`code/data/processed/`): HELM 79 models x 57 subjects (all 79 models have all subjects; every subject table exists under two identical file names and is read once); Open LLM Leaderboard 4 576 rows, 79 duplicate `fullname` rows dropped (4 497), one flagged model excluded as a target (4 496), six normalised task scores (IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-Pro). The leaderboard's own `Average` equals the mean of these six scores (maximum absolute difference $1.4\cdot10^{-14}$, checked from the processed file).

### Licences (judgement)
* HELM scores: neither the public bucket nor the site states a licence for the score data (checked by `venue-repo`/`idea-repo` 2026-11-08, and in the task statement 2026-10-27); the code is Apache-2.0. We use only public scores and redistribute only derived score matrices and results, with attribution to the HELM project; we make no claim that the scores are re-licensable.
* Open LLM Leaderboard `contents` / `results`: no licence field on the dataset (the `contents` card has none, `results` has no card); the `contents` table has a per-model `Hub License` column, which applies to the models, not to the evaluation scores. Same treatment as above. We use no model weights and no per-model licence-restricted content.
* Our code: released with the delivery (licence as stated in `code/README.md`).

## 3. Environment and seeds
Python 3.11.2; `code/requirements.txt` pins numpy 2.4.6, scipy 1.17.1 (HiGHS MILP), pandas 3.0.6, pyarrow 26.0.0, pytest 9.2.0; matplotlib for the figures (version in `figures/README.md`). CPU only; 2 CPUs, 4 GB memory, no job above 2 GB. Seeds: bootstrap over targets seed 0 (1 000 resamples); evaluation-noise, task-bootstrap, task-subset runs `--seed 0` (`src/run_robust.py`); rank-stratified target samples seed 0 (`src/run_core.py`); random-allocation control seed 0; solvers are deterministic. `code/results/manifest.csv` lists every result file with SHA-256, row count, command, seed and code commit.

## 4. Commands and run time (measured, from `code/logs/`)
```
cd code && pip install -r requirements.txt
make data; make data-leaf      # network: HELM + OLLB contents (~1 min); OLLB results (~1.2 GB)
make all                       # test core robust copeland control leaf analyze checks final (offline)
sh scripts/run_all.sh                   # figures and tables (about 2 min), from the repository root; default input code/results
```
`make all` back to back takes 13 500 s = 3.75 h on 2 CPUs of a shared host (tests 38 s, core 8 164 s of which the OLLB ordinal run 5 805 s, robustness 1 784 s, Copeland 310 s, random control 1 155 s, leaf board 1 756 s, analysis 61 s, final about 240 s); every job is single-threaded, about 3--4 CPU-hours (within the 4 CPU-hours of the task's `resources.md`), and independent targets can run in parallel (about 2--2.5 h). Many timings were taken with 3--6 jobs on the host and are upper bounds. (Earlier drafts and the plan quoted 2.6 h, from before the Copeland, control and leaf-board additions; the measured figure replaces it.) The strict re-solve of every infinite ordinal result (`src/recheck_inf.py`) is not in `make all` (about 1.3 h for the OLLB ordinal results). Development runs are not included in these times.

## 5. Script -> table / figure map
See `code/README.md` (analysis outputs: `results/*.csv`, `results/tables/*.csv`, `results/theory_checks.txt`) and `figures/README.md` (each paper figure/table, its generator, and `figures/inputs.sha256`). Every figure and every table with numbers is produced by the generators named there (`scripts/`); the rules table is `tables/tab1_rules.tex`. Numbers quoted in the text of Section 5 are read from `code/results/tables/*` and each paragraph of `sections/experiments.tex` carries a `% src:` comment naming the table it reads.

## 6. What was not run (stated in the paper)
Rank-based rules on all 4 496 Open LLM Leaderboard targets with `ceil`/`front` caps (rank-stratified samples with gain caps and the top-500 slice were run instead); trimmed mean on a sample of targets only; Copeland on 34 target-cap cases only; Schulze and Kemeny not implemented; weighted mean not run; no strategic response by other models; no multi-target interaction. The `results` data set is used, as a granularity board with the same models as the six-task board (not a third independent data set), with score rules on all targets and ordinal rules on its top-500 slice.

## 7. Forbidden material
The task forbids searching for or reading the published paper on this question and any page that cites or discusses it. Records:
* `paper-repo` (this position): searched literature by topic only (voting bribery/manipulation, Vote'n'Rank, NLP leaderboard critiques, Goodhart's law, Open LLM Leaderboard task names) through a literature-search tool returning titles and abstract snippets, and fetched arXiv/Crossref metadata (titles, authors) for the cited works. No page identified as the forbidden paper, and none that cites or discusses it, was read. One result of a search for the Open LLM Leaderboard task names (an EMNLP 2026 paper on benchmark dependence among top models of the same leaderboard) was seen only as a search snippet (about 100 words) and not opened. No citation-graph or "cited by" pages were opened.
* `idea-repo`: its wiki page `Prior-work` ("Search log and prohibited-material hygiene") records no encounter.
* `experiment-repo` (its statement in `experiment-repo`#6): fetched only data hosts (Hugging Face dataset API and files, the HELM bucket); searched for and read no literature on the question and no page citing it.
* `story-repo`: none encountered. This position ran no literature or web search and fetched nothing from the internet; it read only the frozen task inputs (/initial-state), the Forgejo repositories/issues/wiki pages of the other positions, and the experiment-repo results, so it read neither the published paper on this question nor any page citing or discussing it.
* `venue-repo`: none encountered. It searched no literature and read no paper or review page; its only fetches were conference sites for formatting rules (neurips.cc 2026 Call for Papers and Main Track Handbook read; an iclr.cc author-guide URL returned 404; icml.cc 2026 author instructions and github.com/ICLR/Master-Template fetched for status only, not read), the NeurIPS 2026 template zip from media.neurips.cc, and the template files themselves.
* `figtab-repo`: none encountered. It fetched nothing from the web; it read only `/initial-state` and the `experiment-repo`, `story-repo`, `venue-repo` and `paper-repo` repositories.
