# Local code/statistical audit

Date: 2026-11-02. Audit only; no source code, tests, data, or existing run outputs were changed. Recommendations below are for the main agent to implement.

## Verdict

**The BT objective, Newton signs, canonicalization, and primary physical-row witnesses are correct on the checks performed.** All six tests pass. Independently reconstructing each attack by changing the original labels and fitting a fresh BT instance reproduces every reported primary reversal.

**Do not report the Arena matching output as repeated N=3,355 subsampling.** It is twenty copies of the same N=3,222 dataset. Also correct the secondary top-one metric's handling of ties. Claims about individual GPT judging calls, fixed-schedule bootstrap uncertainty, unconditional attack-budget uncertainty, or causal design comparisons require the qualifications below.

Severity: High = blocks the associated reported claim/control, not necessarily the primary witness result; Medium = affects a secondary metric or materially changes interpretation; Low = hardening/reporting issue.

## Confirmed implementation bugs

### B1 — High: Arena size-matching silently becomes twenty identical full-pool runs

**Location:** `src/run.py:108–116`, particularly `sample(n=min(len(human),len(sub)), ...)` and the hard-coded label `arena_top6_n3355`.

**Evidence:** `matching_protocol.json` records an Arena top-six pool of **3,222** rows, whereas human N is **3,355**. `matched.csv` has twenty Arena rows, each with N=3,222, E=2,321, k=7, gap=0.06514500907066484 and identical fitted outputs. Different seeds merely permute the full dataset; they do not generate subsample variability.

**Impact:** Neither equal-N matching nor repeated-subsample uncertainty has been achieved. Treating the twenty rows as replicates is pseudoreplication, even if no formal standard error is computed.

**Minimal fix:** Immediately relabel this as one full top-six cohort analysis, with its actual N, and remove repeated-subsample claims. If genuine repeated size controls are needed, choose and disclose a common N strictly below the eligible pool sizes and rerun both comparison sides, or choose a documented larger eligible cohort before sampling. Do not sample with replacement just to reach 3,355 while calling the results distinct physical judgments. Record requested N, actual N, pool N, and a selected-row-set identifier; assert the intended invariants rather than silently applying `min`.

### B2 — Medium: `top1_changed` can count a tie as a strict replacement

**Location:** `src/run.py:48,63`; the related `leader_same` bootstrap metric at line 69 uses the same argmax convention.

**Evidence:** Local two-player counterexample: participant index 1 has seven wins and three losses. Flipping two winning rows yields a 5–5 tie. The refit scores are numerically zero (approximately ±1.8e-16); `np.argmax(theta) != 1` is true, but nobody strictly exceeds the original leader by 1e-7. Which participant gets counted as top-one depends on index and numerical noise.

**Impact:** Secondary top-one rates are not strict leader-replacement rates and can disagree with the deliberately strict primary success criterion. This check establishes a metric bug; it does not establish how many existing output rows are affected.

**Minimal fix:** Define strict dethroning as `max(theta[:m]) > theta[a] + tol`, with the same documented tolerance as other ranking events. If deterministic tie-broken winner change is desired instead, explicitly give that different estimand a different name and report ties separately. Add this reversed-index 5–5 regression test.

## Claim/protocol blockers and statistical limitations (not BT solver bugs)

### S1 — High for original-call claims: GPT units are exported pair-result rows, not demonstrated reciprocal calls

**Location:** `src/prepare.py:24–30`; Stage 1 of `todos.md` says reciprocal GPT judgments are retained separately.

**Local evidence:** GPT has 2,400 rows, 2,400 distinct **unordered** question/model-pair/turn cells, and judge `gpt4_pair`. Its winners include 380 `tie (inconsistent)` and 220 `tie` rows. There is no second reciprocal observation for a cell in this input. The available columns do not expose two underlying reciprocal call labels. Thus this code does not implement the stated separate-reciprocal-judgment protocol. The input strongly signals a derived pair-result unit; the exact upstream combining procedure is not established by this local audit.

