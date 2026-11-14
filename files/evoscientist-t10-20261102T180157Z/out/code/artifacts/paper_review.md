# Self-Review

Draft: `/work/paper.tex`  
Compiled manuscript: `/work/paper.pdf`  
Review artifact: `/work/artifacts/paper_review.md`  
Review date: 2026-11-02 UTC

## Verdict

**Major rework for the contribution argument; no fatal mathematical or statistical implementation error found in the audited setting.** This is a credible, unusually transparent, guarantee-aware audit, but its technical ingredients are elementary specializations of established tools and its practical gains occur in deliberately favorable simulations, not the two empirical distributions. That is a significance/novelty concern, not evidence that its theorems are false. Fixing the two blocking items below would not by itself establish ICML acceptance readiness.

The exact random-stratum Clopper–Pearson (CP) construction is sound, including its pooled score-mass dependence. The oracle projection is correctly restricted to the displayed score-control estimator class; it is not global confidence-interval optimality. All **26 numeric macros, 442 summary rows, 1,768 paired comparisons, 442 full-results table rows, 14 main-table rows, and 20 ablation rows** checked against their sources. The 884,000 raw interval records pass endpoint, containment, and replicate-key checks. All seven existing tests pass. A sampled deterministic replay of 96 datasets matches 1,326 saved endpoint triples. These checks support the reported audit, not uniform empirical certification of coverage.

**Two unresolved blocking corrections:** (B1) the threshold-feature necessity claim is not supported by the confounded ablation; (B2) Tables 1–3 put captions below tables, contrary to the supplied ICML template. Other actionable, nonfatal findings concern covariance-normalization wording, figure/source synchronization, font-format clarification, missing cross-references, numerical p-value underflow, and limits of freeze-timing evidence.

**Execution and restrictions.** Pass 1 was completed and its suspicions recorded before loading `five_aspect_review.js`. The required code interpreter/task-dispatch interface is unavailable; the script was subsequently read, and all five aspects were completed using the expressly permitted sequential fallback. No aspect is missing. Pass 3 was independently executed with local shell Python, not assumed covered by the script. No network, topic search, new literature, citation chasing, or inference about the unidentified prohibited work was used. Only existing local materials were inspected. No manuscript, method, analysis, or plotting source was changed; the only delivered file is this review.

### Reject-first simulation

I would reject a broad methods submission because the projection identity, low-dimensional cross-fitting, CP-plus-union-bound stratification, and simultaneous Bernstein selection do not yet constitute a strong new technical advance. The synthetic mechanisms deliberately align with the chosen basis; the empirical studies show no rich-basis width improvement; normal-based gains do not meet a strict finite-sample requirement. The valid stratified gain is real but demonstrated against a specified labeled CP comparator, not against the strongest available finite-sample inference. The paper largely admits these points, so the proper objection is limited new knowledge and external relevance—not a fabricated coverage or leakage failure.

## Pass-1 Suspicions

These are the independently raised doubts, carried forward rather than replaced by the checklist. “Resolved” means the suspected defect was explained, not that every research limitation disappeared. Five remain open: S0, S4, S8, S9, S10.

