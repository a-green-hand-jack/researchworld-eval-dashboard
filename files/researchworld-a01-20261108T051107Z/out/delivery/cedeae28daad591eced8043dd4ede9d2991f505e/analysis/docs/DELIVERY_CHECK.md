# Analysis handoff reconciliation (2026-11-08)

Checked the answers to figtab-repo#9 and paper-repo#53 against delivery root
revision e2a32856c68675989ebab51cfa11b6d4e4e4a88d. Machine-readable results:
`results/delivery_analysis_check.json`. All checks in this reconciliation pass.

The frame/cap/unit figures and tables have provenance hashes matching the
canonical supplied numerical CSVs. Checks cover fig13/14/15, matched-frame,
cap and cost-unit tables, the main frame/cap tables, the all-target controls
figure and gain10 headline-range table. `draft=false` for every checked output.
All36 main cap-table count cells and12 min-minus-mean sign cells reproduce
from `final_caps_feasibility.csv`. All90 cost-unit inverse-median cells and
21 displayed midpoint alternatives agree with `final_costscale_summary.csv`
to half a unit of their printed precision (111 numerical cells).

The two reported definition defects are corrected: HELM gain10 median K21 and
plurality K9 appear as finite whole-panel medians, with their actual ranges,
and the controls provenance includes all feasible targets with0/0=1.
The report no longer claims highest-Average duplicate selection can only raise
rival task scores/costs. It states the checked74/79 coordinatewise exceptions.
The full-frame diagnostic reference rows supplied in experiment-repo#9/paper
PR58 are now integrated in the main frame table. At paper revision
1e9b1ced5ef5bdf5500ffacee3bbeafc9fc1f5c6, all six displayed correlations/gaps
match their canonical CSV at the printed precision; its provenance source
hash also matches.

This is an analysis-source and numerical integration check of the named
outputs, not the independent report review or a clean end-to-end study pass.
The original16-file clean job subsequently passed all457772 rows at absolute
1e-5, maximum finite difference5.8069e-9; all174000 robustness/control rows
have zero difference. `clean_reproduction.json` and its artifact-hash audit
are the completed gate records. Historical selected-file audits remain partial.

The verdict table added at paper revision d21a6207276b8de47e313bf2bbe1e98b481f0d1a
was also reconciled with the matched-frame draw-level summaries. At the
ceiling, minimum's median K exceeds mean's in100/100 OLLB79 draws, the fixed
top79 frame, and60/100 HELM6 draws (8 lower,32 tied). Thus the HELM6 K sign
reverses by majority/median while the OLLB signs persist. Minimum has lower
median L1 in every draw/fixed frame, and mean has the largest median L1 among
score rules in every draw/fixed frame. These support the table's stated
median/majority classifications; they do not imply targetwise universal orders.
Exact counts and the source hash are in the machine-readable audit.
