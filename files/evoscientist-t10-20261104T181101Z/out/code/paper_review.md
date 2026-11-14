# Self-Review

Draft: `/work/paper.tex`, rendered `/work/paper.pdf`. Review artifact: `/work/paper_review.md`. Mechanical evidence: `/work/paper_review_mechanical.json`; reproduce with `python /work/artifacts/paper_review_scan.py`.

## Verdict

**Major-rework for NeurIPS main-track contribution sufficiency; no fatal statistical theorem error or numerical aggregation error established.** The three required pre-submission corrections below are local, not a demand to rerun experiments. The major-rework verdict reflects a contribution score of 2, not a claim that the experiments or CP guarantee are invalid. After local corrections this remains a credible, unusually transparent audit with substantial venue-level novelty/significance risk.

**Reject-first simulation.** A skeptical reviewer could reject because the central variance identity is a standard conditional-expectation projection, the exact construction combines classical binomial inversion and union bounds, and the only multiplicity-adjusted width wins occur in the deliberately aligned sharp-tail mechanism test. Both real prediction pools show sizeable penalties. Running many Monte Carlo repetitions precisely establishes this narrow result but does not supply additional scientific settings or make the statistical ingredients novel. The paper already admits these facts; stronger novelty adjectives would worsen, not solve, the problem. Its defensible contribution is the explicit accounting of validity, nonlinear information, mass uncertainty and selection costs, including retained failures—not a new general PPI method.

**Prioritized disposition**

| Priority | Finding | Disposition |
|---|---|---|
| P1 | F1: ideal PPI++ consistency versus a fixed implementation variance cutoff | Required scope clarification; not demonstrated damage to this grid |
| P1 | F2: Figure 3 points readers to ratio uncertainty absent from the cited full table | Required factual reporting correction |
| P1 | F3: five table captions violate the official above-table convention | Required formatting correction |
| P1 strategic | F4: modest, readily derived construction; narrow empirical positive result | Acceptance risk, not a fatal scientific defect; no guaranteed prose-only cure |
| P2 | F5: abstract joins the full trial count to a single-cell effect | Separate study size from the 3,000-trial headline |
| P2 | F6: three figures and two labeled tables are never cited in prose | Add precise callouts |
| P2 | F7: positive MC uncertainty rounds to zero / point-looking intervals | Change display precision, not estimates |
| P2 | F8: thirds counterexample uses a differently normalized “loss” | Specify approximation error versus variance loss |
| P2 auditability | F9: protocol-lock chronology is declared, not independently established | Qualify provenance; retain smoke/post-audit distinctions |

All three passes ran in order. Pass 1 was recorded after the complete TeX/PDF read and **before** loading the skill/checklists/script. No code interpreter or typed subagent dispatcher was available; Pass 2 used the expressly permitted sequential five-aspect fallback. The JavaScript seats were inspected but were not executed or represented as independent reviews. Pass 3 used an independent read-only Python/shell scan. No experiments, predictor fitting, downloads, searches, citation traversal, or manuscript edits were performed. Only the three allowlisted source-paper findings in `source_verification.md` were used for source fidelity; no excluded paper was identified. README/reproduction-driver work and the unbuilt archive are parent-owned release tasks, **not blockers here**.

## Pass-1 Suspicions

Confidence describes the suspicion at intake, not proof of a defect. “Open” includes narrowed, explicitly qualified concerns; five items remain open.

