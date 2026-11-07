# Self-Review

Draft: `/work/paper/main.tex`, `/work/paper/appendix.tex`, `/work/paper/checklist_filled.tex`; compiled `/work/paper/main.pdf`.
Output: `/work/artifacts/paper_self_review.md`.

## Verdict

**Reject-first simulation:** A main-conference reviewer could reject this as an incremental application of established influence selection and refit verification, with exposure accounting rather than a new robustness result. The two-flip headline concerns an exceptionally weakly separated, estimator-sensitive pair; matching does not isolate a judge/design effect, and the NBA panels do not establish a practical attack or defense. The useful empirical documentation may not supply sufficient new general knowledge for NeurIPS Main Track.

**Score-based verdict: major-rework for main-conference contribution sufficiency, not for numerical invalidity.** Scores: contribution **2/5**, clarity **4/5**, results **4/5**, testing **4/5**, method **4/5**. Acceptance is not assured by correcting the presentation.

**Local-delivery assessment:** The numerical study is credible within its stated bounds. No contradiction was found in the checked headline numbers. One grouped claim-calibration correction should precede delivery: replace necessity language at `main.tex:129,172` with sufficient-witness language. Two additional handoff issues concern submission mode and a replay-command example, not the primary results. Honest limited novelty is **not** fabricated firstness: the abstract and introduction expressly disclaim priority, optimality, production replication, and causal attribution.

Review execution: Pass 1 read the complete TeX and 27-page PDF and recorded suspicions before loading the checklist helper. Pass 2 completed all five aspects sequentially: the required code-interpreter/task-dispatch runtime for `fiveAspectReview(draftText)` is unavailable, so the skill's fallback was used after reading its helper. Pass 3 used read-only local Python scans and artifact recalculations. No network, literature search, new literature, code-agent delegation, primary-result rerun, or manuscript/code modification occurred. Only the five bibliography sources were used for literature positioning, through existing permitted reading notes; they were not freshly reread in full. Rendered figure pages supplied by the PDF reader were inspected; separate shell rendering was unavailable without installing tools.

## Pass-1 Suspicions

Recorded before the helper; “open” includes unresolved judgments, not just proven defects.

| ID | Location and initial suspicion | Confidence | Evidence that would settle it | Disposition |
|---|---|---|---|---|
| S1 | `main.tex:172`, deletion “requires” counts: an incomplete search may have been promoted to necessity. | High | Exhaustive lower-bound evidence, or correction to sufficient witnesses. | **Open; confirmed wording defect.** Source `supplement.py:12–34` only searches selected prefixes. Mechanical scan also finds “require” at `main.tex:129`. B1 below. |
| S2 | Title, abstract, Introduction: two flips may only advertise a near tie rather than robustly established leadership. | High | Original gap, resampling separation, fixed-target tie/ridge results, and explicit qualification. | **Resolved as disclosed scope**, not a hidden defect: gap 0.008133696; positive in 110/200 resamples; tie removal gives gap −0.022627228. All are prominent. |
| S3 | Related work and contribution paragraph: fixed-schedule reversals plus accounting may be too incremental for Main Track. | High as rejection risk | A non-obvious mechanism, methodological advance, or stronger generalizable empirical insight; exhaustive novelty cannot be established within this source boundary. | **Open judgment.** No false priority claim found; contribution score remains 2. |
| S4 | §4.4 / Appendix C: ordered-cell matching could mix representations or conceal different observation units. | Medium | Shared-cell construction and representation check, plus unit/selection disclosure. | **Resolved within local evidence.** `run.py:102–110` aligns ordered cells; protocol records 1,232. Existing `code_audit.md:124` reports zero answer-pair representation mismatches without printing text. Exported GPT-result unit and selected-support caveats are explicit. This review did not inspect raw responses. |
| S5 | §4.4 / Table 3: corrected Arena subsets might still be pseudo-replicates or obsolete summaries. | Medium | Twenty distinct hashes, actual N below pool size, current summary reconciliation. | **Resolved.** Pool 3,222; actual N 2,400; 20 distinct hashes in current `matched.csv`; budgets 2/6/14 min/median/max. |
| S6 | §4.3 / Figure 1 / Table 5: interval values or interpretation may disagree with artifacts. | Medium | Recompute actual endpoints, percentiles and positive counts; inspect actual labels. | **Resolved.** Values agree; bands are explicitly descriptive and conditional, not minimum-budget or selection-valid population intervals. |
| S7 | §3.2 / Appendix A.4: optimizer tolerance might dominate the strict reversal event. | Medium | Saved verified gaps, fresh-reconstruction gradients, numerical error scale. | **Resolved for six primary witnesses.** Smallest absolute verified negative gap is 8.7081873e−4; largest reconstruction gradient 2.639204e−9. No borderline 1e−7 success is being sold. |
| S8 | `main.tex:2`, PDF p1: `[preprint]` may be wrong for conference submission. | High, conditional | Intended delivery mode and official local template options. | **Open conditional handoff issue.** Fine for local/preprint delivery; official anonymous submission must not use preprint mode. F2 below. |
| S9 | Appendix G.1, PDF p17: `--replay` may not survive PDF extraction/copying. | Medium for visual issue; high for incomplete instruction | Copy-safe rendering and a complete command with required directory argument. | **Open minor issue.** Extraction yields U+0015 before `replay`; source also omits the required argument. Cannot establish the visible glyph from extraction alone. F3 below. |
| S10 | Intro scope paragraph / Appendix H.1: process-boundary language may crowd the scientific argument. | Medium | Reader/editor judgment after separating scientific scope from administrative provenance. | **Open editorial judgment**, not an integrity defect. Keep compliance records; optionally shorten repetitive public-facing process prose. |

