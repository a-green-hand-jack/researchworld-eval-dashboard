# Self-Review

## Verdict

**Needs-work; one blocking presentation issue.** The manuscript is a credible, unusually transparent **descriptive standard-method study**, not a confirmatory success paper or algorithmic contribution. Its central numerical statements are supported by the supplied artifacts. Original cohort defects are not silently transferred to the later sensitivities. This is a trust assessment, **not a prediction or promise of acceptance**.

**Draft reviewed:** `/work/paper/main.tex` and `/work/paper.pdf` (byte-identical to `/work/paper/main.pdf`). **Review output:** `/work/paper/self_review.md`.

**Concise must-fix / priority list for the main agent:**
1. **B1 — Make Figures 1–2 readable at final PDF size and distinguish curves without color alone.** Their legends are approximately 2.75 and 3.14 pt. Preserve the data; change presentation, not experiments.
2. **Minor factual fix:** Appendix D.2's “approximately 377 MB compressed” should be **377 MiB**, or approximately **396 MB**. The archive is 395,746,943 bytes.
3. **Clarify the correlation selector:** define `corr` as the fitted PSD-repaired/shrunk unit-diagonal matrix actually supplied to the selector, not an unspecified empirical Pearson correlation.
4. **Recommended substantive clarification:** quantify the corrected OpenLLM giant component beside the uncertainty caveat: 2,890 rows, including 91.4% of seed-71 test rows. Do not present the narrow conditional interval as a population/family-generalization guarantee.
5. **Editorial priority:** sharpen the one scientific takeaway beyond the audit inventory; retain the failed-gate, dependence, convergence, and random-bank caveats. Add explicit appendix table callouts.

**Reject-first simulation:** A hostile reviewer could reject because the paper applies familiar estimators to highly coverage-selected panels, provides no demonstrated new algorithm or broad generalization result, and retains incomplete baseline optimization and planned comparisons. The repaired OpenLLM experiment is dominated structurally by one connected component and is reused-data evidence. The main plots are too small to inspect comfortably. The audit is valuable, but transparency alone does not establish sufficient scientific contribution for a selective venue.

**Trust score: 8/10:** baseline fairness 1/2; reproducibility detail 2/2; honest limitations 2/2; failure transparency 2/2; statistical soundness 1/2. Numeric fidelity is high; broad inferential confidence is not. No fresh confirmation is required to permit the descriptive reporting already used here.

### Review execution and limits

Pass 1 read all 537 TeX lines and all 26 PDF pages before opening the checklist/script; suspicions were recorded before Pass 2. Then read `/skills/paper-review/SKILL.md`, its counterintuitive protocol and script. No code-interpreter/task-dispatch interface is exposed, so `await fiveAspectReview(draftText)` could not run. All five aspects were completed using the expressly permitted **sequential fallback**; none is missing. Pass 3 used local shell/Python scans and computations. No web access, topical literature search, new fitting, retuning, experimental rerun, or result modification occurred.

Read the rules, completed checklist, original audit, execution log, sensitivity protocol, runner/model/sensitivity/analysis/diagnostics code, local reading notes, bibliography, and requested CSVs. Independently checked arithmetic against stored losses; regenerated core bootstrap summaries in memory using the existing analysis function, without writing results. This checks implementation consistency, not bootstrap coverage. The previous audit's exhaustive prediction-array reconstruction was inspected, not repeated or represented as new work here. No manuscript edits or compilation were performed; the existing PDF and build log were inspected.

Inspection fingerprints: TeX SHA256 `a88ffa5f7b595d26cfae369bbba06c6ae32f9e8771e383de6016f9d9d40392c8`; PDF SHA256 `5a5b7e455155d4d18474c93d47ba0aaebac7f55463411847c687d804053e8aae`.

## Pass-1 Suspicions

The following were raised independently before the checklist. “Resolved” means the suspicion was settled or explicitly bounded by the later evidence, not that the underlying experiment became confirmatory. Four remain open.

