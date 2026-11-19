# Self-Review

Draft: `/work/paper.tex`, with `/work/paper/appendix.tex`; compiled `/work/paper.pdf` and `/work/artifacts/paper_extracted.txt` (15 pages: main 1–7, impact/references 8, appendix 9–15).
Output: `/work/artifacts/paper_review.md`.

Review boundary: local draft, numerical artifacts, analysis code, and tests only. No network, literature discovery, source-collection reading, identification of excluded work, or source edits. Pass 1 was completed and its suspicions recorded before loading the review checklist. No code-interpreter tool was available; Pass 2 therefore used the skill's sequential five-aspect fallback, not parallel sub-reviewers. Pass 3 used local Python/shell scans. Findings distinguish verified defects from judgments and untested robustness.

## Verdict

**Reject-first simulation:** A selective-venue reviewer could reject this as an elementary optimization exercise on two historical score matrices: independent upward score edits are not demonstrated developer actions, endpoint monotonicity and threshold counting are straightforward, and the main reversal is conditional on a selected feasible cohort. The present package also contains a visible author-template error and lacks a clean installation/reviewer-release entry point. None of the numerical care alone establishes sufficient novelty, practical impact, or acceptance-level significance.

**Verdict: needs-work.** The central snapshot results survive this audit. I found no contradiction in the stated support theorems, magnitude/strictness exceptions, or highlighted numerical results. The paper correctly disclaims real training, resource-cost, causal contamination, and universal aggregator-ranking claims. Four concrete submission blockers are listed below; broader contribution strength remains a separate acceptance risk after those repairs. This is not a prediction of acceptance.

### Verified headline quantities

Fresh calculations used saved target-level CSVs, not just the summary JSON. Values below match the prose and generated tables.

| Claim / source locator | Recomputed evidence | Assessment |
|---|---|---|
| Dimensions; abstract and §5.1 | HELM 79 × 57; Open Raw 4,576 × 6; audit reports no primary exclusions | Supported |
| Table 1, `/work/paper.tex:140–145` | At rho=.5, feasible mean/median/Borda: HELM 40/41/33; Open 4030/2927/1960. At rho=.25, Open mean/median 573/30. Full-headroom shared first: all targets feasible | Supported |
| Full-cap within-rule median counts, §6.1 | HELM 16/21/46; Open 2/3/6, mean/median/Borda respectively | Supported; these are medians, not Table 2's means |
| Fixed cohorts, `/work/paper.tex:163–165` | Exact saved IDs reproduce N=31 and 1839. Mean differences Kmed−Kmean: HELM −13.129032 → +2.645161; Open −0.380642 → +0.953235 | Supported as cohort averages |
| Individual reversals, same paragraph | 25 HELM and 724 Open targets have strictly negative differences at .5 and strictly positive differences at 1 | Supported; not all cohort members |
| Pair-only check, same paragraph | N=37 and 2926; differences −15.027027 → +3.027027 and −0.573821 → +0.855092 | Supported; does not require Borda feasibility |
| Table 2 descriptive intervals | Independently reconstructed contrasts and reran the documented bootstrap; all four interval endpoints match saved values within 1.2e−16 | Computation supported; interpretation caveat F6 |
| Magnitude, `/work/paper.tex:176,181` | Independent mean-deficit and cheapest-median-crossing formulas: averages .1456149917956006 and .03439489955145626 over 77 common cardinal nonwinners. All 77 favor median magnitude; 64 have larger median support | Supported; saved L1_min agrees within 5e−16, not confused with witness_L1 |
| Heuristics, `/work/paper.tex:186` | Half-cap headroom excess 6.121212 / .320918 and random excess 8.191919 / .490476, HELM/Open | Supported |
| Ties/scales/rosters, `/work/paper.tex:188–190` | HELM finite median/Borda changes 18/3; Open Borda feasibility/finite-support changes 1/4. Normalized feasibility 4424/3429/1969. Lower/upper median 4163/780. Dedup/availability Borda feasibility changes 3/45 | Supported; feasibility and finite-support changes are distinct |
| Validation, `/work/paper.tex:136`; appendix C.2 | Six results CSVs contain exactly 128,915 rows. All 238 positive HELM Borda rows have saved zero gap and agreeing dual bound | Counts and recorded diagnostics verified; not formal certificates |
| Tests | Saved log: five passed. Fresh `OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m pytest /work/tests -q -p no:cacheprovider`: **5 passed in 28.10 s** | Supported |

