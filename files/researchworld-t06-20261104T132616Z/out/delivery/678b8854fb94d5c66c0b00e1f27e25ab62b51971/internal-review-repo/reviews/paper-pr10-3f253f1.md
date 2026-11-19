# Review of paper-repo#10 (interim, into release), head 3f253f1

Inspected: paper/main.pdf (15 pp, 8 main) and main.tex, all 5 main figures and Tables 1-4 as rendered, code/REPRODUCE.md, results/adv_budgets.csv, hutian/delivery status (success).

## Checked and holds
- quoted_numbers.py regenerates quoted_numbers.tex byte-identically; figures/make_all.py (with absolute --results/--out) regenerates all tables identically and all figures (PDF bytes differ only by timestamps).
- Raw data re-downloaded, sha256 match REPRODUCE.md. Independent check (own scipy L-BFGS BT fit on raw rows, ridge 1, tie = half win): base gaps match (Arena 0.8637, MT-human 0.376); the removal sets returned by the shipped search for the Arena C1 claim (455 rows) and MT-human C1 (91 rows) were applied to raw rows and the independent refit flips both (gap -0.0027, -0.0037). Verified-upper-bound claim holds.
- Figures are legible, labelled, non-blank, and match the text numbers. PENDING items are marked, not filled with numbers. Item 8 handling is disclosed and consistent with idea-repo Brief.

## Blocking finding (F1): Arena claim set excludes the real runner-up
Claims on Arena (and pooled NBA) concern the 20 participants with the most comparisons, not the leaderboard order. On the full 64-model fit (my run, shipped code, ridge 1): rank 1 gpt-4-1106-preview 210.4 Elo (7387 cmp), rank 2 gpt-4-0125-preview 209.0 Elo (1160 cmp) - excluded from the claim set; gap 0.0081 ln-units; verified flip budget of "gpt-4-1106-preview is top-1" = 3 comparisons (vs 455 in the paper). rank 5 qwen1.5-72b-chat is also excluded. Consequently the headline "top-1 needs 0.79% of Arena, random removal of half never changes it" (abstract, intro, Sec 4.3, Sec 5 "well separated statements need ~1%"), Fig. 1 (ranks 1..20 inside the subset), Fig. 2/3/4, Table 2/4 Arena rows describe a leaderboard that is not the Arena leaderboard, and the Arena conclusion is reversed for the actual top-1 claim. NBA pooled top-3 are all in the eligible set, so it is unaffected for C1.
Needed: define claims over all participants (or all challengers of each claimed participant: c1_challengers), rerun Arena C1/C2/C3 on the full set or on a top-by-score window, state the eligibility rule and its consequence in the abstract, and relabel Fig. 1 ranks as in-subset or show the full order.

## Other findings
- F2: abstract, Sec 2 ("after idea-repo's literature review" - internal process wording), Sec 4.3/5 and Appendix ("[PENDING: details]") carry open markers; controls (synthetic / N-matched), tie-handling and lambda ablations (31% of Arena votes are ties, handled as half wins), exhaustive check and budget intervals are not in the paper although rigor criteria require them; results for several already exist in experiment-repo (bfa92d1). Acceptable for an interim only if F1 is fixed; required for final.
- F3: README says `make_all.py` regenerates everything but gives no arguments; with a relative --results it fails (subprocess cwd differs). Document `--results <abs> --out <abs>`.
- F4: Table 3 covers 48 claims; the text does not say how they were chosen.
- F5: pooled regression slope 0.81 with CI [0.67, 0.86] (estimate near upper end) is dominated by 1371 NBA-season claims; state how many independent clusters/seasons and Arena/MT points (5 datasets) carry the pooled claim.

## Conclusion
Request changes. Approve once F1 is resolved and the interim marks are consistent with the numbers shown.

---
# Round 2: head 2e6b899
Re-inspected the PDF (16 pp; 9 main pages, venue checker OK), figures and tables as rebuilt, and independently recomputed on the raw Arena data with the shipped search: all 63 adjacent claims of the full 64-model fit give median budget 4 (paper: 4) - confirmed. Runner-up exclusion (F1) is now disclosed in the abstract and Sec 5 and the full-set evidence is in the ablation; exhaustive check (652 of 900), controls and ablations are in; F3/F4/F5 addressed. Remaining PENDING markers are explicit (full-set C1-C3 recomputation, NBA check, dataset-level intervals).
Remaining defect (F6): the Introduction headline (lines 42-45: "the top-1 claim of every dataset survives random removal of half the data yet can be changed by 0.15-6%") and Sec 5 "What the evidence says" (well-separated statements need ~1% on crowd data) are unqualified for Arena, contradicting the paper's own disclosure that the full-leaderboard top-1 against the excluded runner-up is far smaller. Qualify both with the 20-model restriction. 

---
# Round 3: head 534d20b
Diff from 2e6b899 is the two qualifying edits (intro headline, Sec 5) plus rebuilt PDF; F6 resolved, text in the built PDF matches. Venue checker OK, quoted numbers regenerate, delivery status success. Conclusion: approve as an interim version; remaining PENDING items (full-leaderboard Arena C1-C3, NBA check, dataset-level budget intervals, appendix details) are explicitly marked and must be closed before final.