| ID | Location and original suspicion | Confidence | Evidence that would settle it | Outcome after all passes |
|---|---|---|---|---|
| S1 | `paper.tex:32`, §§3–6: classical projection plus Bonferroni CP may be insufficient new knowledge | High | A concrete audit insight distinct from claiming new statistical ingredients; an adequate venue-level contribution argument | **Open, F4.** No priority overclaim found, but no broad practical efficiency result either. This is a judgment, not an allegation of duplication. |
| S2 | §4, `paper.tex:80–100`: conditioning, unknown weights or selection may invalidate “exact” coverage | Medium | Conditional-count law, error accounting, feasible simplex and corrected selection in proof and implementation | **Resolved.** Counts, not every score, are conditioned on; all response/mass budgets and selection corrections match. |
| S3 | §3 / Appendix B: same-sample fitted controls and the zero-variance faster-rate case might be unjustified | Medium | Product-remainder expansion, scaled variance consistency, and unconditional pooled-mean identity | **Open only in narrowed form, F1.** The bin-control arguments survive direct algebra; the ideal scalar plug-in guarantee needs an implementation-cutoff caveat. |
| S4 | §5/C/D: totals, nine wins, 31 failures, point intervals, selector counts or mass gaps may not match artifacts | Medium | Independent raw-output aggregation and checks of all formulas/printed values | **Resolved.** All 1,656,000 existing method rows and separate 7,500 mass rows checked; no numerical discrepancy beyond serialization precision. |
| S5 | §5.1/C.3/E: “before outcome inspection” might overstate the protocol timing | Medium | Independently dated lock/history specifying what outcomes were already seen | **Open as provenance limitation, F9.** Manifest asserts a lock before full inspection; it is not itself independent proof of timing. No evidence establishes a false lock. |
| S6 | Tables 1–5/Figures 1–4: caption placement, callouts and MC uncertainty may be inconsistent | High | Source searches, rendered display inspection and table-to-artifact mapping | **Open, confirmed F2/F3/F6/F7.** |
| S7 | §5/D: true weights or conditional-mean information might enter feasible competitors | Medium | Follow arguments and known-weight branches in the runner and interval functions | **Resolved.** Known weights affect only the explicitly infeasible diagnostic; the matched ablation is separate. |
| S8 | §6/C.4/checklist: empirical-pool or ethics language may overstate original training independence, licensing or deployment evidence | Medium | Stated conditional empirical law, disclosed provenance limits and release exclusions | **Resolved as an overclaim suspicion, not as legal certification.** Conditional empirical-population scope and unknown licensing/training provenance are explicit. Original data permission remains unresolved. |
| S9 | Abstract, `paper.tex:22`: “Across 103500 … 26.5%” may sound like an aggregate effect | High | Trace the gain to its actual trial subset and read the abstract alone | **Open, F5.** The effect uses one 3,000-trial cell, although “in … an example” partially qualifies it. |

## 5-Aspect Findings

Scores use 1–5, higher better. All five aspects were completed sequentially; none is missing.

### Contribution — 2/5

**F4 — Novelty/significance risk, high confidence as a review judgment.** Locations: `paper.tex:32,54–77,80–100,160–164`; PDF pp.2–4,7. A capable specialist could plausibly derive the projection identity and CP/union-bound construction in an afternoon. That observation does not refute either result. The favorable tails indicator is intentionally aligned with the synthetic response, and all nine designated significant width reductions occur in that scenario. Source notes support honest attribution to the three cited originals and explicitly deny exhaustive novelty clearance; nothing in this review establishes that the complete audit itself appeared elsewhere.

**Narrow fix:** keep the existing no-priority language. Sharpen the audit's new-to-the-reader takeaway: scalar/nonlinear headroom can coexist with a finite-sample exact gain, yet unknown masses and protected selection reverse that gain at small unlabeled budgets and on the supplied real pools. Do not market the variance identity, stratification, CP, or selection correction as inventions. Even excellent wording cannot guarantee main-track sufficiency. A stronger universal method claim is unsupported by the current artifacts and should not be added.

The skill's easy-subset kill-switch is a real acceptance warning here, not a reason to erase negative results or demand unauthorized new experiments. Recent-baseline exhaustiveness cannot be assessed under the source restriction, and is not alleged.

### Clarity — 4/5

The estimand, meaning of fixed inputs, scope of same-sample fitting, and distinction between finite and asymptotic coverage are unusually clear. Module motivations are present: projection locates opportunity; CP accounts for response/mass uncertainty; the simplex enforces mass coherence; union bounds pay for choosing a partition.

**F5 — Abstract framing, high confidence; interpretive risk rather than a false number.** `paper.tex:22`, PDF p.1 lines 8–11. The total is 103,500 paired inputs; 26.5% is the sharp-tail `n=500,N=10000` effect from 3,000 of those inputs. **Narrow fix:** “We audit 103,500 paired trial inputs. In a nearly deterministic nonlinear example at 500 labels, the selection-protected interval is 26.5% narrower … over 3,000 repetitions.” Keep the negative real-pool sentence.

**F6 — Missing callouts, mechanically confirmed.** Figures `fig:main` (`paper.tex:124–127`), `fig:real` (`319–321`), and `fig:bins` (`323–325`) have no text `\ref`; neither do `tab:paired` (`132–135`) and `tab:mass` (`312–315`). Figure 2 is cited and is not missing. **Narrow fixes:** cite Figure 1 and Table 2 with the sharp-tail/smooth-U discussion; cite Table 5 in the mass paragraph; cite Figure 3 with the real-pool result; cite Figure 4 with bin-complexity limitations. The longtable is included in Appendix F but has no table label; give it one if the Figure 3 caption is to refer to it precisely.