| ID / location | Suspicion and confidence | Evidence that would settle it | Later disposition |
|---|---|---|---|
| S1 — Introduction contributions; Discussion | The paper may offer an audit inventory rather than sufficient new scientific knowledge. **Medium-high; judgment.** | A crisp, evidence-linked statement of what readers learn beyond standard Gaussian prediction and familiar coverage/dependence warnings. | **Open.** Modest descriptive contribution is real; venue sufficiency remains uncertain. Do not manufacture algorithm novelty. |
| S2 — Abstract; Tables 2–3; §3.4 | Reductions/intervals might conceal wrong weighting, narrow support, or omitted random-bank uncertainty. **Medium.** | Recompute equal-split core estimates and paired intervals; inspect supports and bank sensitivity. | **Resolved as a numeric/support suspicion.** All checked estimates agree; narrow supports and conditional uncertainty are prominently disclosed. |
| S3 — §3.3 corrected OpenLLM | Zero recorded-key overlap might only be asserted, or original alias findings might still apply. **Medium.** | Reconstruct retained metadata and all train/validation/test key intersections for every sensitivity seed. | **Resolved.** All corrected SHA/Base Model/component intersections are zero. Original overlaps remain confined to original evidence. |
| S4 — §4.1 native objective | Native inference could optimize unavailable coordinates or use undisclosed target information. **Medium-high.** | Trace `evaluate`, `path`, masks, and scored supports. | **Resolved as a reporting concern.** Full-panel objective mismatch is real and explicitly stated; no current-code unacquired target-value input was found. |
| S5 — §4.1; Appendix C | Capped factor fits and missing feasible baselines could exaggerate comparative conclusions. **High.** | Selected-fit logs, omitted-analysis ledger, and exact strength of claims. | **Resolved by bounded claims, not experimental repair.** Limits are admitted; no claim against a converged optimum is made. |
| S6 — Appendix D.2 | Very short resource totals might omit most claimed work. **Medium.** | Sum all stored reports and check their timing boundaries. | **Resolved for the stated timing scope.** 48 reports sum to 516.7044 s; exclusions are explicit. Separate MB/MiB slip found below. |
| S7 — PDF p.1 | “Affiliation / Address / email” might be unfinished author placeholders. **High initially.** | Compare rendered anonymous block with unmodified official style. | **Resolved.** The official anonymous style hardcodes these strings at lines 336–341. They are not unfilled author data. Do not reveal identities or change mandated style to remove them. |
| S8 — PDF pp.7,12–14 | Small labels, crowded uncertainty table, and color-only distinctions may hide results. **High.** | Inspect final-size renders and compute embedded-font scaling. | **Open; B1 confirmed.** Table 4 is also awkwardly wrapped, though readable. |
| S9 — Related work; source appendix | Five selected-section readings may not support all literature statements. **Medium.** | Match citations and descriptions to the recorded inspected sections. | **Resolved within the restricted scope.** Five keys match five read sources; notes support the specific descriptions. No exhaustive novelty or full-paper-reading claim is made. |
| S10 — Appendix D.1 commands | Reproduction sequence may omit dependencies or rely on stale cache. **Medium.** | Inspect command entry points, dependencies and cache behavior; distinguish documented commands from a full clean rerun. | **Resolved to stated scope.** Manuscript includes diagnostics/MC/reproduction steps and cache warning; only the recorded single-run exact reproduction is established, not a new clean end-to-end rerun. |
| S11 — §3.4; connected OpenLLM results | Narrow component-bootstrap intervals may obscure dominance by one enormous component. **Medium-high.** | Component sizes and split placement; explicit interpretation of conditional resampling. | **Open as an inferential concern.** Code matches the stated bootstrap; reliable population coverage is not established. Existing imbalance caveat should be quantified further. |
| S12 — Appendix D; checklist | Complete resources/release/user deliverables may be missing despite a complete PDF. **High.** | Compare request with actual packaging and recorded timing/memory/license evidence. | **Open.** Full-project resource accounting is unavailable; final bundle/report packaging remains the main agent's task. Honest No/NA answers do not fill missing records. |

