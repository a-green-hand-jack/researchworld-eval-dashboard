# Analysis reproduction and evidence scope

This directory contains the analysis owner's code and numerical evidence. The study measures prediction-region coverage of a directly observed random composition. It uses fully synthetic data and no classifier, pretrained model, paid API, GPU or downloaded dataset. No prohibited paper, mirror, discussion or citation page was searched, encountered or read by the analysis position. Each collaborating position supplies its own literature/provenance statement to the report owner.

## Environment and smoke checks

Use Python 3.11 with NumPy 2.4.6, SciPy 1.17.1 and pandas 3.0.6. Scientific packages are provided by the research environment. Thread limits are set by the shell runner. From the delivery root:

```bash
bash analysis/scripts/check_core.sh
```

The checks test the rank boundary including infinity, ILR isometry/inversion, true-zero scoring on the original event, generator domains, missing-group behavior, and independently integrated region volumes. They are implementation checks, not the study's main evidence.

## Pilot and diagnostics

`configs/proposed.json` is the pre-freeze design manifest. Pilot outcomes are explicitly nonconfirmatory and are not combined with the final trials. The first reduced-integration exploratory pilot used 2 repeats per cell at 2^10 points and 8 centers per group; it also applied adaptation/group calibration outside the heterogeneous arm before the final comparison restriction. The implementation was still being stabilized, so its metadata does not pin an immutable source hash. Its measurements guide runtime planning only. A subsequent full-precision pilot uses an immutable committed worktree and records source hashes, peak RSS and exact arguments. The final study will use independent seeds.

```bash
bash analysis/scripts/run.sh --config analysis/configs/proposed.json \
  --output analysis/results/pilot --repeats 2 \
  --volume-power 10 --volume-centers 8
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 analysis/scripts/diagnostics.py --output analysis/results/diagnostics_extended
```

The first command documents the exploratory pilot's historical command; the final source includes the later comparison restriction and provenance improvements, so it does not reproduce the exploratory pilot byte-for-byte. The immutable full-precision pilot and all final results use pinned source hashes. The diagnostic saves actual 10,000-repetition continuous-score rank checks and independent uniform-simplex versus transformed-region integration at nested resolutions and four independent Sobol scrambles. Never interpret integration scrambles as independently refitted models.

## Study execution and summaries

After the manifest and feasibility gate are frozen, use its exact config and recorded arguments:

```bash
bash analysis/scripts/run.sh --config analysis/configs/frozen.json \
  --output analysis/results/confirmatory
python3 analysis/scripts/summarize.py \
  --input analysis/results/confirmatory/trials.jsonl \
  --output analysis/results/confirmatory_summary
```

`frozen.json` records the accepted immutable scientific configuration. Independent feasibility GO was returned in story-repo#11. The final-power pilot took 14.105 seconds for ten K=3 trials; the ~47-minute serial / up-to-two-hour shared-host forecast is planning, to be replaced by actual final metadata. No unrun outcome is described as measured. A tracked resource job, rather than a sandbox background process, executes longer runs. Each trial produces an atomic checkpoint; rows and individual area estimates are also exported in JSONL. `NaN` marks inapplicable/unmeasured quantities and is never a zero. Rows with `inapplicable_exact_zeros` retain their denominators and are excluded only from numeric averages explicitly requiring a defined score. Input hashes cover the generated X and Y arrays for each partition; fits and group scales are retained. Seeds, full configs, dependency versions and source hashes appear in run metadata.

`summary.csv` uses independent outer-trial means and two-sided Student-t intervals. `paired_contrasts.csv` subtracts two methods within each shared-data trial, then forms the same interval on the differences. A difference is method minus reference; negative volume favors the named method at the observed coverages. No per-test-point pooled binomial interval is used to claim uncertainty over independently refitted/calibrated models. All figure/table scripts are owned separately in `figures/`; their owner maps final visual items to these source tables.

## Domain and interpretation

`method_contract.md`, `design.md` and `proofs.md` define events, score formulas, zero transforms, DGPs, model fitting, numerical integration, assumptions and claims. Every final estimate must identify a manifest cell and independent repeat set. K=10 efficiency is intentionally unmeasured; its rows support coverage/applicability only. Finite smoothed-ILR full-domain status may be unknown unless a vertex excludes full coverage or a rigorous global bound certifies it; `full_status_unknown_rate` preserves this distinction. Infinite-threshold rate is exact. A QMC volume close to one does not certify a full domain.

## Failures and changes