| ID | Location and initial suspicion | Confidence after audit | Evidence that would settle it; disposition |
|---|---|---|---|
| S0 | `paper.tex:43`, Proposition 1, §6: elementary results may not support the contribution level. | High as a venue-strength judgment; priority unassessed. | A precise new-knowledge argument beyond familiar projection/cross-fitting/concentration, or stronger independent empirical relevance. **Open: significance limitation**, not a correctness error. Local PPI++ §6 already discusses a conditional-expectation variance bound. |
| S1 | §4.2/Theorem 1, Appendix A.3: pooling labeled memberships into the mass interval could invalidate a proof relying on independence. | High. | Conditional CP coverage for each random stratum, marginal CP coverage for pooled mass, then a union bound. Present in the text and implemented correctly. **Resolved.** |
| S2 | §4.1/Appendix A.2: overlapping fits, reused unlabeled observations, or ridge scaling might invalidate inference. | High for the stated regular asymptotic regime. | Direct code/proof comparison and variance tests. `methods.py:35–57` uses the stated vanishing ridge, index folds, held-out residuals, and variance of the weighted average control. **Resolved**, subject to stated iid/nondegeneracy assumptions, not finite-sample validity. |
| S3 | §5.1/Appendix B: the stratified replay could use different observations despite sharing a seed. | High for source-level alignment and sampled replay. | Same RNG initialization and call order, plus output replay. All methods share one input call; both runners match structurally. First three repetitions of every cell reproduce saved endpoints. **Resolved within this evidence scope**; no saved sampling IDs or full 64,000-dataset replay is claimed. |
| S4 | Abstract/§5/numeric macros: savings, family counts, or extreme p-values might be wrong. | High. | Raw-data recalculation clears every macro, table, paired SE, and rejection count. However, 14 asymptotic and two oracle p-values and adjusted p-values are exported as zero through floating-point underflow. **Open: audit-output precision**, not a headline-number failure. |
| S5 | §2/§5.3/§6: gains against conservative comparators might be generalized to all finite-sample methods. | High. | Explicit scope and baseline disclosure. The missing betting-style MeanCI is already acknowledged; comparisons are explicitly recipe-specific. **Resolved as an overclaim concern**; stronger-baseline completeness remains an honest limitation. |
| S6 | §3/§6: oracle score efficiency might be presented as optimal confidence intervals. | High. | Check quantifiers and conclusion. Optimization is explicitly within Equation (1), with no minimax/admissibility/global-length claim. **Resolved.** |
| S7 | §2/§5.4/references: unrestricted PPI++ might be conflated with its clipped package implementation or citations misattributed. | High for checked claims and metadata. | Local source text, bibliography, package test, and code. The two baselines remain distinct; six citation keys resolve. **Resolved**, without certifying unrestricted literature priority. |
| S8 | `paper.tex:161`, Appendix B: freeze timing might be asserted more strongly than the artifacts establish. | Medium. | All five files in `prerun_sha256.json` match current bytes; amendment files exist. Independent timestamped evidence would establish chronology. **Open: provenance boundary**; nothing inspected establishes misconduct or post-result tuning. |
| S9 | Figures 1–3/Tables 1–4: presentation and source traceability might be incomplete. | High. | Visual PDF inspection, source scans, and in-memory source rendering. Captions for Tables 1–3 are below; several objects lack explicit references; current Figure 1 rendering differs in legend placement from the saved asset. **Open: confirmed presentation/synchronization issues.** |
| S10 | Appendix B/PDF: page/style claim or compiled artifact might fail submission checks. | High for page/style facts; medium for font-policy interpretation. | PDF has 19 pages; body/impact end on p.7, references start p.7, appendix starts p.8. Official style files match the local archive. Figures introduce embedded Type0 fonts despite literal Type1-only wording in the template. **Open only for formatting clarification**; no page-limit breach found. |

## 5-Aspect Findings

### Contribution sufficiency — 2/5

- **Central weakness:** `paper.tex:43`, §§3–4 and §6 offer a scoped synthesis/audit rather than a clearly new method or difficult theorem. The restricted-source protocol cannot establish priority, and the manuscript correctly says so. The local PPI++ source, §6.1–6.2 (PDF pp.10–12), already supplies the scalar optimum and a conditional-expectation efficiency bound; replacing full features by the frozen score yields a closely related specialization. The finite-n identity and explicit residual gap are useful exposition, but cannot carry the novelty argument alone.
- The elementary exact comparator is correct and useful; neither random-count CP conditioning nor the union bound should be sold as a new general stratification principle. The paper currently avoids that error.
- The likely additional value is a reproducible, guarantee-aware negative-result study. Sharpen which common decision it changes and for whom. More independently chosen populations or a stronger audit question would strengthen significance; simply adding grander claims would weaken trust.
- The missing stronger finite-sample betting baseline is **already disclosed** in §2 and §6. It limits comparative completeness, not the validity of results for tested recipes. No unrun benchmark performance is inferred here.

