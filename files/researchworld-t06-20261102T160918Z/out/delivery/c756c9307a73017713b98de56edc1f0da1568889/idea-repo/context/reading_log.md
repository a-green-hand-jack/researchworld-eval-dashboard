# Source reading and access record

Date: 2026-11-02 UTC. All five frozen files (TASK.md, data.md, deliverable.md, resources.md, starter_literature.md) were read in full. The full objective issue was read before settling this context and will be checked again before completion.

The linked starter papers are external context, not new experiment inputs. Only their explicitly permitted PDF links were opened; no cited, citing or related-work pages were followed. Returned PDF versions were identified from their text and hashed. `sources.json` records versions, URLs, size, page count and SHA-256. PDFs and extracted text remain outside the repository in `/hutian/reading`; copyright PDFs are not bundled with the submission.

Actually inspected sections for claims in the dossier:

| Source | Reading scope used |
| --- | --- |
| Chiang 2403.04132v1 | Main paper: introductory context and §§3–5 model/estimation, §§6.3–8 vote validation/experiments/limitations; Figure 5 caption and surrounding uncertainty discussion |
| Zheng 2306.05685v4 | Main §§1–7, Appendix C, setup of Appendix D.3; order-swap and agreement tables |
| Koh 1703.04730v3 | Main influence derivation/replacement in §§1–2, approximation discussion §§3–4 and selected §5 applications |
| Broderick 2011.14999v5 | §§1–2, §3.2 and §3.3; exact-refit and linearization limits. Detailed economics applications/proof appendix were not needed for or used in this dossier |
| Min 2501.17858v2 | Main §§1–8 and impact statement, particularly threat model, both strategy definitions, idealized/realistic simulations and defenses. Classifier appendix details were not used |
| Singh 2504.20879v2 | Abstract/introduction, §2 methods/data-source summary and §9 conclusion. No new numerical claim here relies on its detailed experiments/appendices |
| Huang 2508.11847v1 | All main sections and appendices/text/captions, including Table 1 and model/tie conventions. No assertion of independently verified graphics or rerun results |
| Bradley–Terry 1952 | DOI/Crossref metadata only. Full article not obtained/read; original is not marked citation-ready |

Access failures: DOI 10.2307/2334029 redirects to a denied page (HTTP 403); direct JSTOR `/stable/pdf/2334029.pdf` returned 3,038-byte HTML rather than a PDF; Crossref's publisher PDF URL for DOI 10.1093/biomet/39.3-4.324 returned HTTP 403. OpenAlex exact-DOI metadata exposed no open-PDF location. These are recorded source-access limits, not missing evidence for the ranking definition: that definition is present in the reviewed permitted Chiang and Huang sources. A manuscript owner may use a reviewed secondary source, or obtain/read the original before presenting it as consulted.

No prohibited study or derivative page was sought or identified. We do not infer its title/authors/results. All literature payloads read came from allowlisted starter paper IDs or exact metadata queries for the supplied 1952 DOI. No live vote was cast and no model identity attack was performed.

Tools used: Python standard-library urllib/hashlib/json for acquisition/provenance; Poppler pdftotext/pdfinfo for PDF reading. No dependency was installed. `fetch_sources.py` reproduces the seven pinned PDF requests into a caller-selected directory; it does not broaden research to other papers. Its live-download step was not re-run solely to repeat already successful network requests; all underlying seven acquisitions executed successfully in this turn.
