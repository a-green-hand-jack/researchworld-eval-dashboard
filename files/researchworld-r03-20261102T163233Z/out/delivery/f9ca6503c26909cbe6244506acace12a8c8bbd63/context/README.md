# Checked research context

This directory is the self-contained context delivery owned by idea-repo. Paper-repo owns final manuscript prose; the study plan owns the division of work. The frozen objective governs.

- `Brief.md`: full frozen instructions, requirement ledger, settled scope and feasibility limits.
- `PRIOR_WORK.md`: consulted permitted literature, read sections, method/result distinctions and comparison/reporting implications.
- `READING_LOG.md`: actual access scope and prohibited-content record.
- `SOURCE_REGISTER.md` and `literature/sources.json`: exact consulted versions, direct permitted URLs, bytes and PDF hashes.
- `literature/references.bib`: citation resources; first-submission years are used consistently with arXiv records. No numerical reproduction of prior papers is implied.
- `frozen-inputs.json`: original frozen input hashes and paths.
- `tools/fetch_literature.py`: Python-standard-library direct retrieval and checksum verification of the ten permitted papers, with cache under `context/literature/`.

From the delivery root run `python3 context/tools/fetch_literature.py`. Optional extraction uses `pdftotext -layout context/literature/<name>.pdf context/literature/<name>.txt`. The PDF cache totals approximately 41 MB; it is not needed to build the manuscript and is not part of the delivered files. Add cache PDF/text patterns to the root gitignore if running retrieval in a development checkout.

Reading environment: Python 3.11.2, Poppler pdftotext 22.12.0 and PyMuPDF 1.28.2. No additional external literature was consulted during settled-scope maintenance. The bibliography and source notes may be used by the report owner without another literature search. Study measurements come separately from the analysis delivery.
