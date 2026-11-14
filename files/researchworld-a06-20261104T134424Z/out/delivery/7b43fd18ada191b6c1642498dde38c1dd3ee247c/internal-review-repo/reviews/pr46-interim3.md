# Review of paper-repo#46 (interim version 3 into `release`)

Head inspected: `b1fd7e4d3e95c94a7fbe4aad503d8d9b675b3822` (checks: `hutian/delivery` success). Outcome: **approved** as an interim version.

## Inspected
- PDF rebuilt from `paper/` = committed `paper.pdf` text (25 pages); `quote_numbers.py` regenerates without diff; main text ends p.9, references p.10; no tracked .pyc.
- Opened Fig. 4 (disjoint/iid/procedures, Gaussian-max overlay), Tables 3, 4, 7, 8 and the setup/compute table at reading resolution; all legible, labelled.
- Checked against results: matrix is 21x2000 (accuracy 15.2-20.8%, mean 18.2%, sd 1.41 pp, mean phi 0.356); naive gap/coverage at K=21 (n=50/100/200/400: 7.7/5.2/3.3/2.0 pp; coverage .73/.78/.80/.82); iid arm 7.4/3.3/2.0; Gaussian-max check file: 54 cells, max |diff| 0.41 pp (0.0041), 5 cells with |z|>2. Real hybrid row now the median-unbiased version (RMSE 4.8 pp, coverage .965); the earlier stale hybrid/conditional rows are gone.
- Resolved since v2: K=21 real arm with iid arm and SH/SR replays (#3 partly), real-matrix Gaussian-max check and generator calibration with disclosed residuals (#4), Table 1 estimand (#6), real equal-item protocols, re-timed run times, no forward reference to "regenerated" results.

## Minor, not blocking
- Abstract "predicts it to within 5%": at K=21 the disjoint n=100 difference is 5.3% and iid n=800 8.5%; say "about 5%" or give the range.
- Calibration (Table 8) agrees to ~8%/-5% on average but |z|>2 in 23 and 12 of 54 cells; the text says "not exactly", acceptable.

## Still required for `final`
- Real scale: K=21 of 60 with a 1.4 pp spread; K=60 (31 of 60 complete at the time) or the real claims clearly rescoped everywhere incl. title ("Reliable Reporting"); still no adaptive optimiser run, no real leakage arm or two-system comparison (stated as not done). If K=60 lands, the greedy arm and the text/tables must be regenerated from one snapshot and re-checked by me.
- Everything frozen: no wording about pending results.
