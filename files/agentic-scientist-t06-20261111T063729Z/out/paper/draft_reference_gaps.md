# Draft reference gap analysis

**Status:** ready. Three targeted retrieval targets.

Coverage of Bradley–Terry theory (extensions, existence/consistency, uncertainty) is dense. The existing bibliography does not cover three areas the draft relies on or motivates itself with. The draft concedes this in its "Scope of the bibliography" paragraph and in the Extended limitations. Numeric claims are grounded in `paper_data.json` and are not targets.

## Missing literatures
- Chatbot Arena / MT-Bench pairwise LLM evaluation and the datasets used
- Influence functions and leave-one-out / Cook's-distance-style deletion diagnostics
- Manipulation and rigging of crowd-vote or pairwise-comparison rankings

## Targets

1. **arena-leaderboard-context** (Introduction, high, benchmark_context)
   - Anchor: "Leaderboards that aggregate 'which of A and B is better' judgments into Bradley–Terry (BT) ratings are used to choose models…"
   - Reason: The motivating claim about leaderboard use has no citation. The Data section uses Arena 55k/140k and MT-Bench human judgments without citing the platform or dataset papers.
   - Search topics: Chatbot Arena platform paper; MT-Bench human judgments / LLM-as-a-judge; Arena human-preference dataset.

2. **influence-deletion-method** (Problem Setup and Method, high, background)
   - Anchor: "Deleting row $i$ perturbs the stationarity condition by $-\nabla\ell_i$, so a Newton step predicts the change of the gap…"
   - Reason: The first-order influence formula with leverage correction is the core of the studied configuration and the basis of the B2 comparator. It has no citation to influence-function or case-deletion literature. Only Broderick et al. is cited.
   - Search topics: influence functions for black-box predictions; Cook's distance / case deletion in logistic regression; one-step leave-one-out approximations for M-estimators.

3. **manipulation-positioning** (Related Work, medium, positioning)
   - Anchor: "Work on adversarial manipulation of crowd-vote leaderboards, on evaluation practices of arena-style platforms, and on influence functions…"
   - Reason: The draft motivates the removal budget through deliberate action and rigging, then disclaims any positioning against that work. One or two citations would replace the disclaimer.
   - Search topics: adversarial vote manipulation of LLM arena leaderboards; robustness of pairwise-comparison rankings to corrupted comparisons.

## Not targeted
Related-work paragraphs on BT extensions, estimation and uncertainty are well supported. Adding more there would only grow the bibliography.
