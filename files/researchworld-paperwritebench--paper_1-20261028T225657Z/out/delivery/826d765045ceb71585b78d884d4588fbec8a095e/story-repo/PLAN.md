# Study plan: VL-Rethinker write-up

Objective: `story-repo`#1. The task asks for a complete, accurate paper in `template.tex`: NeurIPS-2025 preprint style, ~11 pages. It must cite only keys from the unchanged `references.bib` and report results only from `tables/` and `figures/`, with `code/` as the method reference.
This plan says which questions the paper answers, what evidence answers each, and who delivers what. It does not fix any wording or conclusion.

## 1. Questions the paper must answer, and the evidence for each

| # | Question / claim | Evidence (frozen input) | What it shows, and its limits |
|---|---|---|---|
| Q1 | Does vanilla GRPO lose its learning signal as training goes on ("vanishing advantages")? | `figures/vanishing_adv.jpg` | Over 16 logged points (x16 steps), the share of queries with non-zero advantage ("effective queries") falls from about 0.41 to about 0.20. The share where all responses are correct rises from about 0.19 to about 0.47. The all-incorrect share stays near 0.31–0.34. Qualitative trend from one run; no error bars. |
| Q2 | Does SSR change the advantage distribution? | `figures/adv_histogram.jpg` | GRPO has about 0.37 of its mass in the bin at 0. GRPO-Filter removes zero advantages but is skewed to small negative values. GRPO-SSR is bimodal, with mass away from 0. **The supplied caption ("training dynamics...") does not describe this panel:** it is an advantage histogram. |
| Q3 | Does SSR make RL training more stable and effective? | `figures/ssr_eval_curve.jpg`; `tables/table_im.tex` rows 2–4 | Validation reward: SSR reaches about 0.455; Filter about 0.436 (run logged only to about 23 x16 steps); GRPO peaks about 0.429 near step 11, then degrades to about 0.40. On benchmarks without Forced Rethinking, MathVision goes SSR 29.8 > Filter 28.5 > GRPO 26.0. MathVerse is **not** monotonic (GRPO 51.4 > Filter 50.0). Report that. |
| Q4 | Does Forced Rethinking add to SSR? | `table_im.tex` rows 1–2; `figures/foret_ablation.jpg` | Full vs. w/o FR: MathVision 32.3/29.8, MathVista 74.9/72.4, MathVerse 54.2/53.2, MMMU-Pro 41.7/40.9, EMMA 29.7/29.5. |
| Q5 | Does the trained model rethink *selectively*, and does it help more than forcing rethinking at test time? | `figures/foret_ablation.jpg` | Base VL-Reasoner-7B (SSR, no FR) scores 29.75/72.35/53.13/40.94. With rethinking forced at test time, the relative gain is +0.5–2.5%. The "bound" is +3.8–13.2%. VL-Rethinker-7B gains +1.8–8.5%. Its rethinking ratio is about 36/24/78/18% on MathVision/MathVista/MathVerse/MMMU-Pro. The rethinking ratio does **not** track the gain (MathVerse: highest ratio, smallest gain), so claims about "selectivity" must stay within what these four points show. "bound" must be defined from the code/context, not guessed. |
| Q6 | What does a rethinking trajectory look like, and which triggers appear? | `figures/rethinking.jpg` | Shows one qualitative example (a hallucination, then a self-correction after "Wait, there might be a mistake") and a word cloud of rethinking phrases. **The supplied caption ("Illustration of the Vanishing Advantages problem") is wrong for this image.** |
| Q7 | 7B: how does it compare with general VLMs and VL reasoning models? | `tables/table_le.tex` | It is best in every column. Its margin over the best *listed* model is MathVista +1.9 (MM-Eureka-7B-Qwen 73.0), MathVerse +3.9 (MM-Eureka 50.3), MathVision +2.4, MMMU-Pro +4.4, MMMU +0.7 (InternVL2.5-8B 56.0), EMMA +3.1 and MEGA +2.2. **The supplied Δ row (+4.7/+6.3) is against OpenVLThinker, not the best prior model** (found by internal-review-repo and figtab-repo). The overview's "surpassing by 2–6 points" does not hold for all columns. Overview's 7B numbers 74.9/54.2/32.3, 41.7 match. |
| Q8 | 72B: open-source SoTA, and its place relative to proprietary models? | `tables/table_rr.tex`, `figures/teaser-2.jpg` | Against the best listed open model it is +5.6/+6.3/+6.5 (MathVision, Qwen2.5-VL-32B 38.4; the supplied Δ says +6.8)/+3.7/−1.5 (MMMU, QvQ-72B 70.3; the supplied Δ says −1.4)/+4.4/+2.3. It beats o1 on MathVista (80.4 vs 73.9) and MathVerse (63.5 vs 57.0), and trails o1 on MathVision, MMMU-Pro, MMMU, EMMA and MEGA. **The table's bold marks 72B as best even where o1 is higher**, so the caption must say "best among open-source" or the bolding must change (AGENTS.md: bold the best among compared methods). The table also has VL-Rethinker-32B (MEGA 19.9; Qwen2.5-VL-32B is 13.3): report it, but do not explain it beyond the data. |
| Q9 | Does the training data mix matter? | `table_im.tex` rows 5–6 | Removing text data (16K→13K) and science+text data (→11K) lowers every benchmark. Whether these rows include FR is ambiguous in the table; state only what the table states. |

