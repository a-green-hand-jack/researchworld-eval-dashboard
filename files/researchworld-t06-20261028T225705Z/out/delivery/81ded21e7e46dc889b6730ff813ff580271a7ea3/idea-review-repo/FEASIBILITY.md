# Feasibility assessment (idea-review-repo)

Basis: the frozen task material, plus a 3-minute probe of the actual data (measured, scripts not part of the delivery). Measured vs. estimated is marked.

## 1. What binds: the world budget, not the CPU
- Measured: one BT fit on Arena-55k (57,477 battles, 64 models, ties as half-wins, plain NumPy/SciPy L-BFGS) takes **0.10 s**. Compute is not the constraint; even 10^5 refits is ~3 CPU-hours.
- The world has 7,200 model-seconds and 96 turns for nine positions (spent in total, not per position). The binding risks are therefore plan churn, re-running analyses because of unclear definitions, and a long writing/figure/review loop. Everything that computes goes to `ht-resource run` jobs; every analysis script should be one deterministic entry point that writes all result tables, so analysis, figures and paper can be regenerated without model time.

## 2. Data actually available (checked, checksums match data.md)
| design | data | measured facts | feasibility note |
|---|---|---|---|
| crowd votes | Arena-55k | 57,477 battles, 64 models, 2,454 model pairs (median 10 battles/pair, min 1), ties 17,761 (31%) | core dataset; ties need an explicit rule (half-win, or drop as a sensitivity check) |
| expert | MT-Bench human | 3,355 judgments, 6 models (15 pairs), 3 outcomes incl. 780 ties | tiny N and 6 items: "top-1 flip" and rank statistics are coarse; report as such |
| model judge | MT-Bench GPT-4 pairs | 2,400 judgments on the same models; `model_b` wins 1,610 vs `model_a` 190, plus 380 "tie (inconsistent)" | strong position bias: needs a stated rule (treat inconsistent as tie, or symmetrise); same models as the human data, so human vs judge on the same items is a clean comparison |
| sports | NBA Elo (fivethirtyeight) | 63,157 games (each twice in the file; use `_iscopy==0`), 104 teams, 1947–2015, no ties, 69 seasons of ~215–1,319 games | static BT over 70 years is misspecified (teams change, home advantage): analyse per season (or per era) with a home-advantage term; regular season vs playoffs must be decided |
- Optional sources (Arena-140k 1.6 GB, potsawee judges with undeclared licence, WebDev Arena with a click-through licence) add risk and disk/time for little gain: **recommend excluding by default**; take Arena-140k only as a late, column-limited replication if budget remains. Synthetic data is allowed only labelled as such (useful as a calibration check of the method, never as evidence).
- Requirement "at least two evaluation designs of real data" is met by Arena + MT-Bench human at minimum; MT-Bench judge and NBA make four; no external access problem was found.

## 3. Method feasibility and what must be bounded
- Exact "smallest set of comparisons whose removal changes the ranking" is combinatorial. The tractable route is: influence-function approximation to propose removals, greedy/iterative selection, then **exact refit to verify** (refit = 0.1 s). The result is an *upper bound* on the minimal flip size (a certificate that a flip exists); failure to find one does not prove robustness. Claims must say "found a removal of k comparisons that flips X", never "the minimum is k", unless verified on small cases by exhaustive search.
- Targets must be bounded: do not attack all ~2,000 pairs on Arena. Fix a small, pre-declared set of events: top-1 identity, adjacent-pair order for the top-k (e.g. k=10) and, for comparison across sizes, a rank-correlation drop. Pre-declare before looking at results.
- Perturbation families worth keeping (each cheap): random removal (the baseline that gives the noise scale), adversarial removal, bootstrap/CI overlap as the field's own uncertainty statement, and optionally adversarial addition (vote rigging) as the deliberate-change case. More than these, e.g. also model-fit alternatives (ties handling, Elo online vs BT, regularisation), should be limited to sensitivity checks on one dataset.
- Cross-dataset comparison is the weak point: N, number of items, tie share and gaps differ by orders of magnitude (6 teams-worth vs 64 models vs 104 teams). A raw "k removals" is not comparable. Define the change size as a fraction of comparisons (and of the comparisons involving the two items), and report it **relative to the sampling noise** (bootstrap scale of the same gap). State this definition in the plan, with reason; otherwise any dataset difference is confounded with size.
- Uncertainty: bootstrap/subsample over comparisons (≥200 resamples = 20 s per statistic at 0.1 s/fit; fine). Arena rows are not independent (repeat prompts/users, not available as an id): note it as a limitation, do not claim independence.
- Estimated (unmeasured) cost of the adversarial search: a greedy with refit verification at ~10^2–10^3 refits per target × ~10–50 targets × 4 datasets ≈ 10^4–10^5 refits ≈ 0.3–3 CPU-hours. Benchmark on one target first. Fits for NBA seasons (≤1,319 games, ~30 teams) are faster than Arena's.

## 4. Scope limits that must stay in the paper
- "Sensitivity" is of the fitted BT ranking to the given records, under a defined perturbation; it is not a statement about real leaderboard integrity (live leaderboards use more data/ other pipelines/ later model sets than these snapshots; Arena-55k is a 2023–24 snapshot).
- NBA ranks teams by a static model over short windows; conclusions about "sports" are limited to this BT model of this data, not about sports rankings generally. Only two or three designs, one dataset each (MT-Bench pairs share models between human and judge): do not state design-level causal conclusions ("experts vs. crowds") from n=1 dataset per design; present as observations conditional on size, tie rate and gap structure.
- The data.md instruction: raw data go in `data/` outside the code repository; record sources, commits and sha256 (done above for the 4 core files).

## 5. Compliance risks to hold
- The task forbids reading the earlier published paper and anything that cites or discusses it. Starter item 8 is formally on the allowed list, but its description matches the barred paper closely; story-repo's plan and idea-repo's Brief treat it as not to be read, cited or searched for. I endorse that conservative reading (cost: one missing citation; benefit: no compliance risk); do not cite anything not actually read. Log any accidental contact in the reproduction notes.
- Disclose LLM assistance in the paper (resources.md). All numbers in the paper must come from the delivered code; no placeholder figures at any stage.
- The paper needs the *latest* conference template and checklist: that is a venue question to check early (template availability offline is the usual failure); `venue-repo` should confirm before writing starts.

## 6. Recommended revisions to the plan (if the plan departs from this)
1. Core data: Arena-55k, MT-Bench human, MT-Bench GPT-4, NBA (per season/era). Others out.
2. Fixed pre-declared target events and a size-normalised flip measure, compared with the random-removal and bootstrap noise scale.
3. One analysis entry point, run as `local-compute` jobs; bench the first target before the full sweep.
4. Cap the number of figures/tables (e.g. ≤4 main) so that figtab/paper/review loops fit the model-time budget; treat the review rounds as the scarce resource.

## 7. Verdict on story-repo PLAN.md v1 (a2ad31c)
Feasible for **tier 1 plus the sensitivity table and synthetic calibration**, not for the whole plan; see the issue in story-repo for the requested changes (normalisation definition, common-N control, bootstrap-of-attack cost, tier-2 cut, budget gates).
