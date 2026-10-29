# Post-Draft Reference Query Plan

**Status:** ready

**Central topic:** This is citation repair for an existing draft, an empirical study that predicts the expected cover time of simple random walks on small connected graphs (5 ≤ n ≤ 30) from cheap graph statistics and compares the predictor with classical cover-time bounds. The plan fills only the two gaps listed in `draft_reference_gaps.md`/`.json`. It is not a literature refresh.

## Inputs used
- **`draft_reference_gaps.md` and `draft_reference_gaps.json`:** the primary driver. They define two rewrite targets: `related-work-comparators` (high priority) and `positioning-family-asymptotics` (medium priority).
- **`paper.tex`:** used to confirm the anchors.
  - The Matthews method is described in Background (line 73), Compared predictors (line 118), Table 2 and the "more demanding comparison" paragraph, with no citation.
  - Feige's upper bound is attributed to `Feige1995ATL` at lines 46, 70 and 252, and it has no citation at line 117.
  - The "asymptotics for specific families" sentence (line 76) has no citation.
  - The Discussion makes uncited regime claims about random 3-regular, Erdős–Rényi and grid graphs (lines 252 and 255).
- **`references.bib` and `references_provenance.json`:** the bibliography holds five sources (Aleliunas 1979, Chandra 1989, the Lovász survey twice, and Feige's *lower*-bound paper). The first-pass queries for Feige's upper bound hit HTTP 429, and the Matthews query returned zero candidates. That explains the comparator gap. The new queries use exact titles so they don't match the papers already in the bib again.
- **`global_memory_summary.md`:** qualitative context only. The physics-mixture variant in memory was never executed, so it gets no queries.

## Queries (6)

### Target 1: comparator provenance (high)
1. **`Feige A tight upper bound on the cover time for random walks on graphs`** (`baseline_comparator`)
   - (4/27)n³ is the cubic term of the primary best-bound comparator, but it is cited to Feige's lower-bound paper in the Introduction, Background, Design rationale and Discussion.
   - The exact title separates the upper-bound paper from `Feige1995ATL`.
2. **`Matthews Covering problems for Markov chains Annals of Probability`** (`baseline_comparator`)
   - The Matthews-type reference (max hitting time × H_{n−1}) is a row in Table 2 with error 0.605, and the text discusses it. It is never cited.
   - The query uses the exact title plus venue because the first-pass query found nothing.
3. **`Levin Peres Wilmer Markov Chains and Mixing Times cover time Matthews method`** (`core_method`)
   - This is the optional textbook anchor from the gap memo, covering the Matthews method and the hitting-time computation.
   - It is also a fallback if the 1988 article is not indexed. Keep at most one textbook citation.

### Target 2: family-specific asymptotics (medium)
4. **`Cooper Frieze The cover time of random regular graphs`** (`benchmark_context`)
   - This grounds the "asymptotics for specific families" sentence in Positioning.
   - It also supports the Discussion's claim that random 3-regular graphs lie in the near-n ln n regime, where gains over the bounds are largest.
5. **`Cooper Frieze The cover time of sparse random graphs`** (`benchmark_context`)
   - The draft samples Erdős–Rényi graphs from p ≈ 2 ln n / n up to 0.5, and the Discussion places them near n ln n with sparse-to-dense regime shifts.
   - The G(n, c ln n / n) cover-time asymptotic covers that density range.
6. **`Dembo Peres Rosen Zeitouni Cover times for Brownian motion and random walks in two dimensions`** (`benchmark_context`)
   - This supports the Discussion's explanation that grid cover time (asymptotically n log² n on the torus) is not a single power law in the statistics at this scale.

## Deliberately excluded
- **The research question itself:** no query phrases it (e.g. "predict cover time from graph statistics"), because such queries could surface the original paper.
- **ML/GNN graph-property prediction:** the gap memo excludes support for the "we are not aware of" sentence.
- **Sources already in the bib:** no re-searches for AKLLR 1979, Chandra et al. 1989, the Lovász survey or Feige's lower bound.
- **Generic methodology:** no regression, bootstrap or cross-validation queries. The quantitative claims are grounded in `paper_data.json` and `analysis/` via `@evidence` tags.
- **Extremal and wider cover-time topics:** no queries on lollipop hitting-time extremal results, cover-time algorithms or Gaussian free field work. The draft does not expose gaps there.
- **The physics-mixture variant:** it has no execution evidence.

## Note for the rewrite stage (no retrieval)
- **Duplicate entry:** drop the duplicate Lovász entry `Asz1993RandomWO`. Only `Lovász2001RandomWO` is cited.
- **Feige citations:** once Feige's upper-bound paper is retrieved, keep `Feige1995ATL` only for the n ln n lower bound. Cite the new key for (4/27)n³ and for the lollipop attaining it.
