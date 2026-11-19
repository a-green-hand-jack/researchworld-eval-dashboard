# Regression GATE under network interference

This repository supplies the corrected 102-cell CPU study of regression-based global average treatment effect estimation. All planned cells completed: 40,800 assignment/noise repetitions, 2,937,600 estimator outputs and 306 exact one-hop HT risks. `paper.pdf` reports supported positive and adverse findings with uncertainty. **The complete report, corrected displays and portable reproduction workflow are supplied. Owner checks and independent review have distinct scopes; reviewed version status is recorded by the final-branch pull request and published release.**

The count-before-division exposure correction supersedes the first execution's numerical authority. All corrected empirical/exact-risk outputs, integer-event checks and selected replay are supplied; `analysis/exposure_boundary_correction.md` and `analysis/roundoff_v1/` preserve the defect and historical provenance. Pilot results are calibration evidence only. Do not pool them into production accuracy or resume superseded checkpoints as corrected results.

## Read and build

```sh
./build-paper.sh
```

Sources are `main.tex`, `sections/`, `appendices/` and `references.bib`. The build verifies the unchanged official NeurIPS 2026 assets; `venue/requirements.md` specifies the nine-content-page limit. The filled official 16-item checklist is `appendices/checklist.tex`, included after the appendices. Anonymous submission styling does not assert actual submission/acceptance. Measured build environment: TeX Live 2022/Debian, pdfTeX 1.40.24 and latexmk 4.79. References begin on a separate page to expose the main-content boundary.

## Install and reproduce

Use Python 3.11.2. Exact numerical dependencies are in `code/environment.json` and `code/requirements-lock.txt`: NumPy 2.4.6, SciPy 1.17.1, pandas 3.0.6, NetworkX 3.6.1, scikit-learn 1.9.1 and PyArrow 26.0.0. Display generators use measured Matplotlib 3.11.2.

```sh
python3 -m pip install -r code/requirements-lock.txt
python3 -m pip install matplotlib==3.11.2
python3 -m pip install --no-deps -e ./code
python3 code/scripts/download_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -m unittest discover -s code/tests -v
```

Run installation, download and tests from the delivery root. Then prepare a distinct workspace and run its copied source:

```sh
python3 code/scripts/reproduce_workspace.py prepare --workspace /path/to/reproduction
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -u /path/to/reproduction/code/scripts/run_study.py --workspace /path/to/reproduction
python3 /path/to/reproduction/code/scripts/reproduce_workspace.py postprocess \
  --workspace /path/to/reproduction
```

Preparation copies code/configurations, the downloaded public graph and reference documentation; it copies **no results**. If downloading after preparation, run the copied `code/scripts/download_data.py` first. Original receipts are labelled history under the workspace's `analysis/reference_delivery/`; fresh receipts are written separately. Preparation also supports an existing results-only workspace from the earlier launcher, preserving those results. It refuses an existing `code/` or `analysis/` layout. Postprocessing runs once per preparation and refuses to overwrite its receipt; preserve a failed workspace and prepare another results-only copy for a retry.

The copied launcher executes all three panels, exact one-hop HT risk, support bounds and summaries. Checkpoints are atomic; repeating the launcher resumes only source/config-compatible cells and refuses mixed-source resumes. Postprocessing regenerates all summaries, diagnostics, checkpoint/integer-boundary/raw-summary/decomposition/dependency audits, a selected four-cell replay, findings and the 94-row claim registry. All commands use the copied source/configurations and the reproduction's results. A successful `analysis/workspace_postprocessing.json` records each stage, commands, actual wall/CPU/RSS and output hashes. Original resource receipts are not new-host measurements. The three disjoint shards in the original corrected execution preserve the same complete configurations and per-cell streams as this sequential launcher.

Public input is SNAP's combined ego-Facebook topology, credited to McAuley and Leskovec (NIPS 2012): 4039 nodes and 88234 edges. `code/data/manifest.json` records the source URL, 218576-byte acquisition on 2026-11-03 and SHA-256 `125e84db872eeba443d270c70315c256b0af43a502fcfe51f50621166ad035d7`. The downloader rejects mismatches; `code/src/gatebench/graphs.py` documents simple-undirected processing and seeded graphs/partitions. The supplied SNAP page states no data license. Public bytes are downloaded from the source, rather than redistributed under an invented grant. Treatments, covariates and outcomes are synthetic; this is not actual platform experimental evidence.

