# Reproducing the results

Definitions of every quantity and the schema of every result file: `results/README.md`.

## Environment
Python 3.11.2, numpy 2.4.6, scipy 1.17.1, pandas 3.0.6, pyarrow 26.0.0, scikit-learn 1.9.1 (only for the fitter validation in
`s0_base.py`). CPU only; no GPU; no network access is needed after the data are in place. Each `results/*.meta.json` records the
versions actually used. Set `PYTHONHASHSEED=0` (done in `run_all.sh`; no result depends on Python's string hash, seeds come from
`numpy.random.default_rng` with explicit integer lists, and `zlib.crc32` where a name enters a seed).

## Data (not in the repository; set `BT_DATA` = the directory holding these four files; if unset, `<repository root>/data` is used)
| file | source | sha256 |
| --- | --- | --- |
| `arena55k.csv` | HF `lmarena-ai/arena-human-preference-55k` @18c298340948c0e7f7727399fd459cca6ce0ca6f `train.csv` | 0692154aaf20fc6649090c3f49b6b5dd1e693a765ecb5f0856ae0da5946f5be2 |
| `mt_human.parquet` | HF `lmsys/mt_bench_human_judgments` @f7d2896d2cc5d80f8b55c2bbc722613555233c25 `data/human-00000-of-00001-25f4910818759289.parquet` | 4877bc46a40929f4082c3c79593700fb897b1d6c7f4c473032694a01322f5769 |
| `mt_gpt4.parquet` | same repository and revision, `data/gpt4_pair-00000-of-00001-c0b431264a82ddc0.parquet` | 57068327ffb5f8fddb15fedbbfe40b26fe862da2326331e5cf64a42320a00e71 |
| `nbaallelo.csv` | github `fivethirtyeight/data` @4c1ff5e3aef1816ae04af63218015066e186c147 `nba-elo/nbaallelo.csv` | d46ed3540ee8d9eca31b3e94cc8c777e0be5156173d814ebf65b8195e8d616bc |

The loaders refuse a file whose sha256 differs (`btlib/data.py`). The LLM-judge predictions for Arena battles (potsawee) listed in an early
draft were cut by plan v2 (no declared licence); no result here uses them.

## Commands
`bash code/run_all.sh <group>`. Order: A and B (parallel), `collect0`, then C, D, E, F, G, H (independent, each wrote its own
output files, run as parallel jobs of 2 CPUs; F-H read `budgets_remove.csv`), finally `collect`. Total CPU work is dominated by groups E, C, B and D.
**Total: about 10 wall-hours when the steps run one after another, each with 2 worker processes (sum of the measured step times in `results/runtimes.csv`: A 0.5 h, B 1.7 h, C 2.2 h, D 1.5 h, E 3.5 h, F 0.4 h, G 0.15 h, H 0.04 h, collect0 + collect 0.1 h), i.e. at most about 20 CPU-hours; with the groups run in parallel the critical path is about 3.5 h (group E).** These are the measured times of the jobs that produced the delivered files, on a host shared with other jobs, so a quiet machine should be no slower. `results/runtimes.csv` has one row per step (`group,command,seconds`); the rows of A-E come from the run that produced the first-round files, F-H and `collect` from the second round.

