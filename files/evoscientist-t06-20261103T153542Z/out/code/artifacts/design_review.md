# Design review: paired-comparison ranking stability

## 1. Assumptions, scope, and falsifiable claims

**Scope.** A CPU-only, unattended, finite-snapshot sensitivity study, not an estimate of real-world manipulation prevalence, model quality, or population-wide ranking truth. Use only the user-authorized Arena crowdsourced-human snapshot, MTBench human and GPT-4 paired judgments, and one NBA season. Analyze four source strata; the two MTBench strata are not independent domain replications. No web use, related-paper investigation, code agents, or implementation is part of this review. Methods are limited to Bradley–Terry (BT), its local influence approximation, and exact numerical refits.

**Snapshot blocker.** `/work/data` and `/work/artifacts` were empty on inspection; no brief-named file was found under `/work`. Exact releases, checksums, and NBA season were not supplied in the visible request. Do not guess, download substitutes, or choose snapshots after seeing outcomes. The parent must supply the authorized brief and a frozen manifest before execution; otherwise stop with `BLOCKED_SNAPSHOT_MANIFEST`.

**Smallest claim.** On a specified observed comparison design, frozen first-order BT influence scores either do or do not predict exact-refit changes in specified score gaps. A separate claim asks whether influence-based selection outperforms simple selection rules at equal edit cost. Neither claim implies that one domain is inherently more robust than another.

Pre-register before perturbation results:

- **H1: prediction validity.** On a uniform sample of eligible single edits, the median across preselected targets of tie-aware Spearman correlation between predicted and exact gap changes is at least 0.70, separately for flips and deletions in each source. Require at least 30 sampled eligible edits and three nondegenerate targets per source/operation; otherwise mark this test inconclusive. Report every source/operation, not just a pooled correlation. Calibration slope, normalized absolute error, and sign accuracy are required diagnostics, not interchangeable substitutes for H1.
- **H2: useful targeting.** At the preregistered 1% global eligible-row budget, unrestricted static influence selection yields a larger mean exact gap reduction than both uniform random and direct-pair-first selection, separately for flips and deletions. Test within source; use simultaneous uncertainty controls across the 16 source-by-operation-by-comparator contrasts. Claim cross-design support only if all four sources support both operations' contrasts; mixed results imply a source/operation-conditional conclusion. A zero integer anchor budget is inconclusive. This is a demanding test, not a presumed outcome.
- **Secondary:** exact reversal rates, budget–damage curves, incident-only perturbations, full-ranking movement, and approximation breakdown. These cannot rescue a failed primary claim.

## 2. Top five rejection risks and concrete controls

| Likely rejection | Concrete controls and decisive evidence |
|---|---|
| **1. “Cross-domain differences are comparison-design confounding.”** Arena participation, MTBench judge/question structure, and NBA schedule differ jointly with source, size, density, exposure, and baseline margins. | Keep source-specific estimates; tabulate graph coverage, component sizes, degree/incident counts, repeat counts, tie rates, gap distributions, and judge structure. Compare human/GPT-4 only on a matched MTBench question–model-pair–turn intersection as a secondary control. Add common-support restrictions on target exposure and baseline standardized gaps, and a fixed-design BT parametric simulation as diagnostics. If support is absent, report non-comparability rather than extrapolate. No causal attribution to “human versus GPT-4” or domain. |
| **2. “Budgets and edit semantics favor the proposed attack.”** Flips and deletions change different things; a global fraction hides concentrated endpoint exposure. | Use the same decisive-row eligibility for primary flips and deletions, one row = one edit, and identical eligible pools and integer budgets across policies. Report both global and target-incident denominators and realized incident edits. Separate unrestricted and incident-only action domains. Compare scopes at matched absolute counts, never equal percentages alone. Treat flips versus deletions as distinct interventions, not equal-strength equivalents. |
| **3. “Influence scores are only self-confirming linearization.”** Selecting and reporting the largest predicted effects can hide wrong signs or finite-change errors. | Freeze baseline predictions and selected edit sets before refitting. Validate an independently sampled uniform edit set plus a separately labeled high-score tail; run infinitesimal finite-difference checks and full-edit exact refits. Report signed calibration, error, top-set realized gain, and cumulative prediction failure. Include random and direct-pair-first controls. No post hoc target changes or adaptive recomputation in the primary method. |
| **4. “Disconnected graphs, ties, or regularization manufacture rankings.”** Deletions can destroy identifiability, and arbitrary tie breaking creates reversals. | Fit a fixed ridge BT objective, report its estimand, audit undirected and directed outcome graphs, preserve all nodes, and never present cross-component ordering as empirically identified. Flag disconnection/separation, compare regularization strengths, and distinguish numerical ties, statistical uncertainty, and strict reversals. Report conservative disconnection bounds instead of silently dropping difficult attacks. |
| **5. “Uncertainty is pseudoreplication or researcher selection.”** Votes, questions, repeated judges, and games are not interchangeable independent trials. | Freeze targets, thresholds, budgets, seeds, and exclusions. Use prompt/question/judge identifiers where available; paired cluster resampling for matched MTBench; distinguish finite-snapshot Monte Carlo uncertainty from sampling uncertainty. Treat NBA fixed-schedule BT bootstrap as model-based, not distribution-free. Recompute policies in bootstrap replicates, retain failures, and report all planned cells and unsupported uncertainty assumptions. |

