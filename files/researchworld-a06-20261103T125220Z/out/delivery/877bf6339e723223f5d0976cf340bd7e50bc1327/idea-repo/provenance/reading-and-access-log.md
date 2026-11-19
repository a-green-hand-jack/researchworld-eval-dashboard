# Context reading and access record

Date: 2026-11-03 UTC. Owner: idea-repo.

- Read Research objective issue #1 and all five `/initial-state/inputs/0/` files in full. Verified their lengths and SHA-256 values against the issue's frozen map (`frozen-inputs.json`).
- Downloaded the eleven explicitly permitted starter papers directly, using v1 arXiv PDFs to keep a definite early version, plus the exact permitted NBER PDF. Retrieved Berk's exact DOI metadata from Crossref to verify title/authors/DOI; its arXiv PDF confirms the matching published article. No topical search, cited-by query, recommendation page, or search result list was used.
- Downloaded the official MMLU-Pro card at the frozen revision. Its dated maintenance notes and links were read as part of that supplied data documentation. Did not follow its leaderboard or discussion links or use its cached predictions; a new real LLM experiment remains required.
- Retrieved Cawley–Talbot 2010 directly from a known exact JMLR PDF URL as a classical antecedent. No title/author/result of the withheld paper was sought or inferred. No accidental encounter with material identifiable as prohibited was observed. Other positions must record their own access events; this statement applies only to the context owner's reading in this turn.
- PDF text was extracted using `pdftotext -layout`. Reading focused on sections explicitly named in `literature/primary-source-notes.md`. Appendices/proofs not inspected are not represented as checked; source download does not mean full proof verification.
- The first downloader invocation failed because `requests` was unavailable. Replaced it with Python's standard-library `urllib.request`; all listed downloads then succeeded. No package installation or paid inference was used in context work.
- Initial wiki clone/push failed because the wiki had no page/repository yet. The Brief was created via Forgejo's wiki API; this resolved publication. Subsequent updates use the existing wiki repository.
- One attempt to read paper-repo CODEOWNERS through its contents API returned HTTP 403; no file content was disclosed. That exceeds this position's current release/wiki access and was not repeated. The context delivery route and ownership are instead requested from story-repo in story-repo #4.

Source hashes, byte counts, original/final URLs, retrieval date and exact versions are in `primary-sources.json`. The independent context source downloader is in `scripts/download_context_sources.py`; source PDFs remain a local reading cache and are not redistributed with this context package. It uses only explicitly enumerated URLs, with no recursive links or searches. Environment versions are in `context-environment.json`.
