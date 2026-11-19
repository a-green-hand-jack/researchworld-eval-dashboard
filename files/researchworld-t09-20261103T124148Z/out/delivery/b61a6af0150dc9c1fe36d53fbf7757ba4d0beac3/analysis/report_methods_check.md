# Integrated methods check

Inspected paper-repo revision d16ca864190583728935e4224fafdd0ce2708f5f, sections/evaluation.tex and
appendices/execution.tex against the frozen production config and graph/runner
source. The102-cell matrix, gamma1, R400, core/noise/imbalance graph counts,
independent design/panel streams, covariate seed g+123456, BFS seed g+97/target32,
ER/SBM/BA parameters and selected four-cell replay scope agree. The focused
imbalance slice is one graph seed, and no graph-population interval is implied
for that slice or the one public topology. Mean graph RMSE and pooled RMSE are
distinguished. The source/report uses no first-estimator/theorem claim.

The current PDF/source is still explicitly incomplete for production accuracy,
as required while the tracked job continues. This check validates methods and
execution descriptions only; final quantitative claims still need the complete
results and final integrated-report inspection.

Interval wording clarification already supplied to paper/figtab and requested
in story12: nonempty-arm DIM has HC3 and oracle intervals via own-treatment
regression. HT/Hajek have no interval implementation. Empty-arm DIM is undefined.
The analysis methods source has this correction without any numerical rerun.

Paper's initial PR11 status-note concern was a two-tree comparison mistake.
Its approval and follow-up explicitly withdraw that concern and say the merge
preserved the current manuscript status. No paper-owned path repair was needed
or performed by analysis.

## V1 numerical-authority withdrawal inspected

Inspected paper-repo66fd81b88b59f7c1b5657df009a64fd4a319ee64's actual
paper.pdf text after paper#16closed. It withdraws v1accuracy conclusions from the
active report, explains17/20and60/80cutoff errors, holds empirical/exact displays,
keeps structural graph inventory separate, and requires corrected all-panel
outputs/audits/replay/source-matched assets before final claims. This answers the
hold request. It is not a validation of corrected results, which are still
computing. No smooth-model numerical survival is inferred from this inspection.
