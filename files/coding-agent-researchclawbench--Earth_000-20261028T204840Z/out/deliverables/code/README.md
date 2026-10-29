# Reproduce the glacier benchmark analysis

All commands and output locations below stay under `/work`. The `data/` and
`related_work/` trees are inputs and are never edited.

The preconfigured environment is `/work/.venv`. To create it in a fresh workspace:

```bash
cd /work
python3 -m venv /work/.venv
/work/.venv/bin/pip install --cache-dir /work/.cache/pip -r /work/code/requirements.lock.txt
```

Run the deterministic numerical analysis, report renderer, and scientific checks:

```bash
/work/.venv/bin/python /work/code/analyze.py
/work/.venv/bin/python /work/code/build_report.py
/work/.venv/bin/python /work/code/validate_outputs.py
```

The pipeline does not require network access after dependency installation. It
recreates the CSV/JSON/NPZ analysis products and seven PNG figures. Matplotlib's
cache is directed to `/work/.cache/matplotlib`. The rendered report is
`/work/report/report.md`; its narrative source is `report_template.md`.

`extract_references.py` optionally extracts supplied PDF text and downloaded
article HTML. `download_references.py` optionally refreshes the external
reference cache and its provenance manifest. Neither is required for numerical
reproduction. The constants reference is a snapshot from the repository's main
branch, not a pinned historical release; SHA-256 hashes record the exact fetched
bytes. The 997 kg/m³ factor is independently verified from every result row.

Scientific scope: this is an audit and analysis of the released GlaMBIE consensus,
with a secondary reconstruction from homogenized method groups. It is not a
complete re-execution of the original raw-submission processing workflow. See the
report for the selection, density, confidence-interval, and covariance caveats.

Dependency versions are locked in `requirements.lock.txt`. No random simulation
is used. Covariance and Fieller intervals are calculated analytically. The
validator checks source fidelity, mass/unit closure, input preservation, positive
semidefinite covariance matrices, ratio-interval equations, and rendered assets.
