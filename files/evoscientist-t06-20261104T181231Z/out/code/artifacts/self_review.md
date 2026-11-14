# Self-Review

Draft: `/work/paper/main.tex` (with `appendix.tex`, `checklist_completed.tex`, `permitted_literature.bib`, and the supplied 25-page `main.pdf`).
Output: `/work/artifacts/self_review.md`.
Final delivery-presence check: 2026-11-04 19:13:18 UTC. No manuscript or code was edited. No browsing, prior research findings, or restricted-paper identity inference was used.

## Verdict

**Needs-work for submission delivery/formatting; the evidence supports the narrow empirical conclusions.** No scientific or numerical bug was demonstrated. The 4/6 uncapped and 1/6 capped reversal counts, exposure measurements, NBA arithmetic restriction, matched-panel contrast, and uncertainty descriptions agree with the supplied measurements and implementation. These results do not establish causal evaluator effects, method superiority, nonlinear optimality, or population-level robustness; the manuscript correctly avoids those claims.

Three release blockers remain at this audit snapshot: the promised reproduction/resource deliverables are absent, the PDF contains Type-3 fonts, and all 13 table captions violate the supplied template's placement rule. These are not reasons to discard the experiments. This is a verification verdict, not a predicted conference acceptance decision.

**Reject-first simulation.** A skeptical reviewer could regard the contribution as a careful reporting audit rather than a methodological advance: inverse-Hessian selection is established, the exposure identity is elementary, and much of the sports contrast follows directly from integer feasibility. The evidence must therefore stand on its concrete diagnostic value and reproducibility, not novelty inflation. The current draft makes that distinction honestly, but its release/checklist assertions outrun the currently available package, and the compiled PDF fails two explicit formatting requirements. Those are the actionable weaknesses; inventing a requirement for causal experiments or SOTA superiority would misreview the paper's actual claims.

## Pass-1 Suspicions

Recorded after reading the complete draft/PDF and before the structured aspect review. “Open” includes a verified issue awaiting repair, not only an unproven scientific concern.

| ID | Location and original suspicion | Confidence and settling evidence | Disposition |
|---|---|---|---|
| S1 | Abstract; §5.1; Table 2: counts and standardized effects could conceal inconsistent raw margins or denominators. | High-priority check; source CSVs, original margins, exact sets, and refits settle it. | **Resolved.** Counts, fractions, margins, and D agree. Table 8 supplies edited raw margins; counts/N recover realized fractions. Adding raw reductions/fractions to Table 2 would improve accessibility, not fix a false claim. |
| S2 | §5.1 NBA cap comparison could mistake arithmetic infeasibility for robustness. | High; reconstruct incident capacities and feasible count bounds. | **Resolved.** Zero-cap teams are 27/26/28; count bounds and selected counts are 1/2/1. The text explicitly explains the restriction and cap+1 changes it. |
| S3 | §4 matched panels; §5.3: aggregation could change units or compare unsynchronized targets. | High; compare cell IDs, endpoints, degrees, groups, target pair, and paired draws. | **Resolved.** All schedule fields match; both target GPT-4 versus Claude-v1. Aggregate-cell cost caveats are explicit. |
| S4 | §3.4; §5.2; Appendix F: bootstrap reversal rates might be interpreted as edit-caused flips or significance. | High; inspect resampling/selection code, summaries, and interval labels. | **Resolved.** Procedure is recomputed on expanded samples; pre-existing reversals can contribute. The text/caption discloses this and distinguishes random-subset ranges, original sampling variation, and exploratory procedure variation. |
| S5 | Eq. (4); Appendix A: derivative signs or noncanonical sufficient statistics could invalidate selection. | High; independently differentiate the estimating equation and run orientation/finite-difference tests. | **Resolved.** Both signs are correct; canonical a<b is enforced in `bt.py:22–27`; all 11 tests pass. |
| S6 | §5.1; Appendix E: “all tested conditions” and complete replay claims might exceed the evidence. | High; inspect every MILP row and replay every deterministic witness. | **Resolved.** All 16 MILP rows report status/gap 0; 338 witnesses cold-replay. Maximum greedy surrogate loss is 0.007115 and maximum greedy/integer refit-margin difference 0.010381 over tested conditions. Neither is a nonlinear certificate. |
| S7 | §5.4 Arena deletion discrepancy might reflect optimizer failure rather than nonlinearity. | Medium; cold starts, residuals, and an independent row-loss optimizer. | **Resolved.** Cold replay agrees; production residuals are small. Independent BFGS gives the same deletion margin within 2.60e-8 (with a precision-loss warning, so not a separate convergence certificate). The large linear/refit discrepancy is real. |
| S8 | Introduction/related work: is this enough new knowledge beyond established influence analysis? | Medium, subjective; contribution judgment within the permitted literature, not an unbounded novelty search. | **Open, nonblocking scope judgment.** Existing application is explicitly credited. Preserve the denominator/uncertainty-audit framing; no evidence here establishes broad originality or method superiority. |
| S9 | Tables 1–13: caption placement may violate venue requirements. | High; supplied official template, not generic taste, settles it. | **Open, demonstrated defect.** All 13 captions follow content; template requires captions before tables. See B3. |
| S10 | Appendix G; checklist items 4/5/8/13: resources/archive claims may precede actual delivery. | High at final presence check; finalized files, archive inspection, and fresh PDF settle it. | **Open, delivery blocker.** Relevant files/archive remain absent at the final check. They are being finalized by the primary assistant, not verified here. See B1. |
| S11 | §3.1/§4; dated plan: “before outcome inspection” chronology cannot be independently established by current code/results. | Low suspicion; an immutable pre-outcome record or contemporaneous execution history would settle chronology. | **Open, provenance limitation only.** `todos.md` records the settings and code agrees; exploratory additions are disclosed. No evidence of retrospective tuning was found. Do not call this independently preregistered. |

