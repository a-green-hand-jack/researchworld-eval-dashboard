# Figure generation and provenance

## Executed pilot diagnostic

`pilot_budget_accounting.pdf` and its PNG preview present **pilot work
accounting only**. They are not evidence of main-study SHAP reliability. The
plot shows all 72 measured calls (two pilot inputs, three fitted models, two
estimators and two nominal budgets on three datasets); coincident model traces
overlap. Exhaustive Kernel cells are hollow; old permutation cache-coverage
flags are deliberately not interpreted as exactness. No reliability statistic
or uncertainty interval is computed from this pilot.

Generate both this plot and `tables/pilot_call_costs.tex` from the repository
root with:

```sh
python3 figures/generate_pilot_accounting.py --preview
```

Input is the unchanged committed analysis JSONL at `inputs/pilot.jsonl`.
`inputs/pilot-source.json` pins its analysis revision, original path and SHA-256.
The generator validates the full pilot grid, stages, configuration and data hash.
Output manifests map panels/table rows to actual JSONL line numbers, source
columns, formatting, generator and output hashes. The plotting helper is
`rendering.py`; it performs no statistical inference. This snapshot is included
so reproduction does not depend on a mutable external checkout. Future main
study outputs are separate inputs/assets, not extensions of these pilot points.

Figure include (paper owner controls float placement and numbering):

```tex
\begin{figure}[tb]
\centering
\includegraphics[width=\linewidth]{figures/pilot_budget_accounting.pdf}
\caption[Pilot requested and actual prediction work.]{\input{figures/pilot_budget_accounting.caption.tex}}
\label{fig:pilot-budget-accounting}
\end{figure}
```

The table already includes its caption, label and float environment; use
`\input{tables/pilot_call_costs.tex}` with `booktabs` loaded. This is suitable
for a computational-budget/validation appendix, not the main reliability
comparison. The 2048 pilot settings differ from the dimension-specific candidate
main grids precisely because some pilot calls exhausted the small games.

Rendering versions actually used: Python 3.11.2, Matplotlib 3.11.2 (bundled
STIXGeneral), pdfTeX 1.40.24 / TeX Live 2022, poppler `pdftoppm`, and PyMuPDF
for independent inspection. Python plotting depends only on Matplotlib and the
standard library; `--preview` additionally needs `pdflatex`, `times`, `booktabs`,
`geometry` and `pdftoppm`. The script uses installed CPU tools, no network or
experiment rerun. Rendering completed in under a minute here, a descriptive
reproduction expectation rather than a benchmark measurement.

The figure is 5.5 by 2.7 inches, with embedded TrueType fonts; the table preview
uses a 5.5-inch text block and embedded Type 1 fonts. `inspection.md` records
actual output inspection. Pilot placement in root main.pdf was reinspected and accepted on pages 7/8 at
paper revision eadf0096245664b5d1f1b94fc79a801cb65d8c29; see inspection.md.
Recheck after subsequent layout changes. Numerical main-study figure/table work remains open
in figtab-repo issues #2/#4 and experiment-repo issue #4.


## Main renderer prepared from the final evidence contract

`generate_main.py` binds to the analysis-owned result schema at
`de214716c29b7186c005e22f03da2ed4b92674e9`. It has not been run on main results,
which were unavailable when this code was prepared. It must not be treated as
an executed artifact. Python syntax/import/CLI checks have passed; rendering
and visual acceptance wait for actual results.

The intended command takes the delivered analysis-owned frozen JSON config,
complete results directory and verified full analysis revision as arguments:
`python3 figures/generate_main.py --results results --config PATH_TO_FROZEN_CONFIG
--analysis-revision FULL_ANALYSIS_REVISION`. Supply actual paths/values from the
handoff; no placeholder configuration or measurement is bundled.