The frozen design uses graph seeds 201–205 and production masters 2202601 (core), 2202602 (noise), 2202603 (imbalance); pilot master 89103 is separate. Every cell has R=400, eight mechanisms and nine estimators. Saved assignment/noise/prediction seeds and master-namespaced pairing IDs define valid within-cell comparisons. Different designs and panels have independent replicate streams. Fresh prediction outcomes are evaluation data unavailable to the estimator. All models/bases are fixed before observing outcomes, with no accuracy-selected grid.

## Verify delivered outputs and claim routes

Use the prepared `postprocess` command above to verify a new run. The paths below describe the delivered tree and the same paths within that reproduction. Individual stage commands and definitions are in `analysis/delivery_reproduction.md` and `analysis/supplementary_analysis.md`; running legacy stage commands at the delivered root regenerates its original receipts, so preserve those receipts before doing so.

Corrected raw files are `results/production_{core,noise,imbalance}` (Parquet, metadata and `exact_ht/` JSON). Complete summaries are `results/summary`; diagnostics, covariance/support/failure and exact-risk routes are `results/diagnostics`. `analysis/final_findings.md` and its 94-value `results/diagnostics/claim_evidence.csv` map selected findings to actual CSV hashes, selectors, metrics, denominators and uncertainty. `analysis/methods.md` specifies operational versus estimable-only risk, conditional-defined returns and interval scope. No undefined output is assigned zero error.

All 13 scientific/summary checks passed during integration. Delivered hashes for every raw/metadata/source/configuration and summary/diagnostic/findings input were checked, and the findings report/registry regenerated byte for byte. `analysis/supplementary_analysis.md` defines H1–H4 diagnostic outputs and uncertainty. The owner's complete raw-to-summary audit passed 73440 scalar and 48960 paired checks, preserving 280 all-undefined graph/model groups. The supplementary audit checked 676164 comparisons and 5256 independent contrasts. The separate integer-event audit replayed all 40800 assignments using exact cutoff inequalities without model refitting. These are internal validity checks, not independent research review.

The completed selected clean replay covers four structurally selected cells (regular n=2000, degree 4/80, seed 201, both designs, all R=400): 115200 rows, every column and Parquet hash matched, measured 84.09 seconds. It is neither a full-grid replay nor an independent implementation. `analysis/reproduction_audit.json` preserves source hashes and the receipt. `analysis/v2_dependency_audit.json` confirms all 102 graph/config metadata records and 36 adjacency identities match the superseded execution; it validates structural reuse, not old numerical outputs.

The portable-workspace validation is `analysis/portable_workspace_validation.md`/JSON. It ran full postprocessing on byte-copied existing 102-cell raw/exact evidence under an interpreter guard denying original evidence reads; it did not independently simulate the full grid. All 18 summary/diagnostic CSVs and native findings/claim values matched original bytes; the selected four-cell replay was freshly computed. Summed stage wall time was 737.48 seconds, including that replay (99.77 seconds), separate from the original study's execution measurements below. An outer harness failed after the pipeline passed because it also monitored editable Markdown; the immutable-evidence/output verifier passed, and the failure is preserved. `notes/portable-workspace-integration-check.json` records report-level smoke/hash/source-binding checks; these do not replace independent review.

## Execution resources and history

`analysis/final_execution.json`, `analysis/execution_reconciliation.md`, `analysis/resource_jobs.json` and timing/calibration receipts preserve measured resource definitions and additional superseded/preliminary work. Corrected execution used CPU-only workers, one BLAS/OpenMP/MKL thread per disjoint shard. Resource creation-to-completion lifecycle was 923.21 seconds; summed reported running time was 2427.93 seconds and CPU spend 2590.74 seconds. These are different quantities. Maximum recorded simulation/exact-risk process RSS was 496880 KiB; later summary/audit cumulative child-process peak RSS was 522460 KiB. Neither measures total container peak.

The conservative 7.30-hour allowance in `analysis/pilot_budget.json` is a planning estimate, not measured completion. Per-cell function timings exclude some orchestration and cannot be added and called whole-job wall time. The resource records and `analysis/roundoff_v1/` retain superseded execution and audits; preliminary calibration is `analysis/pilot_timings.csv`/`calibration_finalization.json`. There is no instrumented total for every exploratory sandbox or language-model computation; the checklist states this limit. New hosts need not reproduce original timings. Long/repeated computation in the research environment runs on tracked resources.

`code/scripts/complete_corrected_study.py` is the original three-shard installation/finalization tool and can move local prior outputs aside; ordinary reproduction uses the clean-workspace launcher above. `reconcile_execution.py` consumes saved original resource receipts, not a portable profiler for a new run.

