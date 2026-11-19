# Source-access addendum

Date: 2026-11-02 UTC. This supplements `access_log.md`, `access_events.jsonl` and `sources/dataset_provenance_accesses.json`; it does not replace their exact automated events.

## Access policy
No topic search, paper-identification attempt, citation graph, aggregator, recommendation, or follow-up-paper reading. Original methodological PDFs are four user-listed originals. Additional dataset provenance is the user-listed Traud original and read data/policy pages. No known forbidden work or discussion was encountered. Allowed originals may themselves contain references; none was followed to identify the forbidden work. Stored HTML was parsed as text without executing scripts or loading subresources.

## Parent-agent direct accesses
- Public graphs and data/policy pages: exact URL, returned URL, bytes, hash and available Last-Modified in `data/manifest.json`; originals hash-match user-provided snapshots. Requests are in `fetch_data.py`.
- Official ethics only: `https://neurips.cc/public/EthicsGuidelines`, HTTP200, stored `sources/neurips_ethics.html` and stripped text; read the ethics code, not linked further-reading resources.
- Additional dataset-original direct attempt: `https://snap.stanford.edu/people/jure/pubs/circles-nips12.pdf` returned404, no original paper read. The permitted original title was already explicitly named by the user/data page; no unknown paper title/author guessing was involved.
- Software installation used configured Python package index for NetworkX, pytest and pypdf, with log `install.log`; no source-code repository search or external estimator download.

## Unsuccessful paper retrieval and truthful bibliography handling
Exact McAuley/Leskovec and Rossi/Ahmed attempts/hashes/statuses in dataset source notes. Their originals are not asserted to have been read. Bibliography entries cite the actually read dataset/repository pages and reproduce the pages' named creator/source attributions. Full paper-level citation/right compliance remains unconfirmed; no proxy failure was silently converted into a scientific source. Official template route deviations are disclosed separately in the original access log.

## Reproduction boundary
The analysis, plots and PDF can be regenerated wholly from delivered results/source. Simulations only require user-listed graph downloads; source literature is not fetched in the reproduction script. The portable archive omits original article PDFs and original/converted public topologies rather than assigning new rights to them.
