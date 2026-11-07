# Reproducing the analysis

Section A (data and analysis) is written by `experiment-repo`; figures and tables (section B) are appended by `figtab-repo`.

## A. Data and analysis

**Environment.** CPU only (2 cores suffice). Python 3.11.2, numpy 2.4.6, scipy 1.17.1 (HiGHS via `scipy.optimize.milp`), pandas 3.0.6, pyarrow 26.0.0. No GPU, no random seeds beyond those named below.

**Data (public, licences not declared; no copy is shipped — only fetch scripts, snapshot ids and SHA-256 checksums).**

| source | snapshot | used for |
|---|---|---|
| HELM MMLU, 79 models × 57 subjects (exact match, `# eval` 100–1534 per subject) | release v1.13.0, `https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/`; file list `data/helm_v1.13.0_filelist.txt` | board 1 |
| Open LLM Leaderboard v2 `contents` (4,576 rows, 6 tasks) | `open-llm-leaderboard/contents` @ `9c09a7cae43334062a82cb164f2ef255013dafa2`, parquet sha256 `f13a7061…78dca5` | board 2, headline level |
| Open LLM Leaderboard v2 `results` (39 sub-task accuracies, 699 models) | `open-llm-leaderboard/results` @ `aa81ecc38fdc5708254b833923368970efdf5ef5` | board 2, sub-task level |

Retrieved 2026-11-02. `results/data_manifest.json` lists SHA-256 of every file used, counts and exclusions. The supplied data description gives 13.6 MB for the `results` dataset; the full dataset is about 1.2 GB, so only a bounded subset
(selection rule fixed before looking at any sub-task value, see `code/analysis/01b_fetch_olb_results.py`: main population with a results directory, top 300 by Average plus 400 random others, numpy seed 20261102, latest result file per model; 80 MB) is fetched.

**Steps.**
```
bash code/fetch_data.sh                      # fetch + build data/processed/* (~5 min, needs network)
python3 code/tests/test_solvers.py           # exactness tests of all solvers against brute force (~10 min)
python3 code/tests/test_real.py              # solver sets re-checked with the independent reference rules on real boards
cd code/analysis
python3 09_per_target.py helm                # per-target k_min/G_min grids (each ~2-5 min; olb_subtask ~40 min)
python3 09_per_target.py olb_headline ; python3 09_per_target.py olb_headline_raw ; python3 09_per_target.py olb_subtask
for s in pop_all pop_nomerge pop_official field_top10 field_top50 field_top10_helm field_top50_helm; do python3 09_per_target.py ablation_$s; done
python3 06_frontier.py helm ; python3 06_frontier.py olb ; python3 06_frontier.py olb --raw    # Δ*(k) frontier (upper bound of G_min for ordinal rules)
python3 10_baselines.py helm ; python3 10_baselines.py olb                                    # seed 99
python3 12_subsample.py helm ; python3 12_subsample.py olb_subtask                           # seed 20261103
python3 13_noise_robust.py helm 200 ; python3 13_noise_robust.py olb 100                      # seed 424242
python3 14_verification.py                                                                   # seed 31415
python3 02_min_k.py helm ; python3 02_min_k.py olb ; python3 03_l1.py ; python3 04_noise.py helm 200 ; python3 04_noise.py olb 100 ; python3 05_synthetic.py 150   # exploratory grids (appendix)
python3 15_manifest.py
python3 11_collect.py                        # assembles the figtab-schema tables in results/ (bootstrap seed 20261104)
python3 16_headline.py                       # results/headline.csv (after 11_collect.py)
python3 07_summarize.py                      # tab_*.csv summaries of the exploratory grids
```
Long jobs were run as independent background jobs; each script is single-process. Output location, columns and definitions: `results/README.md`.

**Which script makes which table.** `per_target*.csv` ← 09 (+ 11); `paired_stats`, `feasibility`, `power_mean_*`, `ablation`, `subsample_curves*`, `baselines*`, `noise_robust.csv`, `per_target_noise.csv` ← 11; `verification.csv` ← 14; `data_manifest.json` and `data/manifest.json` (identical copy, venue-required path) ← 15.

**Code layout.** `code/lbattack/rules.py`: reference implementation of the rules on a full score matrix (independent of the solvers, used for every validation). `code/lbattack/solvers.py`: exact/heuristic minimal-investment solvers
(closed forms for mean / geometric & power means / min / median; subset enumeration for n ≤ 10; multi-cover MILP for Borda, plurality, Copeland, Condorcet; greedy-plus-prune upper bound for the trimmed mean at n > 10; `g_min` = exact minimal points for separable rules).

**Independence statement.** No search for, access to, or reading of the prior published paper on this question (or anything citing it) took place; nothing from it was used.

## B. Figures and tables

(appended by `figtab-repo`)
