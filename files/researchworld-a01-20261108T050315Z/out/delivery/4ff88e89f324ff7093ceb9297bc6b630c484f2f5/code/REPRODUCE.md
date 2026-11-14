# Reproduction notes — minimum targeted investment to top a multi-task leaderboard

Everything under `code/` is produced by the scripts in `code/src/`; every number in the paper's tables and figures comes from
`results/tidy/*.csv.gz` and `results/tables/*.csv`, which `src/consolidate.py` builds from the raw experiment CSVs
(`results/raw/*.csv.xz`; `consolidate.py` unpacks them to `results/*.csv` when those are absent; SHA-256 of the uncompressed CSVs in `results/MANIFEST.sha256.json`). Nothing is typed in by hand.

**Status.** Final for this delivery: all jobs listed in §6 have ended; §7 lists what exists and what was not computed.

## 1. Environment

| item | version |
|---|---|
| Python | 3.11.2 |
| numpy / scipy / pandas | 2.4.6 / 1.17.1 / 3.0.6 |
| MILP solver | HiGHS through `scipy.optimize.milp` (scipy 1.17.1) |
| tests | pytest (`python3 -m pytest -q tests`, 10 tests, about 70 s) |
| hardware | CPU only; sandbox jobs of 2 CPUs and under 1 GB each, on a shared, heavily loaded host (wall-clock times below are inflated by that) |

No GPU. Seeds: `--seed 0` everywhere (target sampling, bootstrap, noise draws, theory instances). Re-running gives identical output
(HiGHS is deterministic for these models; the MILP rows that hit the time limit are flagged, see §5).

## 2. Data (acquire once, needs network)

| dataset | source | pinned version | built into |
|---|---|---|---|
| Open LLM Leaderboard v2 (OLLB), 6 tasks: IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO | HF dataset `open-llm-leaderboard/contents` (parquet) | commit `9c09a7cae43334062a82cb164f2ef255013dafa2`; file SHA-256 in `data/processed/manifest.json` | `data/processed/ollb6.csv` (4,497 models after dropping 79 duplicate `fullname`s, best-scoring variant kept; the experiments use the 4,496 unflagged ones, since `newsbang/Homer-v0.5-Qwen2.5-7B` is flagged and removed from targets and rivals alike (`mti/data.py`: `d[~d.Flagged]`); submission dates 2024-06-08 to 2025-03-13) |
| OLLB per-item/raw sub-scores (evaluation-noise model) | HF dataset `open-llm-leaderboard/results` | commit `aa81ecc38fdc5708254b833923368970efdf5ef5` (10.5k JSON files, SHA-256 per file) | `data/processed/ollb_noise.json` |
| HELM MMLU, 57 subjects, 79 models, exact-match | `gs://crfm-helm-public/mmlu/benchmark_output/releases/v1.13.0/` | release v1.13.0, SHA-256 of all 303 files in the manifest written by `fetch_helm.py` | `data/processed/helm_mmlu57.csv` (+ `helm_mmlu_all.csv`, `helm_mmlu_neval.csv`) |

```
python3 src/fetch_helm.py        /data/helm/v1.13.0
python3 src/fetch_ollb_results.py /data/ollb_results           # only for the noise model
# download train-00000-of-00001.parquet of open-llm-leaderboard/contents at the commit above
python3 src/build_data.py /data/ollb/train-00000-of-00001.parquet /data/helm/v1.13.0 data/processed
python3 src/ollb_items.py                                      # data/processed/ollb_noise.json
```
The processed files are delivered (`data/processed/`, 2 MB), so every experiment below runs offline.

Licences: OLLB `contents` carries no licence declaration on the dataset card that this work could verify; HELM outputs are published by
Stanford CRFM (public bucket; licence not checked per file). Neither is redistributed beyond the derived score matrices in `data/processed/`
(model names and scores only). Per-model licences are in the OLLB `Hub License` column and are blank for 1,736 of 4,497 models.

Snapshot caveat: both leaderboards are frozen snapshots (OLLB up to 2025-03-13; HELM v1.13.0); rankings and all costs refer to
those snapshots.

## 3. Commands

`run.sh` holds the main and robustness experiments, `run_extra.sh` the feasibility / baseline quantities, eps sensitivity, theory checks and
the consolidation. Targets are independent offline processes and can run in parallel (that is how they were run, one `local-compute` job each).