## 5-Aspect Findings

The code-interpreter tool required by `five_aspect_review.js` is unavailable. The skill's permitted **sequential checklist fallback** was completed for all five aspects; there are no missing aspects. Mechanical checks were executed separately with shell Python, not attributed to the unavailable script.

### Contribution — 3/5

The contribution is an exposure-aware interpretation/reporting audit, not a new influence technique. The elementary exposure identity plus actual counterfactual witnesses, feasibility diagnostics, and uncertainty separation provide useful concrete knowledge. The Arena comparison is particularly informative because counts are similar (574 versus 555), whereas the NBA contrast has an explicitly different arithmetic mechanism. Six full cohorts are not six independent evaluation designs or a prevalence estimate, and the paper does not say otherwise.

Do not add a method-superiority claim. Related work expressly credits the closest permitted BT-deletion application; the AMIP-style deletion control is present. Failure to reproduce a published minimum-edit number is not a missing comparison for the stated claim, given its explicit scope disclaimer.

### Clarity — 4/5

Terminology and edit units are unusually explicit. Fixed-pair reversal, incidental winner change, original uncertainty, and random-edit variation are distinguished. The claim “4 of 6” is not directly visible in Table 2's columns, but it is recoverable from Table 1 plus D and appears directly in Table 8's margins. Optional improvement: include raw margin reductions/edited margins and actual global fractions beside the primary endpoint.

**Navigation repair:** add direct text references to `tab:controls` (Appendix C), `tab:feasibility` (Appendix D), `fig:approx`, and `tab:grid` (Appendix E). They currently have no explicit `\ref`/`\eqref` references; appendix-level references do not identify the individual exhibit.

**Reverse outline:** Introduction: denominator ambiguity → established influence work → why operations differ → observational scope → three audit components → conditional takeaway. Method: fitted target → units/exposure/cap arithmetic → selection and refitting → uncertainty semantics. Results: exposure/count contrast → point flips versus uncertainty → matched initial separation versus response → specification limits. These sequences are coherent; no promised component silently disappears from the conclusion.

### Results — 5/5

All central numerical statements checked against the supplied artifacts agree. This score reflects measurement/claim alignment, not novelty or acceptance likelihood. Independent checks performed:

