# Allowlisted literature notes: regression GATE under network interference

## Scope and evidence

Acquired/read on 2026-11-02 UTC. Literature evidence is limited to the four original PDFs explicitly supplied by the user [1–4]. No search engines, arXiv abstract pages, citation graphs, recommendations, repositories, dataset hosts, or reference destinations were accessed. No attempt was made to identify the prohibited paper. No known prohibited material was encountered. The PDFs contain their own related-work/reference text; this was not used to expand the source list or followed externally.

**Status:** source acquisition and focused reading only. No experiment code or paper draft was inspected or altered. **No baseline was implemented, evaluated, or reproduced.** All performance statements below are the source authors' results, not results from this workspace. Repository/code availability, dataset access, and licenses remain unverified because those destinations are outside this task's allowlist.

PDFs were read through local text extraction because `pdftotext` and standard PDF-reading Python packages were unavailable. The local extractor decodes PDF text streams and font encodings; mathematical glyphs, equations, tables, and layout can be lossy. Equations below use normalized notation and prose-supported definitions, not verbatim extracted typography. Page references are 1-indexed PDF pages. This is not a complete proof audit or visual verification of every equation/table.

## Verified bibliography and paths

| Ref. | Title and authors verified on PDF page 1 | Version/year visible in downloaded PDF | Original local PDF |
|---|---|---|---|
| [1] | **Regression adjustments for estimating the global treatment effect in experiments with interference** — Alex Chin | arXiv v2, margin dated 5 March 2019; title page says “This version: March 6, 2019.” The identifier is from 2018; do not confuse it with the downloaded version's year. | `/work/artifacts/sources/1808.08683.pdf` |
| [2] | **Model-Based Regression Adjustment with Model-Free Covariates for Network Interference** — Kevin Han and Johan Ugander | arXiv v1, margin dated 10 February 2023; title page dated February 13, 2023. | `/work/artifacts/sources/2302.04997.pdf` |
| [3] | **Estimating Average Causal Effects under General Interference, with Application to a Social Network Experiment** — Peter M. Aronow and Cyrus Samii | arXiv v4, margin dated 20 June 2018. The identifier is from 2013; the title page says “Submitted to the Annals of Applied Statistics.” A journal publication year was not independently established from this title page. | `/work/artifacts/sources/1305.6156.pdf` |
| [4] | **Graph Cluster Randomization: Network Exposure to Multiple Universes** — Johan Ugander, Brian Karrer, Lars Backstrom, and Jon Kleinberg | arXiv v1, margin dated 30 May 2013. The template-like ACM copyright placeholder is not a reliable publication date. | `/work/artifacts/sources/1305.6979.pdf` |

Locally derived text is at the same four paths with `.txt` replacing `.pdf`; extraction metadata uses `.extraction.json`. Original download SHA-256 hashes and all requests/errors appear in `/work/artifacts/access_log.md` and `/work/artifacts/access_events.jsonl`.

## Key findings

### 1. Estimand alignment comes before estimator comparison

The global contrast compares **everyone treated** with **everyone controlled**:

\[
\tau=\frac1n\sum_i\{E[Y_i(\mathbf1)]-E[Y_i(\mathbf0)]\}.
\]

Chin and Han/Ugander formulate expected-response GATEs with stochastic errors [1, §2, pp. 6–7; 2, §2, p. 3]. The exposure papers primarily use fixed potential outcomes and randomization-based contrasts [3, §4, pp. 8–10; 4, Eq. (1), p. 2]. These viewpoints should not be conflated when defining Monte Carlo truth or interval coverage.

Under interference, an ordinary treated-minus-control mean generally targets a design-dependent own-treatment contrast, **not GATE**. For example, with mean response `alpha + beta * own_treatment + gamma * treated_neighbor_fraction`, GATE is `beta + gamma`, whereas the Bernoulli own-treatment contrast is `beta` [1, §2.1, pp. 7–8].

### 2. Chin: engineered interference features and counterfactual regression

**Method.** Under independent Bernoulli assignment, construct `X_i = x_i(W_-i, G)`, including an intercept. Fit separate OLS regressions within treatment and control. Recompute the same features under global treatment/control, `X_i^(1)` and `X_i^(0)`. With `omega_w = n^-1 sum_i X_i^(w)`, estimate

