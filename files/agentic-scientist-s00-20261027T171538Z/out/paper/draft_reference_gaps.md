# Draft Reference Gap Analysis

**Status:** ready

**Summary:** The draft (`paper.tex`) cites only five classical cover-time sources. Two citation gaps are worth fixing with a small, targeted retrieval pass:

1. One comparator has no citation, and another is credited to the wrong paper.
2. The positioning and discussion text refers to family-specific cover-time asymptotics without citing any.

Neither fix needs a rewrite of the paper's story.

## Current coverage

The draft's current coverage was checked against `references.bib` and `references_provenance.json`:

- **Aleliunas et al. 1979.** Cited for the 2m(n−1) bound. Adequate.
- **Chandra et al. 1989.** Cited for the commute-time and effective-resistance link. Adequate.
- **Lovász survey.** Cited for the closed forms and general background. Adequate.
- **Feige 1995, "A Tight *Lower* Bound on the Cover Time".** Cited both for the n ln n lower bound and for the (4/27)n³ *upper* bound. The upper-bound attribution is wrong; see Target 1.
- **Retrieval failures.** The original retrieval hit HTTP 429 on the queries for the 2m(n−1) bound and Feige's upper bound. The query for the Matthews bound returned no candidates. This explains the gaps below.

All quantitative claims are grounded in `paper_data.json` and `analysis/` through `@evidence` tags. None of them needs a literature citation.

## Rewrite targets

### 1. `related-work-comparators`: Background and Related Work (also Introduction, Method §Compared predictors, Discussion). Priority **high**. Intent: comparator.

**Anchors:**
- "Matthews' method bounds the cover time by the maximum hitting time times $H_{n-1}$."
- "Feige's upper bound $\tfrac{4}{27}n^3+o(n^3)$ is the exact worst case…"

**Why this is high priority:**
- **Matthews has no citation.** The Matthews-type reference is a row in the main results table (Table 2, error 0.605), and the text discusses it as "a more demanding comparison". It is never cited, either in Background or in the Compared predictors list.
- **The cubic bound is credited to the wrong paper.** The best bound min{2m(n−1), (4/27)n³} is the primary comparator. Its cubic term is credited to Feige1995ATL, which is the lower-bound paper. The upper bound comes from Feige's separate tight-upper-bound paper. The same misattribution recurs in the Introduction, the Design rationale and the Discussion, where the lollipop attains (4/27)n³.
- **Reviewers will check.** Reviewers at a venue that rewards honest baselines will check where each comparator comes from.

**Search topics:**
- Matthews, "Covering problems for Markov chains"
- Feige, "A tight upper bound on the cover time for random walks on graphs"
- Optional textbook anchor for the Matthews method and hitting-time computation: Levin–Peres–Wilmer, *Markov Chains and Mixing Times*

### 2. `positioning-family-asymptotics`: Background and Related Work (Positioning), supporting the Discussion. Priority **medium**. Intent: benchmark_context.

**Anchor:** "it derives bounds that hold for all graphs, or asymptotics for specific families"

**Why it matters:**
- **The Positioning paragraph leaves a gap.** It points to family-specific asymptotic work but cites none of it.
- **The Discussion depends on that work without citing it:**
  - It says random 3-regular and dense Erdős–Rényi graphs lie in the near-n ln n regime, which is where the gains are largest.
  - It suggests that grid cover times are not a single power law at this scale, which is offered as the reason grids have high error.
- **One to three citations would close the gap.** Citations for random-regular, random-graph and 2D-torus cover-time asymptotics would ground both points and connect the chosen test families to known results. The narrative stays unchanged.

**Search topics:**
- Cooper–Frieze, cover time of random regular graphs
- Cooper–Frieze, cover time of sparse random graphs (Erdős–Rényi)
- Dembo–Peres–Rosen–Zeitouni, cover times for random walks in two dimensions (torus)

## Deliberately not targeted

- **Quantitative results** (Tables 2–3, per-family numbers, controls). These are grounded in evaluator output.
- **Simulator closed forms** (C₁₂, K₁₀, P₁₀). These are already covered by the Lovász survey.
- **The "we are not aware of" positioning sentence.** No search on ML or GNN prediction of graph properties is requested. The run used neither. The reference plan also forbids queries phrased as the research question, because they could surface the original paper. Adding that literature would mean reshaping the paper's framing.
- **The unevaluated physics-mixture variant.** There is no execution evidence for it, so no literature is needed.

## Non-retrieval hygiene note (for the later rewrite stage)

`references.bib` lists the Lovász survey twice: `Asz1993RandomWO` (with a garbled author name) and `Lovász2001RandomWO`. Only the 2001 key is cited in the draft. The duplicate needs no retrieval, but the later rewrite stage should drop it.