## 3. Estimator, interventions, and fair comparisons

### BT estimand and exact influence formulas

Canonicalize each comparison to fixed item ordering: `x_r = e_i - e_j`, with `y_r = 1` for an i win, `0` for a j win, and `1/2` for an explicit tie. Do not treat missing, invalid, or “both bad” judgments as ties without an explicit authorized mapping. Let

`L(theta) = sum_r w_r [log(1 + exp(x_r^T theta)) - y_r x_r^T theta] + (lambda/2)||theta||²`, with `sum(theta)=0`.

Primary rows have unit weight and **lambda = 1 in this sum-loss convention**; sensitivity values are 0.1 and 10. This is a stabilized descriptive score, not an unpenalized-MLE claim. Keep lambda fixed after deletions; do not renormalize by the remaining sample size. Aggregate identical sufficient-statistic cells for fitting without changing the objective or row-level edit cost.

At the baseline fit, `p_r = sigmoid(x_r^T theta)` and `H = sum_r w_r p_r(1-p_r)x_r x_r^T + lambda I`, restricted to the centered subspace. Solve linear systems; do not explicitly invert H. For a set S of unit-weight edits:

- **Flip:** replace each decisive `y_r` with `1-y_r`, keeping endpoints and all other metadata fixed. Prediction: `delta_theta = H^-1 sum_S (1-2y_r)x_r`.
- **Delete:** remove that observation, keeping all nodes and the same penalty. Prediction: `delta_theta = H^-1 sum_S (p_r-y_r)x_r`.

These are baseline first-order approximations; finite deletions also change curvature. Define a target as baseline-higher item a versus b, with gap `m = theta_a-theta_b > 0`. Predicted damage is `- (e_a-e_b)^T delta_theta`; positive values reduce that gap. **Every reported realized effect uses an exact converged refit of the changed objective.** Predictions alone are never attack outcomes.

### Targets, ties, and action units

Within the largest baseline connected component, choose up to six distinct adjacent-rank pairs at equally spaced rank positions, including top-two and the bottom adjacent pair. Use all adjacent pairs if fewer exist. Freeze identities and orientation before testing policies. This is a declared rank-stratified target set, not a random sample of all pairs; report target-level results. Do not replace hard or ambiguous targets after seeing results.

Retain explicit ties as half-win contributions in the primary BT fit, but make **only decisive rows editable for both primary operations**. Ties have no unique outcome reversal. A separately labeled all-row deletion sensitivity may delete ties. A tie-removed refit is a robustness check, not an alternative chosen by performance. In primary experiments, an edit affects one judgment/game record, not an entire prompt block; a capped secondary block-deletion check addresses correlated records and uses block-count budgets, never mixes them with row budgets.

Use a numerical score tolerance `epsilon = 1e-6`, contingent on tighter solver accuracy. Strict reversal means the edited gap is below `-epsilon`; `|gap| <= epsilon` is a numerical tie. Baseline gaps within epsilon are unresolved and are counted/reported rather than relabeled using item IDs. Statistical overlap of confidence intervals is a separate notion from a numerical tie. Report changes involving initially uncertain targets without claiming a securely identified rank reversal.

### Policies and budgets

For each target, define `U_all` as all eligible baseline rows and `U_inc` as eligible rows touching a or b. Baseline counts are `N_e` and `N_inc`; denominators never shrink after deletion.

