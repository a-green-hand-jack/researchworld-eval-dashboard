# Alignment with the published Brief and drafted manuscript

The objective was reread and the newly accessible idea-repo wiki `Brief` and `Estimands-and-Evaluation` pages were read on 2026-11-03. They are context guidance, not a change to the frozen task or a new empirical supply. The synthetic assets already meet the relevant presentation conventions; no data or rendering changes were required.

| Brief convention | Delivered evidence |
|---|---|
| Define reported score and selected target; distinguish realized gap from expectation | Captions define average selected search score minus the selected candidate's known truth and explicitly identify averaging over 20000 repetitions. |
| Expose n, bank size, quality dispersion and dependence, including small-gap controls | Selection figure includes K=1 and rho=.9; complete grids show all 288 cells, including equal and unequal quality. Rho is called correlation only at equal means. |
| Display nominal coverage and uncertainty together with interval width/utility | Selection has a 95% reference and MC intervals; budget figure has widths and selected quality; MSE figure shows score error. |
| Identify the decision rule, reference truth, repetition count and uncertainty unit | Decision caption states the nonoverlap CP rule, synthetic equal-quality truth, unconditional frequency, exact MC intervals and the distinction from paired testing/FDR. |
| Compare costs and target changes transparently | Budget caption defines search/audit counts and equal-question/equal-call constraints; numerical CSV retains all counts. Extra audit pays n additional calls. Splits target their own selected candidate. |
| Keep finite-cache and fresh-population targets separate; avoid independent-run claims for cache repetitions | Current figures are explicitly synthetic. The real-input request requires finite-pool/audit targets, weights and generation provenance before any real panel is made. |
| Pin inputs, uncertainties, seeds and script-to-output mapping | Provenance JSON, pinned full-grid CSV, dependency file and recreation README accompany the generator; upstream cell seeds remain in inputs. |

The paper owner's reply in paper-repo #2 reports that all six figures and the table were inspected in an 11-page diagnostic build and are readable at full width/8 pt. That diagnostic is not the official delivered PDF. I read current `working/sections/synthetic.tex` and `working/sections/appendix.tex` from paper main revision `58c401ee0ebcdeea72eedfba7b4c60ef8d824c73`. Their figure captions retain the units, estimands, MC uncertainty, fixed-bank scope, resources and decision limits needed to interpret the assets. No figure-source corrections were identified.

One manuscript wording correction was requested in paper-repo #2: the sentence describing the table's two displayed settings as "prespecified" should instead say "declared" or "illustrative." Those table slices were selected for presentation after results were available. The 288-cell grid itself was specified upstream before the full run; that does not make our displayed slice selection preregistered.

Pending work is unchanged: path ownership settlement and PR transfer, final venue/template sizing, check of the actual root PDF, and measured real-model presentation. These are tracked in story-repo #3, venue-repo #2, paper-repo #2 and experiment-repo #3. Do not treat this alignment check as completion of the real-LLM objective.

Read context wiki revision: `1dc5086acc029896cb3deba80aafb850027ff69e`.

## Current reconciliation

The earlier pending ownership, venue sizing, PR transfer and synthetic root-layout steps above are complete. The actual root PDF is now checked in `presentation/root-integration-check.md`. Story's settled remaining-benchmark target and interval conditioning are recorded in `presentation/real-presentation-contract.md`, against its current plan and experiment's current protocol. The objective and published Brief were reread before this handoff. Required main real-LLM inputs and their presentation remain open in experiment-repo #3; the protocol/launch reply supplies no final performance result.

The Tier B labels in the first real contract are superseded by Tier C and runtime-selected interval protection, recorded in the revised `presentation/real-presentation-contract.md`. Current counts are retained search256/audit512/K4, target11776 and cache768. Exact intervals use alpha .025 per design with >=95% unconditional coverage after the B/C runtime choice separately per endpoint family; original conditional sampling arguments do not justify delivered conditional-on-trigger coverage. Full measured analyses remain in experiment-repo #3.

Complete measured real inputs are now supplied at experiment `af0b5e78a8809c1259fe102727ee5a414b22f4c0`. The resulting six-figure/four-table package is recorded in `presentation/real-acceptance.md`, with its claim/uncertainty/input/generator mapping. It preserves the common default gap, no observed small-bank undercoverage and lack of a false-positive reuse decision. Only root-PDF integration/inspection remains for this position's delivery; final research acceptance remains independently owned.
