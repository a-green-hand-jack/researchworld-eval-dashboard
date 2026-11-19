# Restricted-access audit

Session date: 2026-11-03 UTC.

## Boundary and outcome

Research evidence was limited to the seven user-supplied original PDFs. Their abstracts and selected method/result pages were read; exact reading scope is in `/work/literature_notes.md`. All pages were extracted locally as part of processing those allowed documents, but extraction is not a claim that every page was substantively read.

**No known accidental forbidden external-content access occurred.** No topical web search, unsupplied paper, citing/discussing page, recommendation, citation service, repository, or paper listing was retrieved. Reference/related-work text within the supplied originals and sample references/navigation within official venue materials were encountered only as part of explicitly allowed documents. None of their external paper/repository links was followed. The excluded paper was undisclosed; no attempt was made to infer its identity.

No experiment code was implemented or run. Python utilities present in this workspace only download/extract/read allowed documents, preserve provenance, and inventory artifacts.

## Network requests actually made

Requests used HTTPS and disabled automatic redirects; no redirects were followed. Unlisted external URLs appearing inside documents were not requested. The supplied `/abs/` records are citation/provenance identifiers; only their allowed `/pdf/` counterparts were downloaded.

### Supplied original papers — all HTTP 200 PDF responses

- https://arxiv.org/pdf/2201.02177
- https://arxiv.org/pdf/2301.05217
- https://arxiv.org/pdf/2210.01117
- https://arxiv.org/pdf/2309.02390
- https://arxiv.org/pdf/2310.06110
- https://arxiv.org/pdf/2303.06173
- https://arxiv.org/pdf/1711.05101

Times, bytes and SHA-256: `downloads.json`. Parsed version strings and page counts: `pdf_metadata.json` and the reading notes.

### Official template/guideline pages and assets — separate from topical research

- https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles — 404, body not read/saved.
- https://neurips.cc/Conferences/2026/CallForPapers — 200.
- https://iclr.cc/Conferences/2027/AuthorGuide — 404, body not read/saved.
- https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip — 200, officially linked by the CFP.
- https://neurips.cc/Conferences/2026/MainTrackHandbook — 200, officially linked by the CFP.
- https://iclr.cc/Conferences/2027/CallForPapers — 200.
- https://iclr.cc/Conferences/2027/AuthorGuidelines — 200, officially linked by the CFP.
- https://media.iclr.cc/Conferences/ICLR2027/iclr-2027-style-files.zip — 200, officially linked by Author Guidelines.
- https://iclr.cc/Conferences/2027/AIPolicyForAuthors — 200, officially linked by Author Guidelines.

Saved request logs, official pages, archives, hashes and submission requirements: `/work/template/PROVENANCE.md` and the JSON logs beside it. The selected venue is ICLR 2027; NeurIPS 2026 materials are segregated as a fallback.

## Future stop-and-log procedure

If any future request or tool output reveals known forbidden content: **stop immediately**, make no further topical retrievals or experimental use, and append an incident record with timestamp, requested/final URL, how it was encountered, the scope of exposure, and the fact that work stopped. Do not summarize the forbidden material into literature notes. No incident record is needed for ordinary navigation/link text embedded in an otherwise allowed source, provided the link is not followed and no prohibited content is fetched.
