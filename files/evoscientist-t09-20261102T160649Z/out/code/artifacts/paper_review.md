# Self-Review

## Verdict

**needs-work — one fixable statistical reporting blocker; no detected failure of the central GATE calculations.**

- **Draft:** `/work/paper/main.tex`; PDF `/work/paper/main.pdf`; extracted text `/work/artifacts/paper_extracted.txt`.
- **Review artifact:** `/work/artifacts/paper_review.md`.
- **Priority:** fix or suppress the pooled failure-conditioned MCSEs (F1); expose heatmap availability (F2); reconcile the analysis protocol and validation claims (F3–F4). Remaining fixes are small. No main simulation rerun appears necessary.
- **Scope:** strictly offline. Literature/provenance assessment used only `literature_notes.md` and `data_source_notes.md`. No new literature, searches, prohibited-paper identification, or draft edits. README preparation is concurrent; its absence/completeness is **not** assessed as a failure.
- **Workflow:** end-to-end adversarial reading and suspicion recording preceded loading `five_aspect_review.js`. No code-interpreter/task-dispatch runtime is available, so all five aspects were reviewed sequentially using its checklists. Pass 3 was separately executed with local Python/shell checks, not assumed covered by Pass 2. All five aspects completed. Figure PNGs were visually inspected; PDF page/text/layout checks used pypdf, not a full rendered-page inspection.

**Reject-first simulation:** A hostile reviewer could reject this as elementary algebra plus familiar extrapolation warnings, with a reporting pipeline that does not fully deliver its promise of uncertainty-qualified reproducibility: failure-conditioned mixture SEs omit random accepted-weight variation, a heatmap compares differently selected subsets without showing their availability, and the manuscript overstates validation actually enforced by the analyzer. These are stronger objections than demanding SOTA wins from an explicitly diagnostic study. Novelty cannot be comprehensively resolved under the source restriction.

## Pass-1 Suspicions

“Open” means an actionable issue or an explicitly unresolved question remains after all passes; “resolved” does not mean a general theorem was established by numerical tests.

| ID | Original suspicion and location | Confidence | Evidence that would settle it; result | Status |
|---|---|---|---|---|
| S1 | Valid-count pooling may give the wrong repeat-MC SE for the claimed conditional mixture; §4 metrics, Appendix B | High | Reconstruct the estimator and variance from attempted raw records. Confirmed omitted accepted-weight variation in sparse cells; F1. | **Open** |
| S2 | Table 2 confuses availability counts/fractions and observed error bias with noise-integrated bias; §5.2/Table 2 | High | Compare captions, macros and CSVs. Bias distinction is correctly stated, but availability notation/accent need F7. The table's −.956 and prose's −1.000 are different correctly defined metrics, not conflicting estimates. | **Open** |
| S3 | Exact-rank symmetry may not survive the numerical Gram threshold; Proposition 3/Appendix B | Medium | Check accepted sets under complementation and near the cutoff. Add has zero rank failures in all reported suites; exhaustive irregular-small-graph checking found no mismatched pairs. Exact-rank proof is sound; numerical rule still merits the qualification below. | Resolved for reported cancellation evidence; general numerical invariance not certified |
| S4 | Count, two-hop, interaction endpoints, covariance orientation or exposure probabilities could be wrong; §4/Eqs. 8–9 | High-priority suspicion, now low residual concern | Independently check features/endpoints, irregular covariance and exhaustive probabilities; replay existing records. Checks passed; see audit. | Resolved |
| S5 | The decomposition might be circular or use outcome information to construct bias/variance; Proposition 1/§5.1 | Medium | Trace `M`, `Y`, `w`, `truth`, `b`, `v`; recompute same-record gaps. Bias uses noiseless `M`, not `Y`; all 16 dedicated checks reproduced. | Resolved |
| S6 | Novelty/diagnostic contributions could be less new than framing suggests; introduction/related work | Medium | Permitted notes already discuss feature variance, count/fraction and multi-hop failures. An authorized independent literature assessment would settle broader novelty; not performed or recommended through prohibited routes. Reverse-substitution evidence exists in released summaries/heatmap. | **Open: novelty only** |
| S7 | Figure/table references, design labels and absolute-bias ordering may be ambiguous; Figs. 1–4/Table 3 | High | Source reference scan and plotting-code inspection confirm F2/F8. Figure 2 actually plots `abs(mean(b))`, not `mean(abs(b))`. | **Open** |
| S8 | “Known covariance repairs only when bias absent” may omit assumptions; abstract/§4/Appendix A | Medium | Check Gaussianity and positive variance. Both are stated for coverage; conditional error accounting itself needs neither Gaussianity nor correct mean specification. | Resolved |
| S9 | Generated numbers/PDF/counts may have drifted; §5/Appendix B | Medium | Recompute numerical summaries, check PDF boundary and code assertions. Current counts/numbers pass, but the analyzer does not enforce the expected-count validation claimed in prose; F4. | **Open: validation claim** |
| S10 | “Prespecified”/“fully reproducible” may overstate the protocol's alignment with analysis; intro/Appendix B | Medium | Compare frozen protocol with code and manuscript. Formula/mixture descriptions differ; F3. No inference of post-hoc outcome selection follows from this discrepancy. README not judged. | **Open: protocol reconciliation** |

