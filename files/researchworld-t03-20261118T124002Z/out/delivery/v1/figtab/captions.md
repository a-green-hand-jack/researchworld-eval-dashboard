# Caption text for the delivered figures and tables

Caption bodies for `paper/`; the paper places and may shorten them. Numbers are read from the `.json` / `.tex` beside each item or from the named
result file, not typed from memory; re-check them after any rebuild (`make_all.sh`). "Preliminary" means the input is not yet final in
`results/STATUS.md`: do not print a number from a preliminary item as a result.

All figures are drawn at the width they are placed at (include without `width=`/`scale=`). Tables are tabular bodies: place them in `table*` with `\small`.

## Fig 1 — `fig1_tail.pdf`, `figure*` (C1)

```latex
\caption{\textbf{One SHAP run is not reliable for a sizeable share of instances, even when the mean looks fine.}
(a)~Empirical CDF over instances of $r_3$, the probability that the top-3 features of a single run equal those of the exact Shapley values,
at the shipped KernelSHAP budget, for the exact top-3 (solid) and the $\epsilon$-tolerant top-3 (dotted; a set counts as correct if it differs from the exact top-3 only in features whose attribution lies within a relative $\epsilon=0.1$ of the cut), one colour per dataset and model;
triangles mark the mean of the exact $r_3$; the thin vertical line is $r_3=0.9$. Only the lower part of the CDF is drawn.
On ACS the exact tail is almost entirely ties (the $\epsilon$-tolerant curves lie at the bottom); on German it is not.
(b)~Fraction of instances with $r_3\ge 0.9$ against the number of attributes $d$ (feature subsets of each dataset), shipped budget, with 95\% cluster-bootstrap intervals.
(c)~Observed $r_3$ against $z$, the gap between the $k$th and $(k{+}1)$th attribution in units of its standard error, binned by quantile (Covert--Lee runs at the shipped budget):
with the true $z$ (needs the exact values) and with the plug-in $z$ of a single run.
$r_3$ from $R{=}20$ reruns per instance; 100 instances per cell, three model seeds.}
```

The x16 version of the exact ECDF is `figA_ecdf_x16.pdf` (`figure`; "Exact $r_3$ at $\times1$ (solid) and $\times16$ (dashed) budget, as Fig. 1a").
Reads: `tidy_*_R20.csv` (all 18 Tier-1 cells; columns `r`, `r_eps10`), `plugz_*_R20.npz`; (b) also the d=8, 12 subset cells.
**(b)**: German and ACS d=8, 12, 20 / 8, 12, 16 are all drawn now (German d=12 GBDT s0 rebuilt by experiment-repo); STATUS.md still calls the d-curve preliminary, so check it before quoting. Arrhythmia (d=12, 16, 40; margin scale, 1 seed) is not drawn: another scale and dataset, and d>20 is 20 instances. If the paper has to cut, (b) goes first (outline cut order).

## Fig 2 — `fig2_yardstick.pdf`, `figure` (C3)

```latex
\caption{\textbf{Rerun noise of the shipped KernelSHAP against variation practitioners already accept.}
For each instance, the disagreement between reruns of the explainer (mean pairwise $1-$ top-3 Jaccard over $R{=}20$ runs) is compared with the disagreement of the
\emph{exact} Shapley values across background resamples, across retrains that differ in the seed only, and across bootstrap retrains of the training set
(retrains within $0.01$ AUC of the audited model). Bars: share of instances where the rerun disagreement is smaller than (blue), equal to (grey) or larger than (orange) the reference; ties are mostly $0=0$.
Seed-only retraining of the logistic regression is deterministic, so that bar is absent. 30 instances per cell, seed 0.}
```

Reads: `yardstick_R20.csv` (`.json` has the shares per bar).
**Partial**: 4 of 6 cells (ACS LR/MLP/GBDT, German LR); German MLP/GBDT still running at `experiment-repo`. Rebuild before the caption is final; the "30 instances, seed 0" clause and the cell list change with it.
Colour wording matches the legend of the current build.

## Fig 3 — `fig3_certificates.pdf`, `figure*` (C4)

```latex
\caption{\textbf{In-run certificates are calibrated, and conservative.}
(a, b)~Calibration of the five certificates on fresh reruns, for the top-3 (a) and top-5 (b): $P(\text{top-}k\text{ of the delivered run is exact}\mid\text{certified})$
against the nominal level $1-\delta$, pooled over instances and seeds with 95\% cluster-bootstrap intervals; colour = rule, marker = dataset and model.
On the diagonal = calibrated; above = conservative; below = over-claims.
(c)~Power: share of runs certified by a coalition stage ($\times\tfrac14,\times1,\times4$ of the Covert--Lee schedule) against the share of instances an oracle that knows $r_3(x;B)$ would certify at that stage
($r_3\ge 0.9$, $R\approx 200$ reruns on 30 stratified instances per seed-0 cell; mean over the six cells, bars = range).
Below the diagonal = the certificate gives up power relative to the oracle.}
```

Reads: `certificate_coverage.csv`, `oracle_tightness.csv`. Final (Tier 1). (c) shares are conditional on the strata, not population rates; the caption says "stratified".
Appendix `figA_calibration_k135.pdf` (`figure*`): same panels (a, b) for $k=1,3,5$; caption: "Calibration of the certificates for $k=1,3,5$ (as Fig. 3a,b)".

## Fig 4 — `fig4_budget.pdf`, `figure` (C2)

