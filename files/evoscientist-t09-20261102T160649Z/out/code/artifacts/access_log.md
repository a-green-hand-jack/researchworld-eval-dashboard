# Access log: closed-list literature and official template acquisition

Acquisition date: **2026-11-02 UTC**. Machine-readable event log: `/work/artifacts/access_events.jsonl`. All times below are UTC. This document reports actual accesses, including the template provenance-route caveat; it is not a claim of a broader literature review.

## Scope and restrictions

- Literature requests were limited to the four exact user-supplied arXiv PDF URLs below. No abstract pages, search engines, topic queries, citation graphs, recommendations, aggregators, newer papers, repository pages, or reference destinations were requested.
- No attempt was made to identify the prohibited published paper or its discussions/citing pages. No known prohibited material was encountered. Consequently there is no identified prohibited URL/extent incident to report. This is not a claim that every work mentioned inside the permitted PDFs was identified or screened.
- Local PDF extraction includes original reference text because it extracts whole downloaded files, but references were not followed externally. Some source reads included related-work paragraphs and the start of the references on Chin PDF p. 30; these were not used for source discovery. Official HTML contains external links that were not followed.
- A required procedural-memory preflight searched only downloader/logging mechanics and returned no observations. It did not access literature.
- All network requests used the standard-library downloader `/work/artifacts/acquire_allowlisted.py`. Redirects were configured to be blocked before following; **none occurred**. No browser subresources, scripts, CSS, cookies/analytics calls, or linked pages were fetched implicitly.
- No experiment code or manuscript draft was inspected or changed. Local scripts created under `artifacts/` are acquisition/extraction/audit helpers only. No baseline, experiment, training, or reproduction was performed.

## Template provenance-route caveat

The specifically requested NeurIPS 2026 StyleFiles route returned 404, as did its PaperInformation parent and a 2025 StyleFiles fallback probe. The permitted official 2026 Call for Papers was then used for acquisition provenance: it explicitly linked the official 2026 media ZIP and the official Main Track Handbook. The ZIP was downloaded only after that exact link had been read. **Its link was verified on the CFP, not on a StyleFiles page.** If the instruction “media.neurips.cc URLs referenced there” is construed literally as requiring the unavailable StyleFiles page rather than the permitted submission instructions, this is a **provenance-route deviation** and requires user review; it must not be presented as exact StyleFiles-route compliance. All conference requests still went only to `neurips.cc` or the directly linked `media.neurips.cc` asset. No third-party fallback or invented style was used.

## Complete external request chronology

Exactly **10 GET requests** were logged: **7 successes and 3 HTTP 404 failures**, with no redirects. Failed response bodies were not saved or interpreted. A 404 shows that a particular route was unavailable, not that the 2026 template itself was unavailable.

| UTC completion time | URL | Outcome | Saved destination |
|---|---|---|---|
| 2026-11-02T16:10:12.602642+00:00 | https://arxiv.org/pdf/1808.08683 | 200 | `/work/artifacts/sources/1808.08683.pdf` |
| 2026-11-02T16:10:13.101264+00:00 | https://arxiv.org/pdf/2302.04997 | 200 | `/work/artifacts/sources/2302.04997.pdf` |
| 2026-11-02T16:10:13.680354+00:00 | https://arxiv.org/pdf/1305.6156 | 200 | `/work/artifacts/sources/1305.6156.pdf` |
| 2026-11-02T16:10:14.141972+00:00 | https://arxiv.org/pdf/1305.6979 | 200 | `/work/artifacts/sources/1305.6979.pdf` |
| 2026-11-02T16:11:49.426693+00:00 | https://neurips.cc/Conferences/2026/PaperInformation/StyleFiles | HTTP Error 404: Not Found | `Not saved` |
| 2026-11-02T16:12:01.340936+00:00 | https://neurips.cc/Conferences/2026/CallForPapers | 200 | `/work/paper/template/neurips_2026_callforpapers.html` |
| 2026-11-02T16:12:03.061110+00:00 | https://neurips.cc/Conferences/2026/PaperInformation | HTTP Error 404: Not Found | `Not saved` |
| 2026-11-02T16:12:17.912437+00:00 | https://neurips.cc/Conferences/2025/PaperInformation/StyleFiles | HTTP Error 404: Not Found | `Not saved` |
| 2026-11-02T16:12:59.410610+00:00 | https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | 200 | `/work/paper/template/Formatting_Instructions_For_NeurIPS_2026.zip` |
| 2026-11-02T16:13:01.366945+00:00 | https://neurips.cc/Conferences/2026/MainTrackHandbook | 200 | `/work/paper/template/neurips_2026_maintrackhandbook.html` |

## Original download integrity

All successful responses ended at the original requested URL (no redirects). Sizes and hashes below refer to exact original response bytes.

