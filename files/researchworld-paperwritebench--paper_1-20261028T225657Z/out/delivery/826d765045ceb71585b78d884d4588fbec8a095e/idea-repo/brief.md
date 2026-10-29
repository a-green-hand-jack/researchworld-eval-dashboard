# Brief — VL-Rethinker write-up (owner: idea-repo, context)

Source of truth: `idea-repo#1` (task frozen at `/initial-state/inputs/0/INSTRUCTIONS.md`). This page states what the task asks, what the supplied material establishes, and where they disagree. All numbers below are read from the frozen inputs (file named for each); nothing here is a new measurement.

## 1. What the task asks (quoted)

- "Your goal is to write up the following idea" (VL-Rethinker research overview, `inputs/7/research_overview.md`). "Note that idea_text represents a preliminary hypothesis and may not necessarily align with the experiments that were eventually performed."
- "First, make sure to refer to the experiment data contained in table/ and figure/ folders." Also "refer to: code/ as the proposed method's code implementation".
- "Please read the current template.tex file and update it to produce a complete, coherent, and scientifically accurate paper."
- "This must be an acceptable complete LaTeX writeup, suitable for a 11-page double-column paper." (Note: template uses `neurips_2025` [preprint], which is single-column; see §6.)
- "Make sure to use the citations from the references.bib file and report results accurately based on the experimental data provided."
- "do not use the \begin{filecontents}{references.bib} environment. Instead, all citations should refer to an external file named references.bib."

### Deliverables (delivered tree paths)
- `template.tex` — the completed paper (edited in place; keep its preamble/style, `\model` macro, `unsrtnat` + `\bibliography{references}`).
- `references.bib` — must be present; **AGENTS.md: "Do not make any changes to reference.bib"** → deliver the supplied file unchanged.
- Figures/tables referenced by the paper must resolve from the delivered tree (task paths `figures/*.jpg`, `tables/*.tex`). The template has no `\graphicspath`; AGENTS.md says "Do not remove the \graphicspath directive" — none exists, so figure paths must be written to resolve (e.g. `figures/...`) and the files delivered alongside.

### Writing constraints from `AGENTS.md`/`CLAUDE.md` (identical files)
- Method paper; "scientifically accurate, objective, and truthful. Accurately report the experimental results, even if they are negative or inconclusive."
- Keep conference style; keep references.bib inclusion; no Acknowledgements; no Limitations or Future Work sections.
- Abstract: one paragraph, no formatted equations; key numbers allowed.
- Intro: context, intuition, contributions; **method overview figure on page 2**.
- Related Work: multiple citations per subsection, gap vs. this work.
- Method: reproducible detail; **no results in Method**.
- Experiments: data, setup, baselines; no hardware details; **bold the best result among compared methods** (not necessarily ours).
- Analysis: ablations, multiple perspectives, only claims supported by data.
- Compilable LaTeX; escape `%`; no duplicate labels; "Do not hallucinate new citations or any results not in the logs"; cite only keys that exist in references.bib.
- (AGENTS.md also says "Always include references within filecontents" — this **contradicts the task**, which forbids filecontents; the task wins.)

## 2. Template state (`inputs/10/template.tex`)
Empty sections: Abstract, Introduction, Preliminaries, Our Method, Experiments, Related Work, Conclusion. Defines `\model` (=VL-Rethinker), `\base` (MM-thinker, unused in data), tcolorbox styles (`questionbanner`, `promptbox`), algorithm/algpseudocode loaded, draftwatermark "AI-Generated" (keep).

## 3. The study the paper reports (from overview + code)

**Problem.** GRPO for VLMs suffers *vanishing advantages*: with binary rewards, a query whose 8 (group) rollouts are all correct or all wrong gives zero group-normalized advantage for every rollout → no gradient. As training proceeds the share of such queries grows, the effective batch shrinks, training is unstable, and long/reflective reasoning is not incentivized.