### Writing clarity — 3/5

**Reverse outline.** Introduction paragraphs progress from exhausted data budgets → three distinct guarantees → fixed-input/score-transformation scope → three contributions. Method progresses from oracle diagnostic → attainable cross-fit approximation → exact binary protection → simultaneous bounded selection. Experiments progress from frozen sampling/uncertainty → asymptotic efficiency and failures → valid finite-sample comparisons → ablations and implementation checks. This is coherent; the conclusion returns to the same distinctions. No promised contribution disappears.

Actionable issues:

1. **Unsupported necessity wording:** `paper.tex:204`, §5.4, “the threshold feature is needed for the step mechanism.” See B1. Prefer “the rich basis contains the threshold feature and exactly represents the step conditional mean”; do not attribute the measured incremental gain to an isolated component that was not isolated.
2. **Normalization wording differs from code:** `paper.tex:286` says all sample variances/covariances except the package baseline use denominator n−1. Ridge fitting instead divides both centered Gram and cross-moment matrices by training sample size (`methods.py:39–40`). Narrow the statement to interval variance estimates/scalar tuning and explicitly state the ridge-fit convention. This does not invalidate the theorem or reported numbers.
3. `paper.tex:289`, “No training ... was necessary,” should say **no underlying-predictor retraining**. Nuisance regressions are fitted throughout §4.1.
4. Add an explicit reference to Figure 2 (`fig:validity`) and Table 2 (`tab:exact`); label and reference the ablation table, heatmap, and complete-results table. Referring to Appendix C helps, but does not replace object-level navigation.
5. Separate operational access/failure logs from the scientific story where possible. They support reproducibility, but are not additional evidence of scientific novelty.

**Counterintuitive protocol:** reject-first paragraph appears above. The strong statement to delete/narrow is the threshold necessity claim; no edit was silently made. Promote the already-disclosed betting-baseline limitation into the finite-tier result paragraph rather than leaving it only in related work/discussion. Trust the reproducibility more strongly than broad superiority. Attack novelty as above, rather than strengthening its adjectives.

### Experimental results quality — 4/5

**Headlines are numerically trustworthy, but must retain their validity qualifications.**

| Headline / source | Audited value | Interpretation |
|---|---:|---|
| Quadratic, n=2000, CF-rich/PPI++ | ratio 0.8203; 18.0% saving | Substantial within this basis-aligned mechanism; normal-based. |
| Step, n=2000, CF-rich/PPI++ | ratio 0.6070; 39.3% saving | Coverage 0.9355, Wilson [0.9239, 0.9455]; not a matched-validity superiority result. |
| Step coverage warning | one-sided p=0.0023948; Holm p=0.4693801 | Unadjusted warning, not familywise rejection; manuscript accurately distinguishes these. |
| Rare, n=30, CF-rich | coverage 0.2645, Wilson [0.2456, 0.2843] | Genuine failure of this normal recipe; cross-fitting does not protect against unseen rare successes. |
| Step, n=2000, stratified CP/labeled CP | ratio 0.7222, paired SE 0.0008 | 27.8% saving; MC savings interval [27.63%, 27.93%]. Both recipes have analytical guarantees. |
| Same exact comparison | widths 0.03198 vs 0.04429 | Coverage 1.0000 for stratified CP; theorem, not observed coverage, provides validity. |
| Galaxies/forest, n=2000, CF-rich | 0.65% / 0.36% wider | Empirical non-gains, not proof that every nonlinear score procedure must fail. |
| EB selection, step n=2000 | 5.86% below labeled EB; 1.625× labeled CP width | Failure of practical efficiency relative to an alternative valid recipe, not a coverage failure. |

