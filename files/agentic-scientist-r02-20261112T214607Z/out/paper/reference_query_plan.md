# Reference Query Plan

**Status:** ready. Eight queries; planning only. No references have been retrieved or verified as read at this stage.

## Central topic

Reliability and reference-measure efficiency of training-only locally scaled split-conformal regions for continuous logistic-normal compositions in isometric log-ratio (ILR) coordinates, across homoscedastic, boundary-concentrated heteroscedastic, and covariate-shift settings.

## Grounding and evidence boundaries

Primary grounding is `paper_data.json`, especially `/all_programs`, `/final_evaluation/metrics`, and `/final_evaluation/evaluation_evidence/episodes`. Implementation and workload interpretation come from:

- `results/ideas/02_cross_fitted_tail_adaptive_residual_scaling/program_1/src/program.py` and `src/METHOD.md` in that same configuration.
- `task/task_contract.json` and `task/evaluate_final.py`, including the generator, baseline region definitions, reference probes, and uncertainty calculations.

The global memory summary was used only as planning context. Its earlier statement that repeated-run uncertainty was unavailable is superseded by the actual final evidence: six seed episodes (1009, 2003, 3001, 4001, 5003, 6007), Wilson coverage intervals, and 2,000 paired seed-bootstrap resamples. Source documentation predates evaluation and is not evidence that later recorded runs were absent. Candidate diagnostics are marked unverified; no component-selection or attribution claim is inferred from them.

The strongest successful search configuration is the tail-adaptive selection family, with aggregate utility 0.8784929468848246 versus 0.8769659694273084 for the incumbent. This small difference has no isolated component ablation or demonstrated between-configuration significance. The separate completed final evaluation reports mean utility 0.8772268474776957, bootstrap interval [0.8766236679621646, 0.8781275287778212], and mean utility gap to global ILR 0.04762325792650014. Its paired interval for that baseline gap is [0.043901240346666696, 0.050616967867983816]. These intervals compare the final evaluated method with evaluator baselines, not the tail family with its earlier incumbent configuration.

Case means computed solely from the recorded final episodes show greater utility than global ILR in B/S cases and slightly lower utility in H cases. This supports a setting-dependent scaling question, not universal improvement. Final marginal and fixed-group absolute coverage errors are 0.011729600694444453 and 0.015105333854689552. They are empirical diagnostics, not conditional validity guarantees. Reference mass is 0.4508402082655165; it is probability under mixed reference probes, not simplex volume. Aggregate utility combines coverage errors and reference mass, so a utility gain alone does not establish improvement in every component.

The count-noise/latent-composition bridge was not implemented under the scale-only interface. The attempted honest interaction ensemble failed with no usable performance evidence. Neither supplies a contribution-driven retrieval target. No real dataset, neural architecture, or transfer experiment is evidenced. The figure directory is empty. No existing BibTeX or reference provenance is present, so there are no earlier off-topic retrieval queries to repeat.

## Methods and comparison story

- Fixed training-only ILR ridge center; the candidate receives scale-training covariates and residual norms only. Calibration and region construction remain evaluator-owned.
- Positive residual-scale regression: quadratic-feature ridge on log norms versus a family adding additive quantile stumps at quantile 0.9 and log-space ridge/tail blends.
- Training-only three-fold selection, fitting-only quantile alignment, and a one-standard-error heuristic. That heuristic is not a significance test; overlapping fitting folds do not yield an independent uncertainty estimate.
- Actual baselines: global ILR, raw-simplex L-infinity, coordinatewise Bonferroni, uncalibrated training quantiles, full simplex, and singleton center; actual controls: constant scales and permuted training residuals.
- Related but unimplemented comparators: conformalized quantile regression and shift-aware weighted conformal inference. These are context, not additional experimental results.
- Representation comparison: raw-coordinate regions versus ILR norm regions. Scale-model comparison: log-norm ridge versus a training-selected tail-adaptive family. Neither comparison establishes a general neural architecture effect or isolates a selected blend's contribution.

## Benchmark context and result-driven themes

The only evaluated dataset family is the task-owned `logistic-normal-v1` synthetic generator, with six covariates and composition dimensions 3 and 10:

- H3/H10: interior, homoscedastic.
- B3/B10: boundary-concentrated, heteroscedastic, but strictly positive rather than exact-zero responses.
- S3/S10: the boundary/heteroscedastic setup with a test-covariate mean shift.

