# Figure/table plan (working notes; not a delivery)

Claims from story-repo `plan/study-plan.md` §1. Result-file schema requested in world/experiment-repo#3.

| item | claim | shows | encoding |
|---|---|---|---|
| Fig A | Q1a, Q1b | optimism Δ = reported − θ(ĉ) vs n, by K; T0 (known truth) and T1 (real MMLU-Pro) side by side, theory curve overlaid | small multiples (T0 | T1), x = n log, y = Δ in accuracy points, colour = K, bands = 95% CI over replicates, dashed = theory; zero line |
| Fig B | Q1b | Δ by procedure, τ, leakage | panels per factor, same y scale as A; τ=0 worst case labelled |
| Table C / Fig C | Q2a, Q2b | bias, RMSE, coverage (± MC SE), width, item cost for M0–M5 | table with all cells; coverage figure with Wilson intervals and a 95% reference line, failure cells visible |
| Table D | Q1c, Q2a | false-claim rate and power per reporting method (naive included) | table + Wilson CI; marks the nominal 5% |
| Fig E | Q2b | live tool vs cached replay of the same search sets | paired scatter/difference plot, identity line; "not completed" if T2 does not run |
| Table F | all | compute actually used | from compute.csv |

Rules: every estimate carries an interval, and the caption states its type and the replicate count; T0/T1/T2 are labelled as different evidence; claim id in each caption; colour-blind-safe palette; vector PDF at the venue's column width (waiting on venue-repo).
Generators: `figures/<name>.py`, `tables/<name>.py`, reading only `results/` from experiment-repo.
