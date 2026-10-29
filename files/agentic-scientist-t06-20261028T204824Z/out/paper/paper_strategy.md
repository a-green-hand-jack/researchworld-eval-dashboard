# Paper strategy (paper_standalone, ICLR 2026, single column, 8–9 body pages)

**Status:** ready. **Provisional title:** *How Few Edits Displace the Top of a Bradley-Terry Leaderboard? A Verified First-Order Influence Attack Across Crowd, Expert, LLM-Judge and Sports Comparison Data*

## What the grounded evidence is
- Frozen selection = the original first-order influence starter (`selection_kind=baseline`, `completed_no_winner`, search delta 0.0). Three attempted variants: 3 total, 0 scored, 3 unscored. Unscored means missing evidence, not a loss.
- Sealed final evaluation: `qualified` / `completed` (`final.qualification.*`). Edit success (family-averaged) 0.606; per design: crowd 1.000, sports 0.833, expert-human 0.374, LLM-judge 0.216. Baselines (aggregate only): constant 0.071, random 0.071, win-rate heuristic 0.574. Margin versus best baseline 0 (the method is the influence baseline). Permuted-input control gap 0, valid proposal rate 1. Three seeds give identical scores.
- Top-1 displacement at the 2% budget: crowd 1/1 (drop/flip), sports 1/1, expert-human 0/1, LLM-judge 0/0.
- Search score 0.914 and final 0.606 are different scopes; never compare them.

## Central question and thesis
**Question.** How many edits (0.1–2% of rows, drop or flip) does a first-order influence search need to dethrone the rank-1 competitor of a ridge BT leaderboard, and does this differ across evaluation designs?
**Thesis.** Under exact-refit verification, one-shot first-order edit search shows strongly design-dependent rank-1 vulnerability: it displaces rank 1 in all crowd and sports cases at 2%, never for the LLM judge, and only by flipping for expert-human data. This is a bounded measurement for one attack and one target, not a general sensitivity law, and no improved search method was established.

## Framing decision
Framings considered:
1. Method-improvement (re-linearised or multi-rival search beats the starter). **Rejected**: nothing was scored.
2. Noise-versus-intent sensitivity with calibration and subsampling ablations. **Rejected**: no such experiments exist in the artifacts.
3. **Selected**: thesis-first measurement and limitations paper on cross-design heterogeneity under a verified attack. It is the only story the final evaluation supports, and it answers the task's cross-design question. It is not edit mode, so no prior manuscript was preserved or discarded.

## Method groups
- Studied method (role: proposed, but not claimed as novel): first-order influence edit search.
- Baselines: constant, random, win-rate heuristic (aggregate values only).
- Supporting: trusted refit verification, permuted-input control, valid-proposal rate.
- Optional ablation-style note: the three unscored variants, one paragraph, no comparison.

## Results focus
1. Per-design edit success and ordering crowd > sports > expert human > LLM judge.
2. Displacement rates at 2% by design × mode (a table, with 0/1 values explained).
3. Reference scale from baselines; the influence search versus the win-rate heuristic is a small gap with no uncertainty estimate, so no reliable ranking is claimed.
4. Validity checks and seed-identical outcomes. State that there is no between-seed variance and no confidence interval.
5. Within-MT-Bench contrast of human versus GPT-4 judge, with the cause explicitly untested.
6. Search and final scopes kept separate.

## Figures (all full text width, since the ICLR template is single column, about 5.5 in)
| id | type / generator | content | budgets |
|---|---|---|---|
| overview_protocol | diagram / generate-concept-figure, page 1–2 | data → BT fit → gap → drop/flip edits ≤ k → trusted refit → edit success | 1 panel |
| design_scores | bar / matplotlib (PDF + 300 DPI PNG) | (a) edit success by design; (b) family-averaged success: constant, random, win-rate, influence | 2 panels, ≤4 categories, 1 series each |

Tables: setup (designs, sources, cases), results (scores and 2%-budget displacement rates). No trajectory figures, since the thesis is not about dynamics.

## Body-page plan (8–9 pages, no padding)
About 1 page introduction with overview figure; 1 related work and BT background (only cited keys in `references.bib`); 1.5 problem formulation, attack, scoring, controls; 0.5 designs and data; 2 results; 1.5 analysis of what the evidence does and does not show (hypotheses labelled untested); 1 limitations. Detail beyond that goes to the supplement; tighten rather than pad.

## Supplementary plan
Evaluator specification and metric definitions; full metric table (all `final.metric.*`); seeded runs and evidence; search-stage context and unscored variants (`study.*`); algorithm description of the influence search from the frozen program; LLM usage statement. Nothing essential to the thesis is hidden there.

## Limits the paper must state
One attack (one-shot, first-order), one target (rank 1), a fixed evaluator BT specification; designs confounded with dataset size, competitor count and gap size; NBA is not a preference design; expert-human and LLM-judge share one source; no noise/intent attribution; no data-sampling uncertainty; candidate diagnostics unverified; failure to displace rank 1 shows only that this heuristic failed within the budget; no improvement over the baseline was established. The bib lacks several task-brief references (Arena, MT-Bench, influence functions, AMIP, vote rigging), so cite only what exists. The excluded paper must not be sought or cited.

## Avoid
Headings: experiment chronology, search campaign or history, milestones, first valid result, cycles. Phrases: correctness rate, eligible, combined_score, rubric, "outperforms", "state of the art", unqualified "flip rate", "statistically significant", any confidence-interval claim.