**Open suspicions: 6** (S1, S2, S6, S7, S9, S10).

## 5-Aspect Findings

### Contribution — 3/5

The contribution is a controlled diagnostic audit, not a superior estimator. Elementary error accounting and the support counterexample are appropriately labeled; the symmetry result supplies a useful caution about balanced quadratic benchmarks. However, the permitted Chin/Han notes already describe variance costs of richer adjustment, count/fraction distinctions, and multi-hop failures. Emphasize the **jointly controlled attribution of failure mechanisms**, not discovery of these concerns individually. A capable specialist could derive much of the algebra quickly; novelty sufficiency remains uncertain, not disproved. No missing-SOTA blocker is imposed.

### Clarity — 4/5

The reverse outline is coherent:

- **Introduction:** endpoint target → prior adjustment/exposure limitations → narrow audit question → bounded contributions.
- **Method:** shared error schedule/target → fixed features and contrast → error identity → support obstruction → symmetry.
- **Protocol:** graphs/designs → mechanisms/noise → estimators/ablations → conditional metrics.
- **Results:** degree/size → unnecessary flexibility/two-hop → threshold support → allocation → count/fraction → clustering/covariance → rare tails.

The methods' motivations are present. F7–F9 are inexpensive clarity/mechanical fixes. Related work already explains why ReFeX-LASSO and its bootstrap are not reproduced. The source-access narrative is unusually long but honest; do not replace it with unsupported novelty assurances.

### Results — 3/5

Headline numerical claims are supported and reproducible from the existing records. Trust is reduced by F1 and the subset presentation in F2, not by absence of SOTA superiority. Main displayed regression comparisons are all-valid and do **not** inherit F1's missingness problem.

| Abstract/introduction claim | Evidence checked | Assessment |
|---|---|---|
| 24,000 experiments | 12,000 main + 7,200 size + 4,800 allocation unique assignments | Supported; not 1.68M independent experiments |
| Degree raises risk at fixed size | Regular degree sweep; Fig. 1; RMSE .197 → .777 | Supported within these fixed graphs/design |
| Correct extra features can amplify error | Regular128 Quad RMSE 6.872; mean conditional variance; paired contrasts | Supported; Add→Quad adds interactions as well as curvature |
| Count/fraction matters on heterogeneous graphs | Stanford Add/count bias −.898; Count/count RMSE .033; reverse direction in summaries/Fig. 4 | Supported; Lin↔Count is the cleaner parameterization-only comparison |
| Tiny observed signal residual can hide endpoint effect | Regular128 threshold mean conditional bias −1; Oracle 0/900 Bernoulli availability | Supported; not an identifiable real-data bias diagnostic |
| Balanced curvature can conceal average bias | Proposition 3 and allocation .2/.5/.8 results | Supported with stated symmetry/rank scope |
| Covariance matters with unit marginal variance | Ego coverage .480 versus known-covariance .950; independent covariance check | Supported under fresh Gaussian schedules |
| Clustering is not uniformly beneficial | BA quadratic RMSE .314 → .378, all three seeds | Supported; independent design streams |
| Uncertainty-qualified comparisons | Correct all-valid MCSEs; explicit rare-tail warnings | **Needs repair for failure-conditioned pooling: F1** |

### Testing — 4/5

Controls, feature additions/substitutions, allocation and size sensitivities, different graph classes, failure cases, and public-topology synthetic outcomes fit the diagnostic question. Three fixed graph seeds are not a graph-population study, and the paper says so. Eight supplied tests pass. Independent checking here additionally exercised fractional exposure events distinct from full exposure on an irregular graph, at p=.2/.5/.8.