\[
\widehat\tau=\omega_1^\top\widehat\beta_1-\omega_0^\top\widehat\beta_0.
\]

This is a contrast of **global-counterfactual predictions**, not merely the coefficient of own treatment [1, §3, Eqs. (10)–(13), pp. 11–14]. Features may include treated-neighbor count, fraction, multiple radii, or multiple network layers. Count and fraction can encode different interference mechanisms on irregular graphs [1, §3.1, p. 12].

**Assumptions/limits.** The linear unbiasedness proposition requires separate linear response surfaces, strict exogeneity, appropriate feature independence from own treatment, and full-column-rank arm-specific design matrices. Independent, homoscedastic errors are additional assumptions for the displayed variance formula, not automatic consequences of random treatment assignment. Heteroskedasticity-robust SEs alone do not address residual network dependence [1, Assumptions 2–3, Proposition 1, Theorem 1, pp. 11–14]. Incomplete features may leave both omitted interference and correlated residuals. Full rank can fail, and count/fraction can be collinear on equal-degree or equal-sized-group networks [1, pp. 12–14].

**Inference.** The linear estimator uses design resampling of assignments/features to estimate expected inverse Gram matrices, combined with residual variance [1, §3.3, Algorithm 1, pp. 14–15]. The nonlinear extension uses held-out predictions plus observed-arm residual corrections (Eq. (22)); its bootstrap regenerates assignments/features and resamples residuals, then recomputes the estimator. Simple residual resampling needs independent errors. Graph cross-fitting does not itself guarantee independence, and general nonlinear theoretical guarantees are explicitly left open [1, §4, pp. 17–18].

**Author evaluation protocol.** Facebook100 largest components: Caltech, 762 nodes/16,651 edges; Stanford, 11,586 nodes/568,309 edges. The basic linear study uses 1,000 simulated experiments, 200 feature-distribution replicates for variance estimation, and Gaussian 90% CIs, reporting bias, empirical SE, estimated/empirical SE ratio, and coverage [1, §5.1–5.2, pp. 19–22]. Other studies use dynamic linear-in-means interference on a 1,000-node small-world graph and Caltech, plus nonlinear aggregate/average peer effects on Stanford. The nonlinear GAM study uses two-fold cross-fitting, 50 bootstrap replicates, and 200 simulation replicates; the comparison Hájek threshold is `q=0.75` [1, §5.4–5.5, pp. 22–27]. These are separate protocols, not one universal train/test split.

**Observed limitations/results.** More complete features reduce bias but can increase variance; one-step adjustment and nominal CIs fail under some multi-step misspecification. In weak-interference settings difference-in-means can have better error, and lower bias need not mean lower RMSE [1, pp. 24–26]. Real-data insurance adoption uses four one-/two-hop count/fraction features, OLS and five-fold logistic adjustment; the original timing/stratification is simplified rather than faithfully reproduced [1, §6, pp. 27–29]. The text on p. 27 reports **4,382** nodes while Table 4 reports **4,832**; do not silently resolve this inconsistency without the actual data.

### 3. Han/Ugander: ReFeX-LASSO feature generation and selection-aware uncertainty

**Method.** Start with local base features, recursively aggregate over neighbors, and select features against outcomes with LASSO. In sequential **ReFeX-LASSO**, previously selected features remain unpenalized; stop if no new active feature is selected or the iteration budget is reached. **Post-ReFeX-LASSO** generates candidates before one selection stage. Then fit separate-arm OLS on selected features and evaluate the feature maps under all-zero/all-one assignments [2, Algorithms 1–2, §4.1 Eq. (6), pp. 5–9]. The selection regression includes own treatment; it is not itself the final GATE estimate.

**Assumptions/theory boundary.** The working response is linear in a sufficiently rich feature map with exogenous errors and independent Bernoulli assignments. The formal setup can absorb own treatment into arm-specific functions and leave the feature map dependent on `W_-i` [2, §2, pp. 3–5]. The reported consistency theorem in §4.3 is for **post-ReFeX-LASSO**, under a true sparse linear feature representation, bounded feature norms, and restricted-eigenvalue conditions; do not describe it as unrestricted consistency of the preferred sequential algorithm or of arbitrary graph learning [2, pp. 10–11]. “Model-free covariates” does not mean model-free identification or guaranteed endpoint extrapolation.