**Method (as implemented in `inputs/3/openrlhf`).**
- Base models: Qwen2.5-VL-7B/32B/72B-Instruct (`README.md`). Pipeline (Fig. overview-2): VL-Instruct →(GRPO-SSR)→ VL-Reasoner →(Forced Rethinking)→ VL-Rethinker.
- GRPO-style group advantages, no critic, rule-based binary correctness reward (answer in `\boxed{}`), `init_kl_coef 0.0`, n=8 rollouts/query, temperature 1.0 (val 0.6, top-p 0.95), actor LR `${lr}e-7` with default lr=10 → 1e-6, `normalize_reward`, asymmetric clip ε_low=0.2 / ε_high=0.35 "according to DAPO" (`models/loss.py`), training max new tokens 2048 (`max_out_tokens`), 3 episodes default (`train_vlm_multi.sh`).
- **GRPO-Filter** (baseline): drop zero-advantage queries, refill the batch by re-sampling non-zero ones uniformly (`replay_buffer.py: active_sampling`, `do_ssr=False`).
- **SSR** (`active_sampling`, `do_ssr=True`): keep a replay buffer (deque, size half the rollout batch) of non-zero-advantage experiences; build the training batch from current non-zero-advantage items (+10% all-correct "positive" items) sampled with probability ∝ |advantage|, then fill the rest from the replay buffer sampled ∝ |advantage|+1e-4. **In the code the exponent α is effectively 1** (the overview's |A|^α is the general form; no α>1 setting appears in the code). Report as "∝|A|^α (α=1 in our implementation)" or simply ∝|A| — do not invent another α.
- **Forced Rethinking** (`experience_maker.py`, `data_version` contains `force_append_wait`): after the first rollout, a random subset of responses (each skipped with p=0.35, so q≈0.65 of eligible ones; ineligible: truncated or >maxtoken−1024 tokens) gets a rethinking trigger appended and is continued. Triggers: "Wait", "Wait, does it seem right?", "Wait, let's double check", "Wait, there might be a mistake" (self-verification / questioning / correction). With prob. 0.5 the original response is first cut before its final answer (`\boxed`/"answer"/last "Wait"). Only rethought responses that end **correct** are kept, at most 2 per query; on those (positive-advantage, reward ≥0.99) an auxiliary SFT (NLL) loss is added with coefficient `aux_loss_coef` 0.05 (`models/loss.py`, `ppo_trainer.py`). Responses with >5 "wait" are marked invalid (`experience_maker.py:775`), discouraging redundant rethinking.
- Data: overview says "~38.9K curated, verifiable multimodal queries" (ViRL39K per README: 8 categories, model-capability annotations). **The 7B ablation table lists Data = 16K** (13K without text-only, 11K without science & text). So: 38.9K is the curated pool; the 7B runs use 16K. That the final 72B used a different subset is **not established** by the material.

## 4. Results the paper must report (exact, from tables/figures)

### Table `tables/table_rr.tex` (72B/32B vs proprietary & open-source; label `table:main_results`)
VL-Rethinker-72B: MathVista 80.4, MathVerse 63.5, MathVision 44.9, MMMU-Pro 55.9, MMMU 68.8, EMMA 38.5, MEGA 51.3. VL-Rethinker-32B: 78.8/56.9/40.5/50.6/65.6/37.9/19.9. Δ row (vs open SoTA): +5.6/+6.3/+6.8/+3.7/−1.4/+4.4/+2.3.
Proprietary: o1 73.9/57.0/60.3/62.4/78.2/45.7/56.2 — o1 is higher than 72B on everything except MathVista and MathVerse; GPT-4o, Claude-3.5-Sonnet, Gemini-2.0-Flash are below the 72B on all five reasoning benchmarks of the teaser (Fig. teaser-2 restates these numbers).

### Table `tables/table_le.tex` (7B; label `table:7b_results`)
VL-Rethinker-7B: 74.9/54.2/32.3/41.7/56.7/29.7/37.2; Δ vs prev SoTA row: +4.7/+6.3/+2.4/+4.4/+0.7/+3.1/+2.2.

### Table `tables/table_im.tex` (7B ablations; label `table:ablation_results`)
| Variant | Algo | Data | MathVision | MathVista | MathVerse | MMMU-Pro | EMMA |
|---|---|---|---|---|---|---|---|
| VL-Rethinker-7B | SSR | 16K | 32.3 | 74.9 | 54.2 | 41.7 | 29.7 |
| w/o Forced Rethinking | SSR | 16K | 29.8 | 72.4 | 53.2 | 40.9 | 29.5 |
| no SSR | Filter | 16K | 28.5 | 72.0 | 50.0 | 40.0 | 26.9 |
| no SSR & Filter | GRPO | 16K | 26.0 | 70.9 | 51.4 | 38.8 | 26.2 |
| no Text | SSR | 13K | 29.1 | 73.5 | 53.5 | 41.1 | 28.7 |
| no Science & Text | SSR | 11K | 28.0 | 71.6 | 50.3 | 39.7 | 28.0 |
Readings: Forced Rethinking adds +2.5 MathVision, +2.5 MathVista, +1.0 MathVerse, +0.8 MMMU-Pro, +0.2 EMMA over SSR-only. SSR vs Filter (both w/o FR): +1.3/+0.4/+3.2/+0.9/+2.6. Filter vs GRPO: +2.5/+1.1/**−1.4 (MathVerse: Filter < GRPO)**/+1.2/+0.7. The ablation rows (other than the first) are trained **without** Forced Rethinking — inferred from the row structure ("- no SSR" indented under "w/o Forced-Rethinking"); state it as such.

### Figures
- `figures/vanishing_adv.jpg` (caption: "Illustration of the Vanishing Advantages problem"): ratio of queries vs steps (×16): effective (non-zero-adv) queries fall ≈0.41→≈0.20 over 15×16 steps while all-correct rises ≈0.19→≈0.47; all-incorrect ≈0.40→≈0.33. Which model/scale is **not stated**.
- `figures/rethinking.jpg` (same caption in summary, but content is "An Example of Forced Rethinking" + word cloud of rethinking phrases: "double check", "mistake", "recheck", "might", "seem right", …). The example shows self-correction after a trigger; note its final answer still says KL needs more information. Caption should describe the actual content, not "vanishing advantages".
- `figures/adv_histogram.jpg`: advantage distributions of GRPO (peak ≈0.37 mass at 0), GRPO-Filter (zero removed, skewed negative, mass near small |A|), GRPO-SSR (bimodal, mass shifted toward |A| ≈0.3–0.9).
- `figures/ssr_eval_curve.jpg`: validation reward vs steps(×16): SSR rises to ≈0.455 (≈step 26) and stays ≈0.45; Filter ≈0.435 at its last point (step 23); GRPO peaks ≈0.429 (step 11) then declines to ≈0.398 (step 29). Both captions in the summary are "Comparisons of training dynamics of GRPO, GRPO-Filter and GRPO-SSR" — combine adv_histogram + ssr_eval_curve in one figure or give distinct captions/labels.
- `figures/foret_ablation.jpg` ("Relative Improvement with Different Re-thinking Strategies", 7B): baseline VL-Reasoner-7B (SSR, no FR) 29.75/72.35/53.13/40.94 on MathVision/MathVista/MathVerse/MMMU-Pro; VL-Reasoner + trigger forced at test time 30.49/72.90/53.56/41.15 (+2.49/+0.76/+0.80/+0.53 % rel.); "bound" (oracle upper bound of forced rethinking; code `force_append_wait_all` counts a query correct if its rethought response is correct — treat as an upper bound, not an achievable method) 33.68/76.00/55.14/42.51 (+13.21/+5.04/+3.77/+3.85 %); VL-Rethinker-7B 32.27/74.90/54.19/41.69 (+8.46/+3.52/+1.98/+1.84 %). Rethinking ratio of VL-Rethinker (right axis, read from plot, approximate): ≈36% MathVision, ≈24% MathVista, ≈78% MathVerse, ≈18% MMMU-Pro → **rethinking is selective, not uniform** (supports "rethink selectively" claim). Exact ratios are not given in any file; quote as approximate or not at all.
- `figures/overview-2.jpg`: method overview (training queries → VL-Instruct → SSR [(a) rollout & filter into replay buffer, (b) selective replay re-distributing advantages] → VL-Reasoner → Forced Rethinking ("Wait, does it seem right?") → VL-Rethinker). Must be on page 2.
- `figures/teaser-2.jpg`: 72B vs Gemini-2.0-Flash, GPT-4o, Claude-3.5-Sonnet, o1 on 5 benchmarks (matches table_rr).

## 5. Claims in the overview vs the data — what must be corrected or qualified
1. **7B "surpassing OpenVLThinker/R1-OneVision by 2–6 points"**: from table_le, vs OpenVLThinker-7B: +4.7 MathVista, +6.3 MathVerse, +7.0 MathVision, +4.4 MMMU-Pro, +3.1 EMMA; vs R1-Onevision-7B: +10.8, +7.8, +2.4, +20.1, +8.9. "2–6" does not hold; report per-benchmark numbers.
2. **7B Δ row uses underlined "prev SoTA" that ignores MM-Eureka-7B (Qwen)** on MathVista (73.0 > 70.2) and MathVerse (50.3 > 47.9). Against the best listed 7B model the margins are +1.9 (MathVista) and +3.9 (MathVerse), not +4.7/+6.3. The text must not claim +4.7/+6.3 over "all previous" models; either say "over the best general/R1-style models underlined" or use the true max. Recommend: correct the Δ row or explain it.
3. **72B MathVision Δ +6.8**: best open model listed is Qwen-2.5-VL-32B 38.4 → +6.5; +6.8 is vs Qwen-2.5-VL-72B (38.1). **72B MMMU Δ −1.4**: open models listed: QvQ-72B 70.3, Llama4-Scout 69.4 → gap −1.5 / −0.6; −1.4 matches no row. Both Δ values do not follow from the table; the 72B MMMU 68.8 is bolded but is not the best open entry (QvQ 70.3). Bolding must follow AGENTS.md ("bold the best result among the compared methods").
4. **Table bolding**: in table_rr, bold marks only "ours"; o1 is best on MathVision/MMMU-Pro/MMMU/EMMA/MEGA among all compared. Decide (story/paper) whether bold = best open-source (say so in caption) or best overall; in either case MMMU bold must move.
5. **Ablation chain "32.3→29.8→26.0"** in the overview mixes rows: 29.8 = w/o FR (SSR), 26.0 = plain GRPO (no FR, no SSR, no filter); Filter = 28.5. Report as three steps.
6. **Data**: "~38.9K" vs table "16K" for 7B; see §3.
7. **32B model** appears in table_rr but not in the overview: MEGA 19.9 (far below 72B's 51.3, and Qwen-2.5-VL-32B's 13.3 is similarly low) and MMMU-Pro 50.6 < Qwen-72B. Must be reported truthfully, not hidden.
8. MMMU val numbers with † are reproduced by the authors (Qwen2.5-VL); README notes they could not reproduce Qwen2.5-VL's reported MMMU-val. Caption must keep the † note.
9. "Improving both accuracy and efficiency" (overview): no efficiency measurement (tokens, length) exists in the material. Only selectivity of rethinking (rethinking ratio) is supported. Do not claim efficiency gains numerically.
10. "MEGA core 51.3 (+2.3)": among open models only; o1/GPT-4o/Claude/Gemini are higher (52.3–56.2).

## 6. Conventions and format
- Venue style: `neurips_2025` [preprint] (single column). The task says "11-page double-column"; the template's style must not be changed (AGENTS.md). Treat as ~11 pages of content in the given style; venue/format decision belongs to paper-repo.
- Benchmarks and splits as in tables: MathVista testmini, MathVerse testmini, MathVision test, MMMU-Pro overall, MMMU val, EMMA full, MEGA-Bench core. Metric: accuracy (%).
- Evaluation: rule-based answer matching re-using training correctness judgement, vLLM, sampling temperature 0.6 / top-p 0.95 for validation (`train_vlm_multi.sh`); README notes lmms_eval compatibility. Greedy (temperature 0) when n_samples=1 at eval (`experience_maker.py`). Which setting produced the tables is **not stated**.
- Prompt: "Please reason step by step, and put your final answer within \boxed{}" (README); resolution min 256·28·28, max 1280·28·28.

## 7. Citation keys available (references.bib, 114 entries) — use only these
Benchmarks: `mathvista`, `mathverse`, `mathvision`, `yue2024mmmu`, `mmmupro`, `emma`, `chen2024mega`. Base/general VLMs: `qwen2_5_vl`, `qwen2vl`, `qwen2_5`, `internvl_2_5`, `llavaov`, `llava`, `gpt4o`, `claude35`, `gemini`, `team2024gemini`, `openai-o1`. RL reasoning (text): `deepseek-r1` (GRPO), `drgrpo`, `dapo`, `kimi-1_5`, `simplerl`, `open-reasoner-zero`, `deepscaler2025`, `lightr1`, `s1`, `ppo`, `instructgpt`, `DPO`, `letsverify`, `wei2022chain`. Multimodal reasoning: `mmeureka`, `vision-r1`, `lmm-r1`, `R1OneVision`, `OpenVLThinker`, `r1vl`, `virgo`, `insight_v`, `llamav_o1`, `Mulberry`, `llavacot`. Replay: `per` (Prioritized experience replay). Data sources: `ai2d`, `GeoQA`, `chang2022mapqa`, `masry2022chartqa`, `docvqa`, `figureqa`, `saikh2022scienceqa`, `lu2021iconqa`, `lu2021inter`, `johnson2017clevr`, `visualwebinstruct`, `mammothvl`.
**Missing keys** (do not invent): no DeepSeekMath/GRPO-original entry (cite GRPO via `deepseek-r1`), no QvQ, Llama-4, Kimi-VL, InternVL2, R1-VL is `r1vl`. **Caution:** `curriculum` is "ROI-constrained bidding via curriculum-guided Bayesian RL" — not a curriculum-learning reference for LLMs; `wang2025learning` is code integration for math LMs.

## 8. Not established by the material
- Training steps/compute for the 72B/32B runs, data subset used for them, the exact eval sampling for the tables, which run produced `vanishing_adv.jpg`, exact rethinking ratios, any variance/seeds (all results are single runs; no error bars exist — say so, do not invent).

## 9. Method facts from `code/` with file:line (answers story-repo#2 in idea-repo)
Paths relative to `/initial-state/inputs/3/` (task path `code/`). "Script default" = value in `scripts/train_vlm_multi.sh`, not proof of what the reported runs used.

### SSR vs Filter — `openrlhf/trainer/ppo_utils/replay_buffer.py`, `active_sampling` (L402–520)
- Each rollout batch item's advantage is read (L408); items with advantage exactly 0 are "zero" (all 8 rollouts of the query equally rewarded); zero items with reward>0.95 are "positive" (all-correct) items (L416–422).
- Persistent buffer `keep_items`: a `deque` with maxlen = half the rollout batch (L404–405), appended with all non-zero-advantage items of every batch (L423) → FIFO of recent informative experiences.
- **Filter** (`do_ssr=False`, `--filter` ≠ SSR, L441–455): drop zero-advantage items and refill to full batch size by repeating non-zero items, uniform sampling (`p=None`, L450).
- **SSR** (`--filter SSR`, `ppo_trainer.py` L530–532; L486–520): target = half the batch (L486). Candidates = current non-zero items + up to 10% (of their count) all-correct items (L488–492); sampled **with probability ∝ |A|** (L496–502). Rest of the target filled from `keep_items`, sampled ∝ (|A|+1e-4) (L508–518). → priority exponent **α = 1** in this implementation; no other α appears.
- Advantages: group-normalized (`--advantage_estimator group_sft`/GRPO-style, `--normalize_reward`), `init_kl_coef 0.0` and k3 KL estimator flag (script L263) → effectively no KL penalty.
- Policy loss: PPO-clip with asymmetric clip ε_low=0.2, ε_high=0.35 "according to DAPO" (`models/loss.py` L98–104).

### Forced Rethinking — `openrlhf/trainer/ppo_utils/experience_maker.py`
- Enabled when `--data_version` contains `force_append_wait` (L1591); training only, plus two eval modes (L1592–1593).
- Eligibility (L1865–1874): response must have ended with EOS and be ≤ maxtoken−1024 tokens; in groups with accuracy >0.7 incorrect responses are skipped (L1868); each remaining response is skipped with prob. 0.35 (L1872) → **q ≈ 0.65 of eligible responses** get a trigger.
- Truncation: with prob. 0.5 the response is cut before its last "Wait", `\boxed`, "answer", and last paragraph break (L1916–1930), so the model must re-derive the answer.
- Triggers (L1893–1905): "Wait" / "Wait, does it seem right?" / "Wait, let's double check" / "Wait, there might be a mistake". Choice (L1935–1938, training): with prob. 0.5 → "Wait" (p 0.4) or "Wait, does it seem right?" (p 0.6) [questioning]; otherwise "Wait, let's double check" if the first answer was correct [self-verification], "Wait, there might be a mistake" if incorrect [self-correction]. Continuation sampled at temperature 0.9 (L1949–1950).
- Kept (L2011–2050): continuation 30–1024 tokens; **only rethinks that end correct** (L2018); ≤2 per query (L2023); >4 rethinking phrases dropped (L2042–2044). A kept rethink *replaces* the original rollout in the group (L2052–2063).
- Auxiliary SFT: NLL on kept-rethink responses with positive advantage, token-averaged (`models/loss.py` L107–122), added with `aux_loss_coef` (`ppo_trainer.py` L703); script default `aux=0.05` (script L164).
- Native over-rethinking: responses with >5 "wait" are invalid (L775–777).

### `figures/foret_ablation.jpg` definitions
- "VL-Reasoner-7B" = the SSR model without Forced Rethinking (its numbers 29.75/72.35/53.13/40.94 match table_im row "w/o Forced-Rethinking" 29.8/72.4/53.2*/40.9; *MathVerse 53.13 rounds to 53.1, table says 53.2 — minor inconsistency).
- "(forced)": the trigger is appended to VL-Reasoner's responses at test time (eval mode `force_append_wait_eval`, L1592, L2031; eval trigger is "Wait", L1932–1933) and the continued answer is scored.
- "(bound)": eval mode `force_append_wait_all`, code comment "this is upper bound" (L2032): a rethought answer counts only when it is correct, otherwise the original stands → an **oracle upper bound** of test-time rethinking, not an achievable method.
- Caveat: in the shipped code the "incorrect → drop" check (L2018) runs before both eval branches, so the code as given does not reproduce the forced/bound difference exactly; describe the two by the semantics above and say "bound" is oracle.
- "Rethinking Ratio": not computed under that name in the code. Closest: share of responses containing a rethinking phrase ("wait,", "wait a", "alternatively"; counting L1780–1786, ratio L1890). Describe as "fraction of VL-Rethinker-7B responses that contain a self-reflection phrase"; values only approximate from the plot (§4).

### Hyperparameters (script defaults, `scripts/train_vlm_multi.sh` L140–164, L230–290)
group size n=8; train batch `bsz`=512; rollout batch = 512 (`rbuffer=${bsz:-1024}` reads `bsz`, so 512 — script quirk); micro batch 4; LR `${lr}e-7` with lr=10 → **1e-6**; temperature 1.0 (rollout), 0.6/top-p 0.95 (validation); `generate_max_len` 6144, `max_out_tokens` 2048; prompt max 2048; episodes 3; KL coef 0; entropy coef 0; aux SFT 0.05; ZeRO-3, bf16. Paper should present these as "default settings of our training script".

### Base models and data
- Qwen2.5-VL-7B-Instruct → VL-Rethinker-7B; Qwen2.5-VL-72B-Instruct → VL-Rethinker-72B (`README.md`); the 32B row in table_rr implies Qwen2.5-VL-32B (README: "We are training 32B") — base for 32B is inferred, not stated.
- Pool: ViRL39K (~38.9K verifiable queries, 8 categories, model-capability annotations "what queries to use when training models at different scales", README). The 7B ablations use 16K (13K w/o text-only, 11K w/o science+text — so ≈3K text-only and ≈2K science queries, by difference). Relation 16K ⊂ 38.9K is inferred from the capability-annotation remark; the 72B training subset is not given.

## 10. Citation-key map (references.bib) — MISSING = no entry, do not invent
| Item | Key |
|---|---|
| MathVista / MathVerse / MathVision | `mathvista` / `mathverse` / `mathvision` |
| MMMU / MMMU-Pro | `yue2024mmmu` / `mmmupro` |
| EMMA / MEGA-Bench | `emma` / `chen2024mega` |
| OpenAI-o1 / GPT-4o | `openai-o1` / `gpt4o` |
| Claude-3.5-Sonnet | `claude35` |
| Gemini-2.0-Flash | MISSING (closest: `gemini` = Gemini family; `team2024gemini`/`gemini_1_5` = Gemini 1.5, duplicates) |
| Qwen2.5-VL (7B/32B/72B) / Qwen2-VL | `qwen2_5_vl` / `qwen2vl` |
| InternVL2.5 (8B, 78B) | `internvl_2_5` |
| InternVL2-8B | MISSING (only `internvl_2_5`) |
| LLaVA-OV | `llavaov` |
| Kimi-VL, Llama4-Scout, QvQ-72B | MISSING (all three) |
| MM-Eureka | `mmeureka` |
| R1-VL / R1-Onevision / OpenVLThinker | `r1vl` / `R1OneVision` / `OpenVLThinker` |
| GRPO | MISSING as original (DeepSeekMath); cite via `deepseek-r1`; critiques/variants `drgrpo`, `dapo` |
| PPO / RLHF | `ppo` / `instructgpt` |
| LLM slow thinking, RL for reasoning | `openai-o1`, `deepseek-r1`, `kimi-1_5`, `simplerl`, `open-reasoner-zero`, `deepscaler2025`, `lightr1`, `s1`, `wang2025learning` |
| CoT / verification | `wei2022chain`, `feng2023towards`, `letsverify` |
| Prioritized experience replay | `per` |
| Multimodal reasoning RL | `vision-r1`, `lmm-r1`, `mmeureka`, `r1vl`, `R1OneVision`, `OpenVLThinker` |
| Multimodal slow-thinking via SFT/distillation/search | `virgo`, `insight_v`, `llamav_o1`, `Mulberry`, `llavacot` |
| Multimodal instruction data | `mammothvl`, `visualwebinstruct`, `infinity-mm`, `llava` |
| Do not use for curriculum learning | `curriculum` (it is an ad-bidding paper) |
