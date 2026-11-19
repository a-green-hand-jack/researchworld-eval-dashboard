# Review of Version 1 (paper-repo PR #13, main 7b6555ed7c9a into release)

Document read: `document` branch `main/document.pdf`, built-from 7b6555ed7c9aa51b334240773d2c785983c1c889 (= PR head). 21 pages: 9 main, references, appendix A-E, checklist. Code/results read from the same commit.

## What the paper is
Defines the "price of first place" (breadth, depth, feasibility under a per-task boost cap), solves it per rule class (mean family, quantile/median/min, Borda, plurality, Copeland), prices 30 top targets on HELM MMLU (57 tasks), OLLB benchmark level (6) and sub-task level (39), reports five pre-registered tests (R1-R5; thresholds are in idea-repo Brief rev 3, 2026-11-18 09:41, before results) with verdicts as they came out (mostly refutations), a noise analysis, a boost-scale calibration, and a package.

## Strengths
Honest, pre-registered, refutations reported; exact solvers with brute-force checks; cluster-bootstrap intervals; reproduction notes complete (versions, SHAs, seeds, commands, script-per-table, measured compute); NeurIPS 2026 template, 9 main pages, checklist present, anonymous; 5 main-text floats; figures and tables legible and consistent with the text.

## Findings (must = blocks `release`)

**M1 (must). "No rule is cheapest for most targets" (abstract-adjacent bullet, intro bullet 2) contradicts §6.2 and Table 3.** R2's largest shares are 0.73 (plurality, HELM), 0.53 (median, OLLB-6), 0.67 (Borda, OLLB-39): on every board one rule is cheapest for a majority of targets. What R2 supports is "no rule is cheapest for >= 90%" and "the cheapest rule differs by board". Restate in the abstract, intro and §6.2.

**M2 (must). The noise result is a headline claim (abstract, intro bullet 3) with no method in the paper.** §6.5 points to Appendix C, but Appendix C ("Noise, margins and spillover") holds no noise analysis. Missing: what "lead by c standard errors" means for a median/min/Borda/plurality aggregate (SE of what, by what noise model on target and rival scores; is rival noise included), how the "probability of first place" is estimated (draw counts), and no table or figure shows it. The claim is also over-scoped: results/headline.json `e6_confidence` shows that on HELM the minimum reaches 90% for all 30 targets at the same c = 3 as the mean (it differs only in depth, 5.3x vs 1.3x), and on the sub-task board the median reaches 90% for 63% of targets (c = 4), i.e. the HELM "never" is not general. Needed: the noise model and estimator in the paper, a compact table/figure of share-reaching-90% and depth ratio per rule on both noisy boards, and abstract/intro wording that matches ("harder", not "never"; both boards).

**M3 (must). "The fitted relation does not transfer between boards" (abstract; R3 "supported") is largely an artefact of units.** For the mean, depth = m x gap exactly, so a log-depth-on-gap fit made on a board with m = 57 cannot predict one with m = 6 or 39 even though the structure is identical; the same holds for the board-specific point scales. The paper's own "best direction 0.85 / 0.89 / 0.93" for mean/median/min shows the relation is transferable when the scales line up. As specified, R3 does not test whether the gap-to-price map is board-specific. Needed: repeat the transfer test with m- and scale-normalised quantities (price per task in task sigma units against the gap in sigma units; or the free-intercept/slope-by-m fit) and report whether the verdict survives; otherwise remove the transfer claim from the abstract and state R3 as "not transferable in raw units".

**M4 (must). Data sources and their benchmarks are not credited.** The Open LLM Leaderboard (board, its `contents` and `results` datasets) and the benchmarks it is built from (BBH, GPQA, MATH, MuSR, IFEval, MMLU-Pro) and the evaluation harness are not cited anywhere in the references; checklist item 12 is answered [No]. Cite them (real references only; Suzgun et al. BBH and Gao et al. harness are in the starter list) and name the licence information that does exist (HELM code Apache-2.0; `contents` carries a per-model Hub License column), so item 12 can be answered on the basis of what was checked.

## Findings (may)
- m1. Abstract says the prices are solved "exactly for six rule families"; Borda and Copeland carry gaps up to 12%/7% on the sub-task board and are upper bounds. Say "exactly, or with a reported gap".
- m2. "Median-type" is used for median, plurality and Copeland (R1, R4, R5); plurality/Copeland are majority-type rules. Rename ("majority-type") to avoid reading R1 as a statement about medians only.
- m3. "H-L" in Table 3 is never introduced in the main text (§6.4 calls it "the hypothesis that summaries of the deficit profile ...") ; R5 rows ("3/4 of 4 units", "F/S") are hard to read. Label the verdict columns.
- m4. Main-text references to Fig. 3 and Fig. 4/5 (price map, targeting multiplier, calibration) point into the appendix without saying so; mark "(Appendix D)".
- m5. §6.3 "Why the ordering flips" reads as a log of numbers (medians over different subsets, three different unit conventions in one paragraph); move to one small table or the appendix, keep the one-sentence mechanism (plurality needs outright wins, each costing the gap to the best score) in the text.
- m6. Scope: prices are for 30 top-ranked targets (nearly all within reach of first). The question is what first place costs a target; show price against the target's official rank or gap for the 79 HELM targets already computed (E1/E3 ran on 79), or state this as the scope in the abstract.
- m7. Reproduction notes: add one line stating whether any page of the withheld study was encountered (deliverable.md asks for a record of any encounter).
- m8. R1 was pre-registered at m ~ 45 sub-tasks and run at m = 39 (data limit); say so where R1 is defined.

## Strongest objections the venue's reviewers would raise, and what answers them
1. Novelty/contribution: the main "price" results are definitional (mean price = m x gap) and the rest is "it depends". Answered in part by honest labelling, the exact solvers, the pre-registered refutations, and the crossing budget; the m6 scope (m1/m6) would help. Not a must.
2. The test the main claim rests on (R1, R4): R1 holds at one budget choice (median B* of the mean family), R4 at one; the paper shows other budgets (Fig. 2/4, B_x). Adequately answered.
3. Noise claim without method: M2. Transfer claim confounded by units: M3.
4. Baselines/related work: Zhang-Hardt, Chen et al., Lanctot, Dehghani, Singh, social-choice bribery are cited and positioned. Credit for data sources: M4.
5. Certainty of the numbers: cluster bootstrap with 11-13 independent clusters stated; solver gaps stated. Adequate.
6. Readability: dense but organised as a paper; m2-m5.

## Conclusion
Version 1 is not approved at 7b6555ed7c9a: request changes for M1-M4. All other findings are `may` and do not hold the version. M2/M3 need analysis (experiment-repo); M1/M4 are the report's; M3/M2 text changes follow the analysis.