Exact stratification improves against labeled CP in precisely three cells: step at n=100,500,2000, all N/n=10. EB selection improves against labeled EB in precisely one cell: step at n=2000. These checks support the prose's negative conclusions.

**Trust assessment:** high for numerical traceability and mechanism-level evidence; moderate for asymptotic interpretation; limited for deployment/generalization. Tiny MC standard errors quantify repeated-sampling computation under the specified laws, not uncertainty over selecting scientific populations or feature families.

**Figure/table inspection:** Figures 1–2 are legible vector graphics and distinguish the reference ratios; no pipeline illustration is necessary for this audit paper. Figure 1's seven series all use the same marker/line style, so color-independent identification could improve despite the sensible palette. Its saved legend occupies the upper-right panel and can crowd curves. Figure 3 is informative but dense at print size; its 0.94/0.95 rounding should not decide validity, and its caption properly refers to full values. Tables use booktabs/no vertical rules. Avoid automatically bolding the narrowest interval across validity tiers: that would encourage the comparison error the paper critiques. Captions should state width's direction and coverage's nominal target rather than implying larger coverage is always better.

### Experimental testing completeness — 3/5

Strengths: 32 cells, 2,000 paired repetitions each, stress tests for rare events and sample ratios, known synthetic truths, two explicit empirical-distribution targets, scalar/polynomial/rich and unsafe in-sample controls, package endpoint checks, and exact enumeration at a small design. Negative results are retained. Additional arbitrary “seeds” are not automatically required: independent repetitions already address Monte Carlo noise under these laws.

Limitations:

- Mechanism tests are intentionally favorable to the fixed feature dictionary; two empirical distributions do not establish broad utility. More repetitions of these same cells cannot fix that external-validity limitation.
- **Component attribution is incomplete:** polynomial→rich adds both cubic and threshold. The current data establish a richer-basis effect, not threshold necessity. B1 can be fixed by narrowing prose; no new method implementation is required.
- Stronger finite-sample betting comparison is absent and explicitly disclosed. Keep conclusions conditional on implemented recipes. Do not fabricate a result, imply all valid PPI is Bernstein-based, or portray the omission as a hidden defect.
- The exact threshold and error allocation are fixed, not tuned. Absence of threshold optimization is honest scope, not a flaw requiring a post-result search.
- Tests establish useful identities and boundary examples, not distribution-free coverage by simulation. The general analytical proofs remain essential.

### Method design — 4/5

**Projection:** completion of the centered square proves the exact fixed-control variance identity. The residual projection variance gives the scalar excess and equality iff m(S) is affine when Var(S)>0. Constant-score and zero-outcome-variance cases are addressed. Optimization is over Equation (1), not every CI, every statistic of the full data, or all features X.

**Cross-fitting:** bounded fixed-dimensional features, positive-definite limiting covariance, observation-independent fixed folds, vanishing ridge, finite positive limiting n/N, and nondegenerate variance suffice for the stated pointwise CLT. A finite number of coefficient errors o_p(1) multiplied by score-mean differences O_p(n^−1/2) is negligible at first order; independence of those products is not needed. The shared-unlabeled variance is correctly computed as the variance of the average fold control. None of this makes the normal interval uniformly finite-sample valid, and the manuscript does not claim that.

**Exact CP and EB:** both constructions correctly budget simultaneous errors and retain score uncertainty. Selection among fixed EB controls is valid on the common simultaneous-coverage event. Known support ranges, rather than observed ranges, are used. Endpoint clipping preserves already-covered bounded means, including the documented collapse of disjoint raw intervals.

Practical assumptions are strong but visible: common iid score marginal, independent unlabeled sampling, external frozen predictor, binary labels for the CP implementation, and a partition/dictionary chosen independently of the observations. Label shift, dependent records, adaptive partitions, and predictor leakage require new justification; they are disclosed exclusions, not tested protections.

