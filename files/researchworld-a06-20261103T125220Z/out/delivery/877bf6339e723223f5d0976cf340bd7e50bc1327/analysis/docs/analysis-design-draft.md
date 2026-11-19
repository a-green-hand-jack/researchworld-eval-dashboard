# Analysis design draft — not a results claim

## Targets and separation

For a frozen deterministic system/configuration c and question X from target distribution P, define theta(c)=E_P[Y(c,X)], Y in {0,1}. Given search questions S, choose c_hat(S)=argmax empirical accuracy with a prespecified tie rule. Primary estimands are E[reported accuracy - theta(c_hat)], interval coverage of theta(c_hat), probability a claimed improvement over a frozen default is false, and regret relative to the best frozen candidate. An optimizer's expected future performance E_S theta(c_hat(S)) differs from the conditional performance theta(c_hat(S)) of a particular selected system. Report both only with the appropriate repeated experiment.

A finite prompt bank is an exhaustive search problem. Increasing K will use randomly ordered bank prefixes fixed independently of the question outcomes; repeatedly shuffling bank subsets can assess sensitivity. This is not evidence for newly generated adaptive prompts.

## Real experiment proposed pending timed pilot/plan settlement

Pinned MMLU-Pro revision from supplied data.md. No externally cached model answers. Greedy generated outputs from Qwen2.5 instruction GGUF (pinned model hash), CPU-only llama.cpp, with raw text and invalid answers retained. Use validation questions only for runtime/formatting checks. Main pool/partition seeds and prompt bank frozen before main outcomes. Question-level random partition, stratification/micro versus macro target stated explicitly; no prompts selected by test or audit accuracy. Baseline is one frozen ordinary prompt. Vary n and K using a score matrix, drawing selection samples only from the selection pool. Fresh audit questions are disjoint. If a finite pool is reused across repeats, repetitions measure conditional resampling behavior; their Monte Carlo standard error is not uncertainty about the population or a new model. Resample independent questions in both pools for uncertainty, and retain candidate dependence by resampling whole rows.

The observed selected-minus-audit difference is noisy. Audit size, per-prompt audit standard error, covariance and reference uncertainty must accompany bias/coverage summaries. Exact finite-bank evaluation targets and fresh finite audit estimates must not be conflated with an oracle population truth. Category estimates and invalid-response rates diagnose failure modes, rather than retrospectively excluding difficult categories. Model size is limited by measured CPU runtime, not by the objective's GPU suggestion.

## Synthetic experiments proposed

Generate correlated Bernoulli correctness with known candidate means and controlled shared question difficulty. Include equal-quality candidates (pure selection optimism), heterogeneous qualities (actual gains versus noise), and strongly correlated candidates. Study n and K, with repetitions sized by a timed pilot. Compare reused-score reporting with an independent holdout at matched total question/answer budget, plus simultaneous fixed-bank intervals. Naive binomial coverage can be exact for K=1 but fail after winner selection. Use known means for all coverage and decision-error evaluations; report Monte Carlo standard errors. Include one genuinely adaptive search simulation only if its mechanism and target are explicit; do not imply fixed-bank guarantees cover arbitrary adaptive candidate generation.

## Reporting alternatives and guarantees to check

- Independent holdout: freeze selected configuration before exposing audit labels; exact binomial Clopper–Pearson interval under iid questions. Its guarantee conditions on selection but requires independent future questions.
- Simultaneous fixed-bank bounds: Bonferroni binomial intervals at alpha/K (or bounded Hoeffding bounds) cover every frozen candidate jointly, hence the selected candidate; may be conservative. K must include every queried configuration. This claim does not survive arbitrary same-data candidate construction.
- Data splitting chooses among fewer observations; compare actual selected quality and total answer budget, not interval coverage alone. Audit reuse for further selection invalidates the simple independent-holdout guarantee.

All quantities above are prospective definitions. Nothing in this draft is a measured finding.