Optional strengthening without new simulations: display Lin beside Quad for a cleaner curvature-only comparison, and Lin beside Count for a cleaner count/fraction replacement. Do not demand unrelated learned estimators or new literature. F4 is an inexpensive reproducibility guard worth adding.

### Method — 4/5

The linear contrast, shared-schedule target cancellation, support lower bound, conditional MSE identity, and complement proof are internally consistent. Count normalization and normalized nonreturning two-hop endpoints are correct. Covariance orientation is correct even on irregular graphs. Ridge's lack of OLS cancellation and its diagnostic-only residual intervals are disclosed. Oracle truth/variance is used for auditing, not tuning or operational prediction.

**Rank qualification, not a demonstrated defect:** Proposition 3 proves invariance of mathematical full rank. The raw-coordinate eigenvalue cutoff in `weights()` is not generally invariant under the nonorthogonal complement basis transformation. Add is accepted on every reported attempt, and a small exhaustive check passed, so there is no detected impact on the reported cancellation. Add one sentence distinguishing numerical acceptance from exact-rank theory; if future near-cutoff cells support a symmetry claim, test paired acceptance explicitly or use a complement-equivariant parameterization.

## Protocol Audit & Mechanical Scans

### Dataflow reconstructed and independently checked

1. Graphs are generated/loaded, symmetrized/binarized, and reduced to the largest component before degree normalization. Fixed `x` and deterministic BFS blocks use graph information only.
2. Each `(suite, graph index, design index, rep)` seeds one assignment/noise stream. Designs/suites have distinct streams; mechanisms and methods share assignment and underlying Gaussian draws **within** an experiment.
3. `features()` computes `s`, nonreturning `t`, normalized count, threshold, and interactions. Cached global endpoint features generate each method's contrast and analytic mechanism truths. All truths are 1 or 2 to floating-point tolerance.
4. Fixed-feature regressions fit the observed mixed-assignment outcomes, then transport to the two global endpoints. No train/test split is required for this explicitly parametric simulation audit; an observed-fit diagnostic is not held-out endpoint validation. No outcome-based feature selection or truth-based tuning was found.
5. `M` is the known noiseless simulation mean; `Y=M+noise`. `b=w'M−T` and `v` are oracle audit quantities. They are not inferred from training residuals or fed back into model selection.
6. Each estimator retains its own availability. Paired losses use intersection keys `(graph_seed, rep)` within a design. Failures are neither redrawn nor zero-filled. HT numerical underflow is separately labeled.
7. Analysis aggregates valid records and generates tables/macros/plot data. Missingness changes the accepted graph mixture. This final step contains F1/F3/F5.

**Executed checks:**

- `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python -m pytest -q -p no:cacheprovider /work/test_gate.py`: **8 passed**.
- Independently scanned all raw suites: **840,000 / 504,000 / 336,000** records; **12,000 / 7,200 / 4,800** assignments; exactly **70 records per assignment**; no duplicate full method/mechanism keys; successful estimates/errors/biases/variances finite.
- Recomputed stored bias, MSE, their current MCSE formulas, and decomposition mean/MCSE across all 2,520 aggregate cells with at least two valid records where applicable. Differences are floating-point scale (maximum MSE-MCSE discrepancy approximately `4.55e-13`). This verifies implementation consistency, **not** the adequacy of the MCSE estimand.
- Replayed five existing main assignments: regular128/11/Bernoulli/0, regular32/23/cluster/10, ego/0/Bernoulli/0, Stanford/0/Bernoulli/0, BA/37/cluster/299. All 70 statuses match for each; maximum numerical discrepancy across estimates, errors, biases, variances, leverage, SEs and signal fit is approximately `1.78e-15`. No suite was rerun or overwritten.
- Independently enumerated exposure probabilities on an 8-node irregular graph under Bernoulli and four-block assignments at p=.2/.5/.8: maximum discrepancy `6.67e-16`. Direct dense covariance agrees with sparse `exact_variances`; marginal variances differ from 1 by at most `2.23e-16`. Two-hop own-treatment feedback is numerical zero; endpoints reproduce `[1,2,2,2,2,2,2]`.
- Exhaustive small-graph Add complement check: 254 accepted assignments, zero acceptance mismatches, maximum odd-weight discrepancy about `4.09e-10`. This is numerical evidence, not a general numerical-rank theorem.
- Dedicated decomposition check: **16/16** within 1.96 MCSE; maximum absolute standardized gap **1.79904**. No claim that every other cell passes is made.

