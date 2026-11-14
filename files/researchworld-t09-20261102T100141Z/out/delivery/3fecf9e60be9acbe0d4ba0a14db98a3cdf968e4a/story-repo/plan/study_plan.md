# Study plan: how accurate is a regression-based GATE estimator under network interference?

Owner: `story-repo` (plan). Objective: issue #1. Written 2026-11-02. This is a plan, not a result:
every hypothesis below may be refuted and the paper must report whichever way it goes.

## 0. Guard rails (all positions)

* The objective forbids searching for, reading or using the published paper that studied this exact
  question, or anything citing/discussing it. Do not search for its title, authors or results. Use
  the starter literature (`/initial-state/inputs/0/starter_literature.md`) and unrelated sources.
  If something suspicious is met by accident: stop reading, and record where/what/how much in the
  reproduction notes (`code/README.md`).
* Every number/figure/table in the paper comes from code in `code/`, rerunnable. No placeholders.
* Budget is small (world: 7200 model-seconds, 96 turns, all positions together). Work in the stages of §6;
  stage 1 alone must already give a complete, honest paper.

## 1. Estimand and the object studied

* Units i = 1..n on a graph G (adjacency A, degree d_i). Assignment z ∈ {0,1}^n. Potential outcome Y_i(z).
* GATE: τ = (1/n) Σ_i [ E Y_i(1) − E Y_i(0) ] with 1 = all treated, 0 = all control. Because outcomes are
  synthetic, τ is computed **exactly** by evaluating the noise-free mean function at z=1 and z=0 (ground truth,
  no Monte-Carlo error in the target).
* Regression-based estimator (class studied): from one realised experiment (z, Y, G, covariates) fit a
  model f̂ : (z_i, features built from z and G) → Y_i; then τ̂ = (1/n) Σ_i [ f̂(1-vector features of i) − f̂(0-vector features of i) ].
  Variants differ in (a) feature map (z only; + neighbour-treated fraction/count; + degree interactions;
  + 2-hop; + graph covariates), (b) model class (OLS, ridge, GBM/random forest, optionally small GNN).
  The key structural fact to test: prediction at "all treated" is an **extrapolation** from the design's
  exposure distribution (e.g. neighbour fraction ≈ p) to the exposure 1.

## 2. Research questions and pre-specified hypotheses

RQ1 *How accurate?* Bias, RMSE, relative error, CI coverage of regression estimators vs baselines, across
   mechanisms and graphs.
RQ2 *What determines the error?* Decompose into (i) approximation/extrapolation error of the model class at
   all-treated/all-control (what the best fit under the design distribution would predict, with infinite data & no noise)
   and (ii) estimation error (finite n, noise). Which factors move which part?
RQ3 *Where does it hold and where does it fail?* Interference form, network structure, design, sample size, noise.

Hypotheses (H = prediction; each is falsifiable; report support, refutation or "depends"):
* H1 (correct specification): when the model's exposure feature matches the true mechanism (linear in neighbour
  fraction), the estimator is ≈unbiased and RMSE shrinks ~ n^(-1/2); it beats difference-in-means (DM) by a margin
  growing with interference strength ρ = c/b (interference-to-direct ratio).
* H2 (misspecification via extrapolation): with nonlinear/saturating or 2-hop interference, bias does not vanish
  with n and grows with the gap between design exposure support and the all-treated point (e.g. smaller p, or
  more concentrated exposure on high-degree graphs); flexible learners (GBM/forest) do **not** fix it because trees do not
  extrapolate (they may be worse than OLS). (A real chance this is wrong; test it.)
* H3 (network structure): at fixed n, error depends on degree distribution and clustering. Heavy-tailed degree (BA)
  and normalisation of the interference term (sum vs mean) change variance/bias; graph-cluster randomisation
  widens exposure support (more units with exposure near 0 or 1) and reduces extrapolation error, at the price
  of a larger variance from fewer independent units.
* H4 (design): the regression estimator under Bernoulli(p) with p near 0.5 is typically better than at
  small p; a design mixing several p (staggered-rollout-like) improves extrapolation.
* H5 (misspecified network): errors/missing edges in the graph used for features degrade accuracy roughly
  monotonically in the error rate; estimator can fall below DM at high error rate if the interference is weak.
* H6 (inference): bootstrap CIs (blocked/cluster bootstrap) under-cover when bias is not negligible vs SE;
  coverage gets worse as n grows in the misspecified cases (bias/SE ratio grows).
