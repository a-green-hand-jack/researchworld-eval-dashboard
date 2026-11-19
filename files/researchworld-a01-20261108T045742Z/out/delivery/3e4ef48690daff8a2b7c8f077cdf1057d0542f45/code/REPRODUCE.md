# Reproduction notes (code/ of the delivery)

Everything below is CPU-only. All numbers in `results/` were produced by the scripts named here from the pinned public data.

## 1. Environment
Python 3.11.2 (Linux x86_64); numpy 2.4.6, scipy 1.17.1 (MILP solver = HiGHS through `scipy.optimize.milp`), pandas 3.0.6,
pyarrow 26.0.0, pytest 9.2.0. No GPU, no network after `make data`. Hardware used: jobs of 2 CPUs / 4 GB on a shared host.
Wall times below are as measured in those jobs (the host was oversubscribed, so they are upper-ish bounds).

## 2. Data (public; versions and hashes)
| Data | Source / version | Check |
|---|---|---|
| Open LLM Leaderboard `contents` | `huggingface.co/datasets/open-llm-leaderboard/contents`, commit `9c09a7cae43334062a82cb164f2ef255013dafa2` (2025-03-20), file `data/train-00000-of-00001.parquet`, 1,109,997 B | sha256 `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` (also in `data/processed/manifest.json`) |
| HELM MMLU | `storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` (release summary dated 2025-01-10), per-subject tables `groups/json/mmlu_mmlu_subject:<subject>.json`; the bucket is listed through the GCS JSON API (directory URLs 404) | `MANIFEST.sha256.json` is written by `src/fetch_helm.py`; its sha256 is `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` |
| Item counts / normalisation floors for OLLB (evaluation-noise robustness only) | one `results_*.json` of `open-llm-leaderboard/results` @ `aa81ecc38fdc5708254b833923368970efdf5ef5` (`n-samples`) | sha256 in `data/processed/ollb_noise.json` |

