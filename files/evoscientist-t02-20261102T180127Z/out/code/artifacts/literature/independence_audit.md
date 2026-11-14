# Independence audit

## Constraints followed
- No topical/keyword web searches, literature discovery, citation-graph queries, recommendations, aggregators, or external repositories were consulted.
- Fetched only the seven specified arXiv abstract/PDF endpoints for literature. Raw abstract HTML was archived but not rendered/read, avoiding recommendation/sidebar material. Only paper document text is used for research claims.
- Local extraction and document navigation are not external searches. Bibliographies are excluded from subsequent `*.reading.txt` viewing copies. Original PDFs/text remain intact as requested.

## Accidental exposure — stopped and excluded
- Source: https://arxiv.org/pdf/2201.02177 (allowlisted document), page 5, beginning of its REFERENCES section.
- Extent: first read of local `2201.02177.txt`, requested lines 1–205, displayed the REFERENCES heading and initial bibliography entries (local lines 184–205). No linked paper, URL, cited-by list, recommendation, or repository was opened. Reading of the bibliography stopped immediately upon recognition.
- Handling: bibliography entries were not used for evidence, identity inference, novelty assessment, or follow-up. No forbidden-paper identity was guessed. Subsequent reads use bibliography-filtered copies. One nonallowlisted URL visibly printed in that accidental bibliography excerpt was `http://arxiv.org/abs/1609.04836`; it was not opened, searched, identified, or used. It is recorded here only as the literal accidental-exposure URL, without inferring any forbidden-paper identity.
- This is reported conservatively as accidental forbidden-related material exposure; the underlying source itself was allowlisted. Permitted-paper reading continued, not bibliography reading.
- Source: https://neurips.cc/Conferences/2026/MainTrackHandbook . A broad formatting-policy excerpt also displayed its `Further reading` list, local extracted-text lines 192–240 (including resource/paper titles, not their bodies). Stopped using/reading that section upon recognition; no listed resource was opened and no title was used to infer a forbidden-paper identity. Only official formatting instructions beginning at the Authors section are used as policy evidence.
- Source: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip , member `neurips_2026.tex`. A tail excerpt intended to check appendix/checklist inclusion displayed example bibliography entries at local lines 464–478. Stopped at recognition; these examples are not consulted-paper sources and were not followed or used.
- Source: https://neurips.cc/Conferences/2026/CallForPapers . The official navigation extraction incidentally displayed the URL `/accounts/login?nextp=/virtual/2026/loc/sydney/poster/150797` (no paper title or content). It was not opened or used; no identity was inferred. Global navigation, proceedings, and submission-platform links were not followed.
- Some permitted-paper excerpts also contain embedded Related Work paragraphs, citations and author-reported code URLs. These are not additional consulted sources; no external destination, citation relationship, or repository was inspected. Reading notes use only claims/methods of the seven allowlisted documents themselves. No effort was made to identify any forbidden paper.

## Extraction caveat
- pypdf emitted `Exceeded 5000 form XObject invocations ... further form content is skipped` during extraction of the batch. Original PDFs are preserved. Text-only figure extraction may omit graphical labels; do not treat plots as quantitatively digitized evidence.
