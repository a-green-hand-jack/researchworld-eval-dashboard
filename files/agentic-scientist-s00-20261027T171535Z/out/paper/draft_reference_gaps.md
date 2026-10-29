# Draft reference gap analysis

**Status:** ready. The bibliography has three entries (Feige upper and lower bounds, Kiwi et al. on hyperbolic random graphs). The Feige and Kiwi citations are adequate. Three places in the draft need targeted retrieval. No retrieval was run in this stage.

## Missing literatures
- Aleliunas et al. random-walk cover time bound / universal traversal sequences
- Lovász survey on random walks on graphs
- Commute-time identity, effective resistance and Matthews-type cover time bounds
- Ridge regression (Hoerl and Kennard)

## Rewrite targets

### 1. related-work-worst-case-bounds (high, comparator)
- **Section:** Related Work (also the Introduction)
- **Anchor:** "The $2m(n-1)$ bound of Aleliunas et al. follows by summing commute times ... Lovász's survey on random walks on graphs"
- **Reason:** The 2m(n-1) bound is the headline comparator. It is attributed only by author name, with no `\cite`. The Lovász survey is also named without a citation. A reviewer would expect both to be cited directly.
- **Search topics:** Aleliunas–Karp–Lipton–Lovász–Rackoff, "Random walks, universal traversal sequences, and the complexity of maze problems"; Lovász, "Random walks on graphs: a survey".

### 2. discussion-resistance-matthews-features (medium, positioning)
- **Section:** Discussion and Limitations (the Conclusion repeats the point)
- **Anchor:** "resistance-based quantities motivated by the commute-time identity and Matthews-type bounds"
- **Reason:** The paper's main proposed next step, richer resistance-based features, rests on the commute-time identity and Matthews bounds. Neither has any support in the draft or the bibliography.
- **Search topics:** Chandra et al., electrical resistance and commute/cover times; Matthews bounds on covering times via maximum hitting time.

### 3. method-ridge-regression-background (low, background)
- **Section:** Related Work ("Statistical prediction with cheap features")
- **Anchor:** "Predicting a graph functional from low-dimensional summaries is a standard use of regression"
- **Reason:** The paper claims no novelty for the model class, so a single classic ridge reference suffices.
- **Search topics:** Hoerl and Kennard, "Ridge regression: biased estimation for nonorthogonal problems".

## Deliberately not targeted
- Quantitative claims, the evaluation protocol and the closed-form cover times are grounded in `paper_data.json` and the repository scripts.
- Broader literatures were skipped (cover times of random regular or Erdős–Rényi graphs, learned graph-property prediction). Covering them would reshape the related-work story rather than fill a thin spot.