Within each action domain compare:

1. **Random:** uniform sampling without replacement, with frozen seeds; 10 repeats per grid point and 20 at the primary anchor.
2. **Influence:** rank all admissible rows by predicted damage, select the top k once using the baseline fit. No iterative reranking. Ties use seeded hashing. Select exactly k, including negative scores if needed; disclose that fact.
3. **Direct-pair-first heuristic:** prioritize direct a-over-b wins; then other a wins or b losses; then other direct a–b rows; then remaining rows. Randomize within tiers with frozen seeds. This defines a full-budget heuristic when direct meetings are scarce. Report tier composition and direct-pair availability. A direct-only result is secondary and must use a common feasible count across all policies, not silently under-spend.

Primary budget fractions are `{0, 0.001, 0.005, 0.01, 0.02, 0.05}`: `floor(beta*N_e)` for unrestricted edits, `floor(beta*N_inc)` for incident-only edits. Also evaluate the union of these integer counts in both domains wherever feasible, enabling fixed-k comparisons. Deduplicate repeated counts; zero counts are baseline points, not evidence. Add a labeled k=1 diagnostic when positive fractions round to zero. Never cap an infeasible requested count silently.

For every attack report k, `k/N_e`, `k/N_inc`, and **actual edited incident rows / N_inc**. For unrestricted attacks, `k/N_inc` is only an exposure-normalized cost, not actual incident exposure. Denominator changes merely reparameterize curves at fixed scope; do not treat them as independent experiments. Scope changes alter the action space and must be labeled. A matched-null diagnostic samples random edits matching the influence set's endpoint-degree bins, endpoint-incident count, and available source/judge strata; exact-match infeasibility is reported rather than concealed.

## 4. Numbered stages and gates

### Stage 0 — Freeze authorization and environment

- **Goal:** eliminate provenance ambiguity and accidental external research.
- **Run:** parent validates local-only manifests, paths, checksums, season/date filters, licenses, and schema; records package versions and CPU resources. No network fallback. Snapshot manifest must quote the authorized brief identifiers.
- **Success:** all four strata and exact NBA season identified; no guessed substitutions; no writes outside approved outputs. CPU smoke test needs no accelerator.
- **Artifacts:** `snapshot_manifest.json`, `environment.txt`, preregistered `protocol.json`, seed list, task ledger. Missing metadata is a hard stop, not a tuning opportunity.

### Stage 1 — Audit data and establish baseline estimands

- **Goal:** ensure comparisons and fit are meaningful before ranking robustness is measured.
- **Run:** canonicalize outcomes; audit duplicates, missing labels, model/version IDs, self-comparisons, order reversals, invalid dates, ties, prompt/judge grouping, repeated games, and exposure. For NBA, include only the authorized season and declared phase; do not treat quarters or box-score rows as extra games. Produce the matched MTBench intersection without pooling judges: retain one judgment per source per canonical question–pair–turn block by a fixed label-independent ID hash, ensuring identical comparison designs rather than merely overlapping questions. Preserve all judgments in the main source-specific analysis. Fit baseline ridge BT and tie-aware empirical win-rate baselines; report descriptive gaps, not predictive superiority.
- **Success:** accounting balances raw/retained/excluded rows with reasons; no duplicate game IDs or unresolved item aliases; zero non-finite scores; baseline centered gradient infinity norm <= 1e-8. Record connected components, directed strongly connected components, isolated nodes, and potential unpenalized separation. Cold/warm refits agree to <= 1e-8 in score gaps.
- **Artifacts:** data-quality table, graph/exposure table, exclusion ledger, baseline scores/targets, component plots, solver logs.

### Stage 2 — Falsify influence predictions before full attack curves

