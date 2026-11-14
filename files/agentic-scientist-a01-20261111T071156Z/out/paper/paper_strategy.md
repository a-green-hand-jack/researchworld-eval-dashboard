# Paper strategy (paper_standalone, ICLR 2026, double-blind)

**Provisional title:** Verified Minimal-Investment Planning for Leaderboard Rank Targeting under Multiple Aggregation Rules

## Central question
Under a declared per-task score-gain investment model, can a plan-verified planner find investments that make a target model strictly first on public multi-task leaderboards at a cost matching an evaluator-owned reference solver, across several aggregation rules, and how does it compare with naive baselines?

## Central thesis
The sealed final evaluation (Open LLM Leaderboard snapshots, seeds 9001/9002) is **qualified** (status completed, correct = true). Main efficiency relative to the reference solver is 1.0032 vs 0.8166 for the better naive baseline; control efficiency 1.0002; plan validity 1.0. The claim is narrow and conditional on the investment model: planner cost-efficiency, not real training effects, not generalization to other boards, and not a ranking of aggregation rules.

## Why this framing
- Grounded artifacts hold final metrics, 2 final seeds, and 3 scored search attempts on HELM MMLU v1.13.0 (0 unscored). No `downstream_study` block exists.
- **No per-rule or per-target cost data are retained.** The brief's question (how required investment varies with rule) therefore stays a motivating hypothesis, explicitly untested here. Missing diagnostics are unknown, not negative.
- Efficiency > 1 means verified plans were on average marginally cheaper than the reference (per-episode cap 2). Neither the reference nor the planner is claimed optimal.
- Prior paper: none (not edit mode); status "rejected" is vacuous, the draft is fresh.

## Method groups
1. Proposed: verified minimal-investment planner (frozen search winner: exact solvers for mean/median/maximin/plurality; verified heuristics/MILP level selection for trimmed/Borda/Copeland/z-score; boundary polishing; fallback).
2. Baseline: naive uniform-gain and greedy marginal-cost (better per case); only final main metric retained (0.8166).
3. Supporting: reference solver defining the efficiency scale.
4. Ablation/control: permuted-input and shuffled-null controls (final 1.0002; search 0.9967).
5. Ablation: three search-stage variants on HELM (main efficiency 1.0031 / 1.0031 / 1.0051; combined 1.00183 / 1.00183 / 1.00339). MILP layer: no measured difference; polishing: +0.0016 combined, 2 seeds, no significance claim.

## Results focus
Final comparison with per-seed values; search-stage component comparison kept separate; descriptive search-to-final observation (1.0051 vs 1.0032, different data); explicit scope statement on what is not measured. Only uncertainty available: two seeds.

## Figures (single-column template, text width ≈ 5.5 in)
1. `overview_schematic` (required, full width, page 1-2, generate-concept-figure): matrix → investment model → rules → planner → verifier → efficiency vs reference.
2. `final_efficiency_comparison` (required, matplotlib, full width at 0.8): planner vs baseline vs reference line; control and validity; ≤2 panels, ≤3 categories.
3. `search_variant_comparison` (optional, matplotlib, 0.8 width): zoomed bars or a table for the three variants.
PDF + 300 DPI PNG exported from source; LaTeX references PDF.

## Page budget
Fill 8-9 pages with problem formalization and investment-model justification, rule set (conceptual sensitivity marked as not measured), planner/verification design, evaluation protocol and qualification rule, results, and a candid limitations section (no spillover, uniform costs, field K, cap policy, 2 seeds, unverified candidate diagnostics, no per-rule evidence). If content is thin, shorten claims; no filler.

## Supplementary plan
(1) Investment model, field, targets, rule definitions; (2) efficiency metric, evaluator protocol, full metric/per-seed tables; (3) planner components and verification procedure; (4) data provenance, snapshot SHAs, seeds, runtime, license caveats, LLM usage.

## Warnings for writer
- `references.bib` has only three on-topic entries (Dey 2014, Yang 2014, Obraztsova 2011); the rest are off-topic robust-statistics items. Starter literature is absent from the bib: cite only after verified addition.
- Avoid chronology headings, pipeline-native labels (`combined_score`, "correctness rate", "eligible"), and any state-of-the-art, optimality or significance claims.
- Anonymize; include LLM Usage section.

## Forbidden headings/phrases
Experiment 1/2, Search Progression, Milestones, First Valid Result, Campaign Phases, Iteration History; "correctness rate", "correct and eligible", "combined_score", "rubric", "state of the art", "optimal planner".
