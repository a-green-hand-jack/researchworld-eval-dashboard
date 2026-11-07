# Feasibility assessment (idea-review-repo)

Scope: can the planned study meet the objective (predict a new LLM's full-benchmark score and ranking from a small
item subset, using source-model item-level results; fair comparison with existing and simple methods; ICML/ICLR/NeurIPS-style
paper + reproducible code) within CPU-only, one week, and the shared world budget?
Labels: [M] measured by me this turn, [P] planning arithmetic/judgement, [S] sourced from the task files.

## 1. Measured facts about the data [M]
Pinned commit 55faff49…, all 13 `.jbl` files download (~78 MB) and load with joblib; every matrix is complete (no NaN), values {0,1}.

| benchmark | models x items | identical-row models | acc range (min–max over models) |
|---|---|---|---|
| arc_challenge | 218 x 1172 | 9 | .205–.751 |
| bbh | 446 x 5761 | 21 | .241–.747 |
| gpqa | 447 x 1192 | 23 | .225–.437 |
| ifeval | 448 x 541 (bool) | 21 | .037–.880 |
| mmlu_pro | 448 x 12032 | 23 | .103–.597 |
| musr | 448 x 756 | 21 | .323–.536 |
| openllm_math | 447 x 894 (int64) | 72 | .000–.356 |
| commonsense | 83 x 500 | 1 | .222–.972 |
| gsm | 83 x 1000 | 0 | .028–.956 |
| legalbench | 79 x 2047 | 0 | .228–.702 |
| math | 83 x 437 | 0 | .025–.934 |
| med_qa | 83 x 1000 | 1 | .215–.869 |
| mmlu | 83 x 567 | 1 | .229–.811 |

