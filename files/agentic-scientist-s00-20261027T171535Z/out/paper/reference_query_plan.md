# Reference Query Plan

**Status:** ready

## Central topic
Predicting the start-averaged expected cover time of simple random walks on small connected graphs (6<=n<=30) from cheap graph statistics and effective-resistance (Matthews-type) features, compared against generic worst-case bounds such as 2m(n-1), with error analyzed by graph family under Monte Carlo uncertainty.

## Grounding
- Final evaluation (ridge baseline on 5 cheap statistics): family-macro log MAE 0.181; generic 2m(n-1) bound 1.754; constant predictor 0.870; shuffled labels 1.423; median MC relative SE about 0.029.
- The Matthews/resistance idea (`c01_matthews_resistance_predictor`) is implemented but unscored; queries about it are motivated by the idea bundle and treated as method context, not as a result.
- Benchmark: 12 synthetic families (path, cycle, star, complete, grid, complete bipartite, barbell, lollipop, binary tree, random tree, Erdős–Rényi, random regular), n in [6,30]. No external data.
- Per-family results are not in the artifacts, so family-dependent failure is a hypothesis only.

## Core methods
- Log-linear (ridge) regression of log cover time on log n, log m, log mean degree, log max degree, log diameter (the evaluated baseline)
- Matthews-type predictor: m*R_max*H_{n-1} using effective resistances from the Laplacian pseudo-inverse / hitting-time linear solves (proposed idea; implemented but not scored in the final evidence)
- Monte Carlo estimation of start-averaged cover time with standard errors
- Leave-one-family-out evaluation with family-macro log error

## Comparators
- Generic worst-case cover time bound 2m(n-1) (Aleliunas et al. 1979)
- Feige's tight upper/lower bounds on cover time (n^3-scale, 4/27 n^3)
- Matthews bound via maximum hitting time times harmonic number
- Resistance-based commute/cover time bounds (Chandra et al.)
- Constant (family-agnostic) predictor and label-shuffled predictor as sanity controls

## Queries
1. `random walks universal traversal sequences complexity of maze problems cover time bound 2m(n-1)` [baseline_comparator] - Source of the generic 2m(n-1) bound that is the primary comparator (bound macro log MAE 1.754).
2. `Feige tight upper bound on the cover time for random walks on graphs` [baseline_comparator] - Tight n^3-scale worst-case bound; starter literature and a looseness baseline.
3. `Feige tight lower bound on the cover time for random walks on graphs` [baseline_comparator] - Companion lower bound, needed to frame the range within which small-graph cover times can fall.
4. `Lovász random walks on graphs: a survey hitting times commute times cover time` [core_method] - Starter survey; standard reference for hitting/commute-time identities used in the resistance features.
5. `Matthews bounds for cover times of Markov chains maximum hitting time harmonic number` [core_method] - Basis of the Matthews-type offset m*R_max*H_{n-1} in the proposed predictor.
6. `electrical resistance of a graph captures its commute and cover times` [core_method] - Justifies effective-resistance features (Laplacian pseudo-inverse) and resistance-based cover time bounds.
7. `maximum hitting time for random walks on graphs lollipop extremal` [result_driven_theme] - Lollipop/barbell are test families and the expected worst case for cheap-statistic predictors; extremal-graph theory explains family-dependent error.
8. `cover time of random regular graphs and sparse Erdős–Rényi random graphs` [benchmark_context] - Random regular and Erdős–Rényi are benchmark families; asymptotic cover times give context for where simple predictors should be reliable.
9. `ridge regression biased estimation for nonorthogonal problems` [baseline_comparator] - The evaluated baseline is ridge regression on standardized log features.

## Avoided
- generic 'optimization', 'benchmarking', 'scientific method', or paper-writing phrases
- queries about run chronology, attempts, or search history
- queries targeting the original paper answering this research question or any page discussing it (task prohibits)
- deep-learning/GNN cover-time prediction queries not supported by artifacts
- external dataset names (none used)

No prior references provenance existed, so there are no earlier generic queries to correct. Rejected alternatives: broad "cover time prediction machine learning/GNN" queries (nothing in the run uses them), generic "regression benchmarking", and chronology queries.
