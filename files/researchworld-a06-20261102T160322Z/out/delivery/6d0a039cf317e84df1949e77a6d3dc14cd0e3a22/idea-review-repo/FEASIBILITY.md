# Feasibility assessment v1 (2026-11-02)

Status of each item: **M** = measured by me this turn, **S** = stated in the supplied material, **E** = my estimate.

## 1. What is actually available (checked)
- **No GPU** in sandbox or in `local-compute` jobs (M: no `nvidia-smi`). `resources.md` allows a 24 GB GPU "or equivalent API budget", but neither is present.
- **No usable API budget** (M): the `OPENAI_*`/`ANTHROPIC_*` variables in the sandbox are the harness's own model route; `/models` answered "model route not authorized", a Messages call returned a provider error. Do not plan on API LLMs; do not use the harness key for experiments.
- **CPU only**: sandbox and each job have 2 CPUs, 4 GB RAM (M: loading Qwen2.5-1.5B in fp32 was OOM-killed). The host is shared (40 CPUs, load ~30 at the time). Jobs have **no network**: fetch models/data first.
- Network works for HF/PyPI/GitHub (M): MMLU-Pro at the pinned revision `b189ec76…` (test 12,032 rows; columns question_id, question, options, answer, answer_index, cot_content, category, src) and Qwen2.5-0.5B/1.5B-Instruct downloaded; `transformers` 5.22.1 + torch 2.14.1+cpu installed.
- **World budget** (S, `ht-role status`): 7200 model-seconds and 96 turns for all 9 positions (~800 s each); compute in jobs is not charged. Every extra issue/round trip is expensive; the plan must be executable with few coordination rounds.

## 2. Measured inference cost
Qwen2.5-0.5B-Instruct, fp32, 2 threads, one forward pass over a zero-shot chat prompt (mean 228 tokens, 8 questions, includes warm-up): **~1.5 s/question** (bf16 was 4x slower: 6.1 s/q — use fp32). Scoring = next-token logits over the letters A–J after "The answer is (": one forward, no generation.
- 1.5B fp32 does not fit in 4 GB; 1.5B bf16 would be ~4x slower than 0.5B fp32 per parameter-count scaling plus the bf16 penalty (E: >10 s/q) — not viable at matrix scale.
- Generation / chain-of-thought is not viable at scale on 2 CPUs with these models (E: tens of seconds per question and 0.5B CoT is poor). Plan direct-answer letter scoring only.
- Not yet measured: 0.5B accuracy on MMLU-Pro (E: near chance, roughly 10–20 %), spread between prompt configs, run-time with few-shot prefixes.

## 3. What is feasible: the cached-matrix design
The only way to make "search then report" experiments affordable is to separate expensive LLM calls from cheap statistics:
1. Run the real LLM once on a **finite pool of configurations C × finite pool of questions Q** and cache the 0/1 correctness (and letter log-probs) matrix.
2. Every search/report experiment (random search, successive halving/bandit, greedy edit search, different search-set sizes n, pool sizes, noise) is a **replay on the cached matrix** with thousands of resampled search/held-out splits: milliseconds each, CPU only.
3. A fully synthetic arm (known true accuracies, controllable n, number of configs, config-effect variance, correlation) covers the theory and the reporting-method calibration at no LLM cost.

Budget guidance (E, from 1.5 s/forward):
| design | forwards | CPU-hours | note |
|---|---|---|---|
| pilot: C=16, Q=500 | 8k | ~3.5 | do first; measures accuracy, config spread, runtime |
| main: C≈48–64, Q≈2000–3000 | 100–190k | 40–80 | split across parallel 2-CPU jobs; wall time depends on how many jobs the shared host gives (unknown, assume 4–8) |
| ceiling | ≤ ~200k | ~85 | beyond this the one-week limit is at risk; do not enlarge to the full 12k test set × many configs (720k+ forwards) |
Each shard must write results incrementally (jobs can be killed; they stop after idle time) and print a `HUTIAN_WAKE:` line only at the end of a stage.
Few-shot demonstrations lengthen prompts (cost scales with tokens): cap at 0–2 shots or cache the shared prefix KV.