### Prioritized fixable findings

#### F1 — High severity; high confidence; **blocking for the current uncertainty claim**

**Location:** `analyze.py:27–39` (`strat_se`); §4 metrics; Appendix B MCSE paragraph; released `summary.csv` failure-conditioned cells.

**Evidence:** The pooled estimate is a ratio, `theta_hat = sum(V H)/sum(V)`, where `V` indicates a valid output and `H` is error or squared error. Its stated target is the fixed equal-attempt graph mixture **conditioned on validity**. The current SE treats realized valid-count graph weights as fixed and includes only within-valid-stratum outcome variation. It omits accepted-count/weight variation relevant to repeat-MC uncertainty around that fixed target. The appendix acknowledges the omission, but the supplied columns remain generic `bias_mcse`, `mse_mcse`, `rmse_mcse`.

A raw attempt-level, fixed-stratum ratio influence calculation gives, for **main / WS32 / Bernoulli / Hajek80 / correlated**, 11 valid out of 900:

| MCSE | Stored | Attempt-level ratio calculation |
|---|---:|---:|
| Bias | .319320 | .462416 |
| MSE | .453964 | .826508 |

The MSE difference is a factor **1.82**. This is material in released sparse cells, although it does not change all-valid headline regressions. The alternative calculation is itself only a local asymptotic diagnostic with 11 successes, not a precision certificate.

**Fix:** For each metric use attempted records and a stratified ratio variance, e.g. `U=V*(H−theta_hat)` and `SE²=sum_j R_j * sample_var_j(U) / N_valid²`; then apply the RMSE delta transform when justified. Alternatively, suppress pooled precision for sparse/failure-prone cells and explicitly label any retained SE as conditional on realized accepted counts and targeting that count-specific mixture. Preserve per-seed availability/estimates. Do not manufacture precision when only one success occurs or when rare tails remain unseen. A caveat alone should not leave misleading general-purpose MCSE columns in the released reporting contract.

#### F2 — Medium severity; high confidence

**Location:** Appendix B Figure 4; `plot_results.py:64–79`.

**Evidence:** WS/threshold Oracle heatmap RMSE **.850737** uses **181/900** valid attempts, whereas Add's **1.052445** uses **900/900**. The heatmap presents them in the same risk matrix without in-cell availability. Its CSV disclaimer and “no significance rankings” sentence do not expose that these are risks on differently selected subsets.

**Fix:** Annotate `181/900`, mark/hatch incomplete cells, and say explicitly that method-conditional cells are not common-subset comparisons. Optionally show a separate common-valid comparison; do not impute loss zero for failures. No new experiments needed.

#### F3 — Medium severity; high confidence

**Location:** `artifacts/analysis_protocol.md`, bullets 4–6; Appendix B; `analyze.py`; methodology description in `results_audit.md`.

**Evidence:** The frozen protocol calls pooled conditional results an “equal-weight mixture” and uses pooled `SD/sqrt(N)` wording. Current code uses valid-count weighting and stratified MCSEs; the manuscript correctly explains accepted-weight reweighting. The protocol is therefore not an accurate unqualified description of the released estimator. This is a documentation/version discrepancy, not evidence of selective reporting.

**Fix:** Preserve the frozen original and append a dated analysis amendment that identifies the estimand, strata, accepted-weight behavior, F1 repair, and affected outputs. Reconcile audit descriptions. If chronology is not documented, qualify “prespecified” to the verified design choices rather than implying every final analysis formula was frozen unchanged.

#### F4 — Medium severity; high confidence

**Location:** Appendix B, “All three suites validate ... expected assignment counts”; `analyze.py:49–59`.

**Evidence:** Analyzer checks runtime-file existence, finite successful values and duplicate keys, but **does not assert expected assignment counts, exact replication coverage, 70 method/mechanism records per attempt, or an allowed-status set**. `len(d)//70` merely reports an inferred count. A stale runtime marker plus a truncated but unique file could pass. My independent checks show that the **current** files have all the expected records, so no current truncation is alleged.

**Fix:** Add manifest/config-derived assertions and a completeness check before writing summaries, or delete the unsupported claim that the delivered analyzer already enforces them. A small truncation/unknown-status regression test would make this guarantee meaningful.

#### F5 — Low severity; high confidence

**Location:** `analyze.py:65–73`; `paired.csv`; §5.1 paired contrast.