The original full validator was inspected, not rerun end-to-end in this review. Its saved all-checks-passed flag and tolerance reruns are recorded evidence, not a claim of a fresh independent audit of every row. Fresh checks included cohort reconstruction, headline summaries, all HELM full-cap cardinal magnitude formulas, exact synthetic enumeration, bootstrap regeneration, hashes, and tests.

## Pass-1 Suspicions

“Open” includes calibrated judgments and unresolved verification boundaries, not only proven defects. **Seven remain open.**

| ID | Original suspicion and location | Confidence | Evidence that would settle it / later result | Status |
|---|---|---|---|---|
| S1 | Technical contribution may be too elementary for the intended venue (§1, §4, §7) | Medium, judgment | Independent domain assessment of the mechanism and its decision value; no forbidden literature comparison. Proof correctness does not settle significance | **Open**, F10 |
| S2 | Cohort selection or averaging may manufacture the reversal (§5.2, §6.2) | Medium initially | Reconstructed exact IDs, pair-only cohorts, all-target feasibility, and 25/724 individual reversals. These support the stated conditional finding, not population generality | Resolved within scope; abstract precision repair F2 |
| S3 | 64/77 could use endpoint magnitudes instead of minima (§6.3) | Medium initially | Independently recomputed exact-formula cardinal minima from HELM matrix and checked saved L1_min | Resolved |
| S4 | Strict candidates, baseline winners, unattained infima, or even-median exclusions may be mishandled (§4.2; appendix A) | Medium initially | Clean proofs explicitly cover these branches; checked boundary examples and continuity argument | Resolved in stated mathematical scope |
| S5 | 128,915/238/five test groups may overstate validation (§5.3) | Medium initially | CSV counts, validator code, bounds, saved logs, and fresh five-test run agree. Validation is numerical and support/witness-focused, as disclosed | Resolved as stated; regression-coverage recommendation F5 |
| S6 | Bootstrap intervals may imply uncertainty that a fixed, correlated roster does not support (§5.2; Table 2) | High interpretive risk | An explicit resampling interpretation or removal of intervals. Arithmetic alone does not settle coverage | **Open**, F6 |
| S7 | Precision sensitivity and task deletion may be incomplete (§6.4; appendix C.3) | High | A declared rounding/measurement perturbation analysis and broader deletion coverage, or explicit restriction to unperturbed tables. Current parity/empty-cohort caveats are honest | **Open**, F7 |
| S8 | “Complete commands” may not constitute a clean reproducible package (§5.3; appendix C.4) | High | README, install specification, TeX/system prerequisites, portable entry point, and accessible reviewer bundle | **Open**, F4 |
| S9 | AUTHORERR and pinned-hash overflow may survive compilation (PDF pp.1,3) | High | PDF and final log confirm both; a corrected rebuild would settle them | **Open**, F1/F8 |
| S10 | “Tractable” may exceed endpoint reduction and numerical evidence (conclusion) | High | General complexity proof or narrower wording. The covering formulation alone gives no general efficiency guarantee | **Open**, F3 |
| S11 | Four matrices or unique-first claims may not match exact certificates (appendix B) | Medium initially | Fresh Fraction enumeration reproduces every support triple under both conventions | Resolved |
| S12 | Citation/source-access assertions cannot be certified inside this restricted review (§2; appendix D) | High verification boundary | Authorized provenance assessment without source expansion. This review checks only internal citation resolution and does not certify previous access behavior or comprehensive novelty | **Open**, scope boundary, not an allegation |

## 5-Aspect Findings

### Contribution — 2/5

**F10 — Medium, residual acceptance risk: correctness is stronger than the present significance case.** Locators: `/work/paper.tex:40`, §§4 and 7. A capable researcher could plausibly derive endpoint monotonicity and odd-median crossings quickly. The stronger paper-level knowledge is their combined consequence: feasibility-aware, fixed-cohort ceiling reversal and disagreement between count and magnitude. This is a judgment about depth, not a claim of duplication by any unexamined paper.