(Script: ad-hoc, reproducible with `joblib.load` + numpy; experiment-repo's data audit is the delivered version.)

## 2. Risks, and what to bound or revise

**R1. Statistical power on the HELM side (high).** 79–83 models; a 20% target split is only ~16 target models, so Spearman/Kendall per
benchmark has a very wide sampling interval, and the 6 HELM benchmarks share the same ~83 models (not independent). [P]
Revise: report ranking metrics with CIs that resample *models* (not just seeds); use repeated random splits plus leave-one-family-out
rather than a single split; treat HELM-vs-method differences per benchmark as exploratory and make claims on pooled/paired differences
across benchmarks, stating the dependence.

**R2. Near-ties / floor / chance benchmarks (high).** gpqa (max .437, chance .25), musr (.32–.54), openllm_math (min 0.0, 72 identical rows) have a
narrow range of true scores. Subset noise at n items is about sqrt(p(1-p)/n) ≈ .16/.11/.07/.05/.035 at n=10/20/50/100/200 [P], comparable to
the full spread of true scores on these benchmarks, so rank correlation will be low for *every* method at small n. Expect "no method ranks reliably"
on these; this is a legitimate negative result, not a failure. Revise: report MAE/RMSE *relative to the random-subset baseline at the same n*
and to the spread of true scores, and report Spearman only with CIs; do not pool ranking metrics across benchmarks without normalising.

**R3. Leakage through near-duplicate / same-family models (high, validity).** Open LLM Leaderboard rows include merges and fine-tunes of common
bases; exact duplicates are 21–72 rows per benchmark, near-duplicates are surely more. A random model split lets a target have a near-copy among
the sources, which flatters every source-based method and hides the extrapolation problem. [P]
Revise: keep the `extrap` (top-20% as targets) protocol as headline alongside `random`, add family-out (needs model-name parsing from
`data/openllm_model_list.txt`; cheap), and dedupe exact duplicates *before* splitting (already done). State that split protocol is the primary
experimental factor.

**R4. Item-selection method fit on source models only; selection and prediction must not use target data (validity).** Any anchors/IRT
fit/item weights must be learned from sources alone; the target's responses only on the chosen subset. Check this in the harness
(a unit test on a fake target would suffice).

**R5. Compute (low–moderate).** Matrices are small; the largest (mmlu_pro 448 x 12032) fits in memory. The experiment-repo reports a 3–5 h sweep
for 13 benchmarks x 2 protocols x 20 reps x ~10 methods x 5 budgets at one thread/job [S: story-repo#2]. The sandbox has 2 CPUs and shares the host. [P]
Extending to mass/AIPW variants, source-count / extrap-fraction / latent-rank ablations multiplies that by roughly the number of ablation arms; this is
feasible if ablations run on a subset of benchmarks (suggest: mmlu_pro, bbh, ifeval + two HELM) and fewer reps (10). Bound: each added
arm gets a timed pilot first; the full grid is not repeated after each method change (freeze methods before the final sweep).
Wall-clock one-week limit is not the binding constraint; the world's shared model-time and turn budget is, so do not respawn the whole sweep for cosmetic changes.

**R6. Baseline coverage (scope limit, must be stated).** Faithful reimplementation is feasible on CPU for: random subset, stratified-by-difficulty,
Anchor Points (k-medoids on source response vectors), tinyBenchmarks-style IRT / anchor-IRT, regression/latent-factor predictors, and the proposed
method. Not feasible/faithful here: Pacchiardi et al. (needs item text/embeddings; per-model item text is not in the supplied matrices and
details are gated), Active Evaluation Acquisition (needs training an RL/neural policy on text-less data; at most a simplified greedy variant), metabench
(GAM on IRT subscores; only a simplified information-based selection). Say so in the paper; do not label a simplified variant with the original method's name.

**R7. Novelty positioning (moderate, content).** A model-assisted estimator with a control-variate/difference correction on a random sample is
close to prediction-powered inference and to survey-sampling model-assisted estimation. The contribution should be framed as the *systematic comparison under
extrapolation* plus the (design-unbiased, variance-reduced) estimator with its honest conditions, not as a new principle; related-work
section must cite PPI/survey-sampling literature (cite only what was actually read). If the proposed method does not beat stratified/AIPW-off baselines under
extrap, that negative result stands and is acceptable to the objective.

**R8. Multiplicity and analysis hygiene (moderate).** 13 benchmarks x 2 protocols x 5 budgets x ~20 methods invites cherry-picking. Pre-declare the headline
comparison (e.g. proposed vs best baseline per benchmark at n=50, 100, extrap protocol, paired difference in RMSE with model-level bootstrap CI), report
all others as secondary, correct or at least flag multiplicity, and freeze it before the final sweep. Avoid selecting hyperparameters (rank, ridge, k) on target models:
tune by CV on sources.

**R9. Compliance with the "do not access" clause (moderate, process).** The task forbids the published paper on this exact problem, yet
`starter_literature.md` item 6 (arXiv:2506.07673) is listed and declared usable, and the data repository README (inspected as data.md directs)
summarises that paper's conclusions. [S] experiment-repo has already disclosed reading that README paragraph. Guidance: use only starter item 6 as the task allows;
do not search for or open reviews, blogs, citing papers or the repo's other pages beyond data/code files; record every incidental encounter (what, where, how much)
in the reproduction notes; because the README conclusions have been seen, avoid framing hypotheses as discovered independently and let the experiments state what they
show. `benchpred` code was inspected, not trusted; do not copy its code without noting it (MIT licence, attribute it).

**R10. Delivery logistics (moderate).** The ICML/ICLR/NeurIPS latest template and checklist must be obtainable (network is allowed); page limit counts main text only for most;
the paper-repo `.forgejo/CODEOWNERS` does not yet exist (open requests from figtab-repo: story-repo#3). The reproduction README must list env versions, seeds, commands, runtimes, and map every
figure/table to a script (objective deliverable 2): ask experiment-repo/figtab-repo to name the generating script in each result/figure file.

## 3. Recommended bounds (summary)
1. Headline: `extrap` protocol + `random`, family-out as a robustness check; budgets n in {10,20,50,100,200} plus a fraction-of-benchmark view.
2. Primary metrics: RMSE/MAE (and bias) vs true full score; Spearman/Kendall with model-level bootstrap CIs; per-benchmark and pooled-by-paired-difference results.
3. Freeze the method list and the primary comparison before the final sweep; ablations on a benchmark subset.
4. State the unfaithfully-covered baselines (R6) up front; no renamed simplified variants.
5. Keep the claim scope conditional ("holds for these 13 benchmarks, these split protocols, binary scores, source model counts ...").
6. Whole plan fits the one-week / CPU-only limit; the real risks are statistical power (R1, R2) and validity (R3, R4), not compute.