- A working ILR-volume Jacobian missed a sqrt(K) factor; the independent simplex integral caught it before any experiment pilot. It was corrected and regression checked; no confirmatory evidence used it.
- The first implementation accidentally staged Python bytecode. Those artifacts were removed and ignored; they are not study inputs.
- Exploratory pilots are not evidence for rankings or calibration rates. All method/configuration changes before the confirmatory freeze are retained in git; post-freeze changes must be logged and rerun where affected.
- Any failed or incomplete confirmatory trial must remain visible in the failure/completeness record. Do not drop it silently or call an unrun requirement a negative finding.

The additional scripts `validate_results.py` and `audit_regions.py` check complete planned trial/method/group grids and independently recompute numerical area at matched recorded centers. The audit regenerates only test inputs from the recorded seed, verifies their SHA-256 against the stored input hash, and uses stored fitted coefficients/calibration thresholds; it does not refit a model or count integration randomizations as new scientific trials. Its prespecified trials/centers/resolution are in the candidate manifest. A lower-resolution smoke check against actual pilot checkpoints is stored in `results/audit_smoke/` and is not confirmatory precision evidence.

`numerical_allowance.py --audit <integration_audit.csv> --contrasts <paired_contrasts.csv> --output <dir>` forms paired high-resolution differences and applies the pre-outcome empirical allowance in design.md, retaining both raw and statistically enlarged intervals. Missing audits or enlarged intervals crossing zero remain unresolved. `region_cases.jsonl` records the first test observation of trial zero in each core K=3 cell for every applicable method, with original target, center, actual test threshold, X/group and input hashes. This is the reusable measured-case supply for figure rendering; contour candidates on zero faces require the explicitly stated score-domain handling.

## Frozen two-shard resource execution

The accepted scientific configuration is unchanged. The first fourteen K=3 cells, then five K=10 cells, are assigned alternately to shard 0 and 1. Each cell retains all 100 independent trials. From the pinned immutable worktree, launch these independent jobs:

```bash
ht-resource run local-compute --cwd /hutian/experiment-confirmatory --note 'Frozen confirmatory shard 0 plus prescribed numerical audit' -- bash analysis/scripts/run_confirmatory_shard.sh 0 /hutian/repo/analysis/results/confirmatory/shard_0
ht-resource run local-compute --cwd /hutian/experiment-confirmatory --note 'Frozen confirmatory shard 1 plus prescribed numerical audit' -- bash analysis/scripts/run_confirmatory_shard.sh 1 /hutian/repo/analysis/results/confirmatory/shard_1
```

Each runs the full prescribed power16/four-scramble audit immediately after its main cells. After both succeed, `bash analysis/scripts/finalize_confirmatory.sh` validates every checkpoint and provenance, rebuilds canonical exports from atomic checkpoints, checks the complete audit schedule, summarizes independent trials and executes the numerical-allowance rule. No append-log duplication can enter canonical inference. The runtime source pin, exact hashes, jobs and outcomes are recorded in `results/confirmatory/execution.json` after launch.

