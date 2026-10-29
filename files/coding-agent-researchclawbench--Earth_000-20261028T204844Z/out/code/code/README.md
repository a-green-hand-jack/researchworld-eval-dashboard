# Reproduce the GlaMBIE benchmark analysis

Run commands from `/work`. All analysis and report artifacts stay under this root;
`data/` and `related_work/` are inputs and are never modified.

```bash
python3 -m venv .venv
.venv/bin/pip install --cache-dir outputs/pip-cache -r code/requirements.txt
MPLCONFIGDIR=/work/outputs/mplconfig .venv/bin/python code/analyze.py
.venv/bin/python code/write_report.py
.venv/bin/python code/validate_deliverables.py
```

The pipeline is deterministic, with no Monte Carlo sampling. `requirements.txt`
pins the versions used for the actual run; `outputs/run_metadata.json` records
Python and platform versions. `analyze.py` regenerates eight PNG figures and
the tabular products. `write_report.py` builds `report/report.md` using these
products. `validate_deliverables.py` checks source preservation, interval bounds,
annual coverage, regional aggregation, covariance units, input hashes, image
integrity, and report links.

`extract_literature.py` extracts the five supplied PDFs. It can also download the
primary GlaMBIE paper if its cached HTML is absent. Literature extraction is
optional for reproducing the numerical analysis and report; the extracted and
cached references from the completed run are already in `outputs/literature/`.

## Scientific scope

The primary annual time series is the released consensus in GlaMBIE 1.0.0,
not a new reduction of every raw input file. New computations comprise data
audits, regional attribution, method-native comparisons, weighting and omission
diagnostics, and covariance scenarios. No unvalidated reweighted estimate is
substituted for the released consensus.

The published error fields are 95% half-widths. Convert to standard deviations
by dividing by 1.96 before building a likelihood or covariance. All `_h95`
exports retain half-width units; covariance files contain actual variances in
Gt². Temporal correlation scenarios describe measurement errors, not climatic
autocorrelation. The report documents the release's numerical mass conversion
factor of 0.997 and preserves it for exact source consistency.
