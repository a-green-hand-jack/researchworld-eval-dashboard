# Targeted investment needed to top a multi-task leaderboard — code and reproduction

Paper: `paper/main.pdf` (LaTeX source: `paper/main.tex`, `paper/appendix.tex`, `paper/refs.bib`, ICML 2026 template files `icml2026.sty/.bst` copied from https://media.icml.cc/Conferences/ICML2026/Styles/icml2026.zip). The ICML 2026 template has no paper checklist; the required Impact Statement is included in the paper.

## Layout
| path | content |
|---|---|
| `src/core.py` | exact solvers (closed forms; 0-1 programs via HiGHS), rule evaluation, witness verification |
| `src/common.py`, `src/load_helm.py` | data loading; parse HELM per-subject tables -> `out/helm_scores_raw.csv`, `out/helm_neval_raw.csv` |
| `src/exp_*.py` | experiments (write `out/*.csv`) |
| `src/analysis_*.py` | tables (`paper/tables/*.tex`, `out/tables/*.csv`), figures (`paper/figs/*.pdf`), logs (`out/analysis_*_log.txt`) |
| `src/download_data.py` | downloads all public data (no account) and writes `data/CHECKSUMS.sha256` |
| `tests/test_core.py` | brute-force validation of all solvers (output `out/test_log.txt`) |
| `run_all.sh` | runs everything in order |
| `data/` | downloaded data (HELM release v1.13.0: 303 files; OLB `contents` parquet) + `CHECKSUMS.sha256` |

## Environment
Python 3.11.2 in a venv (`python3 -m venv venv && venv/bin/pip install numpy==2.4.6 pandas==3.1.0 scipy==1.17.1 matplotlib==3.11.2 pyarrow==26.0.0`; full freeze in `requirements.txt`; `pymupdf` there was only used to look at the PDF). LaTeX: pdflatex + bibtex (TeX Live from Debian). CPU only; the container is limited to 4 cores (`NPROC`, default 4, in `src/common.py`).

## Data (all public, no account)
* HELM MMLU, release **v1.13.0** (summary.json date 2025-01-10), `gs://crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (303 files, 11.4 MB). We use `groups/json/mmlu_mmlu_subject:<subject>.json` (57 files; EM and `# eval` per model). Version v1.13.0 is the one prescribed by the task.
* Open LLM Leaderboard `contents` parquet, dataset commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (last updated 2025-03-20), sha256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5`. The `results` dataset was not used.
* Licences: HELM code Apache-2.0; no explicit licence for the score data; OLB card has no licence field (per-model hub licences in the `Hub License` column). Only numeric scores and model names are used; nothing is redistributed (the data are fetched by the script).
* Run: `venv/bin/python -I src/download_data.py data` (about 1 min), then `cd data && sha256sum -c CHECKSUMS.sha256`.

## Reproduce
```
bash run_all.sh            # add --download to fetch the data first
cd paper && pdflatex main && bibtex main && pdflatex main && pdflatex main
```
Measured wall time of `run_all.sh` on 4 cores: about 11-12 minutes (solver validation 51 s, Exp A 95 s, Exp B 254 s, Exp F 152 s, the others < 1 min each); the full run was executed once end-to-end from the downloaded data. All randomness is seeded (task subsets seed 0, noise bootstrap seed 1, random permutations seeds 1000*rule_index+target, paired bootstrap seed 3, noise-bins seed 4); solvers are deterministic.

## Script -> paper artefact
| artefact | produced by |
|---|---|
| Fig. 1 (investment vs rank), Tab. 1 (same targets), Tab. 2 (rank groups), Tab. 4 (paired), Kendall tau, leaders | `exp_helm_main.py` -> `analysis_helm.py` |
| Fig. 2 (gain caps) | `exp_helm_caps.py` -> `analysis_helm.py` |
| Fig. 3 (scaling in n) | `exp_helm_scale.py` -> `analysis_helm.py` |
| Fig. 4 (noise), noise numbers in 5.1 | `exp_helm_noise.py` -> `analysis_helm.py` |
| noise-bins table (appendix, Tab. 8) | `exp_helm_noise_bins.py` |
| Fig. 6 (order-statistic family, appendix) | `exp_helm_quantile.py` -> `analysis_helm.py` |
| Tab. 6 random-order ablation | `exp_helm_random.py` -> `analysis_helm.py` |
| Tab. 5 convex-cost table | `exp_helm_convex.py` |
| Fig. 5 and OLB tables | `exp_olb.py` -> `analysis_olb.py` |
| Tab. 3 bound tightness, separation instances (Prop. 4) | `analysis_theory.py` (`out/theory_summary.txt`) |
| solver validation | `tests/test_core.py` (`out/test_log.txt`) |
Numbers quoted in the text come from `out/analysis_helm_log.txt`, `out/analysis_olb_log.txt`, `out/theory_summary.txt`, `out/log_convex.txt`.

## Notes and caveats
* Every plan returned by a solver is applied to the leaderboard and the rule is recomputed (assertions in `core.solve`); the status of each MILP solve is stored (`status` column; all 0 = optimal).
* Investment measures: `B` (tasks touched), `P` (summed accuracy gain, fraction units), `D` (test-equivalent questions). CSV columns `P`, `D` can contain values like -1e-16 (numerical zeros); analysis scripts clip at 0.
* Tolerances: strict inequalities are enforced with 1e-9 slack; ties at a ceiling are not exploited (no cell of either board equals the ceiling).
* **Restricted-content record.** The task forbids reading one specific published paper and anything discussing it. Literature search used the scholarly-search tool with queries on bribery/margin of victory in elections, robustness of benchmark rankings, Goodhart/gaming of leaderboards, training on the test task, diversity-stability in multi-task benchmarks, the computational-social-choice handbook, and Open LLM Leaderboard contamination. Only titles and abstract snippets of the results were read; none was recognised as the restricted paper or as a page discussing it. The starter-list item "Leaderboard Incentives" (arXiv:2603.08371) appeared in a result list; only its snippet was read.