**F8 — Normalization ambiguity in a mathematical example.** `paper.tex:73` defines approximation loss as `E[(m−m_B)^2]/[n(1+r)]`; `paper.tex:215` then calls the equal-thirds “loss” `1/12`. The latter is correctly the **unscaled approximation error**: only the middle third is mixed, with conditional variance `1/4`, giving `(1/3)(1/4)=1/12`. The variance loss is `1/[12n(1+r)]`. **Narrow fix:** replace “loss 1/12” by “squared approximation error 1/12 (variance loss 1/[12n(1+r)])”. No theorem change is needed.

**Reverse outline, paragraph-level sequence in the core sections**

- Introduction (`24–32`): inherited fixed-predictor problem → narrow binary-mean question/empirical-population target → separate information, fitting and validity costs → three modest contributions and explicit attribution. Coherent; no promised contribution disappears.
- Setting (`35–51`): sampling and estimand → deterministic-control definition → unbiasedness/existing PPI and finite-sample precedent → scalar coefficient → pooled variance/unrestricted tuning/divisor convention → fixed-allocation versus random-count scope. Coherent; the literal fixed-score versus downstream-summary distinction is addressed rather than hidden.
- Headroom (`54–75`): define conditional mean → projection identity → orthogonality proof idea → no global impossibility → bin approximation/refinement caveat → feasible fixed-bin asymptotics. Good order; F8 is a terminology mismatch downstream, not a logical gap.
- Exact method (`78–100`): fixed partition/counts → response and mass CP boxes → simplex endpoints → one-bin special case → coverage/selection theorem → union-bound proof → numerical implementation scope → four-partition selector and unsafe alternative. Each module earns its place.
- Experiments (`104–156`): paired budgets/size → laws and shift → method roster/additions → MC/multiplicity definitions → main synthetic comparison → smooth-U and negative controls → coverage/width figure → finite-unlabeled costs → paired-ratio table → empirical-pool sampling → negative real result → real table → rare-event collapse → shift collapse → matched-budget mass comparison. The substantive narrative is coherent; the missing callouts make several displays feel detached, and Figure 2 being in Appendix D requires a long jump.
- Discussion (`159–173`): conditional answer → scope and comparator limits → numerical/logging limits → impact, licenses and process disclosure → practical recommendation. Honest but the process narrative is long relative to the scientific conclusion; moving operational failure detail to Appendix E would be optional polishing, not a blocker.

### Results — 4/5

The sharp-tail reduction is large relative to MC error and correctly separated from coverage guarantees. Negative real-pool results, rare-event collapse, and shifted clipped intervals are retained. Main tables explicitly avoid equal-validity rankings. It would be a mistake to bold the narrowest Wald interval as universally “best”; no such bolding is present.

**F2 — False/ambiguous uncertainty pointer, high confidence.** `paper.tex:321`, Figure 3 / PDF p.14: “MC intervals and coverage are supplied in the full results table.” Figure 3's metric is **mean-width ratio to PPI++**. `generated/all_results.tex` / Table 6 has mean width ± MCSE, coverage, and coverage Wilson bounds; it has **no paired ratio MC interval**. Marginal width SEs do not determine a paired ratio SE without covariance. The needed numbers do exist in `paired.csv`, and Table 2 gives only one of the six real Safe-CP/PPI++ cells. **Narrow fix:** “Paired ratio MC intervals are provided in paired.csv; marginal width uncertainty and coverage intervals are in Appendix F.” Alternatively place the already-computed real-pool ratio bounds in the figure/table. No new experiment is needed.

**F3 — Official table-caption rule violated, high confidence.** Tables 1–5 put `\caption` after the table/input: `paper.tex:114–118,132–135,143–147,258–273,312–315`. This is visible on PDF pp.5,6,11,14. The bundled official source says the table number/title “always appear before the table” (`template/neurips_2026.tex:321–323`; example `341–356`). **Narrow fix:** move each caption/label before its table content, then compile. Table 6's longtable caption is already above and should not be moved. Figures correctly have captions below.

