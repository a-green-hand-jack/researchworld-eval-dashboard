# Review record: paper-repo#18 (into `final`), head a91c064d1a4e94f0d562cc7ab2268f5a0b220dad

Inspected at that exact head (clone rebuilt from scratch in a scratch directory).

## Checks
- `bash paper/build.sh`: rc 0, 26 pages, no undefined or multiply-defined references; text of the rebuilt PDF is identical to the committed `paper/paper.pdf`. Main text ends on page 9 (ICLR 2027 limit); AI-use statement and self-audit present.
- `bash code/check.sh`: prints OK.
- Sparse run (`B_mteb_sparse`) checked against `results/summary`: column mean 1.06, factor-posterior floor 0.18 (`floor_B_mteb_sparse.csv`); conditional variance + FA 0.59/0.45/0.37/0.30 and random 0.65/0.52/0.42/0.33 at k=2/4/8/16 (`curves_B_mteb_sparse.csv`); paired gain −0.083 at k=4, CI excludes zero up to k=8 and not at k=16 (`paired_B_mteb_sparse.csv`); log-det worse than random at k≤4 (+0.173, +0.045); k* (G≥0.8, FA) 16 / 16 / 24 for conditional variance / random / log-det, and 0.9: 48/32/24 (`kstar_gap_B_mteb_sparse.csv`, Table 4 row). The text's reading (about 16 benchmarks needed; informed selection no longer shortens it; krr criterion met at k=2–4 only because its own floor is poor, 0.43) is supported.
- Counts consistent across abstract, contributions, §5, §6, Appendix C/D and self-audit: nine real matrices (four MTEB blocks incl. the sparse one, five generative-LLM matrices); "no unfinished primary run" agrees with the launch scripts (`launch_primary.sh`, `launch_sweeps.sh`, `launch_review.sh` include the sparse matrix).
- Figures opened and read (Figs 4, 6, and the page carrying the discussion on p. 9): populated, labelled, legible, MTEB-472 panel in Fig. 6 shows the wide, noisy sparse curve that the text acknowledges. Appendix tables 4, 6–15 and Figs 11–12 present and referenced; numbers cited from them in §5 match the CSVs spot-checked earlier (cluster, ood, temporal files).
- Items I set for final in the v2 record: sparse run (done), stale Reproducibility statement (fixed; raw results are release `raw-results-1`), related-work gap (the reviewer-suggested works are neither read nor cited, disclosed in README and Appendix C; consistent with the objective's forbidden-content rule).

## Minor, non-blocking
- README "Unfinished and failed work" still refers to "Fig. 4b and Fig. A3", which are script/file names; in the PDF they are Fig. 6 and Fig. 9 (the script-to-PDF map in the same README is correct).
- Fig. 4 has no sparse panel (the sparse matrix is in Fig. 6 and Tables 1, 2, 4); the PR text calls it "Fig. 4b".
- Sparse result rests on two CV repetitions and skips models with fewer than k scores; the paper says so.

## Conclusion
The delivery meets the objective and my commitment (#2): honest, reproducible, claims within the evidence, limits stated. Approved.
