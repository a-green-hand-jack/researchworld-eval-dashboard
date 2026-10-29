# Post-draft reference query plan

**Status:** ready. No retrieval was run in this stage.

## Central topic
Ridge-regression prediction of start-averaged cover time on small connected graphs (6 ≤ n ≤ 30), compared against the generic 2m(n-1) worst-case bound. This plan only fills citation gaps exposed by the current draft.

## Existing bibliography (not re-queried)
- Feige, tight upper bound on cover time
- Feige, tight lower bound on cover time
- Kiwi et al., cover and hitting times of hyperbolic random graphs

The gap artifact judges these adequate, so they are excluded.

## Queries (5)

1. **Aleliunas et al., "Random walks, universal traversal sequences, and the complexity of maze problems"** (`baseline_comparator`). This is the source of the 2m(n-1) bound, the headline comparator. It is attributed by author name only, in the Introduction and in Related Work (worst-case bounds). It has priority high.
2. **Lovász, "Random walks on graphs: a survey"** (`baseline_comparator`). The Related Work worst-case-bounds paragraph names this survey for hitting-time and commute-time machinery without a citation. It has priority high and shares the same paragraph as query 1.
3. **Chandra et al., "The electrical resistance of a graph captures its commute and cover times"** (`core_method`). Discussion ("Feature attribution and ceiling") and the Conclusion propose resistance-based features, motivated by the commute-time identity, as the next step. Nothing currently supports that. It has priority medium.
4. **Matthews bounds on covering times via maximum hitting time** (`core_method`). It supports the "Matthews-type bounds" claim in the same passages and the unscored Matthews-style candidate in the supplementary model-selection note. It has priority medium.
5. **Hoerl and Kennard, "Ridge regression: biased estimation for nonorthogonal problems"** (`core_method`). Related Work ("Statistical prediction with cheap features") and the Method's ridge estimator are uncited. One classic reference is enough because the paper claims no novelty for the model class. It has priority low.

## Deliberately excluded
- Cover times of random regular or Erdős–Rényi graphs, and learned graph-property prediction. The gap artifact skips these because they would reshape the related-work story rather than fill a thin spot.
- Re-retrieval of the Feige and Kiwi references.
- Quantitative claims, the evaluation protocol and the closed-form cover times. These are grounded in the run's data files and scripts, not in literature.
