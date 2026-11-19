# Model size and delayed modular generalization

This repository owns executable experiments, uncertainty analysis and reproduction
for the registered 204-run study in `configs/confirmatory.json`. All 204 registered runs are complete and independently raw-audited. All 23 cells,
registered paired contrasts and 13 sensitivity definitions are complete. The usable
analysis-owner handoff and its claim limits are in `reproduction/final_results.md`;
`results/final-study-summary.json` selects exact source-pinned values without new
estimation. Pilots remain excluded from confirmatory inference.

Start with `reproduction/README.md` for the environment, synthetic data, exact
commands, historical implementations and complete-study integrity gates.

- `code/src/`: deterministic CPU MLP training, exact arithmetic/data splits,
  event rules, uncertainty and resource forecasting.
- `code/scripts/`: registered grids, analysis, predictions, independent audit,
  sensitivities, attempt inventory and timed finalization.
- `configs/`: exact pilot, benchmark and confirmatory configurations/seeds.
- `results/`: measured curves, model/optimizer states, metadata, derived artifacts
  and hashed manifest for the latest checked snapshot.
- `environment/`: installed dependency versions.
- `reproduction/`: methods, commands, access/attempt history, resource/deadline
  records and dated scientific checkpoint handoffs.
- `code/archive/`: exact historical pilot and benchmark trainers.

A fresh reproduction uses new output directories and all 204 registered runs.
Completed configurations are verified and skipped; interrupted runs require an
explicit `--resume` and exact configuration/trainer match. Computation uses one
thread per run, with at most two independent tracked jobs in this study. No seed
replacement or performance stopping is used. Non-events from complete curves,
execution interruptions and unstarted registrations remain separate.

P1/P2 are supported within the registered recipe/window. P3's frozen-feature
fit-comparability gate fails, leaving its mechanistic interpretation unresolved.
Scope depends on optimizer/split/threshold choices; saturated restricted clocks do
not imply equal eventual learning. Complete science is ready for report/presentation
integration and independent exact-version review. Figure/table and paper delivery
belong to their owners. See the final handoff for CPU missingness and recovery,
precision, resource, access and interpretation limits.
