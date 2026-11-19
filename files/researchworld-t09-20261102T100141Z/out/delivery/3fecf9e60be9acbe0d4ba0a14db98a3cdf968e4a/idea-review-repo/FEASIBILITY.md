# Feasibility
**Deliver:** a pre-work feasibility judgement of the study plan against the objective (`Research objective`#1 and `deliverable.md`, `resources.md`, `data.md`), published as the wiki page `Feasibility` and updated when story-repo's plan or the budget changes. It names risks, costs, scope limits and what to bound or revise. It produces no evidence of its own beyond the cost benchmark below.
**Standard:** every cost figure is marked measured / sourced / estimated; every recommendation says which requirement it protects.
**Not mine:** the plan (story-repo), analyses (experiment-repo), figures, venue, paper, review.

### First judgement (before a plan exists)

**Verdict: feasible if scoped to a bounded factorial simulation. At risk if scope grows toward every network x mechanism x estimator x design cell, or toward unbounded-resampling inference.**

Measured (my sandbox, 2 CPUs, `networkx`/`scipy`/`sklearn`): one replicate on a 10k-node BA(m=25) or WS(k=50) graph, Bernoulli(0.5) assignment, linear-in-(z, neighbor-mean z) outcome, OLS GATE estimate takes about 4 ms (200 reps each). Both graphs gave bias near 0 and SD 0.12-0.15 on a true GATE of 1.5. Graph build and exposure features are cheap. The Stanford3 download endpoint answers HTTP 200 through the proxy. **Compute is not the binding constraint.** The objective's "tens of CPU hours" is an unmeasured upper bound and is generous for regression estimators with 1e3-1e4 reps per cell.

**Binding constraint: the shared model-time budget (7200 s, 96 turns, 9 positions), not CPU.** Every position's turn spends it, including writing, review and revision loops. Consequences:
1. The experiment code must be written once, run through `ht-resource run` as a single seeded grid with resumable output, and not be rewritten across turns.
2. A paper, a venue template with checklist, and two review rounds need enough turns held back. Reserve a final stretch for paper, figures and review, and do not let experiments consume the whole budget.
3. A world that ends without a release delivers nothing. Aim for one complete delivery into `final` early, not many intermediate releases.

### Risks and scope limits

- **Theory vs. simulation.** The objective asks what determines the error, not only how large it is. A full finite-sample theorem is not feasible in this budget. Feasible and sufficient: a derivation or bound for the *linear* exposure model (bias from misspecification, variance from the effective number of independent units and degree/cluster structure), then empirical checks of its predictions. State clearly which claims are proved and which are empirical.
- **Factor explosion.** Bound the factors to about 4-5, each with 3-4 levels: network family and size (SBM, BA, WS, plus one real graph, Stanford3 or ego-Facebook), interference strength and form (linear one-hop; heterogeneous; nonlinear/saturating; two-hop), assignment (Bernoulli vs. graph-cluster randomization), model class (OLS on z and neighbor fraction, richer features, optionally a regularised or GNN-type model), and sample size n. Run a main grid, then one-factor sweeps and ablations, not the full product.
- **GNN/GCN baselines.** CPU-only training in a replicate loop is the one place where cost can blow up. Make it optional and limited to a few cells with few seeds, or drop it. A CPU-fast linear/ridge/tree comparison covers the question.
- **Inference/CIs.** Repeated simulation gives the sampling distribution of the estimator cheaply, so uncertainty comes from Monte Carlo SEs over replicates. Block bootstrap on the estimator itself multiplies cost 100-500x. Run it on a small subset only, and only if the plan makes coverage a claim.
- **Real graphs.** Stanford3 (11,586 nodes, 568k edges, CC BY-SA, sha256 in `data.md`) is the cheaper and sufficient real graph. The ego-Facebook graph (4,039 nodes) is optional. Record sha256 and citations. A 568k-edge graph is fine in sparse form, but dense neighbourhoods make exposures concentrate, which is itself a finding to report.
- **Cluster randomization needs a clustering.** Use a fast method (Louvain via `networkx`, or label propagation); on Stanford3 it can take minutes, so compute once and cache it.
- **Ground truth.** GATE is known exactly in a synthetic model (all-ones minus all-zeros outcome), so error is exactly measurable. Do not claim anything about real-platform behaviour; real graphs supply topology only, with synthetic outcomes.
- **Forbidden material.** The task excludes one published paper and anything citing or discussing it. Searches for related work should stay on the starter list (Chin 2019, Han & Ugander 2023, Aronow & Samii, Ugander et al., Eckles et al., Cortez et al.) and other independent work. Searching for phrases like "regression GATE estimation error bound" risks hitting the excluded paper. If one is met, stop reading and record it in the reproduction notes. idea-repo and paper-repo should be told. This is a compliance risk, not a compute risk.
- **Novelty.** Chin 2019 and Han & Ugander 2023 already cover regression-adjusted GATE under correct/misspecified models. The contribution must be stated narrowly (a systematic characterisation of when the error is small or large and what drives it), not as a new estimator. Do not oversell.
- **Venue.** Page limit, latest-year template and checklist are required deliverables. venue-repo must fix the venue early, and experiments should be sized to what fits the main text, with the rest in an appendix.

### What to bound or revise (asks to story-repo)

1. Fix a grid in the plan with a stated cell count and replicates per cell (suggest 500-2000 per cell, which is minutes of CPU per cell).
2. Pick the primary metrics in advance: bias, RMSE, relative RMSE and CI coverage if inference is claimed. Report Monte Carlo SEs.
3. Keep GNN and bootstrap inference as optional subsets, run only after the main grid is done.
4. Put the minimum viable delivery first: main grid, 2-3 figures, one table, a theory section for the linear case, then the paper. Extras come later.
5. Seed everything, write results to files with the script that produced them, and record package versions, since the deliverable requires reproduction notes and a figure-to-script map.
6. Run the code once in a small smoke test before the full grid, so a bug does not cost a full-grid run.

I will revise this when the plan or the budget changes.
