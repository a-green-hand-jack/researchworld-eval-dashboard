# Re-review of paper-repo#37 at head `6eb4bdd5dedb6f545731ad50aeb4d13535762930` (checks: success)

Delta from the head I rejected (`d4c10c7`): real Table 3 no longer prints bias/RMSE for the conditional and hybrid rows (dashes, with a note), the real-section text quotes no real conditional/hybrid point-estimate number, "only 1 of 106 cells" wording fixed. Rebuilt PDF = committed PDF (24 pages), quote_numbers regenerates, no real hybrid/conditional bias or RMSE remains in the text (grep).

Finding 1 of my previous record is resolved by withholding the non-reproducible cells; the coverage/width cells of the two rows are still from the older `real_summary.csv` (paper-repo states they are unaffected by the point-estimate change; the dither/hybrid-median change makes this plausible but unproven) and must be regenerated with the K>5 replay (experiment-repo#15/#16). Not blocking an interim.

Still required for `final`: real arm at larger K or rescoped real claims, the iid arm, real gap vs K with the Gaussian-max overlay and real-matrix check of the formula, generator calibration, premise/novelty evidence, recorded run times (external #3, #4, #10, #11).