**F7 — Display precision hides nonzero MC uncertainty, high confidence.** Table 5 (`generated/mass_ablation.tex:5–6`) prints MCSE `0.00000` at `N/n=20,100`, though `mass_ablation_summary.csv:4–5` gives `3.0252518e-6` and `1.8847046e-6`. Table 6 rounds **129 positive width MCSEs** to `0.00000`. Table 2's irrelevant-score ratio interval prints `[1.266,1.266]` (`generated/paired_table.tex:7`) despite nonzero interval length. These are rounding effects, not zero simulation variation. **Narrow fix:** scientific notation or two significant digits for MCSEs; enough ratio digits to distinguish endpoints, or explicitly state rounding. Preserve all estimates.

Figures are vector PDFs and are legible at the inspected size. Figure 1 uses an accessible multi-color palette; Figures 2/4 rely heavily on color with similar markers, so distinct line styles would improve grayscale accessibility. A pipeline schematic is not necessary for this elementary construction. Figure 4 plots widths only; its coverage warning points to the full table rather than pretending coverage is plotted. The main missing figure issue is provenance/callouts, not lack of a new graphic.

### Testing — 4/5

Coverage and mean reported width are the right paired metrics; selection, bin complexity, finite unlabeled budgets, known weights, negative controls and failure mechanisms are all examined. The matched-response-budget ablation is **completed**, exploratory and separate; it must not be requested again or retroactively labeled confirmatory. Hoeffding supplements are descriptive and consistently excluded from locked families. Stratified PPI's fixed-allocation design is explicitly not reproduced because it would change the information/allocation task. No claimed-but-silently-missing direct comparator was found.

**F9 — Lock timing is not independently authenticated, medium confidence about chronology, high about evidence limits.** `paper.tex:109,293`; `multiplicity_manifest.json:2,17`; `analysis_audit.md`, opening scope paragraph. The JSON states “locked before full outcome inspection” but contains no independent dated seal/version history establishing that fact. The draft's “before outcome inspection” at line 109 is also stronger than its later “before full outcome inspection,” given disclosed smoke checks. **Narrow fix:** use the consistent phrase “declared locked before full outcome inspection, after mechanics-only smoke checks”; identify an existing dated protocol/history if available. Otherwise say the within-declared-family tests are multiplicity-adjusted without implying an externally verified preregistration. This is not evidence of outcome-driven tuning and does not invalidate the finite-sample theorem or the observed differences.

No per-method timing comparison, formal quantile-error certification or original-run fallback counts is available; those omissions are already acknowledged. No deployment validation or exhaustive nonasymptotic baseline search is claimed. These are limitations, not hidden missing experiments. This review did not rerun the six unit tests because the request prohibits new experiments; their six definitions and the stated prior result were inspected, not independently re-executed.

### Method — 4/5

The conditional-count construction, simplex optimization, fixed-family selection protection and fixed-bin first-order arguments survive the mathematical audit below. Data availability is realistic for the stated task: all feasible procedures use the same labels and scores, fixed boundaries, and no unlabeled outcomes. Conservative costs often outweigh benefits; the manuscript reports that rather than promising dominance.

**F1 — Qualify theoretical transfer to the thresholded PPI++ implementation.** High confidence in the distinction; no demonstrated impact on reported cells. `paper.tex:44–48,253,276` describes a consistent scalar plug-in with `Var(S)>0`, then discloses a fixed `1e-14` numerical threshold. `intervals.py:130` actually returns zero whenever the **pooled variance** is at most `1e-14`, not merely for a constant score. A fixed cutoff does not vanish asymptotically. Analytically, let `Z~Bernoulli(1/2)`, `S=1/2+10^-7 Z`, and `Y=Z`. Then `Var(S)=2.5e-15>0`, and the ideal coefficient is `1/[10^-7(1+r)]`, whereas the thresholded implementation suppresses it. This is an analytic scope counterexample, not a new simulated experiment.

**Narrow fix without changing any results/code:** say the ideal formula's consistency applies to the implementation when the population pooled variance is strictly above the cutoff (under common-population sampling, `Var(S)>1e-14`), and below-cutoff controls intentionally revert to labeled Wald. Change “denominator threshold” at line 276 to “pooled score-variance threshold,” matching the code. The fallback can remain a consistent mean estimator; the issue is transfer of the ideal coefficient/efficiency statement, not proof of finite-sample invalidity caused by the safeguard. Keep the mathematical ideal result under `Var(S)>0` separate. This paper's synthetic nonconstant score laws have variance far above the cutoff; no reported headline has been shown to depend on it.

## Protocol Audit & Mechanical Scans

Eight deduplicated protocol/mechanical findings are **F1–F3 and F5–F9**. F4 is the separate contribution judgment. Three are required pre-submission corrections, listed below.

