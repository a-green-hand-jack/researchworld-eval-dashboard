# Results (377 graphs, 13 families)

## A. Leave-one-family-out (LOFO) generalisation, pooled over held-out predictions
| predictor | median factor [95% CI] | 90th pct factor | within x1.25 | frac over-predicted |
|---|---|---|---|---|
| bound 2m(n-1) | 6.09 [5.21, 7.17] | 37.31 | 0.00 | 1.00 |
| scaled bound kappa*2m(n-1) | 2.46 [2.17, 2.69] | 6.84 | 0.12 | 0.49 |
| logm,logn | 1.64 [1.56, 1.70] | 2.44 | 0.20 | 0.66 |
| logm,logn,logdiam,logdmax | 1.28 [1.26, 1.30] | 1.59 | 0.41 | 0.47 |
| Matthews h_max*H_(n-1) (reference, needs hitting times) | 1.53 [1.34, 1.72] | 3.34 | 0.39 | 0.97 |

## B. Random 10-fold CV, repeated 20 times (mean of per-repeat medians)
| predictor | median factor (CV) | within x1.25 |
|---|---|---|
| scaled bound kappa*2m(n-1) | 2.23 (sd 0.016) | 0.14 |
| logm,logn | 1.47 (sd 0.009) | 0.25 |
| logm,logn,logdiam,logdmax | 1.19 (sd 0.003) | 0.66 |

## C. Per-family LOFO median factor (predictor: logm,logn,logdiam,logdmax)
| family | count | median factor | within x1.25 | bound 2m(n-1) median factor | Matthews median factor |
|---|---|---|---|---|---|
| barbell | 28 | 1.11 | 0.82 | 4.14 | 3.08 |
| bipartite | 30 | 1.21 | 0.60 | 31.57 | 1.10 |
| complete | 30 | 1.31 | 0.00 | 89.05 | 1.00 |
| cycle | 30 | 1.38 | 0.13 | 4.00 | 1.84 |
| gnp | 23 | 1.33 | 0.35 | 21.72 | 1.78 |
| grid | 30 | 1.51 | 0.03 | 7.00 | 1.92 |
| hypercube | 30 | 1.28 | 0.40 | 8.11 | 1.21 |
| lollipop | 30 | 1.56 | 0.37 | 2.84 | 3.88 |
| path | 30 | 1.20 | 0.87 | 1.74 | 2.99 |
| random_tree | 30 | 1.16 | 0.77 | 2.26 | 2.30 |
| regular | 26 | 1.17 | 0.62 | 14.70 | 1.32 |
| star | 30 | 1.59 | 0.00 | 5.08 | 1.02 |
| wheel | 30 | 1.25 | 0.47 | 12.58 | 1.14 |

## D. Full-data fit, logm,logn,logdiam,logdmax: log C = b0 + b1 log m + b2 log n + b3 log diam + b4 log dmax
coefficients: -0.521, 0.141, 0.514, 1.327, 0.803
in-sample R^2 (log scale): 0.9630; residual sd 0.250

## E. Where it fails: worst LOFO graphs (top 8 by |log error|)
| family | n | m | diam | dmax | C_mc | predicted | factor |
|---|---|---|---|---|---|---|---|
| lollipop | 28 | 327 | 3 | 26 | 1231.0 | 298.8 | 4.12 |
| lollipop | 28 | 258 | 6 | 23 | 2429.6 | 601.3 | 4.04 |
| lollipop | 26 | 256 | 4 | 23 | 1405.8 | 357.6 | 3.93 |
| lollipop | 25 | 214 | 5 | 21 | 1581.0 | 418.9 | 3.77 |
| lollipop | 22 | 211 | 2 | 21 | 419.4 | 134.1 | 3.13 |
| lollipop | 22 | 141 | 6 | 17 | 1215.1 | 402.3 | 3.02 |
| lollipop | 16 | 81 | 4 | 13 | 437.4 | 162.9 | 2.69 |
| gnp | 30 | 200 | 3 | 18 | 136.7 | 335.2 | 2.45 |

Monte Carlo: median relative SE of C_mc = 1.32%, max = 3.87%
