# Review of paper-repo#9 (interim report into release), head 59a8815531b50aafcc3b9952862e89e995cdeb39

## Inspected
- Paper text (all 19 pages, `paper/paper.pdf`), every figure on the page (Figs 1-10) and every table (1-8).
- Rebuilt `paper/` from source in a clean copy: compiles, 19 pages, no undefined references; main text ends on page 9 (ICLR 2027 limit 9, appendix/statements outside).
- Re-ran `code/figtab/make_all.sh` on the committed `results/`: LaTeX tables byte-identical to `tables/`; figures regenerate (PDFs differ only in metadata).
- Spot-checked text numbers against `results/summary`: MTEB-56 krr k=4 (random 0.301, GV 0.222, D-opt 0.203, lev 0.385, qr 0.366, kcenter 0.336, central 0.279; RMSE 7.8/6.8/6.6), floors (krr 0.152, fa 0.181, mean 1.043), oracle k=1,2 (0.292/0.225 vs GV 0.424/0.271 vs random 0.570/0.415), Table 1 k* statements, Table 8 synthetic statements, leak table: all match.
- Proofs of Props 1-2 checked by hand: correct (Jensen lower bound, Wishart inverse-mean upper bound, submodularity of log det).
- Citations spot-checked (Federiakin 2501.17200, Meng 2010.14013, Sloth): exist. No forbidden-content item seen; log stated.

## Conclusion: supported as an interim version
Protocol holds out whole models with selection and fitting on training models only, fixed targets, bootstrap CIs over held-out models, pre-stated gap-closed criterion, random/popular/spectral/greedy baselines, oracle and leakage checks, shift splits, theory checked on synthetic and real. Claims are scoped (MTEB embedding models; short curves for LLM matrices), negative results (spectral heuristics worse than random, temporal failure, cost-aware instability, Bayes-curve optimism) are reported. Unfinished work (MTEB-sparse primary run, synthetic miss50) is named as unfinished in the paper and README, with no numbers from it.

## Non-blocking points for the final version
1. Missingness: the objective's sparse-matrix setting is covered only by near-complete blocks, random extra deletions, and synthetic data until the MTEB-sparse run finishes; the final must include it or keep the stated limitation.
2. Fig. 8a plots FA inference (y-label says so) while Sec. 5.3 cites the kernel-ridge oracle/random values (0.29/0.23, 0.57/0.42) and points to Fig. 8; the curve values on the plot differ (e.g. random k=1 about 0.64). State the rule in the text or plot krr. Same for Fig. 8b (rule not given in caption).
3. Cosmetic: "Eq. equation 1" in Sec. 3; Fig. 10 has no legend; Fig. 9d legend overlaps points; "24-48" k*(0.9) range for MTEB-357 includes a random-selection value in a sentence about informed selection.
4. Bootstrap is over held-out models, not families; with correlated models within an organisation intervals on random folds are likely somewhat narrow (the leave-family-out split partly addresses this). Worth a sentence.
5. Raw per-model tables are not in git, so raw -> summary is verifiable only by re-running; this is disclosed.
