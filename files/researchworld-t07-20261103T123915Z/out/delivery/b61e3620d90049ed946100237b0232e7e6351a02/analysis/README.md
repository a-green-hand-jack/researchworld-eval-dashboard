# Reproducible few-item benchmark prediction analysis

This repository supplies the analysis for the frozen research objective. Read `notes/methods_frozen.md`, `notes/crossfit_difference.md`, `notes/result_schema.md` and `notes/resource_freeze.md`. The complete study and its score/rank/robustness evidence are delivered in `results/study/`. Read `notes/results_interpretation.md` for the measured findings, supported conclusions and limitations. Every required scenario completed; documented post-scoring numerical-rank correction and a failed/repaired supplemental diagnostic are preserved.

Use Python 3.11+ with the exact versions in `requirements.txt` / `results/environment.json`. CPU only; no LLM calls or paid API. Run from this directory (in the integrated delivery: `cd analysis`).

```bash
python3 -m pip install -r requirements.txt
source scripts/env.sh
python3 scripts/fetch_data.py
python3 scripts/audit_data.py
python3 tests/test_design.py
python3 tests/test_mirt_gradient.py
python3 tests/test_aipw.py
python3 tests/test_guard.py
python3 tests/test_metrics.py
python3 tests/test_macro_pairing.py
python3 tests/test_pipeline.py
```

Data are the 13 public binary matrices at upstream commit `55faff496947789f94e6b5908c77cbc3e84f81ad`. `results/data_manifest.json` and `config/data_manifest.json` pin every downloaded input. Raw files are excluded from git. Repeated identical model names are identity-deduplicated with a recorded original-row map; other response collisions remain in primary results. HELM identities are opaque row IDs. Acquisition uses only explicitly authorized frozen data paths.

The committed `config/` is the study configuration, including the explicitly archived pre-target scoring amendment in `notes/freeze_amendments/2026-11-05_macro_pairing.json`; estimator/tuning/split/draw rules are unchanged. The committed configuration is immutable after that amendment; do not regenerate it to reproduce a run. `python3 scripts/freeze.py` is its generating command and checks the original pilot partitions, but it belongs to pre-target study design. Before changing it, ensure no target result exists and record the dated amendment with the plan/feasibility owners. Development/final seeds have disjoint deterministic namespaces and budgets are nested within each draw. Final target membership never changes.

```bash
# All fitting, tuning, and historical refits; no target evaluation:
python3 scripts/run_study.py develop
# Only after independent feasibility and ownership gates are recorded in config/gate.json:
python3 scripts/run_study.py predict
# Requires every expected prediction file; computes truth, metrics and uncertainty:
python3 diagnostics/score_canonical.py
```

For persistent CPU jobs use `ht-resource run local-compute --cwd <this-directory> -- bash -c 'source scripts/env.sh; python3 -u scripts/run_study.py develop --benchmarks ...'`. Independent benchmark subsets can run in two single-thread jobs if host capacity allows. Resume commands reuse identical source caches/development selections and completed prediction files. Do not run the same benchmark/scenario cache concurrently.

All45 scenarios completed219 source fits (168 development+51 selected refits), all successful under the declared relative-objective stopping rule;13 used continuation. The218 unaffected fit components total1312.55s elapsed; one suspension-affected record is preserved and a separate identical-source replication took173.82s elapsed/173.78s CPU. These are component measurements, not a fabricated end-to-end source CPU total. The supplemental same-configuration source replay used1460.129 CPU seconds and1155.498s observed parallel wall time. It matches219 fits/45 selected-parameter packages but retains one GSM development anchor-ridge loss-grid mismatch (same selected alpha1); all78 final anchor selections/mean predictions reproduce exactly. See notes/compute_accounting.md. A fresh fit+tune run on comparable hardware can be budgeted roughly30–60min as an extrapolation; the pre-study12–24h largest-fit bound is retained historically in resource_freeze.md. Source fitting is cached, and results rendering needs no fits. In a disposable fresh-run copy, clear only the study fits/development/predictions caches, retaining configuration and historical diagnostic archives, before running develop/predict again.

The two complete cache-reusing prediction commands took37.75s and29.83s elapsed concurrently (67.47 process CPU seconds total). Corrected full scoring took237.37s elapsed/237.24s CPU, peak RSS about1.20GiB. Saved-output audits/formula/summary generation take seconds to about1.5min per diagnostic. Exact per-command thread settings, CPU/elapsed/RSS and exit statuses are in results/study/execution/. Host contention can change these times; do not sum reused per-method source costs as aggregate execution cost.

Final result schema is in `notes/result_schema.md`. Prediction files omit target truth; retrospective scoring adds it after all predictions exist. Every figure/table should be generated by presentation-owner code from these saved results, without refitting merely to render. The integrated `presentation/manifest.json` belongs to the presentation owner and maps each display to its generator and inputs; this analysis does not author those final displays.