### Data flow, assumptions and comparison fairness

1. **Synthetic flow:** `run_experiments.py:26–52,92–109` fixes the laws, draws independent labeled and unlabeled scores, generates only labeled outcomes, then passes the same arrays to all fourteen original methods. `supplement_baselines.py:24–36` regenerates the same seed/cell/batch sequence for two Hoeffding methods. Regeneration matches by inspected code, not by saved score-stream hashes; the actual original score streams were not stored.
2. **Real flow:** `run_experiments.py:45–50,81–88` loads fixed outcome/score arrays, independently draws labeled/unlabeled indices with replacement, and never passes unlabeled outcomes to inference. Record overlap is not dependent sampling. Conditioning on the fixed empirical joint law makes original predictor-training uncertainty irrelevant to that conditional target, but not resolved for deployment. The manuscript states this correctly.
3. **Fitting/selection:** fitted bin means use all labels, without learning boundaries. Safe CP uses four independently prespecified partitions and rebuilds each at `alpha/4`; it does not choose an unadjusted 95% interval and retroactively call it safe. Selector choice zero denotes the corrected labeled candidate, not ordinary labeled CP.
4. **Information boundary:** true tail masses are computed in the runner and passed into `all_intervals`, but inspection of `intervals.py:151–152` shows they are used only in `oracle_mass_cp`. All feasible branches are computed without those weights. No true conditional-mean oracle is evaluated as a feasible competitor. The fixed tail partition is domain knowledge/prespecification, not secretly fitted to each replication.
5. **Matched mass:** `mass_ablation.py:19–25` fixes the response component error at `.05/4` for `K=2`; original known-mass CP uses `.05/2`. The matched comparison therefore separates unknown-mass width from budget reallocation on the same cells. The conditional law is held fixed; the diagnostic remains infeasible and post-audit.
6. **Assumption ledger:** binary outcomes/support `[0,1]`; independent iid common-population samples; evaluation-independent fixed score/partitions; finite fixed `K` and positive active masses for asymptotics; `n,N→∞` with bounded `n/N`; nonzero limiting variance for ordinary studentization. Zero masses, empty cells, constant scores, nonfinite results, and degenerate faster-rate cases have explicit treatments. Shift violates the common-population assumption and is explicitly excluded from all three declared families. Nothing extends Safe CP to arbitrary shift.
7. **Compute/tuning fairness:** no training, data allocation or scene-specific boundary tuning is hidden. Shared data is established; equal measured method runtimes are neither established nor claimed. Main coverage statements concern ideal real-arithmetic intervals, not a machine-verified special-function implementation.

### Mathematical claims checked independently

- **Projection and affine equality:** for `h0=h−Eh`, `n V_h=Var(Y)−2 E[(m−mu)h0]+(1+r)E h0²`. Completing the square gives the displayed minimum. Since `1/[n(1+r)]=N/[n(n+N)]`, the minimum becomes `E Var(Y|S)/n+Var(m)/(n+N)`. Cauchy–Schwarz gives the nonnegative scalar gap and the affine equality condition when `Var(S)>0`. No global impossibility theorem follows, and none is claimed.
- **Bin approximation:** replacing `m` by `E[Y|B]` gives the stated normalized gap. Refinement, not arbitrary bin count, orders the oracle error; a binned class need not contain the scalar score. Correct apart from F8's terminology.
- **Conditional law:** multinomial factorization gives independent binomial response counts conditional on the cell-count vector. Conditioning on every score would generally change that law; the paper explicitly avoids it. Zero-mass bins are almost surely empty.
- **Exact budget/feasibility:** for `K≥2`, `2K` intervals at total error `alpha/(2K)` union-bound to `alpha`. CP contains each observed proportion, so `D/N` is feasible in the box-simplex for every data realization. On joint coverage, nonnegative weights give the displayed endpoint chain. `K=1` correctly spends no mass budget. An additional union bound over `M` corrected candidates covers arbitrary data-dependent choice among them.
- **Optimization/numerics:** sorted filling solves the box-simplex LP; the dual lower/upper formulas bound every feasible objective even if a computed primal threshold is approximate. The code pads quantiles and endpoints outward and declares its floating-point limitation. That is not a formal quantile error bound, but the paper does not claim one.
- **Same-sample bins:** each estimated cell mean differs by `O_p(n^-1/2)`; each labeled/unlabeled frequency contrast is `O_p(n^-1/2)` when `n/N` is bounded. Their finite sum is `O_p(n^-1)`, without requiring independence of factors. Scaled consistency `n Vhat→v_rho`, not merely `Vhat→0`, supports Wald studentization when `v_rho>0`.
- **Degeneracy:** with `rho>0`, zero limit requires a constant binary response. With `rho=0` and deterministic bin responses, occupancy gives the pooled-mean identity; on that event `Vhat=[n s_L²+N s_U²]/(n+N)²`. Thus `(n+N)Vhat→mu(1−mu)`, and an unconditional iid pooled CLT transfers through the high-probability equality event. No CLT is improperly conditioned on occupancy. These are pointwise fixed-population results, not uniform results for shrinking masses/growing bins.
- **Hoeffding:** labeled residual range is two and unlabeled score range one, giving the stated union radius. It is a valid simple specialization, not an optimal exact PPI baseline. Source notes support the PPI finite-sample component principle, pooled unrestricted PPI++ coefficient, and fixed-allocation scope of Stratified PPI.

