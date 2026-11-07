# CPU study plan: selecting whole benchmarks for unseen embedding models

Status: prospective protocol; no experiments or web searches performed by the planner. Read together with `success_criteria.md` (decision rules) and `todos.md` (execution order). Freeze these files and resolved manifests before exposing test scores. Proposed script names below describe future runner responsibilities, not existing implementations.

## 1. Assumptions, scope, and defensible claims

- Input: incomplete historical model × benchmark scores, not benchmark items. Each acquired label is one whole benchmark score for a new model. Equal label cost is assumed; no claim about wall-clock evaluation savings without actual cost measurements.
- Primary source: MTEB results commit `6dabbcc68c28ea5f180ce7df79347b3ca9cc6383`, CC0-1.0. The reported 548 directories are a discovery lead, NOT 548 unique usable models. No data were present in `/work/data/raw` at planning time. Determine actual rows, tasks, revisions and coverage from the pinned snapshot.
- CPU only, one week, total workspace storage <5 GB. No embedding model inference, GPU, foundation-model training, transductive fitting, or new benchmark collection. Ground-truth labels already in the snapshot simulate costly evaluation of genuinely held-out rows.
- Narrow question: does standard shrinkage-Gaussian conditional prediction combined with training-only greedy benchmark selection improve score prediction on fixed, never-acquired audit tasks for unseen model organizations?
- Potential contributions: a reproducible evaluation/cohort protocol for incomplete public scores, a careful empirical comparison of standard estimators/selectors, and a boundary-condition analysis. Gaussian conditioning, covariance shrinkage, trace design and low-rank regression are NOT claimed as algorithmic novelties.
- Predeclared claims: C1 selection utility against random with the same imputer; C2 competitiveness against simple selectors and low-rank prediction; C3 robustness boundaries under organization shift and missingness. C2/C3 are secondary; no universal generalization, optimality, causal missingness correction, or representative-MTEB claim.
- All split-test models are absent from fitting, preprocessing, hyperparameter selection, and acquisition design. Organization is an imperfect family proxy, not proof of independence from shared pretrained ancestors.
- No web access in this planning task. Future executor must obey intake access restrictions: no topical searches, citation graphs, or attempts to identify the prohibited work. If literature work is authorized, only exact allowed starter bodies (avoid bibliographies), specified data endpoints, official conference pages and generic software docs; log each access in `/work/literature/access_log.md`. Cite only works actually read. Stop and log incidental prohibited exposure; do not guess what was prohibited.

## 2. Study stages and gates

### Stage 0 — Preflight, manifests and prospective registration (day 1)
**Goal:** establish a small, auditable CPU workflow before any analysis.

**What to run, later:** environment/disk/thread preflight; pinned data acquisition and schema inventory; resolve dependency versions into a lockfile; create split/config manifests and artifact checksums. High-level runner interfaces: `preflight`, `acquire --commit <pinned>`, `inventory`, `freeze-protocol`.

**Success signals:** CPU execution enforced; <5 GB projected storage; exact source/version/license recorded; no prohibited access; no test-score summaries; no silent malformed-record or duplicate handling. Record OS, CPU/RAM, BLAS/thread settings, package versions, seeds, command lines and timing.

**Artifacts:** `environment/`, `data/source_manifest.json`, `data/schema_inventory.csv`, `literature/access_log.md`, `protocol/registration.json`, checksums for this plan and criteria.

### Stage 1 — Extract, split and freeze feasible cohorts (days 1–2)
**Goal:** separate a fair dense evaluation from naturally incomplete historical fitting.

