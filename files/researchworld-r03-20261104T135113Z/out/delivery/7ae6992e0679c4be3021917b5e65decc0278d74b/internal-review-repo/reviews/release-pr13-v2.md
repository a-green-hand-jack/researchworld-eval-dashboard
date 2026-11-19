# Review of paper-repo#13 (version 2 into release), head 7c9db567a715067d9bcbbe3eb61a8ad109e69112

## Inspected
- Paper text (23 pages), rebuilt from source in a clean copy: compiles, no undefined references, same page count as the committed PDF; main text ends on page 9. Figures 1-12 and Tables 1-11 opened and read (new: Fig. 10-12, Tables 9-11, HELM-Lite-28 row).
- `code/check.sh` run: prints OK (7.5 s).
- Numbers spot-checked against `results/summary`: family-cluster paired CIs for gv_fa vs random (k=1 -0.146 [-0.221,-0.061]; k=8 -0.039 [-0.066,-0.024]; contains 0 from k=12); "four informed selectors beat random up to k=16 under family CIs" (adapt_loc, dopt, fwd_ridge, mtl: all CIs exclude 0); per-repetition k* (GV 2,2,2 vs random 4,4,4); Table 10 k* by split vs the text (2/3/5, 8/3/6, 2/8/6, 4/2/6); out-of-range detector (flag rates, flagged/unflagged error 0.94 vs 0.12; temporal 2.5 vs 0.75); central vs gv_fa/dopt contrasts as stated.
- Findings of my earlier request paper-repo#10 and experiment-repo#6: all text items resolved (central-selector claim over the full k range, "shrinks to <=0.03", matrix count, equation reference, Fig. 7 rule stated, §6 recommendation restored with the measured detector behaviour and its MTEB-275 weakness, clustering/multiplicity caveats, theory as a sanity check, disclosure wording, README map, launch lines, raw-results release, plain-python check).

## Conclusion: supported as a second interim version
Claims in abstract, contributions, Sec. 5-6 match the shipped results and carry their scope (MTEB-dominated, random folds optimistic, shift results, no selector uniformly best, detector a warning). Cluster-robust intervals and k* intervals now back the "significant" statements.

## Open for final
1. The sparse MTEB primary run (objective's missing-cell setting) is still unfinished and stated as such; final must include it or keep the limitation in abstract and contributions.
2. Reproducibility statement (statements.tex) still says raw per-model tables are not versioned; they are now the release raw-results-1 (README says so). Align.
3. Related-work positioning against the two suggested low-rank/adaptive works is not done (they were left unread under the exclusion rule); acceptable, keep the log.