The code prepares adequacy versus actual mean prediction rows, adequacy versus
actual mean wall seconds, and same-reference-denominator run error versus
independent-run disagreement. It reads supplied `ci_low/high`, never raw
bootstrap endpoints in their place, retains boundary-adjustment/interval labels
and denominators in panel provenance, and labels conservative observed-boundary
intervals distinctly. It makes no population >=.95 certification or individual
reliability claim. Plain text caption sources are passed to the paper owner for
LaTeX integration, not blindly included as unescaped TeX.

The script refuses partial/debug manifests, nonfrozen configs, changed primary
definitions, missing metric instances, changed repeat counts, nonexact reference
records, incomplete raw run-status denominators and exhaustive calls needing
explicit annotations. The latter is a deliberate handoff check: if any primary
cell contains exhaustive calls, adapt the plot/caption to mark them before
rendering. Prepared companion code for conditions, component/threshold/floor sensitivities
and per-instance heterogeneity is described below. Final numerical rendering
and visual checks still depend on the validated main handoff.
Required main-renderer packages: Matplotlib, NumPy, pandas and a pandas Parquet
engine (PyArrow in this environment), with actual versions recorded on execution.


## Diagnostic renderers prepared, not executed on main results

`generate_diagnostics.py` consumes the same frozen configuration and complete
main evidence as `generate_main.py`, plus `stratified_metrics.csv`,
`floor_sensitivity.csv` and `instance_success.csv`. Use the same three CLI
arguments (`--results`, `--config`, `--analysis-revision`). It requires the
analysis source identity, not a figure-repository revision. No numerical output
from this code is currently delivered. Syntax, import, CLI and absent-evidence
gates were checked; actual rendering and inspection remain required.

For each dataset it prepares four companion views, with fitted-model columns:

- `conditions_DATASET`: the prespecified near-top1-gap and low-signal strata,
  across all three requested budgets, with stratum n visible. Empty strata stay
  unavailable; singleton estimates have no interval. Requested labels do not
  claim equal actual work. All main event cases remain in their strata.
- `metric_sensitivity_DATASET`: error cutoffs .10/.20/.40, primary/strict/tie-aware
  signed selection, and floors .001/.01/.05. Each row explicitly changes one
  convention; floor .01 and signed two-of-three at .20 remain primary. The same
  calls supply these correlated scenarios, not independent comparisons.
- `accuracy_components_DATASET`: magnitude-only versus joint pass probabilities,
  mean unsigned/signed top3 overlaps, and unnormalized absolute L1 error.
  Overlap means are not mislabeled as success probabilities. Error uses
  probability units and a common within-row scale across fitted models.
- `instance_distribution_DATASET`: ECDFs of the supplied observed successes/30
  per input, retaining endpoint masses and all budgets. The ECDF describes
  finite-run observations, not known latent per-input success probabilities.
  It supplies no new confidence band or individual certification.

All intervals are supplied by analysis. The code preserves boundary flags,
unavailable intervals and exact CSV-line/source-ID mappings. It neither fits
statistics nor selects favorable strata/scenarios. Method color/marker and
scenario line style encode different objects; PDF and PNG still need inspection
in grayscale and at their 5.5-inch manuscript placement. Plain caption sources
require paper-owned LaTeX escaping and wrappers. Shared-helper provenance is
included as a hashed input (`generate_main.py`) alongside the rendering helper
and generator. This candidate inventory is not a requirement to include every
plot in the nine-page body; placement follows the completed claim evidence.

## Executed main evidence, 2026-11-05

The preceding preparation notes are historical. The complete main handoff has
now been rendered from analysis `c291b715fcfed90d5b5905e2d7a8e1f721937616`.
See `MAIN_HANDOFF.md` for the actual inventory, main/appendix recommendations,
claim limits, caption integration and reproduction. CPU time is now the timing
comparison alongside actual prediction rows; interrupted wall records are
explicitly qualified. `bash figures/reproduce_main.sh` reproduces all main
assets from the integrated analysis-owned results/config and runs the artifact
audit. No analysis is rerun. Main source data are not duplicated into this
position's delivered roots; paper receives them in analysis PR #16.
