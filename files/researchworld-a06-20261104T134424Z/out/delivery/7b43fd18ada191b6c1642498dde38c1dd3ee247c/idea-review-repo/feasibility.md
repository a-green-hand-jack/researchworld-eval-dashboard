# Feasibility judgement (idea-review-repo) — v1, 2026-11-04

Judged against `Research objective` (issue #1) and `idea-repo` wiki `Brief` (v1). Labels: **[M]** measured by me, **[E]** my planning estimate, **[S]** sourced from the task files.

## Verdict
The objective **is achievable in this world, but only in a scaled-down form**. The synthetic study, the replay-based statistics and all reporting-method validation are comfortably feasible on 2 CPUs. The weak point is the single mandatory real-LLM × real-benchmark stage: it is feasible only as *small open-weight model (≈0.5B), single-forward-pass option-logit scoring, a modest cached (config × item) matrix*, and its size is set by CPU throughput that is today **unmeasured under clean conditions and measured as very slow under contention**. Anything the task text assumes about a 7–8B model, ~10^7 generated tokens, CoT, or DSPy/MIPRO with a capable proposer is out of reach and must not appear in the plan as if done.

## Measured facts [M]
Probe: `evidence/cpu_throughput_probe.py`, log `evidence/cpu_throughput_probe.log`.
- Sandbox: 2 CPUs, 4 GB; `local-compute` identical, no network. Host load average was 160–176 on a 40-processor host (shared with other worlds) while I measured.
- Qwen2.5-0.5B-Instruct, fp32, 2 threads, zero-shot, mean prompt 221 tokens: **0.077 items/s ≈ 13 s per (config,item)**. bf16 was unusably slower (>6 min for 32 items, abandoned).
- Pinned MMLU-Pro fetch works through research-network: test 12,032 rows; categories 410 (computer science) – 1,351 (math); 10 options.
- `transformers`/`torch` install fine via pip; `huggingface_hub` too. Not installed by default: transformers, llama.cpp, vLLM, DSPy.

## Planning arithmetic [E] (labelled as estimates; experiment-repo must replace with a clean measurement)
Cost unit = one forward pass on one (config, item).
| scenario | rate | forward passes per week of one 2-CPU job |
|---|---|---|
| contended, as measured | 0.08/s | ≈ 46 k |
| roofline for 0.5B fp32 on 2 cores (~1 GFLOP/token × 221 tokens ≈ 0.2 TFLOP/item at ~40–100 GFLOPS) | 0.2–0.5/s | ≈ 120–300 k |
| quantised llama.cpp (needs build/wheel; untested) | possibly 2–5× the above | unknown |
Two CPUs are shared between the real-LLM job, synthetic jobs, and the analysis, and the same week must also hold writing and review, so **budget at most ~40–60 % of the week and ≤ ~50–100 k forward passes for the cache**; the whole matrix must be done by ~day 4–5.
Consequences for sizing (K configs × N items cached for all configs, because any config can be the selected one and truth needs all configs on the held-out pool):
- K=24, N=2,000 → 48 k passes: feasible only if throughput ≥ ~0.15/s; at the contended 0.08/s it consumes the whole week.
- K=12–16, N=1,000–1,500 is the safe tier; N=12,032 × any K>2 is **not** feasible; the full test split is out of reach.
- 1.5B in fp32 needs ~6 GB > 4 GB RAM: **not feasible in torch fp32**; only via quantised weights, and then it is ~3× slower per pass.
- Few-shot configs lengthen prompts (5-shot ≈ 5× tokens) — a 5-shot grid is ~5× the cost; keep demos to 1–3 shots and few such configs.
- **Cost saver to demand**: put the varying instruction *after* the item (question+options prefix identical across configs) and reuse the prefix KV cache across configs; this can cut cost per extra config to ~20–30 % of a full pass. Instruction-only configs then cost ≈ 1 + 0.25·(K−1) passes per item. Must be verified for exact equivalence by the experiment owner.

## Risks and scope limits
1. **Throughput risk (high).** See above. Mitigation: first job is a clean, timed pilot (tokens/s, items/s, per-thread scaling, fp32 vs int8/GGUF) that fixes N and K *before* the large run; run the cache as chunked `ht-resource run` jobs writing checkpoints (a job ends after 259,200 s or if idle; chunk per config×item-block so partial caches stay usable); stage it (stage A small N,K → analysable result; then extend). A partial cache must be reported as partial.
2. **Weak signal from a 0.5B model (medium-high).** Zero-shot MMLU-Pro accuracy of a 0.5B model is near chance (10 %) plus a few points; a prompt pool may have almost no true quality spread, so the real experiment would measure mainly pure selection-on-noise. That is still a legitimate "real" setting, but conclusions about the effect of *true spread* must come from synthetic data or from config families that really differ (e.g. answer-format/letter-prior/option-order variants, 0/1/3-shot), and the paper must not generalise real-model results to 7–8B systems. My 4/16 accuracy is a 16-item sample and is not evidence of capability; accuracy should be measured on the full cache.
3. **Truth definition (medium).** "True performance on fresh items" is the accuracy over the cached pool, finite. Keep tuning-set n ≤ ~N/4 and score on the complement (or report with finite-population correction); resampled dev sets are then not independent of the pool, so repeated-replication uncertainty is conditional on the pool. State this; also give pool-level uncertainty (bootstrap over pool items).
4. **No generation noise in the real stage.** Letter-logit scoring is deterministic, so factor (c) of the Brief (sampling temperature/seed noise) cannot be tested in the real LLM; keep it synthetic-only, or a very small sampled-decoding side check. Say so.
5. **Search tool (medium).** DSPy/MIPRO need a proposer LM; a 0.5B proposer is not credible and installing/using DSPy adds cost without benefit. Replay of algorithms (random search, successive halving, best-arm/bandit, greedy bootstrap-few-shot over a *fixed pre-enumerated pool*) on the cache is cheap and exact, but **adaptive proposal of new instructions cannot be replayed** from a cache; say that the real-LLM claims cover pool-based search only. Do not claim to have run DSPy/MIPRO unless it is run.
6. **Demo-leakage arm (medium).** Demos drawn from the dev items need per-(demo-set × item) outcomes, multiplying cost; bound it to a few demo sets, or run it in synthetic only and list it as a limitation.
7. **Statistics compute (low).** ≤16 CPU-h is the task author's number [S]; with vectorised numpy on cached 0/1 matrices, thousands of replications × bootstrap are fine on 2 CPUs if the design grid is bounded (e.g. replications ≤ 2,000–5,000 per cell, bootstrap B ≤ 500–1,000, K ≤ ~200 synthetic). A whole-pipeline nested bootstrap (outer reps × B × search) is the one expensive item: bound by cell count. Selection-aware intervals (AKM conditional/hybrid) require solving truncated-normal problems per replication: fine for K~10–200, must be vectorised.
8. **Scope breadth (high).** Brief §4 lists 7 candidate reporting methods, ≥10 drivers and several search algorithms. A full factorial is infeasible. Required to bound: pick a core set of reporting methods (naive, held-out split, K-fold cross-fit/nested, bootstrap-the-search, AKM-type winner correction, Ladder-type thresholding, report-the-quantile) and a one-factor-at-a-time + a small interaction grid for drivers. Coverage of nominal intervals in a full-factorial grid is what a reviewer will ask; bound it to cells that matter instead.
9. **Shared host (medium).** Other worlds contend for CPUs; wall-clock per job is not controllable. Track the live rate in the job log and re-size.
10. **Sourcing/forbidden-paper (process).** Not a feasibility limit but a hard constraint: all positions use topical queries only. I used none beyond dataset/model fetches.
11. **Time (high).** One wall-clock week for everything, including release review. Suggested gates: D0–1 pilots + synthetic engine; D1–4 cache build in background while synthetic study and method code are finished on the cache's first slice; D4–5 freeze and run final stats; D5–7 figures, paper, review. If the cache is not complete at D4, freeze whatever complete configs/items exist and report it as the real-LLM scale.

## What must be bounded or revised so the objective can be met
- Real stage = ≈0.5B open model, letter-logit scoring, pool-based search replay, K≈12–24, N≈1–2 k, sized from a clean pilot; report compute actually used and the measured contention.
- Real-LLM claims are about "a tiny model on MMLU-Pro with a prompt/few-shot pool", and the paper's headline generalisation should come from the synthetic study plus the real replication, each with its scope stated.
- Ask `ht-human` (via story-repo/idea-repo) once whether a real API or GPU budget exists; absent a grant, don't use the harness credentials.
- Do not promise: 7–8B models, CoT, full 12,032-item test split, DSPy/MIPRO runs, generation-noise real-LLM results, full-factorial grids.

## Re-judgement v2 — 2026-11-05 (against `story-repo` PLAN.md @82a71bb and `experiment-repo` main @8dd4986)
Plan check: PLAN §4–§6 adopt the bounds of v1 (≈0.5B, letter-logit, pool-based replay, synthetic-only generation noise, staged cache with D4 freeze, no DSPy/MIPRO claim); no requirement of the objective is dropped. Feasible as written, with the points below.
- **Larger cache than I bounded, but affordable.** experiment-repo runs 60 configs × 2,000 items (120 k passes) as 10 parallel `local-compute` jobs (6 configs each) using a cached instruction+demo prefix (`code/score.py`), not one job; my v1 arithmetic assumed a single job. Parallelism × prefix reuse is what makes 120 k reachable. It is [E] feasible only if per-job rate ≥ ~0.05 items/s; the progress rate is not visible to me (jobs print to a file I cannot read), so completion by D4 is **unverified**.
- **Truth definition resolved:** `analysis/lib.py` draws T i.i.d. from the pool and takes truth = exact pool mean of the selected config; no truth-sampling noise. The price is that every real-LLM statement is conditional on the 2,000-item pool (the plan already says so).
- **Residual risks:** (1) `score.py` saves only after a full config (2,000 passes); a job killed by the 72 h cap or a crash loses the config in progress. (2) Cache order is config-major, so at the D4 freeze each job has finished 0..6 whole configs and the completed set is unbalanced across instruction/demo/layout families; the plan's "first 500 items, then 1,000, then N" staging is not what is running. (3) Synthetic main cells ran M=500 repetitions where PLAN §3.4 asks ≥2,000. (4) Both CPUs of every job are shared with other worlds (containers/CPU 3–5); wall-clock is not controllable.

## Update 2026-11-05 — answer of `experiment-repo`#4 [reported by experiment-repo, not measured by me]
Per-job rate 0.12–0.2 items/s (5–8 s/item) at 0.4–1.4 cores, host load ~93; ≈17–28 h of running-world time per job for 6 configs × 2,000 items, so the 72 h cap is not binding; the cache looks reachable by D4. Checkpoint is per config (≈3–5 h at risk); freeze rule = configs complete on all 2,000 items, K reported as that count, family composition tabulated in `results/`; synthetic OFAT/stress cells M=2,000, interaction grid M=500. Judgement: the earlier concerns are answered; remaining open item is verifying at the freeze that the completed set and the reported compute match these projections.
