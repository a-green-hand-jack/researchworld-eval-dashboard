# Minimum targeted investment to top a multi-task leaderboard — code, results, reproduction notes

How much targeted investment (raising a target model's scores on chosen sub-datasets) does a model need to rank **first**, and how does that
depend on the aggregation rule? This repository holds the exact solvers, the experiment drivers, the result files and the analysis. In
`paper-repo` it is delivered under `code/` (source, tests, job scripts, notes, compact outputs); the per-instance result CSVs stay here
(see "Result files").

**Provenance statement.** All code, experiments and analyses were produced by AI agents (Claude models, run through the ResearchWorld /
Claude Code harness) working autonomously; no human wrote or ran any of it. Every number in the paper must come from the files listed in
`results/MANIFEST.md`.

## 1. Setting (conventions used everywhere)

* Score matrix `X` (m models x n sub-datasets), higher is better. The *target* model may raise its score on task t to any value in
  `[x_t, cap_t]`; all other models are fixed (single deviator, no reaction by others).
* **First** = strictly above every rival under the rule, with margin eps = 1e-3 points for score rules; Borda: Borda total (points per task
  = models strictly below + 0.5 per tie) larger than every rival's by at least 0.5; Condorcet winner: strict majority of tasks against every
  rival; plurality: strictly more first-place credit than every rival (tied first places share the credit), margin 1e-4. A target may tie a
  rival's task score (half credit) unless `--no-tie-levels`; eps/tie sensitivity runs are in `analysis/robust_eps_ties.csv`.
* **Costs**: K = number of tasks touched, L1 = total score points added, Linf = largest single-task jump (each minimised separately,
  exactly). `n*Linf` is the cost of the uniform "general improvement" with the same largest jump (claim C5).
* **Caps**: `ceil` (task maximum of the scale), `front0`/`front2` (best rival value on the task, +0/+2 points), `gain5/10/20` (at most 5/10/20 points
  above the current score), `emp95/emp99` (95th/99th percentile of the empirical fine-tune-minus-base gains of OLLB pairs; OLLB only, HELM has none).
* **INF = proven infeasible** under the cap (`feasible=0`, L1/K/Linf = +inf); **NaN = solver time-out** (`censored=1`, with `*_lb`/`*_ub`
  bounds and HiGHS status/gap per solve in `<m>_status`). Measured: **0 time-outs in 260,572 solves**, so no censoring correction was needed.
  Infeasible targets are explicit rows, never dropped.
* Rank groups (strata) are by the target's rank under the plain mean: 2, 3-5, 6-10, 11-30, 31-100, 101-500, >500 (rank 1 has nothing to do).

Data: **OLLB** `open-llm-leaderboard/contents` @ `9c09a7cae43334062a82cb164f2ef255013dafa2` (last updated 2025-03-20), 6 tasks
(IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO; the leaderboard's *normalised* scores, mean of normalised scores = the OLLB rule). 4576 rows,
79 duplicate `fullname` rows dropped (best-scoring variant kept), 4497 used, one flagged submission removed in `mti.data.load`, so the score
matrix has 4496 models and every one is a target (the leader's cost is 0). **HELM MMLU** release v1.13.0
(2025-01-10), 57 subjects, 79 models (all complete). Version choice follows `/initial-state` (v1.13.0).

## 2. Exact solvers (`src/mti/`)

* `scorerules.py` — mean and weighted means (closed form for L1; greedy on headroom for K), power means (geometric = p 0, harmonic = p -1,
  p -5; power mean of score+1; water-level for L1, greedy for K), median and min (closed forms; exact for odd and even n), trimmed mean t=1 (n-binary MILP),
  Linf by bisection on a monotone value function.
* `ordinal.py` — Borda, Condorcet-winner requirement, plurality as MILPs with lazy rival constraints (HiGHS through `scipy.optimize.milp`,
  `TIME_LIMIT=120 s`, `MIP_REL_GAP=1e-9`). Condorcet is **sufficient** for first under any Condorcet-consistent rule (an upper bound for
  Copeland/Schulze/Kemeny), not necessary. Copeland itself was **not** computed (optional item of the plan).
* `tests/` — solvers against brute force on small random instances (`python3 -m pytest -q tests`, 10 tests, ~1 min).
* `src/theory_checks.py` — closed forms coded independently of the solvers (mean, min, median L1 and K; bounds `Linf <= L1 <= n*Linf`;
  task-subset identity for the mean) versus solver output on every instance: **all PASS** (`results/theory_checks.txt`, per-instance
  `results/theory_pairs.csv`, max |difference| ~ 1e-13).

## 3. Environment

Python 3.11.2, numpy 2.4.6, scipy 1.17.1 (bundled HiGHS), pandas 3.0.6, pyarrow 26.0.0, pytest 9.2.0 (`requirements.txt`). CPU only; jobs
ran in 2-CPU containers on a shared host (wall time therefore exceeds CPU time, often several-fold).

## 4. Data steps and checksums

`make data` (needs network) runs `src/fetch_helm.py`, `src/fetch_ollb.py`, `src/build_data.py`, `src/ollb_items.py` and, for the follow-up analyses of section 9, `src/build_dup_variants.py`, `src/ollb_items_check.py`, `src/helm_subject_sizes.py`. The built matrices are
committed (`data/processed/`) and were rebuilt byte-identically from the raw files.

| input | identifier | SHA-256 |
|---|---|---|
| OLLB `data/train-00000-of-00001.parquet` | commit `9c09a7cae43334062a82cb164f2ef255013dafa2` | `f13a7061e63133bc8745d89f8c7a56148584940ede22d3b27e21cad1e078dca5` |
| HELM v1.13.0 (303 files, `mmlu/benchmark_output/releases/v1.13.0/`, fetched 2026-11) | per-file hashes in `data/processed/helm_v1.13.0_files.sha256.json` | manifest file `830bdb10a5518c50689d60c86623cc3d79ff5317d7e6b96408ea7dc2058de12b` |
| processed matrices `data/processed/*` | `src/build_data.py` | listed in `results/MANIFEST.md` |

`ollb_noise.json` (per-task item counts and chance floors) is the only input to the evaluation-noise Monte Carlo (OLLB side). It is built by
`src/ollb_items.py` from the `n-samples` field of **one** pinned file of the OLLB `results` dataset (@ `aa81ecc38fdc5708254b833923368970efdf5ef5`,
`0-hero/Matter-0.2-7B-DPO/results_2024-08-07T13-21-02.903091.json`) and the Raw/normalised column pairs of `contents`. That one file stands for all models because the item counts do not vary: `src/ollb_items_check.py` read the latest complete results file of 60 randomly sampled models of the same snapshot and found one and the same count vector (IFEval 541, BBH 5761, MATH Lvl 5 1324, GPQA 1192, MUSR 756, MMLU-PRO 12032; `results/analysis/ollb_item_counts_check.csv`; the only exception, an early partial run of one model with BBH only, is skipped by the script and counted). Item counts are a property of the leaderboard's fixed task set, not of the evaluated model.

## 5. Commands, seeds, runtimes

Everything is deterministic given the seeds: rank-stratified target sample `--seed 0` (ranks 2-21 plus 150 log-uniform in rank, 136 distinct
targets), Dirichlet weights seed `1000+k`, Monte-Carlo draws `--seed 0` (R=100 noise / task-bootstrap draws, R=50 task-subset draws),
bootstrap over targets B=1000 seed 0.

```
bash reproduce.sh # OFFLINE REPRODUCTION FROM THE DELIVERED TREE (no make needed): unpack results/instances/*.csv.gz, regenerate
                  # ollb_powmeans_weighted.csv, run analyze.py + analyze_robust.py + theory_checks.py, compare all files with MANIFEST.json
make reproduce    # the same steps through make
make tests        # solver unit tests
make experiments  # re-run every solver job from data/processed/ (all jobs/*.sh; independent, run with make -j)
make analysis     # python3 src/analyze.py --B 1000 --seed 0 ; src/analyze_robust.py ; src/analyze_fits.py ; src/analyze_capcomp.py ; src/analyze_dup_rule.py ; src/score_cap_defence.py
make theory       # closed forms vs solvers
make manifest     # results/MANIFEST.md|json (SHA-256 and one-line convention for every result file)
make verify       # compare the files present with results/MANIFEST.json (src/verify_manifest.py)
```

**Measured cost** (solver CPU seconds recorded per solve, `results/analysis/censoring_and_cpu.csv`; the first column of each log line gives wall time):

| block | targets | CPU |
|---|---|---|
| OLLB score rules, all 8 caps, all 4496 targets (6 rules incl. trimmed-mean MILP) | 4496 | 0.26 CPU-h |
| OLLB power means + 20 weighted means, 8 caps | 4496 | 0.06 CPU-h |
| OLLB ordinal rules on the sample (Borda, Condorcet x 4 main caps) | 136 | 1.78 CPU-h (Borda 0.99, Condorcet 0.79) |
| OLLB plurality, 8 caps on the sample + top-500 slice on 4 caps | 136 / 500 | 0.13 CPU-h |
| HELM, 6 caps, 10 rules incl. Borda, Condorcet, plurality, trimmed mean | 78 | 0.27 CPU-h |
| data-slice variants, eps and tie runs (OLLB + HELM) | various | 0.77 CPU-h |
| **sum of measured solver CPU** | 260,572 solves | **3.25 CPU-h** (core grid in `censoring_and_cpu.csv`: 2.45 CPU-h) |

Ordinal rules on the plan's four main caps: Borda 0.33/0.15/0.20/0.32 CPU-h and Condorcet 0.29/0.14/0.07/0.29 CPU-h for ceil/emp95/gain10/front2
(1.82 CPU-h with plurality), inside the plan's ~4 CPU-h bound for ordinal compute. The noise / task-bootstrap / task-subset replicate runs
(`jobs/*_robust.sh`) did not record per-solve CPU; their wall times are 2-30 min each (see `logs/`). The scheduler's own accounting of all jobs
of this position (including data builds, the analysis, the tests, aborted and repeated runs) is about 7.7 CPU-h, i.e. **above** the objective's
rough 4 CPU-h estimate for the whole project; the *required* grid fits in it, the robustness/sensitivity extras and development reruns do not.
**Reconciling the three runtime numbers:** 3.25 CPU-h is the recorded HiGHS/solver CPU of the 260,572 solves; 7.7 CPU-h is the scheduler's CPU accounting of every job of this position
(including the unrecorded replicate runs, data builds, analysis, tests, aborted and repeated runs); ~4.9 h is the summed wall time of the 34 job logs on oversubscribed hosts, so wall
and CPU are not comparable. (An earlier "several CPU-days" in the Makefile and "~48 h" of summed wall time here were wrong and are corrected.) Wall time is not a good cost measure here: most jobs shared hosts that were oversubscribed (summed job wall time in `logs/`: about 4.9 h over 34 jobs, several of which ran concurrently).

## 6. Result files and the script-to-claim map

Per-instance files `results/*.csv` (one row per target x cap x rule; SHA-256 and the one-line convention of each file in
`results/MANIFEST.md` / `MANIFEST.json`) and derived tables in `results/analysis/`. **What the `code/` delivery contains.** The per-instance CSVs (~209 MB raw) are shipped gzip-compressed (`results/instances/*.csv.gz`, 12 MB,
gzip -9 with mtime 0; SHA-256 of every packed file is in `results/MANIFEST.md|json`, and `bash reproduce.sh` unpacks them to `results/*.csv`, whose
own SHA-256 are listed too). The two files not packed are regenerated: `ollb_powmeans_weighted.csv` (131 MB; ~4 solver CPU-minutes, ~29 min wall; it is also
a release asset of `world/experiment-repo`, release `results-large-v1`) and `theory_pairs.csv` (kept, 7 MB). `world/experiment-repo` holds the same files uncompressed.

**Reproduction path from the delivered tree, measured** (fresh copy of `code/` with `results/analysis/`, `theory_pairs.csv` and `theory_checks.txt` deleted,
`bash reproduce.sh`, one 2-CPU container on a shared host, exit 0): unpack < 1 s; regenerate `ollb_powmeans_weighted.csv` 1720 s; `analyze.py` 106 s;
`analyze_robust.py` 8 s; `theory_checks.py` 9 s; **total 1844 s wall, 1575 s CPU (user 1539 + sys 36)** for the first version of the script (91 manifest files). Result: 89 of 91 manifest files were byte-identical; the other two
(`ollb_powmeans_weighted.csv`, `analysis/censoring_and_cpu.csv`) differ only in the measured `cpu_s` column (timing), and the manifest records their SHA-256 without that
column (`sha256_without_volatile`), which matches (`src/verify_manifest.py` accepts exactly that). The solver runs that produced the other files (ordinal MILPs, HELM,
noise/bootstrap replicates, variants) are re-run by `make experiments`, not by `reproduce.sh`: 3.25 CPU-h of recorded solver CPU plus the replicate runs (which did not
record CPU), about 4.9 h of summed job wall time on the shared host (section 5).

**Re-test of the delivered tree after the `logs/` fix and the section-9 analyses** (`git archive` of the paper-repo PR branch, `code/` only, so no `logs/` and no unpacked results; `bash reproduce.sh`, exit 0): the script prints `total 2214 s wall` (scheduler spend 1703 s; the shared host was busier than in the first measurement, the powmeans step alone is about 1800 s), and `src/verify_manifest.py` reports **136 files match, 0 differ, 0 missing** (the two `cpu_s`-column files match without that column). `reproduce.sh` now also re-runs the section-9 analyses (`analyze_fits.py`, `analyze_capcomp.py`, `analyze_dup_rule.py`, `score_cap_defence.py`); the solver runs behind them (`jobs/ollb_cap_composition.sh`, `jobs/ollb_dup_rule.sh`, each run takes 10-30 s per cap and rule in `logs/ollb_capcomp_*.log` and `logs/ollb_dup_*.log`) are not re-run by `reproduce.sh`; their per-instance results are in `results/instances/` and the commands are in `make experiments`.

| claim (plan) | producing script(s) | result file(s) |
|---|---|---|
| C1 mean closed form, K=1 share | `run_core.py`, `theory_checks.py` | `ollb_score_*.csv`, `helm_main.csv`, `theory_pairs.csv`, `theory_checks.txt` |
| C2 rule ordering | `run_core.py`, `analyze.py` | `analysis/summary_groups.csv`, `rule_comparison_vs_mean.csv`, `ordering_stability.csv`, `pooled_feasibility.csv` |
| C3 median/min/trimmed (breadth) | `run_core.py`, `theory_checks.py` | `summary_groups.csv` (K columns), `theory_pairs.csv` |
| C4 growth with rank, feasibility vs rank | `analyze.py` | `analysis/rank_dependence.csv`, `summary_groups.csv` |
| C5 targeted vs uniform | `analyze.py` | `analysis/targeted_vs_uniform.csv` |
| C6 caps, n, normalisation, slice, noise, ties | `run_robust.py`, `run_core.py`, `analyze_robust.py` | `analysis/robust_*.csv`, `weighted_means.csv`; inputs `*_noise_*`, `*_taskboot_*`, `helm_tasksub_ceil.csv`, `*_variants.csv`, `*_eps0.1.csv`, `*_notie.csv` |
| follow-ups of the external review of v1 (section 9) | `run_core.py` (`jobs/ollb_cap_composition.sh`, `jobs/ollb_dup_rule.sh`), `analyze_fits.py`, `analyze_capcomp.py`, `analyze_dup_rule.py`, `score_cap_defence.py`, `build_dup_variants.py`, `ollb_items_check.py`, `helm_subject_sizes.py` | `analysis/rank_dependence_fits.csv`, `rank_monotonicity.csv`, `cap_composition_*.csv`, `duplicate_rule_*.csv`, `score_cap_defence*.csv`, `ollb_item_counts_check.csv`, `helm_subject_sizes.csv`; inputs `ollb_capcomp_*.csv`, `ollb_dup_*.csv` |
| solver accounting | `run_core.py`, `analyze.py` | `analysis/censoring_and_cpu.csv` (and `*_status`, `censored` columns) |

Figure/table scripts are `figtab-repo`'s (`figtab/`); they read the files above.

## 7. Scope and honest limits

* The cap is an assumption, not a measurement (emp95/emp99 are empirical gains of OLLB fine-tune pairs). Every claim is conditional on a cap family.
* Ordinal rules (Borda, Condorcet, plurality) were run on a **rank-stratified sample of 136 targets** and the four main caps (plurality: all eight,
  and the top-500 slice), not on all 4496 targets. Group-level statements use the target's stratum; population rates use stratum weights and are
  flagged `weighted=1`. Score rules cover every target and every cap.
* n = 6 tasks (OLLB) makes rank rules coarse; HELM (57 subjects, one benchmark family, 79 models) is not generalised to other leaderboards.
* Investment is score points under a cap, not training data or compute. Other models do not react.
* Findings that run against the study plan's stated hypotheses (reported, not adjusted; numbers in `results/analysis/`): (C2) the L1 ordering is
  *not* mean < power means < ... < median < min: at the `ceil` cap the mean and trimmed mean need the most points on both data sets (the mean's L1 is n times its gap), while
  median, min and plurality need far fewer; (C3) `min` does not need K = n (it needs only the tasks below the best rival's minimum); (C5) targeted
  investment is (almost) no cheaper than the uniform one for the mean at `ceil` and the gain caps (group-median L1/(n Linf) = 0.93-1.00; exactly 1 on OLLB) but
  is cheaper under binding caps (OLLB emp95 0.42-0.89, HELM front0 0.61-0.70; range over all caps 0.42-1.00), and much cheaper for median/min/plurality
  (group medians 0.03-0.51 across all caps and both data sets; Borda 0.36-0.73, Condorcet 0.26-0.60), i.e. the plan's hypothesis (targeting pays for the mean) is not supported at `ceil`/gain caps and only partly under binding caps, while rules that reward concentration gain the most. The medians in these statements are group medians per rank stratum;
  see `summary_groups.csv` for the intervals.

## 8. Forbidden material, licences

* **Forbidden paper.** No search of the literature or the web was made by this position (no search or fetch tool calls in its session logs); data
  were fetched only by the scripts above from the two listed hosts. No page of, or citing, the published paper on this question was
  encountered or read as far as this position's logs show. No accidental encounter to report.
* **Licences.** The data are public leaderboard scores. The HELM storage bucket and the OLLB `contents`/`results` datasets declare no licence
  (the HELM *code* is Apache-2.0; the OLLB `contents` card has a per-model `Hub License` column but no dataset licence). We used only aggregate
  scores for research analysis, did not redistribute raw files (only derived score matrices of 79 and 4497 models, committed in
  `data/processed/` with sources and checksums), and treat that as permissible research use of public data, without any claim that a licence
  covers it. This is our judgement, not a legal opinion; anyone redistributing the processed matrices should re-check the upstream terms.

## 9. Follow-up analyses requested by the external review of v1 (world/experiment-repo#6)

Measured; all numbers are in `results/analysis/` (file names below). Group = rank under the plain mean; "feasible" = the target can reach strict first within the cap.

**9.1 Composition of the empirical cap** (`cap_composition_pairs.csv`, `cap_composition_types.csv`, `cap_composition_feasible.csv`; caps in `src/mti/data.py`).
The 540 pairs are the leaderboard entries whose declared `Base Model` is itself in the data. By the self-declared `Type` of the fine-tune: 346 domain-specific
fine-tunes, 154 chat (RLHF/DPO/IFT), 24 pretrained, 13 continuously pretrained, 2 merges, 1 other, so 500 of 540 are chat or domain fine-tunes, as the reviewer says.
`Type` is metadata submitted with the model: it does not say whether a "domain" fine-tune is in fact an instruction conversion. Split by Type, 386 pairs are non-chat
(`nochat`); excluding in addition 179 pairs whose model name carries a chat-like token (instruct, chat, it, dpo, sft, rlhf, orpo; regex in `src/mti/data.py`) leaves 207 (`nochatname`).
95th-percentile gain per task (all pairs / `nochat` / `nochatname` / chat only): IFEval 46.0 / 44.6 / 55.7 / 49.8, MATH Lvl 5 21.3 / 19.4 / 18.8 / 24.3, BBH 7.3 / 7.0 / 7.9 / 7.3, MUSR 7.2 / 7.2 / 6.9 / 6.7, GPQA 3.8 / 3.9 / 3.1 / 3.3, MMLU-PRO 3.2 / 3.2 / 3.2 / 2.9.
Removing the chat-typed pairs lowers the IFEval cap by 1.4 and the MATH cap by 1.9 points; removing chat-like names as well does **not** lower IFEval (it rises, the tail is
carried by non-chat-named models) but lowers MATH to 18.8. So the cap does not collapse when the labelled chat conversions are removed.
Feasible share of targets at emp95 (all pairs -> `nochat` -> `nochatname`): mean 7.5% -> 6.7% -> 6.9%, median 3.1% -> 2.7% -> 2.9%, min 1.4% -> 1.7% -> 0.8%, plurality (stratum-weighted) 2.9% -> 2.3% -> 2.2%;
feasibility stays confined to targets already ranked within the top ~500 (at emp95 the share at ranks >500 is 0-0.5% under every variant, `cap_composition_feasible.csv` by rank group). The chat-only cap is more permissive for plurality (12.8%) and the mean (8.3%).
Target-dependent caps (the 95th percentile of the share of the base model's remaining headroom closed, applied to the target's own score; `empfrac95`, and on non-chat pairs): feasible share mean 1.4% (1.0% non-chat), median 1.7% (1.4%), min 0.8% (0.8%), plurality 0.4% (0.2%), i.e. much *tighter* than emp95, because a model near the ceiling cannot close the same absolute gap.
A flat quarter of the remaining headroom (`head0.25`): mean 12.2%, median 9.4%, plurality 4.4%, min 100% (a 25% headroom closure is enough to lift the lowest task of every target above the best rival's minimum; the cap is not the binding constraint for this rule).
Conclusion: the conclusions drawn from the emp95/emp99 caps (scarce feasibility for lower-ranked targets, rank ordering of rules) do not depend on chat-typed pairs; the absolute feasible shares do depend on the cap definition, from 0.4% to 12% for the same rule.
Not done: a cap calibrated on pairs verified to be pure base-to-domain fine-tunes by reading model cards (no such data are supplied).

**9.2 Functional form of the rank dependence** (`rank_dependence_fits.csv`, `rank_monotonicity.csv`; `src/analyze_fits.py`).
At `ceil`, power / linear-in-rank / log fits of median L1 against rank were compared on the group medians (7 groups on OLLB, 4-5 on HELM, which has only 79 models) and on target-level values.
The answer depends on the criterion. By relative error (rmse of log10 L1) the power form is preferred for 25 of 32 OLLB and 16 of 18 HELM rule/design cells at group level (the log form for 7 OLLB cells, linear for 2 HELM cells),
and at target level for 21 of 32 OLLB (linear 10, log 1) and all 31 HELM cells. By R^2 on the L1 scale (dominated by the high ranks) linear in rank wins 14 of 32 OLLB and 17 of 18 HELM group-level cells.
OLLB, mean (4495 targets): L1 ~ rank^0.44 (rmse log10 0.033; R^2 on L1 0.954) against linear R^2 0.980; median exponent 0.64, min 0.61 (min fits poorly, R^2 0.72). Exponents at group level 0.32-0.62 (OLLB); on HELM group-median exponents 1.1-2.0 for most rules from 5 points (mean 1.58 with rmse log10 0.26 and R^2 0.25, Borda 1.53, plurality 1.23), and the apparent 3.1 for median and Condorcet is an artefact of near-zero L1 at ranks 2-5 (group-median rmse log10 0.93, R^2 negative).
So "investment grows roughly as a power of rank: sub-linearly on OLLB (target-level exponents 0.4-0.6 for mean, median, min) and at about or above linear on HELM" is a fair description; the power law is not a better description than a linear one in absolute terms (R^2 on L1), only in relative error, and ranks span three decades only on OLLB. HELM has 79 models, so its fits rest on 4-5 groups.
Monotonicity: HELM group medians are monotone in rank for all 31 rule/design cells. OLLB group medians are monotone in 19 of the 32 rule/design cells and non-monotone in 13 (`rank_monotonicity.csv`): among the headline rules harmonic mean, median and min (design `all`), plus Condorcet and plurality on the stratified sample; the mean, geometric mean, trimmed mean and Borda are monotone. Example, OLLB min at ceil:
median L1 3.7, 3.1, 13.1, 9.7, 14.4, 12.3, 46.5 for the ranks 2, 3-5, 6-10, 11-30, 31-100, 101-500, >500 (non-monotone at 2->3-5, 6-10->11-30, 31-100->101-500); for min, harmonic, plurality and Condorcet the decreases lie within the bootstrap interval of the preceding group (`decreases_within_ci=1`), but not for the median (2->3-5 and 3-5->6-10: 9.6, 8.4, then 0.6 points at ranks 6-10, a 93% drop; `decreases_within_ci=0`), so the median's non-monotonicity is not explained by sampling noise in the 4 targets of that group alone.
Groups at ranks 2 and 3-5 hold 1 and 3-5 targets, so their medians are single observations.

**9.3 Duplicate-name rule and the noise-model input** (`duplicate_rule_sensitivity.csv`, `duplicate_rule_leaders.csv`; `src/build_dup_variants.py`, `jobs/ollb_dup_rule.sh`).
All 79 duplicated full names in the pinned `contents` snapshot are float16/bfloat16 pairs; 36 of the pairs share a submission date (ties broken by file order; `src/build_dup_variants.py`). The delivered matrix keeps the best-scoring variant; re-running
mean/median/min at ceil and emp95 with `first` (earliest submission, 41 of 79 rows differ from the delivered choice), `latest` (38 differ) and `worst` (the lowest-scoring variant, 79 differ; an extreme bracket) gives the same leader and the same runner-up under all three rules (`duplicate_rule_leaders.csv`; leader score 52.08 mean, 55.62 median, 23.15 min).
Group medians of L1 (ceil and emp95, mean/median/min) change by at most 5.3% over all groups (largest: min at ranks 31-100, 13.8 -> 14.5 under `first` and `worst`; median at ranks 31-100 17.9 -> 18.3, 2.0%); under `latest` by at most 2.2%; mean at ceil changes by <= 0.13% in every group. Mean at emp95, ranks 101-500: median L1 82.3 (delivered) / 80.5 (`first`) / 84.1 (`latest`) / 83.2 (`worst`), infeasible share 41% / 38% / 45% / 43%.
The dedup rule does not move any headline statement. Note that the same pinned `contents` snapshot defines "base" pairs: variants appear as `Base Model` candidates in the emp95 calibration of each variant run.
**Noise-model item counts** (`ollb_item_counts_check.csv`): see section 4: identical across 60 sampled models.

**9.4 Reading K** (`helm_subject_sizes.csv`, `score_cap_defence.csv`, `score_cap_defence_groups.csv`; `src/helm_subject_sizes.py`, `src/score_cap_defence.py`).
(a) HELM MMLU test items per subject (v1.13.0, identical for all 79 models): minimum 100 (10 subjects), median 173, maximum 1534 (professional_law); 14,042 items in total.
One item is 1.0 point on a 100-item subject and 0.07 on the largest; the binomial standard error of a subject accuracy at 50% is 5.0 points for 100 items, median 3.8, minimum 1.3.
(b) Score-cap defence: every model's task score is clipped at c_t (all models and the target; the target may still raise task t from its clipped score up to c_t) and the leader under the rule is untouched.
At c_t = leader_t + h with h = 5, 10, 20 the share of targets that can reach first with an uncapped attack stays 100% for mean, median and min on both datasets (OLLB and HELM) and the median cost is unchanged (OLLB mean 180.5, median 109.1, min 43.2 points; HELM mean 696, median 112, min 98): matching the leader on every task is already enough, so a clip *above* the leader removes nothing;
with a further gain10 attack cap the share is 0.5-2.2% (OLLB mean), 4.1-4.5% (median), 9.9% (min); HELM 33-37% (mean), 50-51% (median), 18% (min), against 2.5/4.5/9.9% (OLLB) and 37.2/51.3/17.9% (HELM) without the clip: the clip only matters where it lowers a target's own starting scores (131 OLLB targets at h=10, mean).
At h = 0 (clip at the leader) nobody can reach strict first (a tie is the most any target can get). Clipping at a per-task percentile of all models (q = 99/95/90) also clips the leader (the leader's score is cut on 2-6 of 6 tasks on OLLB, 5-47 of 57 on HELM; `n_tasks_where_first_is_clipped`). OLLB mean: attackable at q99 and q95 (share 100% with an uncapped attack; 5.5% and 5.8% with gain10) and closed at q90. OLLB median and min: closed at q99, q95 and q90. HELM mean: attackable at all three (100% uncapped; 16.7%, 10.3%, 10.3% with gain10). HELM median and min: attackable at q99 (100%; 42% and 18% with gain10), closed at q95 and q90. "Closed" means no target can reach *strict* first because the clipped leader ties with the clipped rivals on the clipped tasks: the percentile clip turns a strict ranking into ties; it does not make first place more expensive in score points.
Reading: score caps close the leaderboard to strict ranking only by creating ties; they do not make first place more expensive in score points. The definition used is stated above; other readings of "clip at the leader's score plus the gain10 increment" (a per-model rather than per-task clip, tie-allowed first) are not run.
