# Exploratory development log

## 2026-11-03: before any training result

Read frozen `TASK.md`, `data.md`, `resources.md`, `deliverable.md` and `starter_literature.md` at `/initial-state/inputs/0/`. All decisions below are exploratory and precede confirmatory plan agreement.

Implementation chosen for a cheap pilot: all ordered pairs modulo prime 31, random 50% train fraction, full-batch AdamW, learning rate 0.001, weight decay 1.0, concatenated one-hot input, one ReLU hidden layer, widths 32/128/512, training for 2000 steps. Initial hidden matrix/bias use PyTorch Linear's default uniform initialization with fan-in 2p; output Linear uses its own default fan-in width. No embedding dimension changes with width. All parameters including biases decay. Fixed split seed 100 and initialization seed 200 across pilot widths. Evaluation every 100 updates includes step zero; no early stopping. This is a timing check and exploratory feasibility probe, not evidence for the final prediction. A 2000-step horizon may miss delayed generalization.

The exact one-hot affine operation is evaluated by gathering the two active weight columns. Independent forward and gradient equivalence checks passed. Fourier-template energy was checked with a compatible sinusoid (fraction one) and incompatible sinusoid (fraction zero). This is a functional alignment diagnostic, not a claim about a uniquely identified internal circuit.

The initial implementation check used PyTorch's default thread count and was unnecessarily slow under container CPU sharing. Future checks set one intra-op thread. Training sets one thread explicitly before work.

## After 2000-step timing pilot

Actual three-width timing is in `notes/timing-pilot.md`; raw files in `results/timing/`. Training fit occurred; no validation threshold was reached by the short horizon. Based only on cost and this censoring, expand the exploratory horizon to 20000 updates at ReLU widths 32/128/512 with decay 1; include width 128 decay 0.1 and width 128 GELU as regime-finding controls. Same exploratory seeds and fraction. No confirmatory hypothesis or grid is selected from these partial results yet. Two independent resource jobs will run the five pilots concurrently; each uses one PyTorch thread.

## After five completed full pilots

All five 20000-step exploratory configurations completed. Width512/decay1/ReLU crossed held-out 95% after a long delay, establishing an actual grokking regime. Width32/128, width128 decay0.1, and width128 GELU are right-censored for that event at 20000. See `notes/full-pilot-preliminary.md` and raw generated evidence. Exploratory seeds remain 100/200. No confirmatory grid, hypothesis test or seed has been run. The pending design request to story-repo includes actual costs and proposed censoring/regularization/symmetry/parameterization controls.

The idea-repo and venue-repo release listings were empty on first inspection, and their wiki remotes had no readable repository/page yet; no context Brief was available at that time. The objective and frozen supporting documents therefore remain the authoritative input. These supplies will be read when delivered.
