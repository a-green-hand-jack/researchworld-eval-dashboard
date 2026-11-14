# Restricted-access audit

Date: 2026-11-02. No scientific discovery/keyword search, citation traversal, recommendation query, related-paper query or scientific search page was used. The required initial internal-memory preflight returned no results. No prohibited work was identified, guessed or intentionally accessed; no claim is made to have identified the user's unnamed exclusion.

## Scientific originals accessed

Only these seven allowed arXiv works were retrieved and read in the excerpts listed in `reading_notes.md`:

| Original URL | Full text retrieved | Read version |
|---|---|---|
| https://arxiv.org/abs/2406.01574 | https://arxiv.org/pdf/2406.01574 | v6 |
| https://arxiv.org/abs/2310.03714 | https://arxiv.org/pdf/2310.03714 | v1 |
| https://arxiv.org/abs/2406.11695 | https://arxiv.org/pdf/2406.11695 | v2 |
| https://arxiv.org/abs/2310.11324 | https://arxiv.org/pdf/2310.11324 | v2 |
| https://arxiv.org/abs/1411.2664 | https://arxiv.org/pdf/1411.2664 | v3 |
| https://arxiv.org/abs/1502.04585 | https://arxiv.org/pdf/1502.04585 | v1 |
| https://arxiv.org/abs/1212.6906 | https://arxiv.org/pdf/1212.6906 | v6 |

Raw arXiv landing snapshots were stored, but only citation metadata/revision information was parsed. Recommendation/sidebar material was not rendered or navigated. Local PDF text extraction is not access to a different scientific work. References printed inside allowed originals were not followed; externally printed software/dataset URLs were not visited.

## Inaccessible allowed original: Berk DOI

- Allowed request: https://doi.org/10.1214/12-AOS1077
- Redirect destination: https://projecteuclid.org/journals/annals-of-statistics/volume-41/issue-2/Valid-post-selection-inference/10.1214/12-AOS1077.full
- Response: HTTP 200 but only 1,170 bytes of access-block/Incapsula HTML, not the paper.
- Direct original-publisher PDF endpoint attempted: https://projecteuclid.org/journals/annals-of-statistics/volume-41/issue-2/Valid-post-selection-inference/10.1214/12-AOS1077.pdf
- Response: HTTP 200 but `text/html`, 1,161 bytes; likewise not a PDF.
- Saved as `berk.doi.html` and `berk.publisher_pdf_attempt.html`; no fake `.pdf` extension remains. The retrieval log records the initially attempted PDF filename, before renaming the non-PDF response.
- No security-challenge script, iframe, mirror, search or alternative scientific source was followed. No content claims or bibliography entry were produced for this unread work.

The allowed Polo and best-arm starters were not retrieved. Seven actual readings met the requested 6–9 target.

## Incidental material within an allowed original

One local excerpt of https://arxiv.org/pdf/2406.01574 extended from §6.2/§6.3 through limitations/conclusion and into the start of the p.9 bibliography: references [1]–[4] appeared. No cited paper was opened, no titles/authors were used as query material, and none of those entries was used as evidence or added to the bibliography. Subsequent relevant reads were restricted by section/line boundaries. This is an exposure log, not an assertion that any of these entries is the unidentified prohibited work. No recognized prohibited content was encountered.

Some originally requested excerpts also included ordinary related-work text inside the allowed originals. Those texts did not trigger any navigation or additional paper access. No attempt was made to identify the prohibited paper through them.

## Conference author/style materials

Visited only:
- https://neurips.cc/Conferences/2026/CallForPapers
- https://neurips.cc/Conferences/2026/MainTrackHandbook
- https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip

Read author-format/checklist rules and official source files. Did not inspect accepted papers, proceedings, scientific programs, scientific search pages or sidebar/recommendation links. Ordinary navigation labels present in saved page HTML were not followed. No ICML fallback was necessary.

## Deliverables and verification

- `reading_notes.md`: seven original-source readings, verified bibliographic identity/version, actual read sections, short evidence quotes, protocols, availability qualifications and selected-winner/iid caveats.
- `references.bib`: seven verified arXiv entries only.
- `template_provenance.md`: exact official URLs, submission/camera-ready distinction, checklist obligations and source hashes.
- Seven original PDFs plus page-marked extracted `.txt` files and original-page metadata.
- `source_manifest.json`: source-file SHA-256 digests and sizes.
- `verification_report.json`: confirms seven valid PDF signatures, seven BibTeX entries, all 14 evidence quotes present in normalized extracted text and at most 80 characters, and byte-identical extraction of all three official template sources.
- Extraction caution: the PDF extractor emitted an XObject-limit warning while processing MMLU-Pro. The notes rely on the quoted textual passages, not a claim of complete figure/graphic extraction; the original PDF is retained.
- `retrieval_log.json` and `template_retrieval_log.json`: initial direct-retrieval results; first MMLU-Pro landing retrieval and handbook retrieval are separately described in the notes/provenance.
- `/work/paper/`: unmodified official ZIP and its three source members.

No algorithm implementation, experiment, model evaluation, conference-paper browsing or novelty claim was performed.
