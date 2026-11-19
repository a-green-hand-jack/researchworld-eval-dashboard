# Run status (update on every push)
| grid | claim | state |
|---|---|---|
| e1 | C1 iid slice, n x d x p x sigma (ER, R=400) | done (R=400, 150 cells; sandwich not run in 6 cells with n(d+1)^2 > 3e7) |
| e1b | C1 across graph families | done (R=300) |
| e2 | C2 bias vs exact projection, kappa x shape x p x d x sigma (R=200) | done (R=200, 320 cells) |
| e2b | C2 plateau in n | done (R=200) |
| e3 | C3 regression vs HT crossover | done (R=300; HT exact) |
| e3c | C3 relaxed Hajek at delta 0.1/0.25/0.5/0.75, same draws as e3 | done |
| e4 | C4 collapse across graphs (pilot-size, R=200) | done (R=200, 261 cells; sandwich not run in the 9 Stanford3 q=1 cells) |
| e5 | C7 GCR cluster scale | done (R=150, 112 cells; Hájek-relaxed not run under GCR) |
| e6 | C5 mechanism x method map | done (R=100, 60 cells, 6000 rows; GCN not run on Stanford3 (n = 11586), 10 cells fewer; F10) |
| e12 | C6 D4 degree transport (PREREG addendum, fixed before the cells were generated) | done (R=100, 132 cells, 13 200 rows; F12; bootstrap intervals not recomputed) |
| e11 | H4/C5 observed-graph error q x interference range | done (R=100, 80 cells, 8000 rows; F11) |
| e7 | C6 diagnostic, interval (pre-registered; R=120) | done (R=120, 480 cells, 57 600 rows; F9) |
| e8 | C7 staggered rollout at matched measurements | done |
| e9 | C1/C6 standard errors as n grows (iid, HC2, HC3, sandwich, CRVE, resampling) | done (R=100, 48 cells) |
| e10 | design-only variance (assignment redrawn only), same standard errors | done (R=500, 128 cells) |