Nominal coverage levels are 0.95 and 0.90. Fixed evaluation groups use the sign of the first covariate. Efficiency uses a mixture of training-derived ILR Gaussian probes and uniform-simplex probes. The literature priorities are therefore local scale adaptation under heteroscedasticity, the distinction between marginal and conditional coverage, the failure of ordinary exchangeability arguments under shift, and geometry/reference-measure dependence of region efficiency. Internal H/B/S labels are not external benchmark names and should not be searched as such.

## Eight retrieval queries

| # | Query | Category | Run-specific reason |
| --- | --- | --- | --- |
| 1 | `"Distribution-Free Predictive Inference For Regression"` | core_method | Starter-list foundation for split calibration, finite-sample ranks, and locally adaptive residual scaling. Covers validity and scaling together rather than duplicating generic conformal searches. |
| 2 | `quantile regression boosting decision stumps pinball loss` | core_method | Directly matches the successful log-norm quantile-stump implementation and its loss; does not claim isolated stump gains or successful interaction forests. |
| 3 | `"Conformalized Quantile Regression"` | baseline_comparator | Reviewer-relevant neighboring quantile methodology. Distinguish learned radial scale from conformalized response-quantile endpoints; CQR was not evaluated. |
| 4 | `"Isometric logratio transformations for compositional data analysis"` | architectural_shift | Foundational geometry for the actual raw-coordinate versus ILR region comparison, with a shared center rather than an invented architecture transition. |
| 5 | `logistic normal distribution compositional data simplex` | benchmark_context | Establishes the synthetic response family and positive near-boundary context, not count data or an external dataset. |
| 6 | `multivariate conformal prediction Bonferroni hyperrectangles` | baseline_comparator | Motivated by the implemented joint raw-coordinate and coordinatewise Bonferroni baselines; efficiency comparisons remain reference-measure dependent. |
| 7 | `"Conformal Prediction Under Covariate Shift"` | result_driven_theme | Starter-list anchor for interpreting the shifted S cases without asserting that unweighted split calibration remains valid under shift. |
| 8 | `limits distribution free conditional predictive inference conditional coverage` | result_driven_theme | Prevents empirical fixed-group coverage and aggregate utility from being mistaken for conditional or multivalid guarantees. |

Queries are future search instructions, not assertions that the requested documents have been retrieved, read, or verified. Queries 1, 4, and 7 use narrow foundational title anchors; the others separate method, distribution, and evaluation neighborhoods. No combined search for the specific compositional-conformal evaluation problem is needed.

## Exclusions and safe downstream use

Do not identify, infer, retrieve, read, or use the prohibited prior paper or any mirror, preprint, abstract/venue/review page, code, media, or source citing, discussing, or reproducing it. Do not expand citation networks, recommendations, or citing-paper lists. Do not guess the forbidden title or authors to build an exclusion list. The plan cannot certify unseen future search results as safe: screen before reading, stop immediately on an accidental encounter, and record the location and amount read in the reproduction record without further investigation.

Avoid broad direct conjunctions such as `conformal prediction compositional outputs evaluation`, `conformal prediction simplex benchmark`, or `reliability evaluation compositional conformal methods`. They are unnecessarily likely to target the forbidden neighborhood. Use the separated foundational queries above instead.

Reject CIFAR/image-softmax set predictors, pretrained neural architectures, multinomial count-depth bridges, latent-target reconstruction, binomial atom checks, and honest interaction-forest superiority as retrieval targets for this paper: they were not evaluated successfully here. Do not frame strict-positive boundary cases as exact-zero composition experiments. Do not search or claim geometric-volume superiority or unweighted shift/conditional guarantees from these results.

Reject broad optimization, benchmarking, scientific-method, paper-writing, campaign chronology, and harness-score queries. Unlike those generic alternatives, each selected query explains an implemented method, a real comparator, an actual representation/distribution, or a result-backed interpretation boundary. No unnecessary citations to full-simplex/singleton sanity controls are requested.

## Handoff

The JSON companion mirrors these choices and contains exactly eight queries. Later retrieval must enforce the prohibition above and verify actual sources before citation. This stage creates neither bibliography/provenance nor paper/claim-grounding files and runs no reference-retrieval tools.
