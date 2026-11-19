# Pre-registration of the data-only diagnostic and the bias-aware interval (H6, H7)

Fixed before any evaluation cell (grid `e7`, fresh seeds, never used to tune anything) was generated.
Exploratory grids e1–e4 are not used to set thresholds below; the constants are chosen here a priori.

Notation. Unit i: assignment z_i, outcome y_i, exposure fraction g_i (treated share of neighbours),
p̂ = mean(z). Estimator under audit: REG-L (OLS on 1, z, g) (primary); the diagnostic is also evaluated
for REG-Q. "Bias" = E[τ̂ − τ] over assignments (measured per cell from replicates).

## D1 — extrapolation validation (primary)
1. Upper-tail check: fit the audited feature map on units with g ≤ q80 (80% quantile of g), predict the units with
   g > q80, Δ_up = mean(y − ŷ) over the tail, gap_up = mean(g | tail) − mean(g | fit set),
   s_up = Δ_up / gap_up, corner error e1 = s_up · (1 − p̂)  (error per unit exposure gap × the distance (1−p̂)
   from the data centre to the all-treated corner).
2. Lower-tail check: same with g < q20 against the fit set g ≥ q20; s_low = Δ_low / (mean(g|fit) − mean(g|tail)),
   e0 = s_low · p̂.
3. Score: with e1, e0 defined as (true − predicted) at the treated / control corner, the estimated bias of
   τ̂ (= predicted contrast − true contrast) is b̂ = e0 − e1; the diagnostic score is |b̂|. Units with tied g are kept on the fit side.

## D2 — spread over a model family
Spread = max − min of τ̂ over {REG-L, REG-Q, REG-G} (fixed feature sets). Score = spread / 2.

## D3 — curvature test
Fit REG-Q; ĉ₂ = coefficient of g²; se₂ = network-robust (dependence pattern: closed 2-hop neighbourhoods)
standard error. M̂ = 2|ĉ₂| + 4 se₂ (i.e. |h''| ≤ M̂, upper 2-sigma). Bound
B = M̂ · ((1 − p̂)² + p̂²) / 2   (the Taylor remainder bound at the two corners for |h''| ≤ M̂).

## Baselines
(a) leverage L alone (graph + design only; score L·σ̂_resid/√n, i.e. the iid standard error of τ̂),
(b) corner distance Z = sqrt(d̄(1−p̂)/p̂) alone.

## Evaluation (cells: grid e7, graphs ER/SBM/BA/WS at d in 5..80, p in {0.1, 0.25, 0.5, 0.75}, response family
of the Brief incl. 2-hop and threshold stress cases, σ_idio in {0, 0.5, 1})
* Cell level: Spearman rank correlation between the median over replicates of the score and the cell's measured |bias|
  (cells with |bias| ≤ 2 MC-SE excluded from precision/recall but kept in the rank correlation); the same for each baseline.
* Replicate level: Spearman between score and |τ̂ − τ|.
* Flag: "unreliable" iff score > 0.10 · max(|τ̂|, sd(y)) (D1, D2); actual positive := cell |bias| > 0.10 · (|β|+|γ|).
  Precision, recall, and AUC (threshold-free). Baselines get their best-possible threshold (oracle-favoured) to be fair to them.
* Failures (2-hop omitted, threshold mechanisms, all families extrapolating the same wrong way) are reported as such.

## Bias-aware interval
Primary: τ̂_REG-L ± (1.96 · se_sandwich + B)  (additive, B from D3), with se_sandwich the network-robust standard error.
Comparators: iid-OLS interval; sandwich interval; unit-pairs bootstrap percentile interval (B=200); block bootstrap by
Louvain clusters (B=200). Evaluate coverage of τ (replicates per cell) and mean width, by regime
(variance-dominated: |bias| ≤ 0.5·sd; bias-dominated: |bias| > 2·sd; between). A cell where coverage < 0.90 is reported as a failure.

## Addendum (2026-11-19, before grid e12 exists): D4 — degree transport (the Brief's "constructive addition")
Written after e7 and before any e12 cell was generated; D1–D3, the baselines and the interval above are unchanged and are re-evaluated on e12's cells too.
Definition (data only, from (graph, z, y)): R = units whose degree is at most the 25th percentile of the degree distribution (ties kept; need |R| >= 50,
else the score is undefined). Fit y ~ 1 + z + g + g^2 + g^3 by OLS on R only (g = treated share of neighbours); transport the fitted h to all units
under the declared assumption "same h across degrees": tau_D4 = b_z + h(1) - h(0), where h(g) = c1 g + c2 g^2 + c3 g^3 (a corner contrast read off the
fitted curve at g = 1 and g = 0). Score D4 = |tau_D4 - tau_REG-L| (the estimated bias of REG-L). Flag rule and "positive" are those of D1/D2
(score > 0.10 max(|tau_hat|, sd(y)); positive = cell |bias| > 0.10 (|beta|+|gamma|)). Recorded with it: the largest g among the 99% quantile of R (support reached).
Grid e12 (`netgate/grids.py`): graphs BA (d = 5, 10, 20), Stanford3 (q = .05, .1, .2), ego-Facebook (q = .1, .25, .5) = heterogeneous; ER (d = 5, 20) = homogeneous control;
p in {0.25, 0.5}; responses (sigma_idio = 0.5): concave, convex, threshold (kappa = 1, no degree dependence); convex with het_gamma = 0.5 and concave with het_gamma = 0.5
(indirect effect proportional to 1 + 0.5 x standardised log degree) and count (degree-multiplicative): the stress cases where the assumption is false.
R = 100 replicates, fresh seeds; bootstrap intervals not recomputed (diagnostics D1-D3 only).
Predictions stated in advance (each can fail): (i) on the heterogeneous graphs without degree dependence the D4 score ranks cells by |bias| better than D1, D2, D3 and
the baselines (Spearman and AUC), and tau_D4 has smaller |bias| than REG-L in the bias-dominated cells; (ii) on ER the advantage is absent (R spans a narrow g range) or tau_D4 is
unstable (large variance); (iii) in the degree-dependent stress cases D4 is not informative and tau_D4 is biased. The reported objects are: Spearman with |bias| (cell level),
AUC and flag precision/recall (rule above), the bias and RMSE of tau_D4 against REG-L, each by graph class (heterogeneous / control) and response group (no degree dependence / stress), with
95% bootstrap intervals over cells; a result against (i) is reported as it is.