Processing (`src/build_data.py`): OLLB 4576 rows -> 79 duplicate `fullname` rows dropped (best-scoring variant kept) -> 4497 models;
the one `Flagged` model is removed at load time (4496 in all analyses); 6 normalised task scores (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO;
the leaderboard's own normalisation) and the raw accuracies. HELM: 79 models x 57 subjects, no missing cells, EM x 100.
`data/processed/*.csv` are committed so every analysis runs without network.
Licence: the leaderboard/benchmark score tables carry no separate licence statement; we only redistribute the derived score matrices
(facts, no model outputs). The datasets' own repositories govern reuse; our code is released under Apache-2.0 (`LICENSE`); the licence covers the code and our result files, not the upstream score tables in `data/processed/`.

## 3. Commands (from the repository root = `code/`)
`make data` (network, ~2 min) · `make test` (8 tests, ~1-1.5 min; solvers vs brute force and LP) · `make theory` (~40 s) · `make helm` · `make helm_extra` ·
`make ollb_score` · `make ollb_ordinal` · `make ollb_variants` · `make robust` · `make summary` · `make all`.
Seeds: targets sampled with `--seed 0` (default); bootstrap CIs `numpy.random.default_rng(0)`; robustness drivers `--seed 0`;
task-subset bootstrap seeds `1000*b+n`. Solvers are deterministic.

Measured wall times (2 CPUs): `helm` 14 min (6 caps x 8 rules x 79 targets; 2.5 min of it per ordinal rule-cap block);
`ollb_score` ceil 0.7 min, the 5 other caps with 6 rules each 17-60 min per cap (dominated by the trimmed-mean MILP; the empirical-gain caps ran in 2 min each once the quantiles were cached);
`ollb_ordinal` (sampled targets, 3 rules) 11-39 min per cap, run the four caps in parallel;
`robust`: noise R=100 24 min, task-bootstrap R=50 2 min, task-subset R=200 3 min per cap; `ollb_variants` raw and non-merged score rules ~7 min each (trimmed mean not run there: its MILP costs ~40 min per cap on 4496 targets), top-500 incl. rank rules ~1 h.
Total CPU time on the order of 12 CPU-hours (parallelisable over the jobs), above the 4 CPU-hour planning estimate of the brief because the exact ordinal MILPs on 4496 models were not anticipated; the task's time limit is one week.

## 4. What each script produces
| Script | Output | Supports |
|---|---|---|
| `src/theory_checks.py` | `results/theory_checks.csv` | C1/C2 closed forms (mean, min, median) and cap monotonicity vs the exact solvers |
| `src/run_core.py helm ...` | `results/helm_main.csv` (6 caps x 8 rules, all 79 targets), `helm_wmean.csv` (item-count weighted mean, 4 caps) | C1-C4, C6, C8 |
| `src/run_core.py ollb ...` | `ollb_closed.csv` (ceil, score rules), `ollb_score_caps.csv` (front0/front2/gain5/gain10/gain20) and `ollb_score_emp.csv` (emp95/emp99), score rules + trimmed1, all 4496 targets, `ollb_ordinal_{ceil,front2,gain10,emp95}.csv` (Borda/Condorcet/plurality; 20 top challengers + 100 rank-log-uniform targets) | C3-C6 |
| `src/run_core.py helm ... --eps` | `helm_margin1_score.csv`, `helm_margin_score.csv` (statistical margin 1 and 2 x SE, score rules) | C7 (v) |
| `src/run_core.py ollb_raw / ollb_nomerge / ollb_top500` | `ollb_raw_score.csv`, `ollb_nomerge_score.csv`, `ollb_top500.csv` | C7 (i), (ii) |
| `src/run_robust.py noise|taskboot|tasksub` | `helm_noise_gain10.csv`, `helm_taskboot_gain10.csv`, `helm_tasksub_{gain10,front2}.csv`, `helm_tasksubpaired_{gain10,front2}.csv` (mean-rank targets, `--targets mean`; the unpaired `helm_tasksub_*.csv` were written before the columns `target_def`, `rank_own`, `n_above_lead_median` were added, the default `--targets own` gives the same targets and costs, ~15 min with two jobs in parallel) | C2, C7 (iii), (iv) |
| `src/summarize_main.py` | `summary_*_by_rule_group.csv` (median K/n, L1/n, Linf with bootstrap CI per rank group; feasible share), `summary_*_ratio_to_mean.csv` (L1 rule / L1 mean per target) | headline table and figures |
| `src/summarize_robust.py` | `summary_helm_tasksub{,paired}_*_{by_n,slopes}.csv`, `summary_helm_noise_gain10_*`, `summary_helm_taskboot_gain10_*` | C2, C7 |
| `src/condorcet_existence.py` | `results/condorcet_existence.csv` | does the original leaderboard have a Condorcet winner |

Column conventions of the tidy CSVs: `L1` total score points raised, `K` number of tasks raised, `Linf` largest single-task jump,
`gap` aggregate gap to the best rival under the rule, `rank_mean` initial rank under the mean rule, `rank_rule` initial rank under the studied rule.
`inf` = infeasible within the cap (reported, never dropped); empty/NaN = solver time limit (120 s per MILP; count these before using a cell).
Summaries: medians are over targets *feasible* under that cap/rule and the feasible share is a separate column; medians must not be compared across
cells with different feasible shares. Groups are by initial rank under the mean rule; `top10` = initial ranks 2-11 (the plan's primary target set).

## 5. Modelling choices and known limits of the analysis (see also the paper)
- Investment model: raise the target's score on tasks to any level in [x_t, cap_t]; all other models fixed (no reaction); "first" = strictly above every rival by eps (1e-3 points) under the rule.
- Cap `emp95/emp99` = per-task 95th/99th percentile of (fine-tune - base) differences over 540 OLLB pairs; transfer to HELM was not done (no pair data).
- Rank rules use half credit for exact ties. For rank rules `eps` only fixes the strict-pass granularity; a *statistical* margin is therefore not defined by `eps` for them, and
  we did not run margin variants for Borda/Condorcet/plurality (an earlier attempt that did was removed because it did not implement a significance-tie semantics). Their noise robustness is `run_robust.py noise`.
- Score-rule margin: eps = k x 0.6 points, 0.6 = median SE of the difference of two models' equal-weight mean across 57 subjects (binomial, `# eval` items); for median/min it is only an approximate scale.
- Condorcet winner is a *proxy* for pairwise rules: it implies being first under every Condorcet-consistent rule, so its cost upper-bounds Copeland/Schulze/Kemeny. The original OLLB (n=6) has no Condorcet winner (`condorcet_existence.csv`); HELM has one (the mean-first model).
- Models are not independent (merges, same-base fine-tunes); slices `ollb_nomerge`, `ollb_top500` probe it.
- Ordinal OLLB runs use sampled targets (top-20 challengers plus 100 log-rank-uniform targets), not all 4496.

## 6. Forbidden-material log
This position (experiment-repo) ran no literature search and opened no web page other than the pinned dataset URLs above (Hugging Face, Google Cloud Storage). No paper, mirror, citing page or discussion of the already-published study of this question was encountered, searched for or read by this position.

### Addendum: OLLB margins and C5 table
`make ollb_margin_c5` (script `scripts/run_ollb_margin_emp99.sh`, three parallel jobs, ~7 min): OLLB score-rule margins k x 0.96 points (k = 1, 2; SE of a difference of two top models' mean aggregate from `data/processed/ollb_noise.json` item counts and benchmark floors, computed at the top-11 models' scores) and ordinal rules at emp99 for the top 20 targets. `src/c5_table.py` -> `results/c5_top10_emp*.csv`. Outputs: `ollb_margin{1,2}_score.csv`, `ollb_ordinal_emp99_top20.csv`, `summary_ollb_margin{1,2}se_*`, `c5_top10_emp*.csv`. Claims C5 and C7 (v).

### Addendum: slope intervals and noise spread
`summary_helm_tasksub*_slopes.csv` now carry two slope families per cost measure: `slope_{L1,K}_*` (log-log fit to per-n medians; medians are integers, so the bootstrap interval is discrete and can touch the estimate) and `slope_{L1,K}_mean_*` (fit to per-n means over feasible draws; percentile bootstrap over draws within each n cell, 500 resamples). Quote the mean-based interval as the uncertainty of the slope. `summary_helm_noise_gain10_by_rule.csv` and `summary_helm_taskboot_gain10_by_rule.csv` gain `abs_spread_q05_q95_med` (median over targets of the 5-95% range of L1 across draws, in points) next to the relative CV.

### Addendum: paired raw-vs-normalised comparison
`python3 src/raw_vs_norm_paired.py results/ollb_closed.csv results/ollb_raw_score.csv results/ollb_raw_vs_norm_paired_per_target.csv results/summary_ollb_raw_vs_norm_paired.csv` (seconds; seed 0, 2000 bootstrap resamples over targets). Claim C7 (i).