**Minimal fix:** State that the GPT edit unit is one **exported pair-result row**, not one individual GPT call, and mark the protocol deviation. Describe the inconsistent-to-half mapping explicitly. Do not infer individual-call edit costs from these data. Keeping 380 inconsistent results at y=.5 is a transparent modeling convention, not a factual finding that they are genuine preference ties; consider a separately labeled exclusion sensitivity if that distinction matters. No new download is required to make the narrower claim honest.

### S2 — Medium: uncertainty resampling is not conditional on the original fixed comparison schedule

**Location:** `src/run.py:64–73`.

Rows are bootstrapped for Arena/NBA; questions are cluster-bootstrapped for MT. This is a legitimate empirical pairs/cluster bootstrap, but edge counts change and some original rows disappear or are repeated. MT human total N varies: **3,136–3,646** in the 200 observed draws. This does not preserve the original fixed schedule. The fixed-schedule property of each primary label attack is unaffected.

**Minimal fix:** Call these empirical row/question-cluster resampling summaries with fixed target identities, not conditional fixed-schedule outcome uncertainty. If fixed-schedule uncertainty is required, define a separate outcome-resampling model on the original rows and state its dependence assumptions; that is a different analysis, not a renaming of this bootstrap. Holding the original targets fixed is appropriate for a selected-target descriptive analysis, but does not yield post-selection-valid or simultaneous population confidence intervals.

### S3 — Medium: bootstrap witness budgets are positive-margin-conditioned and use duplicated bootstrap slots

**Location:** `src/run.py:69–73`; `run_metadata.json` labels `bootstrap_witness_repeats` as 30.

Recomputation is attempted only in the first 30 draws and only if the original leader still beats the original runner-up. Valid witness counts are **16/30 Arena, 29/30 MT human, 30/30 MT GPT, 24/30 NBA2013, 28/30 NBA2014, 29/30 NBA2015**. Missing values otherwise conflate not-attempted, already-reversed/tied, and search-failure states. The expanded dataset treats repeated copies of one original judgment as separate attackable slots. This is coherent as a bootstrap-pseudodataset statistic, but is not an attack on unique original physical row IDs.

**Minimal fix:** Report the conditioning and actual counts, not “30 witness estimates per dataset.” Add an explicit status and attempted/successful denominator. For an unconditional fixed-pair budget distribution, already strict-reversed samples need k=0, while exact ties need separate handling under the strict target definition; heuristic search failures remain unresolved, not numeric lower bounds. Label all budgets as edits to resampled slots. If the intended unit instead remains an original physical ID, the duplicate-weight attack definition must be redesigned explicitly.

### S4 — Medium: sensitivity ablations sometimes change the target, not just the estimator

**Location:** `src/run.py:87–94`; `audit_one` reselects leaders unless targets are supplied.

Observed examples: dropping Arena ties reverses which of the two GPT-4 variants is the leader; NBA2015 at ridge=10 changes the runner-up from HOU to ATL. The latter changes E from 193 to 199. Therefore the resulting changes in k or k/E mix estimator sensitivity, target selection, and sometimes denominator changes.

**Minimal fix:** Label these as reselected-top-pair sensitivity analyses and show target names. For a same-claim sensitivity comparison, additionally freeze baseline target identities across ridge/home/tie analyses and record when the baseline pair is already reversed, rather than searching as though its margin were positive.

### S5 — Medium: E normalization is useful but does not make different designs exchangeable

**Location:** `src/run.py:16–21,55–63,98–116`.