| URL | Bytes | Content type | SHA-256 |
|---|---:|---|---|
| https://arxiv.org/pdf/1808.08683 | 5,080,015 | `application/pdf` | `631a0b11b48b1dc1e67c23290498258b55c545e9ad785064f9ca12d4456f48e2` |
| https://arxiv.org/pdf/2302.04997 | 366,694 | `application/pdf` | `c4873151e7448ae2c327cedb0b8aed9da13bf76e6fc5e79ed02d8c2438a7a876` |
| https://arxiv.org/pdf/1305.6156 | 1,031,502 | `application/pdf` | `0e90860ec951314c117b018ae76acb5adb1c476aec0516315c4d6c34bc6cccbb` |
| https://arxiv.org/pdf/1305.6979 | 355,800 | `application/pdf` | `0112a57936fb0ec7ca33ff38b601fdc20982920eaf328ff431b0c9d36e106e35` |
| https://neurips.cc/Conferences/2026/CallForPapers | 53,579 | `text/html; charset=utf-8` | `6e527f14a1c57f052c90776172709e473c6fc5be06effdb40b72701386f40897` |
| https://media.neurips.cc/Conferences/NeurIPS2026/Formatting_Instructions_For_NeurIPS_2026.zip | 20,259 | `application/zip` | `82473931e3ef710fcd3f4a8cd4119b9de32e56825f90f9e5a6d55f2d01b817d9` |
| https://neurips.cc/Conferences/2026/MainTrackHandbook | 167,185 | `text/html; charset=utf-8` | `93e4f17909a269b9937dba0f6d9c7ddb018d73b7d556b81073a2848e21f90441` |

All seven successful downloads were rehashed locally when preparing this log and matched their acquisition records.

## Official archive member integrity

Archive: `/work/paper/template/Formatting_Instructions_For_NeurIPS_2026.zip`. The official ZIP contains exactly three files and no compiled PDF. ZIP CRC validation passed; each extracted original was compared byte-for-byte to its archive member.

| Exact extracted host path | Bytes | SHA-256 |
|---|---:|---|---|
| `/work/paper/template/official_2026/neurips_2026.tex` | 19,118 | `cf4cee7991665306d1daaa3985be4feec7f8889d6d072ffa12f99a8e1537d797` |
| `/work/paper/template/official_2026/checklist.tex` | 26,167 | `780ba13c480f652dcc42e69ed61a752ce0ea270f15d332d4a45b059dabad84f6` |
| `/work/paper/template/official_2026/neurips_2026.sty` | 13,704 | `c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a` |

## Reading and local processing record

- Original PDFs were downloaded once each and retained unchanged in `/work/artifacts/sources/`. Page counts found by the local PDF page-tree parser: Chin 38, Han/Ugander 34, Aronow/Samii 40, Ugander et al. 9.
- Focused reading covered Chin model/feature/inference/simulation/application sections (PDF pp. 6–29), Han/Ugander definitions, Algorithms 1–5, theory and simulation/application sections (pp. 3–25), Aronow/Samii exposure/estimation/inference/refinement/misspecification and application sections (pp. 4–27, with start of p. 28), and Ugander et al. exposure, probability, variance and clustering sections (pp. 2–9). All title-page metadata was read. Some introductory text was also read; none of its cited sources was followed.
- `pdftotext`, `pypdf`, `PyPDF2`, PyMuPDF/`fitz`, and `pdfminer` were unavailable in the active Python environment. No package installation or package-registry request was made. Local reader/tool checks found no usable alternative PDF reader.
- `/work/artifacts/extract_pdf_local.py` uses local PDF objects, zlib streams, and installed fontTools glyph names to produce `.txt` and `.extraction.json` files alongside each PDF. It makes no network requests. A token-delimiter issue initially omitted text immediately before some font changes; it was corrected and all four local text outputs regenerated before the final methods notes. This local extractor is not a full PDF renderer: equation symbols, tables, and layout can remain lossy. No visual/equation-by-equation or proof audit is claimed.
- `/work/artifacts/local_extract.py` locally converts successful official HTML to text without fetching any URLs. A compact handbook extraction is also saved. Local text derivatives are not original downloads and do not receive source-status citations.
- Official 2026 style/template/checklist members were read, and the CFP template link plus the handbook formatting/checklist paragraphs were checked. The style identifies `neurips_2026` dated 2026-01-29. The template shell includes `\input{checklist.tex}`. Submission limit: nine content pages including figures/tables, excluding references, technical appendices and checklist. The handbook permits one additional content page for accepted camera-ready papers. Checklist inclusion is mandatory.
- No LaTeX build was run. The package dependencies, resulting layout/page count, and compile success were not tested. Instructions in `/work/paper/template/README_acquisition.md` are for later work on a separate copy, not a verified build.
- Two environment-check shell commands were blocked before execution because of system-path restrictions. Several malformed local tool calls returned argument-validation errors; a direct PDF file read did not yield usable text. These were local tooling failures, not external access or source failures.
- No paper repository/code, dataset, data license, or supplementary-material download was verified. Bibliographic years in the notes distinguish downloaded arXiv version dates from identifier years and do not infer a journal/conference year from a template placeholder.

## Final deliverables

- `/work/artifacts/literature_notes.md`: verified bibliography, methods, assumptions, inference/evaluation protocols, limitations, source-linked planning checks and template status.
- `/work/artifacts/access_log.md`: this audit.
- `/work/artifacts/access_events.jsonl`: original machine-readable request log.
- `/work/artifacts/sources/{1808.08683,2302.04997,1305.6156,1305.6979}.pdf`: four original downloads; matching `.txt` files are locally derived.
- `/work/paper/template/Formatting_Instructions_For_NeurIPS_2026.zip`: exact official archive.
- `/work/paper/template/official_2026/{neurips_2026.sty,neurips_2026.tex,checklist.tex}`: unmodified exact archive members.
- `/work/paper/template/README_acquisition.md`: provenance, requirements, integrity and later-use instructions.
- `/work/paper/template/template_manifest.json`: generated member-integrity metadata.

No external requests were made after the official handbook acquisition recorded above.
