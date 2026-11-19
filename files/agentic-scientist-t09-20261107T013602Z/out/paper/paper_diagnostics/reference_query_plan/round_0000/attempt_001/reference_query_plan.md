# Reference Query Plan

**Status: ready.** Ten queries; planning only. No external search or reference retrieval was performed.

## Central Topic

Regression-based estimation of the all-treated versus all-control global average treatment effect under network interference, emphasizing endpoint-contrast-targeted ridge tuning, exposure representation, and topology-dependent error.

## Grounding and Evidence Boundaries

- Primary evidence: `paper_data.json`, particularly `best_correct`, `all_programs[*].evaluation_evidence`, `final_evaluation`, and the empty `ablation_studies` array. Global memory is qualitative planning context, not quantitative evidence.
- Configuration evidence: `results/ideas/03_endpoint_contrast_sure_for_exposure_regression/program_1/src/program.py` and its `program_0/src/program.py` comparator. The selected estimator actually calls the endpoint-risk fitting and prediction path, with fallback and a constant-outcome bypass.
- Development evidence includes two successful variants, each evaluated over eight seeds. The diagnostic-only variant preserves the hinge-regression comparator; the quadratic endpoint-risk variant improves its aggregate error metrics. This does not establish statistical significance or a tuning-only benefit.
- Final evidence includes 24 seeds and 576 scientific cases: four graph families, six mechanism identifiers, and 24 replicates per family/mechanism cell. Constant, permutation, and replay controls are separate from these scientific cases. Recorded errors show family/mechanism heterogeneity and no uniform superiority over one-hop OLS.
- Final evaluation is not a matched final comparison against the hinge-regression variant. Use the recorded within-case simple baselines for final comparisons; do not compare aggregate development and final metrics as if they used identical workloads.
- Case fields explicitly contain validated endpoint contrasts, truth, observed-fit RMSE, baseline estimates, and exposure support. Candidate-generated diagnostics are marked unverified; do not use them as independent scientific evidence.
- No same-reference GCV ablation is present. The separate nonbacktracking two-hop GCV attempt has no valid comparative result; its local failure log reports evaluator disconnection before candidate responses. Neither scientific inferiority nor a candidate root cause follows.
- `figures/` is empty. Neither `references.bib` nor `references_provenance.json` exists, so there are no prior retrieval queries to reuse or correct.

## Methods and Expected Comparators

The core method is regression adjustment: predict outcomes under all treatment and all control and average their difference. The selected model uses supplied covariates, own treatment, one-hop treated-neighbor fraction, treatment/exposure interaction, and quadratic curvature features that vanish at exposure endpoints. It centers and scales the observed design, performs SVD ridge fitting with an unpenalized intercept, checks endpoint-contrast estimability and residual degrees of freedom, and selects among five fixed penalties using an endpoint-linear-functional risk estimate.

The Stein-style motivation is conditional on a correct linear reference and independent homoskedastic Gaussian noise. A fixed-penalty risk argument is not an unbiased post-selection risk guarantee. Row-space estimability is also not evidence of empirical endpoint coverage or robustness to misspecification.

Measured comparators are difference in means, own-treatment OLS, one-hop OLS, and the evaluated fixed-penalty hinge-exposure regression. Constant prediction and copying observed outcomes also occur as diagnostic baselines; they do not merit separate literature searches. Same-reference GCV is an expected tuning comparator, not an executed successful ablation. Exposure-mapping inverse-probability estimators and graph-cluster randomization are contextual alternatives, not methods benchmarked here. Related published regression-adjustment methods likewise must not be described as reproduced implementations.

## Benchmarks and Representation Shifts

- Synthetic SBM, Barabasi-Albert (BA), and Watts-Strogatz (WS) graph families appear in development and final evidence.
- Facebook100 Stanford3 (`socfb-Stanford3`) appears in final scientific cases. Cite both the original network source and the repository attribution required by the supplied task. The public graph does not make synthetic outcomes a real platform experiment.
- The supported representation change is from fixed one-hop hinges with fixed ridge strength to a quadratic one-hop reference with endpoint-risk-selected ridge strength. These changes are confounded; there is no isolating ablation.
- The change from prediction-oriented to endpoint-oriented tuning is methodologically relevant but not empirically isolated against same-reference GCV. There is no validated neural or multi-hop architecture transition.
- Synthetic topology names identify the scope but do not need separate broad graph-generation queries within this small budget. Stanford3 provenance is the higher-priority dataset citation need. SNAP ego-Facebook is unused.