## Presented displays

All five corrected vector figures and twenty numerical tables are included in `paper.pdf`. Figures 1–3 present accuracy, paired prediction/GATE contrasts and support/allocation/covariance limits in the main text. Figures 4–5 and the numerical companions are in Appendix D; Table 1 is the complete graph inventory in Appendix C. Native figure width is 5.5 inches. Captions retain conditional versus graph uncertainty, actual failure denominators, oracle scope and extreme risk values.

```sh
python3 figures/render_exact_ht.py
python3 figures/render_core.py
python3 figures/render_final.py
python3 tables/render_graph_inventory.py
```

The four commands regenerate all packaged displays without rerunning simulations or statistical aggregation. `figures/display-map.json` maps every display to actual result paths/fields/selections, input snapshots and its generator. Full selected source rows and byte hashes are packaged in the subpackage manifests. The complete-study source registry is separate from this display selection.

| PDF display | Source asset(s) | Generator |
| --- | --- | --- |
| Figure 1: degree/size and response shape | `figures/core-accuracy.pdf` | `figures/render_core.py` |
| Figure 2: paired prediction/GATE differences | `figures/core-prediction.pdf` | `figures/render_core.py` |
| Figure 3: support, allocation and coverage | `figures/final-stress.pdf` | `figures/render_final.py` |
| Figure 4: oracle decomposition and MC residuals | `figures/final-decomposition.pdf` | `figures/render_final.py` |
| Figure 5: complete core exact HT risk range | `figures/exact-ht-risk.pdf` | `figures/render_exact_ht.py` |
| Table 1: all 36 graphs/partitions | `tables/graph-inventory.tex` | `tables/render_graph_inventory.py` |
| Tables 2–7: accuracy, prediction, mapping/flexibility, topology, public estimators and finite/exact HT | `tables/core-{accuracy,prediction,boundaries,topology,public,public-ht}.tex` | `figures/render_core.py` |
| Tables 8–18: support, coupled risks, imbalance, noise, widths, decomposition, residual checks, design/support, independent contrasts, baselines and failures | `tables/final-{support,support-risk,imbalance,noise,widths,decomposition,identity-checks,design-support,contrasts,baselines,failures}.tex` | `figures/render_final.py` |
| Table 19: all 216 core endpoint-family risks | `tables/exact-ht-risk.tex` | `figures/render_exact_ht.py` |
| Table 20: all 90 noise/imbalance endpoint-family risks | `tables/final-exact-stress.tex` | `figures/render_final.py` |

Presentation verification matched 239 original source hashes, 38 generated-output hashes and every selected field, then regenerated the four packages byte for byte. It checks source/selection/rendering fidelity, not an independent statistical implementation. Corrected 102-cell metadata applicability revalidates graph-inventory provenance. `figures/corrected-presentation-qa.md` records standalone color/grayscale and official-style proof inspection; `notes/` records the actual integrated PDF checks. V1 numerical assets are superseded history, not active authority.

## Sources, workflow and review

`notes/source-reading.md` records direct consulted references/URLs/hashes, including the original official NIPS 2012 graph-source PDF and official venue ethics/checklist guidance. The reserved-prior-work restriction remains in force: do not search for, identify, access or use the withheld study or pages discussing it. Exact permitted starter/data-source URLs and official venue assets were consulted. No prohibited encounter is known from this report position's consultation; the context and analysis records likewise state no known encounter within their respective scope. This does not certify unrecorded searches by others. Any encounter must be logged with URL, content and amount read.

Language-model agents assisted design, implementation, source consultation, presentation and writing, as disclosed in `appendices/workflow.tex`; they are workflow participants, not empirical evidence. `.forgejo/CODEOWNERS` assigns protocol to story, numerical code/results to experiment, figures/tables to figtab, official venue assets to venue and report/build/root guide to paper. Integrated presentation and venue-format checks are supplied in `figures/integrated-paper-qa.md` and `venue/manuscript-audit.md` for the unchanged PDF. The analysis owner's integrated numerical/method check is supplied in `analysis/integrated_claim_check.md`/JSON for the identical PDF. `study/final_coverage.md`/JSON/checker supplies the completed plan-owner objective/evidence/reproduction coverage; `notes/final-review-candidate.md` records the report's pre-review assessment. Independent approval of the exact version is recorded by the pull request merged into `final`; these owner receipts do not substitute it.