## 5-Aspect Findings

### Contribution — 3/5

The contribution is an auditable descriptive comparison and clarification of evaluation estimands, not a novel selector or Gaussian theorem. That framing is consistent in abstract, introduction, theory, discussion, and conclusion. A capable researcher could derive the Gaussian identities quickly; the draft correctly declines novelty, submodularity, greedy-optimality, universal-budget, and full-suite claims.

**Major scientific risk:** the genuinely new knowledge needs a sharper synthesis. A defensible emphasis is: selection ranking changes across distinct support-conditioned settings; simple audit-aware comparators can beat residual-trace selection; lower changing-target error is not fixed-target transfer. The first two are descriptive observations, not controlled causal conclusions. Make these lessons easier to find, without promoting the sensitivities to confirmation. No unsupported abstract/introduction claim was found that should be deleted merely to satisfy the counterintuitive exercise.

### Clarity — 3/5

Definitions of budgets, supports, loss units, aggregation, and descriptive status are unusually explicit. The prose is nevertheless repetitive and provenance-heavy. The abstract contains many qualifications before a reader has a simple mental model of candidates, acquired anchors, and never-acquired audits.

**Reverse outline:** Introduction proceeds motivation → target-removal confound → failed-gate/dependence restrictions → descriptive contributions; this is coherent. Method proceeds covariance/inductive prediction → factors/tuning → selector families → native-support mismatch → population interpretation; also coherent, but the dense selector paragraph should be separated into predictor-controlled comparisons versus complete selector/predictor configurations. Results proceed original comparisons → wider support → repaired dependence → budgets → deletion → contextual cohorts → numerical checks → random-bank uncertainty. The last four topics feel like an audit miscellany; group them explicitly as diagnostics and limitations.

Minor issues: define the fitted `corr` matrix precisely; add direct references to Tables 4–9, which currently have no exact table-number callouts in TeX. Local paths are useful only if the accompanying package contains them. Avoid padding the paper with stronger public-release promises while packaging is pending.

### Results — 4/5

**Strong numeric fidelity:** all 846 summary point-estimate rows reproduce from the stored loss export to floating-point precision. That export agrees with all 48 constituent loss CSVs across 1,001,850 records. All 33 compact main-table estimates match. Core bootstrap outputs for all four primary reported conditions reproduce to below `5e-16` using the existing analysis implementation. This is not an independent statistical coverage validation.

The paper gives absolute errors and contrasts, not just relative percentages; retains negative D-optimal/deletion results; acknowledges factor nonconvergence; and does not assert application adequacy, measured benchmark-runtime savings, or significance against the strongest comparator.

**Blocking presentation issue B1:** at the official 5.5-inch text width, the 12-inch Figure 1 shrinks 9-pt plotting text to about **4.13 pt**, and its 6-pt legend to **2.75 pt**. Figure 2 shrinks its 10.5-inch canvas to approximately **4.71-pt** ordinary text and **3.14-pt** legend. Both are visibly small in PDF p.7. Same-circle, solid-line red/green curves need distinct markers/dashes. Vector output does not cure undersized typography. Figure 3 is larger relative to its original canvas and less problematic, but should also receive redundant curve encodings. Table 4's interval wrapping and stretched justification produce many underfull-box warnings; improve its layout without shrinking its text.

### Testing — 3/5

Eleven methods, five preset holdouts, distinct native/wide/connected conditions, paired support, matched random/factor anchors, selected-budget records, three-seed deletion stresses, and implementation checks support the narrow descriptive comparisons. Item-level compression papers have incompatible inputs; their absence as numerical baselines is explicitly explained. No undisclosed missing “claimed SOTA” comparison was found.

**Major residual limitations, already disclosed:** complete-training-row covariance was feasible but omitted; additional planned diagnostics and standardized-variance reference were omitted; selected factor fits are capped; no availability/category/chronological/lineage test or predictive-interval calibration was completed. These prevent claims of comprehensive evaluation or optimal low-rank benchmarking. They do **not** require fresh confirmation to report existing descriptive numbers. Do not retune retrospectively for this review.