## Protocol Audit & Mechanical Scans

### Reconstructed data flow and fairness

1. **Synthetic laws:** `run_experiments.py:17–31,49–59` generates independent uniform labeled/unlabeled scores, then Bernoulli labels with the stated conditional means. Truth and moments agree with the formulas. Every procedure receives the same current arrays. Only the explicitly labeled oracle reference receives conditional means; ordinary methods do not.
2. **Empirical laws:** `run_experiments.py:44–54` loads fixed paired datasets, draws labeled and unlabeled indices independently with replacement, and supplies no unlabeled labels to inference. Truth is the full snapshot's label mean, evaluated outside fitting. Verified binary outcomes and score support [0,1]; snapshot sizes are 16,743 and 1,596, with means approximately 0.2592725 and 0.1516291. Repeated rows/overlapping source indices are compatible with this iid empirical-distribution target. They would require different reasoning for a without-replacement or original-population target, which is not claimed.
3. **Nuisance fitting:** `methods.py:35–57,80–87` uses only current labeled training folds; held-out rows provide corrections. Folds are index modulo five, not score-sorted. No hyperparameter search or new predictor call occurs. The unsafe in-sample comparator is separately labeled.
4. **Exact replay:** both runners use `SeedSequence([20261102, scenario_id, n, ratio])` and the same draw sequence. Ordinary inference functions consume no RNG. Supplementary records represent the same repeated-sampling datasets, not independent replication. Sampled replay reproduced the first three repetitions of every cell: 96 datasets, 1,326 interval triples, maximum endpoint/raw-width export difference 4.95×10^−12. All stored method/replicate keys are unique and complete. This is stronger than checking key alignment alone, but does not manufacture missing sampling IDs or constitute a full replay.
5. **Comparison budget:** inference inputs and label budgets match. Cross-fitting is allowed nuisance fitting under the paper's definition of a frozen predictor. Exact binary and Bernstein methods have distinct assumptions/guarantees from normal recipes, explicitly separated in the comparisons. No per-method runtime ranking is supportable: summary `seconds` is cumulative cell time. Whole-run timings 127.2 and 12.1 seconds match manifests.
6. **Freeze evidence:** all five current files match their prerun SHA-256 entries. The exact-addition amendment explicitly predates its declared inspection of full results. These are consistent local records, not an independently timestamped preregistration. No contrary statistical-code drift was found.

### Exact random-stratum theorem: dependence audit

Let A_i=1{S_i>1/2}, B_j=1{T_j>1/2}, p=P(A=1), and q_h=P(Y=1|A=h). Let E_h be coverage of q_h by its CP interval and E_p coverage of p by the pooled-membership interval.

- Conditional on the entire labeled membership vector, stratum h contains M_h fixed rows whose outcomes are independent Bernoulli(q_h). Thus P(E_h^c | A_1,…,A_n)≤α/3. For M_h=0, [0,1] has failure probability zero. Integrating gives P(E_h^c)≤α/3.
- The n+N memberships are iid Bernoulli(p) under the stated two-sample common-marginal design, so P(E_p^c)≤α/3. This is a **marginal**, not a claimed conditional guarantee after freezing the labeled memberships.
- Although E_p shares labeled scores with E_0 and E_1, P(E_p∩E_0∩E_1)≥1−α follows from the union bound. Independence is unnecessary.
- On this event, (1−p)q_0+pq_1 lies in the image of the rectangle. Nonnegative coefficients select the q endpoints, and affinity in p selects a mass endpoint. This is exactly `exact_stratified.py:13–22`.
- Zero population-mass strata can have arbitrary q_h; their target coefficient is zero. Boundary successes/failures and empty samples are handled by CP endpoint conventions.