**Evidence:** Paired loss differences are correctly formed on common records, but their SE uses pooled `sd(delta)/sqrt(N)`, unlike the fixed-graph stratification used elsewhere. For regular128/linear Quad−Add: stored **2.2670533**, stratified **2.2689685**; regular32: **.1023680** versus **.1023698**. No substantive headline change is implied.

**Fix:** Use the same fixed-stratum convention for paired contrasts; with missing common-valid counts use the appropriate ratio treatment or qualify the conditional target. Do not describe this small all-valid discrepancy as invalid pairing or a reversed result.

#### F6 — Low severity; high confidence

**Location:** §4 “Intervals are not implemented for DIM or exposure estimators”; `gate.py:143–146`; `summary.csv`.

**Evidence:** The shared append function emits `oracle_cover` for DIM, Hajek80 and HTfull, and analysis publishes `known_coverage`. For main/regular32/Bernoulli/linear, denominators are **900, 11, 900**, respectively, despite nominal residual-interval denominators being zero. The manuscript sentence is too broad for the actual output schema.

**Fix:** Say “residual-variance intervals are not implemented” and identify generic known-noise diagnostics, or emit NA for excluded methods. Neither option makes a biased exposure contrast a valid GATE interval. Keep zero-variance HT degeneracy distinct from the positive-variance regression coverage claim.

#### F7 — Low severity; high confidence

**Location:** Table 2 caption; generated `support_table.tex` and its writer at `analyze.py:95–100`.

**Evidence:** Caption says availability is “valid/attempted,” but cells contain rounded proportions (.233/.057), not denominators (210/900, 51/900). Also `H'ajek` renders an apostrophe rather than the Hájek accent. Prose elsewhere supplies some, but not every, denominator.

**Fix:** Prefer explicit counts plus proportions; otherwise label the columns “availability proportion.” Generate `H\'ajek`/Hájek correctly. Keep the correctly distinguished empirical bias and noise-integrated conditional bias labels.

#### F8 — Low severity; high confidence

**Location:** Figures 1–2, Figure 4 and Table 3 references; `plot_results.py`.

**Evidence:** `fig:heatmap` and `tab:graphs` have no direct `\ref` in the source (the graph-statistics appendix has only a section-level pointer). Figure 1's caption omits **Bernoulli(.5)**, although that is its data filter. Figure 2's axis “Absolute conditional GATE bias (mean)” is ambiguous; code plots **`|mean(b)|`**, not **`mean(|b|)`**. Figure 1's legend also obscures the middle TwoHop point. All four PNGs otherwise have legible labels and adequate color/shape distinctions.

**Fix:** Add direct references, design qualification, the explicit ordinate `|E[b(Z)]|`, and move the legend. No generic “best method” bolding is needed for these deliberately non-ranking tables; an RMSE-down cue is optional.

#### F9 — Low severity; high confidence

**Location:** §4 covariate construction; Appendix B; `gate.py:52–56`.

**Evidence:** Prose calls the component “log degree”; implementation uses **`log1p(d)`**, centers/scales it when nonconstant, adds `.5*N(0,1)`, then standardizes again. This is a small but real reproducibility difference, not a suspected explanation of the substantive results.

**Fix:** Write the exact transformation, including the constant-degree branch, rather than a shorthand that implies `log(d)`.

**Distinct protocol/mechanical findings: 9** (F1–F9). The exact/numerical rank qualification is recorded separately as an unproved extension, not counted as a demonstrated implementation failure.

### Mechanical and assumption checks cleared or bounded

