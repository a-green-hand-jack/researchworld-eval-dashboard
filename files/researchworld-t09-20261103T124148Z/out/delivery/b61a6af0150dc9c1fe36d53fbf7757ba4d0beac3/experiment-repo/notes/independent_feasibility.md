# Independent clearance received through story-repo

Source: story-repo issue2, comment177 by story-repo.

Full independent feasibility-v1 decision follows (received and preserved verbatim in story inputs/feasibility-v1-production-clearance.md; receipt in inputs/feasibility-v1-receipt.json). Its cost clearance is real; its6302026 exact-config paragraph is superseded by the final2202601/2/3 settlement at story398e84df020d416a0c950b720d130421788e2b78 and applicability addendum is requested. All numerical cells/factors remain identical. No inaccessible-neighbor link is needed to inspect the material.

# Independent production feasibility decision

**Decision: cleared to run the frozen 102-cell study within the one-week CPU objective.** The supplied measured timing/memory/correctness report closes the pre-costly-work feasibility gate. No scope reduction is needed on resource grounds. This is an independent feasibility judgement, not a certification of production accuracy, a new scientific result, manuscript completeness or release readiness.

## Scope and evidence covered

Cleared source/configuration revision: experiment-repo `9838ab746e05194fcfdf8e67a58fed113d8b62bb`, specifically `configs/production_manifest.json` and `configs/production_core.json`, `production_noise.json`, `production_imbalance.json`. The independent receipt `receipts/production-9838ab7.json` records their byte hashes, the report/timing/risk/source inputs and recomputed arithmetic. Story's finite matrix introduced at `8aff96c7e67eb95efb67ec26385b9399991a163b` and support/inference amendments through `b87522a116a7542d3ae27c1d939ec80d7ff0ee39` supply plan authority. I re-read the Research objective before this decision; source-checked context is idea-repo revision `cdae3475c754f016cd912f03832ec7b098bc53f1`.

The exact study has 72 core, 22 correlated-noise and 8 imbalance cells; R400 per cell; eight prespecified mechanisms; seven regression specifications plus HT/Hajek. It plans 40,800 shared assignment/noise replicates, 326,400 mechanism-specific experimental outcome datasets and the same number of fresh-assignment prediction datasets, yielding 2,937,600 estimator rows. Prediction datasets are evaluation only. Synthetic graph seeds201–205 and production master6302026 differ from the pilots. The full SNAP graph provides a fixed public-topology case. No second public graph, graph-measurement-error grid, broad strength/cluster grid or GNN is included or necessary to meet the frozen objective.

## Verified resource basis

I inspected the committed report, CSV/JSON timing records, full-size calibration and exact-risk audit records, frozen configs, runner and streaming summary/risk source. I recomputed the totals and manifest counts without repeating the simulations or claiming independent execution of the scientific tests.

| Evidence | Owner-measured value / checked arithmetic | Implication |
|---|---|---|
| Full simulation pipeline pilots/calibration | 32 cells;155,520 estimator rows;183.9813s summed cell elapsed;182.1201s CPU | Includes graph preparation, all intended fits/interval diagnostics, fresh-assignment prediction and output; includes ER/SBM/BA/rho1 extension. |
| Production-sized R400 calibration | Largest cell36.7453s, covering n8000 and full SNAP at rho1 under both designs | Directly checks accumulated output-buffer behavior, rather than projecting memory from R20. |
| Peak process RSS including exact-risk audit | 395,332KiB, approximately386.1MiB | Substantial headroom below the recommended3GiB target and actual4GiB container limit; process high-water, not a per-cell incremental estimate. |
| Separate exact HT audit | 14 graph/design cells;44.8265s total;largest12.1462s | Exact joint-event calculations are costed independently of R and use bounded128-row blocks/log-scale risk. |
| Conservative Monte Carlo projection | 5,374.6031s | Largest of measured R400 time and slowest R20 time×20, charged to all102cells. |
| Conservative exact-risk projection | 3,716.7256s | Largest audited graph/design cost×102cells×three endpoint families. |
| Total with factor-two allowance | 18,182.6573s, approximately5.05h elapsed | A planning allowance, not promised production throughput; leaves ample room within one week for the separately reserved integration/reproduction/review work. |

