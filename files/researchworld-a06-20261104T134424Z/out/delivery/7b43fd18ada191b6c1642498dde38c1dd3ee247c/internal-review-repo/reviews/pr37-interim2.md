# Review of paper-repo#37 (interim version 2 into `release`)

Head inspected: `d4c10c7bd7e5409c295b4c9cb7c192b615da82f2` (checks: `hutian/delivery` success). Outcome: **changes requested** (one reproducibility/consistency defect, cheap to fix; the rest improved).

## Inspected
- PDF rebuilt from source = committed `paper.pdf` (24 pages; main text ends p.9 with references starting there); `quote_numbers.py` regenerates; `__pycache__` pyc no longer tracked.
- Opened appendix tables 1-7 and Fig. 5 at reading resolution; main figures unchanged from v1 review.
- Appendix A (definitions + validation of conditional/hybrid), the equal-budget protocol table (Table 2), margin-based claim rates, pass/fail counts: present and consistent with `results/README.md`.

## Resolved since v1 (external #5-#9, #11 in large part)
Hybrid out of the abstract's headline; K=2 closed-form/PIT/replication-port validation and heavy-tail diagnosis; fresh-set and equal-budget protocols; one-sided coverage counts; claim definitions; self-contained forbidden-material sentence; pyc removed.

## Findings open at this head
1. **Real-LLM Table 3 hybrid row is from the superseded estimator.** `results/real_summary.csv` was last written at the K=5 interim commit, before `analysis/lib.py` changed the hybrid point estimate to the hybrid median (README: "always within x ± c_beta sk"). The table shows hybrid bias -11.56 pp / RMSE 51.7 pp at n=50 (sigma ~ 5-6 pp, so a point estimate confined to x ± c_beta·sk cannot have that RMSE); the synthetic hybrid file was regenerated (bias -0.2…-1.7 pp, RMSE ≈ 5-8 pp). So the delivered code does not reproduce the delivered real table, the text's statement that the hybrid's point estimate is the hybrid median is contradicted by the real table, and REPRODUCE's "every number regenerates" fails for this row. Fix: rerun `analysis/run_real.py` (≈1500 s at K=5) with the current `lib.py`, regenerate `real_summary.csv`, Table 3, and the real-section sentences quoting hybrid RMSE/bias (also the cond/hybrid "midpoint" note in the table). Check that no other results file with hybrid/cond columns (ranking, compare, fresh_protocol_real) predates the lib change. Owner: experiment-repo, then figtab/paper.
2. Text typo: "meets the criterion in only 1 cells" (Sec. 4.1) - fix the generated plural.

## Still required for `final` (not blocking this interim)
- Real arm at materially larger K (or rescoped claims) and the iid check arm; real gap vs K with the Gaussian-max overlay; real-matrix check of the formula; generator calibrated to the real matrix (external #3, #4); an adaptive search on the real benchmark if budget allows.
- Novelty/premise evidence (external #10) and the recorded run times (external #11).