- **Goal:** separate implementation errors from finite-perturbation failures.
- **Run:** check a small synthetic connected example against analytic gradients; use continuous flip interpolation and deletion weight changes of size 1e-4 to test influence derivatives. For each source/operation, select up to 96 uniform eligible single rows without replacement, shared across targets, plus up to 32 additional high-score rows. Record inclusion probabilities; evaluate uniform and enriched sets separately. Exact-refit full edits and multi-edit sets at the declared budgets. Include a small fixed-design BT simulation retaining endpoints/counts, with ties handled in a separately specified decisive-only simulation.
- **Success:** derivative relative error <= 1e-4 or absolute error <= 1e-7, with denominator handling logged; exact fits meet Stage 1 solver criteria. H1 is assessed on full single edits, not infinitesimal checks. Report signed prediction-versus-refit plots, calibration slope/intercept, MAE normalized by the uniform-sample mean absolute realized effect, and sign accuracy excluding effects below epsilon. Near-zero variance makes correlation non-evaluable, not zero or a success.
- **Artifacts:** frozen prediction file, sampled edit IDs, exact-refit audit table, residual plots, cumulative-error-versus-budget plot. Failed derivative checks stop substantive runs; failed H1 remains a valid empirical result.

### Stage 3 — Equal-budget targeting and design controls

- **Goal:** test H2 and characterize concentration without cross-design overclaiming.
- **Run:** exact-refit the full policy/operation/scope/count grid, reusing frozen attack sets and paired random seeds. Run matched MTBench and matched-null controls; apply common-support exposure/gap summaries without selecting favorable subsets. Use the same baseline parameters and target identities for all policies in a cell.
- **Success:** complete planned cells or explicit failure records; all policies spend the same feasible k. Primary endpoint is exact gap reduction divided by the fixed baseline gap scale `max(|m|, 0.1)` and averaged equally over targets within source; report raw gap changes alongside it. Report reversal rate, fraction of pairs discordant relative to the baseline with ties separated, top-5 set overlap where meaningful, and graph damage as secondary outcomes. Do not replace the endpoint with whichever metric favors influence.
- **Artifacts:** tidy attack-results table; policy difference table; curves with global/incident axes; realized exposure and disconnection panels; target-level results.

### Stage 4 — Uncertainty, robustness, and bounded conclusions

- **Goal:** distinguish numerical exactness, perturbation randomness, sampling uncertainty, and model dependence.
- **Run:** 100 bootstrap replicates at the fixed 1% unrestricted anchor, with frozen target identities but recomputed baseline fits, influence scores, selected sets, and exact refits. Resample Arena by prompt/session blocks if identifiers exist; MTBench by question with matched human/GPT-4 blocks resampled jointly, and add judge-aware sensitivity when identifiers permit. If such identifiers are absent, label row bootstrap as an IID sensitivity only and do not make dependence-robust claims. For NBA use a schedule-fixed BT parametric bootstrap, labeled model-based; it cannot establish robustness to unmodeled season dynamics. Preserve original target orientation and report bootstrap baselines already tied/reversed separately from perturbation-induced crossings. Use paired contrasts within each replicate, including a random-policy draw. Report intervals, not a pooled vote-level test.
- **Success:** distinguish Monte Carlo uncertainty over random edits from bootstrap uncertainty. Use approximate familywise 95% simultaneous intervals for H2's 16 contrasts: estimate each contrast's bootstrap standard deviation, obtain the 95th percentile of the bootstrap maximum absolute standardized deviation from its observed estimate, and apply that common multiplier to the observed contrasts. Pair MTBench source replicates; freeze the replicate-index coupling for other sources. Flag zero-variance contrasts and disclose limited 100-replicate resolution; no narrow-tail significance claims. Refit ridge sensitivities, tie-removed fits, and matched MTBench controls. Report model dependence if signs, disconnection conclusions, or target success rates change materially.
- **Artifacts:** uncertainty table, bootstrap diagnostics and failure rates, robustness table, claim-to-evidence matrix, concise limitations. Failure to support H1/H2 leads to a negative/conditional conclusion, not another search for targets or snapshots.

## 5. Evaluation protocol and difficult cases

**No artificial train/test split for the primary estimand:** it measures sensitivity of a fixed observed ranking, not held-out predictive accuracy. Freeze preprocessing/model/targets before attack evaluation. Uniform audit edits are not used to tune the policy. Any exploratory changes require a labeled new protocol version; original tests remain visible. If predictive metrics are later added, split by prompt/question blocks (NBA chronologically) and do not mix those results with ranking-sensitivity claims.

**Disconnections:** ridge makes computation possible but does not make relative locations of separate components data-identified. The primary target list is within the largest baseline component; smaller components and their excluded mass are reported separately. For every deletion flag whether target endpoints separate and whether any component splits. Present regularized numeric outputs as such, plus conservative reversal-rate bounds counting target-disconnected cases as all failures versus all successes. Report connected-case effects with their retained denominator, not as an unbiased substitute. Also report new directed separation even when the undirected graph remains connected. Fixed-node flips preserve the comparison graph but can create outcome separation. Never infer robust ordering of an isolated node from its shrinkage score.