**Inference.** Re-run feature selection inside a graph-block bootstrap. Partition by randomized `k`-hop-max clustering with `k=T*+1`, resample clusters, and pool bootstrap estimates across multiple random clusterings. For sequential ReFeX-LASSO, generate features on the **original fixed graph**, but use the bootstrap sample for selection/fitting; do not paste sampled clusters into a new graph by default. Percentile bounds are quantiles of all `ell*B` estimates [2, Algorithms 3–5, pp. 13–15]. The paper explicitly provides **no general theoretical coverage guarantee** for this procedure [2, p. 12].

**Author evaluation protocol.** RMSE/bias studies use the Swarthmore Facebook100 largest component: 1,657 nodes/61,049 edges, Bernoulli(0.5), simple linear, truncated linear-in-means, and sigmoid-type nonlinear outcomes. Defaults are `T=2`; base features are treated-neighbor fraction/count and two neighborhood-edge treatment-composition fractions; aggregation functions are **mean and variance**. Comparators include difference-in-means, fractional Hájek with `q=0.8`, fraction-only/count-only regressions, and oracle-feature adjustment [2, §5.1–5.3, pp. 16–21]. The read main text does not establish a precise point-estimation replication count; do not substitute the CI study's count.

For CI evaluation, the paper switches to the **sparser farmer network**, uses nominal 90% intervals, `ell=3` random clusterings and `B=100` bootstrap samples per clustering, and repeats the complete process 100 times. It reports coverage and average interval length, comparing graph-block, naive unit bootstrap, and natural-village blocks [2, §5.4, pp. 21–23]. For Model 6, Table 7 reports 91% ReFeX-LASSO block-bootstrap coverage versus 67% naive-bootstrap coverage; these are 100-run empirical proportions, not precise universal coverage guarantees.

**Failure modes.** Dense Swarthmore has mean two-hop/three-hop neighborhood sizes about 1,093/1,622 out of 1,657 nodes; the paper therefore does not use it as the primary multi-hop CI benchmark. Poorly isolated blocks, too few blocks, or substantially imbalanced block sizes can defeat the bootstrap. Post-generation selection is often higher-variance due to many correlated candidates, but sequential selection is not uniformly best. In the nonlinear example, Table 5 gives ReFeX-LASSO RMSE 2.75 versus 1.92 for fraction-only adjustment [2, pp. 19–23]. Real farmer-data truth is unknown; agreement between estimators is not validation of GATE accuracy [2, §6, pp. 24–25].

### 4. Aronow/Samii: exposure-based design inference, not automatic regression GATE

**Method.** Specify a known assignment design and an exposure mapping `D_i=f(W, theta_i)` that fully captures relevant interference. Compute marginal exposure probabilities `pi_i(d)` and joint probabilities `pi_ij(d,d')`. For an exposure mean,

\[
\widehat\mu_{HT}(d)=\frac1n\sum_i\frac{1\{D_i=d\}Y_i}{\pi_i(d)}.
\]

Contrasting exposure means gives an unbiased contrast under properly specified mapping, consistency of observed potential outcomes, and positive marginal exposure probabilities [3, §§3–4, pp. 4–11]. This is GATE only when the chosen exposure states genuinely represent the all-treated/all-control outcomes for the target population.

**Inference/refinements.** Variance estimation requires **joint**, not just marginal, exposure probabilities; mutually impossible exposures yield zero joint probabilities and unidentified terms. The paper supplies conservative corrections rather than claiming ordinary independent-unit SEs suffice [3, §5, pp. 11–15]. Hájek ratio estimation stabilizes weights but is not exactly finite-sample unbiased; covariate-adjusted difference/regression estimators are distinct refinements [3, §7, pp. 17–20]. In particular, its auxiliary-covariate WLS estimator is not Chin's treatment-derived-feature endpoint extrapolation estimator.