After finalized exports, derive planned group/coordinate/sensitivity summaries with:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 analysis/postprocess/study_summaries.py --input analysis/results/confirmatory/trials.jsonl --summary analysis/results/confirmatory/summary --config analysis/configs/frozen.json --output analysis/results/confirmatory/derived
```

This descriptive postprocessing inherits the frozen interval/unit rules; it adds no scientific trials or fitted procedure. It verifies common seed/training provenance for cross-cell paired contrasts and identical test arrays outside the specified prevalence shift. Cross-cell area contrasts are labeled descriptive and do not receive a ranking decision from the within-cell method-pair numerical allowance. Its source/input hashes are saved separately, so its later source does not alter the immutable generation/audit pin. An attempted pipeline check on the historical exploratory pilot exposed that pilot's missing immutable input provenance; that pilot is ineligible for these provenance-checked sensitivity summaries. The final-power five-cell pilot passed the remaining derived-summary branches.

## Reproduction on a regular CPU machine

The ResearchWorld job launcher is an execution record, not a dependency of the scientific code. An exported archive needs neither the original analysis git objects nor any bundled trial outputs. It **does** need an immutable execution identity before the final audit. That identity is now retained independently of the result directory at `provenance/frozen-execution.json`.

From the delivery root with the recorded Python packages, choose an absent or completely empty output root. The example preserves the bundled results for comparison and generates new trials in a different directory:

```bash
reproduction_root=analysis/results/reproduced
python3 analysis/postprocess/initialize_reproduction.py --root "$reproduction_root"
bash analysis/scripts/run_confirmatory_shard.sh 0 "$reproduction_root/shard_0"
bash analysis/scripts/run_confirmatory_shard.sh 1 "$reproduction_root/shard_1"
bash analysis/scripts/finalize_confirmatory.sh "$reproduction_root"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 analysis/postprocess/study_summaries.py --input "$reproduction_root/trials.jsonl" --summary "$reproduction_root/summary" --config analysis/configs/frozen.json --output "$reproduction_root/derived"
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 analysis/postprocess/audit_final.py --root "$reproduction_root" --config analysis/configs/frozen.json --output "$reproduction_root/final_audit.json" --source-mode files
```

The initializer checks the frozen config and all 16 original source-file hashes using only local files. It then writes **only `execution.json`**, with original source/config identity and an explicit not-yet-executed status. It copies no checkpoints, generated inputs, fitted coefficients, estimates, summaries, audit results, original resource jobs or timing records. A nonempty output root is rejected so existing checkpoints cannot silently enter this fresh reproduction. The shards subsequently create all new checkpoints and run metadata; finalization builds canonical summaries from those checkpoints; the final audit checks completeness and numerical policy. Initialization alone is not a scientific run or a passed audit. The original job-completion and cost records remain historical evidence about the original run, not measurements of the new machine.

For a clean archive with no bundled `analysis/results/confirmatory/` directory, use `reproduction_root=analysis/results/confirmatory` in the same block, including initialization first. The frozen template lives outside that removable result directory. The default frozen config stays at `analysis/configs/frozen.json`; all commands run from the delivery root. Do not add Python helpers to `analysis/scripts/` or modify its existing files before reproduction: the frozen runner records every Python file in scripts/ and src/. The initializer lives in postprocess/ to preserve the frozen source inventory.

The scripts above accept the custom output root at every stage. `analysis/postprocess/finalize_study.sh` is the historical canonical-root convenience wrapper, not the custom-root entry point. `evidence_report.py` reads canonical `analysis/results/confirmatory/` tables and original historical resource records. The delivered figure scripts instead read separately hashed frozen snapshots under `figures/source_data/core/`, `figures/source_data/final/` and `figures/source_data/diagnostics/`. Regenerating either a custom or canonical analysis output root does not update those snapshots. Default rendering reproduces the delivered original-snapshot figures; it does not consume newly run trials. Pre-study diagnostic snapshots are separate from the confirmatory experiment. The evidence report describes original measured resource records, so do not relabel those original costs as fresh-run timings. No original resource-job snapshot, checkpoint bundle, git history, result table or case file is a prerequisite for the initializer/shard/finalization/derived/file-mode-audit sequence. The source files, configs, helper/template and stated Python environment are the inputs. The final audit creates its own output and should run last, after the derived summaries.

Checkpoint exports are deterministic apart from timing/platform metadata; run timings and compressed-file byte hashes may differ across machines. Final audit checks actual data, expected identities/counts and numerical policy, not equality of machine timing. The analysis repository retains the original frozen source commit and supports the stronger audit with `--source-mode git` (the script default). The integrated report repository and exported archives need not retain that foreign git object; `--source-mode files` verifies recorded scientific source-file hashes and all result checks, and records this explicitly reduced source-verification mode. The completed original analysis audit used the stronger git mode. The initializer checks original pinned files without requiring git in either setting.

A controlled archive-only prerequisite check is recorded in `provenance/fresh-root-check.json`: initialization with no `.git` and no result directory, exactly one provenance file created, accepted original identity, rejection of nonempty roots/config/source mismatches, and final-audit parsing of that identity before its expected stop at the absent fresh shard metadata. This checks the fresh-output input gap; it does not claim a second 1,900-trial run.

## Verify reproduced evidence before presentation rendering

After the complete fresh-output block above succeeds, the supported connection to presentation is an explicit **scientific-equivalence gate followed by original-snapshot rendering**. From the delivery root, with the same `reproduction_root`:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 figures/scripts/verify_fresh_results.py \
  --fresh-root "$reproduction_root" \
  --analysis-root analysis \
  --report /tmp/fresh-presentation-equivalence.json \
  --render
```

The `--fresh-root` argument is required and accepts either the custom root above or a newly generated canonical root. It never defaults to bundled results. Write the JSON receipt outside the scientific input directories; only a previous verifier receipt may be overwritten. Omit `--render` to verify without rendering. This route requires the complete finalized 19-cell evidence and its own completed `final_audit.json`; initialization, a partial shard or an unaudited result directory is insufficient.