Minimal repair: foreground that narrow explanatory contribution and state what a benchmark designer would learn or decide from the profile. Do not substitute “first,” “novel,” or stronger strategic-training claims for evidence. An independent assessment of venue fit remains necessary even after copyediting. New training is not required to validate the paper's deliberately structural estimand.

### Clarity — 4/5

**F1 — High, submission blocker: visible template error.** `/work/paper.tex:19–26`; PDF p.1, printed lines 049–051: `AUTHORERR: Missing \\icmlcorrespondingauthor.` Compilation success is not a clean PDF. Minimal repair: satisfy the local template's anonymous corresponding-author configuration without inserting identifying information; rebuild and inspect the first page.

**F2 — Medium, claim-precision blocker: abstract suppresses the averaging qualifier.** `/work/paper.tex:28` says median “needs fewer edits ... but more” on fixed cohorts. In the 1,839-target Open cohort at half headroom, only 790 favor median, 958 tie, and 91 favor mean; 724 strictly reverse across caps. Minimal replacement: **“For shared first, median needs fewer edits on average at half headroom but more on average at full headroom on fixed jointly feasible nonwinner cohorts.”** The body already supports this wording. This is not a numerical correction.

Reverse outline: motivation → why median intuition is incomplete → fixed-row estimand → training boundary → contributions; definitions → endpoint reduction → cardinal solutions → Borda coupling; data/protocol → all-target feasibility → fixed-cohort reversal → independent magnitude contrast → sensitivities. This order is coherent. The extensive internal-process/source-policy disclosures interrupt the scientific story somewhat, but no reorganization is required to repair a hidden logical gap.

### Results — 4/5

Headline quantities and plotted estimands match saved evidence. Conditional comparisons are paired fairly; the all-target curves prevent silently treating infeasibility as a finite cost. The fixed cohorts are only **39.24% of HELM** and **40.19% of Open** rosters, so their mean contrasts must not be read as roster-wide statements. The paper already recognizes this distinction.

**F6 — Medium, nonblocking interpretation risk: a bootstrap resampling model is not a population uncertainty model.** `/work/paper.tex:131,158`; `/work/paper/appendix.tex:323`; `/work/code/summarize.py:12–20`. The fixed-cohort statistic is known, while resampling target effects treats their empirical distribution as a draw distribution. Holding competitors fixed is appropriate for that calculation, but does not address correlated submissions or establish any frequentist coverage for the observed roster. Current disclaimers substantially mitigate this. Minimal repair: label these **“empirical target-resampling intervals (descriptive; no population-coverage claim)”**, or remove the interval column and retain exact paired sign counts. Do not add training seeds or hypothesis tests merely to satisfy a generic checklist.

### Testing — 3/5

**F5 — Medium, recommended regression repair: the magnitude headline lacks dedicated automated magnitude tests.** `/work/tests/test_optimize.py:15–34` compares K; the remaining tests cover ranks, support, saturation, and monotonicity. `/work/code/validate.py:25–49` checks endpoint witness_L1, not optimal L1_min or L1_attained. `/work/code/optimize.py:98–101` produces the headline magnitude fields. This review's independent formulas validate the current 64/77 result, so this is not evidence that it is wrong. Minimal repair: add independent mean/odd-median magnitude tests covering baseline winners, infeasibility, ceiling equality, zero crossing deficits under strict first, and attainment flags; add a saved-data regression for 77/64. Do not infer optimized even-median/Borda magnitude from endpoint costs.

**F7 — Medium, residual robustness gap, not a falsification:** `/work/paper.tex:136,197–199`; `/work/paper/appendix.tex:334–338`. Tolerance reruns are not score-rounding or measurement-uncertainty experiments. No such perturbation result is supplied. The task diagnostic uses 12 targets per panel, HELM deletes pairs rather than single subjects, and Open changes median parity. Saved Open half-cap panels deleting MATH Lvl 5 or MUSR have empty common cohorts; GPQA deletion has one target and contrast zero. Minimal repair if doing no more experiments: explicitly say **no score-rounding perturbation study was performed**, and preserve the existing diagnostic-only wording. A broader robustness claim would require new declared local experiments, not a new interpretation of these intervals. Those experiments were not run in this review.