### Method — 4/5

Current data flow supports training-only standardization/covariance/factors, validation-only hyperparameters and global budget selection, and inductive prediction from one row's acquired scores. Fixed audits are never acquired; random paths average losses rather than predictions. Gaussian assumptions and boundaries are explicit; the displayed strict reversal and suppressor arithmetic are consistent. No algorithm novelty or real-data calibration guarantee is asserted.

Known defects remain defects of the evidence: original revision overlap, missing historical sealing, and native objective/support mismatch. They are not erased by favorable metrics. The manuscript appropriately restricts the corresponding interpretations rather than disguising them as successful tests. Real-world availability, informative reporting, mixed task metrics, imperfect ancestry metadata, and uniform label-count costs remain important deployment boundaries.

## Protocol Audit & Mechanical Scans

### Reconstructed data flow

Pinned source tables → metadata/mask canonicalization → original organization/row partitions and permanent candidate/audit roles → training-only eligibility/panel selection → fixed mask-defined validation/test eligibility → training preprocessing and estimators → validation random-path tuning → validation-only one-SE budget heuristic → frozen-budget/per-budget fixed-audit test losses → equal-budget-within-split, equal-split summaries → paired cross-appearance cluster bootstrap. Deletion changes training labels only and repeats training preprocessing/tuning. Wide MTEB changes panel/eligibility and uses native validation. Connected OpenLLM changes grouping and clusters by persistent components. Sensitivities follow the original audit and use reused data.

### Nine audit/scanning findings and dispositions

1. **A1 — Original evidence restrictions, correctly reported; high confidence.** Only seed 37 passes the original MTEB local gate; study gate is 1/5 versus required 3/5. Original panels are 8 candidates/4 audits, with union 15 panel tasks/6 audit tasks. Original OpenLLM train/test shared SHA counts are 5,5,4,5,6. No manuscript fix needed to these disclosures; never generalize them to every sensitivity.
2. **A2 — Native objective mismatch and historical sealing, correctly reported; high confidence.** `src/models.py:57` optimizes all unacquired panel coordinates; `src/run.py:74–75` scores observed unacquired coordinates. Original native MTEB exercises incomplete panels in 84/210 appearances. Schema-head score exposure and incomplete lock hashes are admitted. These do not invalidate the implemented policy's paired fixed-audit loss, but do block aligned-native-objective or exposure-free historical claims.
3. **A3 — Baseline completeness, major experimental boundary; high confidence.** Selected original seeds 11/37 have 0/3 convergence-flagged factor starts; seed 53 has 2/3. Wide seeds 11/37/53 have 1/3. Feasible complete-row covariance and other planned checks are absent. The draft already labels these correctly; preserve the limitation and do not claim a converged optimum or completed plan.
4. **A4 — Giant-component uncertainty, major interpretive concern; medium-high confidence.** Corrected OpenLLM has a 2,890-row component (64.3% of all 4,497 rows). In seed 71 it accounts for 2,890/3,161 = 91.4% of test rows. Conditional component resampling gives a highly influential cluster large weight variation; a randomly resampled cluster can also be omitted. The code implements the stated conditional procedure, but reproducible percentiles are not proof of inferential coverage. Add component size/context near the repaired result. No new confidence procedure or fresh test is demanded here.
5. **A5 — Final-size graphics, blocking presentation defect; high confidence.** See B1 and calculated font sizes above. Captions and vector resolution are adequate; typography and color-only distinctions are not.
6. **A6 — Fitted-correlation definition, minor reproducibility ambiguity; high confidence.** §4.1 writes `corr(t,a)^2`. `src/run.py:36–44` passes the selected shrunk, PSD-repaired matrix to the correlation selector; `src/models.py:52–53` squares those entries. Define this explicitly. It need not equal separately computed pairwise Pearson correlation on incomplete data. No numerical change is requested.
7. **A7 — Archive-size units, minor factual error; high confidence.** Appendix D.2's approximately 377 MB is 377.41 **MiB**, or 395.75 decimal MB. Source SHA256 matches; only the unit/rounded decimal number needs correction.
8. **A8 — Appendix float callouts, minor mechanical issue; high confidence.** Exact references to `tab:full`, `tab:allcontrasts`, `tab:splits`, `tab:sensitivity`, `tab:synthetic`, and `tab:map` are absent. Section references provide partial navigation, but add table callouts. Table 4 is densely wrapped; consider left-aligned cells and shorter interval formatting. Do not bold a purported universal winner across distinct estimands.
9. **A9 — Deliverable completeness, open scope/accounting issue; high confidence.** Full-project compute, all per-run memory peaks, agent-model/API accounting, and historical storage peak are not recorded. Checklist Nos/NA are honest. Final anonymized code/report packaging is pending and belongs to the main agent; it is not counted as a scientific/manuscript blocker in this review. Do not invent unavailable accounting or infer a licensing violation from an unspecified license.

