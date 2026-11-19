# Completed evidence and integration checks

All main and changed-background computations completed and passed their full saved-vector/source/grid/seed/reference/endpoint/rank audits. Main97200calls/540refs; separate background5760calls/144refs. No failed attempts. Main capturedwarnings0; background18non-numerical Matplotlib deprecations retained/disposed. The numerical claims and limits are in notes/main-evidence.md and notes/background-evidence.md.

Main is supplied by paper PR16. Deliver the final background supplement and reproduction clarification, then close evidence requests#3/#4 with concrete paths. Fresh-root regeneration is required because released checkpoints omit joblib models; README now states audit-only versus recomputation commands, and results/reproduction_preflight.json verifies an actual fresh single-input/180call rerun matches exactly. Do not change frozen attribution sources/config.

Remaining own work after supplement: check the integrated results/text/figures when paper/presentation deliver them, resolve requested analysis corrections if any, and make every supplied claim traceable. Final report/figures and release decision belong to their owners.

Paper follow-up requested whole-study cost accounting. This is now supplied by scripts/computation_ledger.py, notes/computation-ledger.md, results/computation_ledger.{json,csv} plus archived completion/resource records. Selected disjoint process clocks28206.958919seconds are an incomplete recorded subtotal; sampled managed counter and postprocessing costs stay nonadditive. Failed TreeExplainer/precision/setup/local validations without CPU clocks are explicit unknowns. Update PR17 with this final requested ledger before closing request#3.