Open suspicions: **5** (S1, S3, S8, S9, S10).

## 5-Aspect Findings

### Contribution — 2/5

- **High rejection risk, not factual misconduct:** the derivative and selection/refit architecture are straightforward extensions. Existing permitted notes establish that Huang et al. already study Arena/MT-Bench deletion sensitivity with full refits and exposure/gap analysis; Broderick et al. already establish achieved sensitivity via refitting; Min et al. already manipulate outcomes for newly appended votes. The manuscript acknowledges all three distinctions correctly (`main.tex:33–49`).
- The bounded contribution is real: existing-row binary reversals preserve the schedule, with physical-row accounting, incident/edge controls, fixed-target estimator checks and an NBA comparison. None individually demonstrates deep methodological novelty. A capable specialist could likely derive the basic flip score quickly; the artifact collection is more substantial than the formula.
- The most defensible new knowledge here is **how the interpretation of a witnessed budget changes when exposure, weak separation and estimator conventions are reported together**. This is not a demonstrated universal law or isolated causal mechanism. Better framing cannot guarantee Main Track sufficiency; stronger insight would require additional research, not a cosmetic firstness claim.

### Clarity — 4/5

**Reverse outline:**
- Introduction paragraphs: interpretability problem → closest prior overlap → fixed-schedule contrast → near-tie limitation → three bounded contributions → empirical/source scope.
- Method: objective and edit unit → strict endpoint → derivative used only for ordering → finite verification/search incompleteness → denominators → controls.
- Experiments: protocol/data/QC → primary budgets and separation → random controls → matching/cohort checks → fixed-target sensitivity and comparator negative result.
- Discussion/conclusion: conditional evidence → unresolved dependence/search issues → offline interpretation → responsible use → bounded conclusion.

The sequence is coherent; no central module is unmotivated. Exposure, direct exposure, decisive edit pool, original-pair reversal, and top-one replacement are distinguished. Fix B1's two local necessity verbs. Process-heavy repetitions can be shortened without deleting the scientific limitations. The replay example needs a complete argument (F3). Seven main pages are not a problem under a nine-page limit.

### Results — 4/5

The checked witness counts, fractions, controls, descriptive bands, matching summaries, fixed-target ablations and comparator counts agree with the local outputs. Trust in the **conditional numerical witnesses** is high; evidence for population winner changes, real label errors, judge quality, or design superiority is intentionally absent and not claimed.

Figures were checked in the compiled PDF, not inferred only from captions:
- **Figure 1, p5:** blue circles/orange diamonds distinguish denominators; panel (b) places original margins against empirical bands and zero. Actual axes are “Witness budget (%) — log scale” and “Leader − runner-up log-strength”; panel title is “Empirical resampling bands.” No “minimum attack budget” or population-confidence label remains.
- **Figure 2, p14:** actual horizontal label is “Nominal exposure-referenced total budget (%)”; vertical label “Pair reversal rate.” Legend: Uniform, Incident uniform, Incident adverse, Frozen influence. Nominal-grid positioning and rounded integer budgets are disclosed. Deterministic influence is not displayed as 100 independent trials.
- **Figure 3, p14:** actual axes are “Baseline adjacent-pair gap” and “Exposure-scaled witness budget (%),” both logarithmic. **Minor accessibility improvement:** six cohorts share the same marker shape and rely on color; add marker shapes/direct labels if revising. This is not a numerical blocker.

