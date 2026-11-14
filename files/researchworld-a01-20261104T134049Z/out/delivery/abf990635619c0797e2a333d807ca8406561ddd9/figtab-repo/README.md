# figtab-repo — figures and tables

Presentation position. Scripts in `scripts/` read result files of `experiment-repo` (path passed as argument) and write
vector PDF + PNG into `figures/`, LaTeX tables into `tables/`.

| output | script | inputs | status |
|---|---|---|---|
| (draft) investment vs. rank per rule | `scripts/fig_rank_rules.py` | `results/ollb_closed.csv`, `results/helm_main.csv` | prototype on partial results; not delivered |

Shared style (colour per rule, fonts, rank bins with bootstrap CI over targets): `scripts/style.py`.
Commitment: issue #2.
