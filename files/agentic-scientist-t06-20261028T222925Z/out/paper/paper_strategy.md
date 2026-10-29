# Paper Strategy (paper_standalone / write-paper-standalone, ICLR 2026)

**Status:** ready

**Provisional title:** *How Many Comparisons Change the Leader? Refit-Verified Influence Perturbations of Bradley-Terry Leaderboards Across Evaluation Designs*

## 1. Grounded situation (what the artifacts actually say)
- **Final evaluation:** status `completed`, outcome `qualified`, correct. All integrity checks passed: replay match 1.0, failed-episode fraction 0.0, synthetic and permutation control scores 0.0. Sources: `final.qualification.*`, `final.metric.*`.
- **Evaluated configuration:** the selected configuration is the baseline (`study.selection_kind = baseline`, `search_score_delta = 0.0`, `investigation_outcome = completed_no_winner`). Its code is identical to the baseline: an AMIP-style one-step influence ordering of comparison rows by their effect on the leader–challenger (or top-k boundary) margin, followed by exponential and binary prefix search verified by exact ridge-BT refits.
- **Pre-declared superiority test vs AMIP:** *not supported* (`claim_supported = 0`; mean log2 ratio vs AMIP 0.0, CI [0.0, 0.0]). This holds by construction, because the instrument *is* the AMIP ordering.
- **Refined variants:** 3 attempts (category-count relinearized search with prune and swap). All 3 are **unscored** (`study.attempts.unscored = 3`) because of execution failures. Their effect is unknown, not negative.
- **Verified sizes** (identical across seeds 101/102/103; `final.evidence.episodes`):

| Source (design) | n (derived) | drop top-1 | flip top-1 | drop top-k |
|---|---|---|---|---|
| Arena-140k (crowd votes) | 135,622 | 62 (0.046%) | 46 (0.034%) | top-5: 21 |
| MT-Bench human (experts) | 3,355 | 92 (2.74%) | 46 (1.37%) | top-3: 229 |
| MT-Bench GPT-4 (LLM judge) | 2,400 | 143 (5.96%) | 61 (2.54%) | top-3: 150 |
| NBA 2014 (sports) | 1,319 | 7 | 4 | top-5: 1 |
| NBA 2015 (sports) | 1,311 | 16 | 8 | top-5: 1 |

  NBA season-mean fractions are 0.876% (drop) and 0.457% (flip). Each n is derived exactly as k divided by the reported fraction.
- **Comparators:** mean clipped log2(k_random/k) = 3.975, CI [3.934, 4.0], i.e. about 16×, censored at the clip of 4. The direct leader–challenger heuristic was matched or beaten in all Arena, GPT-4 and NBA cases (family scores 0). It was marginally better in at least one MT-Bench-human case (family log2 score −0.0053).

## 2. Central question
How small a verified perturbation of comparison data suffices to change the top-1 or top-k of a ridge Bradley–Terry leaderboard? Perturbations are dropping or flipping individual comparisons. And how does that size differ across crowdsourced-vote, expert-human, LLM-judge and sports designs?

## 3. Central thesis
A refit-verified, influence-ordered search changes the leader in every design with only tens of comparisons. Those sets are about 16× smaller than random perturbations.

Which design looks "most fragile" depends on the **scale** and on the **target**:
- **Scale.** As a fraction of the data, Arena is the most fragile (0.046%) and the GPT-4 judge the least (6.0%). As an absolute count, NBA is the most fragile (7 and 16 games).
- **Target.** Top-k set changes can cost far less (a single NBA game, in both seasons) or more (MT-Bench top-3) than top-1 changes.

All sizes are verified upper bounds. Cross-design differences are descriptive, not causal.

## 4. Why this framing (alternatives compared)
- **Methods-superiority paper (rejected).** No configuration beats the AMIP ordering. The pre-declared test is unsupported and the refined variants are unscored. Claiming an improvement would be fabricated.
- **Negative-results paper about the failed search refinements (rejected).** There is no measured evidence about them: they are unscored, not losses. That paper would have no data.
- **Measurement/methodology paper (chosen).** It uses all grounded final evidence: 15 real cases, 2 controls, 2 comparators and determinism. It directly answers the task's open question: sensitivity, how to scale perturbation size, and whether sensitivity differs across designs. It also carries an honest, interesting conceptual finding: conclusions depend on scale and target. The qualified evaluation becomes validation of the instrument, and the unsupported superiority test is disclosed explicitly.
- **Edit mode:** not applicable. There is no prior manuscript or staged inputs, so `prior_paper_story_status = rejected` simply records that there is no prior story to preserve.

## 5. Method groups
1. **Refit-verified influence-ordered perturbation search** (the studied instrument). Presented as adapting the drop-data robustness idea (Broderick et al.) to leaderboard targets and to flip perturbations, not as a new algorithm that beats AMIP.
2. **Random comparator** (baseline): a noise-like reference.
3. **Direct leader–challenger heuristic** (baseline): the "obvious attack" reference, grounded at family level only.
4. **Validity controls** (supporting): synthetic planted exact minimum, row-permutation invariance, seed replay.