All three graphics are vector PDFs and legible at the supplied page scale. All eight tables have captions above, booktabs rules and no vertical rules. There is no competitive “best” cell whose bolding or arrow direction could be wrong; lower witness counts are not universally better scientific outcomes. Tables and figures all have references in the text/artifact map. No pipeline diagram is needed merely to satisfy a generic checklist.

### Testing — 4/5

For the claimed conditional audit, coverage is substantial: four equal-budget controls, fixed-target ridge/tie/inconsistent-row sensitivity, NBA home adjustment, adaptive flips, same-estimator deletion, original-row reconstruction, 200 resamples per panel, 20 human judge-choice seeds and 20 genuinely different Arena subsets. Failures and negative findings are retained. Saved tests report seven passes.

The closest deletion work is discussed and a same-estimator deletion comparator is included; the paper explicitly explains why published filtering/estimator/counts are not reproduced. New-vote injection is a different intervention, not a missing directly commensurate flip baseline. Generic demands for predictive accuracy, GPUs, SOTA gain tests or train/test splitting would be misplaced.

Remaining limits are real but already bounded: no exact global-minimum benchmark at study scale, no margin/cohort-isolated causal comparison, no dependence-complete bootstrap, no real-world attack/defense validation, and no independent upstream label audit. Additional such evidence would strengthen the contribution; none is required to make the six conditional witnesses true. The replay validates execution in a separate environment, not independent data or independent estimator code.

### Method — 4/5

Objective, flip-benefit sign, strict event, aggregation and positive-ridge existence/uniqueness/centering arguments are consistent with `bt.py`. For a continuous label change, the gradient differentiates to `H dtheta = x_i delta_y_i`, giving the stated margin derivative and its negative benefit. Canonicalization changes both orientation and outcome; home designs also reverse the home covariate. The home coefficient receives ridge as documented.

Frozen positive-benefit selection is an incomplete heuristic. The paper correctly says that powers-of-two probing can miss transient crossings and that a noncrossing k−1 is not an optimality certificate. No mathematical robustness guarantee has been smuggled in. Retrospective outcome access is realistic for an offline auditor, not demonstrated live-attacker access. Sum-loss ridge changes relative strength with sample size, and half-label ties are an estimator convention; both implications are discussed. B1 is wording inconsistent with these otherwise sound boundaries, not evidence that all counts are wrong.

## Protocol Audit & Mechanical Scans

### Dataflow and information audit

1. **Inputs → parsing:** `prepare.py` uses pinned local Arena winner fields, two MT exports, and deduplicated NBA games. Arena threshold is 100 appearances; all 64 pass. MT maps 380 inconsistent GPT results and 220 ordinary ties to 1/2. NBA selects `_iscopy==0`, then seasons separately. Processed edge-list columns omit response/prompt text.
2. **Fit:** all observed rows enter each unweighted sum-loss ridge fit; lambda=1 is specified, not optimized for the headline. There is no supervised training/test partition and no predictive-generalization claim. Logs record exploratory planning and departures, not an externally timestamped preregistration.
3. **Select/evaluate:** original leader/runner-up and initial benefits are selected on those same rows. Distinct decisive rows are flipped once; aggregate counts preserve the schedule and row cost. Numerical refits assess the same fixed contrast. This reuse is intrinsic to retrospective sensitivity, **not hidden held-out leakage**.
4. **Controls:** every control uses the same dataset, estimator, target and witnessed budget, with 100 trials. They are not equal-information adversaries: the adverse pool uses outcome/target information; edge matching uses witness locations. That asymmetry is stated and is part of the comparison, not evidence of attack superiority against all alternatives.
5. **Resampling:** Arena/NBA resample rows; MT resamples question clusters. Targets stay fixed, schedules/multiplicities change; first-30 auxiliary searches may edit duplicated slots. The paper does not treat these as physical-row minimum-budget intervals or independent population validation.
6. **Matching:** MT aligns ordered cells and samples one human row per shared cell; GPT runs once. Arena top-six selection uses the full-data ranking, subsets overlap, and targets are reselected per subset. These post-selections are disclosed. Twenty distinct hashes do not imply twenty independent populations.
7. **Sensitivity/comparators:** `supplement.py` freezes primary target identities for ridge/tie/home checks; already-reversed Arena is retained as k=0 specification change. Adaptive flips never reuse rows. Static deletion uses full refits but an incomplete selected-prefix search. Original-row witness verification uses a fresh BT object with changed saved-row labels, not a separately developed solver.
8. **Reproducibility:** source order is prepare → tests → run → supplement → report. `report.py` reads current fixed-target and comparator artifacts. This review independently compared the **13 existing accepted/replay CSVs** with rtol=1e−8, atol=1e−9: all agree, without fitting again. `validation.json` and saved logs support the earlier checks. Replay memory/time are scoped to its main child process, not total project compute.

