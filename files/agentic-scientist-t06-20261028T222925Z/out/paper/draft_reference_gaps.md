# Draft Reference Gaps

**Status:** ready

## Summary
The draft (`paper.tex`) already has dense, well-placed citations. All 27 entries in `references.bib` are cited. The Introduction and the three Related Work paragraphs (paired-comparison models, influence and drop-data robustness, LLM leaderboard manipulation) cover the expected literature. Every quantitative claim is grounded in `paper_data.json` or `analysis/derived_stats.json`, so no numeric claim needs a citation.

Three paragraph-specific gaps remain where 1–3 targeted citations would materially improve reviewer-facing support. None of them requires reshaping the paper's story.

## Rewrite targets

### 1. `method-upper-bound-auditing` (Method, "What a verified size means"; Discussion, "Upper bounds, not minima") — **high**, positioning
- **Anchor:** "Computing $k^\star$ is a combinatorial search problem. Provable auditing is known only in special settings…"
- **Why:** The paper's central caveat is that each size is an upper bound from a one-step influence ordering, and that the true minimum "may be smaller, possibly by a lot". Only one citation supports this (low-dimensional OLS auditing), and the limitation paragraph has none. Reviewers who know the drop-data literature will expect two kinds of follow-up work: algorithms that tighten or certify drop-data sets (greedy or exact search, lower-bound certificates), and documented failure modes of the one-step approximation. Both bear directly on how loose the reported sizes may be.
- **Search topics:**
  - failure modes of approximate maximum influence perturbation for worst-case data dropping
  - greedy or exact algorithms for finding minimal data-dropping sets that overturn a conclusion
  - robustness auditing lower bounds and certificates for small data subsets in regression

### 2. `related-work-corruption-robust-ranking` (Related Work, "Manipulation and validity of LLM leaderboards") — **medium**, comparator
- **Anchor:** "Adversarial attacks on rank aggregation have also been analyzed as games between attacker and aggregator"
- **Why:** The flip perturbation is motivated as modeling mislabeled or adversarially cast votes. Only one paper on attacks against rank aggregation is cited. Theory for ranking from pairwise comparisons under a fraction of adversarially corrupted comparisons is the natural comparator family for the flip results, and it is absent.
- **Search topics:**
  - rank aggregation from pairwise comparisons with adversarial corruptions
  - data poisoning attacks on Bradley–Terry or BTL ranking from pairwise comparisons

### 3. `method-data-sports-design` (Method, "Data and protocol") — **medium**, benchmark_context
- **Anchor:** "NBA games from two seasons of the FiveThirtyEight Elo record … each game a comparison between two teams"
- **Why:** The NBA seasons are one of four designs and drive the count-scale finding (7 and 16 games; a single game moves the top-5 set). The only sports citation is Elo (1978), which is about chess. Without a citation for paired-comparison or BT modeling of team sports, the sports design looks unmotivated next to the well-cited LLM designs.
- **Search topics:**
  - Bradley–Terry paired comparison models for rating sports teams
  - statistical rating systems for professional basketball or team sports

## Considered and deferred
- **LLM-judge vs. expert disagreement (Results, "Expert humans vs. an LLM judge").** The paragraph explicitly declines a causal "judge effect" interpretation. Zheng et al. and Dubois et al. already cite judge biases. Further judge-bias citations would add bibliography size, not support.
- **"Style-controlled scores" (Limitations).** This is a single-phrase mention. Its canonical source is probably a blog post rather than a retrievable paper, so it is not worth a retrieval pass.
- **Tie handling as half wins (Related Work).** Davidson (1970) is already cited for tie models, which is enough.
- **Refined search variants (knapsack, relinearization, swap).** These were never evaluated, so seeking citations for them would inflate an ungrounded part of the story.

## Constraints for the retrieval pass
- Use component-literature queries only. Do not use title copies of the research question or "follow-ups of Huang et al. (2025)" queries; `reference_query_plan.json` forbids them.
- Add at most 1–3 citations per target. Insert them only at the anchored sentences, with no broader rewrite.