Refined variants appear only in an appendix paragraph, as not evaluated.

## 6. Results to emphasize (thesis-first order)
1. Instrument validity (Table 2): controls, determinism, about 16× vs random, and the AMIP-equivalence and unsupported superiority test.
2. Main cross-design result (Fig. 2): count vs fraction panels across 5 sources × 3 targets.
3. Drop vs flip (flip always needs fewer rows), and top-1 vs top-k (NBA top-5 = 1 game; Arena top-5 = 21 vs 62; MT-Bench top-3 is costlier).
4. Controlled contrasts (Fig. 3): MT-Bench human vs GPT-4 judge. The judge leader needs more drops for top-1 (143 vs 92), but fewer for top-3 (150 vs 229). The figure also shows the ordering reversal between the count and fraction scales.

## 7. Figures and layout
The template is ICLR single-column with a 5.5 in text width (`paper.sty`). Every figure therefore spans the text width, so readability is set by panel count and label size, not by shrinking.

| id | type | generator | span | budget | rationale |
|---|---|---|---|---|---|
| protocol_overview | diagram | generate-concept-figure | full width (0.95) | 1 panel, ≤6 stages | Wide ~3:1 flow: designs → BT fit → influence order → refit-verified prefix → k (count, fraction). A side band shows comparators and controls. Place on page 1–2. |
| fragility_by_design_two_scales | grouped dot/bar, log axes | matplotlib | full width (1.0) | 2 panels × 5 categories × 3 series | About 2.6 in per panel keeps 8 pt labels. Annotate integer k. Use the same target colours in both panels. |
| controlled_contrasts | dumbbell + slope | matplotlib | full width (0.9) | 2 panels, ≤5 categories, ≤2 series | Compact. Direct labels replace legends. |

Tables: (1) designs and cases; (2) instrument validation and comparators; Appendix: all per-case, per-seed sizes.

Export each plot as vector PDF (referenced in LaTeX) plus a 300-DPI PNG. Any raster-only output must be at least 2400 px wide. Never upscale.

## 8. Page budget (8–9 body pages; page 8 must be ≥75% full)
| Section | Pages |
|---|---|
| Introduction (+ Fig. 1) | ~1.4 |
| Related work | ~0.7 |
| Problem setup (estimator, targets, perturbations, two size scales and why) | ~0.9 |
| Method (mechanism of influence ordering; exact-refit verification; upper-bound semantics; comparators; controls) | ~1.2 |
| Setup (Table 1) | ~0.6 |
| Results (Table 2, Figs. 2–3) | ~2.4 |
| Discussion and limitations | ~0.9 |
| Conclusion | ~0.2 |

Spend any spare space on mechanism and limitations, not padding.

## 9. Supplementary plan
The appendix covers:
- per-case and per-seed verified sizes and durations;
- the estimator and case construction, including the derivation of n;
- comparator and control definitions and family-level scores;
- the pre-declared superiority test and the unevaluated refinements, with qualification status;
- the reproducibility record (pinned data commits and checksums, numpy 2.2.6 / scipy 1.15.3, seeds, commands, figure-to-script map);
- the mandatory **LLM Usage** section.

None of this is needed to support the thesis.

## 10. Limitations the paper must state
- Sizes are upper bounds, not certified minima. Exactness is shown only on the synthetic control.
- There is no data-resampling uncertainty on k. Seed agreement reflects determinism only.
- The random-ratio summary is clipped at log2 = 4, so it is censored.
- Results hold for one estimator only: ridge 0.1, ties counted as half, players with fewer than 50 comparisons removed.
- Cross-design differences are confounded with n, participant count, graph structure, tie rate and the leader's margin.
- Coverage is one snapshot per source and two NBA seasons.
- The heuristic comparator is known only at family level.
- Refined search configurations were not evaluated.

## 11. Forbidden headings and phrases
- **Headings:** chronology or progression headings ("Search Progress", "Iteration/Cycle k", "Experiment A/B", "First Successful Run", "Milestones", "Run History", "Improvement Trajectory").
- **Pipeline terms:** correctness rate, correct and eligible, eligible, combined_score, rubric, worker ids, program_N, harness, sandbox.
- **Overclaims:** "outperforms AMIP", "state of the art", "minimum number of comparisons is" (for real data), "LLM judges are more robust than humans", "crowdsourced leaderboards are unreliable".

## 12. Citation guidance
`references.bib` is mostly off-topic noise. Use only `Broderick2020AnAF`, `Giordano2019AHS` and `Monari2000WithdrawingAE`, plus optionally `Alaa2020DiscriminativeJQ`.

The task's starter literature (Bradley–Terry; Chatbot Arena; MT-Bench / LLM-as-a-judge; Koh & Liang; vote rigging; Leaderboard Illusion; the Arena preference-dropping paper) is essential context. Add it only through the grounded reference mechanism, and describe it only at the level of the brief.

Position the contribution as follows:
- the cross-design comparison;
- drop vs flip;
- top-1 vs top-k;
- the scale-dependence insight;
- a validated, refit-verified protocol.

Do not claim to be the first to show that Arena leaders are fragile.