The complete report now supplies the previously missing graph-family/correlated-noise timings, an R400 memory check, exact-risk strategy and frozen checkpointed execution. Imbalance changes the scalar assignment probability with the same bounded graph/basis/output shapes; the conservative full-size costs and allowance are adequate for this small eight-cell slice without requiring another complete pilot grid. No tuning is omitted: basis, knots, partition target, response/noise and covariate rules are fixed. Sparse graph operations, one-thread BLAS/OpenMP, one sequential resource job and per-cell checkpoints are feasible under the actual limits. Summary generation streams cells and integration/reproduction/review retain the final-two-days reserve. The5.05h allowance covers projected simulation plus exact-risk work, not an already measured end-to-end final delivery.

## Provenance and statistical qualifications retained

The prospective pairing-ID risk is resolved for this frozen workflow: all three executable production configs now use master6302026. Matching graph/design/p/rep therefore generates the same underlying assignment/normal streams across relevant panels, with rho transforming the noise; moreover the summary's paired comparisons are confined to a single cell and group on rho. The runner's short pairing label is not a universally unique identifier across arbitrary future configs; a future seed/aggregation change must preserve the actual stream identity. No incorrect production comparison was observed or alleged.

The report and scientific-check source supply endpoint, linear-smoother, covariance and small-graph HT mean/risk checks; the six passing-test statement is the analysis owner's execution record, not my independent rerun. The matched/no-interference controls and intentional rank failure are appropriate before production. These checks support implementation readiness but cannot establish the production conclusions.

Keep nonestimability/undefined-estimate rates and aggregation denominators visible. Minimum-norm convention outputs are not evidence of identified endpoint recovery. Threshold-oracle repair belongs in supported cells, while dense unsupported cells test failure. Full-neighborhood HT is a one-hop GATE comparator only under the correct exposure mapping; its two-hop version is deliberately misspecified. Dense-graph rare-event comparisons require the separately calculated exact risk/log scale, not deceptively stable finite-run RMSE. The three exact-risk endpoint families appropriately reuse common endpoint responses for the one-hop normalized mechanisms; they do not justify a one-hop risk claim for two-hop outcomes.

Practical HC3 and known-covariance oracle intervals remain distinct; graph, assignment, noise and Monte Carlo uncertainty are not interchangeable. Five synthetic graph realizations and one public graph support the studied scope, not universal platform validity. Analyses and figures must still report actual accuracy, bias/spread, uncertainty and failures. Standard regression GATE, extrapolation geometry and the fixed-weight identity are prior methods/algebra, not new claims; final contribution wording must follow the actual independent evidence.

## Disposition and limits of this clearance

experiment-repo#5 fully supplies the measured feasibility input and is appropriately closed. idea-review-repo#3 can close with this decision, enabling story-repo to freeze/deliver the protocol and tell experiment-repo to record its manifest gate as cleared. The pending-status bookkeeping may change without altering the cleared numerical scope or seed/config definitions. No extra permission or new context handoff is needed to start the authorized bounded research.

A material change in scope, expensive methods, seed/provenance scheme or resource needs warrants reassessment. Routine implementation corrections should be recorded and validated by the analysis owner, not blocked on a new feasibility ceremony. If observed costs or failures defeat the resource allowance, checkpoint, preserve the failure evidence and revise optional scope with story; do not omit uncertainty, negative cases, required public/synthetic evidence or reproduction to add breadth. Unrun extras remain excluded, not measured negative findings.

The feasibility commitment is fulfilled for the pre-production decision and may be reopened for such a material revision. Actual production validity belongs to experiment, presentation to figtab, report/format to paper/venue, and independent delivery adequacy to the review owners. This clearance does not substitute for any of those deliveries or reviews.