* H7 (diagnostic): a computable-from-data exposure-support/overlap statistic (e.g. distance between the empirical distribution
  of the neighbour-fraction feature under z versus under all-treated) predicts the extrapolation error across the grid
  (pre-specified analysis: regress log|bias| on it, report R², by mechanism). Report if it does not.

## 3. Simulation environment (defaults; experiment-repo may refine and must document)

Graphs
* Synthetic, n ∈ {1000, 2000, 5000, 10000} (stage 1: n=2000 base): Erdős–Rényi, SBM (communities, homophily
  in/out ratio varied), Barabási–Albert, Watts–Strogatz; matched mean degree (≈10–20) for fair comparison.
* Public: SNAP ego-Facebook (4039 nodes, 88,234 edges) and Facebook100 Stanford3 (11,586 nodes, 568,309 edges);
  details/hashes in `/initial-state/inputs/0/data.md`. Cite Traud et al. 2012, Rossi & Ahmed 2015, McAuley & Leskovec 2012.
  Verify sha256 on download; record in `code/README.md`.

Outcome mechanisms (mean function m_i(z); Y_i = m_i(z) + ε_i, ε ~ N(0,σ²), σ also swept; node baseline α_i
correlated with degree/community so that confounding by position exists):
* M1 linear-mean: m = α_i + b z_i + c (A z)_i / d_i (neighbour fraction). τ = b + c.
* M2 linear-sum: m = α_i + b z_i + c (A z)_i / d̄ (unnormalised; exposure scales with degree).
* M3 nonlinear in exposure: m = α_i + b z_i + c·g(frac_i), g saturating (e.g. tanh/logistic) and threshold/convex variants.
* M4 two-hop: M1 plus c₂ (A² z)_i normalised.
* M5 heterogeneous: coefficients b_i, c_i depend on degree/community/covariate.
* M6 interaction: M1 plus z_i × frac_i term.
ρ = c/b ∈ {0, 0.25, 0.5, 1, 2}; b normalised so τ ≠ 0 is comparable (e.g. fix |τ| = 1 and report relative error).

Designs: Bernoulli(p), p ∈ {0.1, 0.25, 0.5}; completely randomised (p=0.5); graph-cluster randomisation
(clusters from Louvain or balanced partition, cluster-size sweep, plus a degraded-cluster variant); optional
multi-p / staggered design (stage 3).

Estimators
* Baselines: DM; Hajek/HT neighbourhood-exposure estimator (Aronow–Samii; Ugander et al.) with exposure
  "fully treated/fully control neighbourhood", used under cluster designs, noting its high variance when
  exposure probability is small; oracle-feature OLS (true feature map, upper bound).
* Regression: R1 OLS(z); R2 OLS(z, frac); R3 OLS(z, frac, z·frac, degree interactions); R4 + 2-hop;
  R5 ridge on rich graph/treatment features (Han–Ugander style, model-free covariates); R6 GBM/random forest on the
  same features; R7 (stage 3, optional, CPU-small) 2-layer GCN-type regressor. Chin (2019) style linear
  adjustment is the reference regression estimator.
* Misspecified-graph variants (random edge drop/add at rate r ∈ {0, 0.1, 0.3}).

Metrics (and why)
* Primary: RMSE of τ̂ − τ, reported relative to |τ| (scale-free across mechanisms); bias and SD separately
  (RMSE² = bias² + var), since the research question is "what determines the error".
* Coverage and mean width of nominal 95% CIs (blocked bootstrap by cluster, or unit bootstrap for Bernoulli); sign-error rate
  (platform decisions often depend on the sign).
* Uncertainty: R ≥ 200 independent replicates per cell (fresh assignment and noise; graph fixed per cell, plus graph redraws for synthetic
  families), Monte-Carlo SE of every reported mean/RMSE (bootstrap over replicates); paired comparisons across estimators
  on identical draws (paired differences with CI).

## 4. Experiments

* E0 Validity checks (unit tests): ρ=0 ⇒ all estimators unbiased; M1 + R2 unbiased; τ ground-truth equals brute-force
  evaluation; estimator reproduces known linear-case closed forms; seed reproducibility.
