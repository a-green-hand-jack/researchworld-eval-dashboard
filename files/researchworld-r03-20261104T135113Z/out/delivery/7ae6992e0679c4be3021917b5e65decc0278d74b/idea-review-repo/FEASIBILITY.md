# Feasibility judgement (working note; the issue "Commitment: feasibility" carries the same content)

Probes run 2026-11-04 from `probe/mteb_matrix_probe.py` (MTEB tarball at the pinned commit) and direct downloads of the pinned HF parquet files. All numbers below are measurements of the data as downloaded, not results of the study.
## Commitment

I (idea-review-repo, **feasibility**) will deliver: (1) this judgement, from measured probes of the pinned data, of whether "choose k benchmarks, infer the other N−k for a new model" can be answered on CPU within a week and <5 GB; (2) the bounds/revisions the plan needs; (3) a re-check once `story-repo`'s plan and `experiment-repo`'s first protocol exist (I comment here only if a bound is violated). Standard: every figure below is something I ran; planning estimates are labelled as such. Probe code: `probe/mteb_matrix_probe.py` in this repo (working material, not a delivery).

## Verdict
**Feasible, with scope bounds.** Data, compute and time are not the binding constraints. The binding constraints are (a) what the MTEB matrix can say about *generative LLMs*, (b) the missing-data/leakage design of the evaluation protocol, and (c) a literature-search hazard (below).

## Measured facts (probes)
**MTEB, pinned commit 6dabbcc… (GitHub tarball, not a git clone):**
- Download 396 MB in ~90 s; extracted 2.8 GB. Tarball + extraction = 3.2 GB, so it fits <5 GB only if the tarball and raw tree are deleted after the matrix is built (keep only the parsed matrix, ~MBs). Do not also keep a git clone (history ~0.6 GB more).
- Parsing 547 non-empty model dirs (548 listed, one empty): 1,295 distinct task names, **overall fill 12.1 %**; tasks per model: median 72, p10 14, p90 363, max 922. (My parse averaged `main_score` over the first of test/validation/dev and over all subsets/revisions; task names include language/version variants. It is a probe, not the final extraction rule; `experiment-repo` owns that.)
- Dense blocks exist: tasks covered by ≥100 models: 357 → 135 models cover ≥80 % of them, block fill 0.948; tasks with ≥200 models: 56 → 162 models, fill 0.986; ≥300 models: only 2 tasks. So the usable regime is N≈50–360 benchmarks × M≈135–310 models, with real missingness inside.
- **Scale hazard:** `main_score` ranges −0.22 … 78,556 (1st–99th percentile 0.001–0.98). Some entries are not on a 0–1 accuracy-like scale or are outliers; the extraction must detect/clip/exclude them and say so, or every error metric is dominated by a few cells.
- Models are embedding models, tasks are embedding tasks (the data note says so). Many models are near-duplicates (variants/quantizations/same family). I did not measure the duplicate rate or release dates.

**Optional sources (downloaded at pinned commits, file shape only):**
- Open LLM Leaderboard `contents`: 4,576 × 36; six benchmarks (IFEval, BBH, MATH Lvl 5, GPQA, MUSR, MMLU-PRO) with columns `<name> Raw` and normalized `<name>`. Only N=6, so k≤5; useful as a generative-LLM check of the *small-N* regime, not for "how big must k be".
- LiveBench `model_judgment`: 60,372 rows, columns question_id/task/model/score/turn/category; 195 models, 3 categories, 7 tasks. Long per-question format; needs aggregation; N=7 or 3.
- HELM Lite core_scenarios.json: URL answers HTTP 200; not parsed (91 × 10).
- Not probed: BigCodeBench, AlpacaEval, cross-leaderboard model-name merging (expected costly, error-prone, and gives a very sparse matrix; not recommended).

**Compute / environment:** my sandbox has 2 CPUs; the shared host is heavily loaded (load ≈229 on 40 CPUs when probed), so wall-clock is slower than CPU-hours suggest. Planning estimate (not measured): closed-form ridge / conditional-Gaussian predictors and greedy forward selection over N≤360 candidates are seconds per fold; iterative matrix completion (soft-impute/ALS) on ~300×360 is ~seconds per fit. The worst case is nested selection × many folds × many k × many methods × repeats (≈ folds 135–300 × k-grid 10 × methods 5–8 × seeds): hours to a few tens of CPU-hours, within the "tens of CPU-hours" in resources.md only if fold counts/greedy refits are bounded. Run it with `ht-resource run`, not in a turn.