## 4. Risks and what to bound
1. **Weak model risk (high).** If 0.5B is near chance, config differences are mostly noise/letter-position bias and "real" selection effects are hard to interpret. Bound: pilot first, report model accuracy; restrict to the question subset where accuracy is above chance, or add a second model only if it fits 4 GB (e.g. a ~1B model in fp32), else state the limitation. Do not claim generality to strong LLMs; claims are conditional on this model/benchmark/search space.
2. **"True performance" is itself estimated.** With a finite pool, fresh-question truth = accuracy on the held-out part of the pool; its sampling noise (SE ≈ 0.9 pp at 2,500 held-out questions) is comparable to plausible gaps (1–3 pp). Bound: hold out ≥ 2,000 questions never used in search; report gaps with uncertainty that includes held-out noise; use the synthetic arm for exact-truth calibration. Search sets (n ≈ 25–500) are drawn from the other part and are repeated many times (resampling, not one run).
3. **Search tool realism.** Real DSPy/MIPRO need generation and many LM calls; not affordable on CPU at scale (jobs have no network, no pip). Bound: implement search procedures (random search, successive halving/bandit, greedy hill-climbing over instruction/format/demo choices) as replays of the cache, and say plainly that they emulate the class of tools, not DSPy itself. Any claim about DSPy specifically is out of scope unless a small real DSPy run is actually done and reported as such.
4. **Config pool design.** The pool must be diverse enough that configs genuinely differ (instruction wording, answer-format cue, option-label style, shot count/selection); a pool of near-duplicates gives a trivial result. A pool defined after seeing results is itself a selection; fix and pre-register the pool before the main run.
5. **Reporting-method claims.** A "more reliable report" (held-out split, cross-fitting, bias correction, selection-adjusted CI, Ladder-style) must be judged by coverage/bias over many replays with known truth (synthetic) and against the held-out truth (real). Replays share one question pool, so replicates are not independent of the pool; treat pool-level uncertainty by bootstrapping questions and say so. Needs reps ≥ 1,000 per cell; cheap.
6. **Reproducibility.** Seeds, pinned HF revision, library versions, model SHA, and which script makes each figure/table must be kept from the start; the paper must report actual compute used (measured, not the task's estimates).
7. **Coordination budget.** 800 model-seconds per position: avoid review ping-pong; one pilot, one main run, one analysis, one writing pass.
8. **Prohibited material.** Searching terms like "prompt optimization overfitting benchmark report" may surface the published paper; stay with the starter list and classical selective-inference/adaptive-data-analysis literature; if a hit is accidental, stop and record it.
9. **Venue deliverable** (PDF + LaTeX in an official latest template, checklist, reproduction README) is cheap in compute but needs figtab/paper time late; do not let the experiment run past ~day 4 of 7.

## 5. Recommended scope (what keeps the study able to meet the objective)
- Keep: both research questions; synthetic arm (gap vs n, #configs, effect variance, noise; effect on pairwise comparisons/"A beats B" conclusions; reporting methods with coverage); one real arm = Qwen2.5-0.5B-Instruct (fp32) × MMLU-Pro × cached matrix × emulated search tools.
- Drop/defer: full 12k test, generation/CoT, real DSPy runs at scale, API models, multiple large models.
- Gate: after the pilot, decide model/subset/pool size from measured numbers; revise this assessment if accuracy ≈ chance.

---
# v2 (2026-11-02): review of `story-repo` plan/study-plan.md (c1679c7) and a second measurement

## Measured (M) additions
- Qwen2.5-0.5B-Instruct, fp32, 2 threads, 150 random MMLU-Pro test items, zero-shot chat prompt, argmax over letters A–J: **accuracy 17.3 %** (SE ≈ 3 pp; chance 10 %), **1.46 s/item**. So the model is above chance but weak; config-to-config spread is not yet measured.
- Qwen2.5-1.5B: a bf16→fp32/int8 conversion in the 4 GB sandbox was OOM-killed again; treat 1.5B as not available. Only ≤ ~0.6B-parameter models fit in fp32 in 4 GB.

## Verdict on the plan
| item | verdict |
|---|---|
| T0 synthetic | Meets. Cost lives in M3 (bootstrap re-runs selection B times per replication) and M2: full factorial n(6)×K(7)×τ(~5)×procedure(3)×leakage(2) with B≈200, 1000 reps is ≈10⁴ cells×reps×B selection runs, order 10–20 CPU-h (E). Bound: fractional grid; M3/M4 at B=100–200 and ≥300 reps on a subset of cells; M0/M1/M2/M4 at the full 1000 reps. Run as sharded jobs with incremental output. |
| T1 real, cached matrix | Meets **if shrunk** to: 1 model (Qwen2.5-0.5B-Instruct fp32), N ≈ 2,500 items (stratified, ≈180/subject), C ≈ 48 configs (floor 16, gated on the pilot), search n ≤ 500 so the disjoint fresh set stays ≥ 2,000 (SE ≈ 0.8 pt at 17 %). ≈120k forwards ≈ 50 CPU-h (E). The plan's "C≈100+, N≥3000, n up to 2000 real" does not fit; n ∈ {1000, 2000} stays synthetic-only. |
| T1 config pool | "LLM-generated / proposer-generated" configs and "reasoning-style" (CoT) variants are **not feasible** (no generation at scale). Use template-built configs: instruction wording × answer-cue × option-label style × ≤2 fixed demos (demos taken from the 70 validation items, not from the search or fresh items; fixed-prefix KV caching keeps cost near zero-shot). Fix the pool before the main run. |
| T1 "few-shot demos drawn from D" leakage factor | Not cacheable (the config would depend on D). **T0-only**; say so. A real-leakage arm is out of scope. |
| T1 adaptive proposer | Emulate as bandit/greedy-edit search over the finite pool (replay). State this. |
| T1 subject breakdown | Descriptive only (≈180 items/subject; SE ≈ 3 pp). |
| T1 resampling | Replications share one item pool, so they are not independent; ≥200 resampled search sets per cell is cheap, but report uncertainty with a bootstrap over items (or state it is conditional on the pool). |
| T2 live tool | Real DSPy MIPROv2 needs generation by the 0.5B model plus a local LM server (no network in jobs); engineering and time cost high (E: ~1–2 h per run at n=50 and K≈10, plus fresh-set scoring). A "faithful own implementation of the search loop" with live letter-logit scoring is feasible (E: K=20×n=100 ≈ 50 min + fresh 1,000 items ≈ 25 min per seed, 5 seeds ≈ 6 CPU-h) but it adds fidelity of the loop (adaptive proposer, bootstrapped demos), not independent statistical evidence, since live scoring equals the cache; the "T1 reproduces live gap" check is then near-tautological. Cut first; if run, label it exactly as run. |
| M0–M4 | CPU-cheap on the cache (K≤200, n≤500). Meets. |
| M5 | Cheap, qualitative. |
| Q2 protocol | Meets; item 6 (separate calibration split) needs N large enough: with N=2,500 and n≤500, reserve ≥ 500 for method tuning and ≥ 2,000 for scoring only if method hyper-parameters are tuned at all; prefer fixing them in advance (cheaper). |

## What is at risk
1. Binding constraint is **model time** (≈800 s/position), not compute: breadth (6 methods × 3 procedures × leakage × grid) must be coded once. Priority: T0 core + M0–M4 → T1 pilot launched immediately (long, model-free compute) → M5 → T2 last.
2. 0.5B accuracy 17 % with unknown config spread: if the pilot shows spread < ~1 pt across configs, the real arm is the τ≈0 regime; still reportable (it shows the naive gap with no true differences) but Q1b's τ-dependence then rests on T0; say so.
3. All real claims are conditional on one weak model, one benchmark, a template config pool and emulated search.
