# Source acquisition and reading log

All six frozen supplied files were read in full. Exact permitted starter papers were retrieved from version-specific arXiv URLs; only the sections documented in the evidence map were read, so possession of full extracted text does not imply reading every appendix or cited reference. No references were followed to identify the prohibited paper. No prohibited-content encounter has been identified.

`access.json` records retrieved PDF/source hashes and URLs. The extracted texts were made with `pdftotext -layout`; these are prior-work source records, never experimental data or our research results. The PDF parser emitted `xref num 484 not found but needed, try to reconstruct` during the first batch, but extraction exited successfully. Checked formulas were legible in the retained text. For exact typography consult the linked permitted PDF. The original PDFs are ignored by git and not part of delivery.

`fetch_context.py` refetches the nine exact arXiv PDFs and writes a fresh `retrieval-rerun.json` without overwriting the original access log. The two non-PDF source URLs can be retrieved directly using the log. Uses Python standard library and pdftotext; no dependency changes were needed. Tools used: Python 3.11 and poppler pdftotext (versions recorded in `tool-versions.txt`).

All study-result numbers must come from analysis-owned runs. None are supplied in this repository.