1. Inventory model IDs/revisions, organizations, task IDs/configs/languages, evaluation split, metric names/directions/ranges, and coverage masks. One cell = canonical whole-task main metric for a fixed task version/config/evaluation split. Never mix train/dev/test evaluation variants or metric versions. Exclude composite leaderboard averages and category aggregates when constituent tasks are present; never treat subtasks, seeds or languages as independent duplicates of the same whole benchmark.
2. Use schema-defined task aggregation only; quarantine tasks needing unavailable weights or ambiguous metrics. Use task metadata for score units/direction, NOT full-data extrema to guess percent versus fraction. Retain raw and canonical values. Invalid/sentinel/nonfinite scores remain missing, never zero. Report disagreements among duplicate evaluations; if a cell cannot be resolved by fixed metadata rules, mark it missing. Drop exact duplicate score rows using training-only checks; globally group explicit aliases/revisions/base-ID derivatives using metadata before splitting.
3. Split the full canonical model universe before choosing tasks. Assign metadata-connected aliases to one group; primary grouping key is normalized organization, expanded by explicit revision/alias connections. Unknown organizations form one conservative group, not one new organization per row. Known shared base families across organizations are a flagged limitation and, where explicit metadata allow, a stricter connected-family sensitivity analysis. No grouping based on test score similarity.
4. Use five fixed outer seeds `11,23,37,53,71`. For each, hash-shuffle groups once and greedily allocate whole groups approximately 60/20/20% of rows to train/validation/test (stable tie breaks; do not retry seeds to improve outcomes). Matching random-row splits are secondary and still keep exact aliases/revisions together. Each split regime independently selects its panel from its own training partition; differing panels/cohorts make the regime comparison descriptive, not an isolated causal estimate of organization shift. Record imbalance and overlap, not just nominal percentages.
5. Within each split use TRAIN ONLY to find eligible tasks: at least 40 valid observations, >=60% train coverage, schema validity, and standard deviation >1e-6 of declared score range. Cap the panel at 24 tasks. Assign each task a permanent audit/candidate role using a stable cryptographic hash of `audit-role:101:<canonical task ID>` (hash integer modulo 3 equals 0 → audit, otherwise candidate), independent of scores; within each role choose highest training coverage, breaking ties by hash. Never change roles to improve accuracy. Preserve task-type diversity where available via metadata round-robin, then coverage order. Store the exact deterministic ordering.
6. Predeclared feasibility ladder: try total panel `(candidate C, audit T) = (16,8)`, then `(10,6)`, then `(8,4)`. Select the first panel with sufficient complete-panel evaluation rows. Training uses ALL eligible training rows, including incomplete rows (>=2 panel cells), and is never restricted to complete rows for the main estimator. Validation/test dense cohorts require observed values for every selected panel task. This is a coverage-conditioned estimand, explicitly not the whole leaderboard population.
7. Minimum per accepted split: >=60 usable train rows from >=15 groups, >=20 complete validation rows from >=5 groups, >=30 complete test rows from >=8 groups. Use only masks/counts to check held-out feasibility; no held-out scores/statistics. This mask-conditioned sampling is disclosed rather than called fully blind population sampling. No tier selection by accuracy, no replacement of failed seeds. Require >=3 of the five preset organization splits; otherwise stop confirmatory claims and publish a feasibility/coverage report. Freeze task panels, row IDs, masks, seeds, tiers and exclusions before test-score access.
8. Secondary native-coverage cohort: retain each eligible held-out row with >=2 observed audit cells and >=4 available candidates. Its feasible anchor set F_i (observed candidates) and target T_i (observed audit tasks) are fixed for ALL policies before prediction. Evaluate k<=|F_i| only; fix row eligibility at the largest reported k for each curve, never let policies choose which rows/targets get scored. Record this as mask-informed, coverage-biased simulation. It cannot reveal performance on historically unreported cells.

**Success signals:** no model/group overlap; each panel has disjoint C and T; primary targets and rows identical across policies; feasibility gate satisfied without using test values; extraction exclusions and selection bias quantified.

**What to run:** `extract --schema-policy <frozen>`, `make-splits`, `make-panels --train-only`, `audit-cohorts`. These are planned interfaces.

**Artifacts:** canonical long table and matrix/mask; row/task dictionaries; exclusion/duplicate audit; organization mapping; five split manifests; panel/coverage table; coverage heatmap; inclusion versus exclusion metadata summary. No claim that 548 directories survive.

### Stage 2 — Standard estimators, selectors and correctness checks (days 2–3)
**Goal:** isolate acquisition quality from imputation quality and forbid transduction.

**Preprocessing:** fit each task's mean and standard deviation on observed TRAIN cells only; scale floors fixed above. Use these transforms for validation/test and inversion to score units. No full-matrix centering, task filtering on test variance, test-row refitting or clipping based on test distributions. If clipping to documented task ranges is used, make it a uniformly applied secondary analysis, not the primary result.

**Main estimator:** on standardized training scores, compute pairwise-overlap covariance using overlap-centered pairs (>=20 shared observations; insufficient off-diagonals set to zero and logged). Symmetrize, project to PSD by eigenvalue clipping at 1e-8, and renormalize diagonals to one. Shrink toward its diagonal:

`Sigma_lambda = (1-lambda) Sigma_PSD + lambda diag(Sigma_PSD)`.

Condition an unseen row only on its acquired coordinates A:

`prediction_U = mu_U + Sigma_UA solve(Sigma_AA, x_A - mu_A)`.

Use stable solves with a fixed 1e-6 numerical ridge in standardized units; never invert explicitly. The tiny ridge is numerical regularization, not a fitted observation-noise model. Log failures and condition numbers. No score from other held-out rows is used to infer a new row.

**Main deployment selector (G-deploy):** start A empty, U=(C\A) union T. At each step consider j in C\A; condition on j and score ONLY residual, still-unmeasured coordinates U\{j}. Choose minimum posterior residual trace. Given current conditional covariance V, the ideal exact-observation expression is

`R(j) = sum_{u in U\{j}} [V_uu - V_uj^2 / V_jj]`.

Use the consistent ridge-stabilized block-conditioning computation operationally, recomputed for A union {j}. This excludes j's residual variance. Equivalently in the ideal exact-observation case, `R(j)=trace(V_UU)-V_jj-sum_{u!=j} V_uj^2/V_jj`. Tracing a fully conditioned covariance over the old U is also correct if j's posterior variance is zero; the errors to guard against are retaining its PRE-acquisition variance or subtracting it twice. Self-removal legitimately favors high-variance tasks in deployment, but cannot establish useful transfer: the primary fixed audit evaluation below tests that separately. Selector paths depend on TRAIN covariance, not acquired score values; call this static/sequential design, not score-adaptive acquisition. Native-coverage paths may depend on F_i, never on unavailable target scores.

**Acquisition baselines, same tuned Gaussian imputer:**
- Random: 50 fixed random permutations, nested prefixes across k; same permutations reused wherever eligible across methods/ablations. Average loss over all 50, not best seed.
- High variance: descending train variance in original canonical score units; also report standardized-variance ties deterministically because standardization otherwise destroys this baseline. State its unit dependence.
- Correlation coverage: greedily maximize `sum_{t in T} max_{a in A} corr_train(t,a)^2`, using the same train-derived correlations, uniform target weights and fixed ties. It is an audit-aware comparator, not identical to deployment objective.
- G-audit ablation: greedily minimize posterior trace over fixed T only; no audit task can be selected. This tests whether the deployment objective and task self-removal undermine fixed-target transfer.

**Prediction baselines:**
- Train mean, k=0; display flat at larger k but mark it as spending zero labels.
- Masked low-rank ridge: fit training-only factors to observed standardized cells by minimizing `sum_observed (z_ij - u_i dot b_j)^2 + alpha*(||U||_F^2 + ||B||_F^2)` (do NOT impute test rows jointly); use rank-r task loadings. Solve each new row's latent ridge regression from A with the same alpha and predict U; k=0 returns zero standardized residual. Fixed 3 initialization seeds averaged in prediction; train reconstruction convergence tracked. Compare on identical anchors to Gaussian, especially random anchors and G-deploy anchors, to isolate the imputer. Also evaluate a standard low-rank D-optimal loading selector (greedy `logdet(alpha I + sum_{a in A} b_a b_a^T)` gain, averaged across the three fits) as a complete low-rank baseline; it uses training factors only. No optimality claim for it.

**Ablations designed before testing:** shrinkage lambda=1 (diagonal, predicts means), lambda=0 after PSD repair, tuned shrinkage; pairwise covariance versus mean-filled training covariance with identical PSD/shrinkage handling; complete-training-row covariance only if >=40 rows (otherwise mark infeasible); G-audit versus G-deploy; correct residual-exclusion objective versus a clearly labeled intentionally wrong diagnostic `R_wrong(j)=R(j)+V_jj` that retains j's PRE-acquisition variance (not a correctly fully conditioned trace). Raw unprojected pairwise covariance is a numerical diagnostic, not an accepted covariance when indefinite.

**Hyperparameters:** Gaussian lambda grid `{0,.1,.3,.6,.9,1}`; choose once per outer split by mean validation fixed-audit normalized MSE averaged over random anchors at k={1,2,4}. Then SHARE that lambda across all Gaussian selectors, primary baselines and selection ablations. This makes the primary comparison a selector comparison, not unequal tuning. Low-rank rank `{1,2,4,8}` (truncate at dimension limit) × ridge `{.01,.1,1}`; select on the same validation criterion/random anchors, not training reconstruction. Max 18 estimator configurations per split, plus fixed ablations. Ties within 1e-4 loss: stronger shrinkage, then lower rank/stronger ridge. No test-based retuning. Per-selector tuning is optional sensitivity only and must use equal grids/validation budgets. Preserve every validation candidate result.

