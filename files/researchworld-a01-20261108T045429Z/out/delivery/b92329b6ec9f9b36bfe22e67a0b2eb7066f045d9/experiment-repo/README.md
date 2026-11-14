# Analysis code: minimum targeted investment to top a multi-task leaderboard

Code, data manifests and results for *how much targeted investment (raising a target model's scores on chosen sub-datasets) is needed to rank first, as a function of the aggregation rule?* — Open LLM Leaderboard (OLLB) and HELM MMLU v1.13.0.
`RESULTS.md` is the hand-off of definitions, findings (with the table each one is read from) and caveats; this file is how to reproduce them.
Licence of this code: MIT. The data are not ours (see "Data and licences").

## Environment
Python 3.11.2, `pip install -r requirements.txt` (numpy 2.4.6, scipy 1.17.1 with HiGHS for the MILPs, pandas 3.0.6, pyarrow 26.0.0 for the parquet, pytest 9.2.0). CPU only; peak memory of any job < 2 GB; nothing needs a GPU. The measurements below are from a 2-CPU, 4 GB container on a host shared with other jobs (up to 6 of our jobs ran at once), so they are upper-ish bounds.

## Data and licences
| Data | Source / version | Checksum |
|---|---|---|
| HELM MMLU v1.13.0 (79 models x 57 subjects) | `storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (303 objects) | manifest SHA-256 `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` (`data/processed/manifest.json`) |
| OLLB `contents` | `huggingface.co/datasets/open-llm-leaderboard/contents` @ `9c09a7cae43334062a82cb164f2ef255013dafa2` | `data/train-00000-of-00001.parquet` SHA-256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` |
| OLLB `results` (**used**, for the 39-leaf-task board and the item counts of the noise model) | `huggingface.co/datasets/open-llm-leaderboard/results` @ `aa81ecc38fdc5708254b833923368970efdf5ef5`: 10 509 run files, **~1.2 GB** to download (the data notes' "13.6 MB" is wrong) | digest of the sorted (path, file-SHA-256) list `bcee5e13b1aa5eb6fbe1eaeb5775dcb532be23de22087f7160692d63940ae99f` in `data/processed/ollb_leaf_manifest.json` (every file's SHA-256 is recorded in the downloader's JSONL, not redistributed: 114 MB) |

Neither data set declares a licence. We redistribute only derived score matrices (`data/processed/`: HELM 79x57, OLLB 4497x6, OLLB leaf 4506x39) and results, with attribution to the HELM project and the Open LLM Leaderboard; no model weights are used. `cais/mmlu` is not used. Open LLM Leaderboard rows: 4576 raw, 79 duplicate `fullname` dropped, 1 flagged model excluded as a target (4496 targets). Leaf board: newest run with all 38 leaf tasks (39 incl. the merged ones: see manifest) per `fullname`, flagged models dropped; 10 of its 4506 models have no row in `contents`.

## Commands
```
pip install -r requirements.txt
make data         # NETWORK: re-download HELM + OLLB contents (~1 min), rebuild data/processed, check hashes
make data-leaf    # NETWORK: ~1.2 GB OLLB `results` -> compact JSONL (resumable, 32 threads) -> data/processed/ollb_leaf.csv
make all          # = test core robust copeland control leaf analyze checks final   (everything offline, uses data/processed)
```
All per-target result CSVs (about 70 MB in total) are included uncompressed, so `make analyze final` and the figure generators run without recomputation. Targets can be run alone (`make core`, `make robust`, ...). All randomness is seeded: bootstrap over targets seed 0 (1000 resamples); evaluation-noise, task-bootstrap, task-subset runs `--seed 0` (`src/run_robust.py`); rank-stratified target samples seed 0 (`src/run_core.py`); random-allocation control seed 0; solvers are deterministic. `results/manifest.csv` lists every result file with SHA-256, row count, producing command, seed and the code commit.

## Measured wall-clock per `make` target (2 CPUs, shared host; from `logs/`)
| Target | What | Measured |
|---|---|---|
| `test` | solvers vs brute force (7 tests, incl. Copeland MILP) | 38 s on an idle host; 194 s when 6 other jobs ran |
| `core` | HELM main 862 s; OLLB closed forms 44 s + capped 272 s + empirical caps 43 s; OLLB ordinal (sampled targets) 5 805 s; top-500 slice 977 s; trimmed 53 s; no-merge 47 s; raw 61 s | 8 164 s = 2.3 h |
| `robust` | HELM evaluation noise 966 s; task bootstrap 352 s; task subsets 193 s + 212 s; OLLB noise 35 s + 26 s | 1 784 s = 0.5 h |
| `copeland` | 34 MILPs, 0.2-50 s each, 2 processes | 310 CPU-s (~3 min wall) |
| `control` | random-allocation control, two caps (two parallel jobs) | 572 s and 583 s |
| `leaf` | leaf board: closed forms 74 s + caps 307 s; 6-benchmark aggregates 73 s; task subsets 13 s + 14 s; top-500 slice with all 8 rules 886 s; task subsets of the top-500 slice 389 s | 1 756 s = 0.5 h |
| `analyze` | tables | 61 s |
| `checks` | numerical checks of the propositions | seconds |
| `final` | `results/final/` (150 s) + extras + manifest | ~4 min |
| recheck of all `inf` (not in `make all`, `src/recheck_inf.py`) | strict re-solve of every infinite ordinal result | OLLB ordinal gain 4 598 s (1 504 infinite results); leaf top-500 about 70 s; HELM + OLLB top-500 not timed (minutes) |

Sum of the `make all` targets run back to back: 13 500 s = **3.75 h** wall (test 38 s + core 8 164 s + robust 1 784 s + copeland 310 s + control 1 155 s + leaf 1 756 s + analyze 61 s + final ~240 s), of which the OLLB ordinal run is 1.6 h. Every job is single-threaded (HiGHS runs one thread; CPU use of a job was 0.7-1.0 CPU), so this is about 3-4 CPU-hours, within the 4 CPU-hour estimate of `resources.md`; independent targets can run as parallel jobs on the 2 CPUs (about 2-2.5 h wall). The 2.6 h quoted in the plan was an estimate made before the Copeland, control and leaf-board additions. Several timings were taken while 3-6 jobs shared the host, so they are upper-ish bounds (the test took 38 s on an idle host and 194 s on a loaded one).

## Script -> table / figure map
| Output | Script (Makefile target) |
|---|---|
| `data/processed/*` | `src/fetch_helm.py`, `src/fetch_ollb.py`, `src/build_data.py`, `src/ollb_items.py` (`data`); `src/fetch_ollb_results.py`, `src/build_leaf.py` (`data-leaf`) |
| solvers | `src/mti/scorerules.py` (mean, geometric, harmonic, median, min, trimmed mean: closed form / water-filling / MILP), `src/mti/ordinal.py` (Borda, Condorcet winner, Copeland, plurality: MILP), `src/mti/data.py` (loaders, cap scenarios); tests in `tests/` |
| `results/helm_main.csv`; `ollb_closed`, `ollb_score_caps`, `ollb_score_emp`, `ollb_ordinal_gain`, `ollb_top500`, `ollb_trimmed`, `ollb_nomerge_score`, `ollb_raw_score` | `src/run_core.py` (`core`) |
| `results/helm_noise_gain10`, `helm_taskboot_gain10`, `helm_tasksub_{ceil,gain10}`, `ollb_noise_{ceil,gain10}` | `src/run_robust.py` (`robust`) |
| `results/copeland_check.csv`, `results/final/copeland_vs_condorcet.csv` | `src/run_copeland.py`, `src/copeland_table.py` (`copeland`) |
| `results/random_control_{ceil,gain10}.csv`, `results/final/random_control_summary.csv` | `src/run_random_control.py` (`control`), `src/summarize_extras.py` |
| `results/leaf_*.csv`, `leaf6_score.csv`, `results/final/leaf_*.csv` | `src/run_core.py`, `src/run_robust.py` (`leaf`), `src/summarize_extras.py` |
| `results/tables/summary_*`, `*_relL1_vs_mean.csv` | `src/summarize.py` (`analyze`) |
| `results/tables/{group_medians,cheapest_rule,elasticity,rankslope,spearman}_*`, `robust_*`, `tasksub_*` | `src/analyze.py` (`analyze`) |
| `results/theory_checks.txt` | `src/theory_checks.py` (`checks`) |
| `results/final/*` (figure-ready files: status encoding, per-task units, theory per target, group summaries, robustness) | `src/finalize.py` (`final`); schema in its docstring and in `RESULTS.md` |
| `results/recheck_inf*.csv` | `src/recheck_inf.py` |
| `results/manifest.csv` | `src/manifest.py` |

Figures and tables of the paper are produced by the generators in `scripts/` of the delivery root from `results/final/` (hashes of their inputs in `figures/`); numbers quoted in the paper text are read from `results/tables/` and `results/final/`.

## Status of "inf"
An `inf` investment means no allocation under the cap makes the target first (proved by the MILP). Every `inf` of an ordinal rule was re-solved with a strict solver that raises on a time-out (`results/recheck_inf*.csv`); the solvers also raise (instead of returning `inf`) on any non-optimal status.