Literature/code access is logged in `notes/literature_access.json`; only explicitly permitted sources/direct pinned code were consulted. The candidate's residual correction is not claimed novel or superior. MAP-MIRT is a disclosed adapter, not exact tinyBenchmarks variational fitting. Data/license and unresolved upstream identity limits are reported in the accompanying notes.

Post-scoring verification and report inputs (run after `score_study.py` finishes):

```bash
python3 diagnostics/audit_scoring.py
python3 diagnostics/check_aipw_formula_reconstruction.py
python3 diagnostics/aipw_formula_diagnostic.py
python3 diagnostics/summarize_results.py
python3 diagnostics/write_evidence_note.py
python3 diagnostics/check_formula_outputs.py
python3 diagnostics/summarize_rank_precision.py
python3 diagnostics/verify_rank_correction.py
```

Read `config/gate.json`, `config/gate_followup.json` and `notes/execution_gate.md` together for the precise prospective-decision/execution chronology; the original authorization record is preserved without backdating the later formal scorer-hash extension.

The final scoring entry point is `diagnostics/score_canonical.py`. It calls the frozen scorer with documented numerical rank/tie canonicalization, retaining raw predictions for every score-error calculation. The original exact-float rank outputs are archived for review in `results/study/original_raw_ties/`; they must not feed final ranking claims. Read `notes/postscore_amendments/2026-11-05_rank_numerics.json` and reproduce the independent invariant/precision checks with `diagnostics/check_rank_numerics.py` and `diagnostics/audit_rank_precision.py`. This repair was made after initial scoring, not presented as a prospective tuning choice.


Supplemental full-source timing is reproducible independently of the primary caches. From the preserved delivery (with all original source fits and final evidence intact), prepare a fresh sibling workspace. The setup refuses an existing workspace. Run the two benchmark groups in separate measured processes; sequential execution is also valid, but changes elapsed-time interpretation. Run the audit only after both commands finish.

```bash
# In this analysis directory, with scripts/env.sh already sourced:
python3 diagnostics/setup_source_timing_replay.py
cd ../source-timing-replay
source scripts/env.sh
python3 diagnostics/run_measured.py --record ../analysis/results/study/execution/source_replay_A.json -- python3 scripts/run_study.py develop --benchmarks mmlu_pro ifeval arc_challenge commonsense gsm math med_qa
python3 diagnostics/run_measured.py --record ../analysis/results/study/execution/source_replay_B.json -- python3 scripts/run_study.py develop --benchmarks bbh gpqa musr openllm_math legalbench mmlu
cd ../analysis
python3 diagnostics/check_source_timing_replay.py
python3 diagnostics/summarize_compute.py
```

The `../analysis` paths above refer to the integrated paper delivery. For a standalone checkout with another directory name, substitute its absolute path for each measurement path and return directory. The audit accepts `--replay-root <path>` if a different sibling location is used. Keep measurement outputs from a reproduction in a separate copy: the delivered files record the actual study, and their timestamps/hashes should remain available. The audit verifies original final-evidence hashes before any new summary generation. Fresh-run timings are new observations; no attempt is made to infer the original suspended source command's active CPU.

For a fresh complete study, retain the historical `original_raw_ties/` archive as directed above; `verify_rank_correction.py` compares regenerated canonical error fields against that historical artifact. It is a numerical-repair audit, not a requirement to repeat the obsolete raw-float scoring. Run `audit_rank_precision.py` before `summarize_rank_precision.py` when regenerating sensitivity inputs. All final rank claims use canonical outputs.


Supplemental measured cost is in `notes/compute_accounting.md` and `results/study/compute_accounting.json`: source replay1460.129 CPU seconds; the source replay plus original cached predictions and canonical scoring1764.841 CPU seconds (29.41 CPU minutes). This combines phases measured at different times and excludes acquisition, pilots, diagnostic checks, obsolete scoring, rendering and setup. The original source end-to-end CPU remains unknown. The replay preserves a one-grid GSM development-loss discrepancy with no changed selected alpha; it is not exact reproduction of every intermediate. `diagnostics/audit_anchor_reproduction.py` checks the final78 correctness/IRT anchor selections and mean predictions against saved original outputs at identical observed items, with no tuning or added target observations. It reproduced them exactly. A bounded1/2-thread diagnostic reproduces both loss grids exactly:1 thread matches the replay and2 threads match the original, with one of30 development representatives changed and alpha1 retained. This establishes numerical thread sensitivity; the original effective thread-pool count was not recorded, so historical execution settings are not inferred as fact. Preserve both loss grids in `source_replay_discrepancies.json` and `source_timing_replay_audit.json`.