**Success signals:** deterministic repeatability; label-reveal guards; exact target pairing; predictions invariant to permutation of other test rows; diagonal case equals train means; k=0 equals mean; posterior update/residual exclusion agrees with direct conditioning on a toy PSD matrix; low-rank inference works for a single held-out row. Tests may use synthetic examples, not test outcomes.

**What to run:** `check-contracts`, `fit --train`, `tune --validation`, `freeze-models`. Future implementation only.

**Artifacts:** correctness-test report; selected hyperparameters; all validation losses; solver/PSD diagnostics; cached train-only acquisition paths; fit/time/memory logs.

### Stage 3 — Frozen paired held-out evaluation (days 3–4)
**Goal:** test C1 before optional expansions.

- Label counts: k={0,1,2,4,6,8}, limited by panel size; core confirmatory summary uses k={1,2,4}, common to all panel tiers. Use nested acquisition paths and identical held-out rows and audit cells across all policies/budgets within each split.
- Primary fixed-audit protocol: T is complementary to candidates C and is never selectable. Every policy predicts exactly T for each dense-cohort model. Candidate-set construction and audit roles are independent of policy choices. For native coverage, fixed T_i and F_i are likewise shared.
- Primary loss: per-model mean squared error over audit tasks after TRAIN-SD standardization; then mean across held-out models. This gives uniform task weights on the dense panel, avoids unit dominance, and is called normalized MSE (NMSE). Core budget summary is the arithmetic mean of NMSE at k=1,2,4, then equal-weight mean over accepted preset splits. Do not call this logarithmic area under a curve.
- Primary paired contrast: G-deploy versus random with the SAME Gaussian imputer. Define relative improvement `I=1 - L_G/L_random`; always also report absolute paired difference. No best-of-random, best split, or best k selection.
- Secondary: NMSE/RMSE/MAE curves; raw-score RMSE by task and macro-average canonical 0–1 score units only where compatible; per-category errors; organization-macro NMSE; random-row versus organization splits; train-mean improvement; all full baselines; rank correlation of a fixed audit aggregate only as exploratory. Spearman is undefined for constant predictions and is reported as such, not filled with a favorable number.
- Secondary deployment error: predict all genuinely unmeasured coordinates `(C\A) union T`. Its targets differ by policy, so explicitly mark it NON-PAIRED-IN-TARGET and not evidence for C1. Additionally show fixed-audit loss and an identical predeclared candidate holdback subset if feasible. Never report measured-label reconstruction as prediction performance.
- Uncertainty: report all split-level contrasts, mean and range. Use 2,000 paired organization-cluster bootstrap draws: sample organization IDs once per draw, carry all their model/budget/method/repeated-split records together, recompute equal-split losses and ratios. Preserve paired random paths. Do not treat tasks, random permutations, or repeated appearances in overlapping splits as independent samples. Intervals are conditional on the trained split pipelines and selected cohort; they do not capture all training/data-source uncertainty. Repeat the random-policy seed bank once as an MC sensitivity if its estimated SE exceeds 1% of its loss.
- C1 is the only confirmatory comparison; mark additional comparator/budget tests descriptive, or Holm-adjust a predeclared secondary family if making significance claims. CIs are not distribution-free proof of generalization.

**Success signals:** criteria file applied mechanically; no post-test cohort/metric/tuning changes; >=3 valid organization splits; complete paired predictions; intervals and split heterogeneity reported even for negative results.

**What to run:** `evaluate --frozen-manifest --test-once`, `paired-summary`, `bootstrap --cluster organization`.

**Artifacts:** per-cell predictions and masks (license permitting), per-model losses, split/budget/baseline tables, fixed-audit label curves, paired-difference/CI plot, secondary deployment panel clearly labeled, immutable test access log.

### Stage 4 — Stress tests and optional stopping (days 4–5)
**Goal:** bound conclusions, not rescue a failed headline.