### Original versus sensitivity independence audit

Re-selected the local parquet metadata using the implemented precision/fullname rule, aligned it to manifest IDs, removed blank keys, and compared stripped/lowercased keys. Pair order below is **train–validation / train–test / validation–test**.

| Evidence version | SHA overlap, seeds 11/23/37/53/71 | Base Model overlap | Component/group overlap |
|---|---|---|---|
| Original OpenLLM organization | `1/5/3`, `0/5/2`, `3/4/3`, `5/5/1`, `0/6/0` | Nonzero; e.g. train–test counts 53,47,40,38,39 | Original organization names are separated, but this does not separate aliases |
| Corrected alias-connected OpenLLM | **`0/0/0` in every seed** | **`0/0/0` in every seed** | **`0/0/0` in every seed** |

Thus the repaired zero-recorded-key claim is **actually supported**, not merely a prospective assertion. It does not prove all ancestry separation. The original audit predates these repaired cohorts and must not be applied wholesale to them.

### Claim-to-artifact ledger

| Claim / location | Evidence and check | Assessment |
|---|---|---|
| Abstract and §3: source breadth | `mteb.csv`: 279×62, 9,882 observed cells; 57.12799% rounds to 57.13%. `openllm.csv`: 4,497×6 complete, from 4,576 raw records. | Supported; ingestion breadth is not target breadth. |
| Table 1 / failed gate | `cohort_counts.csv`, original manifests: every row/group count matches; only seed 37 passes. | Supported; all five retained descriptively. |
| Original MTEB headline | `summary.csv`, organization/base/dense/core: residual 0.357226 vs random 0.420811; difference −0.063585, interval [−0.092525,−0.040874]; reduction 15.1100%, [9.7206,20.5783]%. | Supported at printed rounding; conditional only. |
| Wide MTEB headline/comparators | organization/wide_native/native/core: 0.239021 vs 0.296316; difference −0.057295; 19.3358%, [14.2898,24.8109]%. Audit/correlation/filled point losses 0.228496/0.223303/0.216915. | Supported; not a controlled improvement over original support. |
| Original OpenLLM | organization/base/dense/core: 0.469092 vs 0.530080; difference −0.060988; reduction 11.5054%, [9.5793,13.7228]%. | Numerically supported; original independence claim quarantined. |
| Corrected OpenLLM | organization/alias_connected/dense/core: 0.428561 vs 0.499632; difference −0.071071; 14.2246%, [11.6399,16.0655]%; D-opt factors 0.649826. | Supported descriptive repaired analysis, not untouched confirmation. |
| Tables 2,4,5; all methods | 33 compact cells checked; all four 11-method core bootstrap outputs reproduce in memory; generated tables match their generating definitions. | Supported. No unique winning method follows. |
| Table 6 / seed direction | `split_results.csv`: original residual loss below random in each of five seeds; other printed split values agree. | Supported; repeated holdouts, not independent folds. |
| Wide support and Table 7 | `sensitivity_cohorts.csv` and manifests: 49 candidates/12 audits; observed row audits 4–12; tests 47,44,47,43,46. Corrected OpenLLM tests 614,423,505,603,3161; seed-71 test fraction 70.2913%. | Supported; neither full62 ground truth nor balanced splits. |
| Native/random-row context | Summary: original native MTEB residual/random 0.302602/0.347936; random-row dense rounds to 0.313/0.437. | Supported; distinct selected supports, not replications or causal shift contrast. |
| Selected budgets, §5.2 | `validation_budgets.csv`: residual (2,2,2,1,1), random (4,4,6,2,2), audit (2,4,4,1,1), correlation (6,2,4,1,4). Residual/random dense losses match all printed per-seed numbers. | Supported; selected-budget native joins are not fabricated. |
| Training deletion | Summary, propensity_0.5: residual/random raw RMSE 0.107606/0.105964; NMSE 1.152477/1.136884. MNAR_0.5 no-shrink RMSE 0.138609. | Supported reversal. Raw units mix metrics; stresses cover three seeds/six methods. |
| Synthetic identity and trace caveat | `synthetic_identity.csv`: all five printed rows match; maximum discrepancy/MC-SE 1.27263. `risk_calibration.csv`: seed11 k2 trace/error .288395/.400433; seed37 .323178/.218251. | Supports implementation check, not predictive calibration. |
| Random-bank uncertainty | `random_bank_mc.csv`: original organization relative MC-SE ranges 1.2089–2.7279% MTEB, 1.5718–2.3708% OpenLLM. Second-bank ranges round to −1.7/+4.5%, −5.6/+6.5%, −2.9/+2.7%, −4.1/+2.5%. | Supported. Original-bank conditional intervals omit this source of uncertainty. |
| Resources, Appendix D.2 | `run_resources.csv`: 20 base +18 stress +10 sensitivity reports; sums 266.1029+4.8974+245.7041 =516.7044 s. Printed timing ranges agree. Reproduction JSON records 3,520 exact CSV records, 3.514 s wall, 5.273 s user, .115 s system, 157,672 KiB RSS. | Supported within declared scope; not total-project compute or label-acquisition cost. |
| Source/format provenance | Recomputed raw MTEB/parquet/official-ZIP SHA256 values match manuscript. Package pins match `requirements.txt`; environment/hardware/storage records match quoted snapshots. | Supported as local records, not historical peak or prospective registration evidence. |
| Related-work descriptions and citations | Five cited keys exactly equal five bib entries; descriptions match `literature/reading_notes.md` inspected-section scopes. | Supported bounded literature discussion; no new literature or exhaustive novelty verification. |