- E counts the physical-row union incident to either target, including ties; N also includes ties. This is internally consistent with the stated protocol, but neither is the number of eligible decisive edits. Report decisive pool sizes as well.
- Global influence attacks may edit nonincident rows. Then k/E is an **exposure-scaled total budget**, not a fraction of incident rows edited. The current six primary witnesses all have `incident_k == k`, so this warning is structural rather than a demonstrated error in those six results.
- `local_budget=frac` sets `k=ceil(frac*E)` (at least one), not exactly k/E=frac. Uniform controls can spend those edits remotely. Actual incident edit counts and realized k/E should accompany any local-dose interpretation.
- Different domains have different participants, leader gaps, edge schedules, tie fractions and label units. E does not remove those differences. Fixed sum-loss ridge=1 also has different relative strength when N differs.
- Arena's six-model cohort is selected using full-data fitted outcomes, is not the MT participant cohort, and its freshly selected leader differs from the full-Arena leader. This is a post-selection descriptive cohort control, not evidence isolating a causal effect of the comparison design.

**Minimal fix:** Use descriptive, within-estimand language; show N, E, decisive counts, targets, baseline gaps and units. Do not call k/E a design-invariant robustness measure or claim cross-domain differences are caused by design. Correct B1 before calling the Arena exercise an N-matched control.

## Search and control validity

**No primary selection/search correctness bug found**, subject to the following limits.

1. `benefits` is the derivative of *decreasing* the leader-minus-challenger margin, so descending positive scores select the intended attack direction. It is a frozen local approximation, not an exact finite-flip oracle. Filtering initial scores to positive rows excludes potentially useful joint attacks; this limits search power, not witness validity.
2. `witness` verifies an actual strict reversal (<-1e-7) and the preceding prefix. Even without monotonicity, its bisection retains a noncrossing/crossing bracket and finds a verified neighboring transition. It need not find the earliest crossing along the full ordering and cannot establish a globally minimum set. Powers-of-two probes can miss a crossing that later reverses again. `k=None` means **no witness found by this search**, not robustness through 20% or a certified lower bound. The cap is 20% of decisive rows, not E or all N, and is also limited by the selected ordering's length. Preserve these distinctions in any censored plot or table.
3. All primary exported witnesses use distinct indices and decisive labels, and no tie rows are flipped. Aggregation changes sufficient statistics, not the physical-row budget. NBA `_iscopy==0` is checked for unique game IDs; Arena IDs are unique in the observed preparation artifact. Reciprocal source rows must not be fabricated to satisfy the protocol.
4. Equal-k uniform, incident-uniform, incident-beneficial, and edge-matched sampling are sensible controls for the stated heuristic. Incident-beneficial sampling itself uses outcome/target information; it is not an uninformed null. Edge matching holds edge edit counts, not directional win/loss edits. Holding edge *and canonical original outcome* edit counts makes the aggregate refit identical by construction; the ten assertions correctly test that algebraic invariance, not ten independent confirmations of a discovery.
5. There are 100 control repeats per dataset/method in the observed CSV. Report rates and Monte Carlo precision, not “random flips cannot reverse the ranking.” Zero successes in 100 trials still permits nonzero event probability (roughly a 3% one-sided 95% upper bound under independent repeats).
6. The primary event is **original runner-up strictly exceeds original leader**, which implies the original leader is dethroned but does not imply the runner-up becomes top-ranked. Other competitors can overtake first. Do not describe this witness as the minimum edits for *any* top-one change.

## Mathematical verification

For canonical edge vector x_e, counts n_e and wins w_e, the fitted objective is

`L(t) = sum_e [n_e log(1+exp(x_e^T t)) - w_e x_e^T t] + lambda/2 ||t||^2`.

Thus `g=X^T(n*p-w)+lambda*t` and `H=X^T diag(n*p*(1-p)) X+lambda*I`. For positive ridge H is positive definite. Solving `H step=g` and updating `t -= rate*step` has the correct Newton sign. This is a **sum loss**, with no hidden averaging. Positive ridge automatically centers participant scores at the optimum because their design columns sum to zero; it also penalizes the home coefficient when included.

For original row i, canonical wins change by `delta_w_i=sign_i*(1-2*y_i)`. For margin `c^T t=t_leader-t_challenger`, implicit differentiation gives `delta_margin=c^T H^-1 x_edge(i) delta_w_i`. The code negates this to define a positive attack benefit. Canonicalizing the home covariate by the same orientation sign is correct.

