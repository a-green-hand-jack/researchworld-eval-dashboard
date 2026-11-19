# Protocol changes, analysis additions and non-changes

## Governing record
`protocol.json` and the exact240 jobs in `confirm_jobs.json` were frozen before any seed0--7 training. The older `todos.md` / `design_review.md` are design sketches; they do not override the freeze. In particular, the final recipe uses70% data and20,000 updates (not the earlier30% /12,000--24,000 sketch), and includes capacity/robustness controls in the original frozen ledger.

## Experimental changes before freeze (exploratory only)
- Initial30%-data baseline failed to demonstrate delayed generalization within12,000 updates.
- A separate seed901 grid explored fraction.5/.7, width32/128 and decay.1/1. Four additional independent seed902/903 runs validated the.7/.1 setting; narrow width remained partly censored.
- Nine initial pilots used sourcev1. Additional absolute-energy/layer diagnostics, CPU/initial hashes and the matched-mean option were added before four validation pilots and all confirmation. The archived v1 bytes exactly match the early source hash. No main training algorithm changed during confirmation.
- The provisional16-pilot design was not treated as mandatory: exactly13 exploratory runs were used and retained. The final freeze discloses their selection and outcomes.

## After freeze
- **No experimental deviations:** no seed omission, horizon extension, optimizer change, split replacement, best-checkpoint selection, new width or new confirmatory family. Numerical failure and administrative censoring are distinct.
- The full projection formula, absolute energies, thresholds90/95%, normalization, modulus/subtraction/data-fraction controls and common-clock cadence/landmark checks were frozen or implemented before confirmation.
- **Static construction check:** an explicit eight-unit cosine solution was algebraically verified on exhaustive inputs after implementation. It is an expressivity sanity check, not a training run or learned test result.
- **Post-hoc descriptive stability audit:** late regression noticed during completed decay-curve review motivated `stability.py`. It reports retention, final99 and persistent-to-observed-end onsets. No new primary tests are added, no frozen event definition is changed, and the resulting endpoint is explicitly labeled post-hoc in the paper.
- **Post-review exploratory width summary:** the freeze designated remaining-width contrasts secondary. After full-grid inspection, all adjacent pairs plus64→256 are now tabulated under the unchanged shifted/capped estimand. The latter fully observed range has an opposite-signed interaction, but was chosen post hoc and carries unadjusted intervals, no new confirmatory claim. `secondary_width_audit.md` independently checks its numbers and unchanged primary family. There is no new training or amendment of W.
- **Technical repeat:** one exact width64/seed0 rerun tests numerical reproducibility; all401 non-timing rows match. It is not a ninth seed or part of statistical estimates.

## Interpretation changes required by evidence
- W's predicted negative interaction is contradicted; retain the negative finding rather than change the hypothesis or contrast.
- C128 is compatible only with first qualifying onset timing. Seven of eight half-decay runs finish below99%; do not claim durable acquisition or full-trajectory equivalence.
- C32 is mostly censored; non-rejection is not support for collapse. Its full20,000-update event incidence and its shorter common-clock incidence are different quantities.
- Exact representability at width8 rules out a pure expressivity explanation, not optimization inaccessibility. Width/decay contrasts do not identify a serial discovery--cleanup mechanism. Projection does not recover a named causal circuit.
