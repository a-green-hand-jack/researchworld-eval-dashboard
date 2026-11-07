# Figures and tables

These assets present committed experiment-repo results; they do not compute attacks or claim measured training costs. Input analysis revision: `d58e1529360f4cdf771f6d87f941f9ae9a7fe8ee`. `manifest.json` records exact input hashes, output hashes, dependencies and the generation command. `captions.tex` contains all caption macros. The final manuscript should input that file and use label `fig:budget` for the budget plot; the gain caption references it.

In the integrated delivery root (analysis `results/` and `data/` alongside this directory):

```bash
python3 presentation/render.py --analysis-root . --output-root . --width 5.5
```

Before integration, pass the experiment-repo checkout as `--analysis-root`. Rendering takes about six seconds on the shared two-CPU sandbox (measured wall time; varies by machine). No randomness is introduced by rendering. Font and canvas dimensions are configurable through the source and `--width`; the confirmed NeurIPS 2026 text width is 5.5 inches (venue/geometry.json). Keep plot labels at 8 pt or larger at that final width. Python/NumPy/pandas/Matplotlib versions are in `manifest.json`.

| Asset | Claim or purpose | Caption macro |
|---|---|---|
| `figures/budget_curves.pdf` | Distribution of exact investment needed, on common challengers | `\BudgetCurvesCaption` |
| `figures/gain_reachability.pdf` | Rule dependence changes with achievable gains; infeasible cases retained | `\GainReachabilityCaption` |
| `figures/task_composition.pdf` | Dependence on benchmark composition, with explicit sensitivity ranges | `\TaskCompositionCaption` |
| `tables/cohorts.tex` | Frozen score source, tasks, retained evaluations and challenger definition | `\CohortsCaption` |
| `tables/primary_budgets.tex` | Median budgets and fractions for common challengers | `\PrimaryBudgetsCaption` |
| `tables/paired_borda.tex` | Target-matched counts; limits of a universal ordering | `\PairedBordaCaption` |
| `tables/robustness.tex` | Task, normalization and model-cohort sensitivity | `\RobustnessCaption` |
| `tables/random_selection.tex` | Optimal versus random task selection, with Monte Carlo error | `\RandomSelectionCaption` |
| `tables/ceiling_sensitivity.tex` | Unit versus best-observed ceilings on common challengers | `\CeilingSensitivityCaption` |

PDF is vector output with embedded TrueType fonts; PNG copies permit inspection. Table fragments use `booktabs`; CSV companions contain the displayed cells (including LaTeX formatting). Original numerical inputs remain in analysis `results/`. The cohort membership file and gain-plot values under this directory make denominator checks immediate. Table rounding is to one decimal for fractions and means, integers for counts.

The primary budget plot excludes the union of incumbent winners under the primary setting. The gain plot keeps each full evaluation cohort fixed across gain settings, including incumbent winners. Composition/random/raw/unique sensitivity summaries use their own explicitly captioned full cohorts. Colors and line styles are consistent across plots. No confidence interval is invented for deterministic finite-cohort curves. Source score licenses are undeclared upstream; see analysis reproduction notes. This position accessed no literature search results or prohibited material.

The refreshed schema explicitly selects `cohort=full_cohort` for the primary random-baseline intervals and verifies its expectation denominator equals the full cohort. Primary curves read `results/challenger_budget_curves.csv`; the generator cross-checks them against the fixed primary membership and raw optimal-budget rows. Restricted-gain random stopping estimates are not displayed in this package.