Consistency points that the analysis and report owners must settle against the inputs, not the overview:
- **Data size.** The overview says ~38.9K curated queries. The code README calls the pool ViRL39K, "with model-capability annotations for data selection". The ablation table gives 16K for the 7B run. The paper should present 38.9K as the curated pool and 16K as the 7B training set, unless the code says otherwise. The 72B training set size is not given in any supplied input; do not invent one.
- **Ablation chain.** The overview's "32.3→29.8→26.0" skips the Filter row (28.5); report all rows.
- **Method facts from the code** (answered in idea-repo#2; source: `idea-repo` Brief §9, `brief.md` at ececbc7/a7941c6):
  - **SSR:** the buffer keeps non-zero-advantage items (half the rollout batch). Batches mix current non-zero items (plus at most 10% all-correct items) with the buffer, sampled **∝|A|, i.e. α=1**. The paper may present the general |A|^α form, but must state that α=1 was used.
  - **Filter:** drops zero-advantage queries and refills uniformly.
  - **Forced Rethinking:** 4 trigger types; q≈0.65 of eligible rollouts; 50% truncated before the answer. Only correct rethinks are kept (≤2 per query) and replace the rollout. Auxiliary NLL loss, coefficient 0.05.
  - **Hyperparameters:** script defaults only: n=8, batch 512, LR 1e-6, T=1.0, KL 0, clip 0.2/0.35, max output 2048. Label them as such.
  - **Base models:** Qwen2.5-VL-7B/72B-Instruct (README). The 72B training-set size is not given.
- **`foret_ablation` terms:**
  - "forced" means a trigger appended at test time to VL-Reasoner-7B (the `table_im` row 2 model).
  - "bound" is an oracle: a rethink counts only when it is correct.
  - "rethinking ratio" is not computed under that name in the code; the closest is the share of responses that contain a rethinking phrase.
  - So Q5 supports "rethinking frequency varies across benchmarks (≈18–78%)", **not** an efficiency or token-saving claim. The overview's "improving both accuracy and efficiency" has no supplied efficiency measurement and must not be asserted.
- **Citations:** Brief §10 maps the keys. There are no keys for Gemini-2.0-Flash, InternVL2, Kimi-VL, Llama4-Scout or QvQ, or for an original GRPO paper (use `deepseek-r1`). `curriculum` is an ad-bidding paper, so do not cite it for curriculum learning. Table rows without keys stay uncited; no new entries.

## 2. Paper structure (≈11 pp. double column, NeurIPS preprint style; no Limitations/Future Work/Acknowledgements)

1. Abstract: one paragraph, no equations.
2. Introduction, with the teaser (`teaser-2`) on p.1–2 and the method overview (`overview-2`) on p.2 (AGENTS.md); contributions list.
3. Preliminaries: GRPO objective, group-normalised advantage; why identical rewards in a group give zero advantage.
4. Method: 4.1 vanishing advantages (Q1, `vanishing_adv`); 4.2 SSR (buffer of non-zero-advantage samples, |A|^α prioritised replay, compared with Filter; algorithm box); 4.3 Forced Rethinking (triggers, fraction q, keep successful rethinks, aux SFT loss; `rethinking.jpg` example). No results in Method.
5. Experiments: setup (data, base models Qwen2.5-VL-7B/32B/72B, benchmarks, baselines, evaluation protocol, † reproduced numbers); main results at 72B/32B (Q8) and 7B (Q7).
6. Analysis: SSR ablation and dynamics (Q2, Q3: `adv_histogram` + `ssr_eval_curve`, can share one figure), Forced Rethinking (Q4, Q5), data mix (Q9).
7. Related work: multimodal reasoning and slow thinking, RL for LLM reasoning (GRPO/PPO/R1-style), VLM RL (R1-VL, R1-OneVision, OpenVLThinker, MM-Eureka), replay/prioritised experience. Cite only keys found in `references.bib`.
8. Conclusion.

All 7 figures and 3 tables are to be used. `\graphicspath{{figures/}}` must be present.

## 3. Division of work (who delivers what)

- `idea-repo` (context): the brief. Code-derived method facts (SSR formula and α, Filter vs SSR in `replay_buffer.py`, triggers and q, aux SFT loss, the definition of "bound" and of "rethinking ratio", hyperparameters). The bib keys available for each related-work topic and for each baseline/benchmark.
- `figtab-repo` (presentation): the delivered `figures/` and `tables/`, with captions that state what each actually shows (correct the two mismatched captions; fix or caption the bolding in the 72B table), and the layout of combined figures.
- `paper-repo` (analysis, venue, report): verifies every number and claim against the inputs (the Q1–Q9 limits above), and ships `template.tex` (which `\input`s or embeds the tables and includes the figures), the unchanged `references.bib`, and whatever style file the venue needs in order to compile.
- `internal-review-repo` (review): judges the versions against the objective.
- `story-repo` (plan, this file): proposes `.forgejo/CODEOWNERS` in `paper-repo` and revises it as the split settles; checks each version against this plan.