### Submission/style/checklist scans

- **Pagination verified:** main text pp.1–8; references p.9; appendices pp.10–19; checklist pp.20–26. Thus **8 content pages, 26 total**, within the locally preserved nine-content-page rule. PDF is 364,128 bytes, below 50 MB.
- The used official style is byte-identical to the preserved original; no `final`/`preprint`, margin reduction, identifying acknowledgment, or unmasked author information was found. The template's “Submitted to…” footer is automatic and immediately qualified by the draft notice. The recorded conference deadline has passed; formatting is not evidence of current submission eligibility.
- All **16 official questions and 16 guideline blocks are unchanged** after whitespace normalization; each answer and justification is filled. Nos for open access, compute accounting and existing-asset licensing, and NA for unreviewed ethics code, are honest and allowed by the preserved checklist instructions. Do not demand fabricated Yes answers.
- No TODO/FIXME/TBD/XXX markers in main/checklist/bib/generated table inputs; no missing citation keys, duplicate labels, unresolved references, missing figure files, or overfull boxes. Underfull warnings are present, particularly in Table 4 and long path/URL material. Template source examples are not manuscript placeholders.
- All three figures are called out, vector PDF assets exist, table captions are above booktabs tables, and there are no vertical table rules. Main NMSE direction is explicit. Lack of bolded “best” cells is not a validity defect for these non-superiority, multi-estimand tables.
- Abstract/introduction promises are delivered: scoped descriptive comparison in §5; support/dependence restrictions in §3 and Appendix C; standard derivations and boundaries in §4.2/Appendix A. Conclusion echoes these promises without suddenly adding runtime, full-suite, universal-budget, or family-independence claims.

