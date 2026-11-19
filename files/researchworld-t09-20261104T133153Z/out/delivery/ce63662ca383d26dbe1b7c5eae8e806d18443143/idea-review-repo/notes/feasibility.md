# Feasibility assessment (idea-review-repo) — v1, before costly work

Basis: objective issue + `/initial-state` files; two measurements made in this turn (below). Planning estimates are marked *est.*

## Verdict
The objective is feasible within one week and CPU only **if the study stays a simulation/semi-synthetic study of a regression-adjusted GATE estimator, with theory limited to what can be checked numerically**. A full new theorem with tight bounds is *not* a safe commitment; make it a stretch goal with an empirical fallback that still answers every question in the objective.

## Measured facts (this turn)
- `socfb-Stanford3` downloads from the stated URL (HTTP 200, 1,649,740 B, sha256 matches `data.md`: b1221e41…20d); .mtx loads in 0.27 s: n=11,586, 568,309 edges, mean degree 98.1, max degree 1,172 (dense, heavy-tailed).
- Sandbox: 2 CPUs, 4 GB RAM (the host shows more, but the ceiling is ours), scipy 1.17.1, sklearn 1.9.1, networkx 3.6.1, torch CPU available.
- One full replicate on Stanford3 (Bernoulli(0.5) assignment, linear-in-means outcome, OLS on [1, z, mean-neighbour z, sum-neighbour z], predict all-1 vs all-0) takes ≈ 11 ms; 200 replicates = 2.3 s. So linear/ridge estimators are not a compute constraint: 10^3–10^4 replicates per cell is *est.* minutes per cell.

## Compute budget (est.)
- Linear / sparse-feature regressions (OLS, ridge, neighbourhood-exposure features, polynomial in exposure): ~10 ms–1 s per replicate on n≈10^4. A grid of ~10^3 cells × 10^3 reps ≈ 10^6 replicates ≈ a few CPU-hours. Fits in 2 CPUs.
- Cluster-randomised designs need a graph partition once per graph (METIS may need installing; label-propagation / networkx Louvain on 568k edges is *est.* seconds–minute). Do once, cache.
- Flexible learners (GBM, small GNN/GCN on CPU) are 10^2–10^3× costlier (*est.* 1–60 s per fit). Restrict to a small number of cells, ≤200 reps, and say so. A GNN baseline is optional, not required by the objective.
- Variance/inference via bootstrap or block bootstrap multiplies cost by B (100–500): apply only to a subset of cells (coverage study), not the whole grid.
- Total *est.* well under the "tens of CPU-hours" in `resources.md`; the binding constraint is the 4 GB memory and 2 CPUs, plus wall-clock of turns, not compute. Use `ht-resource run` for anything > 1–2 min; do not hold sandbox jobs.

## Risks and what to bound
1. **Ground truth must be exact.** GATE is computable exactly only because the outcome model is known (evaluate it at all-1 and all-0). Real/semi-real outcomes are not allowed here; state that "truth" is model-defined. Bound: all outcome models must be coded so Y(1) and Y(0) are evaluable without noise.
2. **Scope creep in factors.** Network × interference form × design × estimator × feature set × n × noise is a combinatorial explosion. Bound: choose ≤4 primary factors with one-factor-at-a-time sweeps around a default plus one 2-way interaction grid; relegate the rest to appendix. Pre-register hypotheses (story-repo) before running.
3. **Well-specified vs misspecified.** If the regression is correctly specified the result is a textbook OLS result and is uninformative (novelty risk). The informative regimes are misspecification (nonlinear exposure response, heterogeneous neighbour influence, degree-dependent effects), high-degree/heavy-tail networks, and sample-size scaling. Include these as primary, with a correctly-specified control.
4. **Dense Stanford3 graph (mean degree ~98, hub degree 1,172)**: exposure features concentrate (fraction treated → p), so treated fraction neighbourhoods have little variation under Bernoulli design; this is a *finding* for the study, but also means one real graph is not enough for "network structure" claims. Add ≥3 synthetic families (SBM, BA, WS; plus ego-Facebook, 4,039 nodes) with matched size/density to separate structure from size. Stanford3's dense A·z features are 11.6k×11.6k sparse: fine in memory (~7 MB).
5. **Theory.** A claim "error is determined by X" invites a bound. Feasible: error decomposition (bias from misspecification + variance of the fitted parameters + design effect), derived under linear/low-order exposure models and checked numerically with the simulation. Not feasible in a week: tight general-graph minimax bounds. Bound: state theory as proposition(s) with explicit assumptions, label empirical scaling laws as empirical, and report where they fail.
6. **Uncertainty.** Every table/figure needs replicate counts, MC standard errors or CIs; ≥500 replicates per headline cell (*est.* cheap). Use common random numbers across estimators within a replicate (same z, same noise) so comparisons are paired.
7. **Baselines to bound the set**: difference-in-means, Horvitz–Thompson / Hajek on exposure mappings (Aronow–Samii), cluster randomisation + DM (Ugander et al.), regression on neighbour-treated-fraction (Chin), and an oracle-feature regression. HT with k-hop exposures has huge variance on a dense graph; expect near-zero effective sample (*est.* not computed) — report this rather than tune it away.
8. **Forbidden material.** The published paper that studied this question must not be retrieved. Search by starter-literature authors/topics only; do not query for "regression GATE estimation error bound networks" combinations aimed at recent (post-2024-10) work, and stop reading and log (in the reproduction notes) any page that discusses it or cites it. Report accidental encounters honestly. Related-work searches should be bounded to pre-2024-10-16 literature plus clearly unrelated work.
9. **Deliverable load.** A conference paper (ICML/ICLR/NeurIPS, latest template — venue-repo must verify the *latest* template and page limit with a real fetch, not memory), a checklist, and a reproduction README with per-figure scripts. Paper writing and figure work are as long as the experiments; do not start the full grid before the story fixes which tables/figures exist, but do start a small pilot (the 11 ms/replicate harness) immediately so the grid is shaped by what is measured.
10. **Environment.** METIS / `torch_geometric` may be unavailable or slow to install; fallback is Louvain (networkx) and a hand-written 2-layer GCN with scipy sparse. No GPU needed.

## Recommended scope (for story-repo)
- Primary: estimator = regression-adjusted GATE with exposure features, vs 4 baselines above; networks = Stanford3, ego-Facebook, SBM, BA, WS (n≈4k–12k); interference = linear-in-means, nonlinear saturating, degree-heterogeneous, with monotone strength γ; designs = Bernoulli(p) and graph-cluster randomisation; metrics = bias, RMSE, relative RMSE, CI coverage (block bootstrap on a subset), and a decomposition of error into bias/variance.
- Stretch: analytic error decomposition; GNN/GBM regression; staggered rollout comparison (Cortez et al.).
- Cut first if time runs short: GNN, staggered rollout, multiple outcome families beyond three.

## What this assessment does not do
It produces no results; all performance claims above are *est.* except the listed measurements. Re-assess once the pilot grid exists. Requests welcome via issues here.