**Probability computation/calibration.** Exact enumeration may be infeasible. The paper simulates assignments, uses `(X_i+1)/(R+1)` smoothing for marginal probabilities, and does not apply the same smoothing to cross-exposure joint matrices. Proposition 4.1 bounds Monte Carlo propensity-induced relative bias by `(1-pi_min)^(R+1)`; the paper's example requires at least 10,593 replicates for target 0.005 at `pi_min=0.0005` [3, §§3–4, pp. 7–10]. This calibrates simulation effort; it is not permission to turn truly impossible exposures into supported ones.

**Assumptions/failure modes.** Consistency needs bounded outcomes/inverse probabilities and sufficiently limited pairwise exposure dependence; the displayed Wald-coverage result imposes stronger local dependence and nondegenerate limiting variance [3, §6, pp. 15–17]. Tiny probabilities lead to unstable estimates. Under exposure misspecification, HT estimates design-weighted mixtures of assignment-specific outcomes, **not generally GATE**, and the earlier inference theory does not transfer automatically [3, §8, pp. 20–21].

**Author evaluation protocol.** Add Health school networks, 144 school classes averaging 626 students; randomize 10% without replacement within each school; symmetrize friendship nominations; omit zero-tie students. Use activity-count baseline outcomes and multiplicative potential-outcome effects for four direct/indirect exposure states. Run 500 simulated replications and report bias, empirical SD, RMSE, mean SE, and 90%/95% normal-CI coverage. Compare HT, Hájek, exposure-probability WLS, OLS, and unadjusted exposure means [3, §9, pp. 21–25]. The field application has two-stage school/student randomization and restricts analysis to 2,050 students with the necessary exposure support; it is not a Bernoulli GATE benchmark [3, §10, pp. 24–27].

### 5. Ugander et al.: graph-cluster randomization changes the design

**Method.** Partition the graph and randomize entire clusters independently. Define full-neighborhood, absolute-count, fractional-neighborhood, and stronger core/component exposure conditions; use exposure-probability HT to estimate the global contrast [4, §§2–3, pp. 3–5]. Under vertex Bernoulli assignment, full-neighborhood treatment exposure is `p^(d_i+1)`; under cluster randomization it is `p^s_i`, where `s_i` counts clusters intersecting the **closed** neighborhood. Control probabilities replace `p` with `1-p` [4, pp. 4–5].

For fractional/absolute neighborhood exposure, the paper gives a dynamic program for weighted sums of independent cluster assignment indicators, accounting for the vertex's own cluster; stated complexity is `O(d_max*s_i)`. It does **not** supply an efficient exact algorithm for arbitrary core exposure probabilities [4, §3.1, p. 5].

**Theory boundary.** Bounded degrees, bounded cluster sizes, and bounded outcomes give `O(1/n)` HT variance. A 3-net clustering (choose centers, mark their radius-two balls, assign each node to a nearest center with consistent ties) controls the number of clusters intersecting each neighborhood on **restricted-growth graphs**. The improved degree dependence is conditional on that graph class, bounded outcomes, and nondegenerate assignment probabilities; not a blanket guarantee for dense social graphs [4, §3.2 and §4, pp. 6–9]. Its clustering algorithm is different from Han/Ugander's randomized `k`-hop-max bootstrap blocking.

**Author evaluation protocol.** The main numerical illustration is synthetic cycle powers: `n=5000`, degrees `2k` for `k=1,...,5`, one million cluster randomizations, and empirical estimator variance versus contiguous cluster size [4, §4.1, p. 7]. It is not a held-out dataset or a regression comparison. Exposure misspecification still biases the global contrast, and clustering trades increased exposure probability against stronger dependence between units. This design cannot be retroactively imposed on an already completed Bernoulli experiment.

## Reading-derived checks for any later experiment (none run here)

