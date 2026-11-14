# Research and run record

All work was performed in `/work` on 2026-11-02 UTC. The task's one-week ceiling
was not needed; the selected low-dimensional CPU simulations run in minutes.
No research claims are based on unexecuted experiments.

1. Started from an empty workspace. Downloaded the official ICML 2026 template,
   exact starter-paper PDFs, and the provided SNAP graph. Installed a pinned
   Python 3.11 environment with single-thread BLAS execution.
2. Wrote `EXPERIMENT_PLAN.md` and implemented main, correlated-noise, scaling,
   saturation and validation experiments. Planned counts were 400 repetitions
   except validation (150). These counts were all completed, without early
   stopping, selecting seeds, or omitting unfavorable candidate results.
3. Ran `code/verify.py` before main simulations. Checks include endpoint feature
   contrasts, exact-fit calibration, conditional correlated-noise variance with
   30,000 independent noise draws, one-hop HT enumeration on a six-node cycle,
   and explicit rejection of an unestimable contrast. All passed.
4. Refined the preliminary pointwise curvature bound to the exact Peano kernel,
   and added `sensitivity` plus correct-indicator threshold-oracle diagnostics.
   The final verification script also checks the sharp bound and cubic Peano
   identity against dense numerical integration. This extension was not an
   initially preregistered analysis and is labeled as such in the paper.
5. Completed main/noise/scaling/validation/saturation runs. Exact elapsed times
   for timed suites appear in `results/*_run.json`; process output is in `logs`.
   Initial main/noise/scaling/validation/sensitivity times were approximately
   103/107/30/129/19 seconds, respectively. Independent processes partly
   overlapped. No GPU was used.
6. Main results showed unexpectedly good cubic OLS on Facebook relative to
   regular/BA graphs. Added an explicitly exploratory low-degree outcome
   exclusion study, preserving graph and target. After inspecting its results,
   extended it with equal-count uniformly random outcome deletion. Re-ran this
   small ablation in full with the control; reported output includes both.
   The main graph/assignment streams and original degree-cutoff results were
   unchanged. This control supports support effects beyond sample count, but
   still relies on homogeneous-response transfer.
7. Generated every figure/table and numeric macro from actual raw CSVs through
   `code/analyze.py`. The first LaTeX draft compiled successfully. A layout
   audit found two overwide display equations and inefficient float/checklist
   placement; display lines and placement were corrected without changing
   the official style, margins or font sizes. Final body is 7 pages, PDF 16
   pages, under the official 8-page submission-body limit.
8. In empirical decomposition checks, the largest absolute discrepancy among
   360 non-HT main summaries is about 4.045 paired MCSEs (SBM, cluster,
   correctly specified cubic fit; repeated across representable response laws).
   This finite-repetition deviation is retained and disclosed; we did not
   change seeds/counts to force agreement with the exact algebraic identity.
   Direct conditional-noise verification separately passes. Summaries contain
   every discrepancy and its MCSE.
9. Wrote executable `reproduce.sh`, data hash verification and artifact audit.
   A separate output directory is used for a full end-to-end reproduction
   check. All eight decompressed raw CSV files, all summary CSV files, and all
   generated numerical LaTeX fragments match byte-for-byte. Verification is
   recorded in `logs/reproduction_comparison.json`. Final derived tables add
   Wilson coverage intervals and a sensitivity-width table; derivation and
   LaTeX build were rerun in both directories after that reporting refinement.
   PDF binary hashes differ as expected from TeX build timestamps/paths.

## Failed and incomplete items

- One allowed SNAP source-paper PDF request returned HTTP 502. No contents
  were read; the data page is cited instead. See `SOURCE_ACCESS.md`.
- The first attempt to apply the matched-deletion/layout code patch failed
  context verification. It made no changes; the corrected patch was applied.
  No experimental run failed because of this edit.
- HT rare tails are unresolved by the selected repetition count; empirical
  zeros do not establish low risk. No importance-sampling or exact large-graph
  joint-exposure variance study was completed.
- Closed-neighborhood HT is intentionally an invalid exposure model for the
  two-hop response, and is labeled accordingly, not claimed unbiased there.
- High-degree threshold oracle fits are often inestimable, including every
  degree-128 main assignment. These are preserved as failures of estimability,
  not assigned an arbitrary pseudoinverse answer or silently dropped.
- RF has relatively poor endpoint accuracy and worse predictive MSE here;
  ridge's fixed mild penalty does not solve the dense-graph variance problem.
  All implemented comparator outputs are retained.
- Initial archive-unpack verification used a `tarfile.extractall(filter=...)`
  keyword unavailable in Python 3.11.2. Manifest/hash verification had passed;
  extraction was retried with the compatible API on our own generated archive.
  This did not affect research data or PDF results.
- No GNN, adaptive graph-feature selection, rollout design, feasible covariance
  estimator, unknown-curvature learning or repeated-graph-realization study was
  run. They are limitations/future work, not completed experiments.

No prohibited-source encounter was observed under the restricted direct-source
access strategy. The complete access record is `SOURCE_ACCESS.md`.
