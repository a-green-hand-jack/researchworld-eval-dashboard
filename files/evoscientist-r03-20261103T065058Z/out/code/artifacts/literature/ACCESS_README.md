# Access and reproduction record

## Access policy used

Only these six arXiv IDs were fetched: `2210.07316`, `2402.14992`, `2407.12844`, `2407.13696`, `2405.10938`, `2412.06540`.

For each ID, exactly two HTTP requests were made: `https://arxiv.org/abs/<ID>v1` and `https://arxiv.org/pdf/<ID>v1`. All 12 returned HTTP 200. No topic search, citation discovery/traversal, recommendation service, repository, dataset, conference, review, blog, or other discussion page was accessed. Links described as code/data availability in the notes were transcribed from these allowed papers and **not visited**. No attempt was made to identify the excluded exact-problem work.

The complete original PDFs and abstract pages are archived under `sources/`. `access_log.jsonl` records request timestamps, exact URLs, response type, file size and SHA-256, plus the local incidental-exposure event below. The PDF title-page version stamps were verified against all six v1 IDs. The dated stamps in the PDFs are authoritative for the versions read; no effort was made to reconcile arXiv identifier/date quirks against other sources.

## Reading scope and incidental exposure

The synthesis used each allowed paper's own method, protocol, result, and limitation descriptions. Sections/pages supporting claims are listed in `allowed_literature.md`. Selected appendices were read for MTEB dataset structure, observational-scaling PCA/imputation, and Sloth limitations. This is a targeted technical reading, not a claim of full appendix coverage.

Complete source files necessarily contain reference lists. Those are archival material, not additional allowed sources. A local keyword-location command inadvertently displayed limited bibliography-line snippets from three allowed papers (MTEB, tinyBenchmarks, Sloth), and a MTEB appendix range began with two trailing bibliography lines. No entry was followed, fetched, investigated, or used as evidence. No excluded exact-problem work was identified; no attempt was made to infer its identity. The local exposure is recorded in the access log without copying reference titles or inferring which work is excluded. Unrestricted keyword extraction over full documents was stopped; later reads used explicit method/evaluation/appendix ranges.

## Extraction caveats

- `full_text_v1.txt` uses pypdf layout extraction; `plain_text_v1.txt` uses standard extraction. Both are complete sources and include references.
- Layout extraction emitted warnings for rotated text and can corrupt plotted glyphs. Do not infer numerical plot values from corrupted text. Notes rely on readable prose, captions and tables.
- Initial reference-free copies used a heading regex on layout text, which missed some multi-column reference boundaries. Offline audit rebuilt every `body_before_references_v1.txt` using verified plain-text reference headings. These copies deliberately omit appendices that come after references; use explicit source-page ranges for permitted methodological appendices.
- Citation metadata was parsed from each fetched abstract page. Starter-list shorthand titles were not silently substituted for the actual fetched titles.
- No results were experimentally reproduced. Paper-reported results, methodological implications and proposed experiments are explicitly distinguished.

## Files and commands

- Literature notes: `allowed_literature.md`
- Six-entry bibliography: `references.bib`
- Network/local-event provenance: `access_log.jsonl`
- Integrity, URLs, PDF page counts, version checks, environment: `manifest.json`
- Direct acquisition: `fetch_allowed.py`
- Offline audit: `audit_artifacts.py`

Acquisition uses Python, `requests`, and `pypdf`; exact installed versions are recorded in `manifest.json`. Commands (absolute paths):

```sh
python /work/artifacts/literature/fetch_allowed.py
python /work/artifacts/literature/audit_artifacts.py
```

**Do not rerun acquisition just to audit:** it appends to the request log and would create additional network entries. The offline audit intentionally checks that this session has exactly 12 source requests and fails if acquisition is rerun without starting a separate provenance run. It performs no network access. To verify this session, run only the offline audit. It checks allowlisted URLs, source hashes, six v1 PDF stamps, six BibTeX IDs and reference-free reading boundaries; it then refreshes the manifest.

The acquisition script enforces exact host/path allowlists and does not follow arbitrary source-page links. The whole artifact directory is well below the task's 5 GB storage ceiling; byte counts are in the manifest. No paid API, GPU, model inference, or experiment runs were used.