```
./run.sh test                      # unit tests: solvers vs brute force, Copeland vs naive, data reproduces the published averages
./run.sh main_helm main_helm_pow   # HELM, all rules and caps (79 targets)
./run.sh main_ollb_closed main_ollb_closed_emp   # OLLB, score rules, all 4,496 targets
./run.sh main_ollb_ord_a main_ollb_ord_b main_ollb_ord_c   # OLLB, ordinal MILPs on the rank-stratified sample (136 targets)
./run.sh std_z_closed std_z_ord std_pct_closed time_milp  # standardised OLLB variants; MILP timing at M=4,496
./run.sh rob_slices_a rob_slices_b rob_noise_helm rob_noise_ollb rob_taskboot rob_tasksub   # robustness
./run_extra.sh helm_empm x_helm x_ollb_score x_ollb_ord x_ollbz x_ollbpct eps_helm eps_ollb_score eps_ollb_ord theory
./run_extra.sh consolidate         # results/tidy, results/tables, results/MANIFEST.sha256.json
```
(`run.sh` and `run_extra.sh` are bash; each target is a function at the top of the file with the exact `python3 src/...` command line.)

## 4. What the code computes (definitions the tables rely on)

* Instance: score matrix X (M models x T tasks, higher is better), target i, rivals fixed. The target may raise its score on task t anywhere in
  [x_t, cap_t]; cap scenarios: `ceil` (task maximum, 100 on both datasets), `front0/front2` (best rival's score on t, plus 0 / 2 points),
  `gain5/10/20` (h raw points), `emp95/emp99` (OLLB: per-task percentile of the observed fine-tune-minus-base gain, 540 base/fine-tune pairs),
  `empm95/empm99` (HELM proxy: the OLLB MMLU-PRO percentile applied to every subject), `sgain<h>` (h standardised units).
* "First": strictly above every rival; margin eps = 1e-3 score points for score rules, strict for ordinal rules. eps = 0 is only a tie
  sensitivity for score rules (`tie_flag`); it is degenerate for the ordinal solvers and left NaN there.
* Three separate optima per (rule, target, cap): `L1_star` (minimum total points), `K_star` (minimum number of tasks touched), `Linf_star`
  (smallest largest single-task lift, bisection). `feasible = 0` when even full investment at the caps cannot make the target first
  (the optima are NaN, never imputed). Because all rules are monotone in the target's own scores, feasibility at cap c is the same as being
  first at y = c, `d_star` (smallest uniform lift) equals `Linf_star` at the ceiling, and the minimal feasible cap parameters
  (`min_front_margin`, `min_emp95_mult`) follow by bisection (`src/mti/feas.py`). `L1_prop` is a headroom-proportional allocation baseline.
* Score rules: exact closed forms (mean, min, median, trimmed mean) or exact convex/greedy solvers (geometric, harmonic and power means),
  checked against brute force (`tests/`). Ordinal rules: Borda, Condorcet (strict-majority winner; an upper bound for any Condorcet-consistent
  rule such as Copeland), plurality: exact MILPs (HiGHS) with lazy rival-constraint generation (no M x K matrix; about 350 MB at M = 4,496).
* Cohorts: score rules run on all targets (`cohort = full`); on OLLB the ordinal MILPs run on a rank-stratified sample (`cohort = sample`,
  `in_sample = 1`: ranks 2-21 plus log-uniform tail targets; 136 targets) with `weight` = stratum population / sampled count, so weighted
  statistics estimate the full-leaderboard quantity; HELM runs every target for every rule. Cross-rule comparisons are made on the
  common feasible cohort (targets with a result under both rules; the denominator is reported in `results/tables/rel_L1_vs_mean_*.csv`).
  `rank_mean` is the target's rank under the plain mean and defines the strata.
* Standardised OLLB variants (`ollb_z`: per-task z-score, only mean / median / min / trimmed mean, caps in SD units; `ollb_pct`: rank
  percentile in (0, 100], all score rules); transform anchors are fixed from the snapshot. Ordinal rules are invariant to monotone per-task
  transforms, so K* and feasibility under z / pct equal raw OLLB at the same raw-level caps; the ordinal z run is therefore restricted to
  caps `ceil, sgain1` on a 60-target sample as a check, not as new evidence.
* Intervals: the sampling unit is the target (1,000 bootstrap resamples of targets, percentile 95% intervals of the stratum-weighted median); with only 79 models on HELM they describe the 78 non-leader targets, not a population of leaderboards.
  Evaluation-noise draws (R = 100 / 100) and task bootstrap / subset draws are labelled *conditional sensitivity*: they resample the
  scores or tasks of this snapshot and do not estimate sampling variation of a leaderboard.

## 5. Output map (script -> output -> where it is used)

| output | script (command) | content |
|---|---|---|
| `results/raw/helm_main.csv.xz`, `helm_pow`, `helm_empm` | `run_core.py helm ...` | HELM, every rule x cap x target |
| `results/raw/ollb_closed`, `ollb_closed_emp`, `ollb_ord_{a,b,c}` | `run_core.py ollb ...` | OLLB, score rules (all targets), ordinal rules (sample) |
| `results/raw/ollbz_*`, `ollbpct_*`, `slice_ollb_{nomerge,top500,raw}_*` | `run_core.py ollb_z / ollb_pct / ollb_nomerge ...` | standardised variants and leaderboard slices (no merged models; top-500 by average; raw instead of normalised scores) |
| `results/raw/extra_*`, `eps_*` | `run_extra.py`, `run_core.py --eps` | feasibility, min feasible caps, uniform lift, proportional allocation; eps sensitivity |
| `results/raw/*noise*`, `*taskboot*`, `*tasksub*` | `run_robust.py` | evaluation noise, task bootstrap, task-subset scaling |
| `results/theory_checks.csv` | `theory_checks.py` | propositions P1-P4 (closed forms for mean, median, min; Linf = uniform lift) against the solvers |
| `results/time_milp_ollb.csv` | `time_milp.py` | MILP time per solve at M = 4,496 (columns `sec_L1_milp`, `sec_K_milp`) |
| `results/tidy/<set>.csv.gz` | `consolidate.py` | the tidy schema (see the docstring at the top of `src/consolidate.py`), one file per data set |
| `results/tables/*.csv` | `consolidate.py` | cost by stratum, pooled costs with intervals, relative cost vs mean, eps sensitivity, robustness summaries |

MILP bookkeeping: each ordinal solve now has a 600 s limit and the raw CSV stores `milp_status` (`optimal` / `time_limit`; a time-limit
incumbent is an upper bound, not a minimum) and `sec` (seconds). The main OLLB ordinal runs (`ollb_ord_a/b/c`) were started before this
change: they used a 120 s limit and did not store the status. For them the evidence that no solve silently failed is an independent check:
`feas.py` decides feasibility without a MILP, and `results/tables/completeness.csv` reports, per (data set, cap, rule), how many rows were
checked (`n_xchecked`) and how many disagree with the solver's finite / infinite answer (`n_xmismatch`); a time-limited solve without
incumbent would show up as a mismatch. A time-limited *incumbent* would not (it is finite), so costs of those older ordinal runs are
exact minimums only to the extent that no solve reached 120 s; the slowest solve measured at M = 4,496 was 115 s (`time_milp_ollb.csv`).
(`gap` in the raw files is the target's score gap to the best rival under the rule, not a solver gap.)

## 6. Run log (wall-clock on the shared host)

See `logs/` (kept in the repository; HiGHS output removed from the delivered copies) for per-run timings (`<cap> <rule> done <s>s` lines);
job start / end times are those of the `local-compute` jobs of this position, all started on 2026-11-08 (UTC):

| log | what | wall-clock to last solve (s) | note |
|---|---|---|---|
| `main_helm`, `main_helm_pow`, `helm_empm` | HELM, all rules and caps | 862, 6, 45 | all targets |
| `main_ollb_closed`, `main_ollb_closed_emp` | OLLB score rules, 4,496 targets | 2164, 116 | |
| `main_ollb_ord_b`, `main_ollb_ord_c` | OLLB ordinal, gain / empirical caps, 136 targets | 4984, 2598 | trailing `.csv: command not found` in the log: a shell artefact of editing `run.sh` while the job ran; the CSV is complete (12 and 8 cap x rule cells x 136 targets) |
| `main_ollb_ord_a` | OLLB ordinal, `ceil, front0` (job was started with `ceil,front0,front2` and stopped by hand after `front0`, 6,737 s) | 3,396 (ceil), 6,737 (front0) | Borda at `ceil`: 1,824 s for 136 targets (13 s per solve); at `front0`: 2,215 s |
| `ord_front2_{borda,condorcet,plurality_trimmed1}` | OLLB ordinal at the headline cap `front2`, run as three parallel jobs started 07:44 UTC (`milp_status` and `sec` recorded) | 1,698 / 890 / 71 | all 136 + 136 + 272 solves `optimal` |
| `resolve_front0_borda` | one `front0` Borda L1 solve (target 3591) that had returned no incumbent in the 120 s run, found by the solver-vs-independent check; re-solved with the 600 s limit | 44 | optimal, L1 = 209.68; replaces the old row in the tidy file |
| `std_z_closed`, `std_pct_closed`, `std_z_ord` | standardised variants | 4720, 511, 2113 | `std_z_ord` relaunched with the lazy MILP at caps `ceil, sgain1` and 60 targets after an out-of-memory kill of the first launch (dense M x K matrices) |
| `rob_slices_a`, `rob_slices_b`, `slice_raw_ord` | leaderboard slices (no-merge, top-500, raw scores) | about 6,200 (a), 266 (b), 2,573 (raw ordinal) | the ordinal part of `rob_slices_b` was killed (out of memory, before the lazy MILP) and re-run as `slice_raw_ord` (caps `ceil, gain10`, 60 targets) |
| `rob_noise_helm`, `rob_noise_ollb`, `rob_taskboot`, `rob_tasksub` | evaluation noise (100 + 100 draws), task bootstrap (200 OLLB + 100 HELM draws), task subsets (100 draws per size and cap) | 2,538; about 12,000; about 11,000 + 400; n/a | `rob_tasksub` prints nothing; its CSVs hold all draws. `.csv: command not found` at the end of some logs is the shell artefact described above |
| `x_helm`, `x_ollb_score`, `x_ollb_ord`, `x_ollbpct`, `x_ollbz` | feasibility / baseline quantities | 7, 209, 37, 33, 123 | |
| `eps_helm`, `eps_ollb_score`, `eps_ollb_ord` | eps sensitivity | 716, 101, 1531 | eps = 0 only for score rules |
| `theory` | propositions P1-P4 (31,080 instances) | about 25 min | first run flagged 15% of P4 rows by 1e-5…5e-5 (bisection bracket); tolerance set to 1e-4 and re-run: all instances agree |
| `time_milp` | per-solve MILP time, M = 4,496 | see `results/time_milp_ollb.csv` | median per solve at cap `ceil`: Borda 8.3 s (max 115 s) for L1, 5.2 s for K; Condorcet 5.6 s (max 72 s) / 4.3 s; plurality 0.2 s; vectorised Copeland scores for M = 4,496: 3.1 s |

Per-solve MILP times are also stored for every ordinal row after the status change (`sec`).

## 7. Completeness and caveats

`results/tables/completeness.csv` lists, for every (data set, cap, rule) in the tidy files, the targets present against the expected cohort size, the
number of rows cross-checked against the independent feasibility test and the number of mismatches, and the number of solves at the MILP time
limit. At the end of the runs every listed cell is complete (350 of 350), 564k rows were cross-checked, 1 mismatch (OLLB `front0` Borda,
target 3591, the 120 s-limit case re-solved above, now 0), no recorded solve ended at the time limit.

Cells and their sizes: HELM, all rules x 8 caps x 79 targets (the 78 non-leaders enter the tables); OLLB score rules, 9 rules (mean, geometric, harmonic, power means, median, min) x 8 caps x 4,496
targets; OLLB ordinal (Borda, Condorcet, plurality) and trimmed mean, 8 caps x 136 targets;
`ollb_z`: mean, median, min at 5 caps, 4,496 targets; ordinal Borda / Condorcet at `ceil, sgain1` on the `--nsample 60` stratified sample (72 targets; check); `ollb_pct`: all score rules at
`ceil, front0, sgain10, sgain25`; `ollb_nomerge` and `ollb_top500`: `ceil, front0, gain10` (ordinal on the stratified sample: 136 targets, 116 for top-500); `ollb_raw`: score rules at
the same three caps and a `--nsample 60` (72-target) ordinal check at `ceil, gain10`. Cells not run: `front0`/`front2` for the z and percentile ordinal variants
(rank invariance), the plurality / trimmed-mean rules in `ollb_z` / `ollb_raw` ordinal checks, and ordinal rules at eps = 0 (degenerate).

* `min_front_margin` (minimal best-rival margin) is 0 for every rule and target: capping at the best rival's score on every task already
  beats every rival. It is stored for completeness; the informative minimal-cap quantities are `d_star` and `min_emp95_mult`.
* HELM cap `empm*` is a proxy: the empirical gain distribution exists only for OLLB, and HELM subjects borrow its MMLU-PRO percentile.
* Condorcet is the strict-majority-winner condition; it upper-bounds the cost under any Condorcet-consistent rule (Copeland, Schulze, ...).
  Copeland itself is computed exactly (vectorised, any M) only as the rank used to order targets under that rule.
* Plurality on a score matrix counts per-task winners; with 6 or 57 tasks many targets are infeasible at small caps — see `feasible`.
* Costs in raw points are unit-dependent across tasks (OLLB tasks have different spreads); the standardised variants and the
  stratum-wise relative-to-mean costs are given for that reason.

## 8. Prohibited material log

The published paper on this question was not searched for or read by this position, and no page about it was encountered. (Nothing to log.)

## 9. Use of LLM agents

All code, experiments and analysis text in this package were produced by LLM agents (Claude, via Claude Code) working as a research
organisation; humans did not edit them. The agent is responsible for any error: results are reproducible from the code and the pinned
inputs above, and the test suite checks the solvers against brute force.