**Assessment:** the dependence objection is cleared. This is an analytical argument, not a numerical coverage claim. It establishes neither uniform width improvement nor optimality of the rectangular region/error split. The existing n=6,N=8 enumeration is a numerical check only.

### Numeric and mechanical scan coverage

Executed local scans/recomputations, using `keep_default_na=False` for result CSVs:

- **884,000 raw records / 32 cells:** endpoints ordered and in [0,1]; recorded coverage agrees with containment; replicate/method keys unique and paired pivots complete.
- **442 summaries:** coverage, Wilson endpoints, mean widths, width SEs, raw widths, ratios and paired ratio SEs agree. Maximum absolute discrepancies from rounded raw exports: width 3.50×10^−13, raw width 1.42×10^−12, ratio 1.22×10^−11. These are not reproducibility failures.
- **1,768 paired comparisons:** independently reconstructed ratios, SEs and 95% MC endpoints match. These are ratios of mean widths, not means of individual ratios.
- **All 26 macros:** independently recomputed and matched `tables/numbers.tex`, including savings endpoints, empirical width increases, coverage intervals, family counts, interval count, and both timings.
- **Every table data row:** all 442 full-results, 14 main-results, and 20 ablation rows match their CSV values at displayed precision. Appendix Table 4's MC SE is specifically width SE (`analyze.py:79–82`); clarify the caption/header accordingly.
- **Log-space undercoverage screen:** recomputation from binomial log-PMF sums plus log-space Holm gives finite 0/160, asymptotic 59/256, oracle 6/26. Family totals sum to 442. Holm does not require independent method-cell tests. The paper correctly includes the unsafe in-sample control in the asymptotic family, and correctly distinguishes a warning from rejection/certification.
- **Promise→delivery:** contribution (i) → Proposition 1/Appendix A.1 → §6; (ii) → Figures 1–2/Tables 1–2 and full results → §6; (iii) → §4.2–4.3/Appendix A.3–A.4/§5.3 → §6. No disappearing contribution found.
- **Claimed comparisons:** unrestricted PPI++, clipped package recipe, labeled CP, EB, and oracle controls are present. Cross-PPI/DML/StratPPI are contextual sources with distinct training/allocation designs, not secretly copied benchmark numbers. The unimplemented betting baseline has an explicit explanation.
- **Citations:** all six cited keys resolve to six entries; no uncited entry, unresolved citation, or broken source cross-reference found. Authors/titles/years and relevant attribution agree with the local source materials, including PPI++ unrestricted mean tuning and the Bernstein Theorem 4 constants. The Bernstein two-sided radius correctly uses log(4/δ) after two one-sided applications. Bibliographic entries identify arXiv versions; this audit does not certify priority, exhaustive coverage, or current publication venues.
- **Markers/build:** no TODO/FIXME/TBD or unresolved LaTeX references found in paper, included tables, or bibliography. Build log has underfull boxes and benign hyperref warnings, but no overfull box or undefined citation/reference. No numerical conclusion rests on these warnings.
- **Pages/style/anonymity:** PDF is 19 pages, 363,231 bytes. Main text/impact fit by p.7; appendix begins p.8. `icml2026.sty`, `.bst`, `algorithm.sty`, `algorithmic.sty`, and `fancyhdr.sty` match the local official-template archive byte-for-byte. Anonymous author/PDF metadata contain no detected author identity. Impact statement is present. This verifies the local 2026 format, not an unavailable future venue policy or human submission approval.
- **Tests:** `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 python -m pytest /work/tests -q -p no:cacheprovider` → **7 passed**. Tests include package endpoints, projection identity, boundaries, reused-unlabeled covariance identity, synthetic moments, empty strata, and small exact enumeration.

### Eight deduplicated protocol/mechanical findings