- Replayed **338** deterministic witnesses from cold starts, checking indices, IDs, endpoints, original responses, exposures, applicable caps, and global budgets. Maximum margin discrepancy **7.31624e-9**; maximum replay gradient **6.98697e-9**.
- Reconciled **18,293** recorded fits (7,832 + 3,253 + 7,208); maximum recorded gradient **9.99941e-9**.
- Recomputed original-bootstrap summaries, all **80** random/control summary rows including Wilson intervals, and all **16** exploratory-bootstrap summary rows; maximum discrepancies ≤2.23e-16.
- Regenerated **12 numerical tables plus results macros in memory only**; all 13 TeX products exactly match the supplied files. The remaining, manually written source-provenance table was read, not independently license-verified.
- Independently evaluated the row-level loss with SciPy BFGS on five important conditions. Margins agree within 3.95e-8; four BFGS runs reported precision loss, so the production solver's tighter residuals and cold replay remain the convergence evidence.

### Testing — 4/5

All **11 tests passed** on this review run. Tests cover derivatives, an analytical two-player fit, canonicalization, cap selection, deletion/subset equivalence, adaptive uniqueness/replay, toy MILP brute force, and safe Unicode witnesses. Random edits, deletion, ridge, tie exclusion, source restrictions, aggregate-cell matching, whole-question operations, adaptive selection, and integer surrogates are relevant controls for an audit rather than a SOTA competition.

No full experiment pipeline, fresh 300-replicate resampling run, or clean reproduction-archive run was performed here. Existing raw replicate outputs were independently summarized; deterministic witnesses were freshly refitted. Dependence beyond the documented clusters and winner-selection-adjusted inference remain acknowledged limitations, not hidden defects. Archive-level testing is still required under B1.

### Method — 4/5

The sum-loss ridge objective, gradient/Hessian, centered solution, flip/deletion derivatives, weighted-average exposure identity, and endpoint-slot count bound are correct under the stated assumptions. The implementation matches them. Positive ridge makes the objective coercive/strictly convex; summing its gradient yields zero-sum fitted coordinates. Differentiating g=0 gives the printed flip/deletion signs. Pair aggregation is exact because counts and response sums suffice for this loss.

Offline knowledge/access, fixed original top-pair selection, fractional ties, equal aggregate-cell weights, unchanged deletion ridge, and incomplete dependence modeling are all disclosed. Static selection, adaptive selection, and a solver-optimal linear surrogate do not certify a nonlinear optimum. No causal or optimality overclaim requiring a scientific rewrite was identified.

## Protocol Audit & Mechanical Scans

### Reconstructed data flow and information availability

1. Fixed public records → validity/self-comparison filters → canonical orientation and immutable row IDs. NBA keeps one non-copy NBA row per game for 2013–2015, including playoffs; historical Elo is not used.
2. Fit the whole observed snapshot with sum-loss ridge 0.1; choose the original top pair on that same snapshot. There is no predictive train/test split: fitting, perturbation selection, and refit measurement on the same archive define the descriptive estimand, not test leakage into a generalization claim.
3. Static influence selects beneficial records under a floor global budget, optionally floor endpoint caps. Uniform random subsets use non-ties. Deletion has different semantics and its own residual influence score. All selected sets are fully refitted.
4. Original bootstrap resamples prompt-hash/question/game clusters and holds the pair fixed. Matched MT panels share cells and synchronized question draws. Exploratory bootstrap expands sampled rows and recomputes capacities, selection, and refits, still holding the original contrast fixed.

No hidden labels, future outcomes, historical Elo, trained manipulation classifier, or paid judge predictions enter the implementation inspected. Oracle-like offline edit access is explicit and is not represented as live attack feasibility. Comparisons share each cohort's objective and schedule; random versus targeted selection is intentionally unequal information, not an algorithm-accuracy contest. Count-matched and cap-feasible controls appropriately expose their different constraints and possible underfill.

### Claim–evidence map

