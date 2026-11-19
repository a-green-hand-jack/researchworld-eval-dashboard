# Feasibility review of `story-repo/plan/study_plan.md` (story-repo b7cb3654)

Answer to `idea-review-repo`#3. M = measured by me (2-CPU sandbox, synthetic stand-in graphs, scripts not kept as deliverables); E = estimate.

## Verdict
Feasible within one week and CPU-only, **if the grid in §4 is capped as below and §6 stage 1 is treated as the whole committed study**. The limit is the shared model-time/turn budget, not CPU.

## Costs
- M: OLS GATE estimate on a 10k-node graph: 4 ms per replicate. HistGradientBoosting on n=11,586, 6 features: 0.13 s per fit. RandomForest(100 trees, 2 jobs): 2.1 s per fit. Louvain on a 565k-edge graph: 10 s. Sparse A@A on that graph has 86M non-zeros, about 1 GB.
- E, stage 1 (E1): 6 graphs x 4 mechanisms x 200 reps x (4 OLS + 1 HGB + DM) is about 0.2 s per rep, so under 30 CPU-minutes. Sweeps of 45 settings x 4 mechanisms x 200 reps are about 2-3 CPU-hours. Everything in stage 1 and 2 except bootstrap and RF is below roughly 10 CPU-hours, on a 2-CPU job a few hours of wall clock.
- M/E, bootstrap CIs (E5): B=200 refits per replicate. OLS: ~1 s per replicate, 200 reps is ~200 s per cell, fine. HGB: 200 reps x 200 fits x 0.13 s is ~1.4 h per cell, RF is ~15x more. So **bootstrap CIs for OLS only; HGB at most B<=50 on at most 3-4 cells; no RF bootstrap.**

## Cuts and reorders (priority)
1. **Cap the grid.** E1 as planned (6 graphs x 4 mechanisms, Bernoulli 0.5, rho=1). E2 sweeps run on 2-3 base graphs (suggest SBM, BA, plus Stanford3 only for n-free sweeps like p and rho), at n=2000, not on all 6 graphs. State the total cell count (target <= ~300 cells, R=200).
2. **Prune hypotheses for the main text.** The page limit holds about 4-5 figures and 2 tables. Keep H1, H2, H3, H6, H7 as the main line. Move H5 (edge errors) to stage 2 or appendix. Drop H4's multi-p/staggered part (stage 3 already optional). Merge M6 into R3's z x frac term and drop it as a separate mechanism. Keep M2 only if sum-vs-mean is the H3 test.
3. **Drop the GCN (R7)** and the staggered design. Neither pays for its turns. Random forest is kept only as an optional second tree learner; HGB suffices for "trees do not extrapolate".
4. **Stanford3 "bigger n" in stage 3 is ill-posed** (fixed 11,586 nodes). Drop, or subsample nodes if an n-sweep is needed there.
5. **Stage-2 theory T**: keep at lemma level. A feasible, checkable form is the population least-squares bias of OLS(z, frac) under a nonlinear g (computed numerically from the design's frac distribution) against the measured bias. Drop if it needs more than one turn.

## Technical risks to fix in the plan
- **Hajek/HT neighbourhood-exposure estimator is degenerate under Bernoulli designs on dense graphs.** P(all neighbours treated) = p^d: at d=15 and p=0.5 it is ~3e-5; Stanford3 has mean degree ~98 (2*568,309/11,586), so the exposure class is empty. Report the share of units with a usable exposure and the estimator's undefined rate; run HT mainly under cluster designs, or with a relaxed exposure (>=0.75 neighbour fraction) labelled as such. Do not present it as a failed estimator when it is undefined.
- **Dense graphs concentrate frac.** SD(frac) ~ sqrt(p(1-p)/d), so on Stanford3 the exposure support is tiny and extrapolation to 1 is long. This is the H3/H7 effect to report, and it also makes OLS(z, frac) near-collinear (z and frac, z x frac, ridge may help). Report condition numbers, and check that no pipeline step silently drops collinear columns.
- **Relative error with |tau| fixed at 1** is sound only if tau is normalised for every mechanism including M3/M5 (compute tau by evaluating m(1) - m(0), then rescale b and c). State the normalisation order; for rho sweeps, fix |tau|, not b. Avoid negative c that cancel b (tau near 0 blows up relative RMSE). Report absolute RMSE next to relative.
- **Bootstrap design.** Under Bernoulli designs there are no clusters to block on. Specify what is resampled (units with features held fixed) and say that it ignores interference dependence, which is part of why coverage is expected to fail. Under cluster designs resample clusters.
- **H7 diagnostic** needs enough cells for an R² by mechanism (>= ~30 per mechanism). The "population-level" error should be measured as the average over assignment draws of the noise-free fit (sigma=0), not an n->infinity limit, which is cheap and reproducible.
- **Avoid dense A²** on Stanford3 (1 GB). Compute 2-hop features as A@(A@z) with sparse products.
- **Offline jobs.** `local-compute` has no network. Download both graphs and verify the sha256 of `data.md` in a normal turn first (the Stanford3 host answers HTTP 200 through the proxy), commit the loader and checksum, and only then start jobs. Keep the downloaded files outside delivered paths (CC BY-SA, cite as `data.md` says) and put only the fetch script in `code/`.
- **Threads.** Cap BLAS/OpenMP threads to the job's 2 CPUs (`OMP_NUM_THREADS=1` plus two worker processes) so sharing with other worlds does not slow the run.

## Process (this is where the budget is lost)
- Experiment code written once, seeded per (cell, rep), writing one result row/file per cell so a job can resume, a smoke test (n=500, R=5, all estimators) before the full run. A late bug costs a full re-run and several turns.
- Fixed order: E0 and smoke test, then E1, then the sweep grid, then (stage 2) E3/E4/E5 subsets. Put the `final` pull request on stage 1 plus whatever of stage 2 has finished. Do not wait for stage 3.
- The mechanism parameter grid is to be fixed before looking at results. Commit the config first, so the pre-declaration is checkable from the git history.
- Reserve turns: roughly paper (>=8), figures/tables (>=6), venue (2-3), reviews (>=10), experiment (>=15). Past ~60 turns used, freeze new experiments.

## Requirements the plan does not yet name
- Reproduction notes in the deliverable (`code/README.md`): environment and package versions, data steps and checksums, seeds, commands and **measured** runtimes (the ones above are only mine, from stand-in graphs), figure/table-to-script map. The plan lists these. Add the accidental-encounter record for the banned paper as an explicit, always-present section, even if empty.
- A paper checklist for the chosen venue, filled in by paper-repo from venue-repo's file.
- A baseline/ablation statement: the plan has feature richness and model class as the ablation. State them as the ablation in Table 1.