**Uncertainty and pairing:** four source strata do not supply four independent domains. Aggregate attacks are nested/reused edit sets, random seeds are not new datasets, bootstrap draws are not new seasons, and target pairs share items. Source-specific paired bootstrap contrasts carry the inferential burden where assumptions are defensible. Main single-snapshot numerical effects remain descriptive even without valid sampling intervals. Missing block IDs or model misspecification narrows claims rather than authorizing false precision.

**Design-control definitions:** curvature-standardized baseline gap is `m/sqrt(c^T H^-1 c)`, with `c=e_a-e_b`; this is a model-curvature diagnostic, not a dependence-robust z-score. Predeclare common-support bins using log2 incident counts and standardized-gap intervals `[0,0.5), [0.5,1), [1,2), [2,4), [4,infinity)`. Report only occupied shared bins, target counts, and excluded mass; never extrapolate to empty bins. Global rank-movement metrics use baseline-component membership and explicitly flag post-edit disconnected pairs; cross-component ridge ordering is not counted as identified ranking evidence.

## 6. Dependencies, resource preflight, and unattended execution

**Data:** authorized local snapshots plus schema/label mappings, item/version identifiers, timestamps/season definitions, and available prompt/question/judge/game IDs. The matched MTBench intersection may be empty; in that event report the control unavailable, never infer a judge effect from unmatched subsets.

**Environment:** Python 3.10+; `numpy`, `scipy`, `pandas`, `pyarrow` for Parquet if used, `networkx`, `matplotlib`, `pyyaml`, `psutil`, `threadpoolctl`, and `pytest` for parent-authored checks. No torch, transformer models, GPU, or CUDA dependency. Use only already cached packages or an approved offline wheel source; lack of dependencies produces an actionable stop.

**Parent's high-level preflight commands:** `python --version`, `python -m pip check`, `python -m pip freeze`, `lscpu`, `free -h`, and `df -h /work`; optionally `nvidia-smi` solely to record accelerator status, with absence accepted. GPU/CUDA/VRAM are not required and must not gate this study. Record CPU count, BLAS threads, RAM, free disk, paths, and checksum verification. Suggested starting allowance: 4 CPU threads, 8 GB RAM, 10 GB free disk, revised upward only from measured local data size.

**Execution contract:** parent implements sequential audit → derivative validation → prediction audit → exact attack grid → uncertainty/report phases; commands/scripts are to be created by the parent, not assumed to exist. Pilot ten representative exact fits and one bootstrap; estimate total time, peak RSS, and disk from unique fit counts. Cache aggregated sufficient statistics and baseline Hessian solves; keep attack IDs at row resolution. Declare a ceiling of 30,000 unique refits and 8 CPU-hours for the initial protocol. If the pilot exceeds either, freeze a reduced protocol *before outcome inspection* or report a resource block. Do not silently reduce seeds or bootstrap replication mid-analysis. Mandatory audit/primary tests take precedence over optional controls.

Run long phases in resumable background jobs with bounded threads, deterministic seeds, per-fit statuses, atomic checkpoints, and no interactive prompts/network access. Host tool calls exceeding 300 seconds require background execution and logs. Exact-fit failures receive one deterministic cold-start/higher-iteration retry; persistent failures stay in the results and prevent passing the affected gate. Solver logs include gradient norm, objective, iteration count, and warm/cold provenance.

**Iteration triggers:** change implementation only after analytic/finite-difference failure; change optimization settings after solver failure while preserving the objective; retain but qualify finite-influence failures; stop cross-source comparisons when common support or matched data are missing. Do not change datasets, season, target set, objective, or primary budget to obtain significance. Large ridge sensitivity, high disconnection incidence, missing clustering metadata, or attack effects comparable to numerical tolerance mandates narrower claims, not more aggressive searching.

## Recommendations

1. Make exact-refit prediction validity the core result; targeting superiority is a separate, falsifiable test.
2. Treat cross-design contrasts as descriptive unless supported by matched controls; do not rank domains by raw percent-edited curves.
3. Require the authorized snapshot manifest first, and retain negative, disconnected, tied, and inconclusive outcomes in the final evidence table.