| Claim/location | Supplied evidence and independent verification | Assessment |
|---|---|---|
| Abstract / §5.1: 4/6 uncapped, 1/6 strict-cap reversals at nominal 1% | `primary_endpoint_summary.csv`; cold witness refits: U flips Arena/NBA2013/2014/2015; C flips Arena only | Supported |
| §5.1: Arena 574 edits, 17.41% max exposure; capped 555; D 22.494→1.881 | Exact values: exposure 0.174137931; D 22.4941217/1.8811440; edited margins −1.2436559/−0.1001208 | Supported; not an equal-count causal effect |
| §5.1: NBA caps largely restrict counts | Reconstructed 27/26/28 zero capacities; bounds 1/2/1 versus global count 13 | Supported; explicitly not robustness certification |
| §5.2: Arena near tie, 52% leader retention, 35% random reversals | Margin 0.00423843; original interval [−0.103223, 0.105761]; `bootstrap.csv`, `random.csv` and summary recomputation | Supported; winner retention is not generally pair positivity |
| §5.2: non-Arena random reversals zero or one; NBA2015 interval positive | Primary random counts 0/0/1/0/0; NBA2015 original interval [0.158936, 1.385957] | Supported under stated uncertainty approximation |
| §5.3: common 1,814 cells and paired margin difference 0.479 | Cell IDs/endpoints/degrees/groups identical; paired difference 0.4790073, percentile interval [0.1726481, 0.7948121] | Supported; no evaluator-accuracy conclusion |
| §5.3: matched response versus initial separation differ | U margins human 0.030440, GPT-4 0.428448; standardized reductions 2.210847 and 2.049662 | Supported descriptive distinction, not an equivalence test |
| §5.4: ridge pattern persists; tie removal already changes Arena ordering | `ablations.csv`, regenerated Table 9; Arena altered unedited margin −0.0326252 | Supported; no false edit-induced baseline flip |
| §5.4: deletion linear 0.764 versus exact 2.281 | `primary_endpoint_summary.csv`: 0.7639742 versus 2.2813957; cold replay and independent row-loss check | Supported finite-budget nonlinearity |
| Appendix F: Arena capped edited interval crosses zero | `bootstrap_sensitivity_summary.csv`: [−0.2093437, 0.0008682], 97% negative edited margins | Supported; upper endpoint near zero is not stable significance evidence |
| Appendix E: 338 replays, discrepancy <1e-7 | Fresh replay agrees with `validation.json`; max 7.31624e-9 | Supported |
| §4 / Appendix G / checklist: complete delivered code/resources | Final presence check described below | Not yet supported at review cutoff |

### Mechanical results and discrete findings

**Five findings (P1–P5); the first three are release blockers.**

- **P1 — Type-3 fonts, demonstrated.** `main.pdf` has `/Type3` resources `/F57` (including page 1) and `/F218` (page 11). `main.log:754–755` records bitmap EC typewriter fonts `ectt0900`/`ectt1000`. Supplied `neurips_2026.tex:376–377,416–417` permits only Type-1 or embedded TrueType fonts and requires fixing Type-3 fonts. These are not merely “unembedded fonts”: Type-3 glyph programs exist but still violate this requirement.
- **P2 — Table captions, demonstrated.** All **13/13** table captions follow their content, starting at `main.tex:105–109`, `122–126`, `149–153`, and continuing throughout `appendix.tex`. Supplied `neurips_2026.tex:322–323` says the table number/title must precede the table.
- **P3 — Final delivery/checklist mismatch, demonstrated absence at cutoff.** `/work/paper/resources.tex`, `/work/README.md`, `/work/requirements.txt`, and `/work/reproduce.py` remain absent; no reproduction distribution archive was found (the official template zip is unrelated). Appendix G and checklist items 4/5/8/13 claim these deliverables/documentation. The reviewed PDF p.17 still contains the provisional runtime-replay fallback. Existing runtime metadata do exist; this is not a claim that no runtimes were measured. Final archive contents, privacy exclusions, clean reproduction, and finalized resource reporting **were not verified**.
- **P4 — Missing direct exhibit references, demonstrated, nonblocking.** `tab:controls`, `tab:feasibility`, `fig:approx`, and `tab:grid` have no direct in-text reference. Minimum repair: add explicit references in their introducing paragraphs.
- **P5 — Plan chronology not independently authenticated, low-confidence provenance concern, nonblocking.** `todos.md` documents the locked settings and the implementation agrees. The review cannot establish temporal precedence from a dated assertion alone. Preserve the distinction between internally recorded pre-outcome planning and independent preregistration; retain contemporaneous plan/run history if available. No tuning misconduct is demonstrated.

**Other scans passed:** six citation keys, all in the permitted bibliography; no uncited bibliography entries, missing references, duplicate labels, TODO/FIXME/TBD markers in manuscript/appendix/checklist/bib, unresolved LaTeX references, or overfull-box warnings. Bibliographic version annotations are explicit. External bibliographic truth, license compliance, prior network history, and exhaustive novelty were not independently certified; no browsing was undertaken. The closest-work/deletion relationship is explicitly acknowledged and no promised superiority comparison is missing.

