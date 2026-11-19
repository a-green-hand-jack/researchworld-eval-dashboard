# Recreate figures and tables

From the delivery root, with Python 3.11.2 and the versions in `presentation/requirements.txt`:

```
python3 -m pip install -r presentation/requirements.txt
python3 presentation/render.py
```

The table preview also requires `pdflatex` (TeX Live 2022 was used), `booktabs`, `geometry`, and Poppler `pdftoppm`, available in the supplied research environment. `presentation/table-preview.tex` renders the actual table source at 8 pt in a 5.5-inch text area.

This renders six vector PDFs and six PNG previews under `figures/`, a booktabs LaTeX table and full-precision derived CSV under `tables/`, and a PDF/PNG table preview. Runtime in this CPU sandbox is approximately 15 seconds. The generator reads only the committed input CSV and verifies its SHA-256 against `presentation/provenance.json`; it performs no simulation and needs no network or random seed. Input rows retain all upstream seeds. Installing dependencies is unnecessary when the recorded scientific stack is already available.

`presentation/captions.md` supplies the captions, scope and suggested placement. Use figures at native 5.5-inch width (`\linewidth` in the official ICLR 2027 template). Axis labels and titles are 9 pt; tick and legend text are 8 pt. Do not shrink these figures further. Some intermediate logarithmic tick labels are omitted to prevent collisions; every data point is retained. The table requires `booktabs` in the manuscript preamble. The table preview is an inspection aid; the delivered LaTeX is the publication source.

Source experiment, exact input paths, full upstream revision, SHA-256 hashes and plotting environment are recorded in `presentation/provenance.json`. These are synthetic results only. The raw experiment and independent exact-null validation belong to experiment-repo; its source input must be included separately by that owner in the reproduction package. The copied validation JSON preserves the checks that accompany these presentation inputs and is not rerun by rendering.

The generator checks row uniqueness, complete metric grids, finite means/MCSEs, repetition counts, input hashes and integer event counts. Event bands are exact marginal 95% Monte Carlo binomial intervals, including nonzero upper endpoints for zero observed events; other bands use mean ±1.96 MCSE. These quantify simulation error, not a posterior interval or uncertainty across models. No additional method fitting or experimental inference is performed here.

Output mapping:

| Output | Source metrics and filters |
|---|---|
| synthetic-selection | optimism_reused: spread=0, n=32/128/512; coverage_naive/simultaneous/independent_audit: spread=0, n=64; all K/rho |
| synthetic-budgets | width_* and selected_quality/quality_split_*: K=32, spread=.08; all n/rho |
| synthetic-decisions | false_superiority_naive/simultaneous: n=512, spread=0; all K/rho |
| synthetic-optimism-grid | optimism_reused: all cells |
| synthetic-coverage-grid | coverage_naive: all cells |
| synthetic-mse | mse_reused/independent_audit/split_question_budget/split_call_budget: K=32; all n/rho/spread |
| synthetic-methods table | bias/coverage/width/quality metrics: (n,K,rho,spread)=(64,16,.5,0),(128,32,.5,.08); model-call and question counts follow upstream protocol formulas |

`presentation/real-presentation-contract.md` records the settled finite-audit targets, interval conditioning and planned claim/encoding requirements for the separate pending real-model package. It supplies no main real-model values. Synthetic integration into the official root PDF was checked at paper revision `07a6b51f5277f3e5606c3c87ccafc7b908683ba0`; the root check is recorded in `presentation/root-integration-check.md`.

The completed measured-real package is reproduced with `python3 presentation/render_real.py`; see `presentation/REAL-README.md`, `real-provenance.json`, `real-output-map.json` and `real-captions.md` for its independent target/uncertainty/input mapping. The measured inputs answer experiment-repo #3; final real-root-PDF integration remains to be checked after the paper owner merges/builds the figures.
