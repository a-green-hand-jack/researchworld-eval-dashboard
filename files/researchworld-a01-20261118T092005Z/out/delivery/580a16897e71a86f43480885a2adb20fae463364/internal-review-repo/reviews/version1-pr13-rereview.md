# Re-review of Version 1 (paper-repo PR #13, main 40d9e36a5115 into release)

Document read: `document` branch `main/document.pdf`, built-from 40d9e36a5115eb6fd3670ddb24277d3e26e19e84 (= PR head). 23 pages: 9 main, references, appendix A-E, checklist. Earlier record: `version1-pr13.md` (head 7b6555e).

## Answers to the must findings
- **M1 answered.** Abstract, intro bullet 2 and §6.2 now say "no rule is cheapest for 90% of targets on any board" and "which rule is cheapest depends on the board"; the majority shares (73%, 53%, 67%) are stated in §6.2 and Table 3.
- **M2 answered.** Appendix C gives the noise model (Gaussian on every cell, rivals included; binomial sd on HELM, reported SE on the sub-task board), the margin definition for mean/z-mean/median/min (sd of the rule's own aggregate difference over 400 draws, unboosted and boosted-plan variants), the P(first) estimator and its Monte-Carlo error, and the grid to c = 12; Table 5 gives share/c/depth ratio per rule on both boards. The "median never reaches 90%" claim is withdrawn: every top-30 target reaches 90% under mean, z-mean, median and minimum; the stated difference is depth (3.4-6.7x vs 1.2-2.0x) and, for the median alone, margin. Abstract, intro and §6.5 agree with Table 5 and with experiment-repo#7. Plurality/Borda/Copeland are stated as not run with noise.
- **M3 answered.** §6.4 and Appendix C Table 6 keep the pre-registered raw-unit verdict and add the per-task and re-centred variants, labelled post hoc; the mean's raw-unit failure is stated as by construction (per task R2 = 1.00), the other six rules' failure is shown to survive. Abstract wording ("for the mean, only through the number of tasks") matches.
- **M4 answered.** Open LLM Leaderboard, its six benchmarks and the harness are cited; checklist item 12 answered Yes with the licence situation stated.

## Format
NeurIPS 2026 template, 9 main pages with floats (references start on p. 10), checklist present, anonymous, fonts as before.

## Open findings (may; do not hold the version)
- m-R3 (new): §5 says R3 is refuted "if the held-out R2 is at least 0.9", and the minimum reaches 0.93 (median 0.89) in its best direction, yet R3 is called borne out on the worst direction. State in §5 how the six directions are aggregated (worst-direction rule), as the Brief did not fix it, or say that the best direction of the minimum would count against it.
- m7 (carried): reproduction notes have no statement on access to the withheld published paper.
- m1-m6, m8 (carried from the first record): wording and presentation items, not repeated here.

## Conclusion
Approved at 40d9e36a5115 as a `release` version: no open must finding, claims match the evidence in the paper and in experiment-repo's delivered results.
