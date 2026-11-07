# Study plan: what does a reported benchmark score mean after automatic tuning?

Owner: `story-repo` (plan). Version 1. Sources: objective (`story-repo`#1), `idea-repo` wiki `Brief` and `Prior-work`,
feasibility judgement of `idea-review-repo` (`feasibility.md`; bounds in `story-repo`#4). Where this plan and the objective differ, the objective wins.
This file fixes *questions, comparisons, scope, success criteria, order of work and who delivers what*. It does not fix results, and the
analysis owner may refine designs as long as every item in §3–§5 is either done or reported as not done (with the reason).

## 0. Setting and notation (one definition for all positions)

A *system* is tuned on a *tuning set* T of n items drawn from a benchmark population; a *search procedure* S picks a configuration
ĉ from a candidate set 𝒞 (|𝒞|=K, or an adaptive search with evaluation budget B) using only T. Accuracy of config c on the population is μ_c.

- **Naive report**  R_naive = acc_T(ĉ)  (the same items select and score).
- **Truth**  μ_ĉ = accuracy of the *selected* configuration on fresh items. Synthetic: exact (known item model). Real: accuracy of ĉ on the pool items
  not in T (finite pool; every statement is conditional on the pool and says so).
- **Optimism gap**  Δ = R_naive − μ_ĉ. Report E[Δ], its MC standard error, and the distribution of Δ (quantiles, P(Δ>0)), never a point value alone.
- Note the three sources to separate: (a) **selection bias** (max over K noisy estimates), (b) **extra adaptivity** (rounds, budget allocation, successive halving),
  (c) **demo leakage** (few-shot demos taken from T so that T items are in the prompt). Item-sampling noise vs. generation noise: generation noise exists in synthetic data only
  (real scoring is deterministic letter-logit; stated as a scope limit).
- **Reporting method** M maps (T, search transcript, optionally extra items) to a point report and optionally an interval for μ_ĉ.
  Reliability = bias E[M−μ_ĉ], RMSE, interval coverage vs. nominal 95% (and 90%), width, one-sided lower-bound validity, and *cost* (items spent).
- The unit of repetition is the **whole pipeline** (draw T → search → select → report → compare to truth).

## 1. Research questions → claims the paper may make → evidence that decides each

| id | question | evidence that decides it (a claim is stated only if the evidence supports it; conditional/negative outcomes are reported as such) |
|---|---|---|
| Q1 | How large is Δ? | Synthetic grid (exact truth) + real-LLM replay (MMLU-Pro cache). Mean Δ with CIs per cell. |
| Q2 | Which factors move Δ? | Synthetic one-factor-at-a-time (OFAT) + small interaction grid (§3); real replay varies n, K, search procedure, subject, config family. Compare with the analytic extreme-value prediction (§3.3). |
| Q3 | Does Δ change conclusions? | Pairwise-comparison study (§4): false-claim rate, wrong-sign rate, ranking flips, ship/no-ship errors, unfair comparison when two systems used different search budgets; naive-CI coverage. |
| Q4 | Is there a more reliable report? | Candidate set (§5), validated by whole-pipeline repetition in synthetic **and** real replay against the pre-registered criteria of §6. May end as "no method is uniformly reliable"; that is an admissible result. |
| Q5 | How should reliability be tested? | The validation protocol itself (§6) is a contribution: known/near-exact truth, whole-pipeline repetition, MC error on every metric, equal-item-budget comparison, failure-case search (adversarial configs: ties, one outlier, strong correlation). |

## 2. Division of work

| position | what it delivers for this plan |
|---|---|
| `idea-repo` | context: Brief, Prior-work, positioning vs. starter list; owns the single forbidden-material log. |
| `idea-review-repo` | feasibility checks (done once; re-judges after the clean pilot and at the D4 freeze). |
| `experiment-repo` | all computation: pilot timing, response cache, synthetic simulator, replay searches, reporting methods, validation, results files with seeds/versions, `code/`, run notes. Chooses implementations and refines grids inside §3–§6. |
| `figtab-repo` | exhibits E1–E7 (§7) from committed results files only. |
| `paper-repo` | manuscript, checklist, `REPRODUCE.md` assembled from experiment-repo's `code/README` + figtab's script map. |
| `venue-repo` | venue (NeurIPS 2026 main, ≤9 pages), `venue-artifacts.json` from the paths in CODEOWNERS. |
| `story-repo` | this plan, CODEOWNERS, claim list and exhibit requirements; revises on request, answers scope questions. |
| `internal-review-repo`, `external-review-repo` | review. |

Delivered paths: see `.forgejo/CODEOWNERS` of `paper-repo` (proposed by pull request; summarized in `story-repo`#3).

## 3. Synthetic study (CPU only, exact truth)

3.1 **Data model** (documented, with the parameter ranges used):
item i has latent difficulty; config c has quality μ_c; correct-probability p_ic = link(μ_c, d_i, ρ) so that configs are positively correlated across items
(corr ρ ∈ {0, 0.3, 0.6, 0.9}); outcomes Bernoulli (optionally with generation noise: each (c,i) re-sampled per call with flip probability ε). True spread of μ_c
across 𝒞: σ_μ ∈ {0, small, medium, large} (σ_μ=0 is the pure winner's-curse case); base accuracy ∈ {0.1 (10-option chance), 0.3, 0.5, 0.8}.
Item heterogeneity: Beta-distributed item difficulty. A **calibrated variant** fits this model to the real cache (§4) so synthetic factors are grounded.

3.2 **Factors** (one-factor-at-a-time around a reference cell; then a small interaction grid on n × K × σ_μ; **no full factorial**):
tuning-set size n ∈ {50,100,200,500,1000,2000}; number of candidates / budget K ∈ {2,4,8,16,32,64,128}; σ_μ; ρ; base accuracy; search procedure
(exhaustive best-of-K; random search with budget; successive halving; best-arm identification (LUCB/successive-rejects style, after Shi et al.); multi-round greedy / bootstrap-demo style adaptive search); generation noise ε (synthetic only); demo leakage (demos taken from T, m ∈ {0,3,8} demos).

3.3 **Theory check** (depth chosen modestly): for σ_μ=0 and exhaustive search, E[Δ] ≈ σ_n · E[max of K correlated standard normals], σ_n=√(p(1−p)/n); compare with simulation across K, n, ρ (extreme-value / Gaussian-max approximation; Chernozhukov et al.), and state where it fails (small n, p near 0, large σ_μ, adaptive search). With σ_μ>0 compare with the conditional-on-selection (truncated-normal) bias formula used by Andrews–Kitagawa–McCloskey. Any theorem stated in the paper must be proved there or cited; otherwise it is an empirical approximation, labelled as such.

3.4 **Replications**: ≥2,000 whole-pipeline repetitions for each main cell (≥500 for interaction cells), seeds recorded; bootstrap-based methods capped at B≈200–500 per repetition; MC standard errors reported; coverage compared with the binomial MC band, not with 0.95 exactly.

## 4. Real-LLM × real-benchmark study (the mandatory real setting), scaled to this world

Facts of this world (measured/verified by others): 2 CPUs, 4 GB, no GPU, jobs offline, no declared LLM API; measured ≈0.077 items/s for Qwen2.5-0.5B-Instruct fp32 on a loaded host (`idea-review-repo/feasibility.md`). The plan therefore **does not assume a 7–8B model, CoT generation, or DSPy/MIPRO runs**.

4.1 **Model and scoring**: one small open-weight instruct model (target Qwen2.5-0.5B-Instruct, fp32, revision hash recorded; `experiment-repo` may switch only after a timed pilot, with the reason recorded). Score by **a single forward pass reading the next-token logits over the 10 option letters** (deterministic; cache `argmax` correctness and the 10 logits). This is a deviation from the MMLU-Pro CoT protocol; the paper states it and scopes real claims to "small model, letter-logit scoring".
4.2 **Benchmark**: MMLU-Pro pinned at revision `b189ec765aa7ed75c8acfea42df31fdae71f97be` (test split; 10 options; 14 subjects); a fixed random **pool of N≈1,000–2,000 items** (stratified by subject; size fixed from the clean timed pilot, may be 2k only if the pilot supports it). Items used as demos come from the 70-item validation split or from a reserved slice, except in the leakage arm (4.5).
4.3 **Configuration pool** (𝒞, K≈12–24, all evaluated on all N items): families chosen because they produce real spread for a weak model:
answer-format instruction variants (e.g. "Answer:" / "The answer is (" / plain letter), letter-prior calibration or option-order permutation, instruction wording variants, and few-shot count (0/1/3 shots; few configs with demos because they multiply cost). Put varying text *after* the item so the question prefix can share a KV cache (≈4× cheaper). If real spread is tiny (a 0.5B model is near the 10% chance level on MMLU-Pro), that is itself a finding (small σ_μ → winner's curse dominates), and the "effect of true spread" claim is taken from §3.
4.4 **Replay**: draw tuning subsets T ⊂ pool (n ≤ N/4, e.g. n∈{50,100,200,400}); search procedures implemented **in-house over the fixed pool** (random search, best-of-K, successive halving, best-arm, greedy/bootstrap-demo selection over pre-built demo sets); report on T; truth = accuracy of ĉ on pool∖T. Thousands of resamples, CPU only. Pool uncertainty (finite pool) is handled by an outer split of the pool (resample pools of half size) or stated as a conditional-on-pool limitation. No claim of having run DSPy/MIPRO: the adaptive instruction-proposal step of those tools cannot be replayed from a cache and a 0.5B proposer would not be credible; their relation is discussed in related work and limitations.
4.5 **Leakage arm** (small): a few fixed demo sets (≈6 sets × 3 demos) drawn from items that may fall in T; for replay draws in which a demo item is in T, the demo item's outcome is its with-demo-in-prompt outcome (extra forward passes only for those few items). Larger-scale leakage is synthetic only.
4.6 **Staging** (a partial cache must stay analysable): D0–1 clean timed pilot (throughput with shared-prefix KV, int8/other if installable); D1–4 cache built by chunked, checkpointed `local-compute` jobs in order of priority (all configs on the first 500 items, then 1,000, then up to N); D4 **freeze** (whatever is complete defines the real-LLM scale; reported as such); D4–5 final analysis and figures; D5–7 manuscript and review. Compute actually used is logged by `experiment-repo`.
4.7 **Budget question**: no position can reach `ht-human` from here; this plan assumes **no** API/GPU. If any real budget appears, the extension would be a larger model on the same pool (same code), not a change of design.

## 5. Conclusion-level analysis and reporting methods

5.1 **Do gaps change conclusions** (synthetic and real replay): (i) two systems A and B with equal true quality (null) and with true difference δ ∈ {0, small, medium}: P(naive reports A>B by ≥ margin) = false-claim rate; wrong-sign rate; (ii) A searched with budget K_A, B with K_B ≠ K_A: the bias in the difference attributable only to unequal budgets; (iii) tuned vs. untuned baseline (the baseline's score is an unselected fresh number); (iv) ranking flips among M tuned systems; (v) coverage of the naive 95% Wilson/normal CI around R_naive; (vi) a ship/no-ship threshold rule (ship if report ≥ τ) → false-ship rate.
5.2 **Reporting methods** (the core set; each implemented once, used in both settings):
 1. naive (baseline); 2. held-out split (fraction f of the item budget reserved; ĉ chosen on the rest; report on holdout; costs items: compare at **equal total items**); 3. K-fold cross-fitting / nested (search inside folds, report out-of-fold; estimand = procedure's performance, stated as such); 4. bootstrap-the-search (bias correction; known failure for extremal statistics shown, not hidden); 5. winner-aware correction after Andrews–Kitagawa–McCloskey (median-unbiased / conditional and hybrid CIs for the selected arm, with the Gaussian approximation; where its assumptions fail, say so); 6. simultaneous / max-statistic bound by Gaussian multiplier bootstrap (Chernozhukov et al.) giving a lower bound valid for the selected arm; 7. Ladder-type thresholded reporting (Blum–Hardt), meaningful only for sequential submissions; 8. performance-quantile / distribution report over 𝒞 (Polo et al.; Sclar et al.) — a *different estimand*, evaluated for what it answers, not as an estimator of μ_ĉ.
5.3 **Proposed reporting protocol**: not fixed in advance. After the validation (§6) the paper proposes the best-justified protocol, which must include (at minimum) the disclosed search specification (K or B, n, procedure, seeds) so that the gap can be reasoned about, plus whichever estimator/interval of §5.2 passes §6 — possibly a combination (e.g. winner-aware interval on the same items vs. a small fresh holdout). If none passes, the finding is "only a disjoint holdout is reliable; here is its price".

## 6. Validation protocol (pre-registered success criteria; edits only by a dated note in this file)

For each (setting, cell, method), over R whole-pipeline repetitions report: bias, RMSE, coverage of the nominal interval (with the MC band), mean interval width, lower-bound violation rate, and the items consumed. A method is called **reliable in a cell** if |bias| is within 2 MC s.e. of 0 *or* below 0.5 percentage point (whichever is larger), and coverage is within the 95% MC band of nominal; **reliable overall** only if it is reliable across the whole interaction grid minus pre-declared failure cells. Required stress cells: σ_μ=0 (pure winner's curse), a single outlier config, K≫n^½, strong correlation, small n, and base accuracy near chance. Real replay is a **transfer check** for the synthetic-calibrated claims (same metrics, truth = pool∖T), not a replacement for them. Negative outcomes (a method fails, a factor has no effect, real spread is tiny) are reported as measured.

## 7. Exhibits (figtab-repo draws only from committed results files; each needs claim, n of repetitions, CI method in caption)

| id | exhibit | claim it must support |
|---|---|---|
| E1 | Δ vs. K for several n (synthetic, σ_μ=0 and σ_μ>0) with the §3.3 analytic prediction overlaid, CIs | Q1,Q2: size and shape of the gap; where the approximation holds |
| E2 | Tornado/panel of OFAT effects on E[Δ] (n, K, σ_μ, ρ, base acc., search procedure, ε, leakage) | Q2: which factors matter, ranked, with CIs |
| E3 | Real-LLM replay: reported vs. fresh score (y=x line) and Δ vs. (n,K), per search procedure; per-subject inset | Q1,Q2 in the real setting |
| E4 | Decision impact: false-claim / wrong-sign / false-ship rates, naive vs. budget-matched comparison | Q3 |
| E5 | Reliability of reporting methods: bias, RMSE, coverage with MC bands (synthetic stress grid) | Q4,Q5 |
| E6 | Same on the real replay (transfer check) + cost in items (equal total items) | Q4 |
| E7 | Setup/compute table (model + revision, search procedures, grids, repetitions, seeds, compute used, what was not done) | rigour, reproducibility |
Main text ≤9 pages: E1,E3,E4,E5/E6 likely main, others appendix; figtab-repo and paper-repo decide placement.

## 8. Rules for every position

- Forbidden-paper rule (Brief §2) applies to every search; topical queries only; report any accidental hit to `idea-repo`.
- No placeholders, no illustrative numbers; unfinished work is written as unfinished. Every number in the paper traces to a script and a committed results file.
- Pin: dataset revision, model revision hash, package versions, seeds; record compute actually used (CPU-hours, wall-clock, forward passes).
- Scope statements required in the paper: small model / letter-logit scoring; finite pool; fixed-pool search (no instruction proposal); generation noise synthetic-only; DSPy/MIPRO not run.
