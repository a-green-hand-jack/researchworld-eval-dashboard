# Figure and table plan (revised when results arrive)

Venue (NeurIPS 2026, `venue.json`): one column, 5.5 in full width, ~2.7 in per panel; figure text >= 7 pt, table text >= 8 pt (`\footnotesize`) at the printed size; at most 7 main-text floats, aim 5-6, each about 1/3 page. Main text: Fig. 1-4, Table 1, Table 3; Table 2 half-width or a sentence; Fig. 5 folds into Table 3 / appendix unless the results need it in the text. Tables live in `tables/`.

Rules for all: drawn at the placed width (no rescaling), every text element >= the venue's
smallest type size, colour-blind-safe palette with one fixed colour+marker+dash per rule
(see `figtab/style.py`) so that a rule is identifiable in greyscale; uncertainty always
drawn and named once in the text (cluster bootstrap by incumbent and family), not repeated
in captions; every caption says what is plotted and what to see in it. Axes in the units
the Brief fixes for cross-m comparison (k/m; mean boost per task; B in sigma units).

| item | claim | what it must show | design | needs (DATA_CONTRACT) |
|---|---|---|---|---|
| Fig. 1 | C1 | one real target, one board: different rule -> different cheapest plan | x: breadth k (tasks touched); y: least total boost; one line per rule (5 rules); vertical/horizontal marker where B cap makes it infeasible (line ends); label the target and the incumbent in the panel title. Full width, 2 panels only if both a "mean-favoured" and a "median-favoured" target exist (this is the no-dominance message) | `frontier` |
| Fig. 2 | C1, C2, C5 | frontier shapes hold across targets; price vs B per rule | 2x2 small multiples (board x {frontier, price vs B}); median line + IQR band over top-30 targets; targeting multiplier as a separate small panel, not an inset (insets are illegible at the venue's type size) | `frontier`, `price` |
| Fig. 3 | C4 (headline) | does the median/mean breadth gap move with m | panel (a): k*/m vs m per rule, HELM random subsets (median, band), OLLB at m=6 and ~45 as paired points joined by line, free vs bundled as filled vs open markers; panel (b): same for B* in sigma units. Slope CI of R4 printed in the panel. Log-x. If the slope CI includes 0 the figure still shows it plainly | `m_effect`, `m_effect_fit` |
| Fig. 4 | C2, C3 | pairwise rule cost differences; ordering depends on the target | forest plot: rows = rule pairs, per board and incumbent mode (own vs common) as two markers; x = mean log price ratio with CI; share of targets with A cheaper as text at right; Kendall tau in the caption only if short. Zero line prominent | `paired`, `rule_order` |
| Fig. 5 | C6, C8 | (a) does gap alone predict price; (b) is B in the observed range | (a) dot-with-CI per rule for held-out R^2, gap vs gap+disp+corr; (b) strip/box of observed fine-tune gains per parent-size bucket with the B grid as horizontal lines, bucket sizes (n, n bases) on the axis | `predictors`, `calibration` |
| Table 1 | C1 | rule -> influence class -> price shape -> exact method -> size limit | text table from `table1_rules.yaml`; the size-limit and "solver verified against brute force on n instances" columns are read from `solver_check`, not typed | `solver_check` |
| Table 2 | -- | boards, snapshots, m, N, noise, targets | from `boards` | `boards` |
| Table 3 | C2, C3, C4, C6, C7 | the R1-R5 verdicts with numbers and CIs; unit robustness | one row per R with statistic, CI, threshold, verdict; second block: rule ordering by unit. Verdict words copied from the file, never hand-set | `verdicts`, `units` |

Known risks to the claim being clear (raised to story if they bite):
- Seven rules x two boards x two incumbent modes x B grid is more than a figure carries. Main text keeps the five rules of Fig. 1 plus mean-family/median-type grouping where the Brief groups them; the full grid goes to the appendix/release.
- If Fig. 3's HELM and OLLB regimes use different units on y, they must not share an axis; they get separate panels.
- Fig. 5 should merge into Table 3 if analysis delivers only one of (a), (b) (outline §7).

Updates after the first look at analysis' plan: `borda` and `winrate` are one rule (no `winrate` line); OLLB sub-task board has m=39; Table 1 is typeset by `paper-repo` in the text (its size-limit facts can come from `solver_check`); Fig. 3 panel (b) is the R4 quantity (median-type/mean-type breadth ratio, paired) and B* in sigma units moves to the appendix.

## Delivered state (paper-repo `dev`, built from `results/` of 963f33c; `sh figures/scripts/build_all.sh`)

| file | label in the text | claim | placement |
|---|---|---|---|
| `figures/fig1_teaser.pdf` | `fig:teaser` | C1 | main, intro |
| `figures/fig2_price_map.pdf` | (none yet) | C1, C2, C5: breadth/depth map, feasibility vs B, targeting multiplier | main (7th float) or appendix |
| `figures/fig3_m_effect.pdf` | `fig:m` | C4 (R4 mixed in sign over budgets) | main |
| `figures/fig4_pairs.pdf` | `fig:paired` | C2, C3 | main |
| `figures/fig5_predictors_calibration.pdf` | (none yet) | C6, C8 | appendix |
| `tables/table_price.tex` | `tab:price` | C1 | main |
| `tables/table3_verdicts.tex` | `tab:verdicts` | R1-R5 | main |
| `tables/table2_boards.tex` | (`tab:boards` is typeset inline in data.tex) | -- | appendix |
