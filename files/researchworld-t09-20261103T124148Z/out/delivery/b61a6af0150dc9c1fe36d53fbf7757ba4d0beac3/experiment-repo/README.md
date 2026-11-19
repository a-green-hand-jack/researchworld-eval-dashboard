# Regression GATE accuracy under network interference

This repository supplies the analysis, executable simulations and validity record
for the ResearchWorld study. The report/presentation are delivered by their owners
in paper-repo. Scientific scope is 102 cells with R400: seven synthetic regimes
with five graph seeds each, plus one full fixed SNAP topology; eight outcome laws,
seven regressions and full-neighborhood HT/Hajek baselines. Core/noise/imbalance
use independent masters 2202601/2202602/2202603. All outcomes are synthetic.

The numerical authority is corrected count-before-division exposure code. V1
production is superseded after a scientific boundary check found normalized sparse
sums could misclassify 17/20=.85 and 60/80=.75. Original source/results and audit
receipts are preserved on `archive-roundoff-v1` and under `notes/roundoff_v1/`.
No graph, config, seed, repetition count or scientific condition changed.

Start with `notes/final_findings.md` and `results/diagnostics/claim_evidence.csv`
for supported claims, adverse results, exact table/row/hash routes and uncertainty.
`notes/methods.md` specifies scoring/conditioning and estimability rules;
`notes/execution_reconciliation.md` and `final_execution.json` establish actual
completion, resource costs and provenance. Audit receipts and selected replay
are internal checks, distinct from independent release review.

To reproduce from this development layout, use Python3.11 and the measured
versions in `environment.json`/`requirements-lock.txt`:

```sh
python3 -m pip install -r requirements-lock.txt
python3 -m pip install --no-deps -e .
python3 scripts/download_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -m unittest discover -s tests -v
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python3 -u scripts/run_study.py --workspace /path/to/empty/workspace
```

A measured timing pilot sized production; its conservative allowance was 7.30h,
not a measured runtime. Corrected actual costs are in the execution reconciliation.
Outputs checkpoint atomically per cell. The launcher refuses mixed-source/config
resumes. See `notes/delivery_reproduction.md` for commands in the delivered
`code/`, `results/`, `analysis/` layout and the distinction between a portable clean
reproduction and historical correction/resource receipts. Four structurally chosen
cells have a clean exact replay; no independent implementation is claimed.

`data/manifest.json` records graph provenance, frozen source hash and terms. Raw
public data are downloaded and not redistributed. No prohibited-paper search or
access occurred. No plot/table rendering is supplied here: figtab-repo owns those
assets and their script-to-display mapping.

Clean-workspace postprocessing is self-contained: `scripts/reproduce_workspace.py
prepare --workspace NEW` copies code/configs and historical reference receipts,
never results; launch `NEW/code/scripts/run_study.py --workspace NEW`, then run
`NEW/code/scripts/reproduce_workspace.py postprocess --workspace NEW`. Existing
results-only workspaces can also be prepared. Fresh diagnostics, claim registry
and audit/replay receipts stay in NEW; original receipts remain preserved. See
`notes/delivery_reproduction.md` for the complete commands and provenance limits.