Checks performed:

- `pytest -q -p no:cacheprovider /work/tests/test_bt.py`, with source path set and bytecode disabled: **6 passed**.
- Independent original-label refits for all saved witnesses:

| Dataset | Distinct decisive flips | Refit margin |
|---|---:|---:|
| Arena | 2 | -0.000870818731 |
| MT human | 46 | -0.007132467517 |
| MT GPT | 61 | -0.006430681069 |
| NBA2013 | 3 | -0.058564631052 |
| NBA2014 | 4 | -0.066514875036 |
| NBA2015 | 8 | -0.052903582031 |

Maximum difference from stored primary refit margins was <5.4e-11. Independent fit gradients were <2.7e-9 and participant scores centered to numerical precision.

- A mixed-orientation home-covariate example agrees between the aggregate objective and the original-row objective to 1.8e-15. Finite-difference flip benefits across every decisive row agree to <5.3e-11.
- The observed primary runtime gradient maxima are all <1e-8. The implementation nevertheless allows return up to 1e-6 (`bt.py:68`), looser than the protocol's <1e-7 gate. This did not affect the recorded primary fits; align or document the tolerance for future runs.
- `disagreement` measures the fraction of all participant pairs with a strict sign inversion; ties contribute zero. This is not a tie-corrected Kendall tau distance. Keep the literal metric name/definition, especially for symmetric bootstrap outcomes.

## Matching/data leakage assessment

The matched MT analysis really does retain the same ordered question/model-pair/turn schedule on both sides: 1,232 cells, N=1,232 and primary E=711. The 1,751 eligible human source rows in these ordered shared cells have identical answer-pair representations to their matching GPT rows in the local inputs (zero mismatches in a local comparison without printing answer text). There is no detected prompt/answer mismatch or held-out-evaluation leakage in that check.

The code samples one original human judgment per cell rather than averaging judgments into a soft label; this preserves a physical-row flip interpretation and is reasonable, but differs from the planned averaging sensitivity and needs a documented deviation. It intersects **ordered** cells: human data have 2,396 ordered but 1,814 unordered cells, while GPT has 2,400 of both. The 1,232-cell intersection is therefore an order-selected subset, not every semantically shared unordered pair. Preserve that narrow interpretation; canonicalize orientation and labels only if intentionally changing to unordered-cell matching. The twenty human runs vary which judge row is sampled, not questions or the GPT labels, and should not be described as twenty independent datasets.

Using the same observed labels to choose a leader and construct an adversarial witness is intrinsic to this retrospective audit, not conventional train/test leakage. What is unsupported is interpreting those selected-target results as out-of-sample ranking guarantees or as a causal comparison of human/GPT/crowd/sports designs. No source provenance/hash or upstream reciprocal-call reconstruction audit was performed.

## Recommended implementation order

1. Fix or withdraw B1's repeated equal-N matching claim; regenerate only the affected control artifacts if desired.
2. Fix B2's strict top-one/tie semantics and add a regression test; regenerate affected secondary summaries.
3. Correct GPT unit/protocol language (S1), bootstrap conditioning/status reporting (S2–S3), and changing-target sensitivity labels (S4).
4. Keep the six primary results as refit-verified **witness upper bounds**, with explicit physical exported-row units and descriptive cross-design comparisons (S5).

## Scope and contamination disclosure

Read the five requested files and local numerical/raw-data artifacts needed for the checks. No network access, code-agent delegation, prior-work files, or memory bodies were used. A mandatory higher-priority memory preflight returned a prior-work summary/snippet before the local audit; therefore the requested absolute no-memory-access condition could not be met. That retrieved material was not used as evidence or included as substantive findings here. No persistent memory was written. The only task output created is this audit; Python checks disabled bytecode/cache writes. This is a snapshot audit, not a claim of exhaustive absence of defects.