No new leakage, forbidden future-information dependency, or unfair copied-baseline setup was found within the stated endpoint. Assumptions—finite fixed design, positive ridge, observed-label access, exported-row edit units, empirical resampling units, and incomplete search—are discussed downstream rather than silently abandoned.

### Claim-to-evidence map

| Claim / promise | Evidence | Assessment / conclusion alignment |
|---|---|---|
| Fixed observed schedules, sum-loss ridge and frozen influence proposals | Equations 1–3; `bt.py:18–76,82–102`; `run.py:13–22` | Supported; Conclusion retains estimator/target conditionality. |
| Six sufficient budgets 2/46/61/3/4/8, with physical-row verification | Table 1; `baseline.csv`, `witness_rows.csv`, `witness_verification.csv` | Supported as witnesses, not minima. Echoed in Conclusion. |
| Arena 0.0035% globally versus 0.024% exposure | 100×2/57477 = 0.003479653%; 100×2/8413 = 0.023772733% | Supported after rounding. |
| Uniform and incident-uniform controls yield no reversals in 100 trials per panel; edge controls sometimes succeed | Table 2; 2,400 rows in `controls.csv`; `control_summary.csv` | Supported, correctly not a universal impossibility claim. |
| Matched GPT witness exceeds human witnesses on selected support | Table 3; `matched.csv`; `matching_protocol.json` | 33 versus 14–21; support/causal restrictions explicit. No claim of a larger true minimum is made. |
| Arena is weakly separated and reverses under tie removal | Figure 1/Table 5; fixed-target table | 110/200 positive; tie-free gap −0.022627228. Supported and promoted to Introduction. |
| Fixed-target ridge/tie checks qualify any single fragility number | Table 6; `fixed_target_ablations.csv` | Arena k=1/2/11 across lambda; GPT k=40/47/61 across tie conventions; NBA k unchanged. Supported. |
| Adaptive flips give no smaller witnessed counts; MT linear predictions understate refit counts | Table 7; `method_comparison.csv`, baseline `predicted_k` | Supported: 45 versus 46 and 56 versus 61 for MT. No global-optimality inference. |
| Static deletion “requires” 3/92/144/5/7/16; MT flips “require” exposure percentages | `main.tex:172,129` | **Unsupported necessity wording.** The counts/percentages are numerically correct sufficient witnesses. B1 gives minimal correction. |
| Reproducible CPU-only evidence trail, not exhaustive novelty or production replication | Appendix G; saved replay/tests/resource records; five permitted literature notes | Supported within stated scope. Conclusion promises no stronger outcome. |

### Numeric reconciliation

Primary values recomputed/cross-checked, in dataset order Arena, MT human, MT GPT, NBA 2013/2014/2015:

| Dataset | N / exposure E / decisive rows | k | 100k/N | 100k/E | Verified negative margin |
|---|---:|---:|---:|---:|---:|
| Arena | 57477 / 8413 / 39716 | 2 | 0.003479653 | 0.023772733 | −0.000870819 |
| MT human | 3355 / 1825 / 2575 | 46 | 1.371087928 | 2.520547945 | −0.007132468 |
| MT GPT | 2400 / 1440 / 1800 | 61 | 2.541666667 | 4.236111111 | −0.006430681 |
| NBA 2013 | 1314 / 199 / 1314 | 3 | 0.228310502 | 1.507537688 | −0.058564631 |
| NBA 2014 | 1319 / 196 / 1319 | 4 | 0.303260045 | 2.040816327 | −0.066514875 |
| NBA 2015 | 1311 / 193 / 1311 | 8 | 0.610221205 | 4.145077720 | −0.052903582 |

