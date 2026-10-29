# Results summary

Graphs: 236 (n in [4,30]), MC walks per graph: 2000.

Monte Carlo relative standard error: median 0.0117, max 0.0279.

Validation vs exact (n<=8, 28 graphs): max |MC-exact|/exact = 0.0249; all within 3 SE: True.

Ratio C / (2m(n-1)): median 0.173, min 0.007, max 0.593.


## Repeated 5-fold CV (20 repeats)

| predictor | median APE | 95% bootstrap CI | 90th pct APE |
|---|---|---|---|
| scale: kappa*n*m | 0.593 | [0.535, 0.664] | 3.163 |
| scale: kappa*m*diam | 0.357 | [0.296, 0.439] | 0.907 |
| scale: kappa*n*m*diam | 0.486 | [0.414, 0.556] | 1.651 |
| loglin: n,m,diam | 0.310 | [0.237, 0.379] | 0.744 |
| loglin: n,m,diam,dmax | 0.163 | [0.151, 0.178] | 0.461 |
| bound 2m(n-1) (no fit) | 4.786 | [3.913, 5.612] | 23.136 |

## Leave-one-family-out

| predictor | median APE | 95% bootstrap CI | 90th pct APE |
|---|---|---|---|
| scale: kappa*n*m | 0.634 | [0.586, 0.707] | 3.316 |
| scale: kappa*m*diam | 0.392 | [0.327, 0.478] | 1.081 |
| scale: kappa*n*m*diam | 0.518 | [0.431, 0.574] | 1.786 |
| loglin: n,m,diam | 0.374 | [0.286, 0.456] | 0.903 |
| loglin: n,m,diam,dmax | 0.229 | [0.207, 0.260] | 0.574 |
| bound 2m(n-1) (no fit) | 4.786 | [3.961, 5.656] | 23.136 |

Per-family median APE under LOFO (loglin n,m,diam vs bound):

| family | count | loglin APE | scale n*m APE | bound APE | median C/bound |
|---|---|---|---|---|---|
| barbell | 16 | 0.150 | 0.387 | 3.852 | 0.206 |
| bipartite | 22 | 0.215 | 2.354 | 17.036 | 0.056 |
| complete | 9 | 0.213 | 7.049 | 42.639 | 0.023 |
| cycle | 14 | 0.394 | 0.328 | 2.994 | 0.250 |
| gnp | 24 | 0.509 | 1.742 | 13.795 | 0.072 |
| grid | 27 | 0.800 | 0.234 | 5.099 | 0.164 |
| lollipop | 23 | 0.701 | 0.592 | 1.727 | 0.367 |
| path | 27 | 0.048 | 0.730 | 0.736 | 0.576 |
| regular3 | 8 | 0.637 | 0.917 | 9.730 | 0.093 |
| regular4 | 8 | 0.739 | 1.959 | 15.561 | 0.060 |
| special | 3 | 0.595 | 0.642 | 7.883 | 0.113 |
| star | 27 | 0.684 | 0.210 | 3.798 | 0.208 |
| tree | 14 | 0.213 | 0.556 | 1.565 | 0.390 |
| wheel | 14 | 0.118 | 1.194 | 11.061 | 0.083 |

## Full-data fits (all graphs)

- scale: kappa*n*m: kappa = 0.3279
- scale: kappa*m*diam: kappa = 1.0326
- scale: kappa*n*m*diam: kappa = 0.0590
- loglin: n,m,diam: coefficients [-0.362, 1.123, 0.29, 0.731] (intercept, then log-features)
- loglin: n,m,diam,dmax: coefficients [-0.433, 0.505, 0.108, 1.333, 0.824] (intercept, then log-features)
