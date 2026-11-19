# Debug log — experiment.py

## Purpose
Fix German dataset loading under pandas 3 and prevent incomplete/mismatched stored cells from being silently skipped. Offline only; no training, SHAP computation, or full experiment execution.

## Setting / reproduction
- Read `experiment.py` and the failure in `experiment_main.log` (lines 472–529).
- pandas 3.0.6; before patch, `python -c "import experiment as e; e.load_data('german')"` reproduced `Cannot use median strategy with non-numeric data: could not convert string to float: 'A14'`.
- Original skip logic returned on `.npz` existence alone. Pilot is already isolated in `results/pilot`; no relocation or experiment-design changes made.

## Root cause / fix
German string columns are inferred as pandas StringDtype rather than object, so `dtype == 'object'` excluded all 13 categorical features and selected median imputation. Classify nonnumeric columns using `not pd.api.types.is_numeric_dtype(...)`, preserving existing imputation/encoding choices. Before skipping an existing cell, validate 4-D phi instance/repetition/budget axes, stored instance count and budgets, and JSON n/repetitions/background (8 normally, 16 for sensitivity). Background is in the JSON sidecar, not a phi axis. Missing/invalid metadata or mismatches raise; existing artifacts are never silently replaced.

## Results / verification
From `/work`, run `python debug_regression.py`:
- 3 tests passed (0.875 s); model fitting and Game construction are explicitly forbidden by mocks.
- German inferred/object/string/category inputs: `(1000, 61)`, all finite, 13 categoricals; train/validation/test = 600/200/200; instances/background = 30/16. Categorical features use most-frequent imputation + one-hot encoding; numeric features use median + scaling.
- Pima: `(768, 8)`, 0 categoricals; ACS: `(3767, 478)`, 7 categoricals; all finite. Dataset metadata output redirected to temporary directories.
- 16 synthetic resume scenarios passed: normal/sensitivity matches skip; pilot-size, repetitions, rank, budget-axis, instances, budgets, report n/repetitions/background, missing/corrupt report, and missing phi reject. Artifact bytes unchanged in every scenario.
- Additional read-only check: all 12 existing main `.npz` cells validate for n=30/repetitions=20/background=8. Isolated pilot phi `(2, 3, 4, 8)` rejects a main request `(30, 20, 4, d)`. SHA-256 hashes of every existing results file were identical before/after this check.

## Artifacts / next steps
- Production change: `experiment.py` only, categorical detection plus fail-closed resume validation.
- Exact production diff: `experiment.patch`.
- Repeatable loading/synthetic-resume regression checks: `debug_regression.py`.
- No full experiment was restarted. A future main run may resume compatible completed cells; mismatches require explicit operator resolution rather than replacement.