Every primary k equals its saved incident-edit count. Direct exposures are 134/200/160/9/10/9, not union exposures. Reconstructed margins differ from stored margins by at most **5.3144e−11**; largest reconstruction gradient is **2.6393e−9**. All k−1 stored margins are positive, without proving earlier-prefix or subset optimality.

**Actual Wilson endpoints, percent units:** 0/100 → [0, **3.699350**]; edge controls Arena 17/100 → [**10.893566,25.548005**], NBA 2013 27/100 → [**19.269584,36.432117**], NBA 2014 1/100 → [**0.176743,5.448620**], NBA 2015 15/100 → [**9.305985,23.283560**]. MT edge controls are 0/100. NBA 2013 adverse is also 1/100. Recomputed endpoints match CSVs within 7.7e−17 in probability units. Prose rounding, including [0.2,5.4]%, is correct.

**Actual 2.5th–97.5th empirical gap bands:** Arena [−0.102829813,0.107076607]; MT human [0.137257555,0.655279802]; MT GPT [0.554834140,1.086941799]; NBA 2013 [−0.478894757,0.894144791]; NBA 2014 [−0.387180510,0.780242692]; NBA 2015 [0.089688330,1.268567550]. Positive counts are **110/199/200/155/163/199 out of 200**. First-30 slot-witness counts are **16/29/30/24/28/29**; the other first-30 draws are already reversed, not failed robustness certificates.

Matched summaries agree: human k=14/16.5/21, median exposure 2.320675%; GPT k=33, exposure 4.641350%; median gaps 0.325292/0.819015. Arena subsets k=2/6/14 and median exposure 0.347431%. Fixed-target table has 19 rows, including the already-reversed Arena case; adaptive and deletion counts agree with Table 7. Adjacent count is **160 = 63+5+5+29+29+29**.

Generated macros agree: main runtime **42.0 s** (42.0346335 unrounded), **15,032** primary-object fit calls, maximum recorded primary gradient **9.997324e−9**, macro rounded to 1.0e−8. Replay is **41.260396 s**, **301.871094 MiB**; neither is total-project metering. No percentage-improvement or SOTA claim needs rescuing by a significance calculation.

### Mechanical findings and cleared scans

**F1 — Medium, high confidence: unsupported necessity wording (B1).** Locations `main.tex:129,172`; see Blocking Issues. This is not a false numerical count and not evidence of fabricated minima throughout the draft.

**F2 — Conditional submission-format gate, high confidence.** `main.tex:2` loads `[preprint]`; PDF p1 says “Preprint.” Local `template/PROVENANCE.md` says anonymous submission uses the default or `[main]`, not preprint/final. Minimal action **only if preparing a real submission:** switch to the official anonymous submission option and rebuild/recheck page boundaries. The current local/preprint deliverable is not blocked by this. The style file itself is byte-identical to the locally preserved official ZIP (SHA-256 `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a`).

**F3 — Low, high confidence for missing argument; limited visual confidence: replay instruction/copyability.** `appendix.tex:219` names `src/validate.py --replay` without a path, whereas `src/validate.py:10` defines a required `Path` argument when that flag is used. Minimal copy-safe example, from `/work`: `PYTHONPATH=/work/src python /work/src/validate.py --replay /work/reproduction_check`. Set the path to the actual replay root in a relocated archive. PDF p17 text extraction also turns the two hyphens into U+0015; use a verbatim/path-safe command and check copying. This does not negate the existing successful replay.

