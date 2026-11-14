# Context for research on scores reported after automatic LLM configuration search

This repository belongs to the context position. It supplies the study requirements and consulted prior-work evidence to the plan and feasibility positions. It contains no measured LLM or synthetic experiment findings; those belong to experiment-repo.

- [`context/Brief.md`](context/Brief.md): all frozen requirements verbatim, operational interpretation, ownership handoff, unresolved constraints; mirrored to the `Brief` wiki page.
- [`literature/primary-source-notes.md`](literature/primary-source-notes.md): consulted source sections, methods/results attributable to prior work, benchmark/scoring conventions, distinctions and claim boundaries for the study.
- [`context/estimands-and-evaluation.md`](context/estimands-and-evaluation.md): selected-configuration versus selection-procedure targets; independent/fixed-bank/adaptive distinctions; evaluation, decision and presentation advice.
- [`literature/context-references.bib`](literature/context-references.bib): references to sources actually consulted, with explicit versions.
- [`provenance/`](provenance): input hashes, exact primary-source URLs/versions/byte hashes, environment, reading scopes, source restrictions and access log.

The same context materials are published in a source-notes release and on the wiki for positions that cannot read this repository's code. Story-repo has settled the plan and ownership in story #4: experiment owns analysis/method validity, paper owns final prose/bibliography, and story relays this context package to paper. The Brief records that agreement and the independent feasibility/venue handoffs, and the current Tier C 11,776-question remaining-benchmark audit target and runtime-design guarantee distinction from idea #5 / story #11 (with Tier B retained as history), with inspected revisions in `provenance/handoff-reconciliation.json`. These are working/context documents, not another position's final manuscript, analysis or figure delivery.

## Reproduce the source cache

Requirements: Python 3 standard library, HTTPS access and Poppler `pdftotext`; actual versions are in `provenance/context-environment.json`. No models, API budget, random seeds or stochastic study computation are used here.

```bash
python3 scripts/download_context_sources.py \
  --output-dir /path/to/local/context-source-cache \
  --verify-manifest provenance/primary-sources.json
```

This accesses only enumerated permitted direct source URLs; it does not search or follow links. The original download took less than a minute in this environment, but network time varies. The manifest checks detect changes at mutable URLs (notably the NBER file); do not silently use new bytes as if they were the consulted revision. The source papers are not redistributed in this repository or its release. The script writes its own download manifest and extracted text into the requested local directory.

All five original inputs remain read-only at `/initial-state/inputs/0/`. To check them independently, use their exact paths and hashes in `provenance/frozen-inputs.json`.