1. **Start with aligned targets and simple controls.** Separate difference-in-means, fixed-feature separate-arm regression, selected-feature regression, and exposure HT/Hájek. Match the assignment design and target population; compare cluster-randomized designs separately. A fixed-feature baseline alone is not a reproduction of ReFeX-LASSO or either source's full simulation program.
2. **Stress-test endpoint transport, not only predictive fit.** Include no-interference, one-hop count/fraction, multi-hop, and nonlinear regimes. Report GATE bias, empirical SD, RMSE, estimated/empirical SE ratio, coverage and interval length. Use analytic or separately simulated global-endpoint truth, not ordinary mixed-assignment outcomes. Calibrate Monte Carlo uncertainty of both truth and coverage; no tuning to evaluation truth.
3. **Audit features, probabilities, and uncertainty.** Exclude own-treatment feedback where the feature assumptions require it: a raw higher power of an adjacency operator can return to the origin. Check arm-wise rank/conditioning, isolated-node conventions, endpoint feature recomputation, and selection stability. For fractional exposure, include **own-arm assignment** and an unambiguous integer threshold: treated-neighbor count at least `ceil(q*d_i)`, control treated-neighbor count at most `floor((1-q)*d_i)`. Verify probabilities against small-graph enumeration; detect empty Hájek denominators rather than silently dropping failed runs. Re-run selection in bootstraps and diagnose block balance/isolation. Ordinary held-out predictive accuracy does not validate GATE extrapolation or interval coverage.

These checks are practical implications of [1–4], not newly established theoretical results or implementation claims. In particular, the prose/indicator/threshold displays in early PDF versions should not be copied mechanically when building exposure events.

## Official NeurIPS 2026 template status

**Downloaded successfully:** exact official archive `/work/paper/template/Formatting_Instructions_For_NeurIPS_2026.zip` [5–6]. The requested 2026 StyleFiles route and PaperInformation parent returned 404, as did a 2025 StyleFiles fallback probe. The official 2026 CFP directly linked the downloaded ZIP. **Provenance caveat:** the ZIP link was verified in the permitted official submission instructions (CFP), not in the unavailable StyleFiles page. If “referenced there” is interpreted strictly as requiring a StyleFiles-page link, this is a provenance-route deviation; do not claim that exact route was verified. See the access log.

Unmodified archive members, byte-checked against the ZIP:
- `/work/paper/template/official_2026/neurips_2026.sty` — header identifies the 2026 package, dated 2026-01-29.
- `/work/paper/template/official_2026/neurips_2026.tex` — official shell, including `\input{checklist.tex}`.
- `/work/paper/template/official_2026/checklist.tex` — official checklist.

The ZIP contains these three files; it does not include a compiled PDF. No style/template was invented or substituted. No LaTeX compilation was performed.

**Verified requirements:** nine submission content pages including figures/tables; references, optional technical appendices, and mandatory checklist excluded. The handbook allows one additional content page for an accepted camera-ready paper [7, “Authors / Paper Formatting Instructions”]. Checklist omission triggers desk rejection; put it after references and optional appendices, retain questions/guidelines and use the supplied answer macros plus brief justifications [6, `checklist.tex`]. For an anonymous main-track submission use the default `\usepackage{neurips_2026}` or `[main]`, not `final`/`preprint`; preserve style dimensions. Camera-ready `[main,final]` and public `[preprint]` are different modes [6]. Keep all three files together; usage instructions are at `/work/paper/template/README_acquisition.md`. No draft has been created or edited.

### Sources

[1] Chin, *Regression adjustments for estimating the global treatment effect in experiments with interference*: https://arxiv.org/pdf/1808.08683

[2] Han and Ugander, *Model-Based Regression Adjustment with Model-Free Covariates for Network Interference*: https://arxiv.org/pdf/2302.04997

[3] Aronow and Samii, *Estimating Average Causal Effects under General Interference, with Application to a Social Network Experiment*: https://arxiv.org/pdf/1305.6156

[4] Ugander, Karrer, Backstrom and Kleinberg, *Graph Cluster Randomization: Network Exposure to Multiple Universes*: https://arxiv.org/pdf/1305.6979

[5] Official NeurIPS 2026 Call for Papers (template-link provenance): https://neurips.cc/Conferences/2026/CallForPapers

[6] Official NeurIPS 2026 formatting archive: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip

[7] Official NeurIPS 2026 Main Track Handbook (format/checklist requirements): https://neurips.cc/Conferences/2026/MainTrackHandbook