## Risks, and what to bound or revise
1. **Scope of claims.** MTEB supports claims about *predictability among embedding benchmarks*, not "LLMs". The task's own data note says this. Bound: state the claim per dataset; use OLLB/LiveBench/HELM only as small-N cross-checks; do not pool leaderboards. If the paper's title/abstract say "LLMs" it must be qualified.
2. **Leakage in the hold-out.** Leave-one-model-out with family near-duplicates inflates accuracy. Bound: split by model family (name prefix / base model) or at least report with and without near-duplicates removed; also a temporal split (older→newer) as a stress test if release dates can be obtained (unverified).
3. **Missingness in the protocol.** A new model's k observed benchmarks must come from benchmarks it actually has, and error scored only on its observed held-out cells; the selection rule must use only the training matrix (and cannot see the test model's held-out scores). Training-matrix missingness (12 % overall) must be handled by the selector and predictor (fit on pairwise-complete or via completion), and the choice of dense sub-block (thresholds above) is itself a result-bearing decision: sweep it and report sensitivity.
4. **"What k is enough" needs a definition.** A threshold must be fixed before looking (e.g., error within x% of the error with all N−1 predictors, or of the oracle best-k, with a confidence interval); otherwise the answer is unfalsifiable. Report k as a curve with uncertainty (bootstrap over test models and over selection draws, paired against baselines) and stop at k where the curve plateaus.
5. **Baselines must be non-trivial.** Per-benchmark training mean; mean of the k observed (scale-adjusted); random-k + same predictor; best-k oracle chosen on the test fold (an upper bound, labelled as such); full-information predictor (k=N−1). Without these the headline would not be interpretable.
6. **Selection cost.** Exhaustive subset search is infeasible (C(360,k)); use greedy / leverage / D-optimal / clustering selectors and say they are heuristics; the theory (below) is where optimality can be said.
7. **Theory is feasible but must stay small.** Under a rank-r Gaussian factor model with noise σ², the conditional-expectation predictor's error given a subset S is the Schur-complement term; k≥r with well-conditioned loadings gives error → noise floor; greedy log-det selection has a submodularity argument. Bound: one or two propositions, checked on synthetic data (generated with known r, σ) and then compared to the real-data scree/rank; do not claim the real matrix is low-rank Gaussian without the check. (Rank/noise estimation under 12 %–5 % missingness is the weak point.)
8. **Literature-search hazard (integrity).** deliverable.md forbids reading the already-published paper on this exact question or anything citing it. Natural queries ("predict benchmark scores from a few benchmarks", "benchmark subset selection", "active benchmark selection") may surface it. Bound: `idea-repo` should search by adjacent topics from `starter_literature.md` (IRT/psychometrics, tinyBenchmarks, metabench, Sloth, observational scaling laws, matrix completion, optimal experimental design), stop reading and log (what, where, how much) in the reproduction notes on any accidental encounter. I did no literature search in this probe.
9. **Reproducibility package.** Data fetch must be by the pinned tarball/commit with a checksum, raw-tree deletion step, seeds, per-figure script, runtime. The pinned HF files were downloaded by `resolve/<commit>/…` URLs. The conference's "latest official template" and checklist are `venue-repo`'s; I have not verified they can be fetched.

## What the plan can safely assume
- One week, CPU only, <5 GB: yes, if raw data are deleted after parsing and heavy loops are run as jobs.
- Primary experiments on the MTEB dense block(s) (e.g., ≥100-model tasks × 135 models and ≥200-model tasks × 162 models, plus a sweep); small-N cross-checks on OLLB/LiveBench/HELM Lite.
- Synthetic factor-model experiments are cheap and are needed for the theory check; they must be labelled synthetic and not mixed with real results.

## What would change this judgement
- If scale outliers/duplicate task variants cannot be cleaned to a defensible matrix in the extraction step, the usable N shrinks (the dense block is still 56 tasks).
- If family-grouped splits leave too few test families for useful intervals (check count of families before fixing the protocol).
- If fold × method × k grid runs exceed ~20 CPU-hours at the first pilot timing, cut folds (not the baselines) first.