| ID | Finding, location, confidence | Severity and action |
|---|---|---|
| P1 | **Confounded feature attribution:** `paper.tex:204`, `methods.py:82`, Table 3. Polynomial→rich adds cubic and threshold simultaneously. High confidence. | Scientific interpretation correction; B1. Narrow necessity wording rather than inventing an unrun ablation. |
| P2 | **Table captions below tables:** `paper.tex:170–176,191–197,295–299`; PDF pp.5,6,10. Local `template/example_paper.tex:158–160` explicitly requires captions over tables. High confidence. | Submission-format correction; B2. Table 4 already has its caption above. |
| P3 | **Figure-font policy needs reconciliation:** recursive PDF resource inspection finds embedded Type0 DejaVuSans fonts from figures, alongside Type1 text fonts. `plot.py:14` uses `pdf.fonttype=42`; local template lines 157 and 176–182 literally require Type1 fonts. High confidence in font facts; medium in current enforcement. | All fonts inspected are embedded and none are Type3. Do not call this a scientific defect or certain desk-rejection. Resolve against the applicable supplied-format requirement before submission. |
| P4 | **Figure 1 asset/source layout drift:** `plot.py:36` now puts a seven-column figure legend outside at the bottom; saved `figures/efficiency/plot.pdf` and manuscript p.5 retain an inside-right legend. High confidence, confirmed by in-memory rendering. | Non-numerical reproducibility defect. Synchronize generated figures and compiled PDF with released plotting source, then recheck layout/page count. No result change was found or inferred. |
| P5 | **P-value underflow:** `analyze.py:24–29`; `results/all_summary.csv`, columns `under_p`, `under_holm`. Fourteen asymptotic and two oracle entries are zero from underflow. The comment promises explicit flagging, but there is no flag column. High confidence. | Nonblocking for reported counts: log-space recomputation confirms them. Preserve log probabilities or explicit below-representability indicators in future exported audit outputs; do not interpret numerical zero as exact probability zero. No code was changed. |
| P6 | **Navigation/metric presentation:** `fig:validity` and `tab:exact` have no explicit source references; Appendix C's table and heatmap and Appendix E's table lack object-level references. Table 4's “MC SE” is width SE. High confidence. | Add labels/references and disambiguate SE/metric direction. Keep coverage near nominal conceptually distinct from width minimization. Improve monochrome series identification as practical. |
| P7 | **Freeze chronology is not independently authenticated:** `paper.tex:161`, local prerun hashes/amendments. High confidence in hash match; limited evidence on chronology. | Provenance limitation, not evidence of tuning misconduct. Avoid describing local files as an independently registered confirmatory protocol; retain existing amendment disclosure. |
| P8 | **Broad covariance-convention sentence is inaccurate:** `paper.tex:286` versus `methods.py:39–40`; also ambiguous “No training” at line 289. High confidence. | Nonfatal writing correction: distinguish regression's denominator-m training moments from denominator-(m−1) CI variance estimates, and nuisance fitting from predictor retraining. |

## Blocking Issues

**Count: 2. Neither is a fatal coverage theorem or statistical-code error.** They are corrections required before releasing the present submission package. The broader contribution-strength concern remains even after fixing them.

### B1 — Remove or qualify unsupported threshold necessity

- **Location:** `paper.tex:204`, §5.4; Table 3 / `tables/ablation.tex`; `methods.py:8–12,82–83`.
- **Confidence:** high that the ablation does not isolate the threshold; the phrase could be intended narrowly as exact representation, but currently overstates what the comparison establishes.
- **Evidence:** `cf_poly2` uses S and (2S−1)^2; `cf_rich` adds both (2S−1)^3 and 1{S>1/2}. There is no rich-minus-threshold comparison.
- **Analytical stress test, not an invented benchmark:** for t=2S−1 uniform on [−1,1] and m=.5+.49 sign(t), the projection covariance vector onto (t,t^3) is .49(1/2,1/4), with Gram matrix [[1/3,1/5],[1/5,1/7]]. Its explained variance is 0.2063359375, exceeding the scalar projection's 0.180075. Thus a polynomial cubic correction already has additional step-law oracle information without a threshold. This does not report learned-cubic performance or finite-sample coverage.
- **Minimal repair:** replace the necessity sentence with: “The quadratic basis captures the quadratic mechanism; the rich basis, which includes a threshold feature, exactly spans the step conditional mean.” State that cubic and threshold contributions are not separately ablated. If claiming only exact span, make that qualifier explicit.
- **Resolution criterion:** text no longer infers individual-feature necessity from this joint addition, or an independently justified isolating comparison is supplied. No new implementation is needed for the writing repair.

