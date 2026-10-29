# Draft reference gap analysis

**Status:** ready. Three targeted retrieval needs, none requiring a rewrite of the paper story.

## Overall assessment
The draft is densely cited on Bradley-Terry estimation (ties, order effects, existence of the MLE, penalised fits, asymptotics) and on sampling uncertainty. It also cites the single-point influence-function paper, the dropping-data robustness paper, the two Arena integrity papers, and the Arena and MT-Bench data sources. All quantitative claims are grounded in `paper_data.json` and are out of scope here. The gaps concern the paper's actual subject (small adversarial edits to comparison data), the caveats on first-order approximations, and the sports data.

## Targets

### 1. Poisoning and manipulation literature (high, positioning) — Related Work
- **Anchor:** the "Influence and robustness to dropping data" and "Integrity of crowd-sourced leaderboards" paragraphs.
- **Why:** the paper asks how few dropped or reversed rows displace rank 1, which is a data-poisoning or manipulation question. No citation covers influence-based poisoning, label-flip attacks, or adversarial manipulation of rank aggregation and rating systems. The "generic, evaluator-verified probe" framing cannot be positioned without this, and reviewers would likely flag it.
- **Search topics:** influence-function-based data poisoning; label-flipping attacks on logistic or pairwise models; adversarial robustness of rank aggregation from pairwise comparisons; manipulation-resistant rating systems (Elo / BT).

### 2. Accuracy of first-order group-removal approximations (medium, background) — Problem Setting and Method
- **Anchor:** "(i) Additivity. The per-row effects are summed without modelling how p_i and A change…". The "Linearisation error" hypothesis in the analysis section relies on the same claim.
- **Why:** the claim that the additive first-order heuristic can be inaccurate at a 2% budget is uncited. Only single-point influence and the dropping-data robustness paper are cited.
- **Search topics:** accuracy of influence functions for group effects; infinitesimal-jackknife approximation error when dropping data in M-estimators or logistic regression.

### 3. Sports rating context (medium, benchmark_context) — Problem Setting and Method
- **Anchor:** Table 1 row "Sports: NBA regular-season games of 2008, 2012, 2015; home team listed first".
- **Why:** NBA results are used as a fourth BT design (and called a "sports proxy" in Limitations) without any citation to BT or Elo-style rating of sports teams. One or two references would justify the design and the home-team-first and tie conventions. The Arena and MT-Bench rows are already cited.
- **Search topics:** Bradley-Terry rating of sports teams with home advantage; Elo rating applied to basketball or team sports.

## Deliberately not flagged
- BT model variants and estimation: already over-supported.
- Uncertainty of rankings: adequately cited.
- LLM-judge and Arena data descriptions: covered by the Chiang and Zheng citations.
- Numerical results, reference-policy scores and validity checks: grounded in `paper_data.json`.