## Query Set

1. **Core method:** `"Regression adjustments for estimating the global treatment effect in experiments with interference" Chin`
   - Allowed starter-title lookup for the implemented fit-and-predict endpoint regression family. Avoids unrestricted discovery of papers answering the task question.
2. **Architectural shift:** `"Model-based regression adjustment with model-free covariates for network interference" Han Ugander`
   - Allowed starter-title lookup for graph-derived exposure representations and related regression adjustment. Contextualizes the hinge-to-quadratic shift, not an unsupported neural or successful multi-hop comparison.
3. **Core method:** `Stein unbiased risk estimation linear functional ridge regression`
   - Classical foundations for endpoint-functional risk scoring using reference weights, ridge weights, and estimated residual noise. Do not imply that a network-specific endpoint-SURE reference exists or that selected risk is unbiased.
4. **Baseline comparator:** `generalized cross validation ridge regression`
   - Classical prediction-oriented tuning comparator. Grounded in the attempted GCV method and the missing same-reference ablation, not in an observed successful GCV comparison.
5. **Baseline comparator:** `"Estimating average causal effects under general interference, with application to a social network experiment" Aronow Samii`
   - Allowed starter-title lookup for exposure mappings and design-based inverse-probability estimation. Context only; not an evaluated inverse-probability baseline.
6. **Baseline comparator:** `"Graph cluster randomization: network exposure to multiple universes" Ugander`
   - Allowed starter-title lookup for design-side changes to endpoint exposure probabilities. Do not claim the study compares randomization designs.
7. **Result-driven theme:** `"Design and analysis of experiments in networks: Reducing bias from interference" Eckles Karrer Ugander`
   - Allowed starter-title lookup connecting topology, interference bias, and neighbor-informed analysis. Motivated by heterogeneous errors and nonuniform baseline comparisons, not a demonstrated causal explanation of those errors.
8. **Result-driven theme:** `linear model estimable contrasts variance extrapolation`
   - Foundational statistical context for contrast row-space checks, variance amplification, and the distinction between algebraic estimability and supported endpoint extrapolation.
9. **Benchmark context:** `"Social structure of Facebook networks" Traud Mucha Porter`
   - Allowed starter-title lookup for Facebook100/Stanford3 graph provenance and social structure. Does not establish anything about real experimental outcomes.
10. **Benchmark context:** `"The Network Data Repository with Interactive Graph Analytics and Visualization" Rossi Ahmed`
    - Repository attribution explicitly required by the supplied task for `socfb-Stanford3`; distinct from the original network source.

## Result-Driven Priorities

Prioritize endpoint-functional shrinkage, exposure representation, and conditional performance rather than a universal superiority narrative. The aggregate development improvement motivates the method neighborhood, while final family/mechanism variation and simple-baseline comparisons require limitations-focused context. Recorded endpoint support and implemented estimability guards justify statistical background, but do not prove that either explains the observed error pattern. Published theory must not be substituted for missing ablations, noise stress tests, uncertainty analysis, or evidence of robustness.

## Access Guardrails and Rejected Alternatives

The prohibited paper remains unidentified: do not infer its title, authors, or findings. No query attempts to discover it. For later retrieval, use the permitted starter-title lookups directly and restrict the three general statistical queries to classical foundational sources. A query is not permission to open arbitrary results. Do not expand citation graphs, follow cited-by or related-paper recommendations, or read surveys, notes, reproductions, mirrors, or discussion pages that violate the task restriction. If prohibited content is encountered accidentally, stop reading immediately and record the location and amount seen in the reproducibility record. None was encountered during this local-only stage.

Avoid unrestricted searches combining the full task question, regression GATE error, and network interference. Also exclude unsupported GNN/GCN/spectral-CNN/attention comparisons; claims of successful nonbacktracking two-hop GCV; claims of tuning superiority over same-reference GCV; unexecuted hidden-twin or correlated-noise studies treated as results; unused SNAP ego-Facebook, MNIST, and 20NEWS; and generic optimization, benchmarking, scientific-method, paper-writing, internal-score, or campaign-history queries.

These ten queries are preferable because each fills a specific estimator, comparator, statistical-validity, or observed-dataset citation role. Broad architecture sweeps and generic citation-abundance searches would not explain the actual endpoint-regression study. No BibTeX entries or provenance records have been generated; the references must still be retrieved, checked for permitted access, and read before being cited.
