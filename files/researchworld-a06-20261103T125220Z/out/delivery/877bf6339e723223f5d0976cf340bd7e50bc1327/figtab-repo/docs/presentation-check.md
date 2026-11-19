# Synthetic presentation acceptance check

The objective and frozen `deliverable.md` require a complete research paper, measured evidence including one real LLM/benchmark setting, uncertainty reporting, and a generator for each figure/table. This delivery satisfies only the synthetic presentation part. Real-model evidence and its figures remain outstanding; no synthetic panel stands in for an LLM measurement.

Checked against commitment issue #3:

- Six figures cover optimism, coverage, resource/quality tradeoffs, the specified decision error, complete-grid patterns and score MSE. The numerical table presents two fully identified settings and includes total model calls. No data were invented and no experiments were repeated.
- Plotting input is a pinned copy of the upstream 288-cell summary, with its full source revision and hashes. Rendering validates input hashes, metric grids, event counts and repetition counts.
- Scales and units are explicit. The optimism plot includes the zero baseline, coverage includes 95%, and decision error includes the 5% frozen-pair bound. The MSE axis is logarithmic and labeled in pp². Split protocols target their own selected candidate.
- Bands distinguish Monte Carlo precision from the intervals being evaluated. Event intervals include upper limits for zero observed events. Full-grid dot annotations use marginal tests and disclose the absence of multiplicity correction.
- The generator and captions specify n/K/rho/spread, the fixed bank, candidate qualities, independent audit cost, CP/Bonferroni conditions, and equal-question/equal-call budgets. Extra audit shares the full-search winner; simultaneous correction does not debias the score.
- All six final vector PDFs and all six final PNGs, plus the table PDF/PNG preview, were opened as raster contact sheets. Labels, legends, panels, color scales and boundaries were checked. An initial title overflow and table-preview clipping were fixed before this check.
- The actual booktabs table source was compiled using pdfLaTeX (TeX Live 2022) in a 7-inch text area at 8 pt and its PDF raster was opened and checked. It compiles without overfull boxes.
- The output CSV and LaTeX numbers were checked against the upstream metric names and budget formulas. Table parentheses are MCSE, with three decimals to avoid unnecessarily rounding small nonzero errors to zero.

Venue/template and story path settlement were requested in venue-repo #2 and story-repo #3. Current art is designed for full-width 6.75–7-inch placement. These choices can be adjusted once concrete venue requirements arrive. The idea brief was not yet accessible during the initial production turn. Its subsequently published Brief and Estimands-and-Evaluation wiki pages have now been read and checked against this package; see `docs/brief-alignment.md`.

## Settled venue revision

The later venue answer selects ICLR 2027 with a single 5.5-inch text column. All six figures were redesigned at native 5.5 inches, with 9 pt axis/panel labels and 8 pt tick/legend text. Some intermediate tick labels are omitted without dropping points. The table preview now uses the actual LaTeX source. Every revised export and official-style diagnostic page was inspected; see the delivered `presentation/acceptance.md`. The earlier 7-inch diagnostic is superseded. Story settled `figures/`, `tables/`, and `presentation/` for figtab in paper PR #5; package transfer can now proceed.
