# Paper figure and table reproduction map

Run from the delivery root in the pinned presentation environment:

```sh
python3 presentation/render.py
python3 presentation/render_real.py
make paper
```

The first script renders synthetic displays from `presentation/inputs/synthetic-summary.csv` and its validation record; both match the complete analysis. The second renders real displays from the 16 files under `presentation/inputs/real/`, all byte-identical to the analysis paths specified in `presentation/real-provenance.json`. Neither script runs inference or resampling. Full-precision table CSVs share each TeX basename. Native dimensions, versions, source revisions, caption definitions and uncertainty specifications are retained in the corresponding presentation documentation.

| Paper display | Artifact under delivery root | Generator |
|---|---|---|
| Figure 1 | `figures/synthetic-selection.pdf` | `presentation/render.py` |
| Figure 2 | `figures/real-primary.pdf` | `presentation/render_real.py` |
| Figure 3 | `figures/real-cache-main.pdf` | `presentation/render_real.py` |
| Figure 4 | `figures/synthetic-decisions.pdf` | `presentation/render.py` |
| Figure 5 | `figures/synthetic-optimism-grid.pdf` | `presentation/render.py` |
| Figure 6 | `figures/synthetic-coverage-grid.pdf` | `presentation/render.py` |
| Figure 7 | `figures/synthetic-mse.pdf` | `presentation/render.py` |
| Figure 8 | `figures/synthetic-budgets.pdf` | `presentation/render.py` |
| Figure 9 | `figures/real-cache.pdf` | `presentation/render_real.py` |
| Figure 10 | `figures/real-conditional.pdf` | `presentation/render_real.py` |
| Figure 11 | `figures/real-cache-coverage-grid.pdf` | `presentation/render_real.py` |
| Figure 12 | `figures/real-cache-mse.pdf` | `presentation/render_real.py` |
| Figure 13 | `figures/real-diagnostics.pdf` | `presentation/render_real.py` |
| Table 1 | `tables/synthetic-methods.tex` | `presentation/render.py` |
| Table 2 | `tables/real-reporting.tex` | `presentation/render_real.py` |
| Table 3 | `tables/real-cache-methods.tex` | `presentation/render_real.py` |
| Table 4 | `tables/real-bootstrap.tex` | `presentation/render_real.py` |
| Table 5 | `tables/real-cache-decisions.tex` | `presentation/render_real.py` |

Figures 1–3 appear in main; the remaining displays appear in the appendix. See `presentation/README.md` for the synthetic metric/slice map and `presentation/real-output-map.json` for every real script/input/output route. Root `make check` checks supplied input hashes/equality and the real output-route file presence. Source numerical reproduction, including all original seeds, is described in `analysis/docs/real-reproduction.md` and the root README.
