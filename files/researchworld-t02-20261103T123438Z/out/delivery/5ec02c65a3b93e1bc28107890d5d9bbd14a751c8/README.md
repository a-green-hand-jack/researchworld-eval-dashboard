# Model width and delayed modular generalization

The complete study is in [paper.pdf](paper.pdf), with [LaTeX source](manuscript/main.tex), all code and raw evidence. It tests a falsifiable explanation of model width and delayed generalization on synthetic modular arithmetic using 204 registered CPU runs. A world release requires independent approval of the exact version PR into `final`; a candidate on `main` is not yet that release.

Under the main addition-modulo-31 recipe, onset counts increase from 0/12 at width 32 to 12/12 at width 512, and the endpoint restricted-onset contrast is −43800 updates (95% paired interval [−44150, −43433]). Substantial delay persists at width 512. The frozen-feature fit gate fails, leaving the complete explanatory account unresolved. Learning rate, decay, split, event definition, operation and compute budget qualify the size relationship; no universal size law or unique mechanism is claimed.

| Material | Entry point |
|---|---|
| Paper, sources, build | [paper.pdf](paper.pdf), [manuscript/](manuscript/README.md), [build instructions](build/README.md) |
| Exact candidate review inventory | [manuscript/review-inventory.md](manuscript/review-inventory.md), [display inventory](manuscript/display-inventory.json), [claim sources](manuscript/claim-evidence.json) |
| Protocol, predictions, ownership | [plan/protocol.md](plan/protocol.md), [plan/artifact-contract.md](plan/artifact-contract.md), [plan/division.md](plan/division.md) |
| Complete experimental evidence and reproduction | [reproduction/README.md](reproduction/README.md), [final results and limits](reproduction/final_results.md), [environment](environment/environment.json) |
| All figures, tables and four CSV companions | [presentation/README.md](presentation/README.md), [manifest](presentation/manifest.json) |
| Completed actual-access provenance | [final cutoff](reproduction/final-access-consolidation.md), [exact originals](reproduction/final-access-consolidation.json) |
| Official NeurIPS 2026 rules and assets | [venue/README.md](venue/README.md) |

Run `make paper`, `make audit`, and `make inventory` from the root. The current PDF has eight content pages, references beginning on page 9, supporting appendices, and all 16 answered official checklist questions. The former incomplete reading copy has been retired; dated inspection/preparation records remain historical evidence.

Data are exhaustive synthetic operation tables generated in memory; no external dataset download is needed. The package retains seeds, configurations, curves, terminal states, attempts, failures, recovery records, uncertainty and source hashes. All 204 registered runs completed, while one recovered run has unavailable CPU100 accounting. Recorded known-component CPU cost is a lower bound. Actual access histories and permitted citation scopes are retained; the prohibited prior study was not sought, and no exhaustive novelty audit is asserted.
