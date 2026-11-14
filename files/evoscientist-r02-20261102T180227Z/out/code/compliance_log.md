# Access and compliance report

Date: 2026-11-02 UTC. Workspace: `/work`.

## Scholarly/template access

Eight explicit research HTTP requests, all HTTP 200 with no redirects:

1. https://arxiv.org/pdf/2107.07511
2. https://arxiv.org/pdf/1904.06019
3. https://arxiv.org/pdf/2009.14193
4. https://arxiv.org/pdf/2402.10723
5. https://api.github.com/repos/ICLR/Master-Template/contents/
6. https://raw.githubusercontent.com/ICLR/Master-Template/master/README.md
7. https://api.github.com/repos/ICLR/Master-Template/contents/iclr2027
8. https://raw.githubusercontent.com/ICLR/Master-Template/master/iclr2027.zip

Exact access timestamps, bytes, paths and SHA-256 values are in `access_log.json`. Template sources were read from the permitted archive and verified against the permitted directory API, not fetched from additional sites.

- External topical/broad searches: **0**.
- Citation graph, recommendation, or external citing/discussion pages: **0 accessed**.
- Extra papers or substitute arXiv identifiers: **0 fetched**.
- NeurIPS fallback: not used; ICLR 2027 was available.
- Embedded code/data/policy links in the allowed documents: some were recorded as source-reported pointers, **not opened**.
- The unidentified forbidden paper was not searched for or identified. No forbidden-content encounter was identified. Incident log: **none** (therefore no incident URL or amount-read entry).

The four PDFs themselves were expressly allowed. Local text extraction of those PDFs does not authorize visiting references or other pages citing them. This report does not claim to have identified the prohibited work or checked its citation network.

## Local tools and infrastructure

- The earlier internal memory preflight returned no relevant observations; this was not a web search.
- Read local paper-navigator guidance, but did not run its discovery workflow. Consulted the local math-skill scope while assessing a proof caveat; did not initiate a theorem-proof pipeline or additional literature search.
- Installed `pypdf` with `python -m pip install pypdf --disable-pip-version-check` because the environment lacked PDF text extraction. This is an infrastructure/package download, not scholarly browsing. Package-registry requests are not included in the eight-entry research URL log; individual registry URLs were not captured. The audit records the installed version.
- Used Python standard-library download/hash/archive operations and local PDF extraction. No experiment code was written or executed; no training, tuning, or evaluation runs were launched. Official example LaTeX sources were saved unmodified, not implemented as an experiment.

## Deliverables and checks

- `literature_notes.md`: target distinctions, finite-sample rank calibration, group/Mondrian limits, weighted shift assumptions, experimental protocols, metrics, failure modes, page/equation evidence, and BibTeX.
- `literature/references.bib`: four verified arXiv records. Corrects the attribution of 2009.14193 to Angelopoulos et al.; no Romano paper was silently substituted.
- `literature/{2107.07511,1904.06019,2009.14193,2402.10723}.pdf`: original downloads; respectively 51, 17, 18, 16 pages, all text-extractable and matching the recorded download hashes.
- `template/`: official 2027 archive/source package, API evidence, README, and integrity manifest; all seven source files match official Git blob hashes.
- `template_provenance.md`: official provenance, immutable hash evidence, exact nine-/ten-page rule, and remaining appendix-policy uncertainty.
- `research_audit.json`: machine-readable integrity, parsing, request-allowlist, and implementation-status checks.

Verification limits: source package not compiled; external code/data availability not tested; forbidden work remains unidentified; latent-probability coverage is not asserted merely from observed-vector coverage. The credal paper's noise-transfer argument has a specifically located proof caveat in the notes; this is not presented as a completed mathematical refutation.
