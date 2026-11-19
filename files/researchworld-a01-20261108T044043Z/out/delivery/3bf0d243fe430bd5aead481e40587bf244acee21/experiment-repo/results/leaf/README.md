# OLLB leaf-task run (request experiment-repo#8: does the n = 6 OLLB picture survive a finer partition?)

**Gate (passed on 499 of the 500 best-ranked models).** Source: `open-llm-leaderboard/results` at commit
`aa81ecc38fdc5708254b833923368970efdf5ef5`, all result files of the 500 models best ranked under the six-task mean (the `ollb_top500`
slice). Rule for models with several result files: the latest file whose six task-level raw metrics equal the `Raw` columns of the
processed leaderboard table (|diff| < 1e-6; BBH and MuSR `Raw` are unweighted means of their leaves, IFEval the mean of the two strict
accuracies, the rest the aggregate). 372 of the 500 models have several files; the chosen file is the model's latest file for 498 of
the 499 covered models (e.g. the first calme-3.2 file differs from the published MATH score by 0.004 and is rejected by the rule).
499 models have a validated file with all 39 leaves; **one model (rank 432, `VAGOsolutions/SauerkrautLM-v2-14b-DPO`) has no file that
reproduces its published raw scores and is left out (missing fraction 0.002); no value is imputed** (`results/ollb_leaves_gate.json`,
`data/processed/ollb_leaves.csv`, built by `code/fetch_ollb_leaves.py` + `code/build_ollb_leaves.py`).
**Source provenance:** `results/leaf/source_manifest.csv` lists every retrieved result file (1,018 files of the 500 models: path in the pinned commit, git object id,
SHA-256 of the downloaded bytes and of the reduced record kept in the retrieval's `leaves.jsonl`); `results/leaf/selected_files.csv` is the file the file rule chose for
each model (the one rejected model is listed as `no_matching_file`); `results/leaf/source_digests.json` and the `source` block of `results/ollb_leaves_gate.json`
hold the SHA-256 of the reduced `leaves.jsonl` and of `files.csv`. A second retrieval reproduced `leaves.jsonl` byte for byte (identical SHA-256).
Score components: 24 BBH, 3 GPQA, 7 MATH-hard, 3 MuSR, MMLU-PRO, IFEval = 39. They are the leaderboard's score components, **not 39 disjoint
subtasks**: the three GPQA components (diamond, main, extended) are nested, overlapping variants of one question set (by the dataset's construction
diamond is a subset of main, and main of extended; item-level overlap was not verified here, because only aggregated accuracies are used), so the leaf
partition counts GPQA questions more than once and weights GPQA by three of 39 components. The same holds for the item-count-weighted published GPQA
aggregate. Read the leaf run as "a finer partition of the leaderboard's own components", not as 39 independent measurements. Leaf score = raw accuracy normalised as the leaderboard does
(random baseline 1/num_choices from the task configs, clipped at 0; MATH, IFEval baseline 0), 0..100. Check: the mean of the normalised
leaves reproduces the published normalised BBH, MuSR and MMLU-PRO scores of all 499 models to 3e-14. The published GPQA score is the
aggregate over the three leaves weighted by item count, so the leaf mean differs from it (max 1.8 points); MATH and IFEval have no
leaf-level published score.

**What is run** (`code/run_leaf.sh`, `code/assemble_leaf.py`; ~11 min of compute, no MILP time limit hit, nothing censored):
the 39-leaf matrix (`ollb_leaf`) and, as the comparator, the six published tasks of the same 499 models (`ollb6_leafslice`), same rules and
caps: mean, median, min on all 499 targets; Borda, Condorcet, plurality on the 50 best targets (by each partition's own mean rank);
caps `ceil`, `gain10`, and `emp99task` (OLLB-six `emp99` for the six-task side).
* **Per-leaf `emp99` was not run:** the 499-model slice has only 23 (fine-tune, base) pairs, too few to take a per-leaf 99th percentile.
  `emp99task` gives every leaf the empirical 99th-percentile gain of its parent task (from all OLLB pairs, as in the core grid),
  a transfer assumption; it is not a per-leaf estimate.
* Copeland and the evaluation-noise and leaf-resampling intervals were not run for the leaf partition. Intervals here are the
  bootstrap 95% CIs over targets within rank strata of the core grid (`summarize.py`); the feasible share is in every `*_infeasible` column.

**Reading it.** (1) The leaf mean is not the leaderboard average: BBH is 24 of 39 leaves, so the leaf-mean and six-task-mean
rankings of these models correlate 0.81 and a target's rank stratum differs between the two partitions. Strata in
`summary_leaf_groups.csv` use each partition's own mean rank; `paired_leaf_vs_six.csv` pairs the same model and groups by its six-task rank.
(2) L1 grows with the number of tasks for score rules, so compare per task (`L1_per_task`, `L1_per_task_ratio_med` = ratio x 6/39).
(3) Files: `core_leaf.csv` (one row per cap x rule x target, same columns and status as `core_ollb.csv`), `summary_leaf_groups.csv`,
`summary_leaf_relL1_vs_mean.csv`, `frontier_leaf.csv`, `paired_leaf_vs_six.csv`; `runs_*.csv` are the raw run files.
