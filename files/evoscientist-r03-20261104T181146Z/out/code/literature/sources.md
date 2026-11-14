# Verified sources and acquisition scope

Acquired 2026-11-04 (UTC). Network access was restricted to the five user-specified arXiv PDFs and official NeurIPS rules/template resources. No literature search, citation graph, abstract/metadata API, repository, dataset site, related-paper page, or external PDF hyperlink was visited. Code/data locations mentioned in the notes are **paper-reported, not visited or independently checked**.

## Local artifacts

- PDFs: `/work/literature/<arxiv-id>.pdf` (five files listed below).
- Reading notes: `/work/literature/reading_notes.md`.
- BibTeX: `/work/literature/references.bib`.
- Audit trail, request status, byte counts and PDF/archive SHA256 hashes: `/work/literature/access_log.md`.
- Body-only approximate text: `/work/literature/<arxiv-id>.body.txt`.
- Official 2026 template and rules: `/work/paper/RULES.md` and `/work/paper/neurips2026/`.

## Paper metadata verified against the downloaded PDFs

Titles and author order below were read from PDF page 1; tinyBenchmarks and Sloth also have useful PDF title/author metadata. Line breaks, small caps, superscripts and typographic spacing were normalized. For metabench, the display title places the project name and subtitle on separate lines; no subtitle punctuation is inferred in the BibTeX title.

| Source | arXiv ID | Title | Authors in printed order | Downloaded PDF |
|---|---|---|---|---|
| [1] | 2210.07316 | MTEB: Massive Text Embedding Benchmark | Niklas Muennighoff; Nouamane Tazi; Loïc Magne; Nils Reimers | 24 pages; no explicit arXiv version verified |
| [2] | 2402.14992 | tinyBenchmarks: evaluating LLMs with fewer examples | Felipe Maia Polo; Lucas Weber; Leshem Choshen; Yuekai Sun; Gongjun Xu; Mikhail Yurochkin | 24 pages; ICML 2024, PMLR 235 printed on p.1; arXiv version unverified |
| [3] | 2407.12844 | metabench A Sparse Benchmark of Reasoning and Knowledge in Large Language Models | Alex Kipnis; Konstantinos Voudouris; Luca M. Schulze Buschoff; Eric Schulz | 37 pages; ICLR 2025 printed on p.1; arXiv version unverified |
| [4] | 2405.10938 | Observational Scaling Laws and the Predictability of Language Model Performance | Yangjun Ruan; Chris J. Maddison; Tatsunori Hashimoto | 45 pages; NeurIPS 2024 printed on p.1; arXiv version unverified |
| [5] | 2412.06540 | Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families | Felipe Maia Polo; Seamus Somerstep; Leshem Choshen; Yuekai Sun; Mikhail Yurochkin | 46 pages; NeurIPS 2025; p.1 explicitly prints arXiv:2412.06540v5, 1 Dec 2025 |

### BibTeX conventions and limitations

Entries are arXiv `@misc` records, not fabricated publisher exports. `year` denotes the initial arXiv identifier year (2022 for [1], 2024 for [2]–[5]); that convention is distinct from the conference year printed in later PDF revisions and recorded in each relevant `note`. No DOI, proceedings page interval, unprinted version, or exact initial submission date is supplied. Unversioned PDF URLs resolve to the snapshot downloaded here; use the recorded SHA256 hashes to identify these bytes. Four arXiv version numbers remain unverified, intentionally.

## Reading scope and extraction caveats

These are **selected-section research notes, not claims of complete-paper reading**. PDF page numbers are 1-indexed physical pages, not necessarily printed page labels. See the notes for exact inspected pages. Bibliography sections and post-bibliography appendices were not read. Each body text file ends immediately before the first References heading (p.10 / p.10 / p.11 / p.14 / p.11 respectively). Material elsewhere in these allowed papers may name other work; no such reference was used for discovery or followed.

No system PDF extractor or third-party Python PDF parser was available. Local offline helpers `_offline_pdf_text.py` and `_prepare_reading.py` extracted text from the already-downloaded allowlisted PDFs using standard-library parsing/decompression, without network access or package installation. These are acquisition aids, not an implementation of a research method. Layout, tables, ligatures and some mathematical symbols can be imperfect; the original PDFs remain authoritative. Titles/authors and the substantive prose supporting the notes were readable. Figures were not visually inspected; plots lacking readable numerical labels were not used to invent precise results. Proofs and code were not audited; no reported empirical result was reproduced.

## Direct source URLs

[1] MTEB: Massive Text Embedding Benchmark: https://export.arxiv.org/pdf/2210.07316

[2] tinyBenchmarks: evaluating LLMs with fewer examples: https://export.arxiv.org/pdf/2402.14992

[3] metabench A Sparse Benchmark of Reasoning and Knowledge in Large Language Models: https://export.arxiv.org/pdf/2407.12844

[4] Observational Scaling Laws and the Predictability of Language Model Performance: https://export.arxiv.org/pdf/2405.10938

[5] Sloth: scaling laws for LLM skills to predict multi-benchmark performance across families: https://export.arxiv.org/pdf/2412.06540

[6] Official NeurIPS 2026 Call for Papers: https://neurips.cc/Conferences/2026/CallForPapers

[7] Official NeurIPS 2026 Main Track Handbook: https://neurips.cc/Conferences/2026/MainTrackHandbook

[8] Official NeurIPS 2026 formatting ZIP, directly linked by [6]: https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip

The initially tried official `/Conferences/2026/PaperInformation/StyleFiles` endpoint returned 404. This did **not** require a fallback year: the 2026 CFP supplied the functioning official 2026 ZIP link. No 2025 template was substituted.