- Missingness: keep dense validation/test targets and anchors unchanged; independently delete 0/20/50% of originally observed TRAIN cells. Compare MCAR, task-propensity deletion calibrated from training coverage, and an explicitly synthetic score-dependent mask preferentially hiding high scores. At each requested extra deletion rate rho in {.2,.5}, use MCAR p_ij=rho; task-propensity p_ij=min(.95,a/(c_j+.05)), where c_j is original TRAIN task coverage; score-dependent p_ij=min(.95,a*(.1+q_ij)), where q_ij is that score's within-task TRAIN percentile. In the last two cases choose scalar a so mean p over originally observed training cells equals rho. Couple masks across rates with one uniform draw per cell. The deletion generator may use original TRAIN scores, but the estimator must not access deleted values. Fix deletion seeds and probabilities using training data only. Keep task panels fixed as a declared conditional-panel stress design, but recompute means, scales, pairwise covariances and all estimator fits from RETAINED observed training cells only; repeat the same bounded validation tuning under each deletion. Do not use synthetically hidden labels in preprocessing or fitting. Compare methods on the same retained-training normalization within a deletion condition; show raw-unit errors as well when comparing levels. Never create ground truth for historically missing cells. Log achieved rates, pair overlap, PSD repair and collapse to mean. Stress tests are secondary, not substitute test sets for choosing the headline.
- Availability stress, separate from train-label deletion: pre-mask candidate availability per validation/test row at 20%, independently of score; share masks across policies, fix rows with >=4 feasible anchors, keep T intact. Label this exogenous availability simulation.
- Native incomplete historical cohort as Stage 1, with same target cells/rows for every method; compare coverage-conditioned results and selection rates to the dense cohort. Report no conclusions about unobserved MNAR labels.
- Optional risk stopping only if core is complete: using VALIDATION fixed-audit curves, select the smallest global k within one organization-cluster SE of the minimum validation loss over available k (including 0). Freeze one k per policy/split, then apply to all test rows. Report test loss and labels, not test-chosen k. This is validation-based global budget choice, NOT calibrated per-model risk or a guaranteed confidence bound. Include fixed-k results regardless.

**Success signals:** same target supports; no deletion outside training in train-missingness experiment; seeds and achieved coverage logged; direction reversals explicitly reported. Do not require a positive result to pass the research integrity gate.

**What to run:** `stress --frozen-masks`, optional `select-budget --validation`, then a single registered stress evaluation.

**Artifacts:** deletion robustness plot, covariance/overlap diagnostic table, cohort selection comparison, optional risk–label table.

### Stage 5 — Optional transfer and complete reproducible report (days 5–7)
**Goal:** finish a narrow honest paper; transfer is a stretch goal, never a core dependency.

- Optional Open LLM leaderboard snapshot `9c09a7cae43334062a82cb164f2ef255013dafa2`, reported 4576 rows/six tasks; verify actual content and license (unspecified in intake). Do not redistribute raw data without confirmed permission. Use the same frozen pipeline with six whole tasks, deterministic 3-candidate/3-audit roles, k={0,1,2,3}; primary-style budget summary k={1,2}. Organization/alias splits and complete-cohort gates still apply. No language-model inference. Call it exploratory pipeline transfer; do not pool its metrics with MTEB, and do not use it to rescue C1. Defer HELM/LiveBench/BigCodeBench/AlpacaEval entirely within this week.
- Build results inventory, timings, table/figure-to-command map, data access/exclusion log, and claim ledger. Negative/conditional outcomes are valid completion. Exact Gaussian trace identity may be checked on toy cases but no unnecessary theorem/submodularity/optimality claim.
- If the executor is tasked with the intake paper deliverable, use the latest official ICML/ICLR/NeurIPS template verified on an official page at execution time; record venue/year/page limit/checklist instead of assuming a version now. Compile LaTeX/PDF locally. No citations inferred from paper IDs or titles. The present task supplies plans, not manuscript or code.

**Artifacts:** reproducibility README, environment lockfile, commands/seeds/version/timing manifest, tables/plots, `/work/paper/` LaTeX and PDF if commissioned, limitations/checklist, checksum manifest. Essential figures: (1) split→train-only fit→acquire C→predict fixed T diagram; (2) audit error versus k with CIs, group/random panels; (3) missingness stress. Essential tables: cohort coverage, paired main comparison, ablations, resources. Plain diagrams should highlight protocol, not imply a novel Gaussian module.

## 3. Dependencies and resource envelope

