# Feasibility judgement of `PLAN.md` (world/story-repo, commit fc57928)

Position: `idea-review-repo`. Judged against objective #1 and `/initial-state/inputs/0/*`.
Answers request `idea-review-repo#2`. Measured facts, estimates and judgements are marked.

## Verdict
Feasible, **if scope is bounded as below**. Compute (CPU, one week) is not the constraint.
The binding constraints are (a) the shared model time (7200 s, 96 turns, 9 positions) and
(b) the number of claim types x perturbation families x scales x datasets in the plan,
which is larger than a short pipeline plus a conference paper can carry. The plan's
objective coverage (>=2 real evaluation designs, defined size scales, uncertainty,
limitations) is adequate; nothing in it needs more data than `data.md` supplies.

## 1. Compute (measured on SYNTHETIC BT data; timing only, not a result)
Newton BT/logistic fit, pure NumPy, 2-CPU sandbox, script `bench/bench.py`:

| instance (N comparisons, K participants) | cold fit | warm refit after 50 drops | one bootstrap replicate |
| --- | --- | --- | --- |
| 57,000, 64 (Arena-55k shape) | 0.04 s | 0.02 s | 0.03 s |
| 63,000, 110 (pooled NBA shape) | 0.16 s | 0.02 s | 0.03 s |
| 1,230, 30 (one NBA season) | 0.002 s | 0.001 s | 0.001 s |
| 3,300, 6 (MT-Bench shape) | 0.003 s | 0.002 s | 0.002 s |

Consequences (estimates from these timings, real data not yet run):
- 1,000 bootstrap replicates on Arena-55k ~ 30 s; influence of all N points on all K scores
  is one solve and an N x K product: seconds.
- Greedy/batched removal with exact refit: even 500 refits per claim is < 15 s on Arena.
  NBA: ~70 seasons x ~29 adjacent pairs x ~200 refits ~ minutes. Total core compute is
  CPU-minutes to a few CPU-hours; run it as an `ht-resource` job, not inside a turn.
- Download: Arena-55k csv 184 MB, MT-Bench parquets ~1.4 MB, NBA csv 18 MB; the three URLs
  answered HTTP 200 from the sandbox (HEAD only, nothing downloaded).
Not feasible-by-cost: bootstrapping inside the perturbation search (see 2).

## 2. Specific changes requested of the plan
1. **C4 (significance) must have a smooth search surrogate.** "Bootstrap CI excludes 0" is not
   a function a removal search can follow, and re-bootstrapping per candidate multiplies cost
   by ~1000. Define one primary SE (Hessian/sandwich Wald z for theta_i - theta_j; with ties
   as half wins this is quasi-likelihood, say so), search on z, and re-verify the final
   perturbed data with the bootstrap interval; report where Wald and bootstrap disagree.
2. **Exact-search check: ILP is not applicable; brute force only for small k.** The BT MLE is
   an argmax of a nonlinear objective, so "smallest removal that flips the order" is not a
   linear program. What is realistic: the MLE depends only on cell counts (pair x outcome), so
   enumerate removals over cell-count vectors. With MT-Bench (15 pairs x 2-3 outcomes) this is
   exhaustive for k <= ~5, and for small subsamples (e.g. 6 participants, a few hundred
   comparisons) possibly more. For larger k the check is greedy vs beam/random-restart local
   search, which gives a *tighter upper bound*, not a proof. State this; report the greedy
   gap only where exhaustive search is possible, and do not call k* "minimal".
3. **Censor the search.** Set k_max (suggest 5% of N or the budget of refits, whichever is
   smaller) and report "k* > k_max" as censored; do not drop censored claims from summaries.
   For claims with a large gap (z >> 3) this is the expected case, and it is a finding.
4. **Regularisation / separation.** Removal can disconnect the comparison graph or create
   perfect separation (MT-Bench has few comparisons per pair; a participant can have 0 losses
   to another). Fix a small ridge or restrict to connected cases, record it, and include one
   sensitivity run, because k* then depends on the regulariser.
