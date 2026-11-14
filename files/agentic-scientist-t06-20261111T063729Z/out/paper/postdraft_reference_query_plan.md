# Post-draft reference query plan

**Status:** ready. Six queries, all driven by `draft_reference_gaps.md/json`.

**Central topic:** Citation gaps in a paper on minimal removal sets (verified by exact Bradley-Terry refit) that flip adjacent-pair rankings of pairwise-comparison leaderboards.

## Existing bibliography (context)
The bibliography already covers Bradley-Terry extensions, existence and consistency of the MLE, estimation and uncertainty (Davidson, Simons, Butler, Bong, Gao, Li, Yan and others), plus Broderick et al. on dropping data. No query below revisits those areas.

## Queries

### 1. arena-leaderboard-context (Introduction, high)
- `Chatbot Arena open platform for evaluating LLMs by human preference`, category `benchmark_context`.
- The opening claim that BT leaderboards are used to choose and announce models, and the Arena 55k/140k data in the Data section, have no platform citation.

### 2. arena-leaderboard-context (Data, high)
- `Judging LLM-as-a-judge with MT-Bench and Chatbot Arena human pairwise judgments`, category `benchmark_context`.
- The MT-Bench human judgments and the Arena human-preference data are used without citing the dataset paper.

### 3. influence-deletion-method (Problem Setup and Method, high)
- `Understanding black-box predictions via influence functions`, category `core_method`.
- The Newton-step influence of deleting row i is the core of the studied configuration. Only Broderick et al. is cited.

### 4. influence-deletion-method (Problem Setup and Method, high)
- `Cook's distance case deletion diagnostics one-step approximation logistic regression`, category `baseline_comparator`.
- The leverage-corrected leave-one-out approximation and the B2 influence-only comparator follow classical deletion diagnostics.

### 5. manipulation-positioning (Related Work, medium)
- `adversarial vote manipulation of LLM arena leaderboard rankings`, category `result_driven_theme`.
- The budget is motivated through deliberate action and rigging, yet the "Scope of the bibliography" paragraph disclaims positioning against that work.

### 6. manipulation-positioning (Related Work, medium)
- `robustness of rankings from pairwise comparisons to adversarial or corrupted comparisons`, category `baseline_comparator`.
- One or two general comparator citations would replace the disclaimer.

## Not targeted
BT extensions, estimation and uncertainty related work. The gap memo says more citations there would only grow the bibliography. Numeric claims are grounded in `paper_data.json`. No Elo or sports queries are added because the gap artifact does not flag them.
