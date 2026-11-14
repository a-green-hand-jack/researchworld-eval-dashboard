# Analysis audit corrections and authoritative numbers

Scientific inputs are unchanged: `protocol.md`, `main_manifest.json`, and `train.py` still match the local freeze. All205 final runs have the original frozen training source hash. No run, endpoint definition, threshold, budget or seed was changed after outcomes.

The independent audit initially reviewed `analyze.py` before these small reporting changes:
1. The misleadingly named `conservative_wilson_difference_envelope` JSON field was renamed `uncalibrated_difference_of_95pct_marginal_wilson_intervals`, with an explicit comment that it has no automatic95% paired/simultaneous coverage. Its value is not used as a confidence interval in the paper.
2. Generated width-table medians now use exact `g` formatting, retaining1087.5/887.5/737.5 instead of rounding to integers.
3. `main_table_full.tex` wraps the generated rows in a complete tabular, avoiding a LaTeX alignment error with booktabs/input expansion. Numerical table entries did not change apart from the corrected display precision.

After these changes the independent numerical audit was rerun successfully. Its7475 checks still pass. `independent_audit.md` is the original time-of-review report and describes the pre-label-fix script; this note records integration fixes rather than rewriting history.

## Authoritative analysis
- `runs.csv`, `audit_endpoints.csv`: five-evaluation canonical endpoints from raw metrics, not three-evaluation summary clocks.
- `audit_checks.json:primary_exact_bootstrap`: quoted P1 confidence limits, including adjusted component limits. Exact weighted empirical-bootstrap enumeration removes optional-extension/RNG-order Monte Carlo drift; it is not exact population coverage.
- `audit_checks.json:P2_uncertainty`: calibrated conservative bounds and cellwise Wilson intervals. The bootstrap[1,1] is retained but not interpreted as population certainty.
- `audit_sensitivity.csv`: includes delay ratios3/10 in addition to threshold/persistence grid, supplying the original script's omitted ratio sensitivity.
- `random_label_null.json`: additional post-hoc orbit-respecting conditional null. Its modest excess is disclosed, not used to claim a clean negative-control pass or to select/retrain runs.

Recompute in order: `analyze.py`, `analysis/independent_audit_recompute.py`, `analysis/independent_audit_supplement.py`, `random_label_null.py`, `generate_tables.py`, `plot.py`. No extra training is involved. See README for complete commands.
