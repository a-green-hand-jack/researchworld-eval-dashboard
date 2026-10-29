# Post-Draft Reference Query Plan

**Status:** ready

**Central topic:** How few comparisons have to be dropped or flipped to change the top-1 or top-k set of a Bradley–Terry leaderboard. Sizes come from a one-step influence (AMIP-style) search verified by exact refits. The comparison covers crowdsourced (Chatbot Arena), expert and LLM-judge (MT-Bench), and sports (NBA) designs.

## Scope
This is an incremental pass driven only by `draft_reference_gaps.{md,json}`. All 27 existing bib entries are already cited, and coverage is dense. Three paragraph-specific gaps remain, and each gets two queries (6 in total). Each target should add at most 1–3 citations, inserted only at the anchored sentences.

## Queries

### Target 1: `method-upper-bound-auditing` (high, positioning)
Anchors: Method, "What a verified size means" ("Computing $k^\star$ is a combinatorial search problem. Provable auditing is known only in special settings…"), and Discussion, "Upper bounds, not minima" (no citation yet).

1. **`core_method`**: *failure modes of approximate maximum influence perturbation when dropping many data points together*
   Looks for documented cases where the one-step AMIP ordering misses smaller drop sets. These would support the caveat that the true minimum may be much smaller. Skip Broderick2020, Basu2020, Koh2017 and the Giordano jackknife papers, which are already cited.
2. **`core_method`**: *exact algorithms and lower-bound certificates for the minimal data-dropping set that overturns a statistical conclusion*
   Adds greedy, exact or certified drop-set work next to Moitra2022 (low-dimensional OLS), which is currently the only support for "provable auditing only in special settings".

### Target 2: `related-work-corruption-robust-ranking` (medium, comparator)
Anchor: Related Work, "Adversarial attacks on rank aggregation have also been analyzed as games between attacker and aggregator" (currently Ma2022 only).

3. **`baseline_comparator`**: *ranking from pairwise comparisons with a fraction of adversarially corrupted comparisons*
   Corruption-robust BTL/rank-aggregation theory is the natural comparator for the flip perturbation, which models mislabeled or adversarial votes. Shah2015 covers stochastic noise only, so do not use it again.
4. **`baseline_comparator`**: *data poisoning attack on Bradley-Terry-Luce rank aggregation from pairwise comparisons*
   Attack-side papers on BTL-type aggregators to sit next to our drop and flip sets. Exclude Ma2022 and Min2025, which are already cited.

### Target 3: `method-data-sports-design` (medium, benchmark_context)
Anchor: Method, "Data and protocol" ("NBA games from two seasons of the FiveThirtyEight Elo record … each game a comparison between two teams"). The only sports citation is Elo (1978), which is about chess.

5. **`benchmark_context`**: *Bradley-Terry paired comparison model for rating sports teams from game results*
   Motivates modeling team games as BT comparisons, since the NBA design drives the count-scale finding.
6. **`benchmark_context`**: *statistical rating models for professional basketball team strength and game outcome prediction*
   Fallback for a basketball- or team-sport-specific reference. Use it only if query 5 returns nothing suitable, and add at most one citation.

## Deliberately not queried (deferred in the gap memo)
- More LLM-judge bias work: Zheng2023 and Dubois2024 are enough.
- "Style-controlled" Arena scores: the source is likely a blog post.
- Tie models beyond Davidson (1970).
- The knapsack, relinearized and swap search variants: these were never evaluated.
- Re-queries of literatures already in the bib: AMIP, influence functions and jackknife, top-K/spectral ranking, the Arena and MT-Bench platforms, BT CIs and bootstrap.

## Forbidden patterns (carried over from `reference_query_plan.json`)
- Do not copy the research-question title into a query.
- No "Huang et al. 2025 follow-ups" or "who cites" queries.
- No generic filler, and no chronology or infrastructure queries.
- Do not query the untested knapsack variant as if it were a contribution.
- If a retrieval for queries 1–2 returns Huang2025DroppingJA or pages that cite it, discard those results.