5. **s3 as written is expensive/ill-defined** ("k with flip probability 0.5 under random
   removal"; random removal may never reach 0.5 within k_max). Use the bootstrap z-gap as the
   primary noise-unit scale and, for B1, report flip probability on a short log-grid of k
   (e.g. 6-8 values, 200 draws each) instead of root finding. This is cheap and censoring-safe.
6. **Reduce the claim grid.** Primary: C1, C2 (adjacent pairs; for Arena restrict to the top
   10 plus all pairs in the CI-overlap region, for NBA to the champion and the top 4), C4.
   C3 (top-k sets) and Kendall tau are secondary and the first thing to drop. Adjacent-pair
   claims over ~70 NBA seasons x 29 pairs are ~2,000 instances: summarise by distributions,
   and treat per-pair results as exploratory (multiplicity).
7. **Matched contrast M-h vs M-g needs an explicit item rule.** Restrict both to the same
   (question, model pair, turn) items; human data has several judges per item and ties; the
   replicate unit is the question (cluster bootstrap). Write the item alignment and the
   dropped counts in `results/`. This contrast is the strongest evidence in the study; check
   it first (the plan's early pilot on MT-Bench-h is right).
8. **s4 is cheap and necessary, but does not remove all confounds.** Subsampled Arena matches
   N, K and comparisons per participant; it does not match spread of strengths or outcome
   noise. Add score spread and tie rate as covariates in E4 and say that the cross-design
   statement is conditional on 3-4 designs (the plan already says so; keep it in the abstract
   scope, not only in limitations).
9. **NBA specifics**: `_iscopy` duplication, regular season vs playoffs (`is_playoffs`),
   home court (a covariate or a documented omission), neutral sites. Per-season primary, as
   planned; pooled fit labelled secondary.

## 3. Scope order (what to cut first, if model time tightens)
Must keep: E0; E1; E2 (P1) for C1/C2/C4 on A, M-h, M-g, N-per-season; B1/B2 baselines; s1, s2,
s3 (z-gap), s4; the M-h/M-g contrast; uncertainty on every headline number; the ties and
home-advantage sensitivity (it bears on validity, so keep it in E5 core).
Keep if cheap (same machinery): P2 flips and P3 additions, limited to C1 and the top pair for
P3 (cell-level candidates make both inexpensive).
Cut first, in this order: Kendall tau / C3 -> E5 order-of-arrival and Elo-ranker pieces ->
Arena 140k -> Arena LLM-judge labels. I would put the LLM-judge optional *above* Arena 140k
(a second matched contrast on the same 50k battles is worth more than a second crowd dataset
from another period) but it carries an unresolved licence question and a 142 MB file, so it
stays optional and conditional on the licence check. WebDev Arena: skip (agreement required).
Synthetic data: not needed.

## 4. Model-time and delivery risks (the real ones)
- 7200 s of model time across nine positions, 58 s used at the time of writing. Each
  position's code or paper turn costs minutes. Recommend: `experiment-repo` writes one
  pipeline (loaders -> fit -> perturb -> summaries) with a pilot, then launches the full runs
  as one `ht-resource` job and returns; no per-claim hand analysis. Aim for <= 3 pushes of
  `results/`.
- Paper work (template, checklist, figures, bibliography) is serial after results; the plan
  should freeze the claim list and metric names now so `figtab-repo` and `paper-repo` can
  draft against stable names (the plan allows this; make the file schema of `results/`
  explicit early).
- One-week wall-clock is not binding; model time and turns are.

## 5. Excluded-material risk
Starter item 8 matches the description of the excluded published paper (agree with
`PLAN.md` section 0: do not open, search or cite it; log accidental encounters). A second,
non-access risk: P1 with influence functions is the obvious method for this question, so
the paper's novelty must rest on what we do ourselves (flips and additions, random and
sampling-noise baselines, scale definitions, matched design contrasts, validity conditions),
not on "first to show that few comparisons change a ranking". Do not tune choices to what the
excluded paper might have found. Whether and how related work acknowledges that a task-listed
paper exists that we did not read is a decision for `idea-repo`/`paper-repo`; I recommend a
neutral statement in the reproduction notes rather than a citation of unread work.

## 6. What this judgement does not do
It does not predict the direction or size of any result, and the timings above come from
synthetic data of the stated shapes; real-data timings must be recorded by `experiment-repo`.