**Cleared:**
- PDF is **27 pages / 393,126 bytes**: main pp1–7; references p8; appendix pp9–19; filled checklist pp20–27. The seven-page main text is within the official nine-page submission limit. References/appendix/checklist are excluded, not a reason to call the paper overlength.
- All five cited keys resolve, all five bibliography entries are used, and no sixth research source appears. Metadata include authors, title, year, pinned arXiv identity/version and URL; arXiv-only citation formatting is not an invented missing-venue defect. Claims about the closest work match the permitted notes; no new literature was sought.
- **44 labels**, no duplicates or unresolved `ref/eqref/pageref`; all 11 TeX inputs and three graphic paths exist. No unresolved citation or overfull-box warnings found in the current build log.
- No TODO/FIXME/XXX/placeholder markers in the reviewed manuscript, generated tables/macros or bibliography. Historical plan/audit logs and pristine official template placeholders are not manuscript leftovers.
- Anonymous author line; PDF author metadata blank; no acknowledgment or obvious identifying self-citation found. No margin/font/style reduction found in the reviewed source. Conference mode remains F2, not an anonymity allegation.
- No false public-code-hosting claim. README/archive/license/notices packaging is in progress under the main agent and **was not treated as missing or as a blocker**. Final bundle existence/content remains the packaging handoff, not something this review certifies in advance.

Deduplicated protocol/mechanical findings: **3** (F1–F3). No additional dataflow-validity blocker found.

## Blocking Issues

**B1 — One grouped, small but necessary claim correction before delivery (medium severity; high confidence).**

1. `main.tex:129`: replace “MT human and GPT-4 require 2.521% and 4.236% of target exposure” with **“The MT human and GPT-4 witnesses use 2.521% and 4.236% of target exposure.”**
2. `main.tex:172`: replace “Static deletion under the same estimator and original targets requires 3, 92, 144, 5, 7, and 16 deletions” with **“Static deletion under the same estimator and original targets yields sufficient witnesses of 3, 92, 144, 5, 7, and 16 deletions.”**

Neither necessity assertion follows from a selected-prefix search. The reported values need not change; no new primary experiment is needed. These are **unsupported lower-bound implications**, not numerically disproved counts. Surrounding upper-bound disclaimers reduce the severity but do not make those local verbs precise.

**Blocking issue count: 1.** No critical numerical failure, leakage defect, or demonstrated false headline value was found. F2 is an additional gate for an actual conference submission, not local delivery. Novelty insufficiency, observational confounding, limited resampling dependence models and offline access assumptions are research/venue limitations, **not silently repairable formatting blockers**. The main-conference verdict remains major-rework even after B1 because contribution sufficiency is a separate judgment.

## Prebuttal Notes

- **“This is already known.”** Agree that ranking sensitivity, outcome manipulation and full-refit verification are established. The bounded deliverable is existing-row fixed-schedule reversal witnesses with exposure accounting, controls and fixed-target estimator diagnostics. Do not answer with “first,” and do not promise that this distinction meets Main Track standards.
- **“Two flips only reverse a near tie.”** Correct: gap 0.00813, 110/200 positive resamples, and tie removal alone reverses the pair. This is the paper's interpretation lesson, not evidence of displacing a clearly established population winner.
- **“These are not minimal attacks.”** Correct. Successful k-edit sets upper-bound unknown minima; k−1 checks and adaptive equality do not prove optimality. Apply B1 consistently.
- **“Human versus GPT differences are confounded.”** Correct. Ordered-cell matching restricts support, not margin, judge population, dependence or all conventions. Report 33 versus 14–21 as witnessed budgets, not causal robustness or judge-quality superiority.
- **“Why not reproduce the deletion paper?”** The table is a same-estimator intervention comparator, with distinct fixed-target and filtering conventions explicitly stated. It is not a reproduction or a count-efficiency win over that work.
- **“The bootstrap validates the attack.”** It does not. It describes selected-target empirical margins under changed schedules; auxiliary slot edits are separately labeled. No population/minimum-budget interval is claimed.
- **“Reproducibility is only asserted.”** Point to saved row IDs, numerical residuals, tests, pinned data/environment and the 13 already matching replay CSVs. State that fresh-object reconstruction shares estimator code and the replay shares raw snapshots; neither is independent data collection or human validation.

**Counterintuitive protocol completed:** reject-first paragraph above; unsupported necessity claims selected for replacement rather than defense (no edits authorized); near-tie/tie-removal limitation already promoted to the Introduction; novelty attacked rather than embellished. Trust scorecard **9/10**: baseline fairness 2, reproducibility 2, honest limitations 2, failure transparency 2, statistical scope 1 (dependence and selection remain incompletely modeled, although correctly disclosed). No generic SOTA-gain or mandatory holdout kill-switch applies to this conditional audit. Strong numerical trust and limited novelty can coexist.
