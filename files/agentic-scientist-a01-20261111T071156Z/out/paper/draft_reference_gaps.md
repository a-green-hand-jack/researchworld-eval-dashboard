# Draft reference gap analysis

**Status:** ready. The draft is mostly well-supported. Quantitative claims are grounded in `paper_data.json` and are not flagged. Three targeted retrieval needs remain.

## Missing literatures
- Priced, swap and weighted bribery under Copeland, Borda and plurality.
- Open LLM Leaderboard (v2) documentation.
- Goodhart's law and metric gaming in ML evaluation.

## Rewrite targets

### 1. `related-work-social-choice-bribery` (related work, high, comparator)
- **Anchor:** "Our problem is a continuous variant: the 'voters' are tasks, the intervention changes one candidate's scores..."
- **Why:** The paper positions itself against manipulation, bribery and margin-of-victory problems, but the cited works are generic or about election attacks. It cites nothing on cost-priced or swap bribery, or on bribery and control under Copeland, Borda and plurality. Those are the closest comparators for the rules the planner handles heuristically.
- **Search topics:** priced and swap bribery; Copeland, Borda and plurality bribery and control; bribery under score-based voting with per-voter costs.

### 2. `heldout-data-open-llm-leaderboard` (related work, high, benchmark_context)
- **Anchor:** "The Open LLM Leaderboard aggregates six benchmarks"
- **Why:** The whole held-out evaluation uses Open LLM Leaderboard snapshots. The draft cites only the component benchmarks, not the leaderboard itself.
- **Search topics:** Open LLM Leaderboard v2 description; evaluation-harness documentation.

### 3. `intro-incentive-gaming-claim` (introduction, medium, background)
- **Anchor:** "Rankings influence adoption, publication and funding, so developers have an incentive to act on them"
- **Why:** This is the premise of the motivating question and it has no support. One or two Goodhart or leaderboard-incentive references would be enough.
- **Search topics:** Goodhart's law and metric gaming in ML benchmarks; benchmark culture and leaderboard incentives.

## Deliberately not flagged
- Software citations (NumPy, SciPy, MILP solver). These are low value for the narrative.
- Planner heuristics such as bisection and greedy search. They are standard and described in the paper itself.
- The contamination and leaderboard-gaming paragraph, which is already densely cited.
