# Repeated-run SHAP reliability: executable analysis

This repository owns the analysis for the frozen ResearchWorld objective (issue#1; commitment#2). It supplies `analysis/` and `results/` in the integrated paper. Results remain conditional on the selected models, unweighted held-out row datasets and empirical interventional backgrounds. They are not causal or deployment-safety guarantees.

## Environment and acquisition

Python3.11; exact top-level versions are in `requirements.txt`, detailed installed versions in `environment-versions.json`. Install with `python3 -m pip install -r requirements.txt`. Set `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` for the reported CPU/thread policy. No GPU or paid API is used.

Run `python3 scripts/fetch_data.py` to download the exact public German Credit, ACS2018 1-year California and OpenML37 Diabetes inputs. URLs, original retrieval times, checksums and sizes are in `data/manifest.json`. Reproduction checks raw dataset hashes, rather than silently accepting changed upstream bytes. ACS uses folktables0.0.12 ACSIncome filtering, without survey weighting; source person-CSV row IDs survive filtering. Impossible zero clinical values in five Diabetes fields become missing and receive train-only median imputation. Detailed target/preprocessing choices are in `src/shap_reliability/data.py` and `models.py`.

Raw archives, fitted bundles and development smoke outputs are ignored by git. Census documentation from the actual downloaded archive is retained under `notes/source-snapshots/`; `notes/data-attribution.md` integrates the supplied source-use wording and preserves the context snapshot. No forbidden-paper search or accidental encounter occurred in this analysis work: network use has been limited to the prescribed public datasets and package installation.

## Verification

Run `PYTHONPATH=src python3 tests/test_estimators.py` and `PYTHONPATH=src python3 tests/test_metrics.py`. These test analytic/brute-permutation games, grouped features, exact Kernel/direct identity, efficiency, the primary event and denominator, matching repeatability normalization, and finite-boundary inference. A full fresh ACS preprocessing/fitting/prediction/reference check is `python3 scripts/preflight_acs.py`; its measured memory/efficiency record is `results/acs_preflight.json`.

## Main study

The configuration is `configs/main.json` after story's recorded freeze; `main-proposal.json` preserves the pre-freeze proposal. The runner refuses an unfrozen configuration. Regenerate a single cell into a fresh output root with `python3 scripts/run_study.py --dataset german --model logistic --output results/reproduction/main`. The60-input/30-repeat primary matrix is nine dataset/model cells, two estimators and three dimension-specific budgets. Run all cells sequentially with:

```sh
python3 scripts/run_queue.py --output results/reproduction/main german:logistic german:forest german:histboost acs:logistic acs:forest acs:histboost diabetes:logistic diabetes:forest diabetes:histboost
python3 scripts/audit_panel.py --input results/reproduction/main --output results/reproduction/panel_audit.json
python3 scripts/aggregate.py --input results/reproduction/main --output results/reproduction
python3 scripts/evidence_handoff.py --input results/reproduction
python3 scripts/audit_timing.py --input results/reproduction
```

Independent cell queues can run in parallel if memory/CPU allow; each predictor uses one thread. Every completed input is atomically checkpointed. Rerunning the identical source/config skips completed inputs; changed source/config refuses reuse. Metadata records executing code revision, signed source files, raw-data checksums, seeds/IDs, fitted-model quality, versions and hardware. Failures are recorded and stop the affected job for diagnosis; incomplete cells cannot be reported as a complete study.

The delivered `results/main` checkpoints can be independently audited and reaggregated without data acquisition or fitting. In the integrated delivery, work from `analysis/` and audit the existing evidence with:

```sh
python3 scripts/audit_panel.py --input ../results/main --output ../results/panel_audit.json
python3 scripts/aggregate.py --input ../results/main --output ../results
python3 scripts/evidence_handoff.py --input ../results
python3 scripts/audit_timing.py --input ../results
```
 This regenerates the delivery-root numerical inputs consumed by presentation scripts. To rerun explanations from scratch, use a fresh root: pass `--output ../results/reproduction/main` to the runner/queue and adjust every audit/aggregate/ledger/timing input/output to `../results/reproduction`. The packaged raw checkpoints include metadata but intentionally omit fitted joblib bundles; do not request resumption against those read-only delivered checkpoints without the bundles. Fresh-root execution refits deterministically and creates the bundles. A one-input/all180calls fresh-output regeneration check agrees exactly with delivered Diabetes logistic vectors (`results/reproduction_preflight.json`). Presentation owns the figure/table generation commands and mapping; its manifest links each display to these outputs.

## Evidence, inference and runtime

`notes/result-schema.md` defines every raw/aggregate output. Exact coalition enumeration supplies all540 fixed empirical-game references. SHAP0.50.0 Kernel uses raw-feature groups, probability/identity output and `l1_reg=0`; the comparator uses paired antithetic permutation paths with within-run coalition caching. Budget fairness uses measured model rows and CPU/wall time, rather than equating nominal sample labels. The primary event is normalizedL1<=.20 AND signed top3 overlap>=2/3, with floor.01 and threshold/selection sensitivities.

`notes/boundary-inference.md` specifies cluster uncertainty and conservative finite-sample claim guards. All-success observations cannot become a population95% reliability certificate. Pairwise comparisons are reduced once per input. The mean of30 explanations is separately labeled and charged30-run cost.

Measured pilot timing/projections and their limitations are in `notes/pilot-handoff.md` and `results/pilot_cost_projection.{csv,json}`. Main point projection is roughly7–8 CPU hours; the measured-ledger safety/reserve estimate is about13 hours against the supplied approximate24 CPU-hour planning target. These are projections until `results/job_costs.csv` records complete main jobs. German forest/HGB exact references dominate. Pilot inputs are excluded from the main panel; no pilot reliability value is a main result. `notes/development-log.md` retains corrections, negative controls and abandoned options. Optional background sensitivity is separately labeled, pilot-first and follows the primary study.

Completed main evidence and its claim limits are in `notes/main-evidence.md`; `results/claim_ledger.json` traces the complete numerical handoff. All nine main cells are measured/audited. Main whole-job CPU is7.49345hours; recorded elapsed clocks include large interruptions, exposed in `results/timing_audit.json`. Completed changed-background results remain separate.

The completed separate background-size/resampling arm is interpreted in `notes/background-evidence.md`. From this root, after main reproduction, run `python3 scripts/run_background_queue.py` then `python3 scripts/aggregate_background.py`. For integrated reproduction from `analysis/`:

```sh
python3 scripts/run_background_queue.py --main-results ../results --output ../results/background
python3 scripts/aggregate_background.py --main-results ../results --input ../results/background --output ../results/background_sensitivity
```

After fresh-root main regeneration, point the optional commands at `results/reproduction` (standalone) or `../results/reproduction` (integrated), and put their outputs under that same fresh root. The arm holds main models/input IDs fixed and changes one training-row background draw at each B8/B128 size; it cannot isolate size from resampling. Its 144 exact changed targets and 5,760 calls are separate from primary estimator-only evidence. Cell clocks exclude startup/data-loading overhead and captured import deprecations stay explicit.

Whole-study known/unknown computation accounting is in `notes/computation-ledger.md` and `results/computation_ledger.{json,csv}`. Regenerate with `python3 scripts/computation_ledger.py` (integrated: `--input ../results`). It deduplicates nested phase clocks, retains sampled resource observations separately and explicitly lists uninstrumented preliminary/failed/validation work;7.83527CPU hours is a recorded subtotal, not an exact study total.