### B2 — Correct table-caption placement

- **Location:** `paper.tex:170–176,191–197,295–299`; Tables 1–3 on PDF pp.5,6,10.
- **Confidence:** high; explicit local template rule at `template/example_paper.tex:158–160`.
- **Minimal repair:** place each caption/label before its table content, rebuild, and check floats/page count. Leave the already top-captioned longtable intact.
- **Resolution criterion:** rebuilt Tables 1–3 follow the supplied caption-placement instruction. This is formatting, not an unsupported scientific result.

## Prebuttal Notes

- **“The exact theorem ignores dependence.”** It does not: each conditional-label interval has unconditional failure ≤α/3 after integrating memberships; pooled mass has marginal failure ≤α/3; the union bound requires no event independence. Do not claim conditional mass coverage after fixing labeled memberships.
- **“You prove the best confidence interval.”** No. Proposition 1 optimizes fixed score controls in Equation (1). It does not prove admissibility, minimax length, or global optimality, even among all score-data procedures.
- **“Your 39.3% gain is not valid inference.”** Correct under a uniform finite-sample requirement; the paper reports it as an asymptotic-tier width result accompanied by coverage 93.55%, not as a valid 95% dominance result. The exact 27.8% comparison has a different reference and a separate theorem.
- **“No Holm rejection establishes validity.”** It does not. The guarantee is analytical. The step-cell unadjusted warning remains informative despite adjusted p≈0.4694; normal failure in rare cells is decisive for the tested recipe.
- **“The benchmarks are selected to fit your basis.”** Synthetic mechanisms are deliberately aligned, disclosed mechanism tests. Two empirical non-gains are retained. Concede the limited external evidence; do not manufacture generalization.
- **“Where is the stronger finite-sample betting baseline?”** It is not implemented, as already disclosed. These results concern the tested CP/EB recipes. Do not assert it would win or lose; no benchmark result exists here.
- **“StratPPI/Cross-PPI already solve this.”** Acknowledge established stratification/cross-fitting. Explain the specific fixed-input design, unknown mass uncertainty, random label counts, and narrow diagnostic purpose. This explanation narrows scope; it does not establish a major new theorem.
- **“Your threshold ablation proves necessity.”** Withdraw that attribution. The rich basis adds two components jointly; exact representability is different from necessity for incremental gains.
- **“Empirical rows overlap, so sampling is invalid.”** The target is the fixed paired empirical distribution with independent with-replacement draws, not the original scientific population or without-replacement inference. Shared source indices do not invalidate that explicitly conditional design.
- **“The package test validates the unrestricted baseline.”** It validates `ppipp_pkg` only. `ppipp` deliberately uses unrestricted tuning and its original-paper pooled variance convention; the two are not interchangeable.
- **“Was this independently preregistered?”** Local frozen hashes and amendments match; independent timing was not established by this review. Describe the evidence precisely.
- **Novelty defense:** foreground reliable decision guidance, explicit opportunity/equality cases, and honest adverse results. Admit elementary ingredients and restricted priority assessment. Do not substitute computational volume or the absence of fatal bugs for an ICML-level contribution argument.

**Final handoff:** retain the headline numbers and qualified conclusions; resolve B1–B2; correct the nonfatal prose and artifact issues; then reassess the contribution argument with human authors. No current evidence warrants a blanket “submission-ready” or acceptance prediction.