### Numerical and claim–artifact mapping

The script hashes 148 input files and rereads all 78 main/supplement raw endpoint files plus all 39 diagnostic files. All hashed inputs were unchanged. It imports no experiment runner and samples nothing. Saved endpoints and aggregations are verified; this is not independent recomputation of every interval from absent original score streams.

| Manuscript claim | Exact artifact/key | Reproduced result / judgment |
|---|---|---|
| Abstract/§5: study size | `results/design.json`; all raw cells | 30×3,000 + 9×1,500 = **103,500 inputs**, 39 cells; 14 original + 2 descriptive methods; **1,449,000 + 207,000 = 1,656,000 rows**. Matched mass has **7,500 separate rows**, not added to that total. |
| Abstract, §3: nonlinear headroom, affine no-headroom within family | Proposition 1, Eqs.(3)–(5), Appendix A.3 | Algebra and equality condition checked; delivered again in §6. No unsupported global bound claim. |
| Abstract/Introduction: valid unknown-mass/selection construction | §4, Appendix A.1–A.2; `intervals.py:53–63,144–149` | Statistical guarantee and implementation budgets align; floating-point limitation disclosed. |
| Abstract/§5.2: 26.5% narrower at sharp tails/500 | `summary.csv:173,165`; `paired.csv:344`, `(10,safe_cp,ppi_pp)` | `0.0643527/0.0875700=0.734872010434`; reduction **26.5128%**, pointwise MC95 **[26.2804,26.7452]%**; **3,000/3,000** coverage. Single-cell, not aggregate; F5. |
| Tails CP versus label CP at 500 | `summary.csv:171,163`; `paired.csv:341` | Reduction **39.7887%**; paired ratio `0.602113086329`. |
| Safe CP at 2,000 labels | `paired.csv:376`, cell 11 | Reduction **33.4204%**, matching 33.4%. |
| Smooth-U Bin4 at 2,000 | `paired.csv:270`; `summary.csv:136`, cell 8 | Reduction **11.2305%**, coverage **.948**; correctly descriptive/asymptotic, not an exact-method width win. |
| Nine adjusted designated width wins | `paired.csv`, 72 nonmissing Holm entries | **4 Safe/PPI++ + 5 Tails/label = 9**, all sharp tails. Width tests use approximate paired-t marginal p-values and Holm; ratio intervals remain pointwise. |
| Finite-unlabeled width ratios | `paired.csv:888,920,344,952`, cells 27,28,10,29 | **1.291765,1.060918,.734872,.554093**, matching prose. Figure 2 displays only sensitivity ratios 1,5,100; ratio 20 is the main cell, not an omitted run. |
| Exact-family minimum | `summary.csv:99`, `(6,label_cp)` | **2830/3000=.943333**, Wilson **[.934479,.951054]**, simultaneous lower **.927340750024**. Three exact-family rates below .95, all labeled CP. Not a theorem violation. |
| Analytic CP anomaly diagnostic | Appendix C.3; existing analytic diagnostic artifact | Exact binomial sum **.9542558154**; nominal-boundary lower-tail p **.0532630699**; actual-coverage-boundary p **.0031050791**. The prior exploratory Holm36 report gives **.111783**. This review recomputed the first three analytically; the .111783 comes from the supplied audit, not a new simulation. |
| Negative real results | `paired.csv:1112,1208`; `summary.csv:557,605`; diagnostics cells 34,37 | Safe/PPI++ ratios **1.528857,1.872761**: **52.9%,87.3% wider**. Corrected labeled candidate chosen **3,000 times in each**. |
| Real-pool target/sample sizes | Existing `data/{forest,galaxies}.npz`, `data_eda.json` | **242/1596=.1516290727**, **4341/16743=.2592725318**; scores finite and within support. Original files read, no new samples. |
| Rare-event PPI++ collapse | `summary.csv:293`; cell-18 raw PPI++ endpoints/diagnostics | **1878/3000=.626**, **1,121 [0,0]** intervals and **one** additional nondegenerate miss. Labeled CP coverage **.982**. Mechanism agrees with all-zero label probability `.99^100`. |
| 31 asymptotic undercoverage results | 252 nonmissing adjusted tests in `summary.csv` | **31** reproduced; adjusted real-pool PPI++ failures at `n=100` included. Non-rejection elsewhere is not validity certification. |
| Shift failure | Cell-22/23 raw outputs and diagnostics | At 500: **0/3000** coverage, **2,883 [1,1]**; at 2,000: **3,000 [1,1]**. All **16** ratios with the zero-width PPI++ denominator at cell 23 remain undefined. No illegal precision ranking. |
| Matched mass gap | `mass_ablation_summary.csv:4`; matching raw joins `(cell_id,seed,rep)` | Unknown **.0537949997**, matched **.0294817676**, reallocated **.0262067986**; mass gap **.0243132321**, paired MCSE **.00000302525**, reallocation gap **.00327496897**. All four ablation cells reproduce. |
| Tables/macros/runtime | All `generated/*.tex`; `numbers.json`; run/supplement metadata | All **624** full-table rows, **7** main, **6** real, **6** paired and **4** mass rows checked at printed precision; **73** number macros reproduce. **39.0803s→39.1s**, **7.7516s→7.8s** are stored wall times, not freshly measured performance. |
| Conclusion: conditional, not universal/deployment-level improvement | §6 against the above positive/negative results | Supported and consistent with the introduction. Retain all restrictions. |