No trained-model/SOTA baseline is required for the stated task. The available comparator rules, exact support reference, headroom/random heuristics, ceiling variation, pair-only cohorts, tie conventions, and roster/scale sensitivities test the central structural story. They do not establish application-level training benefit.

### Method — 4/5

**F3 — Medium, claim-precision blocker: the conclusion overstates computational delivery.** `/work/paper.tex:202`: “A monotone endpoint reduction makes minimum task count tractable, but not minimum magnitude.” Endpoint reduction leaves a binary covering/subset problem for Borda; the paper does not prove polynomial-time tractability. Moreover mean and odd-median magnitude are explicitly solved earlier. Minimal replacement: **“Endpoint reduction turns minimum task count into finite subset selection; minimum magnitude is a separate optimization.”** If desired, add “Our evaluated panels admit enumeration, analytic solutions, or numerically certified MILP optima,” preserving the numerical qualification.

Mathematical support audit:

- Endpoint proof preserves actual support by excluding zero-headroom coordinates, applies to both winner conventions, and correctly updates rival Borda points.
- Mean capacity prefixes and attained shared magnitude handle zero edits and infeasibility. Strict feasible magnitude from a non-strict baseline is an unattained infimum.
- Odd median uses r=max(0,h−q); strict first recomputes both q and eligible crossings. Cheapest boundary deficits are valid only on the feasible branch. The plateau holds only on the feasible ceiling domain for fixed target/rivals/panel/convention.
- Conventional even medians are monotone and continuous, but not covered by the odd crossing formula. Six-task support enumeration is valid; no even-median magnitude theorem is claimed.
- Borda gain-plus-rival-loss covering and the Bmax−2n pruning argument are sound. Integer strict margins are appropriate for doubled points. The appendix correctly supplies both an attained strict Borda magnitude example and an unattained shared one; continuous-cardinal nonattainment cannot be transferred to Borda.
- Fresh exact enumeration gives shared triples A=(2,2,3), B=(2,3,2), C=(3,3,2), D=(2,1,2); unique triples A=(2,3,3), B=(2,3,2), C=(3,3,3), D=(2,2,2). Four matrices cover six ordered-pair shared-first inequalities. They do not establish unique-first non-ordering, exactly as disclosed.

## Protocol Audit & Mechanical Scans

### Data flow, assumptions, fairness, and information availability

Reconstructed flow: pinned public score exports → complete finite bounded matrices and stable row IDs → fixed-rival target optimization for declared ceilings/rules/winner conventions → saved support/magnitude/witness diagnostics → explicitly saved cohort IDs → paired summaries, descriptive resampling, and figures. There is **no training, inference, fitted response model, or train/test split** in this study. Released evaluation scores are inputs to an ex-post diagnostic; optimizing on them is not covert evidence of held-out improvement. It would be invalid to reinterpret this as a generalization or training-resource experiment, and the text does not do so.

Assumptions checked against downstream discussion: independent upward edits/no regressions; perfect-score endpoint; equal task weights and equal edit costs; fixed task panels/rivals; complete data; exact ordering of stored float scores; shared versus unique winners; finite cohorts and correlated configurations. §§3, 5, and 7 revisit these assumptions. No one-time hidden deployment-information assumption was found. The score oracle is explicitly hypothetical, not an executable training policy.

Comparison audit: rules share the same matrices, ceilings, task weights, and winning convention in primary comparisons. Borda rivals are recomputed. Conditional nonwinner exclusions and exact half-cap cohort freezing reproduce from code. Pair-only cohorts address the Borda-selection objection. Scale/roster variants change the estimand, and the text says so. The half-cap choice is described as frozen, but these local files alone do not establish independent preregistration; do not turn that wording into a prospective-confirmation claim.

### Concrete audit findings (nine; also counted in metadata)

