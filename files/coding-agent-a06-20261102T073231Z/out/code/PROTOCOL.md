# Analysis protocol (written before model responses)

Created 2026-11-02 UTC. This is a prospective analysis plan, not a registry submission.

## Scope
Study reporting after a fixed, finite prompt search. Do not claim coverage for
unbounded adaptive prompt generation, reused holdouts, distribution shift, or
unobserved large models. No broad literature search; access only supplied papers
and direct official software/model/data/conference sources.

## Real experiment
- Qwen2.5-0.5B-Instruct, official Q8_0 GGUF, revision
  9217f5db79a29953eb74d5343926648285ec7e67; CPU llama.cpp.
- MMLU-Pro test, b189ec765aa7ed75c8acfea42df31fdae71f97be.
- Uniform random 2,048 questions, seed 20261102, first 1,024 development,
  remaining 1,024 locked audit. No use of validation examples or explanations.
- Freeze 24 configurations: 2 instructions x 3 label punctuation styles x
  4 cyclic option rotations. A configuration always rotates by the same amount;
  decode its generated label back to the original option index.
- Generate one answer constrained to legal option letters, greedily, without
  chain of thought. This is a defined constrained-decoding system, not a claim
  about the model's usual unconstrained benchmark score. Retain every response.
- Uniform candidate tie breaking is implemented using random priorities fixed
  separately for every Monte Carlo repetition. Primary actual deployment choice
  uses smallest candidate ID on ties.
- Primary locked audit: tune all 24 on first 128 development questions; report
  selected training accuracy, locked audit accuracy and exact 95% binomial CI;
  compare to fixed candidate 0 using paired correctness.
- Empirical-population replay: development matrix is an exactly known finite
  population. Draw iid question rows WITH replacement; this preserves dependence
  among candidate outputs and makes the target mean known. Repeat 4,000 times.
  n = 32,64,128,256; K = 1,4,8,16,24; fixed nested candidate order.
  Target is the selected candidate's development-population accuracy, NOT an
  assertion that this finite population equals unseen natural-language tasks.
- Assess mean optimism, apparent versus population gain over candidate 0,
  naive exact-binomial interval coverage, Bonferroni exact-binomial simultaneous
  interval coverage, independently evaluated exact-binomial interval coverage,
  widths, and erroneous positive superiority claims. Report Monte Carlo SEs.
- Equal total-label budget ablation: full reuse of n versus tune n/2 and audit
  n/2; both are supplied by the cached matrix. Evaluate what is lost in selection
  quality as well as gained in inferential reliability.
- Candidate duplication ablation: duplicate each column eight times. Duplication
  must not change exhaustive-search performance; it should widen a raw-count
  Bonferroni interval. Deduplicating identical programs before seeing responses
  restores the original guarantee. Do not deduplicate merely identical observed
  response vectors when treating candidates as population functions.

## Synthetic experiment
- Equimean Bernoulli arms p=.3, shared-row mixture correlation rho=0,.5,.9.
  Candidate counts 1,4,16,64; sample sizes 32,128,512; 4,000 repetitions.
  Verify how search size, correlation and sample size affect optimism, coverage,
  and false superiority. Independent Bernoulli audits of same size.
- Heterogeneous arms and Gaussian common-noise example may be added as explicitly
  labeled secondary analyses, with seeds and all configurations recorded.

## Reporting
- No optional stopping based on desired results; engineering changes and failed
  attempts go in logs and README. Statistical methods are standard; novelty is
  the estimand-aware evaluation and linked evidence, not a new general solution
  to adaptive data analysis. State finite-pool and small-model limitations.
- Main paper: ICML 2026 official style, <=8 body pages, references/appendix extra;
  include impact statement and a completed reproducibility/ethics checklist.