Maximum raw mean-width discrepancy is `4.98e-13`; maximum paired-ratio discrepancy is `4.68e-10` (large ratios included); width endpoint identity discrepancy is `1.12e-15` or less. Coverage, Wilson bounds and exact lower bounds match within `5e-13`; Holm undercoverage within `9.01e-13`. Mass joins/means match within `1e-16`. All discrepancies are compatible with saved precision, not numerical failures.

### Mechanical, format, citation and checklist results

- **Page count passes:** 32 total PDF pages; **main 1–7**, references **8**, appendix **9+**, full results **16–26**, checklist **27–32**. The official limit is **9 content pages**, not nine total. US Letter `612×792pt` throughout. The working style file is byte-identical to the bundled official style. No page-limit blocker.
- Exactly **three citation keys**, `ppi`, `ppiplus`, `stratppi`, all resolved by the three complete BibTeX entries. No uncited bibliography entries, missing reference labels, duplicate labels, or visible `??`. Source notes—not new literature searching—support the specific attribution claims. Publication-record exhaustiveness was not re-audited.
- No `TODO`, `FIXME`, `TBD` or `\todo` remains in the included manuscript/checklist/generated TeX or bibliography. Template answer-choice comments are not unfilled answers. All **16 checklist items** have both an answer and justification; conservative **No** answers for resource completeness and asset licensing match the text.
- All figure assets exist. Figures are captioned below, tables use booktabs and no vertical rules. Table-caption noncompliance and missing callouts are F3/F6. No bolded-best or direction-arrow inconsistency exists because neither encoding is used; avoiding a single “best” across guarantee classes is sensible.
- No undefined-reference or overfull warning in the inspected build log. There are underfull boxes, `h→ht` float warnings and an amsmath command warning; none establishes a scientific/layout blocker. Standalone `pdffonts` is unavailable, so no dedicated PDF-font embedding audit is claimed. No new compile was run.
- Source archive is not built yet and README/driver are being completed by the parent. This review does not claim to have tested the final archive, live download availability or a clean-environment reproduction. Excluding raw third-party arrays, giving hashes/retrieval instructions, and retaining explicit unknown-license status are appropriate mitigations, not proof that all historical usage terms have been resolved. Do not silently change the checklist's asset-license answer to Yes.
- Promise/delivery check: (i) variance identity → §3/A.3 → §6; (ii) finite-sample unknown-mass selection → §4/A.1–A.2 → §6; (iii) paired validity/width audit → §5/C/D/F → §6. All promised components are delivered; F2 concerns the location of one type of uncertainty, not a missing experiment.