| group | command | writes | reproduces |
| --- | --- | --- | --- |
| A | `s0_base.py` | `base_*.csv`, `dataset_summary.csv`, `validation_fitter.csv`, `s0_base.meta.json` | E1 |
| A | `s1_run.py --what random --units arena55k,mt_human,mt_gpt4,nba_all` | `parts/s1_random_*.csv` | E2 |
| A | `s1_run.py --what adv --units arena55k,mt_human,mt_gpt4,nba_all` | `parts/s1_adv_*.csv` | E3, E6 (heuristics) |
| B | `s1_run.py --what adv --units nba_seasons` | `parts/s1_adv_nba<year>.csv` (69 seasons) | E3, E4 |
| C | `s2_controls.py --tasks syn,sub,arena6` | `s2_controls_syn_sub_arena6.csv` (SYNTHETIC rows: `kind=syn`) | E4 controls |
| D | `s2_matched.py --human-draws 20 --B 1000` | `s2_matched_*.csv` | E5 |
| D | `s1_exhaustive.py --instances 60 --m 60,80,100 --kmax 5` | `s1_exhaustive.csv` | E6 |
| E | `s3_extra.py --what rigging` / `ablation` / `uncert` | `s3_rigging.csv`, `s3_ablations.csv`, `s3_uncert.csv` | E8, E7, E3 intervals |
| collect0 | `s2_collect.py`, `s3_influence.py` | `budgets_remove.csv`, `random_all.csv`, `s3_influence.csv` | E2-E4 |
| F | `s5_cluster.py` / `s5_constrained.py` / `s5_noise.py` | `s5_cluster_se.csv` (#7) / `s5_constrained.csv` (#8a) / `s5_noise.csv` (#8b) | cluster SE, constrained adversary, noise-equivalent budget |
| G | `s5_estimator.py` / `s5_published.py` / `s5_restarts.py` | `s5_estimator*.csv` (#9b) / `parts/s5_published_*.csv` (#9a) / `parts/s5_restarts_*.csv` (#10a) | estimator sensitivity, published-output claims, randomised restarts |
| H | `s5_control.py --D 40` / `s5_window.py --part score`, `--part count` | `s5_control_*.csv` (#10c) / `parts/s5_window_*.csv` (#6 sweep) | Arena-six vs MT-Bench intervals, window sweep |
| collect | `s3_models.py --B 2000`, `s4_export.py`, `s5_window.py --part merge`, `--part support`, `s5_merge.py`, `s5_zshares.py`, `s5_oos.py --B 2000` | `s3_models_*.csv` (incl. `M0c`/`M1c`), tidy tables, `s5_window_*.csv`, `s5_nba_eras*.csv`, `s5_published*.csv`, `s5_restarts*.csv`, `s5_z_shares.csv`, `s5_khat.csv`, `s5_oos_summary.csv`, `s5_collinearity.csv` | E2-E8, #6, #7, #9-#11 |

Seeds: random perturbations `default_rng([1, f_index, seed])` (200 seeds; bootstrap 1000); bootstrap for base-fit intervals
`default_rng([0, 10000 + b])`; z-gap bootstrap `[2, 10000 + b]`; random-removal reference for the leverage `[3, a, b, k, s]`;
heuristic baselines `[4, a, b, s]`; matched human draws `[7, d]`; controls `[11, crc32(kind|name|par), rep]`; budget uncertainty
`[21, sum(ord(name)), b]`; the claim-level and cluster bootstraps in `s3_models.py`/`s4_export.py` use fixed seeds in the code.

## Run times
Measured wall seconds per step (jobs shared a 40-CPU host with other jobs, so these are upper bounds): `results/runtimes.csv`
(`group,command,seconds`; the command may contain commas, the last field is the seconds). Per-fit costs: warm-started Newton fit 0.3 ms on Arena-55k, 5 ms cold.

## Script to artifact map
`btlib/core.py` (fitter, influence, greedy/one-shot/polish/relabel search, heuristics), `btlib/analysis.py` (claims, perturbation
samplers, budgets), `btlib/report.py` (per-claim tables), `btlib/units.py` (leaderboard units), `btlib/data.py` (loaders +
checksums), `btlib/prov.py` (provenance). Scripts as in the table above.

## Provenance notes
- Each `*.meta.json` records `code_rev` = HEAD when its script finished, and `+dirty` if `code/` had uncommitted changes. The compute jobs started at commit
  265a2b5 (`s0_base`, `s1_run`, `s2_controls`, `s3_extra`, `s1_exhaustive` and everything in `btlib/` except the removal of the judge-data checksums from `btlib/data.py`
  are byte-identical in every later commit, see `git diff 265a2b5 <code_rev> -- code`); later commits changed only `s2_matched.py`
  (a robustness variant and removal of the cut judge comparison; `s2_matched` was rerun after that change), `s3_models.py`, `s3_influence.py`,
  `s4_export.py` and the docs. `s0_base.meta.json` and `s1_random.meta.json` therefore name 265a2b5, `s1_adv.meta.json` (written by the last
  of the two adversarial jobs) the later commit.
- Failed/abandoned runs: an earlier run of the stage-1 sweeps on a development tree (`+dirty` metas) was discarded and rerun in full
  from the committed tree before any number was used; a greedy search that was non-optimal in one instance (92 vs 91 on a direct cell)
  led to the added `polish` step; no other runs were abandoned.
- Restricted material: the paper listed as item 8 of the starter reading, and anything citing it, was not read or searched
  (incident log: none).
- LLM assistance: the code, analyses and these notes were written with Claude (Anthropic); every number comes from the code here.
- MT-Bench matched keys: 80 questions x 2 turns x 15 model pairs = 2,400 keys (question, turn, unordered model pair), all present in the GPT-4 file (one verdict each); the
  human file covers 1,814 of them (3,355 judgments). The plan's two figures are counts of ORDER-SENSITIVE keys (question, turn, model_a, model_b as presented to the judge):
  the human file has 2,396 distinct ordered keys (the same 1,814 unordered keys, some presented in both orders), the GPT-4 file 2,400, and 1,232 ordered keys occur in both files.
  The 1,232-key set is used, as the robustness variant `mt_human_ordmatched` / `mt_gpt4_ordmatched` (human judgments on those keys: 1,751) in `s2_matched.py` and the row
  `mt_human_ordmatched_vs_gpt4_ordmatched_1232keys` of `matched_pairs.csv`; the headline matched comparison uses the 1,814 unordered keys.
- Second round (requests of paper-repo #7-#12 and internal-review #6): scripts `s5_*.py` and the revised Arena / NBA-all claim set were run as separate jobs from the working tree
  (each `*.meta.json` records `code_rev` and `+dirty`; `core.adversarial_flip` gained the `gain_noise` option for the restarts and `s3_models.py` the `M0c`/`M1c` models while
  other jobs were running, with unchanged defaults, so no earlier output depends on the change). `s5_published.py` first gave empty budgets in a pilot because the
  perturbed counts were formed with the wrong sign of `delta`; fixed and rerun before any number was used. Intervals of `s5_control_summary.csv` are conditional on the single
  realised set of 1,367 Arena battles and the 3,355 MT-Bench judgments (resampling variation only).