| Audit ID | Severity / finding | Concrete locator | Minimal repair |
|---|---|---|---|
| P1 / F1 | High: printed AUTHORERR | PDF p.1; main :19–26 | Correct anonymous template configuration and inspect rebuilt PDF |
| P2 / F2 | Medium: missing “on average” and primary winner convention in headline | Main :28; fixed_cohort.csv, Open triple rho=.5 | Add average/shared-first qualifiers |
| P3 / F3 | Medium: unsupported general tractability implication | Main :202; optimize.py :60–66 | Replace with finite subset selection; separate magnitude optimization |
| P4 / F4 | Medium: reproduction entry point incomplete | Main :136; appendix :340–366 | Add install/run/reviewer-bundle documentation, including system dependencies |
| P5 / F5 | Medium: magnitude fields not regression-tested/independently validated in supplied validator | Tests :15–56; validate.py :25–49 | Add dedicated magnitude/attainment and saved-headline checks |
| P6 / F6 | Medium: resampling coverage interpretation remains vulnerable | Main :131,158; appendix :323 | Empirical-resampling label or omit intervals |
| P7 / F7 | Medium: precision robustness untested; deletion scope limited | Main :136,197–199; appendix :334–338 | Explicitly name unrun perturbation analysis; retain limited-scope language |
| P8 / F8 | Low: overfull pinned revision string | Main :122; final paper.log :654–655, 5.8225 pt overflow | Use a breakable path or explicit safe line break, as in appendix |
| P9 / F9 | Low: figure/table navigation and display polish | PDF p.6 Fig.2; plot.py :47; appendix :327–332 | Move legend off Borda line; add label and explicit text reference for sensitivity Table 5 |

**F4 detail:** No project README, dependency-install file, project code-license file, or reviewer-release link is supplied in the inspected package. The appendix supplies installed Python-package versions and commands for an already prepared `/work` environment, but not its setup. `code/plot.py:13` requires external LaTeX/fonts (`text.usetex=True`); this is not captured by Python versions alone. Main :136's “complete commands” is too generous for a clean machine. Minimal repair: a short reproduction README, environment/install specification, TeX/font/build prerequisites, expected output map/timing pointers, portable repository-root instructions, and an anonymous reviewer bundle or persistent release when appropriate. The data-license ambiguity is explicitly disclosed; public accessibility must not be rebranded as permission. Author-controlled code licensing can be documented separately. All explicitly referenced local paths do exist; missing documentation is not missing score data.

### Mechanical coverage and figure/table checks

- **Promise–delivery:** estimand → §3/appendix A; support/plateau/Borda → §4/appendix A; fixed-cohort and metric reversals → §6; non-ordering → appendix B; each is echoed in §8. No promised training experiment silently disappears. F3 is the conclusion's overstatement, not a missing proof of the actual support characterization.
- **Claimed-but-missing comparisons:** no method is declared a directly comparable SOTA algorithm and then omitted. Related-work conceptual framing is not a claim of empirical superiority. External citation-content/priority verification was deliberately not attempted.
- **Citations/refs/markers:** 44 distinct labels; no duplicate labels or unresolved ref/eqref targets. All six used citation keys have bibliography entries. No TODO/FIXME/TBD or unresolved `??` markers found in main, appendix, generated tables, or bibliography. Final `paper.log` has no undefined citation/reference warning; first-pass warnings in the aggregated build log are not final defects.
- **Page/layout:** actual final PDF has 15 pages, as supplied. Main ends on p.7, impact/references occupy p.8, appendix pp.9–15. Current venue page-limit/policy compliance was not externally rechecked. No author-identity leak was observed in the inspected manuscript, but F1 must be repaired without compromising anonymity.
- **Tables:** all five captions are above booktabs tables; no vertical rules or falsely bolded best entries. No single “best aggregator” direction exists here, so winner-highlighting/arrows would be misleading. Feasibility counts, count means, within-rule count medians, and normalized paired differences are distinguished correctly. Sensitivity Table 5 lacks its own label/direct text callout (F9), although appendix C.3 is referenced.
- **Figures:** three vector-PDF figures are present and text-referenced. Axes, cohorts, winner convention, units, and endpoint line-segment interpretation agree with saved calculations and plotting code. Blue/vermilion/green is not a red–green-only scheme; grayscale line styles could still be improved. Figure 2's legend crosses the upper Borda series in the Open panel (F9). Figure 3 has overplotting, but its count claim is established by CSVs, not visually counting dots. A pipeline diagram or SOTA teaser is not necessary for this diagnostic paper.
- **Hashes/data QC:** freshly computed SHA-256 values for contents.parquet and helm_summary.json exactly match appendix C.1. Saved audit quantities agree with prose: 54 duplicate Open score rows, one flag, 1683 unavailable rows, zero HELM duplicates, normalized-average reconstruction error 1.6653345369377348e−16. Raw fractions are not divided by 100; only normalized percentages are.
- **Compute:** timing_all.json records 104.56 s analysis wall time; saved validation summary records 147.95 s, separately. Do not imply these include every task diagnostic, plotting step, dependency setup, or PDF build. CPU-only numerical analysis is consistent with inspected code.