The comparison contract and full supported commands are in [figures/FRESH_RESULTS.md](../figures/FRESH_RESULTS.md). The gate checks the original snapshot/source/config hashes, fresh completeness and scientific audit fields, every consumed final scientific row/column, core keyed subsets and all saved region-case fields. Each consumed fresh export must match its own audit hash. Counts, statuses, flags, scientific keys and missing-value patterns must agree exactly; real-valued scientific quantities use absolute tolerance `1e-12` and relative tolerance zero. CSV row order, gzip container bytes and the recorded `method_seconds`/`trial_seconds` timing measurements may differ. Original core and final fixed-seed bootstrap exports use different trial orders: the gate verifies every archival core endpoint from fresh raw trial values in the original checkpoint-manifest order with the pinned interval function, while checking final endpoints directly. [core-bootstrap-order.md](provenance/core-bootstrap-order.md) and its exact replay receipt document that source-backed mapping; no uncertainty column is omitted.

Missing, duplicate, extra, changed or unaudited scientific inputs cause nonzero exit before rendering. A prior successful receipt cannot remain as the current result of a failed attempt. A successful gate permits `render_core.py`, `render_regions.py`, `render_final.py` and `render_full_tables.py` to run sequentially, explicitly rendering the **original immutable snapshots after scientific equivalence**. It neither replaces snapshots with fresh files nor certifies that new trials were actually executed. A scientifically different run requires a new attributed analysis/presentation handoff. A rendering failure is reported separately from equivalence failure.

Pre-study diagnostics remain separate: the gate verifies their original snapshot integrity, but `--render` excludes `render_diagnostics.py` and does not certify diagnostic regeneration. The independent generation command is `PYTHONPATH=analysis/src python3 analysis/scripts/diagnostics.py --output <separate-diagnostic-root>` (with the thread limits above). Its outputs do not enter the confirmatory finalizer and are not automatically substituted into the diagnostic snapshots. `python3 figures/scripts/render_diagnostics.py` reproduces the saved original diagnostic figures explicitly.

The presentation owner's [verification record](../figures/verification/README.md) documents positive and controlled-failure checks against the existing delivered exports, including byte-identical gated rendering of all 44 PDF/TeX/CSV outputs outside `source_data/`. The analysis-owned `provenance/fresh-presentation-command-check.json` records an independent invocation of the actual verification-only CLI against existing completed evidence. Neither check is a second 1,900-trial scientific execution or a fresh timing measurement of the original study.

## Completed run and final evidence

All 1,900 frozen trials and the full matched-center audit completed successfully. Use `analysis/EVIDENCE.md` for claim-to-result mappings and limits; `results/confirmatory/final_audit.json` for the complete checked inventory, hashes, cases and numerical decision audit. `summary/`, `numerical_allowance/`, `derived/`, `region_cases.jsonl`, and `key_evidence.csv` are the figure/report inputs. The core-only bundle is historical interim evidence and is superseded by these complete results.

The two scientific jobs consumed 2,401.187 resource CPU seconds and a 1,263.427-second parallel creation-to-end wall window (about 21.1 minutes); peak main-run RSS was 181,500 KiB. Measured main-run elapsed times were 1,077.780 and 1,154.991 seconds. These definitions and raw job outcomes are in results/scientific_resources.json and confirmatory/resource_jobs.json; the initially forecast 47-minute serial/up-to-two-hour allowance is no longer a measured-cost claim. Ordinary sequential reproduction has about 37.2 minutes of main-run elapsed work on this host, plus both audits and postprocessing; a different host can vary. The finalization job's separate resource record is results/finalization_resource.json. No scientific trial failed; the historical failed launcher affected no trial.

The final audit retains 159 out-of-range mean-area warnings in the tiny-epsilon zero arm (largest 1.000373924) without clipping. Treat this arm as numerically saturated near one, not as a geometrically impossible true volume or certified full domain. All 339 paired area comparisons have their scheduled audits; 76 are unresolved and 258 pass the purely geometric/statistical practical-resolution rule. Relevant achieved coverage still determines whether an efficiency interpretation is meaningful.

Regenerate the analysis handoff after final aggregation/audit with:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 analysis/postprocess/evidence_report.py
```

`provenance/access-inventory.json` retains all nine positions' attributed dated source-access statements and external retrieval details. It does not turn their individual statements into independent blanket certification.

## Dependency and generated-asset terms

`provenance/ASSET_TERMS.md` attributes the installed Python/NumPy/SciPy/pandas stack and its ordinary runtime dependencies, with unmodified local license/NOTICE texts and SHA-256 records in `provenance/package-terms/` and `dependency-terms.json`. It separately records original synthetic-code/data/result attribution and their unspecified project reuse terms; repository availability is not interpreted as a license grant. The original directly used package versions match the scientific metadata. This provenance-only addendum changes no frozen scientific source or result.