**PDF/checklist:** 25 US-Letter pages; `main.aux` puts `maintextend` on **page 8**, below the supplied nine-content-page limit. References begin p.9, appendix p.10, checklist p.19. All 16 checklist answers/justifications are present (14 Yes, 2 N/A). Anonymous author presentation/empty author metadata show no obvious identity leak. Legal/IRB exemption is not inferred from secondary-data status. Underfull source-table boxes and h→ht float warnings are not demonstrated clipping defects. Figures were inspected in the supplied PDF: vector plots, blue/orange plus marker distinctions, explicit scales and interval semantics; no invented requirement for an algorithm pipeline figure or “best result” highlighting applies to this descriptive audit. All numerical tables use booktabs without vertical rules. The log-scale curve intentionally omits budget zero; the zero-budget measurements exist in the source data.

## Blocking Issues

1. **B1 — Finish and verify the promised release, then update/recompile the PDF/checklist (P3).** At the final audit these remain unfinished, consistent with the primary assistant's stated work in progress. Minimum fix: provide the README, pinned requirements, reproduction entry point, finalized resource report, and anonymized archive; inspect its manifest/exclusions and run the documented reproduction path in a clean environment. Confirm measured time/memory statements against the final report, or narrow checklist item 8. Rebuild so p.17 no longer reports a provisional source. Presence alone is not successful reproduction. **Do not claim this review verified the finalized package.**
2. **B2 — Remove bitmap Type-3 fonts and rebuild (P1).** Minimum fix: supply vector EC/typewriter fonts (for example the appropriate cm-super font installation) or a suitable vector monospaced replacement without altering the official style; then inspect the rebuilt PDF's complete font inventory. This review did not alter the TeX environment or test that remedy.
3. **B3 — Move all 13 table captions/labels before their tabular content (P2).** Minimum fix: relocate each caption/label above its `\input{tables/...}` or explicit `tabular`, preserving figure captions below figures; rebuild and recheck pagination/references. This is a documented template issue, not a scientific blocker.

No new experiment is required to repair a demonstrated scientific error, because none was found. New causal, globally optimal, or evaluator-superiority claims would require new evidence and should not be introduced during these repairs.

## Prebuttal Notes

- **“This is standard influence analysis.”** Agree. Point to explicit prior-work credit; the contribution is how denominator, feasible edit count, original separation, and edit-unit provenance change interpretation, supported by measured witnesses.
- **“NBA caps just prevent enough edits.”** Agree; Eq. (3), Table 7, actual counts, and cap+1 make that mechanism explicit. Do not defend the contrast as equal-budget protection.
- **“Arena was already tied.”** Agree for point-order interpretation. The original interval crosses zero; the audit separately shows large targeted score change and the effect of exposure allocation.
- **“The bootstrap proves the edited ranking/significance.”** It does not. Original SD is a reference scale; random ranges are conditional subset variability; exploratory distributions resample and reselect and include initially reversed samples.
- **“Human versus GPT-4 differences are causal or show accuracy.”** Neither is claimed. Same-cell matching controls schedule only, not label quality, human multiplicity, dependence, or all evaluator differences.
- **“The attack is optimal / failure proves robustness.”** No. Exact refits demonstrate feasible witnesses; only the tested additive surrogate has solver-reported optimality.
- **Unsupported-claim deletion protocol:** do not fabricate a strong scientific claim to delete—the draft already removed the obvious overclaims. The current unsupported present-tense assertions concern finished resources/archive; finalize and verify them or narrow those assertions/checklist answers. No edits were made by this reviewer.
- **Limitation promotion:** the important restrictions already appear in the abstract/main discussion (integer feasibility, original near-ties, no causal/optimality claims). Keep them there. Optional sentence in the exploratory-bootstrap results: the near-zero Arena upper endpoint should not carry a binary significance conclusion with only 300 descriptive replicates.
- **Trust assessment:** high for supplied numerical witnesses and summary alignment; conditional for final package/compute disclosure; deliberately bounded for novelty, legal compliance, and planning chronology.