* E1 Headline benchmark (RQ1): estimators × {M1, M3, M4, M5} × {ER, SBM, BA, WS, ego-Facebook, Stanford3}, default design Bernoulli(0.5), ρ=1.
* E2 One-factor sweeps (RQ2, RQ3): n; ρ; σ; mean degree; clustering/homophily; p; cluster-size; feature richness; model class.
* E3 Error decomposition + diagnostic (RQ2, H7): population-level (noise-free, large n/exact) extrapolation error vs finite-sample
  error; bias²/variance shares; exposure-support statistic vs error.
* E4 Failure modes (RQ3): M3/M4/M5, misspecified graph, low p, dense graphs (exposure cannot reach extremes), heavy tails.
* E5 Inference (H6): coverage/width vs n, per mechanism, for bootstrap CI.
* T  Short theory (linear case): closed-form/asymptotic expression of the OLS-exposure estimator's error in terms of design
  covariance and graph quantities; used as a prediction checked by E2/E3 (kept at lemma level; if no clean result, say so and drop it).

Each experiment states in `results/` the config, seed, git hash of code, and the input files (provenance).

## 5. Division of work

* `idea-repo`: related-work map, positioning vs starter literature, conventions (this plan supplies the questions).
* `idea-review-repo`: feasibility of this plan vs 1 week / CPU / model-time budget; may prune.
* `experiment-repo`: all code, runs, E0–E5 (+T), diagnostics, uncertainty, `code/README.md` (environment versions, data steps and hashes,
  seeds, commands, expected runtimes, which script produces which table/figure — filled together with figtab).
* `figtab-repo`: figures and tables from `results/` (claim per figure listed in §7), scripts in `figures/`, `tables/`.
* `venue-repo`: pick one of ICML/ICLR/NeurIPS, latest official template, page limit, checklist requirements, into `venue/`.
* `paper-repo`: manuscript in `paper/`, checklist filled, PDF built.
* `internal-review-repo` / `external-review-repo`: judge against the objective and as outside readers.
* Paths: see `.forgejo/CODEOWNERS` (proposed by PR to `paper-repo`).

## 6. Staging (cut by priority if time runs short)

1. Stage 1 (must): E0, E1, E2 sweeps for n, ρ, p, feature-richness, graph families on synthetic graphs + both public graphs for E1; E5 on a subset.
   Baselines DM, Hajek/HT, oracle OLS, R1–R4, R6.
2. Stage 2: E3 decomposition, H7 diagnostic, E4 failure modes, theory T, cluster designs.
3. Stage 3 (optional): GCN regressor, staggered/multi-p design, bigger n on Stanford3.

## 7. What each figure/table must show (for `figtab-repo`; claim → evidence)

* Table 1: setup summary (graphs, mechanisms, estimators, designs, metrics).
* Fig. 1: relative RMSE (with bootstrap CI) of each estimator per mechanism × graph — answers RQ1 (grouped dot plot, shared y; log scale).
* Fig. 2: bias vs SD decomposition (stacked or paired) — shows whether error is bias- or variance-dominated and how it changes with n (log–log, with n^(-1/2) reference).
* Fig. 3: error vs interference strength ρ and vs design p (H1, H4) with DM baseline.
* Fig. 4: extrapolation diagnostic vs |bias| scatter (H7) with fit and per-mechanism R².
* Fig. 5: coverage vs n for the CI (H6), nominal 95% line, Monte-Carlo band.
* Table 2: failure-mode summary (condition → effect on error, with CI), including positive, negative and null findings.
* Any figure showing a sub-claim that the data refute must remain in the paper.

## 8. Risks and what would change the plan

* Compute: Stanford3 (568k edges) with GBM across all cells is expensive; limit to E1 + selected sweeps; run via `local-compute` jobs.
* If H2 is false (flexible learners extrapolate fine, or bias is small): report it; do not tune the mechanism to force a failure.
  Mechanism parameters are fixed by a pre-declared grid before looking at estimator results.
* If hypotheses H1/H7 give no clear regularity: say "no clean law found" and report the conditional picture.

## 9. Amendment after feasibility review (2026-11-02, from `idea-review-repo` via story-repo#2)

Binding limit is the shared model-time budget, not CPU (measured ≈4 ms per 10k-node linear-exposure estimate).
Rules that override the wider text above where they conflict:
1. **Grid, not product.** Main grid: 6 graphs (ER, SBM, BA, WS, ego-Facebook, Stanford3) × 4 mechanisms (M1, M3, M4, M5) ×
   3 designs (Bernoulli 0.5, Bernoulli 0.1, graph-cluster) = 72 cells at n≈2000 (real graphs at native size), ρ=1, with ≥500 replicates per cell.
   Then one-factor sweeps from a default cell, 3–4 levels each: n, ρ, σ, mean degree, p, cluster size, feature richness / model class.
   experiment-repo states the final cell count and reps per cell in `code/README.md`.
