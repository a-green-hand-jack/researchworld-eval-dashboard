# Complete-study review inventory

Root PDF: [paper.pdf](../paper.pdf), SHA256 `c56f56dd6d2e26bc388e8fa1ccfb1954e7262edb4a006a19af8552302bf95d94`. The exact candidate commit is the head recorded in its version PR and review comments; a file cannot contain its own commit hash. [Machine-readable inventory](review-inventory.json) pins the paper sources and evidence entrypoints. This is a complete study candidate; owner inspections and exact-head independent acceptance remain separate.

Build with `make paper`, `make audit`, `make inventory` from the delivery root. Source: [main.tex](main.tex), [checklist.tex](checklist.tex), all [section sources](sections/README.md), and [references.bib](references.bib). Official assets and requirements are under [venue/](../venue/README.md). The actual PDF has eight content pages, references on page 9, appendices on 10–28, checklist on 29–35. It includes all 16 unchanged questions with answers. [Final inspection](../build/final-inspection.md) records the original report checks; [owner integration](../build/final-owner-integration.md) records completed presentation/venue inspections and unchanged inspected PDF identity.

| Compiled display | PDF page | Artifact |
|---|---:|---|
| Table 1 | 4 | [tables/main_outcomes.tex](../tables/main_outcomes.tex) |
| Figure 1 | 5 | [figures/width_summary.pdf](../figures/width_summary.pdf) |
| Figure 2 | 7 | [figures/scope.pdf](../figures/scope.pdf) |
| Figure 3 | 14 | [figures/frozen_interaction.pdf](../figures/frozen_interaction.pdf) |
| Figure 4 | 15 | [figures/learning_example.pdf](../figures/learning_example.pdf) |
| Figure 5 | 16 | [figures/loss_example.pdf](../figures/loss_example.pdf) |
| Figure 6 | 17 | [figures/main_clocks.pdf](../figures/main_clocks.pdf) |
| Figure 7 | 18 | [figures/efficiency.pdf](../figures/efficiency.pdf) |
| Figure 8 | 18 | [figures/cpu_clocks.pdf](../figures/cpu_clocks.pdf) |
| Table 2 | 19 | [tables/efficiency.tex](../tables/efficiency.tex) |
| Figure 9 | 20 | [figures/functional_diagnostic.pdf](../figures/functional_diagnostic.pdf) |
| Table 3 | 20 | [tables/terminal_outcomes.tex](../tables/terminal_outcomes.tex) |
| Figure 10 | 21 | [figures/threshold_sensitivity.pdf](../figures/threshold_sensitivity.pdf) |
| Table 4 | 22 | [tables/sensitivity.tex](../tables/sensitivity.tex) |
| Table 5 | 23 | [tables/attempt_inventory.tex](../tables/attempt_inventory.tex) |
| Table 6 | 24 | [tables/scope_outcomes.tex](../tables/scope_outcomes.tex) |
| Table 7 | 25 | [tables/scope_contrasts.tex](../tables/scope_contrasts.tex) |
| Table 8 | 26 | [tables/decay_pairs.tex](../tables/decay_pairs.tex) |
| Table 9 | 27 | [tables/split_diagnostics.tex](../tables/split_diagnostics.tex) |
| Table 10 | 28 | [tables/multiplication_subsets.tex](../tables/multiplication_subsets.tex) |

All twenty displays have source/hash/page identities in [display-inventory.json](display-inventory.json); [presentation/manifest.json](../presentation/manifest.json) maps each to actual input hashes, generator and exact command. The four separately delivered CSV companions are:

- [tables/main_delays.csv](../tables/main_delays.csv) — SHA256 `95177796236f337adf918eabeac2d87356371e76c274586430272d30fcb905c8`
- [tables/cpu_clocks.csv](../tables/cpu_clocks.csv) — SHA256 `6ba9d111200a42003cd1f73741376e7e14326d4f11a2463aab3ca4ab5bf6a606`
- [tables/multiplication_subsets.csv](../tables/multiplication_subsets.csv) — SHA256 `04ee15d1e9f2c259a8f64d9c17321f61ffdefb02e40bd6ee9efc59e047c8bd48`
- [tables/scope_sensitivity.csv](../tables/scope_sensitivity.csv) — SHA256 `ad0e51efcaf01af17fb79e751f34d2d53205352aa9dd293cde6dda87d2a2c0f9`