### Unmet original user deliverables / boundaries

The PDF, LaTeX, current official template, filled checklist, pinned acquisition code, seeds, package versions, commands, per-pipeline timings and table/figure map are present. **Genuinely unseen-family/ancestry-independent predictive accuracy is not established**, even though corrected recorded-key separation is established. This is an unresolved scientific target, not a prohibition on descriptive reporting or an instruction to rerun now.

Full-project timings/compute, every run's memory, agent API/model costs, and historical peak storage cannot be certified. Current 870,484,414-byte inventory is below 5 GB but not a historical peak. The literal author-block template words are mandated anonymous boilerplate, not unfinished scientific content. Final packaging items referenced by README (`final_report.md`, `submission_code.zip`, `storage_report.json`) were not present in the root listing at inspection; the main agent already owns packaging. No verified public anonymous release is claimed or required for this descriptive manuscript. Do not redistribute unresolved-license raw/row-level OpenLLM material merely to fill the bundle.

## Blocking Issues

**Count: 1.**

### B1 — Figures 1–2 fail final-size legibility/accessibility

- **Location:** PDF p.7; `main.tex` Figures 1–2; `src/analyze.py` plotting function.
- **Evidence:** 5.5-inch official text width versus 12/10.5-inch figure canvases; calculated ordinary text approximately 4.13/4.71 pt and legends 2.75/3.14 pt; same-marker solid-line color distinctions.
- **Required fix:** use larger final-size fonts and legends, distinct dash/marker encodings, and a less compressed panel arrangement. Preserve every plotted datum and interval definition. A single-column vertical arrangement or selected main panels plus readable appendix panels is preferable to merely enlarging the caption. Recheck the PDF at 100%/print size, keep the main paper within nine content pages, and recompile/copy the final PDF after the main agent patches presentation.

No numerical-result replacement, retuning, additional confirmation experiment, mandatory new algorithm, or retrospective purification of original data is required by this blocking item. A6/A7 are small recommended manuscript corrections; A4 is a substantive uncertainty-communication improvement. Experimental omissions remain disclosed limits, not hidden completed deliverables.

## Prebuttal Notes

- **“No novelty.”** Agree that the estimators/theory are standard. Defend the descriptive evidence and explicit distinction between acquisition objectives/target supports; do not claim priority under a five-source restricted review. Whether that contribution suffices remains a reviewer judgment.
- **“The primary study failed.”** Correct: 1/5 feasibility versus 3/5 required. All five preset splits remain descriptive. Neither seed 37 nor later sensitivities restores confirmation.
- **“OpenLLM leaks aliases.”** Original splits share revision keys and are quarantined. Separately versioned connected sensitivities have verified zero recorded SHA/Base Model/component overlap in all partition pairs, but reused data and unknown ancestry remain limitations.
- **“The bootstrap is overconfident.”** Percentiles are conditional on fixed pipelines/cohorts and original random bank, not validated population or individual predictive coverage. Disclose the giant component and finite-bank uncertainty; interval reproduction is not a coverage proof.
- **“Weak/incomplete baselines.”** Acknowledge capped factor fits and omitted feasible complete-row covariance. Comparisons are to the implemented fixed-compute baselines, not converged optima or the strongest imaginable predictor.
- **“Native greedy optimizes the wrong support.”** Correct for an observed-support-aligned interpretation. The evaluated policy deliberately remains the original full-panel implementation, with paired fixed audits; changing-target deployment curves are diagnostic only.
- **“Low error means benchmarks can safely be skipped.”** No. Equal benchmark counts are not measured costs; mixed-metric average errors, missing targets, and no predictive calibration do not establish safety or per-model reliability.

**Exact changes made by this reviewer:** none to manuscript, bibliography, checklist, figures, code, data, or experiment results. Created only `/work/paper/self_review.md`. The main agent should patch presentation/wording and handle final packaging.