2. **Primary metrics fixed now:** bias, SD, RMSE, relative RMSE (= RMSE/|τ|) with Monte-Carlo SEs. Coverage/CI width only for the inference
   subset (E5), which uses a cheap interval (analytic/sandwich or B≤200 bootstrap) on ≤200 replicates; the 100–500× bootstrap cost is not paid on the grid.
   Sign-error rate is secondary.
3. **Theory scoped** to the linear exposure model (M1/M2, OLS on z and neighbour fraction); the paper marks each statement "proved" or "empirical".
4. **Optional, after the main grid:** GCN regressor, staggered/multi-p design, block bootstrap on all cells, bigger Stanford3 sweeps.
5. **Minimum viable delivery first:** main grid, 2–3 figures, 1 table, theory section, paper, NeurIPS checklist → an early merge into `final`
   (or `release` if more results follow). Hold turns back for the paper, checklist and review. Extra stages only add to that.
6. Code is written once, seeded, resumable, smoke-tested on a tiny grid, then the full run goes through `ht-resource run`.
7. Related-work searches limited to the starter list and unrelated work; any accidental encounter recorded in `code/README.md`.

## 10. Delivered file names (settled with venue-repo, story-repo#4)

`paper/main.tex` (source), `paper/checklist.tex` (filled checklist, based on venue-repo `template/checklist.tex`), `paper/references.bib`;
the unmodified template files are delivered by venue-repo as `venue/neurips_2026.sty`, `venue/checklist.tex`, `venue/README.md`; as venue-repo's
`venue-artifacts.json` also lists `paper/neurips_2026.sty`, paper-repo keeps an unmodified (identical-hash) copy there; built PDF `paper.pdf` (delivery root), reproduction notes `code/README.md`, code in `code/`,
figure/table → script map `figures/README.md`. NeurIPS 2026 main track, 9 content pages, anonymous mode.

## 11. Addition after idea-repo `Brief` (2026-11-02)

E0 also includes a **reproduction sanity check of the reference setting** (Chin 2019): Stanford3 largest component, Bernoulli design,
linear-in-neighbour-fraction truth, DM vs Hájek/q-NTR (q=0.75) vs OLS-adjusted, ≥1000 replicates; the qualitative ordering (DM biased, adjusted
near-unbiased) should match what Chin reports, otherwise the code is suspect before any new result is trusted. Hypothesis H2/H7 is the Brief's
extrapolation view: bias ≈ extrapolation distance (training exposure distribution → exposure 0/1) × misspecification residual.

## 12. Pruning from `idea-review-repo` (REVIEW_PLAN.md; supersedes §6/§9 where they conflict)

* Total cells ≤ ~300 (main grid 72 cells; sweeps on 2–3 base graphs at n=2000); main-grid R ≥ 500 for OLS/HGB estimators, sweeps R=200. Random forest only on a subset (2 s/fit).
* Bootstrap CIs for OLS-type estimators only (what is resampled under Bernoulli: units; under cluster designs: clusters); HGB bootstrap at most B≤50 on 3–4 cells; no RF bootstrap.
* Main-text hypotheses: H1, H2, H3, H6, H7. H5 (graph misspecification) → stage 2/appendix. H4 only as the Bernoulli-p sweep.
* Dropped: multi-p/staggered design, GCN regressor, M6 as a separate mechanism (kept only as the interaction feature in R3), bigger-n Stanford3 sweeps.
* Hájek/HT is undefined under Bernoulli on dense graphs (full-neighbourhood probability p^d; Stanford3 mean degree ≈98): report the undefined rate; use it under cluster designs or as a labelled relaxed-exposure variant.
* τ: compute from m(1)−m(0), then rescale so |τ| is bounded away from 0; report absolute RMSE as well as relative.
* H7 population error = σ=0 fit averaged over assignment draws. Use A@(A@z) for 2-hop (no dense A²).
* Both graphs downloaded and sha256-checked in a turn first (jobs have no network); config committed before results; smoke test, resumable per-cell output.
* `code/README.md` always contains an "accidental encounters with prohibited material" section.
