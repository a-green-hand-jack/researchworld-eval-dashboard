# Executed main presentation handoff

Rendered on 2026-11-05 from analysis revision
`c291b715fcfed90d5b5905e2d7a8e1f721937616`, source/config signature
`8369b51bd944ea510afbc5a372f17d1c7f28f15a6a08d9c242bf6b3effaaef26`.
The complete analysis has 97,200 calls, 540 exact references, 9 fitted cells,
60 inputs/condition and 30 repeats/input. This is a main-result delivery;
the archived initial pilot remains a separate diagnostic.

## Recommended use in the report

Main body: `one_run_budget.pdf` plus `error_repeatability.pdf` show adequacy
versus actual work and distinguish two-run disagreement from reference error.
`budget_cpu.pdf` is the CPU companion; choose body/appendix placement to meet
the page limit. `tables/primary_rates.tex` gives every lowest-budget condition
with its exact supplied intervals/costs, and the all-success highest-budget
observation with its inference limit. Use `tables/study_coverage.tex` for
predictive quality and actual training/test/player counts.

Appendix: `conditions_{german,acs,diabetes}.pdf` shows reference-defined strata;
`metric_sensitivity_DATASET.pdf` shows cutoff/selection/floor dependence;
`accuracy_components_DATASET.pdf` distinguishes magnitude/selection components
and absolute probability-unit error; `instance_distribution_DATASET.pdf`
preserves individual-input heterogeneity. `tables/reference_assessability.tex`
reports caution counts without multiplying repeated reference counts;
`tables/main_compute.tex` reports actual process/reference costs and memory.
`budget_time.pdf` preserves recorded wall-time positions with explicit severe
interruption caveats. It is not a deployment-latency comparison.

All numerical conditions are retained in the supplied analysis tables. No
method superiority at equal cost follows from nominal budget labels. Every
highest-budget primary rate is observed 1, but its displayed boundary interval
is [0.824670,1] and none certifies a population mean >=0.95. Strict signed-top3
recovery still varies. There are no low-signal inputs; all reference norms
exceed .05, so the three floor scenarios coincide. Empty low-signal strata
are untested, not negative findings. The near-tie strata are sparse and their
intervals are descriptive. Mean-of-30 vectors remain analysis-owned auxiliary
evidence with 30-call cost; they are not plotted as one-run explanations.

## Reproduction and inclusion

From the delivered paper root (with analysis PR #16 results/config present),
run `bash figures/reproduce_main.sh`. Inputs are the analysis-owned results
and `analysis/configs/main.json`; no experiment is rerun. Renderers do not
fit models, calculate new confidence intervals, exclude inconvenient inputs
or change adequacy definitions. Source hashes, CSV lines, keys, denominators,
interval labels, generator and output hashes accompany every output in its
manifest. The script ends with source/output hash, width and font checks.

The fixed-background inventory has 16 broad/companion figure PDFs plus the
compact criterion/input contrast, and four LaTeX tables. The completed
background supplement adds two figure PDFs and one table: 19 one-page
5.5-inch figures and five numerical tables in total, all with previews,
plain caption sources and executable generators.
Use `\includegraphics[width=\linewidth]{figures/NAME.pdf}` and keep figure
captions below. Captions are plain text (`NAME.caption.txt`); paper owns proper
LaTeX escaping and optional short-caption wrappers. A caption must retain its
metric, fixed-game scope, independent n, interval switch and claim limits.
Tables have their own float/caption/label; include with
`\input{tables/NAME.tex}` and load `booktabs`. Preview PDFs use a 5.5-inch text
block and are inspection artifacts, not manuscript includes.

`figures/inspection.md` records opened outputs and checks. Paper owns final
placement and caption integration; final root-PDF inspection remains required.
The separate changed-background arm is now included below. Requests #2/#4
remain open through integrated root-PDF output inspection.


## Completed supplement and compact main contrast

`criterion_instance_contrast.pdf` supports the requested compact main-text
contrast: high-budget strict signed recovery across all nine fitted cells and
an ACS RF lowest-budget ECDF highlighting an observed 0/30 input. Its caption
keeps broad-event observed success distinct from exact signed recovery and
from a per-input probability certificate. It uses the original complete-main
revision; its primary/strict and input records are mapped explicitly.

`background_sensitivity_{acs,diabetes}.pdf` uses separate analysis revision
`5d8d8e37ed7868e8d088315688c0843678abee55`: 144 exact changed targets and
5,760 calls, 12 retained main inputs/model, 20 runs/estimator at the middle
budget, and one training-background draw each at B8/B128. Top and middle rows
compare the exact changed target with B32 (normalized shift and top1 match);
bottom row measures estimator accuracy against the changed game's own exact
target. These are separate objects and are not pooled with fixed-B32 runs.
B32 is a comparison target, not population truth. Size and row sample change
together, so this is not a pure-size or background-variance estimate.

`tables/background_compute.tex` reports six phase-timer/memory rows, excluding
imports/bundle/data loading. It preserves the 18 captured compatibility notices
and zero failures, and cannot be added to overlapping reference/call costs.
The background figures, table and code are checked and opened as recorded in
inspection.md. The reproduction wrapper now includes both the compact contrast
and background supplement; preview compilation covers all five tables.


## Integrated presentation acceptance

All assets and caption semantics were accepted in the actual 48-page root PDF
at paper revision `8aa79e935dae75d9fdcc3be7b9f290d9c16692a1` after opening
every placed figure/table page. `figures/inspection.md` records the PDF hash,
26 inspected pages, asset-specific checks and passing provenance/width/font
audit. Earlier pending-placement statements above describe handoff history;
requests figtab-repo#2/#4 and commitment #3 are now fulfilled for this revision.
Later changes to assets, captions or placement require a targeted recheck.