- **Promise–delivery:** decomposition, support obstruction, symmetry, and controlled diagnostic experiments are delivered in §§3–5 and echoed in §6. The conclusion could explicitly repeat the decomposition/symmetry contributions, but they do not disappear substantively.
- **Comparisons:** no method called directly reproduced or uniformly superior is silently omitted. ReFeX-LASSO, nonlinear procedures, optimized designs and related inference are explicitly excluded. No unjustified SOTA requirement.
- **Numbers:** generated headline macros, allocation biases, Table 1, availability examples, BA seed-direction claim, ego Wilson intervals and all 16 decomposition checks agree with existing outputs. The regular128 threshold empirical error bias differs from conditional bias because noise is resampled; it is not an arithmetic inconsistency.
- **Heavy tails:** all-zero HT estimates with empirical bias −2 and zero empirical bias MCSE do not contradict exact one-hop HT unbiasedness. Main text explicitly warns against treating them as true bias/precision evidence or risk rankings. Stanford zero numerical propensities are labeled unavailable, not lack of mathematical positivity. F1's ratio correction does **not** repair unseen tails.
- **Assumptions:** static known graph, no isolates, positive two-hop denominators, outcome-independent fixed features, assignment/noise independence, positive rank acceptance where conditional statements are used, Gaussian coverage benchmark, and infeasible oracle information are stated or checked. No new deployment-valid covariance estimator is claimed. Wilson fixed-mixture approximation is disclosed.
- **Citations/markers:** all eight citation keys resolve, no duplicate labels or undefined references, and no TODO/FIXME/TBD markers in the delivered paper/checklist/generated TeX. Only the two missing direct figure/table references in F8 were found. Bibliographic metadata were not independently expanded; the permitted notes do not independently certify the Aronow journal year, so retain the explicit consulted-preprint identification rather than overclaiming verification.
- **Venue/layout:** official local style is byte-identical to the archived official 2026 style; anonymous `[main]` mode is used. **Eight content pages; references start page 9; 20 PDF pages total** including appendix/checklist. No overfull-box or undefined-reference warnings; only underfull warnings. Anonymous affiliation/address/email placeholders come from anonymous style behavior, not an identity leak. Official checklist is present. No online venue-policy recertification was attempted.
- **Source/rights boundary:** provenance notes support distinguishing SNAP combined ego-Facebook from Stanford3's Facebook100 largest component. SNAP licensing and full requested paper-level attribution remain explicitly unresolved; an offline reviewer cannot clear them. Treat these as a **human pre-submission rights/accountability gate**, not evidence of a scientific dataflow failure. Do not solve them by visiting unauthorized sources.

## Blocking Issues

**B1 — Repair or suppress misleading failure-conditioned pooled MCSEs (F1).** Before claiming all released comparisons are uncertainty-qualified, align the MCSEs and labels with the intended accepted-mixture estimand. Acceptance criterion: an attempted-record test reproduces a defensible ratio/stratified calculation or the problematic pooled precision columns are explicitly unavailable/conditional-on-counts, with the amendment documented. Existing all-valid headline results can remain.

**Blocking count: 1.** F2–F9 should be addressed before submission but do not currently overturn the main results. Novelty sufficiency and uncertain data rights remain external human sign-off questions, not resolved by this review and not counted as discovered scientific blockers.

## Prebuttal Notes

- **“This is familiar OLS.”** Agree that the algebra is standard. Defend the controlled joint audit, measured contrast geometry, support/availability separation and balanced-curvature trap; do not imply an exhaustive novelty search.
- **“Missing modern estimator baselines.”** The question diagnoses fixed-feature endpoint transport, not SOTA superiority. Existing exclusions are explicit. Show Lin↔Quad and Lin↔Count from existing records when a cleaner ablation is needed.
- **“Your error bars are wrong.”** Do not defend F1 by pointing only to a limitations paragraph. Repair/suppress those MCSEs and show that all-valid headline estimates are unaffected. Explain fixed-graph versus graph-population uncertainty.
- **“Oracle succeeds only on easy assignments.”** Acknowledge it; show attempted/valid counts on the heatmap and common-valid paired contrasts. Never present a selected-subset RMSE as unconditional reliability.
- **“Quadratic misspecification has no bias.”** Under the stated complement law its average contrast bias cancels; conditional bias variance, asymmetric allocation and other nonlinearities remain distinct.
- **“Known covariance makes everything valid.”** Only centered Gaussian contrasts with positive variance obtain the stated conditional nominal coverage. It cannot remove endpoint bias, and it is an oracle benchmark here.
- **“HT appears biased.”** The finite simulation missed compensating rare events; empirical zero SE is not evidence of precision. No true-risk ranking is claimed.

**Counterintuitive actions:** delete or rewrite the unsupported assertion that expected-count validation is already enforced (F4); promote the accepted-subset issue into Figure 4 itself (F2); narrow novelty to the controlled synthesis. Trust score: comparison fairness **2/2**, reproducibility **1/2**, limitations **2/2**, failure transparency **2/2**, statistics **1/2** = **8/10**. This is not permission to ignore B1.

**Review provenance:** draft SHA-256 `24b83305b597b20c7c75c47d9a0d2194801699af16be979b909b1182feb87538`; PDF SHA-256 `90ab9582357bc72fe4f3c2710c160db9f886038943b029a1f171e1803bd902e6`. No manuscript or analysis outputs were regenerated by this review.