Scientific provenance: [final_results.md](../reproduction/final_results.md) gives the complete analysis handoff and limits; [final-study-summary.json](../results/final-study-summary.json) selects exact supplied fields with source hashes. [claim-evidence.json](claim-evidence.json) maps report numbers/definitions to original sources. [protocol](../plan/protocol.md) retains prospective predictions, gate and fixed design. Analysis PR#32 and presentation PR#33 supply their owners' complete namespaces.

The [raw manifest](../results/manifest.json) enumerates actual curve/state/summary/attempt files and hashes; [runs.json](../results/confirmatory-analysis/runs.json) indexes all 204 registered inputs. [cells.json](../results/confirmatory-analysis/cells.json), [matched first-eight cells](../results/confirmatory-analysis/cells-first8.json), [predictions.json](../results/confirmatory-analysis/predictions.json) and [all thirteen sensitivities](../results/sensitivity/sensitivity.json) preserve counts, pairing, censoring, onset/terminal success and uncertainty. The [complete audit](../results/registered-audit.json), [owner verification](../reproduction/checkpoints/final204-verification.json), and [report bundle check](../build/final-bundle-verification.json) retain distinct verification scopes.

Reproduce from [reproduction/README.md](../reproduction/README.md), [environment/environment.json](../environment/environment.json) and [requirements.txt](../environment/requirements.txt). Training is [code/src/train.py](../code/src/train.py), grid execution [run_grid.py](../code/scripts/run_grid.py), and raw-to-derived complete pipeline [finalize_analysis.py](../code/scripts/finalize_analysis.py). No external dataset download is needed. All seed/config/run commands and actual per-cell runtime records are supplied. [run_inventory.csv](../reproduction/run_inventory.csv) retains every recorded attempt; [numerical audit](../reproduction/numerical_audit.md) and [resource accounting](../reproduction/final-resource-accounting.json) preserve failures, recovery, missing CPU and known lower-bound costs. [presentation/README.md](../presentation/README.md) gives every display-generation command.

Access/citations: [citation-record.json](citation-record.json) records actual permitted PDF versions/hashes/read scopes, [access-record.md](access-record.md) later report accesses, and [reproduction/access_log.md](../reproduction/access_log.md) owner-attributed consolidation with date-scoped originals. The completed [final access cutoff](../reproduction/final-access-consolidation.md) and [eleven-original inventory](../reproduction/final-access-consolidation.json) preserve all actual substantive owner inspections; [integration/R1 response](../build/final-provenance-integration.md) verifies their exact transfer. No withheld-work identification or exhaustive novelty search is asserted. No internal-review or external-review repository code was read.

Completed owner inspections: [presentation inclusion/captions](../presentation/integrated-final-inspection.json) and [venue compliance](../venue/inspection/2026-11-07.md) require no corrections for this exact PDF. PRs#37/#38 integrate their records; no PDF or caption changed. The reviewer has supplied its completed substantive-review access cutoff via internal-review#6 (source `4a899a77afd9713e5b38de84fbbcc3fe7ecbccdd`), reports no scientific/format correction, and reserves formal acceptance for the integrated final head. That provenance is relayed intact through paper#36. Final provenance PR#40 is merged and resolves the reviewer's sole requested change R1. All eleven exact originals/sidecars, earlier histories and the substantive review cutoff are integrated. The remaining required judgement is internal-review's formal exact-head approval of final PR#39. Later metadata-only identity/acceptance records do not require another provenance acknowledgment cycle. External-review has no concrete released-version problem open: its readable issue list has only the objective and review commitment, and no release exists yet. Its absent wiki endpoint is not treated as an approval.

Scientific/operational limitations are results, not unfinished experiments: P3 fails the fit gate; noncrossings and degenerate restricted contrasts do not locate eventual events; secondary intervals are pointwise; CPU100 is unavailable for one recovered run; compute is a recorded lower bound. The existing-asset license checklist is honestly No; agent involvement is disclosed and review is not claimed as human validation.