## Blocking Issues

**Three required pre-submission corrections; zero established fatal theorem/aggregation errors.** These are distinct from the strategic venue-risk finding F4.

1. **B1 / F1 — Separate ideal scalar theory from the fixed-cutoff implementation.** At `paper.tex:253,276`, add the above-cutoff condition for transferring coefficient consistency to the code, and identify the cutoff as pooled score variance. Do not alter experimental results or claim a grid-wide bug without evidence.
2. **B2 / F2 — Correct Figure 3's uncertainty provenance.** At `paper.tex:321`, point paired ratio MC bounds to the actual paired artifact, or expose those existing bounds in the display. Do not assert they are in Table 6 as currently formatted.
3. **B3 / F3 — Move captions above Tables 1–5.** Fix the five named environments, preserve the already-correct longtable caption, then compile and recheck main-page count.

F5–F9 are worthwhile narrow repairs/qualifications, not reasons to invent new experiments. Missing original fallback counters, special-function certification, peak-memory measurements, deployment validation and complete license resolution are genuine disclosed limitations; they are not transformed into hidden fatal defects by this review.

## Prebuttal Notes

**Counterintuitive protocol completed:** reject-first paragraph above; novelty attacked explicitly; trust scored independently of gains; one unsupported pointer identified for deletion; a meaningful scope limitation selected for promotion. No manuscript text was actually changed, per instruction.

- **Delete rather than defend:** delete/rewrite “MC intervals … supplied in the full results table” for Figure 3 unless the relevant ratio bounds are actually added. Do not inflate the exact coverage observed frequencies into MC certification of ≥95% everywhere.
- **Promote a limitation:** explicitly state that fixed, prespecified partitions are substantive prior structure: the sharp-tail partition is intentionally aligned with a nearly deterministic law, not automatically learned without a label cost. The paper already calls the example favorable; bring that connection into the contribution takeaway instead of burying it in §6.
- **Trust scorecard:** baseline fairness **2/2**, reproducibility/auditability **1/2** (unlogged original fallbacks/unauthenticated lock timing, not transient README work), honest limitations **2/2**, failure transparency **2/2**, statistical soundness **2/2**: **9/10**. Strong trust does not erase weak novelty.

| Likely criticism | Honest short response and boundary |
|---|---|
| “This is obvious stratification/CP.” | Agree that the ingredients are classical. The intended contribution is the paired validity–width accounting under random counts, unknown masses and selection; do not claim methodological priority. This may still be insufficient for the venue. |
| “You only win on a hand-built example.” | Correct for adjusted designated wins. The example isolates nonlinear information unavailable to a scalar correction; both real pools and limited-unlabeled reversals are reported. No typical-effect-size claim follows. |
| “You compare exact to asymptotic intervals.” | Yes, with guarantee classes disclosed. Width is not treated as an equal-validity ranking; standalone Tails CP versus labeled CP also supplies a feasible exact-to-exact comparison. |
| “Stratified PPI is missing.” | Its verified fixed-allocation/weight design is not reproduced under the immutable iid-label task; §2 explains the mismatch. Do not pretend this establishes exhaustive superiority. |
| “Cross-fitting is missing.” | For fixed finite bins, the fitted error multiplies a bin-frequency contrast, yielding an `O_p(n^-1)` remainder. Growing bins or learned boundaries are outside the theorem. |
| “94.3% contradicts exact coverage.” | A finite MC hit rate need not exceed the true guarantee. The minimum labeled-CP Wilson interval includes .95; validity comes from the theorem, not empirical calibration. |
| “Known weights give you extra information.” | Only infeasible diagnostics receive them. The matched-budget ablation is exploratory and separated from all confirmatory families. |
| “Repeated empirical records leak information.” | Independent with-replacement draws from a conditioned empirical law can overlap without statistical dependence. This is not deployment validation or new unique scientific information. |
| “The lock was preregistered.” | Do not make that stronger claim. The manifest declares a pre-full-inspection lock after mechanics checks; independent authentication is not available in the supplied evidence. |
| “The release is not reproducible.” | Numerical artifacts already reproduce against all saved endpoints. Final archive/driver validation remains a release gate owned by the parent; this review does not certify a completed package. |

**Recommended order:** make B1–B3 and F5/F8 wording fixes; repair display precision/callouts and lock phrasing; regenerate only documentation/displays as needed; compile and run the read-only scan; then decide whether the audit contribution, without inflated claims, meets the intended venue. No new scientific experiments are prescribed.