```latex
\caption{\textbf{Reliability against budget: the shipped defaults, and the unbiased estimator that needs far more.}
Fraction of instances with $r_3\ge 0.9$ against the budget in coalitions relative to the shipped KernelSHAP default ($2d+2048$) of the same cell, one panel per dataset (three models, three seeds pooled; 95\% cluster-bootstrap bands).
Markers: shipped defaults (KernelSHAP at $\times1$; Permutation at its own 500 evaluations). Colour = explainer, fixed across figures.}
```

Reads: `tidy_*_R20.csv`. Final. Cut first if the page limit forces it (outline cut order); its content then moves to the appendix as `figA_budget_by_model.pdf` (`figure*`, "as Fig. 4 with one panel per dataset and model").
The bold heading is a neutral description; the claim sentence (what the curves show) is the paper's. The panels show: on German the shipped KernelSHAP default is still rising at x1, on ACS it is near its plateau; Covert--Lee is far below at every budget up to x16.

## Table 1 — `tab1_reliable_fraction.tex`, `table*` (C1 + C5)

```latex
\caption{\textbf{Reliability of single runs per explainer.}
$F_3$: fraction of instances with $r_3\ge 0.9$ (95\% cluster-bootstrap interval over seeds, then instances); mean $r_3$; Nogueira stability of the top-3 across reruns;
$F_3^{\epsilon}$ and mean $r_3^{\epsilon}$: the same with the $\epsilon$-tolerant top-3 ($\epsilon=0.1$); bias share: share of the unreliable instances whose \emph{mean} attribution over reruns already has the wrong top-3 (a repeatable but wrong explanation). The \texttt{l1\_reg=False} row is the paired variant.
Budget: the shipped KernelSHAP default ($2d+2048$ coalitions) for the KernelSHAP rows and Covert--Lee, $500$ for Permutation.
100 instances per cell, three model seeds, $R{=}20$ reruns.}
```

Reads: `tidy_*_R20.csv`. Final. Read off (check before quoting): shipped-default $F_3$ ranges 0.71 to 0.93 over the six cells, `l1_reg=False` paired 0.92 to 0.95, Permutation 0.72 to 0.91, Covert--Lee 0.29 to 0.41; the bias share of the default is 0.42 to 0.52 on German and 0.10 to 0.17 on ACS.

## Table 2 — `tab2_certificates.tex`, `table*` (C4)

```latex
\caption{\textbf{What certification costs and what it gives up} ($k{=}3$, $\delta{=}0.1$). Each cell is the range over the six dataset--model groups (per-group values in Table~\ref{tab:cert-cells}).
\emph{Certificate}: share of fresh runs certified at some stage of the seven-stage schedule; $P(\text{exact}\mid\text{certified})$; correct rate of the delivered run.
\emph{Against the oracle} (stage $\times4$; 30 stratified instances per seed-0 cell, $R\approx 200$; shares are conditional on the strata, not population rates):
share of oracle-certifiable instances the rule certifies, and share of the others it certifies.
\emph{Coalitions to reach the delivered rate}: this certificate, against the cheapest fixed budget on the grid whose pooled $P(\text{top-3 exact})$ reaches that rate,
for the same estimator, for KernelSHAP with \texttt{l1\_reg=False}, and for the shipped KernelSHAP default
($\le$ marks the grid floor; n/a: no fixed budget up to $\times16$ reaches the rate; counts of cells in parentheses).}
```

Reads: `certificate_coverage.csv`, `oracle_tightness.csv`, `cost_at_equal_reliability.csv` (column `comparison`). Final.
The oracle block is from the R~200 subset only. Appendix `tabA_certificates.tex` (label `tab:cert-cells` in the text) has the per-cell values; caption: "Per-cell values behind Table 2".

## Appendix

- `figA_bstar.pdf`, `figure`: "Required budget $B^*(x)$ per instance: predicted from $c\sigma^2/\mathrm{gap}^2$ ($c$ fitted per cell) against the smallest grid budget at which $r_3\ge 0.9$ (Covert--Lee, $k=3$, $\delta=0.1$). Instances not reliable by $\times16$ are censored there and drawn hollow. Spearman rank correlation over uncensored points in the legend." Reads `instances_R20.csv`; numbers in `figA_bstar.json`. Final for the Tier-1 cells.
- `fig2_yardstick_perm.pdf`, `figure`: "As Fig. 2, for the Permutation explainer." Same partial state as Fig 2.
- `figA_budget_by_model.pdf`, `figure*`; `figA_calibration_k135.pdf`, `figure*`; `tabA_certificates.tex`: see above.

- `figA_c5_split.pdf`, `figure`: "What the unreliable instances of the shipped KernelSHAP default are made of. Per cell group (three seeds pooled), the instances with $r_3<0.9$ at the shipped budget ($n$ in the labels) split by the \emph{mean} attribution of the default's reruns: wrong top-3 under the default but right under paired \texttt{l1\_reg=False} (truncation bias; 95\% cluster-bootstrap interval); wrong under both; right but the runs scatter (noise), split by the gap between the $3$rd and $4$th attribution against the rerun SD of that difference ($z_{\rm true}$ below / at or above 1; a descriptive threshold). Interval widths reflect small $n$ on ACS." Reads `c5_split_R20.csv`; shares in `figA_c5_split.json`. Only the six main groups are drawn (d-curve groups have n of 0 to 20 unreliable instances; Arrhythmia d=40 is 1 seed x 20 instances, preliminary). What the noise segments mean for budget is the paper's to state; the figure shows only the split.

## Not delivered (no item)

- E7 control, `cells_not_run` marking, k/eps/delta sensitivity: one sentence of text, from `e7_controls.csv`, `cells_not_run.csv`.