- Data: pinned MTEB score snapshot and task/model metadata; no raw embedding datasets needed. Prefer bounded snapshot download without full git history; inspect remote/archive size before acquisition. Keep one compressed raw snapshot plus compact canonical table; no repeated extraction copies. If projected total exceeds 4 GB, stop optional acquisitions and reduce retained redundant raw packaging without losing provenance. Absolute hard limit 5 GB.
- Environment: Python 3.11 or a compatible available release; `numpy`, `scipy`, `pandas`, `scikit-learn`, `pyarrow`, `matplotlib`, `seaborn`, `joblib`, `threadpoolctl`, `psutil`, `PyYAML`, `requests`, `pytest`; `huggingface-hub` only for optional data. Resolve and pin working versions before runs, record BLAS. `scikit-learn` shrinkage helpers are not assumed valid for pairwise-missing covariance. TeX tooling only if producing the paper, never download multi-GB TeX installations blindly.
- Preflight commands to be run by executor: `python --version`, `lscpu`, `free -h`, `df -h /work`, and a dependency/BLAS report. Record GPU/CUDA/VRAM as irrelevant/unused; `nvidia-smi` only if present, no GPU requirement. Set `CUDA_VISIBLE_DEVICES=''`, BLAS threads 1–4, one outer job initially. No torch/transformers required.
- Target workstation: 4 CPU cores and 8 GB RAM; matrix up to ~1,000 rows × 24 tasks is tiny. Pairwise fitting ~O(n d^2), covariance solves ~O(d^3), far below training a language model. Low-rank iterations and repeated bootstrap should dominate; profile one validation split before multiplying runs. Timeouts: max 200 low-rank iterations, relative objective tolerance 1e-5, fixed 3 starts, log nonconvergence; preserve a valid simpler baseline if low-rank fails.
- Budget: <=24 CPU core-hours core evaluation, <=48 including stress/optional transfer; <=2 GB process RSS target. These are ceilings, not measured runtimes. Reduce optional work before compromising splits or fairness. In tooling with a 300 s command timeout, run long work in bounded batches/background with log/status files; do not blindly rerun timed-out jobs. Reserve final two days for analysis/reproducibility.

## 4. Iteration triggers and change control

- Cohort fails gate: follow frozen panel ladder, not model-performance filtering. Fewer than three valid preset group splits → descriptive feasibility only; do not silently switch to random rows. Native-coverage analysis may remain explicitly secondary. Any new cohort design requires versioned protocol before a fresh untouched test set; old test results become exploratory.
- Pair overlaps sparse/PSD repair large: report fraction missing pairs and relative Frobenius PSD change; >25% unsupported pairs or >20% repair norm triggers a warning and diagonal/mean-filled sensitivity, not hidden parameter expansion. Covariance has no positive-definiteness guarantee before repair.
- Validation no better than train mean: keep mean/diagonal, report failure; no larger model or new objective fishing. Underperformance on group but not random splits → narrow to within-organization results, not unseen-family generalization.
- Main comparison null/negative: no change to C1. Use the predeclared boundary-condition/negative-result narrative. Audit versus deployment reversal → discuss target-removal/objective alignment, not advertise deployment-only accuracy as acquisition success.
- Test-discovered implementation bug: quarantine affected results; log bug and scope; repair with synthetic/train/validation checks; publish both invalidation and rerun history. Re-exposure is no longer a pristine confirmatory test. Never delete inconvenient runs.
- Optional OpenLLM only after core artifacts complete, license checked, storage/time gates pass. No replacement of MTEB just because another dataset looks easier.

## 5. Limitations and top-five pre-emptive rejection risks

| Risk / likely rejection | Planned response and remaining limitation |
|---|---|
| 1. Standard method / limited novelty | Explicit standard-method framing; contribution is falsifiable protocol and evidence, not invented algorithmic novelty. Empirical value remains contingent on results. |
| 2. Wins arise by measuring/removing hard targets | Fixed complementary audit T, identical row/cell supports, same-imputer random baseline; deployment-changing-target error secondary only. |
| 3. Leakage / near-duplicate families / transduction | Organization+alias grouping, train-only transformations/covariance, validation-only tuning, single-row inference and permutation guards; organization still misses shared cross-org ancestors. |
| 4. Cherry-picked dense panel / MNAR historical reporting | Frozen training-only task selection and mask-only feasibility ladder; inclusion/exclusion tables, native-coverage and synthetic deletion sensitivity; no recovery claim for truly missing labels. |
| 5. Weak baselines / small uncertain evidence / unequal cost | Mean, random same imputer, variance, correlation, low-rank selector and fixed-anchor imputer comparisons; >=3 preset splits, clustered paired uncertainty, equal k and bounded tuning. Task measurement costs and public-score noise remain unmodeled. |

Additional limitations: deterministic covariance policy is not score-adaptive; Gaussian moments may fit poorly; score noise and benchmark contamination are inherited; task-role choices constrain the estimand; CPU timing excludes actual benchmark evaluations; repeated splits share training/test organizations; optional six-task transfer is small and exploratory. No guarantee of publication or superiority.
