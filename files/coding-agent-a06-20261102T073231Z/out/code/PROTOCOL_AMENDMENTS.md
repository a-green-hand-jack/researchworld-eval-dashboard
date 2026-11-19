# Prospective clarifications

2026-11-02, before real-model response generation:

1. The original phrase "equal total-label budget" next to the n/2 split was
   imprecise. That comparison matches question count, and costs fewer actual
   LLM calls because only the chosen configuration is audited. Report it as an
   equal-question comparison.
2. Add an exactly matched LLM-call comparison. For a reuse design costing K*n
   calls, tune t=n-ceil(n/K) questions on each of K configurations and audit only
   the winner on h=K*ceil(n/K) independent questions. Thus K*t+h=K*n exactly.
   With K=24 this preserves most tuning questions and buys an audit of about n
   questions. Measure selection quality, audit bias, exact-binomial coverage,
   interval width, and paired false superiority. This allocation is fixed by
   arithmetic and not fitted to outcomes.
3. The data actually contain 3--10 options, despite the shorthand "10 options"
   in the task. Grammar and rotations use the actual option count for each item.

2026-11-02, 08:04 UTC, after synthetic null results but before real locked audit:

4. Add a labeled secondary heterogeneous-mean simulation to test the claim that
   true separation stabilizes selection. Fix K=64, n=128, independent Bernoulli
   candidates, baseline and all ordinary candidates p=.3, one candidate p=.3+gap
   for gap in {0,.02,.05,.15}; 4,000 repetitions, separate seed 77302. Report
   optimal-selection probability, oracle regret, optimism, and interval coverage.
   This does not alter the primary null simulation or the real-data protocol.

2026-11-02, final validation after all real responses and primary analysis:

5. Correct budget accounting for paired superiority tests. Winner-only auditing
   costs h calls and supports accuracy reporting; a paired comparison additionally
   requires h baseline calls. The original K*t+h accuracy experiment is unchanged,
   but its unbudgeted paired-test diagnostic columns are removed. Add a separately
   labeled cost-accounting correction experiment with K=24, n in {32,64,128,256},
   t=n-ceil(2n/K), h=(K/2)*ceil(2n/K), so K*t+2h=K*n exactly. Use a separate seed
   88303 and 4,000 repetitions. Report both baseline and winner audit calls,
   selected quality, and false superiority frequency. This is a final-validation
   addition, not part of the original prospective primary design. It requires no
   additional LLM inference, and leaves earlier random draws unchanged.