### Counterintuitive protocol and trust/claims audit

- Reject-first paragraph appears before favorable conclusions above.
- **Delete/rewrite unsupported strength:** replace the general “tractable ... but not magnitude” sentence (F3); no source was edited during review.
- **Promote a meaningful limitation:** state the lack of a rounding/measurement perturbation study explicitly. Keep the already-prominent score-to-training boundary; do not hide it in the appendix.
- **Attack novelty:** retain the finite-table mechanism and diagnostic contribution, not priority rhetoric (F10). Restricted-source disclosure does not settle novelty in either direction.
- **Trust scorecard, 0–2 each:** comparison fairness 2; reproducibility 1; honest limitations 2; failure transparency 2; statistical interpretation 1. **8/10.** This is an internal trust score, not acceptance probability.
- **Abstract/introduction claims:** bounded score edits, endpoint support reduction, odd crossings, rival-aware Borda, table dimensions, conditional reversal, and 64/77 are supported. The headline needs averaging/convention precision; practical training efficacy and universal superiority are explicitly disclaimed. No evidence that more than 20% of front-matter claims are unsupported. Generic SOTA-significance thresholds are inapplicable to an exact fixed-table diagnostic.

## Blocking Issues

Four specific repairs should precede submission; none requires web access, excluded-source identification, or new training.

1. **B1 / F1 — High:** remove the literal AUTHORERR from the anonymous PDF and inspect the rebuilt front matter.
2. **B2 / F2 — Medium:** qualify the abstract's fixed-cohort reversal as an **on-average, shared-first** result; preserve the distinction from 25/724 individual reversals.
3. **B3 / F3 — Medium:** replace the unsupported general tractability/“not magnitude” sentence with the finite-subset-selection statement.
4. **B4 / F4 — Medium:** supply a clean-environment reproduction entry point and accessible reviewer package; document Python and external TeX requirements, execution order, and code/data release status separately.

F5–F9 are recommended hardening/polish, not evidence that the main quantities are false. F10 remains a substantive venue-risk question even if every blocking repair is completed. A realistic selective-venue acceptance standard is a defensible non-obvious insight with sufficient reader value, independently inspectable evidence, precise scope, and credible reproducibility—not merely passing tests or removing LaTeX errors.

## Prebuttal Notes

- **“This is not a training attack.”** Agree: the estimand is an ex-post score-table diagnostic; no efficacy, resource conversion, or contamination inference is established. Do not invent such a defense.
- **“The reversal is survivor bias.”** Exact target IDs are held fixed across caps, pair-only cohorts also reverse, individual reversals are saved, and all-target curves disclose feasibility. This answers changing-composition objections, not generalization beyond the conditional cohorts.
- **“Median is therefore always easier/harder.”** No: ceiling, winner convention, and cost metric matter; synthetic non-ordering covers shared first only.
- **“64/77 used the wrong cost.”** Independent threshold-deficit formulas reproduce optimal cardinal L1_min; endpoint witness_L1 is a different field. Strict-first infima and Borda magnitude are not used for this headline.
- **“The error bars prove significance.”** They do not. They are empirical target-resampling summaries with fixed competitors; finite-roster effects are already known exactly and correlated submissions prevent naïve population inference.
- **“The solver output is a formal proof.”** No: matching numerical bounds and full-rival witnesses support the empirical Borda optima; separate rational certificates establish the synthetic examples.
- **“The task ablation establishes general robustness.”** It does not: HELM single deletion is unrun, parity differs, cohorts can be empty or tiny, and precision perturbation is untested.
- **“Novelty is limited / literature is incomplete.”** Concede the access boundary, explain the narrow combined mechanism and its use, and seek an independent venue-fit judgment within authorized constraints. Do not infer, identify, or characterize prohibited material.
